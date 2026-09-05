"""``DjangoListField`` - non-Relay ``list[T]`` field for root Query fields.

Spec: ``docs/SPECS/spec-020-list_field-0_0_7.md``.
Extension spec: ``docs/spec-050-list_field_arguments-0_0_15.md``.
Target release: ``0.0.7``.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import strawberry
from django.db import models
from django.db.models.functions import Random
from graphql import GraphQLError
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
)
from .types import DjangoType
from .types.base import _is_relay_shaped
from .utils.directives import validated_field_directives
from .utils.querysets import (
    _LIST_ARGUMENT_VISIBILITY_POLICY,
    SyncMisuseError,
    _dispose_sync_awaitable,
    _validate_post_orderset_result,
    apply_type_visibility_async,
    apply_type_visibility_sync,
    initial_queryset,
    is_async_only_iterable,
    prepared_resolver_source,
    reject_async_iterable_in_sync_context,
    reject_awaitable_sync_source,
    reject_residual_async_source,
    wrap_async_queryset_adapter,
)
from .utils.typing import is_async_callable, schema_config_from_info

__all__ = ("DjangoListField", "ListArgumentError")


def _validate_djangotype_target(
    target_type: type,
    resolver: Callable | None,
    *,
    field: str,
) -> None:
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
) -> None:
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
    its own wording.
    """
    # The definition comes back from the base validator's ONE contained read;
    # re-reading the attribute directly here would let a stateful metaclass
    # answer the first (guarded, defaulted) read and detonate the second.
    definition = _validate_djangotype_target(target_type, resolver, field=field)
    if not _is_relay_shaped(target_type, definition.interfaces):
        raise ConfigurationError(relay_error_message)


class ListArgumentError(GraphQLError, DjangoStrawberryFrameworkError):
    """An argument to ``DjangoListField`` was invalid or violated policy bounds.

    Dual-inherits ``GraphQLError`` (so Strawberry/GraphQL transport serializes it
    as an execution error with structured extensions) and
    ``DjangoStrawberryFrameworkError`` (so consumers can catch it alongside any
    other framework error).
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
        if reason not in {
            "negative",
            "non_integer",
            "order_required",
            "over_ceiling",
            "queryset_required",
        }:
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
                f"integer, got {value}."
            )
        elif reason == "over_ceiling":
            self.value = value
            msg = (
                f"Invalid argument {argument!r} on {field}: value {value} exceeds "
                f"the maximum allowed ceiling of {ceiling}."
            )
        elif reason == "order_required":
            self.value = value
            if order_argument:
                ordering_phrase = f"via {order_argument!r} or model 'Meta.ordering'"
            else:
                ordering_phrase = "via model 'Meta.ordering'"
            msg = (
                f"Invalid argument {argument!r} on {field}: non-zero offset ({value}) "
                f"requires an active ordering {ordering_phrase}."
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


def _resolve_argument_wire_name(info: Any, parameter_name: str) -> str:
    """Resolve the active GraphQL wire name for an internal parameter name.

    Only invoked on error paths (e.g. inside ``ListArgumentError`` instantiation or
    normalizer error branches) so successful requests perform zero name conversions.
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
    if arg_def is not None:
        config = schema_config_from_info(info)
        try:
            name_converter = config.name_converter
        except AttributeError:
            return fallback
        except Exception as exc:
            raise ConfigurationError(
                f"Failed to read the name converter for argument {parameter_name!r}: {exc}",
            ) from exc
        try:
            return name_converter.from_argument(arg_def)
        except Exception as exc:
            raise ConfigurationError(
                f"Failed to resolve wire name for argument {parameter_name!r}: {exc}",
            ) from exc
    return fallback


@dataclass(frozen=True, slots=True)
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
        if isinstance(norm_offset, bool) or not isinstance(norm_offset, int):
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
        if isinstance(norm_limit, bool) or not isinstance(norm_limit, int):
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


