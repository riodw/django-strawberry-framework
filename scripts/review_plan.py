"""Generate, scope and reconcile the REVIEW flow's per-release plan.

``docs/review/REVIEW.md`` is the method; this script owns only the plan's
shape and the inventory arithmetic Worker-0 would otherwise do by hand. It is
pure git plus filesystem: nothing is imported from the package and no Django
settings are loaded.

``plan``
    Write ``docs/review/review-<release>.md`` (``0.0.15`` becomes
    ``review-0_0_15.md``; the release is read from the package
    ``__version__`` unless ``--target-release`` names it). The inventory is
    ``git ls-files 'django_strawberry_framework/*.py'`` minus every
    ``__init__.py``: one file item per module, one folder integration item per
    package folder (carrying that folder's ``__init__.py`` on its
    ``Init files:`` line), the project integration item (carrying the
    package-root ``__init__.py``, public exports and the cross-folder
    lifecycle), and the final gate. ``--scope`` (repeatable; a package folder,
    module or ``__init__.py``, repo- or package-relative) limits the run: a
    folder covers its modules, its subfolders and their folder items; a
    folder's ``__init__.py`` selects that folder's item; the project item is in
    scope only for the whole package or the package-root ``__init__.py``. Every
    item outside the scope is listed under ``## Out of scope this run`` so an
    unticked box never reads as examined. A scope entry that matches no
    inventory file fails the run. An existing plan is resumed, never replaced:
    ``plan`` refuses it and names ``resume``; ``--force`` replaces it only
    while ``## Owned changes`` and ``## Outcomes`` still hold nothing beyond
    the generated text, and carries its run ids forward. ``--changed``
    replaces ``--scope`` with the release's own changes: every module whose
    committed content changed between ``--since`` (default: the latest tag
    reachable from ``HEAD``) and ``HEAD``, the folder integration item of the
    folder each such module sits in, the folder item of a changed folder
    ``__init__.py`` and the project item for a changed package-root
    ``__init__.py``. Dirty and untracked paths are concurrent work, never
    scope; the plan's ``## Cycle baseline`` records them. The ``Scope:`` line
    reads ``changed since <rev> (<sha>)``. When nothing changed the plan is
    written with ``Status: complete``, a ``Nothing in scope:`` line, every
    item out of scope and no final gate.

``resume``
    Append one run to an existing plan and nothing else: a
    ``## Run <release> <date>-<n>`` heading numbered after the highest recorded
    run, its ``Scope:`` line, a ``Drift:`` line when ``HEAD`` moved past the
    last recorded one or ``git status --short`` names a path neither the
    ``## Cycle baseline`` block nor an earlier ``Drift:`` line records (the
    plan's own directory and ``## Owned changes`` paths excluded), the
    already-itemized items this run works, and a new pending item for every
    in-scope file, folder or project item the plan lacks. ``--changed``
    recomputes that scope as ``plan`` does; an empty one appends a
    ``Nothing in scope:`` line and no item. Every existing byte stays in
    place; the file is opened for append only.

``scope``
    Print the package ``.py`` files changed between ``--since`` (default: the
    latest tag reachable from ``HEAD``) and the working tree, in three groups:
    committed changes with their ``HEAD`` blob ids, dirty or untracked paths
    (concurrent work, with working-tree ``git hash-object`` ids), and renames.
    Every path names the plan item that covers it: a module its own file item,
    a folder's ``__init__.py`` that folder's integration item, the
    package-root ``__init__.py`` the project item. ``--json`` emits the same
    data machine-readably.

``reconcile --plan PATH``
    Read-only. Compare a plan's items with the current inventory and report
    tracked or untracked ``.py`` files without an item, items whose file is
    gone or renamed, folders without an item, ``__init__.py`` files missing
    from their owning item's ``Init files:`` line, listed on an item that does
    not own them, or listed but gone, and items whose status requires
    artifacts that are missing beside the plan. Exit 1 when anything is off,
    0 when clean.

Usage::

    uv run python scripts/review_plan.py plan [--scope PATH ... | --changed [--since REV]]
        [--mode MODE] [--target-release RELEASE] [--output PATH] [--force]
    uv run python scripts/review_plan.py resume [--plan PATH]
        [--scope PATH ... | --changed [--since REV]] [--target-release RELEASE]
    uv run python scripts/review_plan.py scope [--since REV] [--json]
    uv run python scripts/review_plan.py reconcile --plan docs/review/review-0_0_15.md
"""

from __future__ import annotations

import argparse
import ast
import difflib
import json
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

