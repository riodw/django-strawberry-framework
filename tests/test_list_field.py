"""DjangoListField tests for validation, resolvers, visibility, optimization, sidecars, and permissions.

Spec: ``docs/SPECS/spec-020-list_field-0_0_7.md``.

Package tests; system-under-test is ``django_strawberry_framework``
(``AGENTS.md #"Package source lives in django_strawberry_framework"``). The file
is the flat single-file Layer-3 module's mirror per ``docs/TREE.md #"test_list_field.py       # DjangoListField (single-file Layer-3 module)"``.

Holds the validation cluster (5 tests) and the behavior
cluster (17 tests) - 22 total. Three of them cover real bug fixes -
the own-class-registration guard (rejects a ``DjangoType`` subclass that omits
its own ``Meta``), the async-callable-object detection (detects
``async def __call__`` at construction time so the coroutine return
doesn't bypass ``_post_process_consumer_async``), and the
``functools.partial``-wrapped async-callable-*instance* detection
(``is_async_callable`` now unwraps ``partial.func`` before the
``__call__`` async check - without it that resolver was misclassified as
sync and skipped ``get_queryset``). The fourth is a contract pin for
``functools.partial``-wrapped async *functions*:
``inspect.iscoroutinefunction`` looks through ``functools.partial``
natively (3.8+), so the first branch already routes them; the test pins
the end-to-end behavior.

The spec's inventory at ``docs/SPECS/spec-020-list_field-0_0_7.md #"Optional ``resolver=`` constructor argument that overrides the default body"`` calls out
"``Manager``/``QuerySet``" together for the consumer-resolver returns;
both arms are load-bearing (the field wrapper owns the
``Manager -> QuerySet`` coercion; the optimizer's downstream coercion is
a safety net, not a substitute). The **sync** ``Manager``-return arm
lives in ``examples/fakeshop/test_query/test_library_api.py::
test_library_branches_via_djangolistfield_consumer_manager_resolver_over_http``
per the live-HTTP-first rule at ``examples/fakeshop/test_query/README.md #"**Coverage rule.**"``;
the **async** ``Manager``-return arm stays here because async resolvers
are genuinely unreachable from the sync ``GraphQLView`` mounted at
``/graphql/`` (Strawberry's sync execution rejects them with
``RuntimeError: GraphQL execution failed to complete synchronously``).
"""

import asyncio
import functools
import inspect
import pickle
import subprocess
import sys
import time
from types import SimpleNamespace
from typing import Any

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category, Item
from asgiref.sync import sync_to_async
from django.db import models
from django.db.models import Prefetch
from django.test import RequestFactory
from graphql import GraphQLError
from strawberry.schema_directive import Location as _DirectiveLocation
from strawberry.schema_directive import schema_directive as _schema_directive
from strawberry.types import Info

from django_strawberry_framework import (
    DjangoListField,
    DjangoOptimizerExtension,
    DjangoType,
    ListArgumentError,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import (
    ConfigurationError,
    DjangoStrawberryFrameworkError,
)
from django_strawberry_framework.list_field import (
    _ListArguments,
    _normalize_list_arguments,
    _resolve_argument_wire_name,
    _synthesized_list_signature,
)
from django_strawberry_framework.permissions import apply_cascade_permissions
from django_strawberry_framework.registry import registry
from django_strawberry_framework.resource_policy import (
    ResourcePolicy,
    stash_resource_policy,
)
from django_strawberry_framework.types.relay import SyncMisuseError


@pytest.fixture(autouse=True)
def _isolate_global_registry() -> None:
    """Clear the global registry on entry/exit so tests touching it don't leak.

    Mirrors the autouse fixture in ``tests/test_registry.py::_isolate_global_registry``. Tests
    that declare ``DjangoType`` subclasses at function scope would otherwise
    leave registered types behind for subsequent tests.
    """
    registry.clear()
    yield
    registry.clear()


# =============================================================================
# Validation tests (Decision 5).
# =============================================================================
#
# Each test below maps one-to-one with a bullet in the spec's validation test
# plan. They assert that the constructor raises ``ConfigurationError`` with the
# documented message shape.


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
    """Non-class arguments trip the first guard (spec #"DjangoListField requires a DjangoType class; got <repr>")."""
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField requires a DjangoType class; got",
    ):
        DjangoListField(non_class)  # type: ignore[arg-type]


def test_djangolistfield_rejects_non_djangotype_class() -> None:
    """A plain class that doesn't subclass ``DjangoType`` is rejected (spec #"DjangoListField requires a DjangoType subclass; got <name>")."""

    class NotADjangoType:
        pass

    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField requires a DjangoType subclass; got NotADjangoType",
    ):
        DjangoListField(NotADjangoType)


def test_djangolistfield_rejects_djangotype_without_definition() -> None:
    """An abstract ``DjangoType`` base without ``Meta`` is rejected (spec #"is not a registered DjangoType (no __django_strawberry_definition__)").

    Per ``django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"if meta is None:"``, the absence of a ``Meta`` makes
    ``__init_subclass__`` return early WITHOUT setting
    ``__django_strawberry_definition__`` (assigned at
    ``django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__django_strawberry_definition__ = definition"``), so ``hasattr(..., "__django_strawberry_definition__")``
    is the discriminator the guard relies on.
    """

    class AbstractBase(DjangoType):
        pass

    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField target AbstractBase is not a registered DjangoType",
    ):
        DjangoListField(AbstractBase)


def test_djangolistfield_rejects_djangotype_subclass_without_own_meta() -> None:
    """Subclass of a concrete ``DjangoType`` without its own ``Meta`` is rejected.

    Pins the own-class registration invariant at ``list_field.py``'s
    ``definition.origin is target_type`` guard.
    ``__django_strawberry_definition__`` is assigned in
    ``DjangoType.__init_subclass__`` (``django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__django_strawberry_definition__ = definition"``) and inherited via
    MRO; a subclass that omits ``Meta`` would otherwise pass the guard via the
    parent's definition and bind the field to a target whose model, selected
    fields, and ``Meta.primary`` state belong to the parent class.
    """

    class ParentCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ChildCategoryType(ParentCategoryType):
        pass

    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField target ChildCategoryType is not a registered DjangoType",
    ):
        DjangoListField(ChildCategoryType)


def test_djangolistfield_rejects_non_callable_resolver() -> None:
    """A non-callable ``resolver=`` is rejected after target-type guards pass (spec #"DjangoListField resolver must be callable")."""

    class _T(DjangoType):
        class Meta:
            model = Category

    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField resolver must be callable\.",
    ):
        DjangoListField(_T, resolver="not callable")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Hostile constructor seams (0.0.15 hunt). The guards' rejection messages
# interpolate deployment-supplied values, so each render must be guarded, the
# definition READ must be contained, and the ``directives=`` forward must
# carry the same hostile-container containment every field factory now shares
# (``utils/directives.py::validated_field_directives``) and
# ``connection.py::DjangoConnectionField`` still inlines.
# ---------------------------------------------------------------------------


class _HostileRepr:
    """A deployment value whose repr detonates."""

    def __repr__(self) -> str:
        raise RuntimeError("hostile __repr__ detonated")


class _HostileNameMeta(type):
    """A metaclass whose ``__name__`` read detonates.

    CPython enforces a str ``__qualname__`` at class creation but NOT a
    readable ``__name__``: the property shadows the ``type.__name__`` getset
    descriptor in the metaclass MRO.
    """

    @property
    def __name__(cls) -> str:  # type: ignore[override]
        raise RuntimeError("hostile __name__ detonated")


class _DefinitionTrapMeta(type):
    """A metaclass whose ``__getattr__`` raises a NON-AttributeError for the definition."""

    def __getattr__(cls, name: str):
        if name == "__django_strawberry_definition__":
            raise RuntimeError("hostile definition read detonated")
        raise AttributeError(name)


class _ExplodingDirectives:
    """A hostile directives container that raises mid-iteration."""

    def __iter__(self):
        yield _ProbeTag()
        raise ValueError("hostile iterator detonated midway")


@_schema_directive(locations=[_DirectiveLocation.FIELD_DEFINITION], name="probeTag")
class _ProbeTag:
    """A REAL directive instance for the pass-through positive control."""

    marker: str = "probe"


def test_djangolistfield_non_class_guard_survives_a_hostile_repr() -> None:
    """The non-class arm renders through ``_safe_arg_repr`` (mutation-guard parity).

    Pre-fix the raise-site f-string interpolated ``{target_type!r}`` directly,
    so a hostile ``__repr__`` detonated the message assembly and the raw
    RuntimeError replaced the promised typed rejection.
    """
    with pytest.raises(ConfigurationError, match="requires a DjangoType class"):
        DjangoListField(_HostileRepr())  # type: ignore[arg-type]


def test_djangolistfield_non_djangotype_guard_survives_a_hostile_metaclass_name() -> None:
    """The subclass arm renders through ``_safe_class_name``.

    Pre-fix ``{target_type.__name__}`` detonated on a metaclass whose
    ``__name__`` property raises.
    """

    class NotADjangoType(metaclass=_HostileNameMeta):
        pass

    with pytest.raises(ConfigurationError, match="requires a DjangoType subclass"):
        DjangoListField(NotADjangoType)


def test_djangolistfield_unregistered_guard_survives_a_hostile_metaclass_name() -> None:
    """The own-class arm renders ``_safe_class_name`` for BOTH name interpolations.

    Pre-fix ``{target_type.__name__}`` appeared twice in the message and either
    read detonated the assembly.
    """

    class AbstractBase(DjangoType, metaclass=_HostileNameMeta):
        pass

    with pytest.raises(ConfigurationError, match="is not a registered DjangoType"):
        DjangoListField(AbstractBase)


def test_djangolistfield_definition_read_failure_is_typed_not_raw() -> None:
    """A raising non-AttributeError from the definition read fails the typed reject.

    ``getattr(target, name, None)`` suppresses only ``AttributeError``; pre-fix
    a metaclass ``__getattr__`` raising anything else escaped raw instead of
    reaching the "not a registered DjangoType" rejection (fail closed - a
    read that cannot be answered is a target that cannot be PROVEN
    registered).
    """

    class TrappedBase(DjangoType, metaclass=_DefinitionTrapMeta):
        pass

    with pytest.raises(ConfigurationError, match="is not a registered DjangoType"):
        DjangoListField(TrappedBase)


def test_djangolistfield_rejects_bare_string_directives() -> None:
    """A bare str is iterated element-wise by Strawberry - rejected typed instead."""
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField directives must be a sequence of directive instances",
    ):
        DjangoListField(_DirectiveHolderType(), directives="not-a-directive-list")  # type: ignore[arg-type]


def test_djangolistfield_rejects_bare_bytes_directives() -> None:
    """A bare bytes iterates into ints downstream - rejected typed instead."""
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField directives must be a sequence of directive instances",
    ):
        DjangoListField(_DirectiveHolderType(), directives=b"\x01\x02")  # type: ignore[arg-type]


def test_djangolistfield_rejects_non_iterable_directives() -> None:
    """A non-iterable detonated raw TypeError inside strawberry.field pre-fix."""
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField directives could not be read",
    ):
        DjangoListField(_DirectiveHolderType(), directives=42)  # type: ignore[arg-type]


def test_djangolistfield_rejects_hostile_iterator_directives() -> None:
    """An iterator raising midway escaped raw ValueError pre-fix - now typed."""
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField directives could not be read",
    ):
        DjangoListField(_DirectiveHolderType(), directives=_ExplodingDirectives())  # type: ignore[arg-type]


def test_djangolistfield_passes_real_directive_instances_through() -> None:
    """Positive control: a real directive instance tuple constructs unchanged."""
    field = DjangoListField(_DirectiveHolderType(), directives=(_ProbeTag(),))
    assert field is not None


def test_djangolistfield_default_directives_omitted_constructs() -> None:
    """Positive control: the () default keeps constructing (no new posture)."""
    field = DjangoListField(_DirectiveHolderType())
    assert field is not None


def _DirectiveHolderType() -> type:
    """A concrete DjangoType the directives rows can bind (guards run first)."""

    class DirectiveHolderType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    return DirectiveHolderType


# ``test_djangolistfield_rejects_non_bool_nullable_list`` is deliberately NOT
# planned: ``nullable_list=`` is not a constructor argument; outer
# nullability is driven entirely by the consumer's class-attribute annotation.)


# =============================================================================
# Behavior tests (Decisions 2, 3, 4, 6).
# =============================================================================
#
# One test per named method in the spec test plan, plus the dual-execution
# test. Tests pin the
# production contract through ``schema.execute_sync(...)`` /
# ``await schema.execute(...)`` against real Django models; the autouse
# fixture above isolates each test's registry state.


# -----------------------------------------------------------------------------
# Group A - Default-resolver shape and ``cls.get_queryset`` invocation.
# -----------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_async_get_queryset_is_awaited() -> None:
    """Default resolver awaits an ``async def get_queryset(...)`` under ``await schema.execute(...)``.

    Pins the async branch at ``django_strawberry_framework/list_field.py::DjangoListField #"if in_async_context():"`` - the
    ``apply_type_visibility_async(target_type, qs, info)`` call when
    ``in_async_context()`` returns True and ``get_queryset`` is
    ``async def`` (spec Decision 2 async path; Decision 3
    ``apply_type_visibility_async``; spec #"test_djangolistfield_async_get_queryset_is_awaited").
    The adapter protocol enables safe async list completion without DJANGO_ALLOW_ASYNC_UNSAFE.
    """
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        async def get_queryset(cls, queryset, info, **kwargs):
            return await sync_to_async(
                lambda: queryset.exclude(name__startswith="a"),
            )()

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = await schema.execute("{ allCategories { id name } }")
    assert result.errors is None
    names = [row["name"] for row in result.data["allCategories"]]
    assert names, "expected at least one non-filtered Category row"
    assert all(not name.startswith("a") for name in names)


