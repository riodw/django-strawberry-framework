"""Generate per-file stripped diffs between a commit and HEAD.

For every Python file changed between ``<commit-hash>`` and HEAD whose path
passes the inclusion rule (see below), the script

1. Renders the OLD revision (``commit:old_path``) through ``review_inspect``
   into ``old/`` with a stable ``a__b__c`` stem. For a rename the old side is
   the pre-rename path, so a move reads as an edit instead of "+entire file".
2. Renders the NEW revision into ``new/``. By default (``--against head``) the
   new side is read from ``HEAD:<path>`` so both sides are what they claim;
   ``--against worktree`` reads the working copy instead (uncommitted and
   untracked files included) and every diff it writes opens with a header line
   saying so.
3. Writes a unified diff of the two stripped files to ``diff/``.

Output location: with ``--output-dir PATH`` the three folders are written
under ``PATH/{old,new,diff}/``; each run is rendered into a staging directory
inside ``PATH`` and each folder is then published as one complete replacement
(the snapshot helper's publish-with-rollback), so a failed run leaves the
previous output intact and parallel runs with distinct ``PATH`` values never
touch each other. Nothing else under ``PATH`` is touched. Without
``--output-dir`` the script clears and rewrites ``docs/shadow/{old,new,diff}/``
at the repo root, the folders this script owns under ``docs/shadow/``.

The shared git / ``review_inspect`` plumbing -- ``_run_git``,
``_validate_commit``, ``_stem_for``, ``_file_at_commit``, ``_inspect_quiet``,
the temp-tree ``_materialize_and_inspect`` primitive and
``_publish_staged_snapshot`` -- lives in
``review_historical_package_snapshot_at_commit`` (the canonical home for the
shared review machinery) and is imported here. This module adds the changed-file
enumeration, the new-side selection, the diff writers and the list mode. Added
or deleted files get an empty stripped file on the missing side so the per-file
diff still renders.

Inclusion rule: a ``.py`` path whose name is not ``__init__.py`` and which does
not contain ``test``. ``--include-init`` admits ``__init__.py`` files (they carry
the public surface) and ``--include-tests`` admits paths containing ``test``
(which also covers package source such as ``django_strawberry_framework/testing/``).
A rename is judged by its new path, a deletion by its old path.

Diff lens options (all default off, so the default output is unchanged):

- ``--keep-literals`` keeps string literals and f-string bodies in the stripped
  files, so relation names, ``only()`` fields and ``__all__`` edits show.
  Comments and docstrings are still removed.
- ``--collapse-blank`` drops blank lines before diffing, so blanked docstrings
  and comments stop producing blank-only hunks. Hunk line numbers then count
  non-blank lines only.
- ``--prose`` additionally writes ``diff/<stem>.prose.diff`` per file: every
  change region whose code (comments stripped, docstrings blanked) is identical
  on both sides, as raw old vs new source lines, each hunk headed by its
  enclosing ``path::QualifiedName``. Regions that change code and prose together
  are in the code diff, not here.

List mode: ``--list`` prints only the changed-file inventory -- status (``M``,
``A``, ``D``, ``R old -> new``), the HEAD blob id, and a separate group of paths
that are dirty or untracked in the working tree -- and writes nothing.
``--json`` prints the same data as JSON. The base defaults to the latest tag
reachable from HEAD when neither ``<commit-hash>`` nor ``--since`` is given.

Usage:
    uv run python scripts/review_changed_python_diffs_against_head.py <commit-hash> [--path PATHSPEC ...]
        [--output-dir PATH] [--against head|worktree] [--include-tests] [--include-init]
        [--keep-literals] [--collapse-blank] [--prose]
    uv run python scripts/review_changed_python_diffs_against_head.py --list [--json] [--since REV]

The ``uv run`` prefix is required so the script sees the project's virtual
environment (it transitively imports ``review_inspect``, which depends on the
project's pinned Python / dependency versions). Run from anywhere inside the
repository; git paths are resolved from ``git rev-parse --show-toplevel``.

``--path`` (repeatable) scopes the diff to one or more git pathspecs so a
focused review does not have to wade through every changed file -- e.g.
``--path django_strawberry_framework/filters`` restricts the run to that
subtree. Each pathspec narrows the set; with none supplied the default is the
whole repository (every changed ``*.py``). The inclusion rule still applies on
top of the scope. Rename detection pairs only paths inside the scope, so a file
moved into the scope from outside it reads as added.

This diff lens is best for reviewing EDITS to code that already existed at
``<commit-hash>``. For a subsystem largely BORN after that commit the old side
is near-empty and every file reads as "+entire file"; reach for
``review_historical_package_snapshot_at_commit`` (a full stripped snapshot)
instead.

Example:
    uv run python scripts/review_changed_python_diffs_against_head.py \
        1e6b5830766545d3cb46e3aff21c6dd58a935da4 \
        --path django_strawberry_framework/filters \
        --output-dir /tmp/review-diff
"""

