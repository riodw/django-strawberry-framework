"""Benchmark the optimizer's cross-request plan cache (B1).

The plan cache is the package's single clearest performance advantage over
``strawberry-graphql-django``: that package rebuilds the entire selection-tree
walk on *every* request (a throwaway per-request ``cache`` dict), whereas this
package walks a given operation once and serves the finished
``OptimizationPlan`` from a 256-entry LRU on every subsequent request with the
same shape.

This script quantifies that. For each candidate query it runs two modes
against the *same* seeded database:

* **warm** - the default behaviour: the plan cache persists across requests, so
  only the first request walks and the rest are cache hits.
* **cold** - the plan cache (and its counters) are cleared before *every*
  request, forcing a full walk each time. This is the behaviour upstream has by
  construction (no cross-request plan cache exists to clear).

Because both modes execute identical SQL against identical data, DB time and
GraphQL parse time cancel in the difference: ``cold - warm`` isolates exactly
the per-request selection-tree walk that the cache eliminates. ``cache_info()``
reports the realised hit/miss/size counters as independent proof the cache is
serving hits.

The walk cost is row-count-independent (it is a function of the selection tree,
not the result set), so the headline delta holds regardless of how much data is
seeded. A query whose plan is marked non-cacheable (a relation into a type with
a custom ``get_queryset``, a consumer ``Prefetch``, etc.) shows zero hits - the
script reports that honestly rather than hiding it.

Runs entirely in-process against an in-memory SQLite database; it never touches
the tracked ``examples/fakeshop/db.sqlite3``.

Usage::

    uv run python scripts/bench_plan_cache.py
    uv run python scripts/bench_plan_cache.py --iterations 2000 --seed 5
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
    """Configure Django against an in-memory DB and migrate + seed it.

    The in-memory override happens before any connection is opened, so the
    on-disk ``db.sqlite3`` is never read or written.
    """
    sys.path.insert(0, str(_FAKESHOP))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django
    from django.conf import settings

    django.setup()
    # Repoint the default alias at an in-process database so migrate/seed/query
    # all hit throwaway state, never the committed fixture file.
    settings.DATABASES["default"]["NAME"] = ":memory:"

    from django.core.management import call_command

    call_command("migrate", run_syncdb=True, verbosity=0)


# Candidate queries. Mix of cacheable shapes (the headline) and a known
# non-cacheable shape (a relation into a custom-``get_queryset`` type) so the
# report contrasts both. Queries that fail to validate against the schema are
# skipped with a note rather than aborting the run.
CANDIDATES: dict[str, str] = {
    "glossary scalar (cacheable)": """
        query { allGlossaryTerms { title anchor statusText } }
    """,
    "glossary nested (cacheable)": """
        query {
          allGlossaryTerms {
            title
            aliases { id }
            categoryMemberships { id }
            sourceLinks { id }
            outgoingLinks { id }
            incomingLinks { id }
          }
        }
    """,
    "glossary deep (cacheable)": """
        query {
          allGlossaryTerms {
            title anchor statusText body
            aliases { id label normalized }
            relatedTerms { id title }
            categoryMemberships { id category { id } }
            sourceLinks { id }
            outgoingLinks { id rawLabel kind { id key label } targetTerm { id title } }
            incomingLinks { id sourceTerm { id title } }
          }
        }
    """,
    "products scalar": """
        query { allItems { edges { node { name description } } } }
    """,
    "products nested (custom get_queryset -> non-cacheable)": """
        query {
          allItems { edges { node { name category { name } } } }
        }
    """,
}


def _reset(optimizer: Any) -> None:
    optimizer._plan_cache.clear()
    optimizer._cache_hits = 0
    optimizer._cache_misses = 0


def _bench_one(
    schema: Any,
    optimizer: Any,
    query: str,
    iterations: int,
    warmup: int,
    *,
    cold: bool,
) -> tuple[list[int], Any]:
    """Return (timings_ns, cache_info) for ``iterations`` runs of ``query``."""
    _reset(optimizer)
    timings: list[int] = []
    for i in range(iterations + warmup):
        if cold:
            _reset(optimizer)
        start = time.perf_counter_ns()
        result = schema.execute_sync(query)
        elapsed = time.perf_counter_ns() - start
        if result.errors:
            raise RuntimeError(result.errors)
        if i >= warmup:
            timings.append(elapsed)
    return timings, optimizer.cache_info()


def _us(ns: float) -> float:
    return ns / 1000.0


def main() -> int:
    """Parse args, bootstrap the example project, and print the benchmark table."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=1000, help="measured runs per mode")
    parser.add_argument("--warmup", type=int, default=50, help="discarded warmup runs per mode")
    parser.add_argument("--seed", type=int, default=3, help="Item rows per Faker provider to seed")
    args = parser.parse_args()

    _bootstrap_django()

    from apps.products.services import seed_data
    from config.schema import _optimizer, schema

    seed_data(args.seed)

    print(
        f"plan-cache benchmark - {args.iterations} iterations/mode "
        f"({args.warmup} warmup), seed={args.seed}\n",
    )
    header = f"{'query':<52} {'cacheable':>9} {'warm us':>9} {'cold us':>9} {'walk us':>9} {'speedup':>8}"
    print(header)
    print("-" * len(header))

    for label, query in CANDIDATES.items():
        try:
            warm_t, warm_info = _bench_one(
                schema,
                _optimizer,
                query,
                args.iterations,
                args.warmup,
                cold=False,
            )
            cold_t, _ = _bench_one(
                schema,
                _optimizer,
                query,
                args.iterations,
                args.warmup,
                cold=True,
            )
        except RuntimeError as exc:
            print(f"{label:<52} SKIPPED (schema rejected query): {exc}")
            continue

        warm_med = statistics.median(warm_t)
        cold_med = statistics.median(cold_t)
        walk = cold_med - warm_med
        speedup = cold_med / warm_med if warm_med else float("nan")
        cacheable = "yes" if warm_info.hits > 0 else "no"
        print(
            f"{label:<52} {cacheable:>9} {_us(warm_med):>9.1f} {_us(cold_med):>9.1f} "
            f"{_us(walk):>9.1f} {speedup:>7.2f}x",
        )
        print(
            f"{'':<52} cache_info(warm): hits={warm_info.hits} "
            f"misses={warm_info.misses} size={warm_info.size}",
        )

    print(
        "\nwarm = plan cache persists (this package's default).\n"
        "cold = plan cache cleared before every request (upstream's per-request re-walk).\n"
        "walk = cold - warm = the selection-tree walk the cache eliminates per cached request.",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
