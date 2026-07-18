"""Phase 2: the work-tracking dimension (transitions / attempts / decisions).

Adds the ``Actor`` / ``AttemptOutcome`` / ``VerificationKind`` lookups, the
``CardTransition`` / ``WorkAttempt`` / ``Decision`` work-tracking models, the
``CardItem`` verification columns, and ``CardReference.resolved_at`` (2G). Every
new model is wired into the ``UUIDModel`` one-hot side-table in a single
constraint Remove/Add pair wrapping all six new one-to-one links (the one-hot
dance). Lookup rows are seeded by the following migration.
"""

import django.db.models.deletion
import django.db.models.lookups
import django.utils.timezone
from django.db import migrations, models

import apps.kanban.constraints


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0012_cardpathlink_through"),
    ]

    operations = [
        migrations.CreateModel(
            name="Actor",
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
                ("key", models.SlugField(unique=True)),
                ("label", models.TextField()),
                ("order", models.PositiveIntegerField(default=0)),
                (
                    "kind",
                    models.SlugField(
                        choices=[("human", "Human"), ("agent", "Agent")],
                        default="human",
                    ),
                ),
            ],
            options={
                "verbose_name": "actor",
                "verbose_name_plural": "actors",
                "ordering": ["order"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="AttemptOutcome",
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
                ("key", models.SlugField(unique=True)),
                ("label", models.TextField()),
                ("order", models.PositiveIntegerField(default=0)),
            ],
            options={
                "verbose_name": "attempt outcome",
                "verbose_name_plural": "attempt outcomes",
                "ordering": ["order"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CardTransition",
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
                ("note", models.TextField(blank=True, default="")),
                ("occurred_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "verbose_name": "card transition",
                "verbose_name_plural": "card transitions",
                "ordering": ["card", "occurred_at"],
            },
        ),
        migrations.CreateModel(
            name="Decision",
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
                ("question", models.TextField()),
                ("choice", models.TextField()),
                ("rationale", models.TextField(blank=True, default="")),
                ("decided_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "verbose_name": "decision",
                "verbose_name_plural": "decisions",
                "ordering": ["decided_at"],
            },
        ),
        migrations.CreateModel(
            name="VerificationKind",
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
                ("key", models.SlugField(unique=True)),
                ("label", models.TextField()),
                ("order", models.PositiveIntegerField(default=0)),
            ],
            options={
                "verbose_name": "verification kind",
                "verbose_name_plural": "verification kinds",
                "ordering": ["order"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="WorkAttempt",
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
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("summary", models.TextField(blank=True, default="")),
                ("evidence", models.TextField(blank=True, default="")),
            ],
            options={
                "verbose_name": "work attempt",
                "verbose_name_plural": "work attempts",
                "ordering": ["card", "started_at"],
            },
        ),
        migrations.RemoveConstraint(
            model_name="uuidmodel",
            name="kanban_uuidmodel_exactly_one_link",
        ),
        migrations.AddField(
            model_name="carditem",
            name="verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="cardreference",
            name="resolved_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name="actor",
            constraint=models.CheckConstraint(
                condition=models.Q(("kind__in", ["agent", "human"])),
                name="actor_kind_valid",
            ),
        ),
        migrations.AddField(
            model_name="carditem",
            name="verified_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="verified_items",
                to="kanban.actor",
            ),
        ),
        migrations.AddField(
            model_name="uuidmodel",
            name="actor",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="uuid",
                to="kanban.actor",
            ),
        ),
        migrations.AddField(
            model_name="uuidmodel",
            name="attemptoutcome",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="uuid",
                to="kanban.attemptoutcome",
            ),
        ),
        migrations.AddField(
            model_name="cardtransition",
            name="actor",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="transitions",
                to="kanban.actor",
            ),
        ),
        migrations.AddField(
            model_name="cardtransition",
            name="card",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="transitions",
                to="kanban.card",
            ),
        ),
        migrations.AddField(
            model_name="cardtransition",
            name="from_status",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="transitions_from",
                to="kanban.status",
            ),
        ),
        migrations.AddField(
            model_name="cardtransition",
            name="to_status",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="transitions_to",
                to="kanban.status",
            ),
        ),
        migrations.AddField(
            model_name="uuidmodel",
            name="cardtransition",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="uuid",
                to="kanban.cardtransition",
            ),
        ),
        migrations.AddField(
            model_name="decision",
            name="actor",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="decisions",
                to="kanban.actor",
            ),
        ),
        migrations.AddField(
            model_name="decision",
            name="card",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="decisions",
                to="kanban.card",
            ),
        ),
        migrations.AddField(
            model_name="decision",
            name="supersedes",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="superseded_by_set",
                to="kanban.decision",
            ),
        ),
        migrations.AddField(
            model_name="uuidmodel",
            name="decision",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="uuid",
                to="kanban.decision",
            ),
        ),
        migrations.AddField(
            model_name="carditem",
            name="verification_kind",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="card_items",
                to="kanban.verificationkind",
            ),
        ),
        migrations.AddField(
            model_name="uuidmodel",
            name="verificationkind",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="uuid",
                to="kanban.verificationkind",
            ),
        ),
        migrations.AddField(
            model_name="workattempt",
            name="actor",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="work_attempts",
                to="kanban.actor",
            ),
        ),
        migrations.AddField(
            model_name="workattempt",
            name="card",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="work_attempts",
                to="kanban.card",
            ),
        ),
        migrations.AddField(
            model_name="workattempt",
            name="outcome",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="work_attempts",
                to="kanban.attemptoutcome",
            ),
        ),
        migrations.AddField(
            model_name="uuidmodel",
            name="workattempt",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="uuid",
                to="kanban.workattempt",
            ),
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
                        "cardpathlink",
                        "carditem",
                        "label",
                        "boarddoc",
                        "boarddoccardreference",
                        "attemptoutcome",
                        "verificationkind",
                        "actor",
                        "cardtransition",
                        "workattempt",
                        "decision",
                    ),
                    models.Value(1),
                ),
                name="kanban_uuidmodel_exactly_one_link",
            ),
        ),
    ]
