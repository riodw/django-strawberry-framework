"""Postgres planner regression for the Part 1 row-preserving correlated ``EXISTS``.

Live HTTP already pins the emitted SQL and the row-preserving payload on the
shipped ``allLibraryLoans`` ``LoanFilter`` leaf
(``examples/fakeshop/test_query/test_library_api.py::test_library_loans_deep_leaf_sql_shape_is_row_preserving``
and
``examples/fakeshop/test_query/test_library_api.py::test_library_loans_filter_by_deep_to_many_email_is_row_preserving_over_http``):
one root query, no ``SELECT DISTINCT``, membership tables inside ``EXISTS``,
matching loan ids each once. Rungs 1-3 cannot observe
``EXPLAIN (ANALYZE, BUFFERS)`` actual-row counts: that is not a GraphQL wire
shape. This module is the guarded regression twin of
``scripts/capture_pg_predicate_explain.py`` (artifact
``docs/row-preserving-predicates-part1-pg-explain.md``): it drives the same
fakeshop ``LoanFilter`` deep to-many leaf
``book__loans__patron__email__icontains`` and asserts the top plan node's
ACTUAL rows equal the production result with no outer multiplication.

The whole module is ``@pytest.mark.pg`` so the default SQLite suite auto-skips
it (root ``conftest.py``).
"""

import re

import pytest
from apps.library.filters import LoanFilter
from apps.library.models import Book, Branch, Loan, Patron, Shelf
from django.db import connection as db_connection
from django.http import HttpRequest

pytestmark = [pytest.mark.pg, pytest.mark.django_db]

_LEAF = "book__loans__patron__email__icontains"
_NEEDLE = "cardio"


def _seed():
    """Seed a deterministic library dataset with a known 'cardio'-matching subset."""
    branch = Branch.objects.create(name="pg-explain-central")
    shelf = Shelf.objects.create(code="PGX", branch=branch)
    patrons = [
        Patron.objects.create(
            name=f"p{index}",
            email=(
                f"cardio{index}@example.com" if index % 4 == 0 else f"neuro{index}@example.com"
            ),
        )
        for index in range(12)
    ]
    books = [Book.objects.create(title=f"b{index}", shelf=shelf) for index in range(20)]
    for book_index, book in enumerate(books):
        for offset in range(3):
            Loan.objects.create(
                book=book,
                patron=patrons[(book_index * 3 + offset) % len(patrons)],
                note=f"loan-{book_index}-{offset}",
            )


def _production_qs():
    """Return the compiled ``.qs`` from the real fakeshop ``LoanFilter`` path."""
    LoanFilter.get_filters()  # publish the expansion snapshot (as apply_* does).
    filterset = LoanFilter(
        data={_LEAF: _NEEDLE},
        queryset=Loan.objects.order_by("id"),
        request=HttpRequest(),
    )
    return filterset.qs


def test_explain_analyze_buffers_shows_no_outer_fan_out():
    """EXPLAIN(ANALYZE, BUFFERS) executes the emitted query with no outer multiplication.

    Live
    ``examples/fakeshop/test_query/test_library_api.py::test_library_loans_deep_leaf_sql_shape_is_row_preserving``
    already pins the distinct-free correlated ``EXISTS`` SQL over ``/graphql/``.
    This row is the planner half that HTTP cannot see: the top plan node's
    ACTUAL row count equals both the production result count and the
    direct-invocation dedup oracle, and the plan text carries no ``DISTINCT``.
    A JOIN + outer-``DISTINCT`` rewrite would instead multiply the outer
    ``library_loan`` rows before collapsing them.
    """
    _seed()
    qs = _production_qs()

    production_pks = list(qs.values_list("pk", flat=True))
    leaf = LoanFilter.get_filters()[_LEAF]
    oracle_pks = sorted(
        leaf.filter(Loan.objects.all(), _NEEDLE).distinct().values_list("pk", flat=True),
    )
    assert production_pks == oracle_pks
    assert production_pks  # the seed guarantees matches, so the proof is non-vacuous.

    compiled_sql, compiled_params = qs.query.get_compiler(using=qs.db).as_sql()
    with db_connection.cursor() as cursor:
        cursor.execute("EXPLAIN (ANALYZE, BUFFERS) " + compiled_sql, compiled_params)
        plan = "\n".join(row[0] for row in cursor.fetchall())

    assert "DISTINCT" not in plan.upper()
    # The top node's ACTUAL rows == the correct answer: no outer fan-out.
    top_actual_rows = int(re.search(r"actual time=[\d.]+\.\.[\d.]+ rows=(\d+)", plan).group(1))
    assert top_actual_rows == len(production_pks)
