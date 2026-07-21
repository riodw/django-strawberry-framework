"""Seed the four net-new ``Section`` rows for the ``other`` reclassification.

The signed-off Phase 0.5 reclassification moved 378 ``other`` card items into
eleven target sections in the committed board snapshot. Four target sections
did not yet exist, so this data-only migration seeds those four keys, appended
after the then-current max ``order`` of 8 (``other``). The exact resulting item
UUID-to-section assignments remain in the kanban tables of the committed
``examples/fakeshop/db.sqlite3`` (the retired ``KANBAN.json`` export that once
mirrored them was removed with the export itself);
the one-shot command and review report were retired after the empty ``other``
section was removed.

* ``test_plan`` -> "Test plan" / 9
* ``decision`` -> "Decision" / 10
* ``open_question`` -> "Open question" / 11
* ``note`` -> "Note" / 12

Data migrations run against historical models, so the ``post_save``
``create_uuid_row`` signal does not fire -- the ``UUIDModel`` side-rows are
created explicitly here (mirroring migration 0014's ``_seed``).

The reclassification and subsequent removal of ``other`` are intentionally
irreversible: these section rows now own card items and cannot be deleted under
the ``PROTECT`` foreign key. The migration therefore declares a no-op reverse
instead of exposing a reverse function that can only fail.
"""

from django.db import migrations

NEW_SECTIONS = (
    ("test_plan", "Test plan", 9),
    ("decision", "Decision", 10),
    ("open_question", "Open question", 11),
    ("note", "Note", 12),
)


def _seed(apps, schema_editor):
    alias = schema_editor.connection.alias
    Section = apps.get_model("kanban", "Section")
    UUIDModel = apps.get_model("kanban", "UUIDModel")

    for key, label, order in NEW_SECTIONS:
        row, created = Section.objects.using(alias).get_or_create(
            key=key,
            defaults={"label": label, "order": order},
        )
        if created:
            UUIDModel.objects.using(alias).create(section=row)


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0014_seed_worklog_lookups"),
    ]

    operations = [
        migrations.RunPython(_seed, migrations.RunPython.noop),
    ]
