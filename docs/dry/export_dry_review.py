"""Export DRY analysis sections from .md artifacts into a DRY-cycle plan.

Scans every ``*.md`` file in a source directory, extracts each file's
``DRY analysis`` heading section (any ATX heading level), prefixes every
top-level bullet with ``- [ ]``, and writes ``docs/dry/dry-<release>.md``
for Worker 0 to drive the DRY-consolidation workflow (see
``docs/dry/DRY.md``).

The extractor is code-fence-aware so template snippets inside fenced blocks
(in ``BUILD.md`` / ``REVIEW.md`` / worker role docs) are not mistaken for
real findings.
"""

from __future__ import annotations

import argparse
import datetime
import re
from pathlib import Path

VERSION_SUFFIX_PATTERN = re.compile(r"-(\d+(?:_\d+)+)\.md$")


def _compute_fence_mask(lines: list[str]) -> list[bool]:
    """Return ``mask[i] = True`` when ``lines[i]`` is inside a fenced code block.

    Handles 3+ backtick fences. A fence is closed by a marker with at least as
    many backticks as the opener. The fence-marker lines themselves are
    considered structural (``False``).
    """
    mask = [False] * len(lines)
    in_fence = False
    fence_len = 0
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        n = 0
        while n < len(stripped) and stripped[n] == "`":
            n += 1
        if n >= 3:
            if not in_fence:
                in_fence = True
                fence_len = n
            elif n >= fence_len:
                in_fence = False
                fence_len = 0
            mask[i] = False
        else:
            mask[i] = in_fence
    return mask


def _heading_level(line: str) -> tuple[int, str] | None:
    """Return ``(level, body)`` if the line is an ATX Markdown heading, else ``None``."""
    stripped = line.lstrip()
    if not stripped.startswith("#"):
        return None
    n = 0
    while n < len(stripped) and stripped[n] == "#":
        n += 1
    if n == 0 or n >= len(stripped) or stripped[n] != " ":
        return None
    return n, stripped[n + 1 :].rstrip()


