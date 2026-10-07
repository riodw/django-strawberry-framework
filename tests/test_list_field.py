"""Package-side DjangoListField tests for construction-time validation, helper mechanics, and internals a live request cannot express.

Specs: ``docs/SPECS/spec-020-list_field-0_0_7.md`` for the field itself and
``docs/spec-050-list_field_arguments-0_0_15.md`` for its ``offset`` / ``limit`` /
``orderBy`` argument surface.

Package tests; system-under-test is ``django_strawberry_framework``
(``AGENTS.md #"Package source in"``). Wire-reachable behavior lives in
``examples/fakeshop/test_query/test_list_field_api.py`` (sync HTTP) and
``examples/fakeshop/test_query/test_list_field_async_api.py`` (async HTTP),
under ``examples/fakeshop/test_query/README.md #"Live-first, both verdicts, and the must-not."``

What stays here, and why no live request can express it:

Construction-time ``ConfigurationError`` never reaches a schema: non-class /
non-DjangoType / unregistered / hostile-repr / hostile-metaclass / directives /
``max_rows`` / ``trusted_max_rows`` / a definition that is not the registry's
exact object.

Helper mechanics GraphQL ``Int`` coercion never supplies: exact-int rejection of
subclasses, unprintable large ints, pickle / repr of ``ListArgumentError``,
``_ListArguments`` immutability, the omitted-args policy-free path, signature
synthesis, wire-name fallback without an executable schema, and malformed
published metadata. The consumer argument matrix is the live sync suite.

Capture-scope internals: the ``ContextVar`` ledger the offset guard consumes,
including reset after a post-``OrderSet`` seal rejection. Consumer-context
isolation over HTTP is the live sibling.

Adapter / cleanup protocol: ``_AsyncQuerySetRows`` wrap/unwrap, declined sync
generator suspension, iterator ``aclose`` notes, Future cancellation (the JSON
error cannot show ``Future.cancelled()``). Live async HTTP covers exotic
resolver classification, safe completion, and ``aclose`` on a rejected window.

A grouped queryset and a merely-truthy ``default_ordering`` have no wire spelling;
a non-expression order term never arrives from GraphQL. Live HTTP pins the
offset-guard verdicts those helpers feed, including hostile ``QuerySet``
subclasses and list-degrading Managers. Instance-shadowed ``.all()`` stays in
``tests/utils/test_querysets.py``: the list field iterates the sealed queryset
and never calls ``.all()`` on the hook result, so HTTP cannot exhibit the leak.

Optimizer-adapter unwrap/rewrap of the async queryset adapter, and the pre-fetch
``check_deadline`` call site. Root list-field SQL is
``examples/fakeshop/test_query/test_library_api.py::
test_library_branches_via_djangolistfield_optimized_nested_selection``.
"""

import asyncio
import contextlib
import copy
import datetime
import gc
import inspect
import pickle
import warnings
from collections.abc import Callable, Generator, Iterator
from types import SimpleNamespace
from typing import TypeVar

import pytest
import strawberry
from apps.library import models as library_models
from apps.products import services
from apps.products.models import Category, Item
from asgiref.sync import sync_to_async
from django.db import models
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models import QuerySet, Value
from django.db.models.functions import Lower, Now, Random, RowNumber
from django.db.models.sql.compiler import SQLCompiler
from django.test import RequestFactory
from graphql import GraphQLError, GraphQLResolveInfo
from strawberry.schema_directive import Location as _DirectiveLocation
from strawberry.schema_directive import schema_directive as _schema_directive
from strawberry.types import Info
from strawberry.types.arguments import StrawberryArgument
from typing_extensions import override

