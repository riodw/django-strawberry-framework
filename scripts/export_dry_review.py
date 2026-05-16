"""Export DRY analysis sections from review artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path


def _artifact_sort_key(path: Path) -> tuple[str, str]:
    """Keep output deterministic across filesystems."""
    return (path.name.count("__") == 0, path.name)


def _dry_block(path: Path) -> str | None:
    """Return artifact content before ``## High:`` when it has a DRY section."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if "## DRY analysis" not in lines:
        return None
    try:
        high_index = lines.index("## High:")
    except ValueError:
        return None
    return "\n".join(lines[:high_index]).rstrip()


def export_dry_review(review_dir: Path, output: Path) -> list[Path]:
    """Write the combined DRY review document and return skipped artifacts."""
    blocks: list[str] = []
    skipped: list[Path] = []
    for artifact in sorted(review_dir.glob("rev-*.md"), key=_artifact_sort_key):
        block = _dry_block(artifact)
        if block is None:
            skipped.append(artifact)
            continue
        blocks.append(block)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n\n---\n\n".join(blocks) + "\n", encoding="utf-8")
    return skipped


def main() -> None:
    """Parse CLI args and export the DRY review document."""
    parser = argparse.ArgumentParser(
        description="Combine DRY analysis sections from docs/review/rev-*.md into docs/DRY.md.",
    )
    parser.add_argument(
        "--review-dir",
        type=Path,
        default=Path("docs/review"),
        help="Directory containing rev-*.md artifacts.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/DRY.md"),
        help="Output Markdown file.",
    )
    args = parser.parse_args()

    skipped = export_dry_review(args.review_dir, args.output)
    print(f"Wrote {args.output}")
    if skipped:
        skipped_names = ", ".join(path.name for path in skipped)
        print(f"Skipped artifacts without DRY/High sections: {skipped_names}")


if __name__ == "__main__":
    main()