def _extract_dry(path: Path) -> tuple[str, list[str]] | None:
    """Return ``(title, dry_lines)`` for the file's DRY analysis section, or ``None``.

    The title is the file's first H1 outside any code fence (falling back to
    the file name). The DRY analysis section is everything between a heading
    whose body is exactly ``DRY analysis`` and the next heading at the same
    or higher level, code-fence-aware on both ends. Top-level bullets in the
    extracted content are prefixed ``- [ ]`` so Worker 0 can tick them.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    fence_mask = _compute_fence_mask(lines)

    title: str | None = None
    for i, line in enumerate(lines):
        if fence_mask[i]:
            continue
        match = _heading_level(line)
        if match is not None and match[0] == 1:
            title = match[1]
            break
    if title is None:
        title = path.name

    dry_index: int | None = None
    dry_level: int | None = None
    for i, line in enumerate(lines):
        if fence_mask[i]:
            continue
        match = _heading_level(line)
        if match is None:
            continue
        level, body = match
        if body == "DRY analysis":
            dry_index = i
            dry_level = level
            break
    if dry_index is None or dry_level is None:
        return None

    end_index = len(lines)
    for i in range(dry_index + 1, len(lines)):
        if fence_mask[i]:
            continue
        match = _heading_level(lines[i])
        if match is None:
            continue
        if match[0] <= dry_level:
            end_index = i
            break

    content = lines[dry_index + 1 : end_index]
    while content and not content[0].strip():
        content.pop(0)
    while content and not content[-1].strip():
        content.pop()

    transformed: list[str] = []
    for line in content:
        if line.startswith("- ") and not line.startswith(("- [ ]", "- [x]")):
            line = "- [ ] " + line[2:]
        transformed.append(line)

    return title, transformed


def export_dry_plan(
    source_dir: Path,
    output: Path,
    *,
    target_release: str | None = None,
) -> list[Path]:
    """Write the DRY-cycle plan to ``output`` and return files skipped (no DRY section)."""
    artifacts = sorted(source_dir.glob("*.md"))
    blocks: list[str] = []
    skipped: list[Path] = []
    for artifact in artifacts:
        result = _extract_dry(artifact)
        if result is None:
            skipped.append(artifact)
            continue
        title, dry_lines = result
        body = "\n".join(dry_lines) if dry_lines else "- [ ] (no DRY bullets recorded)"
        block = f"## {title}\n\n_Source: `{artifact.as_posix()}`_\n\n{body}"
        blocks.append(block)

    today = datetime.date.today().isoformat()
    title_suffix = f": {target_release}" if target_release else ""
    header = (
        f"# DRY consolidation plan{title_suffix}\n\n"
        f"Source: `{source_dir.as_posix()}/`\n"
        f"Generated: {today}\n"
        f"Workflow: `docs/dry/DRY.md`\n\n"
        "One finding at a time. Worker 0 dispatches > Worker 1 triages > "
        "Worker 2 implements > Worker 1 verifies > Worker 0 ticks.\n\n"
        "## Findings\n\n"
    )

    if blocks:
        body = "\n\n---\n\n".join(blocks) + "\n"
    else:
        body = "_No DRY analysis sections found in the source directory._\n"

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(header + body, encoding="utf-8")
    return skipped


def _default_output(target_release: str) -> Path:
    """Return ``docs/dry/dry-<release-underscored>.md`` for the given release."""
    return Path(f"docs/dry/dry-{target_release.replace('.', '_')}.md")


def _infer_target_release(source_dir: Path) -> str:
    """Infer the target release from a versioned ``*-X_X_X.md`` file in ``source_dir``.

    Scans every ``.md`` file in ``source_dir`` for a trailing ``-<digits>(_<digits>)+``
    suffix before ``.md`` (matches ``review-0_0_5.md``, ``build-014-foo-0_0_6.md``,
    etc.). Returns the version in dotted form (``0.0.5``, ``0.0.6``). Raises
    ``SystemExit`` if no version-suffixed file exists, or if multiple distinct
    versions are present (the caller must pass ``--target-release`` to disambiguate).
    """
    versions: set[str] = set()
    for path in source_dir.glob("*.md"):
        match = VERSION_SUFFIX_PATTERN.search(path.name)
        if match:
            versions.add(match.group(1))
    if not versions:
        raise SystemExit(
            f"error: could not infer --target-release: no .md file in {source_dir.as_posix()}/ "
            "matches the version-suffix pattern '*-X_X_X.md' (e.g. 'review-0_0_5.md' or "
            "'build-014-foo-0_0_6.md'). Pass --target-release explicitly or add a versioned plan file.",
        )
    if len(versions) > 1:
        listed = ", ".join(sorted(versions))
        raise SystemExit(
            f"error: could not infer --target-release: multiple distinct versions found in "
            f"{source_dir.as_posix()}/: {listed}. Pass --target-release explicitly.",
        )
    return next(iter(versions)).replace("_", ".")


def main() -> None:
    """Parse CLI args and emit the DRY consolidation plan."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate a DRY consolidation plan from every *.md file in a source directory. "
            "Used as Worker 0's first step in the docs/dry/DRY.md workflow."
        ),
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        required=True,
        help="Directory containing .md files to scan (e.g. docs/builder or docs/review).",
    )
    parser.add_argument(
        "--target-release",
        type=str,
        default=None,
        help=(
            "Target package release (e.g. '0.0.6'). When omitted, inferred from the "
            "unique '*-X_X_X.md' file in --source-dir (e.g. 'review-0_0_5.md' or "
            "'build-014-foo-0_0_6.md'). Required if zero or multiple version-suffixed "
            "files are present."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Output Markdown file. Defaults to docs/dry/dry-<release-underscored>.md "
            "when --target-release is provided."
        ),
    )
    args = parser.parse_args()

    if not args.source_dir.is_dir():
        raise SystemExit(
            f"error: --source-dir {args.source_dir.as_posix()} is not a directory "
            "(expected docs/builder or docs/review).",
        )

    target_release = args.target_release
    if target_release is None:
        target_release = _infer_target_release(args.source_dir)
        print(f"Inferred --target-release: {target_release}")

    output = args.output if args.output is not None else _default_output(target_release)

    skipped = export_dry_plan(args.source_dir, output, target_release=target_release)
    print(f"Wrote {output}")
    if skipped:
        skipped_names = ", ".join(path.name for path in skipped)
        print(f"Skipped files without a DRY analysis section: {skipped_names}")


if __name__ == "__main__":
    main()
