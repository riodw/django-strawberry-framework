"""Validate that a spec's project-specific terms are glossary-anchored.

Two checks per term in the spec's companion ``*-terms.csv``:

1. ``docs/FEATURES.md`` has a ``## <heading>`` whose GitHub auto-anchor
   matches the term's ``anchor`` column.
2. The spec markdown contains at least one ``](...FEATURES.md#<anchor>)``
   link pointing to that anchor.

Exits 0 when every term passes both checks, 1 when any term fails, and 2
on a CLI / file-not-found error.

Usage::

    uv run python scripts/check_spec_glossary.py \\
        --spec docs/spec-014-meta_primary-0_0_6.md \\
        --terms docs/spec-014-meta_primary-0_0_6-terms.csv \\
        --features docs/FEATURES.md \\
        --auto-link

Only ``--spec`` is required. ``--terms`` defaults to the spec path with
``-terms.csv`` appended to the stem (e.g.
``docs/spec-014-meta_primary-0_0_6.md`` →
``docs/spec-014-meta_primary-0_0_6-terms.csv``). ``--features``
defaults to ``docs/FEATURES.md`` and accepts an override for testing or
for validating against a fork's renamed glossary.

Pass ``--auto-link`` to also rewrite the spec in place: for every term
listed as missing a link, the script finds the first prose mention
outside fenced code blocks and existing links, and wraps it as a
``[term](FEATURES.md#anchor)`` reference. The backtick-wrapped form is
preferred when the spec already says e.g. ``Meta.fields`` in inline
code — the rewrite becomes ``[Meta.fields](FEATURES.md#metafields)``
with the inline-code backticks preserved inside the link label. The
run is idempotent: a second pass is a no-op once every term has at
least one link.

The CSV is the source of truth: trim it when a term does not warrant a
glossary entry, extend it when a new term needs one.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

HEADING_PATTERN = re.compile(r"^##\s+(.+?)\s*$")
LINK_PATTERN = re.compile(r"\]\([^)]*FEATURES\.md#([^)]+)\)")
FENCE_PATTERN = re.compile(r"^```", re.MULTILINE)
EXISTING_LINK_PATTERN = re.compile(r"\[[^\]]*\]\([^)]*\)")


def github_anchor(heading: str) -> str:
    """Approximate GitHub's H2 auto-anchor slugger for ``docs/FEATURES.md``.

    Drops backticks, lowercases, strips non-word characters other than
    whitespace and hyphens, then collapses whitespace runs to single
    hyphens. Underscores and existing hyphens are preserved. Matches the
    anchor form GitHub renders for headings like ``## `Meta.primary``` →
    ``metaprimary`` and ``## Relation handling`` → ``relation-handling``.
    """
    text = heading.replace("`", "").lower()
    text = re.sub(r"[^\w\s\-]", "", text)
    return re.sub(r"\s+", "-", text.strip())


def load_terms(csv_path: Path) -> list[tuple[str, str]]:
    """Return ``[(term, anchor), ...]`` from the terms CSV.

    Rows missing either column are silently skipped — the CSV uses a
    header row (``term,anchor,notes``); blanks in the body are tolerated
    so the file can carry trailing-comma whitespace from spreadsheet
    exports without confusing the checker.
    """
    rows: list[tuple[str, str]] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            term = (row.get("term") or "").strip()
            anchor = (row.get("anchor") or "").strip()
            if term and anchor:
                rows.append((term, anchor))
    return rows


def features_anchors(features_path: Path) -> dict[str, str]:
    """Return ``{anchor: heading_text}`` for every H2 in ``FEATURES.md``."""
    anchors: dict[str, str] = {}
    with features_path.open(encoding="utf-8") as handle:
        for line in handle:
            match = HEADING_PATTERN.match(line)
            if match:
                heading = match.group(1).strip()
                anchors[github_anchor(heading)] = heading
    return anchors


def spec_link_anchors(spec_path: Path) -> set[str]:
    """Return the set of ``FEATURES.md`` anchors linked from the spec."""
    text = spec_path.read_text(encoding="utf-8")
    return {match.group(1) for match in LINK_PATTERN.finditer(text)}


def check_terms(
    terms: list[tuple[str, str]],
    features_index: dict[str, str],
    spec_anchors: set[str],
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Return ``(missing_glossary, missing_links)`` lists of ``(term, anchor)``."""
    missing_glossary: list[tuple[str, str]] = []
    missing_links: list[tuple[str, str]] = []
    for term, anchor in terms:
        if anchor not in features_index:
            missing_glossary.append((term, anchor))
        if anchor not in spec_anchors:
            missing_links.append((term, anchor))
    return missing_glossary, missing_links


def _fenced_code_ranges(text: str) -> list[tuple[int, int]]:
    """Return ``(start, end)`` byte ranges covering every fenced code block.

    Toggles on each ``^```` line — odd matches open a block, even matches
    close it. An unterminated fence at end-of-file extends to the end of
    the document, which is the safe default (we would rather skip than
    rewrite into a malformed block).
    """
    ranges: list[tuple[int, int]] = []
    in_block = False
    start = 0
    for match in FENCE_PATTERN.finditer(text):
        if not in_block:
            start = match.start()
            in_block = True
        else:
            ranges.append((start, match.end()))
            in_block = False
    if in_block:
        ranges.append((start, len(text)))
    return ranges


def _existing_link_ranges(text: str) -> list[tuple[int, int]]:
    """Return ``(start, end)`` ranges for every existing ``[label](target)`` link."""
    return [(m.start(), m.end()) for m in EXISTING_LINK_PATTERN.finditer(text)]


