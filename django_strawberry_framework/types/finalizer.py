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
  Relay interface expects. ``_bind_filtersets`` then runs four ordered
  subpasses (bind owners, expand filtersets, materialize input classes,
  reject orphan ``filter_input_type`` references) per spec-021 Decision 6
  / H1 of rev8 — every subpass MUST complete across all wired types
  before the next subpass starts so cross-filterset references resolve
  against bound owners regardless of registration order. Runs before
  Phase 3 so the ``strawberry.type`` decorator sees the mutated bases
  AND the materialized input-class module globals.
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

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:  # pragma: no cover - type-checking-only import.
    from .definition import DjangoTypeDefinition


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
    audit's tests pin against (spec-014 #"with the fix sentence",
    spec-014 #"test_finalize_ambiguity_error_message_contains_actionable_fix").
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

    _bind_filtersets()

    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        strawberry.type(type_cls, name=definition.name, description=definition.description)
        definition.finalized = True

    registry.mark_finalized()


def _bind_filterset_owner(filterset_cls: type, definition: DjangoTypeDefinition) -> None:
    """Bind ``filterset_cls._owner_definition`` with strict multi-owner validation.

    First binding writes ``filterset_cls._owner_definition = definition``
    and returns. Re-binding the same ``(filterset_cls, definition)``
    pair is idempotent (supports partial-finalize recovery per spec-021
    Decision 6 lines 683-685). A second, distinct owner triggers the
    H2-rev8 strict-equality check across the two owner-dependent axes:

    1. **Own-PK Relay identity.** A filterset's own primary key resolves
       to a Relay ``GlobalID`` typed to the *owner* — keyed on
       ``owner.origin``'s Relay-node-ness and its ``graphql_type_name``.
       Two owners that disagree on either would make the shared
       filterset's ``id`` filter resolve to a different (or
       differently-typed) GlobalID depending on which owner finalized
       first; only the FIRST binding is stored, so the second owner would
       silently mis-resolve. This is the genuine owner-dependent axis (see
       the scope note), so it is checked directly.
    2. **Declared relation targets.** For every ``RelatedFilter`` declared
       on ``filterset_cls``, both owners' ``related_target_for(field_name)``
       must resolve to the EXACT same ``DjangoTypeDefinition`` AND the
       EXACT same ``graphql_type_name``.

    Any divergence raises ``ConfigurationError`` naming both owners (and,
    for the relation axis, the offending field and both resolved target
    type names) per spec-021 line 574.

    Scope note: ``related_target_for`` resolves a relation's target via the
    process-global ``registry.primary_for(target_model)`` lookup keyed on
    the TARGET model — NOT on the owner — so for two legitimate owners
    (which necessarily share the filterset's ``Meta.model``) the relation
    targets are invariant and cannot diverge. The own-PK identity is the
    real owner-dependent axis. Widening the relation walk to every FK / PK
    declared via ``Meta.fields`` would therefore guard a non-divergent
    surface and stays deferred (spec lines 575-576) until real demand
    surfaces.
    """
    previous: DjangoTypeDefinition | None = getattr(filterset_cls, "_owner_definition", None)
    if previous is None:
        filterset_cls._owner_definition = definition
        return
    if previous is definition:
        return
    # Axis 1 — own-PK Relay identity. ``owner.origin`` Relay-node-ness and
    # ``graphql_type_name`` are the only owner-dependent inputs to the
    # filterset's own-PK GlobalID resolution; a divergence here means the
    # shared ``id`` filter would resolve ambiguously across owners.
    prev_is_relay = implements_relay_node(previous.origin)
    new_is_relay = implements_relay_node(definition.origin)
    if prev_is_relay != new_is_relay or (
        prev_is_relay and previous.graphql_type_name != definition.graphql_type_name
    ):
        raise ConfigurationError(
            _format_owner_pk_mismatch_error(filterset_cls, previous, definition),
        )
    # Axis 2 — declared relation targets.
    related_filters = getattr(filterset_cls, "related_filters", {}) or {}
    for field_name in related_filters:
        prev_target = previous.related_target_for(field_name)
        new_target = definition.related_target_for(field_name)
        if prev_target is None and new_target is None:
            continue
        if prev_target is None or new_target is None:
            raise ConfigurationError(
                _format_owner_mismatch_error(
                    filterset_cls,
                    previous,
                    definition,
                    field_name,
                    prev_target,
                    new_target,
                ),
            )
        prev_definition, _ = prev_target
        new_definition, _ = new_target
        if (
            prev_definition is not new_definition
            or prev_definition.graphql_type_name != new_definition.graphql_type_name
        ):
            raise ConfigurationError(
                _format_owner_mismatch_error(
                    filterset_cls,
                    previous,
                    definition,
                    field_name,
                    prev_target,
                    new_target,
                ),
            )


