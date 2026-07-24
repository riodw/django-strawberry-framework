"""FilterSet tests for Meta validation, relations, Relay fields, permissions, visibility, and logic trees.

Covers the metaclass (`FilterSetMetaclass`), `FilterSet`'s class-creation
behavior (cycle-safe `get_filters` expansion + `_get_fields` narrowing),
the Decision-4 owner-aware Relay-vs-scalar conditional in
`filter_for_field`, and the Decision-8 / M1-of-rev5 apply pipeline
(`apply_sync` / `apply_async` / `apply` + the five named helpers).
"""

from __future__ import annotations

import contextlib
import datetime
import uuid
from collections import OrderedDict
from typing import Any, NamedTuple
from unittest import mock

import pytest
import strawberry
from apps.kanban import filters as kanban_filters
from apps.kanban import models as kanban_models
from apps.library import models as library_models
from apps.library.filters import BookFilter
from apps.products.models import Category, Item
from apps.scalars import models as scalar_models
from django.db.models import Q
from django.http import HttpRequest
from django_filters import CharFilter
from graphql import GraphQLError

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import (
    FilterSet,
    FilterSetMetaclass,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    RelatedFilter,
)
from django_strawberry_framework.filters.base import (
    _GLOBALID_RELATION_PK_ATTR,
    _GlobalIDMultipleChoiceField,
)
from django_strawberry_framework.filters.inputs import convert_filter_to_input_annotation
from django_strawberry_framework.filters.sets import (
    _GENERATION_TOKEN_ATTR,
    _MODEL_CHOICE_ONLY_EXTRAS,
    FilterGenerationProvenance,
    _fingerprint_of,
    _lookups_for_field,
    filter_generation_provenance,
)
from django_strawberry_framework.optimizer.predicates import correlated_inner_root
from django_strawberry_framework.registry import registry
from django_strawberry_framework.sets_mixins import collect_related_declarations
from django_strawberry_framework.types.relay import SyncMisuseError, apply_interfaces
from tests._relation_fixtures import (
    RpToFieldChild,
    RpToFieldTarget,
    relation_fixture_tables,
)


class ShelfProxy(library_models.Shelf):
    """Module-scope proxy of ``Shelf`` for the model-mismatch precheck test.

    Declared at module scope (not inside the test body) so Django's app
    registry sees it during normal app loading; late-bound model
    registration inside a function body has shifting tolerance across
    Django releases.
    """

    class Meta:
        proxy = True
        app_label = "library"


@pytest.fixture(autouse=True)
def _isolate_registry():
    registry.clear()
    yield
    registry.clear()


def _make_info(request: HttpRequest | None = None) -> Any:
    """Return a minimal `info`-shaped object carrying `info.context.request`."""

    class _Context:
        def __init__(self, req: HttpRequest):
            self.request = req

    class _Info:
        def __init__(self, ctx):
            self.context = ctx

    return _Info(_Context(request or HttpRequest()))


class _MedtricsLoanGraph(NamedTuple):
    """Captured pks of the four root loans seeded by ``_seed_medtrics_loan_graph``.

    Pks are captured at creation time; assertions must compare against these
    rather than trusting insertion-order pk faith.
    """

    relation_and_direct: int
    relation_only: int
    direct_only: int
    unrelated: int


def _seed_medtrics_loan_graph() -> _MedtricsLoanGraph:
    """Seed the shared Medtrics reproduction graph on the library models.

    Builds ``Loan.book -> Book.loans -> Loan.patron -> Patron.email`` so a
    self-join across ``book__loans__patron__email`` fans out root ``Loan`` rows.
    Uses inline ``Model.objects.create`` (the library app has no services).

    Four root loans, with distinct patrons per loan (the
    ``unique_open_loan_per_book_patron`` constraint forbids repeating a
    ``(book, patron)`` pair):

    - ``relation_and_direct``: on ``shared_book``, note contains "Cardio",
      patron email "Cardio A";
    - ``relation_only``: also on ``shared_book``, note WITHOUT "Cardio",
      patron email "Cardio B";
    - ``direct_only``: on a second book, note contains "Cardio", patron email
      "Neurology";
    - ``unrelated``: on a third book, note and patron email neither containing
      "Cardio".
    """
    branch = library_models.Branch.objects.create(name="Medtrics Central")
    shelf = library_models.Shelf.objects.create(branch=branch, code="MED-1")
    shared_book = library_models.Book.objects.create(shelf=shelf, title="Shared Ward Manual")
    second_book = library_models.Book.objects.create(shelf=shelf, title="Second Manual")
    third_book = library_models.Book.objects.create(shelf=shelf, title="Third Manual")

    patron_a = library_models.Patron.objects.create(name="Patron A", email="Cardio A")
    patron_b = library_models.Patron.objects.create(name="Patron B", email="Cardio B")
    patron_c = library_models.Patron.objects.create(name="Patron C", email="Neurology")
    patron_d = library_models.Patron.objects.create(name="Patron D", email="Ortho")

    relation_and_direct = library_models.Loan.objects.create(
        book=shared_book,
        patron=patron_a,
        note="Cardio direct",
    )
    relation_only = library_models.Loan.objects.create(
        book=shared_book,
        patron=patron_b,
        note="routine checkout",
    )
    direct_only = library_models.Loan.objects.create(
        book=second_book,
        patron=patron_c,
        note="Cardio direct",
    )
    unrelated = library_models.Loan.objects.create(
        book=third_book,
        patron=patron_d,
        note="routine checkout",
    )

    return _MedtricsLoanGraph(
        relation_and_direct=relation_and_direct.pk,
        relation_only=relation_only.pk,
        direct_only=direct_only.pk,
        unrelated=unrelated.pk,
    )


# ---------------------------------------------------------------------------
# Metaclass behavior
# ---------------------------------------------------------------------------


def test_filterset_metaclass_is_django_filter_metaclass_subclass():
    from django_filters.filterset import FilterSetMetaclass as DjangoFilterMetaclass

    assert issubclass(FilterSetMetaclass, DjangoFilterMetaclass)


def test_filterset_metaclass_collects_related_filters():
    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    assert isinstance(BranchFilter.related_filters, OrderedDict)
    assert "shelves" in BranchFilter.related_filters
    assert BranchFilter.related_filters["shelves"].bound_filterset is BranchFilter


def test_filterset_metaclass_none_removal_survives_diamond_inheritance():
    """An earlier base's ``None`` tombstone prevents later-base resurrection."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BaseFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    class RemovedFilter(BaseFilter):
        shelves = None

    class KeptFilter(BaseFilter):
        pass

    class CombinedFilter(RemovedFilter, KeptFilter):
        pass

    for filterset_cls in (RemovedFilter, CombinedFilter):
        assert "shelves" not in filterset_cls.declared_filters
        assert "shelves" not in filterset_cls.related_filters
        assert not any(
            name == "shelves" or name.startswith("shelves__")
            for name in filterset_cls.base_filters
        )
        assert not any(
            name == "shelves" or name.startswith("shelves__")
            for name in filterset_cls.get_filters()
        )
    assert "shelves" in BaseFilter.related_filters


def test_filterset_metaclass_aliases_filter_fields_to_fields():
    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            filter_fields = {"code": ["exact"]}

    # Aliasing happens at metaclass time; the `Meta.fields` attribute lands.
    assert ShelfFilter._meta.fields == {"code": ["exact"]}


def test_filterset_metaclass_does_not_expand_at_class_creation():
    class ShelfFilter(FilterSet):
        # `RelatedFilter("SiblingFilter")` references a class declared LATER.
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter("ShelfFilter", field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # Class creation succeeded with a string forward reference; nothing cached yet.
    assert BranchFilter.__dict__.get("_expanded_filters") is None


# ---------------------------------------------------------------------------
# get_filters expansion
# ---------------------------------------------------------------------------


def test_filterset_get_filters_triggers_expansion():
    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact", "icontains"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    filters = BranchFilter.get_filters()
    # Same-class filter plus expanded `<rel>__<child_lookup>` keys.
    assert "name" in filters
    assert "shelves__code" in filters
    assert "shelves__code__icontains" in filters


def test_filterset_get_filters_caches_after_full_resolution():
    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    first = BranchFilter.get_filters()
    second = BranchFilter.get_filters()
    assert first is second
    assert BranchFilter.__dict__.get("_expanded_filters") is first


def test_filterset_get_filters_resets_expansion_guard():
    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    BranchFilter.get_filters()
    assert BranchFilter._is_expanding_filters is False


def test_filterset_get_filters_does_not_cache_when_string_filterset_remains():
    class BranchFilter(FilterSet):
        # Reference to a non-existent class - `expand_related_filter` raises.
        bogus = RelatedFilter("DefinitelyDoesNotExistFilter", field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    with pytest.raises(ImportError):
        BranchFilter.get_filters()
    assert BranchFilter.__dict__.get("_expanded_filters") is None


# ---------------------------------------------------------------------------
# _get_fields override
# ---------------------------------------------------------------------------


def test_filterset_get_fields_includes_pk_for_all_fields_shorthand():
    class ItemFilter(FilterSet):
        class Meta:
            model = Item
            fields = "__all__"
            # ``Item.attachment`` is a ``FileField`` (spec-038 Slice 4) that
            # ``django-filter`` has no default filter for; the ``"__all__"``
            # sweep would otherwise raise on it. Excluding it keeps this test
            # focused on its intent: the shorthand adds the PK column.
            exclude = ("attachment",)

    fields = ItemFilter.get_fields()
    pk_name = Item._meta.pk.name
    assert pk_name in fields


def test_filterset_get_fields_excludes_m2m_for_all_fields_shorthand():
    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = "__all__"

    fields = BookFilter.get_fields()
    # `Book.genres` is an M2M relation; it must be excluded.
    assert "genres" not in fields


def test_filterset_get_fields_does_not_alter_explicit_dict_meta():
    class ItemFilter(FilterSet):
        class Meta:
            model = Item
            fields = {"name": ["exact"]}

    fields = ItemFilter.get_fields()
    # Explicit dict is returned by `super().get_fields()` unchanged.
    assert set(fields.keys()) == {"name"}


# ---------------------------------------------------------------------------
# Decision-4 owner-aware filter_for_field
# ---------------------------------------------------------------------------


def test_filter_for_field_picks_global_id_multiple_choice_filter_for_relay_m2m_target():
    """An M2M to a Relay-Node-shaped target maps to `GlobalIDMultipleChoiceFilter`.

    Decision 4 ports BOTH `GlobalIDFilter` (single-valued) and
    `GlobalIDMultipleChoiceFilter` (multi-valued); the runtime override
    has to pick the multi-valued primitive for `ManyToManyField` so the
    underlying queryset semantics match the field's cardinality.
    """

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    # The finalizer's owner-binding pass lands in Slice 3; here we just need
    # `GenreType` to be a subclass of `relay.Node` so `implements_relay_node`
    # returns `True`. `apply_interfaces` is the existing Slice-4-of-spec-011
    # helper that injects bases.
    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class GenreFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"name": ["exact"]}

    class BookFilter(FilterSet):
        genres = RelatedFilter(GenreFilter, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("genres")
    resolved = BookFilter.filter_for_field(field, "genres")
    assert isinstance(resolved, GlobalIDMultipleChoiceFilter)


def test_filter_for_field_picks_global_id_filter_for_relay_forward_fk_target():
    """A forward FK to a Relay-Node-shaped target maps to `GlobalIDFilter`.

    Complement of the M2M case above - single-valued relations pick the
    single-value Relay primitive.
    """

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(ShelfType, ShelfType.__django_strawberry_definition__)

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("shelf")
    resolved = BookFilter.filter_for_field(field, "shelf")
    assert isinstance(resolved, GlobalIDFilter)
    assert not isinstance(resolved, GlobalIDMultipleChoiceFilter)


def test_filter_for_field_marks_non_pk_to_field_relation_globalid_with_pk_path():
    """A forward FK on a non-pk ``to_field`` gets the pk-qualification flag (High 3).

    The generated ``GlobalIDFilter`` must carry the boolean
    ``_GLOBALID_RELATION_PK_ATTR`` flag set ``True`` so its predicate derives
    ``f"{field_name}__pk"`` and compares the target's primary key (which a Relay
    GlobalID carries) rather than the raw FK-stored ``code`` column.
    """

    class TargetType(DjangoType):
        class Meta:
            model = RpToFieldTarget
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(TargetType, TargetType.__django_strawberry_definition__)

    class ChildFilter(FilterSet):
        class Meta:
            model = RpToFieldChild
            fields = {"name": ["exact"]}

    field = RpToFieldChild._meta.get_field("target")
    resolved = ChildFilter.filter_for_field(field, "target")
    assert isinstance(resolved, GlobalIDFilter)
    assert getattr(resolved, _GLOBALID_RELATION_PK_ATTR, None) is True


def test_filter_for_field_fk_to_pk_relation_globalid_carries_no_marker():
    """An ordinary FK-to-pk GlobalID relation filter must NOT carry the marker."""

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(ShelfType, ShelfType.__django_strawberry_definition__)

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("shelf")
    resolved = BookFilter.filter_for_field(field, "shelf")
    assert isinstance(resolved, GlobalIDFilter)
    assert getattr(resolved, _GLOBALID_RELATION_PK_ATTR, False) is not True


# ---------------------------------------------------------------------------
# High 3 (feedback.md): a forward, single-valued Relay relation ``in`` lookup
# is list-shaped over the wire, so the PRODUCTION generation path must emit
# ``GlobalIDMultipleChoiceFilter`` -- NOT the scalar ``GlobalIDFilter`` that a
# cardinality-only reselection produced. These tests drive the real
# ``FilterSet.get_filters()`` generation path (not a hand-built primitive) so
# they prove the generated class, its list-shaped input annotation, and its
# execution. Red->green: before the fix, ``shelf__in`` / ``target__in``
# generated ``GlobalIDFilter`` and rejected the list at decode time
# ("Invalid GlobalID: [...] is not a valid GlobalID ...").
# ---------------------------------------------------------------------------


def test_generated_forward_fk_in_is_multiple_choice_over_fk_to_pk():
    """Forward Relay FK ``in`` over an ordinary FK-to-pk generates a list filter (High 3).

    The generated ``shelf__in`` leaf must be ``GlobalIDMultipleChoiceFilter`` with a
    ``list[str]`` input annotation, while the sibling ``shelf`` (exact) leaf stays the
    scalar ``GlobalIDFilter`` -- proving the cardinality-selected non-``in`` shape is
    byte-identical and only the lookup-aware ``in`` shape changed.
    """

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(ShelfType, ShelfType.__django_strawberry_definition__)

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"shelf": ["exact", "in"]}

    field = library_models.Book._meta.get_field("shelf")
    generated = BookFilter.get_filters()

    in_leaf = generated["shelf__in"]
    assert isinstance(in_leaf, GlobalIDMultipleChoiceFilter)
    assert convert_filter_to_input_annotation(in_leaf, field) == list[str] | None
    # An ordinary FK-to-pk relation carries no pk-qualification marker.
    assert getattr(in_leaf, _GLOBALID_RELATION_PK_ATTR, False) is not True

    exact_leaf = generated["shelf"]
    assert isinstance(exact_leaf, GlobalIDFilter)
    assert not isinstance(exact_leaf, GlobalIDMultipleChoiceFilter)
    assert convert_filter_to_input_annotation(exact_leaf, field) == str | None


@pytest.mark.django_db
def test_generated_forward_fk_in_execution_matches_requested_targets():
    """The generated forward-FK ``in`` leaf unions the requested targets (High 3).

    Also pins the package's established list semantics for the generated leaf: an
    empty list matches nothing and a malformed member rejects the whole input with
    the offending index named.
    """

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(ShelfType, ShelfType.__django_strawberry_definition__)

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"shelf": ["in"]}

    in_leaf = BookFilter.get_filters()["shelf__in"]
    assert isinstance(in_leaf, GlobalIDMultipleChoiceFilter)

    branch = library_models.Branch.objects.create(name="Central")
    shelf_a = library_models.Shelf.objects.create(code="A", branch=branch)
    shelf_b = library_models.Shelf.objects.create(code="B", branch=branch)
    shelf_c = library_models.Shelf.objects.create(code="C", branch=branch)
    library_models.Book.objects.create(title="book-a", shelf=shelf_a)
    library_models.Book.objects.create(title="book-b", shelf=shelf_b)
    library_models.Book.objects.create(title="book-c", shelf=shelf_c)

    requested = [
        strawberry.relay.to_base64("ShelfType", str(shelf_a.pk)),
        strawberry.relay.to_base64("ShelfType", str(shelf_b.pk)),
    ]
    result = in_leaf.filter(library_models.Book.objects.all(), requested)
    assert set(result.values_list("title", flat=True)) == {"book-a", "book-b"}
    # Matches the explicit whole-list ``shelf__in`` ORM (never a per-element OR).
    expected = library_models.Book.objects.filter(shelf__in=[shelf_a.pk, shelf_b.pk])
    assert set(result.values_list("pk", flat=True)) == set(
        expected.values_list("pk", flat=True),
    )

    # Empty list is a restrictive membership predicate: it matches nothing.
    assert in_leaf.filter(library_models.Book.objects.all(), []).count() == 0

    # A malformed member rejects the whole input with the offending index named.
    with pytest.raises(GraphQLError, match="index 1"):
        in_leaf.filter(
            library_models.Book.objects.all(),
            [strawberry.relay.to_base64("ShelfType", str(shelf_a.pk)), "not-a-globalid"],
        )


def test_generated_forward_fk_to_field_in_is_pk_qualified_multiple_choice():
    """Forward Relay FK ``in`` over a non-pk ``to_field`` is pk-qualified (High 3).

    ``RpToFieldChild.target`` binds on ``RpToFieldTarget.code`` (a non-pk column), so
    the generated ``target__in`` leaf must be a ``GlobalIDMultipleChoiceFilter`` that
    STILL carries the boolean ``_GLOBALID_RELATION_PK_ATTR`` marker (stamped after the
    lookup-aware class is chosen) so its predicate derives ``target__pk__in`` and
    compares the target primary key a Relay GlobalID carries. The sibling exact leaf
    keeps the marked scalar ``GlobalIDFilter`` shape.
    """

    class TargetType(DjangoType):
        class Meta:
            model = RpToFieldTarget
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(TargetType, TargetType.__django_strawberry_definition__)

    class ChildFilter(FilterSet):
        class Meta:
            model = RpToFieldChild
            fields = {"target": ["exact", "in"]}

    field = RpToFieldChild._meta.get_field("target")
    generated = ChildFilter.get_filters()

    in_leaf = generated["target__in"]
    assert isinstance(in_leaf, GlobalIDMultipleChoiceFilter)
    assert getattr(in_leaf, _GLOBALID_RELATION_PK_ATTR, None) is True
    assert convert_filter_to_input_annotation(in_leaf, field) == list[str] | None

    exact_leaf = generated["target"]
    assert isinstance(exact_leaf, GlobalIDFilter)
    assert not isinstance(exact_leaf, GlobalIDMultipleChoiceFilter)
    assert getattr(exact_leaf, _GLOBALID_RELATION_PK_ATTR, None) is True


@pytest.mark.django_db(transaction=True)
def test_generated_forward_fk_to_field_in_execution_matches_by_decoded_pk():
    """The generated non-pk-``to_field`` ``in`` leaf unions targets by decoded pk (High 3).

    The FK stores / joins on ``code`` but a Relay GlobalID carries the target's pk, so
    the pk-qualified ``target__pk__in`` predicate returns the children of the encoded
    targets, whereas the raw ``target__in`` (pk values against the ``code`` column)
    matches nothing -- the red->green proof that ``pk != code`` matters.
    """
    from django.db import connection

    class TargetType(DjangoType):
        class Meta:
            model = RpToFieldTarget
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(TargetType, TargetType.__django_strawberry_definition__)

    class ChildFilter(FilterSet):
        class Meta:
            model = RpToFieldChild
            fields = {"target": ["in"]}

    in_leaf = ChildFilter.get_filters()["target__in"]
    assert isinstance(in_leaf, GlobalIDMultipleChoiceFilter)
    assert getattr(in_leaf, _GLOBALID_RELATION_PK_ATTR, None) is True

    with relation_fixture_tables(connection):
        alpha = RpToFieldTarget.objects.create(code="ALPHA", label="A")
        beta = RpToFieldTarget.objects.create(code="BETA", label="B")
        gamma = RpToFieldTarget.objects.create(code="GAMMA", label="G")
        RpToFieldChild.objects.create(target=alpha, name="a-child")
        RpToFieldChild.objects.create(target=beta, name="b-child")
        RpToFieldChild.objects.create(target=gamma, name="g-child")
        assert alpha.pk != alpha.code

        requested = [
            strawberry.relay.to_base64("TargetType", str(alpha.pk)),
            strawberry.relay.to_base64("TargetType", str(beta.pk)),
        ]
        result = in_leaf.filter(RpToFieldChild.objects.all(), requested)
        assert set(result.values_list("name", flat=True)) == {"a-child", "b-child"}
        expected = RpToFieldChild.objects.filter(target__pk__in=[alpha.pk, beta.pk])
        assert set(result.values_list("pk", flat=True)) == set(
            expected.values_list("pk", flat=True),
        )

        # The raw non-pk path compares the pk values against the stored ``code``
        # column and matches nothing -- why the ``__pk`` qualification is required.
        wrong = RpToFieldChild.objects.filter(target__in=[str(alpha.pk), str(beta.pk)])
        assert wrong.count() == 0


@pytest.mark.django_db(transaction=True)
def test_expanded_related_filter_derives_pk_path_from_live_field_name():
    """Finding 2: an expanded ``to_field`` GlobalID leaf compiles against the rebased path.

    ``_expand_related_filter`` deepcopies a child leaf and rebases its
    ``field_name`` to ``"<relation>__<child_field>"``. The old ABSOLUTE-string
    marker (``"target__pk"``) went stale after that rebase and compiled
    ``target__pk`` against the PARENT model -> ``FieldError``. The boolean flag
    survives the deepcopy, and ``GlobalIDFilter.filter`` derives
    ``"children__target__pk"`` from the LIVE ``field_name``, so the expanded leaf
    filters the parent correctly against the target's primary key (``pk != code``).
    """
    from django.core.exceptions import FieldError
    from django.db import connection

    class TargetType(DjangoType):
        class Meta:
            model = RpToFieldTarget
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(TargetType, TargetType.__django_strawberry_definition__)

    class ChildFilter(FilterSet):
        class Meta:
            model = RpToFieldChild
            fields = {"target": ["exact"]}

    class ParentFilter(FilterSet):
        children = RelatedFilter(ChildFilter)

        class Meta:
            model = RpToFieldTarget
            fields = {"code": ["exact"]}

    # (a) The expanded leaf's LIVE field_name is the full relation path, and the
    # boolean pk-qualification flag rode the deepcopy through unchanged.
    expanded_leaf = ParentFilter.get_filters()["children__target"]
    assert isinstance(expanded_leaf, GlobalIDFilter)
    assert expanded_leaf.field_name == "children__target"
    assert getattr(expanded_leaf, _GLOBALID_RELATION_PK_ATTR, False) is True

    with relation_fixture_tables(connection):
        t1 = RpToFieldTarget.objects.create(code="C1", label="one")
        t2 = RpToFieldTarget.objects.create(code="C2", label="two")
        RpToFieldTarget.objects.create(code="C3", label="three")  # no children
        RpToFieldChild.objects.create(target=t1, name="t1-child")
        RpToFieldChild.objects.create(target=t2, name="t2-child")
        assert t1.pk != t1.code

        encoded = strawberry.relay.to_base64("TargetType", str(t1.pk))
        result = expanded_leaf.filter(RpToFieldTarget.objects.all(), encoded)

        # (b) The derived ``children__target__pk`` predicate returns exactly the
        # parent whose children point back at ``t1`` -- matching the explicit ORM.
        production = list(result.order_by("id").values_list("pk", flat=True))
        expected = list(
            RpToFieldTarget.objects.filter(children__target__pk=t1.pk)
            .order_by("id")
            .values_list("pk", flat=True),
        )
        assert production == expected == [t1.pk]

        # The rebased-but-NOT-pk-qualified predicate compares against the ``code``
        # column (pk != code) and wrongly matches nothing -- why ``__pk`` matters.
        assert list(RpToFieldTarget.objects.filter(children__target=str(t1.pk))) == []

        # The OLD absolute-string marker ("target__pk") would compile against the
        # PARENT model, which has no ``target`` field -> FieldError.
        with pytest.raises(FieldError):
            list(RpToFieldTarget.objects.filter(target__pk=str(t1.pk)))


def _passthrough_filter(qs, value):
    """A stand-in ``.filter`` callable that returns the queryset unchanged."""
    return qs


@pytest.mark.django_db(transaction=True)
def test_expanded_to_field_leaf_live_signature_gates_correlated_exists():
    """Blocker 2 end-to-end: the canonical semantic signature is the ONE auth gate.

    Exercises the expanded ``children__target`` shape through the PARENT
    ``FilterSet`` and its ``.qs`` -> ``FilterSet._apply_flat_leaves`` live gate --
    NOT ``expanded_leaf.filter()`` in isolation like
    ``test_expanded_related_filter_derives_pk_path_from_live_field_name``, which
    never instantiates the parent or runs the authorization check. The leaf is a
    ``GlobalIDFilter`` on ``RpToFieldChild.target`` (a forward FK on the non-pk
    ``to_field="code"``), reached across the reverse to-many ``children`` prefix,
    so it is eligible for the correlated adapter AND pk-marked.

    Red->green vs the pre-fix ``_CandidateFingerprint`` (feedback.md Blocker 2):
    before the semantic signature covered the pk-qualification marker and the
    effective ``.filter`` implementation, flipping ``_GLOBALID_RELATION_PK_ATTR``
    or replacing ``.filter`` on the LIVE per-request instance left the fingerprint
    (and token) still matching, so the tampered filter was STILL routed through
    ``EXISTS`` and compiled the known-wrong raw-``to_field`` comparison. Now every
    such drift diverges the signature and fails closed to the outer invocation.
    """
    from django.db import connection

    class TargetType(DjangoType):
        class Meta:
            model = RpToFieldTarget
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(TargetType, TargetType.__django_strawberry_definition__)

    class ChildFilter(FilterSet):
        class Meta:
            model = RpToFieldChild
            fields = {"target": ["exact"]}

    class ParentFilter(FilterSet):
        children = RelatedFilter(ChildFilter)

        class Meta:
            model = RpToFieldTarget
            fields = {"code": ["exact"]}

    # Publish the atomic expansion snapshot (sets ``base_filters`` + candidate
    # rows). The expanded to_field leaf is an eligible, token-bearing, pk-marked
    # candidate; its FROZEN signature now records the pk-qualification decision.
    ParentFilter.get_filters()
    candidate = ParentFilter._expansion_snapshot().candidates["children__target"]
    assert candidate.eligible is True
    assert candidate.token is not None
    assert candidate.fingerprint is not None
    assert candidate.fingerprint.pk_qualified is True

    with relation_fixture_tables(connection):
        t1 = RpToFieldTarget.objects.create(code="C1", label="one")
        RpToFieldChild.objects.create(target=t1, name="t1-child")
        t2 = RpToFieldTarget.objects.create(code="C2", label="two")
        RpToFieldChild.objects.create(target=t2, name="t2-child")
        t3 = RpToFieldTarget.objects.create(code="C3", label="three")  # no children
        # The auto pk and the FK-stored ``code`` to_field column differ, so ONLY the
        # ``__pk`` qualification returns the right row.
        assert t1.pk != t1.code
        encoded = strawberry.relay.to_base64("TargetType", str(t1.pk))
        outer = RpToFieldTarget.objects.order_by("id")

        def _build_fs():
            return ParentFilter(
                data={"children__target": encoded},
                queryset=outer,
                request=HttpRequest(),
            )

        # (1) UNTOUCHED live instance -> authorized -> ONE correlated EXISTS, the
        #     pk-qualified rows (only ``t1``, whose child's ``target`` pk is ``t1``).
        clean_fs = _build_fs()
        clean_qs = clean_fs.qs
        assert len(_reserved_aliases(clean_qs)) == 1
        assert str(clean_qs.query).upper().count("EXISTS") == 1
        assert list(clean_qs.order_by("id").values_list("pk", flat=True)) == [t1.pk]
        # It was authorized BECAUSE the live signature + token match the frozen row.
        clean_leaf = clean_fs.filters["children__target"]
        assert getattr(clean_leaf, _GENERATION_TOKEN_ATTR, None) == candidate.token
        assert _fingerprint_of(clean_leaf) == candidate.fingerprint

        # (2) FLIP the pk-marker on the LIVE per-request instance -> FAIL CLOSED.
        #     No reserved EXISTS alias attaches; the (now-tampered) predicate runs as
        #     the plain outer JOIN invocation, never blessed into the adapter.
        flipped_fs = _build_fs()
        flipped_leaf = flipped_fs.filters["children__target"]
        setattr(flipped_leaf, _GLOBALID_RELATION_PK_ATTR, False)
        # (4) TOKEN ALONE is INSUFFICIENT: the token still equals the frozen row's
        #     token, but the signature diverged, so the leaf is not routed.
        assert getattr(flipped_leaf, _GENERATION_TOKEN_ATTR, None) == candidate.token
        assert _fingerprint_of(flipped_leaf) != candidate.fingerprint
        flipped_qs = flipped_fs.qs
        assert _reserved_aliases(flipped_qs) == []
        assert "EXISTS" not in str(flipped_qs.query).upper()

        # (3) REPLACE the live ``.filter`` callable -> FAIL CLOSED. The instance-level
        #     override diverges the signature (frozen ``filter_override`` is ``None``);
        #     the outer invocation runs the override (a passthrough), so no reserved
        #     EXISTS alias attaches and every row is returned unfiltered.
        replaced_fs = _build_fs()
        replaced_leaf = replaced_fs.filters["children__target"]
        replaced_leaf.filter = _passthrough_filter
        assert getattr(replaced_leaf, _GENERATION_TOKEN_ATTR, None) == candidate.token
        assert _fingerprint_of(replaced_leaf) != candidate.fingerprint
        replaced_qs = replaced_fs.qs
        assert _reserved_aliases(replaced_qs) == []
        assert "EXISTS" not in str(replaced_qs.query).upper()
        assert list(replaced_qs.order_by("id").values_list("pk", flat=True)) == [
            t1.pk,
            t2.pk,
            t3.pk,
        ]


@pytest.mark.django_db(transaction=True)
def test_expanded_to_field_in_leaf_routes_through_correlated_exists():
    """Round-4 High 3: the expanded non-pk-``to_field`` ``in`` leaf through the adapter.

    The only regression that composes all three recently corrected mechanisms at
    once -- lookup-aware ``in``, non-pk pk-qualification, and live candidate
    authorization -- over the reverse to-many ``children`` prefix. The prior High-3
    ``in`` tests invoked the generated CHILD leaf directly on the child queryset;
    this expands ``children__target__in`` across the reverse hop through the PARENT
    ``FilterSet`` and its ``.qs`` -> ``_apply_flat_leaves`` gate. Proves the
    expanded live class + list annotation, marker + token survival through
    deepcopy/rebasing, one correlated ``EXISTS`` (no outer join / ``DISTINCT``),
    correct rows for two encoded target pks (where ``pk != code``), and restrictive
    empty-list behavior through the adapter.
    """
    from django.db import connection

    class TargetType(DjangoType):
        class Meta:
            model = RpToFieldTarget
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(TargetType, TargetType.__django_strawberry_definition__)

    class ChildFilter(FilterSet):
        class Meta:
            model = RpToFieldChild
            fields = {"target": ["in"]}

    class ParentFilter(FilterSet):
        children = RelatedFilter(ChildFilter)

        class Meta:
            model = RpToFieldTarget
            fields = {"code": ["exact"]}

    ParentFilter.get_filters()
    candidate = ParentFilter._expansion_snapshot().candidates["children__target__in"]
    assert candidate.eligible is True
    assert candidate.token is not None
    assert candidate.fingerprint is not None
    assert candidate.fingerprint.pk_qualified is True

    expanded_leaf = ParentFilter.get_filters()["children__target__in"]
    assert isinstance(expanded_leaf, GlobalIDMultipleChoiceFilter)
    assert getattr(expanded_leaf, _GLOBALID_RELATION_PK_ATTR, None) is True
    child_target_field = RpToFieldChild._meta.get_field("target")
    assert (
        convert_filter_to_input_annotation(expanded_leaf, child_target_field) == list[str] | None
    )

    with relation_fixture_tables(connection):
        t1 = RpToFieldTarget.objects.create(code="C1", label="one")
        RpToFieldChild.objects.create(target=t1, name="c1")
        t2 = RpToFieldTarget.objects.create(code="C2", label="two")
        RpToFieldChild.objects.create(target=t2, name="c2")
        t3 = RpToFieldTarget.objects.create(code="C3", label="three")  # no children
        assert t1.pk != t1.code
        requested = [
            strawberry.relay.to_base64("TargetType", str(t1.pk)),
            strawberry.relay.to_base64("TargetType", str(t2.pk)),
        ]
        outer = RpToFieldTarget.objects.order_by("id")

        clean_fs = ParentFilter(
            data={"children__target__in": requested},
            queryset=outer,
            request=HttpRequest(),
        )
        clean_qs = clean_fs.qs
        # Marker + token survived the deepcopy/rebasing onto the live instance.
        live = clean_fs.filters["children__target__in"]
        assert getattr(live, _GENERATION_TOKEN_ATTR, None) == candidate.token
        assert getattr(live, _GLOBALID_RELATION_PK_ATTR, None) is True
        assert _fingerprint_of(live) == candidate.fingerprint
        # One correlated EXISTS; no outer join (root table only) and no DISTINCT.
        assert len(_reserved_aliases(clean_qs)) == 1
        sql = str(clean_qs.query).upper()
        assert sql.count("EXISTS") == 1
        assert "DISTINCT" not in sql
        outer_tables = sorted({j.table_name for j in clean_qs.query.alias_map.values()})
        assert outer_tables == [RpToFieldTarget._meta.db_table]
        # Correct rows: t3 has no child, so only the two encoded (by pk) targets match.
        assert list(clean_qs.order_by("id").values_list("pk", flat=True)) == [t1.pk, t2.pk]

        # Restrictive empty list THROUGH the adapter: the leaf is still routed (it is
        # an eligible token-matched candidate), invoked on the inner root, and yields
        # ``inner_root.none()``; ``attach_exists`` composes ``Exists(none)``, which
        # Django folds to a constant-false predicate. The result is 0 rows out of the
        # 3 seeded targets -- restrictive, NOT the no-op that would return all rows.
        empty_qs = ParentFilter(
            data={"children__target__in": []},
            queryset=outer,
            request=HttpRequest(),
        ).qs
        assert RpToFieldTarget.objects.count() == 3
        assert list(empty_qs.values_list("pk", flat=True)) == []


# ---------------------------------------------------------------------------
# Round-4 Blocker 2 (feedback.md): a consumer-selected relation filter over a
# Relay-node target -- chosen via ``Meta.filter_overrides`` OR a shadowed
# class-level ``FILTER_DEFAULTS`` -- must be honored byte-for-byte. Before the
# fix, ``filter_for_lookup`` unconditionally replaced ANY Relay-node relation
# with a package GlobalID primitive and ``filter_for_field`` stamped it
# ``package_replacement``, DISCARDING the consumer's filter class AND marking the
# leaf eligible. Now ownership is resolved once (``_generation_origin_for_field``)
# BEFORE any Relay conversion: only the proven framework default is converted; a
# consumer selection is returned unchanged, stays ``override_generated``, and
# never gets a candidate row.
# ---------------------------------------------------------------------------


def test_blocker2_direct_m2m_relation_override_on_relay_target_is_honored():
    """A ``Meta.filter_overrides`` M2M relation filter over a Relay target is kept."""
    import django_filters
    from django.db import models as django_models

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class CustomRelationFilter(django_filters.ModelMultipleChoiceFilter):
        pass

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact"]}
            filter_overrides = {
                django_models.ManyToManyField: {"filter_class": CustomRelationFilter},
            }

    leaf = BookFilter.get_filters()["genres"]
    # The consumer's class survives -- NOT replaced by GlobalIDMultipleChoiceFilter.
    assert isinstance(leaf, CustomRelationFilter)
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "override_generated"
    # override_generated is not framework-generated, so it gets NO candidate row.
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None
    assert "genres" not in snapshot.candidates


def test_blocker2_direct_forward_fk_relation_override_on_relay_target_is_honored():
    """A ``Meta.filter_overrides`` forward-FK filter over a Relay target is kept."""
    import django_filters
    from django.db import models as django_models

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(ShelfType, ShelfType.__django_strawberry_definition__)

    class CustomFKFilter(django_filters.ModelChoiceFilter):
        pass

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"shelf": ["exact"]}
            filter_overrides = {
                django_models.ForeignKey: {"filter_class": CustomFKFilter},
            }

    leaf = BookFilter.get_filters()["shelf"]
    assert isinstance(leaf, CustomFKFilter)
    assert not isinstance(leaf, GlobalIDFilter)
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "override_generated"
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None
    assert "shelf" not in snapshot.candidates


def test_blocker2_filter_defaults_shadow_relation_override_on_relay_target_is_honored():
    """A shadowed class-level ``FILTER_DEFAULTS`` relation override is honored too.

    The capability check already withholds a token from a ``FILTER_DEFAULTS``
    shadow (``generation_capable=False``), but before the fix the Relay conversion
    STILL discarded the consumer's class and stamped ``package_replacement``. The
    ownership oracle now detects the shadow and leaves the selection unchanged.
    """
    import django_filters
    from django.db import models as django_models
    from django_filters import filterset as df_filterset

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class CustomRelationFilter(django_filters.ModelMultipleChoiceFilter):
        pass

    class BookFilter(FilterSet):
        FILTER_DEFAULTS = {
            **df_filterset.BaseFilterSet.FILTER_DEFAULTS,
            django_models.ManyToManyField: {
                "filter_class": CustomRelationFilter,
                "extra": lambda f: {
                    "queryset": library_models.Genre._default_manager.all(),
                },
            },
        }

        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact"]}

    leaf = BookFilter.get_filters()["genres"]
    assert isinstance(leaf, CustomRelationFilter)
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "override_generated"
    assert record.generation_capable is False
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None
    assert "genres" not in snapshot.candidates


def test_blocker2_related_filter_expansion_preserves_child_relation_override():
    """An expanded ``<related>__<relation>`` leaf inherits the child's override.

    The child ``BookFilter`` overrides its own Relay-node M2M relation
    (``genres``) via ``Meta.filter_overrides``. When a parent expands it across
    ``book`` (Loan -> Book), the expanded ``book__genres`` leaf must keep the
    consumer's class and its ``override_generated`` origin, so it never becomes a
    correlated-EXISTS candidate.
    """
    import django_filters
    from django.db import models as django_models

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class CustomRelationFilter(django_filters.ModelMultipleChoiceFilter):
        pass

    class ChildBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact"]}
            filter_overrides = {
                django_models.ManyToManyField: {"filter_class": CustomRelationFilter},
            }

    class LoanParentFilter(FilterSet):
        book = RelatedFilter(ChildBookFilter, field_name="book")

        class Meta:
            model = library_models.Loan
            fields = {"note": ["exact"]}

    expanded = LoanParentFilter.get_filters()
    leaf = expanded["book__genres"]
    assert isinstance(leaf, CustomRelationFilter)
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "override_generated"
    snapshot = LoanParentFilter._expansion_snapshot()
    assert snapshot is not None
    assert "book__genres" not in snapshot.candidates


@pytest.mark.django_db
def test_blocker2_honored_override_runs_outer_with_no_reserved_alias():
    """End-to-end: the honored consumer M2M filter runs OUTER, not through EXISTS.

    ``Book.genres`` is a to-many hop, so a framework GlobalID replacement would be
    an eligible correlated-EXISTS candidate. With the consumer override honored,
    the leaf is ``override_generated``/ineligible: the request runs the consumer's
    ``ModelMultipleChoiceFilter`` on the OUTER queryset (a plain relation JOIN with
    the framework's fan-out ``distinct``), attaching NO reserved predicate alias
    and NO ``EXISTS``. The rows are the consumer filter's own membership result,
    proving its semantics ran rather than being smuggled into the adapter.
    """
    import django_filters
    from django.db import models as django_models

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class CustomRelationFilter(django_filters.ModelMultipleChoiceFilter):
        pass

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact"]}
            filter_overrides = {
                django_models.ManyToManyField: {
                    "filter_class": CustomRelationFilter,
                    "extra": lambda f: {
                        "queryset": library_models.Genre._default_manager.all(),
                    },
                },
            }

    BookFilter.get_filters()
    snapshot = BookFilter._expansion_snapshot()
    assert "genres" not in snapshot.candidates

    genre_a = library_models.Genre.objects.create(name="A")
    genre_b = library_models.Genre.objects.create(name="B")
    branch = library_models.Branch.objects.create(name="Central")
    shelf = library_models.Shelf.objects.create(code="S", branch=branch)
    book1 = library_models.Book.objects.create(title="book-1", shelf=shelf)
    book1.genres.add(genre_a)
    book2 = library_models.Book.objects.create(title="book-2", shelf=shelf)
    book2.genres.add(genre_b)
    book3 = library_models.Book.objects.create(title="book-3", shelf=shelf)
    book3.genres.add(genre_a, genre_b)

    # The consumer's ModelMultipleChoiceField cleans a raw pk list -- a shape the
    # discarded GlobalID primitive would have rejected -- proving the consumer
    # filter runs.
    result = BookFilter(
        data={"genres": [str(genre_a.pk)]},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    ).qs
    assert _reserved_aliases(result) == []
    assert "EXISTS" not in str(result.query).upper()
    assert set(result.values_list("title", flat=True)) == {"book-1", "book-3"}


def test_filter_for_field_picks_scalar_filter_for_non_relay_target():
    """A non-Relay `DjangoType` target returns whatever upstream produced (not GlobalIDFilter)."""

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("shelf")
    resolved = BookFilter.filter_for_field(field, "shelf")
    assert not isinstance(resolved, GlobalIDFilter)


def test_filter_for_field_returns_default_when_target_model_not_registered():
    """No registered `DjangoType` for the target -> upstream default unchanged."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("shelf")
    resolved = BookFilter.filter_for_field(field, "shelf")
    assert not isinstance(resolved, GlobalIDFilter)


@pytest.mark.parametrize(
    ("model_class", "field_name"),
    [
        (Category, "items__name"),
        (library_models.Book, "genres__name"),
        (library_models.Genre, "books__title"),
    ],
)
def test_filter_for_field_marks_generated_to_many_paths_distinct(model_class, field_name):
    class GeneratedFilter(FilterSet):
        class Meta:
            model = model_class
            fields = {field_name: ["icontains"]}

    filter_instance = GeneratedFilter.get_filters()[f"{field_name}__icontains"]

    assert filter_instance.distinct is True


def test_filter_for_field_keeps_generated_to_one_path_non_distinct():
    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"shelf__code": ["icontains"]}

    filter_instance = BookFilter.get_filters()["shelf__code__icontains"]

    assert filter_instance.distinct is False