from __future__ import annotations

import argparse
import ast
import difflib
import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

if __package__:
    from scripts.review_historical_package_snapshot_at_commit import (
        _clear_shadow_output,
        _file_at_commit,
        _inspect_quiet,
        _materialize_and_inspect,
        _publish_staged_snapshot,
        _run_git,
        _stem_for,
        _validate_commit,
    )
    from scripts.review_inspect import _remove_docstring_statements, _strip_comments
else:
    from review_historical_package_snapshot_at_commit import (
        _clear_shadow_output,
        _file_at_commit,
        _inspect_quiet,
        _materialize_and_inspect,
        _publish_staged_snapshot,
        _run_git,
        _stem_for,
        _validate_commit,
    )
    from review_inspect import _remove_docstring_statements, _strip_comments

OUTPUT_OLD = Path("docs/shadow/old")
OUTPUT_NEW = Path("docs/shadow/new")
OUTPUT_DIFF = Path("docs/shadow/diff")
WORKTREE_HEADER = "# new side: working tree (uncommitted and untracked files included), not HEAD\n"


@dataclass(frozen=True)
class _Change:
    """One changed path: ``status`` is ``M``/``A``/``D``/``R`` (or a porcelain ``XY``)."""

    status: str
    path: str
    old_path: str | None = None

    @property
    def old_side_path(self) -> str:
        """Return the path the OLD side is read from (the pre-rename path for ``R``)."""
        return self.old_path or self.path


@dataclass(frozen=True)
class _SideDirs:
    """The three output folders plus the base their diff labels are relative to."""

    old: Path
    new: Path
    diff: Path
    label_base: Path


def _eligible(path: str, *, include_tests: bool, include_init: bool) -> bool:
    """Return whether ``path`` passes the inclusion rule described in the module docstring."""
    if not path.endswith(".py"):
        return False
    if not include_init and Path(path).name == "__init__.py":
        return False
    return include_tests or "test" not in path


def _parse_name_status(output: str) -> list[_Change]:
    """Parse ``git diff --name-status -z`` output, folding ``R<score>`` to ``R``."""
    fields = [field for field in output.split("\0") if field]
    changes: list[_Change] = []
    index = 0
    while index < len(fields):
        status = fields[index][0]
        if status == "R":
            changes.append(_Change("R", fields[index + 2], fields[index + 1]))
            index += 3
        else:
            changes.append(_Change(status, fields[index + 1]))
            index += 2
    return changes


def _changed_python_files(
    commit: str,
    pathspecs: Sequence[str] | None = None,
    *,
    new_rev: str | None = "HEAD",
    include_tests: bool = False,
    include_init: bool = False,
) -> list[_Change]:
    """Return the eligible ``.py`` changes between ``commit`` and ``new_rev``.

    ``new_rev=None`` compares against the working tree and adds untracked
    files as ``A``. ``pathspecs`` scopes the diff to one or more git pathspecs;
    when omitted the scope is the whole repository (the ``*.py`` pathspec). A
    directory pathspec also matches non-Python files, so the inclusion rule is
    applied in Python rather than relying on the git pathspec. Renames are
    detected (``-M``) so the old side can be read from the pre-rename path.
    """
    scope = list(pathspecs) if pathspecs else ["*.py"]
    revs = [commit] if new_rev is None else [commit, new_rev]
    output = _run_git(
        [
            "diff",
            "-M",
            "--name-status",
            "-z",
            *revs,
            "--",
            *scope,
        ],
    )
    changes = _parse_name_status(output)
    if new_rev is None:
        untracked = _run_git(
            [
                "ls-files",
                "--others",
                "--exclude-standard",
                "--full-name",
                "-z",
                "--",
                *scope,
            ],
        )
        changes.extend(_Change("A", path) for path in untracked.split("\0") if path)
    return [
        change
        for change in changes
        if _eligible(
            change.old_side_path if change.status == "D" else change.path,
            include_tests=include_tests,
            include_init=include_init,
        )
    ]