def _synthesized_list_signature(target_type: type) -> tuple[inspect.Signature, dict[str, Any]]:
    """Build the resolver ``__signature__`` and ``__annotations__`` for DjangoListField.

    Carries ``offset`` and ``limit`` arguments, plus conditional ``order_by`` if the
    target type declares ``Meta.orderset_class``. The return annotation is left empty
    (``inspect.Signature.empty``) and omitted from annotations so the outer class attribute
    annotation retains sole ownership of outer nullability (``list[T]`` vs ``list[T] | None``).
    """
    orderset_class = _orderset_class_for_target(target_type)
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


def _orderset_class_for_target(target_type: type) -> type | None:
    try:
        definition = target_type.__django_strawberry_definition__
        return None if definition is None else definition.orderset_class
    except Exception:
        return None


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


def _build_non_queryset_rejection_error(
    args_record: _ListArguments,
    info: Info,
    *,
    target_type: type | None = None,
) -> ListArgumentError | None:
    field_name = _field_label(info)
    if args_record.order_by_supplied:
        return ListArgumentError(
            field_name,
            _resolve_argument_wire_name(info, "order_by"),
            reason="queryset_required",
        )
    if args_record.offset is not None and args_record.offset > 0:
        has_orderset = False
        if target_type is not None:
            has_orderset = _orderset_class_for_target(target_type) is not None
        order_arg = _resolve_argument_wire_name(info, "order_by") if has_orderset else ""
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
    target_type: type | None = None,
) -> None:
    err = _build_non_queryset_rejection_error(args_record, info, target_type=target_type)
    if err is not None:
        if is_async_only_iterable(source):
            await _cleanup_rejected_async_iterable(source, err)
        raise err


def _handle_non_queryset_rejections_sync(
    args_record: _ListArguments,
    info: Info,
    *,
    target_type: type | None = None,
) -> None:
    err = _build_non_queryset_rejection_error(args_record, info, target_type=target_type)
    if err is not None:
        raise err


def _apply_orderset_sync(
    target_type: type,
    queryset: models.QuerySet,
    order_by: Any,
    info: Info,
) -> tuple[models.QuerySet, type | None]:
    orderset_class = _orderset_class_for_target(target_type)
    if orderset_class is None:
        raise ConfigurationError(
            f"DjangoListField target {_safe_class_name(target_type)} has no orderset_class configured.",
        )
    candidate = orderset_class.apply_sync(order_by, queryset, info)
    if inspect.isawaitable(candidate):
        _dispose_sync_awaitable(candidate)
        raise SyncMisuseError(
            f"{orderset_class.__name__}.apply_sync returned an awaitable in a sync resolver context. "
            f"Make apply_sync synchronous or execute the query asynchronously.",
        )
    sealed = _validate_post_orderset_result(
        target_type,
        queryset,
        candidate,
        f"{orderset_class.__name__}.apply_sync",
    )
    return sealed, orderset_class


async def _apply_orderset_async(
    target_type: type,
    queryset: models.QuerySet,
    order_by: Any,
    info: Info,
) -> tuple[models.QuerySet, type | None]:
    orderset_class = _orderset_class_for_target(target_type)
    if orderset_class is None:
        raise ConfigurationError(
            f"DjangoListField target {_safe_class_name(target_type)} has no orderset_class configured.",
        )
    candidate_awaitable = orderset_class.apply_async(order_by, queryset, info)
    if not inspect.isawaitable(candidate_awaitable):
        raise ConfigurationError(
            f"{orderset_class.__name__}.apply_async returned a non-awaitable value "
            f"({_safe_type_name(candidate_awaitable)}); expected an awaitable coroutine or Future.",
        )
    candidate = await candidate_awaitable
    if inspect.isawaitable(candidate):
        _dispose_sync_awaitable(candidate)
        raise ConfigurationError(
            f"{orderset_class.__name__}.apply_async returned a residual awaitable value "
            f"({_safe_type_name(candidate)}); expected a QuerySet.",
        )
    sealed = _validate_post_orderset_result(
        target_type,
        queryset,
        candidate,
        f"{orderset_class.__name__}.apply_async",
    )
    return sealed, orderset_class


