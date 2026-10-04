"""Executable ORM tests for the correlated-EXISTS predicate primitive.

Guards, reserved-alias allocation, evaluated-outer parity, composite-pk
correlation, and ``_base_manager`` start have no GraphQL envelope. Row-preserving
EXISTS SQL without ``SELECT DISTINCT`` is
``examples/fakeshop/test_query/test_library_api.py::test_genre_connection_flat_leaf_sql_shape_is_row_preserving``
and
``examples/fakeshop/test_query/test_library_api.py::test_library_loans_deep_leaf_sql_shape_is_row_preserving``.
"""

import pytest
from apps.library.models import Book, Branch, Genre, Loan, Shelf
from django.db import connection, router
from django.db.models import Value

from django_strawberry_framework.exceptions import OptimizerError
from django_strawberry_framework.optimizer.predicates import (
    _effective_alias_names,
    _next_reserved_alias,
    attach_exists,
    correlated_inner_root,
)
from tests._relation_fixtures import (
    RpCompositeChild,
    RpCompositeParent,
    relation_fixture_tables,
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


def test_alias_mismatch_message_reports_the_compared_values(monkeypatch):
    """The mismatch guard snapshots both ``.db`` resolutions before comparing
    and formats its message from the snapshots.

    ``.db`` re-resolves through the router on every read of a hint-less
    queryset, so a stateful router whose answers change between reads must see
    the guard report the aliases the comparison actually saw -- never a
    re-resolution inside the message f-string, which could claim a mismatch
    between two identical aliases (and would read the router a third time).
    """
    reads = {"n": 0}

    def flip(model_instance=None, **hints):
        reads["n"] += 1
        return "default" if reads["n"] % 2 else "nonexistent"

    monkeypatch.setattr(router, "db_for_read", flip)
    outer = Book.objects.all()  # hint-less: .db resolves through the router
    inner = correlated_inner_root(outer)  # router read 1 pins the inner to 'default'
    assert inner.db == "default"
    reads_after_build = reads["n"]

    with pytest.raises(OptimizerError) as exc:
        attach_exists(outer, inner)

    message = str(exc.value)
    assert "inner 'default'" in message, message
    assert "outer 'nonexistent'" in message, message
    # Exactly one router read per queryset during attach: the outer read the
    # comparison performed (the inner was pinned at build time).
    assert reads["n"] - reads_after_build == 1, message


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


@pytest.mark.django_db(transaction=True)
def test_composite_pk_correlation_executes_on_composite_fixture():
    """Composite pks share the single ``pk=OuterRef("pk")`` correlation, now
    PROVEN executing against a real composite-primary-key table.

    The ``RpCompositeParent`` fixture (``CompositePrimaryKey("tenant_id",
    "code")``) supplies the DB-backed composite table the fakeshop apps lack, so
    execution is no longer deferred. Django compiles the sole
    ``pk=OuterRef("pk")`` correlation to a tuple comparison over both member
    columns: the structural pin below shows the lhs is a ``ColPairs`` over the
    composite pk's member fields, and the execution below shows a parent with two
    matching children returned exactly once (no fan-out), a childless parent
    excluded, and ``EXISTS`` in the compiled SQL.
    """
    # Structural pin: the correlation is the single pk=OuterRef("pk") term, whose
    # composite lhs targets exactly the primary key's member fields (a tuple
    # comparison), keeping the single-implementation claim.
    inner_root = correlated_inner_root(RpCompositeParent.objects.all())
    (child,) = inner_root.query.where.children
    assert child.lookup_name == "exact"
    assert tuple(child.lhs.targets) == tuple(RpCompositeParent._meta.pk.fields)
    assert child.rhs.name == "pk"
    assert "OuterRef" in type(child.rhs).__name__

    with relation_fixture_tables(connection):
        matched = RpCompositeParent.objects.create(tenant_id=1, code="MATCH", label="m")
        RpCompositeChild.objects.create(parent=matched, name="hit one")
        RpCompositeChild.objects.create(parent=matched, name="hit two")
        empty = RpCompositeParent.objects.create(tenant_id=1, code="EMPTY", label="e")

        outer = RpCompositeParent.objects.all()
        inner = correlated_inner_root(outer).filter(children__name__icontains="hit")
        qs, cond = attach_exists(outer, inner)
        result = qs.filter(cond)

        codes = list(result.order_by("tenant_id", "code").values_list("code", flat=True))
        # Only the parent with matching children, and the multi-child parent
        # appears exactly once (no fan-out duplicate).
        assert codes == ["MATCH"]
        assert result.count() == 1
        assert empty.code not in codes
        assert "EXISTS" in str(result.query).upper()


def test_base_manager_start_does_not_leak_outer_filters():
    inner = correlated_inner_root(Book.objects.filter(title="x"))
    # Only the OuterRef correlation is present; the outer's filters never leak in.
    assert len(inner.query.where.children) == 1