# ---------------------------------------------------------------------------
# Row-preserving relational predicates: raw-ORM oracle + cut-over correctness.
#
# The first test is the PERMANENT raw-ORM oracle documenting the JOIN + global
# ``DISTINCT`` fan-out the row-preserving applicator avoids; the tests that
# follow assert the post-cut-over row-preserving behavior (correlated EXISTS,
# no framework-added ``DISTINCT``).
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_medtrics_ordered_sequence_baseline_freezes_fanout():
    """Document the raw-ORM fan-out the production adapter avoids.

    This case never routes through ``FilterSet``; it is the PERMANENT raw-ORM
    oracle. A disjunction of a direct predicate and a to-many self-join
    predicate fans out root ``Loan`` rows; ``.distinct()`` hides the duplicates
    in the visible sequence but does NOT remove the self-join fan-out from the
    query. The row-preserving adapter (asserted elsewhere) produces the same
    ordered rows WITHOUT the self-join fan-out or a framework-added ``DISTINCT``.
    """
    graph = _seed_medtrics_loan_graph()

    qs = library_models.Loan.objects.order_by("id").filter(
        Q(note__icontains="Cardio") | Q(book__loans__patron__email__icontains="Cardio"),
    )

    sequence = list(qs.values_list("pk", flat=True))
    assert sequence == [
        graph.relation_and_direct,
        graph.relation_and_direct,
        graph.relation_only,
        graph.relation_only,
        graph.direct_only,
    ]
    assert qs.count() == 5

    distinct_sequence = list(qs.distinct().values_list("pk", flat=True))
    assert distinct_sequence == [graph.relation_and_direct, graph.relation_only, graph.direct_only]

    # DISTINCT hides but does not remove the fan-out: the self-join still adds a
    # second ``library_loan`` alias (the T3 arm) and the ``library_patron`` table.
    loan_aliases = [
        alias for alias, join in qs.query.alias_map.items() if join.table_name == "library_loan"
    ]
    assert len(loan_aliases) >= 2
    table_names = {join.table_name for join in qs.query.alias_map.values()}
    assert "library_patron" in table_names


@pytest.mark.django_db
def test_generated_deep_to_many_path_correctness_is_row_preserving():
    """A generated deep to-many leaf is row-preserving via correlated EXISTS.

    A framework-generated deep lookup crossing a to-many
    relation no longer fans out through JOIN + global ``DISTINCT``. The applied
    queryset carries ``query.distinct is False``, its ``alias_map`` contains
    NEITHER the M2M through-table nor the terminal ``library_genre`` table, and
    an ``EXISTS`` owns the membership join -- yielding the SAME single correct
    row. The permanent test-local oracle (the old production behavior: invoke the
    same filter instance directly on the outer queryset, then its own
    ``distinct``) is asserted to yield the identical row set.
    """

    class BookGenreFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"]}

    generated = BookGenreFilter.get_filters()["genres__name__icontains"]
    assert generated.distinct is True

    branch = library_models.Branch.objects.create(name="Deep Branch")
    shelf = library_models.Shelf.objects.create(branch=branch, code="DEEP-1")
    matching_book = library_models.Book.objects.create(shelf=shelf, title="Matched")
    matching_book.genres.add(
        library_models.Genre.objects.create(name="cardiology"),
        library_models.Genre.objects.create(name="cardio-thoracic"),
    )
    other_book = library_models.Book.objects.create(shelf=shelf, title="Other")
    other_book.genres.add(library_models.Genre.objects.create(name="neurology"))

    outer_qs = library_models.Book.objects.order_by("id")
    bare = BookGenreFilter(
        data={"genres__name__icontains": "cardio"},
        queryset=outer_qs,
        request=HttpRequest(),
    )
    result = bare.qs

    # Row-preserving: no outer DISTINCT, no membership/terminal JOIN, one EXISTS.
    assert result.query.distinct is False
    joined_tables = {join.table_name for join in result.query.alias_map.values()}
    assert "library_book_genres" not in joined_tables
    assert "library_genre" not in joined_tables
    assert "EXISTS" in str(result.query).upper()
    production_rows = list(result.values_list("pk", flat=True))
    assert production_rows == [matching_book.pk]

    # Permanent test-local oracle: the OLD production behavior (direct outer
    # invocation of the same filter instance, then its own distinct) yields the
    # same rows the row-preserving production adapter now yields.
    oracle_rows = list(
        generated.filter(outer_qs, "cardio").distinct().values_list("pk", flat=True),
    )
    assert oracle_rows == production_rows


@pytest.mark.django_db
def test_flattened_related_filter_leaf_is_row_preserving():
    """Cut-over: a flattened ``RelatedFilter`` leaf no longer duplicates the parent row.

    Post-cut-over (C.3): although ``_expand_related_filter`` deep-copies a filter
    generated against the CHILD model then prefixes ``field_name`` (so the flat
    ``genres__name__icontains`` leaf on ``BookFilter`` is still a
    ``distinct=False`` leaf with ``field_name="genres__name"``), the applicator
    classifies the EXPANDED path against the root model and routes it through the
    row-preserving correlated ``EXISTS``. The single matching book is returned
    ONCE. The permanent test-local oracle (the old production behavior: direct
    outer invocation of the same ``distinct=False`` leaf) still DUPLICATES the
    row, proving the fix is in the adapter, not the leaf.
    """
    leaf = BookFilter.get_filters()["genres__name__icontains"]
    assert leaf.field_name == "genres__name"
    assert leaf.distinct is False

    branch = library_models.Branch.objects.create(name="Flat Branch")
    shelf = library_models.Shelf.objects.create(branch=branch, code="FLAT-1")
    matching_book = library_models.Book.objects.create(shelf=shelf, title="Matched")
    matching_book.genres.add(
        library_models.Genre.objects.create(name="cardiology"),
        library_models.Genre.objects.create(name="cardio-thoracic"),
    )
    other_book = library_models.Book.objects.create(shelf=shelf, title="Other")
    other_book.genres.add(library_models.Genre.objects.create(name="neurology"))

    outer_qs = library_models.Book.objects.order_by("id")
    bare = BookFilter(
        data={"genres__name__icontains": "cardio"},
        queryset=outer_qs,
        request=HttpRequest(),
    )
    result = bare.qs

    # Row-preserving production: the single matching book is returned ONCE.
    assert list(result.values_list("pk", flat=True)) == [matching_book.pk]
    assert result.count() == 1

    # Permanent test-local oracle: the OLD behavior (direct outer invocation of
    # the same distinct=False leaf) still duplicates the parent row.
    oracle_rows = list(leaf.filter(outer_qs, "cardio").values_list("pk", flat=True))
    assert oracle_rows == [matching_book.pk, matching_book.pk]


# ---------------------------------------------------------------------------
# C.3 / C.3a - flat-leaf applicator + distinct-suppression invocation helper
# ---------------------------------------------------------------------------


def _seed_two_matching_genres_on_one_book():
    """One book with two genres both matching "cardio", plus a non-matching book."""
    branch = library_models.Branch.objects.create(name="Adapter Branch")
    shelf = library_models.Shelf.objects.create(branch=branch, code="ADP-1")
    matching_book = library_models.Book.objects.create(shelf=shelf, title="Matched")
    matching_book.genres.add(
        library_models.Genre.objects.create(name="cardiology"),
        library_models.Genre.objects.create(name="cardio-thoracic"),
    )
    other_book = library_models.Book.objects.create(shelf=shelf, title="Other")
    other_book.genres.add(library_models.Genre.objects.create(name="neurology"))
    return matching_book, other_book


