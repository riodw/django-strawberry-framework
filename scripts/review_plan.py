"""Generate, scope and reconcile the REVIEW flow's per-release plan.

``docs/review/REVIEW.md`` is the method; this script owns only the plan's
shape and the inventory arithmetic Worker 0 would otherwise do by hand. It is
pure git plus filesystem: nothing is imported from the package and no Django
settings are loaded.

``plan``
    Write ``docs/review/review-<release>.md`` (``0.0.15`` becomes
    ``review-0_0_15.md``; the release is read from the package
    ``__version__`` unless ``--target-release`` names it). The inventory is
    ``git ls-files 'django_strawberry_framework/*.py'`` minus every
    ``__init__.py``: one file item per module, one folder integration item per
    package folder, the project integration item (which carries every
    ``__init__.py`` and names the ones holding definitions), and the final
    gate. ``--scope`` (repeatable; a package folder or module, repo- or
    package-relative) limits the run; every item outside it is listed under
    ``## Out of scope this run`` so an unticked box never reads as examined.
    A scope entry that matches no inventory file fails the run. An existing
    plan is never overwritten without ``--force``; its run ids carry forward so
    the new ``Run:`` number follows the highest recorded one.

``scope``
    Print the package ``.py`` files changed between ``--since`` (default: the
    latest tag reachable from ``HEAD``) and the working tree, in three groups:
    committed changes with their ``HEAD`` blob ids, dirty or untracked paths
    (concurrent work, with working-tree ``git hash-object`` ids), and renames.
    ``--json`` emits the same data machine-readably.

``reconcile --plan PATH``
    Read-only. Compare a plan's items with the current inventory and report
    tracked or untracked ``.py`` files without an item, items whose file is
    gone or renamed, folders without an item, and items whose status requires
    artifacts that are missing beside the plan. Exit 1 when anything is off,
    0 when clean.

Usage::

    uv run python scripts/review_plan.py plan [--scope PATH ...] [--mode MODE]
        [--target-release RELEASE] [--output PATH] [--force]
    uv run python scripts/review_plan.py scope [--since REV] [--json]
    uv run python scripts/review_plan.py reconcile --plan docs/review/review-0_0_15.md
"""

from __future__ import annotations

import argparse
import ast
import difflib
import importlib.util
import json
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = "django_strawberry_framework"
REVIEW_DIR = Path("docs/review")
AXES = ("performance", "mechanics", "comments")
MODES = ("autonomous", "pause-after-each-item")
RENAME_SIMILARITY = 0.5
_DRY_HELPERS_PATH = REPO_ROOT / "docs" / "dry" / "export_dry_review.py"


def _load_dry_helpers(path: Path) -> ModuleType:
    """Load the DRY planner module from its file path; ``docs`` is not a package."""
    name = "_review_plan_dry_helpers"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load the DRY plan helpers from {path.as_posix()}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except FileNotFoundError as exc:
        del sys.modules[name]
        raise ImportError(f"the DRY plan helpers are missing: {path.as_posix()}") from exc
    return module


_dry = _load_dry_helpers(_DRY_HELPERS_PATH)
RELEASE_PATTERN = _dry.RELEASE_PATTERN

_RUN_ID = re.compile(
    r"^(?:Run:|## Run) (?P<release>\S+) (?P<date>\d{4}-\d{2}-\d{2})-(?P<n>\d+)\s*$",
    re.MULTILINE,
)
_ITEM_LINE = re.compile(r"^- \[(?P<mark>[ xX])\] (?P<label>.+?)\s*$")
_FIELD_LINE = re.compile(r"^ {4}- (?P<key>[A-Za-z][A-Za-z ]*):(?P<value>.*)$")
_CYCLE_BASELINE_LINE = re.compile(r"CYCLE_BASELINE=(?P<rev>[0-9a-fA-F]{7,64}|HEAD)\b")
_NO_ARTIFACT_STATUSES = frozenset({"pending", "out-of-scope"})


# ---------------------------------------------------------------------------
# git plumbing


