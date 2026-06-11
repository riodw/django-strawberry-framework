"""``DjangoType`` - Meta-class-driven Django-model-to-Strawberry-type adapter.

Consumer surface::

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = "__all__"

A nested ``Meta`` class declares the model and (optionally) ``fields``,
``exclude``, ``name``, ``description``, ``optimizer_hints``,
``interfaces``, ``nullable_overrides``, and ``required_overrides``.
Subclassing
triggers the collection pipeline, which:

1. Detects whether the subclass declares its own ``Meta``. Intermediate
   abstract subclasses without ``Meta`` are skipped so consumers can
   layer their own bases on top of ``DjangoType``.
2. Validates ``Meta`` (required Django model class, supported option
   shapes, ``fields``/``exclude`` exclusivity, deferred-key rejection,
   relation-only optimizer hints, and interfaces).
3. Selects Django fields and builds a ``DjangoTypeDefinition``.
4. Synthesizes scalar annotations and records unresolved relations as
   pending records.
5. Registers the model/type pair for a later ``finalize_django_types()``
   pass.
"""

import functools
import inspect
import re
import typing
from collections.abc import Callable, Mapping, Sequence
from typing import Annotated, Any, ClassVar, NamedTuple

from django.db import models
from strawberry import relay
from strawberry.relay.types import NodeIDPrivate
from strawberry.types.field import StrawberryField

from ..exceptions import ConfigurationError
from ..optimizer.field_meta import FieldMeta
from ..optimizer.hints import OptimizerHint
from ..registry import registry
from ..utils.strings import snake_case
from .converters import convert_scalar
from .definition import DjangoTypeDefinition
from .relations import PendingRelation, PendingRelationAnnotation
from .relay import install_is_type_of

DEFERRED_META_KEYS: frozenset[str] = frozenset(
    {"aggregate_class", "fields_class", "search_fields"},
)

ALLOWED_META_KEYS: frozenset[str] = frozenset(
    {
        "connection",
        "description",
        "exclude",
        "fields",
        "filterset_class",
        "globalid_strategy",
        "interfaces",
        "model",
        "name",
        "nullable_overrides",
        "optimizer_hints",
        "orderset_class",
        "primary",
        "required_overrides",
    },
)
# ``nullable_overrides`` / ``required_overrides`` (spec-029 Decision 6),
# ``connection`` (spec-030 Decision 8), and ``globalid_strategy`` (spec-031
# Decision 6) are net-new ALLOWED keys, NOT DEFERRED_META_KEYS promotions -
# each one's feature ships in the same card that adds it, so they were never
# reserved-but-nonfunctional. DEFERRED_META_KEYS stays unchanged.

# TODO(spec-032-full_relay-0_0_9 Slice 3): Add ``"relation_shapes"`` as the
# next net-new ALLOWED key (same rule as above - NOT a deferred promotion),
# validated by ``_validate_relation_shapes(meta, value, relay_shaped,
# consumer_authored_fields)`` modeled on ``_validate_connection`` and stored
# on ``DjangoTypeDefinition.relation_shapes`` (Decision 7).
# Type-creation validation contract:
#   - absent -> None (every eligible relation defaults to "both" at the
#     Phase-2.5 synthesis);
#   - non-dict / non-str keys / values outside {"list", "connection", "both"}
#     -> ConfigurationError naming the offending entry (typo guard);
#   - declared on a non-Relay-Node type (the precomputed ``relay_shaped``
#     bool ``Meta.connection`` uses) -> ConfigurationError with the
#     add-relay.Node-or-remove-the-key remediation;
#   - a key naming an unknown / non-relation / single-valued (forward FK /
#     OneToOne) / excluded model field -> ConfigurationError naming the field
#     and the reason (the ``Meta.optimizer_hints`` typo-guard precedent);
#   - a key naming a CONSUMER-AUTHORED relation (``consumer_authored_fields``)
#     -> ConfigurationError: overrides own the field's shape (Revision 3; the
#     implicit "both" default still skips consumer-authored relations
#     silently - only an explicit request fails loud).
# The target-is-Node-shaped check runs at FINALIZATION, where relation
# targets are settled (Decision 6) - not here.

# The valid string-strategy set and the package default are the single source
# of truth for the GlobalID-encoding strategy vocabulary: ``_validate_meta`` /
# ``_validate_globalid_strategy`` here, the Slice-2 encoder, and the Slice-3
# decode-shape enforcement all reference these names rather than re-typing the
# literals (spec-031 Decisions 4/5/6, build-031 "DRY-first rule"). ``callable``
# strategies are validated separately (arity + sync-ness), so they are not part
# of the string set.
STRING_GLOBALID_STRATEGIES: frozenset[str] = frozenset({"model", "type", "type+model"})
DEFAULT_GLOBALID_STRATEGY = "model"


def _validate_filterset_class(meta: type, filterset_class: Any) -> type | None:
    """Validate ``Meta.filterset_class`` is a package-``FilterSet`` subclass.

    Local import of ``FilterSet`` at function scope keeps ``types/base.py``
    free of a module-load cycle through ``filters.sets`` (which imports
    ``types.relay`` which imports ``types.base``). Validation runs at
    ``_validate_meta`` time - well after both modules have completed
    module load - so the local import resolves cheaply.

    Returns ``None`` when the meta does not declare ``filterset_class``;
    raises ``ConfigurationError`` for non-``FilterSet`` values.
    """
    if filterset_class is None:
        return None
    # In-function import: dodges the `types -> filters -> types` module-load
    # cycle. Do NOT hoist to module top.
    from ..filters.sets import FilterSet

    if not (isinstance(filterset_class, type) and issubclass(filterset_class, FilterSet)):
        raise ConfigurationError(
            f"{meta.model.__name__}.Meta.filterset_class must be a FilterSet subclass; "
            f"got {filterset_class!r}",
        )
    return filterset_class


def _validate_orderset_class(meta: type, orderset_class: Any) -> type | None:
    """Validate ``Meta.orderset_class`` is a package-``OrderSet`` subclass.

    Local import of ``OrderSet`` at function scope keeps ``types/base.py``
    free of a module-load cycle through ``orders.sets`` (which imports
    ``..types.definition`` under ``TYPE_CHECKING`` and would close the
    cycle at module-load time if the import were hoisted to module
    scope). Validation runs at ``_validate_meta`` time -- well after
    both modules have completed module load -- so the local import
    resolves cheaply.

    Returns ``None`` when the meta does not declare ``orderset_class``;
    raises ``ConfigurationError`` for non-``OrderSet`` values.
    """
    if orderset_class is None:
        return None
    # In-function import: dodges the `types -> orders -> types` module-load
    # cycle. Do NOT hoist to module top.
    from ..orders.sets import OrderSet

    if not (isinstance(orderset_class, type) and issubclass(orderset_class, OrderSet)):
        raise ConfigurationError(
            f"{meta.model.__name__}.Meta.orderset_class must be an OrderSet subclass; "
            f"got {orderset_class!r}",
        )
    return orderset_class