@pytest.mark.django_db
def test_eligible_m2m_candidate_has_no_outer_or_inner_distinct():
    """An eligible M2M candidate composes with no outer DISTINCT and no inner SELECT DISTINCT."""

    class BookGenreFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"]}

    matching_book, _other = _seed_two_matching_genres_on_one_book()
    # Publish the expansion snapshot (production does this via ``apply_*`` ->
    # ``get_filters``); a bare-``.qs`` filterset built before it degrades wholesale.
    BookGenreFilter.get_filters()
    bare = BookGenreFilter(
        data={"genres__name__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    )
    result = bare.qs
    sql = str(result.query)

    assert result.query.distinct is False
    # No DISTINCT anywhere: not on the outer query, not inside the EXISTS body.
    assert "DISTINCT" not in sql.upper()
    assert "EXISTS" in sql.upper()
    assert list(result.values_list("pk", flat=True)) == [matching_book.pk]


@pytest.mark.django_db
def test_invoke_suppressing_helper_restores_distinct_after_success():
    """The helper restores the per-instance ``distinct`` flag after a successful apply."""

    class BookGenreFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"]}

    bare = BookGenreFilter(
        data={"genres__name__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    )
    filter_instance = bare.filters["genres__name__icontains"]
    assert filter_instance.distinct is True

    inner_root = correlated_inner_root(library_models.Book.objects.all())
    result = FilterSet._invoke_suppressing_framework_distinct(
        filter_instance,
        inner_root,
        "cardio",
    )
    assert result.model is library_models.Book
    # Restored to the original live value after a successful invocation.
    assert filter_instance.distinct is True


@pytest.mark.django_db
def test_invoke_suppressing_helper_restores_distinct_after_exception():
    """The helper restores ``distinct`` even when the wrapped invocation raises."""

    class BookGenreFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"]}

    bare = BookGenreFilter(
        data={"genres__name__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    )
    filter_instance = bare.filters["genres__name__icontains"]
    assert filter_instance.distinct is True

    boom = RuntimeError("decode failure mid-invocation")

    def _raising_filter(qs, value):
        # The flag is suppressed at this point; prove it, then blow up.
        assert filter_instance.distinct is False
        raise boom

    filter_instance.filter = _raising_filter
    inner_root = correlated_inner_root(library_models.Book.objects.all())
    with pytest.raises(RuntimeError, match="decode failure"):
        FilterSet._invoke_suppressing_framework_distinct(filter_instance, inner_root, "cardio")
    # Restored to the original live value despite the exception.
    assert filter_instance.distinct is True


@pytest.mark.django_db
def test_inactive_candidates_attach_nothing():
    """With many to-many candidates but ONE active, exactly one EXISTS + one reserved alias."""

    class MultiBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"], "loans__note": ["icontains"]}

    matching_book, _other = _seed_two_matching_genres_on_one_book()
    MultiBookFilter.get_filters()
    bare = MultiBookFilter(
        data={"genres__name__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    )
    result = bare.qs
    sql = str(result.query)

    # Only the active candidate attaches: exactly one EXISTS body and exactly one
    # reserved ``_dst_predicate_`` alias (the alias lives in ``query.annotations``,
    # inlined into the compiled EXISTS SQL).
    assert sql.upper().count("EXISTS") == 1
    reserved = [name for name in result.query.annotations if name.startswith("_dst_predicate_")]
    assert reserved == ["_dst_predicate_0"]
    assert list(result.values_list("pk", flat=True)) == [matching_book.pk]


@pytest.mark.django_db
def test_many_inactive_candidates_match_empty_filter_sql(monkeypatch):
    """N inactive-but-eligible to-many leaves build inner roots yet attach empty-filter SQL.

    Pins the cost-boundary contract documented on ``FilterSet._apply_flat_leaves``:
    a routed no-op builds ``correlated_inner_root`` but attaches NO SQL. Sixteen
    eligible to-many leaves are all routed (sixteen inner-root constructions) yet
    none is active, so the compiled statement must be byte-identical to a
    filterset with no leaves at all -- no ``_dst_predicate_`` reserved alias, no
    ``EXISTS`` -- so the "no SQL attachment" guarantee cannot silently regress
    into a stray tautological ``EXISTS`` per inactive leaf.
    """
    lookups = [
        "icontains",
        "exact",
        "iexact",
        "startswith",
    ]

    class ManyInactiveBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {
                "genres__name": lookups,
                "loans__note": lookups,
                "loans__patron__email": lookups,
                "loans__patron__name": lookups,
            }

    class NoLeafBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields: dict[str, list[str]] = {}

    ManyInactiveBookFilter.get_filters()
    NoLeafBookFilter.get_filters()

    # Count inner-root constructions to prove these leaves genuinely route
    # through the correlated path (not the outer fall-through, which would also
    # attach nothing and mask the routed no-op the boundary is about).
    from django_strawberry_framework.filters import sets as sets_module

    real_inner_root = sets_module.correlated_inner_root
    builds = {"n": 0}

    def _counting_inner_root(queryset):
        builds["n"] += 1
        return real_inner_root(queryset)

    monkeypatch.setattr(sets_module, "correlated_inner_root", _counting_inner_root)

    base = library_models.Book.objects.order_by("id")
    # Every leaf is eligible (to-many path) yet inactive (empty data).
    inactive = ManyInactiveBookFilter(data={}, queryset=base, request=HttpRequest())
    empty = NoLeafBookFilter(data={}, queryset=base, request=HttpRequest())

    inactive_qs = inactive.qs

    # All sixteen eligible leaves are present in cleaned_data ...
    assert len(inactive.form.cleaned_data) == 16
    # ... routed and built an inner root (the documented per-leaf construction
    # cost) ...
    assert builds["n"] == 16
    # ... yet nothing attached: no reserved alias, no EXISTS, empty-filter SQL.
    reserved = [n for n in inactive_qs.query.annotations if n.startswith("_dst_predicate_")]
    assert reserved == []
    assert str(inactive_qs.query).upper().count("EXISTS") == 0
    assert str(inactive_qs.query) == str(empty.qs.query)


@pytest.mark.django_db
def test_restrictive_empty_in_composes_as_exists_over_none():
    """A restrictive membership on a to-many path matches no rows via ``Exists(none)``.

    ``IntegerInFilter`` treats an explicit ``in: []`` as a no-op skip; the
    RESTRICTIVE-empty shape (a non-empty membership whose every value is out of
    range and drops) routes through ``_match_none_queryset`` -> ``inner_root.none()``,
    which the adapter attaches as ``Exists(none)``. Django folds that to a constant
    ``False`` (so the EXISTS text is optimized away), but the reserved alias is
    still attached and the composed result matches nothing.
    """
    # Seed a book that WOULD match a non-empty membership, to prove the input is
    # restrictive (matches nothing), not a widened no-op (matches everything).
    _seed_two_matching_genres_on_one_book()

    class BookGenreInFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__id": ["in"]}

    BookGenreInFilter.get_filters()
    bare = BookGenreInFilter(
        # A member past SQLite's signed-64-bit range drops, leaving an empty but
        # RESTRICTIVE membership (``_match_none_queryset``), unlike an explicit [].
        data={"genres__id__in": [99999999999999999999999]},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    )
    result = bare.qs

    reserved = [name for name in result.query.annotations if name.startswith("_dst_predicate_")]
    assert reserved == ["_dst_predicate_0"]
    assert list(result.values_list("pk", flat=True)) == []


@pytest.mark.django_db
def test_pre_snapshot_filterset_degrades_to_old_behavior(monkeypatch):
    """A filterset with no expansion snapshot behaves byte-for-byte like the old path."""
    matching_book, _other = _seed_two_matching_genres_on_one_book()

    # Expand ``base_filters`` (so the flat leaf is a real form field) THEN force
    # the fail-closed pre-snapshot state (a filterset built before lazy target
    # resolution): every name becomes a non-candidate and the flattened
    # distinct=False leaf duplicates the parent row exactly as it did before.
    BookFilter.get_filters()
    monkeypatch.setattr(BookFilter, "_expansion_snapshot", classmethod(lambda cls: None))
    bare = BookFilter(
        data={"genres__name__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    )
    result = bare.qs

    assert list(result.values_list("pk", flat=True)) == [matching_book.pk, matching_book.pk]
    assert result.count() == 2


@pytest.mark.django_db
def test_not_branch_over_to_many_related_branch_is_row_preserving():
    """A ``not`` tree position over a to-many related branch keeps ``_q_for_branch`` intact.

    Branch negation composes through the outer ``Q(pk__in=...)`` (``_q_for_branch``),
    never pushed inside a child queryset. A genre-name ``not`` branch over the
    reverse-M2M ``books`` relation returns exactly the genres NOT matching, each
    once (row-preserving), which the cut-over must not disturb.
    """
    branch = library_models.Branch.objects.create(name="Not Branch")
    shelf = library_models.Shelf.objects.create(branch=branch, code="NOT-1")
    cardio = library_models.Genre.objects.create(name="cardiology")
    neuro = library_models.Genre.objects.create(name="neurology")
    book_one = library_models.Book.objects.create(shelf=shelf, title="Cardio Atlas One")
    book_two = library_models.Book.objects.create(shelf=shelf, title="Cardio Atlas Two")
    book_one.genres.add(cardio)
    book_two.genres.add(cardio)
    neuro_book = library_models.Book.objects.create(shelf=shelf, title="Neuro Atlas")
    neuro_book.genres.add(neuro)

    from apps.library.filters_genre import GenreFilter

    qs = GenreFilter.apply_sync(
        {"not_": {"books__title": {"i_contains": "cardio"}}},
        library_models.Genre.objects.order_by("id"),
        _make_info(),
    )
    # Only the non-cardio genre survives, exactly once.
    assert list(qs.values_list("pk", flat=True)) == [neuro.pk]


@pytest.mark.django_db
def test_eligible_leaf_in_and_tree_position_is_row_preserving():
    """An ELIGIBLE to-many leaf inside an ``and`` branch stays row-preserving.

    ``GenreFilter`` root; the eligible reverse-M2M ``books__title`` leaf is one
    ``and_`` arm, a scalar ``name`` leaf the other. A genre linked to TWO matching
    books AND carrying the matching name is returned exactly once (no framework
    duplicate); a genre matching only one arm is excluded. The eligible arm routes
    through the correlated ``EXISTS`` applicator inside ``_q_for_branch``.
    """
    from apps.library.filters_genre import GenreFilter

    branch = library_models.Branch.objects.create(name="And Branch")
    shelf = library_models.Shelf.objects.create(branch=branch, code="AND-1")
    both = library_models.Genre.objects.create(name="cardiology")
    book_one = library_models.Book.objects.create(shelf=shelf, title="Cardio One")
    book_two = library_models.Book.objects.create(shelf=shelf, title="Cardio Two")
    book_one.genres.add(both)
    book_two.genres.add(both)
    # Name matches ("cardi") but has no cardio-titled book -> fails the AND.
    library_models.Genre.objects.create(name="cardiovascular")
    # Has a cardio-titled book but its name misses "cardi" -> fails the AND.
    books_only = library_models.Genre.objects.create(name="neurology")
    neuro_book = library_models.Book.objects.create(shelf=shelf, title="Cardio Three")
    neuro_book.genres.add(books_only)

    qs = GenreFilter.apply_sync(
        {
            "and_": [
                {"books__title": {"i_contains": "cardio"}},
                {"name": {"i_contains": "cardi"}},
            ],
        },
        library_models.Genre.objects.order_by("id"),
        _make_info(),
    )
    # Only the genre satisfying BOTH arms, returned exactly once despite two books.
    assert list(qs.values_list("pk", flat=True)) == [both.pk]
    assert qs.count() == 1
    assert "EXISTS" in str(qs.query).upper()


@pytest.mark.django_db
def test_eligible_leaf_in_or_tree_position_is_row_preserving():
    """An ELIGIBLE to-many leaf inside an ``or`` branch stays row-preserving.

    ``GenreFilter`` root; the eligible reverse-M2M ``books__title`` leaf is one
    ``or_`` arm, a scalar ``name`` leaf the other. A genre matching only via TWO
    books (eligible arm) is returned exactly once, unioned with a genre matching
    only the scalar arm; a genre matching neither is excluded. The eligible arm
    routes through the correlated ``EXISTS`` applicator inside ``_q_for_branch``.
    """
    from apps.library.filters_genre import GenreFilter

    branch = library_models.Branch.objects.create(name="Or Branch")
    shelf = library_models.Shelf.objects.create(branch=branch, code="OR-1")
    matched = library_models.Genre.objects.create(name="cardiology")
    book_one = library_models.Book.objects.create(shelf=shelf, title="Cardio One")
    book_two = library_models.Book.objects.create(shelf=shelf, title="Cardio Two")
    book_one.genres.add(matched)
    book_two.genres.add(matched)
    # Matches only the scalar ``name`` arm ("special"); no books at all.
    named_only = library_models.Genre.objects.create(name="special")
    # Matches neither arm: a non-cardio book and a name without "special".
    miss = library_models.Genre.objects.create(name="plain")
    neuro_book = library_models.Book.objects.create(shelf=shelf, title="Neuro Atlas")
    neuro_book.genres.add(miss)

    qs = GenreFilter.apply_sync(
        {
            "or_": [
                {"books__title": {"i_contains": "cardio"}},
                {"name": {"i_contains": "special"}},
            ],
        },
        library_models.Genre.objects.order_by("id"),
        _make_info(),
    )
    # Eligible-arm match (once, despite two books) unioned with the scalar match.
    assert list(qs.values_list("pk", flat=True)) == [matched.pk, named_only.pk]
    assert qs.count() == 2
    assert "EXISTS" in str(qs.query).upper()


@pytest.mark.django_db
def test_qs_and_apply_sync_and_async_over_eligible_candidate():
    """``.qs``, ``apply_sync``, and ``apply_async`` all filter an eligible candidate correctly.

    Uses the fakeshop ``GenreFilter`` flat reverse-M2M leaf ``books__title`` (an
    eligible framework-generated to-many candidate) so the input spelling matches
    the real generated surface.
    """
    import asyncio

    from apps.library.filters_genre import GenreFilter

    branch = library_models.Branch.objects.create(name="Apply Branch")
    shelf = library_models.Shelf.objects.create(branch=branch, code="APL-1")
    cardio = library_models.Genre.objects.create(name="cardiology")
    neuro = library_models.Genre.objects.create(name="neurology")
    book_one = library_models.Book.objects.create(shelf=shelf, title="Cardio One")
    book_two = library_models.Book.objects.create(shelf=shelf, title="Cardio Two")
    book_one.genres.add(cardio)
    book_two.genres.add(cardio)
    neuro_book = library_models.Book.objects.create(shelf=shelf, title="Neuro")
    neuro_book.genres.add(neuro)

    # `.qs` path (snapshot published via get_filters, as apply_* does).
    GenreFilter.get_filters()
    bare = GenreFilter(
        data={"books__title__icontains": "cardio"},
        queryset=library_models.Genre.objects.order_by("id"),
        request=HttpRequest(),
    )
    assert list(bare.qs.values_list("pk", flat=True)) == [cardio.pk]

    # apply_sync path.
    sync_qs = GenreFilter.apply_sync(
        {"books__title": {"i_contains": "cardio"}},
        library_models.Genre.objects.order_by("id"),
        _make_info(),
    )
    assert list(sync_qs.values_list("pk", flat=True)) == [cardio.pk]

    # apply_async path.
    async_qs = asyncio.run(
        GenreFilter.apply_async(
            {"books__title": {"i_contains": "cardio"}},
            library_models.Genre.objects.order_by("id"),
            _make_info(),
        ),
    )
    assert list(async_qs.values_list("pk", flat=True)) == [cardio.pk]


# Row-preserving relational-predicate cut-over cases:
# ``test_medtrics_ordered_sequence_baseline_freezes_fanout`` stays as the
# permanent raw-ORM fan-out oracle,
# ``test_generated_deep_to_many_path_correctness_is_row_preserving`` and
# ``test_flattened_related_filter_leaf_is_row_preserving`` now assert the
# row-preserving production behavior against the permanent test-local oracle.
#
# ---------------------------------------------------------------------------
# C.4 - baseline-vs-rewritten equivalence matrix
#
# For every supported candidate shape, the production ``FilterSet`` path
# (correlated ``EXISTS``) must return the SAME ordered primary-key sequence and
# count as the permanent test-local oracle: the same filter instance invoked
# DIRECTLY on the outer queryset (django-filter's plain pre-rewrite behavior).
# ``distinct=True`` baseline leaves are NOT double-``.distinct()``-ed here -
# upstream ``Filter.filter`` already calls ``qs.distinct()`` when
# ``self.distinct`` is set, so the direct invocation IS the old behavior; a
# ``.distinct()`` chained after it only mirrors the framework's own suppressed
# outer distinct and is applied only where noted (many-side membership leaves).
#
# Cases already proven by the landed C.1-flipped tests
# (``test_generated_deep_to_many_path_correctness_is_row_preserving``,
# ``test_flattened_related_filter_leaf_is_row_preserving``) and the C.3 adapter
# tests are NOT re-added: forward M2M single-parent equivalence, the
# expanded-vs-root classification EXECUTION equivalence (matrix row 13, covered
# by ``test_flattened_related_filter_leaf_is_row_preserving`` which compares the
# expanded ``BookFilter`` ``genres__name`` leaf against its direct-invocation
# oracle), inactive-candidate no-op (row: one active among many), and
# restrictive-empty membership.
#
# Matrix row 7 (``to_field`` FK-to-non-pk hop) is proven by
# ``test_c4_to_field_reverse_to_many_children_is_row_preserving`` below, over the
# ``tests/_relation_fixtures.py`` ``RpToFieldTarget`` reverse to-many
# (``children__name``, whose join binds on the non-pk ``code`` column).
#
# Package-tier notes:
# - matrix row 11 GlobalID-list sub-case: a framework-generated FLAT Relay M2M
#   leaf (``Meta.fields = {"genres": [...]}`` with a Relay-Node target) IS
#   generated as a ``GlobalIDMultipleChoiceFilter``; its form field is
#   constructible because the replacement strips the model-choice-only extras
#   (``_strip_model_choice_extras``), and the decode/apply round-trip is covered
#   by ``test_c4_global_id_list_over_flat_relay_m2m_is_row_preserving`` below.
#   The flat leaf stays package-tier: the fakeshop filtersets declare
#   ``RelatedFilter``s under the same base names, and a declared name shadows
#   the flat leaf in the generated GraphQL input, so no live surface reaches it.
#   The integer-``in`` sub-cases (empty / mixed / all-invalid) ARE covered below.
# ---------------------------------------------------------------------------


def _library_shelf():
    """Create a throwaway ``Branch`` + ``Shelf`` for library-model C.4 fixtures."""
    branch = library_models.Branch.objects.create(name="C4 Branch")
    return library_models.Shelf.objects.create(branch=branch, code="C4-1")


def _make_scalar_specimen(label, parent=None):
    """Create a ``ScalarSpecimen`` with all required non-null scalar fields set."""
    return scalar_models.ScalarSpecimen.objects.create(
        label=label,
        occurred_on=datetime.date(2020, 1, 1),
        occurred_at=datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc),
        occurred_time=datetime.time(1, 2, 3),
        external_id=uuid.uuid4(),
        parent=parent,
    )


@pytest.mark.django_db
def test_c4_reverse_fk_loans_note_is_row_preserving():
    """Matrix row 1 (reverse FK) + row 14 (ordinary generated ``CharFilter``).

    ``Book`` root, generated ``loans__note`` ``icontains`` leaf (a plain upstream
    ``CharFilter`` crossing the reverse-FK ``Book.loans`` to-many hop). A parent
    with two matching loans yields ONE row via correlated ``EXISTS``; equivalence
    against the direct-invocation oracle holds.
    """
    shelf = _library_shelf()
    book = library_models.Book.objects.create(shelf=shelf, title="Matched")
    patron_a = library_models.Patron.objects.create(name="pa", email="a")
    patron_b = library_models.Patron.objects.create(name="pb", email="b")
    library_models.Loan.objects.create(book=book, patron=patron_a, note="Cardio one")
    library_models.Loan.objects.create(book=book, patron=patron_b, note="Cardio two")
    other = library_models.Book.objects.create(shelf=shelf, title="Other")
    library_models.Loan.objects.create(
        book=other,
        patron=library_models.Patron.objects.create(name="pc", email="c"),
        note="routine",
    )

    class BookLoanFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

    leaf = BookLoanFilter.get_filters()["loans__note__icontains"]
    assert isinstance(leaf, CharFilter)
    assert leaf.distinct is True
    outer = library_models.Book.objects.order_by("id")
    result = BookLoanFilter(
        data={"loans__note__icontains": "cardio"},
        queryset=outer,
        request=HttpRequest(),
    ).qs

    production = list(result.order_by("id").values_list("pk", flat=True))
    assert production == [book.pk]
    assert result.count() == 1
    assert "EXISTS" in str(result.query).upper()
    oracle = list(leaf.filter(outer, "cardio").order_by("id").values_list("pk", flat=True))
    assert oracle == production


@pytest.mark.django_db
def test_c4_forward_m2m_multiple_parents_is_row_preserving():
    """Matrix row 2 (forward M2M) gap: MULTIPLE parents, one direct, one via dups.

    ``Book`` root over the forward M2M ``Book.genres``. One book matches through a
    single genre; another matches through two duplicate-matching genres. Both are
    returned exactly once (ordered), equal to the direct-invocation oracle.
    """
    shelf = _library_shelf()
    single = library_models.Book.objects.create(shelf=shelf, title="Single")
    single.genres.add(library_models.Genre.objects.create(name="cardiology"))
    dupes = library_models.Book.objects.create(shelf=shelf, title="Dupes")
    dupes.genres.add(
        library_models.Genre.objects.create(name="cardio-thoracic"),
        library_models.Genre.objects.create(name="cardio-vascular"),
    )
    miss = library_models.Book.objects.create(shelf=shelf, title="Miss")
    miss.genres.add(library_models.Genre.objects.create(name="neurology"))

    class BookGenreFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"]}

    leaf = BookGenreFilter.get_filters()["genres__name__icontains"]
    outer = library_models.Book.objects.order_by("id")
    result = BookGenreFilter(
        data={"genres__name__icontains": "cardio"},
        queryset=outer,
        request=HttpRequest(),
    ).qs

    production = list(result.order_by("id").values_list("pk", flat=True))
    assert production == [single.pk, dupes.pk]
    assert result.count() == 2
    oracle = list(leaf.filter(outer, "cardio").order_by("id").values_list("pk", flat=True))
    assert oracle == production


@pytest.mark.django_db
def test_c4_reverse_m2m_genre_books_title_is_row_preserving():
    """Matrix row 3 (reverse M2M): ``Genre`` root over ``books__title``.

    A genre linked to two matching books is returned once; ordered equivalence
    against the direct-invocation oracle.
    """
    shelf = _library_shelf()
    matched = library_models.Genre.objects.create(name="matched")
    book_one = library_models.Book.objects.create(shelf=shelf, title="Cardio Atlas One")
    book_two = library_models.Book.objects.create(shelf=shelf, title="Cardio Atlas Two")
    book_one.genres.add(matched)
    book_two.genres.add(matched)
    other = library_models.Genre.objects.create(name="other")
    neuro = library_models.Book.objects.create(shelf=shelf, title="Neuro Atlas")
    neuro.genres.add(other)

    class GenreBooksFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"books__title": ["icontains"]}

    leaf = GenreBooksFilter.get_filters()["books__title__icontains"]
    outer = library_models.Genre.objects.order_by("id")
    result = GenreBooksFilter(
        data={"books__title__icontains": "cardio"},
        queryset=outer,
        request=HttpRequest(),
    ).qs

    production = list(result.order_by("id").values_list("pk", flat=True))
    assert production == [matched.pk]
    assert result.count() == 1
    oracle = list(leaf.filter(outer, "cardio").order_by("id").values_list("pk", flat=True))
    assert oracle == production


@pytest.mark.django_db
def test_c4_generic_relation_branch_tags_is_row_preserving():
    """Matrix row 4 (``GenericRelation``): ``Branch`` root over ``tags__tag``.

    ``Meta.fields = {"tags__tag": ["icontains"]}`` DOES generate through
    django-filter's ``get_model_field`` (a plain ``CharFilter``, ``distinct=True``
    because the ``GenericRelation`` is a to-many hop). Two matching tags on one
    branch yield one row; equivalence against the direct-invocation oracle.
    """
    from django.contrib.contenttypes.models import ContentType

    branch = library_models.Branch.objects.create(name="Tagged Branch")
    ct = ContentType.objects.get_for_model(library_models.Branch)
    library_models.TaggedItem.objects.create(tag="cardio-x", content_type=ct, object_id=branch.pk)
    library_models.TaggedItem.objects.create(tag="cardio-y", content_type=ct, object_id=branch.pk)
    other = library_models.Branch.objects.create(name="Other Branch")
    library_models.TaggedItem.objects.create(tag="neuro-z", content_type=ct, object_id=other.pk)

    class BranchTagFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"tags__tag": ["icontains"]}

    leaf = BranchTagFilter.get_filters()["tags__tag__icontains"]
    assert isinstance(leaf, CharFilter)
    assert leaf.distinct is True
    outer = library_models.Branch.objects.order_by("id")
    result = BranchTagFilter(
        data={"tags__tag__icontains": "cardio"},
        queryset=outer,
        request=HttpRequest(),
    ).qs

    production = list(result.order_by("id").values_list("pk", flat=True))
    assert production == [branch.pk]
    assert result.count() == 1
    oracle = list(leaf.filter(outer, "cardio").order_by("id").values_list("pk", flat=True))
    assert oracle == production


@pytest.mark.django_db
def test_c4_isnull_on_nullable_child_field_is_row_preserving():
    """Matrix row 5 (``isnull`` on a nullable child field over a to-many hop).

    ``Genre`` root over ``books__subtitle`` (``subtitle`` is nullable). Both
    ``isnull=True`` and ``isnull=False`` match the production result to the
    direct-invocation oracle. A genre with ZERO books is INCLUDED by
    ``isnull=True`` (LEFT-join null) and EXCLUDED by ``isnull=False`` - and the
    correlated ``EXISTS`` reproduces that outer-join semantics identically.
    """
    shelf = _library_shelf()
    g_has = library_models.Genre.objects.create(name="has-subtitle")
    g_null = library_models.Genre.objects.create(name="null-subtitle")
    g_empty = library_models.Genre.objects.create(name="no-books")
    book_sub = library_models.Book.objects.create(shelf=shelf, title="Has", subtitle="Sub")
    book_nosub = library_models.Book.objects.create(shelf=shelf, title="Null", subtitle=None)
    book_sub.genres.add(g_has)
    book_nosub.genres.add(g_null)

    class GenreSubtitleFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"books__subtitle": ["isnull"]}

    leaf = GenreSubtitleFilter.get_filters()["books__subtitle__isnull"]
    outer = library_models.Genre.objects.order_by("id")
    for value, expected in ((True, [g_null.pk, g_empty.pk]), (False, [g_has.pk])):
        result = GenreSubtitleFilter(
            data={"books__subtitle__isnull": value},
            queryset=outer,
            request=HttpRequest(),
        ).qs
        production = list(result.order_by("id").values_list("pk", flat=True))
        assert production == expected
        oracle = list(
            leaf.filter(outer, value).order_by("id").values_list("pk", flat=True),
        )
        assert oracle == production


@pytest.mark.django_db
def test_c4_nullable_intermediate_to_one_hop_is_row_preserving():
    """Matrix row 6 (nullable intermediate to-one hop in the multiplying chain).

    ``ScalarSpecimen`` root over ``parent__children__label`` - a nullable self-FK
    (``parent``) followed by the reverse-FK to-many hop (``children``). The
    baseline OR would LEFT-OUTER-promote the null hop; the ``EXISTS`` arm is
    simply false for a null ``parent``. The equivalence is TESTED, not assumed:
    the null-parent root is excluded in both production and the oracle.
    """
    parent = _make_scalar_specimen("parent")
    child_match = _make_scalar_specimen("cardiology child", parent=parent)
    sibling = _make_scalar_specimen("root-with-parent", parent=parent)
    root_null = _make_scalar_specimen("cardiology but null parent", parent=None)

    class SpecimenFilter(FilterSet):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {"parent__children__label": ["icontains"]}

    leaf = SpecimenFilter.get_filters()["parent__children__label__icontains"]
    outer = scalar_models.ScalarSpecimen.objects.order_by("id")
    result = SpecimenFilter(
        data={"parent__children__label__icontains": "cardio"},
        queryset=outer,
        request=HttpRequest(),
    ).qs

    production = list(result.order_by("id").values_list("pk", flat=True))
    # child_match and sibling share ``parent`` (whose children include the
    # matching label); root_null has a NULL parent so the EXISTS arm is false.
    assert production == [child_match.pk, sibling.pk]
    assert root_null.pk not in production
    assert "EXISTS" in str(result.query).upper()
    oracle = list(leaf.filter(outer, "cardio").order_by("id").values_list("pk", flat=True))
    assert oracle == production


@pytest.mark.django_db(transaction=True)
def test_c4_to_field_reverse_to_many_children_is_row_preserving():
    """Matrix row 7 (``to_field`` FK-to-non-pk hop), now executable.

    ``RpToFieldTarget`` root over its reverse to-many ``children__name`` -- the
    hop whose join binds on the non-pk ``code`` column (``RpToFieldChild.target``
    is ``FK(to_field="code")``). The production ``FilterSet`` applicator
    (correlated ``EXISTS``) returns each matching target exactly once, equal to
    the deduped direct-JOIN baseline oracle, with ONE correlated ``EXISTS``, no
    framework ``DISTINCT``, correlating on the parent pk while the inner join
    binds children on ``code``.
    """
    from django.db import connection

    with relation_fixture_tables(connection):
        matched = RpToFieldTarget.objects.create(code="T1", label="matched")
        RpToFieldChild.objects.create(target=matched, name="cardio one")
        RpToFieldChild.objects.create(target=matched, name="cardio two")
        other = RpToFieldTarget.objects.create(code="T2", label="other")
        RpToFieldChild.objects.create(target=other, name="neuro")

        class TargetChildrenFilter(FilterSet):
            class Meta:
                model = RpToFieldTarget
                fields = {"children__name": ["icontains"]}

        leaf = TargetChildrenFilter.get_filters()["children__name__icontains"]
        assert leaf.distinct is True
        outer = RpToFieldTarget.objects.order_by("id")
        result = TargetChildrenFilter(
            data={"children__name__icontains": "cardio"},
            queryset=outer,
            request=HttpRequest(),
        ).qs

        production = list(result.order_by("id").values_list("pk", flat=True))
        # Test-local baseline oracle: the raw JOIN fans the parent out once per
        # matching child; dedup to the expected parent set.
        baseline = list(
            RpToFieldTarget.objects.filter(children__name__icontains="cardio")
            .order_by("id")
            .values_list("pk", flat=True),
        )
        assert baseline == [matched.pk, matched.pk]
        expected = sorted(set(baseline))
        assert production == expected == [matched.pk]
        assert result.count() == 1

        sql = str(result.query)
        assert sql.upper().count("EXISTS") == 1
        assert "DISTINCT" not in sql.upper()
        # Correlated on the parent pk (the outer target's auto pk column).
        assert '"products_rptofieldtarget"."id"' in sql
        # The inner join binds children on the non-pk ``code`` to_field column.
        assert '"code" = ' in sql
        assert "target_id" in sql


@pytest.mark.django_db
def test_c4_two_active_leaves_same_relation_cross_row_and():
    """Matrix row 8 (two active leaves on one relation, cross-row AND).

    ``Book`` root with TWO active leaves on the M2M ``genres`` relation matching
    DIFFERENT genre rows of the same book (name ``icontains`` matches one genre,
    ``id__gt`` matches the other). The book qualifies because each ``EXISTS`` is
    independently true; TWO reserved aliases / ``EXISTS`` bodies appear in the
    SQL. The old baseline (two separate ``.filter`` invocations, each its own
    join alias) ALSO matches cross-row, so equivalence holds.
    """
    shelf = _library_shelf()
    book = library_models.Book.objects.create(shelf=shelf, title="CrossRow")
    cardio = library_models.Genre.objects.create(name="cardiology")
    neuro = library_models.Genre.objects.create(name="neurology")
    book.genres.add(cardio, neuro)
    lonely = library_models.Book.objects.create(shelf=shelf, title="Lonely")
    lonely.genres.add(cardio)

    class TwoLeafFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"], "genres__id": ["gt"]}

    TwoLeafFilter.get_filters()
    outer = library_models.Book.objects.order_by("id")
    result = TwoLeafFilter(
        data={"genres__name__icontains": "cardio", "genres__id__gt": neuro.pk - 1},
        queryset=outer,
        request=HttpRequest(),
    ).qs
    sql = str(result.query)

    assert sql.upper().count("EXISTS") == 2
    reserved = [n for n in result.query.annotations if n.startswith("_dst_predicate_")]
    assert reserved == ["_dst_predicate_0", "_dst_predicate_1"]
    production = list(result.order_by("id").values_list("pk", flat=True))
    # ``book`` has cardiology (name match) AND neurology (id__gt match, cross-row);
    # ``lonely`` has only cardiology (fails id__gt) so it is excluded.
    assert production == [book.pk]

    name_leaf = TwoLeafFilter.get_filters()["genres__name__icontains"]
    id_leaf = TwoLeafFilter.get_filters()["genres__id__gt"]
    oracle_qs = name_leaf.filter(outer, "cardio")
    oracle_qs = id_leaf.filter(oracle_qs, neuro.pk - 1)
    oracle = list(oracle_qs.order_by("id").values_list("pk", flat=True))
    assert oracle == production


@pytest.mark.django_db
def test_c4_range_binds_to_single_child_row():
    """Matrix row 9 (positive multi-lookup single-invocation binding).

    A ``range`` leaf on ``Book.loans__id``: both bounds must bind to ONE child row
    inside a single invocation. A book whose loans SPLIT the range (one below, one
    above, none inside) is EXCLUDED; a book with a loan inside the range is
    included. Equivalence against the direct-invocation oracle holds.
    """
    shelf = _library_shelf()
    split = library_models.Book.objects.create(shelf=shelf, title="Split")
    p1 = library_models.Patron.objects.create(name="p1", email="a")
    p2 = library_models.Patron.objects.create(name="p2", email="b")
    low = library_models.Loan.objects.create(book=split, patron=p1, note="low")
    match_book = library_models.Book.objects.create(shelf=shelf, title="Match")
    p3 = library_models.Patron.objects.create(name="p3", email="c")
    mid = library_models.Loan.objects.create(book=match_book, patron=p3, note="mid")
    high = library_models.Loan.objects.create(book=split, patron=p2, note="high")
    # id order: low < mid < high. Range == [mid, mid]: match_book's loan is in
    # range; split's loans (low, high) straddle it with none inside.
    assert low.pk < mid.pk < high.pk

    class BookLoanRangeFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__id": ["range"]}

    leaf = BookLoanRangeFilter.get_filters()["loans__id__range"]
    outer = library_models.Book.objects.order_by("id")
    result = BookLoanRangeFilter(
        data={"loans__id__range": [mid.pk, mid.pk]},
        queryset=outer,
        request=HttpRequest(),
    ).qs

    production = list(result.order_by("id").values_list("pk", flat=True))
    assert production == [match_book.pk]
    assert split.pk not in production
    cleaned = leaf.field.clean([mid.pk, mid.pk])
    oracle = list(leaf.filter(outer, cleaned).order_by("id").values_list("pk", flat=True))
    assert oracle == production


@pytest.mark.django_db
def test_c4_negated_split_across_rows_range_counterexample():
    """Matrix row 10 (negated split-across-rows range counterexample).

    The framework's generated FLAT leaves never carry ``exclude=True`` (proven
    executably by ``test_generated_flat_leaves_never_carry_exclude`` below);
    negation is a logic-tree ``not_`` concern handled by ``_q_for_branch``
    (untouched machinery), so the flat-leaf adapter never sees a negated leaf.
    This test proves a ``not_`` over a to-many ``range`` leaf keeps Django's
    per-condition exclusion semantics: a book with a loan INSIDE the range is
    excluded, while a split-row book (loans straddling the range, none inside) is
    KEPT - matching Django's ``exclude(loans__id__range=...)`` baseline exactly.
    """
    shelf = _library_shelf()
    split = library_models.Book.objects.create(shelf=shelf, title="Split")
    p1 = library_models.Patron.objects.create(name="p1", email="a")
    p2 = library_models.Patron.objects.create(name="p2", email="b")
    low = library_models.Loan.objects.create(book=split, patron=p1, note="low")
    match_book = library_models.Book.objects.create(shelf=shelf, title="Match")
    p3 = library_models.Patron.objects.create(name="p3", email="c")
    mid = library_models.Loan.objects.create(book=match_book, patron=p3, note="mid")
    high = library_models.Loan.objects.create(book=split, patron=p2, note="high")
    assert low.pk < mid.pk < high.pk

    class BookLoanRangeFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__id": ["range"]}

    production = list(
        BookLoanRangeFilter.apply_sync(
            {"not_": {"loans__id": {"range": [mid.pk, mid.pk]}}},
            library_models.Book.objects.order_by("id"),
            _make_info(),
        )
        .order_by("id")
        .values_list("pk", flat=True),
    )
    # ``match_book`` is excluded (has a loan in range); the split-row book is KEPT.
    assert production == [split.pk]
    oracle = list(
        library_models.Book.objects.order_by("id")
        .exclude(loans__id__range=(mid.pk, mid.pk))
        .values_list("pk", flat=True),
    )
    assert oracle == production


def test_generated_flat_leaves_never_carry_exclude():
    """Row 10 invariant, proven executably: no framework-GENERATED flat leaf
    carries ``exclude=True``.

    Negation is a logic-tree ``not_`` concern (``_q_for_branch``), never baked
    into a generated leaf, so the flat-leaf correlated-``EXISTS`` adapter never
    sees a negated leaf. This enumerates a representative generated ``FilterSet``
    across scalar and to-many hops and every lookup, asserting each leaf is
    framework-generated (carries provenance) and non-excluding. A future
    regression that emits ``exclude=True`` on a generated leaf fails here loudly,
    replacing what used to be a bare prose claim.
    """

    class RepresentativeFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {
                "title": ["exact", "icontains"],
                "genres__name": ["icontains", "in"],
                "loans__note": ["icontains"],
                "loans__id": ["range", "gt"],
            }

    generated = RepresentativeFilter.get_filters()
    assert generated  # the representative leaves were actually produced
    for name, leaf in generated.items():
        assert filter_generation_provenance(leaf) is not None, name
        assert leaf.exclude is False, name


@pytest.mark.django_db
def test_c4_integer_in_over_to_many_path():
    """Matrix row 11 (integer ``in`` semantics over an eligible to-many path).

    ``Genre`` root over ``books__id`` ``in``: an explicit empty list is a no-op
    skip (matches every row, == baseline); a mixed valid/invalid membership
    filters on the valid member only; an all-invalid membership matches nothing.
    (The GlobalID-list sub-case is covered by
    ``test_c4_global_id_list_over_flat_relay_m2m_is_row_preserving`` below.)
    """
    shelf = _library_shelf()
    g1 = library_models.Genre.objects.create(name="g1")
    g2 = library_models.Genre.objects.create(name="g2")
    b1 = library_models.Book.objects.create(shelf=shelf, title="b1")
    b2 = library_models.Book.objects.create(shelf=shelf, title="b2")
    b1.genres.add(g1)
    b2.genres.add(g2)

    class GenreBookInFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"books__id": ["in"]}

    outer = library_models.Genre.objects.order_by("id")
    cases = {
        "empty-noop": ([], [g1.pk, g2.pk]),
        "mixed-valid-invalid": ([b1.pk, 99999999], [g1.pk]),
        "all-invalid": ([88888888, 99999999], []),
    }
    for _label, (value, expected) in cases.items():
        GenreBookInFilter.get_filters()
        result = GenreBookInFilter(
            data={"books__id__in": value},
            queryset=outer,
            request=HttpRequest(),
        ).qs
        production = list(result.order_by("id").values_list("pk", flat=True))
        assert production == expected


def test_flat_relay_m2m_leaf_builds_form_field_without_model_choice_extras():
    """The Relay M2M replacement strips model-choice extras so its field builds.

    Regression: upstream's M2M default carries a ``queryset`` extra; forwarding
    it into ``_GlobalIDMultipleChoiceField.__init__`` (a plain
    ``MultipleChoiceField``) raised ``TypeError`` at form-field construction,
    before any predicate could run.
    """

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class FlatBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact", "in"]}

    generated = FlatBookFilter.get_filters()
    for name in ("genres", "genres__in"):
        leaf = generated[name]
        assert isinstance(leaf, GlobalIDMultipleChoiceFilter)
        assert _MODEL_CHOICE_ONLY_EXTRAS.isdisjoint(leaf.extra)
        assert isinstance(leaf.field, _GlobalIDMultipleChoiceField)


def test_flat_relay_fk_leaf_builds_form_field_without_model_choice_extras():
    """The single-valued Relay FK replacement strips the extras too.

    Upstream's FK default carries ``queryset`` AND ``to_field_name`` /
    ``empty_label`` / ``null_label``, none of which ``GlobalIDFilter``'s plain
    ``CharField`` accepts.
    """

    class BookType(DjangoType):
        class Meta:
            model = library_models.Book
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(BookType, BookType.__django_strawberry_definition__)

    class FlatLoanFilter(FilterSet):
        class Meta:
            model = library_models.Loan
            fields = {"book": ["exact"]}

    leaf = FlatLoanFilter.get_filters()["book"]
    assert isinstance(leaf, GlobalIDFilter)
    assert _MODEL_CHOICE_ONLY_EXTRAS.isdisjoint(leaf.extra)
    leaf.field


@pytest.mark.django_db
def test_c4_global_id_list_over_flat_relay_m2m_is_row_preserving():
    """Matrix row 11, GlobalID-list sub-case: decode + row-preserving apply.

    A flat Relay M2M ``in`` leaf decodes real ``global_id_for``-minted ids and
    routes through the correlated-EXISTS applicator: a book linked to BOTH
    requested genres appears exactly once, the reserved alias is attached, and
    the membership tables stay out of the outer query.
    """
    from django_strawberry_framework import finalize_django_types
    from django_strawberry_framework.testing.relay import global_id_for

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            # ``books`` (reverse M2M -> Book) is excluded so finalization does
            # not demand a registered Book type; the filter targets Genre ids.
            fields = ("id", "name")
            interfaces = (strawberry.relay.Node,)

    finalize_django_types()

    shelf = _library_shelf()
    g1 = library_models.Genre.objects.create(name="gid-alpha")
    g2 = library_models.Genre.objects.create(name="gid-beta")
    both = library_models.Book.objects.create(shelf=shelf, title="both genres")
    both.genres.add(g1, g2)
    one = library_models.Book.objects.create(shelf=shelf, title="one genre")
    one.genres.add(g1)
    library_models.Book.objects.create(shelf=shelf, title="no genres")

    class FlatBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres": ["in"]}

    FlatBookFilter.get_filters()
    snapshot = FlatBookFilter._expansion_snapshot()
    assert snapshot is not None
    assert snapshot.candidates["genres__in"].eligible is True

    result = FlatBookFilter(
        data={"genres__in": [global_id_for(GenreType, g1.pk), global_id_for(GenreType, g2.pk)]},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    ).qs

    # ``both`` matches via TWO memberships yet appears once; ``one`` matches once.
    assert list(result.values_list("pk", flat=True)) == [both.pk, one.pk]
    assert result.query.distinct is False
    assert "_dst_predicate_0" in result.query.annotations
    outer_tables = {join.table_name for join in result.query.alias_map.values()}
    assert "library_book_genres" not in outer_tables
    assert "library_genre" not in outer_tables


@pytest.mark.django_db
def test_c4_untouched_surfaces_attach_no_reserved_alias():
    """Matrix row 12 (untouched surfaces): declared / method / custom / overrides.

    Each ineligible surface must run today's unchanged path: no reserved
    ``_dst_predicate_`` alias attaches, and the correct row is still returned. A
    ``distinct=True`` DECLARED filter keeps its own outer ``distinct``.
    """
    shelf = _library_shelf()
    book = library_models.Book.objects.create(shelf=shelf, title="bk")
    p1 = library_models.Patron.objects.create(name="p1", email="a")
    p2 = library_models.Patron.objects.create(name="p2", email="b")
    library_models.Loan.objects.create(book=book, patron=p1, note="Cardio one")
    library_models.Loan.objects.create(book=book, patron=p2, note="Cardio two")
    outer = library_models.Book.objects.order_by("id")

    class DeclaredDistinctFilter(FilterSet):
        loan_note = CharFilter(field_name="loans__note", lookup_expr="icontains", distinct=True)

        class Meta:
            model = library_models.Book
            fields = []

    DeclaredDistinctFilter.get_filters()
    declared = DeclaredDistinctFilter(
        data={"loan_note": "cardio"},
        queryset=outer,
        request=HttpRequest(),
    ).qs
    assert [n for n in declared.query.annotations if n.startswith("_dst_predicate_")] == []
    assert declared.query.distinct is True
    assert list(declared.order_by("id").values_list("pk", flat=True)) == [book.pk]

    class MethodFilter(FilterSet):
        loan_note = CharFilter(method="filter_note")

        class Meta:
            model = library_models.Book
            fields = []

        def filter_note(
            self,
            queryset,
            name,
            value,
        ):
            return queryset.filter(loans__note__icontains=value).distinct()

    MethodFilter.get_filters()
    method = MethodFilter(
        data={"loan_note": "cardio"},
        queryset=outer,
        request=HttpRequest(),
    ).qs
    assert [n for n in method.query.annotations if n.startswith("_dst_predicate_")] == []
    assert list(method.order_by("id").values_list("pk", flat=True)) == [book.pk]

    class CustomLoanNoteFilter(CharFilter):
        """A declared custom ``CharFilter`` subclass (ineligible: not generated)."""

    class CustomSubclassFilter(FilterSet):
        loan_note = CustomLoanNoteFilter(
            field_name="loans__note",
            lookup_expr="icontains",
            distinct=True,
        )

        class Meta:
            model = library_models.Book
            fields = []

    CustomSubclassFilter.get_filters()
    custom = CustomSubclassFilter(
        data={"loan_note": "cardio"},
        queryset=outer,
        request=HttpRequest(),
    ).qs
    assert [n for n in custom.query.annotations if n.startswith("_dst_predicate_")] == []
    assert list(custom.order_by("id").values_list("pk", flat=True)) == [book.pk]

    class OverridesFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}
            filter_overrides = {
                library_models.Loan._meta.get_field("note").__class__: {
                    "filter_class": CharFilter,
                    "extra": lambda f: {"lookup_expr": "icontains"},
                },
            }

    OverridesFilter.get_filters()
    overridden = OverridesFilter(
        data={"loans__note__icontains": "cardio"},
        queryset=outer,
        request=HttpRequest(),
    ).qs
    assert [n for n in overridden.query.annotations if n.startswith("_dst_predicate_")] == []
    assert list(overridden.order_by("id").values_list("pk", flat=True)) == [book.pk]


# ---------------------------------------------------------------------------
# C.4 - multiset contract
#
# A framework-generated predicate is a SQL selection over the queryset it
# receives: each existing root-row occurrence is retained exactly once or
# removed. Framework predicates never multiply rows AND never collapse
# duplicates already present from the consumer's own queryset shaping;
# consumer ordering and explicit consumer ``.distinct()`` pass through
# untouched. These rows assert ordered pk SEQUENCES (never sets), ``count()``,
# and duplicate multiplicity across four INPUT querysets for one fixed
# eligible to-many candidate (``BookFilter`` root, ``genres__name`` icontains).
# ---------------------------------------------------------------------------


def _seed_multiset_book_genre_graph():
    """Three books over the ``genres__name`` icontains candidate.

    ``book_two_genres`` matches "cardio" via TWO genres (its own occurrences
    fan when a consumer joins on genres); ``book_one_genre`` matches via ONE
    genre; ``book_no_match`` carries only a non-matching genre. Every genre
    also contains the letter "o", so a consumer pre-fan on ``icontains="o"``
    includes ``book_no_match`` as a non-matching occurrence the framework
    predicate must drop.
    """
    branch = library_models.Branch.objects.create(name="Multiset Branch")
    shelf = library_models.Shelf.objects.create(branch=branch, code="MS-1")
    book_two_genres = library_models.Book.objects.create(shelf=shelf, title="Book Two Genres")
    book_one_genre = library_models.Book.objects.create(shelf=shelf, title="Book One Genre")
    book_no_match = library_models.Book.objects.create(shelf=shelf, title="Book No Match")
    book_two_genres.genres.add(
        library_models.Genre.objects.create(name="cardiology"),
        library_models.Genre.objects.create(name="cardio-thoracic"),
    )
    book_one_genre.genres.add(library_models.Genre.objects.create(name="cardio-vascular"))
    book_no_match.genres.add(library_models.Genre.objects.create(name="neurology"))
    return book_two_genres.pk, book_one_genre.pk, book_no_match.pk


def _apply_book_genre_leaf(queryset):
    """Apply the eligible framework leaf via the consumer-shaped-queryset seam.

    Constructing ``BookFilter`` with ``queryset=<shaped input>`` is exactly the
    consumer-shaped-queryset seam production uses; form validation is
    transparent (the flat leaf name is a valid form key).
    """
    BookFilter.get_filters()
    return BookFilter(
        data={"genres__name__icontains": "cardio"},
        queryset=queryset,
        request=HttpRequest(),
    ).qs


@pytest.mark.django_db
def test_c4_multiset_non_fanned_input_each_row_once():
    """(a) Non-fanned input: each matching book exactly once, consumer order kept."""
    two, one, _no = _seed_multiset_book_genre_graph()

    result = _apply_book_genre_leaf(library_models.Book.objects.order_by("id"))

    sequence = list(result.values_list("pk", flat=True))
    assert sequence == [two, one]
    assert result.count() == len(sequence)
    # The framework leaf is row-preserving: no framework-added DISTINCT.
    assert result.query.distinct is False


@pytest.mark.django_db
def test_c4_multiset_pre_fanned_consumer_input_multiplicity_survives():
    """(b) Pre-fanned consumer input: existing duplicates that match survive; non-matches drop.

    The consumer deliberately fans the queryset on ``genres__name icontains
    "o"`` BEFORE the framework filter runs. ``book_two_genres`` fans to two
    rows, ``book_one_genre`` to one, ``book_no_match`` to one. The framework
    predicate SELECTS over that multiset: the matching occurrences survive with
    their multiplicity and the non-matching ``book_no_match`` occurrence drops -
    NO framework dedup.
    """
    two, one, no_match = _seed_multiset_book_genre_graph()

    pre_fanned = library_models.Book.objects.filter(genres__name__icontains="o").order_by("id")
    # The consumer's own shaping already produced duplicate rows.
    assert list(pre_fanned.values_list("pk", flat=True)) == [
        two,
        two,
        one,
        no_match,
    ]

    result = _apply_book_genre_leaf(pre_fanned)

    sequence = list(result.values_list("pk", flat=True))
    assert sequence == [two, two, one]
    assert result.count() == len(sequence)
    assert result.query.distinct is False


@pytest.mark.django_db
def test_c4_multiset_consumer_distinct_input_is_preserved():
    """(c) Explicitly consumer-distinct input: consumer's own distinct collapses duplicates."""
    two, one, _no = _seed_multiset_book_genre_graph()

    consumer_distinct = (
        library_models.Book.objects.filter(genres__name__icontains="o").order_by("id").distinct()
    )
    result = _apply_book_genre_leaf(consumer_distinct)

    sequence = list(result.values_list("pk", flat=True))
    assert sequence == [two, one]
    assert result.count() == len(sequence)
    # The consumer's explicit distinct passes through untouched.
    assert result.query.distinct is True


@pytest.mark.django_db
def test_c4_multiset_custom_filter_produced_input_multiplicity_survives():
    """(d) Custom-filter-produced input: the fanned multiplicity from a declared leaf survives.

    A consumer-declared ``CharFilter`` with ``distinct=False`` on a to-many
    path (the old fan-out shape, consumer-owned) runs first and fans the rows;
    the eligible framework leaf then preserves that multiplicity.
    """
    two, one, _no = _seed_multiset_book_genre_graph()

    class ConsumerFanFilter(FilterSet):
        genres_fan = CharFilter(
            field_name="genres__name",
            lookup_expr="icontains",
            distinct=False,
        )

        class Meta:
            model = library_models.Book
            fields = []

    ConsumerFanFilter.get_filters()
    fanned = ConsumerFanFilter(
        data={"genres_fan": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    ).qs
    # The consumer-declared leaf fans the matching book with two genres.
    assert list(fanned.values_list("pk", flat=True)) == [two, two, one]

    result = _apply_book_genre_leaf(fanned)

    sequence = list(result.values_list("pk", flat=True))
    assert sequence == [two, two, one]
    assert result.count() == len(sequence)
    assert result.query.distinct is False


# ---------------------------------------------------------------------------
# C.4 - Medtrics LoanFilter adapter tier (package-tier SQL shape + pagination)
#
# The fakeshop ``LoanFilter`` gains the generated deep path
# ``book__loans__patron__email`` (spelled ``bookLoansPatronEmail`` on the wire).
# These package-tier tests inspect the query object; the live row-semantics
# proof lives in ``examples/fakeshop/test_query/test_library_api.py``.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_c4_medtrics_loanfilter_deep_leaf_sql_shape():
    """The Medtrics deep leaf composes as ONE correlated EXISTS with no root fan-out."""
    from apps.library.filters import LoanFilter

    graph = _seed_medtrics_loan_graph()
    LoanFilter.get_filters()

    result = LoanFilter(
        data={"book__loans__patron__email__icontains": "Cardio"},
        queryset=library_models.Loan.objects.order_by("id"),
        request=HttpRequest(),
    ).qs

    # Root alias_map: exactly ONE library_loan alias, NO patron, NO second
    # book-join fan-out; the outer query carries no framework DISTINCT.
    root_tables = [join.table_name for join in result.query.alias_map.values()]
    assert root_tables == ["library_loan"]
    assert "library_patron" not in root_tables
    assert result.query.distinct is False

    # Exactly one correlated EXISTS owns the inner joins; the inner SQL contains
    # the membership library_loan re-entry and the terminal library_patron.
    sql = str(result.query).upper()
    assert sql.count("EXISTS") == 1
    inner = str(result.query)
    assert inner.upper().count("LIBRARY_LOAN") >= 2  # outer + inner membership re-entry
    assert "library_patron" in inner

    # Ordered pks: the shared-book row matching via TWO patrons appears ONCE.
    sequence = list(result.values_list("pk", flat=True))
    assert sequence == [graph.relation_and_direct, graph.relation_only]
    assert result.count() == 2


@pytest.mark.django_db
def test_c4_medtrics_loanfilter_deep_leaf_package_tier_pagination():
    """Two-edge page-size-1 boundary over the filtered loans (package-tier slicing).

    ``all_library_loans`` is a plain list field (no connection surface), so
    pagination coverage lands here as offset/limit slicing with a stable count.
    """
    from apps.library.filters import LoanFilter

    graph = _seed_medtrics_loan_graph()
    LoanFilter.get_filters()

    filtered = LoanFilter(
        data={"book__loans__patron__email__icontains": "Cardio"},
        queryset=library_models.Loan.objects.order_by("id"),
        request=HttpRequest(),
    ).qs

    total = filtered.count()
    assert total == 2

    page_one = list(filtered[0:1].values_list("pk", flat=True))
    page_two = list(filtered[1:2].values_list("pk", flat=True))
    assert page_one == [graph.relation_and_direct]
    assert page_two == [graph.relation_only]


# ---------------------------------------------------------------------------
# Apply pipeline - request extraction
# ---------------------------------------------------------------------------


def test_request_from_info_uses_context_request_attribute():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    request = HttpRequest()
    info = _make_info(request)
    assert CategoryFilter._request_from_info(info) is request


def test_request_from_info_falls_back_to_bare_http_request():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    class _Info:
        def __init__(self):
            self.context = HttpRequest()

    info = _Info()
    assert CategoryFilter._request_from_info(info) is info.context


def test_request_from_info_raises_for_unsupported_context_shape():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    class _Info:
        context = object()

    with pytest.raises(ConfigurationError):
        CategoryFilter._request_from_info(_Info())


# ---------------------------------------------------------------------------
# Apply pipeline - normalize_input
# ---------------------------------------------------------------------------


def test_normalize_input_returns_empty_dict_for_none():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._normalize_input(None) == {}


def test_normalize_input_skips_none_valued_attrs():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    data = CategoryFilter._normalize_input({"name": None, "i_contains": "foo"})
    assert "name" not in data
    assert data == {"icontains": "foo"}


def test_normalize_input_maps_in_python_attr_to_in_form_data_key():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["in"]}

    data = CategoryFilter._normalize_input(
        {
            "in_": [1, 2, 3],
        },
    )
    assert "in" in data
    assert data["in"] == [1, 2, 3]


def test_normalize_input_maps_logic_keys_to_short_form():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    data = CategoryFilter._normalize_input(
        {"and_": [{"name": "foo"}], "or_": [{"name": "bar"}], "not_": {"name": "baz"}},
    )
    assert data["and"] == [{"name": "foo"}]
    assert data["or"] == [{"name": "bar"}]
    assert data["not"] == {"name": "baz"}


def test_normalize_input_signature_takes_only_input_value():
    """``_normalize_input`` accepts only ``input_value``; no dead owner parameter.

    GlobalID type-name validation happens at queryset-evaluation time
    inside the filter's ``filter()`` method, reading the owner via
    ``filter_instance.parent._owner_definition``. The normalize step
    therefore does not need an owner parameter - passing one is dead
    plumbing that suggests an unfinished wiring path.
    """
    import inspect

    sig = inspect.signature(FilterSet._normalize_input)
    # `cls` is bound on a classmethod's underlying function, so the public
    # signature carries `input_value` only.
    assert list(sig.parameters) == ["input_value"]


def test_normalize_input_walks_strawberry_dataclass():
    """A dataclass-shaped input (Strawberry input) is walked via `__dataclass_fields__`."""

    @strawberry.input
    class _Input:
        name: str | None = strawberry.UNSET

    value = _Input(name="hello")
    # `__dataclass_fields__` carries the declared field names.

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    data = CategoryFilter._normalize_input(value)
    assert data.get("name") == "hello"


def test_normalize_input_inner_bag_loop_skips_unset_lookups():
    """Partial operator bags don't leak ``UNSET`` into form data.

    Strawberry input dataclasses default every operator-bag lookup
    (``exact``, ``i_contains``, ``in_``, ...) to ``UNSET`` rather than
    ``None``. The inner loop in ``_normalize_input`` must skip UNSET
    the same way the outer loop does; otherwise the UNSET sentinel
    reaches ``normalize_input_value`` and either raises
    ``TypeError: argument of type 'UNSET' is not iterable`` (list-like
    filters) or lands in ``data[form_key]`` as a bogus value (scalar
    filters). The common case is a consumer who supplies one lookup
    but not the others - partially-supplied bags must not break.
    """

    @strawberry.input
    class _Bag:
        exact: str | None = strawberry.UNSET
        i_contains: str | None = strawberry.UNSET

    @strawberry.input
    class _Input:
        name: _Bag | None = strawberry.UNSET

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact", "icontains"]}

    # Bag with only ``i_contains`` supplied; ``exact`` defaults to UNSET.
    bag = _Bag(i_contains="foo")
    data = CategoryFilter._normalize_input(_Input(name=bag))
    # The UNSET ``exact`` does NOT pollute form-data as ``name=UNSET``.
    assert "name" not in data
    # The supplied ``i_contains`` lands at its django-filter form key.
    assert data.get("name__icontains") == "foo"


def test_normalize_input_skips_strawberry_unset_attrs():
    """``strawberry.UNSET`` attrs are skipped the same as ``None``.

    Strawberry input dataclasses default unsupplied fields to ``UNSET``
    rather than ``None``. Leaving them in ``data`` would route them
    through the parent form and surface as a spurious "missing /
    invalid" form error for fields the consumer never sent.
    """

    @strawberry.input
    class _Input:
        name: str | None = strawberry.UNSET

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    data = CategoryFilter._normalize_input(_Input())
    assert "name" not in data


# ---------------------------------------------------------------------------
# Apply pipeline - validate_form_or_raise
# ---------------------------------------------------------------------------


def test_validate_form_or_raise_raises_on_invalid_form():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"id": ["exact"]}

    instance = CategoryFilter(data={"id": "not-an-integer"}, queryset=Category.objects.all())
    with pytest.raises(GraphQLError) as excinfo:
        CategoryFilter._validate_form_or_raise(instance)
    error = excinfo.value
    assert error.extensions["code"] == "FILTER_INVALID"
    # `errors` is the structured dict per `ErrorDict.get_json_data()`.
    assert "id" in error.extensions["errors"]


def test_validate_form_or_raise_passes_for_valid_form():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    instance = CategoryFilter(data={"name": "anything"}, queryset=Category.objects.all())
    # No raise expected.
    CategoryFilter._validate_form_or_raise(instance)


# ---------------------------------------------------------------------------
# Apply pipeline - permission checks
# ---------------------------------------------------------------------------


def test_run_permission_checks_fires_only_for_active_input_fields():
    fired: list[str] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, request):
            fired.append("name")

    CategoryFilter._run_permission_checks({}, request=HttpRequest())
    assert fired == []

    CategoryFilter._run_permission_checks({"name": "anything"}, request=HttpRequest())
    assert fired == ["name"]


def test_run_permission_checks_skips_unset_related_branch():
    """``strawberry.UNSET`` on a related branch is treated as "not supplied".

    Strawberry input dataclasses default unsupplied fields to ``UNSET``
    rather than ``None``. The active-branch detection in
    ``_iter_active_related_branches`` must collapse UNSET so the parent
    per-branch permission gate does not fire for fields the consumer
    never sent.
    """
    fired: list[str] = []

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    @strawberry.input
    class BranchInput:
        name: str | None = strawberry.UNSET
        shelves: Any = strawberry.UNSET

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

        def check_shelves_permission(self, request):
            fired.append("shelves")

    BranchFilter._run_permission_checks(BranchInput(), request=HttpRequest())
    assert fired == []


def test_run_permission_checks_recurses_into_active_related_branch():
    fired: list[str] = []

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        def check_code_permission(self, request):
            fired.append("shelf.code")

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    BranchFilter._run_permission_checks({"name": "x"}, request=HttpRequest())
    assert fired == []

    BranchFilter._run_permission_checks(
        {"shelves": {"code": "anything"}},
        request=HttpRequest(),
    )
    assert "shelf.code" in fired


def test_run_permission_checks_recurses_into_logical_branches():
    """Per-call dedup: a gate fires once even when the field appears in many branches.

    The recursion correctly walks ``and`` / ``or`` / ``not`` sub-trees
    so a nested field is gated the same as a top-level one. The dedup
    keys on ``check_<field>_permission`` method names for the lifetime
    of one top-level call; a field appearing in multiple ``or`` arms
    fires its gate ONCE per call (the gate's logic is idempotent, so
    multi-firing is functionally harmless but produces duplicate audit
    log entries - the R4 contract dedupes to avoid that).
    """
    fired: list[str] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, request):
            fired.append("name")

    # ``and`` with the same field in two arms fires the gate ONCE.
    CategoryFilter._run_permission_checks(
        {"and_": [{"name": "foo"}, {"name": "bar"}]},
        request=HttpRequest(),
    )
    assert fired == ["name"]
    fired.clear()

    # ``or`` with the same field fires ONCE.
    CategoryFilter._run_permission_checks(
        {"or_": [{"name": "foo"}]},
        request=HttpRequest(),
    )
    assert fired == ["name"]
    fired.clear()

    # ``not`` with the field fires ONCE.
    CategoryFilter._run_permission_checks(
        {"not_": {"name": "baz"}},
        request=HttpRequest(),
    )
    assert fired == ["name"]
    fired.clear()

    # A fresh top-level call gets a fresh dedup set; the gate fires
    # again because it's a new call.
    CategoryFilter._run_permission_checks({"name": "x"}, request=HttpRequest())
    assert fired == ["name"]


def test_run_permission_checks_dedups_child_gate_across_sibling_branches():
    """A child filterset gate fires once even when entered from sibling ``or`` arms.

    The ``_fired`` map is keyed by ``FilterSet`` class and shared across
    BOTH the logical-branch recursion and the child-filterset recursion.
    So ``or: [{shelves: {...}}, {shelves: {...}}]`` enters ``ShelfFilter``
    twice (once per arm) but its ``check_code_permission`` fires only
    once - the per-class set keyed on ``ShelfFilter`` dedups the second
    entry. The parent's per-branch ``check_shelves_permission`` likewise
    fires once (deduped on the parent's per-class set).
    """
    fired: list[str] = []

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        def check_code_permission(self, request):
            fired.append("shelf.code")

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

        def check_shelves_permission(self, request):
            fired.append("branch.shelves")

    BranchFilter._run_permission_checks(
        {
            "or_": [{"shelves": {"code": "a"}}, {"shelves": {"code": "b"}}],
        },
        request=HttpRequest(),
    )
    # Parent per-branch gate fires once; child class gate fires once -
    # NOT once per arm.
    assert fired.count("branch.shelves") == 1
    assert fired.count("shelf.code") == 1


def test_run_permission_checks_caps_logical_branch_nesting():
    """Pathologically-deep nesting raises ``ConfigurationError`` instead of stack-overflow.

    ``_MAX_LOGIC_DEPTH`` caps the recursion so a malicious or
    accidental ``{and: [{and: [{and: [...]}]}]}`` shape surfaces a
    typed error at the source instead of a Python ``RecursionError``.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    # Build a 20-deep ``and`` chain - well past the 8-level cap.
    deep: dict = {"name": "leaf"}
    for _ in range(20):
        deep = {"and_": [deep]}

    with pytest.raises(ConfigurationError) as excinfo:
        CategoryFilter._run_permission_checks(deep, request=HttpRequest())
    assert "_MAX_LOGIC_DEPTH" in str(excinfo.value)


def test_max_logic_depth_is_overridable_classvar():
    """A subclass can raise ``_MAX_LOGIC_DEPTH`` without monkey-patching.

    The cap is a ``ClassVar`` on ``FilterSet`` so a consumer with a
    legitimate deeper-nesting case (machine-generated queries) can
    subclass and override it. A 12-deep chain that trips the default
    cap of 8 is accepted under an override of 32.
    """

    class DeepCategoryFilter(FilterSet):
        _MAX_LOGIC_DEPTH = 32

        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    deep: dict = {"name": "leaf"}
    for _ in range(12):
        deep = {"and_": [deep]}

    # No raise: 12 levels is under the subclass's raised cap of 32.
    DeepCategoryFilter._run_permission_checks(deep, request=HttpRequest())

    # The base class still caps at 8 - the override is subclass-local.
    class ShallowCategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError):
        ShallowCategoryFilter._run_permission_checks(deep, request=HttpRequest())


@pytest.mark.django_db
def test_evaluate_logic_tree_preserves_request_context():
    captured_requests: list[Any] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def filter_queryset(self, queryset):
            captured_requests.append(self.request)
            return super().filter_queryset(queryset)

    request = HttpRequest()
    info = _make_info(request)
    CategoryFilter.apply_sync(
        {"and_": [{"name": "alpha"}]},
        Category.objects.all(),
        info,
    )
    assert len(captured_requests) > 0
    # First entry in captured_requests is from the parent category filter,
    # and subsequent are from the nested logic branch evaluation.
    # All of them must preserve the same HttpRequest object.
    for req in captured_requests:
        assert req is request


# ---------------------------------------------------------------------------
# Apply pipeline - full apply_sync path
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_apply_sync_filters_against_simple_scalar_input():
    Category.objects.create(name="alpha")
    Category.objects.create(name="beta")

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    info = _make_info()
    qs = CategoryFilter.apply_sync({"name": "alpha"}, Category.objects.all(), info)
    assert list(qs.values_list("name", flat=True)) == ["alpha"]


@pytest.mark.django_db
def test_permission_checks_run_only_through_apply_entrypoint():
    """``apply_*`` is the sole permission-aware entry; the bare ``.qs`` path does not gate.

    Permission hooks fire from ``_run_permission_checks``, which
    ``apply_sync`` / ``apply_async`` invoke up-front (recursing into nested
    branches). The tree-composition path
    (``filter_queryset`` -> ``_q_for_branch`` -> ``.qs``) deliberately does
    NOT re-run permission checks -- it relies on that up-front call. This
    pins the contract (H-filters-7 of the pre-merge review): bypassing
    ``apply_*`` by constructing the filterset and reading ``.qs`` directly
    skips the gate, so ``apply_*`` must remain the only permission-aware
    entry point. If a future refactor moves filtering off ``apply_*`` this
    test fails loudly, so permissions are re-wired rather than silently lost.
    """
    fired: list[str] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, request):
            fired.append("name")

    Category.objects.create(name="alpha")

    # Through ``apply_sync`` (the legal entry): the gate fires.
    CategoryFilter.apply_sync({"name": "alpha"}, Category.objects.all(), _make_info())
    assert fired == ["name"]

    # Bypassing ``apply_*`` (direct construction + ``.qs``): the gate does NOT fire.
    fired.clear()
    bare = CategoryFilter(
        data={"name": "alpha"},
        queryset=Category.objects.all(),
        request=HttpRequest(),
    )
    list(bare.qs)
    assert fired == []


@pytest.mark.django_db
def test_apply_sync_nested_related_gate_fires_once_not_per_level():
    """A nested ``RelatedFilter`` child gate fires exactly once through ``apply_sync``.

    Regression test for the double-fire defect: the related-visibility
    derivation invoked the child filterset's ``apply_sync``, which runs
    ``_run_permission_checks``, AND the top-level dedicated
    ``_run_permission_checks`` pass ALSO recursed into the child -- so a
    nested ``check_<field>_permission`` gate fired once per enclosing level
    (twice at one level of relation nesting, three times at two levels,
    compounding with depth). This violated the documented contract that the
    derivation / tree-composition paths do NOT re-run permission checks
    (only the single up-front pass fires gates) and double-invoked
    side-effectful gates (audit logging, rate limiting, metrics).

    The fix threads ``run_permissions=False`` into the derivation's child
    ``apply_*`` calls so the child's gates fire only via the top-level pass.
    """
    branch = library_models.Branch.objects.create(name="alpha")
    shelf = library_models.Shelf.objects.create(branch=branch, code="AAA")
    library_models.Book.objects.create(shelf=shelf, title="T")

    fired: list[str] = []

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

    class BookType(DjangoType):
        class Meta:
            model = library_models.Book
            fields = ("id", "title")

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact", "icontains"]}

        def check_title_permission(self, request):
            fired.append("title")

    class ShelfFilter(FilterSet):
        books = RelatedFilter(BookFilter, field_name="books")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        def check_books_permission(self, request):
            fired.append("shelf.books")

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

        def check_shelves_permission(self, request):
            fired.append("branch.shelves")

    # One level of relation nesting: the child ``code`` gate is absent, but
    # the parent per-branch ``check_shelves_permission`` must fire once.
    BranchFilter.apply_sync(
        {"shelves": {"code": {"exact": "AAA"}}},
        library_models.Branch.objects.all(),
        _make_info(),
    )
    assert fired == ["branch.shelves"]

    # Two levels of relation nesting: the deepest gate
    # (``BookFilter.check_title_permission``) must fire EXACTLY ONCE, not
    # three times (pre-fix: once per enclosing derivation level plus the
    # dedicated pass).
    fired.clear()
    BranchFilter.apply_sync(
        {"shelves": {"books": {"title": {"i_contains": "T"}}}},
        library_models.Branch.objects.all(),
        _make_info(),
    )
    assert fired.count("title") == 1
    assert fired.count("shelf.books") == 1
    assert fired.count("branch.shelves") == 1


@pytest.mark.django_db
def test_apply_sync_nested_related_gate_still_denies():
    """The single-fire fix must not weaken enforcement: a nested gate still denies.

    The derivation no longer fires the child's gates, but the top-level
    ``_run_permission_checks`` pass still recurses into every active related
    branch, so a raising ``check_<field>_permission`` inside a nested branch
    still aborts ``apply_sync`` with the consumer's ``GraphQLError`` before
    any rows are returned.
    """
    branch = library_models.Branch.objects.create(name="alpha")
    library_models.Shelf.objects.create(branch=branch, code="AAA")

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact", "icontains"]}

        def check_code_permission(self, request):
            raise GraphQLError("denied shelf code")

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    with pytest.raises(GraphQLError) as excinfo:
        BranchFilter.apply_sync(
            {"shelves": {"code": {"i_contains": "AAA"}}},
            library_models.Branch.objects.all(),
            _make_info(),
        )
    assert "denied shelf code" in str(excinfo.value)


@pytest.mark.django_db
def test_apply_async_nested_related_gate_fires_once_and_still_denies():
    """The async related derivation neither duplicates nor bypasses nested gates."""
    import asyncio

    branch = library_models.Branch.objects.create(name="alpha")
    library_models.Shelf.objects.create(branch=branch, code="AAA")
    fired: list[str] = []

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact", "icontains"]}

        def check_code_permission(self, request):
            fired.append("code")

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    queryset = asyncio.run(
        BranchFilter.apply_async(
            {"shelves": {"code": {"i_contains": "AAA"}}},
            library_models.Branch.objects.all(),
            _make_info(),
        ),
    )
    assert list(queryset.values_list("name", flat=True)) == ["alpha"]
    assert fired == ["code"]

    class DenyingShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        def check_code_permission(self, request):
            raise GraphQLError("denied async shelf code")

    class DenyingBranchFilter(FilterSet):
        shelves = RelatedFilter(DenyingShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    with pytest.raises(GraphQLError, match="denied async shelf code"):
        asyncio.run(
            DenyingBranchFilter.apply_async(
                {"shelves": {"code": {"exact": "AAA"}}},
                library_models.Branch.objects.all(),
                _make_info(),
            ),
        )


@pytest.mark.django_db
def test_apply_sync_passes_through_empty_filter_input():
    Category.objects.create(name="alpha")
    Category.objects.create(name="beta")

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    info = _make_info()
    qs = CategoryFilter.apply_sync({}, Category.objects.all(), info)
    assert qs.count() == 2


@pytest.mark.django_db
def test_apply_sync_raises_graphql_error_on_invalid_input():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"id": ["exact"]}

    info = _make_info()
    with pytest.raises(GraphQLError):
        CategoryFilter.apply_sync({"id": "not-an-integer"}, Category.objects.all(), info)


# ---------------------------------------------------------------------------
# Apply pipeline - dispatcher catch-and-rethrow
# ---------------------------------------------------------------------------


def test_apply_dispatcher_rethrows_sync_misuse_with_clearer_message():
    """A ``SyncMisuseError`` from ``apply_sync`` becomes ``RuntimeError``.

    Class-based dispatch: the dispatcher catches the typed subclass
    directly (no substring match) and rethrows with the actionable
    "use apply_async instead" message.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        @classmethod
        def apply_sync(cls, *args, **kwargs):
            raise SyncMisuseError("FakeType.get_queryset returned a coroutine.")

    with pytest.raises(RuntimeError) as excinfo:
        CategoryFilter.apply(None, Category.objects.all(), _make_info())
    assert "apply_async" in str(excinfo.value)


def test_apply_dispatcher_propagates_other_configuration_errors():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        @classmethod
        def apply_sync(cls, *args, **kwargs):
            raise ConfigurationError("totally unrelated configuration problem")

    with pytest.raises(ConfigurationError):
        CategoryFilter.apply(None, Category.objects.all(), _make_info())


def test_apply_dispatcher_propagates_other_runtime_errors():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        @classmethod
        def apply_sync(cls, *args, **kwargs):
            raise RuntimeError("not a sync-misuse error")

    with pytest.raises(RuntimeError) as excinfo:
        CategoryFilter.apply(None, Category.objects.all(), _make_info())
    assert "not a sync-misuse error" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Apply pipeline - _apply_related_constraints active-branch scoping
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_apply_related_constraints_runs_active_branch_only():
    branch = library_models.Branch.objects.create(name="alpha")
    library_models.Shelf.objects.create(branch=branch, code="active")
    library_models.Shelf.objects.create(branch=branch, code="hidden")
    other = library_models.Branch.objects.create(name="beta")
    library_models.Shelf.objects.create(branch=other, code="other-shelf")

    explicit_qs = library_models.Shelf.objects.filter(code="active")

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves", queryset=explicit_qs)

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # Inactive branch: no constraint applied.
    parent_qs = library_models.Branch.objects.all()
    constrained = BranchFilter._apply_related_constraints({"name": "alpha"}, parent_qs, {})
    assert "shelves__in" not in str(constrained.query)

    # Active branch: constraint applied.
    constrained_active = BranchFilter._apply_related_constraints(
        {"shelves": {"code": "active"}},
        parent_qs,
        {},
    )
    # The active branch must restrict the parent count to branches whose
    # shelves intersect the explicit `code="active"` queryset.
    sql = str(constrained_active.query).lower()
    assert "library_shelf" in sql
    assert "active" in sql
    # And materializing the queryset returns only the branch with an active shelf.
    assert list(constrained_active.values_list("name", flat=True)) == ["alpha"]


@pytest.mark.django_db
def test_active_related_branch_without_registered_target_raises():
    """An active related branch with no registered target type fails loud.

    ``_iter_visibility_steps`` raises ``ConfigurationError`` instead of
    skipping: the branch is active (the consumer supplied input for it),
    so skipping would drop the constraint entirely and return unfiltered
    parent rows - a filter the consumer believes is applied doing
    nothing. The same misconfiguration is caught at finalize time for
    schema-wired filtersets (``_bind_filtersets`` subpass 2.5); this
    pins the runtime guard for direct ``apply_*`` callers. An INACTIVE
    branch must not raise - declaring a ``RelatedFilter`` is fine until
    input activates it.
    """
    library_models.Branch.objects.create(name="alpha")

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # No ShelfType registered: the active branch raises.
    with pytest.raises(ConfigurationError) as excinfo:
        BranchFilter.apply_sync(
            {"shelves": {"code": {"exact": "x"}}},
            library_models.Branch.objects.all(),
            _make_info(),
        )
    msg = str(excinfo.value)
    assert "shelves" in msg
    assert "no DjangoType is registered" in msg

    # Inactive branch: same filterset applies cleanly without the target.
    qs = BranchFilter.apply_sync(
        {"name": "alpha"},
        library_models.Branch.objects.all(),
        _make_info(),
    )
    assert list(qs.values_list("name", flat=True)) == ["alpha"]


@pytest.mark.django_db
def test_dict_operator_bag_filters_through_apply_sync():
    """A dict-shaped operator bag filters end-to-end via ``apply_sync``.

    Pins the ``_operator_bag_items`` dict-walk: before it, a dict bag
    fell through to the scalar branch and the filter silently applied
    nothing (every row returned).
    """
    Category.objects.create(name="alpha-match")
    Category.objects.create(name="beta")

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact", "icontains"]}

    qs = CategoryFilter.apply_sync(
        {"name": {"i_contains": "match"}},
        Category.objects.all(),
        _make_info(),
    )
    assert list(qs.values_list("name", flat=True)) == ["alpha-match"]


@pytest.mark.django_db
def test_apply_related_constraints_model_mismatch_raises_configuration_error():
    """A divergent-model ``RelatedFilter(queryset=...)`` surfaces ``ConfigurationError``.

    Django raises ``AssertionError: Cannot combine queries on two
    different base models`` when ``explicit & child_qs`` is called
    against mismatched base models. The opaque assertion is replaced
    with a typed ``ConfigurationError`` naming the offending filter
    and both models, so a GraphQL consumer sees an actionable message
    instead of a raw Django assertion.
    """
    # Branch has shelves; the consumer accidentally passes a Book qs as
    # the explicit constraint for the ``shelves`` branch.
    library_models.Branch.objects.create(name="alpha")
    wrong_model_qs = library_models.Book.objects.all()

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves", queryset=wrong_model_qs)

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # The child_qs_by_branch dict carries the correctly-modeled child qs
    # (Shelf); the explicit constraint is the wrong model (Book). The
    # precheck must surface ConfigurationError.
    child_shelf_qs = library_models.Shelf.objects.all()
    with pytest.raises(ConfigurationError) as excinfo:
        BranchFilter._apply_related_constraints(
            {"shelves": {"code": "active"}},
            library_models.Branch.objects.all(),
            {"shelves": child_shelf_qs},
        )
    msg = str(excinfo.value)
    assert "Book" in msg
    assert "Shelf" in msg
    assert "shelves" in msg


@pytest.mark.django_db
def test_apply_related_constraints_proxy_model_is_rejected():
    """Proxy models are rejected because Django's ``&`` rejects them.

    Django's ``Query.combine`` compares ``self.model != rhs.model``
    via identity, so a proxy and its concrete parent (which share a
    database table) are still rejected by ``&``. The precheck
    surfaces a typed ``ConfigurationError`` BEFORE the consumer hits
    the raw ``TypeError`` so the failure mode is actionable. The
    docstring on ``_apply_related_constraints`` explicitly carves
    proxy / MTI out of the accepted shapes.

    ``ShelfProxy`` is defined at module scope (see top of file) so the
    app registry registers it at import time.
    """
    library_models.Branch.objects.create(name="alpha")

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        # Explicit queryset is keyed on the proxy; the target filterset
        # is keyed on the concrete model. Django's combine rejects
        # this; the precheck surfaces ConfigurationError instead.
        shelves = RelatedFilter(
            ShelfFilter,
            field_name="shelves",
            queryset=ShelfProxy.objects.all(),
        )

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    child_shelf_qs = library_models.Shelf.objects.all()
    with pytest.raises(ConfigurationError) as excinfo:
        BranchFilter._apply_related_constraints(
            {"shelves": {"code": "active"}},
            library_models.Branch.objects.all(),
            {"shelves": child_shelf_qs},
        )
    assert "ShelfProxy" in str(excinfo.value)
    assert "Shelf" in str(excinfo.value)


@pytest.mark.django_db
def test_apply_sync_passes_constrained_queryset_to_filterset_instance():
    """H3-of-rev8 pipeline ordering - constraints land in `self.queryset`.

    `apply_sync` must apply `_apply_related_constraints` BEFORE
    constructing the `FilterSet` instance so the explicit
    `RelatedFilter(queryset=...)` ledger and the visibility queryset
    propagate through to `.qs` via `self.queryset`. A future refactor
    that instantiates first and mutates `self._queryset` afterwards
    would not carry the constraint through `BaseFilterSet`'s internal
    `filter_queryset` path; this test pins the order.
    """
    branch = library_models.Branch.objects.create(name="alpha")
    library_models.Shelf.objects.create(branch=branch, code="active")

    explicit_qs = library_models.Shelf.objects.filter(code="active")

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class ShelfType(DjangoType):
        """Registered target so the active ``shelves`` branch resolves."""

        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

    captured: dict[str, Any] = {}
    real_init = FilterSet.__init__

    def spy_init(self, *args, **kwargs):
        # Record the `queryset` kwarg every consumer-`FilterSet` subclass
        # receives during this call. The active `shelves` branch's
        # visibility scoping now constructs the child `ShelfFilter` first
        # (its `apply_sync` runs during `_derive_related_visibility_*`),
        # so the calls list interleaves child + parent constructions; the
        # test selects the parent (Branch-model) call by queryset model
        # rather than assuming a position.
        captured.setdefault("calls", []).append(kwargs.get("queryset"))
        real_init(self, *args, **kwargs)

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves", queryset=explicit_qs)

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    FilterSet.__init__ = spy_init
    try:
        # Slice 2 strips related-branch keys from the form-data dict
        # before form validation (`shelves` is owned by
        # `_apply_related_constraints`, not the parent's form), so
        # `apply_sync` now returns normally. The contract this test
        # pins is unchanged: the constructor's `queryset=` kwarg must
        # carry the `<rel>__in=<intersected>` clause already baked in.
        # See `docs/builder/bld-slice-2-factories.md` for the
        # carry-forward rationale from Slice 1's spy-test fragility.
        BranchFilter.apply_sync(
            {"shelves": {"code": "active"}},
            library_models.Branch.objects.all(),
            _make_info(),
        )
    finally:
        FilterSet.__init__ = real_init

    # Select the parent (Branch-model) construction; child ShelfFilter
    # constructions from the visibility-scoping pass also land in `calls`.
    parent_querysets = [
        qs for qs in captured["calls"] if qs is not None and qs.model is library_models.Branch
    ]
    assert parent_querysets, "BranchFilter was never constructed with a queryset kwarg"
    parent_queryset = parent_querysets[0]
    # The constrained queryset reached `BranchFilter.__init__` BEFORE the
    # filterset was constructed; the SQL carries the parent-pk
    # `pk__in=<subquery over <rel>__in>` restriction that
    # `_apply_related_constraints` baked in.
    sql = str(parent_queryset.query).lower()
    assert "library_shelf" in sql
    assert "active" in sql


# ---------------------------------------------------------------------------
# Apply pipeline - filter_queryset tree-form logic (Slice 4a)
#
# The scalar ``and``/``or`` union/intersection contracts and the nested
# malformed-subbranch validation contract moved to the live library API suite
# (``examples/fakeshop/test_query/test_library_api.py``) per feedback3.md: those
# behaviors are reachable through the real ``BranchFilter``/``PatronFilter`` over
# ``/graphql/``, where the replacements also prove GraphQL input coercion, root
# visibility, and the HTTP error/data envelope.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Round-5 coverage: helper / config / async / depth-cap branches
# ---------------------------------------------------------------------------


def test_get_filters_skips_none_target_related_filter():
    """A ``RelatedFilter(None, ...)`` placeholder expands to nothing.

    ``_expand_related_filter`` returns an empty mapping when the target
    filterset is unresolved (``None``), so no ``<rel>__<lookup>`` keys
    leak into ``get_filters()``.
    """

    class PlaceholderFilter(FilterSet):
        rel = RelatedFilter(None, field_name="branch")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    filters = PlaceholderFilter.get_filters()
    assert not any(name.startswith("rel__") for name in filters)


def test_normalize_input_returns_empty_for_non_dataclass_non_dict():
    """A value that is neither a dict nor a dataclass normalizes to ``{}``."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._normalize_input(object()) == {}


def test_operator_bag_items_walks_lookup_attr_dict():
    """``_operator_bag_items`` walks a dict whose keys are all lookup attrs.

    The old dict rejection routed a dict-shaped bag down the scalar
    branch, where the range-patch ``data.update(...)`` splatted its keys
    into the form data as unknown fields the form silently ignores - an
    explicit filter input applying NO filtering for direct ``apply_*``
    callers. A dict whose keys are all recognized lookup attrs is now
    walked like a dataclass bag.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact", "icontains"]}

    assert CategoryFilter._operator_bag_items({"exact": "x"}) == [("exact", "x")]
    assert CategoryFilter._operator_bag_items({"i_contains": "y"}) == [("i_contains", "y")]


def test_operator_bag_items_returns_none_for_non_lookup_key_dict():
    """A multi-key filter VALUE (e.g. a range ``{start, end}``) is not a bag.

    ``start`` / ``end`` are not lookup attrs, so the dict must fall
    through to the scalar branch where ``normalize_input_value`` produces
    the positional ``{<field>_0, <field>_1}`` range patch. Treating it as
    a bag would emit bogus ``<field>__start`` / ``<field>__end`` keys.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._operator_bag_items({"start": 1, "end": 5}) is None
    # A mixed dict (some lookup attrs, some not) is also not a bag - all
    # keys must be lookup attrs.
    assert CategoryFilter._operator_bag_items({"exact": "x", "start": 1}) is None


def test_operator_bag_items_still_returns_none_for_scalars():
    """Scalar and sequence values are not operator bags."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._operator_bag_items("x") is None
    assert CategoryFilter._operator_bag_items(["x"]) is None


def test_extract_branch_value_returns_none_for_none_input():
    """``_extract_branch_value(None, ...)`` short-circuits to ``None``."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._extract_branch_value(None, "shelves") is None


def test_request_from_info_raises_when_context_missing():
    """``_request_from_info`` raises when ``info.context`` is ``None``."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    class _Info:
        context = None

    with pytest.raises(ConfigurationError) as excinfo:
        CategoryFilter._request_from_info(_Info())
    assert "info.context" in str(excinfo.value)


def test_run_permission_checks_short_circuits_on_none_and_unset():
    """A ``None`` / ``UNSET`` input is a no-op (no gate fires, no crash)."""
    import strawberry

    fired: list[str] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, request):
            fired.append("name")

    CategoryFilter._run_permission_checks(None, request=HttpRequest())
    CategoryFilter._run_permission_checks(strawberry.UNSET, request=HttpRequest())
    assert fired == []


