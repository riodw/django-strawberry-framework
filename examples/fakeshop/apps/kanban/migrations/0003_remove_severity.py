"""Consolidate card triage onto ``Priority`` alone; drop ``Severity`` entirely.

``Severity`` duplicated the ``Priority`` lookup's shape without a distinct role
(effort is already captured by ``RelativeSize``), so it is removed root and branch:
the ``Card`` / ``UUIDModel`` links, the lookup model, and its seed rows.

The data step runs first and deletes every ``Severity`` row while the historical
relations are still intact, so the deletion collector cascades to each severity's
``UUIDModel`` side-row (``UUIDModel.severity`` was ``on_delete=CASCADE``) and
``SET_NULL``s ``Card.severity``. Clearing those one-hot side-rows before the
``UUIDModel`` one-hot constraint is re-added (now excluding ``severity``) is what
keeps the ``exactly one non-null link`` invariant satisfied on the existing board.
"""

import django.db.models.lookups
from django.db import migrations, models

import apps.kanban.constraints


def _delete_severity_data(apps, schema_editor):
    """Delete the ``Severity`` seed rows, cascading their UUID side-rows."""
    Severity = apps.get_model("kanban", "Severity")
    Severity.objects.using(schema_editor.connection.alias).all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0002_card_glossary_terms"),
    ]

    operations = [
        migrations.RunPython(_delete_severity_data, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="card",
            name="severity",
        ),
        migrations.RemoveConstraint(
            model_name="uuidmodel",
            name="kanban_uuidmodel_exactly_one_link",
        ),
        migrations.RemoveField(
            model_name="uuidmodel",
            name="severity",
        ),
        migrations.AddConstraint(
            model_name="uuidmodel",
            constraint=models.CheckConstraint(
                condition=django.db.models.lookups.Exact(
                    apps.kanban.constraints.OneHotLinkCount(
                        "milestone",
                        "status",
                        "priority",
                        "relativesize",
                        "planningstate",
                        "upstream",
                        "paritylevel",
                        "section",
                        "cardreferencekind",
                        "boarddockind",
                        "targetversion",
                        "specdoc",
                        "trackedpath",
                        "card",
                        "cardreference",
                        "cardglossaryterm",
                        "parityclaim",
                        "carditem",
                        "label",
                        "boarddoc",
                        "boarddoccardreference",
                    ),
                    models.Value(1),
                ),
                name="kanban_uuidmodel_exactly_one_link",
            ),
        ),
        migrations.DeleteModel(
            name="Severity",
        ),
    ]