def _is_inside(position: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in ranges)


def _find_first_outside(
    text: str,
    needle: str,
    *exclusion_ranges: list[tuple[int, int]],
) -> int | None:
    """Find the first occurrence of ``needle`` outside every excluded range."""
    cursor = 0
    while True:
        position = text.find(needle, cursor)
        if position < 0:
            return None
        if not any(_is_inside(position, ranges) for ranges in exclusion_ranges):
            return position
        cursor = position + 1


def auto_link_terms(
    spec_path: Path,
    missing_links: list[tuple[str, str]],
) -> tuple[list[str], list[str]]:
    """Insert ``](FEATURES.md#anchor)`` links at the first valid mention of each term.

    For each ``(term, anchor)`` in ``missing_links``:

    1. Locate the first backtick-wrapped occurrence of the term that is
       not inside a fenced code block or an existing link, and wrap it
       as ``[backtick-term](FEATURES.md#anchor)`` so the inline-code
       formatting survives inside the link label.
    2. If the backtick-wrapped form is absent, look for the plain prose
       form under the same exclusion rules and wrap it as
       ``[term](FEATURES.md#anchor)``.

    The spec file is re-read between terms so each replacement sees a
    fresh code-block / link map (cheap for spec-sized files, avoids the
    range-shifting bookkeeping after an edit).

    Returns ``(linked, skipped)`` — both lists of term names. ``skipped``
    contains terms for which no valid prose occurrence was found.
    """
    linked: list[str] = []
    skipped: list[str] = []
    for term, anchor in missing_links:
        text = spec_path.read_text(encoding="utf-8")
        code_ranges = _fenced_code_ranges(text)
        link_ranges = _existing_link_ranges(text)

        backtick = f"`{term}`"
        position = _find_first_outside(text, backtick, code_ranges, link_ranges)
        if position is not None:
            replacement = f"[`{term}`](FEATURES.md#{anchor})"
            text = text[:position] + replacement + text[position + len(backtick) :]
            spec_path.write_text(text, encoding="utf-8")
            linked.append(term)
            continue

        position = _find_first_outside(text, term, code_ranges, link_ranges)
        if position is not None:
            replacement = f"[{term}](FEATURES.md#{anchor})"
            text = text[:position] + replacement + text[position + len(term) :]
            spec_path.write_text(text, encoding="utf-8")
            linked.append(term)
            continue

        skipped.append(term)
    return linked, skipped


def _print_section(title: str, entries: list[tuple[str, str]], hint: str) -> None:
    print(title)
    for term, anchor in entries:
        print(f"  - {term} (anchor: {anchor}) — {hint.format(anchor=anchor)}")
    print()


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--spec", required=True, type=Path, help="Path to the spec markdown file.")
    parser.add_argument(
        "--terms",
        type=Path,
        default=None,
        help=(
            "Path to the spec's companion `*-terms.csv` (columns: term, anchor, notes). "
            "Defaults to `<spec-stem>-terms.csv` alongside the spec."
        ),
    )
    parser.add_argument(
        "--features",
        type=Path,
        default=Path("docs/FEATURES.md"),
        help="Path to the glossary (default: docs/FEATURES.md).",
    )
    parser.add_argument(
        "--auto-link",
        action="store_true",
        help=(
            "Rewrite the spec in place: for each term in the missing-link list, "
            "wrap the first non-code, non-link occurrence as "
            "[term](FEATURES.md#anchor). Idempotent."
        ),
    )
    return parser.parse_args(argv)


def _default_terms_path(spec_path: Path) -> Path:
    """Derive ``<spec-stem>-terms.csv`` alongside the spec when ``--terms`` is omitted."""
    return spec_path.with_name(f"{spec_path.stem}-terms.csv")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.terms is None:
        args.terms = _default_terms_path(args.spec)

    for path in (args.spec, args.terms, args.features):
        if not path.exists():
            print(f"error: missing file: {path}", file=sys.stderr)
            return 2

    terms = load_terms(args.terms)
    if not terms:
        print(f"error: no terms loaded from {args.terms}", file=sys.stderr)
        return 2

    features_index = features_anchors(args.features)
    spec_anchors = spec_link_anchors(args.spec)
    missing_glossary, missing_links = check_terms(terms, features_index, spec_anchors)

    if args.auto_link and missing_links:
        linked, skipped = auto_link_terms(args.spec, missing_links)
        if linked:
            print(f"auto-link: inserted {len(linked)} link(s) into {args.spec}:")
            for term in linked:
                print(f"  + {term}")
        if skipped:
            print(
                f"auto-link: {len(skipped)} term(s) had no plain prose mention "
                "outside code blocks / existing links:",
            )
            for term in skipped:
                print(f"  - {term}")
        if linked or skipped:
            print()
        # Re-read spec so the post-rewrite missing-link list is accurate.
        spec_anchors = spec_link_anchors(args.spec)
        missing_glossary, missing_links = check_terms(terms, features_index, spec_anchors)

    if missing_glossary:
        _print_section(
            f"Missing glossary entries in {args.features}:",
            missing_glossary,
            "add `## <heading>` whose slug is `{anchor}`",
        )
    if missing_links:
        _print_section(
            f"Spec terms missing a link to {args.features.name}:",
            missing_links,
            "add at least one `](FEATURES.md#{anchor})` reference",
        )

    if missing_glossary or missing_links:
        return 1

    print(f"OK: {len(terms)} terms — all have glossary entries and at least one spec link.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
