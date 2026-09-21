"""``DjangoListField`` - non-Relay ``list[T]`` field for root Query fields.

Spec: ``docs/SPECS/spec-020-list_field-0_0_7.md``.
Extension spec: ``docs/spec-050-list_field_arguments-0_0_15.md``.
Target release: ``0.0.7``.
"""

from __future__ import annotations

import contextlib
import inspect
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import strawberry
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import (
    Case,
    Col,
    CombinedExpression,
    ExpressionWrapper,
    OrderBy,
    Star,
    When,
)
from django.db.models.fields.related_lookups import (
    RelatedExact,
    RelatedGreaterThan,
    RelatedGreaterThanOrEqual,
    RelatedIn,
    RelatedIsNull,
    RelatedLessThan,
    RelatedLessThanOrEqual,
)
from django.db.models.functions import (
    Cast,
    Coalesce,
    Concat,
    ConcatPair,
    ExtractDay,
    ExtractMonth,
    ExtractYear,
    Length,
    Lower,
    TruncDate,
    TruncMonth,
    TruncYear,
    Upper,
)
from django.db.models.lookups import (
    Exact,
    GreaterThan,
    GreaterThanOrEqual,
    In,
    IntegerFieldExact,
    IntegerGreaterThan,
    IntegerGreaterThanOrEqual,
    IntegerLessThan,
    IntegerLessThanOrEqual,
    IsNull,
    LessThan,
    LessThanOrEqual,
    Range,
)
from graphql import GraphQLError
from strawberry.schema.schema_converter import GraphQLCoreConverter
from strawberry.types import Info

from .exceptions import (
    ConfigurationError,
    DjangoStrawberryFrameworkError,
    _safe_arg_repr,
    _safe_class_name,
    describe_value,
)
from .registry import registry
from .resource_policy import (
    _cleanup_rejected_async_iterable,
    _windowed_rows,
    _windowed_rows_async,
    effective_bound,
    policy_from_info,
    validate_collection_bound,
    validate_trusted_flag,
)
from .types import DjangoType
from .types.base import _is_relay_shaped
from .utils.directives import validated_field_directives
from .utils.execution_mode import async_execution, operation_is_async
from .utils.querysets import (
    _LIST_ARGUMENT_VISIBILITY_POLICY,
    apply_orderset_async,
    apply_orderset_sync,
    apply_type_visibility_async,
    apply_type_visibility_sync,
    base_queryset,
    is_async_only_iterable,
    prepared_resolver_source,
    reject_async_iterable_in_sync_context,
    reject_awaitable_sync_source,
    reject_residual_async_source,
    wrap_async_queryset_adapter,
)
from .utils.typing import is_async_callable

if TYPE_CHECKING:  # pragma: no cover - type-checking-only import.
    from .types.definition import DjangoTypeDefinition

__all__ = ("DjangoListField", "ListArgumentError")

_KNOWN_LIST_ARGUMENT_REASONS: frozenset[str] = frozenset(
    {
        "negative",
        "non_integer",
        "order_required",
        "over_ceiling",
        "queryset_required",
    },
)


def _validate_djangotype_target(
    target_type: type,
    resolver: Callable | None,
    *,
    field: str,
) -> DjangoTypeDefinition:
    """Run the shared DjangoType-target constructor guards for a field factory.

    Shared by ``DjangoListField`` and ``DjangoConnectionField`` (and any future
    node field). ``field`` is the factory's public name
    (e.g. ``"DjangoListField"``) interpolated into the ``ConfigurationError``
    messages so each factory's errors name itself. These constructor-site
    checks fail at the line that wrote ``<field>(...)`` rather than at
    finalize-time.

    Order is load-bearing - each target-type check assumes the previous one
    passed. The registration check is the strict invariant:
    ``__django_strawberry_definition__`` is assigned by
    ``DjangoType.__init_subclass__`` (``types/base.py::DjangoType.__init_subclass__``)
    only for concrete subclasses carrying their own ``Meta`` with a ``model``.
    The attribute is inherited via MRO, so ``hasattr`` would accept a subclass
    that omits its own ``Meta`` - binding the field to a target whose
    definition, ``Meta.primary`` state, and model belong to the parent.

    The attribute answer is not trusted on its own word. ``origin is
    target_type`` is only the own-class half; the accepted object must ALSO be
    the exact ``DjangoTypeDefinition`` the registry holds for ``target_type``,
    compared by IDENTITY. ``__init_subclass__`` registers the definition and
    assigns the attribute from one value, so the canonical answer and the
    attribute answer agree for every real target - while a fabricated
    same-origin lookalike, a copy of a real definition, and a definition for a
    type the registry has never seen are all rejected here, at the line that
    constructed the field, instead of surfacing later as a Strawberry
    runtime-type error over an unrelated model. The registry is the one
    canonical metadata source every factory reads, so "registered target"
    cannot mean different things to the list, connection and Relay node
    entry points.

    Every deployment-supplied value in a rejection message renders through the
    guarded helpers (``exceptions.py``): the non-class arm renders
    ``_safe_arg_repr`` (the ``_validate_mutation_target`` parity spelling) and
    the class arms render ``_safe_class_name``, so a hostile ``__repr__`` or a
    metaclass ``__name__`` property that raises cannot detonate the message
    assembly and replace the typed rejection with a raw ``RuntimeError``.

    The definition read is contained: ``getattr``'s default suppresses only
    ``AttributeError``, so a metaclass ``__getattr__`` raising anything else
    would escape raw and the typed "not a registered DjangoType" rejection
    would never exist. A read that cannot be answered is a target that cannot
    be PROVEN registered, so the failure is the same typed reject (fail
    closed, matching ``forms/inputs.py::_model_column_for``'s posture).

    Raises ``ConfigurationError`` on failure; returns the canonical
    ``DjangoTypeDefinition`` when every guard passes, so the Relay validator
    consumes the SAME contained read instead of re-reading the attribute
    directly (a stateful metaclass could answer the first guarded read and
    detonate a second raw one). The caller runs any factory-specific guards
    (e.g. the connection field's Relay-Node guard) AFTER this returns.
    """
    if not inspect.isclass(target_type):
        raise ConfigurationError(
            f"{field} requires a DjangoType class; got {_safe_arg_repr(target_type)}.",
        )
    if not issubclass(target_type, DjangoType):
        raise ConfigurationError(
            f"{field} requires a DjangoType subclass; got {_safe_class_name(target_type)}.",
        )
    try:
        definition = getattr(target_type, "__django_strawberry_definition__", None)
    except Exception:
        # Contained: a metaclass whose __getattr__ raises anything other than
        # AttributeError must reach the typed rejection below, not escape raw.
        definition = None
    canonical = registry.get_definition(target_type)
    if (
        definition is None
        or getattr(definition, "origin", None) is not target_type
        or definition is not canonical
    ):
        raise ConfigurationError(
            f"{field} target {_safe_class_name(target_type)} is not a registered DjangoType. "
            f"This usually means {_safe_class_name(target_type)}'s `Meta` is missing a `model` "
            "declaration, or it inherits a definition from a parent without declaring its own `Meta`.",
        )
    if resolver is not None and not callable(resolver):
        raise ConfigurationError(f"{field} resolver must be callable.")
    return definition


def _validate_relay_djangotype_target(
    target_type: type,
    resolver: Callable | None,
    *,
    field: str,
    relay_error_message: str,
) -> DjangoTypeDefinition:
    """Run the shared DjangoType-target guards plus the Relay-Node-shaped one.

    The Relay-shaped target guard shared by ``DjangoConnectionField`` and
    ``relay.py::_validate_node_target`` (which backs ``DjangoNodeField`` /
    ``DjangoNodesField``) -- single-sited. Delegates the base checks -
    including the registry-canonicality identity check - to
    ``_validate_djangotype_target`` (with the call site's
    ``resolver`` seam), then rejects a non-Relay-Node-shaped target.
    ``_is_relay_shaped`` reads the declared ``Meta.interfaces`` (a
    Meta-declared ``relay.Node`` is in ``definition.interfaces`` before Phase
    2.5 injects it into ``__bases__``) OR direct ``relay.Node`` inheritance.
    The caller supplies the full ``relay_error_message`` so each factory keeps
    its own wording, and the same single definition read is returned onward so a
    factory can build its whole field from it without a second read.
    """
    # The definition comes back from the base validator's ONE contained read;
    # re-reading the attribute directly here would let a stateful metaclass
    # answer the first (guarded, defaulted) read and detonate the second.
    definition = _validate_djangotype_target(target_type, resolver, field=field)
    if not _is_relay_shaped(target_type, definition.interfaces):
        raise ConfigurationError(relay_error_message)
    return definition