# -----------------------------------------------------------------------------
# Group B - Dual-execution.
# -----------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution() -> (
    None
):
    """A sync ``get_queryset`` resolves correctly under both schema-execution shapes.

    Pins the runtime ``in_async_context()`` branch at ``django_strawberry_framework/list_field.py::DjangoListField #"if in_async_context():"``
    - both arms when ``get_queryset`` is SYNC. The ``False`` arm fires
    under ``schema.execute_sync(...)`` (returns ``apply_type_visibility_sync``
    directly); the ``True`` arm fires under ``await schema.execute(...)``
    (returns the coroutine from ``apply_type_visibility_async`` for
    Strawberry's ``AwaitableOrValue`` dispatch). The Edge cases section
    (spec #"`schema.execute_sync` testing") promises both call shapes work; without
    this test the promise is unverified.
    The adapter protocol enables safe async list completion without DJANGO_ALLOW_ASYNC_UNSAFE.
    """
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(name__startswith="a")

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    sync_result = await sync_to_async(schema.execute_sync)(
        "{ allCategories { id name } }",
    )
    async_result = await schema.execute("{ allCategories { id name } }")
    assert sync_result.errors is None
    assert async_result.errors is None
    assert sync_result.data == async_result.data
    names = [row["name"] for row in sync_result.data["allCategories"]]
    assert names, "expected at least one non-filtered Category row"
    assert all(not name.startswith("a") for name in names)


# -----------------------------------------------------------------------------
# Group C - Sync coroutine rejection (Decision 3).
# -----------------------------------------------------------------------------


@pytest.mark.django_db
def test_djangolistfield_sync_path_rejects_coroutine_from_get_queryset() -> None:
    """Sync resolver path raises ``ConfigurationError`` when ``get_queryset`` is async.

    Pins the coroutine-rejection guard at ``django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync #"returned a coroutine in a sync"``. The
    field reuses the production helper per Decision 3 Option A
    (spec #"This spec picks **Option A** for `0.0.7`"); this test asserts the production
    message prefix rather than re-implementing the rejection in a test mock
    (spec #"test_djangolistfield_sync_path_rejects_coroutine_from_get_queryset").
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        async def get_queryset(cls, queryset, info, **kwargs):
            return queryset

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ allCategories { id name } }")
    assert result.errors is not None
    assert len(result.errors) == 1
    # The typed ``SyncMisuseError`` raised by ``apply_type_visibility_sync``
    # surfaces as the GraphQL error's ``original_error`` so consumers
    # can match it directly without substring inspection.
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert "returned a coroutine in a sync resolver context" in str(result.errors[0])


def test_djangolistfield_sync_path_rejects_custom_awaitable_from_get_queryset() -> None:
    """A truthy custom awaitable cannot escape the sync visibility boundary."""

    class DeferredQueryset:
        def __await__(self):
            if False:
                yield None
            return Category.objects.all()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return DeferredQueryset()

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType)

    finalize_django_types()
    result = strawberry.Schema(query=Query).execute_sync("{ allCategories { id } }")

    assert result.errors is not None
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert "returned an awaitable in a sync resolver context" in str(result.errors[0])


# -----------------------------------------------------------------------------
# Group D - Sync consumer-resolver paths.
# -----------------------------------------------------------------------------


@pytest.mark.django_db
def test_djangolistfield_consumer_resolver_queryset_return_gets_get_queryset_applied() -> None:
    """Sync consumer resolver returning a ``QuerySet`` receives ``target_type.get_queryset(...)``.

    Pins the sync consumer-resolver wrapper at ``django_strawberry_framework/list_field.py::DjangoListField #"return _post_process_consumer_sync("``
    - specifically that ``_post_process_consumer_sync`` (the inner call
    site) applies ``target_type.get_queryset(...)`` to a ``Manager``/``QuerySet``
    return (graphene-django parity; spec #"test_djangolistfield_consumer_resolver_queryset_return_gets_get_queryset_applied").
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(name__startswith="a")

    def _resolver(root: Any, info: Info) -> Any:
        return Category.objects.all()

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType, resolver=_resolver)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ allCategories { id name } }")
    assert result.errors is None
    names = [row["name"] for row in result.data["allCategories"]]
    assert names, "expected at least one non-filtered Category row"
    assert all(not name.startswith("a") for name in names)


# The sync ``Manager``-return arm (``django_strawberry_framework/utils/querysets.py::_coerced_manager_queryset`` coverage) lives in
# ``examples/fakeshop/test_query/test_library_api.py::test_library_branches_via_djangolistfield_consumer_manager_resolver_over_http``
# per the live-HTTP-first rule at ``examples/fakeshop/test_query/README.md #"**Coverage rule.**"``.


