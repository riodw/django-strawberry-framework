r"""Benchmark the nested-connection fetch strategies on live Postgres data.

The regression bench for the nested-connection fetch path
(``optimizer/lateral_fetch.py``, ``optimizer/nested_fetch.py``): on seeded
Postgres data it measures the same nested-connection GraphQL request under

* **windowed** - the default strategy: one query that ``ROW_NUMBER()``s EVERY
  child of every selected parent before filtering to the page (O(sum of all
  partition sizes) per request);
* **lateral** - ``unnest(parent_ids) CROSS JOIN LATERAL (... LIMIT-shaped
  page ...)``: one query that pages per parent (O(parents x page) on
  Postgres >= 15 via the monotonic-window run condition);
* **per-parent** - the optimizer-off fallback pipeline (2 + N queries), the
  floor both strategies exist to beat.

Each request shape runs with and without ``totalCount`` (the conditional
count annotation changes both strategies' work), so the report shows where
the lateral win comes from and what the count costs. Executions are full
``schema.execute_sync`` GraphQL requests, so parse/validate time is shared
across modes and the deltas isolate fetch strategy + SQL.

Requires a Postgres target: run with the repo's throwaway server, e.g.::

    docker compose -f docker-compose.postgres.yml up -d
    FAKESHOP_PG_DSN=postgres://fakeshop:fakeshop@127.0.0.1:5432/fakeshop \\
        uv run python scripts/bench_nested_fetch.py
    FAKESHOP_PG_DSN=... uv run python scripts/bench_nested_fetch.py \\
        --parents 500 --children 50 --iterations 30

The script migrates and RESEEDS the library tables in the target database
(deleting existing library rows) - point it only at a scratch database.

Every mode must return the same ``data`` for a shape, a ``lateral`` cell must
have executed ``CROSS JOIN LATERAL`` SQL and no other cell may have; any
violation fails the run (exit 1) after the table prints, because the lateral
strategy falls back to the windowed body silently.

``--sqlite-smoke`` runs windowed against per-parent on the in-memory SQLite
database instead (no Postgres, no ``FAKESHOP_PG_DSN``): it covers
``plans.py``, ``connection.py`` and ``nested_fetch.py`` changes and reports
lateral as unavailable. Its figures are ``vendor=sqlite`` and never comparable
to a Postgres run::

    uv run python scripts/bench_nested_fetch.py --sqlite-smoke --parents 50 --iterations 10
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from typing import Any

from _bench_common import (
    bootstrap_fakeshop_django,
    build_report,
    capture_queries,
    is_memory_db_name,
    write_report,
)


def _seed(parents: int, children: int) -> None:
    """Reseed ``parents`` shelves x ``children`` books (dense, uniform fan-out).

    Also creates the page-order index ``(shelf_id, id)`` a production consumer
    of per-parent pagination would carry: the lateral strategy's
    O(parents x page) shape depends on each lateral branch satisfying its
    ``ORDER BY`` from an index (Postgres stops the branch after the page via
    the row-number run condition). Without it every branch re-sorts its
    partition and the lateral win shrinks to "skips the global sort".
    """
    from apps.library.models import Book, Branch, Shelf
    from django.db import connection

    Book.objects.all().delete()
    Shelf.objects.all().delete()
    Branch.objects.all().delete()
    branch = Branch.objects.create(name="bench-central")
    shelves = Shelf.objects.bulk_create(
        Shelf(code=f"s{index}", branch=branch) for index in range(parents)
    )
    Book.objects.bulk_create(
        Book(title=f"s{shelf_index}-b{book_index}", shelf=shelf)
        for shelf_index, shelf in enumerate(shelves)
        for book_index in range(children)
    )
    with connection.cursor() as cursor:
        # Drop-then-create: IF NOT EXISTS would silently keep a same-named
        # index with a DIFFERENT column list from an earlier experiment, and
        # a mismatched page-order index is worse than none (the planner may
        # walk the pk index filtering on shelf_id - O(table) per branch).
        cursor.execute("DROP INDEX IF EXISTS bench_book_page_order")
        cursor.execute(
            "CREATE INDEX bench_book_page_order ON library_book (shelf_id, id)",
        )
        cursor.execute("ANALYZE library_book")


def _build_schemas(*, lateral: bool = True) -> dict[str, Any]:
    """One finalized type graph, one schema per mode (the parity-test shape).

    Type declaration and strategy mounting come from the shared
    ``strategy_schemas`` module (importable once ``bootstrap_fakeshop_django``
    put the example project on ``sys.path``) - the SAME builders the pg
    parity suite uses, so the bench and the correctness tests cannot compare
    differently-constructed schemas. ``lateral=False`` omits the lateral
    schema for a vendor that cannot run it.
    """
    import strawberry
    from apps.library.models import Book, Shelf
    from strategy_schemas import build_strategy_schema, make_django_type

    from django_strawberry_framework import DjangoListField, finalize_django_types

    make_django_type(
        "BookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}},
    )
    shelf_type = make_django_type("ShelfType", Shelf, ("id", "code", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"shelves": list[shelf_type]},
                "shelves": DjangoListField(shelf_type),
            },
        ),
    )
    schemas = {"windowed": build_strategy_schema(query_cls, "windowed")}
    if lateral:
        schemas["lateral"] = build_strategy_schema(query_cls, "lateral")
    schemas["per-parent"] = build_strategy_schema(query_cls, None)
    return schemas


_PAGE_WITHOUT_COUNT = "edges { cursor node { title } } pageInfo { hasPreviousPage }"
_PAGE_WITH_COUNT = (
    "edges { cursor node { title } } totalCount pageInfo { hasNextPage hasPreviousPage }"
)


def _queries(page_size: int) -> list[tuple[str, str]]:
    return [
        (
            f"first:{page_size} count-free",
            f"{{ shelves {{ id booksConnection(first: {page_size}) "
            f"{{ {_PAGE_WITHOUT_COUNT} }} }} }}",
        ),
        (
            f"first:{page_size} totalCount",
            f"{{ shelves {{ id booksConnection(first: {page_size}) {{ {_PAGE_WITH_COUNT} }} }} }}",
        ),
    ]


def _run(schema: Any, document: str, iterations: int) -> tuple[list[float], int, bool, Any]:
    """Time ``iterations`` requests and inspect one counted request.

    Returns the timing samples (ms), the per-request query count, whether
    the counted request executed lateral SQL - the strategy falls back
    silently, so the report must prove which path actually ran - and the
    counted request's ``data`` for the cross-mode parity check.
    """
    result = schema.execute_sync(document)  # warmup + correctness check
    if result.errors:
        raise SystemExit(f"benchmark query failed: {result.errors}")
    samples = []
    with capture_queries() as ctx:
        counted = schema.execute_sync(document)
    query_count = len(ctx)
    lateral_used = any("CROSS JOIN LATERAL" in entry["sql"] for entry in ctx.captured_queries)
    for _ in range(iterations):
        started = time.perf_counter()
        schema.execute_sync(document)
        samples.append((time.perf_counter() - started) * 1000.0)
    return samples, query_count, lateral_used, counted.data


def _postgres_server_version() -> str:
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("SHOW server_version")
        return str(cursor.fetchone()[0])


def main() -> int:
    """Parse args, seed the target database, and print the strategy matrix."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--parents", type=int, default=200, help="shelf count (default 200)")
    parser.add_argument(
        "--children",
        type=int,
        default=30,
        help="books per shelf (default 30)",
    )
    parser.add_argument("--page-size", type=int, default=2, help="first: N page (default 2)")
    parser.add_argument(
        "--iterations",
        type=int,
        default=20,
        help="timed requests per mode (default 20)",
    )
    parser.add_argument(
        "--sqlite-smoke",
        action="store_true",
        help="windowed vs per-parent on in-memory SQLite; lateral reported unavailable",
    )
    parser.add_argument("--json", dest="json_path", help="also write the report as JSON here")
    args = parser.parse_args()

    provenance = bootstrap_fakeshop_django("sqlite-memory" if args.sqlite_smoke else "pg")

    import django.conf
    from django.db import connection

    # Fakeshop settings refuse to load with DEBUG off; set explicitly so every
    # mode's timed loop pays the same debug-cursor cost whatever the settings say.
    django.conf.settings.DEBUG = True

    if args.sqlite_smoke:
        # ``_seed`` deletes every library row: refuse anything but the
        # process-private in-memory database before it runs.
        name = connection.settings_dict["NAME"]
        if connection.vendor != "sqlite" or not is_memory_db_name(name):
            msg = f"--sqlite-smoke needs an in-memory sqlite database, got {connection.vendor} {name}"
            raise RuntimeError(msg)
        server_version = "n/a (sqlite)"
    else:
        server_version = _postgres_server_version()
    print(f"  server    {connection.vendor} {server_version}")

    _seed(args.parents, args.children)
    schemas = _build_schemas(lateral=not args.sqlite_smoke)

    print(
        f"\nnested-fetch benchmark ({connection.vendor}) - {args.parents} parents x "
        f"{args.children} children, page first:{args.page_size}, "
        f"{args.iterations} timed requests per cell",
    )
    print(
        "windowed row-numbers every child of every parent; lateral pages per parent; "
        "per-parent is the optimizer-off 2+N floor.",
    )
    print()
    header = (
        f"{'query':28} {'mode':11} {'min ms':>9} {'median ms':>10} {'queries':>8} {'lateral':>8}"
    )
    print(header)
    print("-" * len(header))
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for label, document in _queries(args.page_size):
        data_by_mode: dict[str, Any] = {}
        for mode, schema in schemas.items():
            samples, query_count, lateral_used, data = _run(schema, document, args.iterations)
            data_by_mode[mode] = data
            print(
                f"{label:28} {mode:11} {min(samples):9.2f} "
                f"{statistics.median(samples):10.2f} {query_count:8d} "
                f"{'yes' if lateral_used else 'no':>8}",
            )
            if (mode == "lateral") != lateral_used:
                failures.append(
                    f"{label} / {mode}: lateral SQL {'ran' if lateral_used else 'did not run'}",
                )
            rows.append(
                {
                    "label": label,
                    "lateral_used": lateral_used,
                    "median_ms": statistics.median(samples),
                    "min_ms": min(samples),
                    "mode": mode,
                    "queries": query_count,
                    "samples": len(samples),
                    "status": "ok",
                },
            )
        if args.sqlite_smoke:
            print(f"{label:28} {'lateral':11} unavailable (needs Postgres)")
            rows.append({"label": label, "mode": "lateral", "status": "unavailable"})
        reference_mode, reference = next(iter(data_by_mode.items()))
        for mode, data in data_by_mode.items():
            if data != reference:
                failures.append(f"{label}: {mode} data differs from {reference_mode}")
        print()
    print(
        "Every mode must return identical data; lateral must beat windowed on both shapes "
        "at dense fan-outs, and both must beat per-parent.",
    )
    for failure in failures:
        print(f"FAILED: {failure}", file=sys.stderr)

    if args.json_path:
        write_report(
            args.json_path,
            build_report(
                tool="bench_nested_fetch",
                provenance={**provenance.as_dict(), "server_version": server_version},
                params={
                    "children": args.children,
                    "iterations": args.iterations,
                    "page_size": args.page_size,
                    "parents": args.parents,
                    "sqlite_smoke": args.sqlite_smoke,
                },
                rows=rows,
                failures=failures,
            ),
        )
        print(f"wrote {args.json_path}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
