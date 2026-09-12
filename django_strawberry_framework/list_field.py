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
from django.db import models
from django.db.models.functions import Random
from graphql import GraphQLError
from strawberry.schema.schema_converter import GraphQLCoreConverter
from strawberry.types import Info
from strawberry.utils.inspect import in_async_context

from .exceptions import (
    ConfigurationError,
    DjangoStrawberryFrameworkError,
    _safe_arg_repr,
    _safe_class_name,
    _safe_type_name,
    describe_value,
)
from .resource_policy import (
    _close_async_iterator,
    bounded_rows,
    bounded_rows_async,
    effective_bound,
    policy_from_info,
    validate_collection_bound,
    validate_trusted_flag,
)
from .types import DjangoType
from .types.base import _is_relay_shaped
from .utils.directives import validated_field_directives
from .utils.querysets import (
    _LIST_ARGUMENT_VISIBILITY_POLICY,
    SyncMisuseError,
    _dispose_sync_awaitable,
    _snapshot_routing_intent,
    _validate_post_orderset_result,
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
    """Run the four shared DjangoType-target constructor guards for a field factory.

    Shared by ``DjangoListField`` and ``DjangoConnectionField`` (and any future
    node field). ``field`` is the factory's public name
    (e.g. ``"DjangoListField"``) interpolated into the ``ConfigurationError``
    messages so each factory's errors name itself. These four constructor-site
    checks fail at the line that wrote ``<field>(...)`` rather than at
    finalize-time.

    Order is load-bearing - each target-type check assumes the previous one
    passed. The third (own-class registration) check is the strict invariant:
    ``__django_strawberry_definition__`` is assigned by
    ``DjangoType.__init_subclass__`` (``types/base.py::DjangoType.__init_subclass__``)
    only for concrete subclasses carrying their own ``Meta`` with a ``model``.
    The attribute is inherited via MRO, so ``hasattr`` would accept a subclass
    that omits its own ``Meta`` - binding the field to a target whose
    definition, ``Meta.primary`` state, and model belong to the parent.
    ``definition.origin is target_type`` is the strict own-class invariant
    (NOT ``hasattr``).

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

    Raises ``ConfigurationError`` on failure; returns the resolved
    ``__django_strawberry_definition__`` when all four pass, so the Relay
    validator consumes the SAME contained read instead of re-reading the
    attribute directly (a stateful metaclass could answer the first guarded
    read and detonate a second raw one). The caller runs any factory-specific
    guards (e.g. the connection field's Relay-Node guard) AFTER this returns.
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
    if definition is None or getattr(definition, "origin", None) is not target_type:
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
    """Run the four shared DjangoType-target guards plus the Relay-Node-shaped fifth.

    The Relay-shaped target guard shared by ``DjangoConnectionField`` and
    ``relay.py::_validate_node_target`` (which backs ``DjangoNodeField`` /
    ``DjangoNodesField``) -- single-sited. Delegates the
    four base checks to ``_validate_djangotype_target`` (with the call site's
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
        without an OrderSet are caught by _require_orderset_class at pipeline execution time.
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


def _is_random_order_term(term: Any) -> bool:
    """Classify random order terms: exact '?' or Random() / OrderBy(Random())."""
    if term == "?" or isinstance(term, Random):
        return True
    return isinstance(getattr(term, "expression", None), Random)


def _has_no_random_terms(queryset: models.QuerySet) -> bool:
    """Return True if queryset has no random terms in query.order_by or extra_order_by."""
    query = queryset.query
    return all(not _is_random_order_term(term) for term in query.order_by) and all(
        not _is_random_order_term(term) for term in query.extra_order_by
    )


def _is_model_default_ordering_active(queryset: models.QuerySet) -> bool:
    """Return True if the model declares active default ordering on queryset.

    Requires query.default_ordering is True, non-empty and non-random Meta.ordering,
    empty query.order_by and query.extra_order_by, and falsy query.group_by.
    """
    query = queryset.query
    if query.default_ordering is not True:
        return False
    if query.order_by or query.extra_order_by or query.group_by:
        return False
    ordering = query.get_meta().ordering
    if not ordering:
        return False
    return not any(_is_random_order_term(term) for term in ordering)


async def _cleanup_rejected_async_iterable(iterable: Any, primary_error: BaseException) -> None:
    try:
        iterator = aiter(iterable)
    except BaseException as aiter_err:
        try:
            notes = [*getattr(primary_error, "__notes__", ())]
            notes.append(f"Iterator acquisition failed: {aiter_err!r}")
            primary_error.__notes__ = notes
        except Exception:
            pass
        return
    await _close_async_iterator(
        iterator,
        primary_error=primary_error,
        caller="DjangoListField",
    )


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
            await _cleanup_rejected_async_iterable(source, primary)
        raise
    if err is not None:
        if is_async_only_iterable(source):
            await _cleanup_rejected_async_iterable(source, err)
        raise err


def _require_orderset_class(target_type: type, orderset_class: type | None) -> type:
    """Return the field's captured ``OrderSet``, or reject an ordering call without one.

    Reachable only through a direct call that supplies ``order_by`` to a field
    whose target declares no ``Meta.orderset_class``; over the wire the argument
    is simply not published.
    """
    if orderset_class is None:
        raise ConfigurationError(
            f"DjangoListField target {_safe_class_name(target_type)} has no orderset_class configured.",
        )
    return orderset_class


def _apply_orderset_sync(
    target_type: type,
    orderset_class: type | None,
    queryset: models.QuerySet,
    order_by: Any,
    info: Info,
    *,
    model: type[models.Model],
) -> models.QuerySet:
    orderset_class = _require_orderset_class(target_type, orderset_class)
    method_name = f"{orderset_class.__name__}.apply_sync"
    # Frozen BEFORE the override receives the queryset: it can mutate the
    # object it was handed, so a post-call read is not a baseline.
    expected_routing = _snapshot_routing_intent(queryset, method_name)
    candidate = orderset_class.apply_sync(order_by, queryset, info)
    if inspect.isawaitable(candidate):
        _dispose_sync_awaitable(candidate)
        raise SyncMisuseError(
            f"{method_name} returned an awaitable in a sync resolver context. "
            f"Make apply_sync synchronous or execute the query asynchronously.",
        )
    return _validate_post_orderset_result(
        target_type,
        expected_routing,
        candidate,
        method_name,
        model=model,
    )


async def _apply_orderset_async(
    target_type: type,
    orderset_class: type | None,
    queryset: models.QuerySet,
    order_by: Any,
    info: Info,
    *,
    model: type[models.Model],
) -> models.QuerySet:
    orderset_class = _require_orderset_class(target_type, orderset_class)
    method_name = f"{orderset_class.__name__}.apply_async"
    expected_routing = _snapshot_routing_intent(queryset, method_name)
    candidate_awaitable = orderset_class.apply_async(order_by, queryset, info)
    if not inspect.isawaitable(candidate_awaitable):
        raise ConfigurationError(
            f"{method_name} returned a non-awaitable value "
            f"({_safe_type_name(candidate_awaitable)}); expected an awaitable coroutine or Future.",
        )
    candidate = await candidate_awaitable
    if inspect.isawaitable(candidate):
        _dispose_sync_awaitable(candidate)
        raise ConfigurationError(
            f"{method_name} returned a residual awaitable value "
            f"({_safe_type_name(candidate)}); expected a QuerySet.",
        )
    return _validate_post_orderset_result(
        target_type,
        expected_routing,
        candidate,
        method_name,
        model=model,
    )


def _check_nonzero_offset_guard(
    queryset: models.QuerySet,
    args_record: _ListArguments,
    orderset_class: type | None,
    info: Info,
) -> None:
    """Validate that non-zero offset pagination is backed by a deterministic ordering.

    Rejects non-zero offset requests if neither active OrderSet terms nor model default
    ordering is in effect. Note on EmptyQuerySet: Django's EmptyQuerySet vacuously reports
    ordered=True (Category.objects.none().ordered is True). An empty queryset with offset > 0
    and no active orderset or model ordering is accepted by the queryset.ordered check only
    because it represents an empty result window where row ordering is vacuously preserved.
    """
    if args_record.offset is None or args_record.offset <= 0:
        return
    has_active_order = False
    if (
        args_record.order_by_supplied
        and orderset_class is not None
        and orderset_class._input_has_active_terms(args_record.order_by)
        and queryset.ordered
        and _has_no_random_terms(queryset)
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
    reaches ``_require_orderset_class``'s rejection without having opened a
    scope first.
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
        bounded = bounded_rows(post_vis_qs, info, max_rows, trusted=trusted_max_rows)
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
            post_order_qs = _apply_orderset_sync(
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

    bounded = bounded_rows(
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
        bounded = bounded_rows(post_vis_qs, info, max_rows, trusted=trusted_max_rows)
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
            post_order_qs = await _apply_orderset_async(
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

    bounded = bounded_rows(
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
    # ``_default`` uses runtime ``in_async_context()`` per-call so the same
    # factory output dispatches correctly under both ``schema.execute_sync``
    # and ``await schema.execute``. The consumer-wrapper branch below commits
    # per-construction via ``is_async_callable(user_resolver)`` (the
    # ``__call__``/``functools.partial``-aware superset of
    # ``inspect.iscoroutinefunction``) because Strawberry inspects the resolver
    # signature once at schema
    # construction and freezes the sync-vs-async handling.
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
            if in_async_context():
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
            return await bounded_rows_async(
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
                        is_async_context=in_async_context(),
                    )
                rejection = _build_non_queryset_rejection_error(
                    args_record,
                    info,
                    orderset_class=orderset_class,
                )
                if rejection is not None:
                    raise rejection
                return bounded_rows(
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