try:
    import _plan_common
except ModuleNotFoundError:  # imported as ``scripts.review_plan`` (repo root on path)
    from scripts import _plan_common

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = "django_strawberry_framework"
REVIEW_DIR = Path("docs/review")
AXES = ("performance", "mechanics", "comments")
MODES = ("autonomous", "pause-after-each-item")
RENAME_SIMILARITY = 0.5
RELEASE_PATTERN = _plan_common.RELEASE_PATTERN

_RUN_ID = re.compile(
    r"^(?:Run:|## Run) (?P<release>\S+) (?P<date>\d{4}-\d{2}-\d{2})-(?P<n>\d+)\s*$",
    re.MULTILINE,
)
_ITEM_LINE = re.compile(r"^- \[(?P<mark>[ xX])\] (?P<label>.+?)\s*$")
_FIELD_LINE = re.compile(r"^ {4}- (?P<key>[A-Za-z][A-Za-z ]*):(?P<value>.*)$")
_CYCLE_BASELINE_LINE = re.compile(r"CYCLE_BASELINE=(?P<rev>[0-9a-fA-F]{7,64})\b")
_NO_ARTIFACT_STATUSES = frozenset({"pending", "out-of-scope"})
_PLAN_TITLE = re.compile(r"^# REVIEW plan: (?P<release>\S+)\s*$", re.MULTILINE)
_DRIFT_LINE = re.compile(
    r"^Drift: \S+ HEAD (?P<old>\S+)\.\.(?P<new>[0-9a-fA-F]{7,64})\b"
    r"(?:.*?; dirty \+ (?P<paths>.*)|.*)$",
)
_INIT_ENTRY = re.compile(r"`(?P<path>[^`]*__init__\.py)`")
_STASH_SUBJECT = re.compile(r"^(?:WIP on|On) ")
PROJECT_LABEL = "Project integration"
FOLDER_SUFFIX = "/ integration"
INIT_FIELD = "Init files"
LEDGER_HEADING = "## Owned changes"
OUTCOMES_HEADING = "## Outcomes"


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
    main = _plan_common.artifact_name("rev", Path(relative))
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


def _init_owner(relative: str) -> str:
    """Return the label of the item covering a package-relative ``__init__.py``."""
    folder = relative.rpartition("/")[0]
    return f"{folder}{FOLDER_SUFFIX}" if folder else PROJECT_LABEL


def _covering_item(path: str) -> str:
    """Return the label of the plan item covering a repo-relative package ``.py`` path."""
    relative = _package_relative(path)
    return _init_owner(relative) if _is_init(relative) else relative


def _init_field(root: Path, relatives: Sequence[str]) -> str:
    """Render the ``Init files:`` line naming each ``__init__.py`` and its definitions."""
    entries = []
    for relative in relatives:
        names = _init_definitions(root, f"{PACKAGE_DIR}/{relative}")
        entry = f"`{relative}`"
        if names:
            entry += f" (defines {', '.join(f'`{name}`' for name in names)})"
        entries.append(entry)
    return f"{INIT_FIELD}: {', '.join(entries) if entries else 'none'}"


def _folder_item(root: Path, folder: str, inits: Sequence[str]) -> Item:
    """Build one folder integration item carrying the folder's own ``__init__.py``."""
    own = [relative for relative in inits if relative.rpartition("/")[0] == folder]
    return Item(
        kind="folder",
        key=folder,
        label=f"{folder}{FOLDER_SUFFIX}",
        artifacts=_artifact_set(folder),
        extra=(_init_field(root, own),),
    )


def _project_item(root: Path, inits: Sequence[str]) -> Item:
    """Build the project integration item carrying the package-root ``__init__.py``."""
    extra = (
        "Covers: package-root modules as one component; public exports; import-time cost vs "
        "`## Bench baseline`; end-to-end lifecycle across folders; the package-root "
        "`__init__.py` (each folder's `__init__.py` is on its folder item)",
        _init_field(root, [relative for relative in inits if "/" not in relative]),
    )
    return Item(
        kind="project",
        key="project",
        label=PROJECT_LABEL,
        artifacts=_artifact_set("project"),
        extra=extra,
    )