from django_strawberry_framework import (
    DjangoListField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    ErrorPolicy,
    ListArgumentError,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import (
    ConfigurationError,
    DjangoStrawberryFrameworkError,
)
from django_strawberry_framework.list_field import (
    _field_label,
    _ListArguments,
    _model_from_definition,
    _normalize_list_arguments,
    _orderset_class_from_definition,
    _resolve_argument_wire_name,
    _resolver_root_and_info,
    _synthesized_list_signature,
    _validate_djangotype_target,
)
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.registry import registry
from django_strawberry_framework.resource_policy import (
    ResourcePolicy,
)
from django_strawberry_framework.types.relay import SyncMisuseError
from django_strawberry_framework.utils._queryset_private import (
    set_queryset_hints,
)
from django_strawberry_framework.utils.querysets import require_orderset_class
from tests._info import make_info

_M = TypeVar("_M", bound=models.Model)


def _as_strawberry_info(stand_in: object) -> Info[object, object]:
    """Hand a list-field helper an info shape no execution builds.

    Every caller passes a direct-call stub (no ``schema`` / no ``_raw_info``), a hostile or
    hand-built argument-metadata reader, or a spy on the name converter: the shape itself
    is the input under test, so ``tests/_info.py::make_info`` cannot stand in for it.
    """
    # basedpyright: a deliberately partial or hostile info shape is the input under test; the
    # list-field helpers type info as a concrete Strawberry Info
    return stand_in  # pyright: ignore[reportReturnType]


def _as_resolve_info(stand_in: object) -> GraphQLResolveInfo:
    """Hand a duck-typed info to the optimizer hook that takes a graphql-core info."""
    # basedpyright: a stand-in info carrying only the slots the code under test reads;
    # DjangoOptimizerExtension._optimize types info as graphql-core's GraphQLResolveInfo
    return stand_in  # pyright: ignore[reportReturnType]


def _as_orderset_class(cls: type[object]) -> type[OrderSet]:
    """Hand a plain class to the capture scope that takes an ``OrderSet`` class."""
    # basedpyright: a plain stand-in class carrying only the hooks the code under test reads;
    # _order_normalization_scope types the parameter as type[OrderSet]
    return cls  # pyright: ignore[reportReturnType]


@pytest.fixture(autouse=True)
def _isolate_global_registry() -> Iterator[None]:
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
        # basedpyright: the non-class value is the hostile input under test; DjangoListField types
        # the parameter as type[object]
        DjangoListField(non_class)  # pyright: ignore[reportArgumentType]


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
    """An abstract ``DjangoType`` base without ``Meta`` is rejected.

    spec-020 Decision 5 #"is not a registered DjangoType. This usually means".
    Per ``django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"if meta is None:"``, the absence of a ``Meta`` makes
    ``__init_subclass__`` return early WITHOUT setting
    ``__django_strawberry_definition__`` (assigned at
    ``django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__django_strawberry_definition__ = definition"``), so the
    guard's ``getattr(..., None)`` read finds no definition and the target is
    rejected as not registered.
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
        # basedpyright: the non-callable resolver is the hostile input under test; DjangoListField
        # types the parameter as a callable
        DjangoListField(_T, resolver="not callable")  # pyright: ignore[reportArgumentType]


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

    @override
    def __repr__(self) -> str:
        raise RuntimeError("hostile __repr__ detonated")


class _HostileNameMeta(type):
    """A metaclass whose ``__name__`` read detonates.

    CPython enforces a str ``__qualname__`` at class creation but NOT a
    readable ``__name__``: the property shadows the ``type.__name__`` getset
    descriptor in the metaclass MRO.
    """

    @property
    @override
    # basedpyright: the hostile shape under test, a ``__name__`` property whose read raises; the
    # checker rejects any property overriding a base class attribute
    def __name__(cls) -> str:  # pyright: ignore[reportIncompatibleVariableOverride]
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
        # basedpyright: the non-class value whose repr raises is the hostile input under test;
        # DjangoListField types the parameter as type[object]
        DjangoListField(_HostileRepr())  # pyright: ignore[reportArgumentType]


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
        DjangoListField(_DirectiveHolderType(), directives="not-a-directive-list")


def test_djangolistfield_rejects_bare_bytes_directives() -> None:
    """A bare bytes iterates into ints downstream - rejected typed instead."""
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField directives must be a sequence of directive instances",
    ):
        DjangoListField(_DirectiveHolderType(), directives=b"\x01\x02")


def test_djangolistfield_rejects_non_iterable_directives() -> None:
    """A non-iterable detonated raw TypeError inside strawberry.field pre-fix."""
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField directives could not be read",
    ):
        # basedpyright: the non-iterable directives value is the hostile input under test;
        # DjangoListField types the parameter as Sequence[object]
        DjangoListField(_DirectiveHolderType(), directives=42)  # pyright: ignore[reportArgumentType]


def test_djangolistfield_rejects_hostile_iterator_directives() -> None:
    """An iterator raising midway escaped raw ValueError pre-fix - now typed."""
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField directives could not be read",
    ):
        # basedpyright: the raising directives iterable is the hostile input under test;
        # DjangoListField types the parameter as Sequence[object]
        DjangoListField(_DirectiveHolderType(), directives=_ExplodingDirectives())  # pyright: ignore[reportArgumentType]


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


@pytest.mark.django_db(transaction=True)
async def test_djangolistfield_sync_resolver_returning_future_cancels_it() -> None:
    """A rejected asyncio Future is cancelled rather than left pending.

    The JSON error cannot show ``Future.cancelled()``. Live sibling:
    ``test_list_field_api.py::test_shipped_branches_sync_http_rejects_an_awaitable_get_queryset``.
    """

    await sync_to_async(services.seed_data)(1)
    captured: dict[str, asyncio.Future[object]] = {}

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    def _sync_resolver_returning_future(root: object, info: Info) -> asyncio.Future[object]:
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


def test_list_argument_error_rejects_an_unknown_reason_and_renders_bools():
    """``ListArgumentError`` is a GraphQLError; unknown reasons fail closed; bools render as ``bool``.

    Negative / over-ceiling / order-required / queryset-required envelopes are
    the live argument matrix. GraphQL ``Int`` never supplies a bool, so the
    ``bool True`` rendering is only a direct-call fact.
    """
    assert issubclass(ListArgumentError, GraphQLError)
    assert issubclass(ListArgumentError, DjangoStrawberryFrameworkError)
    err = ListArgumentError("items", "offset", "non_integer", value=True)
    assert err.field == "items"
    assert err.argument == "offset"
    assert err.reason == "non_integer"
    assert err.value == "bool True"
    assert err.ceiling is None
    assert err.extensions == {
        "code": "LIST_ARGUMENT_INVALID",
        "argument": "offset",
        "reason": "non_integer",
        "value": "bool True",
    }
    assert (
        "Invalid argument 'offset' on items: expected a non-negative integer, got bool True."
        in str(err)
    )
    with pytest.raises(ValueError, match="Unknown ListArgumentError reason 'custom_reason'"):
        # basedpyright: the unknown reason is the hostile input under test; ListArgumentError types
        # the parameter as _ListArgumentReason
        ListArgumentError("items", "arg", "custom_reason", value=42)  # pyright: ignore[reportArgumentType]


def _named_argument(name: str) -> SimpleNamespace:
    """An argument definition carrying only its ``name``."""
    return SimpleNamespace(name=name)


def _python_named_argument(name: str) -> SimpleNamespace:
    """An argument definition carrying only its ``python_name``."""
    return SimpleNamespace(python_name=name)


def _no_argument_definition(name: str) -> None:
    """A resolver with no definition for any parameter."""
    return None


def test_resolve_argument_wire_name_never_runs_the_schema_name_converter(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
):
    """Neither a valid normalization nor a rejection invokes ``name_converter``.

    The converter is consumer code that Strawberry already ran while building
    the schema; the error path reads the published argument map instead. A
    direct-call stub carries no executable-schema metadata, so the rejection
    reports the default spelling.
    """

    class DummyConverter:
        def __init__(self):
            self.calls = 0

        def from_argument(self, arg: StrawberryArgument) -> str:
            self.calls += 1
            return arg.python_name

    converter = DummyConverter()
    schema_config = SimpleNamespace(name_converter=converter)
    info = SimpleNamespace(
        context={},
        schema=SimpleNamespace(config=schema_config),
        get_argument_definition=_named_argument,
    )
    arm_resource_budget(info.context, ResourcePolicy(max_list_rows=100))

    record = _normalize_list_arguments(
        "items",
        _as_strawberry_info(info),
        None,
        False,
        offset=10,
        limit=20,
    )
    assert record.offset == 10
    assert record.limit == 20
    assert converter.calls == 0

    with pytest.raises(ListArgumentError) as exc_info:
        _normalize_list_arguments("items", _as_strawberry_info(info), None, False, offset=-1)
    assert exc_info.value.reason == "negative"
    assert exc_info.value.extensions is not None
    assert exc_info.value.extensions["argument"] == "offset"
    assert converter.calls == 0


@pytest.mark.parametrize("argument", ["offset", "limit"])
def test_normalize_list_arguments_rejects_int_subclasses_before_their_hooks_can_run(
    argument: str,
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
):
    """``offset`` / ``limit`` must be EXACT ints, so no subclass hook reaches the boundary.

    GraphQL's own ``Int`` coercion always supplies a plain ``int``, so this is
    the direct-call boundary the argument surface also promises to keep typed.
    An ``int`` subclass would otherwise reach the range comparisons and the
    error rendering, running its ``__lt__`` / ``__gt__`` / ``__format__`` inside
    the boundary and replacing the typed ``ListArgumentError`` with whatever the
    consumer hook raised. Each hostile value is rejected as ``non_integer``
    without firing anything.
    """
    fired: list[str] = []

    class HostileInt(int):
        @override
        def __lt__(self, other: object):
            fired.append("__lt__")
            raise RuntimeError("hostile comparison ran")

        @override
        def __gt__(self, other: object):
            fired.append("__gt__")
            raise RuntimeError("hostile comparison ran")

        @override
        def __format__(self, spec: str):
            fired.append("__format__")
            raise RuntimeError("hostile format ran")

    info = make_info(context={})
    arm_resource_budget(info.context, ResourcePolicy(max_list_rows=100))

    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments(
            "items",
            info,
            None,
            False,
            **{argument: HostileInt(5)},
        )
    assert exc.value.argument == argument
    assert exc.value.reason == "non_integer"
    assert isinstance(exc.value.value, str)
    assert exc.value.value.startswith("HostileInt")
    assert fired == []


def test_normalize_list_arguments_renders_an_unprintable_large_int_without_raising(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
):
    """A plain ``int`` too large for CPython to stringify still rejects as a typed error.

    ``sys.set_int_max_str_digits`` caps integer-to-string conversion, so an
    oversized value would detonate an f-string built at the raise site. The
    over-ceiling arm renders through the guarded helper instead.
    """
    info = make_info(context={})
    arm_resource_budget(info.context, ResourcePolicy(max_list_rows=100))

    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments(
            "items",
            info,
            None,
            False,
            offset=10**10000,
        )
    assert exc.value.reason == "over_ceiling"
    assert exc.value.ceiling == 100
    assert "<unprintable int>" in str(exc.value)


@pytest.mark.parametrize(
    ("argument", "value", "rendered"),
    [
        ("offset", True, "bool True"),
        ("offset", False, "bool False"),
        ("offset", "ten", "str 'ten'"),
        ("offset", 3.14, "float 3.14"),
        ("limit", True, "bool True"),
        ("limit", False, "bool False"),
        ("limit", "twenty", "str 'twenty'"),
        ("limit", 3.14, "float 3.14"),
    ],
    ids=[
        "offset-true",
        "offset-false",
        "offset-str",
        "offset-float",
        "limit-true",
        "limit-false",
        "limit-str",
        "limit-float",
    ],
)
def test_normalize_list_arguments_rejects_values_graphql_int_never_supplies(
    argument: str,
    value: object,
    rendered: str,
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
):
    """GraphQL ``Int`` coercion never hands ``_normalize_list_arguments`` a bool, str, or float.

    Those shapes are a direct-call contract: the helper must still reject them as
    ``non_integer`` rather than reaching the range comparisons.
    """
    info = make_info(context={})
    arm_resource_budget(info.context, ResourcePolicy(max_list_rows=100))

    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments(
            "items",
            info,
            None,
            False,
            **{argument: value},
        )
    assert exc.value.argument == argument
    assert exc.value.reason == "non_integer"
    assert exc.value.value == rendered


def test_normalize_list_arguments_names_offset_before_limit_on_direct_call_non_integers(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
):
    """A direct call that GraphQL ``Int`` cannot assemble still names ``offset`` first."""
    info = make_info(context={})
    arm_resource_budget(info.context, ResourcePolicy(max_list_rows=100))

    with pytest.raises(ListArgumentError) as exc:
        _normalize_list_arguments(
            "items",
            info,
            None,
            False,
            offset="bad",
            limit=101,
        )
    assert exc.value.argument == "offset"
    assert exc.value.reason == "non_integer"


@pytest.mark.django_db(transaction=True)
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

        @override
        def __getattribute__(self, name: str):
            if name == "aclose":
                raise RuntimeError("hostile aclose on tracker")
            return super().__getattribute__(name)

    tracker = HostileTracker()

    async def resolver_async_iter(root: object, info: object, **kwargs: object):
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


@pytest.mark.django_db(transaction=True)
async def test_async_completion_adapter_semantics():
    """_AsyncQuerySetRows wraps queryset in async context, exposes __aiter__, and rejects __iter__.

    ``transaction=True`` because the seed runs through ``sync_to_async`` on
    asgiref's executor thread, whose connection sits outside the test-body
    transaction pytest-django opens on the main thread: a plain ``django_db``
    would commit the seeded rows and leave them for every later test.
    """
    from django_strawberry_framework.utils.querysets import (
        unwrap_async_queryset_adapter,
        wrap_async_queryset_adapter,
    )

    await sync_to_async(services.seed_data)(1)

    assert wrap_async_queryset_adapter("not_a_qs") == "not_a_qs"

    qs = Category.objects.all()[:3]
    adapter = wrap_async_queryset_adapter(qs)
    assert unwrap_async_queryset_adapter(adapter)[1]
    assert hasattr(adapter, "__aiter__")
    assert not hasattr(adapter, "__iter__")

    with pytest.raises(TypeError, match="is not iterable"):
        # basedpyright: the test proves the async-only adapter refuses sync iteration
        for _ in adapter:  # pyright: ignore[reportGeneralTypeIssues]
            pass

    rows = [r async for r in adapter]
    assert len(rows) > 0

    unwrapped, was_adapted = unwrap_async_queryset_adapter(adapter)
    assert was_adapted is True
    assert unwrapped is qs

    non_adapter_res, was_adapted2 = unwrap_async_queryset_adapter(qs)
    assert was_adapted2 is False
    assert non_adapter_res is qs


def test_list_field_signature_without_orderset():
    """Target without Meta.orderset_class generates signature with info, offset, limit, and empty return."""

    class NoOrderType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.get(Item) is NoOrderType

    finalize_django_types()
    sig, ann = _synthesized_list_signature(None)

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

    assert registry.get(Item) is WithOrderType

    finalize_django_types()
    sig, ann = _synthesized_list_signature(ItemOrder)

    assert "order_by" in sig.parameters
    assert sig.parameters["order_by"].kind == inspect.Parameter.KEYWORD_ONLY
    assert sig.parameters["order_by"].default is None
    assert sig.parameters["order_by"].annotation == ann["order_by"]

    from django_strawberry_framework.orders import _helper_referenced_ordersets

    order_input_type(ItemOrder)
    assert ItemOrder in _helper_referenced_ordersets
    assert sig.return_annotation is inspect.Signature.empty
    assert "return" not in ann


@pytest.mark.parametrize(
    "shape",
    [
        "limit_alone",
        "zero_offset_with_order",
        "positive_offset_on_model_ordering",
        "order_alone",
        "positive_offset_and_order_without_orderset",
    ],
)
def test_the_capture_scope_stays_closed_for_shapes_the_offset_guard_cannot_use(shape: str):
    """The normalization handoff is paid for by the one request shape that consumes it.

    ``OrderSet._input_has_active_terms`` has exactly one caller - the non-zero
    offset guard's active-order check - and it runs only when a positive
    ``offset`` arrives WITH an ``orderBy`` on a field that captured an
    ``OrderSet`` to normalize through. Every other argument-bearing shape has
    nothing to hand over, so it must not allocate a ledger, set a
    ``ContextVar``, or take the deferred ``orders`` import.

    The no-``OrderSet`` row is the one the predicate can only decide because the
    field's captured sidecar is passed in: over the wire that target publishes
    no ``orderBy`` at all, but a direct call can supply one, and it must reach
    ``require_orderset_class``'s rejection without a scope having been opened
    for a handoff that can never happen.
    """
    from django_strawberry_framework.list_field import _order_normalization_scope
    from django_strawberry_framework.orders.sets import _ORDER_NORMALIZATION_CAPTURE

    @_as_orderset_class
    class SomeOrder:
        pass

    def _record(
        *,
        offset: int | None = None,
        limit: int | None = None,
        order_by_supplied: bool = False,
    ):
        return _ListArguments(
            offset=offset,
            limit=limit,
            order_by=None,
            order_by_supplied=order_by_supplied,
            any_argument_supplied=True,
        )

    args_record, orderset_class = {
        "limit_alone": (_record(limit=5), SomeOrder),
        "zero_offset_with_order": (_record(offset=0, order_by_supplied=True), SomeOrder),
        "positive_offset_on_model_ordering": (_record(offset=3), SomeOrder),
        "order_alone": (_record(order_by_supplied=True), SomeOrder),
        "positive_offset_and_order_without_orderset": (
            _record(offset=3, order_by_supplied=True),
            None,
        ),
    }[shape]
    with _order_normalization_scope(args_record, orderset_class):
        assert _ORDER_NORMALIZATION_CAPTURE.get() is None


def test_the_capture_scope_opens_for_a_positive_offset_with_an_orderset():
    """The one shape the offset guard consumes does open a capture scope, then resets."""
    from django_strawberry_framework.list_field import _order_normalization_scope
    from django_strawberry_framework.orders.sets import _ORDER_NORMALIZATION_CAPTURE

    @_as_orderset_class
    class SomeOrder:
        pass

    args_record = _ListArguments(
        offset=3,
        limit=None,
        order_by=None,
        order_by_supplied=True,
        any_argument_supplied=True,
    )
    with _order_normalization_scope(args_record, SomeOrder):
        assert _ORDER_NORMALIZATION_CAPTURE.get() is not None
    assert _ORDER_NORMALIZATION_CAPTURE.get() is None


@pytest.mark.django_db
def test_list_field_reads_the_target_definition_once_and_dispatches_through_it():
    """The field's ONE definition read is at construction; nothing re-reads it afterwards.

    The counter stays armed across all three phases a stateful target could
    answer differently in - the factory call, schema construction, and a real
    request - and the target is switched to a DECOY definition the moment the
    accepted read is taken. The decoy names a different model and a different
    ``OrderSet``, so any later read would be visible as rows of the wrong table
    or a dispatch through the wrong sidecar.

    That matters concretely: the seed, both visibility seals, the published
    ``orderBy`` argument, and the class the resolver dispatches through all come
    from one object, so a later answer cannot move the field to another table or
    quietly change which ordering ran.
    """
    from django_strawberry_framework.orders import OrderSet

    reads: list[str] = []
    state: dict[str, object] = {"armed": False, "decoy": None}

    class CountingMeta(type):
        @override
        def __getattribute__(cls, name: str):
            if state["armed"] and name == "__django_strawberry_definition__":
                reads.append(name)
                if state["decoy"] is not None:
                    return state["decoy"]
            return super().__getattribute__(name)

    class PublishedOrder(OrderSet):
        class Meta:
            model = Item
            fields = ["name"]

        applies = 0

        @classmethod
        @override
        def apply_sync(
            cls,
            input_value: object,
            queryset: QuerySet[_M],
            info: object,
        ):
            PublishedOrder.applies += 1
            return super().apply_sync(input_value, queryset, info)

    class DecoyOrder(OrderSet):
        class Meta:
            model = Category
            fields = ["name"]

        @classmethod
        @override
        def apply_sync(
            cls,
            input_value: object,
            queryset: QuerySet[_M],
            info: object,
        ):
            raise AssertionError("the field dispatched through a re-read OrderSet")

    class CountedType(DjangoType, metaclass=CountingMeta):
        class Meta:
            model = Item
            fields = ("id", "name")
            orderset_class = PublishedOrder

    class DecoyTargetType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            orderset_class = DecoyOrder
            primary = False

    finalize_django_types()
    target_item = services.seed_decoy_and_target_rows()["item"]
    decoy_names = set(Category.objects.values_list("name", flat=True))

    state["armed"] = True
    field = DjangoListField(CountedType)
    assert reads == ["__django_strawberry_definition__"]

    # From here the target answers with a definition for ANOTHER MODEL carrying
    # another OrderSet: every later read is both counted and consequential.
    state["decoy"] = DecoyTargetType.__django_strawberry_definition__

    @strawberry.type
    class Query:
        items: list[CountedType] = field

    schema = strawberry.Schema(query=Query)
    assert reads == ["__django_strawberry_definition__"]
    assert "orderBy" in str(schema)

    result = schema.execute_sync(
        "{ items(orderBy: [{name: ASC}]) { id name } }",
        context_value={"request": RequestFactory().get("/")},
    )
    assert result.errors is None, result.errors
    assert reads == ["__django_strawberry_definition__"]
    assert result.data is not None
    returned = {row["name"] for row in result.data["items"]}
    assert target_item.name in returned
    # Rows of the decoy definition's table never appear: the seed and both seals
    # stayed on the captured model.
    assert not returned & decoy_names
    assert PublishedOrder.applies == 1


@pytest.mark.django_db
def test_a_consumer_resolver_list_field_also_reads_the_definition_only_at_construction():
    """The ``resolver=`` coloring takes the same one read, and no request-time read.

    A consumer resolver supplies the source, so the seed is not the field's; what
    the field still owns are the two visibility seals and the sidecar dispatch,
    and each of those must run on the construction-time read rather than asking
    the target again mid-request.
    """
    from django_strawberry_framework.orders import OrderSet

    reads: list[str] = []
    state: dict[str, object] = {"armed": False, "decoy": None}

    class CountingMeta(type):
        @override
        def __getattribute__(cls, name: str):
            if state["armed"] and name == "__django_strawberry_definition__":
                reads.append(name)
                if state["decoy"] is not None:
                    return state["decoy"]
            return super().__getattribute__(name)

    class ResolverOrder(OrderSet):
        class Meta:
            model = Item
            fields = ["name"]

    class ResolverDecoyOrder(OrderSet):
        class Meta:
            model = Category
            fields = ["name"]

        @classmethod
        @override
        def apply_sync(
            cls,
            input_value: object,
            queryset: QuerySet[_M],
            info: object,
        ):
            raise AssertionError("the field dispatched through a re-read OrderSet")

    class ResolverCountedType(DjangoType, metaclass=CountingMeta):
        class Meta:
            model = Item
            fields = ("id", "name")
            orderset_class = ResolverOrder

    class ResolverDecoyTargetType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            orderset_class = ResolverDecoyOrder
            primary = False

    finalize_django_types()
    target_item = services.seed_decoy_and_target_rows()["item"]
    decoy_names = set(Category.objects.values_list("name", flat=True))

    def _all_items(root: object, info: object) -> QuerySet[Item]:
        return Item.objects.all()

    state["armed"] = True
    field = DjangoListField(ResolverCountedType, resolver=_all_items)
    assert reads == ["__django_strawberry_definition__"]
    state["decoy"] = ResolverDecoyTargetType.__django_strawberry_definition__

    @strawberry.type
    class Query:
        items: list[ResolverCountedType] = field

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        "{ items(orderBy: [{name: ASC}]) { id name } }",
        context_value={"request": RequestFactory().get("/")},
    )
    assert result.errors is None, result.errors
    assert reads == ["__django_strawberry_definition__"]
    assert result.data is not None
    returned = {row["name"] for row in result.data["items"]}
    assert target_item.name in returned
    assert not returned & decoy_names


@pytest.mark.django_db
def test_an_abstract_model_type_serves_concrete_rows_and_its_default_seed_names_the_model():
    """A ``DjangoType`` over an abstract model serves the concrete rows a resolver returns.

    The generated default resolver has no table to seed from, so it fails with a
    ``ConfigurationError`` naming the abstract model rather than an ``AttributeError``
    off the default manager the abstract model does not have.
    """

    class TitledEntryType(DjangoType):
        class Meta:
            model = library_models.TitledEntry
            fields = ("title",)

    finalize_django_types()
    library_models.ReadingList.objects.create(title="Classics")

    @strawberry.type
    class Query:
        entries: list[TitledEntryType] = DjangoListField(TitledEntryType)

        @strawberry.field(graphql_type=list[TitledEntryType])
        def reading_lists(self) -> list[library_models.TitledEntry]:
            return list(library_models.ReadingList.objects.all())

    schema = strawberry.Schema(query=Query)
    context = {"request": RequestFactory().get("/")}
    served = schema.execute_sync("{ readingLists { title } }", context_value=context)
    assert served.errors is None, served.errors
    assert served.data == {"readingLists": [{"title": "Classics"}]}

    seeded = schema.execute_sync("{ entries { title } }", context_value=context)
    assert seeded.errors is not None
    assert "TitledEntry is an abstract model" in seeded.errors[0].message


@pytest.mark.django_db
def test_the_default_seed_and_both_visibility_seals_use_the_captured_model():
    """The seed queries the captured model's table and the seals validate against it.

    A target whose definition later names another model must not be able to move
    the query, and must not be able to make the source seal and the result seal
    disagree about which table this resolution is over - the two seals of one
    call take one model by construction.
    """
    reads: list[str] = []
    state: dict[str, object] = {"armed": False, "decoy": None}
    seen_models: list[type] = []

    class CountingMeta(type):
        @override
        def __getattribute__(cls, name: str):
            if state["armed"] and name == "__django_strawberry_definition__":
                reads.append(name)
                if state["decoy"] is not None:
                    return state["decoy"]
            return super().__getattribute__(name)

    class SealCountedType(DjangoType, metaclass=CountingMeta):
        class Meta:
            model = Item
            fields = ("id", "name")

        @classmethod
        @override
        def get_queryset(cls, queryset: QuerySet[_M], info: object):
            seen_models.append(queryset.model)
            # Narrow to the two probe rows, one per table, so the answer names
            # which table the seed and the seals were over.
            return queryset.filter(
                name__in=(services.TARGET_ITEM_NAME, services.DECOY_CATEGORY_NAME),
            )

    class SealDecoyType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            primary = False

    finalize_django_types()
    target_item = services.seed_decoy_and_target_rows()["item"]
    decoy_names = set(Category.objects.values_list("name", flat=True))

    state["armed"] = True
    field = DjangoListField(SealCountedType)
    state["decoy"] = SealDecoyType.__django_strawberry_definition__

    @strawberry.type
    class Query:
        items: list[SealCountedType] = field

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        "{ items(limit: 5) { id name } }",
        context_value={"request": RequestFactory().get("/")},
    )
    assert result.errors is None, result.errors
    assert seen_models == [Item]
    assert result.data is not None
    assert [row["name"] for row in result.data["items"]] == [target_item.name]
    assert services.DECOY_CATEGORY_NAME in decoy_names
    assert reads == ["__django_strawberry_definition__"]


@pytest.mark.django_db
def test_list_field_rejects_a_target_whose_definition_hides_its_model():
    """An unreadable or non-model ``definition.model`` fails at the factory line."""

    class ExplodingDefinition:
        origin = None

        @property
        def model(self):
            raise RuntimeError("model read exploded")

    with pytest.raises(ConfigurationError, match="could not read the model from the definition"):
        # basedpyright: the definition whose model read raises is the hostile input under test;
        # _model_from_definition types the parameter as DjangoTypeDefinition
        _model_from_definition(ExplodingDefinition())  # pyright: ignore[reportArgumentType]

    with pytest.raises(ConfigurationError, match="whose model is not a Django model"):
        # basedpyright: the definition whose model is a string is the hostile input under test;
        # _model_from_definition types the parameter as DjangoTypeDefinition
        _model_from_definition(SimpleNamespace(origin=None, model="Item"))  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize(
    "value",
    [
        "false",
        "True",
        1,
        0,
        None,
    ],
)
def test_a_list_field_trusted_max_rows_opt_in_must_be_exactly_boolean(value: object):
    """A misspelled trusted opt-in fails at the line that wrote the field.

    ``trusted_max_rows`` is the one field option whose effect is to let a
    field-declared ``max_rows`` exceed the request's own policy, so it is
    validated where it is declared rather than discovered as a silently widened
    ceiling on every request the field serves.
    """

    class TrustedFlagType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = False

    with pytest.raises(
        ConfigurationError,
        match="DjangoListField trusted_max_rows must be exactly True or False",
    ):
        # basedpyright: each non-bool opt-in is the hostile input under test; DjangoListField types
        # the parameter as bool
        DjangoListField(TrustedFlagType, max_rows=50, trusted_max_rows=value)  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize("value", [True, False])
def test_an_exact_boolean_trusted_max_rows_builds_the_field(value: bool):
    class ExactFlagType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = False

    assert DjangoListField(ExactFlagType, max_rows=50, trusted_max_rows=value) is not None


def test_list_field_direct_call_safe_non_integer_rendering(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
):
    """Safe rendering of non-integer values in ListArgumentError message."""
    info = make_info(context={})
    arm_resource_budget(info.context, ResourcePolicy(max_list_rows=10))

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
    # basedpyright: the undeclared attribute is the extra instance state the roundtrip must carry;
    # ListArgumentError declares no such attribute
    err.custom_tag = "tagged"  # pyright: ignore[reportAttributeAccessIssue]

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


def test_list_field_direct_call_schema_name_fallback_and_definition_lookup(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
):
    """Direct-call stubs fall back to the default spelling; a definition alone is not a name."""
    info_no_def = SimpleNamespace(schema=None)
    assert _resolve_argument_wire_name(_as_strawberry_info(info_no_def), "offset") == "offset"
    assert _resolve_argument_wire_name(_as_strawberry_info(info_no_def), "limit") == "limit"
    assert _resolve_argument_wire_name(_as_strawberry_info(info_no_def), "order_by") == "orderBy"
    assert (
        _resolve_argument_wire_name(_as_strawberry_info(info_no_def), "custom_arg") == "custom_arg"
    )

    class ArgDef:
        name = "order_by"
        python_name = "order_by"
        graphql_name = None

    # A definition but no ``_raw_info``: no executable schema published a name, so
    # the default spelling is the only truthful answer.

    def _order_by_definition(name: str) -> ArgDef:
        return ArgDef()

    info_stub = SimpleNamespace(
        schema=SimpleNamespace(config=SimpleNamespace(name_converter=object())),
        get_argument_definition=_order_by_definition,
        context={},
    )
    arm_resource_budget(info_stub.context, ResourcePolicy(max_list_rows=10))
    _normalize_list_arguments(
        "field",
        _as_strawberry_info(info_stub),
        None,
        False,
        offset=1,
        limit=2,
    )
    with pytest.raises(ListArgumentError) as exc_info:
        _normalize_list_arguments("field", _as_strawberry_info(info_stub), None, False, offset=-1)
    assert exc_info.value.extensions is not None
    assert exc_info.value.extensions["argument"] == "offset"


def test_published_wire_name_rejects_malformed_schema_metadata():
    """Executable-schema metadata that cannot name the argument is a configuration error."""
    from graphql import (
        GraphQLArgument,
        GraphQLField,
        GraphQLInt,
        GraphQLObjectType,
        GraphQLScalarType,
    )

    from django_strawberry_framework.list_field import _published_wire_name

    # graphql-core's ``GraphQLNamedType.__new__`` widens every built-in scalar to its base.
    assert isinstance(GraphQLInt, GraphQLScalarType)

    arg_def = SimpleNamespace(python_name="offset")

    # 1. No ``_raw_info`` at all: a direct-call stub, so no published name.
    assert _published_wire_name(_as_strawberry_info(SimpleNamespace()), arg_def, "offset") is None

    # 2. A ``_raw_info`` read that fails for any other reason is a broken schema.
    class ExplodingInfo:
        @property
        def _raw_info(self):
            raise RuntimeError("simulated raw-info failure")

    with pytest.raises(
        ConfigurationError,
        match="Failed to read the schema field for argument 'offset'",
    ):
        # basedpyright: the info whose _raw_info read raises is the hostile input under test;
        # _published_wire_name types info as a concrete Strawberry Info
        _published_wire_name(ExplodingInfo(), arg_def, "offset")  # pyright: ignore[reportArgumentType]

    # 3. The field exists but no argument carries this definition back-reference.
    other_def = SimpleNamespace(python_name="offset")
    field = GraphQLField(
        GraphQLInt,
        args={
            "offset": GraphQLArgument(GraphQLInt, extensions={"strawberry-definition": other_def}),
        },
    )
    parent = GraphQLObjectType("Query", {"cats": field})
    raw = SimpleNamespace(parent_type=parent, field_name="cats")
    info = SimpleNamespace(_raw_info=raw, field_name="cats")
    with pytest.raises(ConfigurationError, match="has a definition but no published wire name"):
        _published_wire_name(_as_strawberry_info(info), arg_def, "offset")

    # 4. The parent type does not even publish the field.
    raw_missing = SimpleNamespace(parent_type=parent, field_name="missing")
    info_missing = SimpleNamespace(_raw_info=raw_missing, field_name="missing")
    with pytest.raises(
        ConfigurationError,
        match="Failed to read the published arguments for 'offset'",
    ):
        _published_wire_name(_as_strawberry_info(info_missing), arg_def, "offset")

    # 5. The matching back-reference returns the published key, whatever its spelling.
    field_ok = GraphQLField(
        GraphQLInt,
        args={
            "OFFSET": GraphQLArgument(GraphQLInt, extensions={"strawberry-definition": arg_def}),
        },
    )
    parent_ok = GraphQLObjectType("Query", {"cats": field_ok})
    info_ok = SimpleNamespace(_raw_info=SimpleNamespace(parent_type=parent_ok, field_name="cats"))
    assert _published_wire_name(_as_strawberry_info(info_ok), arg_def, "offset") == "OFFSET"


def test_list_field_record_independence(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
):
    """_ListArguments fields operate independently without proxy conflation."""
    info = make_info(context={})
    arm_resource_budget(info.context, ResourcePolicy(max_list_rows=10))

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

    # order_by_supplied drives queryset_required even when order_by=[]
    rec_order_empty = _normalize_list_arguments(
        "f",
        info,
        None,
        False,
        order_by=[],
    )
    assert rec_order_empty.order_by_supplied is True
    assert rec_order_empty.order_by == []

    from django_strawberry_framework.list_field import _build_non_queryset_rejection_error

    rejection = _build_non_queryset_rejection_error(rec_order_empty, info)
    assert isinstance(rejection, ListArgumentError)
    assert rejection.reason == "queryset_required"


def test_omitted_list_arguments_do_not_resolve_policy(monkeypatch: pytest.MonkeyPatch):
    """The no-argument normalization path is allocation-only and policy-free."""

    def _policy_must_not_resolve(_info: object) -> None:
        pytest.fail("omitted arguments must not resolve policy")

    monkeypatch.setattr(
        "django_strawberry_framework.list_field.policy_from_info",
        _policy_must_not_resolve,
    )

    record = _normalize_list_arguments(
        "items",
        make_info(),
        None,
        False,
    )

    assert record == _ListArguments(None, None, None, False, False)


def test_resolver_call_context_accepts_strawberry_shape_and_rejects_unknown_inputs():
    info = SimpleNamespace(field_name="items")
    root = object()

    assert _resolver_root_and_info((root, info), {}) == (root, info)
    assert _resolver_root_and_info((), {"root": root, "info": info}) == (root, info)
    with pytest.raises(TypeError, match="only root and info positional"):
        _resolver_root_and_info((root, info, object()), {})
    with pytest.raises(TypeError, match="unexpected keyword inputs: surprise"):
        _resolver_root_and_info((), {"info": info, "surprise": True})
    with pytest.raises(TypeError, match="multiple values for root"):
        _resolver_root_and_info((root, info), {"root": root})
    with pytest.raises(TypeError, match="multiple values for info"):
        _resolver_root_and_info((root, info), {"info": info})
    with pytest.raises(TypeError, match="requires info"):
        _resolver_root_and_info((root,), {})


def test_field_and_orderset_metadata_reads_fail_closed():
    class HostileInfo:
        @property
        def field_name(self):
            raise RuntimeError("unreadable field name")

    class HostileDefinition:
        @property
        def orderset_class(self):
            raise RuntimeError("unreadable sidecar")

    class Target:
        __django_strawberry_definition__ = HostileDefinition()

    # basedpyright: the info whose field_name read raises is the hostile input under test;
    # _field_label types info as a concrete Strawberry Info
    assert _field_label(HostileInfo()) == "DjangoListField"  # pyright: ignore[reportArgumentType]
    assert _field_label(make_info(field_name="items")) == "items"
    # The sidecar read fails LOUDLY rather than answering None: publishing a
    # schema without ``orderBy`` for a target that declares one would be a
    # silent SDL change at the line that wrote the field.
    with pytest.raises(ConfigurationError, match="could not read Meta.orderset_class"):
        # basedpyright: the definition whose orderset_class read raises is the hostile input under
        # test; _orderset_class_from_definition types the parameter as DjangoTypeDefinition
        _orderset_class_from_definition(Target.__django_strawberry_definition__)  # pyright: ignore[reportArgumentType]


def test_argument_definition_metadata_reads_fail_closed():
    class HostileInfo:
        @property
        def get_argument_definition(self):
            raise RuntimeError("unreadable argument metadata")

    with pytest.raises(ConfigurationError, match="argument-definition resolver"):
        # basedpyright: the info whose get_argument_definition read raises is the hostile input
        # under test; _resolve_argument_wire_name types info as a concrete Strawberry Info
        _resolve_argument_wire_name(HostileInfo(), "offset")  # pyright: ignore[reportArgumentType]

    def raise_from_lookup(_name: str):
        raise RuntimeError("unreadable argument definition")

    with pytest.raises(ConfigurationError, match="definition for argument"):
        _resolve_argument_wire_name(
            _as_strawberry_info(SimpleNamespace(get_argument_definition=raise_from_lookup)),
            "offset",
        )


async def test_list_field_rejected_async_iterator_cleanup_and_notes():
    """Rejected async-only iterator witnesses 0 anext calls, 1 aclose call, and notes on cleanup error."""
    from django_strawberry_framework.list_field import _handle_non_queryset_rejections_async

    class InstrumentedAsyncSource:
        def __init__(self, fail_close: bool = False):
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

    info = make_info(context={})
    args_record = _ListArguments(
        offset=None,
        limit=None,
        order_by=[{"name": "ASC"}],
        order_by_supplied=True,
        any_argument_supplied=True,
    )

    # Clean close
    src_clean = InstrumentedAsyncSource(fail_close=False)
    with pytest.raises(ListArgumentError) as exc_clean:
        await _handle_non_queryset_rejections_async(
            src_clean,
            args_record,
            info,
        )
    assert exc_clean.value.reason == "queryset_required"
    assert src_clean.anext_calls == 0
    assert src_clean.aclose_calls == 1

    # Cleanup error attaches note without masking ListArgumentError
    src_fail = InstrumentedAsyncSource(fail_close=True)
    with pytest.raises(ListArgumentError) as exc_fail:
        await _handle_non_queryset_rejections_async(
            src_fail,
            args_record,
            info,
        )
    assert exc_fail.value.reason == "queryset_required"
    assert src_fail.anext_calls == 0
    assert src_fail.aclose_calls == 1
    notes = getattr(exc_fail.value, "__notes__", [])
    assert any("DjangoListField iterator cleanup failed" in str(n) for n in notes)


def test_list_field_optimizer_adapter_unwrap_rewrap_and_early_returns():
    """DjangoOptimizerExtension._optimize unwrap/rewrap identity, marks, and early return paths."""
    from django_strawberry_framework.utils.querysets import (
        unwrap_async_queryset_adapter,
        wrap_async_queryset_adapter,
    )

    ext = DjangoOptimizerExtension()

    # 1. Non-adapted queryset stays non-adapted
    qs = Category.objects.all()
    info_unresolved = _as_resolve_info(SimpleNamespace(field_name="cats", return_type=object()))
    out1 = ext._optimize(qs, info_unresolved)
    assert not unwrap_async_queryset_adapter(out1)[1]
    assert out1 is qs

    # 2. Adapted queryset on unresolved return type: early return rewraps adapter
    adapter = wrap_async_queryset_adapter(qs)
    out2 = ext._optimize(adapter, info_unresolved)
    assert unwrap_async_queryset_adapter(out2)[1]
    unwrapped2, was2 = unwrap_async_queryset_adapter(out2)
    assert was2 is True
    assert unwrapped2 is qs

    # 3. Adapted queryset on already-evaluated inner queryset: early return rewraps adapter
    qs_evaluated = Category.objects.all()
    qs_evaluated._result_cache = []
    adapter_eval = wrap_async_queryset_adapter(qs_evaluated)
    out3 = ext._optimize(adapter_eval, info_unresolved)
    assert unwrap_async_queryset_adapter(out3)[1]
    unwrapped3, was3 = unwrap_async_queryset_adapter(out3)
    assert was3 is True
    assert unwrapped3 is qs_evaluated

    # 4. Sliced adapter preserves slice marks through unwrap/rewrap
    qs_sliced = Category.objects.all()[2:5]
    adapter_sliced = wrap_async_queryset_adapter(qs_sliced)
    out4 = ext._optimize(adapter_sliced, info_unresolved)
    assert unwrap_async_queryset_adapter(out4)[1]
    unwrapped4, _ = unwrap_async_queryset_adapter(out4)
    assert isinstance(unwrapped4, models.QuerySet)
    assert unwrapped4.query.low_mark == 2
    assert unwrapped4.query.high_mark == 5


def test_list_field_deadline_check_position(
    monkeypatch: pytest.MonkeyPatch,
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
):
    """check_deadline is invoked in pre-fetch position for argument-bearing requests."""
    import django_strawberry_framework.resource_policy as rp

    check_calls = 0
    orig_check = rp.check_deadline

    def spy_check(info: object):
        nonlocal check_calls
        check_calls += 1
        return orig_check(info)

    monkeypatch.setattr(rp, "check_deadline", spy_check)

    info = make_info(context={})
    arm_resource_budget(info.context, ResourcePolicy(max_list_rows=10))

    args_record = _ListArguments(
        offset=1,
        limit=2,
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
        model=Item,
        orderset_class=None,
        is_async_context=False,
    )
    assert res is not None
    assert check_calls == 1


def test_list_field_seal_axis_subclass_and_routing_intent():
    """A sealable subclass is normalized to a plain QuerySet, and routing intent is enforced.

    The ``untrusted`` verdict this seam can also produce is proved over real HTTP
    on both public overrides (the live malformed-result matrices), so it is not
    duplicated here.
    """
    from django_strawberry_framework.utils.querysets import (
        _snapshot_routing_intent,
        _validate_post_orderset_result,
    )

    class CustomQuerySetSubclass(models.QuerySet[Item]):
        pass

    class ItemSealType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    base_qs = Item.objects.all()
    sub_qs = CustomQuerySetSubclass(model=Item)

    # 1. Sealable subclass is normalized to plain QuerySet
    sealed = _validate_post_orderset_result(
        ItemSealType,
        _snapshot_routing_intent(base_qs, "Custom.apply"),
        sub_qs,
        "Custom.apply",
    )
    assert type(sealed) is models.QuerySet

    # 2. Routing intent: _db is None accepted when _hints match, rejected when _hints differ
    qs_match = Item.objects.all()
    set_queryset_hints(qs_match, {"shard": "a"})
    base_with_hints = Item.objects.all()
    set_queryset_hints(base_with_hints, {"shard": "a"})
    sealed_hints = _validate_post_orderset_result(
        ItemSealType,
        _snapshot_routing_intent(base_with_hints, "Custom.apply"),
        qs_match,
        "Custom.apply",
    )
    assert type(sealed_hints) is models.QuerySet

    qs_mismatch = Item.objects.all()
    set_queryset_hints(qs_mismatch, {"shard": "b"})
    with pytest.raises(ConfigurationError, match="changed database routing intent"):
        _validate_post_orderset_result(
            ItemSealType,
            _snapshot_routing_intent(base_with_hints, "Custom.apply"),
            qs_mismatch,
            "Custom.apply",
        )


def test_list_field_declined_sync_cleanup_generator_suspended(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
):
    """Declined sync cleanup: generator truncated by client window stays suspended and resumable."""
    finally_ran = False

    def sync_numbers() -> Generator[int, None, None]:
        nonlocal finally_ran
        try:
            yield from range(10)
        finally:
            finally_ran = True

    info = SimpleNamespace(context={}, schema=None)
    arm_resource_budget(info.context, ResourcePolicy(max_list_rows=10))

    g = sync_numbers()
    args_record = _ListArguments(
        offset=2,
        limit=3,
        order_by=None,
        order_by_supplied=False,
        any_argument_supplied=True,
    )

    from django_strawberry_framework.resource_policy import _windowed_rows

    res = _windowed_rows(g, info, offset=args_record.offset, requested_limit=args_record.limit)
    assert res == [2, 3, 4]
    assert finally_ran is False

    assert next(g) == 5
    assert finally_ran is False
    g.close()
    assert finally_ran is True


#: A fixed aware instant a predicate can compare against without a clock in the statement.
_PREDICATE_STAMP = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)


def _predicate_ordering(lookup: str, threshold: object):
    """A conditional ordering whose predicate compares ``lookup`` against ``threshold``."""
    return (
        models.Case(
            models.When(**{lookup: threshold}, then=Value(0)),
            default=Value(1),
        ),
    )


def test_order_term_classifier_rejects_a_non_expression_term():
    """A term that is neither an expression nor a name is not a readable leaf.

    GraphQL never supplies an ``int`` as an ordering term; the classifier still
    has to fail closed on a term matching neither arm rather than fall through
    to a verdict.
    """
    from django_strawberry_framework.list_field import _is_deterministic_order_term

    # basedpyright: the path under test never reads the query; _is_deterministic_order_term types
    # the parameter as Query
    assert _is_deterministic_order_term(SimpleNamespace(), 42) is False  # pyright: ignore[reportArgumentType]


def test_order_term_classifier_refuses_a_relation_ordering_cycle(monkeypatch: pytest.MonkeyPatch):
    """Two models whose defaults order by each other compile to an error, never to a page.

    Django raises ``FieldError("Infinite loop caused by ordering.")`` for such a
    pair, so the classifier has no order to certify and must stop at the repeat
    rather than follow the relation forever.
    """
    from django_strawberry_framework.list_field import _is_model_default_ordering_active

    monkeypatch.setattr(library_models.Shelf._meta, "ordering", ("branch",))
    monkeypatch.setattr(library_models.Branch._meta, "ordering", ("shelves",))

    assert _is_model_default_ordering_active(library_models.Shelf.objects.all()) is False


def test_order_term_classifier_refuses_a_piece_that_is_not_a_field(
    monkeypatch: pytest.MonkeyPatch,
):
    """A path piece Django reads as a transform or a lookup is not a column this package can name.

    Only a path resolving to a field all the way down says what the rows are
    ordered by, so an unresolvable piece is refused instead of certified.
    """
    from django_strawberry_framework.list_field import _is_model_default_ordering_active

    monkeypatch.setattr(library_models.Shelf._meta, "ordering", ("code__lower",))

    assert _is_model_default_ordering_active(library_models.Shelf.objects.all()) is False


def test_order_term_classifier_reads_a_reverse_relation_target_ordering(
    monkeypatch: pytest.MonkeyPatch,
):
    """A reverse relation expands into its own model's default exactly as a forward one does.

    The name in front of the ordering is a relation either way, and the order the
    rows come back in is the related model's.
    """
    from django_strawberry_framework.list_field import _is_model_default_ordering_active

    monkeypatch.setattr(library_models.Branch._meta, "ordering", ("shelves",))

    monkeypatch.setattr(library_models.Shelf._meta, "ordering", (Random(),))
    assert _is_model_default_ordering_active(library_models.Branch.objects.all()) is False

    monkeypatch.setattr(library_models.Shelf._meta, "ordering", ("code",))
    assert _is_model_default_ordering_active(library_models.Branch.objects.all()) is True


def test_order_term_classifier_follows_a_chain_of_relation_defaults(
    monkeypatch: pytest.MonkeyPatch,
):
    """Expansion is recursive, so a random default two relations away still decides.

    ``Book`` orders by its shelf, the shelf by its branch, and the branch at
    random: the statement the database runs is the random one.
    """
    from django_strawberry_framework.list_field import _is_model_default_ordering_active

    monkeypatch.setattr(library_models.Book._meta, "ordering", ("shelf",))
    monkeypatch.setattr(library_models.Shelf._meta, "ordering", ("branch",))

    monkeypatch.setattr(library_models.Branch._meta, "ordering", (Random(),))
    assert _is_model_default_ordering_active(library_models.Book.objects.all()) is False

    monkeypatch.setattr(library_models.Branch._meta, "ordering", ("name",))
    assert _is_model_default_ordering_active(library_models.Book.objects.all()) is True


def test_order_reference_classifier_reads_the_annotation_a_reference_names():
    """An ``F`` is resolved through the query's annotations before it is read as a column.

    ``Query.resolve_ref`` looks the whole name up as an annotation first, so a
    reference naming a random one carries that randomness and is refused.
    """
    from django_strawberry_framework.list_field import _has_deterministic_ordering

    queryset = Category.objects.annotate(rnd=Random()).order_by(models.F("rnd"))

    assert _has_deterministic_ordering(queryset) is False


def test_order_reference_classifier_keeps_an_expanded_reference_a_column_order(
    monkeypatch: pytest.MonkeyPatch,
):
    """A reference lifted out of an expanded ordering names a column, not another default.

    Only a string term reaches the compiler's relation expansion. A ``Book``
    ordering by its shelf reaches a shelf ordering by ``F("branch")``, which the
    outer query resolves to the foreign key column - so the branch's own random
    default is never what the rows come back in.
    """
    from django_strawberry_framework.list_field import _is_model_default_ordering_active

    monkeypatch.setattr(library_models.Book._meta, "ordering", ("shelf",))
    monkeypatch.setattr(library_models.Shelf._meta, "ordering", (models.F("branch"),))
    monkeypatch.setattr(library_models.Branch._meta, "ordering", (Random(),))

    assert _is_model_default_ordering_active(library_models.Book.objects.all()) is True


class _SubclassedLower(Lower):
    """A subclass of an approved function: an approved name over a different ``as_sql``."""

    @override
    def as_sql(
        self,
        compiler: SQLCompiler,
        connection: BaseDatabaseWrapper,
        function: str | None = None,
        template: str | None = None,
        arg_joiner: str | None = None,
        **extra_context: object,
    ) -> tuple[str, tuple[str | int, ...]]:
        return "RANDOM()", ()


class _SubclassedF(models.F):
    """A subclass of the reference form: an ordinary name over a different resolution."""

    @override
    def resolve_expression(self, *args: object, **kwargs: object):
        return Random()


class _SubclassedQ(models.Q):
    """A subclass of the predicate form, resolving to SQL instead of to its children."""

    @override
    # basedpyright: deliberately resolves to foreign SQL, the predicate subclass the guard refuses
    def resolve_expression(self, *args: object, **kwargs: object):  # pyright: ignore[reportIncompatibleMethodOverride]
        return Random()


class _ResolvingName(str):
    """A field path that is an expression, because it carries ``resolve_expression``."""

    def resolve_expression(self, *args: object, **kwargs: object):
        return Random()


@pytest.mark.parametrize(
    ("term", "expected"),
    [
        (Lower(models.F("code")), True),
        (_SubclassedLower(models.F("code")), False),
        (models.Min("id"), True),
        (models.Count("*"), True),
        (models.Sum("id"), False),
        (models.Window(RowNumber()), False),
        (models.F("code"), True),
        (_SubclassedF("code"), False),
        (models.Q(code__gt="A"), True),
        (_SubclassedQ(code__gt="A"), False),
        (_ResolvingName("code"), False),
    ],
    ids=[
        "approved-function",
        "subclass-of-approved-function",
        "approved-aggregate",
        "row-count",
        "unapproved-aggregate",
        "window",
        "reference",
        "subclass-of-reference",
        "predicate",
        "subclass-of-predicate",
        "name-that-resolves",
    ],
)
def test_order_term_classifier_admits_only_named_forms(term: object, expected: bool):
    """A node is read through because this package names its form, never because it has children.

    An expression's sources say nothing about the SQL it wraps them in, and a
    subclass of a pure function carries an ``as_sql`` of its own under an
    approved name - so membership is by exact type, and a form nobody listed is
    refused however ordinary its children look. The two reference forms are
    matched exactly for the same reason one step earlier: a subclass of ``F`` or
    of ``Q`` resolves to an expression of its own, whatever name or children it
    was built with. Which arm a term takes is decided by ``resolve_expression``
    the way the compiler decides it, so a ``str`` carrying that method is read as
    the expression it resolves to and never as the field path it spells.
    """
    from django_strawberry_framework.list_field import _is_deterministic_order_term

    query = library_models.Shelf.objects.all().query

    assert _is_deterministic_order_term(query, term) is expected


def test_order_predicate_classifier_refuses_an_unresolvable_reference(
    monkeypatch: pytest.MonkeyPatch,
):
    """A predicate naming neither an annotation nor a field is a reference nobody can read.

    The comparison still reaches the statement, so a head this package cannot
    resolve is refused rather than certified on the strength of its literal.
    """
    from django_strawberry_framework.list_field import _is_model_default_ordering_active

    monkeypatch.setattr(
        library_models.Shelf._meta,
        "ordering",
        _predicate_ordering("nowhere__gt", "A"),
    )

    assert _is_model_default_ordering_active(library_models.Shelf.objects.all()) is False


@pytest.mark.parametrize(
    ("aliased", "expected"),
    [(Value(_PREDICATE_STAMP, output_field=models.DateTimeField()), True), (Now(), False)],
    ids=["readable-alias", "unreadable-alias"],
)
def test_order_predicate_classifier_reads_the_annotation_under_a_transform_chain(
    monkeypatch: pytest.MonkeyPatch,
    aliased: models.Expression,
    expected: bool,
):
    """A lookup is a reference plus trailing lookups, and the reference is what decides.

    ``stamp__year__gt`` names the annotation ``stamp`` under a ``year`` transform
    and a ``gt`` lookup, so the verdict follows what ``stamp`` itself is: a
    literal is readable, while a database function called at statement time is
    not.
    """
    from django_strawberry_framework.list_field import _is_model_default_ordering_active

    monkeypatch.setattr(
        library_models.Shelf._meta,
        "ordering",
        _predicate_ordering("stamp__year__gt", 2000),
    )
    queryset = library_models.Shelf.objects.alias(stamp=aliased)

    assert _is_model_default_ordering_active(queryset) is expected


@pytest.mark.django_db
def test_is_model_default_ordering_active_rejects_a_grouped_queryset(
    monkeypatch: pytest.MonkeyPatch,
):
    """Grouping suppresses model default ordering the same way ``QuerySet.ordered`` does.

    A grouped source has one live spelling (``test_list_field_api.py``'s row-count
    control, which annotates ``Count("*")``), but that page is ACCEPTED: an
    annotated ``order_by`` is an explicit ordering, so the guard never consults
    the model default there. The ``group_by`` arm decides only when a grouped
    queryset arrives with no explicit ordering, which no shipped field produces;
    extra-order, random, reverse, and empty-queryset verdicts are the live
    offset-guard matrix.
    """
    from django_strawberry_framework.list_field import _is_model_default_ordering_active

    monkeypatch.setattr(Category._meta, "ordering", ("name",))
    qs = Category.objects.all()
    assert _is_model_default_ordering_active(qs) is True
    qs.query.group_by = ("name",)
    assert _is_model_default_ordering_active(qs) is False


def test_list_field_constructor_validation_precedence():
    """Constructor validates collection bound before target_type or directives."""
    # Negative bound raises collection bound error even if target_type is invalid
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField max_rows must be a positive integer; got int -1\.",
    ):
        DjangoListField(object, max_rows=-1)

    # Zero bound raises collection bound error even if target_type is invalid
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField max_rows must be a positive integer; got int 0\.",
    ):
        DjangoListField(object, max_rows=0)

    # Valid bound proceeds to target_type validation
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField requires a DjangoType subclass; got object\.",
    ):
        DjangoListField(object, max_rows=10)


def test_list_field_post_orderset_validator_zero_consumer_dispatch():
    """_validate_post_orderset_result extracts routing intent without consumer dispatch."""
    from django_strawberry_framework.utils.querysets import (
        _routing_hints_equal,
        _safe_routing_repr,
        _snapshot_routing_intent,
        _validate_post_orderset_result,
    )

    class CatDispatchType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class PoisonAttr:
        @override
        def __eq__(self, other: object):
            raise RuntimeError("PoisonAttr __eq__ called")

        @override
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
    class PoisonGetattributeQS(models.QuerySet[Category]):
        @override
        def __getattribute__(self, name: str):
            if name in ("_db", "_hints"):
                raise RuntimeError(f"consumer __getattribute__ called for {name}")
            return super().__getattribute__(name)

    poison_qs = PoisonGetattributeQS(model=Category)
    sealed = _validate_post_orderset_result(
        CatDispatchType,
        _snapshot_routing_intent(poison_qs, "Poison.apply_sync"),
        poison_qs,
        "Poison.apply_sync",
    )
    assert sealed is not None


def test_list_arguments_immutability():
    """_ListArguments is an immutable frozen dataclass."""
    import dataclasses

    args = _ListArguments(
        offset=0,
        limit=10,
        order_by=None,
        order_by_supplied=False,
        any_argument_supplied=True,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        # basedpyright: the write to the frozen dataclass field is the mutation under test; the
        # checker rejects assignment to a frozen field
        args.offset = 5  # pyright: ignore[reportAttributeAccessIssue]
    with pytest.raises(dataclasses.FrozenInstanceError):
        # basedpyright: the write to the frozen dataclass field is the mutation under test; the
        # checker rejects assignment to a frozen field
        args.limit = 20  # pyright: ignore[reportAttributeAccessIssue]
    with pytest.raises(dataclasses.FrozenInstanceError):
        # basedpyright: the undeclared slot write is the rejected operation under test
        args.extra_attribute = "disallowed"  # pyright: ignore[reportAttributeAccessIssue]


def test_is_model_default_ordering_active_exact_bool_identity(monkeypatch: pytest.MonkeyPatch):
    """_is_model_default_ordering_active requires exact boolean True identity."""
    from django_strawberry_framework.list_field import _is_model_default_ordering_active

    monkeypatch.setattr(Category._meta, "ordering", ("name",))
    query_mock = SimpleNamespace(
        default_ordering=1,
        order_by=(),
        extra_order_by=(),
        group_by=(),
        annotations={},
        extra={},
        get_meta=lambda: Category._meta,
    )
    qs_mock = SimpleNamespace(model=Category, query=query_mock)
    # basedpyright: a stand-in queryset carrying only the slots the code under test reads;
    # _is_model_default_ordering_active types the parameter as QuerySet
    assert _is_model_default_ordering_active(qs_mock) is False  # pyright: ignore[reportArgumentType]

    query_mock.default_ordering = True
    # basedpyright: a stand-in queryset carrying only the slots the code under test reads;
    # _is_model_default_ordering_active types the parameter as QuerySet
    assert _is_model_default_ordering_active(qs_mock) is True  # pyright: ignore[reportArgumentType]


def test_list_field_wire_name_resolution_falls_back_without_a_usable_definition():
    """Every arm that cannot name the wire argument falls back to the default name.

    ``_resolve_argument_wire_name`` runs only while building an error, so a
    context that cannot answer "what is this argument called on the wire?" must
    still produce the error rather than replacing it with its own failure. Two
    such contexts reach the same fallback: no definition for the parameter, and a
    definition with no executable-schema metadata behind it.
    """
    # A resolver that has no definition for the parameter.
    info_no_argdef = SimpleNamespace(
        schema=None,
        get_argument_definition=_no_argument_definition,
    )
    assert _resolve_argument_wire_name(_as_strawberry_info(info_no_argdef), "limit") == "limit"

    # A definition, but no ``_raw_info`` carrying a published argument map.
    info_no_schema = SimpleNamespace(
        schema=None,
        get_argument_definition=_python_named_argument,
    )
    assert _resolve_argument_wire_name(_as_strawberry_info(info_no_schema), "offset") == "offset"


def test_list_field_wire_name_resolution_surfaces_broken_schema_metadata():
    """A definition whose published map cannot be read is a configuration error, not a fallback.

    An absent map is a shape the framework tolerates; a map that blows up while
    being read is a broken schema, and swallowing it would hide the breakage
    behind a default argument name in every subsequent error message.
    """

    class ExplodingRawInfo:
        @property
        def parent_type(self):
            raise RuntimeError("simulated parent-type failure")

    info = SimpleNamespace(
        _raw_info=ExplodingRawInfo(),
        get_argument_definition=_python_named_argument,
    )
    with pytest.raises(
        ConfigurationError,
        match="Failed to read the schema field for argument 'order_by'",
    ):
        _resolve_argument_wire_name(_as_strawberry_info(info), "order_by")


def test_require_orderset_class_rejects_a_target_without_one():
    """Ordering a target that declares no ``orderset_class`` is a configuration error.

    Both colorings of the ordering step route through this one requirement, so
    the message names the target rather than failing later with an attribute
    error inside the ordering call.
    """

    class Orderless:
        __django_strawberry_definition__ = SimpleNamespace(orderset_class=None)

    # basedpyright: a stand-in definition carrying only the slots the code under test reads;
    # _orderset_class_from_definition types the parameter as DjangoTypeDefinition
    assert _orderset_class_from_definition(Orderless.__django_strawberry_definition__) is None  # pyright: ignore[reportArgumentType]
    with pytest.raises(
        ConfigurationError,
        match=r"Field target Orderless has no orderset_class configured\.",
    ):
        # basedpyright: a plain stand-in class carrying only the hooks the code under test reads;
        # require_orderset_class types the parameter as type[DjangoType]
        require_orderset_class(Orderless, None)  # pyright: ignore[reportArgumentType]


@pytest.mark.django_db
def test_djangolistfield_resets_the_capture_scope_when_the_seal_rejects():
    """A rejected ordering result still closes the capture scope it was opened in.

    The post-``OrderSet`` seal runs after ``apply_sync`` has published its
    normalization into the scope, so the rejection path is the one exit that
    leaves a record with the guard never reached. The scope's token is reset in
    ``finally``, so the failing request cannot poison the next resolution on the
    same task, and the consumer context is never written.
    """
    from django_strawberry_framework.orders import OrderSet
    from django_strawberry_framework.orders.sets import _ORDER_NORMALIZATION_CAPTURE

    services.seed_data(1)

    class EvaluatedReturningOrder(OrderSet):
        class Meta:
            model = Category
            fields = ["name"]

        @classmethod
        @override
        def apply_sync(
            cls,
            input_value: object,
            queryset: QuerySet[_M],
            info: object,
        ):
            # Publishes the normalization record, then returns a candidate the
            # seal rejects.
            super().apply_sync(input_value, queryset, info)
            evaluated = Category.objects.all()
            evaluated._result_cache = []
            return evaluated

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            orderset_class = EvaluatedReturningOrder

    @strawberry.type
    class Query:
        cats: list[CategoryType] = DjangoListField(CategoryType)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    context: dict[str, object] = {"request": RequestFactory().get("/")}
    result = schema.execute_sync(
        "{ cats(orderBy: [{name: ASC}]) { id name } }",
        context_value=context,
    )
    assert result.errors is not None
    assert "got evaluated defect" in str(result.errors[0])
    assert set(context) == {"request"}
    assert _ORDER_NORMALIZATION_CAPTURE.get() is None


async def test_list_field_rejected_async_iterator_is_closed_when_building_the_rejection_fails():
    """A failure while CONSTRUCTING the rejection still closes the async-only source.

    Once the record says the source must be rejected, the close is owed on every
    exit: the primary error becomes whatever the error builder raised, and the
    cleanup utility attaches its notes to that instead.
    """
    from django_strawberry_framework.list_field import _handle_non_queryset_rejections_async

    class InstrumentedAsyncSource:
        def __init__(self, fail_close: bool = False):
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

    def _broken_definition_lookup(name: str):
        raise RuntimeError("simulated definition lookup failure")

    info = SimpleNamespace(
        context={},
        schema=None,
        get_argument_definition=_broken_definition_lookup,
    )
    args_record = _ListArguments(
        offset=None,
        limit=None,
        order_by=[{"name": "ASC"}],
        order_by_supplied=True,
        any_argument_supplied=True,
    )

    src_clean = InstrumentedAsyncSource()
    with pytest.raises(
        ConfigurationError,
        match="Failed to read the definition for argument 'order_by'",
    ):
        await _handle_non_queryset_rejections_async(
            src_clean,
            args_record,
            _as_strawberry_info(info),
        )
    assert src_clean.anext_calls == 0
    assert src_clean.aclose_calls == 1

    src_fail = InstrumentedAsyncSource(fail_close=True)
    with pytest.raises(ConfigurationError) as exc_fail:
        await _handle_non_queryset_rejections_async(
            src_fail,
            args_record,
            _as_strawberry_info(info),
        )
    assert src_fail.anext_calls == 0
    assert src_fail.aclose_calls == 1
    notes = getattr(exc_fail.value, "__notes__", [])
    assert any("DjangoListField iterator cleanup failed" in str(n) for n in notes)

    # A source that is not async-only owes no close on the same exit.
    with pytest.raises(ConfigurationError):
        await _handle_non_queryset_rejections_async([1, 2], args_record, _as_strawberry_info(info))


# =============================================================================
# The registry is the one canonical metadata source every factory reads
# =============================================================================


@contextlib.contextmanager
def _swap_definition_attribute(
    target_type: type[DjangoType],
    replacement: object,
) -> Generator[None, None, None]:
    """Put ``replacement`` on ``target_type``'s definition attribute, restoring after."""
    original = target_type.__dict__["__django_strawberry_definition__"]
    # basedpyright: the planted stand-in definition is the hostile input under test; DjangoType
    # types the slot as DjangoTypeDefinition
    target_type.__django_strawberry_definition__ = replacement  # pyright: ignore[reportAttributeAccessIssue]
    try:
        yield
    finally:
        target_type.__django_strawberry_definition__ = original


def test_djangolistfield_rejects_a_fabricated_same_origin_definition() -> None:
    """An object that merely LOOKS like the target's definition is not accepted.

    ``origin is target_type`` proves only that whatever answered the read
    names this class. Anything can name it. The accepted object must be the
    exact ``DjangoTypeDefinition`` the registry holds for the target, so a
    hand-built stand-in carrying a model of its own is rejected at the line
    that constructed the field - not later, as a Strawberry runtime-type error
    over a GraphQL type and a Django model that have nothing to do with
    each other.

    Package-side with its two siblings below: a field whose construction
    raises never reaches a schema, so no request can express the claim. The
    accepted path is what the live tier covers, over every shipped list and
    connection field.
    """

    class FabricatedTargetType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    fabricated = SimpleNamespace(
        origin=FabricatedTargetType,
        model=Item,
        orderset_class=None,
        filterset_class=None,
        interfaces=(),
    )
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField target FabricatedTargetType is not a registered DjangoType",
    ):
        with _swap_definition_attribute(FabricatedTargetType, fabricated):
            DjangoListField(FabricatedTargetType)


