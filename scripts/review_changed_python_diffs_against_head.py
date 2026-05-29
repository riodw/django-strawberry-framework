"""Generate per-file stripped diffs between a commit and HEAD.

For every Python file changed between ``<commit-hash>`` and the currently
checked-out branch (HEAD) whose path does not contain ``test``, the script

1. Renders the OLD revision (``commit:path``) through ``review_inspect`` into
   ``docs/shadow/old/`` with a stable ``a__b__c`` stem.
2. Renders the NEW revision (the working-tree copy) into
   ``docs/shadow/new/``.
3. Writes a unified diff of the two stripped shadow files to
   ``docs/shadow/diff/``.

The shared git / ``review_inspect`` plumbing -- ``_run_git``,
``_validate_commit``, ``_stem_for``, ``_inspect_quiet`` and the temp-tree
``_materialize_and_inspect`` primitive -- lives in
``review_historical_package_snapshot_at_commit`` (the canonical home for the
shared review machinery) and is imported here. This module adds only the
changed-file enumeration, the working-tree NEW side, and the diff writer. Added
or deleted files get an empty stripped file on the missing side so the per-file
diff still renders.

Usage:
    uv run python scripts/review_changed_python_diffs_against_head.py <commit-hash> [--path PATHSPEC ...]

The ``uv run`` prefix is required so the script sees the project's virtual
environment (it transitively imports ``review_inspect``, which depends on the
project's pinned Python / dependency versions). Run from anywhere inside the
repository; the orchestrator resolves ``git rev-parse --show-toplevel`` and
writes outputs under ``docs/shadow/{old,new,diff}/`` at the repo root.

``--path`` (repeatable) scopes the diff to one or more git pathspecs so a
focused review does not have to wade through every changed file -- e.g.
``--path django_strawberry_framework/filters`` restricts the run to that
subtree. Each pathspec narrows the set; with none supplied the default is the
whole repository (every changed ``*.py``). The ``*test*`` exclusion and the
``.py`` / non-``__init__.py`` filter still apply on top of the scope.

This diff lens is best for reviewing EDITS to code that already existed at
``<commit-hash>``. For a subsystem largely BORN after that commit the old side
is near-empty and every file reads as "+entire file"; reach for
``review_historical_package_snapshot_at_commit`` (a full stripped snapshot)
instead.

Example:
    uv run python scripts/review_changed_python_diffs_against_head.py \
        1e6b5830766545d3cb46e3aff21c6dd58a935da4 \
        --path django_strawberry_framework/filters
"""

from __future__ import annotations

import argparse
import difflib
import sys
from collections.abc import Sequence
from pathlib import Path

from review_historical_package_snapshot_at_commit import (
    _clear_shadow_output,
    _inspect_quiet,
    _materialize_and_inspect,
    _run_git,
    _stem_for,
    _validate_commit,
)

OUTPUT_OLD = Path("docs/shadow/old")
OUTPUT_NEW = Path("docs/shadow/new")
OUTPUT_DIFF = Path("docs/shadow/diff")


def _changed_python_files(commit: str, pathspecs: Sequence[str] | None = None) -> list[str]:
    """Return repo-relative ``.py`` paths changed between ``commit`` and HEAD.

    ``pathspecs`` scopes the diff to one or more git pathspecs (e.g. a single
    package directory) so a focused review only sees the files it cares about.
    When omitted the scope is the whole repository (the ``*.py`` pathspec). A
    directory pathspec also matches non-Python files, so the ``.py`` filter is
    applied in Python rather than relying solely on the git pathspec.

    Excludes paths containing ``test`` and package ``__init__.py`` re-export
    shims (``review_inspect`` skips those as a no-op, so feeding them through
    here would only produce an empty diff entry without useful content).
    """
    scope = list(pathspecs) if pathspecs else ["*.py"]
    output = _run_git(
        [
            "diff",
            "--name-only",
            commit,
            "HEAD",
            "--",
            *scope,
            ":(exclude)*test*",
        ],
    )
    return [
        line
        for line in output.splitlines()
        if line.endswith(".py") and Path(line).name != "__init__.py"
    ]


def _write_new_side(path: str, repo_root: Path) -> None:
    """Inspect the working-tree copy of ``path``; emit a placeholder if missing."""
    out_dir = repo_root / OUTPUT_NEW
    new_file = repo_root / path
    if new_file.is_file():
        _inspect_quiet(new_file, out_dir, repo_root)
    else:
        (out_dir / f"{_stem_for(path)}.stripped.py").write_text("")


def _write_diff(path: str, repo_root: Path) -> None:
    """Write a unified diff between the OLD and NEW stripped shadow files."""
    stem = _stem_for(path)
    old_stripped = repo_root / OUTPUT_OLD / f"{stem}.stripped.py"
    new_stripped = repo_root / OUTPUT_NEW / f"{stem}.stripped.py"
    diff = "".join(
        difflib.unified_diff(
            old_stripped.read_text().splitlines(keepends=True),
            new_stripped.read_text().splitlines(keepends=True),
            fromfile=str(old_stripped.relative_to(repo_root)),
            tofile=str(new_stripped.relative_to(repo_root)),
        ),
    )
    (repo_root / OUTPUT_DIFF / f"{stem}.diff").write_text(diff)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate per-file stripped diffs between a commit and HEAD for every "
            "changed .py file whose path does not contain 'test'."
        ),
    )
    parser.add_argument("commit_hash", help="Commit hash to diff HEAD against.")
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
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the orchestrator and return an exit code."""
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    _validate_commit(args.commit_hash)

    repo_root = Path(_run_git(["rev-parse", "--show-toplevel"]).strip())
    # Clear this script's own three folders on every run so stale artifacts
    # from a prior (wider-scoped) run never linger and the summary below
    # reflects only what THIS invocation wrote. The snapshot helper's sibling
    # ``docs/shadow/current/`` is never touched here -- each script owns and
    # clears only its own folders under ``docs/shadow/``.
    for relative in (OUTPUT_OLD, OUTPUT_NEW, OUTPUT_DIFF):
        _clear_shadow_output(repo_root / relative)

    changed = _changed_python_files(args.commit_hash, args.paths)
    if not changed:
        scope_note = f" under {args.paths}" if args.paths else ""
        print(
            f"No changed .py files (excluding tests) between {args.commit_hash} and HEAD"
            f"{scope_note}.",
            file=sys.stderr,
        )
        return 0

    written: list[str] = []
    for path in changed:
        _materialize_and_inspect(args.commit_hash, path, repo_root / OUTPUT_OLD)
        _write_new_side(path, repo_root)
        _write_diff(path, repo_root)
        written.append(f"{_stem_for(path)}.diff")

    print(f"Wrote {len(written)} per-file diffs to {OUTPUT_DIFF.as_posix()}/")
    for name in sorted(written):
        print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
