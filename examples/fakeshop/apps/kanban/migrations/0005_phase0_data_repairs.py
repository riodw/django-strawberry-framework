"""Phase 0 data repairs: reference dedupe, milestone drift, stale blocked_by.

Three self-contained, additive data steps that clean pre-existing rows before
later schema constraints can be added. No schema changes: this migration only
rewrites offending row data via
per-row ``.update()`` (avoiding ``Card.save`` / ``CardReference.save`` signal
and renumber side effects) and deletes duplicate reference rows.

* 0.1 Dedupe ``CardReference`` rows sharing ``(source_card, target_card,
  kind)`` -- keep the row with the lowest ``order``, delete the rest -- then
  renumber every source card's surviving references contiguously from ``0`` by
  their existing ``order``.
* 0.2 Repair ``Card.milestone`` drift: for every card whose ``milestone`` does
  not match ``target_version.milestone``, adopt the ``target_version`` side.
* 0.3 Retype done->done ``blocked_by`` references to ``dependency`` (a shipped
  blocker is informational, not gating).

The reverse is a deliberate no-op: the repaired state is the correct state and
the pre-repair duplicates / drift are not worth reconstructing.
"""

import re

from django.db import migrations

CARD_REF_RE = re.compile(r"\{\{card_ref:(\d+)\}\}")


def _remap_card_ref_placeholders(text: str, old_to_new: dict[int, int]) -> str:
    """Rewrite ``{{card_ref:N}}`` placeholders in ``text`` via ``old_to_new``.

    Card prose (``Card.planning_note`` / ``CardItem.text``) references a source
    card's outgoing references by their ``order`` (see
    ``scripts/build_kanban_md.py::resolve_card_refs_for_card``). Whenever those
    orders are renumbered the placeholders must move with them or they resolve to
    the wrong -- or a missing -- reference. A single ``re.sub`` pass reads the
    original numbering so remaps that swap positions cannot collide.
    """

    def replace(match: "re.Match[str]") -> str:
        old = int(match.group(1))
        new = old_to_new.get(old, old)
        return f"{{{{card_ref:{new}}}}}"

    return CARD_REF_RE.sub(replace, text)


def _dedupe_and_renumber_references(apps, schema_editor):
    """0.1 -- drop duplicate references, renumber per source card, and move the
    card-prose ``{{card_ref:N}}`` placeholders to match the new numbering.

    The dedupe/renumber and the placeholder rewrite are computed from one
    pre-renumber snapshot per source card so the two never drift: a placeholder
    that pointed at a deleted duplicate is remapped to the surviving row's new
    order (same target card, so the rendered id is unchanged), and a placeholder
    that pointed at a surviving row follows that row to its new contiguous order.
    """
    CardReference = apps.get_model("kanban", "CardReference")
    Card = apps.get_model("kanban", "Card")
    CardItem = apps.get_model("kanban", "CardItem")
    alias = schema_editor.connection.alias
    manager = CardReference.objects.using(alias)

    source_ids = list(manager.values_list("source_card", flat=True).distinct())
    for source_id in source_ids:
        rows = list(manager.filter(source_card=source_id).order_by("order", "id"))

        # Dedupe (source, target, kind): keep the lowest-order row; record each
        # deleted row's old order -> the kept row's old order.
        kept_old_order_by_key: dict[tuple, int] = {}
        deleted_old_to_kept_old: dict[int, int] = {}
        survivors = []
        for row in rows:
            key = (row.target_card_id, row.kind_id)
            if key in kept_old_order_by_key:
                deleted_old_to_kept_old[row.order] = kept_old_order_by_key[key]
                row.delete()
            else:
                kept_old_order_by_key[key] = row.order
                survivors.append(row)

        # Renumber survivors contiguously from 0 by existing order.
        old_to_new: dict[int, int] = {}
        for new_order, row in enumerate(survivors):
            old_to_new[row.order] = new_order
            if row.order != new_order:
                manager.filter(pk=row.pk).update(order=new_order)
        # Deleted duplicates inherit the surviving row's new order.
        for deleted_old, kept_old in deleted_old_to_kept_old.items():
            old_to_new[deleted_old] = old_to_new[kept_old]

        # Nothing shifted -> no placeholder rewrite needed for this card.
        if all(old == new for old, new in old_to_new.items()):
            continue

        card = Card.objects.using(alias).get(pk=source_id)
        new_note = _remap_card_ref_placeholders(card.planning_note or "", old_to_new)
        if new_note != (card.planning_note or ""):
            Card.objects.using(alias).filter(pk=card.pk).update(planning_note=new_note)
        for item in CardItem.objects.using(alias).filter(card_id=source_id):
            new_text = _remap_card_ref_placeholders(item.text or "", old_to_new)
            if new_text != (item.text or ""):
                CardItem.objects.using(alias).filter(pk=item.pk).update(text=new_text)
        # ``CardReference.raw_text`` is the third prose surface carrying
        # ``{{card_ref:N}}`` placeholders (the exporter resolves them at
        # build_kanban_md.py::card_reference_lines), so it renumbers too.
        for reference in manager.filter(source_card=source_id):
            new_raw = _remap_card_ref_placeholders(reference.raw_text or "", old_to_new)
            if new_raw != (reference.raw_text or ""):
                manager.filter(pk=reference.pk).update(raw_text=new_raw)


def _repair_milestone_drift(apps, schema_editor):
    """0.2 -- align each card's milestone with its target version's milestone."""
    Card = apps.get_model("kanban", "Card")
    manager = Card.objects.using(schema_editor.connection.alias)
    for card in manager.select_related("target_version").all():
        target_milestone_id = card.target_version.milestone_id
        if card.milestone_id != target_milestone_id:
            manager.filter(pk=card.pk).update(milestone_id=target_milestone_id)


def _retype_done_done_blocked_by(apps, schema_editor):
    """0.3 -- retype done->done ``blocked_by`` edges to ``dependency``."""
    CardReference = apps.get_model("kanban", "CardReference")
    CardReferenceKind = apps.get_model("kanban", "CardReferenceKind")
    alias = schema_editor.connection.alias
    manager = CardReference.objects.using(alias)

    stale = manager.filter(
        kind__key="blocked_by",
        source_card__status__key="done",
        target_card__status__key="done",
    )
    if not stale.exists():
        return

    dependency_kind = CardReferenceKind.objects.using(alias).get(key="dependency")
    for row in stale:
        manager.filter(pk=row.pk).update(kind=dependency_kind)


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0004_remove_planning_state"),
    ]

    operations = [
        migrations.RunPython(_repair_milestone_drift, migrations.RunPython.noop),
        migrations.RunPython(_retype_done_done_blocked_by, migrations.RunPython.noop),
        migrations.RunPython(_dedupe_and_renumber_references, migrations.RunPython.noop),
    ]
