"""WS-1C: replace ``TrackedPath.is_current`` with an explicit ``state`` slug.

``state`` disambiguates the three lifecycle meanings the boolean conflated:
``current`` (exists in the working tree), ``historical`` (linked from a done
card; the file once existed), and ``planned`` (linked from a wip/todo card;
does not exist yet). The backfill maps ``is_current=True`` -> ``current`` and
``is_current=False`` -> ``historical`` when any linked card is done, else
``planned``.
"""

from django.db import migrations, models


def _backfill_state(apps, schema_editor):
    """Derive ``state`` from the old ``is_current`` boolean and card links."""
    TrackedPath = apps.get_model("kanban", "TrackedPath")
    manager = TrackedPath.objects.using(schema_editor.connection.alias)
    for row in manager.all():
        if row.is_current:
            state = "current"
        elif row.cards.filter(status__key="done").exists():
            state = "historical"
        else:
            state = "planned"
        manager.filter(pk=row.pk).update(state=state)


def _restore_is_current(apps, schema_editor):
    """Reverse: ``is_current`` = whether ``state`` is ``current``."""
    TrackedPath = apps.get_model("kanban", "TrackedPath")
    manager = TrackedPath.objects.using(schema_editor.connection.alias)
    for row in manager.all():
        manager.filter(pk=row.pk).update(is_current=(row.state == "current"))


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0009_specdoc_path"),
    ]

    operations = [
        migrations.AddField(
            model_name="trackedpath",
            name="state",
            field=models.SlugField(
                choices=[
                    ("current", "Current"),
                    ("historical", "Historical"),
                    ("planned", "Planned"),
                ],
                default="current",
            ),
        ),
        migrations.RunPython(_backfill_state, _restore_is_current),
        migrations.RemoveField(
            model_name="trackedpath",
            name="is_current",
        ),
        migrations.AddConstraint(
            model_name="trackedpath",
            constraint=models.CheckConstraint(
                condition=models.Q(state__in=["current", "historical", "planned"]),
                name="tracked_path_state_valid",
            ),
        ),
    ]