class ListArgumentError(GraphQLError, DjangoStrawberryFrameworkError):
    """An argument to ``DjangoListField`` was invalid or violated policy bounds.

    Dual-inherits ``GraphQLError`` (so Strawberry/GraphQL transport serializes it
    as an execution error with structured extensions) and
    ``DjangoStrawberryFrameworkError`` (so consumers can catch it alongside any
    other framework error).

    Every numeric value interpolated into the wording renders through
    ``_safe_arg_repr``. For the ordinary ``int`` the boundary admits that is
    byte-identical to the value itself; what it closes is the direct call
    carrying an integer with more digits than CPython will convert to a string,
    which would raise ``ValueError`` from the f-string assembled at the raise
    site and replace this typed rejection with an unrelated exception.
    """

    def __init__(
        self,
        field: str,
        argument: str,
        reason: str,
        value: Any = None,
        ceiling: int | None = None,
        order_argument: str | None = None,
    ) -> None:
        if reason not in _KNOWN_LIST_ARGUMENT_REASONS:
            raise ValueError(f"Unknown ListArgumentError reason {reason!r}.")
        self.field = field
        self.argument = argument
        self.reason = reason
        self.ceiling = ceiling
        self.order_argument = order_argument

        if reason == "non_integer":
            self.value = value if isinstance(value, str) else describe_value(value)
            msg = (
                f"Invalid argument {argument!r} on {field}: expected a non-negative "
                f"integer, got {self.value}."
            )
        elif reason == "negative":
            self.value = value
            msg = (
                f"Invalid argument {argument!r} on {field}: expected a non-negative "
                f"integer, got {_safe_arg_repr(value)}."
            )
        elif reason == "over_ceiling":
            self.value = value
            msg = (
                f"Invalid argument {argument!r} on {field}: value {_safe_arg_repr(value)} "
                f"exceeds the maximum allowed ceiling of {ceiling}."
            )
        elif reason == "order_required":
            self.value = value
            if order_argument:
                ordering_phrase = f"via {order_argument!r} or model 'Meta.ordering'"
            else:
                ordering_phrase = "via model 'Meta.ordering'"
            msg = (
                f"Invalid argument {argument!r} on {field}: non-zero offset "
                f"({_safe_arg_repr(value)}) requires an active ordering {ordering_phrase}."
            )
        elif reason == "queryset_required":
            self.value = value
            msg = (
                f"Invalid argument {argument!r} on {field}: an ordering argument "
                "requires a QuerySet source."
            )
        extensions: dict[str, Any] = {
            "code": "LIST_ARGUMENT_INVALID",
            "argument": argument,
            "reason": reason,
        }
        if self.value is not None:
            extensions["value"] = self.value
        if ceiling is not None:
            extensions["ceiling"] = ceiling

        super().__init__(msg, extensions=extensions)

    def __reduce__(self) -> tuple[object, ...]:
        """Preserve constructor arguments and instance state across pickle roundtrips."""
        return (
            self.__class__,
            (
                self.field,
                self.argument,
                self.reason,
                self.value,
                self.ceiling,
                self.order_argument,
            ),
            self.__dict__,
        )


_DEFAULT_WIRE_NAMES: dict[str, str] = {"offset": "offset", "limit": "limit", "order_by": "orderBy"}


def _published_wire_name(info: Any, arg_def: Any, parameter_name: str) -> str | None:
    """Read the wire name the executable schema PUBLISHED for ``arg_def``.

    Strawberry fixes every argument's GraphQL name once, while it builds the
    schema: ``GraphQLCoreConverter.from_field`` keys the ``GraphQLField.args``
    map by the converter's answer and ``from_argument`` stores the
    ``StrawberryArgument`` under ``DEFINITION_BACKREF`` in each entry's
    ``extensions``. That map is the only name a client could have sent, so the
    error path reads it back instead of running the schema's shared
    ``NameConverter`` a second time at request time - a converter is consumer
    code, may be stateful, and is not the framework's to invoke concurrently.
    Returns ``None`` when ``info`` carries no executable-schema metadata (a
    direct-call stub), so the caller can fall back to the default spelling.
    """
    try:
        raw_info = info._raw_info
        parent_type = raw_info.parent_type
        field_name = raw_info.field_name
    except AttributeError:
        return None
    except Exception as exc:
        raise ConfigurationError(
            f"Failed to read the schema field for argument {parameter_name!r}: {exc}",
        ) from exc
    try:
        published_args = parent_type.fields[field_name].args
        for wire_name, graphql_argument in published_args.items():
            extensions = graphql_argument.extensions or {}
            if extensions.get(GraphQLCoreConverter.DEFINITION_BACKREF) is arg_def:
                return wire_name
    except Exception as exc:
        raise ConfigurationError(
            f"Failed to read the published arguments for {parameter_name!r} on "
            f"{_field_label(info)}: {exc}",
        ) from exc
    raise ConfigurationError(
        f"Argument {parameter_name!r} on {_field_label(info)} has a definition but no "
        "published wire name in the executable schema.",
    )


def _resolve_argument_wire_name(info: Any, parameter_name: str) -> str:
    """Resolve the active GraphQL wire name for an internal parameter name.

    Only invoked on error paths (e.g. inside ``ListArgumentError`` instantiation or
    normalizer error branches) so successful requests perform zero name lookups.
    The name comes from the executable schema's published argument map
    (:func:`_published_wire_name`); the schema's ``NameConverter`` is never
    invoked at request time.
    """
    fallback = _DEFAULT_WIRE_NAMES.get(parameter_name, parameter_name)
    try:
        get_arg_def = info.get_argument_definition
    except AttributeError:
        return fallback
    except Exception as exc:
        raise ConfigurationError(
            f"Failed to read the argument-definition resolver for {parameter_name!r}: {exc}",
        ) from exc
    if get_arg_def is None:
        return fallback
    if not callable(get_arg_def):
        raise ConfigurationError(
            f"Failed to resolve wire name for argument {parameter_name!r}: "
            "info.get_argument_definition is not callable.",
        )

    try:
        arg_def = get_arg_def(parameter_name)
    except Exception as exc:
        raise ConfigurationError(
            f"Failed to read the definition for argument {parameter_name!r}: {exc}",
        ) from exc
    if arg_def is None:
        return fallback
    published = _published_wire_name(info, arg_def, parameter_name)
    return fallback if published is None else published


# ``slots=True`` is deliberately absent: combined with ``frozen=True`` the
# dataclass-generated ``__setattr__`` closes over the pre-slots class, so an
# undeclared attribute raises ``TypeError`` from ``super()`` instead of the
# ``FrozenInstanceError`` every other write path raises.
@dataclass(frozen=True)
class _ListArguments:
    offset: int | None
    limit: int | None
    order_by: Any
    order_by_supplied: bool
    any_argument_supplied: bool


