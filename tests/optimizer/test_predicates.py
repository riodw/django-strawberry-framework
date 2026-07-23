"""Executable ORM tests for the neutral correlated-EXISTS predicate primitive.

Covers ``optimizer/predicates.py`` end to end against real ``apps.library``
models: correlation on the outer pk, reserved-alias allocation across every
effective alias namespace, the three runtime guards, row preservation with no
injected ``DISTINCT``, same-table inner aliasing, evaluated-outer parity, and
the ``_base_manager`` start.

These tests assert the production multiset contract for framework-generated
relational predicates: attaching an existence test is a row-preserving selection
that never multiplies outer rows (no framework fan-out, no injected ``DISTINCT``,
no framework dedup of consumer duplicates). The old accidental global
deduplication of generated to-many leaves was legacy behavior and has been
removed.
"""

import pytest
from apps.library.models import Book, Branch, Genre, Loan, Patron, Shelf
from django.db import connection
from django.db.models import Q, Value
from django.test.utils import CaptureQueriesContext

from django_strawberry_framework.exceptions import OptimizerError
from django_strawberry_framework.optimizer.predicates import (
    _effective_alias_names,
    _next_reserved_alias,
    attach_exists,
    correlated_inner_root,
)

pytestmark = pytest.mark.django_db


def _compose(outer, child_predicate):
    """Mirror the real caller shape: correlate, filter the inner, attach, apply."""
    inner = correlated_inner_root(outer).filter(**child_predicate)
    qs, cond = attach_exists(outer, inner)
    return qs, cond, qs.filter(cond)


def _shelf():
    branch = Branch.objects.create(name="Central")
    return Shelf.objects.create(code="A1", branch=branch)


def test_row_preservation_direct_m2m():
    shelf = _shelf()
    matching = Book.objects.create(title="One", shelf=shelf)
    nonmatching = Book.objects.create(title="Two", shelf=shelf)
    g1 = Genre.objects.create(name="science fiction")
    g2 = Genre.objects.create(name="hard science")
    g3 = Genre.objects.create(name="romance")
    matching.genres.add(g1, g2)
    nonmatching.genres.add(g3)

    _qs, _cond, result = _compose(Book.objects.all(), {"genres__name__icontains": "scien"})

    assert list(result.order_by("pk").values_list("pk", flat=True)) == [matching.pk]
    assert result.query.distinct is False
    tables = {j.table_name for j in result.query.alias_map.values()}
    assert "library_book_genres" not in tables
    assert "library_genre" not in tables
    sql = str(result.query)
    assert "EXISTS" in sql.upper()
    # Correlated on the outer root pk column.
    assert '"library_book"."id"' in sql


def test_same_table_inner_aliasing_from_loan_root():
    shelf = _shelf()
    shared = Book.objects.create(title="Shared", shelf=shelf)
    other = Book.objects.create(title="Other", shelf=shelf)
    p1 = Patron.objects.create(name="P1", email="p1@match.example")
    p2 = Patron.objects.create(name="P2", email="p2@match.example")
    p3 = Patron.objects.create(name="P3", email="p3@nope.example")
    p4 = Patron.objects.create(name="P4", email="p4@nope.example")

    # Ascending pk order: relation_and_direct, relation_only, direct_only, unrelated.
    relation_and_direct = Loan.objects.create(book=shared, patron=p1, note="keyword note")
    relation_only = Loan.objects.create(book=shared, patron=p2, note="")
    direct_only = Loan.objects.create(book=other, patron=p3, note="keyword note")
    Loan.objects.create(book=other, patron=p4, note="")

    qs, cond, result = _compose(
        Loan.objects.all(),
        {"book__loans__patron__email__icontains": "match.example"},
    )

    # Pure relational term: both loans on the shared book, each exactly once.
    assert list(result.order_by("pk").values_list("pk", flat=True)) == [
        relation_and_direct.pk,
        relation_only.pk,
    ]
    # Caller composes the direct note predicate on top of the returned branch.
    composed = qs.filter(Q(note__icontains="keyword") | cond)
    assert list(composed.order_by("pk").values_list("pk", flat=True)) == [
        relation_and_direct.pk,
        relation_only.pk,
        direct_only.pk,
    ]
    # Outer query keeps exactly one library_loan alias (the root); no DISTINCT.
    outer_tables = [j.table_name for j in result.query.alias_map.values()]
    assert outer_tables.count("library_loan") == 1
    assert result.query.distinct is False


def test_reserved_alias_not_selected():
    shelf = _shelf()
    book = Book.objects.create(title="One", shelf=shelf)
    book.genres.add(Genre.objects.create(name="science fiction"))

    _qs, _cond, result = _compose(Book.objects.all(), {"genres__name__icontains": "scien"})

    assert "_dst_predicate_0" not in result.query.values_select
    assert "_dst_predicate_0" not in dict(result.query.annotation_select)
    sql = str(result.query)
    select_clause = sql.split("FROM", 1)[0]
    assert "_dst_predicate_0" not in select_clause


def test_count_emits_no_distinct_wrapper():
    shelf = _shelf()
    book = Book.objects.create(title="One", shelf=shelf)
    book.genres.add(Genre.objects.create(name="science fiction"))

    _qs, _cond, result = _compose(Book.objects.all(), {"genres__name__icontains": "scien"})

    with CaptureQueriesContext(connection) as ctx:
        assert result.count() == 1
    sql = ctx.captured_queries[-1]["sql"].upper()
    assert "SELECT DISTINCT" not in sql
    assert "COUNT(*)" in sql