@pytest.mark.django_db
def test_check_permissions_walks_explicit_requested_fields():
    """The explicit-``requested_fields`` path fires each named gate directly."""
    fired: list[str] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, request):
            fired.append("name")

    instance = CategoryFilter(data={}, queryset=Category.objects.all())
    instance.check_permissions(HttpRequest(), requested_fields={"name", "unknown_field"})
    # Only the declared gate fires; the unknown field has no ``check_*`` method.
    assert fired == ["name"]


def test_evaluate_logic_tree_caps_recursion_depth():
    """``_evaluate_logic_tree`` raises past ``_MAX_LOGIC_DEPTH``.

    The round-4 depth guard is independent of the ``_run_permission_checks``
    cap; this pins the ``_evaluate_logic_tree`` / ``_q_for_branch`` arm.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError) as excinfo:
        CategoryFilter._evaluate_logic_tree(
            Category.objects.all(),
            {"and": [{"name": "x"}]},
            _depth=CategoryFilter._MAX_LOGIC_DEPTH + 1,
        )
    assert "_MAX_LOGIC_DEPTH" in str(excinfo.value)


@pytest.mark.django_db
def test_evaluate_logic_tree_skips_inactive_or_arms():
    """``or: [real, None|UNSET]`` must equal ``or: [real]``, not widen to all rows.

    ``_collect_nested_visibility_querysets_async`` already skips inactive
    children; ``_evaluate_logic_tree`` must do the same. An inactive arm under
    ``or`` previously materialized as ``pk__in=<full qs>`` (match-all) and
    silently defeated every real sibling arm. GraphQL rejects null list
    elements (``[BranchFilterInputType!]``), so this is an ``apply_*`` dict /
    direct-call contract pin rather than a live ``/graphql`` case.
    """
    Category.objects.create(name="alpha")
    Category.objects.create(name="beta")

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact", "icontains"]}

    baseline = CategoryFilter.apply_sync(
        {"or_": [{"name": {"exact": "alpha"}}]},
        Category.objects.all(),
        _make_info(),
    )
    assert sorted(baseline.values_list("name", flat=True)) == ["alpha"]

    for inactive in (None, strawberry.UNSET):
        mixed = CategoryFilter.apply_sync(
            {"or_": [{"name": {"exact": "alpha"}}, inactive]},
            Category.objects.all(),
            _make_info(),
        )
        assert sorted(mixed.values_list("name", flat=True)) == ["alpha"], inactive


def test_evaluate_logic_tree_and_direct_branch_treat_inactive_values_as_identity():
    """Inactive AND arms and direct branch calls return the identity query."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    queryset = Category.objects.all()
    assert CategoryFilter._evaluate_logic_tree(queryset, {"and": [None]}) == Q()
    assert CategoryFilter._q_for_branch(queryset, strawberry.UNSET) == Q()