def _git(root: Path, *args: str, stdin: str | None = None) -> str:
    """Run one git command in ``root`` and return its stdout."""
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "--no-pager",
                *args,
            ],
            check=True,
            capture_output=True,
            text=True,
            input=stdin,
        )
    except FileNotFoundError as exc:
        raise ValueError("git is not installed") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or f"exit {exc.returncode}"
        raise ValueError(f"git {' '.join(args)} failed: {message}") from exc
    return result.stdout


def _nul_fields(output: str) -> list[str]:
    """Split ``-z`` output into its NUL-separated fields."""
    return [part for part in output.split("\0") if part]


def _package_python_pathspec() -> str:
    """Return the pathspec REVIEW's inventory command uses."""
    return f":(top){PACKAGE_DIR}/*.py"


def _tracked_python(root: Path) -> list[str]:
    """Return every tracked package ``.py`` path, repo-relative, sorted."""
    output = _git(root, "ls-files", "-z", "--", _package_python_pathspec())
    return sorted(_nul_fields(output))


def _untracked_python(root: Path) -> list[str]:
    """Return untracked, non-ignored package ``.py`` paths, repo-relative, sorted."""
    output = _git(
        root,
        "ls-files",
        "-z",
        "--others",
        "--exclude-standard",
        "--",
        _package_python_pathspec(),
    )
    return sorted(_nul_fields(output))


def _is_init(path: str) -> bool:
    """Return whether ``path`` names an ``__init__.py``."""
    return path.rsplit("/", 1)[-1] == "__init__.py"


def _package_relative(path: str) -> str:
    """Strip the package prefix from a repo-relative path."""
    return path.removeprefix(f"{PACKAGE_DIR}/")


def _package_folders(paths: Iterable[str]) -> list[str]:
    """Return every package-relative folder below the package root, sorted."""
    folders: set[str] = set()
    for path in paths:
        parent = _package_relative(path).rpartition("/")[0]
        while parent:
            folders.add(parent)
            parent = parent.rpartition("/")[0]
    return sorted(folders)


# ---------------------------------------------------------------------------
# plan


@dataclass(frozen=True)
class Item:
    """One plan item: its checkbox label, fields and artifact names."""

    kind: str
    key: str
    label: str
    artifacts: tuple[str, ...]
    extra: tuple[str, ...] = ()

    def render(self, status: str) -> list[str]:
        """Return the item lines in REVIEW's item shape."""
        lines = [f"- [ ] {self.label}", f"    - Status: {status}"]
        if self.kind == "file":
            lines.append("    - Path class:")
        lines.extend(f"    - {line}" for line in self.extra)
        if self.artifacts:
            lines.append(f"    - Artifacts: {', '.join(self.artifacts)}")
        return lines


def _artifact_set(relative: str) -> tuple[str, ...]:
    """Return the main artifact name plus one record per axis for ``relative``."""
    main = _dry._artifact_name("rev", Path(relative))
    stem = main.removesuffix(".md")
    return (main, *(f"{stem}.{axis}.md" for axis in AXES))


