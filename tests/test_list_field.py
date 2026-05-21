"""Tests for ``django_strawberry_framework.list_field``.

Spec: ``docs/spec-016-list_field-0_0_7.md`` (Test plan section, the
``tests/test_list_field.py (new)`` subsection).

Package tests; system-under-test is ``django_strawberry_framework``
(spec rev5 L3 — framing matches ``AGENTS.md`` line 5). The file is the flat
single-file Layer-3 module's mirror per ``docs/TREE.md:453``.

This file is a SCAFFOLD authored under Slice 1 of the spec. The body
contains TODO test stubs that name every test the Test plan pins:

- 4 validation tests land in Slice 2 (``test_djangolistfield_rejects_*``).
- 14 behavior tests land in Slice 3 (``test_djangolistfield_*`` covering
  default resolver, async ``get_queryset``, dual-execution, sync coroutine
  rejection, sync + async consumer resolver shapes, outer nullability,
  root-position optimization, FK-id elision, ``Meta.primary`` interaction).

The TODO stubs intentionally do NOT import from
``django_strawberry_framework.list_field`` yet — the module currently
contains only pseudo-code (Slice 1 has not produced runnable code).
Importing it now would fail collection and break the 100% coverage gate.

Wire each stub up as the corresponding slice produces the implementation:

    Slice 1 → fill in ``_DjangoTypeFixture``-style fixtures + ensure
              ``DjangoListField`` is importable from the package root.
    Slice 2 → un-skip the 4 validation tests; implement bodies.
    Slice 3 → un-skip the 14 behavior tests; implement bodies.
"""

import pytest
from apps.products.models import Category

from django_strawberry_framework import DjangoListField, DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_global_registry() -> None:
    """Clear the global registry on entry/exit so tests touching it don't leak.

    Mirrors the autouse fixture in ``tests/test_registry.py:34-39``. Tests
    that declare ``DjangoType`` subclasses at function scope would otherwise
    leave registered types behind for subsequent tests.
    """
    registry.clear()
    yield
    registry.clear()


# =============================================================================
# Slice 2 — Validation tests (Decision 5).
# =============================================================================
#
# Each test below maps one-to-one with a bullet in the Test plan's
# "Validation tests (Slice 2)" subsection. They assert that the constructor
# raises ``ConfigurationError`` with the documented message shape.


@pytest.mark.parametrize(
    "non_class",
    [
        "BranchType",
        42,
        DjangoType(),
        None,
    ],
)
def test_djangolistfield_rejects_non_class_argument(non_class: object) -> None:
    """Non-class arguments trip the first guard (spec line 546)."""
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField requires a DjangoType class; got",
    ):
        DjangoListField(non_class)  # type: ignore[arg-type]


def test_djangolistfield_rejects_non_djangotype_class() -> None:
    """A plain class that doesn't subclass ``DjangoType`` is rejected (spec line 547)."""

    class NotADjangoType:
        pass

    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField requires a DjangoType subclass; got NotADjangoType",
    ):
        DjangoListField(NotADjangoType)


def test_djangolistfield_rejects_djangotype_without_definition() -> None:
    """An abstract ``DjangoType`` base without ``Meta`` is rejected (spec line 548).

    Per ``types/base.py:156-158``, the absence of a ``Meta`` makes
    ``__init_subclass__`` return early WITHOUT setting
    ``__django_strawberry_definition__`` (assigned at
    ``types/base.py:245``), so ``hasattr(..., "__django_strawberry_definition__")``
    is the discriminator the guard relies on.
    """

    class AbstractBase(DjangoType):
        pass

    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField target AbstractBase is not a registered DjangoType",
    ):
        DjangoListField(AbstractBase)


def test_djangolistfield_rejects_non_callable_resolver() -> None:
    """A non-callable ``resolver=`` is rejected after target-type guards pass (spec line 549)."""

    class _T(DjangoType):
        class Meta:
            model = Category

    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField resolver must be callable\.",
    ):
        DjangoListField(_T, resolver="not callable")  # type: ignore[arg-type]


# (Rev2 H2 — DROPPED — ``test_djangolistfield_rejects_non_bool_nullable_list``
# is NOT planned. ``nullable_list=`` is not a constructor argument; outer
# nullability is driven entirely by the consumer's class-attribute annotation.)


# =============================================================================
# Slice 3 — Behavior tests (Decisions 2, 3, 4, 6).
# =============================================================================
#
# Slice 3 ships 14 tests (rev5 M1 — one-to-one with the named methods in the
# spec Test plan; rev5 M3 — adds the dual-execution test). Each TODO bullet
# below corresponds to one named test.


# TODO(spec-016, Slice 3 — Decision 2 default resolver sync path):
# ``test_djangolistfield_default_resolver_returns_queryset_filtered_by_get_queryset``
# — declare a ``DjangoType`` whose ``get_queryset`` filters ``is_private=False``;
# assert the default resolver returns a queryset that excludes private rows.