def _normalize_list_arguments(
    field_name: str,
    info: Any,
    max_rows: int | None,
    trusted_max_rows: bool,
    *,
    offset: Any = None,
    limit: Any = None,
    order_by: Any = strawberry.UNSET,
) -> _ListArguments:
    """Normalize and validate pagination arguments against effective resource policy ceilings.

    ``offset`` and ``limit`` must each be an EXACT ``int``. GraphQL's own ``Int``
    coercion always supplies one, so the exactness costs a wire request nothing;
    what it closes is the direct call the spec also promises to keep typed. An
    ``int`` SUBCLASS would otherwise reach the range comparisons and the error
    rendering below, running its ``__lt__`` / ``__gt__`` / ``__format__`` inside
    the argument boundary and replacing the typed rejection with whatever that
    consumer hook raised. Everything that is not exactly an ``int`` -- ``bool``
    included, which is a subclass -- takes the ``non_integer`` arm and renders
    through ``describe_value``.

    Delegation guarantee:
        While offset and limit are validated here (integer type, non-negative, and limit
        within the effective ceiling), order_by structure and semantics are delegated to
        the target DjangoType's OrderSet (or to Strawberry's schema-level input validation
        when executed over GraphQL). Direct callers supplying non-null order_by to a target
        without an OrderSet are caught by
        ``django_strawberry_framework/utils/querysets.py::require_orderset_class``
        at pipeline execution time.
    """
    offset_supplied = offset is not None and offset is not strawberry.UNSET
    limit_supplied = limit is not None and limit is not strawberry.UNSET
    order_by_supplied = order_by is not None and order_by is not strawberry.UNSET
    any_argument_supplied = offset_supplied or limit_supplied or order_by_supplied

    norm_offset = None if not offset_supplied else offset
    norm_limit = None if not limit_supplied else limit
    norm_order_by = None if not order_by_supplied else order_by

    if not any_argument_supplied:
        return _ListArguments(
            offset=None,
            limit=None,
            order_by=None,
            order_by_supplied=False,
            any_argument_supplied=False,
        )

    policy = policy_from_info(info)
    offset_ceiling = policy.max_list_rows

    if norm_offset is not None:
        if type(norm_offset) is not int:
            raise ListArgumentError(
                field_name,
                _resolve_argument_wire_name(info, "offset"),
                reason="non_integer",
                value=describe_value(norm_offset),
            )
        if norm_offset < 0:
            raise ListArgumentError(
                field_name,
                _resolve_argument_wire_name(info, "offset"),
                reason="negative",
                value=norm_offset,
            )
        if norm_offset > offset_ceiling:
            raise ListArgumentError(
                field_name,
                _resolve_argument_wire_name(info, "offset"),
                reason="over_ceiling",
                value=norm_offset,
                ceiling=offset_ceiling,
            )

    if norm_limit is not None:
        effective_ceiling = effective_bound(
            policy.max_list_rows,
            max_rows,
            trusted=trusted_max_rows,
        )
        if type(norm_limit) is not int:
            raise ListArgumentError(
                field_name,
                _resolve_argument_wire_name(info, "limit"),
                reason="non_integer",
                value=describe_value(norm_limit),
            )
        if norm_limit < 0:
            raise ListArgumentError(
                field_name,
                _resolve_argument_wire_name(info, "limit"),
                reason="negative",
                value=norm_limit,
            )
        if norm_limit > effective_ceiling:
            raise ListArgumentError(
                field_name,
                _resolve_argument_wire_name(info, "limit"),
                reason="over_ceiling",
                value=norm_limit,
                ceiling=effective_ceiling,
            )

    return _ListArguments(
        offset=norm_offset,
        limit=norm_limit,
        order_by=norm_order_by,
        order_by_supplied=order_by_supplied,
        any_argument_supplied=any_argument_supplied,
    )


def _synthesized_list_signature(
    orderset_class: type | None,
) -> tuple[inspect.Signature, dict[str, Any]]:
    """Build the resolver ``__signature__`` and ``__annotations__`` for DjangoListField.

    Carries ``offset`` and ``limit`` arguments, plus conditional ``order_by`` when
    the field captured an ``OrderSet`` for its target. The return annotation is left empty
    (``inspect.Signature.empty``) and omitted from annotations so the outer class attribute
    annotation retains sole ownership of outer nullability (``list[T]`` vs ``list[T] | None``).

    ``orderset_class`` is the field's ONE selected class, read from the single
    definition the target validator returned; the SDL published here and the
    class the resolver dispatches through are therefore the same object by
    construction, and a stateful target metaclass has no second read to answer
    differently.
    """
    params: list[inspect.Parameter] = [
        inspect.Parameter("root", inspect.Parameter.POSITIONAL_OR_KEYWORD, default=None),
        inspect.Parameter("info", inspect.Parameter.KEYWORD_ONLY, annotation=Info),
        inspect.Parameter(
            "offset",
            inspect.Parameter.KEYWORD_ONLY,
            default=None,
            annotation=int | None,
        ),
        inspect.Parameter(
            "limit",
            inspect.Parameter.KEYWORD_ONLY,
            default=None,
            annotation=int | None,
        ),
    ]
    annotations: dict[str, Any] = {"info": Info, "offset": int | None, "limit": int | None}

    if orderset_class is not None:
        from .orders import order_input_type

        order_ann = list[order_input_type(orderset_class)] | None
        params.append(
            inspect.Parameter(
                "order_by",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=order_ann,
            ),
        )
        annotations["order_by"] = order_ann

    return inspect.Signature(params, return_annotation=inspect.Signature.empty), annotations


#: Which collection Django's compiler selects as the ordering it will emit.
_ORDER_FROM_EXTRA = "extra"
_ORDER_FROM_EXPLICIT = "explicit"
_ORDER_FROM_MODEL_DEFAULT = "model_default"
_ORDER_FROM_NOTHING = "nothing"

#: The expression leaves this package can read: a column, the ``*`` of a row count,
#: and a literal value. Matched by EXACT type, like every other approved form
#: below, because a subclass carries its own ``as_sql``.
_READABLE_ORDER_LEAVES = frozenset(
    {models.Value, Col, Star},
)

#: Expressions whose own SQL is punctuation around their sources - the branches of
#: a ``CASE``, an operator between two operands, a wrapper that only supplies an
#: output field, the direction marker on a term. A node listed here orders by
#: whatever its sources order by and by nothing else, so it is read through.
_TRANSPARENT_ORDER_EXPRESSIONS = frozenset(
    {
        Case,
        CombinedExpression,
        ExpressionWrapper,
        OrderBy,
        When,
    },
)

#: Database functions whose SQL is a deterministic function of their arguments:
#: the same arguments produce the same value on every execution, so such a node
#: is read through to its sources and adds no volatility of its own. Membership
#: is by EXACT type - a subclass overrides ``as_sql`` and emits whatever it
#: likes, so it is not this class and is not approved. Nothing is listed for
#: being harmless-looking: a function reaches this set only by being one of
#: Django's own and pure.
_APPROVED_ORDER_FUNCTIONS = frozenset(
    {
        Cast,
        Coalesce,
        Concat,
        ConcatPair,
        Length,
        Lower,
        Upper,
    },
)

#: Aggregates under the same rule, listed because the shipped surface emits them:
#: ``orders/sets.py::OrderSet._resolve_order_expressions`` annotates ``Min`` /
#: ``Max`` for a to-many ordering path, and a row count orders by ``Count``.
_APPROVED_ORDER_AGGREGATES = frozenset(
    {models.Count, models.Max, models.Min},
)

#: Transforms a predicate's left-hand side may apply before its lookup, under the
#: same purity rule and the same exact-type match.
_APPROVED_ORDER_TRANSFORMS = frozenset(
    {
        ExtractDay,
        ExtractMonth,
        ExtractYear,
        Length,
        Lower,
        TruncDate,
        TruncMonth,
        TruncYear,
        Upper,
    },
)

#: Lookups a predicate may compare with: Django's own comparison, membership and
#: null tests, each of which compiles to an operator over its two sides and
#: contributes no SQL a caller could steer. The integer- and relation-specific
#: spellings are listed beside the general ones because Django substitutes them
#: by field type for the same operators - an exact-type match sees the class the
#: field hands back, not the base it derives from.
_APPROVED_ORDER_LOOKUPS = frozenset(
    {
        Exact,
        GreaterThan,
        GreaterThanOrEqual,
        In,
        IntegerFieldExact,
        IntegerGreaterThan,
        IntegerGreaterThanOrEqual,
        IntegerLessThan,
        IntegerLessThanOrEqual,
        IsNull,
        LessThan,
        LessThanOrEqual,
        Range,
        RelatedExact,
        RelatedGreaterThan,
        RelatedGreaterThanOrEqual,
        RelatedIn,
        RelatedIsNull,
        RelatedLessThan,
        RelatedLessThanOrEqual,
    },
)

#: Every node read THROUGH to its sources. A term whose type is absent from this
#: union and from ``_READABLE_ORDER_LEAVES`` is refused, whatever it holds.
_APPROVED_ORDER_NODES = (
    _TRANSPARENT_ORDER_EXPRESSIONS | _APPROVED_ORDER_FUNCTIONS | _APPROVED_ORDER_AGGREGATES
)