@pytest.mark.django_db
def test_djangolistfield_consumer_resolver_python_list_return_passes_through() -> None:
    """Sync consumer resolver returning a Python ``list`` bypasses ``target_type.get_queryset(...)``.

    Pins the sync consumer-resolver wrapper at ``django_strawberry_framework/list_field.py::DjangoListField #"return _post_process_consumer_sync("``
    - specifically that ``_post_process_consumer_sync`` returns the
    non-``QuerySet`` result unchanged (the ``return source``
    pass-through arm at ``django_strawberry_framework/utils/querysets.py::post_process_queryset_result_sync #"return source"``; spec #"test_djangolistfield_consumer_resolver_python_list_return_passes_through"). The resolver returns a
    Python ``list`` that contains a row matching the ``get_queryset``
    exclusion filter; the row's presence in the output proves
    ``get_queryset`` was NOT applied to the list return.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(name__startswith="a")

    def _resolver(root: Any, info: Info) -> Any:
        return list(Category.objects.all())

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType, resolver=_resolver)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ allCategories { id name } }")
    assert result.errors is None
    names = [row["name"] for row in result.data["allCategories"]]
    assert any(name.startswith("a") for name in names), (
        "expected an 'a'-prefixed row to survive when consumer returned a list "
        "(get_queryset would have filtered it from a QuerySet return)"
    )


# -----------------------------------------------------------------------------
# Group E - Async consumer-resolver paths.
# -----------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied() -> (
    None
):
    """Async consumer resolver returning a ``QuerySet`` receives ``target_type.get_queryset(...)``.

    Pins the async consumer-resolver wrapper at ``django_strawberry_framework/list_field.py::DjangoListField #"return await _post_process_consumer_async("``
    - specifically that the awaited consumer return is fed to
    ``_post_process_consumer_async`` (the ``await _post_process_consumer_async(...)`` call
    inside the async ``_wrap``), and the
    ``apply_type_visibility_async`` call (``django_strawberry_framework/utils/querysets.py::post_process_queryset_result_async #"return await apply_type_visibility_async"``) fires on a ``QuerySet``
    result. Pins that the wrapper awaits the consumer coroutine BEFORE
    the isinstance check (spec #"test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied").
    The adapter protocol enables safe async list completion without DJANGO_ALLOW_ASYNC_UNSAFE.
    """
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(name__startswith="a")

    async def _resolver(root: Any, info: Info) -> Any:
        return await sync_to_async(lambda: Category.objects.all())()

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType, resolver=_resolver)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = await schema.execute("{ allCategories { id name } }")
    assert result.errors is None
    names = [row["name"] for row in result.data["allCategories"]]
    assert names, "expected at least one non-filtered Category row"
    assert all(not name.startswith("a") for name in names)


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_async_consumer_resolver_manager_return_gets_get_queryset_applied() -> (
    None
):
    """Async consumer resolver returning a ``Manager`` receives ``target_type.get_queryset(...)``.

    Pins the async field-wrapper's ``Manager -> QuerySet`` coercion at
    ``django_strawberry_framework/utils/querysets.py::normalize_query_source #"return _coerced_manager_queryset(source), True"`` - ``normalize_query_source``
    coerces a ``Manager`` return through ``_coerced_manager_queryset`` BEFORE
    the is-queryset check so the subsequent ``await apply_type_visibility_async(...)`` runs on a
    real ``QuerySet`` (symmetric with the sync path; spec #"the **field wrapper** owns the `Manager -> QuerySet` coercion").
    The adapter protocol enables safe async list completion without DJANGO_ALLOW_ASYNC_UNSAFE.
    """
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(name__startswith="a")

    async def _resolver(root: Any, info: Info) -> Any:
        # Return the ``Manager`` itself, not a ``QuerySet`` - exercises
        # the coercion branch at ``django_strawberry_framework/utils/querysets.py::_coerced_manager_queryset``.
        return Category.objects

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType, resolver=_resolver)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = await schema.execute("{ allCategories { id name } }")
    assert result.errors is None
    names = [row["name"] for row in result.data["allCategories"]]
    assert names, "expected at least one non-filtered Category row"
    assert all(not name.startswith("a") for name in names)


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied() -> None:
    """Callable instance with ``async def __call__`` is detected as async at construction.

    Pins ``is_async_callable`` detection of callable objects whose
    ``__call__`` is ``async def`` (``list_field.py``'s helper).
    ``inspect.iscoroutinefunction(instance)`` is False for such objects, but
    ``inspect.iscoroutinefunction(instance.__call__)`` is True - the factory
    must dispatch to the async wrapper either way. Without this, the sync
    wrapper would call the instance, receive a coroutine, find no
    ``Manager``/``QuerySet`` to coerce, and pass the coroutine through; under
    async schema execution Strawberry would still await the coroutine and
    silently skip ``target_type.get_queryset(...)``.
    """
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(name__startswith="a")

    class _AsyncResolver:
        async def __call__(self, root: Any, info: Info) -> Any:
            return await sync_to_async(lambda: Category.objects.all())()

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(
            CategoryType,
            resolver=_AsyncResolver(),
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = await schema.execute("{ allCategories { id name } }")
    assert result.errors is None
    names = [row["name"] for row in result.data["allCategories"]]
    assert names, "expected at least one non-filtered Category row"
    assert all(not name.startswith("a") for name in names)


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_async_staticmethod_resolver_gets_get_queryset_applied() -> None:
    """A ``@staticmethod async def`` resolver referenced in its class body dispatches async.

    The class-body name is the raw, callable ``staticmethod`` descriptor. Without
    unwrapping its ``.__func__``, it is misclassified as sync and its coroutine
    return raises ``SyncMisuseError``. The visibility exclusion proves the fixed
    path awaited the resolver and applied async post-processing.
    """
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(name__startswith="a")

    @strawberry.type
    class Query:
        @staticmethod
        async def _resolve(root: Any, info: Info) -> Any:
            return await sync_to_async(lambda: Category.objects.all())()

        # ``_resolve`` here is the raw ``staticmethod`` descriptor (class-body scope).
        all_categories: list[CategoryType] = DjangoListField(CategoryType, resolver=_resolve)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = await schema.execute("{ allCategories { id name } }")
    assert result.errors is None
    names = [row["name"] for row in result.data["allCategories"]]
    assert names, "expected at least one non-filtered Category row"
    assert all(not name.startswith("a") for name in names)


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_partial_wrapped_async_resolver_gets_get_queryset_applied() -> None:
    """``functools.partial`` wrapping an ``async def`` resolver is detected as async.

    Contract pin (not a fix for a bug that exists today): Python's
    ``inspect.iscoroutinefunction`` looks through ``functools.partial`` wrappers
    natively since 3.8 (empirically verified against the installed Python), so
    the first branch of ``is_async_callable`` already routes
    partial-wrapped async resolvers to the async wrapper. This test pins that
    contract end-to-end through the field's pipeline: ``get_queryset``'s
    ``startswith("a")`` exclusion fires on the awaited QuerySet, proving the
    partial reached ``_post_process_consumer_async`` and not the sync wrapper.
    An explicit ``.func`` unwrap is in place as well. For this shape (partial of
    a plain ``async def``)
    ``inspect.iscoroutinefunction(partial(async_fn))`` is True directly, so the
    first branch already routes it - but the unwrap is load-bearing for the
    partial-of-async-*instance* shape (see
    ``test_djangolistfield_partial_wrapped_async_callable_object_resolver_gets_get_queryset_applied``).
    This test pins the function-partial path regardless.
    """
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(name__startswith="a")

    async def _async_resolver(prefix: str, root: Any, info: Info) -> Any:
        # The ``prefix`` arg makes the partial application non-trivial; the
        # remaining signature ``(root, info)`` is what Strawberry inspects.
        return await sync_to_async(lambda: Category.objects.all())()

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(
            CategoryType,
            resolver=functools.partial(_async_resolver, "ignored"),
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = await schema.execute("{ allCategories { id name } }")
    assert result.errors is None
    names = [row["name"] for row in result.data["allCategories"]]
    assert names, "expected at least one non-filtered Category row"
    assert all(not name.startswith("a") for name in names)


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_partial_wrapped_async_callable_object_resolver_gets_get_queryset_applied() -> (
    None
):
    """``functools.partial`` wrapping an async callable *instance* is detected as async.

    The combination the other two async-resolver tests miss: a
    ``functools.partial`` whose ``.func`` is a callable object with
    ``async def __call__``. ``inspect.iscoroutinefunction(partial)`` unwraps to
    the instance (not a coroutine function -> False) and ``partial.__call__`` is
    the partial's own ``__call__`` (also False), so before ``is_async_callable``
    unwrapped the partial first this resolver was misclassified as sync - its
    coroutine return bypassed ``_post_process_consumer_async`` and silently
    skipped ``target_type.get_queryset(...)``.
    Pins the ``.func`` unwrap fix: ``get_queryset``'s ``startswith("a")`` exclusion
    must fire on the awaited QuerySet.
    """
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(name__startswith="a")

    class _AsyncResolver:
        async def __call__(
            self,
            prefix: str,
            root: Any,
            info: Info,
        ) -> Any:
            # ``prefix`` makes the partial application non-trivial; the remaining
            # ``(root, info)`` is what Strawberry inspects.
            return await sync_to_async(lambda: Category.objects.all())()

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(
            CategoryType,
            resolver=functools.partial(_AsyncResolver(), "ignored"),
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = await schema.execute("{ allCategories { id name } }")
    assert result.errors is None
    names = [row["name"] for row in result.data["allCategories"]]
    assert names, "expected at least one non-filtered Category row"
    assert all(not name.startswith("a") for name in names)


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_async_consumer_resolver_python_list_return_passes_through() -> None:
    """Async consumer resolver returning a Python ``list`` bypasses ``target_type.get_queryset(...)``.

    Pins the async consumer-resolver wrapper at ``django_strawberry_framework/list_field.py::DjangoListField #"return await _post_process_consumer_async("``
    - specifically that ``_post_process_consumer_async`` returns a
    non-``QuerySet`` result unchanged (the ``return source``
    pass-through arm at ``django_strawberry_framework/utils/querysets.py::post_process_queryset_result_async #"return source"``). Pins that the await-then-isinstance
    ordering is symmetric across return shapes (spec #"test_djangolistfield_async_consumer_resolver_python_list_return_passes_through").
    """
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(name__startswith="a")

    async def _resolver(root: Any, info: Info) -> Any:
        return await sync_to_async(lambda: list(Category.objects.all()))()

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType, resolver=_resolver)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = await schema.execute("{ allCategories { id name } }")
    assert result.errors is None
    names = [row["name"] for row in result.data["allCategories"]]
    assert any(name.startswith("a") for name in names), (
        "expected an 'a'-prefixed row to survive when async consumer returned a list "
        "(get_queryset would have filtered it from a QuerySet return)"
    )


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_async_consumer_resolver_async_iterable_is_bounded() -> None:
    """An async iterable return is capped before graphql-core materializes it.

    ``graphql-core`` accepts ``AsyncIterable`` list results, but the synchronous
    ``bounded_rows`` helper cannot slice an async generator. The async wrapper
    must consume only the effective prefix and close the iterator so the field's
    mandatory raw-list bound applies without a ``TypeError`` or unbounded
    materialization.
    """
    await sync_to_async(services.seed_data)(1)
    rows = await sync_to_async(lambda: list(Category.objects.order_by("id")))()
    assert len(rows) > 1

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class _Rows:
        """Async iterable that records both how far it was consumed and its close."""

        def __init__(self):
            self.consumed = 0
            self.closed = False

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.consumed >= len(rows):
                raise StopAsyncIteration
            row = rows[self.consumed]
            self.consumed += 1
            return row

        async def aclose(self):
            self.closed = True

    source = _Rows()

    async def _resolver(root: Any, info: Info) -> Any:
        return source

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(
            CategoryType,
            resolver=_resolver,
            max_rows=1,
        )

    finalize_django_types()
    result = await strawberry.Schema(query=Query).execute("{ allCategories { id name } }")

    assert result.errors is None
    assert len(result.data["allCategories"]) == 1
    assert source.consumed == 1
    assert source.closed is True


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_async_generator_resolver_is_bounded() -> None:
    """An async-generator resolver is dispatched on the async path and capped.

    The wrapper resolves the generator through the async bound, so GraphQL receives
    an already-materialized list of at most ``max_rows`` rows, not the generator.
    """
    await sync_to_async(services.seed_data)(1)
    rows = await sync_to_async(lambda: list(Category.objects.order_by("id")))()
    assert len(rows) > 1

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    async def _resolver(root: Any, info: Info):
        for row in rows:
            yield row

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(
            CategoryType,
            resolver=_resolver,
            max_rows=1,
        )

    finalize_django_types()
    result = await strawberry.Schema(query=Query).execute("{ allCategories { id name } }")

    assert result.errors is None
    assert len(result.data["allCategories"]) == 1


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_sync_resolver_returning_async_iterable_is_bounded() -> None:
    """A sync resolver returning an async-only iterable uses the async cap."""
    await sync_to_async(services.seed_data)(1)
    rows = await sync_to_async(lambda: list(Category.objects.order_by("id")))()
    assert len(rows) > 1

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    def _resolver(root: Any, info: Info):
        async def _rows():
            for row in rows:
                yield row

        return _rows()

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(
            CategoryType,
            resolver=_resolver,
            max_rows=1,
        )

    finalize_django_types()
    result = await strawberry.Schema(query=Query).execute("{ allCategories { id name } }")

    assert result.errors is None
    assert len(result.data["allCategories"]) == 1


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_partial_async_generator_resolver_is_bounded() -> None:
    """A partial-wrapped async-generator callable instance resolves through the async cap.

    The wrapper calls the partial, classifies the returned value by VALUE
    (an async-only iterable), and routes it through the async bound - so
    the async cap, not the sync path, bounds the rows.
    """
    await sync_to_async(services.seed_data)(1)
    rows = await sync_to_async(lambda: list(Category.objects.order_by("id")))()
    assert len(rows) > 1

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class _Resolver:
        async def __call__(
            self,
            prefix: str,
            root: Any,
            info: Info,
        ):
            for row in rows:
                yield row

    resolver = functools.partial(_Resolver(), "ignored")

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(
            CategoryType,
            resolver=resolver,
            max_rows=1,
        )

    finalize_django_types()
    result = await strawberry.Schema(query=Query).execute("{ allCategories { id name } }")

    assert result.errors is None
    assert len(result.data["allCategories"]) == 1


@pytest.mark.django_db
def test_djangolistfield_sync_async_generator_resolver_raises_sync_misuse() -> None:
    """Sync execution rejects an async-generator resolver before GraphQL slices it."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    async def _resolver(root: Any, info: Info):
        if False:
            yield None

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType, resolver=_resolver)

    finalize_django_types()
    result = strawberry.Schema(query=Query).execute_sync("{ allCategories { id name } }")

    assert result.errors is not None
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert "returned an AsyncIterable in a sync execution context" in str(result.errors[0])


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_async_consumer_resolver_async_iterable_can_exhaust_before_bound() -> (
    None
):
    """An async iterable shorter than its cap completes without a close error."""
    await sync_to_async(services.seed_data)(1)
    row = await sync_to_async(lambda: Category.objects.order_by("id").first())()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    async def _resolver(root: Any, info: Info) -> Any:
        async def _rows():
            yield row

        return _rows()

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(
            CategoryType,
            resolver=_resolver,
            max_rows=2,
        )

    finalize_django_types()
    result = await strawberry.Schema(query=Query).execute("{ allCategories { id name } }")

    assert result.errors is None
    assert len(result.data["allCategories"]) == 1


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_sync_resolver_returning_coroutine_rejects_loudly() -> None:
    """A sync consumer resolver that RETURNS a coroutine is rejected, never silently leaked.

    Regression pin for a visibility-hook (data-isolation) bypass. A plain ``def``
    resolver that returns a coroutine - ``return some_async()`` without declaring
    the resolver ``async def`` - is classified SYNC by ``is_async_callable`` (the
    callable itself is not a coroutine function, and a ``def`` returning an
    awaitable is out of that predicate's contract), so ``DjangoListField`` picks
    the sync ``_wrap``. Before the fix, ``post_process_queryset_result_sync`` saw
    the coroutine as a non-``QuerySet`` and returned it unchanged (the
    ``django_strawberry_framework/utils/querysets.py::normalize_query_source``
    ``is_queryset=False`` arm); under ``await schema.execute(...)`` graphql-core
    then awaited that coroutine to a ``QuerySet`` that NEVER ran
    ``target_type.get_queryset`` - the ``exclude(name__startswith="a")``
    visibility filter was silently skipped and every row leaked. The field now
    rejects the coroutine with ``SyncMisuseError`` (mirroring the sync
    async-``get_queryset`` guard) so the invariant "a consumer ``QuerySet`` return
    is never resolved without its visibility hook" holds even for this
    mis-declared resolver shape.
    """
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(name__startswith="a")

    async def _inner() -> Any:
        return await sync_to_async(lambda: Category.objects.all())()

    def _sync_resolver_returning_coroutine(root: Any, info: Info) -> Any:
        # Plain ``def`` (NOT ``async def``) that returns a coroutine - the
        # mis-declared shape ``is_async_callable`` classifies as sync.
        return _inner()

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(
            CategoryType,
            resolver=_sync_resolver_returning_coroutine,
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = await schema.execute("{ allCategories { id name } }")
    # Loud rejection, not a silent leak.
    assert result.errors is not None
    assert len(result.errors) == 1
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert "returned an awaitable" in str(result.errors[0])
    # The non-null list field errors out entirely rather than returning the
    # unfiltered (leaked) rows the pre-fix pass-through would have produced.
    assert result.data is None


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_sync_resolver_returning_custom_awaitable_rejects_loudly() -> None:
    """A non-coroutine ``__await__`` result cannot bypass queryset visibility."""
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(name__startswith="a")

    class _DeferredQueryset:
        def __await__(self):
            # A real non-coroutine awaitable. If passed through to graphql-core,
            # awaiting it returns the raw QuerySet without running get_queryset.
            if False:
                yield None
            return Category.objects.all()

    def _sync_resolver_returning_awaitable(root: Any, info: Info) -> Any:
        return _DeferredQueryset()

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(
            CategoryType,
            resolver=_sync_resolver_returning_awaitable,
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    result = await schema.execute("{ allCategories { id name } }")

    assert result.errors is not None
    assert len(result.errors) == 1
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert "returned an awaitable" in str(result.errors[0])
    assert result.data is None


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_sync_resolver_returning_future_cancels_it() -> None:
    """A rejected asyncio Future is cancelled rather than left pending."""
    import asyncio

    await sync_to_async(services.seed_data)(1)
    captured: dict[str, asyncio.Future] = {}

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    def _sync_resolver_returning_future(root: Any, info: Info) -> Any:
        future = asyncio.get_running_loop().create_future()
        captured["future"] = future
        return future

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(
            CategoryType,
            resolver=_sync_resolver_returning_future,
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    result = await schema.execute("{ allCategories { id } }")

    assert result.errors is not None
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert captured["future"].cancelled() is True


# -----------------------------------------------------------------------------
# Group G - Root-position optimizer cooperation.
# (Listed BEFORE the outer-nullability pair to preserve the spec Test plan's
# stated order; the spec lists the root-optimization test
# (``spec #"test_djangolistfield_at_root_position_is_optimized"``) before the
# nullable-outer pair (``spec #"test_djangolistfield_nullable_outer_via_consumer_annotation"``
# and ``spec #"test_djangolistfield_non_nullable_outer_default_via_consumer_annotation"``).)
# -----------------------------------------------------------------------------


@pytest.mark.django_db
def test_djangolistfield_at_root_position_is_optimized(django_assert_num_queries) -> None:
    """Root-position ``DjangoListField`` triggers ``DjangoOptimizerExtension.resolve``.

    Pins the root-only contract (Decision 4, spec #"Scope narrowing - root only in `0.0.7`"). The
    root-gated ``DjangoOptimizerExtension.resolve`` hook
    (``django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve #"if info.path.prev is not None:"`` - the ``info.path.prev is not None``
    early-return) fires on a ``DjangoListField``-served root query, and
    the planning hook produces ``prefetch_related`` for the nested
    ``items`` selection.

    Query-count derivation (spec #"pin the assertion to exact query count via `assertNumQueries(N)`"): ``N`` = 1 base SELECT
    + 1 SELECT per ``prefetch_related`` relation in the nested selection.
    For ``{ allCategories { id name items { id name } } }`` against
    ``Category`` with ``items`` as a reverse-FK, ``N = 2`` - one Category
    SELECT, one Item prefetch SELECT. Pin via ``assertNumQueries(2)``;
    do NOT use a ``<= N`` bound (a refactor that quietly changes the
    per-query count would otherwise slide past unnoticed).
    """
    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType)

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    with django_assert_num_queries(2):
        result = schema.execute_sync(
            "{ allCategories { id name items { id name } } }",
            context_value=ctx,
        )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert plan is not None
    # The reverse-FK ``items`` relation is planned as a single
    # ``prefetch_related`` entry. The optimizer emits a ``Prefetch``
    # object (carrying the queryset shape) rather than a bare string so
    # downstream FK-id / ``only()`` projection can attach to it; the
    # ``prefetch_to`` attribute names the relation accessor.
    assert len(plan.prefetch_related) == 1
    assert isinstance(plan.prefetch_related[0], Prefetch)
    assert plan.prefetch_related[0].prefetch_to == "items"


# -----------------------------------------------------------------------------
# Group F - Outer-nullability via consumer annotation.
# -----------------------------------------------------------------------------


# NOTE: the nullable-outer counterpart of the test below
# (``list[T] | None`` -> ``[T!]``) was promoted to the live HTTP tier as
# ``examples/fakeshop/test_query/test_library_api.py::
# test_library_branches_via_djangolistfield_nullable_outer_renders_and_resolves``
# per ``test_query/README.md`` (the rendered shape is reachable from a live
# ``/graphql/`` introspection query). ``DjangoListField`` has no
# outer-nullability branch - Strawberry reads the consumer annotation - so the
# ``list_field.py`` lines stay fully pinned by the non-nullable companion below.


def test_djangolistfield_non_nullable_outer_default_via_consumer_annotation() -> None:
    """``list[CategoryType]`` renders as ``[CategoryType!]!`` (non-null outer + items).

    Pins that the default annotation (``list[T]`` without ``| None``)
    renders as ``[T!]!`` - four levels of unwrap match the spec's pinned
    introspection shape (spec #"locate `fields[name == \"allBranches\"]`";
    spec #"`strawberry.field` in the installed Strawberry version is a function, not a class";
    spec #"pin the introspection-query mechanism");
    spec #"test_djangolistfield_non_nullable_outer_default_via_consumer_annotation".
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        '{ __type(name: "Query") { fields { name type '
        "{ kind ofType { kind ofType { kind ofType { kind name } } } } } } }",
    )
    assert result.errors is None
    fields = {f["name"]: f["type"] for f in result.data["__type"]["fields"]}
    field_type = fields["allCategories"]
    assert field_type["kind"] == "NON_NULL"
    assert field_type["ofType"]["kind"] == "LIST"
    assert field_type["ofType"]["ofType"]["kind"] == "NON_NULL"
    assert field_type["ofType"]["ofType"]["ofType"]["kind"] == "OBJECT"
    assert field_type["ofType"]["ofType"]["ofType"]["name"] == "CategoryType"


# -----------------------------------------------------------------------------
# Group G (continued) - FK-id elision (mirrors
# ``tests/optimizer/test_extension.py::test_optimizer_elides_forward_fk_id_only_selection_plan_shape``).
# -----------------------------------------------------------------------------


@pytest.mark.django_db
def test_djangolistfield_fk_id_elision_survives(django_assert_num_queries) -> None:
    """FK-id elision fires under a root ``DjangoListField`` for ``id``-only selections.

    Pins the FK-id elision plan emission for a forward-FK
    ``category { id }`` selection: no JOIN, no prefetch, ``only_fields``
    includes ``category_id``, and the plan's ``fk_id_elisions`` tuple
    carries the resolver key. Mirrors the existing integration pattern at
    ``tests/optimizer/test_extension.py::test_optimizer_elides_forward_fk_id_only_selection_plan_shape`` (spec #"test_djangolistfield_fk_id_elision_survives").
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        all_items: list[ItemType] = DjangoListField(ItemType)

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    with django_assert_num_queries(1):
        result = schema.execute_sync(
            "{ allItems { name category { id } } }",
            context_value=ctx,
        )
    assert result.errors is None
    assert all(item["category"]["id"] for item in result.data["allItems"])
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ()
    assert plan.prefetch_related == ()
    assert plan.only_fields == ("name", "category_id")
    assert plan.fk_id_elisions == ("ItemType.category@allItems.category",)
    assert ctx.dst_optimizer_fk_id_elisions == {"ItemType.category@allItems.category"}


# -----------------------------------------------------------------------------
# Group H - ``Meta.primary`` interaction (Decision 6).
# -----------------------------------------------------------------------------


@pytest.mark.django_db
def test_djangolistfield_with_meta_primary_true_returns_primary_queryset() -> None:
    """``DjangoListField(PrimaryType)`` invokes the primary's ``get_queryset``.

    Pins that when two ``DjangoType``s exist on the same model and one
    carries ``Meta.primary = True``, ``DjangoListField(PrimaryType)``
    returns rows queried via the primary's ``get_queryset``. The test
    discriminates by giving the two types' ``get_queryset``s different
    filtering behavior; pointing the field at the primary picks the
    primary's behavior (Decision 6 multi-type-per-model; spec #"test_djangolistfield_with_meta_primary_true_returns_primary_queryset").
    """
    services.seed_data(1)

    class PrimaryCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            primary = True

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(name__startswith="a")

    class SecondaryCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(name__startswith="b")

    @strawberry.type
    class Query:
        all_primary: list[PrimaryCategoryType] = DjangoListField(PrimaryCategoryType)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ allPrimary { id name } }")
    assert result.errors is None
    names = [row["name"] for row in result.data["allPrimary"]]
    assert names, "expected at least one row from the primary's queryset"
    # The primary's exclusion fired (no ``a``-prefixed rows survive).
    assert all(not name.startswith("a") for name in names)
    # The secondary's exclusion did NOT fire (``b``-prefixed rows survive).
    assert any(name.startswith("b") for name in names), (
        "expected a 'b'-prefixed row to survive - the secondary's get_queryset "
        "must NOT have been applied when the field targets the primary"
    )


@pytest.mark.django_db
def test_djangolistfield_with_secondary_target_uses_secondary_get_queryset() -> None:
    """``DjangoListField(SecondaryType)`` invokes the secondary's ``get_queryset``.

    Pins that the registry's ``Meta.primary`` discriminator does NOT
    override the explicit-target argument: pointing the field at the
    secondary returns the secondary's ``get_queryset`` filter, NOT the
    primary's (Decision 6; spec #"test_djangolistfield_with_secondary_target_uses_secondary_get_queryset").
    """
    services.seed_data(1)

    class PrimaryCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            primary = True

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(name__startswith="a")

    class SecondaryCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.exclude(name__startswith="b")

    @strawberry.type
    class Query:
        all_secondary: list[SecondaryCategoryType] = DjangoListField(SecondaryCategoryType)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ allSecondary { id name } }")
    assert result.errors is None
    names = [row["name"] for row in result.data["allSecondary"]]
    assert names, "expected at least one row from the secondary's queryset"
    # The secondary's exclusion fired (no ``b``-prefixed rows survive).
    assert all(not name.startswith("b") for name in names)
    # The primary's exclusion did NOT fire (``a``-prefixed rows survive).
    assert any(name.startswith("a") for name in names), (
        "expected an 'a'-prefixed row to survive - the primary's get_queryset "
        "must NOT have been applied when the field targets the secondary"
    )


# =============================================================================
# List field <-> cascade composition pin (spec-034). No list_field.py source change
# is involved: the default resolver (and the consumer-resolver wrap) already apply
# the type's get_queryset (Decision 12).
# =============================================================================


@pytest.mark.django_db
def test_list_field_default_resolver_applies_cascade() -> None:
    """``DjangoListField`` over a cascading type drops rows pointing at hidden targets.

    The default resolver applies the type's ``get_queryset`` (where the cascade
    lives), so the list narrows with no list-field-specific code (Decision 12).

    The list field is over ``Item`` (forward FK ``category``); the ``Item`` hook
    calls ``apply_cascade_permissions`` so an item under a private (hidden) category
    drops out. Scoped to the DEFAULT resolver per the stub docstring (the
    consumer-``resolver=`` wrap also applies the hook, but the spec Test plan does
    not widen this pin past the default path).
    """

    class _HidingCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.filter(is_private=False)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return apply_cascade_permissions(cls, queryset, info)

    @strawberry.type
    class Query:
        all_items: list[ItemType] = DjangoListField(ItemType)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    public_cat = Category.objects.create(name="public_cat", is_private=False)
    private_cat = Category.objects.create(name="private_cat", is_private=True)
    Item.objects.create(name="visible_item", category=public_cat)
    Item.objects.create(name="hidden_item", category=private_cat)

    result = schema.execute_sync("{ allItems { id name } }")
    assert result.errors is None
    names = sorted(row["name"] for row in result.data["allItems"])
    # The item under a private category drops; only the visible item remains.
    assert names == ["visible_item"]


# =============================================================================
# Sealed-execution boundary at the list-field surface
# (docs/SPECS/spec-045-visibility_boundary-0_0_14.md #"## Architectural decisions").
# Mirrors the connection-surface regressions in ``tests/test_connection.py`` (the
# hostile-subclass, instance-shadowed ``.all()``, and Manager degrade / alias-drift
# tests). A hostile hook-return whose overrides would erase the visibility
# predicate or synthesize rows is neutralized by sealing: the list field serves
# ONLY the visible rows, sync AND async. Seeding makes visible != raw so the
# assertions are not vacuous.
# =============================================================================


class _HostileListQuerySet(models.QuerySet):
    """A predicate-erasing / synthetic-row ``QuerySet`` subclass.

    Every override would widen the result if ``DjangoListField`` dispatched
    through the consumer object: ``.filter()`` / ``.order_by()`` drop all
    narrowing and ``__iter__`` yields the raw (unfiltered) table rows. The seal
    rebuilds a plain ``QuerySet`` from the validated query state, so none run.
    """

    def filter(self, *args, **kwargs):
        return Category.objects.all()

    def order_by(self, *args, **kwargs):
        return Category.objects.all()

    def __iter__(self):
        return iter(Category.objects.all().order_by("pk"))


def _seed_public_private_categories() -> list[str]:
    """Create two public + one private ``Category``; return the ordered public names."""
    public_a = Category.objects.create(name="public_a", is_private=False)
    public_b = Category.objects.create(name="public_b", is_private=False)
    Category.objects.create(name="private_x", is_private=True)
    return [public_a.name, public_b.name]


def _hostile_list_hook(cls, queryset, info, **kwargs):
    """Return the hostile subclass carrying a genuine ``is_private=False`` predicate.

    The predicate is applied through the UNBOUND ``models.QuerySet.filter`` so the
    subclass's predicate-erasing ``.filter()`` override does not run at seed time.
    """
    return models.QuerySet.filter(_HostileListQuerySet(model=Category), is_private=False)


@pytest.mark.django_db
def test_djangolistfield_hostile_hook_subclass_serves_only_visible_rows_sync() -> None:
    """A hostile-subclass ``get_queryset`` return serves only the visible rows (sync).

    The predicate-erasing / synthetic-row overrides on ``_HostileListQuerySet`` are
    neutralized by ``django_strawberry_framework/utils/querysets.py::_seal_or_defect``:
    the boundary rebuilds a plain ``QuerySet`` from the validated query state, never
    dispatching through the consumer object, so the ``is_private=False`` predicate
    survives and the private row never leaks.
    """
    public_names = _seed_public_private_categories()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        get_queryset = classmethod(_hostile_list_hook)

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ allCategories { id name } }")
    assert result.errors is None
    names = sorted(row["name"] for row in result.data["allCategories"])
    assert names == public_names  # only the visible rows, never the raw private one


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_hostile_hook_subclass_serves_only_visible_rows_async() -> None:
    """Async twin: the hostile subclass overrides are sealed away on the async path too."""
    public_names = await sync_to_async(_seed_public_private_categories)()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        get_queryset = classmethod(_hostile_list_hook)

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = await schema.execute("{ allCategories { id name } }")
    assert result.errors is None
    names = sorted(row["name"] for row in result.data["allCategories"])
    assert names == public_names


@pytest.mark.django_db
def test_djangolistfield_instance_shadowed_all_hook_is_sealed() -> None:
    """A hook returning a PLAIN queryset with an instance-shadowed ``.all()`` is sealed.

    The seal reads the queryset's state from ``__dict__`` via
    ``object.__getattribute__``, never through attribute access, so an instance
    attribute ``all`` shadowing the method (which would drop the predicate if the
    framework called ``.all()``) cannot lie or run: only the visible rows are served.
    """
    public_names = _seed_public_private_categories()

    class ShadowedAllCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            source = Category.objects.filter(is_private=False)
            source.all = lambda: Category.objects.all()  # instance shadow (predicate-dropping)
            return source

    @strawberry.type
    class Query:
        all_categories: list[ShadowedAllCategoryType] = DjangoListField(ShadowedAllCategoryType)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ allCategories { id name } }")
    assert result.errors is None
    names = sorted(row["name"] for row in result.data["allCategories"])
    assert names == public_names


# --- Manager failure propagation at the list-field surface -------------------


class _ListManager(models.Manager):
    """A hostile Manager whose ``.all()`` degrades into a plain list (a bypass shape)."""

    def all(self):
        return ["secret"]


def _degrading_manager() -> models.Manager:
    """An unrouted ``_ListManager`` bound to ``Category``."""
    manager = _ListManager()
    manager.model = Category
    manager._db = None
    return manager


class _DriftManager(models.Manager):
    """A Manager pinned to one alias whose ``.all()`` silently routes to another."""

    def get_queryset(self):
        return Category.objects.using("elsewhere")


def _alias_drift_manager() -> models.Manager:
    """A ``_DriftManager`` pinned to ``other`` whose ``.all()`` drifts to ``elsewhere``."""
    manager = _DriftManager()
    manager.model = Category
    manager._db = "other"
    return manager


@pytest.mark.django_db
def test_djangolistfield_resolver_manager_degrading_to_list_fails_closed_sync() -> None:
    """A consumer resolver returning a Manager that degrades to a list fails closed (sync).

    ``django_strawberry_framework/utils/querysets.py::_coerced_manager_queryset`` refuses
    a ``Manager.all()`` that returns a non-queryset, so the degraded list can never be
    mistaken for the deliberate plain-iterable bypass and skip the visibility hook.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    def _resolver(root: Any, info: Info) -> Any:
        return _degrading_manager()

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType, resolver=_resolver)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ allCategories { id name } }")
    assert result.errors is not None
    assert any("must produce a QuerySet" in str(err.message) for err in result.errors)


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_resolver_manager_degrading_to_list_fails_closed_async() -> None:
    """Sync/async parity: the Manager-degrade failure propagates on the async path too."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    async def _resolver(root: Any, info: Info) -> Any:
        return _degrading_manager()

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType, resolver=_resolver)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = await schema.execute("{ allCategories { id name } }")
    assert result.errors is not None
    assert any("must produce a QuerySet" in str(err.message) for err in result.errors)


@pytest.mark.django_db
def test_djangolistfield_resolver_manager_alias_drift_fails_closed_sync() -> None:
    """A consumer resolver returning a Manager whose ``.all()`` drifts alias fails closed (sync).

    ``_coerced_manager_queryset`` requires the coerced queryset's ``_db`` to EXACTLY
    preserve the manager's explicit routing, so a manager pinned to ``other`` whose
    ``.all()`` self-routes to ``elsewhere`` cannot silently change databases.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    def _resolver(root: Any, info: Info) -> Any:
        return _alias_drift_manager()

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType, resolver=_resolver)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ allCategories { id name } }")
    assert result.errors is not None
    assert any(
        "preserve the manager's explicit routing" in str(err.message) for err in result.errors
    )


@pytest.mark.django_db
def test_djangolistfield_rejects_a_non_positive_max_rows_at_construction() -> None:
    """A bad ``max_rows`` fails at the line that wrote the field, not on a request.

    The row bound is a security boundary, so a typo in it must not be discovered
    by a client (spec-047 Decision 6).
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    with pytest.raises(ConfigurationError, match="DjangoListField max_rows must be a positive"):
        DjangoListField(CategoryType, max_rows=0)


@pytest.mark.django_db
def test_djangolistfield_max_rows_narrows_the_request_policy() -> None:
    """``max_rows`` narrows; it never widens without the trusted opt-in."""
    services.seed_data(2)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType, max_rows=1)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ allCategories { id name } }")
    assert result.errors is None, result.errors
    assert len(result.data["allCategories"]) == 1


@pytest.mark.django_db
def test_djangolistfield_consumer_resolver_returning_none_sync() -> None:
    """Consumer resolver returning None on a nullable list field resolves to None without error."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    def _resolver(root, info):
        return None

    @strawberry.type
    class Query:
        categories: list[CategoryType] | None = DjangoListField(CategoryType, resolver=_resolver)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ categories { id name } }")
    assert result.errors is None, result.errors
    assert result.data == {"categories": None}


@pytest.mark.django_db
async def test_djangolistfield_consumer_resolver_returning_none_async() -> None:
    """Async consumer resolver returning None on a nullable list field resolves to None without error."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    async def _resolver(root, info):
        return None

    @strawberry.type
    class Query:
        categories: list[CategoryType] | None = DjangoListField(CategoryType, resolver=_resolver)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = await schema.execute("{ categories { id name } }")
    assert result.errors is None, result.errors
    assert result.data == {"categories": None}


def test_list_argument_error_properties_extensions_and_repr():
    err1 = ListArgumentError("items", "offset", "non_integer", value=True)
    assert issubclass(ListArgumentError, GraphQLError)
    assert issubclass(ListArgumentError, DjangoStrawberryFrameworkError)
    assert err1.field == "items"
    assert err1.argument == "offset"
    assert err1.reason == "non_integer"
    assert err1.value == "bool True"
    assert err1.ceiling is None
    assert err1.extensions == {
        "code": "LIST_ARGUMENT_INVALID",
        "argument": "offset",
        "reason": "non_integer",
        "value": "bool True",
    }
    assert (
        "Invalid argument 'offset' on items: expected a non-negative integer, got bool True."
        in str(err1)
    )

    err2 = ListArgumentError("items", "offset", "negative", value=-1)
    assert err2.extensions == {
        "code": "LIST_ARGUMENT_INVALID",
        "argument": "offset",
        "reason": "negative",
        "value": -1,
    }
    assert "Invalid argument 'offset' on items: expected a non-negative integer, got -1." in str(
        err2,
    )

    err3 = ListArgumentError("items", "limit", "over_ceiling", value=150, ceiling=100)
    assert err3.extensions == {
        "code": "LIST_ARGUMENT_INVALID",
        "argument": "limit",
        "reason": "over_ceiling",
        "value": 150,
        "ceiling": 100,
    }
    assert (
        "Invalid argument 'limit' on items: value 150 exceeds the maximum allowed ceiling of 100."
        in str(err3)
    )

    err4 = ListArgumentError("items", "offset", "order_required", value=5)
    assert err4.extensions == {
        "code": "LIST_ARGUMENT_INVALID",
        "argument": "offset",
        "reason": "order_required",
        "value": 5,
    }
    assert "requires an active ordering" in str(err4)

    err5 = ListArgumentError("items", "orderBy", "queryset_required")
    assert err5.extensions == {
        "code": "LIST_ARGUMENT_INVALID",
        "argument": "orderBy",
        "reason": "queryset_required",
    }
    assert "requires a QuerySet source" in str(err5)

    err6 = ListArgumentError("items", "arg", "custom_reason", value=42)
    assert "custom_reason" in str(err6)


def test_list_argument_error_pickle_roundtrip():
    err = ListArgumentError("items", "limit", "over_ceiling", value=200, ceiling=100)
    err.custom_attr = "survives"
    pickled = pickle.dumps(err)
    restored = pickle.loads(pickled)

    assert isinstance(restored, ListArgumentError)
    assert restored.field == "items"
    assert restored.argument == "limit"
    assert restored.reason == "over_ceiling"
    assert restored.value == 200
    assert restored.ceiling == 100
    assert restored.extensions == err.extensions
    assert str(restored) == str(err)
    assert getattr(restored, "custom_attr", None) == "survives"


def test_resolve_argument_wire_name_fallback_and_custom():
    # Fallback when info is empty / has no schema config:
    assert _resolve_argument_wire_name(None, "offset") == "offset"
    assert _resolve_argument_wire_name(None, "limit") == "limit"
    assert _resolve_argument_wire_name(None, "order_by") == "orderBy"
    assert _resolve_argument_wire_name(None, "custom") == "custom"

    # Schema config with name converter
    class DummyConverter:
        def __init__(self):
            self.calls = 0

        def from_argument(self, arg):
            self.calls += 1
            return arg.name.upper()

    converter = DummyConverter()
    schema_config = SimpleNamespace(name_converter=converter)
    info = SimpleNamespace(
        schema=SimpleNamespace(config=schema_config),
        get_argument_definition=lambda name: SimpleNamespace(name=name),
    )

    resolved = _resolve_argument_wire_name(info, "offset")
    assert resolved == "OFFSET"
    assert converter.calls == 1


def test_resolve_argument_wire_name_zero_calls_on_valid_normalization():
    class DummyConverter:
        def __init__(self):
            self.calls = 0

        def from_argument(self, arg):
            self.calls += 1
            return arg.name

    converter = DummyConverter()
    schema_config = SimpleNamespace(name_converter=converter)
    info = SimpleNamespace(
        context={},
        schema=SimpleNamespace(config=schema_config),
        get_argument_definition=lambda name: SimpleNamespace(name=name),
    )
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=100))

    # A valid normalization must make ZERO calls to name_converter.from_argument:
    record = _normalize_list_arguments("items", info, None, False, offset=10, limit=20)
    assert record.offset == 10
    assert record.limit == 20
    assert converter.calls == 0

    # On rejection, it must make exactly ONE call:
    with pytest.raises(ListArgumentError) as exc_info:
        _normalize_list_arguments("items", info, None, False, offset=-1)
    assert exc_info.value.reason == "negative"
    assert converter.calls == 1


