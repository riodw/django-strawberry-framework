#!/usr/bin/env python
"""Render the kanban package-file constants from tracked package files."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = "django_strawberry_framework"
DEFAULT_OUTPUT = REPO_ROOT / "examples" / "fakeshop" / "apps" / "kanban" / "constants.py"


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


def package_file_paths() -> tuple[str, ...]:
    """Return tracked repo-relative package file paths."""
    output = run_git(["ls-files", PACKAGE_DIR])
    return tuple(
        sorted(
            line for line in output.splitlines() if line.startswith(f"{PACKAGE_DIR}/") and line
        ),
    )


def render_constants(paths: Sequence[str]) -> str:
    """Render the constants module."""
    lines = [
        '"""Generated kanban allowlist of tracked package files."""',
        "",
        "PACKAGE_FILE_PATHS = (",
    ]
    lines.extend(f'    "{path}",' for path in paths)
    lines.extend([")", "PACKAGE_FILE_PATH_SET = frozenset(PACKAGE_FILE_PATHS)", ""])
    return "\n".join(lines)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Render apps.kanban.constants from tracked django_strawberry_framework files.",
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
    rendered = render_constants(package_file_paths())
    if args.check:
        if not args.output.is_file() or args.output.read_text() != rendered:
            print(
                f"{args.output} is stale; run scripts/build_kanban_package_file_constants.py.",
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