def test_collect_nested_visibility_querysets_async_caps_recursion_depth():
    """``_collect_nested_visibility_querysets_async`` raises past ``_MAX_LOGIC_DEPTH``.

    Third site of the shared ``_raise_logic_depth_exceeded`` helper -- the async
    pre-walker enforces the same depth cap as ``_run_permission_checks`` and
    ``_evaluate_logic_tree``, surfacing the identical typed error rather than
    silently bottoming out into a Python ``RecursionError``.
    """
    import asyncio

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError) as excinfo:
        asyncio.run(
            CategoryFilter._collect_nested_visibility_querysets_async(
                {"and_": [{"name": "x"}]},
                _make_info(),
                _depth=CategoryFilter._MAX_LOGIC_DEPTH + 1,
            ),
        )
    assert "_MAX_LOGIC_DEPTH" in str(excinfo.value)
    # Pin the qualname-prefixed shape that the shared helper preserves.
    assert "CategoryFilter" in str(excinfo.value)


def test_target_type_for_related_filter_returns_none_without_child_model():
    """A ``RelatedFilter`` whose filterset has no model resolves to ``None``."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._target_type_for_related_filter(RelatedFilter(None)) is None


def test_is_own_pk_under_relay_owner_false_for_relation_field():
    """An ``is_relation`` field never takes the own-PK Relay branch."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    # Bind an owner directly on the throwaway local class so the early
    # ``owner is None`` guard is passed; ``registry.clear()`` (autouse
    # teardown) strips the binding afterward.
    BookFilter._owner_definition = object()
    relation_field = library_models.Book._meta.get_field("genres")
    assert BookFilter._is_own_pk_under_relay_owner(relation_field) is False


def test_is_own_pk_under_relay_owner_false_when_model_missing():
    """A non-relation field with a model-less filterset returns ``False``."""
    from types import SimpleNamespace

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    CategoryFilter._owner_definition = object()
    # The local class is discarded after the test, so nulling its own
    # ``_meta.model`` does not leak into other tests.
    CategoryFilter._meta.model = None
    non_relation = SimpleNamespace(is_relation=False)
    assert CategoryFilter._is_own_pk_under_relay_owner(non_relation) is False


def test_filter_for_lookup_rejects_unsupported_lookup_on_relay_owner_pk():
    """Spec-021 H1: an explicit unsupported lookup on a Relay owner's PK raises.

    The ``get_fields`` ``"__all__"`` narrowing only covers the generated
    surface; an explicit ``Meta.fields`` list naming ``range`` / ``gt`` / a
    pattern lookup still reaches ``filter_for_lookup``. A Relay node's wire id
    has no ordering / pattern semantics, so those lookups are rejected with a
    ``ConfigurationError`` (naming the lookup) instead of silently becoming a
    GlobalID-shaped ``String``. Only ``exact`` / ``in`` / ``isnull`` are allowed.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(CategoryType, CategoryType.__django_strawberry_definition__)

    class _Owner:
        origin = CategoryType

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    CategoryFilter._owner_definition = _Owner()
    pk_field = Category._meta.pk

    with pytest.raises(ConfigurationError) as excinfo:
        CategoryFilter.filter_for_lookup(pk_field, "range")
    assert "range" in str(excinfo.value)
    # The same rejection holds via the per-field entry point (which routes
    # through ``filter_for_lookup`` in ``super().filter_for_field``).
    with pytest.raises(ConfigurationError):
        CategoryFilter.filter_for_field(pk_field, "id", "range")

    # The three supported lookups resolve without raising.
    exact_class, _ = CategoryFilter.filter_for_lookup(pk_field, "exact")
    assert exact_class is GlobalIDFilter
    in_class, _ = CategoryFilter.filter_for_lookup(pk_field, "in")
    assert in_class is GlobalIDMultipleChoiceFilter
    isnull_class, _ = CategoryFilter.filter_for_lookup(pk_field, "isnull")
    assert isnull_class is not GlobalIDFilter


def test_resolve_relation_target_type_uses_owner_related_target_for():
    """When the owner resolves the relation, its target type is returned."""
    from types import SimpleNamespace

    target_type = type("ResolvedTargetType", (), {})

    class _Owner:
        def related_target_for(self, field_name):
            # The pair's first member is a ``DjangoTypeDefinition``, whose
            # registered ``DjangoType`` class is ``.origin`` -- NOT ``.type``
            # / ``.type_cls`` (the H3 bug read those nonexistent attrs and
            # dropped every owner-aware resolution to the registry fallback).
            return (SimpleNamespace(origin=target_type), object())

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    CategoryFilter._owner_definition = _Owner()
    relation_field = SimpleNamespace(is_relation=True, related_model=Category)
    resolved = CategoryFilter._resolve_relation_target_type(relation_field, "category")
    assert resolved is target_type


def test_resolve_relation_target_type_returns_none_without_related_model():
    """A relation field with no ``related_model`` and no owner resolves to ``None``."""
    from types import SimpleNamespace

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    field = SimpleNamespace(is_relation=True, related_model=None)
    assert CategoryFilter._resolve_relation_target_type(field, None) is None


@pytest.mark.django_db
def test_apply_related_constraints_skips_branch_without_qs_or_explicit():
    """An active branch with neither child qs nor explicit qs is skipped."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        # No explicit ``queryset=`` on the RelatedFilter.
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    parent_qs = library_models.Branch.objects.all()
    # Active ``shelves`` branch, but the child-qs map is empty AND the
    # RelatedFilter has no explicit queryset -> the branch is skipped.
    constrained = BranchFilter._apply_related_constraints(
        {"shelves": {"code": "x"}},
        parent_qs,
        {},
    )
    assert "shelves__in" not in str(constrained.query)


@pytest.mark.django_db
def test_apply_async_filters_against_scalar_input():
    """``apply_async`` builds the filtered queryset (no related branches)."""
    import asyncio

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    qs = asyncio.run(
        CategoryFilter.apply_async({"name": "alpha"}, Category.objects.all(), _make_info()),
    )
    sql = str(qs.query).lower()
    assert "alpha" in sql


@pytest.mark.django_db
def test_derive_related_visibility_querysets_async_scopes_active_branch():
    """The async visibility derive runs the target ``get_queryset`` per active branch."""
    import asyncio

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    result = asyncio.run(
        BranchFilter._derive_related_visibility_querysets_async(
            {"shelves": {"code": "A"}},
            _make_info(),
        ),
    )
    assert "shelves" in result
    assert result["shelves"].model is library_models.Shelf


def test_normalize_input_operator_bag_passes_unmatched_lookup_through():
    """An operator-bag lookup with no backing filter is written verbatim."""
    import dataclasses

    @dataclasses.dataclass
    class _NameBag:
        gt: Any = None

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    # ``gt`` is not a declared lookup for ``name`` -> no filter instance ->
    # the value lands under the raw ``name__gt`` form key.
    data = CategoryFilter._normalize_input({"name": _NameBag(gt=5)})
    assert data == {"name__gt": 5}


@pytest.mark.django_db
def test_normalize_input_operator_bag_dict_value_merges_into_form_data():
    """A dict-valued operator-bag lookup is merged into the form data via ``update``.

    Exercises the operator-bag ``isinstance(normalized, dict)`` ->
    ``data.update(normalized)`` branch. The framework ``RangeFilter``
    declared at a ``<field>__range`` name groups under the ``<field>``
    operator bag; its ``{start, end}`` value normalizes to the positional
    ``<key>_0`` / ``<key>_1`` patch that the loop merges in. (django-filter's
    own ``range`` lookup instead produces a CSV ``BaseRangeFilter`` whose
    value is a *list*, not a dict -- see
    ``test_convert_filter_to_input_annotation_csv_in_filter_is_list`` -- so
    the framework ``RangeFilter`` is the primitive that drives this
    dict-merge path.)
    """
    import dataclasses

    from django_strawberry_framework.filters import RangeFilter

    @dataclasses.dataclass
    class _FinesBag:
        range: Any = None

    class PatronFilter(FilterSet):
        lifetime_fines_cents__range = RangeFilter(
            field_name="lifetime_fines_cents",
            lookup_expr="range",
        )

        class Meta:
            model = library_models.Patron
            fields = []

    data = PatronFilter._normalize_input(
        {"lifetime_fines_cents": _FinesBag(range={"start": 1, "end": 5})},
    )
    # The dict-valued normalization result is merged key-by-key.
    assert data == {"lifetime_fines_cents__range_0": 1, "lifetime_fines_cents__range_1": 5}


@pytest.mark.django_db
def test_normalize_input_operator_bag_exact_resolves_explicit_suffixed_key():
    """An ``exact`` operator-bag lookup resolves a filter declared under ``<field>__exact``.

    ``exact`` is the only lookup whose form key (the bare ``base_path``) can
    differ from its ``<base_path>__exact`` suffixed key, so it is the one case
    where ``_normalize_input`` probes a second key. ``django-filter`` strips the
    ``__exact`` suffix from *generated* exact filters (they register under the
    bare field name), but a filter declared explicitly under the
    ``<field>__exact`` attribute name is merged into ``get_filters()`` under that
    literal key (``BaseFilterSet.get_filters``'s trailing
    ``filters.update(cls.declared_filters)``). With no bare-``name`` autogen
    filter (``Meta.fields = []``), ``all_filters`` carries only ``name__exact``,
    so the bare-key probe misses and the suffixed-key fallback must resolve the
    declared ``CharFilter`` -- the genuine two-key-differ path.
    """
    import dataclasses

    import django_filters

    @dataclasses.dataclass
    class _NameBag:
        exact: Any = None

    class WeirdCategoryFilter(FilterSet):
        name__exact = django_filters.CharFilter(field_name="name", lookup_expr="exact")

        class Meta:
            model = Category
            fields = []

    assert list(WeirdCategoryFilter.get_filters()) == ["name__exact"]
    # ``base_path`` resolves to the bare ``name`` (from the field python attr),
    # ``form_key`` is the bare ``name`` (exact), ``suffixed_key`` is
    # ``name__exact``; the bare probe misses, the suffixed probe resolves the
    # declared filter and normalizes to the bare ``name`` form-data key.
    data = WeirdCategoryFilter._normalize_input({"name": _NameBag(exact="foo")})
    assert data == {"name": "foo"}


@pytest.mark.django_db
def test_normalize_input_top_level_range_filter_merges_positional_keys():
    """A top-level ``RangeFilter`` attribute expands to positional keys."""
    from django_strawberry_framework.filters import RangeFilter

    class FinesRangeFilter(FilterSet):
        fines = RangeFilter(field_name="lifetime_fines_cents")

        class Meta:
            model = library_models.Patron
            fields = {"id": ["exact"]}

    data = FinesRangeFilter._normalize_input({"fines": {"start": 1, "end": 5}})
    assert data == {"fines_0": 1, "fines_1": 5}