def test_djangolistfield_rejects_a_copy_of_the_real_definition() -> None:
    """A faithful COPY of the registered definition is rejected too.

    Equality is not the test; identity is. A copy is a second object that can
    be mutated independently of the one the registry, the finalizer and the
    optimizer all read, which is exactly the divergence the one-definition rule
    exists to prevent - and it would pass any check weaker than ``is``.
    """

    class CopiedTargetType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    real = CopiedTargetType.__django_strawberry_definition__
    duplicate = copy.copy(real)
    assert duplicate is not real
    assert duplicate.origin is CopiedTargetType
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField target CopiedTargetType is not a registered DjangoType",
    ):
        with _swap_definition_attribute(CopiedTargetType, duplicate):
            DjangoListField(CopiedTargetType)


def test_djangolistfield_rejects_a_target_the_registry_has_never_seen() -> None:
    """A target the registry does not hold is unregistered, and says so.

    The error text promises a REGISTERED target, and registration is a fact
    about the registry rather than about a class attribute that survives
    ``unregister``. Construction is the point at which the consumer can still
    do something about it, so that is where the rejection lands. Package-side
    because a target with no registration reaches no schema and therefore no
    request.
    """

    class DroppedTargetType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    registry.unregister(DroppedTargetType)
    assert registry.get_definition(DroppedTargetType) is None
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoListField target DroppedTargetType is not a registered DjangoType",
    ):
        DjangoListField(DroppedTargetType)