def _init_definitions(root: Path, path: str) -> tuple[str, ...]:
    """Return top-level class and function names an ``__init__.py`` defines."""
    try:
        tree = ast.parse((root / path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeError):
        return ()
    kinds = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    return tuple(node.name for node in tree.body if isinstance(node, kinds))


def _project_item(root: Path, init_paths: Sequence[str]) -> Item:
    """Build the project integration item naming every ``__init__.py``."""
    inits = []
    for path in init_paths:
        names = _init_definitions(root, path)
        entry = f"`{_package_relative(path)}`"
        if names:
            entry += f" (defines {', '.join(f'`{name}`' for name in names)})"
        inits.append(entry)
    extra = (
        "Covers: package-root modules as one component; public exports; import-time cost vs "
        "`## Bench baseline`; end-to-end lifecycle; every `__init__.py` (no file item "
        "reviews them)",
        f"`__init__.py` files: {', '.join(inits) if inits else 'none'}",
    )
    return Item(
        kind="project",
        key="project",
        label="Project integration",
        artifacts=_artifact_set("project"),
        extra=extra,
    )


_GATE_ITEM = Item(
    kind="gate",
    key="gate",
    label="Final gate",
    artifacts=(),
    extra=(
        "Runs: `uv run pytest`; every `## Pending execution` command from every artifact; the "
        "`## Bench baseline` commands in a fresh workspace copy, delta recorded",
    ),
)


def _normalize_scope(entry: str) -> str:
    """Return a scope entry as a package-relative path, ``""`` for the whole package."""
    text = entry.strip().replace("\\", "/").strip("/")
    while text.startswith("./"):
        text = text[2:]
    if text in {"package", PACKAGE_DIR}:
        return ""
    return _package_relative(text)


def _scope_matches(scope: str, relative: str) -> bool:
    """Return whether a package-relative path lies inside one scope entry."""
    return not scope or relative == scope or relative.startswith(f"{scope}/")


def _resolve_scope(entries: Sequence[str], files: Sequence[str]) -> tuple[str, ...] | None:
    """Return the normalized scope, ``None`` for the whole package; fail closed."""
    if not entries:
        return None
    normalized = []
    for entry in entries:
        scope = _normalize_scope(entry)
        if not scope:
            return None
        if not any(_scope_matches(scope, relative) for relative in files):
            raise ValueError(
                f"--scope {entry!r} matches no inventory file under {PACKAGE_DIR}/ "
                "(tracked, non-__init__ .py)",
            )
        if scope not in normalized:
            normalized.append(scope)
    return tuple(normalized)


def _scope_label(scope: tuple[str, ...] | None, files: Sequence[str]) -> str:
    """Render the ``Scope:`` value: folders end in ``/``, modules do not."""
    if scope is None:
        return "package"
    return ", ".join(entry if entry in files else f"{entry}/" for entry in scope)


def _existing_run_max(path: Path, release: str) -> int:
    """Return the highest run number an existing plan records for ``release``."""
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, IsADirectoryError):
        return 0
    runs = [int(match["n"]) for match in _RUN_ID.finditer(text) if match["release"] == release]
    return max(runs, default=0)


def _assert_unique_artifacts(items: Sequence[Item]) -> None:
    """Refuse a plan in which two items would share one artifact name."""
    owners: dict[str, str] = {}
    for item in items:
        for name in item.artifacts:
            if name in owners:
                raise ValueError(
                    f"artifact name collision: {name} belongs to both {owners[name]!r} and "
                    f"{item.label!r}",
                )
            owners[name] = item.label


def _bench_baseline_block() -> list[str]:
    """Render the empty bench table Worker 0 fills at cycle entry and at the gate."""
    commands = (
        'uv run --directory "$WS" python scripts/bench_plan_cache.py',
        'uv run --directory "$WS" python scripts/bench_optimizer_walk.py',
        'uv run --directory "$WS" python -X importtime -c "import django_strawberry_framework"',
    )
    return [
        "## Bench baseline",
        "",
        'Bound to `CYCLE_BASELINE`; `$WS` is a fresh workspace copy (REVIEW.md "Workspace"). '
        "Worker 0",
        "fills Baseline at cycle entry, Gate and Delta at the final gate. "
        "`scripts/bench_nested_fetch.py`",
        "joins only when Rio authorizes a Postgres cell.",
        "",
        "| Command | Baseline | Gate | Delta |",
        "|---|---|---|---|",
        *(f"| `{command}` | | | |" for command in commands),
    ]


_HOW_TO_WORK_ONE_ITEM = """## How to work one item

`docs/review/REVIEW.md` is the method; this section only points into it.

- Roles and dispatch order: "Roles", "Cycle per file item".
- Per-axis looks-for list, instrument and record fields: "The three axes", "Severity".
- Evidence and measurement: "Ground rules", "Workspace".
- Dirty paths, item baselines, ledger rows: "Baseline and ownership".
- Artifact shapes and names: "Artifacts".
- Folder and project items: "Integration passes"; the gate: "Final gate and closeout".
- Plan drift before the first dispatch and before the gate:
  `uv run python scripts/review_plan.py reconcile --plan <this plan>`."""


