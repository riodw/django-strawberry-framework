"""Tests for ``django_strawberry_framework.list_field``.

Spec: ``docs/spec-016-list_field-0_0_7.md`` (Test plan section, the
``tests/test_list_field.py (new)`` subsection).

Package tests; system-under-test is ``django_strawberry_framework``
(spec rev5 L3 — framing matches ``AGENTS.md #"Package source lives in django_strawberry_framework"``). The file is the flat
single-file Layer-3 module's mirror per ``docs/TREE.md #"test_list_field.py       # DjangoListField (single-file Layer-3 module)"``.

Holds the Slice-2 validation cluster (5 tests) and the Slice-3 behavior
cluster (17 tests) — 22 total. Three of the tests are post-016 review
additions from ``docs/feedback.md``: two are real bug fixes — the
own-class-registration guard (High #1, rejects ``DjangoType`` subclass
that omits its own ``Meta``) and the async-callable-object detection
(High #2, detects ``async def __call__`` at construction time so the
coroutine return doesn't bypass ``_post_process_consumer_async``). The
third is a contract pin for ``functools.partial``-wrapped async
resolvers: the post-High-#2 review note suggested an explicit ``.func``
unwrap, but Python's ``inspect.iscoroutinefunction`` already looks
through ``functools.partial`` natively (3.8+), so the case is correctly
handled by the first branch of ``_is_async_callable``; the test pins
the end-to-end behavior and guards against a future Python regression.

The spec's Slice-3 inventory at ``docs/SPECS/spec-016-list_field-0_0_7.md #"Optional ``resolver=`` constructor argument that overrides the default body"`` calls out
"``Manager``/``QuerySet``" together for the consumer-resolver returns;
both arms are load-bearing per rev4 M1 (the field wrapper owns the
``Manager → QuerySet`` coercion; the optimizer's downstream coercion is
a safety net, not a substitute). The **sync** ``Manager``-return arm
lives in ``examples/fakeshop/test_query/test_library_api.py::
test_library_branches_via_djangolistfield_consumer_manager_resolver_over_http``
per the live-HTTP-first rule at ``examples/fakeshop/test_query/README.md #"**Coverage rule.**"``;
the **async** ``Manager``-return arm stays here because async resolvers
are genuinely unreachable from the sync ``GraphQLView`` mounted at
``/graphql/`` (Strawberry's sync execution rejects them with
``RuntimeError: GraphQL execution failed to complete synchronously``).
"""

import functools
from types import SimpleNamespace
from typing import Any

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category, Item
from asgiref.sync import sync_to_async
from django.db.models import Prefetch
from strawberry.types import Info