@pytest.mark.django_db
def test_check_permissions_falls_back_to_active_input_when_no_requested_fields():
    """``check_permissions`` with no explicit set routes through the active-input path."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    instance = CategoryFilter(data={}, queryset=Category.objects.all())
    # No ``requested_fields`` -> the active-input ``_run_permission_checks``
    # branch runs (and is a no-op for a gate-less filterset).
    instance.check_permissions(HttpRequest())


def test_derive_related_visibility_querysets_async_raises_for_unregistered_target():
    """The async derive raises for an active branch whose target type is unregistered.

    The old contract skipped the branch (``result == {}``), which dropped
    the constraint entirely: a filter the consumer supplied input for
    silently returned unfiltered parent rows. Both derive methods route
    through ``_iter_visibility_steps``, which now raises
    ``ConfigurationError`` for the active-but-unresolvable branch.
    """
    import asyncio

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # No ShelfType registered -> ``_target_type_for_related_filter`` is
    # ``None`` -> the active branch raises instead of silently dropping.
    with pytest.raises(ConfigurationError) as excinfo:
        asyncio.run(
            BranchFilter._derive_related_visibility_querysets_async(
                {"shelves": {"code": "A"}},
                _make_info(),
            ),
        )
    assert "no DjangoType is registered" in str(excinfo.value)


@pytest.mark.django_db
def test_iter_visibility_steps_yields_pre_await_tuple_for_active_branches():
    """``_iter_visibility_steps`` yields the shared pre-await state both derive methods consume.

    Pins the DRY-0_0_7 consolidation: both
    ``_derive_related_visibility_querysets_sync`` and
    ``_derive_related_visibility_querysets_async`` route through the
    single ``_iter_visibility_steps`` classmethod, so the helper's
    five-tuple shape (``field_name, target_type, child_filterset,
    child_input, child_base``) is the load-bearing contract. Branches
    missing ``target_type`` or ``child_filterset`` raise (see the
    sibling fail-loud test) so the derive methods carry only the two
    awaits / calls per step.
    """

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    steps = list(
        BranchFilter._iter_visibility_steps({"shelves": {"code": "A"}}),
    )
    assert len(steps) == 1
    field_name, target_type, child_filterset, child_input, child_base = steps[0]
    assert field_name == "shelves"
    assert target_type is ShelfType
    assert child_filterset is ShelfFilter
    assert child_input == {"code": "A"}
    assert child_base.model is library_models.Shelf


@pytest.mark.django_db
def test_iter_visibility_steps_raises_for_branch_without_resolved_target():
    """``_iter_visibility_steps`` fails loud for an active-but-unresolvable branch.

    The guard lives in the helper so each derive method stays a tight
    loop carrying only the two awaits / calls per step. An active branch
    (the consumer supplied input for it) whose ``target_type`` cannot be
    resolved raises ``ConfigurationError`` - the old skip contract
    dropped the constraint and silently returned unfiltered parent rows
    (mirrors the sibling async test, but pins the helper directly).
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # No ShelfType registered -> ``_target_type_for_related_filter`` is
    # ``None`` -> the helper raises before yielding.
    with pytest.raises(ConfigurationError) as excinfo:
        list(BranchFilter._iter_visibility_steps({"shelves": {"code": "A"}}))
    msg = str(excinfo.value)
    assert "'shelves'" in msg
    assert "no DjangoType is registered" in msg


@pytest.mark.django_db
def test_apply_async_nested_or_branch_with_async_get_queryset_does_not_raise_sync_misuse():
    """``apply_async`` pre-derives nested visibility so an async-only ``get_queryset`` hook
    does not raise ``SyncMisuseError`` mid-``.qs`` from a nested ``or_`` branch.

    Before the Medium-#2 fix, ``_q_for_branch`` called
    ``_derive_related_visibility_querysets_sync`` unconditionally, which
    invokes ``apply_type_visibility_sync`` on the target type. A target whose
    ``get_queryset`` is ``async def`` returns a coroutine that
    ``apply_type_visibility_sync`` flags as ``SyncMisuseError``. The pre-walk
    in ``apply_async`` (``_collect_nested_visibility_querysets_async``)
    now awaits every nested branch's visibility BEFORE the ``.qs`` read,
    and ``_q_for_branch`` consults the stash keyed by ``id(child_input)``
    instead of re-deriving sync.
    """
    import asyncio

    from asgiref.sync import sync_to_async

    alpha = library_models.Branch.objects.create(name="alpha")
    library_models.Shelf.objects.create(branch=alpha, code="match")
    beta = library_models.Branch.objects.create(name="beta")
    library_models.Shelf.objects.create(branch=beta, code="other")

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

        @classmethod
        async def get_queryset(cls, queryset, info, **kwargs):
            # Async-only hook: pre-merge ``_q_for_branch`` would raise
            # ``SyncMisuseError`` when its sync derive walked into this.
            return await sync_to_async(lambda: queryset)()

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    qs = asyncio.run(
        BranchFilter.apply_async(
            {"or_": [{"shelves": {"code": "match"}}]},
            library_models.Branch.objects.all(),
            _make_info(),
        ),
    )
    # The async-only ``get_queryset`` ran, the nested branch constrained
    # the parent, and only ``alpha`` (which owns the matching shelf) leaks
    # through. Before the fix, ``.qs`` would raise ``SyncMisuseError``
    # before this assertion could run.
    assert list(qs.values_list("name", flat=True)) == ["alpha"]


@pytest.mark.django_db
def test_apply_async_runs_permission_checks_off_event_loop_thread():
    """``apply_async`` routes finalize (incl. permission checks) through
    ``run_in_one_sync_boundary`` so a blocking ``check_*_permission`` hook
    does not block the event loop.

    Asserts the permission method observed a thread ident DIFFERENT from
    the event-loop thread ident -- which is what
    ``sync_to_async(thread_sensitive=True)`` guarantees. Before the
    Medium-#1 fix, ``_run_permission_checks`` ran inline on the event-loop
    thread, so the two ident reads would have matched.
    """
    import asyncio
    import threading

    captured: dict[str, int] = {}

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, request):
            captured["permission_thread"] = threading.get_ident()

    async def _run() -> int:
        captured["event_loop_thread"] = threading.get_ident()
        await CategoryFilter.apply_async(
            {"name": "alpha"},
            Category.objects.all(),
            _make_info(),
        )
        return captured["event_loop_thread"]

    event_loop_thread = asyncio.run(_run())
    assert captured["permission_thread"] != event_loop_thread


@pytest.mark.django_db
def test_apply_async_collect_nested_visibility_querysets_pre_derives_or_branch():
    """``_collect_nested_visibility_querysets_async`` keys the awaited map on
    ``id(child_input)`` for every nested ``or`` arm.

    Unit-level pin on the new helper -- given an ``or_`` input shape with
    one inner branch carrying an active ``RelatedFilter``, the helper
    returns a map whose only key is ``id`` of that nested child dict, and
    whose value carries the ``shelves`` queryset derived via the async
    path.
    """
    import asyncio

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    inner = {"shelves": {"code": "A"}}
    result = asyncio.run(
        BranchFilter._collect_nested_visibility_querysets_async(
            {"or_": [inner]},
            _make_info(),
        ),
    )
    assert id(inner) in result
    assert "shelves" in result[id(inner)]
    assert result[id(inner)]["shelves"].model is library_models.Shelf
    # Silence the unused ShelfType registration (registry isolation handles it).
    assert ShelfType is not None


# ---------------------------------------------------------------------------
# Permission gate dispatch keys on the field, not the lookup (H2)
# ---------------------------------------------------------------------------


def test_active_permission_field_paths_covers_input_shapes():
    """``_active_permission_field_paths`` resolves source paths, skips the rest (H2)."""
    import dataclasses

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # None / UNSET / non-(dict-or-dataclass) -> empty.
    assert BranchFilter._active_permission_field_paths(None) == []
    assert BranchFilter._active_permission_field_paths(strawberry.UNSET) == []
    assert BranchFilter._active_permission_field_paths(42) == []

    @dataclasses.dataclass
    class _Input:
        name: Any = None
        shelves: Any = None
        and_: Any = None

    # Active scalar resolves to its source path; the related branch and the
    # logical-operator key are excluded (gated elsewhere); ``None`` skipped.
    paths = BranchFilter._active_permission_field_paths(
        _Input(name="x", shelves={"code": "y"}, and_=[{"name": "z"}]),
    )
    assert paths == ["name"]
    # A raw dict resolves via the form-key fallback.
    assert BranchFilter._active_permission_field_paths({"name": "x"}) == ["name"]


# ---------------------------------------------------------------------------
# Per-field ``Meta.fields = {"<field>": "__all__"}`` lookup expansion
# ---------------------------------------------------------------------------


def test_lookups_for_field_returns_concrete_lookups_and_excludes_transforms():
    """`_lookups_for_field` returns concrete lookups and drops Transforms."""
    name_field = Category._meta.get_field("name")  # TextField
    date_field = Category._meta.get_field("created_date")  # DateTimeField

    name_lookups = _lookups_for_field(name_field)
    assert {
        "exact",
        "icontains",
        "gt",
        "lt",
        "in",
        "range",
        "isnull",
        "startswith",
    } <= set(name_lookups)

    date_lookups = _lookups_for_field(date_field)
    assert {"exact", "gt", "lt"} <= set(date_lookups)
    # Temporal transforms (year / month / date / time / ...) are excluded:
    # the per-field operator-bag input shape has no nested-transform form.
    assert {
        "year",
        "month",
        "day",
        "date",
        "time",
        "week",
    }.isdisjoint(date_lookups)

    # A missing field resolves to an empty list (defensive).
    assert _lookups_for_field(None) == []


# ---------------------------------------------------------------------
# DRY consolidation pins (dry-0_0_7): ``FilterSet._iter_input_items``
# ---------------------------------------------------------------------
#
# Three sites (``_normalize_input``, ``_operator_bag_items``,
# ``_active_permission_field_paths``) route through a single shared
# staticmethod that walks dicts AND Strawberry-input dataclasses into
# ``(name, value)`` pairs. The helper returns ``None`` for non-walkable
# shapes and ``[]`` for walkable-but-empty inputs. Site 2
# (``_operator_bag_items``) keeps its scalar/collection/dict pre-rejection
# above the helper call so operator bags remain dataclass-only at the
# call boundary while sites 1 / 3 accept both dict and dataclass shapes.


def test_iter_input_items_returns_pairs_for_plain_dict():
    """Dict input walks to ``list(input.items())`` verbatim."""

    assert FilterSet._iter_input_items({"name": "x", "id": 1}) == [("name", "x"), ("id", 1)]


def test_iter_input_items_returns_empty_list_for_empty_dict():
    """Walkable-but-empty dict returns ``[]`` (sentinel-distinct from None)."""

    assert FilterSet._iter_input_items({}) == []


def test_iter_input_items_walks_strawberry_input_dataclass_via_attribute_sniff():
    """``__dataclass_fields__`` sniff unpacks Strawberry-input shapes."""

    @strawberry.input
    class FooInput:
        name: str = "x"
        count: int = 3

    items = FilterSet._iter_input_items(FooInput(name="y", count=7))
    assert items == [("name", "y"), ("count", 7)]


def test_iter_input_items_returns_none_for_non_walkable_shapes():
    """Non-dict / non-dataclass shapes return ``None`` (not ``[]``)."""

    assert FilterSet._iter_input_items(object()) is None
    assert FilterSet._iter_input_items("scalar") is None
    assert FilterSet._iter_input_items(42) is None
    assert FilterSet._iter_input_items([1, 2, 3]) is None
    assert FilterSet._iter_input_items(None) is None


# ---------------------------------------------------------------------------
# Async-path coverage. These branches live in the apply_async pipeline
# (the nested-visibility pre-walk and the _q_for_branch stash-miss
# fallback). The fakeshop live HTTP suites drive Django's SYNC test
# Client -> sync views -> apply_sync, so per
# examples/fakeshop/test_query/README.md these lines are genuinely
# unreachable from a live /graphql/ request and are earned here as unit
# tests (the README's documented fallback for live-unreachable code).
# ---------------------------------------------------------------------------


def test_collect_nested_visibility_querysets_async_returns_empty_for_none_input():
    """``_collect_nested_visibility_querysets_async(None, ...)`` short-circuits to ``{}``.

    The ``input_value is None or input_value is UNSET`` guard returns the
    empty map before any branch walk -- the apply_async pre-pass over a
    branch with no nested logical input does no work.
    """
    import asyncio

    class BranchFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    result = asyncio.run(
        BranchFilter._collect_nested_visibility_querysets_async(None, _make_info()),
    )
    assert result == {}


def test_collect_nested_visibility_querysets_async_skips_none_child_branch():
    """A ``None`` child inside a logical branch is skipped without a derive.

    ``{"or": [None]}`` yields a single ``None`` child; the child loop's
    ``if child_input is None or child_input is UNSET: continue`` skips it, so
    no visibility derive runs and the result stays empty.
    """
    import asyncio

    class BranchFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    result = asyncio.run(
        BranchFilter._collect_nested_visibility_querysets_async({"or": [None]}, _make_info()),
    )
    assert result == {}


@pytest.mark.django_db
def test_q_for_branch_falls_back_to_sync_derive_on_stash_miss():
    """``_q_for_branch`` with a present-but-missing stash uses the sync-derive fallback.

    Under ``apply_async`` the nested visibility map is pre-derived and threaded
    through ``_nested_qs_by_branch_id`` keyed by ``id(child_input)``. A consumer
    who short-circuits past the async pre-pass (modeled here by an empty stash
    dict, so ``.get(id(child_input))`` misses) still gets a correct result via
    the defensive sync-derive fallback rather than a ``None`` map.
    """
    from django.db.models import Q

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    child_input = {"shelves": {"code": "A"}}
    q = BranchFilter._q_for_branch(
        library_models.Branch.objects.all(),
        child_input,
        info=_make_info(),
        _nested_qs_by_branch_id={},  # present but empty -> stash miss -> sync fallback
    )
    assert isinstance(q, Q)


def test_collect_related_declarations_honors_base_tombstone():
    """A direct base's non-related declaration removes a later inherited candidate."""

    class Declaration:
        def _bind_owner(self, owner):
            raise AssertionError(f"removed declaration was bound to {owner.__name__}")

    declaration = Declaration()

    class Base:
        related_declarations = OrderedDict(probe=declaration)
        all_declarations = {"probe": object()}

    class Child(Base):
        pass

    collected = collect_related_declarations(
        Child,
        (Base,),
        own_items=(),
        declaration_type=Declaration,
        collection_attr="related_declarations",
        inherit_from_bases=True,
        base_declarations_attr="all_declarations",
    )

    assert collected == OrderedDict()


# ---------------------------------------------------------------------------
# Report Defect 3: related-visibility derivation preserves the parent DB alias
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_iter_visibility_steps_threads_parent_db_alias():
    """The child visibility base is pinned to the parent request's DB alias.

    The cascade-permission path builds its base with
    ``._default_manager.using(queryset.db).all()``; the related-visibility path
    must match so an alias-sensitive ``get_queryset`` hook runs against the
    parent's shard rather than the default alias (report Defect 3).
    """

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    input_value = {"shelves": {"code": {"exact": "AAA"}}}
    aliased = list(BranchFilter._iter_visibility_steps(input_value, "shard_b"))
    assert aliased and aliased[0][4].db == "shard_b"
    # No alias threaded -> the router default stays in place (single-DB case).
    default = list(BranchFilter._iter_visibility_steps(input_value))
    assert default and default[0][4].db == "default"


@pytest.mark.django_db
def test_related_visibility_hook_receives_parent_db_alias():
    """The child ``get_queryset`` visibility hook runs against the parent's alias."""
    seen: list[str] = []

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

        @classmethod
        def get_queryset(cls, queryset, info):
            seen.append(queryset.db)
            return queryset

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    BranchFilter._derive_related_visibility_querysets_sync(
        {"shelves": {"code": {"exact": "AAA"}}},
        _make_info(),
        parent_db="shard_b",
    )
    assert seen == ["shard_b"]


# ---------------------------------------------------------------------------
# Report Defect 5: shared traversal budget caps related-derive recursion
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_apply_sync_caps_related_recursion_depth():
    """``apply_sync`` raises a typed error past the shared depth budget (Defect 5).

    The visibility derivation re-enters ``apply_sync`` once per related hop, so a
    self-referential ``RelatedFilter`` would recurse input-deep; the ``_depth``
    guard converts the runaway into a ``ConfigurationError`` at the source.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError) as excinfo:
        CategoryFilter.apply_sync(
            {"name": "x"},
            Category.objects.all(),
            _make_info(),
            _depth=CategoryFilter._MAX_LOGIC_DEPTH + 1,
        )
    assert "_MAX_LOGIC_DEPTH" in str(excinfo.value)


@pytest.mark.django_db
def test_apply_async_caps_related_recursion_depth():
    """Async sibling of ``test_apply_sync_caps_related_recursion_depth``."""
    import asyncio

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError) as excinfo:
        asyncio.run(
            CategoryFilter.apply_async(
                {"name": "x"},
                Category.objects.all(),
                _make_info(),
                _depth=CategoryFilter._MAX_LOGIC_DEPTH + 1,
            ),
        )
    assert "_MAX_LOGIC_DEPTH" in str(excinfo.value)


@pytest.mark.django_db
def test_apply_async_caps_related_recursion_nested_under_logical_branches():
    """The async nested pre-walk shares the related-recursion depth budget.

    A logical branch wrapped around the real self-referential
    ``CardFilter.dependencies`` relation re-enters ``apply_async`` from the
    pre-walk. The caller's depth must reach each nested pre-walk so this mixed
    shape raises the typed cap error instead of overflowing Python's stack.
    """
    import asyncio

    class CardType(DjangoType):
        class Meta:
            model = kanban_models.Card
            fields = ("id", "number")

    deep: dict[str, Any] = {"number": {"exact": 21}}
    for _ in range(kanban_filters.CardFilter._MAX_LOGIC_DEPTH + 2):
        deep = {"or_": [{"dependencies": deep}]}

    with pytest.raises(ConfigurationError) as excinfo:
        asyncio.run(
            kanban_filters.CardFilter.apply_async(
                deep,
                kanban_models.Card.objects.all(),
                _make_info(),
            ),
        )
    assert "_MAX_LOGIC_DEPTH" in str(excinfo.value)
    assert CardType is not None


# ---------------------------------------------------------------------------
# Report Defect 4: malformed logical containers fail loud (no silent identity)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_normalize_input_rejects_malformed_logical_containers():
    """``and`` / ``or`` demand a list; ``not`` demands a single input (Defect 4).

    A mapping supplied where a list is expected is otherwise iterated as its
    string KEYS: the nested clause is never seen, dropping both its gate and its
    predicate (a silent identity-query bypass through the raw ``apply_*`` API).
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError, match="list of filter inputs"):
        CategoryFilter._normalize_input({"or_": {"name": {"exact": "x"}}})
    with pytest.raises(ConfigurationError, match="single filter input"):
        CategoryFilter._normalize_input({"not_": [{"name": {"exact": "x"}}]})


@pytest.mark.django_db
def test_evaluate_logic_tree_rejects_malformed_direct_construction():
    """A directly-constructed malformed logical tree fails loud at query build."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    fs = CategoryFilter(
        data={"or": {"name": {"exact": "x"}}},
        queryset=Category.objects.all(),
    )
    with pytest.raises(ConfigurationError, match="list of filter inputs"):
        _ = fs.qs


def test_validate_logic_branch_shape_accepts_inactive_value():
    """An inactive (``None``) logical value is a no-op, not a shape error (Defect 4)."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    # No raise: ``None`` is filtered as inactive everywhere the branch is read.
    CategoryFilter._validate_logic_branch_shape("and", None)
    CategoryFilter._validate_logic_branch_shape("not", None)


def test_normalize_input_rejects_scalar_logical_elements():
    """A scalar where a filter input belongs is rejected at normalize (Defect 4).

    ``not: "name"``, ``or: ["name"]``, ``and: [42]`` all have the RIGHT container
    but the WRONG element -- a scalar that ``iter_input_items`` cannot walk. Left
    unchecked the branch drops its predicate AND never traverses its ``check_*``
    gate, the same permission + filter bypass as a wrong container one level up.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError, match="must be a mapping or filter-input"):
        CategoryFilter._normalize_input({"not_": "name"})
    with pytest.raises(ConfigurationError, match="must be a mapping or filter-input"):
        CategoryFilter._normalize_input({"or_": ["name"]})
    with pytest.raises(ConfigurationError, match="must be a mapping or filter-input"):
        CategoryFilter._normalize_input({"and_": [42]})


@pytest.mark.django_db
def test_evaluate_logic_tree_rejects_scalar_logical_elements():
    """Scalar logical elements fail loud at query build too (Defect 4, second seam)."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    for tree in ({"not": "name"}, {"or": ["name"]}, {"and": [42]}):
        fs = CategoryFilter(data=tree, queryset=Category.objects.all())
        with pytest.raises(ConfigurationError, match="must be a mapping or filter-input"):
            _ = fs.qs


def test_validate_logic_branch_shape_accepts_inactive_list_element():
    """An inactive (``None``) element inside an ``and`` / ``or`` list is a no-op arm."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    # No raise: ``None`` list arms are skipped downstream, not shape errors.
    CategoryFilter._validate_logic_branch_shape("or", [None, {"name": {"exact": "x"}}])
    CategoryFilter._validate_logic_branch_shape("and", [{"name": {"exact": "x"}}, None])


# ---------------------------------------------------------------------------
# Frozen generation-provenance records
#
# Each generated / declared / replaced / expanded filter instance carries a
# frozen ``FilterGenerationProvenance`` record read through
# ``filter_generation_provenance`` (None = fail closed). These pin the origin,
# the framework-added-distinct bit, expansion inheritance, and deepcopy /
# per-request survival before the LATER candidate-metadata build consumes them.
# ---------------------------------------------------------------------------


def test_generation_provenance_framework_default_for_generated_leaf():
    """A plainly generated CharFilter leaf is ``framework_default``, no distinct."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["icontains"]}

    leaf = BookFilter.get_filters()["title__icontains"]
    record = filter_generation_provenance(leaf)
    # ``BookFilter`` overrides no generation seam, so the capability bit captured
    # at the generation site is ``True``.
    assert record == FilterGenerationProvenance(
        origin="framework_default",
        framework_added_distinct=False,
        expanded_from=(),
        generation_capable=True,
    )


def test_generation_provenance_package_replacement_for_own_pk_global_id():
    """The own-PK GlobalID branch stamps ``package_replacement`` on the new instance."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(CategoryType, CategoryType.__django_strawberry_definition__)

    class _Owner:
        origin = CategoryType

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    CategoryFilter._owner_definition = _Owner()
    pk_field = Category._meta.pk

    resolved = CategoryFilter.filter_for_field(pk_field, "id", "exact")
    assert isinstance(resolved, GlobalIDFilter)
    record = filter_generation_provenance(resolved)
    assert record is not None
    assert record.origin == "package_replacement"
    assert record.framework_added_distinct is False


def test_generation_provenance_package_replacement_for_relay_relation():
    """The Relay-relation branch stamps ``package_replacement`` on the new instance."""

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("genres")
    resolved = BookFilter.filter_for_field(field, "genres")
    assert isinstance(resolved, GlobalIDMultipleChoiceFilter)
    record = filter_generation_provenance(resolved)
    assert record is not None
    assert record.origin == "package_replacement"
    # ``genres`` is an M2M (a many-side hop), so the framework adds distinct.
    assert record.framework_added_distinct is True


def test_generation_provenance_declared_for_consumer_declared_filter():
    """A consumer-declared filter attribute is ``declared``."""
    import django_filters

    class BookFilter(FilterSet):
        title_search = django_filters.CharFilter(field_name="title")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    leaf = BookFilter.get_filters()["title_search"]
    record = filter_generation_provenance(leaf)
    assert record == FilterGenerationProvenance(origin="declared")


def test_generation_provenance_override_generated_for_meta_filter_overrides():
    """A leaf produced through ``Meta.filter_overrides`` is ``override_generated``."""
    import django_filters
    from django.db import models

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}
            # ``Book.title`` is a ``TextField``; key the override on its class so
            # ``try_dbfield`` matches it (the framework mirrors django-filter's
            # own MRO-walked override selection).
            filter_overrides = {
                models.TextField: {"filter_class": django_filters.CharFilter},
            }

    leaf = BookFilter.get_filters()["title"]
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "override_generated"


def test_generation_provenance_framework_added_distinct_for_to_many_path():
    """A generated to-many path leaf records ``framework_added_distinct=True``."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"]}

    leaf = BookFilter.get_filters()["genres__name__icontains"]
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "framework_default"
    assert record.framework_added_distinct is True
    assert leaf.distinct is True