def test_primitive_injects_no_distinct():
    shelf = _shelf()
    book = Book.objects.create(title="One", shelf=shelf)
    book.genres.add(Genre.objects.create(name="science fiction"))

    # The caller suppresses DISTINCT; the primitive must not inject its own.
    _qs, _cond, result = _compose(Book.objects.all(), {"genres__name__icontains": "scien"})
    assert "SELECT DISTINCT" not in str(result.query).upper()


def test_alias_allocation():
    shelf = _shelf()
    Book.objects.create(title="One", shelf=shelf)

    # (a) A consumer .alias() pre-occupies _dst_predicate_0 -> primitive uses _1.
    outer = Book.objects.all().alias(_dst_predicate_0=Value(1))
    inner = correlated_inner_root(outer).filter(genres__name__icontains="x")
    _qs, cond = attach_exists(outer, inner)
    assert cond.children == [("_dst_predicate_1", True)]

    # (b) The effective namespace includes field names AND attnames AND "pk".
    names = _effective_alias_names(Book.objects.all())
    assert "shelf" in names
    assert "shelf_id" in names
    assert "pk" in names

    # (c) extra(select=) pre-occupies _dst_predicate_0 -> next counter used.
    extra_outer = Book.objects.all().extra(select={"_dst_predicate_0": "1"})
    assert _next_reserved_alias(extra_outer) == "_dst_predicate_1"

    # (d) Repeated attachments on one chained queryset advance _0 then _1.
    base = Book.objects.all()
    inner0 = correlated_inner_root(base).filter(genres__name__icontains="x")
    qs0, cond0 = attach_exists(base, inner0)
    inner1 = correlated_inner_root(qs0).filter(genres__name__icontains="y")
    _qs1, cond1 = attach_exists(qs0, inner1)
    assert cond0.children == [("_dst_predicate_0", True)]
    assert cond1.children == [("_dst_predicate_1", True)]

    # (e) An existing _dst_order_*-style annotation coexists; allocation + execution work.
    ordered = Book.objects.all().annotate(_dst_order_0=Value(1))
    inner_o = correlated_inner_root(ordered).filter(genres__name__icontains="scien")
    qs_o, cond_o = attach_exists(ordered, inner_o)
    assert cond_o.children == [("_dst_predicate_0", True)]
    assert qs_o.filter(cond_o).count() == 0


def test_same_model_guard():
    with pytest.raises(OptimizerError, match="does not"):
        attach_exists(Book.objects.all(), correlated_inner_root(Loan.objects.all()))


def test_same_alias_guard():
    # Building with .using() does not hit the DB, so no second database is needed.
    inner = correlated_inner_root(Book.objects.all()).using("nonexistent")
    with pytest.raises(OptimizerError, match="database-alias mismatch"):
        attach_exists(Book.objects.all(), inner)


def test_database_alias_preserved():
    assert correlated_inner_root(Book.objects.using("nonexistent")).db == "nonexistent"


def test_combinator_guard_names_combinator():
    combined = Book.objects.filter(pk=1).union(Book.objects.filter(pk=2))
    inner = correlated_inner_root(Book.objects.all())
    with pytest.raises(OptimizerError, match="union") as exc:
        attach_exists(combined, inner)
    assert "union" in str(exc.value)


def test_evaluated_outer_parity():
    shelf = _shelf()
    matching = Book.objects.create(title="One", shelf=shelf)
    Book.objects.create(title="Two", shelf=shelf)
    matching.genres.add(Genre.objects.create(name="science fiction"))

    evaluated = Book.objects.all()
    list(evaluated)  # force _result_cache
    _qe, _ce, result_e = _compose(evaluated, {"genres__name__icontains": "scien"})
    _qf, _cf, result_f = _compose(Book.objects.all(), {"genres__name__icontains": "scien"})

    rows_e = list(result_e.order_by("pk").values_list("pk", flat=True))
    rows_f = list(result_f.order_by("pk").values_list("pk", flat=True))
    assert rows_e == rows_f == [matching.pk]


def test_composite_pk_correlation_is_outerref_pk():
    """Composite pks share the single ``pk=OuterRef("pk")`` implementation.

    No composite-primary-key model with a DB table exists in the fakeshop
    fixtures (``CompositePrimaryKey`` appears only as a monkeypatched relay gate,
    never a migrated table), so DB-backed execution of the composite tuple
    comparison is deferred to the supported-version matrix step. Here we prove
    the correlation term is the sole ``pk=OuterRef("pk")`` implementation that
    Django compiles to a tuple comparison for a composite pk on supported
    Django.
    """
    inner = correlated_inner_root(Book.objects.all())
    (child,) = inner.query.where.children
    assert child.lookup_name == "exact"
    assert child.lhs.target is Book._meta.pk
    # The rhs is the resolved OuterRef correlating on the outer row's pk.
    assert child.rhs.name == "pk"
    assert "OuterRef" in type(child.rhs).__name__


def test_base_manager_start_does_not_leak_outer_filters():
    inner = correlated_inner_root(Book.objects.filter(title="x"))
    # Only the OuterRef correlation is present; the outer's filters never leak in.
    assert len(inner.query.where.children) == 1
