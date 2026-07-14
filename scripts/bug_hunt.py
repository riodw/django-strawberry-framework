"""Generate the autonomous release-scoped bug-hunt progress file.

The script resolves the current branch's HEAD commit hash, refreshes
the snapshot helper's ``docs/shadow/current/`` folder in-process via
``review_historical_package_snapshot_at_commit.main([<head-sha>])``
(the output location is imported as ``SHADOW_DIR`` so it cannot drift
from the snapshot helper), reads the passed-in dicta (default
``docs/bug_hunt/dicta.md``), inventories the live package, and writes a
progress header, the static single-file hunt brief, one checkbox per live
non-``__init__.py`` Python file, a package-integration item, and the final
test gate. Matching shadows are optional baseline aids for those live files.

The output path defaults to ``docs/bug_hunt/bug_hunt-<release>.md``, where
``<release>`` is the matching version in ``pyproject.toml`` and the package
``__init__.py`` (dots become underscores). This matches the review and DRY
agentflow progress-file naming; ``--target-release`` overrides the version.
Existing progress is preserved unless ``--force`` is passed for an
explicit restart.

Usage:
    uv run python scripts/bug_hunt.py [--dicta PATH] [--output PATH]
        [--package-dir DIR] [--target-release RELEASE] [--force]
"""

from __future__ import annotations

import argparse
import contextlib
import io
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None

if __package__:
    from scripts import review_historical_package_snapshot_at_commit as snapshot
else:
    import review_historical_package_snapshot_at_commit as snapshot

DEFAULT_PACKAGE_DIR = snapshot.DEFAULT_PACKAGE_DIR
SHADOW_DIR = snapshot.SHADOW_DIR
review_historical_package_snapshot_at_commit_main = snapshot.main

BUG_HUNT_DIR = Path("docs/bug_hunt")
DICTA_PATH = BUG_HUNT_DIR / "dicta.md"
PACKAGE_INIT = Path("django_strawberry_framework/__init__.py")

# Dotted-digit release such as 0.0.13; shared with the review and DRY flows.
RELEASE_PATTERN = re.compile(r"^\d+(?:\.\d+)+$")
_PROJECT_TABLE_PATTERN = re.compile(
    r"(?ms)^\[project\][ \t]*(?:#.*)?\n(?P<body>.*?)(?=^\[|\Z)",
)
_VERSION_ASSIGNMENT_PATTERN = re.compile(
    r"""(?m)^version\s*=\s*(?P<quote>["'])(?P<version>[^"']+)(?P=quote)\s*(?:#.*)?$""",
)
_INIT_VERSION_PATTERN = re.compile(
    r"""(?m)^__version__\s*=\s*(?P<quote>["'])(?P<version>[^"']+)(?P=quote)\s*(?:#.*)?$""",
)

# Fallback dicta used when ``--dicta`` points at a missing file.
_FALLBACK_DICTA = (
    "## Package questions\n\n"
    "No maintainer-authored probing questions were supplied. Explore the live source freely; "
    "shadow inputs are orientation only.\n"
)

