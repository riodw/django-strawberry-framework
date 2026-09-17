"""Generate the autonomous release-scoped bug-hunt progress file.

The script resolves the current branch's HEAD commit hash, refreshes
the snapshot helper's ``docs/shadow/current/`` folder in-process via
``review_historical_package_snapshot_at_commit.main([<head-sha>])``
(the output location is imported as ``SHADOW_DIR`` so it cannot drift
from the snapshot helper), reads the passed-in dicta (default
``docs/bug_hunt/dicta.md``), inventories the live package, and writes a
progress header carrying the run id, the cycle baseline (``git status
--short`` at generation, every listed path being concurrent work), the
static hunt brief, one checkbox per live non-``__init__.py`` Python file,
the standing cross-file scenario items, a package-integration item, the
final test gate, and the empty owned-changes ledger and outcomes sections
that Worker 0 fills. Matching shadows are optional baseline aids for the
live files. The method itself lives in ``docs/bug_hunt/HUNT.md``.

The output path defaults to ``docs/bug_hunt/bug_hunt-<release>.md``, where
``<release>`` is the package ``__version__`` in
``django_strawberry_framework/__init__.py`` (dots become underscores) -- the
single version source, from which hatchling also derives packaging metadata.
This matches the review and DRY agentflow progress-file naming;
``--target-release`` overrides the version.
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
_INIT_VERSION_PATTERN = re.compile(
    r"""(?m)^__version__\s*=\s*(?P<quote>["'])(?P<version>[^"']+)(?P=quote)\s*(?:#.*)?$""",
)

# Fallback dicta used when ``--dicta`` points at a missing or question-less file.
_FALLBACK_DICTA = (
    "## Package questions\n\n"
    "No maintainer-authored probing questions were supplied. Explore the live source freely; "
    "shadow inputs are orientation only.\n"
)

# Static boilerplate summarizing the method; ``docs/bug_hunt/HUNT.md`` is canonical.
_HOW_TO_HUNT_ONE_ITEM = """## How to hunt one item
Each file item uses one source file as its entry point into the live system;
scenario items own one cross-file contract. The target is narrow; the
investigation and root-cause fix cross files. `docs/bug_hunt/HUNT.md` is the
method; this brief is a reminder, not a substitute.

- Read the shadow overview and stripped source for baseline orientation, then
  read the complete live target. Shadow markers and stripped line numbers are
  never authoritative.
- Record the contract row for every boundary before probing it: boundary,
  failure class, promised wire shape, masking, rollback, absent unauthorized
  effects. A contract nobody can cite is reported blocked, never fixed.
- Trace callers, dependencies, state, framework hooks, tests, examples, and
  public contracts far enough to understand the target's real behavior. Clean
  layers often fail only when several reasonable assumptions stack together;
  hunt those interactions, not only suspicious local lines.
- Break things, break things, break things, inside the disposable workspace
  copy only: mutate throwaway state, force hostile sequences, interrupt
  lifecycles, and try to make every connected layer fail. A probe that imports
  the shared checkout or opens its database is invalid whatever it found.
- For every extreme, test the opposite extreme and then combine them across
  layers. Discharge every axis of the mandatory matrix. Try to disprove every
  candidate and record only confirmed defects.
- Every claim links to an evidence record: workspace path, imported package
  path, database target, exact command, source digests, collected and executed
  counts, the assertion proving the boundary was reached, a positive control.
- Do not clean up scratch probes, workspaces, or disposable state. Report every
  path and leave it intact so Worker 2 can replay it and Worker 0 can remove it
  only after the item is verified.
- Implement the root-cause fix at the layer that owns the broken invariant in
  the shared tree, attributing every hunk of a dirty path first, including
  connected files when required. Add a permanent behavioral test for every
  production fix at the strongest tier required by `AGENTS.md`.
- After edits run `uv run ruff format .` and `uv run ruff check --fix .`.
- Report evidence, changed files, tests, and validation to Worker 0. Do not edit
  this progress file; Worker 0 runs the mechanical checks, a fresh Worker 2
  verifies, and Worker 0 advances it.

## Hunt items
"""

# Standing cross-file contracts the per-file sweep structurally misses.
_SCENARIOS = (
    (
        "Pagination window semantics",
        "connection.py, keyset.py, relay.py: cursor round trips fix schema, order and key "
        "context; first/last/after/before algebra; a bigger document never charges less on a "
        "named charge dimension.",
    ),
    (
        "Authorization and visibility across actors",
        "utils/querysets.py seal, mutations/permissions.py, resource_policy.py, "
        "optimizer/_context.py: forbidden rows absent across actor switches, prefetch and "
        "reverse relations, cache reuse across executions, awaitable truthiness, point-in-time "
        "authorization.",
    ),
    (
        "Transaction and session lifecycle under interruption",
        "utils/write_transaction.py, the three write pipelines, consumers.py: locks, rollback, "
        "commit hooks, cancellation, sync_to_async boundaries, failure during failure handling.",
    ),
)


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
    """Return the release from the single version source, the package ``__init__``.

    Hatchling derives packaging metadata from the same ``__version__`` literal
    via ``[tool.hatch.version]``, so there is no second declaration to compare
    against and no mismatch state to police.
    """
    return _init_version(repo_root)


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


def _baseline_python_paths(commit: str, package_dir: str) -> frozenset[str]:
    """Return every ``.py`` path under ``package_dir`` at ``commit``, unfiltered.

    Deliberately *not* the snapshot helper's eligible set: the question this
    answers is "did this file exist at the baseline", which must stay independent
    of whether the snapshot would have rendered it. Read once through
    ``git ls-tree -r`` rather than per-file, so classifying every item costs one
    git call and never consults the working tree.
    """
    return frozenset(
        path
        for path in snapshot._tree_paths_at_commit(commit, package_dir)
        if path.endswith(".py")
    )


def _shadow_inputs(
    repo_root: Path,
    current_dir: Path,
    source: str,
    baseline_paths: frozenset[str],
) -> tuple[Path | None, Path | None]:
    """Return trustworthy repo-relative baseline inputs when both exist.

    Artifact presence cannot establish provenance by itself. A complete stale
    pair must not be attached to a source that did not exist at the baseline or
    whose path the snapshot excludes; incomplete pairs are likewise treated as
    missing so the item reports the unexpected gap.
    """
    if source not in baseline_paths or snapshot.snapshot_excludes(source):
        return None, None
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


def _no_shadow_reason(source: str, baseline_paths: frozenset[str]) -> str:
    """Explain why ``source`` has no baseline shadow.

    Two independent facts produce a missing shadow -- whether the snapshot helper
    would ever render this path, and whether the file existed at the hunt baseline
    -- so both are read rather than inferred from each other. Neither implies the
    other: a path-only answer calls every ``testing/`` file old, and a
    baseline-only answer calls every excluded file new. All four combinations are
    named, including the one that should be unreachable, because a silently-wrong
    orientation line is worse than an admitted gap.
    """
    excluded = snapshot.snapshot_excludes(source)
    existed = source in baseline_paths
    if excluded and existed:
        return "path excluded from the snapshot by its 'test' path filter, not new"
    if excluded:
        return (
            "live file added since the hunt baseline; its path is also excluded by the "
            "snapshot's 'test' filter"
        )
    if not existed:
        return "live file added since the hunt baseline"
    return (
        "file existed at the hunt baseline and is snapshot-eligible, so this shadow is "
        "missing unexpectedly -- treat the snapshot as incomplete"
    )


def _file_block(
    source: str,
    stripped: Path | None,
    overview: Path | None,
    baseline_paths: frozenset[str],
) -> str:
    """Render one checkbox block for a single source file."""
    lines = [f"- [ ] {source}", "    - Status: pending"]
    if stripped is not None and overview is not None:
        lines.extend([f"    - {stripped.as_posix()}", f"    - {overview.as_posix()}"])
        orientation = (
            f"Read {stripped.as_posix()} and {overview.as_posix()} for baseline orientation, then "
        )
    else:
        lines.append(f"    - Baseline shadow: none ({_no_shadow_reason(source, baseline_paths)})")
        orientation = "No baseline shadow exists; "
    prompt = (
        f"Use {source} as the entry point. {orientation}hunt the connected live system and "
        "implement every confirmed root-cause fix."
    )
    lines.extend(["    - Prompt:", f"        - {prompt}"])
    return "\n".join(lines) + "\n"


def _progress_header(commit: str, release: str) -> str:
    """Render the stable metadata for one autonomous hunt, run id included."""
    return (
        f"# Bug hunt: {release}\n\n"
        "Status: in-progress\n"
        "Mode: autonomous\n"
        f"Run id: `{release}-{commit}`\n"
        f"Baseline commit: `{commit}`\n"
    )


def _cycle_baseline_block(status_output: str) -> str:
    """Render the concurrent-work inventory captured at generation time.

    Every path listed here was dirty or untracked before the hunt began, so no
    item may edit, revert, tidy, or claim it. An empty listing is stated rather
    than omitted, so a missing section reads as lost instead of as clean.
    """
    listing = status_output.rstrip("\n")
    body = f"```text\n{listing}\n```\n" if listing else "Clean tree at generation.\n"
    return (
        "## Cycle baseline\n\n"
        "`git status --short` at generation. Every path below is concurrent work: never edited, "
        "reverted, tidied, or attributed to an item. Worker 0 appends the `CYCLE_BASELINE` stash "
        "object once at start and nothing afterwards.\n\n"
        f"{body}"
    )


def _scenarios_block() -> str:
    """Render the standing scenario items; Worker 0 appends discovered ones below them."""
    lines = ["## Scenarios", ""]
    for index, (title, prompt) in enumerate(_SCENARIOS):
        lines.extend(
            [
                *([""] if index else []),
                f"- [ ] Scenario: {title}",
                "    - Status: pending",
                "    - Prompt:",
                f"        - {prompt} Hunt the contract across every entry point; implement "
                "every confirmed root-cause fix.",
            ],
        )
    lines.extend(["", "## Integration and final gate", ""])
    return "\n".join(lines) + "\n"


def _ledger_blocks() -> str:
    """Render the sections Worker 0 fills: the owned-changes ledger and the outcomes."""
    return (
        "## Owned changes\n\n"
        "Path, item, symbols for every tracked edit or new file a verified item landed. A later "
        "item may build on a path listed here; any other dirty hunk is external.\n\n"
        "## Outcomes\n\n"
        "Filled by Worker 0 at closeout before any scratch is removed.\n"
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
    """Render the Worker 0 full-suite gate."""
    return (
        "- [ ] Final test gate\n"
        "    - Status: pending\n"
        "    - Owner: Worker 0\n"
        "    - Prompt:\n"
        "        - Run `uv run pytest`; require a passing suite and 100% configured package "
        "coverage.\n"
    )


def _read_dicta(dicta_path: Path) -> str:
    """Return ``dicta_path`` contents (newline-terminated), else the fallback section.

    An empty dicta is the resting state, not a missing one: the file is
    maintainer-owned and stays in the tree between hunts. Both spellings of "no
    questions" therefore resolve to the fallback, so the progress file always
    carries a ``## Package questions`` heading -- an absent section would read as
    lost rather than as unasked. Whitespace-only counts as empty.
    """
    if dicta_path.is_file():
        text = dicta_path.read_text(encoding="utf-8").removeprefix("\ufeff")
        if text.strip():
            if re.search(r"(?m)^## Package questions[ \t]*$", text) is None:
                text = f"## Package questions\n\n{text.lstrip()}"
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
            f"flows. Defaults to the package version in {PACKAGE_INIT.as_posix()}."
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
    try:
        package_dir = snapshot.normalize_package_dir(repo_root, args.package_dir)
    except ValueError as error:
        print(str(error), file=sys.stderr)
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
    source_paths = _live_python_sources(repo_root, package_dir)
    if not source_paths:
        print(
            f"No live non-init Python files under {package_dir!r}.",
            file=sys.stderr,
        )
        return 2
    baseline_paths = _baseline_python_paths(head_sha, package_dir)
    status_output = _run_git(["status", "--short"])
    try:
        _refresh_historical_package_snapshot(
            head_sha,
            package_dir,
            current_dir,
        )
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1

    sections: list[str] = [
        _progress_header(head_sha, release),
        _cycle_baseline_block(status_output),
        _read_dicta(dicta_path),
        _HOW_TO_HUNT_ONE_ITEM,
    ]
    for source in source_paths:
        stripped, overview = _shadow_inputs(
            repo_root,
            current_dir,
            source,
            baseline_paths,
        )
        sections.append(_file_block(source, stripped, overview, baseline_paths))
    sections.extend(
        [
            _scenarios_block(),
            _integration_block(),
            _final_gate_block(),
            _ledger_blocks(),
        ],
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(sections), encoding="utf-8")

    try:
        display_output = output_path.relative_to(repo_root)
    except ValueError:
        display_output = output_path
    print(
        f"Refreshed {SHADOW_DIR.as_posix()}/ from {head_sha} "
        f"({package_dir}) and wrote {len(source_paths)} prompts to "
        f"{display_output.as_posix()}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