def test_synthesized_list_signature_without_and_with_orderset():
    class DummyTypeWithoutOrder:
        pass

    sig, ann = _synthesized_list_signature(DummyTypeWithoutOrder)
    assert sig.return_annotation is inspect.Signature.empty
    assert "return" not in ann
    assert list(sig.parameters.keys()) == [
        "root",
        "info",
        "offset",
        "limit",
    ]
    assert sig.parameters["offset"].kind is inspect.Parameter.KEYWORD_ONLY
    assert sig.parameters["limit"].kind is inspect.Parameter.KEYWORD_ONLY
    assert "order_by" not in ann

    # With definition declaring orderset_class:
    class DummyOrderSet:
        pass

    definition = SimpleNamespace(orderset_class=DummyOrderSet)
    dummy_type_with_order = type(
        "DummyTypeWithOrder",
        (),
        {"__django_strawberry_definition__": definition},
    )

    # Mock order_input_type
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "django_strawberry_framework.orders.order_input_type",
            lambda cls: str,
            raising=False,
        )
        sig2, ann2 = _synthesized_list_signature(dummy_type_with_order)
        assert sig2.return_annotation is inspect.Signature.empty
        assert "return" not in ann2
        assert list(sig2.parameters.keys()) == [
            "root",
            "info",
            "offset",
            "limit",
            "order_by",
        ]
        assert sig2.parameters["order_by"].kind is inspect.Parameter.KEYWORD_ONLY
        assert ann2["order_by"] == (list[str] | None)


