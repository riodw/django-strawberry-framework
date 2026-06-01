"""Build ``KANBAN.md`` from the shared kanban dashboard payload."""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from build_kanban_html import configure_django, fetch_dashboard_data

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MD_PATH = REPO_ROOT / "KANBAN.md"
KANBAN_PAGE_URL = "https://riodw.github.io/django-strawberry-framework/"
CARD_REF_RE = re.compile(r"\{\{card_ref:(\d+)\}\}")
CARD_ID_RE = re.compile(
    r"\b(?:TODO|WIP|BLOCKED|DONE)(?:-[A-Z]+)?-\d{3}-\d+\.\d+\.\d+\b",
)
LINK_DEFINITIONS_KEY = "link-definitions"
COLUMN_DOC_KEYS = {
    "in-progress",
    "to-do-alpha-010",
    "to-do-beta-100",
    "done",
}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Render KANBAN.md from the same GraphQL payload used by KANBAN.html.",
    )
    parser.add_argument(
        "--md",
        type=Path,
        default=DEFAULT_MD_PATH,
        help="Markdown file to write. Defaults to the repository-root KANBAN.md.",
    )
    return parser.parse_args()


def card_key(card: dict[str, Any]) -> str:
    """Return the current kanban card id for ``card``."""
    status = card["status"]["key"].upper()
    status_parts = [status]
    milestone = card.get("milestone")
    if status != "DONE" and milestone:
        status_parts.append(milestone["key"].upper())
    return f"{'-'.join(status_parts)}-{int(card['number']):03d}-{card['targetVersion']['number']}"


def card_url(card: dict[str, Any]) -> str:
    """Return the published dashboard URL for ``card``."""
    return f"{KANBAN_PAGE_URL}#{card['slug']}"


def card_column_key(card: dict[str, Any]) -> str:
    """Return the board column key that owns ``card``."""
    status = card["status"]["key"]
    milestone = card["milestone"]["key"] if card.get("milestone") else ""
    if status == "done":
        return "done"
    if status == "wip":
        return "in-progress"
    if status == "todo" and milestone == "alpha":
        return "to-do-alpha-010"
    if status == "todo" and milestone in {"beta", "stable"}:
        return "to-do-beta-100"
    return "backlog"