#: The container shapes a predicate's right-hand side arrives in: ``__in`` takes a
#: sequence and ``__range`` a pair, and each member is compiled into the statement.
_ORDER_VALUE_CONTAINERS = (
    list,
    tuple,
    set,
    frozenset,
)


def _resolve_order_field_path(opts: Any, path: str) -> tuple[Any, Any] | None:
    """Walk a field path against ``opts``, returning ``(field, related opts)`` or None.

    ``django/db/models/sql/compiler.py::SQLCompiler.find_ordering_name`` hands
    the ``LOOKUP_SEP``-joined pieces to ``_setup_joins``, which resolves each one
    as a field on the model reached so far - ``pk`` naming the primary key and a
    reverse relation naming its own model the same way a forward one does. A
    piece that is not a field of the model in hand is a transform or a lookup,
    which this package does not read: None says the path could not be resolved
    to a field, and an unresolved path is never certified.
    """
    field = None
    for piece in path.split(LOOKUP_SEP):
        if opts is None:
            return None
        name = opts.pk.name if piece == "pk" else piece
        try:
            field = opts.get_field(name)
        except FieldDoesNotExist:
            return None
        related = field.related_model if field.is_relation else None
        opts = related._meta if related is not None else None
    return field, opts


def _is_deterministic_order_field_path(
    query: Any,
    path: str,
    opts: Any,
    seen: frozenset[tuple[Any, str]],
    prefix: str,
) -> bool:
    """Classify a resolved field path, expanding a relation the way the compiler does.

    ``django/db/models/sql/compiler.py::SQLCompiler.find_ordering_name`` does not
    order by a relation: when the path ends on a relation whose target model has
    its own ``Meta.ordering``, and the last piece is neither the field's
    ``attname`` nor ``pk``, the compiler REPLACES the term with that model's
    ordering and keeps recursing. So the order the rows come back in is the
    related model's, and it is that ordering - not the relation name standing in
    front of it - that decides whether the request is repeatable.

    A path Django would reject with ``FieldError("Infinite loop caused by
    ordering.")`` is refused rather than followed: a term whose compilation
    raises is not one this package can certify.

    ``prefix`` is the name the expanded terms hang under. The compiler rewrites
    an expression it lifts out of a related ordering through
    ``prefix_references``, so a reference written against the related model
    arrives at the outer query under the relation path that reached it, and a
    classifier reading references must name them the same way.
    """
    resolved = _resolve_order_field_path(opts, path)
    if resolved is None:
        return False
    field, related_opts = resolved
    if (
        not field.is_relation
        or related_opts is None
        or not related_opts.ordering
        or getattr(field, "attname", None) == path.split(LOOKUP_SEP)[-1]
        or path == "pk"
    ):
        return True
    step = (opts.model, path)
    if step in seen:
        return False
    nested = seen | {step}
    nested_prefix = f"{prefix}{path}{LOOKUP_SEP}"
    return all(
        _is_deterministic_order_term(query, item, related_opts, nested, nested_prefix)
        for item in related_opts.ordering
    )


def _is_deterministic_order_reference(query: Any, name: str, prefix: str) -> bool:
    """Classify the name an expression reference holds, which is always a column order.

    An ``F`` is not a string ordering term and never reaches
    ``django/db/models/sql/compiler.py::SQLCompiler.find_ordering_name``.
    ``django/db/models/sql/query.py::Query.resolve_ref`` reads it instead: the
    whole name as an annotation, then the head of a transform chain, and
    otherwise a field path against the QUERY's own meta - which yields a column
    and never a related model's ``Meta.ordering``. So ``F("branch")`` orders by
    the foreign key column exactly as ``"branch_id"`` does, whatever the branch
    model declares.

    ``prefix`` carries the relation path an expansion lifted this reference out
    of, because ``find_ordering_name`` rewrites such an expression through
    ``prefix_references`` before the outer query resolves it. The annotation and
    ``extra`` steps are read at that same full name, so a reference naming
    unreadable SQL is refused at any depth. There is no dotted ``extra_order_by``
    arm to match the one a string name gets: an ``extra`` ordering is the
    collection the compiler selects outright, so an expression is only ever
    classified while that collection is empty.
    """
    referenced = f"{prefix}{name}"
    annotation = query.annotations.get(referenced)
    if annotation is None:
        annotation = query.annotations.get(referenced.split(LOOKUP_SEP)[0])
    if annotation is not None:
        return _is_deterministic_order_term(query, annotation)
    if referenced in query.extra:
        return False
    return _resolve_order_field_path(query.get_meta(), referenced) is not None


def _is_deterministic_order_name(
    query: Any,
    name: str,
    opts: Any = None,
    seen: frozenset[tuple[Any, str]] = frozenset(),
    prefix: str = "",
) -> bool:
    """Resolve a string ordering term the way the compiler resolves it, then classify it.

    ``django/db/models/sql/compiler.py::SQLCompiler._order_by_pairs`` tests
    ``field == "?"`` exactly, so a descending spelling such as ``"-?"`` is not a
    random order at all - Django resolves it as a column named ``?`` and raises
    ``FieldError``. Every other name is looked up as an annotation (the whole
    name first, then the head of a transform chain), then as an ``extra`` key,
    and only then as a field path, so the name that survives to the field path
    is the only one that could order by a column.

    Raw SQL reached through ``extra`` is opaque, which is not the same as
    deterministic. Those strings are passed through verbatim and this package
    parses no SQL, so it cannot say what such a term orders by - and a term it
    cannot read is one it must not certify as repeatable across the two queries
    an offset window spans.

    Surviving to a field path is still not the end of the resolution:
    ``django/db/models/sql/compiler.py::SQLCompiler.find_ordering_name`` expands
    a path ending on a relation into the related model's own ``Meta.ordering``,
    so a random default one indirection away is what such a name really orders
    by. ``opts`` names the model a path is resolved against, which is the related
    model while such an expansion is being read - and at that depth there are no
    annotations and no ``extra`` to consult, because the compiler resolves those
    terms against the related model's fields alone.
    """
    if name == "?":
        return False
    col = name[1:] if name.startswith("-") else name
    if opts is None:
        annotation = query.annotations.get(col)
        if annotation is None:
            annotation = query.annotations.get(col.split(LOOKUP_SEP)[0])
        if annotation is not None:
            return _is_deterministic_order_term(query, annotation)
        if col in query.extra:
            return False
        if "." in name and name in query.extra_order_by:
            return False
        opts = query.get_meta()
    return _is_deterministic_order_field_path(query, col, opts, seen, prefix)


