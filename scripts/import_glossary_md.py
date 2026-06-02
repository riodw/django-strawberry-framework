"""Import ``docs/GLOSSARY.md`` and spec term CSVs into the glossary app.

This is the bootstrap bridge from the historical markdown source to the new
database-backed glossary. After import, ``scripts/build_glossary_md.py`` can
regenerate the markdown export from the DB.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FAKESHOP_ROOT = REPO_ROOT / "examples" / "fakeshop"
DEFAULT_GLOSSARY_PATH = REPO_ROOT / "docs" / "GLOSSARY.md"
LINK_DEFINITIONS_DELIMITER = "<!-- LINK DEFINITIONS -->"
H2_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
STATUS_PATTERN = re.compile(r"^\*\*Status:\*\*\s*(?P<status>.+?)\s*$", re.MULTILINE)
SEE_ALSO_PATTERN = re.compile(r"^\*\*See also:\*\*\s*(?P<links>.+?)\s*$", re.MULTILINE)
INLINE_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
INDEX_ROW_PATTERN = re.compile(r"^\| .+?\]\(#(?P<anchor>[^)]+)\) \| (?P<status>.*?) \|$")
CATEGORY_LINE_PATTERN = re.compile(r"^- \*\*(?P<label>.+?):\*\*\s+(?P<links>.+)$")
REFERENCE_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(#([^)]+)\)")


@dataclass(frozen=True)
class Section:
    """One H2 section parsed out of the glossary markdown."""

    heading: str
    body: str
    order: int


@dataclass(frozen=True)
class ParsedTerm:
    """A glossary term parsed from a markdown H2 entry."""

    heading: str
    anchor: str
    status_text: str
    body: str
    see_also: tuple[tuple[str, str], ...]
    source_links: tuple[tuple[str, str, str], ...]
    entry_order: int


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Import docs/GLOSSARY.md into the fakeshop DB.")
    parser.add_argument(
        "--glossary",
        type=Path,
        default=DEFAULT_GLOSSARY_PATH,
        help="Markdown glossary to import. Defaults to docs/GLOSSARY.md.",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Do not clear glossary tables before importing.",
    )
    return parser.parse_args()


def configure_django() -> None:
    """Load fakeshop Django settings for direct ORM writes."""
    sys.path.insert(0, str(FAKESHOP_ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django

    django.setup()


def github_anchor(heading: str) -> str:
    """Approximate GitHub's H2 auto-anchor slugger for glossary headings."""
    text = heading.replace("`", "").lower()
    text = re.sub(r"[^\w\s\-]", "", text)
    return re.sub(r"\s+", "-", text.strip())


def plain_label(value: str) -> str:
    """Return display text stripped of markdown code ticks."""
    return value.replace("`", "").strip()


