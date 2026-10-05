r"""Capture the row-preserving-predicate PostgreSQL EXPLAIN artifact.

The [Part 1 plan][part1-plan] (``docs/row-preserving-predicates-part1-plan.md``,
Slice C.3a and Sequencing step 9) requires a PostgreSQL
``EXPLAIN (ANALYZE, BUFFERS)`` artifact captured from the **actually emitted**
query -- "never an idealized hand-written query". This script drives the genuine
production generation + apply path for the two shapes a flat filter leaf over a
to-many path compiles to, reads the SQL straight off each compiled queryset,
runs ``EXPLAIN (ANALYZE, BUFFERS)`` on it against a real Postgres server, and
writes ``docs/row-preserving-predicates-part1-pg-explain.md``:

- a routed leaf: fakeshop ``ScalarSpecimenFilter``'s framework-generated
  reverse-FK relation key ``children``, whose relation no ``RelatedFilter``
  declares and whose target type (``ScalarSpecimenType``) keeps the identity
  ``get_queryset``, so no visibility applies and ``FilterSet._apply_flat_leaves``
  routes it through ``optimizer/predicates.py``'s ``correlated_inner_root`` +
  ``attach_exists`` (one ``EXISTS`` correlated on the outer primary key);
- a walked leaf: fakeshop ``LoanFilter``'s ``book__loans__patron__email__icontains``
  (the Medtrics reverse-FK reproduction shape), whose path walks the declared
  ``book``, ``loans`` and ``patron`` branches, so each hop is one correlated
  ``EXISTS`` built from that hop's visible rows
  (``optimizer/predicates.py::related_rows_exist``), correlated on the link
  columns.

Reproducible recipe (run from the repo root)::

    docker compose -f docker-compose.postgres.yml up -d
    uv sync --group pg
    FAKESHOP_PG_DSN=postgres://fakeshop:fakeshop@127.0.0.1:5432/fakeshop \
        uv run python scripts/capture_pg_predicate_explain.py
    docker compose -f docker-compose.postgres.yml down

The seed + capture run inside a single transaction that is ROLLED BACK at the
end, so a re-run is deterministic and leaves no rows behind (migrations are
committed by ``bootstrap_fakeshop_django`` before the transaction opens). The
Postgres target is the throwaway tmpfs server from
``docker-compose.postgres.yml``; the tracked ``examples/fakeshop/db.sqlite3``
file is NEVER opened (the ``FAKESHOP_PG_DSN`` settings branch swaps the
``default`` alias to Postgres, and this script refuses to run on any other
vendor). The filter sets run with no resolver ``info``, so every target type's
``get_queryset`` answers for an anonymous viewer.
"""

from __future__ import annotations

import datetime
import importlib
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_PATH = REPO_ROOT / "docs" / "row-preserving-predicates-part1-pg-explain.md"

NEEDLE = "cardio"

# The routed production leaf: a framework-generated reverse-FK relation key declared
# on fakeshop's ``ScalarSpecimenFilter.Meta.fields``; no ``RelatedFilter`` declares
# ``children`` and ``ScalarSpecimenType`` scopes nothing, so the leaf is not walked.
SPECIMEN_LEAF = "children"
N_PARENTS = 60
CHILDREN_PER_PARENT = 5

# The walked production leaf: a deep to-many path declared on fakeshop's
# ``LoanFilter.Meta.fields`` (the Medtrics reverse-FK reproduction: Loan -> book
# (to-one) -> loans (to-many reverse FK) -> patron (to-one) -> email (scalar)),
# every relation of which a ``RelatedFilter`` declares.
LOAN_LEAF = "book__loans__patron__email__icontains"
LOAN_HOPS = ("book", "loans", "patron")
N_BOOKS = 300
LOANS_PER_BOOK = 3
N_PATRONS = 60

CARDIO_EVERY = 12  # row i carries a "cardio" value when i % CARDIO_EVERY == 0.
REPAIR_EVERY = 10  # book i is in repair (hidden by ``BookType``) when i % REPAIR_EVERY == 0.

