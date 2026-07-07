"""Shared bootstrap for the benchmark scripts.

Single-sites the fakeshop Django bring-up both benches spelled separately
(``bench_plan_cache.py`` / ``bench_nested_fetch.py``): the example-project
``sys.path`` seam, settings module, ``django.setup()``, and the
``migrate --run-syncdb`` pass. Only the database TAIL differs per bench and
is selected by ``mode`` (docs/feedback.md DRY pass, T6).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

FAKESHOP = Path(__file__).resolve().parent.parent / "examples" / "fakeshop"


def bootstrap_fakeshop_django(mode: str) -> None:
    """Configure Django for the fakeshop example project and migrate.

    ``mode`` selects the database tail:

    - ``"sqlite-memory"``: repoint the default alias at ``:memory:`` BEFORE
      any connection opens, so the tracked ``db.sqlite3`` fixture file is
      never read or written (the plan-cache bench).
    - ``"pg"``: require ``FAKESHOP_PG_DSN`` (the settings module's Postgres
      branch) and refuse a non-Postgres vendor - the lateral strategy only
      executes on Postgres, so there is nothing to compare on SQLite (the
      nested-fetch bench).
    """
    sys.path.insert(0, str(FAKESHOP))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    if mode == "pg" and not os.environ.get("FAKESHOP_PG_DSN"):
        sys.exit(
            "FAKESHOP_PG_DSN is required: the lateral strategy only executes on "
            "Postgres, so there is nothing to compare on SQLite. Start the "
            "throwaway server (docker compose -f docker-compose.postgres.yml up -d) "
            "and re-run with FAKESHOP_PG_DSN=postgres://fakeshop:fakeshop@127.0.0.1:5432/fakeshop.",
        )

    import django

    django.setup()

    if mode == "sqlite-memory":
        from django.conf import settings

        settings.DATABASES["default"]["NAME"] = ":memory:"
    else:
        from django.db import connection

        if connection.vendor != "postgresql":
            sys.exit(f"Expected a postgresql connection, got {connection.vendor!r}.")

    from django.core.management import call_command

    call_command("migrate", run_syncdb=True, verbosity=0)
