#!/usr/bin/env python
"""Render the kanban tracked-path constants from git-tracked package and test files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path

try:
    from _kanban_lib import run_git as _run_git
except ModuleNotFoundError:  # imported as ``scripts.build_kanban_tracked_path_constants``
    from scripts._kanban_lib import run_git as _run_git

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
    """Run ``git --no-pager <args>`` and return stdout (errors as ConstantsRenderError)."""
    return _run_git(args, error_cls=ConstantsRenderError)


def path_root(path: str) -> str | None:
    """Return the tracked root that owns ``path``, or ``None``."""
    for root in TRACKED_ROOTS:
        if path.startswith(root):
            return root
    match = APP_TESTS_ROOT_RE.match(path)
    return match.group(0) if match else None


def tracked_file_paths() -> tuple[str, ...]:
    """Return tracked repo-relative file paths under every tracked root.

    ``-z`` (with ``core.quotePath=false``) keeps a path with a non-ASCII byte,
    a quote or an embedded newline intact instead of C-quoting or splitting it;
    ``--deduplicate`` collapses the three index stages an unmerged path reports
    during a conflicted merge, which would otherwise triplicate its entry.
    """
    output = run_git(
        [
            "-c",
            "core.quotePath=false",
            "ls-files",
            "-z",
            "--deduplicate",
            "django_strawberry_framework",
            "tests",
            "examples/fakeshop/test_query",
            "examples/fakeshop/tests",
            "examples/fakeshop/apps",
        ],
    )
    return tuple(sorted(path for path in output.split("\0") if path and path_root(path)))


def derived_directory_paths(file_paths: Sequence[str]) -> tuple[str, ...]:
    """Return every directory (root included, trailing ``/``) above the tracked files."""
    directories: set[str] = set()
    for file_path in file_paths:
        root = path_root(file_path)
        if root is None:
            raise ConstantsRenderError(f"{file_path} lies under no tracked root.")
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
        *(f"    {json.dumps(path)}," for path in file_paths),
        ")",
        "TRACKED_DIRECTORY_PATHS = (",
        *(f"    {json.dumps(path)}," for path in directory_paths),
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


def current_text(output: Path) -> str | None:
    """Return the constants file's text, or ``None`` when it does not exist yet."""
    if not output.is_file():
        return None
    return output.read_text(encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Render or check the constants module."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    rendered = render_constants(tracked_file_paths())
    unchanged = current_text(args.output) == rendered
    if args.check:
        if not unchanged:
            print(
                f"{args.output} is stale; run scripts/build_kanban_tracked_path_constants.py.",
                file=sys.stderr,
            )
            return 1
        return 0

    # Writing an identical file still bumps its mtime, which dirties git's stat
    # cache and -- because pre-commit stashes unstaged work around the hooks --
    # turns a no-op run into a candidate for a stash conflict. Skip the write.
    if unchanged:
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConstantsRenderError as error:
        print(error, file=sys.stderr)
        raise SystemExit(2) from error
