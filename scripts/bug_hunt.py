"""Generate the per-commit bug-hunt checklist markdown.

The script resolves the current branch's HEAD commit hash, refreshes
``docs/shadow/`` in-process via
``review_historical_package_snapshot_at_commit.main([<head-sha>])``,
reads the passed-in dicta (default ``docs/bug_hunt/dicta.md``), appends
the static single-file review boilerplate, and emits one checkbox +
prompt block per ``*.stripped.py`` file under ``docs/shadow/``.

The output path defaults to ``docs/bug_hunt/bug_hunt.<short-sha>.md``.

Usage:
    uv run python scripts/bug_hunt.py [--dicta PATH] [--output PATH] [--package-dir DIR]
"""

from __future__ import annotations

import argparse
import contextlib
import io
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from review_historical_package_snapshot_at_commit import (
    DEFAULT_PACKAGE_DIR,
)
from review_historical_package_snapshot_at_commit import (
    main as review_historical_package_snapshot_at_commit_main,
)

BUG_HUNT_DIR = Path("docs/bug_hunt")
SHADOW_DIR = Path("docs/shadow")
DICTA_PATH = BUG_HUNT_DIR / "dicta.md"

# Fallback dicta used when ``--dicta`` points at a missing file.
_FALLBACK_DICTA = (
    "# Bug hunt\n"
    "One prompt per file. Read the stripped + overview shadow companions and\n"
    "edit the original source if a defect is found. Shadow line numbers are\n"
    "not canonical; cite original source line numbers in any fix.\n"
)

# Static boilerplate describing how to perform a good single-file bug
# review pass.
_HOW_TO_REVIEW_ONE_FILE = """## How to review a single file
Each prompt below targets exactly one source file. Treat it as a focused
review pass, not a tour:

- Read the `.overview.md` shadow first. It is a structural index —
  quick-scan counts, imports, symbols, control-flow hotspots, executable
  Django/ORM marker lines, calls of interest, and repeated executable
  string literals — pulled from the AST without executing the file. Use
  it to plan the read, not as the source of truth.
- Read the `.stripped.py` shadow next. Comments and docstring statements
  are removed, and other string literals are replaced, so the executable
  structure is easier to scan. **Line numbers in the stripped file are
  not canonical.** Cite original source-file line numbers in every
  finding and every fix.
- Open the original source file alongside (named in the prompt) and
  reconcile the shadow view against the real code before declaring a
  defect.
- Confirm every defect against the actual source. No speculation, no
  "this might be wrong". If you cannot reproduce the failure shape
  mentally or with a quick read, drop the finding and move on. Silence
  on a marker line is acceptable; speculative defects pollute the
  checklist.

For each confirmed defect:

- Classify severity using the criteria in the dicta header above.
- Edit the original source file directly. Stay within the file the
  prompt names — if the fix needs sibling changes, surface that as a
  question rather than expanding the diff unilaterally.
- For **High**-severity fixes, add or update a test that pins the
  corrected behavior under the correct test tree per AGENTS.md
  "Test placement is mandatory". Do not rely on validation alone.
- For **Medium** / **Low** fixes that change a documented contract,
  update the relevant docstring or comment in the same pass so the
  prose matches the final behavior.
- Run `uv run ruff format <file>` and `uv run ruff check <file>` on
  any source file you touched.

When the file is done, tick its checkbox `- [x]` so the next prompt is
obvious.

## Per-file prompts
"""


