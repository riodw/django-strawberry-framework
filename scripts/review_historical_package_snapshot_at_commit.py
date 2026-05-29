"""Generate stripped/overview shadow files for a package snapshot.

Enumerates every ``.py`` file under a target package directory at a given
commit and runs ``review_inspect`` against each file's content as it existed
*at that commit* (the working tree is never read). Outputs land in
``docs/shadow/`` with the usual ``a__b__c`` stem scheme. **Existing files
under ``docs/shadow/`` (including the ``bug_hunt/`` subtree) are deleted
before the new snapshot is written**, so any prior review/build helper
output or diff-helper output there is discarded.

Use this when you want a static review snapshot of the entire package at
some historical checkout, without actually checking that commit out and
without limiting the file set to whatever happens to have changed since.
Paths containing ``test`` are excluded (the package source tree shouldn't
contain any, but the guard matches the diff helper's contract).

``review_inspect.main`` is imported and called in-process so the
orchestrator does not pay Python / ``uv`` startup cost per file.

Usage:
    uv run python scripts/review_historical_package_snapshot_at_commit.py <commit-hash> [--package-dir DIR]

The ``uv run`` prefix is required so the script sees the project's virtual
environment (it imports ``review_inspect`` and the inspector depends on the
project's pinned Python / dependency versions). Run from anywhere inside
the repository; the orchestrator resolves ``git rev-parse --show-toplevel``
and writes outputs under ``docs/shadow/`` at the repo root.

Example:
    uv run python scripts/review_historical_package_snapshot_at_commit.py \
        9096519590040fa25484e05b6a104cb5652b9676 \
        --package-dir examples/fakeshop/apps/library
"""

from __future__ import annotations

import argparse
import contextlib
import io
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from review_inspect import main as review_inspect_main

SHADOW_DIR = Path("docs/shadow")
DEFAULT_PACKAGE_DIR = "django_strawberry_framework"


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
            [
                "git",
                "rev-parse",
                "--verify",
                "--quiet",
                f"{commit}^{{commit}}",
            ],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        print(f"Not a valid commit hash: {commit}", file=sys.stderr)
        sys.exit(2)


def _package_python_files_at_commit(commit: str, package_dir: str) -> list[str]:
    """Return every ``.py`` path under ``package_dir`` at ``commit``.

    Uses ``git ls-tree -r`` so the working tree is never consulted. Paths
    that contain ``test`` are filtered out to match the diff helper's
    exclusion contract.
    """
    output = _run_git(
        [
            "ls-tree",
            "-r",
            "--name-only",
            commit,
            "--",
            package_dir,
        ],
    )
    return [
        line
        for line in output.splitlines()
        if line.endswith(".py") and "test" not in line and Path(line).name != "__init__.py"
    ]


def _stem_for(path: str) -> str:
    """Convert ``a/b/c.py`` into the ``a__b__c`` stem used by review artifacts."""
    return Path(path).with_suffix("").as_posix().replace("/", "__")


def _file_at_commit(commit: str, path: str) -> str:
    """Return the file contents at ``commit:path``."""
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


def _clear_shadow_output(output_dir: Path) -> None:
    """Delete existing shadow output before writing a fresh snapshot."""
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        return
    for child in sorted(output_dir.iterdir()):
        if child.is_dir():
            for nested in sorted(child.rglob("*"), reverse=True):
                if nested.is_file() or nested.is_symlink():
                    nested.unlink()
                else:
                    nested.rmdir()
            child.rmdir()
        else:
            child.unlink()


def _write_snapshot(commit: str, path: str, repo_root: Path) -> None:
    """Materialize ``commit:path`` under a temp root and inspect it.

    Mirroring the repo-relative path under the temp root lets
    ``review_inspect`` derive the same stable ``a__b__c`` stem the file
    would get from the working tree, so the output names stay consistent
    across snapshots.
    """
    out_dir = repo_root / SHADOW_DIR
    contents = _file_at_commit(commit, path)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        tmp_target = tmp_root / path
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        tmp_target.write_text(contents)
        _inspect_quiet(tmp_target, out_dir, tmp_root)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate stripped/overview shadow files for every .py file under "
            "a package directory at the given commit."
        ),
    )
    parser.add_argument("commit_hash", help="Commit hash to snapshot.")
    parser.add_argument(
        "--package-dir",
        default=DEFAULT_PACKAGE_DIR,
        help=(f"Repo-relative directory to scan recursively. Defaults to {DEFAULT_PACKAGE_DIR!r}."),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the orchestrator and return an exit code."""
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    _validate_commit(args.commit_hash)

    repo_root = Path(_run_git(["rev-parse", "--show-toplevel"]).strip())
    out_dir = repo_root / SHADOW_DIR

    paths = _package_python_files_at_commit(args.commit_hash, args.package_dir)
    if not paths:
        print(
            f"No .py files under {args.package_dir!r} at {args.commit_hash} "
            "(after excluding paths containing 'test').",
            file=sys.stderr,
        )
        return 0

    _clear_shadow_output(out_dir)
    for path in paths:
        _write_snapshot(args.commit_hash, path, repo_root)

    print(
        f"Wrote {len(paths)} snapshots from {args.commit_hash} to {SHADOW_DIR.as_posix()}/",
    )
    for entry in sorted(out_dir.iterdir()):
        print(entry.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