def _format_owner_mismatch_error(
    filterset_cls: type,
    previous: DjangoTypeDefinition,
    new: DjangoTypeDefinition,
    field_name: str,
    prev_target: tuple[DjangoTypeDefinition, object] | None,
    new_target: tuple[DjangoTypeDefinition, object] | None,
) -> str:
    """Return the canonical H2-rev8 multi-owner-mismatch message.

    Sibling of ``_format_unresolved_targets_error`` /
    ``_format_ambiguity_error`` above; all three formatters live at the
    top of this module so consumer error matching stays grep-stable.
    Names both owners' qualified names, the offending FilterSet, the
    offending field, and both resolved target type names per spec-021
    line 574.
    """
    prev_name = prev_target[0].origin.__qualname__ if prev_target is not None else "<unresolved>"
    new_name = new_target[0].origin.__qualname__ if new_target is not None else "<unresolved>"
    return (
        f"FilterSet {filterset_cls.__qualname__} cannot bind to multiple owners with "
        f"diverging targets: {previous.origin.__qualname__} resolves "
        f"{field_name!r} to {prev_name}, but {new.origin.__qualname__} resolves it "
        f"to {new_name}. Declare separate FilterSet subclasses for the diverging "
        "owners (per spec-021 H2 of rev8)."
    )


def _format_owner_pk_mismatch_error(
    filterset_cls: type,
    previous: DjangoTypeDefinition,
    new: DjangoTypeDefinition,
) -> str:
    """Return the multi-owner own-PK Relay-identity mismatch message.

    Sibling of ``_format_owner_mismatch_error``; names both owners and
    their Relay-node-ness + ``graphql_type_name`` so the consumer can see
    why the shared filterset's own-PK GlobalID would resolve ambiguously.
    Grep-stable alongside the other ``_format_*`` finalize-error helpers.
    """
    return (
        f"FilterSet {filterset_cls.__qualname__} cannot bind to multiple owners with "
        f"diverging own-primary-key Relay identity: {previous.origin.__qualname__} "
        f"(relay_node={implements_relay_node(previous.origin)}, "
        f"type_name={previous.graphql_type_name!r}) vs {new.origin.__qualname__} "
        f"(relay_node={implements_relay_node(new.origin)}, "
        f"type_name={new.graphql_type_name!r}). The filterset's own `id` filter "
        "resolves to a GlobalID typed to its owner, so owners diverging on "
        "Relay-node-ness or GraphQL type name cannot share one FilterSet. Declare "
        "separate FilterSet subclasses for the diverging owners (per spec-021 H2 of rev8)."
    )


def _format_orphan_filtersets_error(orphans: list[type]) -> str:
    """Return the canonical orphan-``filter_input_type`` error message.

    Sorted by qualified name for deterministic output. When more than
    one orphan is present, the message uses the multi-orphan lead-in
    mirroring ``_format_unresolved_targets_error``'s shape; the single-
    orphan branch uses the spec-pinned actionable message from spec-021
    line 673.
    """
    if len(orphans) == 1:
        cls = orphans[0]
        return (
            f"FilterSet '{cls.__name__}' is referenced via filter_input_type(...) but "
            f"never assigned to a DjangoType via Meta.filterset_class. Add "
            f"'filterset_class = {cls.__name__}' to the relevant DjangoType's Meta."
        )
    lines = [f"  - {cls.__module__}.{cls.__qualname__}" for cls in orphans]
    body = "\n".join(lines)
    return (
        "FilterSets referenced via filter_input_type(...) but not wired to any "
        f"DjangoType:\n{body}\n\n"
        "Add 'filterset_class = <Name>' to the relevant DjangoType's Meta for each."
    )