def _is_deterministic_order_term(
    query: Any,
    term: Any,
    opts: Any = None,
    seen: frozenset[tuple[Any, str]] = frozenset(),
    prefix: str = "",
) -> bool:
    """Classify one selected ordering term by the form Django will compile it into.

    A term's own top level is not what the database orders by. A string is
    resolved through ``query.annotations`` and ``query.extra`` before it is read
    as a field path, and an expression is compiled from its whole source tree,
    so what the rows are ordered by sits one indirection away from the value the
    ordering collection holds whenever it arrives as an annotation alias, an
    ``extra`` select alias, an ``F`` naming either, or an expression nested
    inside a composition.

    A STRING term that resolves to a relation is one more such indirection:
    ``django/db/models/sql/compiler.py::SQLCompiler.find_ordering_name``
    replaces it with the related model's ``Meta.ordering``, and every term of
    that ordering is classified against THAT model - which is what ``opts``
    carries, together with ``seen`` so a relation cycle Django would reject is
    refused instead of followed, and ``prefix`` so a reference lifted out of the
    expansion is named the way the outer query will resolve it. An EXPRESSION
    reference is not that indirection and must not be read as one: only strings
    reach ``find_ordering_name``, while
    ``django/db/models/sql/query.py::Query.resolve_ref`` resolves an ``F`` to a
    column, so ``F("branch")`` orders by the foreign key and never by the branch
    model's own default.

    Certification is positive and the boundary is an explicit list of APPROVED
    FORMS. Having source expressions is not a promise about a node's own SQL:
    ``Func``, ``Transform``, ``Aggregate`` and ``Window`` each emit SQL of their
    own around their sources, and any of them can be subclassed with an
    ``as_sql`` that emits anything at all - so "it has readable children" would
    certify a one-class project expression spelling ``RANDOM()`` over a column.
    A node is therefore read through only when it is one of the forms this
    package names: a transparent composition
    (``_TRANSPARENT_ORDER_EXPRESSIONS``), a pure database function
    (``_APPROVED_ORDER_FUNCTIONS``), one of the aggregates the shipped surface
    emits (``_APPROVED_ORDER_AGGREGATES``), an ``F`` reference, or a ``Q``
    predicate. Each of those is then certified only if every source expression
    it holds is, so an approved wrapper launders nothing:
    ``Coalesce(Random(), Random())`` is refused through its children. A readable
    leaf (``_READABLE_ORDER_LEAVES``) carries all of its own SQL and is named
    outright: a column reference, the ``*`` of a row count, and a literal value.

    Every match is by EXACT type, the two reference forms included. A subclass
    of an approved class is a different ``as_sql`` and is refused, which is the
    whole difference between naming a form and recognizing a family; a subclass
    of ``F`` or of ``Q`` is a different ``resolve_expression``, which is the
    same difference one step earlier - the name or the predicate this package
    reads is not what the subclass hands the compiler, so only ``F`` and ``Q``
    themselves enter the reference and the predicate arms.

    Which arm a term takes is decided the way
    ``django/db/models/sql/compiler.py::SQLCompiler._order_by_pairs`` decides
    it: a term carrying ``resolve_expression`` is an expression and is read as
    one, and only a term without it is read as a string name. A ``str`` subclass
    that carries that method is therefore classified as the expression Django
    will resolve it to rather than as the field path it spells. Everything
    unlisted is refused too -
    ``Random()``, a bare or custom ``Func``, a ``Transform``, an unlisted
    ``Aggregate``, a ``Window``, a ``RawSQL`` fragment, the inner ``Query`` a
    ``Subquery`` wraps - because a term this package cannot read is one it must
    not certify as repeatable across the two queries an offset window spans.
    """
    if hasattr(term, "resolve_expression"):
        node = type(term)
        if node is models.F:
            return _is_deterministic_order_reference(query, term.name, prefix)
        if node is models.Q:
            return _is_deterministic_order_condition(query, term, opts, seen, prefix)
        if node in _READABLE_ORDER_LEAVES:
            return True
        if node not in _APPROVED_ORDER_NODES:
            return False
        return all(
            _is_deterministic_order_term(query, source, opts, seen, prefix)
            for source in term.get_source_expressions()
            if source is not None
        )
    if isinstance(term, str):
        return _is_deterministic_order_name(query, term, opts, seen, prefix)
    return False


def _is_deterministic_order_value(
    query: Any,
    value: Any,
    opts: Any = None,
    seen: frozenset[tuple[Any, str]] = frozenset(),
    prefix: str = "",
) -> bool:
    """Classify one value a predicate's lookup compares its column against.

    A value carries SQL of its own either as an expression or inside a container
    of them, because a lookup taking a sequence compiles every member into the
    statement the same way it compiles a value given alone. Reading only the top
    level would certify a fragment written one bracket deeper - ``name__in`` is
    a list, ``created__range`` a pair - as an ordinary comparison against
    literals. A value that is neither an expression nor such a container is a
    plain literal, which is already as readable as a term gets.
    """
    if hasattr(value, "resolve_expression"):
        return _is_deterministic_order_term(query, value, opts, seen, prefix)
    if isinstance(value, _ORDER_VALUE_CONTAINERS):
        return all(
            _is_deterministic_order_value(query, member, opts, seen, prefix) for member in value
        )
    return True


def _approved_order_transform(lhs: Any, name: str) -> Any:
    """Apply one approved transform to ``lhs``, or return None when it is not one.

    Mirrors ``django/db/models/sql/query.py::Query.try_transform``: the name is
    looked up on the left-hand side's output field and applied to it, so the
    next piece is read against what this one produces. A name the field does not
    register is no transform at all, and a transform outside
    ``_APPROVED_ORDER_TRANSFORMS`` - a project's own, registered on a built-in
    field, emitting whatever its ``as_sql`` says - is refused for the same reason
    an unapproved function is.
    """
    transform = lhs.output_field.get_transform(name)
    if transform is None or transform not in _APPROVED_ORDER_TRANSFORMS:
        return None
    return transform(lhs)


def _is_deterministic_order_lookup_chain(field: Any, pieces: Sequence[str]) -> bool:
    """Classify the transforms and the final lookup a predicate applies to a reference.

    ``django/db/models/sql/query.py::Query.build_lookup`` reads every piece but
    the last as a transform, then tries the last as a lookup and falls back to
    reading it as a transform under an implicit ``exact``. Both are SQL: a
    transform wraps the reference in a function call and the lookup is the
    operator around the comparison, so a predicate's left-hand side is only as
    readable as the chain applied to it. ``code__jitter__gt`` is a column under a
    project transform, and the statement orders by whatever that transform
    emits.

    Each piece is therefore matched by EXACT type against the approved transform
    and lookup sets, and anything unresolvable or unlisted is refused. A
    reference with no trailing pieces is compared with Django's implicit
    ``exact``, which is approved, so an ordinary equality predicate needs no
    spelling of its own.
    """
    lhs = models.Value(None, output_field=field)
    *transforms, final = tuple(pieces) or ("exact",)
    for name in transforms:
        lhs = _approved_order_transform(lhs, name)
        if lhs is None:
            return False
    lookup = lhs.output_field.get_lookup(final)
    if lookup is not None:
        return lookup in _APPROVED_ORDER_LOOKUPS
    lhs = _approved_order_transform(lhs, final)
    if lhs is None:
        return False
    return lhs.output_field.get_lookup("exact") in _APPROVED_ORDER_LOOKUPS


def _is_deterministic_order_predicate_reference(
    query: Any,
    lookup: str,
    opts: Any,
    prefix: str,
) -> bool:
    """Classify the left-hand side of one ``(lookup, value)`` predicate child.

    A lookup string is a reference followed by lookups and transforms, and
    ``django/db/models/sql/query.py::Query.solve_lookup_type`` separates the two
    the way a ``When`` condition is built: it asks
    ``django/db/models/query_utils.py::refs_expression`` for the SHORTEST leading
    run of pieces naming an annotation, and otherwise hands the whole string to
    ``names_to_path``, which consumes as many leading pieces as resolve to fields
    and leaves the rest as the lookup. So ``coin__gt`` is the annotation ``coin``
    under a ``gt``, and ``code__gt`` is a column under the same one.

    An annotation is classified like any other term, which is what refuses a
    predicate comparing a random alias while accepting one comparing a column
    alias. A field path is a column order and is NOT expanded into its related
    model's ``Meta.ordering``: a reference is not a string ordering term, and
    only the latter reaches the compiler's expansion. A head that names neither
    is a reference this package cannot read, so the predicate is refused rather
    than certified. ``opts`` and ``prefix`` scope the two resolutions the same
    way they scope every other reference read inside an expansion.

    Resolving the reference is only half of the side. Whatever pieces follow it
    are transforms and a lookup that wrap it in more SQL, so they are classified
    too, against the resolved field or the annotation's output field - the same
    approved-form boundary, applied to the chain rather than to a node. A head
    that resolves under a transform nobody approved is refused exactly as the
    head itself would be.
    """
    pieces = lookup.split(LOOKUP_SEP)
    for count in range(1, len(pieces) + 1):
        referenced = f"{prefix}{LOOKUP_SEP.join(pieces[:count])}"
        annotation = query.annotations.get(referenced)
        if annotation is not None:
            return _is_deterministic_order_term(query, annotation) and (
                _is_deterministic_order_lookup_chain(annotation.output_field, pieces[count:])
            )
        if referenced in query.extra:
            return False
    target = opts if opts is not None else query.get_meta()
    for count in range(len(pieces), 0, -1):
        resolved = _resolve_order_field_path(target, LOOKUP_SEP.join(pieces[:count]))
        if resolved is not None:
            return _is_deterministic_order_lookup_chain(resolved[0], pieces[count:])
    return False


