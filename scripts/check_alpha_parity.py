"""Enforce that every non-`internal` Alpha card carries a parity link + justification.

The rule is recorded in the board itself as the `decision-alpha-cards-require-parity`
reference `BoardDoc` (rendered into ``KANBAN.md``). The board data lives in the
fakeshop example DB (``examples/fakeshop/db.sqlite3``, app ``apps.kanban``); this gate
reads it through the same Django bootstrap the KANBAN exporters use
(``scripts/build_kanban_html.py::configure_django``).

A card is compliant when it has at least one ``ParityClaim`` (against ``graphene_django``
and/or ``strawberry_django``) AND at least one ``CardItem`` in the ``verified_upstream``
section. Pure-internal housekeeping cards (docs / release / cleanup / test-only / Django-core
hardening) are exempt and carry the ``internal`` label.

Usage::

    uv run python scripts/check_alpha_parity.py

Exit code is non-zero (and the violations are listed) when any non-``internal`` Alpha card
is missing a parity link or its justification.
"""

from __future__ import annotations

import sys

from build_kanban_html import configure_django


def main() -> int:
    """Audit every Alpha card and fail on any non-``internal`` parity gap."""
    configure_django()
    from apps.kanban.models import Card

    alpha = Card.objects.filter(target_version__milestone__key="alpha").order_by("number")
    violations: list[tuple[str, str]] = []
    exempt = 0
    for card in alpha:
        if card.labels.filter(key="internal").exists():
            exempt += 1
            continue
        n_parity = card.parity_claims.count()
        n_justification = card.items.filter(section__key="verified_upstream").count()
        if n_parity and n_justification:
            continue
        missing = []
        if not n_parity:
            missing.append("no parity link")
        if not n_justification:
            missing.append("no `Verified in upstream` justification")
        violations.append((card.card_id, ", ".join(missing)))

    checked = alpha.count() - exempt
    if violations:
        print(
            f"FAIL: {len(violations)} Alpha card(s) violate the parity rule "
            f"(checked {checked} feature cards, {exempt} `internal` exempt):",
        )
        for card_id, why in violations:
            print(f"  - {card_id}: {why}")
        print(
            "\nFix: add a `ParityClaim` + a `Verified in upstream` justification grounded in a "
            "real upstream `path::symbol`, OR label the card `internal` if it is pure housekeeping "
            "(docs / release / cleanup / test-only / Django-core hardening). Never fabricate a "
            "parity link. See the `decision-alpha-cards-require-parity` rule in KANBAN.md.",
        )
        return 1

    print(
        f"OK: {checked} non-`internal` Alpha cards each carry a parity link + a "
        f"`Verified in upstream` justification ({exempt} `internal` exempt).",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
