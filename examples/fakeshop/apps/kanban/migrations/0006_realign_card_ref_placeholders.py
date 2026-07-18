"""One-time realignment of card-prose ``{{card_ref:N}}`` placeholders on the live DB.

Migration ``0005`` deduped and renumbered each source card's ``CardReference``
rows. Card prose (``Card.planning_note`` / ``CardItem.text``) references those
rows by ``order`` (see ``scripts/build_kanban_md.py::resolve_card_refs_for_card``),
so the renumber shifted two cards' placeholders out of alignment -- the KANBAN.md
renderer raised on the resulting unresolved ``{{card_ref:N}}`` placeholders.

``0005`` now performs that placeholder rewrite atomically with the renumber, so a
migration run against un-renumbered data stays consistent. This follow-up exists
only to repair the live ``db.sqlite3``, whose ``0005`` had already renumbered the
rows (destroying the pre-renumber orders) before the atomic rewrite was in place.

The two remaps below were recovered from the pre-migration ``KANBAN.md`` (the
committed ``#### Card references`` lists render each source card's outgoing
references in ``order``) and verified against the post-renumber reference targets
in the live DB:

* Card ``Full Relay story ...`` -- survivors' old->new order ``7->5, 8->6, 9->7``
  (orders 0-4 unchanged); duplicate related edges to cards 27/28/30 were dropped.
* Card `` ``Meta.search_fields`` support `` -- old->new ``2->1, 3->2, 5->3``
  (order 0 unchanged); duplicate dependency edges to cards 27/30 were dropped.

Guarded and idempotent: a card is rewritten only while it still carries a
placeholder whose order is out of range for its current reference count (the
signature of the un-remapped state), so re-running is a no-op. The reverse is a
deliberate no-op -- the realigned placeholders are the correct state.
"""

import re

from django.db import migrations

CARD_REF_RE = re.compile(r"\{\{card_ref:(\d+)\}\}")

# Keyed by card ``title`` (stable, unique) -> old-order -> new-order. Only the
# shifted orders are listed; every other placeholder order is left untouched.
_REMAPS = {
    "Full Relay story (Node + Connection + Root + validation)": {7: 5, 8: 6, 9: 7},
    "`Meta.search_fields` support": {2: 1, 3: 2, 5: 3},
}


def _placeholder_orders(text: str) -> set[int]:
    return {int(order) for order in CARD_REF_RE.findall(text or "")}


def _remap(text: str, old_to_new: dict[int, int]) -> str:
    def replace(match: "re.Match[str]") -> str:
        old = int(match.group(1))
        return f"{{{{card_ref:{old_to_new.get(old, old)}}}}}"

    return CARD_REF_RE.sub(replace, text or "")


def _realign_placeholders(apps, schema_editor):
    Card = apps.get_model("kanban", "Card")
    CardItem = apps.get_model("kanban", "CardItem")
    CardReference = apps.get_model("kanban", "CardReference")
    alias = schema_editor.connection.alias

    for title, old_to_new in _REMAPS.items():
        card = Card.objects.using(alias).filter(title=title).first()
        if card is None:
            continue

        reference_count = CardReference.objects.using(alias).filter(source_card=card).count()
        used = _placeholder_orders(card.planning_note)
        items = list(CardItem.objects.using(alias).filter(card=card))
        for item in items:
            used |= _placeholder_orders(item.text)

        # Already realigned (or never broken): every placeholder is in range.
        if not any(order >= reference_count for order in used):
            continue

        new_note = _remap(card.planning_note, old_to_new)
        if new_note != (card.planning_note or ""):
            Card.objects.using(alias).filter(pk=card.pk).update(planning_note=new_note)
        for item in items:
            new_text = _remap(item.text, old_to_new)
            if new_text != (item.text or ""):
                CardItem.objects.using(alias).filter(pk=item.pk).update(text=new_text)


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0005_phase0_data_repairs"),
    ]

    operations = [
        migrations.RunPython(_realign_placeholders, migrations.RunPython.noop),
    ]