def _closing_blocks() -> list[str]:
    """Render the sections Worker 0 maintains: decisions, ledger, outcomes."""
    return [
        "## Decisions",
        "",
        "Maintainer decisions the run surfaced: ruff rules to enable, trade-offs, contracts "
        "nobody could cite.",
        "",
        "## Owned changes",
        "",
        "One row per tracked edit or new file a verified item landed. A later item may build on a "
        "path",
        "listed here; any other dirty hunk is external.",
        "",
        "| Path | Item | Axis | Symbols changed |",
        "|---|---|---|---|",
        "",
        "## Outcomes",
        "",
        "Filled by Worker 0 at closeout before any scratch is removed; a scoped run adds "
        '"Scope of this run".',
        "",
    ]


def _render_plan(
    root: Path,
    *,
    release: str,
    run_number: int,
    generated_date: str,
    mode: str,
    scope_entries: Sequence[str],
    status_output: str | None,
) -> tuple[str, dict[str, int]]:
    """Render the plan text and its item counts."""
    tracked = _tracked_python(root)
    files = [_package_relative(path) for path in tracked if not _is_init(path)]
    if not files:
        raise ValueError(f"no tracked non-__init__ .py files under {PACKAGE_DIR}/")
    scope = _resolve_scope(scope_entries, files)
    folders = _package_folders(tracked)

    file_items = {
        relative: Item(
            kind="file",
            key=relative,
            label=relative,
            artifacts=_artifact_set(relative),
        )
        for relative in files
    }
    folder_items = {
        folder: Item(
            kind="folder",
            key=folder,
            label=f"{folder}/ integration",
            artifacts=_artifact_set(folder),
        )
        for folder in folders
    }
    project = _project_item(root, [path for path in tracked if _is_init(path)])
    _assert_unique_artifacts([*file_items.values(), *folder_items.values(), project])

    def in_scope_file(relative: str) -> bool:
        return scope is None or any(_scope_matches(entry, relative) for entry in scope)

    def in_scope_folder(folder: str) -> bool:
        return scope is None or any(_scope_matches(entry, folder) for entry in scope)

    ordered: list[Item] = []
    sections: list[tuple[str, list[Item]]] = []

    def walk(folder: str) -> None:
        members = [
            file_items[relative]
            for relative in files
            if relative.rpartition("/")[0] == folder and in_scope_file(relative)
        ]
        ordered.extend(file_items[r] for r in files if r.rpartition("/")[0] == folder)
        if members:
            sections.append((f"{folder}/" if folder else "Package root", members))
        for child in folders:
            if child.rpartition("/")[0] == folder:
                walk(child)
        if folder:
            ordered.append(folder_items[folder])
            if in_scope_folder(folder):
                sections.append((f"{folder}/ integration", [folder_items[folder]]))

    walk("")
    ordered.append(project)
    project_in_scope = scope is None
    if project_in_scope:
        sections.append(("Project", [project, _GATE_ITEM]))
    else:
        sections.append(("Final gate", [_GATE_ITEM]))
    in_scope = {id(item) for _, members in sections for item in members}
    out_of_scope = [item for item in ordered if id(item) not in in_scope]

    lines = [
        f"# REVIEW plan: {release}",
        "",
        "Status: planned",
        f"Mode: {mode}",
        f"Run: {release} {generated_date}-{run_number}",
        f"Scope: {_scope_label(scope, files)}",
        "",
        "Method: `docs/review/REVIEW.md`. Fresh source review; findings from prior build, review, "
        "DRY or",
        "hunt artifacts are not imported.",
        "",
        *_dry._cycle_baseline_block(status_output),
        "",
        "CYCLE_BASELINE=<Worker 0 fills: `git stash create`, empty -> HEAD>",
        f"Untracked under {PACKAGE_DIR}/: <Worker 0 fills>",
        "",
        *_bench_baseline_block(),
        "",
        *_HOW_TO_WORK_ONE_ITEM.split("\n"),
    ]
    for heading, members in sections:
        lines.extend(["", f"## {heading}", ""])
        for item in members:
            lines.extend(item.render("pending"))
    if out_of_scope:
        lines.extend(
            [
                "",
                "## Out of scope this run",
                "",
                f"Not examined under `Scope: {_scope_label(scope, files)}`; an unticked box here "
                "is not a pending",
                "review of this run. A later run moves an item into its scope under its own "
                "`## Run` heading.",
                "",
            ],
        )
        for item in out_of_scope:
            lines.extend(item.render("out-of-scope"))
    lines.extend(["", *_closing_blocks()])
    counts = {
        "file": sum(1 for relative in files if in_scope_file(relative)),
        "folder": sum(1 for folder in folders if in_scope_folder(folder)),
        "out_of_scope": len(out_of_scope),
    }
    return "\n".join(lines), counts