# Static boilerplate describing the Worker 2 single-file hunt.
_HOW_TO_REVIEW_ONE_FILE = """## How to hunt one file
Each item uses one source file as its entry point into the live system. The
target is narrow; the investigation and root-cause fix may cross files.

- Read the shadow overview and stripped source for baseline orientation, then
  read the complete live target. Shadow markers and stripped line numbers are
  never authoritative.
- Trace callers, dependencies, state, framework hooks, tests, examples, and
  public contracts far enough to understand the target's real behavior. Clean
  layers often fail only when several reasonable assumptions stack together;
  hunt those interactions, not only suspicious local lines.
- Break things, break things, break things. Write messy scratch test files and
  be maximally destructive inside disposable scratch scope: mutate throwaway
  state, force hostile sequences, interrupt lifecycles, and try to make every
  connected layer fail.
- For every extreme, test the opposite extreme and then combine them across
  layers. Try to disprove every candidate and record only confirmed defects.
- Do not clean up scratch probes or disposable state. Report every path and
  leave it intact so Worker 1 can independently verify it and clean it up only
  after the item passes.
- Implement the root-cause fix at the layer that owns the broken invariant,
  including connected files when required. Add a permanent behavioral test for
  every production fix at the strongest tier required by `AGENTS.md`.
- After edits run `uv run ruff format .` and `uv run ruff check --fix .`.
- Report evidence, changed files, tests, and validation to Worker 1. Do not edit
  this progress file; Worker 1 independently verifies fixes and advances it.

## Hunt items
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


def _pyproject_version(repo_root: Path) -> str:
    """Read ``[project] version`` from pyproject.toml."""
    pyproject_path = repo_root / "pyproject.toml"
    try:
        text = pyproject_path.read_text(encoding="utf-8")
    except OSError as error:
        raise RuntimeError(f"could not read pyproject.toml: {error}") from error

    if tomllib is None:
        project_match = _PROJECT_TABLE_PATTERN.search(text)
        version_match = (
            _VERSION_ASSIGNMENT_PATTERN.search(project_match.group("body"))
            if project_match is not None
            else None
        )
        if version_match is None:
            raise RuntimeError("[project] version not found in pyproject.toml")
        return version_match.group("version")

    try:
        project = tomllib.loads(text)["project"]
        version = project["version"]
    except (KeyError, tomllib.TOMLDecodeError) as error:
        raise RuntimeError(
            f"could not read [project] version from pyproject.toml: {error}",
        ) from error
    if not isinstance(version, str) or not version:
        raise RuntimeError("[project] version in pyproject.toml must be a non-empty string")
    return version


def _init_version(repo_root: Path) -> str:
    """Read ``__version__`` from the package ``__init__.py``."""
    init_path = repo_root / PACKAGE_INIT
    try:
        text = init_path.read_text(encoding="utf-8")
    except OSError as error:
        raise RuntimeError(f"could not read {PACKAGE_INIT.as_posix()}: {error}") from error
    match = _INIT_VERSION_PATTERN.search(text)
    if match is None:
        raise RuntimeError(f"__version__ not found in {PACKAGE_INIT.as_posix()}")
    return match.group("version")


def _package_release(repo_root: Path) -> str:
    """Return the release shared by pyproject.toml and the package ``__init__``.

    Mirrors the review flow: the release is read from the matching versions so
    the three agentflows name their progress files identically. A mismatch is
    an error -- the two versions must be bumped together.
    """
    pyproject_version = _pyproject_version(repo_root)
    init_version = _init_version(repo_root)
    if pyproject_version != init_version:
        raise RuntimeError(
            f"version mismatch: pyproject.toml has {pyproject_version!r} but "
            f"{PACKAGE_INIT.as_posix()} has {init_version!r}; bump them together",
        )
    return pyproject_version


def _live_python_sources(repo_root: Path, package_dir: str) -> list[str]:
    """Return every live non-init Python source under ``package_dir``."""
    package_root = (repo_root / package_dir).resolve()
    if not package_root.is_dir():
        return []
    return [
        path.relative_to(repo_root).as_posix()
        for path in sorted(package_root.rglob("*.py"))
        if path.name != "__init__.py"
    ]


def _shadow_inputs(
    repo_root: Path,
    current_dir: Path,
    source: str,
) -> tuple[Path | None, Path | None]:
    """Return repo-relative baseline shadow inputs when both exist."""
    stem = Path(source).with_suffix("").as_posix().replace("/", "__")
    stripped = current_dir / f"{stem}.stripped.py"
    overview = current_dir / f"{stem}.overview.md"
    if not stripped.is_file() or not overview.is_file():
        return None, None
    return stripped.relative_to(repo_root), overview.relative_to(repo_root)


def _refresh_historical_package_snapshot(commit: str, package_dir: str, current_dir: Path) -> None:
    """Rebuild the snapshot helper's ``docs/shadow/current/`` from ``commit`` in-process.

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


def _file_block(source: str, stripped: Path | None, overview: Path | None) -> str:
    """Render one checkbox block for a single source file."""
    lines = [f"- [ ] {source}", "    - Status: pending"]
    if stripped is not None and overview is not None:
        lines.extend([f"    - {stripped.as_posix()}", f"    - {overview.as_posix()}"])
        orientation = (
            f"Read {stripped.as_posix()} and {overview.as_posix()} for baseline orientation, then "
        )
    else:
        lines.append("    - Baseline shadow: none (live file added or absent at hunt baseline)")
        orientation = "No baseline shadow exists; "
    prompt = (
        f"Use {source} as the entry point. {orientation}hunt the connected live system and "
        "implement every confirmed root-cause fix."
    )
    lines.extend(["    - Prompt:", f"        - {prompt}"])
    return "\n".join(lines) + "\n"


