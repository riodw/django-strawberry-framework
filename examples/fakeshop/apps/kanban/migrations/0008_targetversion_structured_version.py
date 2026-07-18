"""WS-1B: add structured ``major``/``minor``/``patch`` to ``TargetVersion``.

``TargetVersion.number`` stays canonical (the display string); the structured
triple is backfilled from it and kept in sync by ``TargetVersion.save()``.
Ordering switches to the numeric triple so ``0.0.9`` sorts before ``0.0.16``
(a lexicographic sort of ``number`` gets this wrong at patch >= 10).
"""

from django.db import migrations, models


def _parse_version(number: str) -> tuple[int, int, int]:
    parts = [0, 0, 0]
    for index, segment in enumerate((number or "").split(".")[:3]):
        digits = "".join(ch for ch in segment if ch.isdigit())
        parts[index] = int(digits) if digits else 0
    return parts[0], parts[1], parts[2]


def _backfill_version_triple(apps, schema_editor):
    """Populate ``major``/``minor``/``patch`` from each row's ``number``."""
    TargetVersion = apps.get_model("kanban", "TargetVersion")
    manager = TargetVersion.objects.using(schema_editor.connection.alias)
    for row in manager.all():
        major, minor, patch = _parse_version(row.number)
        manager.filter(pk=row.pk).update(major=major, minor=minor, patch=patch)


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0007_complete_card_ref_realignment"),
    ]

    operations = [
        migrations.AddField(
            model_name="targetversion",
            name="major",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="targetversion",
            name="minor",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="targetversion",
            name="patch",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name="targetversion",
            options={
                "ordering": ["major", "minor", "patch"],
                "verbose_name": "target version",
                "verbose_name_plural": "target versions",
            },
        ),
        migrations.RunPython(_backfill_version_triple, migrations.RunPython.noop),
    ]