def test_subpackage_isolation_orders_not_imported_at_package_root():
    cmd = [
        sys.executable,
        "-c",
        (
            "import sys, django_strawberry_framework; "
            "assert 'django_strawberry_framework.orders' not in sys.modules, "
            "'orders subpackage leaked into package root import'"
        ),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_normalize_list_arguments_all_boundaries():
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=100))

    # Boundary 1: offset boolean
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, None, False, offset=True)
    assert exc.value.argument == "offset"
    assert exc.value.reason == "non_integer"
    assert exc.value.value == "bool True"

    # Boundary 2: offset non-integer (string, float)
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, None, False, offset="ten")
    assert exc.value.argument == "offset"
    assert exc.value.reason == "non_integer"
    assert exc.value.value == "str 'ten'"

    # Boundary 3: offset negative
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, None, False, offset=-1)
    assert exc.value.argument == "offset"
    assert exc.value.reason == "negative"
    assert exc.value.value == -1

    # Boundary 4: offset over ceiling
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, None, False, offset=101)
    assert exc.value.argument == "offset"
    assert exc.value.reason == "over_ceiling"
    assert exc.value.value == 101
    assert exc.value.ceiling == 100

    # Boundary 5: limit boolean
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, None, False, limit=False)
    assert exc.value.argument == "limit"
    assert exc.value.reason == "non_integer"
    assert exc.value.value == "bool False"

    # Boundary 6: limit non-integer
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, None, False, limit=3.14)
    assert exc.value.argument == "limit"
    assert exc.value.reason == "non_integer"
    assert exc.value.value == "float 3.14"

    # Boundary 7: limit negative
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, None, False, limit=-10)
    assert exc.value.argument == "limit"
    assert exc.value.reason == "negative"
    assert exc.value.value == -10

    # Boundary 8: limit over ceiling (with effective bound calculation)
    # 8a: policy 100, field max_rows 50 (untrusted) -> ceiling is 50
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, 50, False, limit=51)
    assert exc.value.argument == "limit"
    assert exc.value.reason == "over_ceiling"
    assert exc.value.value == 51
    assert exc.value.ceiling == 50

    # 8b: policy 100, field max_rows 200 (trusted=True) -> ceiling is 200
    rec = _normalize_list_arguments("items", info, 200, True, limit=150)
    assert rec.limit == 150
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, 200, True, limit=201)
    assert exc.value.argument == "limit"
    assert exc.value.reason == "over_ceiling"
    assert exc.value.value == 201
    assert exc.value.ceiling == 200

    # Boundary 9: deterministic precedence (offset before limit)
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, None, False, offset=-1, limit=-2)
    assert exc.value.argument == "offset"
    assert exc.value.reason == "negative"

    # Omission
    omitted = _normalize_list_arguments("items", info, None, False)
    assert omitted.offset is None
    assert omitted.limit is None
    assert omitted.order_by is None
    assert omitted.order_by_supplied is False
    assert omitted.any_argument_supplied is False

    # Zero and empty supplied
    zero_offset = _normalize_list_arguments("items", info, None, False, offset=0)
    assert zero_offset.offset == 0
    assert zero_offset.any_argument_supplied is True

    empty_order = _normalize_list_arguments("items", info, None, False, order_by=[])
    assert empty_order.order_by == []
    assert empty_order.order_by_supplied is True
    assert empty_order.any_argument_supplied is True

    # Slotted record
    assert hasattr(_ListArguments, "__slots__")
    assert not hasattr(omitted, "__dict__")


@pytest.mark.parametrize("bad_offset", [True, False])
def test_normalize_list_arguments_boundary_1_offset_boolean_rejected(bad_offset):
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=100))
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, None, False, offset=bad_offset)
    assert exc.value.argument == "offset"
    assert exc.value.reason == "non_integer"
    assert exc.value.value == f"bool {bad_offset}"


@pytest.mark.parametrize(
    "bad_offset, expected_desc",
    [("ten", "str 'ten'"), (3.14, "float 3.14")],
)
def test_normalize_list_arguments_boundary_2_offset_non_integer_rejected(
    bad_offset,
    expected_desc,
):
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=100))
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, None, False, offset=bad_offset)
    assert exc.value.argument == "offset"
    assert exc.value.reason == "non_integer"
    assert exc.value.value == expected_desc


@pytest.mark.parametrize("bad_offset", [-1, -10])
def test_normalize_list_arguments_boundary_3_offset_negative_rejected(bad_offset):
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=100))
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, None, False, offset=bad_offset)
    assert exc.value.argument == "offset"
    assert exc.value.reason == "negative"
    assert exc.value.value == bad_offset


@pytest.mark.parametrize("bad_offset", [101, 500])
def test_normalize_list_arguments_boundary_4_offset_over_ceiling_rejected(bad_offset):
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=100))
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, None, False, offset=bad_offset)
    assert exc.value.argument == "offset"
    assert exc.value.reason == "over_ceiling"
    assert exc.value.value == bad_offset
    assert exc.value.ceiling == 100


@pytest.mark.parametrize("bad_limit", [True, False])
def test_normalize_list_arguments_boundary_5_limit_boolean_rejected(bad_limit):
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=100))
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, None, False, limit=bad_limit)
    assert exc.value.argument == "limit"
    assert exc.value.reason == "non_integer"
    assert exc.value.value == f"bool {bad_limit}"


@pytest.mark.parametrize(
    "bad_limit, expected_desc",
    [("twenty", "str 'twenty'"), (3.14, "float 3.14")],
)
def test_normalize_list_arguments_boundary_6_limit_non_integer_rejected(bad_limit, expected_desc):
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=100))
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, None, False, limit=bad_limit)
    assert exc.value.argument == "limit"
    assert exc.value.reason == "non_integer"
    assert exc.value.value == expected_desc


@pytest.mark.parametrize("bad_limit", [-1, -10])
def test_normalize_list_arguments_boundary_7_limit_negative_rejected(bad_limit):
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=100))
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, None, False, limit=bad_limit)
    assert exc.value.argument == "limit"
    assert exc.value.reason == "negative"
    assert exc.value.value == bad_limit


@pytest.mark.parametrize(
    "field_max, trusted, bad_limit, expected_ceiling",
    [
        (
            50,
            False,
            51,
            50,
        ),
        (
            200,
            True,
            201,
            200,
        ),
    ],
)
def test_normalize_list_arguments_boundary_8_limit_over_ceiling_rejected(
    field_max,
    trusted,
    bad_limit,
    expected_ceiling,
):
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=100))
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, field_max, trusted, limit=bad_limit)
    assert exc.value.argument == "limit"
    assert exc.value.reason == "over_ceiling"
    assert exc.value.value == bad_limit
    assert exc.value.ceiling == expected_ceiling


