"""Benchmark the optimizer's selection-tree WALK (the plan-cache-miss path).

Complements ``scripts/bench_plan_cache.py``. That script measures the
STEADY-STATE win of serving a finished ``OptimizationPlan`` from the
cross-request cache (warm vs cold, end to end). This script isolates the COLD
path itself - the walker's plan BUILD - which is what runs on every plan-cache
miss (cold start, or a workload with high query-shape churn) and is where the
remaining optimization candidates live (the throwaway list in
``included_field_selections``, the per-append ``_IndexedList`` key call, the
duplicate ``_resolve_field_map`` on the FK-id-elision path).

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

The walk cost is row-count-independent (it is a function of the selection tree,
not the result set), so seeding is only needed to make one real execution run
its resolvers - the loop timing does not depend on how much data is seeded.

Runs entirely in-process against an in-memory SQLite database; it never touches
the tracked ``examples/fakeshop/db.sqlite3``.

Usage::

    uv run python scripts/bench_optimizer_walk.py
    uv run python scripts/bench_optimizer_walk.py --iterations 20000 --seed 5
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any, NamedTuple

_FAKESHOP = Path(__file__).resolve().parent.parent / "examples" / "fakeshop"

# Below this many measured iterations the per-call median/min are dominated by
# scheduler and GC noise, so the headline ns/call is flagged rather than trusted.
_MIN_RELIABLE_ITERATIONS = 1000


def _bootstrap_django() -> None:
    """Configure Django against an in-memory DB and migrate it.

    The in-memory override happens before any connection is opened, so the
    on-disk ``db.sqlite3`` is never read or written (mirrors
    ``bench_plan_cache.py``).
    """
    sys.path.insert(0, str(_FAKESHOP))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django
    from django.conf import settings

    django.setup()
    settings.DATABASES["default"]["NAME"] = ":memory:"

    from django.core.management import call_command

    call_command("migrate", run_syncdb=True, verbosity=0)


# Candidate queries chosen to stress the walk on different axes: a scalar-heavy
# shape (many ``only_fields`` appends - the ``_IndexedList`` key-call axis), a
# broad one-level-relation shape (fragment inlining + alias merge per level), and
# a deep nested shape (walk recursion depth). A connection shape exercises the
# ``apply_connection_optimization`` -> ``apply_to`` capture path in addition to
# the middleware path. Queries the schema rejects are skipped with a note.
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


def _capture_walk_inputs(schema: Any, query: str) -> _Capture | None:
    """Run ``query`` once, intercepting the first call into ``plan_optimizations``.

    Monkeypatches the name ``plan_optimizations`` in ``optimizer.extension``'s
    namespace (where the extension looks it up) with a recorder that stores the
    first invocation's arguments and then delegates to the real walker so the
    execution still completes. Both the middleware path (``_optimize`` ->
    ``_get_or_build_plan``) and the connection path
    (``apply_connection_optimization`` -> ``apply_to`` -> ``_get_or_build_plan``)
    route through this single call site, so one recorder covers both.

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

    ext_mod.plan_optimizations = _recorder
    try:
        result = schema.execute_sync(query)
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=10000, help="measured walks per query")
    parser.add_argument("--warmup", type=int, default=500, help="discarded warmup walks per query")
    parser.add_argument("--seed", type=int, default=3, help="Item rows per Faker provider to seed")
    args = parser.parse_args()

    _bootstrap_django()

    from apps.products.services import seed_data
    from config.schema import schema

    seed_data(args.seed)

    print(
        f"optimizer-walk benchmark - {args.iterations} walks/query "
        f"({args.warmup} warmup), seed={args.seed}\n"
        "Measures walker.plan_optimizations() on fixed captured inputs "
        "(no DB / parse / conversion).\n",
    )
    if args.iterations < _MIN_RELIABLE_ITERATIONS:
        print(
            f"NOTE: {args.iterations} iterations is below the "
            f"{_MIN_RELIABLE_ITERATIONS}-iteration reliability floor; "
            "figures are noise-dominated.\n",
        )
    header = (
        f"{'query':<44} {'min us':>8} {'median us':>10} "
        f"{'mean us':>8} {'stdev us':>9} {'plan shape':>0}"
    )
    print(header)
    print("-" * 92)

    for label, query in CANDIDATES.items():
        try:
            capture = _capture_walk_inputs(schema, query)
        except RuntimeError as exc:
            print(f"{label:<44} SKIPPED (schema rejected query): {exc}")
            continue
        if capture is None:
            print(f"{label:<44} SKIPPED (no walk triggered - nothing to optimize)")
            continue

        timings = _bench_capture(capture, args.iterations, args.warmup)
        shape = _plan_shape(capture)
        mn = min(timings)
        median = statistics.median(timings)
        mean = statistics.fmean(timings)
        stdev = statistics.stdev(timings) if len(timings) > 1 else 0.0
        print(
            f"{label:<44} {_us(mn):>8.2f} {_us(median):>10.2f} "
            f"{_us(mean):>8.2f} {_us(stdev):>9.2f} {shape}",
        )

    print(
        "\nmin = fastest observed walk (least noise-perturbed; the cleanest signal "
        "for a CPU-bound micro-benchmark).\n"
        "Each walk is one full plan_optimizations() build - the work the plan cache "
        "eliminates on a hit and pays in full on a miss.\n"
        "Compare min/median across a code change to size a walker optimization; a "
        "few percent here is invisible in an end-to-end run.",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