def test_generation_provenance_framework_added_distinct_false_for_to_one_path():
    """A generated to-one path leaf records ``framework_added_distinct=False``."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"shelf__code": ["icontains"]}

    leaf = BookFilter.get_filters()["shelf__code__icontains"]
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.framework_added_distinct is False
    assert leaf.distinct is False


def test_generation_provenance_expanded_leaf_inherits_generated_child_origin():
    """An expanded leaf inherits the child leaf's origin + appends a breadcrumb."""

    class GenreFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"name": ["icontains"]}

    class BookFilter(FilterSet):
        genres = RelatedFilter(GenreFilter, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    leaf = BookFilter.get_filters()["genres__name__icontains"]
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "framework_default"
    assert record.expanded_from == ("name__icontains",)


def test_generation_provenance_expanded_leaf_of_declared_child_stays_declared():
    """Appearing in expansion output does not make a DECLARED child expanded-generated."""
    import django_filters

    class GenreFilter(FilterSet):
        label = django_filters.CharFilter(field_name="name")

        class Meta:
            model = library_models.Genre
            fields = {"name": ["exact"]}

    class BookFilter(FilterSet):
        genres = RelatedFilter(GenreFilter, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    leaf = BookFilter.get_filters()["genres__label"]
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "declared"
    assert record.expanded_from == ("label",)


def test_generation_provenance_expanded_leaf_of_unstamped_child_stays_none():
    """An expanded copy of an UNSTAMPED child leaf inherits no record (fail closed)."""
    import django_filters

    class GenreFilter(FilterSet):
        @classmethod
        def filter_for_field(
            cls,
            field,
            field_name,
            lookup_expr=None,
        ):
            # Returns its OWN object, so the child leaf carries no framework record.
            return django_filters.CharFilter(field_name=field_name)

        class Meta:
            model = library_models.Genre
            fields = {"name": ["icontains"]}

    class BookFilter(FilterSet):
        genres = RelatedFilter(GenreFilter, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    leaf = BookFilter.get_filters()["genres__name__icontains"]
    assert filter_generation_provenance(leaf) is None


def test_generation_provenance_none_for_consumer_overridden_filter_for_field():
    """A consumer ``filter_for_field`` returning its OWN object yields no record."""
    import django_filters

    class OverridingFilter(FilterSet):
        @classmethod
        def filter_for_field(
            cls,
            field,
            field_name,
            lookup_expr=None,
        ):
            return django_filters.CharFilter(field_name=field_name)

        class Meta:
            model = library_models.Book
            fields = {"title": ["icontains"]}

    leaf = OverridingFilter.get_filters()["title__icontains"]
    assert filter_generation_provenance(leaf) is None


def test_generation_provenance_survives_deepcopy_and_per_request_instance():
    """The record survives ``copy.deepcopy`` and the per-request instance filters."""
    import copy

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"], "title": ["exact"]}

    base_leaf = BookFilter.get_filters()["genres__name__icontains"]
    clone = copy.deepcopy(base_leaf)
    clone_record = filter_generation_provenance(clone)
    assert clone_record is not None
    assert clone_record.framework_added_distinct is True

    instance = BookFilter(
        data={},
        queryset=library_models.Book.objects.all(),
        request=None,
    )
    instance_record = filter_generation_provenance(instance.filters["genres__name__icontains"])
    assert instance_record is not None
    assert instance_record.origin == "framework_default"
    assert instance_record.framework_added_distinct is True


def test_generation_provenance_declared_never_restamped_by_later_machinery():
    """A declared filter's record is stamped once and never overwritten."""
    import django_filters

    class BookFilter(FilterSet):
        custom = django_filters.CharFilter(field_name="title")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    declared = BookFilter.declared_filters["custom"]
    first = filter_generation_provenance(declared)
    assert first is not None and first.origin == "declared"

    # Repeated expansion passes must not restamp (same identity preserved).
    BookFilter.get_filters()
    BookFilter.get_filters()
    assert filter_generation_provenance(declared) is first


# ---------------------------------------------------------------------------
# Blocker 1 -- own class-body declaration is an UNCONDITIONAL origin transition
#
# ``FilterSetMetaclass.__new__`` distinguishes an OWN declaration (a
# ``django_filters.Filter`` assigned directly in THIS class body) from an
# INHERITED one. An own declaration transitions to ``origin="declared"`` and
# sheds any generation token REGARDLESS of a borrowed framework stamp, so a
# consumer that deepcopies an eligible generated leaf into a new class body can
# never be re-authorized through the correlated ``EXISTS`` adapter. Inherited
# declarations keep their already-``declared`` record (the ``if provenance is
# None`` fallback only backfills one that somehow lacks a record).
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_blocker1_borrowed_generated_leaf_becomes_declared_and_fails_closed():
    """Blocker 1 (red->green): a borrowed eligible generated leaf fails closed.

    django-filter's declarative machinery lets a consumer deepcopy a filter
    instance obtained from another filterset's ``base_filters`` -- which still
    carries an ``origin="framework_default"`` stamp AND a live generation token --
    and assign it as a class attribute. Before the fix the metaclass preserved the
    framework origin (it stamped ``declared`` only when NO record existed), so the
    candidate builder minted a fresh token and routed the now-consumer declaration
    through the correlated adapter with its ``distinct`` suppressed. The
    declaration-ownership boundary now transitions the own declaration to
    ``declared`` unconditionally and strips the token, so it earns no routable
    candidate row and runs on the OUTER queryset.
    """
    import copy

    from django_strawberry_framework.filters.sets import _GENERATION_TOKEN_ATTR

    # Obtain an ELIGIBLE generated leaf: a framework ``CharFilter`` whose ORM path
    # crosses the reverse-FK ``Book.loans`` to-many hop, carrying
    # ``origin="framework_default"`` and a live generation token.
    class SourceBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

    assert SourceBookFilter._is_generation_capable() is True
    SourceBookFilter.get_filters()
    source_leaf = SourceBookFilter.base_filters["loans__note__icontains"]
    source_record = filter_generation_provenance(source_leaf)
    assert source_record.origin == "framework_default"
    assert source_record.generation_capable is True
    assert getattr(source_leaf, _GENERATION_TOKEN_ATTR, None) is not None

    borrowed = copy.deepcopy(source_leaf)
    # Precondition the fix must correct: the deepcopy still reads as an eligible
    # framework leaf -- origin AND token both survive ``copy.deepcopy``.
    assert filter_generation_provenance(borrowed).origin == "framework_default"
    assert getattr(borrowed, _GENERATION_TOKEN_ATTR, None) is not None

    class DeclaredReuse(FilterSet):
        loans__note__icontains = borrowed

        class Meta:
            model = library_models.Book
            fields = {"title": ["icontains"]}

    own_decl = DeclaredReuse.declared_filters["loans__note__icontains"]
    assert own_decl is borrowed
    # (a) origin transitioned to ``declared`` REGARDLESS of the borrowed stamp.
    assert filter_generation_provenance(own_decl).origin == "declared"
    # (b) the borrowed generation token was stripped from the instance __dict__.
    assert _GENERATION_TOKEN_ATTR not in own_decl.__dict__
    assert getattr(own_decl, _GENERATION_TOKEN_ATTR, None) is None

    # (c) the candidate snapshot yields NO routable row (declared -> no row).
    DeclaredReuse.get_filters()
    snapshot = DeclaredReuse._expansion_snapshot()
    assert "loans__note__icontains" not in snapshot.candidates

    # (d) at request time the leaf runs on the OUTER queryset: no reserved
    # predicate / EXISTS alias is attached, and the original outer invocation
    # (JOIN + framework ``distinct``) yields the matched row.
    matched_pk, _other_pk = _seed_two_books_one_cardio_loan()
    result = DeclaredReuse(
        data={"loans__note__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    ).qs
    assert _reserved_aliases(result) == []
    assert list(result.order_by("id").values_list("pk", flat=True)) == [matched_pk]


def test_blocker1_inherited_declared_filter_retains_declared_record_unchanged():
    """Positive control: an INHERITED declared filter keeps its ``declared`` record.

    A subclass that does not re-declare the filter must not restamp or mangle the
    inherited declaration: it is the SAME instance, and its record (stamped once by
    the base class's metaclass run) is retained untouched.
    """
    import django_filters

    class BaseDeclaredFilter(FilterSet):
        title_search = django_filters.CharFilter(field_name="title")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    base_decl = BaseDeclaredFilter.declared_filters["title_search"]
    base_record = filter_generation_provenance(base_decl)
    assert base_record == FilterGenerationProvenance(origin="declared")

    class SubDeclaredFilter(BaseDeclaredFilter):
        pass

    inherited = SubDeclaredFilter.declared_filters["title_search"]
    # Same instance, same record object -- not re-stamped by the subclass run.
    assert inherited is base_decl
    assert filter_generation_provenance(inherited) is base_record
    assert filter_generation_provenance(inherited) == FilterGenerationProvenance(origin="declared")


def test_blocker1_inherited_declaration_without_record_is_backfilled():
    """The ``if provenance is None`` fallback backfills a record-less inheritance.

    Blocker 1 keeps the fallback for an inherited declaration that somehow reaches
    the subclass metaclass run without a provenance record: it is stamped
    ``declared`` (never left record-less), while an inherited declaration that DOES
    carry a record is untouched (covered by the positive control above).
    """
    import django_filters

    from django_strawberry_framework.filters.sets import _GENERATION_PROVENANCE_ATTR

    class BaseDeclaredFilter(FilterSet):
        title_search = django_filters.CharFilter(field_name="title")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    base_decl = BaseDeclaredFilter.declared_filters["title_search"]
    # Strip the record stamped at base creation to simulate an inherited
    # declaration that reaches the subclass metaclass run without one.
    base_decl.__dict__.pop(_GENERATION_PROVENANCE_ATTR, None)
    assert filter_generation_provenance(base_decl) is None

    class SubDeclaredFilter(BaseDeclaredFilter):
        pass

    inherited = SubDeclaredFilter.declared_filters["title_search"]
    assert inherited is base_decl
    assert filter_generation_provenance(inherited) == FilterGenerationProvenance(origin="declared")


# ---------------------------------------------------------------------------
# Candidate metadata built inside ONE immutable expansion snapshot
#
# ``FilterSet.get_filters`` publishes the expanded filters AND a
# ``CandidateFilterMetadata`` mapping as one frozen ``ExpansionSnapshot``,
# atomically, under the same ``should_cache_expansion`` gate; the snapshot slot
# is registered in ``SetLifecycleAttrs.extra`` so ``registry.clear()`` resets
# filters and metadata together. The mapping contains ONLY proven
# framework-generated leaves (fail closed: an absent name is a non-candidate).
# ---------------------------------------------------------------------------


def test_candidate_snapshot_expanded_to_many_leaf_is_eligible_and_to_one_is_not():
    """An expanded to-many leaf is eligible; a flat to-one leaf has a row but is not."""

    class GenreFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"name": ["icontains"]}

    class BookFilter(FilterSet):
        genres = RelatedFilter(GenreFilter, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = {"title": ["icontains"]}

    BookFilter.get_filters()
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None

    expanded_row = snapshot.candidates["genres__name__icontains"]
    assert expanded_row.eligible is True
    assert expanded_row.path_plan.first_many_index is not None
    # Classified against the ROOT model (Book), on the model-field path.
    assert expanded_row.path_plan.model is library_models.Book
    assert expanded_row.path_plan.path == "genres__name"
    assert expanded_row.provenance.origin == "framework_default"
    assert expanded_row.provenance.expanded_from == ("name__icontains",)

    to_one_row = snapshot.candidates["title__icontains"]
    assert to_one_row.eligible is False
    assert to_one_row.path_plan.first_many_index is None
    assert to_one_row.provenance.origin == "framework_default"


def test_candidate_snapshot_omits_declared_and_method_filters():
    """Declared filters (incl. method filters) are ``declared`` origin -> no row."""
    import django_filters

    class BookFilter(FilterSet):
        title_search = django_filters.CharFilter(field_name="title")
        note_method = django_filters.CharFilter(
            field_name="title",
            method="filter_note",
        )

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

        def filter_note(
            self,
            queryset,
            name,
            value,
        ):
            return queryset

    BookFilter.get_filters()
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None
    # A framework-generated leaf DOES get a row ...
    assert "title" in snapshot.candidates
    # ... but declared / method-carrying declared leaves do NOT (fail closed).
    assert "title_search" not in snapshot.candidates
    assert "note_method" not in snapshot.candidates


def test_candidate_snapshot_skips_expanded_leaf_under_non_relation_prefix():
    """Expanded children of a ``RelatedFilter`` with a non-relation prefix get no row (no raise)."""

    class GenreFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"name": ["icontains"]}

    class BookFilter(FilterSet):
        # ``field_name="id"`` is a bare local column (resolves, but no relation
        # hop); ``field_name="does_not_exist"`` does not resolve at all. Both are
        # permitted non-model declared prefixes (finding 1): their expanded,
        # inherited-framework-origin children must NOT be classified (no raise)
        # and get no candidate row.
        local_prefix = RelatedFilter(GenreFilter, field_name="id")
        missing_prefix = RelatedFilter(GenreFilter, field_name="does_not_exist")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    # Must not raise despite ``id__name`` / ``does_not_exist__name`` being
    # unclassifiable against Book.
    BookFilter.get_filters()
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None
    assert "local_prefix__name__icontains" not in snapshot.candidates
    assert "missing_prefix__name__icontains" not in snapshot.candidates
    # The direct framework-generated leaf still gets its row.
    assert "title" in snapshot.candidates


def test_candidate_snapshot_omits_override_generated_leaf():
    """A ``Meta.filter_overrides`` product is ``override_generated`` -> no row."""
    import django_filters
    from django.db import models as django_models

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}
            filter_overrides = {
                django_models.TextField: {"filter_class": django_filters.CharFilter},
            }

    BookFilter.get_filters()
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None
    assert "title" not in snapshot.candidates


def test_candidate_snapshot_includes_package_replacement_global_id_leaf():
    """An own-PK GlobalID ``package_replacement`` leaf gets a row (ineligible per path)."""

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class _Owner:
        origin = GenreType

    class GenreFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"id": ["exact"], "name": ["icontains"]}

    GenreFilter._owner_definition = _Owner()

    GenreFilter.get_filters()
    snapshot = GenreFilter._expansion_snapshot()
    assert snapshot is not None
    id_row = snapshot.candidates["id"]
    assert id_row.provenance.origin == "package_replacement"
    # The own PK is a local column (no many-side hop), so it is ineligible.
    assert id_row.eligible is False
    assert id_row.path_plan.first_many_index is None


def test_candidate_metadata_helper_raises_on_unclassifiable_framework_leaf():
    """A framework-generated leaf with an unresolvable path is a defect -> RAISES.

    Unreachable through the public pipeline (``get_model_field`` guards
    generation), so the internal build helper is exercised directly with a
    synthetic provenance-stamped filter whose ``field_name`` is garbage.
    """
    import django_filters

    from django_strawberry_framework.exceptions import PathResolutionError
    from django_strawberry_framework.filters.sets import (
        _candidate_metadata_for,
        _stamp_generation_provenance,
    )

    leaf = django_filters.CharFilter(field_name="not_a_real_field")
    _stamp_generation_provenance(
        leaf,
        FilterGenerationProvenance(origin="framework_default"),
    )
    with pytest.raises(PathResolutionError):
        _candidate_metadata_for(library_models.Book, leaf)


def test_candidate_metadata_helper_never_classifies_declared_leaf():
    """A declared leaf with a garbage path returns ``None`` and is NEVER classified."""
    import django_filters

    from django_strawberry_framework.filters.sets import (
        _candidate_metadata_for,
        _stamp_generation_provenance,
    )

    leaf = django_filters.CharFilter(field_name="not_a_real_field")
    _stamp_generation_provenance(leaf, FilterGenerationProvenance(origin="declared"))
    # No raise despite the unresolvable path -- declared leaves fail closed.
    assert _candidate_metadata_for(library_models.Book, leaf) is None


def test_candidate_metadata_helper_returns_none_for_unstamped_leaf():
    """An unstamped (consumer-returned) leaf has no record -> no row, fail closed."""
    import django_filters

    from django_strawberry_framework.filters.sets import _candidate_metadata_for

    leaf = django_filters.CharFilter(field_name="genres__name")
    assert _candidate_metadata_for(library_models.Book, leaf) is None


def test_expansion_snapshot_build_failure_publishes_nothing_then_retry_recovers():
    """A mid-build classification failure publishes NOTHING; a retry republishes both."""
    from django_strawberry_framework.exceptions import PathResolutionError
    from django_strawberry_framework.filters import sets as sets_module

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"], "genres__name": ["icontains"]}

    real_classify = sets_module.classify_path
    calls = {"n": 0}

    def flaky_classify(model, field_path):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise PathResolutionError(model, field_path, field_path)
        return real_classify(model, field_path)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(sets_module, "classify_path", flaky_classify)
    try:
        with pytest.raises(PathResolutionError):
            BookFilter.get_filters()
        # A failed build published neither the filter cache nor the snapshot.
        assert "_expanded_snapshot" not in BookFilter.__dict__
        assert "_expanded_filters" not in BookFilter.__dict__
        assert BookFilter._expansion_snapshot() is None
    finally:
        monkeypatch.undo()

    # After un-patching, the next build succeeds and republishes both together.
    filters = BookFilter.get_filters()
    assert "genres__name__icontains" in filters
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None
    assert "genres__name__icontains" in snapshot.candidates


def test_expansion_snapshot_is_isolated_per_subclass():
    """A subclass builds its OWN snapshot and never observes its parent's."""

    class BaseBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"]}

    class SubBookFilter(BaseBookFilter):
        pass

    BaseBookFilter.get_filters()
    parent_snapshot = BaseBookFilter._expansion_snapshot()
    assert parent_snapshot is not None

    SubBookFilter.get_filters()
    sub_snapshot = SubBookFilter._expansion_snapshot()
    assert sub_snapshot is not None
    # Distinct objects; the subclass never inherits the parent's classification.
    assert sub_snapshot is not parent_snapshot
    # The parent's snapshot is unchanged by the subclass build.
    assert BaseBookFilter._expansion_snapshot() is parent_snapshot


def test_expansion_snapshot_absent_for_unresolved_lazy_target():
    """A ``RelatedFilter`` naming a not-registered target caches no snapshot; each call rebuilds."""

    class BranchFilter(FilterSet):
        # A reference to a non-existent class - expansion raises and nothing
        # (neither the filter cache nor the snapshot) is published, mirroring
        # ``test_filterset_get_filters_does_not_cache_when_string_filterset_remains``.
        bogus = RelatedFilter("DefinitelyDoesNotExistFilter", field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    with pytest.raises(ImportError):
        BranchFilter.get_filters()
    assert BranchFilter._expansion_snapshot() is None
    assert "_expanded_snapshot" not in BranchFilter.__dict__
    # Each call re-attempts the build (no half-built snapshot is ever cached).
    with pytest.raises(ImportError):
        BranchFilter.get_filters()
    assert BranchFilter._expansion_snapshot() is None


def test_expansion_snapshot_none_before_build_is_the_fail_closed_hook():
    """Pre-finalization (no snapshot built), the accessor returns None for the adapter."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter("ShelfFilter", field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # No ``get_filters`` build has cached a snapshot yet: the accessor is None,
    # so a filterset instantiated before its lazy targets resolve presents the
    # unexpanded surface and every flat name is absent from the (absent)
    # mapping -- the adapter degrades to today's behavior.
    assert BranchFilter._expansion_snapshot() is None
    instance = BranchFilter(
        data={},
        queryset=library_models.Branch.objects.all(),
        request=None,
    )
    assert type(instance)._expansion_snapshot() is None


def test_expansion_snapshot_reset_by_registry_clear_and_rebuilt_fresh():
    """``registry.clear()`` resets filters + metadata together; the next build republishes."""

    class GenreFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"name": ["icontains"]}

    class BookFilter(FilterSet):
        genres = RelatedFilter(GenreFilter, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    BookFilter.get_filters()
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None
    assert "genres__name__icontains" in snapshot.candidates

    registry.clear()

    # The snapshot slot is gone from the class dict together with the filter
    # cache -- no stale metadata observable between the clear and the rebuild.
    assert "_expanded_snapshot" not in BookFilter.__dict__
    assert "_expanded_filters" not in BookFilter.__dict__
    assert BookFilter._expansion_snapshot() is None

    BookFilter.get_filters()
    rebuilt = BookFilter._expansion_snapshot()
    assert rebuilt is not None
    assert rebuilt is not snapshot
    assert "genres__name__icontains" in rebuilt.candidates


# ---------------------------------------------------------------------------
# Blocker 1 - live capability gate (token + fingerprint), NOT name-only.
#
# An eligible frozen candidate row authorizes correlated-``EXISTS`` routing ONLY
# when the LIVE per-request filter proves capability: the owning class did not
# override a generation seam (so the row carries a token), the live instance
# carries the SAME token, and its live fingerprint matches the frozen one. Each
# django-filter customization seam below must fail CLOSED to the original outer
# invocation -- no ``_dst_predicate_`` alias, correct outer rows. A positive
# control proves the gate does not over-block an unmodified package leaf.
# ---------------------------------------------------------------------------


def _seed_two_books_one_cardio_loan():
    """Seed a ``Matched`` book (one ``Cardio`` loan) and an ``Other`` book (routine).

    Returns ``(matched_pk, other_pk)``. Each book has exactly ONE loan so an
    ``exclude`` filter's split-exclude semantics are unambiguous.
    """
    shelf = _library_shelf()
    matched = library_models.Book.objects.create(shelf=shelf, title="Matched")
    other = library_models.Book.objects.create(shelf=shelf, title="Other")
    library_models.Loan.objects.create(
        book=matched,
        patron=library_models.Patron.objects.create(name="pa", email="a"),
        note="Cardio one",
    )
    library_models.Loan.objects.create(
        book=other,
        patron=library_models.Patron.objects.create(name="pb", email="b"),
        note="routine",
    )
    return matched.pk, other.pk


def _reserved_aliases(queryset):
    """Return the reserved ``_dst_predicate_`` EXISTS aliases attached to ``queryset``."""
    return [n for n in queryset.query.annotations if n.startswith("_dst_predicate_")]


@pytest.mark.django_db
def test_blocker1_get_filter_predicate_swap_fails_closed_pre_fanned_multiplicity():
    """Round-4 Blocker 1: a helper-seam mutation (get_filter_predicate) fails closed.

    A generated ``Book.genres`` ``ModelMultipleChoiceFilter`` (Genre is NOT a Relay
    node here, so the leaf stays the review's exact family, not a GlobalID) is an
    eligible direct-M2M correlated-``EXISTS`` candidate. A consumer swaps the LIVE
    per-request instance's ``get_filter_predicate`` -- a normal django-filter
    extension seam -- WITHOUT touching ``.filter``. Before the fix the fingerprint
    (and token) still matched, so the leaf was STILL routed through the correlated
    adapter, which suppresses the framework fan-out ``distinct`` and PRESERVES a
    pre-fanned incoming row multiplicity. Now the effective-call-graph signature
    diverges, so the leaf fails closed to the ORIGINAL outer invocation
    (``ModelMultipleChoiceFilter.filter``, honoring ``distinct``), collapsing the
    pre-fan; no reserved ``EXISTS`` alias attaches. Asserts token-equality with
    signature-mismatch, the original outer result, and alias absence.
    """

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact"]}

    BookFilter.get_filters()
    candidate = BookFilter._expansion_snapshot().candidates["genres"]
    assert candidate.eligible is True
    assert candidate.token is not None

    genre = library_models.Genre.objects.create(name="G")
    shelf = _library_shelf()
    book = library_models.Book.objects.create(shelf=shelf, title="book-1")
    book.genres.add(genre)
    # TWO loans (distinct patrons -- Loan is unique per book+patron) for the SAME
    # book, so a join to ``loans`` pre-fans the outer row twice.
    patron_a = library_models.Patron.objects.create(name="pa", email="a@example.com")
    patron_b = library_models.Patron.objects.create(name="pb", email="b@example.com")
    library_models.Loan.objects.create(book=book, patron=patron_a, note="l1")
    library_models.Loan.objects.create(book=book, patron=patron_b, note="l2")

    def _pre_fanned():
        # A relation JOIN with NO distinct: the one book appears once per loan.
        return library_models.Book.objects.filter(loans__isnull=False).order_by("id")

    assert _pre_fanned().count() == 2  # the pre-fan

    def _build_fs():
        return BookFilter(
            data={"genres": [str(genre.pk)]},
            queryset=_pre_fanned(),
            request=HttpRequest(),
        )

    # (1) UNTOUCHED live instance -> authorized -> routed through EXISTS, which
    #     PRESERVES the pre-fanned multiplicity (two rows for the one book).
    clean_fs = _build_fs()
    clean_qs = clean_fs.qs
    assert len(_reserved_aliases(clean_qs)) == 1
    assert str(clean_qs.query).upper().count("EXISTS") == 1
    assert list(clean_qs.values_list("pk", flat=True)) == [book.pk, book.pk]
    clean_leaf = clean_fs.filters["genres"]
    assert getattr(clean_leaf, _GENERATION_TOKEN_ATTR, None) == candidate.token
    assert _fingerprint_of(clean_leaf) == candidate.fingerprint

    # (2) SWAP get_filter_predicate on the LIVE instance (same predicate result) ->
    #     token still equal but the signature diverges -> FAIL CLOSED -> the original
    #     outer invocation honors the framework distinct and collapses the pre-fan to
    #     ONE row; NO reserved alias attaches.
    swapped_fs = _build_fs()
    swapped_leaf = swapped_fs.filters["genres"]
    original_predicate = swapped_leaf.get_filter_predicate
    swapped_leaf.get_filter_predicate = lambda value: original_predicate(value)
    assert getattr(swapped_leaf, _GENERATION_TOKEN_ATTR, None) == candidate.token
    assert _fingerprint_of(swapped_leaf) != candidate.fingerprint
    swapped_qs = swapped_fs.qs
    assert _reserved_aliases(swapped_qs) == []
    assert "EXISTS" not in str(swapped_qs.query).upper()
    assert list(swapped_qs.values_list("pk", flat=True)) == [book.pk]


@pytest.mark.django_db
def test_capability_gate_init_override_fails_closed():
    """Seam 4 (round-4 Blocker 1): a consumer ``__init__`` override is not capable.

    ``__init__`` is the standard place a consumer replaces or mutates
    ``self.filters`` per request. A subclass that defines its own ``__init__`` is
    NOT generation-capable, so no token is minted for its eligible
    ``loans__note__icontains`` leaf and the request runs the ORIGINAL outer
    invocation instead of a correlated ``EXISTS`` -- fail closed regardless of what
    the ``__init__`` body does.
    """
    matched_pk, _other_pk = _seed_two_books_one_cardio_loan()

    class InitOverrideFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    assert InitOverrideFilter._is_generation_capable() is False
    InitOverrideFilter.get_filters()
    row = InitOverrideFilter._expansion_snapshot().candidates["loans__note__icontains"]
    # The path is still eligible, but no capability token was minted.
    assert row.eligible is True
    assert row.token is None
    assert row.fingerprint is None

    result = InitOverrideFilter(
        data={"loans__note__icontains": "Cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    ).qs
    assert _reserved_aliases(result) == []
    # Fails closed to the plain outer invocation, which still returns the match.
    assert list(result.order_by("id").values_list("pk", flat=True)) == [matched_pk]


@pytest.mark.django_db
def test_capability_gate_filter_for_field_override_super_mutate_fails_closed():
    """Seam 1: ``filter_for_field`` super()+mutate -> not capable -> outer, not routed.

    The subclass calls ``super().filter_for_field`` (keeping the framework stamp)
    and MUTATES the returned instance to ``exclude=True``. Because
    ``filter_for_field`` is overridden the class is NOT generation-capable, so the
    eligible ``loans__note__icontains`` leaf runs the ORIGINAL outer invocation
    (honoring the consumer ``exclude``) instead of a positive correlated
    ``EXISTS``. If it were wrongly routed the result would be the matched book;
    the correct outer/exclude result is the OTHER book.
    """
    _matched_pk, other_pk = _seed_two_books_one_cardio_loan()

    class MutatingFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

        @classmethod
        def filter_for_field(
            cls,
            field,
            field_name,
            lookup_expr=None,
        ):
            leaf = super().filter_for_field(field, field_name, lookup_expr)
            leaf.exclude = True  # consumer mutation of the framework-stamped leaf
            return leaf

    assert MutatingFilter._is_generation_capable() is False
    MutatingFilter.get_filters()
    row = MutatingFilter._expansion_snapshot().candidates["loans__note__icontains"]
    # The path is still eligible, but no capability token was minted.
    assert row.eligible is True
    assert row.token is None
    assert row.fingerprint is None

    result = MutatingFilter(
        data={"loans__note__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    ).qs
    assert _reserved_aliases(result) == []
    assert list(result.order_by("id").values_list("pk", flat=True)) == [other_pk]


@pytest.mark.django_db
def test_capability_gate_filter_for_lookup_override_fails_closed():
    """Seam 2: ``filter_for_lookup`` returning a custom generated class -> not capable."""
    import django_filters

    matched_pk, _other_pk = _seed_two_books_one_cardio_loan()

    class CustomGenerated(django_filters.CharFilter):
        """A consumer-owned generated filter class returned from filter_for_lookup."""

    class LookupOverrideFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

        @classmethod
        def filter_for_lookup(cls, field, lookup_type):
            _default_class, params = super().filter_for_lookup(field, lookup_type)
            return CustomGenerated, params

    assert LookupOverrideFilter._is_generation_capable() is False
    LookupOverrideFilter.get_filters()
    leaf = LookupOverrideFilter.get_filters()["loans__note__icontains"]
    assert isinstance(leaf, CustomGenerated)
    row = LookupOverrideFilter._expansion_snapshot().candidates["loans__note__icontains"]
    assert row.token is None

    result = LookupOverrideFilter(
        data={"loans__note__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    ).qs
    assert _reserved_aliases(result) == []
    assert list(result.order_by("id").values_list("pk", flat=True)) == [matched_pk]


@pytest.mark.django_db
def test_capability_gate_class_level_filter_defaults_override_fails_closed():
    """Seam 3: a class-level ``FILTER_DEFAULTS`` shadow -> not capable -> outer."""
    matched_pk, _other_pk = _seed_two_books_one_cardio_loan()

    class DefaultsOverrideFilter(FilterSet):
        # A shadowing COPY breaks the identity check against
        # ``BaseFilterSet.FILTER_DEFAULTS``.
        FILTER_DEFAULTS = dict(FilterSet.FILTER_DEFAULTS)

        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

    assert DefaultsOverrideFilter._is_generation_capable() is False
    DefaultsOverrideFilter.get_filters()
    row = DefaultsOverrideFilter._expansion_snapshot().candidates["loans__note__icontains"]
    assert row.token is None

    result = DefaultsOverrideFilter(
        data={"loans__note__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    ).qs
    assert _reserved_aliases(result) == []
    assert list(result.order_by("id").values_list("pk", flat=True)) == [matched_pk]


@pytest.mark.django_db
def test_capability_gate_replaces_instance_at_init_fails_closed():
    """Seam 4 (ReplacesAtInit): a consumer ``__init__`` swaps in a different filter.

    ``__init__`` is the standard place a consumer replaces ``self.filters`` per
    request, so overriding it is itself a generation-capability BREAK (round-4
    Blocker 1): the class mints NO token or fingerprint for its otherwise-eligible
    ``genres__name__icontains`` leaf, so routing fails closed at the capability
    gate -- independent of whatever the ``__init__`` body does to the live
    instance. The end-to-end result is unchanged from the prior contract (the
    replaced TITLE filter runs on the outer queryset), but the fail-closed
    MECHANISM is now the capability gate rather than a live token/fingerprint miss.
    """
    shelf = _library_shelf()
    by_title = library_models.Book.objects.create(shelf=shelf, title="Cardiology Handbook")
    by_genre = library_models.Book.objects.create(shelf=shelf, title="Neurology Atlas")
    by_genre.genres.add(library_models.Genre.objects.create(name="cardio-club"))

    class ReplacingFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"]}

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Replace the deepcopied live filter with an unstamped title filter.
            self.filters["genres__name__icontains"] = CharFilter(
                field_name="title",
                lookup_expr="icontains",
            )

    # The ``__init__`` override alone makes the class non-capable: no token / no
    # fingerprint is minted, so the leaf can never be routed.
    assert ReplacingFilter._is_generation_capable() is False
    ReplacingFilter.get_filters()
    frozen = ReplacingFilter._expansion_snapshot().candidates["genres__name__icontains"]
    assert frozen.eligible is True
    assert frozen.token is None
    assert frozen.fingerprint is None

    instance = ReplacingFilter(
        data={"genres__name__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    )
    result = instance.qs
    assert _reserved_aliases(result) == []
    # The outer path runs the replaced TITLE filter: matches by title only.
    assert list(result.order_by("id").values_list("pk", flat=True)) == [by_title.pk]


@pytest.mark.django_db
def test_capability_gate_live_mutation_diverges_fingerprint_fails_closed():
    """Seam 5: mutating the live ``self.filters`` entry diverges the fingerprint.

    A capable class with an eligible ``loans__note__icontains`` leaf. The live
    per-request instance's ``distinct`` is flipped to ``False`` before ``.qs``, so
    the live fingerprint no longer matches the frozen one and routing fails
    closed. The outer invocation then runs WITHOUT the framework ``distinct``, so
    a book with TWO matching loans fans out to a duplicate row -- observably
    different from the single-row correlated-``EXISTS`` result, and proof the
    stale row did not authorize routing.
    """
    shelf = _library_shelf()
    matched = library_models.Book.objects.create(shelf=shelf, title="Matched")
    library_models.Loan.objects.create(
        book=matched,
        patron=library_models.Patron.objects.create(name="pa", email="a"),
        note="Cardio one",
    )
    library_models.Loan.objects.create(
        book=matched,
        patron=library_models.Patron.objects.create(name="pb", email="b"),
        note="Cardio two",
    )

    class BookLoanFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

    BookLoanFilter.get_filters()
    instance = BookLoanFilter(
        data={"loans__note__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    )
    # Diverge the live fingerprint by dropping the framework-added distinct.
    instance.filters["loans__note__icontains"].distinct = False

    result = instance.qs
    assert _reserved_aliases(result) == []
    # No distinct + a JOIN over two matching loans fans out to duplicate rows.
    assert list(result.order_by("id").values_list("pk", flat=True)) == [matched.pk, matched.pk]


@pytest.mark.django_db
def test_capability_gate_positive_control_unmodified_leaf_is_routed():
    """Positive control: an unmodified package eligible to-many leaf IS routed.

    Proves the gate does not over-block: a capable class's frozen row carries a
    token, the live deepcopied instance carries the SAME token (survived
    ``copy.deepcopy`` by value), the live fingerprint matches, and the request
    composes as a single distinct-free correlated ``EXISTS``.
    """
    matched_pk, _other_pk = _seed_two_books_one_cardio_loan()

    class BookLoanFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

    assert BookLoanFilter._is_generation_capable() is True
    BookLoanFilter.get_filters()
    frozen = BookLoanFilter._expansion_snapshot().candidates["loans__note__icontains"]
    assert frozen.eligible is True
    assert frozen.token is not None
    assert frozen.fingerprint is not None

    instance = BookLoanFilter(
        data={"loans__note__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    )
    from django_strawberry_framework.filters.sets import (
        _GENERATION_TOKEN_ATTR,
        _fingerprint_of,
    )

    live = instance.filters["loans__note__icontains"]
    # Token survived the per-request deepcopy by VALUE and matches the frozen row.
    assert getattr(live, _GENERATION_TOKEN_ATTR, None) == frozen.token
    assert _fingerprint_of(live) == frozen.fingerprint

    result = instance.qs
    assert _reserved_aliases(result) == ["_dst_predicate_0"]
    assert result.query.distinct is False
    assert list(result.order_by("id").values_list("pk", flat=True)) == [matched_pk]


def test_is_generation_capable_true_for_unmodified_subclass():
    """A plain package ``FilterSet`` subclass with no seam override IS capable."""

    class PlainFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    assert PlainFilter._is_generation_capable() is True
    assert PlainFilter.FILTER_DEFAULTS is FilterSet.FILTER_DEFAULTS


def test_is_generation_capable_false_for_plain_function_seam_override():
    """A plain-function ``filter_for_field`` (no ``__func__``) -> False, never raises.

    A consumer that shadows the generation seam with a plain function (or a
    ``staticmethod``) yields a ``cls.filter_for_field`` that has no ``__func__``
    attribute -- a plain function is not a bound method. ``_is_generation_capable``
    reads it null-safely via ``getattr(..., "__func__", None)`` and returns
    ``False`` cleanly instead of raising ``AttributeError``. Empty ``fields``
    keeps class creation from invoking the shadowed seam during ``get_filters``.
    """

    def _plain_seam(field, field_name, lookup_expr=None):
        raise AssertionError("never invoked")

    class PlainSeamFilter(FilterSet):
        filter_for_field = _plain_seam

        class Meta:
            model = library_models.Book
            fields = []

    # No ``__func__`` on the plain-function attribute -- the missing-attr branch.
    assert not hasattr(PlainSeamFilter.filter_for_field, "__func__")
    assert PlainSeamFilter._is_generation_capable() is False


# ---------------------------------------------------------------------------
# Finding 1 - capability travels through the RelatedFilter EXPANSION boundary.
#
# ``get_filters._build`` reads ``_is_generation_capable()`` on the PARENT
# building the snapshot, but an expanded leaf was generated by the CHILD. The
# child's capability is captured at its generation site on
# ``FilterGenerationProvenance.generation_capable`` and inherited through
# ``_expand_related_filter``; the mint gate requires it, so a non-capable
# child's leaf expanded into a capable parent stays token-less (fail closed)
# while a fully-capable pair still routes through the correlated ``EXISTS``.
# ---------------------------------------------------------------------------


def _seed_matched_book_two_cardio_loans():
    """Create a ``Matched`` book with TWO ``Cardio`` loans; return the book.

    Two matching loans make a flattened to-many leaf's OUTER (fan-out) result
    (``[matched, matched]``) observably different from the row-preserving
    correlated-``EXISTS`` result (``[matched]``).
    """
    shelf = _library_shelf()
    matched = library_models.Book.objects.create(shelf=shelf, title="Matched")
    library_models.Loan.objects.create(
        book=matched,
        patron=library_models.Patron.objects.create(name="pa", email="a"),
        note="Cardio one",
    )
    library_models.Loan.objects.create(
        book=matched,
        patron=library_models.Patron.objects.create(name="pb", email="b"),
        note="Cardio two",
    )
    return matched


@pytest.mark.django_db
def test_capability_gate_related_filter_expands_non_capable_child_fails_closed():
    """Expansion boundary: a non-capable CHILD's leaf expanded into a capable PARENT.

    Finding 1: a CHILD ``FilterSet`` overriding ``filter_for_lookup`` (so the
    child is NOT generation-capable) still gets the inherited package
    ``filter_for_field`` stamp ``origin="framework_default"`` on its custom
    generated instance. When a capable PARENT expands that child through a
    ``RelatedFilter``, the expanded ``loans__note__icontains`` row is
    path-eligible and framework-origin -- yet it must NOT mint a capability
    token, because the child's ``generation_capable`` bit (captured at the
    child's generation site and carried through expansion) is ``False``.
    Otherwise the consumer's custom child filter would be routed through the
    correlated ``EXISTS`` adapter.

    At request time the leaf therefore runs the ORIGINAL child filter on the
    OUTER queryset: with no framework ``distinct`` on the flattened leaf, a book
    with TWO matching loans fans out to a duplicate row -- observably different
    from the single-row correlated-``EXISTS`` result, proving fail-closed.
    """
    import django_filters

    matched = _seed_matched_book_two_cardio_loans()

    class CustomChildGenerated(django_filters.CharFilter):
        """A consumer-owned generated filter class returned from the CHILD's seam."""

    class ChildLoanFilter(FilterSet):
        class Meta:
            model = library_models.Loan
            fields = {"note": ["icontains"]}

        @classmethod
        def filter_for_lookup(cls, field, lookup_type):
            _default_class, params = super().filter_for_lookup(field, lookup_type)
            return CustomChildGenerated, params

    class ParentBookFilter(FilterSet):
        loans = RelatedFilter(ChildLoanFilter, field_name="loans")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    assert ParentBookFilter._is_generation_capable() is True
    assert ChildLoanFilter._is_generation_capable() is False

    ParentBookFilter.get_filters()
    # The expanded leaf is the consumer's custom class, framework-origin, and
    # path-eligible -- but fail-closed: no token, because the child that
    # generated it was not generation-capable.
    leaf = ParentBookFilter.get_filters()["loans__note__icontains"]
    assert isinstance(leaf, CustomChildGenerated)
    row = ParentBookFilter._expansion_snapshot().candidates["loans__note__icontains"]
    assert row.eligible is True
    assert row.provenance.generation_capable is False
    assert row.token is None
    assert row.fingerprint is None

    result = ParentBookFilter(
        data={"loans__note__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    ).qs
    # Not routed through the correlated adapter (no reserved EXISTS alias); the
    # custom child filter ran on the OUTER queryset, so the two matching loans
    # fan out to a duplicate row.
    assert _reserved_aliases(result) == []
    assert list(result.order_by("id").values_list("pk", flat=True)) == [matched.pk, matched.pk]


@pytest.mark.django_db
def test_capability_gate_related_filter_expands_capable_child_is_routed():
    """Positive control: a capable PARENT + capable CHILD over a to-many path DO route.

    The mirror of the fail-closed expansion test. With a fully capable child
    ``FilterSet`` (no generation-seam override), the expanded
    ``loans__note__icontains`` row carries ``generation_capable=True`` and the
    capable parent mints a token + fingerprint. The parent is the sole authority
    on the expanded leaf's token: any child-minted token is popped in
    ``_expand_related_filter`` before the parent re-mints, and the parent's token
    survives the per-request deepcopy by value. The request composes as a single
    distinct-free correlated ``EXISTS``, proving the fix does not over-block the
    legitimate expansion case.
    """
    matched = _seed_matched_book_two_cardio_loans()

    class ChildLoanFilter(FilterSet):
        class Meta:
            model = library_models.Loan
            fields = {"note": ["icontains"]}

    class ParentBookFilter(FilterSet):
        loans = RelatedFilter(ChildLoanFilter, field_name="loans")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    assert ParentBookFilter._is_generation_capable() is True
    assert ChildLoanFilter._is_generation_capable() is True

    ParentBookFilter.get_filters()
    row = ParentBookFilter._expansion_snapshot().candidates["loans__note__icontains"]
    assert row.eligible is True
    assert row.provenance.generation_capable is True
    assert row.token is not None
    assert row.fingerprint is not None

    instance = ParentBookFilter(
        data={"loans__note__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    )
    from django_strawberry_framework.filters.sets import (
        _GENERATION_TOKEN_ATTR,
        _fingerprint_of,
    )

    live = instance.filters["loans__note__icontains"]
    # The parent's token survived the per-request deepcopy by value; the child's
    # token (popped in ``_expand_related_filter``) never rode along.
    assert getattr(live, _GENERATION_TOKEN_ATTR, None) == row.token
    assert _fingerprint_of(live) == row.fingerprint

    result = instance.qs
    # Routed through the correlated adapter: one reserved EXISTS alias, no outer
    # distinct, and the two matching loans collapse to a single row.
    assert _reserved_aliases(result) == ["_dst_predicate_0"]
    assert result.query.distinct is False
    assert list(result.order_by("id").values_list("pk", flat=True)) == [matched.pk]


# ---------------------------------------------------------------------------
# Blocker 2 - resolved-field origin oracle (isnull / transform / precision).
#
# ``_generation_origin_for_field`` mirrors django-filter's RESOLVED-field
# selection: a ``Meta.filter_overrides`` product is ``override_generated`` (and
# thus never an eligible candidate) even when the override is selected via the
# resolved output field (``isnull`` -> BooleanField, a transform -> its output
# field), not the original model field.
# ---------------------------------------------------------------------------


def test_origin_isnull_boolean_override_on_many_side_is_override_generated():
    """Blocker 2: a BooleanField override selected by ``isnull`` -> override_generated.

    ``Loan.note`` is a ``TextField``; the ``isnull`` lookup resolves the SELECTION
    field to ``BooleanField``, which the consumer override governs. The generated
    ``loans__note__isnull`` leaf (a many-side path) must therefore be
    ``override_generated`` and INELIGIBLE (no candidate row), even though the
    unresolved model field is a TextField.
    """
    import django_filters
    from django.db import models

    class CustomBoolean(django_filters.BooleanFilter):
        """Consumer override BooleanField product."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["isnull"]}
            filter_overrides = {
                models.BooleanField: {"filter_class": CustomBoolean},
            }

    leaf = BookFilter.get_filters()["loans__note__isnull"]
    # django-filter actually selected the override product ...
    assert isinstance(leaf, CustomBoolean)
    # ... and the origin oracle agrees via the RESOLVED (BooleanField) selection.
    assert filter_generation_provenance(leaf).origin == "override_generated"
    # An override product gets NO candidate row -> never routed.
    assert "loans__note__isnull" not in BookFilter._expansion_snapshot().candidates


def test_origin_transform_output_field_selects_override_is_override_generated():
    """Blocker 2: a transform whose OUTPUT field selects an override -> override_generated.

    ``ScalarSpecimen.occurred_on`` is a ``DateField``; the ``year`` transform
    resolves the output field to ``IntegerField``, which the consumer override
    governs. The generated ``occurred_on__year`` leaf must be classified from
    that resolved output field, not the unresolved ``DateField``.
    """
    import django_filters
    from django.db import models

    class CustomNumber(django_filters.NumberFilter):
        """Consumer override IntegerField product."""

    class SpecimenFilter(FilterSet):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {"occurred_on": ["year"]}
            filter_overrides = {
                models.IntegerField: {"filter_class": CustomNumber},
            }

    leaf = SpecimenFilter.get_filters()["occurred_on__year"]
    assert isinstance(leaf, CustomNumber)
    assert filter_generation_provenance(leaf).origin == "override_generated"


def test_origin_precision_plain_many_side_leaf_stays_framework_default_and_eligible():
    """Blocker 2: an unmatched leaf on an override-bearing class stays framework_default.

    On the SAME class that carries a ``BooleanField`` override, the plain
    ``loans__note__icontains`` leaf resolves to a ``TextField`` selection the
    override does NOT govern, so it stays ``framework_default`` and eligible (a
    capability token is minted). This proves per-leaf precision -- a
    ``filter_overrides`` entry does NOT blanket-demote every leaf on the class.
    """
    import django_filters
    from django.db import models

    class CustomBoolean(django_filters.BooleanFilter):
        """Consumer override that governs only the isnull-resolved BooleanField."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains", "isnull"]}
            filter_overrides = {
                models.BooleanField: {"filter_class": CustomBoolean},
            }

    BookFilter.get_filters()
    candidates = BookFilter._expansion_snapshot().candidates
    # isnull leaf is the override product -> no row.
    assert "loans__note__isnull" not in candidates
    # icontains leaf is untouched by the BooleanField override.
    icontains = BookFilter.get_filters()["loans__note__icontains"]
    assert filter_generation_provenance(icontains).origin == "framework_default"
    row = candidates["loans__note__icontains"]
    assert row.eligible is True
    assert row.token is not None


def test_generation_origin_oracle_fails_closed_on_unresolvable_lookup():
    """``_generation_origin_for_field`` returns override_generated when resolve_field raises.

    A lookup that cannot be resolved raises ``FieldLookupError`` upstream before
    any filter is generated (so such a leaf can never become an eligible
    candidate); the oracle fails closed to ``override_generated`` -- the
    ineligible origin -- so an unresolvable lookup is never treated as an
    eligible framework leaf. Exercised directly because the public generation
    path raises before reaching here.
    """

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Genre._meta.get_field("name")
    assert (
        BookFilter._generation_origin_for_field(field, "not_a_real_lookup") == "override_generated"
    )


# ======================================================================
# Round-5 High 3: parameterized fail-closed signature acceptance matrix
# ----------------------------------------------------------------------
# The Part 1 plan enumerates a FINITE authorization boundary; round-5 High 3
# requires an acceptance row for EVERY enumerated signature member, not only the
# handful previously exercised. A shared pre-fanned harness proves the SAME four
# invariants for each mutation: the capability token stays EQUAL, the semantic
# signature DIVERGES, no reserved ``EXISTS`` alias attaches, and the ORIGINAL
# outer invocation's result (the framework-``distinct`` collapse of the pre-fan)
# wins. Helper descriptors are covered in BOTH halves the signature models --
# instance ``__dict__`` override and class-level descriptor replacement.
# ======================================================================


class _R5PreFanBookFilter(FilterSet):
    """Module-scope harness: an eligible direct-M2M ``Book.genres`` leaf.

    ``Genre`` is NOT registered as a Relay node, so ``genres`` stays the review's
    exact ``ModelMultipleChoiceFilter`` family (the one whose ``get_filter_predicate``
    reads ``field.to_field_name``), generated through the package's own machinery ->
    eligible, token-bearing. The snapshot is frozen once at import; each test seeds
    its own rows and re-derives the live signature.
    """

    class Meta:
        model = library_models.Book
        fields = {"genres": ["exact"]}


def _r5_prefan_candidate():
    _R5PreFanBookFilter.get_filters()
    candidate = _R5PreFanBookFilter._expansion_snapshot().candidates["genres"]
    assert candidate.eligible is True
    assert candidate.token is not None
    return candidate


def _seed_r5_prefan_genre_book():
    """One ``Book`` pre-fanned by TWO loans (distinct patrons).

    A relation JOIN to ``loans`` with no ``distinct`` makes the one book appear
    twice, so a correlated ``EXISTS`` (which suppresses the framework fan-out
    ``distinct``) preserves the pre-fan while the original outer invocation
    (honoring ``distinct``) collapses it. Returns ``(book, genre)``.

    The genre's ``name`` is set to its OWN pk (as a string). ``get_filter_predicate``
    with a ``to_field="name"`` redirect builds ``{genres: getattr(genre, "name")}`` --
    i.e. it filters the M2M by the EXTRACTED value against the target pk -- so the
    name must be a valid pk for the failed-closed outer predicate to still match the
    same genre (round-5 Blocker 2). For every other (pk-based) mutation the name is
    irrelevant.
    """
    genre = library_models.Genre.objects.create(name="temp")
    genre.name = str(genre.pk)
    genre.save(update_fields=["name"])
    shelf = _library_shelf()
    book = library_models.Book.objects.create(shelf=shelf, title="book-1")
    book.genres.add(genre)
    patron_a = library_models.Patron.objects.create(name="pa", email="a@example.com")
    patron_b = library_models.Patron.objects.create(name="pb", email="b@example.com")
    library_models.Loan.objects.create(book=book, patron=patron_a, note="l1")
    library_models.Loan.objects.create(book=book, patron=patron_b, note="l2")
    return book, genre


def _r5_prefanned_books():
    return library_models.Book.objects.filter(loans__isnull=False).order_by("id")


# -- instance-override mutations (each keeps effective behavior identical so the
#    ONLY observable change is the fail-closed routing collapse) ----------------


def _r5_mut_get_method_instance(leaf):
    original = leaf.get_method
    leaf.get_method = lambda qs: original(qs)


def _r5_mut_is_noop_instance(leaf):
    original = leaf.is_noop
    leaf.is_noop = lambda qs, value: original(qs, value)


def _r5_mut_get_filter_predicate_instance(leaf):
    original = leaf.get_filter_predicate
    leaf.get_filter_predicate = lambda value: original(value)


def _r5_mut_field_to_field_name(leaf):
    # The form field was built by pre-validation (resolving the submitted value by
    # pk); redirecting its ``to_field_name`` now changes ONLY the effective runtime
    # target the model-choice predicate reads (round-5 Blocker 2). The seeded genre's
    # name equals its own pk, so the failed-closed outer predicate
    # (``{genres: getattr(genre, "name")}``) resolves to a valid pk and still matches
    # the same book -> a clean single-row ``distinct`` collapse.
    leaf.field.to_field_name = "name"


def _r5_mut_conjoined(leaf):
    leaf.conjoined = True


def _r5_mut_always_filter(leaf):
    # ``MultipleChoiceFilter.always_filter`` defaults True; flipping it diverges the
    # signature. With a non-empty submitted value the leaf still applies, so the
    # failed-closed outer result is unchanged.
    leaf.always_filter = False


def _r5_mut_null_value(leaf):
    leaf.null_value = "dst-sentinel"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(_r5_mut_get_method_instance, id="get_method"),
        pytest.param(_r5_mut_is_noop_instance, id="is_noop"),
        pytest.param(_r5_mut_get_filter_predicate_instance, id="get_filter_predicate"),
        pytest.param(_r5_mut_field_to_field_name, id="field_to_field_name"),
        pytest.param(_r5_mut_conjoined, id="conjoined"),
        pytest.param(_r5_mut_always_filter, id="always_filter"),
        pytest.param(_r5_mut_null_value, id="null_value"),
    ],
)
def test_signature_matrix_instance_mutation_fails_closed(mutate):
    """Every enumerated signature member, mutated on the LIVE instance, fails closed.

    Asserts the four invariants for each member: token EQUAL, signature DIVERGES,
    no reserved ``EXISTS`` alias, and the ORIGINAL outer result (the pre-fan
    collapsed to one row) rather than the correlated adapter's preserved pre-fan.
    """
    candidate = _r5_prefan_candidate()
    book, genre = _seed_r5_prefan_genre_book()
    fs = _R5PreFanBookFilter(
        data={"genres": [str(genre.pk)]},
        queryset=_r5_prefanned_books(),
        request=HttpRequest(),
    )
    # Validate FIRST so the live form field is built (by pk) BEFORE any mutation --
    # mirrors a consumer mutating effective runtime state post-validation.
    assert fs.form.is_valid()
    leaf = fs.filters["genres"]
    mutate(leaf)
    assert getattr(leaf, _GENERATION_TOKEN_ATTR, None) == candidate.token
    assert _fingerprint_of(leaf) != candidate.fingerprint
    qs = fs.qs
    assert _reserved_aliases(qs) == []
    assert "EXISTS" not in str(qs.query).upper()
    assert list(qs.values_list("pk", flat=True)) == [book.pk]


@contextlib.contextmanager
def _r5_patched_class_descriptor(leaf_cls, name):
    """Temporarily replace ``leaf_cls.<name>`` with a behavior-identical delegate.

    The delegate has the SAME effect as the original (so the failed-closed outer
    result stays deterministic) but a DIFFERENT object identity, so the signature's
    class-descriptor half diverges. ``mock.patch.object`` restores the original --
    including deleting an inherited attribute it had to add -- on exit.
    """
    original = getattr(leaf_cls, name)

    def _delegate(self, *args, **kwargs):
        return original(self, *args, **kwargs)

    with mock.patch.object(leaf_cls, name, _delegate):
        yield


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name",
    [
        "get_method",
        "is_noop",
        "get_filter_predicate",
        "filter",
    ],
)
def test_signature_matrix_class_descriptor_swap_fails_closed(name):
    """A class-level descriptor replacement (the OTHER signature half) fails closed.

    The signature intentionally captures each helper in two halves; this covers the
    class-descriptor half for the full ``.filter`` call graph. Same four invariants.
    """
    candidate = _r5_prefan_candidate()
    book, genre = _seed_r5_prefan_genre_book()
    fs = _R5PreFanBookFilter(
        data={"genres": [str(genre.pk)]},
        queryset=_r5_prefanned_books(),
        request=HttpRequest(),
    )
    assert fs.form.is_valid()
    leaf = fs.filters["genres"]
    with _r5_patched_class_descriptor(type(leaf), name):
        assert getattr(leaf, _GENERATION_TOKEN_ATTR, None) == candidate.token
        assert _fingerprint_of(leaf) != candidate.fingerprint
        qs = fs.qs
        assert _reserved_aliases(qs) == []
        assert "EXISTS" not in str(qs.query).upper()
        assert list(qs.values_list("pk", flat=True)) == [book.pk]


@pytest.mark.django_db
def test_signature_matrix_untouched_leaf_routes_and_preserves_prefan():
    """Positive control: the untampered live leaf re-derives the frozen signature.

    Proves the round-5 Blocker-2 build-on-deepcopy capture of the effective
    ``field.to_field_name`` still yields a signature EQUAL to a genuine request's
    live signature (so genuine requests are never falsely failed closed): the leaf
    routes through ONE correlated ``EXISTS`` and PRESERVES the pre-fan (two rows).
    """
    candidate = _r5_prefan_candidate()
    book, genre = _seed_r5_prefan_genre_book()
    fs = _R5PreFanBookFilter(
        data={"genres": [str(genre.pk)]},
        queryset=_r5_prefanned_books(),
        request=HttpRequest(),
    )
    leaf = fs.filters["genres"]
    assert getattr(leaf, _GENERATION_TOKEN_ATTR, None) == candidate.token
    assert _fingerprint_of(leaf) == candidate.fingerprint
    qs = fs.qs
    assert len(_reserved_aliases(qs)) == 1
    assert str(qs.query).upper().count("EXISTS") == 1
    assert list(qs.values_list("pk", flat=True)) == [book.pk, book.pk]


@pytest.mark.django_db
def test_blocker2_live_field_to_field_name_mutation_fails_closed_pre_fanned():
    """Round-5 Blocker 2: a live ``field.to_field_name`` mutation fails closed.

    ``ModelMultipleChoiceFilter.get_filter_predicate`` reads the built form field's
    ``to_field_name``, NOT ``extra["to_field_name"]``. Before the fix the signature
    signed the constructor copy, so a post-validation mutation of the LIVE field
    (``leaf.field.to_field_name = "name"``) left the token AND signature unchanged
    and the leaf STILL routed through the correlated adapter -- which suppresses the
    framework ``distinct`` and preserves the pre-fanned Book multiplicity. Signing
    the effective runtime read now diverges the signature, so the leaf fails closed
    to the original outer invocation (honoring ``distinct``): the reserved alias is
    absent and the pre-fan collapses. Asserts token equality, signature mismatch,
    alias absence, and the original outer result.
    """
    candidate = _r5_prefan_candidate()
    book, genre = _seed_r5_prefan_genre_book()
    fs = _R5PreFanBookFilter(
        data={"genres": [str(genre.pk)]},
        queryset=_r5_prefanned_books(),
        request=HttpRequest(),
    )
    # Validation (with the default pk-based field) resolves the submitted value to
    # the Genre instance; only AFTER that does the consumer mutate the live field.
    assert fs.form.is_valid()
    leaf = fs.filters["genres"]
    assert (leaf.extra or {}).get("to_field_name") is None
    leaf.field.to_field_name = "name"
    assert leaf.field.to_field_name == "name"  # the effective runtime target moved
    assert getattr(leaf, _GENERATION_TOKEN_ATTR, None) == candidate.token
    assert _fingerprint_of(leaf) != candidate.fingerprint
    qs = fs.qs
    assert _reserved_aliases(qs) == []
    assert "EXISTS" not in str(qs.query).upper()
    # The failed-closed outer predicate ({genres: genre.name}, where the seeded
    # name equals the genre pk) still matches the book, but honors distinct -> ONE
    # row, not the adapter's preserved [book, book].
    assert list(qs.values_list("pk", flat=True)) == [book.pk]


# ======================================================================
# Round-5 Blocker 1: an ``extra``-only class-level ``FILTER_DEFAULTS`` shadow is
# consumer-owned. A shadow that keeps the standard filter class but supplies its
# own ``extra`` factory (restricted queryset, non-default ``to_field_name``, ...)
# is a documented django-filter customization; whole-entry ownership now honors it
# instead of discarding it under Relay conversion.
# ======================================================================


def _register_relay(model):
    # Build the Relay-node type dynamically so each call gets a fresh type bound to
    # ``model`` (the autouse registry-isolation fixture clears it between tests).
    meta = type("Meta", (), {"model": model, "interfaces": (strawberry.relay.Node,)})
    relay_type = type(f"{model.__name__}RelayType", (DjangoType,), {"Meta": meta})
    apply_interfaces(relay_type, relay_type.__django_strawberry_definition__)
    return relay_type


@pytest.mark.django_db
def test_blocker1_m2m_extra_only_shadow_is_consumer_owned():
    """Same base M2M class + a consumer ``extra`` (restricted queryset) is honored."""
    import django_filters
    from django.db import models as dj_models
    from django_filters import filterset as df_filterset

    _register_relay(library_models.Genre)
    base_entry = df_filterset.BaseFilterSet.FILTER_DEFAULTS[dj_models.ManyToManyField]

    class BookFilter(FilterSet):
        FILTER_DEFAULTS = {
            **df_filterset.BaseFilterSet.FILTER_DEFAULTS,
            dj_models.ManyToManyField: {
                "filter_class": base_entry["filter_class"],  # SAME base class
                "extra": lambda f: {"queryset": library_models.Genre.objects.none()},
            },
        }

        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact"]}

    leaf = BookFilter.get_filters()["genres"]
    # The consumer's class survives -- NOT discarded for a package GlobalID.
    assert isinstance(leaf, django_filters.ModelMultipleChoiceFilter)
    assert not isinstance(leaf, GlobalIDMultipleChoiceFilter)
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "override_generated"
    assert "genres" not in BookFilter._expansion_snapshot().candidates
    # OBSERVABLE: the consumer's restricted queryset survived generation (a GlobalID
    # replacement would have stripped it as a model-choice-only extra).
    assert leaf.field.queryset.count() == 0


@pytest.mark.django_db
def test_blocker1_fk_extra_only_shadow_is_consumer_owned():
    """Same base FK class + a consumer ``extra`` (non-default to_field_name) is kept."""
    import django_filters
    from django.db import models as dj_models
    from django_filters import filterset as df_filterset

    _register_relay(library_models.Shelf)
    base_entry = df_filterset.BaseFilterSet.FILTER_DEFAULTS[dj_models.ForeignKey]

    class BookFilter(FilterSet):
        FILTER_DEFAULTS = {
            **df_filterset.BaseFilterSet.FILTER_DEFAULTS,
            dj_models.ForeignKey: {
                "filter_class": base_entry["filter_class"],  # SAME base class
                "extra": lambda f: {
                    "queryset": library_models.Shelf.objects.all(),
                    "to_field_name": "code",
                },
            },
        }

        class Meta:
            model = library_models.Book
            fields = {"shelf": ["exact"]}

    leaf = BookFilter.get_filters()["shelf"]
    assert isinstance(leaf, django_filters.ModelChoiceFilter)
    assert not isinstance(leaf, GlobalIDFilter)
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "override_generated"
    assert "shelf" not in BookFilter._expansion_snapshot().candidates
    # OBSERVABLE: the consumer's non-default to_field target survived.
    assert leaf.field.to_field_name == "code"


@pytest.mark.django_db
def test_blocker1_extra_only_shadow_survives_related_filter_expansion():
    """An ``extra``-only shadow on a child survives ``RelatedFilter`` expansion."""
    import django_filters
    from django.db import models as dj_models
    from django_filters import filterset as df_filterset

    _register_relay(library_models.Genre)
    base_entry = df_filterset.BaseFilterSet.FILTER_DEFAULTS[dj_models.ManyToManyField]

    class ChildBookFilter(FilterSet):
        FILTER_DEFAULTS = {
            **df_filterset.BaseFilterSet.FILTER_DEFAULTS,
            dj_models.ManyToManyField: {
                "filter_class": base_entry["filter_class"],
                "extra": lambda f: {"queryset": library_models.Genre.objects.none()},
            },
        }

        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact"]}

    class LoanParentFilter(FilterSet):
        book = RelatedFilter(ChildBookFilter, field_name="book")

        class Meta:
            model = library_models.Loan
            fields = {"note": ["exact"]}

    leaf = LoanParentFilter.get_filters()["book__genres"]
    assert isinstance(leaf, django_filters.ModelMultipleChoiceFilter)
    assert not isinstance(leaf, GlobalIDMultipleChoiceFilter)
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "override_generated"
    assert "book__genres" not in LoanParentFilter._expansion_snapshot().candidates
    assert leaf.field.queryset.count() == 0


@pytest.mark.django_db
def test_blocker1_extra_only_shadow_runs_outer_with_no_reserved_alias():
    """End-to-end: the honored ``extra``-only shadow runs OUTER, not through EXISTS."""
    import django_filters  # noqa: F401
    from django.db import models as dj_models
    from django_filters import filterset as df_filterset

    _register_relay(library_models.Genre)
    base_entry = df_filterset.BaseFilterSet.FILTER_DEFAULTS[dj_models.ManyToManyField]

    class BookFilter(FilterSet):
        FILTER_DEFAULTS = {
            **df_filterset.BaseFilterSet.FILTER_DEFAULTS,
            dj_models.ManyToManyField: {
                "filter_class": base_entry["filter_class"],
                "extra": lambda f: {"queryset": library_models.Genre._default_manager.all()},
            },
        }

        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact"]}

    BookFilter.get_filters()
    assert "genres" not in BookFilter._expansion_snapshot().candidates

    genre_a = library_models.Genre.objects.create(name="A")
    genre_b = library_models.Genre.objects.create(name="B")
    branch = library_models.Branch.objects.create(name="Central")
    shelf = library_models.Shelf.objects.create(code="S", branch=branch)
    book1 = library_models.Book.objects.create(title="book-1", shelf=shelf)
    book1.genres.add(genre_a)
    book2 = library_models.Book.objects.create(title="book-2", shelf=shelf)
    book2.genres.add(genre_b)
    book3 = library_models.Book.objects.create(title="book-3", shelf=shelf)
    book3.genres.add(genre_a, genre_b)

    # The consumer's ModelMultipleChoiceField cleans a raw pk list -- a shape the
    # discarded GlobalID primitive would have rejected -- proving the consumer ran.
    result = BookFilter(
        data={"genres": [str(genre_a.pk)]},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    ).qs
    assert _reserved_aliases(result) == []
    assert "EXISTS" not in str(result.query).upper()
    assert set(result.values_list("title", flat=True)) == {"book-1", "book-3"}


@pytest.mark.django_db
def test_blocker1_shallow_copy_untouched_entry_stays_framework_default():
    """Positive control: an untouched entry in a shallow-copied defaults map is NOT

    falsely treated as consumer-owned. A ``{**base, M2M: {...}}`` shadow that changes
    ONLY the M2M entry reuses the SAME nested object for the untouched forward-FK
    entry, so the FK relation stays ``framework_default`` and is still converted to
    the package GlobalID primitive, while the changed M2M entry is
    ``override_generated`` and keeps the consumer class.
    """
    from django.db import models as dj_models
    from django_filters import filterset as df_filterset

    _register_relay(library_models.Genre)
    _register_relay(library_models.Shelf)
    base_m2m = df_filterset.BaseFilterSet.FILTER_DEFAULTS[dj_models.ManyToManyField]

    class BookFilter(FilterSet):
        FILTER_DEFAULTS = {
            **df_filterset.BaseFilterSet.FILTER_DEFAULTS,
            dj_models.ManyToManyField: {
                "filter_class": base_m2m["filter_class"],
                "extra": lambda f: {"queryset": library_models.Genre.objects.none()},
            },
        }

        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact"], "shelf": ["exact"]}

    filters = BookFilter.get_filters()
    genres_field = library_models.Book._meta.get_field("genres")
    shelf_field = library_models.Book._meta.get_field("shelf")
    # The CHANGED M2M entry -> consumer-owned; class preserved.
    assert BookFilter._generation_origin_for_field(genres_field, "exact") == "override_generated"
    assert not isinstance(filters["genres"], GlobalIDMultipleChoiceFilter)
    # The UNTOUCHED FK entry (same object in the shallow copy) -> framework default;
    # still converted to the package GlobalID primitive.
    assert BookFilter._generation_origin_for_field(shelf_field, "exact") == "framework_default"
    assert isinstance(filters["shelf"], GlobalIDFilter)