def _check_nonzero_offset_guard(
    queryset: models.QuerySet,
    args_record: _ListArguments,
    orderset_class: type | None,
    info: Info,
) -> None:
    if args_record.offset is None or args_record.offset <= 0:
        return
    has_active_order = False
    if (
        args_record.order_by_supplied
        and orderset_class is not None
        and orderset_class._input_has_active_terms(args_record.order_by, info)
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


def _execute_queryset_pipeline_sync(
    target_type: type,
    source: models.QuerySet,
    info: Info,
    args_record: _ListArguments,
    max_rows: int | None,
    trusted_max_rows: bool,
    *,
    is_async_context: bool,
) -> Any:
    if not args_record.any_argument_supplied:
        post_vis_qs = apply_type_visibility_sync(target_type, source, info)
        bounded = bounded_rows(post_vis_qs, info, max_rows, trusted=trusted_max_rows)
        return wrap_async_queryset_adapter(bounded) if is_async_context else bounded

    post_vis_qs = apply_type_visibility_sync(
        target_type,
        source,
        info,
        policy=_LIST_ARGUMENT_VISIBILITY_POLICY,
    )
    orderset_class = None
    if args_record.order_by_supplied:
        post_order_qs, orderset_class = _apply_orderset_sync(
            target_type,
            post_vis_qs,
            args_record.order_by,
            info,
        )
    else:
        post_order_qs = post_vis_qs
        orderset_class = _orderset_class_for_target(target_type)

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
) -> Any:
    if not args_record.any_argument_supplied:
        post_vis_qs = await apply_type_visibility_async(target_type, source, info)
        bounded = bounded_rows(post_vis_qs, info, max_rows, trusted=trusted_max_rows)
        return wrap_async_queryset_adapter(bounded)

    post_vis_qs = await apply_type_visibility_async(
        target_type,
        source,
        info,
        policy=_LIST_ARGUMENT_VISIBILITY_POLICY,
    )
    orderset_class = None
    if args_record.order_by_supplied:
        post_order_qs, orderset_class = await _apply_orderset_async(
            target_type,
            post_vis_qs,
            args_record.order_by,
            info,
        )
    else:
        post_order_qs = post_vis_qs
        orderset_class = _orderset_class_for_target(target_type)

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
    _validate_djangotype_target(target_type, resolver, field="DjangoListField")
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
            _, info = _resolver_root_and_info(args, kwargs)
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
            qs = initial_queryset(target_type)
            if in_async_context():
                return _execute_queryset_pipeline_async(
                    target_type,
                    qs,
                    info,
                    args_record,
                    max_rows,
                    trusted_max_rows,
                )
            return _execute_queryset_pipeline_sync(
                target_type,
                qs,
                info,
                args_record,
                max_rows,
                trusted_max_rows,
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
                    target_type=target_type,
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
                    )
                await _handle_non_queryset_rejections_async(
                    source,
                    args_record,
                    info,
                    target_type=target_type,
                )
                return await bounded_rows_async(
                    source,
                    info,
                    max_rows,
                    trusted=trusted_max_rows,
                    offset=args_record.offset,
                    requested_limit=args_record.limit,
                )
        else:

            def _wrap(
                *args: Any,
                offset: Any = None,
                limit: Any = None,
                order_by: Any = strawberry.UNSET,
                **kwargs: Any,
            ) -> Any:
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
                        is_async_context=in_async_context(),
                    )
                _handle_non_queryset_rejections_sync(
                    args_record,
                    info,
                    target_type=target_type,
                )
                return bounded_rows(
                    source,
                    info,
                    max_rows,
                    trusted=trusted_max_rows,
                    offset=args_record.offset,
                    requested_limit=args_record.limit,
                )

        wrapped = _wrap

    signature, annotations = _synthesized_list_signature(target_type)
    wrapped.__signature__ = signature
    wrapped.__annotations__ = annotations

    return strawberry.field(
        resolver=wrapped,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
