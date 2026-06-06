"""Delete generated review, builder, and bug-hunt artifacts.

This script intentionally targets only known generated paths:

- contents of ``docs/shadow/`` (recursive) — every per-script folder
  (``current/`` snapshot, ``old/`` ``new/`` ``diff/`` diff sides) plus any
  static-helper / bug-hunt byproducts written to the root
- contents of ``docs/review/temp-tests/``
- contents of every ``docs/**/worker-memory/`` directory
- ``rev-*.py`` and case-sensitive ``review-*.py`` files directly under ``docs/review/``
- contents of ``docs/builder/temp-tests/``
- ``bld-*.md`` files directly under ``docs/builder/``
- ``bld-*.py`` and case-sensitive ``review-*.py`` files directly under ``docs/builder/``
- ``docs/bug_hunt/bug_hunt.*.md``
"""

from __future__ import annotations

import argparse
import shutil
from collections.abc import Iterable, Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLEAR_DIRECTORIES = ("docs/shadow", "docs/review/temp-tests", "docs/builder/temp-tests")
WORKER_MEMORY_ROOTS = ("docs",)
WORKER_MEMORY_DIRECTORY_NAME = "worker-memory"
FILE_GLOBS = (
    ("docs/review", "rev-*.py"),
    ("docs/review", "review-*.py"),
    ("docs/builder", "bld-*.md"),
    ("docs/builder", "bld-*.py"),
    ("docs/builder", "review-*.py"),
    ("docs/bug_hunt", "bug_hunt.*.md"),
)


def _repo_path(relative_path: str) -> Path:
    """Return ``relative_path`` resolved below the repository root."""
    return REPO_ROOT / relative_path


def _delete_file(path: Path) -> bool:
    """Delete ``path`` if it is a file or symlink; return whether it existed."""
    if not path.exists() and not path.is_symlink():
        return False
    if path.is_dir() and not path.is_symlink():
        raise IsADirectoryError(path)
    path.unlink()
    return True


def _delete_tree(path: Path) -> bool:
    """Delete ``path`` recursively if it exists; return whether it existed."""
    if not path.exists() and not path.is_symlink():
        return False
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()
    return True


def _clear_directory(path: Path) -> list[Path]:
    """Delete every child under ``path`` while leaving ``path`` itself in place."""
    if not path.exists() and not path.is_symlink():
        return []
    if not path.is_dir() or path.is_symlink():
        return [path] if _delete_tree(path) else []
    deleted: list[Path] = []
    for child in sorted(path.iterdir()):
        if _delete_tree(child):
            deleted.append(child)
    return deleted


def _glob_files(directory: Path, pattern: str) -> Iterable[Path]:
    """Yield files and symlinks matching ``pattern`` directly under ``directory``."""
    if not directory.exists():
        return ()
    return (
        path for path in sorted(directory.glob(pattern)) if path.is_file() or path.is_symlink()
    )


def _worker_memory_directories() -> Iterable[Path]:
    """Yield every worker-memory directory below configured workflow roots."""
    directories: list[Path] = []
    for root in WORKER_MEMORY_ROOTS:
        root_path = _repo_path(root)
        if not root_path.exists():
            continue
        directories.extend(
            path
            for path in root_path.rglob(WORKER_MEMORY_DIRECTORY_NAME)
            if path.name == WORKER_MEMORY_DIRECTORY_NAME
        )
    return sorted(directories)


def clean_up() -> list[Path]:
    """Delete all configured generated artifacts and return deleted paths."""
    deleted: list[Path] = []

    for directory in CLEAR_DIRECTORIES:
        deleted.extend(_clear_directory(_repo_path(directory)))
    for directory in _worker_memory_directories():
        deleted.extend(_clear_directory(directory))
    for directory, pattern in FILE_GLOBS:
        for path in _glob_files(_repo_path(directory), pattern):
            if _delete_file(path):
                deleted.append(path)

    return deleted


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete generated review, builder, and bug-hunt artifacts.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print deleted paths.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the cleanup command."""
    args = _parse_args(argv)
    deleted = clean_up()
    if not args.quiet:
        for path in deleted:
            print(path.relative_to(REPO_ROOT).as_posix())
        print(f"Deleted {len(deleted)} path(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