@pytest.mark.parametrize(
    "offset_val, limit_val, expected_reason",
    [(-1, -2, "negative"), (True, -1, "non_integer"), ("bad", 101, "non_integer")],
)
def test_normalize_list_arguments_boundary_9_precedence_offset_before_limit(
    offset_val,
    limit_val,
    expected_reason,
):
    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=100))
    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments("items", info, None, False, offset=offset_val, limit=limit_val)
    assert exc.value.argument == "offset"
    assert exc.value.reason == expected_reason


@pytest.mark.django_db
async def test_async_iterable_early_cleanup_hostile_aclose_lookup_notes():
    """Hostile aclose lookup during rejected async iterable cleanup attaches to error notes."""
    from django_strawberry_framework.orders import OrderSet

    class CategoryOrder(OrderSet):
        class Meta:
            model = Category
            fields = ["name"]

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            orderset_class = CategoryOrder

    class HostileTracker:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise StopAsyncIteration

        def __getattribute__(self, name: str):
            if name == "aclose":
                raise RuntimeError("hostile aclose on tracker")
            return super().__getattribute__(name)

    tracker = HostileTracker()

    async def resolver_async_iter(root, info, **kwargs):
        return tracker

    @strawberry.type
    class Query:
        cats: list[CategoryType] = DjangoListField(CategoryType, resolver=resolver_async_iter)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    res = await schema.execute("{ cats(offset: 5) { id } }", context_value={})
    assert res.errors is not None
    assert "requires an active ordering" in str(res.errors[0])
    original_error = getattr(res.errors[0], "original_error", None)
    if original_error is not None:
        notes = getattr(original_error, "__notes__", [])
        assert any("hostile aclose on tracker" in str(note) for note in notes)


def test_apply_orderset_sync_rejects_awaitable():
    """_apply_orderset_sync raises SyncMisuseError when apply_sync returns an awaitable."""
    from django_strawberry_framework.list_field import _apply_orderset_sync
    from django_strawberry_framework.orders import OrderSet

    class SyncAwaitable:
        def __await__(self):
            return iter([])

    class SyncMisuseOrder(OrderSet):
        class Meta:
            model = Category
            fields = ["name"]

        @classmethod
        def apply_sync(
            cls,
            input_value,
            queryset,
            info,
        ):
            return SyncAwaitable()

    class SyncMisuseType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            orderset_class = SyncMisuseOrder

    with pytest.raises(SyncMisuseError, match="returned an awaitable in a sync resolver context"):
        _apply_orderset_sync(SyncMisuseType, Category.objects.all(), None, SimpleNamespace())


def test_apply_orderset_async_rejects_non_awaitable():
    """_apply_orderset_async raises ConfigurationError when apply_async returns non-awaitable."""
    from django_strawberry_framework.list_field import _apply_orderset_async
    from django_strawberry_framework.orders import OrderSet

    class AsyncNonAwaitableOrder(OrderSet):
        class Meta:
            model = Category
            fields = ["name"]

        @classmethod
        def apply_async(
            cls,
            input_value,
            queryset,
            info,
        ):
            return queryset

    class AsyncNonAwaitableType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            orderset_class = AsyncNonAwaitableOrder

    with pytest.raises(ConfigurationError, match="returned a non-awaitable value"):
        asyncio.run(
            _apply_orderset_async(
                AsyncNonAwaitableType,
                Category.objects.all(),
                None,
                SimpleNamespace(),
            ),
        )


def test_apply_orderset_async_rejects_residual_awaitable():
    """_apply_orderset_async raises ConfigurationError when apply_async returns residual awaitable."""
    from django_strawberry_framework.list_field import _apply_orderset_async
    from django_strawberry_framework.orders import OrderSet

    class ResidualAwaitable:
        def __await__(self):
            return iter([])

    class AsyncResidualAwaitableOrder(OrderSet):
        class Meta:
            model = Category
            fields = ["name"]

        @classmethod
        async def apply_async(
            cls,
            input_value,
            queryset,
            info,
        ):
            return ResidualAwaitable()

    class AsyncResidualAwaitableType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            orderset_class = AsyncResidualAwaitableOrder

    with pytest.raises(ConfigurationError, match="returned a residual awaitable value"):
        asyncio.run(
            _apply_orderset_async(
                AsyncResidualAwaitableType,
                Category.objects.all(),
                None,
                SimpleNamespace(),
            ),
        )


def test_offset_guard_random_term_question_mark():
    """Offset guard rejects queries ordered by exact '?'."""
    from django_strawberry_framework.list_field import (
        _check_nonzero_offset_guard,
        _has_no_random_terms,
        _is_random_order_term,
    )

    assert _is_random_order_term("?") is True
    assert _is_random_order_term("name") is False

    qs_random = Category.objects.order_by("?")
    assert _has_no_random_terms(qs_random) is False

    info = SimpleNamespace(context={}, schema=None)
    args_record = _ListArguments(
        offset=5,
        limit=None,
        effective_ceiling=None,
        order_by=[{"name": "ASC"}],
        order_by_supplied=True,
        any_argument_supplied=True,
    )

    class DummyOrderSet:
        @classmethod
        def _input_has_active_terms(cls, val):
            return True

    with pytest.raises(ListArgumentError, match="requires an active ordering"):
        _check_nonzero_offset_guard(qs_random, args_record, DummyOrderSet, info)


def test_offset_guard_random_term_random_function():
    """Offset guard rejects queries ordered by Random() expressions."""
    from django.db.models.expressions import OrderBy
    from django.db.models.functions import Random

    from django_strawberry_framework.list_field import (
        _check_nonzero_offset_guard,
        _has_no_random_terms,
        _is_random_order_term,
    )

    assert _is_random_order_term(Random()) is True
    assert _is_random_order_term(OrderBy(Random())) is True
    assert _is_random_order_term("-name") is False

    qs_random = Category.objects.order_by(Random())
    assert _has_no_random_terms(qs_random) is False

    info = SimpleNamespace(context={}, schema=None)
    args_record = _ListArguments(
        offset=5,
        limit=None,
        effective_ceiling=None,
        order_by=[{"name": "ASC"}],
        order_by_supplied=True,
        any_argument_supplied=True,
    )

    class DummyOrderSet:
        @classmethod
        def _input_has_active_terms(cls, val):
            return True

    with pytest.raises(ListArgumentError, match="requires an active ordering"):
        _check_nonzero_offset_guard(qs_random, args_record, DummyOrderSet, info)


def test_offset_guard_model_default_active(monkeypatch):
    """Model Meta.ordering satisfies offset guard."""
    from django_strawberry_framework.list_field import (
        _check_nonzero_offset_guard,
        _is_model_default_ordering_active,
    )

    monkeypatch.setattr(Category._meta, "ordering", ("name",))

    qs = Category.objects.all()
    assert _is_model_default_ordering_active(qs) is True

    info = SimpleNamespace(context={}, schema=None)
    args_record = _ListArguments(
        offset=5,
        limit=None,
        effective_ceiling=None,
        order_by=None,
        order_by_supplied=False,
        any_argument_supplied=True,
    )
    _check_nonzero_offset_guard(qs, args_record, None, info)


def test_offset_guard_model_default_cleared_by_order_by(monkeypatch):
    """Calling .order_by() clears model default ordering and fails offset guard."""
    from django_strawberry_framework.list_field import (
        _check_nonzero_offset_guard,
        _is_model_default_ordering_active,
    )

    monkeypatch.setattr(Category._meta, "ordering", ("name",))

    qs_cleared = Category.objects.all().order_by()
    assert _is_model_default_ordering_active(qs_cleared) is False

    info = SimpleNamespace(context={}, schema=None)
    args_record = _ListArguments(
        offset=5,
        limit=None,
        effective_ceiling=None,
        order_by=None,
        order_by_supplied=False,
        any_argument_supplied=True,
    )
    with pytest.raises(ListArgumentError, match="requires an active ordering"):
        _check_nonzero_offset_guard(qs_cleared, args_record, None, info)

    qs_grouped = Category.objects.all()
    qs_grouped.query.group_by = ("name",)
    assert _is_model_default_ordering_active(qs_grouped) is False


@pytest.mark.django_db
async def test_async_completion_adapter_semantics():
    """_AsyncQuerySetRows wraps queryset in async context, exposes __aiter__, and rejects __iter__."""
    from django_strawberry_framework.utils.querysets import (
        _AsyncQuerySetRows,
        is_async_queryset_adapter,
        unwrap_async_queryset_adapter,
        wrap_async_queryset_adapter,
    )

    await sync_to_async(services.seed_data)(1)

    assert wrap_async_queryset_adapter("not_a_qs") == "not_a_qs"
    with pytest.raises(TypeError, match="_AsyncQuerySetRows requires a QuerySet"):
        _AsyncQuerySetRows("not_a_qs")

    qs = Category.objects.all()[:3]
    adapter = wrap_async_queryset_adapter(qs)
    assert is_async_queryset_adapter(adapter)
    assert hasattr(adapter, "__aiter__")
    assert not hasattr(adapter, "__iter__")

    with pytest.raises(TypeError, match="is not iterable"):
        for _ in adapter:
            pass

    rows = [r async for r in adapter]
    assert len(rows) > 0

    unwrapped, was_adapted = unwrap_async_queryset_adapter(adapter)
    assert was_adapted is True
    assert unwrapped is qs

    non_adapter_res, was_adapted2 = unwrap_async_queryset_adapter(qs)
    assert was_adapted2 is False
    assert non_adapter_res is qs


def test_async_completion_adapter_sync_iter_raises_type_error():
    """wrap_async_queryset_adapter rejects sync iter() protocol."""
    from django_strawberry_framework.utils.querysets import wrap_async_queryset_adapter

    qs = Category.objects.all()
    adapter = wrap_async_queryset_adapter(qs)
    assert not hasattr(adapter, "__iter__")
    with pytest.raises(TypeError, match="is not iterable"):
        iter(adapter)


def test_list_field_signature_without_orderset():
    """Target without Meta.orderset_class generates signature with info, offset, limit, and empty return."""

    class NoOrderType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    finalize_django_types()
    sig, ann = _synthesized_list_signature(NoOrderType)

    assert sig.parameters["info"].kind == inspect.Parameter.KEYWORD_ONLY
    assert sig.parameters["offset"].kind == inspect.Parameter.KEYWORD_ONLY
    assert sig.parameters["offset"].default is None
    assert sig.parameters["offset"].annotation == int | None
    assert sig.parameters["limit"].kind == inspect.Parameter.KEYWORD_ONLY
    assert sig.parameters["limit"].default is None
    assert sig.parameters["limit"].annotation == int | None
    assert "order_by" not in sig.parameters
    assert "orderBy" not in sig.parameters
    assert sig.return_annotation is inspect.Signature.empty
    assert "return" not in ann


def test_list_field_signature_with_orderset():
    """Target with Meta.orderset_class adds order_by parameter registered in orphan ledger."""
    from django_strawberry_framework.orders import OrderSet, order_input_type

    class ItemOrder(OrderSet):
        class Meta:
            model = Item
            fields = ["name"]

    class WithOrderType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            orderset_class = ItemOrder

    finalize_django_types()
    sig, ann = _synthesized_list_signature(WithOrderType)

    assert "order_by" in sig.parameters
    assert sig.parameters["order_by"].kind == inspect.Parameter.KEYWORD_ONLY
    assert sig.parameters["order_by"].default is None
    assert sig.parameters["order_by"].annotation == ann["order_by"]

    from django_strawberry_framework.orders import _helper_referenced_ordersets

    order_input_type(ItemOrder)
    assert ItemOrder in _helper_referenced_ordersets
    assert sig.return_annotation is inspect.Signature.empty
    assert "return" not in ann


def test_list_field_nullable_outer_annotation_preserved():
    """Outer nullable annotation is preserved without overwrite from synthesized signature."""

    class PreservedType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    @strawberry.type
    class Query:
        items_non_null: list[PreservedType] = DjangoListField(PreservedType)
        items_nullable: list[PreservedType] | None = DjangoListField(PreservedType)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    sdl = str(schema)
    assert "itemsNonNull(offset: Int = null, limit: Int = null): [PreservedType!]!" in sdl
    assert "itemsNullable(offset: Int = null, limit: Int = null): [PreservedType!]\n" in sdl


def test_list_field_direct_call_type_and_bound_rejections():
    """Direct calls to normalizer reject bool, float, str, negative, and over-ceiling values."""
    info = SimpleNamespace(context={}, schema=None)
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))

    # bool rejected
    with pytest.raises(ListArgumentError) as exc_info:
        _normalize_list_arguments("test_field", info, None, False, offset=True)
    assert exc_info.value.reason == "non_integer"

    with pytest.raises(ListArgumentError) as exc_info:
        _normalize_list_arguments("test_field", info, None, False, limit=False)
    assert exc_info.value.reason == "non_integer"

    # float and str rejected
    with pytest.raises(ListArgumentError) as exc_info:
        _normalize_list_arguments("test_field", info, None, False, offset=1.5)
    assert exc_info.value.reason == "non_integer"

    with pytest.raises(ListArgumentError) as exc_info:
        _normalize_list_arguments("test_field", info, None, False, limit="bad")
    assert exc_info.value.reason == "non_integer"

    # negative values rejected
    with pytest.raises(ListArgumentError) as exc_info:
        _normalize_list_arguments("test_field", info, None, False, offset=-1)
    assert exc_info.value.reason == "negative"
    assert exc_info.value.value == -1

    with pytest.raises(ListArgumentError) as exc_info:
        _normalize_list_arguments("test_field", info, None, False, limit=-5)
    assert exc_info.value.reason == "negative"
    assert exc_info.value.value == -5

    # over-ceiling values rejected
    with pytest.raises(ListArgumentError) as exc_info:
        _normalize_list_arguments("test_field", info, None, False, offset=11)
    assert exc_info.value.reason == "over_ceiling"
    assert exc_info.value.ceiling == 10

    with pytest.raises(ListArgumentError) as exc_info:
        _normalize_list_arguments("test_field", info, None, False, limit=11)
    assert exc_info.value.reason == "over_ceiling"
    assert exc_info.value.ceiling == 10


