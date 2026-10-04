r"""Capture the Part 1 correlated-``EXISTS`` PostgreSQL EXPLAIN artifact.

The [Part 1 plan][part1-plan] (``docs/row-preserving-predicates-part1-plan.md``,
Slice C.3a and Sequencing step 9) requires a PostgreSQL
``EXPLAIN (ANALYZE, BUFFERS)`` artifact captured from the **actually emitted**
distinct-free inner query -- "never an idealized hand-written query". This script
drives the genuine production generation + apply path (a real fakeshop
``LoanFilter`` over the framework-generated deep to-many leaf
``book__loans__patron__email__icontains`` -- the Medtrics reverse-FK
reproduction shape), reads the SQL straight off the compiled queryset, runs
``EXPLAIN (ANALYZE, BUFFERS)`` on it against a real Postgres server, and writes
``docs/row-preserving-predicates-part1-pg-explain.md``.

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
vendor).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_PATH = REPO_ROOT / "docs" / "row-preserving-predicates-part1-pg-explain.md"

# The exact production leaf driven below -- a framework-generated deep to-many
# path declared on fakeshop's ``LoanFilter.Meta.fields`` (the Medtrics
# reverse-FK reproduction: Loan -> book (to-one) -> loans (to-many reverse FK,
# the first multiplying hop) -> patron (to-one) -> email (scalar)).
LEAF = "book__loans__patron__email__icontains"
NEEDLE = "cardio"

# Deterministic dataset sizes (documented in the artifact).
N_BOOKS = 300
LOANS_PER_BOOK = 3
N_PATRONS = 60
CARDIO_EVERY = 12  # patron i has a "cardio" email when i % CARDIO_EVERY == 0.

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


def _seed() -> dict[str, int]:
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
        Book(title=f"b{index}", shelf=shelf) for index in range(N_BOOKS)
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
    cardio_patrons = sum(1 for index in range(N_PATRONS) if index % CARDIO_EVERY == 0)
    return {
        "branches": 1,
        "shelves": 1,
        "patrons": len(patrons),
        "cardio_patrons": cardio_patrons,
        "books": len(books),
        "loans": len(loans),
    }


def _drive_production_queryset() -> Any:
    """Instantiate the real fakeshop ``LoanFilter`` and return its compiled ``.qs``.

    This is the genuine production generation + apply path: the metaclass /
    ``get_filters`` build stamps generation provenance and publishes the
    candidate snapshot, and ``.qs`` runs ``FilterSet.filter_queryset`` ->
    ``_apply_flat_leaves``, which routes the eligible framework-generated
    to-many leaf through ``optimizer/predicates.py``'s correlated-``EXISTS``
    primitive with the framework-added ``distinct`` suppressed inside the
    existence body.
    """
    from apps.library.filters import LoanFilter
    from apps.library.models import Loan
    from django.http import HttpRequest

    LoanFilter.get_filters()  # publish the expansion snapshot (as apply_* does).
    filterset = LoanFilter(
        data={LEAF: NEEDLE},
        queryset=Loan.objects.order_by("id"),
        request=HttpRequest(),
    )
    return filterset.qs


def _extract_exists_subquery(sql: str) -> str:
    """Return the ``EXISTS(...)`` correlated inner subquery text, brackets matched."""
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


def main() -> None:
    """Drive the production path, run EXPLAIN, and write the artifact file."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from _bench_common import bootstrap_fakeshop_django

    # sys.path seam + settings + django.setup() + migrate; refuses non-Postgres.
    bootstrap_fakeshop_django("pg")

    import django
    from django.db import connection, transaction

    if connection.vendor != "postgresql":  # defensive: never touch sqlite.
        sys.exit(f"Refusing to run: expected postgresql, got {connection.vendor!r}.")

    with connection.cursor() as cursor:
        cursor.execute("SELECT version()")
        pg_version = cursor.fetchone()[0]

    lines: list[str] = []

    # Everything below runs in ONE transaction that is rolled back, so the
    # throwaway database is left exactly as migrated.
    with transaction.atomic():
        counts = _seed()
        with connection.cursor() as cursor:
            cursor.execute("ANALYZE library_loan")
            cursor.execute("ANALYZE library_book")
            cursor.execute("ANALYZE library_patron")

        qs = _drive_production_queryset()

        # The human-readable emitted SQL (Django inlines the params for display).
        display_sql = str(qs.query)
        # The machine form actually executed by EXPLAIN: the SAME compiled query
        # object, parameterized.
        compiled_sql, compiled_params = qs.query.get_compiler(using=qs.db).as_sql()

        upper = display_sql.upper()
        exists_count = upper.count("EXISTS")
        has_distinct = "DISTINCT" in upper
        outer_tables = sorted({join.table_name for join in qs.query.alias_map.values()})
        inner_subquery = _extract_exists_subquery(display_sql)

        # Fail loudly if this is not the row-preserving correlated-EXISTS shape --
        # an artifact must only be written for the real distinct-free inner query.
        assert qs.query.distinct is False, "outer query carries DISTINCT"
        assert exists_count == 1, f"expected exactly one EXISTS, got {exists_count}"
        assert not has_distinct, "DISTINCT present -- not the distinct-free inner shape"
        assert outer_tables == ["library_loan"], (
            f"outer alias_map should hold only the root table, got {outer_tables}"
        )

        # Correctness cross-check against the test-local oracle (the old
        # production behavior: invoke the same leaf directly on the outer
        # queryset, then dedup) -- proves the row-preserving rewrite returns the
        # SAME rows it EXPLAINs.
        from apps.library.filters import LoanFilter
        from apps.library.models import Loan

        leaf = LoanFilter.get_filters()[LEAF]
        production_pks = list(qs.values_list("pk", flat=True))
        oracle_pks = sorted(
            leaf.filter(Loan.objects.all(), NEEDLE).distinct().values_list("pk", flat=True),
        )
        assert production_pks == oracle_pks, "row-preserving result diverged from oracle"

        with connection.cursor() as cursor:
            cursor.execute(
                "EXPLAIN (ANALYZE, BUFFERS) " + compiled_sql,
                compiled_params,
            )
            explain_output = "\n".join(row[0] for row in cursor.fetchall())

        transaction.set_rollback(True)

    # ------------------------------------------------------------------
    # Render the artifact.
    # ------------------------------------------------------------------
    lines.append("# Part 1 PostgreSQL EXPLAIN (ANALYZE, BUFFERS) artifact")
    lines.append("")
    lines.append(
        "Mandatory planner evidence for the row-preserving-predicates Part 1 "
        "plan (`docs/row-preserving-predicates-part1-plan.md`, Slice C.3a and "
        "Sequencing step 9): the `EXPLAIN (ANALYZE, BUFFERS)` output for the "
        "**actually emitted** distinct-free correlated-`EXISTS` inner query, "
        "captured from the framework's compiled queryset on a real Postgres "
        "server -- not a hand-written query.",
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
    lines.append("## Provenance -- the query came from production code")
    lines.append("")
    lines.append(
        "The SQL below is read directly off the compiled queryset produced by "
        "the real fakeshop `LoanFilter` (`examples/fakeshop/apps/library/"
        "filters.py`). No SQL is hand-written; the EXPLAIN executes the exact "
        "parameterized statement `qs.query.get_compiler(using=qs.db).as_sql()` "
        "returns.",
    )
    lines.append("")
    lines.append("- FilterSet: `apps.library.filters.LoanFilter` (root model `Loan`)")
    lines.append(f"- Active generated leaf: `{LEAF}` = `{NEEDLE!r}`")
    lines.append(
        "- Relation path (Medtrics reverse-FK reproduction): "
        "`Loan.book` (to-one) -> `Book.loans` (to-many reverse FK -- the first "
        "multiplying hop) -> `Loan.patron` (to-one) -> `Patron.email` (scalar)",
    )
    lines.append(
        "- Applicator: `FilterSet._apply_flat_leaves` routes the eligible "
        "framework-generated to-many leaf through `optimizer/predicates.py`'s "
        "`correlated_inner_root` + `attach_exists`, with the framework-added "
        "`distinct` suppressed inside the existence body "
        "(`_invoke_suppressing_framework_distinct`).",
    )
    lines.append("")
    lines.append("## Shape assertions (all passed before this file was written)")
    lines.append("")
    lines.append(f"- outer `query.distinct` is `False`: **{qs.query.distinct is False}**")
    lines.append(f"- exactly one `EXISTS` in the emitted SQL: **{exists_count == 1}**")
    lines.append(
        f"- no `DISTINCT` anywhere (outer or inner existence body): **{not has_distinct}**",
    )
    lines.append(
        "- outer `alias_map` holds only the root table (membership + terminal "
        f"tables live INSIDE the `EXISTS`): **{outer_tables}**",
    )
    lines.append(
        f"- row-preserving result equals the dedup oracle "
        f"({len(production_pks)} rows): **{production_pks == oracle_pks}**",
    )
    lines.append("")
    lines.append("## Emitted SQL (full outer query, params inlined for display)")
    lines.append("")
    lines.append("```sql")
    lines.append(display_sql)
    lines.append("```")
    lines.append("")
    lines.append(
        "The correlated distinct-free inner query (the `EXISTS(...)` subquery "
        "the plan requires evidence for) -- note it is correlated on the outer "
        'pk (`U0."id" = ("library_loan"."id")`), re-enters `library_loan` '
        "as a second alias (the same-table inner-alias shape), and carries no "
        "`SELECT DISTINCT`:",
    )
    lines.append("")
    lines.append("```sql")
    lines.append(inner_subquery)
    lines.append("```")
    lines.append("")
    lines.append(
        "The exact parameterized statement executed by `EXPLAIN` (as returned by "
        "`qs.query.get_compiler(using=qs.db).as_sql()`):",
    )
    lines.append("")
    lines.append("```sql")
    lines.append(compiled_sql)
    lines.append("```")
    lines.append("")
    lines.append(f"Bind params: `{list(compiled_params)!r}`")
    lines.append("")
    lines.append("## EXPLAIN (ANALYZE, BUFFERS)")
    lines.append("")
    lines.append("```text")
    lines.append(explain_output)
    lines.append("```")
    lines.append("")
    lines.append("## What the plan shows")
    lines.append("")
    lines.append(
        "The framework's contribution is the *emitted SQL*: a single distinct-free "
        "`EXISTS` correlated on the outer pk, with every membership/terminal join "
        "(`library_book`, the second `library_loan` alias, `library_patron`) "
        "confined INSIDE the subquery. How Postgres executes that `EXISTS` is the "
        "planner's choice; this captured plan shows:",
    )
    lines.append("")
    lines.append(
        "- **No outer fan-out.** `library_book`, the second `library_loan` alias "
        "(`u0`/`u2`), and `library_patron` are reached only through the pulled-up "
        "existence branch; the final `library_loan` (the outer projection) is read "
        "exactly once per qualifying pk via `library_loan_pkey` "
        "(`Index Scan ... Index Cond: (id = u0.id)`), and the node's actual row "
        "count equals the correct answer -- one row per matching loan, no "
        "multiplication.",
    )
    lines.append(
        "- **The `HashAggregate (Group Key: u0.id)` is the planner's own "
        "semi-join de-duplication of the EXISTS correlation column** -- it collapses "
        'the *inner* match set ("which outer pks have at least one qualifying '
        'related row"), NOT a framework-injected `DISTINCT` over a row-multiplied '
        "OUTER result. The emitted SQL contains no `DISTINCT` (asserted above); "
        "Postgres decorrelated the `EXISTS` into a semi-join and dedups on the "
        "correlation key, which is the standard, cheap `EXISTS` execution shape.",
    )
    lines.append(
        "- **Contrast with the pre-rewrite idiom this replaces:** a `JOIN` across "
        "the membership/terminal tables followed by a global outer `DISTINCT` would "
        "instead fan `library_loan` out on the OUTER side (one outer row per "
        "matching child) and then collapse those duplicates with a `Unique` / "
        "`HashAggregate` over the outer columns. Here the outer row set is never "
        "multiplied in the first place, so no such outer collapse exists.",
    )
    lines.append(
        "- `EXPLAIN (ANALYZE, BUFFERS)` reports the real executed shape (actual "
        "rows, loops, and shared-buffer hits), so this is the planner's behavior "
        "on the genuinely emitted statement, not an estimate over a hand-written "
        "query. (The exact node choice -- decorrelated semi-join here vs. a "
        "per-row `SubPlan` -- can vary by planner version and statistics; the "
        "row-preserving invariants above hold either way because they follow from "
        "the distinct-free correlated-`EXISTS` SQL, not from a particular plan.)",
    )
    lines.append("")
    lines.append("## Environment")
    lines.append("")
    lines.append(f"- PostgreSQL: {pg_version}")
    lines.append(f"- Django: {django.get_version()}")
    lines.append(f"- Python: {sys.version.split()[0]}")
    lines.append(
        "- Seeded (deterministic, rolled back after capture): "
        f"{counts['books']} books, {counts['patrons']} patrons "
        f"({counts['cardio_patrons']} with a `cardio` email), "
        f"{counts['loans']} loans ({LOANS_PER_BOOK} per book).",
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
    print(
        f"  outer distinct={qs.query.distinct}  exists={exists_count}  "
        f"distinct_present={has_distinct}  rows={len(production_pks)}",
    )


if __name__ == "__main__":
    main()
