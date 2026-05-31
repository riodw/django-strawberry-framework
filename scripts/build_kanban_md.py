"""Build ``KANBAN.md`` from the fakeshop kanban database."""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from django.db.models import Prefetch

if TYPE_CHECKING:
    from apps.kanban import models

REPO_ROOT = Path(__file__).resolve().parents[1]
FAKESHOP_ROOT = REPO_ROOT / "examples" / "fakeshop"
DEFAULT_MD_PATH = REPO_ROOT / "KANBAN.md"
CARD_REF_RE = re.compile(r"\{\{card_ref:(\d+)\}\}")
CARD_ID_RE = re.compile(
    r"\b(?:TODO|WIP|BLOCKED|DONE)(?:-[A-Z]+)?-\d{3}-\d+\.\d+\.\d+\b",
)
LINK_DEFINITIONS_KEY = "link-definitions"
COLUMN_DOC_KEYS = {
    "in-progress",
    "to-do-alpha-010",
    "to-do-beta-100",
    "blocked",
    "done",
}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Render KANBAN.md from the kanban tables in the fakeshop database.",
    )
    parser.add_argument(
        "--md",
        type=Path,
        default=DEFAULT_MD_PATH,
        help="Markdown file to write. Defaults to the repository-root KANBAN.md.",
    )
    return parser.parse_args()