# Canonical reference-style link-definition footer required of every standing
# markdown doc (AGENTS.md "Markdown link convention"; enforced by
# ``scripts/check_trailing_commas.py``'s ``_scaffold_in_canonical_order``): the
# ``<!-- LINK DEFINITIONS -->`` delimiter followed by the 10 path-based group
# headers in canonical order, each present even when empty. This is emitted
# verbatim as the tail of the artifact so the generated file stays BYTE-IDENTICAL
# to the checked-in ``docs/row-preserving-predicates-part1-pg-explain.md`` and
# passes the standing-doc link-block validation. Kept as one constant (rather
# than inline literals in ``main``) so the footer test can import and check it.
LINK_DEFINITIONS_FOOTER = (
    "<!-- LINK DEFINITIONS -->\n"
    "\n"
    "<!-- Root -->\n"
    "\n"
    "<!-- docs/ -->\n"
    "\n"
    "<!-- docs/SPECS/ -->\n"
    "\n"
    "<!-- docs/builder/ -->\n"
    "\n"
    "<!-- django_strawberry_framework/ -->\n"
    "\n"
    "<!-- tests/ -->\n"
    "\n"
    "<!-- examples/ -->\n"
    "\n"
    "<!-- scripts/ -->\n"
    "\n"
    "<!-- .venv/ -->\n"
    "\n"
    "<!-- External -->\n"
)


@dataclass(frozen=True)
class Capture:
    """One production leaf's emitted SQL, its asserted shape, and its executed plan."""

    display_sql: str
    compiled_sql: str
    compiled_params: tuple[object, ...]
    exists_count: int
    outer_tables: list[str]
    production_pks: list[int]
    oracle_pks: list[int]
    explain_output: str
    top_actual_rows: int


def _seed_library() -> dict[str, int]:
    """Seed a deterministic library dataset; return row counts for the artifact."""
    from apps.library.models import Book, Branch, Loan, Patron, Shelf

    branch = Branch.objects.create(name="pg-explain-central")
    shelf = Shelf.objects.create(code="PGX", branch=branch)
    patrons = Patron.objects.bulk_create(
        Patron(
            name=f"p{index}",
            email=(
                f"cardio{index}@example.com"
                if index % CARDIO_EVERY == 0
                else f"neuro{index}@example.com"
            ),
        )
        for index in range(N_PATRONS)
    )
    books = Book.objects.bulk_create(
        Book(
            title=f"b{index}",
            shelf=shelf,
            circulation_status=(
                Book.CirculationStatus.REPAIR
                if index % REPAIR_EVERY == 0
                else Book.CirculationStatus.AVAILABLE
            ),
        )
        for index in range(N_BOOKS)
    )
    loans = [
        Loan(
            book=book,
            patron=patrons[(book_index * LOANS_PER_BOOK + offset) % N_PATRONS],
            note=f"loan-{book_index}-{offset}",
        )
        for book_index, book in enumerate(books)
        for offset in range(LOANS_PER_BOOK)
    ]
    Loan.objects.bulk_create(loans)
    return {
        "patrons": len(patrons),
        "cardio_patrons": sum(1 for index in range(N_PATRONS) if index % CARDIO_EVERY == 0),
        "books": len(books),
        "repair_books": sum(1 for index in range(N_BOOKS) if index % REPAIR_EVERY == 0),
        "loans": len(loans),
    }


def _seed_scalars() -> tuple[dict[str, int], list[int]]:
    """Seed deterministic parent / child specimens; return row counts and the routed needle.

    The needle is the primary key of every ``CARDIO_EVERY``-th child, the list the
    ``children`` relation key is given.
    """
    from apps.scalars.models import ScalarSpecimen

    moment = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)

    def specimen(label: str, parent: Any = None) -> Any:
        return ScalarSpecimen(
            label=label,
            occurred_on=moment.date(),
            occurred_at=moment,
            occurred_time=moment.time(),
            external_id=uuid.UUID(int=0),
            parent=parent,
        )

    parents = ScalarSpecimen.objects.bulk_create(
        specimen(f"pg-explain-{index}") for index in range(N_PARENTS)
    )
    children = ScalarSpecimen.objects.bulk_create(
        specimen(f"pg-explain-{parent_index}-{offset}", parent)
        for parent_index, parent in enumerate(parents)
        for offset in range(CHILDREN_PER_PARENT)
    )
    needle = [child.pk for index, child in enumerate(children) if index % CARDIO_EVERY == 0]
    return {"parents": len(parents), "children": len(children), "needle": len(needle)}, needle