def _is_deterministic_order_condition(
    query: Any,
    condition: models.Q,
    opts: Any = None,
    seen: frozenset[tuple[Any, str]] = frozenset(),
    prefix: str = "",
) -> bool:
    """Classify the predicate a conditional ordering term picks its value with.

    ``Case`` / ``When`` order by a value a ``Q`` selects, so the predicate is
    part of the ordering and is read the same way. A predicate's children are
    either nested predicates or ``(lookup, value)`` pairs, and BOTH sides of
    such a pair are compiled into the statement: the lookup names what is
    compared as surely as the value names what it is compared against. Reading
    only the value certifies a predicate that compares unreadable SQL to a
    literal, which orders the rows by that SQL just as ordering on it directly
    would - so the whole comparison is read, each side by its own rule, and the
    value is read for the SQL it carries at any depth a lookup can hold one.
    """
    for child in condition.children:
        if not isinstance(child, tuple):
            if not _is_deterministic_order_value(query, child, opts, seen, prefix):
                return False
            continue
        lookup, value = child
        if not _is_deterministic_order_predicate_reference(query, lookup, opts, prefix):
            return False
        if not _is_deterministic_order_value(query, value, opts, seen, prefix):
            return False
    return True


def _selected_ordering(queryset: models.QuerySet) -> tuple[str, tuple[Any, ...]]:
    """Return the ordering Django will compile for ``queryset``, as ``(source, terms)``.

    ``django/db/models/sql/compiler.py::SQLCompiler._order_by_pairs`` picks ONE
    collection and ignores the rest: an ``extra`` ordering wins outright, an
    explicit ``order_by`` comes next, and the model's ``Meta.ordering`` is
    reached only when nothing explicit was set and ``default_ordering`` still
    stands. They are alternatives, never a union, so a term left in a collection
    Django did not pick is dormant and reaches no SQL.

    Both questions the offset guard asks - is the order this request will run
    under deterministic, and is the model's own ordering that order -
    are this one selection read two ways, so they come from one classification
    of the already-sealed queryset rather than from separate collection scans
    that can disagree with each other and with the compiler.
    """
    query = queryset.query
    if query.extra_order_by:
        return _ORDER_FROM_EXTRA, tuple(query.extra_order_by)
    if query.order_by:
        return _ORDER_FROM_EXPLICIT, tuple(query.order_by)
    if query.default_ordering:
        ordering = query.get_meta().ordering
        if ordering:
            return _ORDER_FROM_MODEL_DEFAULT, tuple(ordering)
    return _ORDER_FROM_NOTHING, ()


def _has_deterministic_ordering(queryset: models.QuerySet) -> bool:
    """Return True when every term of the order Django will compile is deterministic.

    Classifies the SELECTED ordering, not every collection holding terms: a
    ``"?"`` sitting in ``query.order_by`` under an ``extra`` ordering that
    supersedes it never reaches SQL, while a ``"?"`` the model brought in
    through ``Meta.ordering`` does. Either way the verdict has to be about the
    collection Django is going to run.
    """
    _source, terms = _selected_ordering(queryset)
    query = queryset.query
    return all(_is_deterministic_order_term(query, term) for term in terms)


def _is_model_default_ordering_active(queryset: models.QuerySet) -> bool:
    """Return True when the model's own ``Meta.ordering`` is the order Django will compile.

    The guard's public-order eligibility rule: ordering the resolver alone put on
    the queryset never authorizes a positive offset, so the only two orders that
    do are an active ``orderBy`` input and this one. ``default_ordering`` must be
    exactly ``True`` - a merely truthy stand-in is a shape the queryset pipeline
    does not produce, and an offset window is not granted on one. Grouping
    suppresses the default for the same reason ``QuerySet.ordered`` does: an
    aggregate query does not carry the model's row order.
    """
    query = queryset.query
    source, terms = _selected_ordering(queryset)
    if source != _ORDER_FROM_MODEL_DEFAULT:
        return False
    if query.default_ordering is not True or query.group_by:
        return False
    return all(_is_deterministic_order_term(query, term) for term in terms)


def _model_from_definition(definition: Any) -> type[models.Model]:
    """Read the target's Django model off its ONE definition read.

    Called exactly once per field, at construction. The value seeds the default
    resolver and pins both visibility seals, so the table the field queries and
    the table those seals validate against are the same object by construction -
    a stateful target metaclass has no second read through which to substitute
    another model between the seed and the seal.

    Fails LOUDLY for the same reason the sidecar read does: a definition whose
    model cannot be read is a field that cannot be built, and a soft answer
    would defer the failure to a request against an unknown table.
    """
    try:
        model = definition.model
    except Exception as exc:
        raise ConfigurationError(
            f"DjangoListField could not read the model from the definition of "
            f"{_safe_class_name(getattr(definition, 'origin', definition))}: {exc}",
        ) from exc
    if not (isinstance(model, type) and issubclass(model, models.Model)):
        raise ConfigurationError(
            f"DjangoListField target "
            f"{_safe_class_name(getattr(definition, 'origin', definition))} has a definition "
            f"whose model is not a Django model; got {_safe_arg_repr(model)}.",
        )
    return model


def _orderset_class_from_definition(definition: Any) -> type | None:
    """Read the target's declared ``Meta.orderset_class`` off its ONE definition read.

    Called exactly once per field, at construction, from the definition
    ``_validate_djangotype_target`` returned. The read fails LOUDLY: a target
    whose sidecar declaration cannot be read is a broken field, and answering
    ``None`` would publish a schema without ``orderBy`` for a target that
    declares one - a silent SDL change at the line that wrote the field.
    """
    try:
        return definition.orderset_class
    except Exception as exc:
        raise ConfigurationError(
            f"DjangoListField could not read Meta.orderset_class from the definition of "
            f"{_safe_class_name(getattr(definition, 'origin', definition))}: {exc}",
        ) from exc


def _field_label(info: Any) -> str:
    """Return the resolver field label without allowing consumer descriptors to escape."""
    try:
        field_name = info.field_name
    except Exception:
        return "DjangoListField"
    return field_name if isinstance(field_name, str) and field_name else "DjangoListField"


def _resolver_root_and_info(args: tuple[Any, ...], kwargs: dict[str, Any]) -> tuple[Any, Info]:
    """Extract Strawberry's positional resolver context and reject unknown call inputs."""
    if len(args) > 2:
        raise TypeError("DjangoListField resolver accepts only root and info positional inputs.")
    unexpected = set(kwargs) - {"info", "root"}
    if unexpected:
        names = ", ".join(sorted(unexpected))
        raise TypeError(f"DjangoListField resolver received unexpected keyword inputs: {names}.")
    if args and "root" in kwargs:
        raise TypeError("DjangoListField resolver received multiple values for root.")
    if len(args) > 1 and "info" in kwargs:
        raise TypeError("DjangoListField resolver received multiple values for info.")
    root = args[0] if args else kwargs.get("root")
    if len(args) > 1:
        info = args[1]
    else:
        try:
            info = kwargs["info"]
        except KeyError as exc:
            raise TypeError("DjangoListField resolver requires info.") from exc
    return root, info


def _argument_record(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    *,
    max_rows: int | None,
    trusted_max_rows: bool,
    offset: Any = None,
    limit: Any = None,
    order_by: Any = strawberry.UNSET,
) -> tuple[Any, Info, _ListArguments]:
    """Extract root, info, and normalize list arguments for any resolver invocation."""
    root, info = _resolver_root_and_info(args, kwargs)
    field_name = _field_label(info)
    args_record = _normalize_list_arguments(
        field_name,
        info,
        max_rows,
        trusted_max_rows,
        offset=offset,
        limit=limit,
        order_by=order_by,
    )
    return root, info, args_record


def _build_non_queryset_rejection_error(
    args_record: _ListArguments,
    info: Info,
    *,
    orderset_class: type | None = None,
) -> ListArgumentError | None:
    field_name = _field_label(info)
    if args_record.order_by_supplied:
        return ListArgumentError(
            field_name,
            _resolve_argument_wire_name(info, "order_by"),
            reason="queryset_required",
        )
    if args_record.offset is not None and args_record.offset > 0:
        order_arg = _resolve_argument_wire_name(info, "order_by") if orderset_class else ""
        return ListArgumentError(
            field_name,
            _resolve_argument_wire_name(info, "offset"),
            reason="order_required",
            value=args_record.offset,
            order_argument=order_arg,
        )
    return None


