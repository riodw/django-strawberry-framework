"""Seed the four net-new ``Section`` rows for the ``other`` reclassification.

Data-only migration paired with the ``reclassify_other_items`` management
command (see ``kanban-section-other-report.md``): the signed-off Phase 0.5
mapping moves the 378 ``other`` card items into eleven target sections, four of
which do not yet exist. This seeds only those four net-new keys, appended after
the current max ``order`` of 8 (``other``):

* ``test_plan`` -> "Test plan" / 9
* ``decision`` -> "Decision" / 10
* ``open_question`` -> "Open question" / 11
* ``note`` -> "Note" / 12

Data migrations run against historical models, so the ``post_save``
``create_uuid_row`` signal does not fire -- the ``UUIDModel`` side-rows are
created explicitly here (mirroring migration 0014's ``_seed``).

The reverse deletes the seeded rows by key (their UUID side-rows cascade). It is
safe only while no card item points at these sections, so the reverse must run
after the command's ``--rollback`` has emptied them back into ``other``.
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


def _unseed(apps, schema_editor):
    alias = schema_editor.connection.alias
    Section = apps.get_model("kanban", "Section")

    Section.objects.using(alias).filter(
        key__in=[key for key, _, _ in NEW_SECTIONS],
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0014_seed_worklog_lookups"),
    ]

    operations = [
        migrations.RunPython(_seed, _unseed),
    ]