def _dirty_python_files(
    pathspecs: Sequence[str] | None,
    *,
    include_tests: bool,
    include_init: bool,
) -> list[_Change]:
    """Return eligible paths that are dirty or untracked in the working tree (porcelain ``XY``)."""
    scope = list(pathspecs) if pathspecs else ["*.py"]
    output = _run_git(
        [
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--",
            *scope,
        ],
    )
    fields = [field for field in output.split("\0") if field]
    changes: list[_Change] = []
    index = 0
    while index < len(fields):
        entry = fields[index]
        status, path = entry[:2], entry[3:]
        old_path = None
        if "R" in status:
            old_path = fields[index + 1]
            index += 1
        index += 1
        if _eligible(path, include_tests=include_tests, include_init=include_init):
            changes.append(_Change(status, path, old_path))
    return changes


def _head_blobs(paths: Sequence[str], rev: str) -> dict[str, str]:
    """Return ``{path: blob id}`` at ``rev`` for every path present there."""
    if not paths:
        return {}
    literal = [f":(top,literal){path}" for path in paths]
    output = _run_git(
        [
            "ls-tree",
            "-z",
            "--full-tree",
            rev,
            "--",
            *literal,
        ],
    )
    blobs: dict[str, str] = {}
    for record in output.split("\0"):
        if not record:
            continue
        meta, path = record.split("\t", 1)
        blobs[path] = meta.split()[2]
    return blobs


def _worktree_blobs(paths: Sequence[str], repo_root: Path) -> dict[str, str]:
    """Return ``{path: blob id}`` of the working-tree copy for every path present on disk."""
    present = [path for path in paths if (repo_root / path).is_file()]
    if not present:
        return {}
    output = _run_git(["hash-object", "--", *(str(repo_root / path) for path in present)])
    return dict(zip(present, output.split(), strict=True))


def _latest_tag() -> str | None:
    """Return the latest tag reachable from HEAD, or ``None`` when there is none."""
    try:
        return (
            _run_git(
                [
                    "describe",
                    "--tags",
                    "--abbrev=0",
                    "HEAD",
                ],
            ).strip()
            or None
        )
    except subprocess.CalledProcessError:
        return None


def _code_view(source: str) -> str:
    """Return ``source`` with comments stripped and docstrings blanked, literals kept.

    Line count is preserved, so line ``n`` of the view is line ``n`` of the source.
    The literal-stripped view is the one ``review_inspect`` writes to disk.
    """
    return _remove_docstring_statements(_strip_comments(source), ast.parse(source))


def _source(rev: str | None, path: str, repo_root: Path) -> str | None:
    """Return ``path`` at ``rev`` (``None`` = working tree), or ``None`` when absent."""
    if rev is None:
        target = repo_root / path
        return target.read_text(encoding="utf-8") if target.is_file() else None
    return _file_at_commit(rev, path)


def _write_new_side(path: str, repo_root: Path, out_dir: Path | None = None) -> None:
    """Inspect the working-tree copy of ``path``; emit a placeholder if missing."""
    out_dir = repo_root / OUTPUT_NEW if out_dir is None else out_dir
    new_file = repo_root / path
    if new_file.is_file():
        _inspect_quiet(new_file, out_dir, repo_root)
    else:
        (out_dir / f"{_stem_for(path)}.stripped.py").write_text("")