def configure_django() -> None:
    """Load the fakeshop Django settings for the ORM render pass."""
    sys.path.insert(0, str(FAKESHOP_ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django

    django.setup()


def card_key(card: models.Card) -> str:
    """Return the current kanban card id for ``card``."""
    status = card.status.key.upper()
    status_parts = [status]
    if status != "DONE" and card.milestone_id:
        status_parts.append(card.milestone.key.upper())
    return f"{'-'.join(status_parts)}-{card.number:03d}-{card.target_version.number}"


def card_column_key(card: models.Card) -> str:
    """Return the board column key that owns ``card``."""
    status = card.status.key
    milestone = card.milestone.key if card.milestone_id else ""
    if status == "done":
        return "done"
    if status == "blocked":
        return "blocked"
    if status == "wip":
        return "in-progress"
    if status == "todo" and milestone == "alpha":
        return "to-do-alpha-010"
    if status == "todo" and milestone in {"beta", "stable"}:
        return "to-do-beta-100"
    return "backlog"


def size_label(card: models.Card) -> str:
    """Render a card's relative-size range."""
    if not card.relative_size_id:
        return ""
    if card.relative_size_high_id:
        return f"{card.relative_size.label}-{card.relative_size_high.label}"
    return card.relative_size.label


def resolve_card_refs(text: str, doc: models.BoardDoc) -> str:
    """Replace ``{{card_ref:N}}`` placeholders using FK-backed doc references."""
    references = {reference.order: reference for reference in doc.card_references.all()}

    def replace(match: re.Match[str]) -> str:
        reference = references.get(int(match.group(1)))
        if reference is None:
            return match.group(0)
        return card_key(reference.card)

    return CARD_REF_RE.sub(replace, text)


def card_reference_text_replacements(card: models.Card) -> dict[str, str]:
    """Return raw-card-reference prose rewritten with current FK card ids."""
    grouped = defaultdict(list)
    for reference in card.outgoing_references.all():
        if reference.raw_text:
            grouped[reference.raw_text].append(reference)

    replacements = {}
    for raw_text, references in grouped.items():
        tokens = CARD_ID_RE.findall(raw_text)
        if not tokens:
            continue
        resolved_text = raw_text
        for token, reference in zip(tokens, sorted(references, key=lambda value: value.order), strict=False):
            resolved_text = resolved_text.replace(token, card_key(reference.target_card), 1)
        replacements[raw_text] = resolved_text
    return replacements


def resolve_card_text(text: str, replacements: dict[str, str]) -> str:
    """Resolve stale card-id prose snippets using normalized card references."""
    resolved = text
    for raw_text, replacement in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        resolved = resolved.replace(raw_text, replacement)
    return resolved


def bullet_lines(prefix: str, text: str) -> list[str]:
    """Render possibly multi-line text as one markdown bullet."""
    lines = (text or "").strip().splitlines()
    if not lines:
        return []
    rendered = [f"{prefix} {lines[0]}"]
    rendered.extend(f"  {line}" if line else "" for line in lines[1:])
    return rendered


def render_doc(doc: models.BoardDoc) -> list[str]:
    """Render one ordered board-prose document."""
    if doc.key == LINK_DEFINITIONS_KEY:
        return [resolve_card_refs(doc.body, doc).strip()]

    lines = []
    if doc.title:
        heading = "#" if doc.kind.key == "preamble" else "##"
        lines.extend([f"{heading} {doc.title}", ""])

    body = resolve_card_refs(doc.body, doc).strip()
    if body:
        lines.extend([body, ""])
    return lines


def render_card(card: models.Card) -> list[str]:
    """Render a kanban card with its lookup metadata and child rows."""
    reference_replacements = card_reference_text_replacements(card)
    lines = [f"### {card_key(card)} — {card.title}", ""]

    if card.priority_id:
        lines.append(f"- Priority: {card.priority.label}")
    parity_claims = sorted(
        card.parity_claims.all(),
        key=lambda claim: claim.upstream.order,
    )
    if parity_claims:
        parity = ", ".join(
            f"{claim.upstream.emoji} {claim.upstream.label} ({claim.level.label})".strip()
            for claim in parity_claims
        )
        lines.append(f"- Parity: {parity}")
    if card.severity_id:
        lines.append(f"- Severity: {card.severity.label}")
    if card.planning_state_id:
        lines.append(f"- Status: {card.planning_state.label}")
    size = size_label(card)
    if size:
        lines.append(f"- Relative size: {size}")
    labels = sorted(card.labels.all(), key=lambda label: label.key)
    if labels:
        lines.append("- Labels: " + ", ".join(f"`{label.key}`" for label in labels))
    if card.spec_id:
        lines.append(f"- Spec: [{card.spec.name}]({card.spec.url})")
    lines.append("")

    if card.planning_note:
        lines.extend(
            [
                "#### Planning note",
                "",
                resolve_card_text(card.planning_note.strip(), reference_replacements),
                "",
            ],
        )

    dependencies = sorted(card.dependencies.all(), key=lambda dependency: dependency.number)
    if dependencies:
        lines.extend(["#### Dependencies", ""])
        for dependency in dependencies:
            lines.append(f"- `{card_key(dependency)}` — {dependency.title}")
        lines.append("")

    item_groups = defaultdict(list)
    for item in card.items.all():
        item_groups[item.section].append(item)
    for section in sorted(item_groups, key=lambda value: value.order):
        lines.extend([f"#### {section.label}", ""])
        for item in sorted(item_groups[section], key=lambda value: value.order):
            if section.key == "definition_of_done":
                marker = "[x]" if item.is_complete else "[ ]"
                lines.extend(
                    bullet_lines(
                        f"- {marker}",
                        resolve_card_text(item.text, reference_replacements),
                    ),
                )
            else:
                lines.extend(bullet_lines("-", resolve_card_text(item.text, reference_replacements)))
        lines.append("")

    references = sorted(
        card.outgoing_references.all(),
        key=lambda reference: (reference.source.order, reference.order),
    )
    if references:
        lines.extend(["#### Card references", ""])
        for reference in references:
            target = f"`{card_key(reference.target_card)}` — {reference.target_card.title}"
            source = f"{reference.kind.label} via {reference.source.label}"
            text = resolve_card_text(reference.raw_text.strip(), reference_replacements)
            if text:
                lines.extend(bullet_lines(f"- {source}: {text} ->", target))
            else:
                lines.append(f"- {source}: {target}")
        lines.append("")

    return lines


def card_queryset() -> models.QuerySet[models.Card]:
    """Return cards with the related rows needed by the markdown renderer."""
    from apps.kanban import models

    linked_cards = models.Card.objects.select_related(
        "status",
        "milestone",
        "target_version",
        "planning_state",
    )
    return (
        models.Card.objects.select_related(
            "status",
            "milestone",
            "target_version",
            "priority",
            "severity",
            "relative_size",
            "relative_size_high",
            "planning_state",
            "spec",
        )
        .prefetch_related(
            "labels",
            Prefetch("dependencies", queryset=linked_cards.order_by("number")),
            Prefetch(
                "items",
                queryset=models.CardItem.objects.select_related("section").order_by(
                    "section__order",
                    "order",
                ),
            ),
            Prefetch(
                "parity_claims",
                queryset=models.ParityClaim.objects.select_related("upstream", "level").order_by(
                    "upstream__order",
                ),
            ),
            Prefetch(
                "outgoing_references",
                queryset=models.CardReference.objects.select_related(
                    "kind",
                    "source",
                    "target_card__status",
                    "target_card__milestone",
                    "target_card__target_version",
                    "target_card__planning_state",
                ).order_by("source__order", "order"),
            ),
        )
        .order_by("number")
    )


def board_doc_queryset() -> models.QuerySet[models.BoardDoc]:
    """Return board docs with FK-backed card references loaded."""
    from apps.kanban import models

    return (
        models.BoardDoc.objects.select_related("kind")
        .prefetch_related(
            Prefetch(
                "card_references",
                queryset=models.BoardDocCardReference.objects.select_related(
                    "card__status",
                    "card__milestone",
                    "card__target_version",
                    "card__planning_state",
                ).order_by("order"),
            ),
        )
        .order_by("order")
    )


def render_markdown() -> str:
    """Render the complete kanban board markdown."""
    docs = list(board_doc_queryset())
    link_definitions = next((doc for doc in docs if doc.key == LINK_DEFINITIONS_KEY), None)
    docs = [doc for doc in docs if doc.key != LINK_DEFINITIONS_KEY]

    cards_by_column = defaultdict(list)
    for card in card_queryset():
        cards_by_column[card_column_key(card)].append(card)

    rendered = []
    rendered_card_ids = set()
    for doc in docs:
        rendered.extend(render_doc(doc))
        if doc.key in COLUMN_DOC_KEYS:
            for card in cards_by_column.get(doc.key, []):
                rendered.extend(render_card(card))
                rendered_card_ids.add(card.pk)

    remaining_cards = [
        card
        for cards in cards_by_column.values()
        for card in cards
        if card.pk not in rendered_card_ids
    ]
    if remaining_cards:
        rendered.extend(["## Backlog", ""])
        for card in sorted(remaining_cards, key=lambda value: value.number):
            rendered.extend(render_card(card))

    if link_definitions is not None:
        rendered.extend(render_doc(link_definitions))

    text = "\n".join(line.rstrip() for line in rendered).strip()
    return f"{text}\n"


def main() -> None:
    """Build the markdown board."""
    args = parse_args()
    configure_django()
    markdown = render_markdown()
    args.md.write_text(markdown, encoding="utf-8")
    print(f"Wrote {args.md}")


if __name__ == "__main__":
    main()