def _default_output(release: str) -> Path:
    """Return ``docs/review/review-<release-underscored>.md``."""
    return REVIEW_DIR / f"review-{release.replace('.', '_')}.md"


def _run_plan(args: argparse.Namespace) -> int:
    """Write a fresh plan; refuse to overwrite without ``--force``."""
    root = args.root.resolve()
    release = args.target_release or _dry._package_version(root / PACKAGE_DIR)
    if not RELEASE_PATTERN.fullmatch(release):
        raise ValueError(
            f"invalid --target-release {release!r}; expected dotted digits such as 0.0.15",
        )
    output = _dry._resolve_path(args.output or _default_output(release), root)
    if output.exists() and not args.force:
        raise FileExistsError(_dry._overwrite_error(output))
    content, counts = _render_plan(
        root,
        release=release,
        run_number=_existing_run_max(output, release) + 1,
        generated_date=_dry._validate_date(args.generated_date),
        mode=args.mode,
        scope_entries=args.scope,
        status_output=_dry._git_status_short(root),
    )
    _dry._atomic_write(output, content, force=args.force)
    print(
        f"Wrote {_dry._display_path(output, root)} ({counts['file']} file item(s), "
        f"{counts['folder']} folder item(s) in scope, {counts['out_of_scope']} out of scope)",
    )
    return 0


# ---------------------------------------------------------------------------
# scope


@dataclass
class ScopeReport:
    """Changed package ``.py`` files between a base revision and the working tree."""

    since: str
    since_sha: str
    head_sha: str
    committed: list[dict[str, object]] = field(default_factory=list)
    dirty: list[dict[str, object]] = field(default_factory=list)
    renames: list[dict[str, object]] = field(default_factory=list)

    def folders(self) -> list[str]:
        """Return the package-relative folders any changed path sits in."""
        paths: list[str] = [str(entry["path"]) for entry in (*self.committed, *self.dirty)]
        paths.extend(str(entry["new"]) for entry in self.renames)
        folders = {_package_relative(path).rpartition("/")[0] for path in paths}
        return sorted(f"{folder}/" if folder else "(package root)" for folder in folders)

    def as_dict(self) -> dict[str, object]:
        """Return the report as JSON-ready data."""
        return {
            "since": self.since,
            "since_sha": self.since_sha,
            "head_sha": self.head_sha,
            "committed": self.committed,
            "dirty": self.dirty,
            "renames": self.renames,
            "folders": self.folders(),
        }


def _latest_tag(root: Path) -> str:
    """Return the latest tag reachable from ``HEAD``."""
    try:
        return _git(root, "describe", "--tags", "--abbrev=0", "HEAD").strip()
    except ValueError as exc:
        raise ValueError("no tag is reachable from HEAD; pass --since <rev>") from exc


def _head_blobs(root: Path) -> dict[str, str]:
    """Return ``path -> blob id`` for every package file at ``HEAD``."""
    output = _git(root, "ls-tree", "-r", "-z", "HEAD", "--", f":(top){PACKAGE_DIR}")
    blobs = {}
    for record in _nul_fields(output):
        meta, _, path = record.partition("\t")
        blobs[path] = meta.split()[2]
    return blobs


def _worktree_blobs(root: Path, paths: Sequence[str]) -> dict[str, str]:
    """Return ``path -> git hash-object`` for every existing working-tree path."""
    present = [path for path in paths if (root / path).is_file()]
    if not present:
        return {}
    output = _git(root, "hash-object", "--stdin-paths", stdin="\n".join(present) + "\n")
    return dict(zip(present, output.split(), strict=True))


def _parse_name_status(output: str) -> list[tuple[str, str, str | None]]:
    """Parse ``--name-status -z`` into ``(status, path, rename target)`` rows."""
    fields = _nul_fields(output)
    rows: list[tuple[str, str, str | None]] = []
    index = 0
    while index < len(fields):
        status = fields[index]
        if status[:1] in {"R", "C"}:
            rows.append((status, fields[index + 1], fields[index + 2]))
            index += 3
        else:
            rows.append((status, fields[index + 1], None))
            index += 2
    return rows


