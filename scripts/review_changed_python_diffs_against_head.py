"""Generate per-file stripped diffs between a commit and HEAD.

For every Python file changed between ``<commit-hash>`` and the currently
checked-out branch (HEAD) whose path does not contain ``test``, the script

1. Renders the OLD revision (``commit:path``) through ``review_inspect`` into
   ``docs/shadow/bug_hunt/old/`` with a stable ``a__b__c`` stem.
2. Renders the NEW revision (the working-tree copy) into
   ``docs/shadow/bug_hunt/new/``.
3. Writes a unified diff of the two stripped shadow files to
   ``docs/shadow/bug_hunt/diff/``.

The shared git / ``review_inspect`` plumbing -- ``_run_git``,
``_validate_commit``, ``_stem_for``, ``_inspect_quiet`` and the temp-tree
``_materialize_and_inspect`` primitive -- lives in
``review_historical_package_snapshot_at_commit`` (the canonical home for the
shared review machinery) and is imported here. This module adds only the
changed-file enumeration, the working-tree NEW side, and the diff writer. Added
or deleted files get an empty stripped file on the missing side so the per-file
diff still renders.

Usage:
    uv run python scripts/review_changed_python_diffs_against_head.py <commit-hash>

The ``uv run`` prefix is required so the script sees the project's virtual
environment (it transitively imports ``review_inspect``, which depends on the
project's pinned Python / dependency versions). Run from anywhere inside the
repository; the orchestrator resolves ``git rev-parse --show-toplevel`` and
writes outputs under ``docs/shadow/bug_hunt/{old,new,diff}/`` at the repo root.

Example:
    uv run python scripts/review_changed_python_diffs_against_head.py 1e6b5830766545d3cb46e3aff21c6dd58a935da4
"""

from __future__ import annotations

import argparse
import difflib
import sys
from collections.abc import Sequence
from pathlib import Path

from review_historical_package_snapshot_at_commit import (
    _inspect_quiet,
    _materialize_and_inspect,
    _run_git,
    _stem_for,
    _validate_commit,
)

OUTPUT_OLD = Path("docs/shadow/bug_hunt/old")
OUTPUT_NEW = Path("docs/shadow/bug_hunt/new")
OUTPUT_DIFF = Path("docs/shadow/bug_hunt/diff")


def _changed_python_files(commit: str) -> list[str]:
    """Return repo-relative ``.py`` paths changed between ``commit`` and HEAD.

    Excludes paths containing ``test`` and package ``__init__.py`` re-export
    shims (``review_inspect`` skips those as a no-op, so feeding them through
    here would only produce an empty diff entry without useful content).
    """
    output = _run_git(
        [
            "diff",
            "--name-only",
            commit,
            "HEAD",
            "--",
            "*.py",
            ":(exclude)*test*",
        ],
    )
    return [line for line in output.splitlines() if line and Path(line).name != "__init__.py"]


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
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the orchestrator and return an exit code."""
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    _validate_commit(args.commit_hash)

    repo_root = Path(_run_git(["rev-parse", "--show-toplevel"]).strip())
    for relative in (OUTPUT_OLD, OUTPUT_NEW, OUTPUT_DIFF):
        (repo_root / relative).mkdir(parents=True, exist_ok=True)

    changed = _changed_python_files(args.commit_hash)
    if not changed:
        print(
            f"No changed .py files (excluding tests) between {args.commit_hash} and HEAD.",
            file=sys.stderr,
        )
        return 0

    for path in changed:
        _materialize_and_inspect(args.commit_hash, path, repo_root / OUTPUT_OLD)
        _write_new_side(path, repo_root)
        _write_diff(path, repo_root)

    diff_dir = repo_root / OUTPUT_DIFF
    print(f"Wrote per-file diffs to {OUTPUT_DIFF.as_posix()}/")
    for entry in sorted(diff_dir.iterdir()):
        print(entry.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