async def _handle_non_queryset_rejections_async(
    source: Any,
    args_record: _ListArguments,
    info: Info,
    *,
    orderset_class: type | None = None,
) -> None:
    """Reject a non-queryset source, closing an async-only one on EVERY rejecting exit.

    Decision 8 promises a rejected async-only source is never advanced and is
    closed when possible, with the primary error keeping precedence. Building
    the rejection can itself fail (malformed schema metadata behind the wire
    name lookup), and that exit owes the same close: the source is being
    rejected either way, so the failure becomes the primary error the cleanup
    utility attaches its notes to.
    """
    try:
        err = _build_non_queryset_rejection_error(
            args_record,
            info,
            orderset_class=orderset_class,
        )
    except BaseException as primary:
        if is_async_only_iterable(source):
            await _cleanup_rejected_async_iterable(source, primary, caller="DjangoListField")
        raise
    if err is not None:
        if is_async_only_iterable(source):
            await _cleanup_rejected_async_iterable(source, err, caller="DjangoListField")
        raise err


def _check_nonzero_offset_guard(
    queryset: models.QuerySet,
    args_record: _ListArguments,
    orderset_class: type | None,
    info: Info,
) -> None:
    """Validate that non-zero offset pagination is backed by a deterministic ordering.

    A positive ``offset`` needs an order the request can name: active ``OrderSet``
    terms the consumer supplied, or the model's own eligible ``Meta.ordering``.
    With neither in effect the offset is rejected, because the rows it skips are
    otherwise whichever rows the database happened to return first.

    The empty-queryset allowance lives inside the active-input branch alone.
    Django reports ``ordered`` True for an ``EmptyQuerySet`` whatever it carries
    (``Category.objects.none().ordered is True``), so that half of the branch is
    vacuous there and an empty window supplied with active terms rides through on
    an order that orders nothing. A request with no active input and no eligible
    model ordering is rejected whether its queryset is empty or not.
    """
    if args_record.offset is None or args_record.offset <= 0:
        return
    has_active_order = False
    if (
        args_record.order_by_supplied
        and orderset_class is not None
        and orderset_class._input_has_active_terms(args_record.order_by)
        and queryset.ordered
        and _has_deterministic_ordering(queryset)
    ):
        has_active_order = True
    if not has_active_order and not _is_model_default_ordering_active(queryset):
        field_name = _field_label(info)
        order_arg = (
            _resolve_argument_wire_name(info, "order_by") if orderset_class is not None else ""
        )
        raise ListArgumentError(
            field_name,
            _resolve_argument_wire_name(info, "offset"),
            reason="order_required",
            value=args_record.offset,
            order_argument=order_arg,
        )


def _order_normalization_scope(
    args_record: _ListArguments,
    orderset_class: type | None,
) -> contextlib.AbstractContextManager[None]:
    """Return the capture scope this request actually needs, or an inert one.

    The handoff exists for exactly one consumer: the non-zero-offset guard's
    active-order check, which is the only caller of
    ``OrderSet._input_has_active_terms``. It runs only when a positive ``offset``
    arrives WITH an ``orderBy`` AND the field captured an ``OrderSet`` to
    normalize through, so every other argument-bearing request - a ``limit``
    alone, ``offset: 0``, positive offset riding model ``Meta.ordering`` - has
    nothing to hand over and does not pay for the scope. One conditional
    context, chosen here, keeps both colorings' pipelines identical in shape and
    the cost on the path that uses it.

    ``orderset_class`` is the field's captured sidecar, so the no-``OrderSet``
    condition is decidable here rather than asserted: over the wire that target
    publishes no ``orderBy`` at all, and the direct call that supplies one
    reaches the rejection in
    ``django_strawberry_framework/utils/querysets.py::require_orderset_class``
    without having opened a scope first.
    """
    if (
        args_record.order_by_supplied
        and orderset_class is not None
        and args_record.offset is not None
        and args_record.offset > 0
    ):
        # Deferred: ``orders`` stays out of the package-root import graph.
        from .orders.sets import capture_applied_order_normalization

        return capture_applied_order_normalization()
    return contextlib.nullcontext()


def _execute_queryset_pipeline_sync(
    target_type: type,
    source: models.QuerySet,
    info: Info,
    args_record: _ListArguments,
    max_rows: int | None,
    trusted_max_rows: bool,
    *,
    model: type[models.Model],
    orderset_class: type | None,
    is_async_context: bool,
) -> Any:
    if not args_record.any_argument_supplied:
        post_vis_qs = apply_type_visibility_sync(target_type, source, info, model=model)
        bounded = _windowed_rows(post_vis_qs, info, max_rows, trusted=trusted_max_rows)
        return wrap_async_queryset_adapter(bounded) if is_async_context else bounded

    post_vis_qs = apply_type_visibility_sync(
        target_type,
        source,
        info,
        model=model,
        policy=_LIST_ARGUMENT_VISIBILITY_POLICY,
    )
    # One task-local capture scope spans public ordering and the offset guard,
    # so the base ``OrderSet`` can hand its normalized terms to the guard without
    # writing into the consumer's ``info.context`` - opened only when that
    # handoff can happen.
    with _order_normalization_scope(args_record, orderset_class):
        if args_record.order_by_supplied:
            post_order_qs = apply_orderset_sync(
                target_type,
                orderset_class,
                post_vis_qs,
                args_record.order_by,
                info,
                model=model,
            )
        else:
            post_order_qs = post_vis_qs

        _check_nonzero_offset_guard(post_order_qs, args_record, orderset_class, info)

    bounded = _windowed_rows(
        post_order_qs,
        info,
        max_rows,
        trusted=trusted_max_rows,
        offset=args_record.offset,
        requested_limit=args_record.limit,
    )
    return wrap_async_queryset_adapter(bounded) if is_async_context else bounded


async def _execute_queryset_pipeline_async(
    target_type: type,
    source: models.QuerySet,
    info: Info,
    args_record: _ListArguments,
    max_rows: int | None,
    trusted_max_rows: bool,
    *,
    model: type[models.Model],
    orderset_class: type | None,
) -> Any:
    if not args_record.any_argument_supplied:
        post_vis_qs = await apply_type_visibility_async(target_type, source, info, model=model)
        bounded = _windowed_rows(post_vis_qs, info, max_rows, trusted=trusted_max_rows)
        return wrap_async_queryset_adapter(bounded)

    post_vis_qs = await apply_type_visibility_async(
        target_type,
        source,
        info,
        model=model,
        policy=_LIST_ARGUMENT_VISIBILITY_POLICY,
    )
    # One task-local capture scope spans public ordering and the offset guard,
    # so the base ``OrderSet`` can hand its normalized terms to the guard without
    # writing into the consumer's ``info.context`` - opened only when that
    # handoff can happen.
    with _order_normalization_scope(args_record, orderset_class):
        if args_record.order_by_supplied:
            post_order_qs = await apply_orderset_async(
                target_type,
                orderset_class,
                post_vis_qs,
                args_record.order_by,
                info,
                model=model,
            )
        else:
            post_order_qs = post_vis_qs

        _check_nonzero_offset_guard(post_order_qs, args_record, orderset_class, info)

    bounded = _windowed_rows(
        post_order_qs,
        info,
        max_rows,
        trusted=trusted_max_rows,
        offset=args_record.offset,
        requested_limit=args_record.limit,
    )
    return wrap_async_queryset_adapter(bounded)