def _bind_filtersets() -> None:
    """Run the four ordered phase-2.5 subpasses for filterset binding.

    Subpass 1 — bind every owner. Walks every wired definition and
    binds ``filterset_cls._owner_definition`` via
    ``_bind_filterset_owner``. The H2-rev8 strict-equality check
    rejects diverging multi-owner reuse before any subsequent subpass
    runs.

    Subpass 2 — expand every filterset. Calls
    ``filterset_cls.get_filters()`` so Layer-4 expansion resolves lazy
    ``RelatedFilter`` refs and cycle guards apply uniformly. Owner
    binding from subpass 1 is visible to every filterset's owner-aware
    ``filter_for_field`` / ``filter_for_lookup`` overrides regardless
    of which type-cls is iterated first.

    Subpass 3 — orphan validation. Compares the FilterSets passed to
    ``filter_input_type(...)`` (per Decision 11) against the set of
    FilterSets wired via ``Meta.filterset_class``. Orphans raise
    ``ConfigurationError`` per spec-021 line 673 with the actionable
    suggestion to add the missing ``filterset_class = <Name>``. Runs
    BEFORE materialization so an orphan failure leaves no partial
    state in ``_materialized_names`` /
    ``FilterArgumentsFactory.input_object_types``; otherwise a re-run
    of ``finalize_django_types()`` after fixing the orphan would see
    stale ledger entries from the prior failed attempt.

    Subpass 4 — materialize input classes. Reads the
    ``FilterArgumentsFactory(filterset_cls).arguments`` property
    (triggers BFS build, idempotent through the factory's class-level
    cache) and materializes EVERY built class from the factory's
    ``input_object_types`` ledger as a real module global of
    ``filters.inputs`` via ``materialize_input_class(name, cls)``. A
    second factory instance for a sibling root sees the cached build
    via the class-level dict.
    """
    # Local imports: keep ``types/finalizer.py`` independent of the
    # filters package's module-load order. The phase-2.5 binding only
    # runs when a definition declares ``filterset_class``, which only
    # works when the filters subsystem has been imported by the
    # consumer.
    from ..filters import _helper_referenced_filtersets
    from ..filters.factories import FilterArgumentsFactory
    from ..filters.inputs import materialize_input_class

    # Subpass 1: bind every owner before any expansion runs.
    wired: list[type] = []
    for _type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        filterset_cls = definition.filterset_class
        if filterset_cls is None:
            continue
        _bind_filterset_owner(filterset_cls, definition)
        wired.append(filterset_cls)

    # Subpass 2: expand every filterset; cross-references now resolve.
    # ``LazyRelatedClassMixin.resolve_lazy_class`` (Slice 1) raises
    # ``ImportError`` when a string-form ``RelatedFilter("Name")`` cannot
    # be resolved. Re-wrap as ``ConfigurationError`` per spec-021 lines
    # 416 + 1030 and the package's "finalize-time errors are
    # ConfigurationError" convention (sibling formatters
    # ``_format_unresolved_targets_error`` / ``_format_ambiguity_error``
    # / ``_format_owner_mismatch_error`` / ``_format_orphan_filtersets_error``
    # all raise ``ConfigurationError`` at finalize time); the original
    # ``ImportError`` is preserved via ``__cause__``.
    for filterset_cls in wired:
        try:
            filterset_cls.get_filters()
        except ImportError as exc:
            raise ConfigurationError(
                f"Cannot finalize Django types: filterset "
                f"{filterset_cls.__qualname__} references an unresolved "
                f"related-filter target. {exc}",
            ) from exc
        except ConfigurationError:
            raise
        except Exception as exc:
            # Uniform finalize-time error shape: any failure surfacing from
            # ``get_filters()`` rebinds as ``ConfigurationError`` so the
            # consumer sees one error class for every finalize failure
            # instead of having to guard for the underlying exception
            # type.
            raise ConfigurationError(
                f"Cannot finalize Django types: filterset "
                f"{filterset_cls.__qualname__} raised during expansion. "
                f"{exc.__class__.__name__}: {exc}",
            ) from exc

    # Subpass 3: orphan validation against the helper-tracked set. Runs
    # BEFORE materialization so a failure here doesn't leave half-
    # materialized input classes in the inputs-module namespace.
    wired_set = set(wired)
    orphans = sorted(
        _helper_referenced_filtersets - wired_set,
        key=lambda cls: f"{cls.__module__}.{cls.__qualname__}",
    )
    if orphans:
        raise ConfigurationError(_format_orphan_filtersets_error(orphans))

    # Subpass 4: materialize every built input class as a module global.
    for filterset_cls in wired:
        factory = FilterArgumentsFactory(filterset_cls)
        # Touch ``.arguments`` to drive ``_ensure_built`` (idempotent
        # through the factory's class-level cache); the cache is shared
        # across instances so dependent input classes built by one
        # factory are visible to a sibling factory's materialize loop.
        factory.arguments
        for name, input_cls in factory.input_object_types.items():
            materialize_input_class(name, input_cls)