def _parse_porcelain(output: str) -> list[tuple[str, str, str | None]]:
    """Parse ``status --porcelain=v1 -z`` into ``(XY, path, rename source)`` rows."""
    fields = output.split("\0")
    rows: list[tuple[str, str, str | None]] = []
    index = 0
    while index < len(fields):
        record = fields[index]
        index += 1
        if not record:
            continue
        code, path = record[:2], record[3:]
        source = None
        if "R" in code or "C" in code:
            source = fields[index]
            index += 1
        rows.append((code, path, source))
    return rows


def build_scope(root: Path, since: str | None) -> ScopeReport:
    """Collect committed, dirty and renamed package ``.py`` changes."""
    base = since or _latest_tag(root)
    report = ScopeReport(
        since=base,
        since_sha=_git(root, "rev-parse", "--verify", f"{base}^{{commit}}").strip(),
        head_sha=_git(root, "rev-parse", "HEAD").strip(),
    )
    diff = _git(
        root,
        "diff",
        "--name-status",
        "-M",
        "-z",
        f"{report.since_sha}",
        "HEAD",
        "--",
        _package_python_pathspec(),
    )
    head_blobs = _head_blobs(root)
    status = _git(
        root,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--",
        f":(top){PACKAGE_DIR}",
    )
    porcelain = [row for row in _parse_porcelain(status) if row[1].endswith(".py")]
    dirty_paths = {path for _, path, _ in porcelain}
    for code, path, target in _parse_name_status(diff):
        if target is not None:
            report.renames.append(
                {
                    "old": path,
                    "new": target,
                    "similarity": code,
                    "where": "committed",
                    "blob": head_blobs.get(target),
                },
            )
            continue
        report.committed.append(
            {
                "status": code,
                "path": path,
                "blob": head_blobs.get(path),
                "init": _is_init(path),
                "also_dirty": path in dirty_paths,
            },
        )
    worktree = _worktree_blobs(root, sorted(dirty_paths))
    for code, path, source in porcelain:
        if source is not None:
            report.renames.append(
                {
                    "old": source,
                    "new": path,
                    "similarity": code.strip(),
                    "where": "index",
                    "blob": worktree.get(path),
                },
            )
        report.dirty.append(
            {
                "status": code,
                "path": path,
                "worktree_blob": worktree.get(path),
                "init": _is_init(path),
            },
        )
    return report


def _render_scope(report: ScopeReport) -> str:
    """Render the scope report as plain text."""
    lines = [
        f"Package .py changes since {report.since} ({report.since_sha[:12]}) to HEAD "
        f"{report.head_sha[:12]}, plus the working tree.",
        "`__init__.py` paths belong to the project integration item.",
        "",
        f"Committed ({report.since}..HEAD): {len(report.committed)}",
    ]
    for entry in report.committed:
        notes = [
            note
            for flag, note in (("init", "project"), ("also_dirty", "also dirty"))
            if entry[flag]
        ]
        suffix = f"  ({', '.join(notes)})" if notes else ""
        blob = entry["blob"] or "-"
        lines.append(f"  {entry['status']:<2} {entry['path']}  HEAD {blob}{suffix}")
    lines.extend(["", f"Dirty or untracked (concurrent work, not committed): {len(report.dirty)}"])
    for entry in report.dirty:
        suffix = "  (project)" if entry["init"] else ""
        blob = entry["worktree_blob"] or "-"
        lines.append(f"  {entry['status']} {entry['path']}  worktree {blob}{suffix}")
    lines.extend(["", f"Renames: {len(report.renames)}"])
    for entry in report.renames:
        lines.append(
            f"  {entry['old']} -> {entry['new']}  ({entry['similarity']}, {entry['where']})",
        )
    folders = report.folders()
    lines.extend(["", f"Folders touched: {', '.join(folders) if folders else 'none'}"])
    return "\n".join(lines)