def _validate_connection(meta: type, connection: Any, relay_shaped: bool) -> dict | None:
    """Validate ``Meta.connection`` shape AND the Relay-Node requirement (spec-030 Decision 8).

    ``None``-short-circuits when unset; otherwise shape-checks the dict (for
    ``0.0.9`` the only recognized sub-key is ``{"total_count": bool}`` - unknown
    sub-keys and non-dict / non-bool values raise) and then enforces that the
    owning type is Relay-Node-shaped (a connection is only meaningful over a
    Relay-Node type). Returns the normalized dict, stored on
    ``DjangoTypeDefinition.connection`` and read by
    ``connection.py::_connection_type_for``.

    The Relay-Node gate takes the precomputed ``relay_shaped`` bool - the
    canonical ``_is_relay_shaped(cls, interfaces)`` value the caller
    (``_validate_meta``) computes once ``cls`` is in hand. That predicate is
    True for BOTH the ``Meta.interfaces`` tuple spelling AND direct inheritance
    (``class Foo(DjangoType, relay.Node)``), so it matches the
    ``DjangoConnectionField`` field guard - "Relay-shaped" means the same thing
    across the whole feature. Taking the bool (not ``interfaces``) keeps the
    predicate single-sourced and prevents the two surfaces drifting apart again.
    """
    if connection is None:
        return None
    if not isinstance(connection, dict):
        raise ConfigurationError(
            f"{meta.model.__name__}.Meta.connection must be a dict; got {connection!r}",
        )
    unknown = sorted(set(connection) - {"total_count"})
    if unknown:
        raise ConfigurationError(
            f"{meta.model.__name__}.Meta.connection has unknown sub-keys: {unknown}. "
            "Only 'total_count' is recognized in 0.0.9.",
        )
    if "total_count" in connection and not isinstance(connection["total_count"], bool):
        raise ConfigurationError(
            f"{meta.model.__name__}.Meta.connection['total_count'] must be a bool; "
            f"got {connection['total_count']!r}",
        )
    if not relay_shaped:
        raise ConfigurationError(
            f"{meta.model.__name__}.Meta.connection requires a Relay-Node-shaped type; "
            "add `relay.Node` to `Meta.interfaces` or inherit `relay.Node` directly.",
        )
    return connection


# The four positional parameters a ``callable`` GlobalID encoder must accept.
# Mirrors the ``resolve_typename(root, info)`` seam (spec-031 Decision 4): the
# callable runs at encode time, BEFORE ``resolve_id``, so it never receives
# ``node_id``. Named once so the validator's error text and the Slice-2 install
# closure stay in lockstep.
_GLOBALID_CALLABLE_PARAMS = (
    "type_cls",
    "model",
    "root",
    "info",
)


def _validate_globalid_strategy(
    meta: type | None,
    value: Any,
    relay_shaped: bool,
    *,
    source: str = "meta",
) -> str | Callable[..., str] | None:
    """Validate one ``globalid_strategy``-shaped value and return the normalized form.

    The single validator shared by BOTH the ``Meta.globalid_strategy`` path
    (via ``_validate_meta``) and the ``RELAY_GLOBALID_STRATEGY`` setting path
    (via ``types/relay.py::_resolve_globalid_strategy``) - spec-031 Decisions
    6/7's "one validator, two sources, source-specific error text" rule. The
    callable arity / sync-ness check lives here once so it is never duplicated
    across the two call sites.

    Structurally modeled on ``_validate_connection``: ``None``-short-circuits
    when unset; a string must be in ``STRING_GLOBALID_STRATEGIES`` (typo guard);
    a callable must accept the four positional ``_GLOBALID_CALLABLE_PARAMS`` and
    must NOT be ``async def`` (an opaque ``TypeError`` / coroutine per request is
    promoted to a build-time ``ConfigurationError``); any other type raises.

    ``source`` selects the error framing: ``"meta"`` (the default) names the
    offending type via ``meta.model.__name__`` and enforces the
    Relay-Node-shape gate; ``"setting"`` names ``RELAY_GLOBALID_STRATEGY`` and
    skips the gate (the per-type gate already ran at type creation, so the
    setting path passes ``relay_shaped=True`` and ``meta=None``).
    """
    if value is None:
        return None
    is_meta = source == "meta"
    subject = (
        f"{meta.model.__name__}.Meta.globalid_strategy" if is_meta else "RELAY_GLOBALID_STRATEGY"
    )
    if isinstance(value, str):
        if value not in STRING_GLOBALID_STRATEGIES:
            raise ConfigurationError(
                f"{subject} got unknown strategy {value!r}; "
                f"valid strategies are {sorted(STRING_GLOBALID_STRATEGIES)} or a callable.",
            )
        normalized: str | Callable[..., str] = value
    elif callable(value):
        _validate_globalid_callable(subject, value)
        normalized = value
    else:
        raise ConfigurationError(
            f"{subject} must be one of {sorted(STRING_GLOBALID_STRATEGIES)} or a callable; "
            f"got {value!r}.",
        )
    # The Relay-Node-shape gate is a ``Meta``-only concern (the setting path's
    # per-type gate already ran at type creation); mirrors
    # ``_validate_connection``'s gate and remediation text.
    if is_meta and not relay_shaped:
        raise ConfigurationError(
            f"{subject} requires a Relay-Node-shaped type; "
            "add `relay.Node` to `Meta.interfaces` or inherit `relay.Node` directly.",
        )
    return normalized


def _is_async_globalid_callable(value: object) -> bool:
    """Return whether ``value`` is (or wraps) an async GlobalID encoder.

    ``inspect.iscoroutinefunction`` returns ``True`` only for the value it is
    handed directly - it does NOT see through two realistic wrapper shapes:

    1. A callable *instance* whose ``__call__`` is ``async def`` - the instance
       itself is not a coroutine function, so its ``__call__`` is checked too.
    2. A ``functools.partial`` around either of the above - ``iscoroutinefunction``
       only unwraps a partial whose ``.func`` is itself an ``async def`` function,
       NOT a partial around an async callable *instance*. So the partial's target
       is checked instead of the partial.

    A single ``.func`` hop reaches that target with no loop to bound: ``partial``
    flattens nested partials at construction (``partial(partial(f)).func is f``),
    so ``.func`` is never itself a ``partial`` and the traversal is provably
    depth-1. Either wrapper, left undetected, survives validation and only fails
    at the first ``types/relay.py::encode_typename`` call (a coroutine return that
    trips the non-``str`` guard plus an unawaited-coroutine warning) - exactly the
    request-time failure the build-time check exists to prevent.
    """
    target = value.func if isinstance(value, functools.partial) else value
    # Inspecting ``__call__``'s async-ness, not testing callability - so
    # ``callable()`` (what B004 suggests) is the wrong tool here.
    return inspect.iscoroutinefunction(target) or inspect.iscoroutinefunction(
        getattr(target, "__call__", None),  # noqa: B004
    )


def _validate_globalid_callable(subject: str, value: Callable[..., str]) -> None:
    """Reject a wrong-arity or async GlobalID encoder at validation time.

    ``inspect.signature`` must bind the four positional ``_GLOBALID_CALLABLE_PARAMS``
    and the encoder must be sync (spec-031 Decision 6).
    The sync-ness test (``_is_async_globalid_callable``) sees through callable
    instances with an ``async def __call__`` and ``functools.partial`` wrappers
    around either an ``async def`` function or such an instance - all of which
    ``inspect.iscoroutinefunction`` alone would miss, letting an async encoder
    survive to request time. A callable that survives both checks is returned to
    the caller untouched; the per-call non-``str`` return guard lives in the
    Slice-2 install closure.
    """
    if _is_async_globalid_callable(value):
        raise ConfigurationError(
            f"{subject} callable encoder must be sync; "
            f"got an `async def`. Expected `(type_cls, model, root, info) -> str`.",
        )
    try:
        inspect.signature(value).bind(*_GLOBALID_CALLABLE_PARAMS)
    except TypeError as exc:
        raise ConfigurationError(
            f"{subject} callable encoder must accept "
            f"`(type_cls, model, root, info) -> str`; got an incompatible signature ({exc}).",
        ) from exc


