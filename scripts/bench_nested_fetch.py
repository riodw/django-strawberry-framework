r"""Benchmark the nested-connection fetch strategies on live Postgres data.

The spec-045 go/no-go gate for the lateral backend
(``optimizer/lateral_fetch.py``): on seeded Postgres data it measures the
same nested-connection GraphQL request under

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
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any

_FAKESHOP = Path(__file__).resolve().parent.parent / "examples" / "fakeshop"


def _bootstrap_django() -> None:
    """Configure Django against the FAKESHOP_PG_DSN Postgres database."""
    sys.path.insert(0, str(_FAKESHOP))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    if not os.environ.get("FAKESHOP_PG_DSN"):
        sys.exit(
            "FAKESHOP_PG_DSN is required: the lateral strategy only executes on "
            "Postgres, so there is nothing to compare on SQLite. Start the "
            "throwaway server (docker compose -f docker-compose.postgres.yml up -d) "
            "and re-run with FAKESHOP_PG_DSN=postgres://fakeshop:fakeshop@127.0.0.1:5432/fakeshop.",
        )

    import django

    django.setup()

    from django.db import connection

    if connection.vendor != "postgresql":
        sys.exit(f"Expected a postgresql connection, got {connection.vendor!r}.")

    from django.core.management import call_command

    call_command("migrate", run_syncdb=True, verbosity=0)


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


def _build_schemas() -> dict[str, Any]:
    """One finalized type graph, one schema per mode (the parity-test shape)."""
    import strawberry
    from apps.library.models import Book, Shelf
    from strawberry import relay

    from django_strawberry_framework import (
        DjangoListField,
        DjangoOptimizerExtension,
        DjangoType,
        finalize_django_types,
        strawberry_config,
    )

    type(
        "BookType",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": Book,
                    "fields": ("id", "title"),
                    "interfaces": (relay.Node,),
                    "connection": {"total_count": True},
                },
            ),
        },
    )
    shelf_type = type(
        "ShelfType",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": Shelf,
                    "fields": ("id", "code", "books"),
                    "interfaces": (relay.Node,),
                },
            ),
        },
    )
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

    def _schema(strategy: str | None) -> Any:
        extensions = []
        if strategy is not None:
            extensions = [
                lambda: DjangoOptimizerExtension(nested_connection_strategy=strategy),
            ]
        return strawberry.Schema(
            query=query_cls,
            config=strawberry_config(),
            extensions=extensions,
        )

    return {
        "windowed": _schema("windowed"),
        "lateral": _schema("lateral"),
        "per-parent": _schema(None),
    }


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


def _run(schema: Any, document: str, iterations: int) -> tuple[list[float], int, bool]:
    """Time ``iterations`` requests and inspect one counted request.

    Returns the timing samples (ms), the per-request query count, and
    whether the counted request executed lateral SQL - the strategy falls
    back silently, so the report must prove which path actually ran.
    """
    from django.db import connection, reset_queries

    result = schema.execute_sync(document)  # warmup + correctness check
    if result.errors:
        raise SystemExit(f"benchmark query failed: {result.errors}")
    samples = []
    reset_queries()
    connection.queries_log.clear()
    schema.execute_sync(document)
    query_count = len(connection.queries_log)
    lateral_used = any("CROSS JOIN LATERAL" in entry["sql"] for entry in connection.queries_log)
    for _ in range(iterations):
        started = time.perf_counter()
        schema.execute_sync(document)
        samples.append((time.perf_counter() - started) * 1000.0)
    return samples, query_count, lateral_used


def main() -> None:
    """Parse args, seed the Postgres target, and print the strategy matrix."""
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
    args = parser.parse_args()

    _bootstrap_django()

    import django.conf

    # ``connection.queries_log`` only records under DEBUG.
    django.conf.settings.DEBUG = True

    _seed(args.parents, args.children)
    schemas = _build_schemas()

    print(
        f"nested-fetch benchmark - {args.parents} parents x {args.children} children, "
        f"page first:{args.page_size}, {args.iterations} timed requests per cell",
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
    for label, document in _queries(args.page_size):
        for mode, schema in schemas.items():
            samples, query_count, lateral_used = _run(schema, document, args.iterations)
            print(
                f"{label:28} {mode:11} {min(samples):9.2f} "
                f"{statistics.median(samples):10.2f} {query_count:8d} "
                f"{'yes' if lateral_used else 'no':>8}",
            )
        print()
    print(
        "Gate: lateral must beat windowed on both shapes at dense fan-outs "
        "(and both must beat per-parent) before 'auto' ships lateral as the default.",
    )


if __name__ == "__main__":
    main()
