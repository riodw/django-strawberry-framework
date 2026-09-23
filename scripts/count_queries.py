r"""Count the SQL one GraphQL operation issues at several parent cardinalities.

The N+1 detector for query-shape claims: a batched operation issues the same
number of queries however many parent rows it resolves, while a per-row read
adds queries as parents grow. One count proves nothing, so the operation runs
at every ``--cardinalities`` value (ascending) against the fakeshop schema and
the counts are compared:

- ``batched`` - every cell issued the same number of queries;
- ``scales with cardinality`` - the count rose at every step;
- ``mixed`` - anything else (rose at some steps, fell or held at others).

Each cell raises the seeded fixture to that cardinality, executes the
operation once to warm the plan cache and per-process lookups (discarded),
then executes it again inside ``_bench_common.capture_queries`` and records
the query count and the root row count. The verdict is evidence only when the
root rows grew with the cardinality; when they did not (a list cap, a
visibility rule hiding the new rows) the run says so and exits 2.

Seeders (``--seeder``; a built-in operation names its own), all cumulative
and deterministic in row counts:

- ``products`` - ``apps.products.services.seed_data(N)``: N ``Item`` rows per
  Faker provider, each with one ``Entry`` per provider ``Property``; one
  ``Category`` per provider and one ``Property`` per provider method are
  created once. Anonymous reads see the public subset only.
- ``library`` - one ``Branch`` holding N ``Shelf`` rows, each with
  ``BOOKS_PER_SHELF`` ``Book`` rows (inline ``Model.objects.create``; the
  library app has no services module).
- ``glossary`` - ``_bench_common.seed_glossary_terms(N)``: N terms, each with
  one alias, category membership, source link and outgoing link.

Execution is ``schema.execute_sync`` as an anonymous viewer against the
in-memory SQLite database; the tracked ``examples/fakeshop/db.sqlite3`` is
never opened. ``--no-optimizer`` runs the same schema without
``DjangoOptimizerExtension``, the positive control that shows the detector can
report ``scales with cardinality``.

Exit codes: 0 ``batched``; 1 ``scales with cardinality`` or ``mixed``; 2 not
measured (an operation error, root rows that did not grow, fewer than two
cardinalities, or a ``--compare`` baseline for a different operation).

Usage::

    uv run python scripts/count_queries.py --operation-name products-items
    uv run python scripts/count_queries.py --query op.graphql --seeder library \
        --cardinalities 2,10,30 --json after.json --compare before.json
    uv run python scripts/count_queries.py --operation-name library-shelves-books --no-optimizer
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any

from _bench_common import (
    bootstrap_fakeshop_django,
    build_report,
    capture_queries,
    load_graphql_document,
    parse_variables,
    root_row_count,
    seed_glossary_terms,
    write_report,
)

BATCHED = "batched"
SCALES = "scales with cardinality"
MIXED = "mixed"

EXIT_BATCHED = 0
EXIT_GROWS = 1
EXIT_NOT_MEASURED = 2

BOOKS_PER_SHELF = 3
DEFAULT_CARDINALITIES = "2,10,30"


@dataclass(frozen=True)
class Operation:
    """A built-in fakeshop operation and the seeder whose rows it reads."""

    document: str
    seeder: str


BUILTIN_OPERATIONS: dict[str, Operation] = {
    "products-items": Operation(
        document=(
            "query { allItems { edges { node { name category { name } "
            "entries { value property { name } } } } } }"
        ),
        seeder="products",
    ),
    "library-shelves-books": Operation(
        document="query { allLibraryShelves { code books { title } } }",
        seeder="library",
    ),
    "glossary-terms": Operation(
        document=(
            "query { allGlossaryTerms { title aliases { label } "
            "outgoingLinks { targetTerm { title } } } }"
        ),
        seeder="glossary",
    ),
}


def classify_counts(counts: list[int]) -> str:
    """Name the query-count shape across ascending cardinalities.

    Raises:
        ValueError: fewer than two counts, since one count has no shape.
    """
    if len(counts) < 2:
        msg = "classify_counts needs counts at two or more cardinalities"
        raise ValueError(msg)
    if all(count == counts[0] for count in counts):
        return BATCHED
    if all(later > earlier for earlier, later in pairwise(counts)):
        return SCALES
    return MIXED


def rows_grew(root_rows: list[int | None]) -> bool:
    """Report whether the root rows rose at every cardinality step.

    A flat count over flat root rows is not a batching proof: the added
    parents never reached the resolver.
    """
    if any(rows is None for rows in root_rows):
        return False
    return all(later > earlier for earlier, later in pairwise(root_rows))


def parse_cardinalities(raw: str) -> list[int]:
    """Parse ``--cardinalities`` into a strictly ascending list of positive ints.

    An empty relation skips its batch query entirely, so a cardinality of 0
    fakes a slope and is refused.

    Raises:
        ValueError: a value is not a positive int, or the list repeats one.
    """
    values = sorted(int(part) for part in raw.split(",") if part.strip())
    if any(value < 1 for value in values):
        msg = f"cardinalities must be positive, got {values}"
        raise ValueError(msg)
    if len(set(values)) != len(values):
        msg = f"cardinalities must be distinct, got {values}"
        raise ValueError(msg)
    return values


def operation_sha1(document: str) -> str:
    """Fingerprint an operation so ``--compare`` refuses a different one."""
    return hashlib.sha1(document.strip().encode("utf-8"), usedforsecurity=False).hexdigest()


def compare_reports(baseline: dict[str, Any], current: dict[str, Any]) -> list[str]:
    """Return the delta lines between two ``count_queries`` JSON reports.

    Raises:
        ValueError: the reports measured a different operation or seeder.
    """
    before_params = baseline["header"]["params"]
    after_params = current["header"]["params"]
    for key in ("operation_sha1", "seeder", "optimizer"):
        if before_params.get(key) != after_params.get(key):
            msg = (
                f"baseline {key}={before_params.get(key)!r} differs from "
                f"current {key}={after_params.get(key)!r}; not the same measurement"
            )
            raise ValueError(msg)
    before_cells = {row["cardinality"]: row for row in baseline["rows"]}
    lines = [f"{'N':>5} {'before':>7} {'after':>7} {'delta':>7}"]
    for row in current["rows"]:
        before = before_cells.get(row["cardinality"])
        if before is None:
            lines.append(f"{row['cardinality']:>5} {'-':>7} {row['queries']:>7} {'-':>7}")
            continue
        delta = row["queries"] - before["queries"]
        lines.append(
            f"{row['cardinality']:>5} {before['queries']:>7} {row['queries']:>7} {delta:>+7}",
        )
    lines.append(f"verdict: {baseline.get('verdict')} -> {current.get('verdict')}")
    return lines


def seed_library_shelves(count: int) -> None:
    """Ensure one branch holds ``count`` shelves of ``BOOKS_PER_SHELF`` books each."""
    from apps.library.models import Book, Branch, Shelf

    branch, _ = Branch.objects.get_or_create(name="count-queries-branch")
    for index in range(Shelf.objects.filter(branch=branch).count(), count):
        shelf = Shelf.objects.create(code=f"s{index}", branch=branch)
        for book_index in range(BOOKS_PER_SHELF):
            Book.objects.create(title=f"s{index}-b{book_index}", shelf=shelf)


def _seed(seeder: str, count: int) -> None:
    if seeder == "products":
        from apps.products.services import seed_data

        seed_data(count)
    elif seeder == "library":
        seed_library_shelves(count)
    else:
        seed_glossary_terms(count)


def _schema(*, optimizer: bool) -> Any:
    from config import schema as fakeshop_schema

    if optimizer:
        return fakeshop_schema.schema
    from django_strawberry_framework import DjangoSchema, strawberry_config

    return DjangoSchema(
        query=fakeshop_schema.Query,
        mutation=fakeshop_schema.Mutation,
        config=strawberry_config(),
    )


def _resolve_operation(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> tuple[str, str, str | None]:
    """Return ``(document, seeder, graphql_operation_name)`` for the CLI flags."""
    if args.query:
        seeder = args.seeder or "products"
        return load_graphql_document(args.query), seeder, args.operation_name
    if args.operation_name not in BUILTIN_OPERATIONS:
        parser.error(
            f"--operation-name {args.operation_name!r} is not built in; choose one of "
            f"{sorted(BUILTIN_OPERATIONS)} or pass --query",
        )
    operation = BUILTIN_OPERATIONS[args.operation_name]
    return operation.document, args.seeder or operation.seeder, None


def main() -> int:
    """Parse args, run the operation at every cardinality, and print the verdict."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    source = parser.add_argument_group("operation (one of --query / --operation-name)")
    source.add_argument("--query", help="GraphQL file holding the operation")
    source.add_argument(
        "--operation-name",
        help=(
            "with --query: the GraphQL operationName to execute; alone: a built-in "
            f"operation ({', '.join(sorted(BUILTIN_OPERATIONS))})"
        ),
    )
    parser.add_argument("--variables", help="JSON object of operation variables")
    parser.add_argument(
        "--seeder",
        choices=("products", "library", "glossary"),
        help="fixture raised to each cardinality (default: the built-in's, else products)",
    )
    parser.add_argument(
        "--cardinalities",
        default=DEFAULT_CARDINALITIES,
        help=f"comma-separated parent counts, one cell each (default {DEFAULT_CARDINALITIES})",
    )
    parser.add_argument(
        "--no-optimizer",
        action="store_true",
        help="run without DjangoOptimizerExtension (positive control)",
    )
    parser.add_argument("--show-sql", action="store_true", help="print every counted statement")
    parser.add_argument("--json", dest="json_path", help="also write the report as JSON here")
    parser.add_argument("--compare", help="baseline JSON from an earlier run; prints deltas")
    args = parser.parse_args()
    if not args.query and not args.operation_name:
        parser.error("pass --query PATH or --operation-name NAME")
    try:
        cardinalities = parse_cardinalities(args.cardinalities)
        variables = parse_variables(args.variables)
    except (TypeError, ValueError) as exc:
        parser.error(str(exc))
    document, seeder, graphql_operation_name = _resolve_operation(args, parser)
    baseline = None
    if args.compare:
        baseline = json.loads(Path(args.compare).read_text(encoding="utf-8"))

    provenance = bootstrap_fakeshop_django("sqlite-memory")
    schema = _schema(optimizer=not args.no_optimizer)
    sha1 = operation_sha1(document)

    print(
        f"\noperation sha1={sha1[:12]} seeder={seeder} "
        f"optimizer={'off' if args.no_optimizer else 'on'} viewer=anonymous",
    )
    print(f"{'N':>5} {'root rows':>10} {'queries':>8}")
    cells: list[dict[str, Any]] = []
    failures: list[str] = []
    for cardinality in cardinalities:
        _seed(seeder, cardinality)
        warm = schema.execute_sync(
            document,
            variable_values=variables,
            operation_name=graphql_operation_name,
        )
        with capture_queries() as ctx:
            result = schema.execute_sync(
                document,
                variable_values=variables,
                operation_name=graphql_operation_name,
            )
        errors = warm.errors or result.errors
        if errors:
            failures.append(f"N={cardinality}: {errors}")
            print(f"{cardinality:>5} ERROR: {errors}")
            continue
        root_rows = root_row_count(result.data)
        cell = {"cardinality": cardinality, "queries": len(ctx), "root_rows": root_rows}
        if args.show_sql:
            cell["sql"] = [entry["sql"] for entry in ctx.captured_queries]
        cells.append(cell)
        print(f"{cardinality:>5} {'?' if root_rows is None else root_rows:>10} {len(ctx):>8}")
        for statement in cell.get("sql", ()):
            print(f"        {statement}")

    counts = [cell["queries"] for cell in cells]
    verdict = None
    if not failures and len(cells) < 2:
        failures.append("fewer than two cardinalities measured")
    elif not failures and not rows_grew([cell["root_rows"] for cell in cells]):
        failures.append(
            "root rows did not grow at every step, so the counts cannot show batching",
        )
    elif not failures:
        verdict = classify_counts(counts)
        absolute = f"absolute={counts[0]}" if verdict == BATCHED else f"counts={counts}"
        print(f"verdict: {verdict}  {absolute}")
    for failure in failures:
        print(f"NOT MEASURED: {failure}", file=sys.stderr)

    report = build_report(
        tool="count_queries",
        provenance=provenance.as_dict(),
        params={
            "cardinalities": cardinalities,
            "graphql_operation_name": graphql_operation_name,
            "operation": args.query or args.operation_name,
            "operation_sha1": sha1,
            "optimizer": not args.no_optimizer,
            "seeder": seeder,
            "variables": variables,
        },
        rows=cells,
        failures=failures,
    )
    report["verdict"] = verdict
    if args.json_path:
        write_report(args.json_path, report)
        print(f"wrote {args.json_path}")
    if baseline is not None:
        try:
            lines = compare_reports(baseline, report)
        except ValueError as exc:
            print(f"compare refused: {exc}", file=sys.stderr)
            return EXIT_NOT_MEASURED
        print(f"\ncompare against {args.compare}")
        print("\n".join(lines))
    if verdict is None:
        return EXIT_NOT_MEASURED
    return EXIT_BATCHED if verdict == BATCHED else EXIT_GROWS


if __name__ == "__main__":
    raise SystemExit(main())