def _symbol_spans(tree: ast.AST) -> list[tuple[int, int, str]]:
    """Return ``(start, end, qualified name)`` for every class and function in ``tree``."""
    spans: list[tuple[int, int, str]] = []

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
                name = f"{prefix}{child.name}"
                start = min([child.lineno, *(dec.lineno for dec in child.decorator_list)])
                spans.append((start, child.end_lineno or child.lineno, name))
                visit(child, f"{name}.")
            else:
                visit(child, prefix)

    visit(tree, "")
    return spans


def _enclosing_symbol(spans: Sequence[tuple[int, int, str]], line: int) -> str | None:
    """Return the innermost qualified name whose span contains ``line``."""
    best: tuple[int, int, str] | None = None
    for span in spans:
        if span[0] <= line <= span[1] and (best is None or span[0] >= best[0]):
            best = span
    return best[2] if best else None


def _nonblank(lines: Sequence[str]) -> list[str]:
    return [line for line in lines if line.strip()]


def _range(start: int, length: int) -> str:
    """Render a unified-diff range (``start`` is zero-based)."""
    return f"{start + 1 if length else start},{length}"


def _prose_diff(
    old_src: str | None,
    new_src: str | None,
    old_path: str,
    path: str,
) -> str:
    """Return a unified diff restricted to the comment/docstring-only change regions."""
    old_src, new_src = old_src or "", new_src or ""
    old_raw, new_raw = old_src.splitlines(), new_src.splitlines()
    old_code = _code_view(old_src).split("\n")
    new_code = _code_view(new_src).split("\n")
    old_spans = _symbol_spans(ast.parse(old_src))
    new_spans = _symbol_spans(ast.parse(new_src))
    hunks: list[str] = []
    matcher = difflib.SequenceMatcher(a=old_raw, b=new_raw, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old_chunk, new_chunk = old_raw[i1:i2], new_raw[j1:j2]
        if not _nonblank([*old_chunk, *new_chunk]):
            continue
        if _nonblank(old_code[i1:i2]) != _nonblank(new_code[j1:j2]):
            continue
        symbol = (
            _enclosing_symbol(new_spans, j1 + 1)
            if new_chunk
            else _enclosing_symbol(old_spans, i1 + 1)
        )
        where = f"{path}::{symbol}" if symbol else path
        hunks.append(f"@@ -{_range(i1, i2 - i1)} +{_range(j1, j2 - j1)} @@ {where}\n")
        hunks.extend(f"-{line}\n" for line in old_chunk)
        hunks.extend(f"+{line}\n" for line in new_chunk)
    if not hunks:
        return ""
    return "".join([f"--- a/{old_path}\n", f"+++ b/{path}\n", *hunks])


def _write_diff(
    change: _Change,
    dirs: _SideDirs,
    *,
    collapse_blank: bool = False,
    header: str = "",
) -> None:
    """Write a unified diff between the OLD and NEW stripped files of ``change``."""
    old_stripped = dirs.old / f"{_stem_for(change.old_side_path)}.stripped.py"
    new_stripped = dirs.new / f"{_stem_for(change.path)}.stripped.py"
    old_lines = old_stripped.read_text().splitlines(keepends=True)
    new_lines = new_stripped.read_text().splitlines(keepends=True)
    if collapse_blank:
        old_lines, new_lines = _nonblank(old_lines), _nonblank(new_lines)
    diff = "".join(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=old_stripped.relative_to(dirs.label_base).as_posix(),
            tofile=new_stripped.relative_to(dirs.label_base).as_posix(),
        ),
    )
    (dirs.diff / f"{_stem_for(change.path)}.diff").write_text(header + diff)


