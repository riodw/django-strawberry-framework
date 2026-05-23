"""Generate per-file stripped diffs between a commit and HEAD.

For every Python file changed between ``<commit-hash>`` and the currently
checked-out branch (HEAD) whose path does not contain ``test``, the script

1. Reads the OLD revision via ``git show <commit>:<path>`` into a temp tree
   that mirrors the repo layout, then runs ``scripts/review_inspect`` against
   it so the generated ``*.stripped.py`` and ``*.overview.md`` land in
   ``docs/shadow/bug_hunt/old/`` with a stable ``django_strawberry_framework__conf``
   style stem.
2. Runs ``scripts/review_inspect`` against the NEW revision (the file as it
   exists in the working tree) into ``docs/shadow/bug_hunt/new/``.
3. Writes a unified diff of the two stripped shadow files to
   ``docs/shadow/bug_hunt/diff/``.

``review_inspect.main`` is imported and called in-process so the orchestrator
does not pay Python / ``uv`` startup cost twice per changed file. Added or
deleted files get an empty stripped file on the missing side so the per-file
diff still renders.

Usage:
    uv run python scripts/review_changed_python_diffs_against_head.py <commit-hash>

The ``uv run`` prefix is required so the script sees the project's virtual
environment (it imports ``review_inspect`` and the inspector depends on the
project's pinned Python / dependency versions). Run from anywhere inside the
repository; the orchestrator resolves ``git rev-parse --show-toplevel`` and
writes outputs under ``docs/shadow/bug_hunt/{old,new,diff}/`` at the repo root.

Example:
    uv run python scripts/review_changed_python_diffs_against_head.py 1e6b5830766545d3cb46e3aff21c6dd58a935da4
"""

from __future__ import annotations

import argparse
import contextlib
import difflib
import io
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from review_inspect import main as review_inspect_main

OUTPUT_OLD = Path("docs/shadow/bug_hunt/old")
OUTPUT_NEW = Path("docs/shadow/bug_hunt/new")
OUTPUT_DIFF = Path("docs/shadow/bug_hunt/diff")


def _run_git(args: Sequence[str]) -> str:
    """Run ``git --no-pager <args>`` and return its stdout."""
    result = subprocess.run(
        ["git", "--no-pager", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _validate_commit(commit: str) -> None:
    """Exit with code 2 if ``commit`` does not resolve to a real commit."""
    try:
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        print(f"Not a valid commit hash: {commit}", file=sys.stderr)
        sys.exit(2)


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


def _stem_for(path: str) -> str:
    """Convert ``a/b/c.py`` into the ``a__b__c`` stem used by review artifacts."""
    return Path(path).with_suffix("").as_posix().replace("/", "__")


def _file_at_commit(commit: str, path: str) -> str | None:
    """Return the file contents at ``commit:path`` or ``None`` if absent."""
    exists = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}:{path}"],
        capture_output=True,
        check=False,
    )
    if exists.returncode != 0:
        return None
    return _run_git(["show", f"{commit}:{path}"])


def _inspect_quiet(target: Path, output_dir: Path, root: Path) -> None:
    """Invoke ``review_inspect.main`` while silencing its stdout chatter."""
    with contextlib.redirect_stdout(io.StringIO()):
        exit_code = review_inspect_main(
            [
                str(target),
                "--output-dir",
                str(output_dir),
                "--root",
                str(root),
            ],
        )
    if exit_code != 0:
        raise RuntimeError(
            f"review_inspect failed for {target} (exit code {exit_code}).",
        )


def _write_old_side(commit: str, path: str, repo_root: Path) -> None:
    """Materialize the OLD revision under a temp root and inspect it.

    Mirroring the repo-relative path under the temp root lets
    ``review_inspect`` derive the same stable stem the NEW side uses, so no
    post-hoc renames are needed.
    """
    out_dir = repo_root / OUTPUT_OLD
    stem = _stem_for(path)
    contents = _file_at_commit(commit, path)
    if contents is None:
        (out_dir / f"{stem}.stripped.py").write_text("")
        return
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        tmp_target = tmp_root / path
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        tmp_target.write_text(contents)
        _inspect_quiet(tmp_target, out_dir, tmp_root)


def _write_new_side(path: str, repo_root: Path) -> None:
    """Inspect the working-tree copy of ``path``; emit a placeholder if missing."""
    out_dir = repo_root / OUTPUT_NEW
    stem = _stem_for(path)
    new_file = repo_root / path
    if new_file.is_file():
        _inspect_quiet(new_file, out_dir, repo_root)
    else:
        (out_dir / f"{stem}.stripped.py").write_text("")


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
        _write_old_side(args.commit_hash, path, repo_root)
        _write_new_side(path, repo_root)
        _write_diff(path, repo_root)

    diff_dir = repo_root / OUTPUT_DIFF
    print(f"Wrote per-file diffs to {OUTPUT_DIFF.as_posix()}/")
    for entry in sorted(diff_dir.iterdir()):
        print(entry.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