def _progress_header(commit: str, release: str) -> str:
    """Render the stable metadata for one autonomous hunt."""
    return (
        f"# Bug hunt: {release}\n\n"
        "Status: in-progress\n"
        "Mode: autonomous\n"
        f"Baseline commit: `{commit}`\n"
    )


def _integration_block() -> str:
    """Render the package-wide integration hunt item."""
    return (
        "- [ ] Package integration\n"
        "    - Status: pending\n"
        "    - Prompt:\n"
        "        - Hunt the final live package across boundaries, including public exports and "
        "`__init__.py` files; implement every confirmed root-cause fix.\n"
    )


def _final_gate_block() -> str:
    """Render the Worker 1 full-suite gate."""
    return (
        "- [ ] Final test gate\n"
        "    - Status: pending\n"
        "    - Owner: Worker 1\n"
        "    - Prompt:\n"
        "        - Run `uv run pytest`; require a passing suite and 100% configured package "
        "coverage.\n"
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
            "Resolve HEAD, refresh docs/shadow/current/ from that commit, "
            "then generate the autonomous release-scoped bug-hunt progress file."
        ),
    )
    parser.add_argument(
        "--dicta",
        type=Path,
        default=DICTA_PATH,
        help=(
            "Optional maintainer-authored probing questions added to the progress file. "
            f"Defaults to {DICTA_PATH.as_posix()!r}."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Override the output checklist path. Defaults to "
            "docs/bug_hunt/bug_hunt-<release>.md where <release> is the package "
            "version (dots as underscores)."
        ),
    )
    parser.add_argument(
        "--target-release",
        default=None,
        help=(
            "Release used to name the progress file, matching the review and DRY "
            "flows. Defaults to the matching version in pyproject.toml and "
            f"{PACKAGE_INIT.as_posix()}."
        ),
    )
    parser.add_argument(
        "--package-dir",
        default=DEFAULT_PACKAGE_DIR,
        help=(
            "Repo-relative directory passed through to "
            "review_historical_package_snapshot_at_commit.py when refreshing docs/shadow/current/. "
            f"Defaults to {DEFAULT_PACKAGE_DIR!r}."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing progress file for an explicit maintainer-requested restart.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Build the bug-hunt checklist and return an exit code."""
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    repo_root = Path(_run_git(["rev-parse", "--show-toplevel"]).strip()).resolve()
    head_sha = _head_sha()
    try:
        release = (
            _package_release(repo_root) if args.target_release is None else args.target_release
        )
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    if not RELEASE_PATTERN.fullmatch(release):
        print(
            f"invalid release {release!r}; expected dotted digits such as 0.0.14",
            file=sys.stderr,
        )
        return 1
    current_dir = (repo_root / SHADOW_DIR).resolve()
    dicta_path = (repo_root / args.dicta).resolve()

    if args.output is None:
        release_slug = release.replace(".", "_")
        output_path = (repo_root / BUG_HUNT_DIR / f"bug_hunt-{release_slug}.md").resolve()
    else:
        output_path = (repo_root / args.output).resolve()
    if output_path.exists() and not args.force:
        print(
            f"Refusing to overwrite existing bug-hunt progress: {output_path}. "
            "Resume it, or pass --force only for an explicit restart.",
            file=sys.stderr,
        )
        return 3
    try:
        _refresh_historical_package_snapshot(
            head_sha,
            args.package_dir,
            current_dir,
        )
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1

    source_paths = _live_python_sources(repo_root, args.package_dir)
    if not source_paths:
        print(
            f"No live non-init Python files under {args.package_dir!r}.",
            file=sys.stderr,
        )
        return 2

    sections: list[str] = [
        _progress_header(head_sha, release),
        _read_dicta(dicta_path),
        _HOW_TO_REVIEW_ONE_FILE,
    ]
    for source in source_paths:
        stripped, overview = _shadow_inputs(repo_root, current_dir, source)
        sections.append(_file_block(source, stripped, overview))
    sections.extend([_integration_block(), _final_gate_block()])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(sections), encoding="utf-8")

    rel_output = output_path.relative_to(repo_root)
    print(
        f"Refreshed {SHADOW_DIR.as_posix()}/ from {head_sha} "
        f"({args.package_dir}) and wrote {len(source_paths)} prompts to "
        f"{rel_output.as_posix()}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
