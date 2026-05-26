"""Finalization lifecycle for collected ``DjangoType`` classes.

``finalize_django_types()`` is the once-only build gate for the package's
``DjangoType`` registry. It runs four phases against every type collected
since the last ``registry.clear()`` and is the only place ``strawberry.type``
decoration touches a consumer-facing class:

- Phase 1 (failure-atomic): walk ``registry.iter_pending_relations()`` and
  classify each pending record as ``unresolved`` (no DjangoType registered
  for the target model), ``consumer_authored`` (consumer wrote their own
  annotation; defense-in-depth path), or ``resolved`` (target registered;
  rewrite the synthesized annotation via ``resolved_relation_annotation``).
  Any unresolved targets raise ``ConfigurationError`` BEFORE any class
  object is mutated, so a finalize() that detects a config error leaves
  every collected class intact for a re-call. The primary-ambiguity audit
  via ``_audit_primary_ambiguity`` runs at the top of Phase 1.
- Phase 2: ``_attach_relation_resolvers`` installs the framework's auto
  relation resolvers across every not-yet-finalized type.
- Phase 2.5: ``apply_interfaces`` injects ``Meta.interfaces`` entries into
  ``cls.__bases__``; types that resolve to ``relay.Node`` (either via
  ``Meta.interfaces`` or direct inheritance) are gated against composite
  primary keys and receive the four ``resolve_*`` defaults Strawberry's
  Relay interface expects. Runs before Phase 3 so the ``strawberry.type``
  decorator sees the mutated bases.
- Phase 3: ``strawberry.type(cls, name=..., description=...)`` decorates
  each type and sets ``definition.finalized = True``.

The function entry-guards on ``registry.is_finalized()`` at the top of
``finalize_django_types()`` so a second call is a no-op. The registry's
finalized flag flips only after every type's Phase 3 call returns, via
``registry.mark_finalized()`` as the last statement of
``finalize_django_types()``: a raise inside Phase 2, 2.5, or 3 leaves
the flag False and supports a fine-grained partial recovery on rerun.
The per-entry ``if definition.finalized: continue`` guards at the head
of each phase loop skip already-decorated types on the rerun.
``registry.clear()`` remains the recommended escape hatch only when the
offending type cannot be fixed in place.
"""

from __future__ import annotations

import strawberry
from django.db import models

from ..exceptions import ConfigurationError
from ..optimizer.field_meta import FieldMeta
from ..registry import registry
from ..utils.strings import snake_case
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

    Sibling convention: ``_format_ambiguity_error`` below owns the canonical
    primary-ambiguity error string; ``types/base.py:_format_unknown_fields_error``
    owns the other consumer-surface ``Meta.fields`` / ``Meta.exclude`` /
    ``Meta.optimizer_hints`` error strings. If consumer-surface ``Meta.*`` keys
    are renamed or supplemented, update the formatters together.
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


def _format_ambiguity_error(
    offenders: list[tuple[type[models.Model], tuple[type, ...]]],
) -> str:
    """Return the canonical primary-ambiguity error message.

    Sibling of ``_format_unresolved_targets_error`` above; both formatters live
    at the top of this module so the finalize-time error strings stay
    grep-stable for tests and consumer error matching. The fix sentence
    (``Declare Meta.primary = True...``) is the actionable guidance the
    audit's tests pin against (spec lines 127, 133).
    """
    parts = [f"  {model.__name__}: {', '.join(t.__name__ for t in types)}" for model, types in offenders]
    body = "\n".join(parts)
    return (
        "Models with multiple registered DjangoType subclasses and no primary:\n"
        f"{body}\n\n"
        "Declare Meta.primary = True on exactly one of the registered "
        "DjangoType subclasses."
    )


def _audit_primary_ambiguity() -> None:
    """Reject models with multiple registered DjangoTypes and no declared primary.

    Walks ``registry.models_with_multiple_types()`` (the Slice 1 helper at
    ``registry.py::TypeRegistry.models_with_multiple_types``); for each model
    whose ``registry.primary_for(...)`` is ``None``, collects the offending
    registered types via
    ``registry.types_for(model)``. Offenders are sorted by ``model.__name__``
    so the error body is deterministic regardless of consumer import order.
    If the offender list is non-empty, raises ``ConfigurationError`` with the
    canonical message built by ``_format_ambiguity_error``.

    Runs exactly once per build, inside ``finalize_django_types()`` after the
    ``registry.is_finalized()`` short-circuit and before pending-relation
    resolution. The pre-resolution placement (M1) is what makes Phase 1
    failure-atomic — an ambiguity raise leaves every collected class intact
    and the pending-relation list preserved for a re-call.
    """
    offenders: list[tuple[type[models.Model], tuple[type, ...]]] = []
    for model in registry.models_with_multiple_types():
        if registry.primary_for(model) is None:
            offenders.append((model, registry.types_for(model)))
    if not offenders:
        return
    offenders.sort(key=lambda entry: entry[0].__name__)
    raise ConfigurationError(_format_ambiguity_error(offenders))