def _run_scope(args: argparse.Namespace) -> int:
    """Print the changed package files since ``--since``."""
    report = build_scope(args.root.resolve(), args.since)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(_render_scope(report))
    return 0


# ---------------------------------------------------------------------------
# reconcile


@dataclass(frozen=True)
class PlanItem:
    """One checkbox item parsed back from a plan."""

    label: str
    ticked: bool
    status: str
    artifacts: tuple[str, ...]


def parse_plan(text: str) -> list[PlanItem]:
    """Parse every checkbox item and its indented fields from a plan."""
    items: list[PlanItem] = []
    current: dict[str, object] | None = None

    def flush() -> None:
        if current is not None:
            items.append(PlanItem(**current))  # type: ignore[arg-type]

    for line in text.splitlines():
        item = _ITEM_LINE.match(line)
        if item:
            flush()
            current = {
                "label": item["label"],
                "ticked": item["mark"] != " ",
                "status": "",
                "artifacts": (),
            }
            continue
        entry = _FIELD_LINE.match(line)
        if current is not None and entry:
            key, value = entry["key"].strip(), entry["value"].strip()
            if key == "Status":
                current["status"] = value
            elif key == "Artifacts":
                current["artifacts"] = tuple(
                    name.strip() for name in value.split(",") if name.strip()
                )
            continue
        if current is not None and line.strip() and not line.startswith("    "):
            flush()
            current = None
    flush()
    return items


def _status_word(status: str) -> str:
    """Return the first word of a status value, lower-cased."""
    return status.split()[0].lower() if status.split() else ""


def _required_artifacts(item: PlanItem) -> tuple[str, ...]:
    """Return the artifacts an item's status says must already exist."""
    word = _status_word(item.status)
    if word == "closed" or not item.artifacts:
        return ()
    if not item.ticked and (not word or word in _NO_ARTIFACT_STATUSES):
        return ()
    if not item.ticked and word == "reviewing":
        return item.artifacts[:1]
    return item.artifacts


def _content_at(root: Path, path: str, revision: str | None) -> str | None:
    """Return ``path`` at ``revision``, or at the last commit that still held it."""
    candidates = [revision] if revision else []
    candidates.append("HEAD")
    last = _git(root, "rev-list", "-1", "HEAD", "--", path).strip()
    if last:
        candidates.extend([f"{last}^", last])
    for candidate in candidates:
        try:
            return _git(root, "show", f"{candidate}:{path}")
        except ValueError:
            continue
    return None


def _similarity(old: str, new: str) -> float:
    """Return the line-level similarity ratio of two texts."""
    matcher = difflib.SequenceMatcher(None, old.splitlines(), new.splitlines(), autojunk=False)
    return matcher.ratio()


@dataclass
class ReconcileReport:
    """Every disagreement between a plan and the current tree."""

    added: list[str] = field(default_factory=list)
    gone: list[str] = field(default_factory=list)
    renamed: list[tuple[str, str, float]] = field(default_factory=list)
    folders_added: list[str] = field(default_factory=list)
    folders_gone: list[str] = field(default_factory=list)
    missing_artifacts: list[tuple[str, str]] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        """Return whether nothing disagrees."""
        return not any(
            (
                self.added,
                self.gone,
                self.renamed,
                self.folders_added,
                self.folders_gone,
                self.missing_artifacts,
            ),
        )