def _production_qs(
    filterset_cls: Any,
    leaf: str,
    root: Any,
    value: object = NEEDLE,
) -> Any:
    """Instantiate a real fakeshop filter set and return its compiled ``.qs``.

    The genuine production generation + apply path: the metaclass /
    ``get_filters`` build stamps generation provenance and publishes the
    candidate snapshot, and ``.qs`` runs ``FilterSet.filter_queryset`` ->
    ``_apply_flat_leaves``, which routes an eligible leaf walking no declared
    hop and applies a leaf walking declared hops over each hop's visible rows.
    """
    from django.http import HttpRequest

    filterset_cls.get_filters()  # publish the expansion snapshot (as apply_* does).
    filterset = filterset_cls(
        data={leaf: value},
        queryset=root.order_by("id"),
        request=HttpRequest(),
    )
    return filterset.qs


def _referenced_tables(qs: Any) -> list[str]:
    """Return the tables the outer statement's ``FROM`` reads: aliases the SQL references.

    A join Django set up and then trimmed (resolving an ``OuterRef`` on a
    foreign-key column) stays in ``alias_map`` with a zero reference count and
    is never emitted.
    """
    query = qs.query
    return sorted(
        {
            query.alias_map[alias].table_name
            for alias, refs in query.alias_refcount.items()
            if refs
        },
    )