def test_list_field_direct_call_offset_before_limit_precedence():
    """Deterministic offset-before-limit precedence when both coordinates are invalid."""
    info = SimpleNamespace(context={}, schema=None)
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))

    with pytest.raises(ListArgumentError) as exc_info:
        _normalize_list_arguments(
            "test_field",
            info,
            None,
            False,
            offset=-1,
            limit=-1,
        )
    assert exc_info.value.argument == "offset"
    assert exc_info.value.reason == "negative"

    with pytest.raises(ListArgumentError) as exc_info:
        _normalize_list_arguments(
            "test_field",
            info,
            None,
            False,
            offset="bad",
            limit=100,
        )
    assert exc_info.value.argument == "offset"
    assert exc_info.value.reason == "non_integer"


def test_list_field_direct_call_safe_non_integer_rendering():
    """Safe rendering of non-integer values in ListArgumentError message."""
    info = SimpleNamespace(context={}, schema=None)
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))

    with pytest.raises(ListArgumentError) as exc_info:
        _normalize_list_arguments(
            "test_field",
            info,
            None,
            False,
            offset="<script>alert(1)</script>",
        )
    assert exc_info.value.reason == "non_integer"
    assert "Invalid argument 'offset' on test_field" in str(exc_info.value)


def test_list_field_trusted_return_cap_asymmetry():
    """Trusted max_rows widens limit up to field bound, but does not widen offset ceiling."""
    info = SimpleNamespace(context={}, schema=None)
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))

    # limit up to 25 accepted when trusted_max_rows=True
    args = _normalize_list_arguments(
        "test_field",
        info,
        max_rows=25,
        trusted_max_rows=True,
        offset=5,
        limit=20,
    )
    assert args.limit == 20
    assert args.effective_ceiling == 25

    # limit > 25 rejected
    with pytest.raises(ListArgumentError) as exc_info:
        _normalize_list_arguments(
            "test_field",
            info,
            max_rows=25,
            trusted_max_rows=True,
            limit=26,
        )
    assert exc_info.value.reason == "over_ceiling"
    assert exc_info.value.ceiling == 25

    # offset > 10 rejected despite trusted_max_rows=True
    with pytest.raises(ListArgumentError) as exc_info:
        _normalize_list_arguments(
            "test_field",
            info,
            max_rows=25,
            trusted_max_rows=True,
            offset=15,
        )
    assert exc_info.value.reason == "over_ceiling"
    assert exc_info.value.ceiling == 10


def test_list_field_error_pickle_round_trip():
    """ListArgumentError preserves constructor args, extensions, and state across pickle."""
    err = ListArgumentError(
        "books",
        "offset",
        reason="negative",
        value=-5,
        ceiling=10,
        order_argument="sort",
    )
    err.custom_tag = "tagged"

    dumped = pickle.dumps(err)
    restored = pickle.loads(dumped)

    assert restored.field == "books"
    assert restored.argument == "offset"
    assert restored.reason == "negative"
    assert restored.value == -5
    assert restored.ceiling == 10
    assert restored.order_argument == "sort"
    assert restored.extensions == err.extensions
    assert getattr(restored, "custom_tag", None) == "tagged"


def test_list_field_direct_call_schema_name_fallback_and_definition_lookup():
    """_resolve_argument_wire_name exercises default fallback and error-lazy converter."""
    info_no_def = SimpleNamespace(schema=None)
    assert _resolve_argument_wire_name(info_no_def, "offset") == "offset"
    assert _resolve_argument_wire_name(info_no_def, "limit") == "limit"
    assert _resolve_argument_wire_name(info_no_def, "order_by") == "orderBy"
    assert _resolve_argument_wire_name(info_no_def, "custom_arg") == "custom_arg"

    from strawberry.schema.name_converter import NameConverter

    converter_calls = 0

    class TrackingConverter(NameConverter):
        def from_argument(self, argument):
            nonlocal converter_calls
            converter_calls += 1
            return super().from_argument(argument)

    class TrackingConfig:
        name_converter = TrackingConverter()

    class TrackingSchema:
        config = TrackingConfig()

    class ArgDef:
        name = "order_by"
        python_name = "order_by"

    def mock_get_arg_def(name):
        return ArgDef()

    info_tracking = SimpleNamespace(
        schema=TrackingSchema(),
        get_argument_definition=mock_get_arg_def,
        context={},
    )
    stash_resource_policy(info_tracking.context, ResourcePolicy(max_list_rows=10))

    # Successful normalization calls converter 0 times (error-lazy)
    converter_calls = 0
    _normalize_list_arguments("field", info_tracking, None, False, offset=1, limit=2)
    assert converter_calls == 0

    # Error path calls converter once
    with pytest.raises(ListArgumentError):
        _normalize_list_arguments("field", info_tracking, None, False, offset=-1)
    assert converter_calls == 1

    # Converter failure raises ConfigurationError rather than swallowing
    class FailingConverter(NameConverter):
        def from_argument(self, argument):
            raise ValueError("simulated converter failure")

    class FailingConfig:
        name_converter = FailingConverter()

    class FailingSchema:
        config = FailingConfig()

    info_failing = SimpleNamespace(
        schema=FailingSchema(),
        get_argument_definition=mock_get_arg_def,
        context={},
    )
    with pytest.raises(
        ConfigurationError,
        match="Failed to resolve wire name for argument 'order_by'",
    ):
        _resolve_argument_wire_name(info_failing, "order_by")


def test_list_field_record_independence():
    """_ListArguments fields operate independently without proxy conflation."""
    info = SimpleNamespace(context={}, schema=None)
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))

    # Omitted arguments
    rec_empty = _normalize_list_arguments("f", info, None, False)
    assert rec_empty.any_argument_supplied is False
    assert rec_empty.offset is None
    assert rec_empty.limit is None
    assert rec_empty.order_by_supplied is False

    # offset=0 with no limit produces omission-identical window
    rec_zero = _normalize_list_arguments("f", info, None, False, offset=0)
    assert rec_zero.any_argument_supplied is True
    assert rec_zero.offset == 0
    assert rec_zero.limit is None
    assert rec_zero.effective_ceiling == 10

    # order_by_supplied drives queryset_required even when order_by=[]
    rec_order_empty = _normalize_list_arguments("f", info, None, False, order_by=[])
    assert rec_order_empty.order_by_supplied is True
    assert rec_order_empty.order_by == []

    from django_strawberry_framework.list_field import _handle_non_queryset_rejections_sync

    with pytest.raises(ListArgumentError) as exc_info:
        _handle_non_queryset_rejections_sync([1, 2, 3], rec_order_empty, info)
    assert exc_info.value.reason == "queryset_required"


def test_list_field_sync_and_async_awaitable_disposal():
    """Awaitables returned in invalid contexts are disposed with actionable errors."""
    from django_strawberry_framework.orders import OrderSet

    class BadSyncOrder(OrderSet):
        class Meta:
            model = Category
            fields = ["name"]

        @classmethod
        def apply_sync(
            cls,
            input_value,
            queryset,
            info,
        ):
            async def _coro():
                return queryset

            return _coro()

    class BadSyncType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            orderset_class = BadSyncOrder

    info = SimpleNamespace(context={"request": RequestFactory().get("/")}, schema=None)

    from django_strawberry_framework.list_field import (
        _apply_orderset_async,
        _apply_orderset_sync,
    )

    with pytest.raises(SyncMisuseError, match="BadSyncOrder.apply_sync returned an awaitable"):
        _apply_orderset_sync(BadSyncType, Category.objects.all(), None, info)

    # Async apply returning non-awaitable
    class BadAsyncNonAwaitableOrder(OrderSet):
        class Meta:
            model = Category
            fields = ["name"]

        @classmethod
        def apply_async(
            cls,
            input_value,
            queryset,
            info,
        ):
            return queryset

    class BadAsyncNonAwaitableType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            orderset_class = BadAsyncNonAwaitableOrder

    with pytest.raises(
        ConfigurationError,
        match="BadAsyncNonAwaitableOrder.apply_async returned a non-awaitable value",
    ):
        asyncio.run(
            _apply_orderset_async(BadAsyncNonAwaitableType, Category.objects.all(), None, info),
        )

    # Async apply returning residual awaitable after await
    class BadAsyncResidualOrder(OrderSet):
        class Meta:
            model = Category
            fields = ["name"]

        @classmethod
        async def apply_async(
            cls,
            input_value,
            queryset,
            info,
        ):
            async def _inner():
                return queryset

            return _inner()

    class BadAsyncResidualType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            orderset_class = BadAsyncResidualOrder

    with pytest.raises(
        ConfigurationError,
        match="BadAsyncResidualOrder.apply_async returned a residual awaitable value",
    ):
        asyncio.run(
            _apply_orderset_async(BadAsyncResidualType, Category.objects.all(), None, info),
        )


def test_list_field_post_orderset_validator_arms():
    """Rejection of invalid return candidates from OrderSet apply methods."""
    from django_strawberry_framework.utils.querysets import _validate_post_orderset_result

    class ItemOrderType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    base_qs = Item.objects.all()

    # 1. Non-QuerySet (None, list, Manager) -> type defect
    for candidate in [None, [1, 2], Item.objects]:
        with pytest.raises(
            ConfigurationError,
            match="must return an unevaluated, unsliced, uncombined QuerySet",
        ):
            _validate_post_orderset_result(
                ItemOrderType,
                base_qs,
                candidate,
                "CustomOrder.apply_sync",
            )

    # 2. Wrong model / table
    with pytest.raises(ConfigurationError, match="table defect"):
        _validate_post_orderset_result(
            ItemOrderType,
            base_qs,
            Category.objects.all(),
            "CustomOrder.apply_sync",
        )

    # 3. Projection / values
    with pytest.raises(ConfigurationError, match="projection defect"):
        _validate_post_orderset_result(
            ItemOrderType,
            base_qs,
            Item.objects.values("id"),
            "CustomOrder.apply_sync",
        )

    # 4. Evaluated QuerySet
    evaluated_qs = Item.objects.all()
    evaluated_qs._result_cache = []
    with pytest.raises(ConfigurationError) as exc_info:
        _validate_post_orderset_result(
            ItemOrderType,
            base_qs,
            evaluated_qs,
            "CustomOrder.apply_sync",
        )
    assert "got evaluated defect" in str(exc_info.value)
    assert "must return an unevaluated, unsliced, uncombined QuerySet" in str(exc_info.value)

    # 5. Sliced QuerySet
    sliced_qs = Item.objects.all()[:2]
    with pytest.raises(ConfigurationError, match="sliced defect"):
        _validate_post_orderset_result(
            ItemOrderType,
            base_qs,
            sliced_qs,
            "CustomOrder.apply_sync",
        )

    # 6. Combined QuerySet
    combined_qs = Item.objects.all().union(Item.objects.all())
    with pytest.raises(ConfigurationError) as exc_info:
        _validate_post_orderset_result(
            ItemOrderType,
            base_qs,
            combined_qs,
            "CustomOrder.apply_sync",
        )
    assert "got combined defect" in str(exc_info.value)
    assert "must return an unevaluated, unsliced, uncombined QuerySet" in str(exc_info.value)

    # 7. Changed routing hints
    hints_qs = Item.objects.all()
    hints_qs._hints = {"instance": object()}
    with pytest.raises(ConfigurationError, match="changed database routing intent"):
        _validate_post_orderset_result(
            ItemOrderType,
            base_qs,
            hints_qs,
            "CustomOrder.apply_sync",
        )


async def test_list_field_rejected_async_iterator_cleanup_and_notes():
    """Rejected async-only iterator witnesses 0 anext calls, 1 aclose call, and notes on cleanup error."""
    from django_strawberry_framework.list_field import _handle_non_queryset_rejections_async

    class InstrumentedAsyncSource:
        def __init__(self, fail_close=False):
            self.fail_close = fail_close
            self.anext_calls = 0
            self.aclose_calls = 0

        def __aiter__(self):
            return self

        async def __anext__(self):
            self.anext_calls += 1
            raise StopAsyncIteration

        async def aclose(self):
            self.aclose_calls += 1
            if self.fail_close:
                raise RuntimeError("aclose error")

    info = SimpleNamespace(context={}, schema=None)
    args_record = _ListArguments(
        offset=None,
        limit=None,
        effective_ceiling=10,
        order_by=[{"name": "ASC"}],
        order_by_supplied=True,
        any_argument_supplied=True,
    )

    # Clean close
    src_clean = InstrumentedAsyncSource(fail_close=False)
    with pytest.raises(ListArgumentError) as exc_clean:
        await _handle_non_queryset_rejections_async(src_clean, args_record, info)
    assert exc_clean.value.reason == "queryset_required"
    assert src_clean.anext_calls == 0
    assert src_clean.aclose_calls == 1

    # Cleanup error attaches note without masking ListArgumentError
    src_fail = InstrumentedAsyncSource(fail_close=True)
    with pytest.raises(ListArgumentError) as exc_fail:
        await _handle_non_queryset_rejections_async(src_fail, args_record, info)
    assert exc_fail.value.reason == "queryset_required"
    assert src_fail.anext_calls == 0
    assert src_fail.aclose_calls == 1
    notes = getattr(exc_fail.value, "__notes__", [])
    assert any("bounded_rows_async iterator cleanup failed" in str(n) for n in notes)


def test_list_field_async_queryset_adapter_protocol():
    """_AsyncQuerySetRows exposes __aiter__ and rejects sync iteration protocol."""
    from django_strawberry_framework.utils.querysets import _AsyncQuerySetRows

    qs = Category.objects.all()
    adapter = _AsyncQuerySetRows(qs)
    assert hasattr(adapter, "__aiter__")
    assert not hasattr(adapter, "__iter__")

    with pytest.raises(TypeError, match="is not iterable"):
        iter(adapter)