def build_reconcile(root: Path, plan_path: Path) -> ReconcileReport:
    """Compare a plan with the current inventory and the artifacts beside it."""
    text = plan_path.read_text(encoding="utf-8")
    items = [item for item in parse_plan(text) if _status_word(item.status) != "closed"]
    tracked = _tracked_python(root)
    untracked = _untracked_python(root)
    inventory = {
        _package_relative(path): label
        for paths, label in ((tracked, "tracked"), (untracked, "untracked"))
        for path in paths
        if not _is_init(path)
    }
    planned_files = {item.label for item in items if item.label.endswith(".py")}
    planned_folders = {
        item.label.removesuffix("/ integration")
        for item in items
        if item.label.endswith("/ integration")
    }
    report = ReconcileReport()
    added = sorted(path for path in inventory if path not in planned_files)
    gone = sorted(path for path in planned_files if path not in inventory)
    baseline = _CYCLE_BASELINE_LINE.search(text)
    revision = baseline["rev"] if baseline else None
    for old in gone:
        old_text = _content_at(root, f"{PACKAGE_DIR}/{old}", revision)
        best: tuple[float, str] | None = None
        if old_text is not None:
            for new in added:
                new_text = (root / PACKAGE_DIR / new).read_text(encoding="utf-8")
                ratio = _similarity(old_text, new_text)
                if ratio >= RENAME_SIMILARITY and (best is None or ratio > best[0]):
                    best = (ratio, new)
        if best is None:
            report.gone.append(old)
        else:
            report.renamed.append((old, best[1], best[0]))
            added.remove(best[1])
    report.added = [f"{path} ({inventory[path]})" for path in added]
    folders = set(_package_folders([*tracked, *untracked]))
    report.folders_added = sorted(folders - planned_folders)
    report.folders_gone = sorted(planned_folders - folders)
    for item in items:
        for name in _required_artifacts(item):
            if not (plan_path.parent / name).is_file():
                report.missing_artifacts.append((item.label, name))
    return report


def _render_reconcile(report: ReconcileReport, plan_path: Path) -> str:
    """Render the reconcile report as plain text."""
    if report.clean:
        return f"{plan_path.as_posix()}: plan matches the inventory; no artifact missing."
    sections = (
        ("Files without an item", report.added),
        ("Items whose file is gone", report.gone),
        (
            "Items whose file was renamed",
            [f"{old} -> {new} (similarity {ratio:.2f})" for old, new, ratio in report.renamed],
        ),
        ("Folders without an integration item", [f"{name}/" for name in report.folders_added]),
        ("Folder items whose folder is gone", [f"{name}/" for name in report.folders_gone]),
        (
            "Items missing artifacts on disk",
            [f"{label}: {name}" for label, name in report.missing_artifacts],
        ),
    )
    lines = [f"{plan_path.as_posix()}: plan disagrees with the tree."]
    for heading, rows in sections:
        if rows:
            lines.extend(["", f"{heading}: {len(rows)}", *(f"  {row}" for row in rows)])
    return "\n".join(lines)


def _run_reconcile(args: argparse.Namespace) -> int:
    """Print plan drift; exit 1 when anything is off."""
    root = args.root.resolve()
    plan_path = _dry._resolve_path(args.plan, root)
    if not plan_path.is_file():
        raise ValueError(f"--plan is not a file: {plan_path.as_posix()}")
    report = build_reconcile(root, plan_path)
    print(_render_reconcile(report, _dry._display_path(plan_path, root)))
    return 0 if report.clean else 1


# ---------------------------------------------------------------------------
# CLI


def _build_parser() -> argparse.ArgumentParser:
    """Build the three-subcommand parser."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="repository root (default: the checkout holding this script)",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    plan = commands.add_parser("plan", help="write docs/review/review-<release>.md")
    plan.add_argument("--mode", choices=MODES, default="autonomous")
    plan.add_argument(
        "--scope",
        action="append",
        default=[],
        help="package folder or module to work this run (repeatable; default: package)",
    )
    plan.add_argument("--target-release", help="release to plan (default: package __version__)")
    plan.add_argument(
        "--output",
        type=Path,
        help="plan path (default: docs/review/review-<rel>.md)",
    )
    plan.add_argument("--generated-date", help="ISO date for the Run: id (default: today)")
    plan.add_argument("--force", action="store_true", help="replace an existing plan")

    scope = commands.add_parser("scope", help="print changed package .py files since a revision")
    scope.add_argument("--since", help="base revision (default: latest tag reachable from HEAD)")
    scope.add_argument("--json", action="store_true", help="emit JSON")

    reconcile = commands.add_parser("reconcile", help="compare a plan with the inventory")
    reconcile.add_argument("--plan", type=Path, required=True, help="plan to compare")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the selected subcommand and return a process exit code."""
    args = _build_parser().parse_args(sys.argv[1:] if argv is None else argv)
    runners = {"plan": _run_plan, "scope": _run_scope, "reconcile": _run_reconcile}
    try:
        return runners[args.command](args)
    except (
        FileExistsError,
        OSError,
        UnicodeError,
        ValueError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
