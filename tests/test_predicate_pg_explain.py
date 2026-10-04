"""Postgres planner regression for the row-preserving to-many filter predicates.

A flat filter leaf over a to-many path compiles to one of two shapes, both
captured by ``scripts/capture_pg_predicate_explain.py`` (artifact
``docs/row-preserving-predicates-part1-pg-explain.md``) and pinned here:

- a routed leaf (``CategoryFilter``'s generated ``items__name__icontains``, whose
  path no ``RelatedFilter`` declares) is one ``EXISTS`` correlated on the outer
  primary key (``optimizer/predicates.py::correlated_inner_root`` +
  ``attach_exists``);
- a walked leaf (``LoanFilter``'s ``book__loans__patron__email__icontains``,
  every relation of which a ``RelatedFilter`` declares) is one ``EXISTS`` per
  declared hop, each built from that hop's visible rows and correlated on the
  link columns (``optimizer/predicates.py::related_rows_exist``).

Live HTTP pins the emitted SQL and payloads; rungs 1-3 cannot observe
``EXPLAIN (ANALYZE, BUFFERS)`` actual-row counts, which is not a GraphQL wire
shape. Each row asserts the top plan node's ACTUAL rows equal the production
result and the dedup oracle, so no outer row is multiplied.

The whole module is ``@pytest.mark.pg`` so the default SQLite suite auto-skips
it (root ``conftest.py``).
"""

import re

import pytest
from apps.library.filters import LoanFilter
from apps.library.models import Book, Branch, Loan, Patron, Shelf
from apps.products.filters import CategoryFilter
from apps.products.models import Category, Item
from django.db import connection as db_connection
from django.http import HttpRequest
from schema_reload import reload_all_project_schemas

pytestmark = [pytest.mark.pg, pytest.mark.django_db]

_NEEDLE = "cardio"
_CATEGORY_LEAF = "items__name__icontains"
_LOAN_LEAF = "book__loans__patron__email__icontains"
_LOAN_HOPS = ("book", "loans", "patron")


@pytest.fixture(autouse=True)
def _project_schema():
    """Register every fakeshop type, so each declared hop resolves its target type."""
    reload_all_project_schemas()


def _seed_library():
    """Loans over books and patrons; every fifth book is in ``repair`` (``BookType`` hides it)."""
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
    books = [
        Book.objects.create(
            title=f"b{index}",
            shelf=shelf,
            circulation_status=(
                Book.CirculationStatus.REPAIR
                if index % 5 == 0
                else Book.CirculationStatus.AVAILABLE
            ),
        )
        for index in range(20)
    ]
    for book_index, book in enumerate(books):
        for offset in range(3):
            Loan.objects.create(
                book=book,
                patron=patrons[(book_index * 3 + offset) % len(patrons)],
                note=f"loan-{book_index}-{offset}",
            )


def _seed_products():
    """Categories over items, every fourth item named ``cardio``."""
    for category_index in range(10):
        category = Category.objects.create(name=f"pg-explain-{category_index}")
        for offset in range(4):
            prefix = "cardio" if (category_index + offset) % 4 == 0 else "neuro"
            Item.objects.create(name=f"{prefix}-{category_index}-{offset}", category=category)


def _production_qs(filterset_cls, leaf, root):
    """Return the compiled ``.qs`` of a real fakeshop filter set for ``{leaf: _NEEDLE}``."""
    filterset_cls.get_filters()  # publish the expansion snapshot (as apply_* does).
    return filterset_cls(
        data={leaf: _NEEDLE},
        queryset=root.order_by("id"),
        request=HttpRequest(),
    ).qs


def _referenced_tables(qs):
    """The tables the outer statement reads: aliases the SQL references.

    A join Django set up and then trimmed (resolving an ``OuterRef`` on a
    foreign-key column) stays in ``alias_map`` with no reference and is never
    emitted, so ``alias_map`` alone over-reports.
    """
    query = qs.query
    return {
        query.alias_map[alias].table_name for alias, refs in query.alias_refcount.items() if refs
    }


