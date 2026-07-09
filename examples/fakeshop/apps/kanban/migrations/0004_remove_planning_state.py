"""Consolidate the card queue onto ``Status`` alone; drop ``PlanningState``.

``PlanningState`` (``planned`` / ``needs_spec`` / ``in_progress`` / ``shipped``)
duplicated the workflow signal already carried by ``Status`` (``backlog`` /
``todo`` / ``wip`` / ``done``): ``planned`` ~ ``todo``, ``in_progress`` ~ ``wip``,
``shipped`` ~ ``done``, and the two axes drifted apart in practice. The ``## In
progress`` board column is now derived from the single ``wip`` card's target
version (see ``scripts/build_kanban_md.py::active_version``), so the per-card
planning flag is redundant and is removed root and branch.

Unlike ``Card.severity`` (``on_delete=SET_NULL``, removed in 0003),
``Card.planning_state`` is ``on_delete=PROTECT``, so its column is dropped
*before* the seed rows are deleted -- otherwise the still-present card references
would raise ``ProtectedError``. Deleting the ``PlanningState`` rows then cascades
each one's ``UUIDModel`` side-row (``UUIDModel.planningstate`` was
``on_delete=CASCADE``), clearing those one-hot side-rows before the ``UUIDModel``
one-hot constraint is re-added without ``planningstate`` -- keeping the
``exactly one non-null link`` invariant satisfied on the existing board.
"""

import django.db.models.lookups
from django.db import migrations, models

import apps.kanban.constraints


def _delete_planning_state_data(apps, schema_editor):
    """Delete the ``PlanningState`` seed rows, cascading their UUID side-rows."""
    PlanningState = apps.get_model("kanban", "PlanningState")
    PlanningState.objects.using(schema_editor.connection.alias).all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0003_remove_severity"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="card",
            name="planning_state",
        ),
        migrations.RunPython(_delete_planning_state_data, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="uuidmodel",
            name="kanban_uuidmodel_exactly_one_link",
        ),
        migrations.RemoveField(
            model_name="uuidmodel",
            name="planningstate",
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
            name="PlanningState",
        ),
    ]