def _run_git(args: Sequence[str]) -> str:
    """Run ``git --no-pager <args>`` and return its stdout."""
    result = subprocess.run(
        ["git", "--no-pager", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _head_sha() -> str:
    """Return the full SHA of the current branch's HEAD commit."""
    return _run_git(["rev-parse", "HEAD"]).strip()


def _short_sha(commit: str) -> str:
    """Return the short SHA for ``commit``."""
    return _run_git(
        ["rev-parse", "--short", commit],
    ).strip()


def _source_path_for(stripped_path: Path) -> str:
    """Recover the original repo-relative source path from a stripped stem.

    ``review_inspect._stable_stem`` joins the relative path's parts with
    ``__``, so reversing is ``stem.split("__")`` — *not* a blind
    ``replace("__", "/")``. The difference matters for paths that contain
    components starting with ``_``: ``optimizer/_context.py`` becomes
    ``optimizer___context`` (two underscores from the join plus the
    leading underscore on ``_context``), which ``split("__")`` correctly
    splits into ``["optimizer", "_context"]`` while a literal replace
    would produce ``optimizer/_/context``.
    """
    stem = stripped_path.name.removesuffix(".stripped.py")
    return "/".join(stem.split("__")) + ".py"


def _stripped_files(current_dir: Path) -> list[Path]:
    """Return every ``*.stripped.py`` under ``current_dir``, sorted."""
    return sorted(current_dir.glob("*.stripped.py"))


def _refresh_historical_package_snapshot(commit: str, package_dir: str, current_dir: Path) -> None:
    """Rebuild ``docs/shadow/`` from ``commit`` in-process.

    Output is silenced here; ``bug_hunt.py`` prints its own status line.
    """
    with contextlib.redirect_stdout(io.StringIO()):
        exit_code = review_historical_package_snapshot_at_commit_main(
            [commit, "--package-dir", package_dir],
        )
    if exit_code != 0:
        raise RuntimeError(
            "review_historical_package_snapshot_at_commit.py failed while refreshing "
            f"{current_dir} for {commit} (exit code {exit_code}).",
        )


def _file_block(source: str, stripped: Path, overview: Path) -> str:
    """Render one checkbox block for a single source file."""
    prompt = (
        f"Read {stripped.as_posix()} and {overview.as_posix()} and check for "
        f"bugs, if any are found make edits to {source}"
    )
    return (
        f"- [ ] {source}\n"
        f"    - {stripped.as_posix()}\n"
        f"    - {overview.as_posix()}\n"
        f"    - Prompt:\n"
        f"        - {prompt}\n"
    )


def _read_dicta(dicta_path: Path) -> str:
    """Return ``dicta_path`` contents (newline-terminated) or the fallback."""
    if dicta_path.is_file():
        text = dicta_path.read_text(encoding="utf-8")
        return text if text.endswith("\n") else text + "\n"
    return _FALLBACK_DICTA


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Resolve HEAD, refresh docs/shadow/ from that commit, "
            "then generate the per-commit bug-hunt checklist by combining "
            "the passed-in dicta, the static how-to-review boilerplate, and "
            "one prompt per .stripped.py file."
        ),
    )
    parser.add_argument(
        "--dicta",
        type=Path,
        default=DICTA_PATH,
        help=(
            "Markdown file passed in as the bug_hunt.<sha>.md dicta header. "
            f"Defaults to {DICTA_PATH.as_posix()!r} (HUNT.md Step 1 writes this)."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Override the output checklist path. Defaults to "
            "docs/bug_hunt/bug_hunt.<short-sha>.md where <short-sha> is "
            "`git rev-parse --short HEAD`."
        ),
    )
    parser.add_argument(
        "--package-dir",
        default=DEFAULT_PACKAGE_DIR,
        help=(
            "Repo-relative directory passed through to "
            "review_historical_package_snapshot_at_commit.py when refreshing docs/shadow/. "
            f"Defaults to {DEFAULT_PACKAGE_DIR!r}."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Build the bug-hunt checklist and return an exit code."""
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    repo_root = Path(_run_git(["rev-parse", "--show-toplevel"]).strip())
    head_sha = _head_sha()
    short_sha = _short_sha(head_sha)
    current_dir = (repo_root / SHADOW_DIR).resolve()
    dicta_path = (repo_root / args.dicta).resolve()

    if args.output is None:
        output_path = (repo_root / BUG_HUNT_DIR / f"bug_hunt.{short_sha}.md").resolve()
    else:
        output_path = (repo_root / args.output).resolve()
    try:
        _refresh_historical_package_snapshot(
            head_sha,
            args.package_dir,
            current_dir,
        )
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1

    stripped_files = _stripped_files(current_dir)
    if not stripped_files:
        print(
            f"No *.stripped.py files in {current_dir} after refreshing {args.package_dir!r} from {head_sha}.",
            file=sys.stderr,
        )
        return 2

    sections: list[str] = [_read_dicta(dicta_path), _HOW_TO_REVIEW_ONE_FILE]
    for stripped in stripped_files:
        source = _source_path_for(stripped)
        overview = stripped.with_name(stripped.name.removesuffix(".stripped.py") + ".overview.md")
        # Keep output paths repo-relative.
        stripped_rel = stripped.relative_to(repo_root)
        overview_rel = overview.relative_to(repo_root)
        sections.append(_file_block(source, stripped_rel, overview_rel))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(sections), encoding="utf-8")

    rel_output = output_path.relative_to(repo_root)
    print(
        f"Refreshed {SHADOW_DIR.as_posix()}/ from {head_sha} "
        f"({args.package_dir}) and wrote {len(stripped_files)} prompts to "
        f"{rel_output.as_posix()}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
