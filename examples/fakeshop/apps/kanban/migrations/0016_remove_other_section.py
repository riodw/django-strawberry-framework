"""Remove the retired ``other`` section lookup row.

Every card item has a real section; the empty ``other`` row is deleted so the
key no longer exists anywhere (its ``UUIDModel`` side-row cascades). The delete
fails loudly if the section still owns any items, so Django cannot record the
migration as successful while leaving the retired key in place. The reverse is
a no-op: a retired lookup is not recreated.
"""

from django.db import migrations


def _remove(apps, schema_editor):
    alias = schema_editor.connection.alias
    Section = apps.get_model("kanban", "Section")
    CardItem = apps.get_model("kanban", "CardItem")

    other = Section.objects.using(alias).filter(key="other").first()
    if other is None:
        return
    remaining = CardItem.objects.using(alias).filter(section_id=other.pk).count()
    if remaining:
        raise RuntimeError(
            "Cannot retire the kanban 'other' section while it still owns "
            f"{remaining} card item(s); reclassify every item before applying migration 0016.",
        )
    Section.objects.using(alias).filter(pk=other.pk).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0015_seed_reclassification_sections"),
    ]

    operations = [
        migrations.RunPython(_remove, migrations.RunPython.noop),
    ]
