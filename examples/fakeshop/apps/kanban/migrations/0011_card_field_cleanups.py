"""WS-1A/1C: card-to-card edge source of truth + field-level cleanups.

* Drop the ``Card.dependencies`` M2M -- ``CardReference`` (``dependency`` /
  ``blocked_by`` kinds) is now the single source of truth for card edges; the
  M2M and its bidirectional signal sync are removed. The M2M rows are redundant
  with the reference rows, so the table just drops.
* Drop the derived ``Card.milestone`` FK (derived from ``target_version``).
* Make ``Card.priority`` non-null with ``on_delete=PROTECT`` (0 null rows live).
* Drop the duplicate ``RelativeSize.rank`` axis (``order`` already carries the
  identical values; ``order`` is the surviving ordering axis).
* Add the missing ``CardReference`` uniqueness constraints (Phase 0 already
  deduped ``(source, target, kind)`` and per-source ``order``).
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0010_trackedpath_state"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="card",
            name="dependencies",
        ),
        migrations.RemoveField(
            model_name="card",
            name="milestone",
        ),
        migrations.AlterField(
            model_name="card",
            name="priority",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="cards",
                to="kanban.priority",
            ),
        ),
        migrations.RemoveField(
            model_name="relativesize",
            name="rank",
        ),
        migrations.AddConstraint(
            model_name="cardreference",
            constraint=models.UniqueConstraint(
                fields=("source_card", "target_card", "kind"),
                name="unique_card_reference_edge",
            ),
        ),
        migrations.AddConstraint(
            model_name="cardreference",
            constraint=models.UniqueConstraint(
                fields=("source_card", "order"),
                name="unique_card_reference_position",
            ),
        ),
    ]
