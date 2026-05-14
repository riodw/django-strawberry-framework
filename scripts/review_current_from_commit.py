"""Generate stripped/overview shadow files for the CURRENT revision.

Covers every Python file changed between a given commit and HEAD, excluding
paths that contain ``test``.

Same file-selection logic as ``scripts/review_diff_from_commit``, but emits
only the new-side ``*.stripped.py`` and ``*.overview.md`` into
``docs/review/current/`` and does not produce diffs. ``review_inspect.main``
is imported and called in-process to avoid the ``uv`` / Python startup cost
of spawning a subprocess per file.

Usage:
    uv run python scripts/review_current_from_commit.py <commit-hash>

The ``uv run`` prefix is required so the script sees the project's virtual
environment (it imports ``review_inspect`` and the inspector depends on the
project's pinned Python / dependency versions). Run from anywhere inside the
repository; the orchestrator resolves ``git rev-parse --show-toplevel`` and
writes outputs under ``docs/review/current/`` at the repo root.

Example:
    uv run python scripts/review_current_from_commit.py 1e6b5830766545d3cb46e3aff21c6dd58a935da4
"""

from __future__ import annotations

import argparse
import contextlib
import io
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from review_inspect import main as review_inspect_main

OUTPUT_CURRENT = Path("docs/review/current")


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
    """Return repo-relative ``.py`` paths changed between ``commit`` and HEAD."""
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
    return [line for line in output.splitlines() if line]


def _stem_for(path: str) -> str:
    """Convert ``a/b/c.py`` into the ``a__b__c`` stem used by review artifacts."""
    return Path(path).with_suffix("").as_posix().replace("/", "__")


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


def _write_current(path: str, repo_root: Path) -> None:
    """Inspect ``path`` in the working tree, or emit empty placeholders.

    Deleted files (present at ``commit`` but missing from the working tree)
    still produce ``*.stripped.py`` and ``*.overview.md`` placeholders so the
    output directory enumerates every changed path.
    """
    out_dir = repo_root / OUTPUT_CURRENT
    stem = _stem_for(path)
    new_file = repo_root / path
    if new_file.is_file():
        _inspect_quiet(new_file, out_dir, repo_root)
    else:
        (out_dir / f"{stem}.stripped.py").write_text("")
        (out_dir / f"{stem}.overview.md").write_text("")


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate stripped/overview shadow files for the current revision of "
            "every changed .py file whose path does not contain 'test'."
        ),
    )
    parser.add_argument("commit_hash", help="Commit hash to compare HEAD against.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the orchestrator and return an exit code."""
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    _validate_commit(args.commit_hash)

    repo_root = Path(_run_git(["rev-parse", "--show-toplevel"]).strip())
    out_dir = repo_root / OUTPUT_CURRENT
    out_dir.mkdir(parents=True, exist_ok=True)

    changed = _changed_python_files(args.commit_hash)
    if not changed:
        print(
            f"No changed .py files (excluding tests) between {args.commit_hash} and HEAD.",
            file=sys.stderr,
        )
        return 0

    for path in changed:
        _write_current(path, repo_root)

    print(f"Wrote current-version shadow files to {OUTPUT_CURRENT.as_posix()}/")
    for entry in sorted(out_dir.iterdir()):
        print(entry.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