_GATE_ITEM = Item(
    kind="gate",
    key="gate",
    label="Final gate",
    artifacts=(),
    extra=(
        "Runs: `uv run python scripts/workspace.py gate review` (default, `FAKESHOP_SHARDED=1` "
        'and Postgres suites in a gate copy that keeps a git index, REVIEW.md "Final gate and '
        'closeout"), each w/ its own counts; every `## Pending execution` command from every '
        "artifact; the `## Bench baseline` commands at `<phase>` `gate`, delta recorded",
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


def _resolve_scope(entries: Sequence[str], paths: Sequence[str]) -> tuple[str, ...] | None:
    """Return the normalized scope, ``None`` for the whole package; fail closed."""
    if not entries:
        return None
    normalized = []
    for entry in entries:
        scope = _normalize_scope(entry)
        if not scope:
            return None
        if not any(_scope_matches(scope, relative) for relative in paths):
            raise ValueError(
                f"--scope {entry!r} matches no inventory file under {PACKAGE_DIR}/ (tracked .py)",
            )
        if scope not in normalized:
            normalized.append(scope)
    return tuple(normalized)


@dataclass(frozen=True)
class _Changed:
    """The ``--changed`` scope: the labels of the items covering committed changes."""

    since: str
    since_sha: str
    labels: frozenset[str]


@dataclass(frozen=True)
class _Inventory:
    """The tracked package inventory, its items in plan order, and one run's scope."""

    files: tuple[str, ...]
    inits: tuple[str, ...]
    folders: tuple[str, ...]
    scope: tuple[str, ...] | None
    ordered: tuple[Item, ...]
    changed: _Changed | None = None

    @property
    def nothing_in_scope(self) -> bool:
        """Return whether a ``--changed`` scope found no committed change."""
        return self.changed is not None and not self.changed.labels

    def in_scope(self, item: Item) -> bool:
        """Return whether the run's scope covers ``item``."""
        if item.kind == "gate":
            return not self.nothing_in_scope
        if self.changed is not None:
            return item.label in self.changed.labels
        if self.scope is None:
            return True
        if item.kind == "file":
            return any(_scope_matches(entry, item.key) for entry in self.scope)
        if item.kind == "folder":
            return any(
                _scope_matches(entry, item.key) or entry == f"{item.key}/__init__.py"
                for entry in self.scope
            )
        return "__init__.py" in self.scope

    @property
    def scope_label(self) -> str:
        """Render the ``Scope:`` value: folders end in ``/``, modules do not."""
        if self.changed is not None:
            return f"changed since {self.changed.since} ({self.changed.since_sha[:12]})"
        if self.scope is None:
            return "package"
        modules = {*self.files, *self.inits}
        return ", ".join(entry if entry in modules else f"{entry}/" for entry in self.scope)


def _changed_scope(root: Path, since: str | None, tracked: Iterable[str]) -> _Changed:
    """Return the labels of the items covering committed package changes since ``since``."""
    report = build_scope(root, since)
    present = set(tracked)
    paths = [str(entry["path"]) for entry in report.committed]
    paths.extend(str(entry["new"]) for entry in report.renames if entry["where"] == "committed")
    labels: set[str] = set()
    for path in paths:
        if path not in present:
            continue
        labels.add(_covering_item(path))
        folder = _package_relative(path).rpartition("/")[0]
        if folder and not _is_init(path):
            labels.add(f"{folder}{FOLDER_SUFFIX}")
    return _Changed(since=report.since, since_sha=report.since_sha, labels=frozenset(labels))


def _build_inventory(
    root: Path,
    scope_entries: Sequence[str],
    *,
    changed: bool = False,
    since: str | None = None,
) -> _Inventory:
    """Collect the tracked inventory, build every item and resolve the scope."""
    tracked = _tracked_python(root)
    files = tuple(_package_relative(path) for path in tracked if not _is_init(path))
    if not files:
        raise ValueError(f"no tracked non-__init__ .py files under {PACKAGE_DIR}/")
    inits = tuple(_package_relative(path) for path in tracked if _is_init(path))
    scope = _resolve_scope(scope_entries, (*files, *inits))
    folders = tuple(_package_folders(tracked))
    file_items = {
        relative: Item(
            kind="file",
            key=relative,
            label=relative,
            artifacts=_artifact_set(relative),
        )
        for relative in files
    }
    ordered: list[Item] = []

    def walk(folder: str) -> None:
        ordered.extend(file_items[r] for r in files if r.rpartition("/")[0] == folder)
        for child in folders:
            if child.rpartition("/")[0] == folder:
                walk(child)
        if folder:
            ordered.append(_folder_item(root, folder, inits))

    walk("")
    ordered.append(_project_item(root, inits))
    _assert_unique_artifacts(ordered)
    return _Inventory(
        files=files,
        inits=inits,
        folders=folders,
        scope=scope,
        ordered=tuple(ordered),
        changed=_changed_scope(root, since, tracked) if changed else None,
    )


def _run_max(text: str, release: str) -> int:
    """Return the highest run number ``text`` records for ``release``."""
    runs = [int(match["n"]) for match in _RUN_ID.finditer(text) if match["release"] == release]
    return max(runs, default=0)


def _existing_run_max(path: Path, release: str) -> int:
    """Return the highest run number an existing plan records for ``release``."""
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, IsADirectoryError):
        return 0
    return _run_max(text, release)


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


_BENCH_RUN = "uv run python scripts/workspace.py run review/bench/<phase>"
_BENCH_COMMANDS = (
    f"{_BENCH_RUN} -- python scripts/bench_plan_cache.py "
    "--json <scratch>/bench/<phase>/plan_cache.json",
    f"{_BENCH_RUN} -- python scripts/bench_optimizer_walk.py "
    "--json <scratch>/bench/<phase>/optimizer_walk.json",
    f"{_BENCH_RUN} --cell pg -- python scripts/bench_nested_fetch.py "
    "--json <scratch>/bench/<phase>/nested_fetch.json",
    f"{_BENCH_RUN} -- python scripts/importtime_report.py --rounds 5 "
    "--json <scratch>/bench/<phase>/importtime.json",
)


def _bench_baseline_block() -> list[str]:
    """Render the empty bench table Worker-0 fills at cycle entry and at the gate."""
    return [
        "## Bench baseline",
        "",
        "Each figure is bound by the package digest and instrument ids in its provenance",
        "header; `CYCLE_BASELINE` is recorded beside it, and each run's workspace run id",
        '(REVIEW.md "Workspace"). `<scratch>` is the absolute session scratchpad, `<phase>`',
        "either `baseline` or `gate`, each its own copy. The nested-fetch row runs in that",
        'copy\'s own Postgres database (REVIEW.md "Database cells").',
        "Worker-0 fills Baseline at cycle entry, Gate and Delta at the final gate.",
        "",
        "| Command | Baseline | Gate | Delta |",
        "|---|---|---|---|",
        *(f"| `{command}` | | | |" for command in _BENCH_COMMANDS),
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
    """Render the sections Worker-0 maintains: decisions, ledger, outcomes."""
    return [
        "## Decisions",
        "",
        "Maintainer decisions the run surfaced: ruff rules to enable, trade-offs, contracts "
        "nobody could cite.",
        "",
        LEDGER_HEADING,
        "",
        "One row per tracked edit or new file a verified item landed. A later item may build on a "
        "path",
        "listed here; any other dirty hunk is external.",
        "",
        "| Path | Item | Axis | Symbols changed |",
        "|---|---|---|---|",
        "",
        OUTCOMES_HEADING,
        "",
        "Filled by Worker-0 at closeout before any scratch is removed; a scoped run adds "
        '"Scope of this run".',
        "",
    ]


def _section_bodies(text: str) -> dict[str, list[str]]:
    """Return every ``## `` heading's non-blank body lines, repeated headings merged."""
    bodies: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = bodies.setdefault(line.rstrip(), [])
        elif current is not None and line.strip():
            current.append(line.rstrip())
    return bodies


def _recorded_closing_content(text: str) -> list[str]:
    """Return the ledger and outcomes headings holding more than the generated text."""
    generated = _section_bodies("\n".join(_closing_blocks()))
    existing = _section_bodies(text)
    return [
        heading
        for heading in (LEDGER_HEADING, OUTCOMES_HEADING)
        if any(line not in generated[heading] for line in existing.get(heading, ()))
    ]


def _in_scope_sections(inventory: _Inventory) -> list[tuple[str, list[Item]]]:
    """Group the in-scope items under their plan headings, in plan order."""
    sections: list[tuple[str, list[Item]]] = []
    for item in inventory.ordered:
        if item.kind == "project" or not inventory.in_scope(item):
            continue
        if item.kind == "file":
            folder = item.key.rpartition("/")[0]
            heading = f"{folder}/" if folder else "Package root"
            if sections and sections[-1][0] == heading:
                sections[-1][1].append(item)
                continue
        else:
            heading = item.label
        sections.append((heading, [item]))
    project = inventory.ordered[-1]
    gate = [_GATE_ITEM] if inventory.in_scope(_GATE_ITEM) else []
    if inventory.in_scope(project):
        sections.append(("Project", [project, *gate]))
    elif gate:
        sections.append(("Final gate", gate))
    return sections


def _nothing_in_scope_lines(inventory: _Inventory) -> list[str]:
    """Return the ``Nothing in scope:`` line of an empty ``--changed`` run, else nothing."""
    if not inventory.nothing_in_scope or inventory.changed is None:
        return []
    return [
        f"Nothing in scope: no committed package .py change since {inventory.changed.since}; "
        "the run stops.",
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
    changed: bool = False,
    since: str | None = None,
) -> tuple[str, dict[str, int]]:
    """Render the plan text and its item counts."""
    inventory = _build_inventory(root, scope_entries, changed=changed, since=since)
    sections = _in_scope_sections(inventory)
    in_scope = {id(item) for _, members in sections for item in members}
    out_of_scope = [item for item in inventory.ordered if id(item) not in in_scope]

    lines = [
        f"# REVIEW plan: {release}",
        "",
        f"Status: {'complete' if inventory.nothing_in_scope else 'planned'}",
        f"Mode: {mode}",
        f"Run: {release} {generated_date}-{run_number}",
        f"Scope: {inventory.scope_label}",
        *_nothing_in_scope_lines(inventory),
        "",
        "Method: `docs/review/REVIEW.md`. Fresh source review; findings from prior build, review, "
        "DRY or",
        "hunt artifacts are not imported.",
        "",
        *_plan_common.cycle_baseline_block(status_output),
        "",
        "CYCLE_BASELINE=<Worker-0 fills: `git stash create`, empty -> the `git rev-parse HEAD` sha>",
        f"Untracked under {PACKAGE_DIR}/: <Worker-0 fills>",
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
                f"Not examined under `Scope: {inventory.scope_label}`; an unticked box here "
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
        "file": sum(
            1 for item in inventory.ordered if item.kind == "file" and id(item) in in_scope
        ),
        "folder": sum(
            1 for item in inventory.ordered if item.kind == "folder" and id(item) in in_scope
        ),
        "out_of_scope": len(out_of_scope),
        "nothing": int(inventory.nothing_in_scope),
    }
    return "\n".join(lines), counts


def _default_output(release: str) -> Path:
    """Return ``docs/review/review-<release-underscored>.md``."""
    return REVIEW_DIR / f"review-{release.replace('.', '_')}.md"


def _validated_release(value: str) -> str:
    """Return ``value`` when it is a dotted-digit release, else fail."""
    if not RELEASE_PATTERN.fullmatch(value):
        raise ValueError(
            f"invalid --target-release {value!r}; expected dotted digits such as 0.0.15",
        )
    return value


def _check_since(args: argparse.Namespace) -> None:
    """Refuse ``--since`` without ``--changed``, which alone reads it."""
    if args.since is not None and not args.changed:
        raise ValueError("--since applies only with --changed")


def _run_plan(args: argparse.Namespace) -> int:
    """Write a fresh plan; an existing one is resumed, and replaced only while unworked."""
    _check_since(args)
    root = args.root.resolve()
    release = _validated_release(
        args.target_release or _plan_common.package_version(root / PACKAGE_DIR),
    )
    output = _plan_common.resolve_path(args.output or _default_output(release), root)
    shown = _plan_common.display_path(output, root).as_posix()
    if output.exists():
        if not args.force:
            raise FileExistsError(
                f"plan already exists: {shown}; a plan is resumed, never replaced: run "
                f"`review_plan.py resume --plan {shown}` to add a run to it",
            )
        held = _recorded_closing_content(output.read_text(encoding="utf-8"))
        if held:
            raise ValueError(
                f"refusing --force: {shown} records content under {' and '.join(held)}; run "
                f"`review_plan.py resume --plan {shown}` to add a run instead",
            )
    content, counts = _render_plan(
        root,
        release=release,
        run_number=_existing_run_max(output, release) + 1,
        generated_date=_plan_common.validate_date(args.generated_date),
        mode=args.mode,
        scope_entries=args.scope,
        status_output=_plan_common.git_status_short(root),
        changed=args.changed,
        since=args.since,
    )
    _plan_common.atomic_write(output, content, force=args.force)
    print(
        f"Wrote {shown} ({counts['file']} file item(s), {counts['folder']} folder item(s) in "
        f"scope, {counts['out_of_scope']} out of scope"
        f"{'; nothing in scope' if counts['nothing'] else ''})",
    )
    return 0


# ---------------------------------------------------------------------------
# resume


def _status_paths(line: str) -> list[str]:
    """Return the path, or both rename paths, of one ``git status --short`` line."""
    body = line[3:].strip() if len(line) > 3 else ""
    return [part.strip().strip('"') for part in body.split(" -> ") if part.strip()]


def _split_paths(text: str) -> list[str]:
    """Split a comma- or space-separated path list, dropping backticks."""
    return [token.strip("`") for token in re.split(r"[,\s]+", text) if token.strip("`")]


def _recorded_dirty(text: str) -> set[str]:
    """Return every path the cycle baseline block or a ``Drift:`` line already records."""
    paths: set[str] = set()
    in_baseline = in_fence = in_drift = False
    untracked_prefix = f"Untracked under {PACKAGE_DIR}/:"
    for line in text.splitlines():
        if line.startswith("## "):
            in_baseline, in_fence, in_drift = line.rstrip() == "## Cycle baseline", False, False
            continue
        if in_drift and line.startswith("  ") and not line.startswith("    ") and line.strip():
            paths.update(_split_paths(line))
            continue
        in_drift = False
        drift = _DRIFT_LINE.match(line)
        if drift:
            in_drift = True
            if drift["paths"]:
                paths.update(_split_paths(drift["paths"]))
            continue
        if not in_baseline:
            continue
        if line.startswith("```"):
            in_fence = not in_fence
        elif in_fence:
            paths.update(_status_paths(line))
        elif line.startswith(untracked_prefix):
            paths.update(_split_paths(line.removeprefix(untracked_prefix)))
    return paths


def _ledger_paths(text: str) -> set[str]:
    """Return the ``Path`` cell of every ``## Owned changes`` row."""
    paths = set()
    for row in _section_bodies(text).get(LEDGER_HEADING, []):
        if not row.startswith("|"):
            continue
        cell = row.strip().strip("|").split("|")[0].strip().strip("`")
        if cell and cell != "Path" and not set(cell) <= {"-", ":"}:
            paths.add(cell)
    return paths


def _recorded_head(root: Path, text: str) -> str | None:
    """Return the ``HEAD`` the plan last recorded: latest ``Drift:``, else ``CYCLE_BASELINE``."""
    drifts = [match["new"] for line in text.splitlines() if (match := _DRIFT_LINE.match(line))]
    if drifts:
        return drifts[-1]
    baseline = _CYCLE_BASELINE_LINE.search(text)
    if baseline is None:
        return None
    rev = baseline["rev"]
    try:
        commits = _git(root, "rev-list", "--parents", "-n", "1", rev).split()
        subject = _git(root, "log", "-1", "--format=%s", rev).strip()
    except ValueError:
        return rev
    if len(commits) >= 3 and _STASH_SUBJECT.match(subject):
        return commits[1]
    return commits[0] if commits else rev


def _drift_line(
    root: Path,
    text: str,
    date: str,
    plan_dir: Path,
) -> str | None:
    """Return the ``Drift:`` line for this run, or ``None`` when nothing moved."""
    head = _git(root, "rev-parse", "HEAD").strip()
    old = _recorded_head(root, text)
    moved = True
    if old is not None:
        try:
            moved = _git(root, "rev-parse", "--verify", f"{old}^{{commit}}").strip() != head
        except ValueError:
            moved = True
    excluded = _ledger_paths(text) | _recorded_dirty(text)
    shown_dir = _plan_common.display_path(plan_dir, root)
    own_prefix = None if shown_dir.is_absolute() else f"{shown_dir.as_posix().rstrip('/')}/"
    fresh: list[str] = []
    for line in (_plan_common.git_status_short(root) or "").splitlines():
        for path in _status_paths(line):
            if path in excluded or path in fresh:
                continue
            if own_prefix is not None and f"{path.rstrip('/')}/".startswith(own_prefix):
                continue
            fresh.append(path)
    if not moved and not fresh:
        return None
    line = f"Drift: {date} HEAD {old[:12] if old else 'unrecorded'}..{head[:12]}"
    if fresh:
        line += f"; dirty + {', '.join(fresh)}"
    return line


def _render_resume(
    root: Path,
    text: str,
    *,
    release: str,
    run_number: int,
    generated_date: str,
    scope_entries: Sequence[str],
    plan_dir: Path,
    changed: bool = False,
    since: str | None = None,
) -> tuple[str, dict[str, int]]:
    """Render the lines one resumed run appends, and their counts."""
    inventory = _build_inventory(root, scope_entries, changed=changed, since=since)
    itemized = {item.label for item in parse_plan(text) if _status_word(item.status) != "closed"}
    in_scope = [item for item in (*inventory.ordered, _GATE_ITEM) if inventory.in_scope(item)]
    carried = [item.label for item in in_scope if item.label in itemized]
    added = [item for item in in_scope if item.label not in itemized]
    drift = _drift_line(root, text, generated_date, plan_dir)
    lines = [
        f"## Run {release} {generated_date}-{run_number}",
        "",
        f"Scope: {inventory.scope_label}",
        *([drift] if drift else []),
        *_nothing_in_scope_lines(inventory),
    ]
    if carried:
        lines.extend(
            [
                "",
                "Already itemized above, worked this run:",
                "",
                *(f"- `{label}`" for label in carried),
            ],
        )
    if added:
        lines.extend(["", "New items this run:", ""])
        for item in added:
            lines.extend(item.render("pending"))
    lead = "" if text.endswith("\n\n") else "\n" if text.endswith("\n") else "\n\n"
    counts = {
        "added": len(added),
        "carried": len(carried),
        "drift": int(drift is not None),
        "nothing": int(inventory.nothing_in_scope),
    }
    return lead + "\n".join(lines) + "\n", counts


def _run_resume(args: argparse.Namespace) -> int:
    """Append one run to an existing plan without touching a byte already in it."""
    _check_since(args)
    root = args.root.resolve()
    wanted = _validated_release(args.target_release) if args.target_release else None
    if args.plan is not None:
        plan_path = _plan_common.resolve_path(args.plan, root)
    else:
        release = wanted or _plan_common.package_version(root / PACKAGE_DIR)
        plan_path = _plan_common.resolve_path(_default_output(release), root)
    shown = _plan_common.display_path(plan_path, root).as_posix()
    if not plan_path.is_file():
        raise ValueError(f"no plan at {shown}; run `review_plan.py plan` to write one")
    text = plan_path.read_bytes().decode("utf-8")
    title = _PLAN_TITLE.search(text)
    if title is None:
        raise ValueError(f"{shown} has no `# REVIEW plan: <release>` title")
    release = title["release"]
    if wanted is not None and wanted != release:
        raise ValueError(f"{shown} plans release {release}, not --target-release {wanted}")
    run_number = _run_max(text, release) + 1
    generated_date = _plan_common.validate_date(args.generated_date)
    addition, counts = _render_resume(
        root,
        text,
        release=release,
        run_number=run_number,
        generated_date=generated_date,
        scope_entries=args.scope,
        plan_dir=plan_path.parent,
        changed=args.changed,
        since=args.since,
    )
    with plan_path.open("ab") as stream:
        stream.write(addition.encode("utf-8"))
    print(
        f"Appended run {release} {generated_date}-{run_number} to {shown} "
        f"({counts['added']} new item(s), {counts['carried']} already itemized, "
        f"{'drift recorded' if counts['drift'] else 'no drift'}"
        f"{'; nothing in scope' if counts['nothing'] else ''})",
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
                    "item": _covering_item(target),
                },
            )
            continue
        report.committed.append(
            {
                "status": code,
                "path": path,
                "blob": head_blobs.get(path),
                "init": _is_init(path),
                "item": _covering_item(path),
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
                    "item": _covering_item(path),
                },
            )
        report.dirty.append(
            {
                "status": code,
                "path": path,
                "worktree_blob": worktree.get(path),
                "init": _is_init(path),
                "item": _covering_item(path),
            },
        )
    return report


def _render_scope(report: ScopeReport) -> str:
    """Render the scope report as plain text."""
    lines = [
        f"Package .py changes since {report.since} ({report.since_sha[:12]}) to HEAD "
        f"{report.head_sha[:12]}, plus the working tree.",
        "A folder's `__init__.py` belongs to that folder's integration item, the package-root "
        "`__init__.py` to the project integration item.",
        "",
        f"Committed ({report.since}..HEAD): {len(report.committed)}",
    ]
    for entry in report.committed:
        notes = [str(entry["item"])] if entry["init"] else []
        if entry["also_dirty"]:
            notes.append("also dirty")
        suffix = f"  ({', '.join(notes)})" if notes else ""
        blob = entry["blob"] or "-"
        lines.append(f"  {entry['status']:<2} {entry['path']}  HEAD {blob}{suffix}")
    lines.extend(["", f"Dirty or untracked (concurrent work, not committed): {len(report.dirty)}"])
    for entry in report.dirty:
        suffix = f"  ({entry['item']})" if entry["init"] else ""
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
    inits: tuple[str, ...] = ()


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
                "inits": (),
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
            elif key == INIT_FIELD:
                current["inits"] = tuple(match["path"] for match in _INIT_ENTRY.finditer(value))
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
    inits_unlisted: list[tuple[str, str]] = field(default_factory=list)
    inits_misplaced: list[tuple[str, str, str]] = field(default_factory=list)
    inits_gone: list[tuple[str, str]] = field(default_factory=list)
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
                self.inits_unlisted,
                self.inits_misplaced,
                self.inits_gone,
                self.missing_artifacts,
            ),
        )


