"""Remove the retired ``other`` section lookup row.

Every card item has a real section; the empty ``other`` row is deleted so the
key no longer exists anywhere (its ``UUIDModel`` side-row cascades). The delete
is guarded to run only while the section holds zero items, and the reverse is a
no-op: a retired lookup is not recreated.
"""

from django.db import migrations


def _remove(apps, schema_editor):
    alias = schema_editor.connection.alias
    Section = apps.get_model("kanban", "Section")

    Section.objects.using(alias).filter(key="other", items=None).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0015_seed_reclassification_sections"),
    ]

    operations = [
        migrations.RunPython(_remove, migrations.RunPython.noop),
    ]
