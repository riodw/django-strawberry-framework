"""Finalization lifecycle for collected ``DjangoType`` classes."""

from __future__ import annotations

import strawberry

from ..exceptions import ConfigurationError
from ..registry import registry
from .converters import resolved_relation_annotation
from .relations import PendingRelation
from .relay import (
    _check_composite_pk_for_relay_node,
    apply_interfaces,
    implements_relay_node,
    install_relay_node_resolvers,
)
from .resolvers import _attach_relation_resolvers


def _format_unresolved_targets_error(unresolved: list[PendingRelation]) -> str:
    """Return the canonical unresolved relation target error message.

    Sibling convention: ``types/base.py:_format_unknown_fields_error`` owns the
    other consumer-surface ``Meta.fields`` / ``Meta.exclude`` / ``Meta.optimizer_hints``
    error strings. If consumer-surface ``Meta.*`` keys are renamed or supplemented,
    update both formatters together.
    """
    lines = []
    for pending in unresolved:
        lines.append(
            f"  - {pending.source_model.__name__}.{pending.field_name} -> "
            f"{pending.related_model.__name__} (no registered DjangoType)",
        )
    body = "\n".join(lines)
    return (
        "Cannot finalize Django types: the following relation targets are unresolved.\n"
        f"{body}\n\n"
        "Declare a DjangoType for each unresolved target model, or exclude these "
        "relation fields via Meta.exclude / Meta.fields."
    )


def finalize_django_types() -> None:
    """Resolve pending relations, attach resolvers, and finalize collected types.

    Phase 1 is failure-atomic: unresolved-target detection completes before
    mutating any class object. Phase 2 resolver attachment and Phase 3
    ``strawberry.type(...)`` calls mutate classes in place; a Strawberry-side
    failure there requires ``registry.clear()`` and fresh class recreation.

    Phase 2.5 (between Phase 2 and Phase 3) applies declared interfaces to
    ``cls.__bases__``, gates Relay-node-declared classes against composite
    primary keys, and injects the four ``resolve_*`` defaults that
    ``relay.Node`` would otherwise inherit from the upstream Strawberry
    interface. Runs before Phase 3 so the ``strawberry.type(...)`` decorator
    sees the mutated bases and the injected classmethods at decoration time.
    """
    if registry.is_finalized():
        return

    # TODO(spec-014-meta_primary-0_0_6.md Slice 3): run the primary-ambiguity
    # audit here, after the finalized guard and before pending relation
    # resolution, so ambiguous multi-type models fail before "unresolved target".
    # Pseudo:
    # - walk registry.models_with_multiple_types().
    # - collect models where registry.primary_for(model) is None, paired with
    #   registry.types_for(model) for the error body.
    # - raise ConfigurationError with every model/type and the
    #   "Declare Meta.primary = True on exactly one..." guidance.
    unresolved: list[PendingRelation] = []
    resolved: list[tuple[PendingRelation, type]] = []
    consumer_authored: list[PendingRelation] = []
    for pending in registry.iter_pending_relations():
        definition = registry.get_definition(pending.source_type)
        if definition is not None and pending.field_name in definition.consumer_authored_fields:
            consumer_authored.append(pending)
            continue
        target_type = registry.get(pending.related_model)
        if target_type is None:
            unresolved.append(pending)
            continue
        resolved.append((pending, target_type))

    if unresolved:
        raise ConfigurationError(_format_unresolved_targets_error(unresolved))

    resolved_pending = [*consumer_authored]
    for pending, target_type in resolved:
        pending.source_type.__annotations__[pending.field_name] = resolved_relation_annotation(
            pending.django_field,
            target_type,
        )
        resolved_pending.append(pending)
    registry.discard_pending(resolved_pending)

    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        _attach_relation_resolvers(
            type_cls,
            definition.selected_fields,
            skip_field_names=definition.consumer_assigned_relation_fields,
        )

    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        # ``apply_interfaces`` is the only step that depends on a non-empty
        # ``Meta.interfaces`` tuple. The Relay-node gate and resolver injection
        # are keyed off the resolved MRO (``implements_relay_node``) so they
        # also catch consumers who wrote ``class Foo(DjangoType, relay.Node)``
        # directly without ``Meta.interfaces`` (review feedback
        # ``feedback.md`` § High "Direct relay.Node inheritance bypasses Relay
        # finalization").
        if definition.interfaces:
            apply_interfaces(type_cls, definition)
        if implements_relay_node(type_cls):
            _check_composite_pk_for_relay_node(type_cls)
            install_relay_node_resolvers(type_cls)

    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        strawberry.type(type_cls, name=definition.name, description=definition.description)
        definition.finalized = True

    registry.mark_finalized()
