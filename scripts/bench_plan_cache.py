"""Benchmark the optimizer's cross-request plan cache.

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

"Cold" is this package's walker with the plan cache cleared, not upstream:
the module-level document-key memo in ``optimizer/extension.py`` is retained.

Each query runs ``--rounds`` rounds (warm and cold order alternating per round
so drift does not land on one mode); every figure is reported as the fastest
sample, the median of per-round medians, and the spread of those medians. A
walk figure narrower than its spread is noise. The glossary candidates run on
``--glossary-terms`` seeded terms and the products candidates on
``seed_data(--seed)``; the root row count each query returned is printed
beside its timings. Any query that errors fails the run (exit 1) after the
table prints.

Runs entirely in-process against an in-memory SQLite database; it never touches
the tracked ``examples/fakeshop/db.sqlite3``.

Usage::

    uv run python scripts/bench_plan_cache.py
    uv run python scripts/bench_plan_cache.py --iterations 2000 --seed 5 --rounds 5
    uv run python scripts/bench_plan_cache.py --query op.graphql --variables '{"first": 3}'
    uv run python scripts/bench_plan_cache.py --json before.json
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from _bench_common import (
    bootstrap_fakeshop_django,
    build_report,
    capture_queries,
    load_graphql_document,
    parse_variables,
    reset_plan_cache,
    root_row_count,
    seed_glossary_terms,
    summarize_rounds,
    write_report,
)

# Below this many measured iterations, warm-vs-cold timing deltas are dominated
# by noise (a single sample can even make ``cold`` look faster than ``warm``),
# so the per-request walk delta is suppressed rather than reported as if real.
_MIN_RELIABLE_ITERATIONS = 100


# Candidate queries. Mix of cacheable shapes (the headline) and a known
# non-cacheable shape (a relation into a custom-``get_queryset`` type) so the
# report contrasts both. A query that errors is reported and fails the run.
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
    reset_plan_cache(optimizer)


def _bench_one(
    schema: Any,
    optimizer: Any,
    query: str,
    iterations: int,
    warmup: int,
    *,
    cold: bool,
    variables: dict[str, Any] | None = None,
) -> tuple[list[int], Any]:
    """Return (timings_ns, cache_info) for ``iterations`` runs of ``query``."""
    _reset(optimizer)
    timings: list[int] = []
    for i in range(iterations + warmup):
        if cold:
            _reset(optimizer)
        start = time.perf_counter_ns()
        result = schema.execute_sync(query, variable_values=variables)
        elapsed = time.perf_counter_ns() - start
        if result.errors:
            raise RuntimeError(result.errors)
        if i >= warmup:
            timings.append(elapsed)
    return timings, optimizer.cache_info()


def _us(ns: float) -> float:
    return ns / 1000.0


def _us_summary(rounds: list[list[int]]) -> dict[str, float]:
    summary = summarize_rounds(rounds)
    return {
        "min": _us(summary["min"]),
        "median": _us(summary["median"]),
        "spread": _us(summary["spread"]),
        "spread_pct": summary["spread_pct"],
    }


def _probe(schema: Any, query: str, variables: dict[str, Any] | None) -> tuple[int | None, int]:
    """Execute ``query`` once, returning its root row count and SQL query count.

    Raises:
        RuntimeError: the query returned errors.
    """
    with capture_queries() as ctx:
        result = schema.execute_sync(query, variable_values=variables)
    if result.errors:
        raise RuntimeError(result.errors)
    return root_row_count(result.data), len(ctx)


def _measure(
    schema: Any,
    optimizer: Any,
    query: str,
    args: argparse.Namespace,
    variables: dict[str, Any] | None,
) -> dict[str, Any]:
    """Run every round of one query and return its report row.

    Raises:
        RuntimeError: the query returned errors.
    """
    root_rows, sql_queries = _probe(schema, query, variables)
    warm_rounds: list[list[int]] = []
    cold_rounds: list[list[int]] = []
    warm_info = None
    for round_index in range(args.rounds):
        order = (False, True) if round_index % 2 == 0 else (True, False)
        for cold in order:
            timings, info = _bench_one(
                schema,
                optimizer,
                query,
                args.iterations,
                args.warmup,
                cold=cold,
                variables=variables,
            )
            if cold:
                cold_rounds.append(timings)
            else:
                warm_rounds.append(timings)
                warm_info = info
    # Cacheability is a property of the built plan, not of how many hits a
    # given run happened to observe: a single warm execution has zero hits
    # yet the plan IS cached. Read it from cache-entry behaviour - a plan
    # was stored iff the cache holds an entry after the run.
    cacheable = warm_info.size > 0
    warm = _us_summary(warm_rounds)
    cold = _us_summary(cold_rounds)
    walk = None
    speedup = None
    if cacheable:
        round_walks = [
            [statistics.median(c) - statistics.median(w)]
            for w, c in zip(warm_rounds, cold_rounds, strict=True)
        ]
        walk = _us_summary(round_walks)
        # Only present a walk delta when there are enough samples for the
        # median to be stable and the sign to be meaningful; otherwise n/a,
        # never a negative "saved work" figure.
        if args.iterations < _MIN_RELIABLE_ITERATIONS or walk["median"] <= 0:
            walk = None
        elif warm["median"]:
            speedup = cold["median"] / warm["median"]
    return {
        "cache_info": {"hits": warm_info.hits, "misses": warm_info.misses, "size": warm_info.size},
        "cacheable": cacheable,
        "cold_us": cold,
        "root_rows": root_rows,
        "speedup": speedup,
        "sql_queries": sql_queries,
        "walk_us": walk,
        "warm_us": warm,
    }


def _walk_cells(row: dict[str, Any]) -> tuple[str, str]:
    if not row["cacheable"]:
        return "non-cacheable", "n/a"
    if row["walk_us"] is None:
        return "n/a", "n/a"
    return f"{row['walk_us']['median']:.1f}", f"{row['speedup']:.2f}x"


def main() -> int:
    """Parse args, bootstrap the example project, and print the benchmark table."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--iterations", type=int, default=1000, help="measured runs per mode")
    parser.add_argument("--warmup", type=int, default=50, help="discarded warmup runs per mode")
    parser.add_argument("--seed", type=int, default=3, help="Item rows per Faker provider to seed")
    parser.add_argument(
        "--glossary-terms",
        type=int,
        default=20,
        help="glossary terms to seed, each with one row per relation (default 20)",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=3,
        help="repeated warm/cold rounds per query (default 3)",
    )
    parser.add_argument("--query", help="GraphQL file to bench instead of the built-in set")
    parser.add_argument("--variables", help="JSON object of variables for --query")
    parser.add_argument("--json", dest="json_path", help="also write the report as JSON here")
    args = parser.parse_args()
    if args.rounds < 1 or args.iterations < 1:
        parser.error("--rounds and --iterations must be at least 1")
    try:
        variables = parse_variables(args.variables)
    except (TypeError, ValueError) as exc:
        parser.error(str(exc))
    if variables is not None and args.query is None:
        parser.error("--variables needs --query")

    provenance = bootstrap_fakeshop_django("sqlite-memory")

    from apps.products.models import Item
    from apps.products.services import seed_data
    from config.schema import _optimizer, schema

    seed_data(args.seed)
    glossary_rows = seed_glossary_terms(args.glossary_terms)
    item_rows = Item.objects.count()

    candidates = (
        {Path(args.query).name: load_graphql_document(args.query)} if args.query else CANDIDATES
    )

    print(
        f"\nplan-cache benchmark - {args.iterations} iterations/mode "
        f"({args.warmup} warmup) x {args.rounds} rounds, seed={args.seed}",
    )
    print(
        f"seeded rows: Item={item_rows}, GlossaryTerm={glossary_rows['GlossaryTerm']} "
        "(root rows each query returned are in the rows column)\n",
    )
    if args.iterations < _MIN_RELIABLE_ITERATIONS:
        print(
            f"NOTE: {args.iterations} iterations is below the "
            f"{_MIN_RELIABLE_ITERATIONS}-iteration reliability floor; "
            "walk/speedup are suppressed (shown as n/a).\n",
        )
    width = max(len(label) for label in candidates)
    header = (
        f"{'query':<{width}} {'cacheable':>9} {'rows':>5} {'sql':>4} "
        f"{'warm us':>9} {'min':>8} {'+-%':>5} {'cold us':>9} {'min':>8} {'+-%':>5} "
        f"{'walk us':>13} {'speedup':>8}"
    )
    print(header)
    print("-" * len(header))

    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for label, query in candidates.items():
        try:
            row = _measure(schema, _optimizer, query, args, variables)
        except RuntimeError as exc:
            print(f"{label:<{width}} ERROR: {exc}")
            failures.append(f"{label}: {exc}")
            rows.append({"error": str(exc), "label": label, "status": "error"})
            continue
        row.update(label=label, status="ok")
        rows.append(row)
        warm = row["warm_us"]
        cold = row["cold_us"]
        walk_cell, speed_cell = _walk_cells(row)
        root_rows = "?" if row["root_rows"] is None else str(row["root_rows"])
        print(
            f"{label:<{width}} {'yes' if row['cacheable'] else 'no':>9} {root_rows:>5} "
            f"{row['sql_queries']:>4} {warm['median']:>9.1f} {warm['min']:>8.1f} "
            f"{warm['spread_pct']:>5.1f} {cold['median']:>9.1f} {cold['min']:>8.1f} "
            f"{cold['spread_pct']:>5.1f} {walk_cell:>13} {speed_cell:>8}",
        )
        info = row["cache_info"]
        print(
            f"{'':<{width}} cache_info(warm): hits={info['hits']} "
            f"misses={info['misses']} size={info['size']}",
        )
        if row["walk_us"] is not None and row["walk_us"]["spread"] >= row["walk_us"]["median"]:
            print(f"{'':<{width}} walk is inside its round-to-round spread: noise")

    print(
        "\ncacheable = the built plan is cached (the cache holds an entry after the run), "
        "independent of how many hits this run observed.\n"
        "warm = plan cache persists (this package's default).\n"
        "cold = plan cache cleared before every request (document-key memo retained).\n"
        "walk = cold - warm = the selection-tree walk the cache eliminates per cached request "
        f"(n/a below {_MIN_RELIABLE_ITERATIONS} iterations or when noise-dominated; "
        "never computed for a non-cacheable plan, which walks in both modes).\n"
        "us = median of per-round medians; min = fastest sample; +-% = spread of the "
        "round medians as a percentage of the median.",
    )

    if args.json_path:
        write_report(
            args.json_path,
            build_report(
                tool="bench_plan_cache",
                provenance=provenance.as_dict(),
                params={
                    "glossary_rows": glossary_rows,
                    "glossary_terms": args.glossary_terms,
                    "item_rows": item_rows,
                    "iterations": args.iterations,
                    "query": args.query,
                    "rounds": args.rounds,
                    "seed": args.seed,
                    "variables": variables,
                    "warmup": args.warmup,
                },
                rows=rows,
                failures=failures,
            ),
        )
        print(f"wrote {args.json_path}")
    if failures:
        print(f"FAILED: {len(failures)} query(ies) errored", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