def _extract_exists_subquery(sql: str) -> str:
    """Return the first ``EXISTS(...)`` subquery text, brackets matched."""
    marker = "EXISTS("
    start = sql.upper().find(marker)
    if start == -1:
        return "<no EXISTS( found>"
    open_paren = start + len(marker) - 1
    depth = 0
    for index in range(open_paren, len(sql)):
        char = sql[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return sql[start : index + 1]
    return sql[start:]


def _capture(qs: Any, oracle_pks: list[int]) -> Capture:
    """Run ``EXPLAIN (ANALYZE, BUFFERS)`` on ``qs``'s exact statement and record its shape."""
    from django.db import connection

    display_sql = str(qs.query)
    compiled_sql, compiled_params = qs.query.get_compiler(using=qs.db).as_sql()
    with connection.cursor() as cursor:
        cursor.execute("EXPLAIN (ANALYZE, BUFFERS) " + compiled_sql, compiled_params)
        explain_output = "\n".join(row[0] for row in cursor.fetchall())
    top = re.search(r"actual time=[\d.]+\.\.[\d.]+ rows=(\d+)", explain_output)
    assert top is not None, "EXPLAIN output carries no actual row count"
    return Capture(
        display_sql=display_sql,
        compiled_sql=compiled_sql,
        compiled_params=tuple(compiled_params),
        exists_count=display_sql.upper().count("EXISTS"),
        outer_tables=_referenced_tables(qs),
        production_pks=list(qs.values_list("pk", flat=True)),
        oracle_pks=oracle_pks,
        explain_output=explain_output,
        top_actual_rows=int(top.group(1)),
    )


def _assert_row_preserving(capture: Capture, qs: Any, root_table: str) -> None:
    """Fail loudly unless ``capture`` is a row-preserving, distinct-free ``EXISTS`` shape.

    An artifact is only written for the real emitted query, so every invariant
    the artifact reports is asserted first.
    """
    assert qs.query.distinct is False, "outer query carries DISTINCT"
    assert "DISTINCT" not in capture.display_sql.upper(), "DISTINCT present in the emitted SQL"
    assert capture.outer_tables == [root_table], (
        f"outer statement should read only {root_table}, got {capture.outer_tables}"
    )
    assert capture.production_pks, "the seed guarantees matches, so the proof is non-vacuous"
    assert capture.production_pks == capture.oracle_pks, "result diverged from the dedup oracle"
    assert capture.top_actual_rows == len(capture.production_pks), (
        f"top plan node returned {capture.top_actual_rows} rows, "
        f"the result has {len(capture.production_pks)}: the outer rows multiplied"
    )


def _sql_block(lines: list[str], sql: str) -> None:
    """Append ``sql`` as a fenced ``sql`` block."""
    lines.extend(
        (
            "```sql",
            sql,
            "```",
            "",
        ),
    )


def _render_capture(lines: list[str], capture: Capture) -> None:
    """Append the emitted SQL, the executed statement and its plan."""
    lines.extend(("### Emitted SQL (full outer query, params inlined for display)", ""))
    _sql_block(lines, capture.display_sql)
    lines.append(
        "The exact parameterized statement executed by `EXPLAIN` (as returned by "
        "`qs.query.get_compiler(using=qs.db).as_sql()`):",
    )
    lines.append("")
    _sql_block(lines, capture.compiled_sql)
    lines.extend((f"Bind params: `{list(capture.compiled_params)!r}`", ""))
    lines.extend(
        (
            "### EXPLAIN (ANALYZE, BUFFERS)",
            "",
            "```text",
            capture.explain_output,
            "```",
        ),
    )
    lines.append("")


def _shape_lines(capture: Capture, qs: Any, exists_line: str) -> list[str]:
    """Return the shape-assertion bullets shared by both captures."""
    return [
        "Shape assertions (all passed before this file was written):",
        "",
        f"- outer `query.distinct` is `False`: **{qs.query.distinct is False}**",
        exists_line,
        "- no `DISTINCT` anywhere (outer query or any existence body): "
        f"**{'DISTINCT' not in capture.display_sql.upper()}**",
        "- the outer statement reads only the root table (every related table lives "
        f"INSIDE an `EXISTS`): **{capture.outer_tables}**",
        f"- the result equals the dedup oracle ({len(capture.production_pks)} rows): "
        f"**{capture.production_pks == capture.oracle_pks}**",
        "- the top plan node's actual row count equals the result "
        f"({capture.top_actual_rows} rows), so no outer row is multiplied: "
        f"**{capture.top_actual_rows == len(capture.production_pks)}**",
        "",
    ]


def main() -> None:
    """Drive both production paths, run EXPLAIN, and write the artifact file."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from _bench_common import bootstrap_fakeshop_django

    # sys.path seam + settings + django.setup() + migrate; refuses non-Postgres.
    bootstrap_fakeshop_django("pg")

    import django
    from django.db import connection, transaction

    if connection.vendor != "postgresql":  # defensive: never touch sqlite.
        sys.exit(f"Refusing to run: expected postgresql, got {connection.vendor!r}.")

    # The composed fakeshop schema registers every DjangoType and binds every
    # filter set to its owner type, so each declared hop resolves its target type.
    importlib.import_module("config.schema")
    from apps.library.filters import LoanFilter
    from apps.library.models import Book, Loan
    from apps.scalars.filters import ScalarSpecimenFilter
    from apps.scalars.models import ScalarSpecimen

    with connection.cursor() as cursor:
        cursor.execute("SELECT version()")
        pg_version = cursor.fetchone()[0]

    # Everything below runs in ONE transaction that is rolled back, so the
    # throwaway database is left exactly as migrated.
    with transaction.atomic():
        library_counts = _seed_library()
        specimen_counts, needle = _seed_scalars()
        with connection.cursor() as cursor:
            for table in (
                "library_loan",
                "library_book",
                "library_patron",
                "scalars_scalarspecimen",
            ):
                cursor.execute(f"ANALYZE {table}")

        # Routed leaf: the oracle is the leaf invoked directly on the outer
        # queryset, then deduplicated (the JOIN + DISTINCT idiom the routing replaces).
        routed_qs = _production_qs(
            ScalarSpecimenFilter,
            SPECIMEN_LEAF,
            ScalarSpecimen.objects.all(),
            needle,
        )
        routed_leaf = ScalarSpecimenFilter.get_filters()[SPECIMEN_LEAF]
        routed = _capture(
            routed_qs,
            sorted(
                routed_leaf.filter(ScalarSpecimen.objects.all(), needle)
                .distinct()
                .values_list("pk", flat=True),
            ),
        )
        _assert_row_preserving(routed, routed_qs, "scalars_scalarspecimen")
        assert routed.exists_count == 1, f"expected exactly one EXISTS, got {routed.exists_count}"
        assert '= ("scalars_scalarspecimen"."id")' in routed.display_sql, (
            "the routed EXISTS is not correlated on the outer primary key"
        )

        # Walked leaf: the oracle is the same Django lookup over the rows an
        # anonymous viewer sees (``BookType.get_queryset`` hides ``repair`` books;
        # ``LoanType`` and ``PatronType`` hide nothing), then deduplicated.
        walked_qs = _production_qs(LoanFilter, LOAN_LEAF, Loan.objects.all())
        loan_leaf = LoanFilter.get_filters()[LOAN_LEAF]
        visible_loans = Loan.objects.exclude(
            book__circulation_status=Book.CirculationStatus.REPAIR,
        )
        walked = _capture(
            walked_qs,
            sorted(
                loan_leaf.filter(visible_loans, NEEDLE).distinct().values_list("pk", flat=True),
            ),
        )
        _assert_row_preserving(walked, walked_qs, "library_loan")
        assert walked.exists_count == len(LOAN_HOPS), (
            f"expected one EXISTS per declared hop ({len(LOAN_HOPS)}), got {walked.exists_count}"
        )
        assert '= ("library_loan"."book_id")' in walked.display_sql, (
            "the outermost hop is not correlated on the outer row's book link column"
        )
        raw_pks = sorted(
            loan_leaf.filter(Loan.objects.all(), NEEDLE).distinct().values_list("pk", flat=True),
        )
        hidden_matches = len(raw_pks) - len(walked.production_pks)
        assert hidden_matches > 0, "the seed must put matches behind a hidden book"

        transaction.set_rollback(True)

    # ------------------------------------------------------------------
    # Render the artifact.
    # ------------------------------------------------------------------
    lines: list[str] = []
    lines.append("# Row-preserving predicates: PostgreSQL EXPLAIN (ANALYZE, BUFFERS) artifact")
    lines.append("")
    lines.append(
        "Planner evidence for the row-preserving-predicates Part 1 plan "
        "(`docs/row-preserving-predicates-part1-plan.md`, Slice C.3a and Sequencing "
        "step 9) and for the declared-branch restriction of spec-027 Decision 8 "
        "(`docs/SPECS/spec-027-filters-0_0_8.md`): the `EXPLAIN (ANALYZE, BUFFERS)` "
        "output for the **actually emitted** query of each shape a flat filter leaf "
        "over a to-many path compiles to, captured from the framework's compiled "
        "queryset on a real Postgres server -- not a hand-written query.",
    )
    lines.append("")
    lines.append(
        "This file is generated by `scripts/capture_pg_predicate_explain.py`; "
        "do not hand-edit it. Regenerate with the recipe below.",
    )
    lines.append("")
    lines.append("## Reproducible capture command")
    lines.append("")
    lines.append("```bash")
    lines.append("docker compose -f docker-compose.postgres.yml up -d")
    lines.append("uv sync --group pg")
    lines.append(
        "FAKESHOP_PG_DSN=postgres://fakeshop:fakeshop@127.0.0.1:5432/fakeshop \\",
    )
    lines.append("    uv run python scripts/capture_pg_predicate_explain.py")
    lines.append("docker compose -f docker-compose.postgres.yml down")
    lines.append("```")
    lines.append("")
    lines.append("## Provenance -- the queries came from production code")
    lines.append("")
    lines.append(
        "Each SQL statement below is read directly off the compiled queryset a real "
        "fakeshop filter set produces (`examples/fakeshop/apps/scalars/filters.py`, "
        "`examples/fakeshop/apps/library/filters.py`), with the composed fakeshop "
        "schema loaded so every declared branch resolves its target type. No SQL is "
        "hand-written; each EXPLAIN executes the exact parameterized statement "
        "`qs.query.get_compiler(using=qs.db).as_sql()` returns. The filter sets run "
        "with no resolver `info`, so every target type's `get_queryset` answers for "
        "an anonymous viewer.",
    )
    lines.append("")

    lines.append("## Routed leaf: one `EXISTS` correlated on the outer primary key")
    lines.append("")
    lines.append(
        "- FilterSet: `apps.scalars.filters.ScalarSpecimenFilter` (root model `ScalarSpecimen`)",
    )
    lines.append(
        f"- Active generated relation key: `{SPECIMEN_LEAF}` = the primary keys of "
        f"{len(needle)} children",
    )
    lines.append(
        "- Relation path: `ScalarSpecimen.children` (to-many reverse FK onto the same "
        "model); no `RelatedFilter` declares `children` and `ScalarSpecimenType` keeps "
        "the identity `get_queryset`, so no target visibility applies and the leaf is "
        "not walked",
    )
    lines.append(
        "- Applicator: `FilterSet._apply_flat_leaves` routes the eligible "
        "framework-generated to-many leaf through `optimizer/predicates.py`'s "
        "`correlated_inner_root` + `attach_exists`, with the framework-added "
        "`distinct` suppressed inside the existence body "
        "(`_invoke_suppressing_framework_distinct`).",
    )
    lines.append(
        "- Dedup oracle: the same leaf invoked directly on `ScalarSpecimen.objects.all()`, "
        "then `.distinct()` (the membership `JOIN` + `DISTINCT` idiom the routing replaces).",
    )
    lines.append("")
    lines.extend(
        _shape_lines(
            routed,
            routed_qs,
            f"- exactly one `EXISTS`: **{routed.exists_count == 1}**, correlated on the "
            'outer primary key (`= ("scalars_scalarspecimen"."id")`): **True**',
        ),
    )
    lines.append(
        "The correlated distinct-free inner query -- it re-enters "
        "`scalars_scalarspecimen` as `U0`, joins the children inside the subquery, and "
        "carries no `SELECT DISTINCT`:",
    )
    lines.append("")
    _sql_block(lines, _extract_exists_subquery(routed.display_sql))
    _render_capture(lines, routed)

    lines.append("## Walked leaf: one `EXISTS` per declared hop, built from the visible rows")
    lines.append("")
    lines.append("- FilterSet: `apps.library.filters.LoanFilter` (root model `Loan`)")
    lines.append(f"- Active `Meta.fields` leaf: `{LOAN_LEAF}` = `{NEEDLE!r}`")
    lines.append(
        "- Relation path (Medtrics reverse-FK reproduction): "
        "`Loan.book` (to-one) -> `Book.loans` (to-many reverse FK) -> `Loan.patron` "
        "(to-one) -> `Patron.email` (scalar); `LoanFilter.book`, `BookFilter.loans` "
        "and `LoanFilter.patron` declare each relation, so the leaf walks three hops",
    )
    lines.append(
        "- Applicator: `FilterSet._apply_flat_leaves` -> `FilterSet._apply_relation_leaf` "
        "runs the leaf's terminal over the last hop's visible rows and folds each hop "
        "outward with `FilterSet._reaches_hop`, one `EXISTS` per hop built from that "
        "hop's visible rows and correlated on the hop's link columns "
        "(`optimizer/predicates.py::related_rows_exist`); it is never routed.",
    )
    lines.append(
        "- Dedup oracle: the same leaf invoked directly on the loans whose book "
        "`BookType.get_queryset` shows an anonymous viewer, then `.distinct()`. "
        f"The raw-relation oracle (no visibility) matches {len(raw_pks)} loans, "
        f"{hidden_matches} of them only through a `repair` book the viewer cannot see.",
    )
    lines.append("")
    lines.extend(
        _shape_lines(
            walked,
            walked_qs,
            f"- one `EXISTS` per declared hop ({len(LOAN_HOPS)}: "
            f"{', '.join(f'`{hop}`' for hop in LOAN_HOPS)}): "
            f"**{walked.exists_count == len(LOAN_HOPS)}**, the outermost correlated on "
            'the outer row\'s link column (`= ("library_loan"."book_id")`): **True**',
        ),
    )
    lines.append(
        "Each hop's subquery reads its target table's visible rows (the outermost "
        "`library_book` carries `BookType.get_queryset`'s `repair` exclusion) and "
        "nests the next hop inside it; no subquery re-enters the outer table to "
        "correlate on its primary key, and nothing is joined onto the outer statement.",
    )
    lines.append("")
    _render_capture(lines, walked)

    lines.append("## What the plans show")
    lines.append("")
    lines.append(
        "The framework's contribution is the *emitted SQL*: distinct-free `EXISTS` "
        "subqueries with every related table confined inside them, so the outer "
        "statement reads only the root table and returns each qualifying row once. "
        "Each plan's top node reports exactly the result's row count (asserted above): "
        "the outer row set is never multiplied, so no outer collapse over the root "
        "columns exists. Contrast the idiom both shapes replace: a `JOIN` across the "
        "membership tables followed by a global outer `DISTINCT` fans the root table "
        "out on the OUTER side (one outer row per matching related row) and then "
        "collapses those duplicates with a `Unique` / `HashAggregate` over the outer "
        "columns.",
    )
    lines.append("")
    lines.append(
        "How Postgres executes each `EXISTS` is the planner's choice: it may "
        "decorrelate one into a semi-join (a `Hash Semi Join`, or a `HashAggregate` "
        "over the correlation column, which de-duplicates the *inner* match set, not "
        "the outer rows) or keep a per-row `SubPlan`, and the choice varies by "
        "planner version and statistics. The row-preserving invariants above hold "
        "either way because they follow from the emitted SQL, not from a particular "
        "plan; `EXPLAIN (ANALYZE, BUFFERS)` reports the real executed shape (actual "
        "rows, loops and shared-buffer hits), not an estimate.",
    )
    lines.append("")
    lines.append("## Environment")
    lines.append("")
    lines.append(f"- PostgreSQL: {pg_version}")
    lines.append(f"- Django: {django.get_version()}")
    lines.append(f"- Python: {sys.version.split()[0]}")
    lines.append(
        "- Seeded (deterministic, rolled back after capture): "
        f"{specimen_counts['parents']} parent specimens with "
        f"{specimen_counts['children']} children ({specimen_counts['needle']} named by "
        "the relation key); "
        f"{library_counts['books']} books ({library_counts['repair_books']} in repair), "
        f"{library_counts['patrons']} patrons "
        f"({library_counts['cardio_patrons']} with a `cardio` email), "
        f"{library_counts['loans']} loans ({LOANS_PER_BOOK} per book).",
    )
    lines.append("")

    # ``"\n".join(lines)`` ends with a single ``\n`` (the trailing empty line
    # appended after the Environment section); the extra ``"\n"`` is the blank
    # separator line before the link-definition footer, which itself ends with a
    # final newline. This reproduces the checked-in artifact's tail exactly.
    ARTIFACT_PATH.write_text(
        "\n".join(lines) + "\n" + LINK_DEFINITIONS_FOOTER,
        encoding="utf-8",
    )
    print(f"Wrote {ARTIFACT_PATH.relative_to(REPO_ROOT)}")
    for name, capture in (("routed", routed), ("walked", walked)):
        print(
            f"  {name}: exists={capture.exists_count}  outer={capture.outer_tables}  "
            f"rows={len(capture.production_pks)}  top_rows={capture.top_actual_rows}",
        )


if __name__ == "__main__":
    main()