def normalized_alias(value: str) -> str:
    """Normalize an alias for equality checks."""
    text = plain_label(value).lower()
    text = re.sub(r"[^a-z0-9_]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def status_key(status_text: str) -> str:
    """Map the prose status text to a stable lookup key."""
    lowered = status_text.lower()
    if lowered.startswith("shipped"):
        return "shipped"
    if lowered.startswith("planned"):
        return "planned"
    if lowered.startswith("deferred"):
        return "deferred"
    if lowered.startswith("alpha constraint"):
        return "alpha-constraint"
    if lowered.startswith("post-1.0.0"):
        return "post-1-0-0"
    return "other"


def status_label(key: str) -> str:
    """Return a human label for ``key``."""
    return {
        "shipped": "Shipped",
        "planned": "Planned",
        "deferred": "Deferred",
        "alpha-constraint": "Alpha constraint",
        "post-1-0-0": "Post-1.0.0",
        "other": "Other",
    }[key]


def split_link_definitions(text: str) -> tuple[str, str]:
    """Split the markdown body from the bottom link-definition block."""
    if LINK_DEFINITIONS_DELIMITER not in text:
        return text.rstrip(), ""
    main, link_definitions = text.split(LINK_DEFINITIONS_DELIMITER, 1)
    return main.rstrip(), f"{LINK_DEFINITIONS_DELIMITER}{link_definitions}".strip()


def parse_sections(markdown: str) -> tuple[str, list[Section], str]:
    """Return ``(preamble, h2_sections, link_definitions)``."""
    main, link_definitions = split_link_definitions(markdown)
    matches = list(H2_PATTERN.finditer(main))
    if not matches:
        return main.strip(), [], link_definitions

    preamble = main[: matches[0].start()].strip()
    sections = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(main)
        sections.append(
            Section(
                heading=match.group(1).strip(),
                body=main[match.end() : end].strip(),
                order=index + 1,
            ),
        )
    return preamble, sections, link_definitions


def parse_index_orders(section: Section | None) -> dict[str, int]:
    """Return ``{anchor: index_order}`` from the Index table section."""
    if section is None:
        return {}
    orders = {}
    for line in section.body.splitlines():
        match = INDEX_ROW_PATTERN.match(line.strip())
        if match:
            orders[match.group("anchor")] = len(orders) + 1
    return orders


def parse_see_also(body: str) -> tuple[str, tuple[tuple[str, str], ...]]:
    """Remove and parse the terminal ``See also`` line from a term body."""
    match = SEE_ALSO_PATTERN.search(body)
    if match is None:
        return body.strip(), ()

    links = tuple(
        (label, anchor)
        for label, anchor in REFERENCE_LINK_PATTERN.findall(match.group("links"))
        if anchor
    )
    cleaned = f"{body[: match.start()].rstrip()}\n{body[match.end() :].lstrip()}".strip()
    return cleaned, links


def source_link_kind(target: str) -> str:
    """Classify a non-glossary markdown link target."""
    if target.startswith("http://") or target.startswith("https://"):
        return "external"
    if target.startswith("#"):
        return "glossary"
    return "repo"


def parse_source_links(body: str) -> tuple[tuple[str, str, str], ...]:
    """Return non-glossary links embedded in a term body."""
    links = []
    for label, target in INLINE_LINK_PATTERN.findall(body):
        kind = source_link_kind(target)
        if kind == "glossary":
            continue
        links.append((label, target, kind))
    return tuple(links)


def parse_term(section: Section) -> ParsedTerm | None:
    """Parse ``section`` as a glossary term, or return ``None`` for prose sections."""
    status_match = STATUS_PATTERN.search(section.body)
    if status_match is None:
        return None

    status_text = status_match.group("status").strip()
    if status_text.endswith("."):
        status_text = status_text[:-1]
    body = section.body[status_match.end() :].strip()
    _body_without_see_also, see_also = parse_see_also(body)
    return ParsedTerm(
        heading=section.heading,
        anchor=github_anchor(section.heading),
        status_text=status_text,
        body=body,
        see_also=see_also,
        source_links=parse_source_links(body),
        entry_order=section.order,
    )


def parse_categories(section: Section | None) -> list[tuple[str, list[tuple[str, str]]]]:
    """Return category labels and ordered term-anchor memberships."""
    if section is None:
        return []

    categories = []
    for line in section.body.splitlines():
        match = CATEGORY_LINE_PATTERN.match(line.strip())
        if match is None:
            continue
        categories.append(
            (
                match.group("label"),
                [
                    (label, anchor)
                    for label, anchor in REFERENCE_LINK_PATTERN.findall(match.group("links"))
                ],
            ),
        )
    return categories


def spec_csv_paths() -> list[Path]:
    """Return every committed spec terms CSV path."""
    return sorted(
        [
            *REPO_ROOT.glob("docs/spec-*-terms.csv"),
            *REPO_ROOT.glob("docs/SPECS/spec-*-terms.csv"),
        ],
    )


def spec_path_for_csv(csv_path: Path) -> str:
    """Return the markdown spec path paired with ``csv_path``."""
    spec_name = f"{csv_path.name.removesuffix('-terms.csv')}.md"
    return csv_path.with_name(spec_name).relative_to(REPO_ROOT).as_posix()


def clear_glossary_data(models) -> None:
    """Clear glossary tables in dependency order."""
    for model in (
        models.GlossarySourceLink,
        models.GlossarySpecMention,
        models.GlossaryCategoryMembership,
        models.GlossaryTermLink,
        models.GlossaryAlias,
        models.GlossaryDocument,
        models.GlossaryTerm,
        models.GlossaryTermLinkKind,
        models.GlossaryCategory,
        models.GlossaryStatus,
    ):
        model.objects.all().delete()


def create_statuses(models, parsed_terms: list[ParsedTerm]) -> dict[str, object]:
    """Create and return status lookup rows."""
    order = {
        "shipped": 0,
        "planned": 1,
        "deferred": 2,
        "alpha-constraint": 3,
        "post-1-0-0": 4,
        "other": 5,
    }
    keys = {status_key(term.status_text) for term in parsed_terms}
    statuses = {}
    for key in sorted(keys, key=lambda value: order[value]):
        status, _created = models.GlossaryStatus.objects.get_or_create(
            key=key,
            defaults={
                "label": status_label(key),
                "order": order[key],
            },
        )
        statuses[key] = status
    return statuses


def create_documents(models, preamble: str, sections: list[Section], link_definitions: str) -> int:
    """Create non-term document rows and return their count."""
    count = 0
    if preamble:
        models.GlossaryDocument.objects.create(
            key="preamble",
            title="",
            order=0,
            body=preamble,
            include_heading=False,
        )
        count += 1

    for section in sections:
        if parse_term(section) is not None or section.heading in {"Index", "Browse by category"}:
            continue
        models.GlossaryDocument.objects.create(
            key=github_anchor(section.heading),
            title=section.heading,
            order=section.order,
            body=section.body,
            include_heading=True,
        )
        count += 1

    if link_definitions:
        models.GlossaryDocument.objects.create(
            key="link-definitions",
            title="",
            order=10_000,
            body=link_definitions,
            include_heading=False,
        )
        count += 1
    return count


def create_terms(
    models, parsed_terms: list[ParsedTerm], index_orders: dict[str, int],
) -> dict[str, object]:
    """Create terms and return ``{anchor: term}``."""
    statuses = create_statuses(models, parsed_terms)
    terms = {}
    for term in parsed_terms:
        db_term = models.GlossaryTerm.objects.create(
            title=term.heading,
            title_sort=plain_label(term.heading).lower(),
            anchor=term.anchor,
            status=statuses[status_key(term.status_text)],
            status_text=term.status_text,
            body=term.body,
            entry_order=term.entry_order,
            index_order=index_orders.get(term.anchor, term.entry_order),
        )
        terms[term.anchor] = db_term
        aliases = {term.heading, plain_label(term.heading), term.anchor}
        if plain_label(term.heading).endswith(" scalar"):
            aliases.add(plain_label(term.heading).removesuffix(" scalar"))
        for label in sorted(aliases):
            normalized = normalized_alias(label)
            if normalized:
                models.GlossaryAlias.objects.get_or_create(
                    term=db_term,
                    normalized=normalized,
                    defaults={"label": label},
                )
    return terms


def create_term_links(
    models, parsed_terms: list[ParsedTerm], terms_by_anchor: dict[str, object],
) -> int:
    """Create normalized term-to-term links."""
    see_also, _created = models.GlossaryTermLinkKind.objects.get_or_create(
        key="see-also",
        defaults={"label": "See also", "order": 0},
    )
    count = 0
    for parsed in parsed_terms:
        source_term = terms_by_anchor[parsed.anchor]
        for order, (label, anchor) in enumerate(parsed.see_also):
            target_term = terms_by_anchor.get(anchor)
            if target_term is None:
                continue
            models.GlossaryTermLink.objects.create(
                source_term=source_term,
                target_term=target_term,
                kind=see_also,
                raw_label=label,
                order=order,
            )
            count += 1
    return count


def create_source_links(
    models, parsed_terms: list[ParsedTerm], terms_by_anchor: dict[str, object],
) -> int:
    """Create non-glossary source links from term bodies."""
    count = 0
    for parsed in parsed_terms:
        term = terms_by_anchor[parsed.anchor]
        for order, (label, target, kind) in enumerate(parsed.source_links):
            models.GlossarySourceLink.objects.create(
                term=term,
                label=label,
                target=target,
                kind=kind,
                order=order,
            )
            count += 1
    return count


def create_categories(
    models,
    categories: list[tuple[str, list[tuple[str, str]]]],
    terms_by_anchor: dict[str, object],
) -> int:
    """Create browse categories and ordered term memberships."""
    count = 0
    for category_order, (label, links) in enumerate(categories):
        category = models.GlossaryCategory.objects.create(
            key=github_anchor(label),
            label=label,
            order=category_order,
        )
        for term_order, (_label, anchor) in enumerate(links):
            term = terms_by_anchor.get(anchor)
            if term is None:
                continue
            models.GlossaryCategoryMembership.objects.create(
                category=category,
                term=term,
                order=term_order,
            )
            count += 1
    return count


def create_spec_mentions(models, terms_by_anchor: dict[str, object]) -> int:
    """Create spec mention rows from every spec terms CSV."""
    count = 0
    seen: set[tuple[str, str]] = set()
    for csv_path in spec_csv_paths():
        spec_path = spec_path_for_csv(csv_path)
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for order, row in enumerate(reader):
                anchor = (row.get("anchor") or "").strip()
                term = terms_by_anchor.get(anchor)
                if term is None:
                    continue
                key = (spec_path, anchor)
                if key in seen:
                    continue
                seen.add(key)
                models.GlossarySpecMention.objects.create(
                    term=term,
                    spec_path=spec_path,
                    term_text=(row.get("term") or "").strip(),
                    notes=(row.get("notes") or "").strip(),
                    order=order,
                )
                count += 1
    return count


def import_glossary(glossary_path: Path, *, keep_existing: bool) -> None:
    """Import markdown glossary data into the app tables."""
    from apps.glossary import models
    from django.db import transaction

    markdown = glossary_path.read_text(encoding="utf-8")
    preamble, sections, link_definitions = parse_sections(markdown)
    section_by_heading = {section.heading: section for section in sections}
    parsed_terms = [term for section in sections if (term := parse_term(section)) is not None]

    with transaction.atomic():
        if not keep_existing:
            clear_glossary_data(models)
        document_count = create_documents(models, preamble, sections, link_definitions)
        terms_by_anchor = create_terms(
            models,
            parsed_terms,
            parse_index_orders(section_by_heading.get("Index")),
        )
        link_count = create_term_links(models, parsed_terms, terms_by_anchor)
        source_link_count = create_source_links(models, parsed_terms, terms_by_anchor)
        membership_count = create_categories(
            models,
            parse_categories(section_by_heading.get("Browse by category")),
            terms_by_anchor,
        )
        mention_count = create_spec_mentions(models, terms_by_anchor)

    print(
        "Imported "
        f"{len(parsed_terms)} terms, "
        f"{document_count} docs, "
        f"{membership_count} category memberships, "
        f"{link_count} term links, "
        f"{source_link_count} source links, and "
        f"{mention_count} spec mentions.",
    )


def main() -> None:
    """Run the importer."""
    args = parse_args()
    configure_django()
    import_glossary(args.glossary, keep_existing=args.keep_existing)


if __name__ == "__main__":
    main()