def _reconcile_inits(
    report: ReconcileReport,
    items: Sequence[PlanItem],
    paths: Sequence[str],
) -> None:
    """Record every ``__init__.py`` whose ``Init files:`` listing disagrees with the tree."""
    actual = {_package_relative(path) for path in paths if _is_init(path)}
    listed: dict[str, list[str]] = {}
    for item in items:
        for init in item.inits:
            listed.setdefault(init, []).append(item.label)
    new_folders = {f"{folder}{FOLDER_SUFFIX}" for folder in report.folders_added}
    for init in sorted(actual):
        owner = _init_owner(init)
        on = listed.get(init, [])
        if owner not in on and owner not in new_folders:
            report.inits_unlisted.append((init, owner))
        report.inits_misplaced.extend((init, label, owner) for label in on if label != owner)
    for init in sorted(set(listed) - actual):
        report.inits_gone.extend((label, init) for label in listed[init])


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
        item.label.removesuffix(FOLDER_SUFFIX)
        for item in items
        if item.label.endswith(FOLDER_SUFFIX)
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
    _reconcile_inits(report, items, [*tracked, *untracked])
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
            "`__init__.py` files missing from their item's Init files line",
            [f"{init}: {owner}" for init, owner in report.inits_unlisted],
        ),
        (
            "`__init__.py` files listed on an item that does not own them",
            [
                f"{init}: listed on {on}, owned by {owner}"
                for init, on, owner in report.inits_misplaced
            ],
        ),
        (
            "Items listing an `__init__.py` that is gone",
            [f"{label}: {init}" for label, init in report.inits_gone],
        ),
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
    plan_path = _plan_common.resolve_path(args.plan, root)
    if not plan_path.is_file():
        raise ValueError(f"--plan is not a file: {plan_path.as_posix()}")
    report = build_reconcile(root, plan_path)
    print(_render_reconcile(report, _plan_common.display_path(plan_path, root)))
    return 0 if report.clean else 1