def _render_change(
    change: _Change,
    commit: str,
    new_rev: str | None,
    repo_root: Path,
    dirs: _SideDirs,
    args: argparse.Namespace,
) -> None:
    """Render both sides of ``change`` into ``dirs`` and write its diff(s)."""
    old_path = change.old_side_path
    _materialize_and_inspect(commit, old_path, dirs.old)
    if new_rev is None:
        _write_new_side(change.path, repo_root, dirs.new)
    else:
        _materialize_and_inspect(new_rev, change.path, dirs.new)
    old_src = new_src = None
    if args.keep_literals or args.prose:
        old_src = _file_at_commit(commit, old_path)
        new_src = _source(new_rev, change.path, repo_root)
    if args.keep_literals:
        for src, side_path, side_dir in (
            (old_src, old_path, dirs.old),
            (new_src, change.path, dirs.new),
        ):
            view = "" if src is None else _code_view(src)
            (side_dir / f"{_stem_for(side_path)}.stripped.py").write_text(view)
    header = WORKTREE_HEADER if new_rev is None else ""
    _write_diff(change, dirs, collapse_blank=args.collapse_blank, header=header)
    if args.prose:
        prose = _prose_diff(old_src, new_src, old_path, change.path)
        (dirs.diff / f"{_stem_for(change.path)}.prose.diff").write_text(
            header + prose if prose else "",
        )


def _check_stem_collisions(changes: Sequence[_Change]) -> None:
    """Refuse a run where two changed paths would write the same artifact name on one side."""
    for side in ("old_side_path", "path"):
        by_stem: dict[str, list[str]] = {}
        for change in changes:
            path = getattr(change, side)
            by_stem.setdefault(_stem_for(path), []).append(path)
        collisions = {stem: paths for stem, paths in by_stem.items() if len(paths) > 1}
        if collisions:
            raise RuntimeError(f"diff artifact names collide: {collisions!r}")


def _list_payload(
    base: str,
    head: str,
    changes: Sequence[_Change],
    dirty: Sequence[_Change],
    repo_root: Path,
) -> dict[str, object]:
    """Build the ``--list`` data: changed rows with HEAD blobs, dirty rows with both blobs."""
    head_blobs = _head_blobs(sorted({c.path for c in [*changes, *dirty]}), head)
    worktree_blobs = _worktree_blobs(sorted({c.path for c in dirty}), repo_root)
    return {
        "base": base,
        "base_commit": _run_git(["rev-parse", f"{base}^{{commit}}"]).strip(),
        "head": head,
        "changed": [
            {**asdict(change), "head_blob": head_blobs.get(change.path)} for change in changes
        ],
        "dirty": [
            {
                **asdict(change),
                "head_blob": head_blobs.get(change.path),
                "worktree_blob": worktree_blobs.get(change.path),
            }
            for change in dirty
        ],
    }


def _format_list(payload: dict[str, object]) -> str:
    """Render the ``--list`` payload as plain text."""
    changed = payload["changed"]
    dirty = payload["dirty"]
    lines = [
        f"Changed .py files {payload['base']}..HEAD ({str(payload['head'])[:12]}): {len(changed)}",
    ]
    for row in changed:
        name = f"{row['old_path']} -> {row['path']}" if row["old_path"] else row["path"]
        lines.append(f"{row['status']}  {name}  {row['head_blob'] or '-'}")
    lines.append(f"Dirty or untracked in worktree: {len(dirty)}")
    for row in dirty:
        name = f"{row['old_path']} -> {row['path']}" if row["old_path"] else row["path"]
        lines.append(f"{row['status']}  {name}  {row['worktree_blob'] or '-'}")
    return "\n".join(lines) + "\n"


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate per-file stripped diffs between a commit and HEAD for every "
            "changed .py file whose path does not contain 'test'."
        ),
    )
    parser.add_argument(
        "commit_hash",
        nargs="?",
        help="Commit to diff HEAD against. Defaults to --since, then the latest tag.",
    )
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        metavar="PATHSPEC",
        help=(
            "Git pathspec to scope the diff to (repeatable). Defaults to the whole "
            "repository. E.g. --path django_strawberry_framework/filters."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Write old/, new/ and diff/ under this directory instead of docs/shadow/.",
    )
    parser.add_argument(
        "--against",
        choices=("head", "worktree"),
        default="head",
        help="Read the new side from HEAD (default) or from the working tree.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include paths containing 'test' (e.g. django_strawberry_framework/testing/).",
    )
    parser.add_argument(
        "--include-init",
        action="store_true",
        help="Include __init__.py files.",
    )
    parser.add_argument(
        "--keep-literals",
        action="store_true",
        help="Keep string literals and f-string bodies in the stripped files.",
    )
    parser.add_argument(
        "--collapse-blank",
        action="store_true",
        help="Drop blank lines before diffing.",
    )
    parser.add_argument(
        "--prose",
        action="store_true",
        help="Also write diff/<stem>.prose.diff with the comment/docstring-only change regions.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print only the changed-file inventory (writes nothing).",
    )
    parser.add_argument("--json", action="store_true", help="With --list, print JSON.")
    parser.add_argument(
        "--since",
        metavar="REV",
        help="Base commit; alternative spelling of the positional commit.",
    )
    return parser.parse_args(argv)