def DjangoListField(  # noqa: N802  # PascalCase for graphene-django parity - consumer usage is `DjangoListField(BranchType)`
    target_type: type,
    *,
    resolver: Callable | None = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Sequence[object] = (),
    max_rows: int | None = None,
    trusted_max_rows: bool = False,
) -> Any:
    """Factory for a non-Relay ``list[T]`` root Query field bound to a ``DjangoType``.

    Outer nullability comes from the class-attribute annotation: ``list[T]`` renders
    ``[T!]!`` and ``list[T] | None`` renders ``[T!]``. The default resolver pulls
    ``model._default_manager.all()`` and applies the target type's ``get_queryset``
    visibility hook in sync and async contexts. A custom ``resolver=`` overrides
    the default body; when its return value is a ``Manager`` or ``QuerySet``, the
    wrapper applies ``get_queryset``.

    Argument surface:
    - Every ``DjangoListField`` publishes nullable optional ``offset`` and ``limit``
      arguments (GraphQL ``Int``).
    - When the target ``DjangoType`` declares ``Meta.orderset_class``, a typed
      ``orderBy`` argument is conditionally published. Targets without an orderset
      publish only ``offset`` and ``limit``.
    - Wire argument names follow the active schema naming converter (by default
      camelCase ``offset``, ``limit``, ``orderBy``; with ``auto_camel_case=False``,
      ``order_by``).

    Ordering contract (strictly ordered offset):
    A ``DjangoListField`` provides ordered-offset paging, NOT stable or repeatable
    pagination. An active order fixes the sort expression, not which of two tied rows
    falls on either side of a page boundary. Unlike Relay connection fields, flat
    lists do not inject a primary-key tiebreaker or ``DISTINCT``. Consumers wanting
    deterministic pagination across pages with duplicate values must add a unique
    final term to the ordering themselves.

    Non-zero offset precondition:
    A published ``offset`` argument is a runtime precondition rather than a per-field
    capability claim. Usable only where an order source exists, ``offset > 0``
    requires a materially active order on the post-visibility queryset -- either a
    supplied ``orderBy`` with surviving non-null ordering terms, or a still-effective
    model ``Meta.ordering``. On a target with neither ``Meta.orderset_class`` nor
    still-effective model ``Meta.ordering``, positive offset values permanently raise
    ``ListArgumentError`` with ``reason="order_required"``.

    Row bounds and ceilings:
    Every ``DjangoListField`` is bounded. The effective row bound is the minimum of
    the client ``limit``, the field's ``max_rows``, and the request
    ``ResourcePolicy.max_list_rows`` (with ``trusted_max_rows=True`` permitting
    field-declared widening). Client ``offset`` is bounded by the request's
    ``ResourcePolicy.max_list_rows``. Both ceilings are accepted-coordinate ceilings,
    not physical database scan budgets. Exceeding either ceiling raises
    ``ListArgumentError`` with ``reason="over_ceiling"``.

    Async execution:
    Under asynchronous execution, querysets are completed through the package-internal
    async-only completion adapter, preventing synchronous event-loop iteration during
    GraphQL result execution while preserving query optimization.

    Optimizer cooperation rides the root-gated optimizer extension hook, so
    root-position list selections receive automatic select_related / prefetch_related
    / only planning.
    """
    if max_rows is not None:
        validate_collection_bound(max_rows, field="DjangoListField max_rows")
    validate_trusted_flag(trusted_max_rows, field="DjangoListField trusted_max_rows")
    # ONE definition read for the whole field: the validator's contained read is
    # what the signature, the SDL, the default seed, both visibility seals, and
    # every resolver dispatch below run on, so a stateful target metaclass has no
    # second read to answer differently.
    definition = _validate_djangotype_target(target_type, resolver, field="DjangoListField")
    target_model = _model_from_definition(definition)
    orderset_class = _orderset_class_from_definition(definition)
    directives = validated_field_directives("DjangoListField", directives)

    # Factory-site async commitment (Decision 3; spec-020 Decision 1
    # "Async-detection asymmetry - intentional, not a harmonization candidate"):
    # ``_default`` reads the operation's executor per call
    # (``utils/execution_mode.py::async_execution``) so the same factory output
    # dispatches correctly under both ``schema.execute_sync``
    # and ``await schema.execute``. The consumer-wrapper branch below commits
    # per-construction via ``is_async_callable(user_resolver)`` (the
    # ``__call__``/``functools.partial``-aware superset of
    # ``inspect.iscoroutinefunction``) because Strawberry inspects the resolver
    # signature once at schema
    # construction and freezes the sync-vs-async handling.
    #
    # That commitment is per-RESOLVER, not per-request, so the sync wrapper is
    # the one that runs when a sync consumer resolver is executed inside an
    # event loop - and on that path it returns a value graphql-core completes
    # asynchronously rather than a finished list: the queryset branch returns
    # ``wrap_async_queryset_adapter``'s async-only rows object, and the
    # async-only-iterable branch returns ``_resolve_async_iterable``'s
    # coroutine, which the field executor awaits. Neither is a slip. The
    # alternative is driving ORM iteration or an async generator from a sync
    # frame on the event-loop thread, which is what the async pipeline exists to
    # avoid. Code reaching past the executor to ``field.base_resolver`` under a
    # running loop owes the return value the same completion the executor gives
    # it.
    if resolver is None:

        def _default(
            *args: Any,
            offset: Any = None,
            limit: Any = None,
            order_by: Any = strawberry.UNSET,
            **kwargs: Any,
        ) -> Any:
            _, info, args_record = _argument_record(
                args,
                kwargs,
                max_rows=max_rows,
                trusted_max_rows=trusted_max_rows,
                offset=offset,
                limit=limit,
                order_by=order_by,
            )
            qs = base_queryset(target_model)
            if async_execution():
                return _execute_queryset_pipeline_async(
                    target_type,
                    qs,
                    info,
                    args_record,
                    max_rows,
                    trusted_max_rows,
                    model=target_model,
                    orderset_class=orderset_class,
                )
            return _execute_queryset_pipeline_sync(
                target_type,
                qs,
                info,
                args_record,
                max_rows,
                trusted_max_rows,
                model=target_model,
                orderset_class=orderset_class,
                is_async_context=False,
            )

        wrapped = _default
    else:
        user_resolver = resolver

        async def _resolve_async_iterable(
            source: Any,
            info: Info,
            args_record: _ListArguments,
        ) -> Any:
            if args_record.any_argument_supplied:
                await _handle_non_queryset_rejections_async(
                    source,
                    args_record,
                    info,
                    orderset_class=orderset_class,
                )
            return await _windowed_rows_async(
                source,
                info,
                max_rows,
                trusted=trusted_max_rows,
                offset=args_record.offset,
                requested_limit=args_record.limit,
            )

        if is_async_callable(user_resolver):

            async def _wrap(
                *args: Any,
                offset: Any = None,
                limit: Any = None,
                order_by: Any = strawberry.UNSET,
                **kwargs: Any,
            ) -> Any:
                root, info, args_record = _argument_record(
                    args,
                    kwargs,
                    max_rows=max_rows,
                    trusted_max_rows=trusted_max_rows,
                    offset=offset,
                    limit=limit,
                    order_by=order_by,
                )
                raw_source = await user_resolver(root, info)
                source, is_qs = prepared_resolver_source(
                    raw_source,
                    target_type,
                    async_guard=reject_residual_async_source,
                )
                if is_qs:
                    return await _execute_queryset_pipeline_async(
                        target_type,
                        source,
                        info,
                        args_record,
                        max_rows,
                        trusted_max_rows,
                        model=target_model,
                        orderset_class=orderset_class,
                    )
                return await _resolve_async_iterable(source, info, args_record)
        else:

            def _wrap(
                *args: Any,
                offset: Any = None,
                limit: Any = None,
                order_by: Any = strawberry.UNSET,
                **kwargs: Any,
            ) -> Any:
                root, info, args_record = _argument_record(
                    args,
                    kwargs,
                    max_rows=max_rows,
                    trusted_max_rows=trusted_max_rows,
                    offset=offset,
                    limit=limit,
                    order_by=order_by,
                )
                source = user_resolver(root, info)
                if is_async_only_iterable(source):
                    reject_async_iterable_in_sync_context(
                        source,
                        flavor_noun="DjangoListField",
                        async_executor=operation_is_async(),
                    )
                    return _resolve_async_iterable(
                        source,
                        info,
                        args_record,
                    )
                source, is_qs = prepared_resolver_source(
                    source,
                    target_type,
                    async_guard=reject_awaitable_sync_source,
                )
                if is_qs:
                    return _execute_queryset_pipeline_sync(
                        target_type,
                        source,
                        info,
                        args_record,
                        max_rows,
                        trusted_max_rows,
                        model=target_model,
                        orderset_class=orderset_class,
                        is_async_context=async_execution(),
                    )
                rejection = _build_non_queryset_rejection_error(
                    args_record,
                    info,
                    orderset_class=orderset_class,
                )
                if rejection is not None:
                    raise rejection
                return _windowed_rows(
                    source,
                    info,
                    max_rows,
                    trusted=trusted_max_rows,
                    offset=args_record.offset,
                    requested_limit=args_record.limit,
                )

        wrapped = _wrap

    signature, annotations = _synthesized_list_signature(orderset_class)
    wrapped.__signature__ = signature
    wrapped.__annotations__ = annotations

    return strawberry.field(
        resolver=wrapped,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
