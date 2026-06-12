#!/usr/bin/env python
"""Render the kanban tracked-path constants from git-tracked package and test files."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "examples" / "fakeshop" / "apps" / "kanban" / "constants.py"
# The roots kanban cards may link paths under: the package itself plus the four
# deliberate test locations (see docs/TREE.md "Test layout").
TRACKED_ROOTS = (
    "django_strawberry_framework/",
    "tests/",
    "examples/fakeshop/test_query/",
    "examples/fakeshop/tests/",
)
APP_TESTS_ROOT_RE = re.compile(r"^examples/fakeshop/apps/[^/]+/tests/")


class ConstantsRenderError(RuntimeError):
    """A caller-correctable constants rendering error."""


def run_git(args: Sequence[str]) -> str:
    """Run ``git --no-pager <args>`` and return stdout."""
    try:
        result = subprocess.run(
            ["git", "--no-pager", *args],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or f"git {' '.join(args)} failed."
        raise ConstantsRenderError(message) from error
    return result.stdout


def path_root(path: str) -> str | None:
    """Return the tracked root that owns ``path``, or ``None``."""
    for root in TRACKED_ROOTS:
        if path.startswith(root):
            return root
    match = APP_TESTS_ROOT_RE.match(path)
    return match.group(0) if match else None


def tracked_file_paths() -> tuple[str, ...]:
    """Return tracked repo-relative file paths under every tracked root."""
    output = run_git(
        [
            "ls-files",
            "django_strawberry_framework",
            "tests",
            "examples/fakeshop/test_query",
            "examples/fakeshop/tests",
            "examples/fakeshop/apps",
        ],
    )
    return tuple(sorted(line for line in output.splitlines() if line and path_root(line)))


def derived_directory_paths(file_paths: Sequence[str]) -> tuple[str, ...]:
    """Return every directory (root included, trailing ``/``) above the tracked files."""
    directories: set[str] = set()
    for file_path in file_paths:
        root = path_root(file_path)
        parent = file_path.rsplit("/", 1)[0] + "/"
        while len(parent) >= len(root):
            directories.add(parent)
            if parent == root:
                break
            parent = parent[:-1].rsplit("/", 1)[0] + "/"
    return tuple(sorted(directories))


def render_constants(file_paths: Sequence[str]) -> str:
    """Render the constants module."""
    directory_paths = derived_directory_paths(file_paths)
    lines = [
        '"""Generated kanban allowlist of tracked repository paths (files + directories)."""',
        "",
        "TRACKED_FILE_PATHS = (",
        *(f'    "{path}",' for path in file_paths),
        ")",
        "TRACKED_DIRECTORY_PATHS = (",
        *(f'    "{path}",' for path in directory_paths),
        ")",
        "TRACKED_PATHS = TRACKED_DIRECTORY_PATHS + TRACKED_FILE_PATHS",
        "TRACKED_PATH_SET = frozenset(TRACKED_PATHS)",
        "",
    ]
    return "\n".join(lines)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Render apps.kanban.constants from tracked package and test paths.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Constants file to write. Defaults to apps/kanban/constants.py.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with status 1 if the constants file is stale.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Render or check the constants module."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    rendered = render_constants(tracked_file_paths())
    if args.check:
        if not args.output.is_file() or args.output.read_text() != rendered:
            print(
                f"{args.output} is stale; run scripts/build_kanban_tracked_path_constants.py.",
                file=sys.stderr,
            )
            return 1
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConstantsRenderError as error:
        print(error, file=sys.stderr)
        raise SystemExit(2) from error
