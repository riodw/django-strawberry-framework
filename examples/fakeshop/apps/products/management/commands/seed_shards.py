"""Populate the secondary shard SQLite DB used by the multi-DB / stress-test flow.

Purpose
-------
Create (or refresh) ``db_shard_b.sqlite3`` as a committed,
minimal-but-realistic secondary-shard DB.  This gives the sharded mode
a concrete, repeatable starting state and provides a foundation for
stress-testing the package at hundreds-of-thousands of rows without DB
I/O being the bottleneck.

Mode isolation
--------------
Under ``FAKESHOP_SHARDED=1`` ``config.settings`` ADDS the ``shard_b``
alias on top of the existing single-DB layout - the ``default`` alias
keeps pointing at ``db.sqlite3`` in both modes, so a single dev workflow
populates ``default`` either way.  This command only owns the secondary
shard:

* ``default``  -> ``db.sqlite3`` (the existing dev DB; populated via
                 ``manage.py seed_data`` in either mode - NOT this command)
* ``shard_b``  -> ``db_shard_b.sqlite3`` (secondary shard; populated by
                 this command)

What this command does (on ``shard_b``)
---------------------------------------
1. Runs ``migrate`` on ``shard_b`` so the schema exists.
2. Creates a canonical set of test users on ``shard_b`` via
   :func:`create_users(count=1, db_alias="shard_b")`.  The secondary
   shard gets its own independent user population because shard_b is
   a distinct SQLite file from the default dev DB.
3. Calls :func:`seed_data(count, db_alias="shard_b")` with ``--count 1`` by
   default so there's at least one ``Item`` per Faker provider on shard_b
   to exercise the filter / order / aggregate paths.

Usage
-----
Requires the ``FAKESHOP_SHARDED=1`` env var so ``config.settings`` registers
the ``shard_b`` alias::

    FAKESHOP_SHARDED=1 uv run python examples/fakeshop/manage.py seed_shards

Re-run at any time - every step is idempotent (migrations no-op,
create_users is idempotent by username, seed_data only creates the
shortfall).

Stress testing
--------------
Once shard_b is materialized you can point a stress harness directly
at it under the same env var.  The committed shard file is not touched
by the **test suite** (Django creates a separate
``test_db_shard_b.sqlite3`` file during pytest), so growing it with
millions of rows for load testing is safe from a pytest-isolation
standpoint::

    FAKESHOP_SHARDED=1 uv run python examples/fakeshop/manage.py seed_shards --count 5000

**VCS warning.** ``examples/fakeshop/db_shard_b.sqlite3`` is a tracked
binary fixture. Running ``seed_shards --count 5000`` against the
default path mutates that tracked file in place and will leave a huge
dirty diff that is easy to commit accidentally. Safer workflow for
high-volume load testing:

1. Copy the shard DB to a scratch path outside the repo (e.g.
   ``cp examples/fakeshop/db_shard_b.sqlite3 /tmp/shard_b.sqlite3``)
   and point Django at the copy via ``FAKESHOP_SHARDED=1`` plus a
   one-off override of ``DATABASES["shard_b"]["NAME"]``.
2. Or, after stress testing, discard the dirty fixture with
   ``git checkout -- examples/fakeshop/db_shard_b.sqlite3`` UNLESS
   you intend to refresh the committed fixture for the whole team
   (in which case re-run ``seed_shards`` with the default ``--count
   1`` and commit deliberately).
"""

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.products.services import create_users, seed_data

# Aliases this command operates on.  ``default`` is the existing single-DB
# alias (populated via ``manage.py seed_data`` regardless of mode); only
# ``shard_b`` is owned by this command.
SHARD_ALIASES = ("shard_b",)


class Command(BaseCommand):
    help = (
        "Migrate, create users, and seed the secondary shard SQLite DB "
        "(shard_b -> db_shard_b.sqlite3). Requires FAKESHOP_SHARDED=1 in the environment."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--count",
            type=int,
            default=1,
            help="Number of Item instances per Faker provider on shard_b (default: 1)",
        )

    def handle(self, *args, **options) -> None:
        count = options["count"]

        # Fail fast if the sharded mode isn't active.
        if "shard_b" not in settings.DATABASES:
            raise CommandError(
                "Shard alias `shard_b` not declared in DATABASES. "
                "Set `FAKESHOP_SHARDED=1` in the environment so config.settings "
                "selects the sharded DATABASES layout.",
            )

        # 1. Migrate shard_b (creates schema + auth tables).
        for alias in SHARD_ALIASES:
            self.stdout.write(self.style.NOTICE(f"[{alias}] migrate"))
            call_command("migrate", database=alias, interactive=False, verbosity=0)

        # 2. Create users directly on shard_b.  The secondary shard is a
        #    distinct SQLite file from the default dev DB, so it gets its
        #    own freshly-seeded user set via create_users().  Idempotent
        #    by username so re-runs are safe.
        for alias in SHARD_ALIASES:
            self.stdout.write(self.style.NOTICE(f"[{alias}] create_users"))
            user_result = create_users(count=1, db_alias=alias)
            self.stdout.write(f"  {alias}: {user_result['users']} users")

        # 3. Seed products content on shard_b.
        for alias in SHARD_ALIASES:
            self.stdout.write(self.style.NOTICE(f"[{alias}] seed_data(count={count})"))
            result = seed_data(count, db_alias=alias)
            self.stdout.write(
                self.style.SUCCESS(
                    f"  {alias}: {result['categories']} categories, "
                    f"{result['properties']} properties, "
                    f"{result['items']} items, {result['entries']} entries",
                ),
            )

        self.stdout.write(self.style.SUCCESS("Secondary shard populated."))
