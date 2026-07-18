"""WS-1C: give ``Card.changed_files`` a ``CardPathLink`` through model with ``kind``.

The bare M2M could not distinguish a done card's actually-``changed`` files from
a wip/todo card's ``predicted`` files -- the renderers reinterpreted the same
edge by the source card's status. ``CardPathLink`` records the ``kind`` per link.

Data is preserved: the existing auto M2M rows are copied into ``CardPathLink``
(``kind=changed`` for links on done cards, ``predicted`` otherwise) and a
``UUIDModel`` side-row is created for each, before the old auto table is dropped
via a state/database split (the through model's table already exists, so the
default M2M-alter path -- which would recreate it -- is bypassed).
"""

import django.db.models.deletion
import django.db.models.lookups
from django.db import migrations, models

import apps.kanban.constraints

_ONE_HOT_LINK_NAMES = (
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
    "cardpathlink",
    "carditem",
    "label",
    "boarddoc",
    "boarddoccardreference",
)

_RECREATE_AUTO_TABLE_SQL = """
CREATE TABLE "kanban_card_changed_files" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "card_id" bigint NOT NULL REFERENCES "kanban_card" ("id") DEFERRABLE INITIALLY DEFERRED,
    "trackedpath_id" bigint NOT NULL REFERENCES "kanban_trackedpath" ("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE UNIQUE INDEX "kanban_card_changed_files_card_id_trackedpath_id_uniq"
    ON "kanban_card_changed_files" ("card_id", "trackedpath_id");
"""


def _copy_links_and_uuid_rows(apps, schema_editor):
    """Copy old auto-M2M rows into CardPathLink and create their UUID side-rows."""
    Card = apps.get_model("kanban", "Card")
    CardPathLink = apps.get_model("kanban", "CardPathLink")
    UUIDModel = apps.get_model("kanban", "UUIDModel")
    alias = schema_editor.connection.alias

    through = Card.changed_files.through
    done_card_ids = set(
        Card.objects.using(alias).filter(status__key="done").values_list("id", flat=True),
    )
    for row in through.objects.using(alias).all():
        kind = "changed" if row.card_id in done_card_ids else "predicted"
        link = CardPathLink.objects.using(alias).create(
            card_id=row.card_id,
            path_id=row.trackedpath_id,
            kind=kind,
        )
        UUIDModel.objects.using(alias).create(cardpathlink=link)


def _drop_copied_links(apps, schema_editor):
    """Reverse: copy CardPathLink rows back into the recreated auto M2M table.

    On rollback the ``SeparateDatabaseAndState`` reverse_sql (which recreates the
    empty ``kanban_card_changed_files`` auto table) runs BEFORE this RunPython, so
    the table exists here. Copy every ``(card, path)`` pair back so reversing to
    0011 preserves the links -- a bare delete would lose them all -- then clear the
    ``CardPathLink`` rows (their ``UUIDModel`` side-rows cascade on delete).
    """
    CardPathLink = apps.get_model("kanban", "CardPathLink")
    alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            'INSERT INTO "kanban_card_changed_files" ("card_id", "trackedpath_id") '
            'SELECT "card_id", "path_id" FROM "kanban_cardpathlink";',
        )
    CardPathLink.objects.using(alias).all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0011_card_field_cleanups"),
    ]

    operations = [
        migrations.CreateModel(
            name="CardPathLink",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("updated_date", models.DateTimeField(auto_now=True)),
                (
                    "kind",
                    models.SlugField(
                        choices=[("changed", "Changed"), ("predicted", "Predicted")],
                        default="predicted",
                    ),
                ),
                (
                    "card",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="path_links",
                        to="kanban.card",
                    ),
                ),
                (
                    "path",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="card_links",
                        to="kanban.trackedpath",
                    ),
                ),
            ],
            options={
                "verbose_name": "card path link",
                "verbose_name_plural": "card path links",
                "ordering": ["card", "path"],
            },
        ),
        migrations.RemoveConstraint(
            model_name="uuidmodel",
            name="kanban_uuidmodel_exactly_one_link",
        ),
        migrations.AddField(
            model_name="uuidmodel",
            name="cardpathlink",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="uuid",
                to="kanban.cardpathlink",
            ),
        ),
        migrations.RunPython(_copy_links_and_uuid_rows, _drop_copied_links),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="card",
                    name="changed_files",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="cards",
                        through="kanban.CardPathLink",
                        to="kanban.trackedpath",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql='DROP TABLE "kanban_card_changed_files";',
                    reverse_sql=_RECREATE_AUTO_TABLE_SQL,
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="cardpathlink",
            constraint=models.UniqueConstraint(
                fields=("card", "path"),
                name="unique_card_path_link",
            ),
        ),
        migrations.AddConstraint(
            model_name="cardpathlink",
            constraint=models.CheckConstraint(
                condition=models.Q(kind__in=["changed", "predicted"]),
                name="card_path_link_kind_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="uuidmodel",
            constraint=models.CheckConstraint(
                condition=django.db.models.lookups.Exact(
                    apps.kanban.constraints.OneHotLinkCount(*_ONE_HOT_LINK_NAMES),
                    models.Value(1),
                ),
                name="kanban_uuidmodel_exactly_one_link",
            ),
        ),
    ]