def test_list_field_optimizer_adapter_unwrap_rewrap_and_early_returns():
    """DjangoOptimizerExtension._optimize unwrap/rewrap identity, marks, and early return paths."""
    from django_strawberry_framework.utils.querysets import (
        is_async_queryset_adapter,
        unwrap_async_queryset_adapter,
        wrap_async_queryset_adapter,
    )

    ext = DjangoOptimizerExtension()

    # 1. Non-adapted queryset stays non-adapted
    qs = Category.objects.all()
    info_unresolved = SimpleNamespace(field_name="cats", return_type=object())
    out1 = ext._optimize(qs, info_unresolved)
    assert not is_async_queryset_adapter(out1)
    assert out1 is qs

    # 2. Adapted queryset on unresolved return type: early return rewraps adapter
    adapter = wrap_async_queryset_adapter(qs)
    out2 = ext._optimize(adapter, info_unresolved)
    assert is_async_queryset_adapter(out2)
    unwrapped2, was2 = unwrap_async_queryset_adapter(out2)
    assert was2 is True
    assert unwrapped2 is qs

    # 3. Adapted queryset on already-evaluated inner queryset: early return rewraps adapter
    qs_evaluated = Category.objects.all()
    qs_evaluated._result_cache = []
    adapter_eval = wrap_async_queryset_adapter(qs_evaluated)
    out3 = ext._optimize(adapter_eval, info_unresolved)
    assert is_async_queryset_adapter(out3)
    unwrapped3, was3 = unwrap_async_queryset_adapter(out3)
    assert was3 is True
    assert unwrapped3 is qs_evaluated

    # 4. Sliced adapter preserves slice marks through unwrap/rewrap
    qs_sliced = Category.objects.all()[2:5]
    adapter_sliced = wrap_async_queryset_adapter(qs_sliced)
    out4 = ext._optimize(adapter_sliced, info_unresolved)
    assert is_async_queryset_adapter(out4)
    unwrapped4, _ = unwrap_async_queryset_adapter(out4)
    assert unwrapped4.query.low_mark == 2
    assert unwrapped4.query.high_mark == 5


def test_list_field_deadline_check_position(monkeypatch):
    """check_deadline is invoked in pre-fetch position for argument-bearing requests."""
    import django_strawberry_framework.resource_policy as rp

    check_calls = 0
    orig_check = rp.check_deadline

    def spy_check(info):
        nonlocal check_calls
        check_calls += 1
        return orig_check(info)

    monkeypatch.setattr(rp, "check_deadline", spy_check)

    info = SimpleNamespace(context={}, schema=None)
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))

    args_record = _ListArguments(
        offset=1,
        limit=2,
        effective_ceiling=10,
        order_by=None,
        order_by_supplied=False,
        any_argument_supplied=True,
    )

    class ItemDeadType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    check_calls = 0
    from django_strawberry_framework.list_field import _execute_queryset_pipeline_sync

    monkeypatch.setattr(Item._meta, "ordering", ("name",))
    res = _execute_queryset_pipeline_sync(
        ItemDeadType,
        Item.objects.all(),
        info,
        args_record,
        max_rows=10,
        trusted_max_rows=False,
        is_async_context=False,
    )
    assert res is not None
    assert check_calls == 1


def test_list_field_seal_axis_subclass_and_routing_intent():
    """Sealable subclass normalized to plain QuerySet; foreign Query rejected; routing intent enforced."""
    from django_strawberry_framework.utils.querysets import _validate_post_orderset_result

    class CustomQuerySetSubclass(models.QuerySet):
        pass

    class ItemSealType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    base_qs = Item.objects.all()
    sub_qs = CustomQuerySetSubclass(model=Item)

    # 1. Sealable subclass is normalized to plain QuerySet
    sealed = _validate_post_orderset_result(ItemSealType, base_qs, sub_qs, "Custom.apply")
    assert type(sealed) is models.QuerySet

    # 2. Subclass with _deferred_filter is rejected as untrusted
    sub_qs._deferred_filter = True
    with pytest.raises(ConfigurationError, match="untrusted defect"):
        _validate_post_orderset_result(ItemSealType, base_qs, sub_qs, "Custom.apply")

    # 3. Routing intent: _db is None accepted when _hints match, rejected when _hints differ
    qs_match = Item.objects.all()
    qs_match._hints = {"shard": "a"}
    base_with_hints = Item.objects.all()
    base_with_hints._hints = {"shard": "a"}
    sealed_hints = _validate_post_orderset_result(
        ItemSealType,
        base_with_hints,
        qs_match,
        "Custom.apply",
    )
    assert type(sealed_hints) is models.QuerySet

    qs_mismatch = Item.objects.all()
    qs_mismatch._hints = {"shard": "b"}
    with pytest.raises(ConfigurationError, match="changed database routing intent"):
        _validate_post_orderset_result(
            ItemSealType,
            base_with_hints,
            qs_mismatch,
            "Custom.apply",
        )


def test_list_field_declined_sync_cleanup_generator_suspended():
    """Declined sync cleanup: generator truncated by client window stays suspended and resumable."""
    finally_ran = False

    def sync_numbers():
        nonlocal finally_ran
        try:
            yield from range(10)
        finally:
            finally_ran = True

    info = SimpleNamespace(context={}, schema=None)
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))

    g = sync_numbers()
    args_record = _ListArguments(
        offset=2,
        limit=3,
        effective_ceiling=10,
        order_by=None,
        order_by_supplied=False,
        any_argument_supplied=True,
    )

    from django_strawberry_framework.resource_policy import bounded_rows

    res = bounded_rows(g, info, offset=args_record.offset, requested_limit=args_record.limit)
    assert res == [2, 3, 4]
    assert finally_ran is False

    assert next(g) == 5
    assert finally_ran is False
    g.close()
    assert finally_ran is True


async def test_list_field_async_source_exact_versus_fewer_rows():
    """Distinguish accepted-stop close from natural exhaustion on async source."""
    from django_strawberry_framework.resource_policy import bounded_rows_async

    class CountedAsyncIter:
        def __init__(self, count):
            self.count = count
            self.anext_calls = 0
            self.aclose_calls = 0

        def __aiter__(self):
            return self

        async def __anext__(self):
            self.anext_calls += 1
            if self.anext_calls > self.count:
                raise StopAsyncIteration
            return self.anext_calls

        async def aclose(self):
            self.aclose_calls += 1

    info = SimpleNamespace(context={})
    stash_resource_policy(info.context, ResourcePolicy(max_list_rows=10))

    # Exact rows (offset=1, limit=2, items=3): reaches stop, calls aclose
    exact_src = CountedAsyncIter(3)
    res_exact = await bounded_rows_async(exact_src, info, offset=1, requested_limit=2)
    assert res_exact == [2, 3]
    assert exact_src.aclose_calls == 1

    # Fewer rows (offset=1, limit=5, items=2): naturally exhausts, does NOT call aclose
    fewer_src = CountedAsyncIter(2)
    res_fewer = await bounded_rows_async(fewer_src, info, offset=1, requested_limit=5)
    assert res_fewer == [2]
    assert fewer_src.aclose_calls == 0


def test_is_model_default_ordering_active_edge_states(monkeypatch):
    """_is_model_default_ordering_active rejects group_by, extra_order_by, random, and unreadable."""
    from django.db.models.expressions import OrderBy
    from django.db.models.functions import Random

    from django_strawberry_framework.list_field import _is_model_default_ordering_active

    monkeypatch.setattr(Category._meta, "ordering", ("name",))
    qs = Category.objects.all()
    assert _is_model_default_ordering_active(qs) is True

    # 1. group_by suppresses default ordering
    qs_group = Category.objects.all()
    qs_group.query.group_by = ("name",)
    assert _is_model_default_ordering_active(qs_group) is False

    # 2. extra_order_by suppresses default ordering
    qs_extra = Category.objects.all()
    qs_extra.query.extra_order_by = ("name",)
    assert _is_model_default_ordering_active(qs_extra) is False

    # 3. Recognized random terms alone or mixed suppress
    monkeypatch.setattr(Category._meta, "ordering", ("?",))
    assert _is_model_default_ordering_active(Category.objects.all()) is False

    monkeypatch.setattr(Category._meta, "ordering", ("name", "?"))
    assert _is_model_default_ordering_active(Category.objects.all()) is False

    monkeypatch.setattr(Category._meta, "ordering", (Random(),))
    assert _is_model_default_ordering_active(Category.objects.all()) is False

    monkeypatch.setattr(Category._meta, "ordering", (OrderBy(Random()),))
    assert _is_model_default_ordering_active(Category.objects.all()) is False

    # 4. Empty ordering suppresses
    monkeypatch.setattr(Category._meta, "ordering", ())
    assert _is_model_default_ordering_active(Category.objects.all()) is False


def test_is_model_default_ordering_active_reverse_and_empty_queryset(monkeypatch):
    """Stable .reverse() satisfies predicate; explicit order satisfies empty queryset; unordered empty fails."""
    from django_strawberry_framework.list_field import _is_model_default_ordering_active

    # .reverse() retains default ordering
    monkeypatch.setattr(Category._meta, "ordering", ("name",))
    qs_rev = Category.objects.all().reverse()
    assert _is_model_default_ordering_active(qs_rev) is True

    # Empty queryset with active model ordering satisfies predicate
    qs_none_ordered = Category.objects.none()
    assert _is_model_default_ordering_active(qs_none_ordered) is True

    # Empty queryset without model ordering fails predicate
    monkeypatch.setattr(Category._meta, "ordering", ())
    qs_none_unordered = Category.objects.none()
    assert _is_model_default_ordering_active(qs_none_unordered) is False


def test_list_field_post_apply_seal_benchmark():
    """Diagnostic benchmark baseline for post-apply seal (Decision 5)."""
    from django.db.models import Count

    from django_strawberry_framework.utils.querysets import _validate_post_orderset_result

    class CatBenchType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    qs = (
        Category.objects.annotate(num_items=Count("items"))
        .prefetch_related("items")
        .order_by("name")
    )

    # Warmup
    for _ in range(20):
        _validate_post_orderset_result(CatBenchType, qs, qs, "BenchOrder.apply_sync")

    start = time.perf_counter()
    iterations = 200
    for _ in range(iterations):
        sealed = _validate_post_orderset_result(CatBenchType, qs, qs, "BenchOrder.apply_sync")
        assert sealed is not None
    duration = time.perf_counter() - start

    avg_micros = (duration / iterations) * 1_000_000
    assert iterations == 200
    assert avg_micros > 0


def test_list_field_constructor_validation_precedence():
    """Constructor validates collection bound before target_type or directives."""
    # Negative bound raises collection bound error even if target_type is invalid
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField max_rows must be a positive integer, got -1\.",
    ):
        DjangoListField(object, max_rows=-1)

    # Zero bound raises collection bound error even if target_type is invalid
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField max_rows must be a positive integer, got 0\.",
    ):
        DjangoListField(object, max_rows=0)

    # Valid bound proceeds to target_type validation
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField target_type must be a DjangoType subclass, got <class 'object'>",
    ):
        DjangoListField(object, max_rows=10)


def test_list_field_post_orderset_validator_zero_consumer_dispatch():
    """_validate_post_orderset_result extracts routing intent without consumer dispatch."""
    from django_strawberry_framework.utils.querysets import (
        _routing_hints_equal,
        _safe_routing_repr,
        _validate_post_orderset_result,
    )

    class CatDispatchType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    base_qs = Category.objects.all()

    class PoisonAttr:
        def __eq__(self, other):
            raise RuntimeError("PoisonAttr __eq__ called")

        def __repr__(self):
            raise RuntimeError("PoisonAttr __repr__ called")

    # Safe routing equal avoids consumer __eq__
    poison = PoisonAttr()
    assert _routing_hints_equal({"key": poison}, {"key": poison}) is True
    assert _routing_hints_equal({"key": poison}, {"key": PoisonAttr()}) is False

    # Safe routing repr avoids consumer __repr__
    repr_str = _safe_routing_repr({"key": poison})
    assert "PoisonAttr at" in repr_str

    # None vs {} distinction preserved
    assert _routing_hints_equal(None, {}) is False
    assert _routing_hints_equal({}, None) is False
    assert _routing_hints_equal(None, None) is True
    assert _routing_hints_equal({}, {}) is True

    # Rejection of routing changes without calling consumer __getattribute__
    class PoisonGetattributeQS(models.QuerySet):
        def __getattribute__(self, name):
            if name in ("_db", "_hints"):
                raise RuntimeError(f"consumer __getattribute__ called for {name}")
            return super().__getattribute__(name)

    poison_qs = PoisonGetattributeQS(model=Category)
    sealed = _validate_post_orderset_result(
        CatDispatchType,
        poison_qs,
        poison_qs,
        "Poison.apply_sync",
    )
    assert sealed is not None


def test_list_arguments_immutability_and_slots():
    """_ListArguments is an immutable slotted dataclass."""
    import dataclasses

    args = _ListArguments(
        offset=0,
        limit=10,
        effective_ceiling=10,
        order_by=None,
        order_by_supplied=False,
        any_argument_supplied=True,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        args.offset = 5
    with pytest.raises(dataclasses.FrozenInstanceError):
        args.limit = 20
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        args.extra_attribute = "disallowed"


def test_is_model_default_ordering_active_exact_bool_identity():
    """_is_model_default_ordering_active requires exact boolean True identity."""
    from django_strawberry_framework.list_field import _is_model_default_ordering_active

    query_mock = SimpleNamespace(
        default_ordering=1,
        order_by=(),
        extra_order_by=(),
        group_by=(),
        get_meta=lambda: SimpleNamespace(ordering=("name",)),
    )
    qs_mock = SimpleNamespace(query=query_mock)
    assert _is_model_default_ordering_active(qs_mock) is False

    query_mock.default_ordering = True
    assert _is_model_default_ordering_active(qs_mock) is True
