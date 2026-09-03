"""Fail when kanban anchors collide - card vs card, card vs glossary, or in the render.

``Card.slug`` is a pure function of the title (``slugify(title)`` with ``_``
separators, ``apps/kanban/models.py::Card.slug``) and carries no namespace
prefix, so nothing structural stops two distinct titles from slugifying to one
anchor ("`FieldSet`" and "Field set" both yield ``fieldset``), or a card slug
from equalling a glossary term's stored ``anchor`` (the shipped instance: card
059's original title "`FieldSet`" claimed ``#fieldset``, the glossary term's
anchor). A duplicate anchor makes deep links resolve to the wrong element; a
cross-namespace collision makes ``#<anchor>`` ambiguous the moment any render
surface carries both populations (``KANBAN.html`` already embeds the glossary
lookup arrays).

Three independent gates, any one of which fails the run:

1. two cards whose titles slugify to the same anchor;
2. a card slug equal to a glossary term ``anchor`` (raw string equality - the
   two slug grammars differ in separator, so only separator-free names can
   collide, which is exactly the generic-single-word shape worth refusing);
3. a duplicate ``<a id="...">`` in the rendered ``KANBAN.md`` (belt-and-braces
   over whatever anchor sources a future render adds).

The board and glossary data live in the fakeshop example DB
(``examples/fakeshop/db.sqlite3``); this gate reads it through the same Django
bootstrap the KANBAN exporters use (``scripts/_kanban_lib.py::configure_django``).

Usage::

    uv run python scripts/check_kanban_anchors.py

Exit code is non-zero (and the collisions are listed) on any violation.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from _kanban_lib import configure_django
except ModuleNotFoundError:  # imported as ``scripts.check_kanban_anchors`` (repo root on path)
    from scripts._kanban_lib import configure_django

REPO_ROOT = Path(__file__).resolve().parent.parent
KANBAN_MD_PATH = REPO_ROOT / "KANBAN.md"
RENDER_ANCHOR_RE = re.compile(r'<a id="([^"]+)"></a>')


def card_slug_violations(cards: list[tuple[str, str]]) -> list[str]:
    """Return one message per card pair whose titles slugify to the same anchor."""
    first_owner: dict[str, str] = {}
    violations: list[str] = []
    for card_id, slug in cards:
        owner = first_owner.setdefault(slug, card_id)
        if owner != card_id:
            violations.append(
                f"card anchor collision: {card_id} and {owner} both slugify to #{slug}",
            )
    return violations


def glossary_collision_violations(
    cards: list[tuple[str, str]],
    glossary_anchors: dict[str, str],
) -> list[str]:
    """Return one message per card slug that equals a glossary term's anchor."""
    return [
        f"cross-namespace collision: {card_id} claims #{slug}, "
        f"the anchor of glossary term {glossary_anchors[slug]!r}"
        for card_id, slug in cards
        if slug in glossary_anchors
    ]


def render_anchor_violations(rendered_markdown: str) -> list[str]:
    """Return one message per anchor id that appears more than once in the render."""
    seen: set[str] = set()
    violations: list[str] = []
    for anchor in RENDER_ANCHOR_RE.findall(rendered_markdown):
        if anchor in seen:
            violations.append(f'duplicate rendered anchor: <a id="{anchor}"> appears twice')
        seen.add(anchor)
    return violations


def main() -> int:
    """Audit card, glossary, and rendered anchors; fail loudly on any collision."""
    configure_django()
    from apps.glossary.models import GlossaryTerm
    from apps.kanban.models import Card

    cards = [(card.card_id, card.slug) for card in Card.objects.order_by("number")]
    glossary_anchors = dict(GlossaryTerm.objects.values_list("anchor", "title"))

    violations = card_slug_violations(cards)
    violations += glossary_collision_violations(cards, glossary_anchors)
    violations += render_anchor_violations(KANBAN_MD_PATH.read_text(encoding="utf-8"))

    if violations:
        print("Kanban anchor collisions:", file=sys.stderr)
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1
    print(
        f"OK: {len(cards)} card anchors are unique, none collides with the "
        f"{len(glossary_anchors)} glossary anchors, and the KANBAN.md render carries no duplicate id.",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
