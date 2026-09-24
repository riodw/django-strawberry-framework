"""Benchmark the optimizer's selection-tree WALK (the plan-cache-miss path).

Complements ``scripts/bench_plan_cache.py``. That script measures the
STEADY-STATE win of serving a finished ``OptimizationPlan`` from the
cross-request cache (warm vs cold, end to end). This script isolates the COLD
path itself - the walker's plan BUILD - which is what runs on every plan-cache
miss (cold start, or a workload with high query-shape churn) and on every
request for a non-cacheable plan.

Why a dedicated harness instead of ``bench_plan_cache.py``'s ``cold - warm``
delta: that delta runs the walk through a full ``schema.execute_sync`` - GraphQL
parse, validation, SQL, and the ``ast_to_converted_selections`` conversion all
land on top of the walk. A walker micro-optimization worth a few percent of the
walk is invisible under that noise. Here we capture a real
``(selections, model, info, origin)`` tuple ONCE per candidate query (by
intercepting the extension's call into ``plan_optimizations``), then replay the
REAL ``walker.plan_optimizations`` on those FIXED inputs in a tight loop. Holding
the inputs constant strips DB, parse, and conversion cost, so the measured time
is the selection-tree walk and plan build, and nothing else.

``_bench_common.reset_plan_cache`` clears the plan cache and the
document-key memo before each capture, so a shape the shared extension
already planned still reaches the walker; the timed replay calls the walker
directly and reads neither cache. The walk cost is
row-count-independent (it is a function of the selection tree, not the result
set), so seeding is only needed to make one real execution run its resolvers;
the glossary candidates run on ``--glossary-terms`` seeded terms. Each query
runs ``--rounds`` timed rounds; ``min`` is the fastest walk of any round,
``median`` the median of per-round medians and ``+-%`` the spread of those
medians. A query that errors or triggers no walk fails the run (exit 1) after
the table prints.

What moves the figure: ``optimizer/walker.py``, ``plans.py``, ``selections.py``,
``join_taxonomy.py``, ``utils/relations.py`` and the registry lookups they
make. What it cannot see: the extension's cache key and hit path, nested
connection planning and every fetch strategy; those need
``bench_plan_cache.py`` or a query-count test.

Runs entirely in-process against an in-memory SQLite database; it never touches
the tracked ``examples/fakeshop/db.sqlite3``.

Usage::

    uv run python scripts/bench_optimizer_walk.py
    uv run python scripts/bench_optimizer_walk.py --iterations 20000 --seed 5 --rounds 5
    uv run python scripts/bench_optimizer_walk.py --query op.graphql --variables '{"a": 1}'
    uv run python scripts/bench_optimizer_walk.py --json before.json
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path
from typing import Any, NamedTuple

from _bench_common import (
    FAKESHOP,
    bootstrap_fakeshop_django,
    build_report,
    load_graphql_document,
    parse_variables,
    reset_plan_cache,
    seed_glossary_terms,
    summarize_rounds,
    write_report,
)

_FAKESHOP = FAKESHOP

# Below this many measured iterations the per-call median/min are dominated by
# scheduler and GC noise, so the headline ns/call is flagged rather than trusted.
_MIN_RELIABLE_ITERATIONS = 1000


def _bootstrap_django() -> Any:
    """Configure Django against an in-memory DB, print provenance, and migrate.

    Deprecated alias kept for callers that import it: the bring-up has one
    owner, ``_bench_common.bootstrap_fakeshop_django``, which repoints every
    alias before any connection opens.
    """
    return bootstrap_fakeshop_django("sqlite-memory")


# Candidate queries chosen to stress the walk on different axes: a scalar-heavy
# shape (many ``only_fields`` appends - the ``_IndexedList`` key-call axis), a
# broad one-level-relation shape (fragment inlining + alias merge per level), and
# a deep nested shape (walk recursion depth). A connection shape exercises the
# ``apply_connection_optimization`` -> ``apply_to`` capture path in addition to
# the middleware path. A query that errors is reported and fails the run.
CANDIDATES: dict[str, str] = {
    "glossary scalar (scalar-heavy walk)": """
        query { allGlossaryTerms { title anchor statusText body } }
    """,
    "glossary nested (relation fan-out)": """
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
    "glossary deep (deep recursion)": """
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
    "products connection (edges/node unwrap)": """
        query { allItems { edges { node { name description } } } }
    """,
}


class _Capture(NamedTuple):
    """One recorded ``plan_optimizations`` invocation, replayable in isolation."""

    selections: list[Any]
    model: type
    info: Any
    source_type: type | None


def _capture_walk_inputs(
    schema: Any,
    query: str,
    *,
    optimizer: Any = None,
    variables: dict[str, Any] | None = None,
) -> _Capture | None:
    """Run ``query`` once, intercepting the first call into ``plan_optimizations``.

    Monkeypatches the name ``plan_optimizations`` in ``optimizer.extension``'s
    namespace (where the extension looks it up) with a recorder that stores the
    first invocation's arguments and then delegates to the real walker so the
    execution still completes. Both the middleware path (``_optimize`` ->
    ``_get_or_build_plan``) and the connection path
    (``apply_connection_optimization`` -> ``apply_to`` -> ``_get_or_build_plan``)
    route through this single call site, so one recorder covers both.

    ``optimizer`` is the schema's extension instance; its plan cache and the
    document-key memo are cleared first (``reset_plan_cache``), because a
    plan-cache hit skips the walker and would read as a query with nothing to
    optimize.

    Returns ``None`` when the query triggers no walk (nothing to optimize).
    """
    from django_strawberry_framework.optimizer import extension as ext_mod
    from django_strawberry_framework.optimizer import walker as walker_mod

    real_plan_optimizations = walker_mod.plan_optimizations
    captured: list[_Capture] = []

    def _recorder(
        selected_fields: list[Any],
        model: type,
        info: Any = None,
        *,
        runtime_prefixes: Any = None,
        source_type: type | None = None,
    ) -> Any:
        if not captured:
            captured.append(_Capture(selected_fields, model, info, source_type))
        return real_plan_optimizations(
            selected_fields,
            model,
            info,
            runtime_prefixes=runtime_prefixes,
            source_type=source_type,
        )

    if optimizer is not None:
        reset_plan_cache(optimizer)
    ext_mod.plan_optimizations = _recorder
    try:
        result = schema.execute_sync(query, variable_values=variables)
    finally:
        ext_mod.plan_optimizations = real_plan_optimizations
    if result.errors:
        raise RuntimeError(result.errors)
    return captured[0] if captured else None


def _bench_capture(capture: _Capture, iterations: int, warmup: int) -> list[int]:
    """Return per-call timings (ns) for ``plan_optimizations`` on fixed inputs.

    Calls the REAL walker (not the recorder) directly, bypassing the plan cache
    entirely, so every iteration pays the full walk. The walker does not mutate
    its input ``selected_fields`` (``_merge_aliased_selections`` and
    ``with_runtime_prefix`` build fresh clones), so replaying on the captured
    list is deterministic.
    """
    from django_strawberry_framework.optimizer.walker import plan_optimizations

    timings: list[int] = []
    for i in range(iterations + warmup):
        start = time.perf_counter_ns()
        plan_optimizations(
            capture.selections,
            capture.model,
            info=capture.info,
            source_type=capture.source_type,
        )
        elapsed = time.perf_counter_ns() - start
        if i >= warmup:
            timings.append(elapsed)
    return timings


def _plan_shape(capture: _Capture) -> str:
    """Return a compact ``sr/pf/only/fk/keys`` summary of the built plan."""
    from django_strawberry_framework.optimizer.walker import plan_optimizations

    plan = plan_optimizations(
        capture.selections,
        capture.model,
        info=capture.info,
        source_type=capture.source_type,
    )
    return (
        f"sr={len(plan.select_related)} pf={len(plan.prefetch_related)} "
        f"only={len(plan.only_fields)} fk={len(plan.fk_id_elisions)} "
        f"keys={len(plan.planned_resolver_keys)}"
    )


def _us(ns: float) -> float:
    return ns / 1000.0


def main() -> int:
    """Parse args, bootstrap the example project, and print the walk benchmark."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--iterations", type=int, default=10000, help="measured walks per query")
    parser.add_argument("--warmup", type=int, default=500, help="discarded warmup walks per query")
    parser.add_argument("--seed", type=int, default=3, help="Item rows per Faker provider to seed")
    parser.add_argument(
        "--glossary-terms",
        type=int,
        default=20,
        help="glossary terms to seed, each with one row per relation (default 20)",
    )
    parser.add_argument("--rounds", type=int, default=3, help="timed rounds per query (default 3)")
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

    provenance = _bootstrap_django()

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
        f"\noptimizer-walk benchmark - {args.iterations} walks/query "
        f"({args.warmup} warmup) x {args.rounds} rounds, seed={args.seed}\n"
        f"seeded rows: Item={item_rows}, GlossaryTerm={glossary_rows['GlossaryTerm']}\n"
        "Measures walker.plan_optimizations() on fixed captured inputs "
        "(no DB / parse / conversion).\n",
    )
    if args.iterations < _MIN_RELIABLE_ITERATIONS:
        print(
            f"NOTE: {args.iterations} iterations is below the "
            f"{_MIN_RELIABLE_ITERATIONS}-iteration reliability floor; "
            "figures are noise-dominated.\n",
        )
    width = max(44, *(len(label) for label in candidates))
    header = (
        f"{'query':<{width}} {'min us':>8} {'median us':>10} {'+-%':>5} "
        f"{'mean us':>8} {'stdev us':>9} plan shape"
    )
    print(header)
    print("-" * (len(header) + 30))

    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for label, query in candidates.items():
        try:
            capture = _capture_walk_inputs(
                schema,
                query,
                optimizer=_optimizer,
                variables=variables,
            )
        except RuntimeError as exc:
            print(f"{label:<{width}} ERROR (query failed): {exc}")
            failures.append(f"{label}: {exc}")
            rows.append({"error": str(exc), "label": label, "status": "error"})
            continue
        if capture is None:
            reason = "no walk triggered - nothing to optimize"
            print(f"{label:<{width}} SKIPPED ({reason})")
            failures.append(f"{label}: {reason}")
            rows.append({"error": reason, "label": label, "status": "skipped"})
            continue

        round_timings = [
            _bench_capture(capture, args.iterations, args.warmup) for _ in range(args.rounds)
        ]
        timings = [sample for samples in round_timings for sample in samples]
        summary = summarize_rounds(round_timings)
        shape = _plan_shape(capture)
        mean = statistics.fmean(timings)
        stdev = statistics.stdev(timings) if len(timings) > 1 else 0.0
        print(
            f"{label:<{width}} {_us(summary['min']):>8.2f} {_us(summary['median']):>10.2f} "
            f"{summary['spread_pct']:>5.1f} {_us(mean):>8.2f} {_us(stdev):>9.2f} {shape}",
        )
        rows.append(
            {
                "label": label,
                "plan_shape": shape,
                "status": "ok",
                "walk_us": {
                    "mean": _us(mean),
                    "median": _us(summary["median"]),
                    "min": _us(summary["min"]),
                    "spread": _us(summary["spread"]),
                    "spread_pct": summary["spread_pct"],
                    "stdev": _us(stdev),
                },
            },
        )

    print(
        "\nmin = fastest observed walk (least noise-perturbed; the cleanest signal "
        "for a CPU-bound micro-benchmark).\n"
        "median = median of per-round medians; +-% = spread of the round medians as a "
        "percentage of the median.\n"
        "Each walk is one full plan_optimizations() build - the work the plan cache "
        "eliminates on a hit and pays in full on a miss.\n"
        "Compare min/median across a code change to size a walker optimization; a "
        "few percent here is invisible in an end-to-end run.",
    )

    if args.json_path:
        write_report(
            args.json_path,
            build_report(
                tool="bench_optimizer_walk",
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
        print(f"FAILED: {len(failures)} query(ies) errored or were skipped", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