# Token-shaped NodeID matcher used by the string-form arm of
# ``_id_annotation_is_relay_node_id``. The ``(?:^|\.)`` anchor accepts both the
# qualified (``relay.NodeID[int]``) and unqualified (``NodeID[int]``) spellings
# while rejecting prefixed-substring lookalikes (``NotNodeID[int]``,
# ``MyNodeID[int]``). See ``_id_annotation_is_relay_node_id`` for the full
# string-vs-resolved rationale; the regex lives at module scope so the compile
# happens once at import time.
_NODEID_STRING_RE = re.compile(r"(?:^|\.)NodeID\[")


def _has_node_id_marker(hint: object) -> bool:
    """Return True when ``hint`` is ``Annotated[T, NodeIDPrivate()]``.

    In the installed Strawberry, ``relay.NodeID[T]`` IS
    ``typing.Annotated[T, NodeIDPrivate()]`` - the explicit ``Annotated``
    form and the ``relay.NodeID`` sugar collapse to the same shape, so
    ``typing.get_origin`` returns ``typing.Annotated`` for both and the
    ``NodeIDPrivate`` instance lives in ``typing.get_args(...)``'s
    metadata slot.
    """
    return typing.get_origin(hint) is Annotated and any(
        isinstance(arg, NodeIDPrivate) for arg in typing.get_args(hint)
    )


def _id_annotation_is_relay_node_id(cls: type) -> bool:
    r"""Return True when ``cls.__annotations__['id']`` is ``relay.NodeID[...]``.

    Reads ``cls.__annotations__`` directly - no ``typing.get_type_hints``
    call. The result does not depend on whether other annotations on the
    class resolve (an unrelated forward reference on a sibling attribute
    cannot mask the ``id`` annotation; pinned by
    ``tests/types/test_definition_order.py::test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted``),
    and the function's behavior is identical on every supported Python
    version (``typing.get_type_hints`` handles nested forward references
    differently across 3.10 vs 3.11+, which previously left a code branch
    reachable only on the newer interpreter - the no-``get_type_hints``
    rewrite eliminated the divergence).

    Two annotation forms are accepted:

    1. **String form** (``id: "relay.NodeID[int]"`` or
       ``id: "NodeID[int]"``, typical under
       ``from __future__ import annotations`` or any explicit string
       annotation). Matched against ``(?:^|\.)NodeID\[`` - qualified and
       unqualified token-shaped NodeID references pass; prefixed-substring
       lookalikes (``"NotNodeID[int]"``, ``"MyNodeID[int]"``) and
       non-NodeID typos (``"MissingType"``) are rejected. Downstream
       Strawberry schema construction is responsible for resolving the
       string to a real ``NodeID[T]`` annotation; this function only
       confirms the shape so the H1 collision guard can accept the
       escape hatch at class-creation time.
    2. **Resolved-object form** (``id: relay.NodeID[int]``, evaluated at
       class-creation time). Delegated to ``_has_node_id_marker`` which
       checks for ``Annotated[T, NodeIDPrivate()]``.

    Precondition: ``"id" in cls.__annotations__``. The only call site
    (the Relay-id collision guard in ``DjangoType.__init_subclass__``)
    already gates on ``has_id_annotation`` before invoking this function,
    so the subscript below cannot ``KeyError`` from real flow. A future
    caller that violates the precondition gets a loud ``KeyError`` rather
    than a misleading ``False`` return.
    """
    raw = cls.__annotations__["id"]
    if isinstance(raw, str):
        return bool(_NODEID_STRING_RE.search(raw))
    return _has_node_id_marker(raw)


def _is_relay_shaped(cls: type, interfaces: tuple[type, ...]) -> bool:
    """Return True when ``cls`` or any entry in ``interfaces`` is a Relay-Node-shaped type.

    Single source of truth for the predicate that drives both the H1
    Relay ``id`` collision guard at ``DjangoType.__init_subclass__`` and
    the synthesized-``id``-annotation suppression branch in
    ``_build_annotations``. Both call sites compute the same boolean
    from the same inputs at different timings (class-creation-time vs.
    annotation-synthesis-time); centralizing the predicate keeps the
    Relay-shape contract single-sited.
    """
    return any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)