def _resolve_base(args: argparse.Namespace) -> str | None:
    """Return the base rev from the positional, ``--since`` or the latest tag."""
    if args.commit_hash and args.since and args.commit_hash != args.since:
        print(
            "Pass the base commit either positionally or with --since, not both.",
            file=sys.stderr,
        )
        return None
    base = args.commit_hash or args.since or _latest_tag()
    if base is None:
        print("No commit given and no tag is reachable from HEAD.", file=sys.stderr)
    return base


def _run_list(
    args: argparse.Namespace,
    base: str,
    head: str,
    repo_root: Path,
) -> int:
    changes = _changed_python_files(
        base,
        args.paths,
        new_rev=head,
        include_tests=args.include_tests,
        include_init=args.include_init,
    )
    dirty = _dirty_python_files(
        args.paths,
        include_tests=args.include_tests,
        include_init=args.include_init,
    )
    payload = _list_payload(base, head, changes, dirty, repo_root)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(_format_list(payload), end="")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the orchestrator and return an exit code."""
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    if args.json and not args.list:
        print("--json requires --list.", file=sys.stderr)
        return 2
    base = _resolve_base(args)
    if base is None:
        return 2
    _validate_commit(base)

    repo_root = Path(_run_git(["rev-parse", "--show-toplevel"]).strip())
    head = _run_git(["rev-parse", "HEAD"]).strip()
    if args.list:
        return _run_list(args, base, head, repo_root)

    new_rev = None if args.against == "worktree" else head
    changed = _changed_python_files(
        base,
        args.paths,
        new_rev=new_rev,
        include_tests=args.include_tests,
        include_init=args.include_init,
    )
    _check_stem_collisions(changed)

    if args.output_dir is None:
        # Clear this script's own three folders on every run so stale artifacts
        # from a prior (wider-scoped) run never linger and the summary below
        # reflects only what THIS invocation wrote. The snapshot helper's sibling
        # ``docs/shadow/current/`` is never touched here -- each script owns and
        # clears only its own folders under ``docs/shadow/``.
        for relative in (OUTPUT_OLD, OUTPUT_NEW, OUTPUT_DIFF):
            _clear_shadow_output(repo_root / relative)
        dirs = _SideDirs(
            repo_root / OUTPUT_OLD,
            repo_root / OUTPUT_NEW,
            repo_root / OUTPUT_DIFF,
            repo_root,
        )
        for change in changed:
            _render_change(change, base, new_rev, repo_root, dirs, args)
        diff_display = OUTPUT_DIFF.as_posix()
    else:
        output_dir = args.output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".review-diff-staging-", dir=output_dir))
        try:
            dirs = _SideDirs(staging / "old", staging / "new", staging / "diff", staging)
            for side in (dirs.old, dirs.new, dirs.diff):
                side.mkdir()
            for change in changed:
                _render_change(change, base, new_rev, repo_root, dirs, args)
            for name in ("old", "new", "diff"):
                _publish_staged_snapshot(staging / name, output_dir / name)
        finally:
            shutil.rmtree(staging, ignore_errors=True)
        diff_display = (output_dir / "diff").as_posix()

    if new_rev is None:
        print(WORKTREE_HEADER.removeprefix("# ").strip())
    if not changed:
        scope_note = f" under {args.paths}" if args.paths else ""
        print(
            f"No eligible changed .py files between {base} and HEAD{scope_note}.",
            file=sys.stderr,
        )
        return 0

    written = [f"{_stem_for(change.path)}.diff" for change in changed]
    print(f"Wrote {len(written)} per-file diffs to {diff_display}/")
    for name in sorted(written):
        print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
