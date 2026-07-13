"""Tests for the join-condition taxonomy (``optimizer/join_taxonomy.py``).

The descriptor table pins: one classification per Django relation shape,
against real fakeshop fields, so the windowed strategy's partition, the
prefetch connector column, and the (future) lateral join shape all read from
one classifier that cannot drift per-consumer. The two shims
(``plans.py::window_partition_for_prefetch`` and
``nested_planner.py::_connector_only_field``) keep their own historical pins
in ``test_plans.py`` / ``test_walker.py``; these tests pin the descriptor
directly.
"""

from types import SimpleNamespace

from apps.library.models import Book, Genre
from apps.products.models import Category, Item

from django_strawberry_framework.optimizer.join_taxonomy import (
    LateralJoinShape,
    RelationJoinDescriptor,
    classify_relation_join,
)


def test_reverse_fk_classifies_direct_fk():
    """Reverse FK (graph-node analog B): child table stores the parent id."""
    descriptor = classify_relation_join(Category._meta.get_field("items"))
    assert descriptor == RelationJoinDescriptor(
        kind="reverse_many_to_one",
        windowable=True,
        partition_expr="category_id",
        parent_join_column="category_id",
        through_model=None,
        lateral_shape=LateralJoinShape.DIRECT_FK,
        # The resolved child-side FK object (the lateral join's link field).
        parent_link_field=Item._meta.get_field("category"),
        through_child_field=None,
    )


def test_forward_m2m_classifies_through_table():
    """Forward M2M: partition by the target's reverse query name; join table attaches."""
    descriptor = classify_relation_join(Book._meta.get_field("genres"))
    assert descriptor.kind == "many"
    assert descriptor.windowable is True
    # The reverse query name, NOT the accessor (related_name="books" here).
    assert descriptor.partition_expr == "books"
    # The join table owns the attach; the child only needs its pk.
    assert descriptor.parent_join_column == Genre._meta.pk.attname
    assert descriptor.through_model is Book.genres.through
    assert descriptor.lateral_shape is LateralJoinShape.THROUGH_TABLE
    # Through-link FK pair: parent side (Book) / child side (Genre).
    assert descriptor.parent_link_field.attname == "book_id"
    assert descriptor.through_child_field.attname == "genre_id"


def test_reverse_m2m_classifies_through_table():
    """Reverse M2M: partition by the child's forward M2M field name."""
    descriptor = classify_relation_join(Genre._meta.get_field("books"))
    assert descriptor.kind == "many"
    assert descriptor.windowable is True
    assert descriptor.partition_expr == "genres"
    assert descriptor.parent_join_column == Book._meta.pk.attname
    assert descriptor.through_model is Book.genres.through
    assert descriptor.lateral_shape is LateralJoinShape.THROUGH_TABLE
    # The sides swap on the reverse rel: parent is Genre, child is Book.
    assert descriptor.parent_link_field.attname == "genre_id"
    assert descriptor.through_child_field.attname == "book_id"


def test_forward_single_classifies_unsupported():
    """Forward FK (graph-node analog D): single-valued, nothing to window."""
    descriptor = classify_relation_join(Item._meta.get_field("category"))
    assert descriptor.kind == "forward_single"
    assert descriptor.windowable is False
    assert descriptor.partition_expr is None
    # The connector column still resolves (list-prefetch projection uses it).
    assert descriptor.parent_join_column == "id"
    assert descriptor.lateral_shape is LateralJoinShape.UNSUPPORTED
    assert descriptor.through_model is None


def test_reverse_one_to_one_classifies_direct_fk():
    """Reverse O2O: windowable DIRECT_FK with scalar cardinality (analog B, scalar)."""
    from apps.library.models import Patron

    field = Patron._meta.get_field("card")
    descriptor = classify_relation_join(field)
    assert descriptor.kind == "reverse_one_to_one"
    assert descriptor.windowable is True
    assert descriptor.partition_expr == "patron_id"
    assert descriptor.parent_join_column == "patron_id"
    assert descriptor.lateral_shape is LateralJoinShape.DIRECT_FK


def test_windowable_kind_without_partition_classifies_unwindowable():
    """A many-shaped double with no resolvable partition -> windowable False.

    The shim (``window_partition_for_prefetch``) raises its could-not-resolve
    ``OptimizerError`` from this classification; the descriptor itself never
    raises (callers own the fallback posture).
    """
    double = SimpleNamespace(
        name="mystery",
        many_to_many=False,
        one_to_many=True,
        one_to_one=False,
        auto_created=True,
        remote_field=None,
        field=None,
        reverse_connector_attname=None,
    )
    descriptor = classify_relation_join(double)
    assert descriptor.kind == "reverse_many_to_one"
    assert descriptor.windowable is False
    assert descriptor.partition_expr is None
    assert descriptor.parent_join_column is None


def test_m2m_double_without_related_model_has_no_connector():
    """An M2M double lacking ``related_model`` -> connector ``None`` (defensive)."""
    double = SimpleNamespace(
        name="tags",
        many_to_many=True,
        one_to_many=False,
        one_to_one=False,
        auto_created=False,
        remote_field=SimpleNamespace(attname=None, name="posts", through=None),
        through=None,
        related_model=None,
    )
    descriptor = classify_relation_join(double)
    assert descriptor.windowable is True
    assert descriptor.partition_expr == "posts"
    assert descriptor.parent_join_column is None
    assert descriptor.lateral_shape is LateralJoinShape.THROUGH_TABLE
    # No through model -> no resolvable through-link FK pair either.
    assert descriptor.parent_link_field is None
    assert descriptor.through_child_field is None