def _top_actual_rows(qs):
    """Run ``EXPLAIN (ANALYZE, BUFFERS)`` on ``qs``'s exact statement; return the plan and top rows."""
    compiled_sql, compiled_params = qs.query.get_compiler(using=qs.db).as_sql()
    with db_connection.cursor() as cursor:
        cursor.execute("EXPLAIN (ANALYZE, BUFFERS) " + compiled_sql, compiled_params)
        plan = "\n".join(row[0] for row in cursor.fetchall())
    return plan, int(re.search(r"actual time=[\d.]+\.\.[\d.]+ rows=(\d+)", plan).group(1))


def test_routed_leaf_is_a_single_distinct_free_exists_on_the_outer_pk():
    """The routed leaf compiles to one distinct-free ``EXISTS`` correlated on the outer pk."""
    _seed_products()
    qs = _production_qs(CategoryFilter, _CATEGORY_LEAF, Category.objects.all())
    sql = str(qs.query)

    assert qs.query.distinct is False
    assert sql.upper().count("EXISTS") == 1
    assert "DISTINCT" not in sql.upper()
    assert _referenced_tables(qs) == {"products_category"}
    assert '= ("products_category"."id")' in sql


def test_walked_leaf_is_one_distinct_free_exists_per_declared_hop():
    """The walked leaf compiles to one ``EXISTS`` per declared hop, correlated on the link columns.

    The outer statement reads only ``library_loan``; the outermost hop
    correlates on the outer row's ``book_id``, never by re-reading the loan table.
    """
    _seed_library()
    qs = _production_qs(LoanFilter, _LOAN_LEAF, Loan.objects.all())
    sql = str(qs.query)

    assert qs.query.distinct is False
    assert sql.upper().count("EXISTS") == len(_LOAN_HOPS)
    assert "DISTINCT" not in sql.upper()
    assert _referenced_tables(qs) == {"library_loan"}
    assert '= ("library_loan"."book_id")' in sql


@pytest.mark.parametrize("shape", ["routed", "walked"])
def test_explain_analyze_buffers_shows_no_outer_fan_out(shape):
    """EXPLAIN(ANALYZE, BUFFERS) executes each emitted query with no outer multiplication.

    The top plan node's ACTUAL row count equals both the production result count
    and the dedup oracle, and the plan carries no ``DISTINCT``. The routed oracle
    is the leaf invoked directly on the outer queryset, then deduplicated; the
    walked oracle is the same lookup over the loans an anonymous viewer sees
    (``BookType.get_queryset`` hides ``repair`` books; ``LoanType`` and
    ``PatronType`` hide nothing), so the walked result also differs from the
    raw-relation answer by the matches behind a hidden book.
    """
    if shape == "routed":
        _seed_products()
        qs = _production_qs(CategoryFilter, _CATEGORY_LEAF, Category.objects.all())
        leaf = CategoryFilter.get_filters()[_CATEGORY_LEAF]
        oracle_root = Category.objects.all()
    else:
        _seed_library()
        qs = _production_qs(LoanFilter, _LOAN_LEAF, Loan.objects.all())
        leaf = LoanFilter.get_filters()[_LOAN_LEAF]
        oracle_root = Loan.objects.exclude(book__circulation_status=Book.CirculationStatus.REPAIR)
        raw = set(leaf.filter(Loan.objects.all(), _NEEDLE).values_list("pk", flat=True))
        assert len(raw) > qs.count()

    production_pks = list(qs.values_list("pk", flat=True))
    oracle_pks = sorted(
        leaf.filter(oracle_root, _NEEDLE).distinct().values_list("pk", flat=True),
    )
    assert production_pks == oracle_pks
    assert production_pks  # the seed guarantees matches, so the proof is non-vacuous.

    plan, top_actual_rows = _top_actual_rows(qs)
    assert "DISTINCT" not in plan.upper()
    assert top_actual_rows == len(production_pks)