# ---------------------------------------------------------------------------
# CLI


def _add_scope_arguments(parser: argparse.ArgumentParser, scope_help: str) -> None:
    """Add the mutually exclusive ``--scope`` / ``--changed`` pair and ``--since``."""
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--scope",
        action="append",
        default=[],
        help=f"{scope_help} (repeatable; default: package)",
    )
    group.add_argument(
        "--changed",
        action="store_true",
        help="work the items covering committed package changes since --since",
    )
    parser.add_argument(
        "--since",
        help="base revision for --changed (default: latest tag reachable from HEAD)",
    )


def _build_parser() -> argparse.ArgumentParser:
    """Build the ``plan`` / ``resume`` / ``scope`` / ``reconcile`` parser."""
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
    _add_scope_arguments(plan, "package folder or module to work this run")
    plan.add_argument("--target-release", help="release to plan (default: package __version__)")
    plan.add_argument(
        "--output",
        type=Path,
        help="plan path (default: docs/review/review-<rel>.md)",
    )
    plan.add_argument("--generated-date", help="ISO date for the Run: id (default: today)")
    plan.add_argument(
        "--force",
        action="store_true",
        help="replace an existing plan whose ledger and outcomes are still empty",
    )

    resume = commands.add_parser("resume", help="append one run to an existing plan")
    resume.add_argument(
        "--plan",
        type=Path,
        help="plan to resume (default: docs/review/review-<rel>.md)",
    )
    _add_scope_arguments(resume, "package folder or module this run works")
    resume.add_argument("--target-release", help="release the plan must be for")
    resume.add_argument("--generated-date", help="ISO date for the run id (default: today)")

    scope = commands.add_parser("scope", help="print changed package .py files since a revision")
    scope.add_argument("--since", help="base revision (default: latest tag reachable from HEAD)")
    scope.add_argument("--json", action="store_true", help="emit JSON")

    reconcile = commands.add_parser("reconcile", help="compare a plan with the inventory")
    reconcile.add_argument("--plan", type=Path, required=True, help="plan to compare")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the selected subcommand and return a process exit code."""
    args = _build_parser().parse_args(sys.argv[1:] if argv is None else argv)
    runners = {
        "plan": _run_plan,
        "resume": _run_resume,
        "scope": _run_scope,
        "reconcile": _run_reconcile,
    }
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