class DjangoType:
    """Base class for Django-model-backed Strawberry GraphQL types."""

    _is_default_get_queryset: ClassVar[bool] = True

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Collect model/type metadata without finalizing the Strawberry type."""
        super().__init_subclass__(**kwargs)
        # The ``_is_default_get_queryset`` sentinel must be stamped BEFORE the
        # ``meta is None`` early-return and the finalized-registry guard so an
        # abstract base that overrides ``get_queryset`` without declaring Meta
        # still flips the flag - concrete subclasses inheriting from it then
        # report ``has_custom_get_queryset() is True`` correctly. Pinned by
        # ``test_has_custom_get_queryset_inherits_through_abstract_base_without_meta``.
        has_custom_get_queryset = _detect_custom_get_queryset(cls)
        cls._is_default_get_queryset = not has_custom_get_queryset
        meta = cls.__dict__.get("Meta")
        if meta is None:
            return
        if registry.is_finalized():
            raise ConfigurationError(
                f"finalize_django_types() already ran; cannot register {cls.__name__} "
                "after finalization. Call registry.clear() first if this is a test.",
            )
        validated = _validate_meta(cls, meta)
        fields = _select_fields(meta.model, validated.fields_spec, validated.exclude_spec)
        _validate_optimizer_hints(validated.optimizer_hints, fields, model=meta.model)

        field_map = {snake_case(f.name): FieldMeta.from_django_field(f) for f in fields}
        consumer_annotations = dict(cls.__annotations__)
        consumer_annotated_relation_fields = frozenset(
            field.name
            for field in fields
            if field.is_relation and field.name in consumer_annotations
        )
        consumer_annotated_scalar_fields = frozenset(
            field.name
            for field in fields
            if not field.is_relation and field.name in consumer_annotations
        )
        consumer_assigned_relation_fields, consumer_assigned_scalar_fields = (
            _consumer_assigned_fields(
                cls,
                fields,
            )
        )
        # Four-corner consumer-override contract: relation/scalar x annotation/
        # assignment. Full enumeration of the contract lives on the
        # ``_consumer_assigned_fields`` docstring; this union is the single
        # short-circuit input read by ``_build_annotations`` to skip
        # auto-synthesis for any consumer-authored name on either branch.
        consumer_authored_fields = frozenset(
            {
                *consumer_annotated_relation_fields,
                *consumer_annotated_scalar_fields,
                *consumer_assigned_relation_fields,
                *consumer_assigned_scalar_fields,
            },
        )
        relay_shaped = _is_relay_shaped(cls, validated.interfaces)
        _validate_nullability_override_targets(
            model=meta.model,
            selected_fields=fields,
            consumer_authored_fields=consumer_authored_fields,
            relay_shaped=relay_shaped,
            nullable_overrides=validated.nullable_overrides,
            required_overrides=validated.required_overrides,
        )
        if relay_shaped:
            has_id_assignment = isinstance(cls.__dict__.get("id"), StrawberryField)
            has_id_annotation = "id" in cls.__annotations__
            if has_id_assignment:
                raise ConfigurationError(
                    f"{cls.__name__}: cannot override the id field on a "
                    "relay.Node-shaped type with an assigned strawberry.field. "
                    "Use @classmethod resolve_id for a custom id resolver, "
                    "id: relay.NodeID[<pk_type>] for a custom id annotation, "
                    "or declare a resolver-backed sibling field - e.g., "
                    "`@strawberry.field(description=...) def display_id(self) -> "
                    "strawberry.ID: return str(self.pk)` - if you only need "
                    "GraphQL field-level metadata on a custom identifier "
                    "(a metadata-only sibling without a resolver builds but "
                    "fails at query time); "
                    "or remove relay.Node from Meta.interfaces.",
                )
            if has_id_annotation and not _id_annotation_is_relay_node_id(cls):
                raise ConfigurationError(
                    f"{cls.__name__}: cannot override the id field on a "
                    "relay.Node-shaped type without using strawberry.relay.NodeID[...]. "
                    "The Relay interface supplies id: GlobalID! - declare the id "
                    "field via relay.NodeID[<pk_type>] if you need a different id "
                    "shape, or remove relay.Node from Meta.interfaces.",
                )
        synthesized, pending = _build_annotations(
            cls,
            fields,
            source_model=meta.model,
            field_map=field_map,
            consumer_authored_fields=consumer_authored_fields,
            interfaces=validated.interfaces,
            nullable_overrides=validated.nullable_overrides,
            required_overrides=validated.required_overrides,
        )
        definition = DjangoTypeDefinition(
            origin=cls,
            model=meta.model,
            name=getattr(meta, "name", None),
            description=getattr(meta, "description", None),
            fields_spec=validated.fields_spec,
            exclude_spec=validated.exclude_spec,
            selected_fields=tuple(fields),
            field_map=field_map,
            optimizer_hints=validated.optimizer_hints,
            has_custom_get_queryset=has_custom_get_queryset,
            consumer_authored_fields=consumer_authored_fields,
            consumer_annotated_relation_fields=consumer_annotated_relation_fields,
            consumer_annotated_scalar_fields=consumer_annotated_scalar_fields,
            consumer_assigned_relation_fields=consumer_assigned_relation_fields,
            consumer_assigned_scalar_fields=consumer_assigned_scalar_fields,
            interfaces=validated.interfaces,
            primary=validated.primary,
            filterset_class=validated.filterset_class,
            orderset_class=validated.orderset_class,
            connection=validated.connection,
            globalid_strategy=validated.globalid_strategy,
            # TODO(spec-032-full_relay-0_0_9 Slice 3): Pass
            # ``relation_shapes=validated.relation_shapes`` once the meta
            # validator and the definition slot exist (Decision 7).
        )
        registry.register_with_definition(meta.model, cls, definition, primary=validated.primary)
        for pending_relation in pending:
            registry.add_pending_relation(pending_relation)
        cls.__annotations__ = {**synthesized, **consumer_annotations}
        cls.__django_strawberry_definition__ = definition
        install_is_type_of(cls)

    @classmethod
    def get_queryset(
        cls,
        queryset: models.QuerySet,
        info: Any,  # noqa: ARG003
        **kwargs: Any,
    ) -> models.QuerySet:
        """Default identity hook.

        Subclasses override this to scope visibility (permissions,
        multi-tenancy, soft-delete). The optimizer detects overrides via
        ``has_custom_get_queryset`` and downgrades ``select_related`` to
        ``Prefetch`` so visibility filters apply across joins.
        """
        return queryset

    @classmethod
    def has_custom_get_queryset(cls) -> bool:
        """Return ``True`` if this subclass (or any intermediate base) overrides ``get_queryset``.

        Used by ``DjangoOptimizerExtension`` to decide whether a related-
        field traversal should be downgraded to a ``Prefetch``.

        Implementation: ``__init_subclass__`` flips
        ``_is_default_get_queryset`` to ``False`` at class-creation time
        when the subclass declares its own ``get_queryset``; this method
        returns the negated flag for a constant-time attribute read.
        Inheritance walks naturally - a subclass without its own
        ``get_queryset`` whose parent declared one inherits the parent's
        ``False`` sentinel through the class hierarchy.
        """
        definition = getattr(cls, "__django_strawberry_definition__", None)
        if definition is None:
            return not cls._is_default_get_queryset
        return definition.has_custom_get_queryset


def _detect_custom_get_queryset(cls: type) -> bool:
    """Return whether ``cls`` or an intermediate base overrides ``get_queryset``."""
    for base in cls.__mro__:
        if base is DjangoType:
            return False
        if "get_queryset" in base.__dict__:
            return True
    return False


def _normalize_fields_spec(value: Any) -> tuple[str, ...] | str | None:
    """Normalize ``Meta.fields`` for storage on ``DjangoTypeDefinition``."""
    if value is None or value == "__all__":
        return value
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ConfigurationError(
            "Meta.fields must be '__all__' or a non-string sequence of field names",
        )
    return tuple(value)


def _normalize_sequence_spec(value: Any) -> tuple[str, ...] | None:
    """Normalize optional sequence specs for storage on ``DjangoTypeDefinition``."""
    if value is None:
        return None
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ConfigurationError("Meta.exclude must be a non-string sequence of field names")
    return tuple(value)


def _consumer_assigned_fields(
    cls: type,
    fields: tuple[Any, ...],
) -> tuple[frozenset[str], frozenset[str]]:
    """Return (relation, scalar) names assigned to explicit Strawberry field objects.

    One of four collection sites that together pin the consumer-override
    contract for ``DjangoType``. The four corners are:

    - **relation x annotation** - ``consumer_annotated_relation_fields``,
      collected at ``DjangoType.__init_subclass__`` by walking
      ``cls.__annotations__`` for names that match a selected relation
      field. Honours a consumer-written ``items: list["AdminItemType"]``-
      style annotation.
    - **relation x assigned** - ``consumer_assigned_relation_fields``,
      this function's first return value. Honours a consumer-written
      ``items = strawberry.field(resolver=...)`` assignment on a relation
      column.
    - **scalar x annotation** - ``consumer_annotated_scalar_fields``,
      collected in the same ``__init_subclass__`` walk. Honours a
      consumer-written ``description: int``-style annotation override on
      a scalar column.
    - **scalar x assigned** - ``consumer_assigned_scalar_fields``, this
      function's second return value. Honours a consumer-written
      ``description = strawberry.field(resolver=...)`` assignment on a
      scalar column.

    The four sets are stored on ``DjangoTypeDefinition`` as the
    introspection surface. Their union, ``consumer_authored_fields``, is
    the single short-circuit input that ``_build_annotations`` reads at
    its relation branch and its scalar branch to skip auto-synthesis for
    any name the consumer authored.

    Walks every selected Django field, not just relations. A consumer
    who writes ``name = strawberry.field(resolver=...)`` on a scalar
    column gets the same treatment as the relation case: their
    Strawberry field object is preserved and ``_build_annotations``
    skips synthesizing an annotation for that name. Any non-
    ``StrawberryField`` shadow of a Django field name raises the same
    ``ConfigurationError`` shape so the failure mode is consistent
    across scalar and relation columns.
    """
    relation_assigned: set[str] = set()
    scalar_assigned: set[str] = set()
    class_dict = cls.__dict__
    for field in fields:
        if field.name not in class_dict:
            continue
        value = class_dict[field.name]
        if isinstance(value, StrawberryField):
            if field.is_relation:
                relation_assigned.add(field.name)
            else:
                scalar_assigned.add(field.name)
            continue
        kind = "relation" if field.is_relation else "scalar"
        raise ConfigurationError(
            f"{cls.__name__}.{field.name} shadows a Django {kind} field with an unsupported "
            "class attribute. Use a type annotation for type overrides, or use "
            "strawberry.field(resolver=...) / @strawberry.field for resolver overrides.",
        )
    return frozenset(relation_assigned), frozenset(scalar_assigned)


def _meta_optimizer_hints(meta: type) -> dict[str, Any]:
    """Return ``meta.optimizer_hints`` as a dict, or ``{}`` when unset.

    Centralizes the shape guard used across ``__init_subclass__`` and the
    validators so non-mapping declarations fail before hint keys or
    values are inspected.
    """
    value = getattr(meta, "optimizer_hints", None)
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ConfigurationError(
            f"{meta.model.__name__}.Meta.optimizer_hints must be a mapping of field names to OptimizerHint "
            f"instances, got {type(value).__name__}.",
        )
    return dict(value)


def _format_unknown_fields_error(
    *,
    model: type,
    attr: str,
    unknown: list[str],
    available: set[str],
) -> str:
    """Return the standard "unknown fields ... Available: ..." error message.

    Used by every validator that points at a typo in ``Meta.fields``,
    ``Meta.exclude``, or ``Meta.optimizer_hints``.  Centralizing the
    format keeps the consumer-visible error shape consistent across
    typo-guard sites.
    """
    return f"{model.__name__}.Meta.{attr} names unknown fields: {unknown}. Available: {sorted(available)}."


_INTERFACES_SHAPE_ERROR_LEAD_IN = (
    "Meta.interfaces must be a tuple/list of Strawberry interface classes "
    "or a single interface class"
)


def _interfaces_shape_error(meta: type, got_suffix: str) -> str:
    """Format the top-level ``Meta.interfaces`` shape-rejection message.

    Both raise sites (string-typed raw, other non-sequence raw) share the
    long lead-in defined in ``_INTERFACES_SHAPE_ERROR_LEAD_IN``; this
    helper localizes the wording so the two sites cannot drift.
    """
    return f"{meta.model.__name__}.{_INTERFACES_SHAPE_ERROR_LEAD_IN}, got {got_suffix}."


def _validate_interfaces(meta: type) -> tuple[type, ...]:
    """Validate and normalize ``Meta.interfaces`` per Decision 4.

    Returns a normalized ``tuple[type, ...]`` ready to pass through to
    ``DjangoTypeDefinition.interfaces``. Returns ``()`` when the key is
    absent or set to an empty tuple/list (Decision 4,
    spec-011 #"An empty tuple is the same as not declaring").

    Validation rules (spec-011 #"may be a tuple/list of interface classes"):

    - Accepts a tuple/list of interface classes, or a single real
      Strawberry interface class (e.g. ``interfaces = relay.Node``).
    - Rejects strings, sets, generators, dicts, ints, and other
      non-sequence values.
    - Each entry must satisfy
      ``hasattr(entry, "__strawberry_definition__") and
      entry.__strawberry_definition__.is_interface``.
    - Rejects string entries (no lazy/forward-reference lookup).
    - Rejects ``DjangoType`` self-reference and other ``DjangoType``
      subclasses.
    - Rejects duplicates.

    The composite-pk constraint and ``relay.Node`` MRO inspection live
    in ``finalize_django_types()`` (Relay finalization phase); this
    helper only validates the shape and contents of the
    ``Meta.interfaces`` tuple itself.
    """
    raw = getattr(meta, "interfaces", None)
    if raw is None:
        return ()
    if isinstance(raw, str):
        raise ConfigurationError(_interfaces_shape_error(meta, "a string"))
    if isinstance(raw, type):
        entries: tuple[type, ...] = (raw,)
    elif isinstance(raw, (tuple, list)):
        entries = tuple(raw)
    else:
        raise ConfigurationError(_interfaces_shape_error(meta, type(raw).__name__))
    if entries == ():
        return ()
    seen_ids: set[int] = set()
    duplicates: list[str] = []
    for entry in entries:
        if isinstance(entry, str):
            raise ConfigurationError(
                f"{meta.model.__name__}.Meta.interfaces must contain interface classes, "
                f"not strings (got {entry!r}). Lazy/forward-reference interface lookup is "
                "deferred (no current spec home).",
            )
        if not isinstance(entry, type):
            raise ConfigurationError(
                f"{meta.model.__name__}.Meta.interfaces must contain interface classes, got {entry!r}.",
            )
        if issubclass(entry, DjangoType):
            raise ConfigurationError(
                f"{meta.model.__name__}.Meta.interfaces may not contain DjangoType or "
                f"DjangoType subclasses (got {entry.__name__}). DjangoType is not a "
                "Strawberry interface.",
            )
        # TODO(spec-032-full_relay-0_0_9 Slice 1): Named-helper rejection branch
        # fires BEFORE the generic one below (Decision 8). Each of the six
        # strawberry.relay NON-interface helpers - GlobalID (a scalar-like id
        # wrapper), NodeID (an annotation helper), Connection / ListConnection
        # (generic output types; remediation names Meta.connection /
        # DjangoConnectionField), Edge (machinery-instantiated output type),
        # PageInfo (a generated pagination type) - raises ConfigurationError
        # NAMING the helper, what it actually is, and what the consumer
        # probably meant (relay.Node). All six already fail through the
        # generic branch; the named branch upgrades the message only.
        # Pseudocode:
        #   named = _RELAY_NON_INTERFACE_HELPERS.get(entry)  # noqa: ERA001
        #   if named is not None:
        #       raise ConfigurationError(named.message(meta, entry))  # noqa: ERA001
        definition = getattr(entry, "__strawberry_definition__", None)
        if definition is None or not getattr(definition, "is_interface", False):
            raise ConfigurationError(
                f"{meta.model.__name__}.Meta.interfaces entry {entry.__name__} is not a "
                "Strawberry interface. Use @strawberry.interface or one of the "
                "strawberry.relay interface classes.",
            )
        entry_id = id(entry)
        if entry_id in seen_ids:
            duplicates.append(entry.__name__)
        else:
            seen_ids.add(entry_id)
    if duplicates:
        raise ConfigurationError(
            f"{meta.model.__name__}.Meta.interfaces contains duplicate entries: {sorted(duplicates)}.",
        )
    return entries


class _ValidatedMeta(NamedTuple):
    """Single-pass snapshot of validated ``Meta`` attributes.

    Threading the validated values back from ``_validate_meta`` keeps the
    caller from re-reading ``getattr(meta, ...)`` for the same keys and
    avoids re-running the shape gates (``_normalize_fields_spec``,
    ``_normalize_sequence_spec``, ``_meta_optimizer_hints``) at multiple
    sites in ``__init_subclass__``.
    """

    interfaces: tuple[type, ...]
    primary: bool
    optimizer_hints: dict[str, Any]
    fields_spec: tuple[str, ...] | str | None
    exclude_spec: tuple[str, ...] | None
    filterset_class: type | None
    orderset_class: type | None
    connection: dict | None
    globalid_strategy: str | Callable[..., str] | None
    nullable_overrides: frozenset[str]
    required_overrides: frozenset[str]


def _validate_meta(cls: type, meta: type) -> _ValidatedMeta:
    """Validate a ``DjangoType`` subclass's nested ``Meta`` class.

    Takes ``cls`` (the class object, available at ``__init_subclass__`` time)
    so the Relay-shape predicate (``_is_relay_shaped``) the ``Meta.connection``
    gate needs can see direct ``relay.Node`` inheritance, not only the declared
    ``Meta.interfaces`` tuple.

    Validation order:

    1. ``Meta.model`` is required and must be a Django model class.
    2. ``fields`` and ``exclude`` are mutually exclusive.
    3. Any key in ``DEFERRED_META_KEYS`` raises with a clear message.
    4. Any non-dunder key on ``meta`` not in ``ALLOWED_META_KEYS |
       DEFERRED_META_KEYS`` raises (typo guard).
    5. ``fields``, ``exclude``, and ``optimizer_hints`` have supported
       declaration shapes before field selection or hint validation uses
       them.
    6. If ``Meta.interfaces`` is declared, validate it per
       ``_validate_interfaces`` (spec-011 Decision 4).
    7. ``Meta.connection`` (if declared) is shape-checked and gated to
       Relay-Node-shaped types via the ``relay_shaped`` bool derived from
       ``cls`` + the validated interfaces, so the
       gate accepts the same shapes as the ``DjangoConnectionField`` field guard.

    Returns:
        A ``_ValidatedMeta`` snapshot bundling the validated interfaces
        tuple, the ``primary`` bool, the normalized ``optimizer_hints``
        dict, and the normalized ``fields``/``exclude`` specs. The caller
        threads these through to ``DjangoTypeDefinition`` and
        ``_validate_optimizer_hints`` so the shape gates run exactly once
        per class definition.

    Raises:
        ConfigurationError: any of the above violations.
    """
    model = getattr(meta, "model", None)
    if model is None:
        raise ConfigurationError("Meta.model is required")
    if not isinstance(model, type) or not issubclass(model, models.Model):
        raise ConfigurationError("Meta.model must be a Django model class")

    # ``meta.__dict__`` (this class's OWN keys only, no MRO walk) is
    # deliberate for the typo-guard below (the ``deferred`` / ``unknown``
    # checks): an unsupported key is flagged only when THIS ``Meta``
    # declares it, so a base ``Meta``'s already-validated keys are not
    # re-flagged on every subclass. This is the intentional counterpart to
    # the MRO-walking ``getattr`` check just below; the two differ on
    # purpose -- do not "unify" them.
    declared = {k for k in meta.__dict__ if not k.startswith("_")}

    # Use ``getattr(..., None) is not None`` rather than ``meta.__dict__``
    # membership so a child Meta inheriting ``fields`` from a base Meta
    # still trips the mutual-exclusion check when it declares ``exclude``
    # (and vice versa). ``fields = None`` (or ``exclude = None``)
    # remains "unset" - matches ``_normalize_fields_spec``'s treatment
    # of ``None`` and the broader convention that an explicit ``None``
    # means "no preference".
    has_fields = getattr(meta, "fields", None) is not None
    has_exclude = getattr(meta, "exclude", None) is not None
    if has_fields and has_exclude:
        raise ConfigurationError("Meta.fields and Meta.exclude are mutually exclusive")

    primary = getattr(meta, "primary", False)
    if not isinstance(primary, bool):
        raise ConfigurationError("Meta.primary must be a bool")

    deferred = sorted(declared & DEFERRED_META_KEYS)
    if deferred:
        raise ConfigurationError(
            f"Meta keys not supported yet: {deferred}. The feature that owns them has not shipped.",
        )

    unknown = sorted(declared - ALLOWED_META_KEYS - DEFERRED_META_KEYS)
    if unknown:
        raise ConfigurationError(f"Unknown Meta keys: {unknown}")

    fields_spec = _normalize_fields_spec(getattr(meta, "fields", None))
    exclude_spec = _normalize_sequence_spec(getattr(meta, "exclude", None))
    optimizer_hints = _meta_optimizer_hints(meta)
    interfaces = _validate_interfaces(meta)
    relay_shaped = _is_relay_shaped(cls, interfaces)
    filterset_class = _validate_filterset_class(meta, getattr(meta, "filterset_class", None))
    orderset_class = _validate_orderset_class(meta, getattr(meta, "orderset_class", None))
    connection = _validate_connection(meta, getattr(meta, "connection", None), relay_shaped)
    globalid_strategy = _validate_globalid_strategy(
        meta,
        getattr(meta, "globalid_strategy", None),
        relay_shaped,
    )
    # Override shape stage (spec-029 Decision 8 step 1): the two tuple-set
    # keys reuse the ``Meta.exclude`` non-string-sequence guard
    # (``_normalize_sequence_spec``), then normalize to ``frozenset``. The
    # both-sets collision is a shape-level contradiction visible from the raw
    # ``Meta`` alone (no model/field access needed), so it raises here rather
    # than in the target-validator. Target existence / scope checks
    # (unknown / excluded / consumer-authored / relation / Relay-pk) need the
    # selected fields and run later in ``_validate_nullability_override_targets``.
    nullable_overrides = frozenset(
        _normalize_sequence_spec(getattr(meta, "nullable_overrides", None)) or (),
    )
    required_overrides = frozenset(
        _normalize_sequence_spec(getattr(meta, "required_overrides", None)) or (),
    )
    both_sets_collision = sorted(nullable_overrides & required_overrides)
    if both_sets_collision:
        raise ConfigurationError(
            f"{meta.model.__name__}.Meta names {both_sets_collision} in both "
            "nullable_overrides and required_overrides; a field cannot be both "
            "forced-nullable and forced-required.",
        )

    return _ValidatedMeta(
        interfaces=interfaces,
        primary=primary,
        optimizer_hints=optimizer_hints,
        fields_spec=fields_spec,
        exclude_spec=exclude_spec,
        filterset_class=filterset_class,
        orderset_class=orderset_class,
        connection=connection,
        globalid_strategy=globalid_strategy,
        nullable_overrides=nullable_overrides,
        required_overrides=required_overrides,
    )


def _validate_optimizer_hints(hints: dict[str, Any], fields: tuple[Any, ...], model: type) -> None:
    """Validate ``Meta.optimizer_hints`` keys and values in one pass.

    Combines the field-surface and value checks in one place:

    1. Every hint key names a field on the model (typo guard).
    2. Every hint key is in the type's selected relation field set.
       Excluded fields and selected scalar fields would silently drop
       optimizer intent otherwise - the walker only reads hints after
       entering the relation branch.
    3. Every hint value is an ``OptimizerHint`` instance.

    Field-name error sites route through ``_format_unknown_fields_error``
    so the consumer-visible shape matches ``Meta.fields`` /
    ``Meta.exclude`` typo guards; value errors use a dedicated
    ``OptimizerHint`` message.

    Args:
        hints: The pre-normalized ``Meta.optimizer_hints`` dict (already
            shape-checked by ``_meta_optimizer_hints`` inside
            ``_validate_meta``). Empty dict short-circuits.
        fields: The Meta-filtered list of Django field objects produced
            by ``_select_fields``. Used to derive the selected relation
            field names so excluded or scalar fields with hints raise.
        model: The Django model whose ``_meta.get_fields()`` defines the
            valid hint key surface. Threaded from ``meta.model`` so the
            empty-``fields`` shape (e.g. ``Meta.exclude`` covering every
            field) is not fatal - earlier shapes inferred the model from
            ``fields[0].model`` and ``IndexError``'d here.
    """
    if not hints:
        return
    valid_field_names = {f.name for f in model._meta.get_fields()}
    selected_relation_names = {f.name for f in fields if f.is_relation}

    unknown_hint_fields = sorted(set(hints) - valid_field_names)
    if unknown_hint_fields:
        raise ConfigurationError(
            _format_unknown_fields_error(
                model=model,
                attr="optimizer_hints",
                unknown=unknown_hint_fields,
                available=valid_field_names,
            ),
        )
    excluded_hint_fields = sorted(set(hints) - selected_relation_names)
    if excluded_hint_fields:
        raise ConfigurationError(
            _format_unknown_fields_error(
                model=model,
                attr="optimizer_hints",
                unknown=excluded_hint_fields,
                available=selected_relation_names,
            ),
        )
    bad_values = sorted(k for k, v in hints.items() if not isinstance(v, OptimizerHint))
    if bad_values:
        raise ConfigurationError(
            f"optimizer_hints values must be OptimizerHint instances, "
            f"got non-OptimizerHint for: {bad_values}",
        )


def _validate_nullability_override_targets(
    *,
    model: type[models.Model],
    selected_fields: tuple[Any, ...],
    consumer_authored_fields: frozenset[str],
    relay_shaped: bool,
    nullable_overrides: frozenset[str],
    required_overrides: frozenset[str],
) -> None:
    """Reject every illegal ``nullable_overrides`` / ``required_overrides`` target.

    Stage 2 of the override validation flow (spec-029 Decision 8). Runs in
    ``__init_subclass__`` AFTER ``_select_fields`` + ``consumer_authored_fields``
    + the Relay-shape check, so the selected fields, the consumer-override set,
    and the Relay-pk identity all exist. The shape check + both-sets collision
    already ran earlier in ``_validate_meta``; this helper only validates the
    union of the two normalized sets against the model and selected fields.

    Two distinct name sets are derived as separate error paths so the
    ``Meta.exclude`` contract is not collapsed into "unknown": the model-wide
    names (``model._meta.get_fields()``) gate the *unknown-field* path, and the
    selected-field names gate the *excluded / not-selected* path. The unknown
    path routes through ``_format_unknown_fields_error`` so its consumer-visible
    shape matches the ``Meta.fields`` / ``Meta.exclude`` / ``Meta.optimizer_hints``
    typo guards.

    Check order: unknown -> excluded -> (consumer-authored / relation / Relay-pk).
    The last three operate on selected, known fields, so they run only after the
    first two have confirmed the name exists and is selected. Every failure
    raises ``ConfigurationError`` at type-creation time naming the offending
    field.

    Args:
        model: The Django model the type wraps; ``model._meta.get_fields()``
            defines the valid-field surface (unknown-field path) and
            ``model._meta.pk.name`` the Relay-suppressed pk identity.
        selected_fields: The Meta-filtered Django field objects from
            ``_select_fields`` - defines the selected name set (excluded path)
            and supplies ``field.is_relation`` for the relation-reject path.
        consumer_authored_fields: The four-corner consumer-override union; a
            name here already controls its own nullability via the annotation /
            ``strawberry.field`` assignment, so an override on it is rejected.
        relay_shaped: Whether the type participates in the Relay ``Node``
            interface; when ``True`` the suppressed pk's nullability is the
            interface's contract and cannot be overridden.
        nullable_overrides: Normalized ``Meta.nullable_overrides`` frozenset.
        required_overrides: Normalized ``Meta.required_overrides`` frozenset.

    Raises:
        ConfigurationError: any target is unknown / excluded / consumer-authored
            / a relation field / the Relay-suppressed pk.
    """
    targets = nullable_overrides | required_overrides
    if not targets:
        return
    model_field_names = {f.name for f in model._meta.get_fields()}
    unknown = sorted(targets - model_field_names)
    if unknown:
        raise ConfigurationError(
            _format_unknown_fields_error(
                model=model,
                attr="nullable_overrides/required_overrides",
                unknown=unknown,
                available=model_field_names,
            ),
        )
    selected_by_name = {f.name: f for f in selected_fields}
    excluded = sorted(targets - set(selected_by_name))
    if excluded:
        raise ConfigurationError(
            f"{model.__name__}.Meta nullable_overrides/required_overrides name fields not in "
            f"the selected set: {excluded}. The override targets a field that will not appear "
            "in the GraphQL type (excluded via Meta.exclude or absent from a subset Meta.fields); "
            "select the field or drop the override.",
        )
    relay_pk_name = model._meta.pk.name if relay_shaped else None
    for name in sorted(targets):
        if name in consumer_authored_fields:
            raise ConfigurationError(
                f"{model.__name__}.Meta nullable_overrides/required_overrides names "
                f"consumer-authored field {name!r}; a consumer annotation or strawberry.field "
                "assignment already controls its nullability. Drop the override and control "
                "nullability through the annotation instead.",
            )
        if name == relay_pk_name:
            raise ConfigurationError(
                f"{model.__name__}.Meta nullable_overrides/required_overrides names the "
                f"Relay-Node-suppressed pk {name!r}; the pk's nullability is the relay.Node "
                "interface's contract (id: GlobalID!), not the column's, and cannot be overridden.",
            )
        if selected_by_name[name].is_relation:
            raise ConfigurationError(
                f"{model.__name__}.Meta nullable_overrides/required_overrides names relation "
                f"field {name!r}; nullability overrides are scalar-only for now. Relation-field "
                "nullability override is deferred (see spec-029 Decision 10).",
            )


def _select_fields(
    model: type[models.Model],
    fields_spec: tuple[str, ...] | str | None,
    exclude_spec: tuple[str, ...] | None,
) -> tuple[Any, ...]:
    """Filter ``model._meta.get_fields()`` per ``Meta.fields`` / ``Meta.exclude``.

    Called once from ``DjangoType.__init_subclass__`` and the resulting
    list is reused by ``_build_annotations`` (in this module) and
    ``_attach_relation_resolvers`` (in ``types.resolvers``) so the field
    walk does not happen twice. Iteration order follows
    Django's ``_meta.get_fields()`` so the generated GraphQL type's field
    order matches Django's declared order, with reverse-side relations
    appended at the end.

    The caller threads ``fields_spec`` and ``exclude_spec`` from the
    ``_ValidatedMeta`` snapshot produced by ``_validate_meta`` so the
    shape gates (``_normalize_fields_spec`` / ``_normalize_sequence_spec``)
    run exactly once per class definition - matching the invariant the
    ``_ValidatedMeta`` docstring promises.

    Selection rules:

    - ``fields_spec == "__all__"`` (or both ``fields_spec`` /
      ``exclude_spec`` ``None``) -> every concrete + relation field.
    - ``fields_spec`` as a sequence -> only those names; unknown names raise.
    - ``exclude_spec`` as a sequence -> every field except those names;
      unknown names raise.

    Raises:
        ConfigurationError: ``Meta.fields`` or ``Meta.exclude`` names a
            field that does not exist on ``Meta.model``. The error names
            the model, the unknown values, and the available field set
            so typos surface loudly instead of silently dropping.
    """
    all_fields = list(model._meta.get_fields())
    all_names = [f.name for f in all_fields]
    valid_names = set(all_names)

    if fields_spec == "__all__" or (fields_spec is None and exclude_spec is None):
        selected_names = valid_names
    elif fields_spec is not None:
        unknown = sorted(set(fields_spec) - valid_names)
        if unknown:
            raise ConfigurationError(
                _format_unknown_fields_error(
                    model=model,
                    attr="fields",
                    unknown=unknown,
                    available=valid_names,
                ),
            )
        selected_names = set(fields_spec)
    else:
        unknown = sorted(set(exclude_spec) - valid_names)
        if unknown:
            raise ConfigurationError(
                _format_unknown_fields_error(
                    model=model,
                    attr="exclude",
                    unknown=unknown,
                    available=valid_names,
                ),
            )
        selected_names = valid_names - set(exclude_spec)

    return tuple(f for f in all_fields if f.name in selected_names)


def _build_annotations(
    cls: type,
    fields: tuple[Any, ...],
    *,
    source_model: type[models.Model],
    field_map: dict[str, FieldMeta],
    consumer_authored_fields: frozenset[str] = frozenset(),
    interfaces: tuple[type, ...] = (),
    nullable_overrides: frozenset[str] = frozenset(),
    required_overrides: frozenset[str] = frozenset(),
) -> tuple[dict[str, Any], list[PendingRelation]]:
    """Build the annotation dict the Strawberry type decorator consumes.

    Field-by-field dispatch: scalar entries in ``fields`` are routed
    through ``convert_scalar``. Auto-synthesized relation entries always
    record a ``PendingRelation`` and set the annotation to
    ``PendingRelationAnnotation``; ``finalize_django_types()`` resolves
    them through ``registry.get(...)`` after every type has registered
    so multi-type / primary semantics apply uniformly. Consumer-authored
    fields short-circuit out of the synthesis loop on both branches: a
    name in ``consumer_authored_fields`` skips relation deferral at the
    ``field.is_relation`` branch and skips ``convert_scalar`` at the
    scalar branch. See ``_consumer_assigned_fields`` for the four-corner
    override contract that populates ``consumer_authored_fields``. The
    caller pre-computes the field list with
    ``_select_fields(model, fields_spec, exclude_spec)`` (threading the
    validated specs from the ``_ValidatedMeta`` snapshot) so this function
    does not need ``meta``.

    When ``relay.Node`` appears in ``interfaces``, the primary-key field's
    synthesized scalar annotation is dropped from the returned dict so
    Strawberry's interface-supplied ``id: GlobalID!`` is not shadowed by a
    Django ``int`` field. The pk field stays in ``fields`` so the
    optimizer's ``DjangoTypeDefinition.field_map`` continues to see it as a
    connector column (spec-011 Decision 7 #"keeps every selected Django field including the primary key").

    Args:
        cls: The consumer-facing ``DjangoType`` subclass (its ``__name__``
            threads into ``convert_scalar`` so generated choice enums
            carry a stable name).
        fields: The Meta-filtered list of Django field objects.
        source_model: The Django model the type wraps. Used to resolve the
            primary-key attname when ``relay.Node`` suppression is active.
        consumer_authored_fields: Names of fields whose annotation /
            ``StrawberryField`` assignment is owned by the consumer. The
            synthesized annotation is skipped for these names so consumer
            overrides survive collection.
        interfaces: The validated ``Meta.interfaces`` tuple. When
            ``relay.Node`` is among them, the primary-key field's
            synthesized scalar annotation is suppressed so Strawberry's
            interface-supplied ``id: GlobalID!`` is not shadowed.
        nullable_overrides: Normalized ``Meta.nullable_overrides`` frozenset.
            A selected scalar field named here is forced to ``T | None``
            (``force_nullable=True`` into ``convert_scalar``) regardless of
            ``field.null``.
        required_overrides: Normalized ``Meta.required_overrides`` frozenset.
            A selected scalar field named here is forced to ``T``
            (``force_nullable=False``) regardless of ``field.null``. The two
            sets are validated disjoint and scalar-only upstream.

    Returns:
        A tuple of ``(annotations, pending_relations)``.

    Raises:
        ConfigurationError: an unsupported scalar field type is encountered
            (raised by ``convert_scalar``), or a selected relation has no
            concrete related model to map to a GraphQL type.
    """
    annotations: dict[str, Any] = {}
    pending: list[PendingRelation] = []
    # Suppress the synthesized scalar ``id`` annotation whenever the type will
    # participate in the Relay ``Node`` interface - either through
    # ``Meta.interfaces`` (the canonical path; includes both ``relay.Node``
    # directly and any ``@strawberry.interface`` that subclasses it) or
    # through direct inheritance (``class Foo(DjangoType, relay.Node)``).
    # Without these branches a Strawberry-native consumer would land in
    # Phase 3 ``strawberry.type(...)`` decoration with both the synthesized
    # ``id: int`` and the interface-supplied ``id: GlobalID!`` and the schema
    # build would blow up with ``NodeIDAnnotationError``.
    #
    # The interfaces tuple is checked with ``issubclass`` per entry rather
    # than an exact ``relay.Node in interfaces`` membership test:
    # ``_validate_interfaces`` guarantees every entry is a Strawberry
    # interface class, and a consumer subclass like
    # ``@strawberry.interface class CustomNode(relay.Node)`` is the
    # canonical way to extend Relay-Node behavior.
    suppress_pk_annotation = _is_relay_shaped(cls, interfaces)
    # ``pk_name`` (not ``pk_attname``): ``_meta.pk.name`` is the Django
    # field NAME, not the column attname. For a relation primary key
    # (``OneToOneField(primary_key=True)``) those differ - ``name="user"``
    # vs. ``attname="user_id"`` - and the comparison below is against
    # ``field.name`` so the NAME is what's needed. Naming it ``pk_attname``
    # would invite a future maintainer to reuse it in a
    # ``getattr(root, pk_attname)`` context, which would lazy-load the
    # related row for a relation pk.
    pk_name = source_model._meta.pk.name if suppress_pk_annotation else None
    for field in fields:
        if field.is_relation:
            if field.name in consumer_authored_fields:
                continue
            field_meta = field_map[snake_case(field.name)]
            if getattr(field, "related_model", None) is None:
                raise ConfigurationError(
                    f"{source_model.__name__}.{field.name} is a GenericForeignKey or other "
                    "relation without a concrete related model. It cannot be auto-mapped to "
                    "a single GraphQL type. Exclude it via Meta.exclude, or supply an "
                    "explicit annotation or resolver.",
                )
            # Always defer auto-synthesized relation annotations: the
            # consumer_authored short-circuit above leaves consumer overrides
            # alone, and every other relation field becomes a pending record
            # that ``finalize_django_types()`` resolves through
            # ``registry.get(...)`` (which returns the primary post-finalize,
            # or the single registered type when no primary was declared).
            # The earlier eager-bind branch froze the relation against
            # whichever type was already registered at ``__init_subclass__``
            # time, which mis-bound when a secondary was registered before
            # the primary (the import-order trap closed by spec-014 H1).
            pending.append(
                PendingRelation(
                    source_type=cls,
                    source_model=source_model,
                    field_name=field.name,
                    django_field=field,
                    related_model=field.related_model,
                    relation_kind=field_meta.relation_kind,
                    nullable=field_meta.nullable,
                ),
            )
            annotations[field.name] = PendingRelationAnnotation
        else:
            if field.name in consumer_authored_fields:
                # A consumer-assigned ``StrawberryField`` (or annotation) on a
                # scalar column wins over the auto-synthesized annotation so
                # ``strawberry.field(resolver=...)`` overrides survive
                # collection. Relation override symmetry: see the
                # ``field.is_relation`` branch above.
                continue
            if suppress_pk_annotation and field.name == pk_name:
                # ``relay.Node`` supplies ``id: GlobalID!`` via the interface;
                # dropping the synthesized scalar annotation here keeps the
                # Strawberry surface clean. The pk field stays in ``fields``
                # so the optimizer's field map still sees it as a connector
                # column (spec-011 Decision 7 #"keeps every selected Django field including the primary key").
                continue
            # Per-field nullability override tri-state (spec-029 Decision 7):
            # membership in ``nullable_overrides`` forces ``T | None``,
            # membership in ``required_overrides`` forces ``T``, and absence
            # from both leaves ``None`` so ``convert_scalar`` honors
            # ``field.null``. The two sets are validated to be disjoint and
            # scalar-only in ``_validate_nullability_override_targets`` before
            # this loop runs, so the elif is exhaustive and unambiguous.
            if field.name in nullable_overrides:
                force_nullable: bool | None = True
            elif field.name in required_overrides:
                force_nullable = False
            else:
                force_nullable = None
            annotations[field.name] = convert_scalar(
                field,
                cls.__name__,
                force_nullable=force_nullable,
            )
    return annotations, pending