def sorted_column_cards(column_key: str, cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return cards in the display order for one board column."""
    return sorted(
        cards,
        key=lambda value: value["number"],
        reverse=column_key == "done",
    )


def size_label(card: dict[str, Any]) -> str:
    """Render a card's relative-size range."""
    relative_size = card.get("relativeSize")
    if not relative_size:
        return ""
    relative_size_high = card.get("relativeSizeHigh")
    if relative_size_high:
        return f"{relative_size['label']}-{relative_size_high['label']}"
    return relative_size["label"]


def resolve_card_refs(text: str, doc: dict[str, Any]) -> str:
    """Replace ``{{card_ref:N}}`` placeholders using FK-backed doc references."""
    references = {reference["order"]: reference for reference in doc.get("cardReferences", [])}

    def replace(match: re.Match[str]) -> str:
        reference = references.get(int(match.group(1)))
        if reference is None:
            return match.group(0)
        return card_key(reference["card"])

    return CARD_REF_RE.sub(replace, text)


def card_reference_replacements(card: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    """Return card-reference prose and token rewrites from FK targets."""
    grouped = defaultdict(list)
    for reference in card.get("outgoingReferences", []):
        if reference.get("rawText"):
            grouped[reference["rawText"]].append(reference)

    text_replacements = {}
    token_replacements = {}
    for raw_text, references in grouped.items():
        tokens = CARD_ID_RE.findall(raw_text)
        if not tokens:
            continue
        resolved_text = raw_text
        ordered_references = sorted(references, key=lambda value: value["order"])
        for token, reference in zip(tokens, ordered_references, strict=False):
            resolved_token = card_key(reference["targetCard"])
            token_replacements[token] = resolved_token
            resolved_text = resolved_text.replace(token, resolved_token, 1)
        text_replacements[raw_text] = resolved_text
    return text_replacements, token_replacements


def source_token_replacements(
    card: dict[str, Any],
    source_key: str,
    text: str,
    token_replacements: dict[str, str],
) -> dict[str, str]:
    """Map card-id tokens in one source field to that source's FK targets."""
    replacements = token_replacements.copy()
    tokens = CARD_ID_RE.findall(text)
    if not tokens:
        return replacements

    references = [
        reference
        for reference in card.get("outgoingReferences", [])
        if reference["source"]["key"] == source_key
    ]
    for token, reference in zip(tokens, references, strict=False):
        replacements.setdefault(token, card_key(reference["targetCard"]))
    return replacements


def resolve_card_text(
    text: str,
    text_replacements: dict[str, str],
    token_replacements: dict[str, str],
) -> str:
    """Resolve stale card-id prose snippets using normalized card references."""
    resolved = text
    for raw_text, replacement in sorted(
        text_replacements.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        resolved = resolved.replace(raw_text, replacement)
    for token, replacement in token_replacements.items():
        resolved = resolved.replace(token, replacement)
    return resolved


def bullet_lines(prefix: str, text: str) -> list[str]:
    """Render possibly multi-line text as one markdown bullet."""
    lines = (text or "").strip().splitlines()
    if not lines:
        return []
    rendered = [f"{prefix} {lines[0]}"]
    rendered.extend(f"  {line}" if line else "" for line in lines[1:])
    return rendered


def render_doc(doc: dict[str, Any]) -> list[str]:
    """Render one ordered board-prose document."""
    if doc["key"] == LINK_DEFINITIONS_KEY:
        return [resolve_card_refs(doc["body"], doc).strip()]

    lines = []
    if doc.get("title"):
        heading = "#" if doc["kind"]["key"] == "preamble" else "##"
        lines.extend([f"{heading} {doc['title']}", ""])

    body = resolve_card_refs(doc.get("body", ""), doc).strip()
    if body:
        lines.extend([body, ""])
    return lines


def render_card(card: dict[str, Any]) -> list[str]:
    """Render a kanban card with its lookup metadata and child rows."""
    text_replacements, token_replacements = card_reference_replacements(card)
    slug = card["slug"]
    lines = [
        f'<a id="{slug}"></a>',
        f"### [{card_key(card)} — {card['title']}]({card_url(card)})",
        "",
    ]

    if card.get("priority"):
        lines.append(f"- Priority: {card['priority']['label']}")
    parity_claims = sorted(
        card.get("parityClaims", []),
        key=lambda claim: claim["upstream"]["order"],
    )
    if parity_claims:
        parity = ", ".join(
            f"{claim['upstream']['emoji']} {claim['upstream']['label']} ({claim['level']['label']})".strip()
            for claim in parity_claims
        )
        lines.append(f"- Parity: {parity}")
    if card.get("severity"):
        lines.append(f"- Severity: {card['severity']['label']}")
    if card.get("planningState"):
        lines.append(f"- Status: {card['planningState']['label']}")
    size = size_label(card)
    if size:
        lines.append(f"- Relative size: {size}")
    labels = sorted(card.get("labels", []), key=lambda label: label["key"])
    if labels:
        lines.append("- Labels: " + ", ".join(f"`{label['key']}`" for label in labels))
    if card.get("spec"):
        lines.append(f"- Spec: [{card['spec']['name']}]({card['spec']['url']})")
    lines.append("")

    planning_note = card.get("planningNote") or ""
    if planning_note:
        planning_token_replacements = source_token_replacements(
            card,
            "planning_note",
            planning_note,
            token_replacements,
        )
        lines.extend(
            [
                "#### Planning note",
                "",
                resolve_card_text(
                    planning_note.strip(),
                    text_replacements,
                    planning_token_replacements,
                ),
                "",
            ],
        )

    dependencies = sorted(card.get("dependencies", []), key=lambda dependency: dependency["number"])
    if dependencies:
        lines.extend(["#### Dependencies", ""])
        for dependency in dependencies:
            lines.append(f"- `{card_key(dependency)}` — {dependency['title']}")
        lines.append("")

    item_groups = defaultdict(lambda: {"section": None, "items": []})
    for item in card.get("items", []):
        section = item["section"]
        group = item_groups[section["key"]]
        group["section"] = section
        group["items"].append(item)
    for group in sorted(item_groups.values(), key=lambda value: value["section"]["order"]):
        section = group["section"]
        lines.extend([f"#### {section['label']}", ""])
        for item in sorted(group["items"], key=lambda value: value["order"]):
            if section["key"] == "definition_of_done":
                marker = "[x]" if item["isComplete"] else "[ ]"
                lines.extend(
                    bullet_lines(
                        f"- {marker}",
                        resolve_card_text(item["text"], text_replacements, token_replacements),
                    ),
                )
            else:
                lines.extend(
                    bullet_lines(
                        "-",
                        resolve_card_text(item["text"], text_replacements, token_replacements),
                    ),
                )
        lines.append("")

    references = sorted(
        card.get("outgoingReferences", []),
        key=lambda reference: (reference["source"]["order"], reference["order"]),
    )
    if references:
        lines.extend(["#### Card references", ""])
        for reference in references:
            target_card = reference["targetCard"]
            target = f"`{card_key(target_card)}` — {target_card['title']}"
            source = f"{reference['kind']['label']} via {reference['source']['label']}"
            text = resolve_card_text(
                reference.get("rawText", "").strip(),
                text_replacements,
                token_replacements,
            )
            if text:
                lines.extend(bullet_lines(f"- {source}: {text} ->", target))
            else:
                lines.append(f"- {source}: {target}")
        lines.append("")

    return lines


def render_markdown(dashboard_data: dict[str, Any]) -> str:
    """Render the complete kanban board markdown."""
    docs = sorted(dashboard_data["boardDocs"], key=lambda doc: doc["order"])
    link_definitions = next((doc for doc in docs if doc["key"] == LINK_DEFINITIONS_KEY), None)
    docs = [doc for doc in docs if doc["key"] != LINK_DEFINITIONS_KEY]

    cards_by_column = defaultdict(list)
    for card in dashboard_data["cards"]:
        cards_by_column[card_column_key(card)].append(card)

    rendered = []
    rendered_card_ids = set()
    for doc in docs:
        if doc["kind"]["key"] == "column" and doc["key"] not in COLUMN_DOC_KEYS:
            continue
        rendered.extend(render_doc(doc))
        if doc["key"] in COLUMN_DOC_KEYS:
            for card in sorted_column_cards(doc["key"], cards_by_column.get(doc["key"], [])):
                rendered.extend(render_card(card))
                rendered_card_ids.add(card["id"])

    remaining_cards = [
        card
        for cards in cards_by_column.values()
        for card in cards
        if card["id"] not in rendered_card_ids
    ]
    if remaining_cards:
        rendered.extend(["## Backlog", ""])
        for card in sorted_column_cards("backlog", remaining_cards):
            rendered.extend(render_card(card))

    if link_definitions is not None:
        rendered.extend(render_doc(link_definitions))

    text = "\n".join(line.rstrip() for line in rendered).strip()
    return f"{text}\n"


def main() -> None:
    """Build the markdown board."""
    args = parse_args()
    configure_django()
    dashboard_data = fetch_dashboard_data()
    markdown = render_markdown(dashboard_data)
    args.md.write_text(markdown, encoding="utf-8")
    print(
        "Wrote "
        f"{len(dashboard_data['cards'])} cards and "
        f"{len(dashboard_data['boardDocs'])} board docs to {args.md}",
    )


if __name__ == "__main__":
    main()