from django_strawberry_framework import (
    DjangoListField,
    DjangoOptimizerExtension,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
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
    fields, and ``Meta.primary`` state belong to the parent class (docs/feedback.md
    High #1).
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


# (Rev2 H2 — DROPPED — ``test_djangolistfield_rejects_non_bool_nullable_list``
# is NOT planned. ``nullable_list=`` is not a constructor argument; outer
# nullability is driven entirely by the consumer's class-attribute annotation.)


# =============================================================================
# Slice 3 — Behavior tests (Decisions 2, 3, 4, 6).
# =============================================================================
#
# Slice 3 ships 14 tests (rev5 M1 — one-to-one with the named methods in the
# spec Test plan; rev5 M3 — adds the dual-execution test). Tests pin the
# production contract through ``schema.execute_sync(...)`` /
# ``await schema.execute(...)`` against real Django models; the autouse
# fixture above isolates each test's registry state.


# -----------------------------------------------------------------------------
# Group A — Default-resolver shape and ``cls.get_queryset`` invocation.
# -----------------------------------------------------------------------------


@pytest.mark.django_db
def test_djangolistfield_default_resolver_returns_queryset_filtered_by_get_queryset() -> None:
    """Default resolver applies ``cls.get_queryset(qs, info)`` in a sync context.

    Pins the sync branch at ``django_strawberry_framework/list_field.py::DjangoListField #"return _apply_get_queryset_sync(target_type, qs, info)"`` —
    ``return _apply_get_queryset_sync(target_type, qs, info)`` — by declaring
    a ``DjangoType`` whose ``get_queryset`` excludes the categories whose
    names start with ``"a"`` (e.g. ``address``, ``automotive``) and
    asserting those names are absent from the resolved field output
    (spec Decision 2 #"load-bearing visibility hook"; spec #"test_djangolistfield_default_resolver_returns_queryset_filtered_by_get_queryset").
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
            return queryset.exclude(name__startswith="a")

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ allCategories { id name } }")
    assert result.errors is None
    names = [row["name"] for row in result.data["allCategories"]]
    assert names, "expected at least one non-filtered Category row"
    assert all(not name.startswith("a") for name in names)


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_async_get_queryset_is_awaited(monkeypatch) -> None:
    """Default resolver awaits an ``async def get_queryset(...)`` under ``await schema.execute(...)``.

    Pins the async branch at ``django_strawberry_framework/list_field.py::DjangoListField #"if in_async_context():"`` — the
    ``_apply_get_queryset_async(target_type, qs, info)`` call when
    ``in_async_context()`` returns True and ``get_queryset`` is
    ``async def`` (spec Decision 2 async path; Decision 3
    ``_apply_get_queryset_async``; spec #"test_djangolistfield_async_get_queryset_is_awaited").

    ``DJANGO_ALLOW_ASYNC_UNSAFE`` is set for the duration of the test so
    Strawberry's GraphQL list-completion can iterate the returned
    QuerySet inside ``await schema.execute(...)`` without raising
    ``SynchronousOnlyOperation``. The contract under test is the
    ``DjangoListField`` async-detection / ``get_queryset`` cooperation,
    NOT Django's async-ORM rules — the env var is the documented bypass
    for sync ORM access from an async context in tests.
    """
    monkeypatch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        async def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
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
# Group B — Dual-execution (rev5 M3).
# -----------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution(
    monkeypatch,
) -> None:
    """A sync ``get_queryset`` resolves correctly under both schema-execution shapes.

    Pins the runtime ``in_async_context()`` branch at ``django_strawberry_framework/list_field.py::DjangoListField #"if in_async_context():"``
    — both arms when ``get_queryset`` is SYNC. The ``False`` arm fires
    under ``schema.execute_sync(...)`` (returns ``_apply_get_queryset_sync``
    directly); the ``True`` arm fires under ``await schema.execute(...)``
    (returns the coroutine from ``_apply_get_queryset_async`` for
    Strawberry's ``AwaitableOrValue`` dispatch). The Edge cases section
    (spec #"`schema.execute_sync` testing") promises both call shapes work; without this test the
    promise is unverified (rev5 M3, spec #"add a 14th behavior test, `test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution`").

    ``DJANGO_ALLOW_ASYNC_UNSAFE`` is set so the async-branch QuerySet
    iteration in Strawberry's list-completion can proceed without
    raising ``SynchronousOnlyOperation``; this test pins the field's
    in-async-context dispatch, not Django's async-ORM rules.
    """
    monkeypatch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
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
# Group C — Sync coroutine rejection (Decision 3).
# -----------------------------------------------------------------------------


@pytest.mark.django_db
def test_djangolistfield_sync_path_rejects_coroutine_from_get_queryset() -> None:
    """Sync resolver path raises ``ConfigurationError`` when ``get_queryset`` is async.

    Pins the coroutine-rejection guard at ``django_strawberry_framework/types/relay.py::_apply_get_queryset_sync #"returned a coroutine in a sync"``. The
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
        async def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
            return queryset

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] = DjangoListField(CategoryType)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ allCategories { id name } }")
    assert result.errors is not None
    assert len(result.errors) == 1
    # The typed ``SyncMisuseError`` raised by ``_apply_get_queryset_sync``
    # surfaces as the GraphQL error's ``original_error`` so consumers
    # can match it directly without substring inspection.
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert "returned a coroutine in a sync resolver context" in str(result.errors[0])


# -----------------------------------------------------------------------------
# Group D — Sync consumer-resolver paths (rev2 H1).
# -----------------------------------------------------------------------------


@pytest.mark.django_db
def test_djangolistfield_consumer_resolver_queryset_return_gets_get_queryset_applied() -> None:
    """Sync consumer resolver returning a ``QuerySet`` receives ``target_type.get_queryset(...)``.

    Pins the sync consumer-resolver wrapper at ``django_strawberry_framework/list_field.py::DjangoListField #"return _post_process_consumer_sync("``
    — specifically that ``_post_process_consumer_sync`` (the inner call
    site) applies ``target_type.get_queryset(...)`` to a ``Manager``/``QuerySet``
    return (rev2 H1, graphene-django parity; spec #"test_djangolistfield_consumer_resolver_queryset_return_gets_get_queryset_applied").
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
            return queryset.exclude(name__startswith="a")

    def _resolver(root: Any, info: Info) -> Any:  # noqa: ARG001
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


# The sync ``Manager``-return arm (``django_strawberry_framework/list_field.py::_post_process_consumer_sync #"result = result.all()"`` coverage) lives in
# ``examples/fakeshop/test_query/test_library_api.py::test_library_branches_via_djangolistfield_consumer_manager_resolver_over_http``
# per the live-HTTP-first rule at ``examples/fakeshop/test_query/README.md #"**Coverage rule.**"``.


@pytest.mark.django_db
def test_djangolistfield_consumer_resolver_python_list_return_passes_through() -> None:
    """Sync consumer resolver returning a Python ``list`` bypasses ``target_type.get_queryset(...)``.

    Pins the sync consumer-resolver wrapper at ``django_strawberry_framework/list_field.py::DjangoListField #"return _post_process_consumer_sync("``
    — specifically that ``_post_process_consumer_sync`` returns the
    non-``QuerySet`` result unchanged (the ``return result``
    pass-through arm at ``django_strawberry_framework/list_field.py::_post_process_consumer_sync #"return result  # Python list"``; spec #"test_djangolistfield_consumer_resolver_python_list_return_passes_through"). The resolver returns a
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
        def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
            return queryset.exclude(name__startswith="a")

    def _resolver(root: Any, info: Info) -> Any:  # noqa: ARG001
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
# Group E — Async consumer-resolver paths (rev4 H2).
# -----------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied(
    monkeypatch,
) -> None:
    """Async consumer resolver returning a ``QuerySet`` receives ``target_type.get_queryset(...)``.

    Pins the async consumer-resolver wrapper at ``django_strawberry_framework/list_field.py::DjangoListField #"return await _post_process_consumer_async("``
    — specifically that the awaited consumer return is fed to
    ``_post_process_consumer_async`` (the ``await _post_process_consumer_async(...)`` call
    inside the async ``_wrap``), and the
    ``_apply_get_queryset_async`` call (``django_strawberry_framework/list_field.py::_post_process_consumer_async #"return await _apply_get_queryset_async"``) fires on a ``QuerySet``
    result. Pins that the wrapper awaits the consumer coroutine BEFORE
    the isinstance check (rev4 H2, spec #"test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied"). The
    ``DJANGO_ALLOW_ASYNC_UNSAFE`` env override unblocks Strawberry's
    list-completion iteration of the returned QuerySet under
    ``await schema.execute(...)``.
    """
    monkeypatch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
            return queryset.exclude(name__startswith="a")

    async def _resolver(root: Any, info: Info) -> Any:  # noqa: ARG001
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
async def test_djangolistfield_async_consumer_resolver_manager_return_gets_get_queryset_applied(
    monkeypatch,
) -> None:
    """Async consumer resolver returning a ``Manager`` receives ``target_type.get_queryset(...)``.

    Pins the async field-wrapper's ``Manager → QuerySet`` coercion at
    ``django_strawberry_framework/list_field.py::_post_process_consumer_async #"result = result.all()"`` — ``_post_process_consumer_async`` calls
    ``result.all()`` on a ``Manager`` return BEFORE the isinstance check
    so the subsequent ``await _apply_get_queryset_async(...)`` runs on a
    real ``QuerySet`` (rev4 M1 symmetry with the sync path; spec #"the **field wrapper** owns the `Manager → QuerySet` coercion").
    The ``DJANGO_ALLOW_ASYNC_UNSAFE`` env override unblocks Strawberry's
    list-completion iteration of the returned QuerySet under
    ``await schema.execute(...)``.
    """
    monkeypatch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
            return queryset.exclude(name__startswith="a")

    async def _resolver(root: Any, info: Info) -> Any:  # noqa: ARG001
        # Return the ``Manager`` itself, not a ``QuerySet`` — exercises
        # the coercion branch at ``django_strawberry_framework/list_field.py::_post_process_consumer_async #"result = result.all()"``.
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
async def test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied(
    monkeypatch,
) -> None:
    """Callable instance with ``async def __call__`` is detected as async at construction.

    Pins ``_is_async_callable`` detection of callable objects whose
    ``__call__`` is ``async def`` (``list_field.py``'s helper).
    ``inspect.iscoroutinefunction(instance)`` is False for such objects, but
    ``inspect.iscoroutinefunction(instance.__call__)`` is True — the factory
    must dispatch to the async wrapper either way. Without this, the sync
    wrapper would call the instance, receive a coroutine, find no
    ``Manager``/``QuerySet`` to coerce, and pass the coroutine through; under
    async schema execution Strawberry would still await the coroutine and
    silently skip ``target_type.get_queryset(...)`` (docs/feedback.md High #2).
    """
    monkeypatch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
            return queryset.exclude(name__startswith="a")

    class _AsyncResolver:
        async def __call__(self, root: Any, info: Info) -> Any:  # noqa: ARG002
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
async def test_djangolistfield_partial_wrapped_async_resolver_gets_get_queryset_applied(
    monkeypatch,
) -> None:
    """``functools.partial`` wrapping an ``async def`` resolver is detected as async.

    Contract pin (not a fix for a bug that exists today): Python's
    ``inspect.iscoroutinefunction`` looks through ``functools.partial`` wrappers
    natively since 3.8 (empirically verified against the installed Python at
    review time), so the first branch of ``_is_async_callable`` already routes
    partial-wrapped async resolvers to the async wrapper. This test pins that
    contract end-to-end through the field's pipeline: ``get_queryset``'s
    ``startswith("a")`` exclusion fires on the awaited QuerySet, proving the
    partial reached ``_post_process_consumer_async`` and not the sync wrapper.
    The post-High-#2 review note in ``docs/feedback.md`` suggested the gap was
    real and recommended an explicit ``.func`` unwrap; empirical check at the
    review point showed ``inspect.iscoroutinefunction(partial(async_fn))`` is
    True directly, so the unwrap would be dead code and this test guards
    against a future Python regression that would re-open the bug.
    """
    monkeypatch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
            return queryset.exclude(name__startswith="a")

    async def _async_resolver(prefix: str, root: Any, info: Info) -> Any:  # noqa: ARG001
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
async def test_djangolistfield_async_consumer_resolver_python_list_return_passes_through() -> None:
    """Async consumer resolver returning a Python ``list`` bypasses ``target_type.get_queryset(...)``.

    Pins the async consumer-resolver wrapper at ``django_strawberry_framework/list_field.py::DjangoListField #"return await _post_process_consumer_async("``
    — specifically that ``_post_process_consumer_async`` returns a
    non-``QuerySet`` result unchanged (the ``return result``
    pass-through arm at ``django_strawberry_framework/list_field.py::_post_process_consumer_async #"return result"``). Pins that the await-then-isinstance
    ordering is symmetric across return shapes (rev4 H2, spec #"test_djangolistfield_async_consumer_resolver_python_list_return_passes_through").
    """
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
            return queryset.exclude(name__startswith="a")

    async def _resolver(root: Any, info: Info) -> Any:  # noqa: ARG001
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


# -----------------------------------------------------------------------------
# Group G — Root-position optimizer cooperation (rev2 M3).
# (Listed BEFORE the outer-nullability pair to preserve the spec Test plan's
# stated order; the spec lists the root-optimization test
# (``spec #"test_djangolistfield_at_root_position_is_optimized"``) before the
# nullable-outer pair (``spec #"test_djangolistfield_nullable_outer_via_consumer_annotation"``
# and ``spec #"test_djangolistfield_non_nullable_outer_default_via_consumer_annotation"``).)
# -----------------------------------------------------------------------------


@pytest.mark.django_db
def test_djangolistfield_at_root_position_is_optimized(django_assert_num_queries) -> None:
    """Root-position ``DjangoListField`` triggers ``DjangoOptimizerExtension.resolve``.

    Pins the rev2 M3 root-only contract (Decision 4, spec #"Scope narrowing — root only in `0.0.7`"). The
    root-gated ``DjangoOptimizerExtension.resolve`` hook
    (``django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve #"if info.path.prev is not None:"`` — the ``info.path.prev is not None``
    early-return) fires on a ``DjangoListField``-served root query, and
    the planning hook produces ``prefetch_related`` for the nested
    ``items`` selection.

    Query-count derivation (rev6 M6, spec #"pin the assertion to exact query count via `assertNumQueries(N)`"): ``N`` = 1 base SELECT
    + 1 SELECT per ``prefetch_related`` relation in the nested selection.
    For ``{ allCategories { id name items { id name } } }`` against
    ``Category`` with ``items`` as a reverse-FK, ``N = 2`` — one Category
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
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
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
# Group F — Outer-nullability via consumer annotation (rev2 H2).
# -----------------------------------------------------------------------------


def test_djangolistfield_nullable_outer_via_consumer_annotation() -> None:
    """``list[CategoryType] | None`` renders as ``[CategoryType!]`` (nullable outer).

    Pins that the consumer's class-attribute annotation drives the
    rendered GraphQL type, NOT a constructor argument (rev2 H2,
    spec #"`strawberry.field` in the installed Strawberry version is a function, not a class").
    Verification uses an introspection query against
    ``__type(name: "Query")`` (rev6 M2, spec #"pin the introspection-query mechanism" —
    robust against SDL formatting drift); spec #"test_djangolistfield_nullable_outer_via_consumer_annotation".
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        all_categories: list[CategoryType] | None = DjangoListField(CategoryType)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        '{ __type(name: "Query") { fields { name type { kind ofType { kind ofType { kind name } } } } } }',
    )
    assert result.errors is None
    fields = {f["name"]: f["type"] for f in result.data["__type"]["fields"]}
    field_type = fields["allCategories"]
    # Outer ``NON_NULL`` wrapper is absent here — that is the load-bearing
    # difference vs the non-nullable test below.
    assert field_type["kind"] == "LIST"
    assert field_type["ofType"]["kind"] == "NON_NULL"
    assert field_type["ofType"]["ofType"]["kind"] == "OBJECT"
    assert field_type["ofType"]["ofType"]["name"] == "CategoryType"


def test_djangolistfield_non_nullable_outer_default_via_consumer_annotation() -> None:
    """``list[CategoryType]`` renders as ``[CategoryType!]!`` (non-null outer + items).

    Pins that the default annotation (``list[T]`` without ``| None``)
    renders as ``[T!]!`` — four levels of unwrap match Slice 0's pinned
    introspection shape (spec #"locate `fields[name == \"allBranches\"]`"; rev2 H2,
    spec #"`strawberry.field` in the installed Strawberry version is a function, not a class";
    rev6 M2, spec #"pin the introspection-query mechanism");
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
# Group G (continued) — FK-id elision (mirrors
# ``tests/optimizer/test_extension.py::test_optimizer_elides_forward_fk_id_only_selection``).
# -----------------------------------------------------------------------------


@pytest.mark.django_db
def test_djangolistfield_fk_id_elision_survives(django_assert_num_queries) -> None:
    """FK-id elision fires under a root ``DjangoListField`` for ``id``-only selections.

    Pins the FK-id elision plan emission for a forward-FK
    ``category { id }`` selection: no JOIN, no prefetch, ``only_fields``
    includes ``category_id``, and the plan's ``fk_id_elisions`` tuple
    carries the resolver key. Mirrors the existing integration pattern at
    ``tests/optimizer/test_extension.py::test_optimizer_elides_forward_fk_id_only_selection`` (spec #"test_djangolistfield_fk_id_elision_survives").
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
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
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
# Group H — ``Meta.primary`` interaction (Decision 6).
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
        def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
            return queryset.exclude(name__startswith="a")

    class SecondaryCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
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
        "expected a 'b'-prefixed row to survive — the secondary's get_queryset "
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
        def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
            return queryset.exclude(name__startswith="a")

    class SecondaryCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
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
        "expected an 'a'-prefixed row to survive — the primary's get_queryset "
        "must NOT have been applied when the field targets the secondary"
    )