# TODO(spec-016, Slice 3 — Decision 2 default resolver async path):
# ``test_djangolistfield_async_get_queryset_is_awaited`` — declare a
# ``DjangoType`` with an ``async def get_queryset(...)``; assert the default
# resolver awaits the coroutine in an async context and returns the
# filtered queryset.


# TODO(spec-016, Slice 3 — rev5 M3 dual-execution):
# ``test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution``
# — declare a ``DjangoType`` with a SYNC ``get_queryset(...)``; execute the
# field via ``schema.execute_sync(...)`` AND ``await schema.execute(...)``;
# assert both return the filtered queryset. Pins the runtime
# ``in_async_context()`` branch in the default resolver (the case where
# ``in_async_context()`` is True but ``get_queryset`` is sync). Without this
# test the dual-execution shape promised in Edge cases is unverified.


# TODO(spec-016, Slice 3 — Decision 3 coroutine rejection):
# ``test_djangolistfield_sync_path_rejects_coroutine_from_get_queryset`` —
# declare a ``DjangoType`` with an ``async def get_queryset(...)``; assert
# the sync resolver path raises ``ConfigurationError`` matching the
# ``types/relay.py:215-220`` contract.


# TODO(spec-016, Slice 3 — rev2 H1 graphene-django parity, sync queryset):
# ``test_djangolistfield_consumer_resolver_queryset_return_gets_get_queryset_applied``
# — supply a SYNC ``resolver=`` returning ``Model.objects.filter(...)``;
# give the target a ``get_queryset`` that filters out a known row; assert
# that row is absent from the field's output.


# TODO(spec-016, Slice 3 — rev2 H1 graphene-django parity, sync list):
# ``test_djangolistfield_consumer_resolver_python_list_return_passes_through``
# — supply a SYNC ``resolver=`` returning a Python ``list[T]`` containing a
# row that ``get_queryset`` would have filtered out; assert the row
# survives (``get_queryset`` is NOT applied to non-queryset returns).


# TODO(spec-016, Slice 3 — rev4 H2 async parity, queryset):
# ``test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied``
# — supply an ``async def resolver(...)`` returning ``Model.objects.filter(...)``;
# execute through Strawberry's async schema execution; assert the queryset
# has been threaded through ``target_type.get_queryset(qs, info)`` exactly
# the same way as the sync test. Pins that the wrapper awaits the consumer
# coroutine BEFORE the isinstance check.


# TODO(spec-016, Slice 3 — rev4 H2 async parity, list):
# ``test_djangolistfield_async_consumer_resolver_python_list_return_passes_through``
# — supply an ``async def resolver(...)`` returning a Python ``list[T]``;
# assert ``target_type.get_queryset(...)`` is NOT applied. Pins that the
# await-then-isinstance ordering is symmetric across return shapes.


# TODO(spec-016, Slice 3 — rev2 M3 root-only optimizer cooperation):
# ``test_djangolistfield_at_root_position_is_optimized`` — declare a
# ``DjangoType`` with relations; query through a root ``DjangoListField``
# with a nested selection; assert the optimizer planned ``select_related``
# / ``prefetch_related`` (via ``assertNumQueries`` / SQL-sniffer pattern).
# This is the regression net for the root-only contract (Decision 4).


# TODO(spec-016, Slice 3 — rev2 H2 nullable outer):
# ``test_djangolistfield_nullable_outer_via_consumer_annotation`` — declare
# ``field_or_none: list[BranchType] | None = DjangoListField(BranchType)``;
# assert the rendered GraphQL type is ``[BranchType!]`` (nullable outer,
# non-null items).


# TODO(spec-016, Slice 3 — rev2 H2 non-nullable outer default):
# ``test_djangolistfield_non_nullable_outer_default_via_consumer_annotation``
# — declare ``field: list[BranchType] = DjangoListField(BranchType)``;
# assert the rendered GraphQL type is ``[BranchType!]!`` (non-null outer,
# non-null items).


# TODO(spec-016, Slice 3 — FK-id elision):
# ``test_djangolistfield_fk_id_elision_survives`` — query
# ``{ allBranches { shelves { id } } }`` (or equivalent); assert no JOIN
# was issued for the ``id``-only relation selection (FK-id elision still
# fires).


# TODO(spec-016, Slice 3 — Decision 6 primary target):
# ``test_djangolistfield_with_meta_primary_true_returns_primary_queryset``
# — declare two ``DjangoType``s on the same model, one with
# ``Meta.primary = True``; ``DjangoListField(PrimaryType)`` returns rows
# queried via the primary's ``get_queryset``.


# TODO(spec-016, Slice 3 — Decision 6 secondary target):
# ``test_djangolistfield_with_secondary_target_uses_secondary_get_queryset``
# — declare two types, point the field at the SECONDARY; assert the
# secondary's ``get_queryset`` is applied, not the primary's.