def test_djangolistfield_accepts_and_captures_the_registrys_exact_object() -> None:
    """The accepted definition IS the registry's object, not an equal one."""

    class CanonicalTargetType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    definition = _validate_djangotype_target(
        CanonicalTargetType,
        None,
        field="DjangoListField",
    )
    assert definition is registry.get_definition(CanonicalTargetType)
    assert definition is CanonicalTargetType.__django_strawberry_definition__


# ---------------------------------------------------------------------------
# Executor mode versus the ambient event loop


def _execution_mode_schema() -> DjangoSchema:
    """One schema carrying both list-field flavors over the same rows.

    Both reach a queryset representation, by different call sites: the default
    resolver picks its pipeline, and the synchronous consumer wrapper picks the
    final representation of what the consumer returned. They are the two places
    the executor was read, so they are the two the matrix repeats over.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    def _sync_consumer(root: object, info: Info) -> QuerySet[Category]:
        """A plain ``def`` returning a queryset, which is the committed sync wrapper."""
        return Category.objects.all()

    @strawberry.type
    class Query:
        default_rows: list[CategoryType] = DjangoListField(CategoryType)
        consumer_rows: list[CategoryType] = DjangoListField(
            CategoryType,
            resolver=_sync_consumer,
        )

    finalize_django_types()
    # Masking off, because the subject of these rows is the typed error itself.
    # Under the default policy every unexpected exception reaches the wire as one
    # stable string with ``original_error`` stripped, so a row asserting the
    # misuse would be asserting the mask instead.
    return DjangoSchema(query=Query, error_policy=ErrorPolicy(enabled=False))


_EXECUTION_MODE_FIELDS = ["defaultRows", "consumerRows"]
_EXECUTION_MODE_FIELD_IDS = ["default-resolver", "sync-consumer-resolver"]


@pytest.mark.django_db
@pytest.mark.parametrize("field", _EXECUTION_MODE_FIELDS, ids=_EXECUTION_MODE_FIELD_IDS)
def test_a_list_field_completes_synchronously_outside_an_event_loop(field: str) -> None:
    """The ordinary synchronous state: no loop, the synchronous executor, real rows."""
    services.seed_data(1)
    schema = _execution_mode_schema()

    result = schema.execute_sync(f"{{ {field} {{ name }} }}")

    assert result.errors is None, result.errors
    assert result.data is not None
    assert len(result.data[field]) == Category.objects.count()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("field", _EXECUTION_MODE_FIELDS, ids=_EXECUTION_MODE_FIELD_IDS)
async def test_a_list_field_completes_asynchronously_inside_an_event_loop(field: str) -> None:
    """The ordinary asynchronous state: a loop, the async executor, real rows."""
    await sync_to_async(services.seed_data)(1)
    schema = await sync_to_async(_execution_mode_schema)()

    result = await schema.execute(f"{{ {field} {{ name }} }}")

    assert result.errors is None, result.errors
    assert result.data is not None
    assert len(result.data[field]) == await Category.objects.acount()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("field", _EXECUTION_MODE_FIELDS, ids=_EXECUTION_MODE_FIELD_IDS)
async def test_a_list_field_refuses_a_synchronous_operation_inside_an_event_loop(
    field: str,
) -> None:
    """The third state, which is a misuse rather than a branch.

    ``execute_sync`` under a running loop holds the operation with the
    synchronous executor while the ambient loop says otherwise. A field that
    read the loop there built the async pipeline's coroutine, handed it to the
    executor that cancels top-level awaitables, and answered with Strawberry's
    generic "failed to complete synchronously" while the inner coroutines went
    unawaited. The field now refuses at the call that caused it, with the two
    recourses that actually work.

    Both halves are asserted: the public contract, and that nothing awaitable
    was constructed to be abandoned. A control query proves the failure belongs
    to list-field dispatch rather than to ``execute_sync`` being called under a
    loop at all.
    """
    await sync_to_async(services.seed_data)(1)
    schema = await sync_to_async(_execution_mode_schema)()

    assert schema.execute_sync("{ __typename }").data == {"__typename": "Query"}

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = schema.execute_sync(f"{{ {field} {{ name }} }}")
        gc.collect()

    assert result.data is None
    assert result.errors is not None
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert "await schema.execute" in str(result.errors[0])
    assert [str(warning.message) for warning in caught] == []