def finalize_django_types() -> None:
    """Resolve pending relations, attach resolvers, and finalize collected types.

    Phase 1 is failure-atomic: the primary-ambiguity audit and the
    unresolved-target detection both complete before any class object is
    mutated. If ``_audit_primary_ambiguity`` or the unresolved-target check
    raises ``ConfigurationError``, every collected class is left intact and
    the pending-relation list is preserved for a re-call.

    Phase 2 attaches the framework's auto relation resolvers; Phase 2.5
    applies declared interfaces to ``cls.__bases__``, gates Relay-node
    types against composite primary keys, and injects the four
    ``resolve_*`` defaults that ``relay.Node`` would otherwise inherit
    from the upstream Strawberry interface; Phase 3 calls
    ``strawberry.type(...)`` on each not-yet-finalized type. Phase 2.5
    runs before Phase 3 so the ``strawberry.type(...)`` decorator sees
    the mutated bases and the injected classmethods at decoration time.

    Partial-failure recovery: if ``strawberry.type`` (or any earlier
    Phase 2/2.5 step) raises mid-iteration, the call is partially
    applied. Calling ``finalize_django_types()`` again is safe and
    resumes from the failing entry — the per-entry
    ``if definition.finalized: continue`` guard at the head of each
    phase loop skips already-decorated types on the rerun, and
    ``apply_interfaces`` re-mutating ``__bases__`` is a no-op because
    it filters via ``iface not in type_cls.__mro__``. ``registry.clear()``
    is the recommended path only when the consumer cannot fix the
    offending type in place.

    Lifecycle of the finalized flag: ``registry.mark_finalized()`` runs
    as the last statement of this function and only on Phase 3 success.
    The registry's ``is_finalized()`` flag therefore flips ONLY after
    every collected type has been decorated via ``strawberry.type``; a
    Phase 2/2.5/3 raise leaves the flag False and supports the
    fine-grained rerun above. The function entry-guards on
    ``registry.is_finalized()`` so a second successful call is a no-op.
    """
    if registry.is_finalized():
        return

    _audit_primary_ambiguity()

    unresolved: list[PendingRelation] = []
    resolved: list[tuple[PendingRelation, type, FieldMeta]] = []
    consumer_authored: list[PendingRelation] = []
    for pending in registry.iter_pending_relations():
        # definition is always set; pending records are added after
        # register_with_definition in DjangoType.__init_subclass__
        # (see types/base.py register_with_definition / add_pending_relation
        # ordering). The ``is not None`` guard is kept as defense-in-depth.
        definition = registry.get_definition(pending.source_type)
        # Defense-in-depth: ``types/base.py::_build_annotations`` already skips the
        # pending append for consumer-annotated relations, so this branch
        # is a no-op under the documented call graph. Kept so a future
        # change to ``_build_annotations`` (e.g. a lazy/forward-reference
        # path that does append a pending record) cannot double-mutate
        # ``__annotations__`` here.
        if definition is not None and pending.field_name in definition.consumer_authored_fields:
            consumer_authored.append(pending)
            continue
        target_type = registry.get(pending.related_model)
        if target_type is None:
            unresolved.append(pending)
            continue
        field_meta = definition.field_map[snake_case(pending.field_name)]
        resolved.append((pending, target_type, field_meta))

    if unresolved:
        raise ConfigurationError(_format_unresolved_targets_error(unresolved))

    resolved_pending = [*consumer_authored]
    for pending, target_type, field_meta in resolved:
        pending.source_type.__annotations__[pending.field_name] = resolved_relation_annotation(
            pending.django_field,
            target_type,
            field_meta=field_meta,
        )
        resolved_pending.append(pending)
    registry.discard_pending(resolved_pending)

    # Phase 2 runs BEFORE Phase 2.5; interface base injection cannot
    # supersede framework resolvers attached here. No Strawberry interface
    # currently exposes a same-named ``resolve_<field>`` default for an
    # auto-mapped Django relation, so this is a latent ordering risk, not a
    # live bug. If a future Strawberry interface introduces such a default,
    # swap the loop ordering and pin the consumer-interface-wins behavior in
    # tests.
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
