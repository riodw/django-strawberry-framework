"""Seed the Phase 2 work-tracking lookups and the maintainer actor.

Data-only migration: creates the ``AttemptOutcome`` / ``VerificationKind`` rows
and the single ``maintainer`` (human) ``Actor``, each with its ``UUIDModel``
side-row. Data migrations run against historical models, so the ``post_save``
``create_uuid_row`` signal does not fire -- the side-rows are created explicitly
here (mirroring migration 0012's ``_copy_links_and_uuid_rows``).

The reverse deletes the seeded rows by key (their UUID side-rows cascade),
unconditionally -- rows edited after seeding are removed all the same.
"""

from django.db import migrations

ATTEMPT_OUTCOMES = (
    ("succeeded", "Succeeded"),
    ("failed", "Failed"),
    ("abandoned", "Abandoned"),
    ("blocked", "Blocked"),
)
VERIFICATION_KINDS = (
    ("test_run", "Test run"),
    ("coverage_gate", "Coverage gate"),
    ("manual", "Manual"),
    ("live_query", "Live query"),
)
MAINTAINER_ACTOR = ("maintainer", "Maintainer", "human")


def _seed(apps, schema_editor):
    alias = schema_editor.connection.alias
    AttemptOutcome = apps.get_model("kanban", "AttemptOutcome")
    VerificationKind = apps.get_model("kanban", "VerificationKind")
    Actor = apps.get_model("kanban", "Actor")
    UUIDModel = apps.get_model("kanban", "UUIDModel")

    for order, (key, label) in enumerate(ATTEMPT_OUTCOMES):
        row, created = AttemptOutcome.objects.using(alias).get_or_create(
            key=key,
            defaults={"label": label, "order": order},
        )
        if created:
            UUIDModel.objects.using(alias).create(attemptoutcome=row)

    for order, (key, label) in enumerate(VERIFICATION_KINDS):
        row, created = VerificationKind.objects.using(alias).get_or_create(
            key=key,
            defaults={"label": label, "order": order},
        )
        if created:
            UUIDModel.objects.using(alias).create(verificationkind=row)

    key, label, kind = MAINTAINER_ACTOR
    actor, created = Actor.objects.using(alias).get_or_create(
        key=key,
        defaults={"label": label, "kind": kind, "order": 0},
    )
    if created:
        UUIDModel.objects.using(alias).create(actor=actor)


def _unseed(apps, schema_editor):
    alias = schema_editor.connection.alias
    AttemptOutcome = apps.get_model("kanban", "AttemptOutcome")
    VerificationKind = apps.get_model("kanban", "VerificationKind")
    Actor = apps.get_model("kanban", "Actor")

    AttemptOutcome.objects.using(alias).filter(
        key__in=[key for key, _ in ATTEMPT_OUTCOMES],
    ).delete()
    VerificationKind.objects.using(alias).filter(
        key__in=[key for key, _ in VERIFICATION_KINDS],
    ).delete()
    Actor.objects.using(alias).filter(key=MAINTAINER_ACTOR[0]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0013_worklog_dimension"),
    ]

    operations = [
        migrations.RunPython(_seed, _unseed),
    ]
