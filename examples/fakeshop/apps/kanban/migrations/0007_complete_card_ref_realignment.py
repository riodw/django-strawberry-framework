"""Complete the card-prose ``{{card_ref:N}}`` realignment on the live DB.

Migration ``0005`` renumbered each source card's ``CardReference`` orders;
``0006`` realigned the placeholders in ``Card.planning_note`` / ``CardItem.text``
for the two cards whose out-of-range placeholders first surfaced the problem
(``Full Relay story ...`` and `` ``Meta.search_fields`` support``). Two gaps
remained on the live DB:

* ``CardReference.raw_text`` is a third prose surface carrying the same
  placeholders (the exporter resolves it at
  ``scripts/build_kanban_md.py::card_reference_lines``) and was never realigned
  for any card.
* Seven further cards had references renumbered by ``0005`` (duplicate edges
  deleted and/or gap-compacted) and so carried shifted placeholders in their
  ``planning_note`` / ``CardItem.text`` that ``0006`` did not cover.

``0005`` now performs the renumber and the placeholder rewrite across all three
surfaces atomically, so any future run against un-renumbered data stays
consistent. This migration is the one-time repair for the live ``db.sqlite3``,
whose ``0005`` had already renumbered (destroying the pre-renumber orders) before
that atomic rewrite existed.

The old-order -> new-order maps below were recovered from the committed
(pre-migration) ``KANBAN.md`` -- whose ``#### Card references`` lists render each
source card's outgoing references in ``order`` -- and validated row-by-row
against the live DB's post-renumber reference targets (a re-simulation of
``0005``'s dedupe+renumber reproduced the current numbering with zero
mismatches). Only shifted orders are listed; every other placeholder is left
untouched. A placeholder that pointed at a deleted duplicate maps to the
surviving row's new order (same target card, so the rendered id is unchanged).

``raw_text`` is realigned for every affected card; ``planning_note`` /
``CardItem.text`` are realigned for every affected card *except* the two already
handled by ``0006`` (re-applying the map there would double-shift). The reverse
is a deliberate no-op: the realigned placeholders are the correct state.
"""

import re

from django.db import migrations

CARD_REF_RE = re.compile(r"\{\{card_ref:(\d+)\}\}")

# card title -> {old_order: new_order} (non-identity shifts only).
_REMAPS = {
    "Ordering subsystem": {1: 0},
    "Full Relay story (Node + Connection + Root + validation)": {
        7: 5,
        8: 6,
        9: 7,
        5: 1,
        6: 2,
        10: 4,
    },
    "Upload scalar and file / image field mapping": {1: 0},
    "Form-based mutations (Django Forms / ModelForms)": {2: 1},
    "Channels ASGI router (migration aid)": {1: 0},
    "Test client helper": {2: 1},
    "Response-extensions debug middleware": {1: 0, 2: 0, 3: 0},
    "`Meta.search_fields` support": {2: 1, 3: 2, 5: 3, 6: 4, 1: 0, 4: 2},
    "Postgres full-text search filter primitives": {2: 1, 3: 2, 5: 3, 1: 0, 4: 2},
}

# planning_note / CardItem.text for these two were already realigned by 0006.
_NOTE_ITEMS_DONE_BY_0006 = {
    "Full Relay story (Node + Connection + Root + validation)",
    "`Meta.search_fields` support",
}


def _remap(text: str, old_to_new: dict[int, int]) -> str:
    def replace(match: "re.Match[str]") -> str:
        old = int(match.group(1))
        return f"{{{{card_ref:{old_to_new.get(old, old)}}}}}"

    return CARD_REF_RE.sub(replace, text or "")


def _complete_realignment(apps, schema_editor):
    Card = apps.get_model("kanban", "Card")
    CardItem = apps.get_model("kanban", "CardItem")
    CardReference = apps.get_model("kanban", "CardReference")
    alias = schema_editor.connection.alias

    for title, old_to_new in _REMAPS.items():
        card = Card.objects.using(alias).filter(title=title).first()
        if card is None:
            continue

        # raw_text: realign for every affected card (never touched before).
        for reference in CardReference.objects.using(alias).filter(source_card=card):
            new_raw = _remap(reference.raw_text, old_to_new)
            if new_raw != (reference.raw_text or ""):
                CardReference.objects.using(alias).filter(pk=reference.pk).update(
                    raw_text=new_raw,
                )

        if title in _NOTE_ITEMS_DONE_BY_0006:
            continue

        new_note = _remap(card.planning_note, old_to_new)
        if new_note != (card.planning_note or ""):
            Card.objects.using(alias).filter(pk=card.pk).update(planning_note=new_note)
        for item in CardItem.objects.using(alias).filter(card=card):
            new_text = _remap(item.text, old_to_new)
            if new_text != (item.text or ""):
                CardItem.objects.using(alias).filter(pk=item.pk).update(text=new_text)


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0006_realign_card_ref_placeholders"),
    ]

    operations = [
        migrations.RunPython(_complete_realignment, migrations.RunPython.noop),
    ]
