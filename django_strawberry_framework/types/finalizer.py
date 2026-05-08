"""Finalization lifecycle for collected ``DjangoType`` classes."""

from __future__ import annotations

import strawberry

from ..exceptions import ConfigurationError
from ..registry import registry
from .converters import resolved_relation_annotation
from .relations import PendingRelation
from .resolvers import _attach_relation_resolvers


def _format_unresolved_targets_error(unresolved: list[PendingRelation]) -> str:
    """Return the canonical unresolved relation target error message."""
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
    """
    if registry.is_finalized():
        return

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
    # TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
    # insert Phase 2.5 here: apply ``definition.interfaces`` to
    # ``type_cls.__bases__``, surface incompatible interfaces as
    # ConfigurationError, reject composite-pk Relay nodes, and install Relay
    # ``resolve_*`` defaults before Strawberry decorates the class.

    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        strawberry.type(type_cls, name=definition.name, description=definition.description)
        definition.finalized = True

    registry.mark_finalized()
