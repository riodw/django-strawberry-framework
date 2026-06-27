"""``finalize_django_types()`` - the once-only finalization gate for collected ``DjangoType`` classes.

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
  Relay interface expects. ``_synthesize_relation_connections`` then attaches
  the ``<field>_connection`` siblings for eligible many-side relations per
  ``Meta.relation_shapes`` (spec-032 Decision 6) before the sidecar binding
  runs. ``_bind_filtersets`` then runs four ordered
  subpasses (bind owners, expand filtersets, materialize input classes,
  reject orphan ``filter_input_type`` references) per spec-027 Decision 6
  / H1 of rev8 - every subpass MUST complete across all wired types
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

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import strawberry
from django.db import models
from strawberry import relay
from strawberry.types.field import StrawberryField
from strawberry.utils.str_converters import to_camel_case

from ..exceptions import ConfigurationError
from ..optimizer import logger
from ..optimizer.field_meta import FieldMeta
from ..registry import registry
from ..utils.relations import instance_accessor
from ..utils.strings import snake_case
from .converters import resolved_relation_annotation
from .relations import PendingRelation
from .relay import (
    _accepts_model_label_decode,
    _check_composite_pk_for_relay_node,
    _emits_model_label,
    apply_interfaces,
    implements_relay_node,
    install_globalid_typename_resolver,
    install_relay_node_resolvers,
)
from .resolvers import _attach_file_resolvers, _attach_relation_resolvers

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
    lines = [
        f"  - {pending.source_model.__name__}.{pending.field_name} -> "
        f"{pending.related_model.__name__} (no registered DjangoType)"
        for pending in unresolved
    ]
    body = "\n".join(lines)
    return (
        "Cannot finalize Django types: the following relation targets are unresolved.\n"
        f"{body}\n\n"
        "Declare a DjangoType for each unresolved target model, or exclude these "
        "relation fields via Meta.exclude / Meta.fields."
    )


def _format_ambiguity_error(offenders: list[tuple[type[models.Model], tuple[type, ...]]]) -> str:
    """Return the canonical primary-ambiguity error message.

    Sibling of ``_format_unresolved_targets_error`` above; both formatters live
    at the top of this module so the finalize-time error strings stay
    grep-stable for tests and consumer error matching. The fix sentence
    (``Declare Meta.primary = True...``) is the actionable guidance the
    audit's tests pin against (spec-018 #"with the fix sentence",
    spec-018 #"test_finalize_ambiguity_error_message_contains_actionable_fix").
    """
    parts = [
        f"  {model.__name__}: {', '.join(t.__name__ for t in types)}" for model, types in offenders
    ]
    body = "\n".join(parts)
    return (
        "Models with multiple registered DjangoType subclasses and no primary:\n"
        f"{body}\n\n"
        "Declare Meta.primary = True on exactly one of the registered "
        "DjangoType subclasses."
    )


def _audit_primary_ambiguity(multi_type_models: tuple[type[models.Model], ...]) -> None:
    """Reject models with multiple registered DjangoTypes and no declared primary.

    Walks the pre-materialized multi-type-model list (computed once per build in
    ``finalize_django_types`` from
    ``registry.py::TypeRegistry.models_with_multiple_types`` and shared with the
    Phase-2.5 ``_audit_model_label_routing`` audit); for each model whose
    ``registry.primary_for(...)`` is ``None``, collects the offending registered
    types via ``registry.types_for(model)``. Offenders are sorted by
    ``model.__name__`` so the error body is deterministic regardless of consumer
    import order. If the offender list is non-empty, raises ``ConfigurationError``
    with the canonical message built by ``_format_ambiguity_error``.

    Runs exactly once per build, inside ``finalize_django_types()`` after the
    ``registry.is_finalized()`` short-circuit and before pending-relation
    resolution. The pre-resolution placement (M1) is what makes Phase 1
    failure-atomic - an ambiguity raise leaves every collected class intact
    and the pending-relation list preserved for a re-call. The once-per-build
    guarantee for the underlying ``registry.models_with_multiple_types()``
    generator now lives in ``finalize_django_types``, which materializes the
    walk once and passes it to both audits.
    """
    offenders: list[tuple[type[models.Model], tuple[type, ...]]] = [
        (model, registry.types_for(model))
        for model in multi_type_models
        if registry.primary_for(model) is None
    ]
    if not offenders:
        return
    offenders.sort(key=lambda entry: entry[0].__name__)
    raise ConfigurationError(_format_ambiguity_error(offenders))


def _audit_field_surface(type_cls: type, definition: DjangoTypeDefinition) -> None:
    """Reject an empty or camel-colliding GraphQL field surface on ``type_cls``.

    Two misconfigurations Strawberry only catches late - as a generic
    ``ValueError`` or, worse, a SILENT field drop inside
    ``strawberry.Schema(...)`` - surfaced here with DjangoType attribution:

    * Empty surface - ``Meta.fields = ()`` (or a ``Meta.exclude`` that removes
      every column) with no consumer-authored field leaves a type with zero
      GraphQL fields. Strawberry then raises ``Type <X> must define one or more
      fields`` with no DjangoType context.
    * Name collision - two DISTINCT field names that default-camel-case to ONE
      GraphQL name (``foo_bar`` + ``fooBar`` -> ``fooBar``). Strawberry keeps one
      and silently drops the other. The synthesized-relation-connection guard in
      ``_synthesize_relation_connections`` already covers a generated
      ``<name>_connection`` colliding with an existing field; this covers the
      remaining column-vs-column / field-vs-field case.

    The surface set mirrors the connection guard's: declared annotations, the
    definition's selected fields, and consumer-assigned ``StrawberryField``s. A
    consumer override shares its column's NAME (e.g. ``name`` over ``name``), so
    it is one entry, never a collision; only distinct names colliding under
    ``to_camel_case`` raise.
    """
    names = (
        set(type_cls.__annotations__)
        | {f.name for f in definition.selected_fields}
        | {k for k, v in vars(type_cls).items() if isinstance(v, StrawberryField)}
    )
    if not names:
        raise ConfigurationError(
            f"{definition.graphql_type_name}: DjangoType over "
            f"{definition.model.__name__} has no GraphQL fields. Meta.fields is empty "
            "(or Meta.exclude removes every column) and no field is consumer-authored; "
            "declare at least one field.",
        )
    by_camel: dict[str, list[str]] = {}
    for name in names:
        by_camel.setdefault(to_camel_case(name), []).append(name)
    collisions = {camel: sorted(ns) for camel, ns in by_camel.items() if len(ns) > 1}
    if not collisions:
        return
    details = ", ".join(f"{camel!r} from {ns}" for camel, ns in sorted(collisions.items()))
    raise ConfigurationError(
        f"{definition.graphql_type_name}: distinct fields collide on the GraphQL surface "
        f"under default camel-casing: {details}. Rename one side, or drop one via "
        "Meta.fields / Meta.exclude.",
    )


def _format_model_label_routing_error(
    offenders: list[tuple[type[models.Model], type, str | None]],
) -> str:
    """Return the canonical model-label-routing-invariant error message.

    Sibling of ``_format_ambiguity_error`` above; both live at the top of this
    module so the finalize-time error strings stay grep-stable. Each offender is
    ``(model, emitter_type, primary_strategy)``: a multi-type model whose
    primary's effective strategy cannot decode the model-label IDs an emitter
    type mints (spec-031 Decision 8). The fix sentence branches on the
    primary's recorded strategy: a recorded string strategy can be re-declared
    to a model-label-decodable one, but a ``None`` primary is not
    Relay-Node-shaped at all - ``Meta.globalid_strategy`` is rejected on a
    non-Relay type, so telling the consumer to set it would prescribe an
    impossible fix. Both branches also offer moving the emitter(s) onto the
    ``type`` strategy.
    """
    parts = [
        f"  {model.__name__}: {emitter.__name__} emits model-label GlobalIDs but the "
        f"primary's strategy is {primary_strategy!r}"
        for model, emitter, primary_strategy in offenders
    ]
    body = "\n".join(parts)
    fixes = []
    if any(strategy is not None for _model, _emitter, strategy in offenders):
        fixes.append(
            "Set the primary's Meta.globalid_strategy to 'model' or 'type+model' so the "
            "model-label IDs route correctly, or move the emitting type(s) to the 'type' "
            "strategy so their IDs stay type-scoped.",
        )
    if any(strategy is None for _model, _emitter, strategy in offenders):
        fixes.append(
            "A primary whose strategy is None is not Relay-Node-shaped, so it cannot "
            "declare Meta.globalid_strategy; make the primary Relay-Node-shaped (or "
            "re-declare Meta.primary on a Relay-Node-shaped type), or move the emitting "
            "type(s) to the 'type' strategy so their IDs stay type-scoped.",
        )
    fix_sentence = " ".join(fixes)
    return (
        "Models whose registered DjangoTypes emit model-label GlobalIDs but whose "
        "primary cannot decode them:\n"
        f"{body}\n\n"
        f"{fix_sentence}"
    )


def _audit_model_label_routing(multi_type_models: tuple[type[models.Model], ...]) -> None:
    """Reject multi-type models whose primary cannot decode emitted model-label IDs.

    The model-label-routing invariant (spec-031 Decision 8): for any multi-type
    model, if any registered type's effective strategy emits model-label IDs
    (``model`` / ``type+model``), the model's primary's effective strategy must
    also accept model-label decode (``model`` / ``type+model``). A model-label ID
    routes through ``registry.get(model)`` (the primary), so a primary that
    cannot decode it would reject IDs a secondary emitted.

    Iterates the same pre-materialized multi-type-model list the Phase-1
    ``_audit_primary_ambiguity`` audit consumed:
    a single-type model trivially satisfies the invariant (its lone type both
    emits and decodes) and has no declared primary. For multi-type models the
    Phase-1 ``_audit_primary_ambiguity`` has already guaranteed a primary exists,
    so ``primary_for(model)`` is safe. Offenders are sorted by ``model.__name__``
    for a deterministic message. Sharing the materialized list (computed once in
    ``finalize_django_types``) is what keeps ``models_with_multiple_types()``
    invoked exactly once per build across both audits.

    Runs in Phase 2.5 AFTER every Relay type's ``effective_globalid_strategy`` is
    recorded and BEFORE Phase 3, so a raise leaves every type ``finalized = False``
    and the re-entrancy guard in ``install_globalid_typename_resolver`` keeps a
    re-run from misclassifying installed types.
    """
    offenders: list[tuple[type[models.Model], type, str | None]] = []
    for model in multi_type_models:
        emitter = _first_model_label_emitter(model)
        if emitter is None:
            continue
        primary = registry.primary_for(model)
        primary_strategy = registry.get_definition(primary).effective_globalid_strategy
        if not _accepts_model_label_decode(primary_strategy):
            offenders.append((model, emitter, primary_strategy))
    if not offenders:
        return
    offenders.sort(key=lambda entry: entry[0].__name__)
    raise ConfigurationError(_format_model_label_routing_error(offenders))


def _first_model_label_emitter(model: type[models.Model]) -> type | None:
    """Return the first registered type for ``model`` that emits model-label IDs.

    Iterates ``registry.types_for(model)`` in registration order and returns the
    first type whose recorded ``effective_globalid_strategy`` emits model-label
    IDs, or ``None`` if none do. Single-sources the per-type strategy read so the
    audit body stays readable.
    """
    for type_cls in registry.types_for(model):
        strategy = registry.get_definition(type_cls).effective_globalid_strategy
        if _emits_model_label(strategy):
            return type_cls
    return None


def _warn_model_label_secondary_collapse(
    multi_type_models: tuple[type[models.Model], ...],
) -> None:
    """Warn when a secondary type's model-label GlobalIDs collapse onto the primary.

    A model-label payload (``app_label.model:pk``) always decodes through
    ``registry.get(model)`` - the primary - so any registered type OTHER than the
    primary that also emits model-label IDs (the ``model`` default or
    ``type+model``) has its ``GlobalID``s route to, and refetch AS, the primary
    type: ``node(id:)`` / ``nodes(ids:)`` return the primary, and the secondary's
    distinct identity and ``get_queryset`` visibility scope silently collapse into
    the primary's. This is legal (spec-031 Decision 8: a model-anchored ID cannot
    distinguish secondaries by design), but it is the most likely accidental
    config now that ``model`` is the default - and a regression for a multi-type
    model that, under the pre-``0.0.9`` type-name default, gave each type a
    distinct, correctly-routed ``GlobalID``.

    The hard-error sibling ``_audit_model_label_routing`` has already rejected the
    inverse (a model-label emitter under a primary that CANNOT decode model
    labels). This pass only warns about the legal-but-surprising collapse and
    points at the per-type ``type`` opt-out that restores disjoint identity. It
    runs immediately after that audit, over the same materialized multi-type-model
    tuple, so every type's ``effective_globalid_strategy`` is already recorded.
    """
    for model in multi_type_models:
        primary = registry.primary_for(model)
        secondaries = tuple(
            type_cls
            for type_cls in registry.types_for(model)
            if type_cls is not primary
            and _emits_model_label(registry.get_definition(type_cls).effective_globalid_strategy)
        )
        if not secondaries:
            continue
        secondary_names = ", ".join(sorted(type_cls.__name__ for type_cls in secondaries))
        logger.warning(
            "GlobalID identity collapse on model %s.%s: %s emit model-anchored GlobalIDs "
            "that decode to the primary type %s, so node(id:)/nodes(ids:) refetch them as %s "
            "and their distinct identity / get_queryset scope is lost. Set "
            'Meta.globalid_strategy = "type" on the secondary type(s) for disjoint identity '
            "scopes (spec-031 Decision 8).",
            model._meta.app_label,
            model._meta.model_name,
            secondary_names,
            primary.__name__,
            primary.__name__,
        )


# Re-entrancy marker stamped on every synthesized relation-connection field
# object at attach time. A partial-finalize rerun (the module's documented
# recovery contract) re-enters ``_synthesize_relation_connections``; the
# marker lets the rerun recognize its own prior attachment instead of
# misreading it as a name collision.
_SYNTHESIZED_RELATION_CONNECTION_MARKER = "_dst_synthesized_relation_connection"


def _suppress_relation_list_form(type_cls: type, name: str) -> None:
    """Remove a relation's generated list annotation + Phase-2 resolver (tolerant).

    The ``shape == "connection"`` path drops the generated ``list[T]`` form so
    the SDL carries only the connection sibling. Removals are tolerant of
    already-absent entries: a partial-finalize rerun (the module's recovery
    contract) may re-enter synthesis with the field already suppressed, and
    must not ``KeyError`` / ``AttributeError`` on the second pass.
    """
    type_cls.__annotations__.pop(name, None)
    if name in type_cls.__dict__:
        delattr(type_cls, name)


def _record_relation_connection(
    definition: DjangoTypeDefinition,
    generated: str,
    name: str,
) -> None:
    """Record the walker-readable ``generated -> relation field name`` mapping.

    Lazily initializes ``definition.relation_connections`` to ``{}`` and sets
    the entry. Idempotent (a plain dict assignment), so the re-entrancy
    ``continue`` branch (a prior partial finalize re-running Phase 2.5) records
    the slot just as the first-attach branch does - the walker reads the same
    mapping either way (spec-033 Decision 3).
    """
    if definition.relation_connections is None:
        definition.relation_connections = {}
    definition.relation_connections[generated] = name


def _synthesize_relation_connections() -> None:
    """Synthesize ``<field>_connection`` siblings for eligible many-side relations.

    The Phase-2.5 relation-as-Connection step (spec-032 Decisions 6/7): for
    every not-yet-finalized Relay-Node-shaped type, each selected many-side
    relation (reverse FK, forward / reverse M2M - ``FieldMeta.is_many_side``,
    the same classifier the generated list resolvers key on) whose target type
    is also Relay-Node-shaped gets a ``<field>_connection`` sibling (rendered
    ``<field>Connection`` by Strawberry's camel-casing) per the resolved shape
    from ``definition.relation_shapes`` (absent keys default to
    ``DEFAULT_RELATION_SHAPE``):

    - ``"both"`` (default) - keep the generated ``list[T]`` field; add the
      connection sibling.
    - ``"connection"`` - add the sibling; remove the generated list
      annotation and the Phase-2 list resolver before Phase 3 freezes the
      annotation set, so the SDL never carries the list form.
    - ``"list"`` - synthesize nothing (the shipped shape).

    The synthesized field reuses the spec-030 machinery wholesale:
    ``_connection_type_for`` (per-target connection class + ``totalCount``
    opt-in), ``_build_relation_connection_resolver`` (the relation-manager-
    seeded pipeline carrying the target's ``_synthesized_signature``
    ``filter:`` / ``order_by:`` arguments).

    A non-Node target degrades silently to list-only under the implicit
    default (existing valid schemas keep building) but raises
    ``ConfigurationError`` on an explicit ``"connection"`` / ``"both"``
    request (Decision 6's fail-loud-on-explicit split). Consumer-authored
    relations are skipped under the implicit default - an explicit key
    already raised at type creation (Decision 7 / Revision 3 P2).

    Collision guard (Revision 3 P3): the generated name is checked against
    every existing field name on BOTH surfaces - Python attribute names AND
    default-camel-cased GraphQL names (``to_camel_case``, the rule
    Strawberry's default ``NameConverter`` applies under
    ``auto_camel_case=True``). The schema's actual ``StrawberryConfig`` does
    not exist at finalization time (``strawberry.Schema(...)`` is constructed
    after ``finalize_django_types``), so a collision visible only under a
    non-default ``name_converter`` / ``auto_camel_case=False`` falls through
    to Strawberry's own schema-build duplicate-field error - a documented
    constraint (spec-032 Edge cases), not a gap this guard can close.

    Pre-``033`` strictness posture (spec-032 Decision 12 / Non-goals): the
    synthesized resolver consults NO ``DST_OPTIMIZER_*`` sentinels and
    derives an empty optimizer plan; wiring strictness/planning into the
    connection pipeline is ``WIP-ALPHA-033-0.0.9``'s scope.
    """
    # Function-local plain imports: cycle-safe cross-module reads (the
    # ``_node_fields_declared`` precedent in ``finalize_django_types``). A
    # contract step must never be silently skipped, so deliberately no
    # try/except here.
    from ..connection import _build_relation_connection_resolver, _connection_type_for
    from .base import DEFAULT_RELATION_SHAPE

    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        if not implements_relay_node(type_cls):
            continue
        shapes = definition.relation_shapes or {}
        for field in definition.selected_fields:
            if not field.is_relation:
                continue
            name = field.name
            if not definition.field_map[snake_case(name)].is_many_side:
                continue
            if name in definition.consumer_authored_fields:
                # Implicit-default skip only (the shipped override contract
                # outranks the upgrade); an explicit relation_shapes key
                # naming a consumer-authored relation already raised at type
                # creation (Decision 7 / Revision 3 P2).
                continue
            target_type = registry.get(field.related_model)
            if target_type is None or not implements_relay_node(target_type):
                if shapes.get(name) in ("connection", "both"):
                    target_label = (
                        target_type.__name__
                        if target_type is not None
                        else field.related_model.__name__
                    )
                    raise ConfigurationError(
                        f"{type_cls.__name__}.Meta.relation_shapes[{name!r}] explicitly "
                        f"requests a connection, but the relation's target type "
                        f"{target_label} is not Relay-Node-shaped. Add `relay.Node` to the "
                        f"target's `Meta.interfaces`, or narrow the entry to "
                        f'relation_shapes = {{"{name}": "list"}} / drop it.',
                    )
                # The implicit default degrades silently to list-only
                # (Decision 6): a connection of non-Node types has no Relay
                # identity, and existing valid schemas must keep building.
                continue
            shape = shapes.get(name, DEFAULT_RELATION_SHAPE)
            if shape == "list":
                continue
            generated = f"{name}_connection"
            attached = type_cls.__dict__.get(generated)
            if getattr(attached, _SYNTHESIZED_RELATION_CONNECTION_MARKER, False):
                # Attached by a prior partial finalize. A rerun's Phase 2
                # re-attaches the generated list resolver for this relation, so
                # for a ``"connection"`` shape the list form must be removed
                # AGAIN here - without this the rerun would skip on the marker
                # and leave a reattached, now-unannotated ``items`` resolver
                # that breaks Phase 3 (spec-032 feedback P1). Then skip rather
                # than misread our own field as a collision.
                if shape == "connection":
                    _suppress_relation_list_form(type_cls, name)
                # Re-record the walker-readable slot on rerun: a fresh
                # definition object may have been created after a
                # ``registry.clear()``, so the early-``continue`` must not skip
                # the slot write the first-attach branch performs below
                # (spec-033 Decision 3, re-entrancy path).
                _record_relation_connection(definition, generated, name)
                continue
            existing = (
                set(type_cls.__annotations__)
                | {f.name for f in definition.selected_fields}
                | {k for k, v in vars(type_cls).items() if isinstance(v, StrawberryField)}
            )
            camel = to_camel_case(generated)
            colliding = sorted(n for n in existing if n == generated or to_camel_case(n) == camel)
            if colliding:
                collides_with = ", ".join(repr(n) for n in colliding)
                raise ConfigurationError(
                    f"{type_cls.__name__}: the synthesized relation connection {generated!r} "
                    f"collides with existing field(s) {collides_with} on the GraphQL surface "
                    f"({camel!r} under default camel-casing). Rename the colliding attribute, "
                    f'or opt out with relation_shapes = {{"{name}": "list"}}.',
                )
            field_obj = relay.connection(
                _connection_type_for(target_type),
                # The resolver reads rows off the instance, so it gets the
                # ACCESSOR (``get_accessor_name()``); ``name`` (the related
                # query name) stays the GraphQL vocabulary for the generated
                # field name and the collision guard. The two diverge for a
                # reverse relation without ``related_name`` (Round-4 S3).
                resolver=_build_relation_connection_resolver(
                    target_type,
                    instance_accessor(field),
                    # The relation FIELD NAME (``name``) - the key the walker
                    # builds the window ``to_attr`` ``_dst_<field>_connection``
                    # from (Decision 4) and the resolver's fast-path probe
                    # (Decision 5). It DIVERGES from the accessor for a reverse
                    # relation without ``related_name`` (field ``book`` vs
                    # accessor ``book_set``), so the resolver needs both: the
                    # accessor to read rows, the field name to probe the window.
                    name,
                    # The DECLARING type - the ``parent_type`` the walker keyed
                    # the planned connection's ``resolver_key`` under
                    # (spec-033 Decision 8). Passing the iterated ``type_cls``
                    # (not ``registry.get(model)``) keeps a divergent secondary
                    # type's strictness key honest: its connection is never
                    # window-planned (Decision 3) and stays correctly flagged.
                    type_cls,
                ),
            )
            setattr(field_obj, _SYNTHESIZED_RELATION_CONNECTION_MARKER, True)
            setattr(type_cls, generated, field_obj)
            # Record the walker-readable synthesis mapping on the declaring
            # definition (spec-033 Decision 3). This runs exactly when a sibling
            # is attached, so suppressed shapes ("list" / non-Node /
            # consumer-authored, which ``continue`` above before reaching here)
            # correctly record nothing. The walker reads this slot to recognize
            # and window-plan the nested connection (see ``types/definition.py``).
            _record_relation_connection(definition, generated, name)
            if shape == "connection":
                # Remove the generated list form before Phase 3 freezes the
                # annotation set (spec-032 Edge cases): the Phase-1 resolved
                # relation annotation and the Phase-2 list resolver.
                _suppress_relation_list_form(type_cls, name)


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
    resumes from the failing entry - the per-entry
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

    # Materialize the multi-type-model walk ONCE per finalize. Both audits
    # (Phase-1 ambiguity, Phase-2.5 model-label routing) consume this same
    # tuple, so ``registry.models_with_multiple_types()`` - a one-shot lazy
    # generator (registry.py) - is invoked exactly once per build rather than
    # once per audit. This is a pure read; computing it before
    # ``_audit_primary_ambiguity`` does not disturb Phase 1's failure-atomic
    # contract.
    multi_type_models = tuple(registry.models_with_multiple_types())

    _audit_primary_ambiguity(multi_type_models)

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
        resolved.append(
            (pending, target_type, field_meta),
        )

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
        # File/image columns get a generated parent resolver in the SAME
        # Phase-2 window (the only place resolvers attach before Phase 3
        # ``strawberry.type(...)`` freezes the class). The skip set is the full
        # ``consumer_authored_fields`` union -- BROADER than the relation pass's
        # ``consumer_assigned_relation_fields`` -- so an annotation-only
        # ``attachment: str`` override (already honored by ``_build_annotations``)
        # also gets no generated file resolver (spec-037 Decision 3). Interface
        # injection order below is unchanged; file columns are scalar object
        # wrappers and do not interact with relay.Node defaults.
        _attach_file_resolvers(
            type_cls,
            definition.selected_fields,
            skip_field_names=definition.consumer_authored_fields,
        )

    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        # ``apply_interfaces`` is the only step that depends on a non-empty
        # ``Meta.interfaces`` tuple. The Relay-node gate and resolver injection
        # are keyed off the resolved MRO (``implements_relay_node``) so they
        # also catch consumers who wrote ``class Foo(DjangoType, relay.Node)``
        # directly without ``Meta.interfaces``.
        if definition.interfaces:
            apply_interfaces(type_cls, definition)
        if implements_relay_node(type_cls):
            _check_composite_pk_for_relay_node(type_cls)
            install_relay_node_resolvers(type_cls)
            install_globalid_typename_resolver(type_cls, definition)

    # No-Node-types check (spec-032 Decision 8): a declared ``DjangoNodeField()``
    # / ``DjangoNodesField()`` on a registry with NO Relay-Node-shaped types is
    # a schema-shape error and must fail at build time, not on first traffic.
    # The check lives at finalization (not field construction) because the
    # factories run at class-body time, typically before any DjangoType
    # imports - only the finalizer sees the settled registry. The import is
    # function-local (cycle-safe: top-level ``relay.py`` imports from
    # ``types/``) and PLAIN - unlike ``registry.clear()``'s best-effort
    # teardown blocks, a contract check must never be silently skipped, so
    # there is deliberately no try/except-ImportError here.
    from ..relay import _node_fields_declared

    if _node_fields_declared and not any(
        implements_relay_node(type_cls) for type_cls, _ in registry.iter_definitions()
    ):
        raise ConfigurationError("node lookup configured but no Node types registered.")

    # Relation-as-Connection synthesis (spec-032 Decision 6): after
    # ``install_globalid_typename_resolver``, before Phase 3 freezes the
    # annotation set - and before ``_bind_filtersets`` / ``_bind_ordersets``,
    # so the sidecar registrations made by ``_synthesized_signature`` are
    # orphan-validated and materialized in the same finalize.
    _synthesize_relation_connections()

    # Runs after the Relay loop has recorded EVERY type's
    # ``effective_globalid_strategy`` (so it reads complete data) and before
    # Phase 3 flips ``finalized`` - a Phase-2.5 raise here is recoverable via the
    # install step's re-entrancy guard (spec-031 Decision 8/10).
    # Reuses the multi-type-model tuple materialized at the top of this finalize.
    _audit_model_label_routing(multi_type_models)
    # Legal-but-silent sibling of the audit above: a non-primary type that also
    # emits model-label IDs collapses its identity onto the primary at decode
    # time. Warn (do not raise) and point at the ``type`` opt-out.
    _warn_model_label_secondary_collapse(multi_type_models)

    # Bind ``DjangoMutation`` declarations (spec-036 Slice 2 / Decision 12) in this
    # phase-2.5 window, after primary-type state is settled
    # (``_warn_model_label_secondary_collapse`` above) and before Phase 3's
    # ``strawberry.type`` freezes the schema classes - so each mutation's resolved
    # primary type, generated ``Input`` / ``PartialInput``, and ``<Name>Payload``
    # are materialized as module globals of ``mutations.inputs`` before
    # ``strawberry.Schema(...)`` resolves them. Function-local import (cycle-safe:
    # ``types/finalizer.py`` stays independent of the mutations package's
    # module-load order), mirroring the order / filter local-import idiom; the bind
    # only matters when the consumer has imported the mutations subsystem. A
    # missing / ambiguous primary target raises ``ConfigurationError``; no
    # ``DEFERRED_META_KEYS`` / ``ALLOWED_META_KEYS`` change (a mutation ``Meta`` is
    # its own namespace).
    # Reset the cross-pass materialization ledgers ONCE before the bind sequence so
    # finalize is retry-idempotent (feedback #6). Both bind passes clear their OWN
    # per-pass build cache and then rebuild fresh input class objects, but the
    # ``mutations.inputs`` / ``forms.inputs`` ledgers persist across passes (the
    # ``ModelForm`` flavor rides ``bind_mutations`` yet writes the FORM ledger; the
    # plain-form payload writes the MUTATION ledger), so neither pass can soundly
    # clear them itself - a per-pass clear would wipe the sibling pass's entries.
    # Without this, a re-call after a fixable later-phase failure (the documented
    # recover-in-place path) hit a spurious distinct-class collision in
    # ``materialize_generated_input_class`` that masked the original, now-fixed
    # error. Parked module globals are overwritten in place by the next ``setattr``
    # (the parked-globals lifecycle), so a ledger-only clear is safe. ``registry``
    # is NOT cleared here - this resets only the emit ledgers, not declarations.
    # TODO(spec-039 Slice 2): Replace these hand-maintained direct clears with
    # the registered subsystem-clear list from `registry.py`, iterated through
    # `_clear_if_importable`. The serializer input namespace is behind the DRF
    # soft-import guard, so the new mechanism must be import-guarded by default.
    # Pseudo flow:
    #   - Iterate the registered subsystem-clear targets from `registry.py`.
    #   - For each target, call `_clear_if_importable(...)` and invoke the clear
    #     callback only when its module can be imported under current dependencies.
    #   - Do not special-case serializer clears; registering static strings keeps
    #     DRF out of the finalizer import path.
    from ..forms.inputs import clear_form_input_namespace
    from ..mutations.inputs import clear_mutation_input_namespace
    from ..mutations.sets import bind_mutations

    clear_mutation_input_namespace()
    clear_form_input_namespace()
    bind_mutations()
    # Bind plain ``DjangoFormMutation`` declarations (spec-038 Slice 2 / Decision
    # 6 / Decision 13) in the SAME phase-2.5 window. The model-less plain-form
    # ledger is disjoint from the ``DjangoMutation`` ledger ``bind_mutations()``
    # drains; the ``DjangoModelFormMutation`` flavor is a ``DjangoMutation``
    # subclass and already bound via ``bind_mutations()`` above, so this drains
    # ONLY the plain-form registry, materializing each plain form's form-derived
    # input + its pinned ``{ ok errors }`` payload before ``strawberry.Schema(...)``
    # resolves them. Function-local import (cycle-safe, mirroring the
    # ``bind_mutations`` idiom); the bind only matters when the consumer imported
    # the form-mutations subsystem.
    from ..forms.sets import bind_form_mutations

    bind_form_mutations()
    _bind_filtersets()
    _bind_ordersets()

    # Field-surface audit: after relation/connection synthesis has settled each
    # type's annotation set and before Phase 3 freezes it. Catches an empty
    # surface (``Meta.fields = ()``) and a camel-case name collision between two
    # distinct fields - both of which Strawberry otherwise reports late and
    # without DjangoType attribution (the latter as a silent field drop).
    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        _audit_field_surface(type_cls, definition)

    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        strawberry.type(type_cls, name=definition.name, description=definition.description)
        definition.finalized = True

    registry.mark_finalized()


def _bind_set_owner_common(
    set_cls: type,
    definition: DjangoTypeDefinition,
    *,
    get_model: Callable[[type], type[models.Model] | None],
    format_model_mismatch: Callable[[type, DjangoTypeDefinition], str],
    before_second_owner_check: (
        Callable[[type, DjangoTypeDefinition, DjangoTypeDefinition], None] | None
    ),
    related_attr: str,
    format_target_mismatch: Callable[..., str],
) -> None:
    """Bind ``set_cls._owner_definition`` with shared first-bind/idempotency/target checks.

    The phase-2.5 owner-binding skeleton shared by FilterSet and OrderSet (the
    0.0.9 DRY pass, ``docs/feedback.md`` Major 2). Family-specific behaviour
    enters through hooks:

    - ``get_model`` reads the set's ``Meta.model`` (FilterSet exposes it via
      ``_meta``, OrderSet via the raw ``Meta``).
    - ``format_model_mismatch`` / ``format_target_mismatch`` produce the
      family-named error messages.
    - ``before_second_owner_check`` is the filter-only own-PK Relay-identity
      axis (``None`` for orders -- ``ORDER BY id`` uses the column, not the
      GraphQL ID type, so own-PK identity is not an owner-dependent axis there).
    - ``related_attr`` is ``related_filters`` / ``related_orders``.

    First binding stores ``definition`` after rejecting a ``Meta.model``
    unrelated to the owner's (``definition.model`` must BE the set's model or
    derive from it; otherwise the set's lookups would run against a queryset of
    the wrong model, and the mismatch surfaces here at finalize rather than as
    an opaque query-time ``FieldError``). Re-binding the same
    ``(set_cls, definition)`` pair is idempotent (partial-finalize recovery). A
    second, distinct owner runs the optional pre-check then the declared-
    relation-target agreement walk: every declared related target must resolve
    to the EXACT same ``DjangoTypeDefinition`` AND ``graphql_type_name`` across
    both owners.

    Scope note: ``related_target_for`` resolves via the process-global
    ``registry.primary_for(target_model)`` keyed on the TARGET model -- not the
    owner -- so for two legitimate owners (which share the set's ``Meta.model``)
    the relation targets are invariant. The own-PK identity is the real
    owner-dependent axis, which is why only the filter side wires a pre-check.
    """
    previous: DjangoTypeDefinition | None = getattr(set_cls, "_owner_definition", None)
    if previous is None:
        set_model = get_model(set_cls)
        if (
            set_model is not None
            and definition.model is not None
            and not issubclass(definition.model, set_model)
        ):
            raise ConfigurationError(format_model_mismatch(set_cls, definition))
        set_cls._owner_definition = definition
        return
    if previous is definition:
        return
    if before_second_owner_check is not None:
        before_second_owner_check(set_cls, previous, definition)
    related = getattr(set_cls, related_attr, {}) or {}
    for field_name in related:
        prev_target = previous.related_target_for(field_name)
        new_target = definition.related_target_for(field_name)
        if prev_target is None and new_target is None:
            continue
        # Short-circuits before indexing a ``None`` target: an exactly-one-None
        # pair diverges, as does a both-present pair whose resolved definition
        # or GraphQL type name differs.
        diverges = (
            prev_target is None
            or new_target is None
            or prev_target[0] is not new_target[0]
            or prev_target[0].graphql_type_name != new_target[0].graphql_type_name
        )
        if diverges:
            raise ConfigurationError(
                format_target_mismatch(
                    set_cls,
                    previous,
                    definition,
                    field_name,
                    prev_target,
                    new_target,
                ),
            )


def _bind_filterset_owner(filterset_cls: type, definition: DjangoTypeDefinition) -> None:
    """Bind ``filterset_cls._owner_definition`` with strict multi-owner validation.

    First binding writes ``filterset_cls._owner_definition = definition``
    and returns. Re-binding the same ``(filterset_cls, definition)``
    pair is idempotent (supports partial-finalize recovery per spec-027
    Decision 6 #"Partial-finalize lifecycle"). A second, distinct owner triggers the
    H2-rev8 strict-equality check across the two owner-dependent axes:

    1. **Own-PK Relay identity.** A filterset's own primary key resolves
       to a Relay ``GlobalID`` typed to the *owner* - keyed on
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
    type names) per spec-027 #"owning `FilterSet`'s target `DjangoType`".

    Scope note: ``related_target_for`` resolves a relation's target via the
    process-global ``registry.primary_for(target_model)`` lookup keyed on
    the TARGET model - NOT on the owner - so for two legitimate owners
    (which necessarily share the filterset's ``Meta.model``) the relation
    targets are invariant and cannot diverge. The own-PK identity is the
    real owner-dependent axis. Widening the relation walk to every FK / PK
    declared via ``Meta.fields`` would therefore guard a non-divergent
    surface and stays deferred (spec-027 #"Relation traversal under") until
    real demand surfaces.
    """
    _bind_set_owner_common(
        filterset_cls,
        definition,
        get_model=lambda cls: cls._meta.model,
        format_model_mismatch=_format_owner_model_mismatch_error,
        before_second_owner_check=_check_filterset_owner_pk_identity,
        related_attr="related_filters",
        format_target_mismatch=_format_owner_mismatch_error,
    )


def _check_filterset_owner_pk_identity(
    filterset_cls: type,
    previous: DjangoTypeDefinition,
    new: DjangoTypeDefinition,
) -> None:
    """Filter-only own-PK Relay-identity axis for multi-owner binding.

    A filterset's own primary key resolves to a Relay ``GlobalID`` typed to the
    *owner* -- keyed on ``owner.origin``'s Relay-node-ness and its
    ``graphql_type_name``. Two owners that disagree on either would make the
    shared filterset's ``id`` filter resolve to a different (or differently-
    typed) GlobalID depending on which owner finalized first; only the FIRST
    binding is stored, so the second owner would silently mis-resolve. Wired as
    the ``before_second_owner_check`` hook of ``_bind_set_owner_common``; the
    order side passes ``None`` because ``ORDER BY id`` uses the column, not the
    GraphQL ID type (spec-027 H2 of rev8 / spec-028 Decision 6).
    """
    prev_is_relay = implements_relay_node(previous.origin)
    new_is_relay = implements_relay_node(new.origin)
    if prev_is_relay != new_is_relay or (
        prev_is_relay and previous.graphql_type_name != new.graphql_type_name
    ):
        raise ConfigurationError(
            _format_owner_pk_mismatch_error(filterset_cls, previous, new),
        )


def _format_owner_mismatch_error(
    filterset_cls: type,
    previous: DjangoTypeDefinition,
    new: DjangoTypeDefinition,
    field_name: str,
    prev_target: tuple[DjangoTypeDefinition, models.Field] | None,
    new_target: tuple[DjangoTypeDefinition, models.Field] | None,
) -> str:
    """Return the canonical H2-rev8 multi-owner-mismatch message.

    Sibling of ``_format_unresolved_targets_error`` /
    ``_format_ambiguity_error`` above; all three formatters live at the
    top of this module so consumer error matching stays grep-stable.
    Names both owners' qualified names, the offending FilterSet, the
    offending field, and both resolved target type names per spec-027
    #"owning `FilterSet`'s target `DjangoType`".
    """
    prev_name = prev_target[0].origin.__qualname__ if prev_target is not None else "<unresolved>"
    new_name = new_target[0].origin.__qualname__ if new_target is not None else "<unresolved>"
    return (
        f"FilterSet {filterset_cls.__qualname__} cannot bind to multiple owners with "
        f"diverging targets: {previous.origin.__qualname__} resolves "
        f"{field_name!r} to {prev_name}, but {new.origin.__qualname__} resolves it "
        f"to {new_name}. Declare separate FilterSet subclasses for the diverging "
        "owners (per spec-027 H2 of rev8)."
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
        "separate FilterSet subclasses for the diverging owners (per spec-027 H2 of rev8)."
    )


def _format_owner_model_mismatch_error(filterset_cls: type, owner: DjangoTypeDefinition) -> str:
    """Return the first-bind owner/filterset model-mismatch message.

    Fires on the FIRST owner binding when a ``Meta.filterset_class`` is
    keyed on a model unrelated to its owner type's model. Surfacing it at
    finalize - rather than as the opaque query-time ``FieldError`` the
    mismatch would otherwise raise once a lookup runs against the wrong
    model's queryset - names both models so the consumer can realign the
    wiring. Grep-stable alongside the other ``_format_*`` finalize-error
    helpers (H-core-3 of the pre-merge review).
    """
    return (
        f"FilterSet {filterset_cls.__qualname__} is declared as the filterset_class "
        f"of {owner.origin.__qualname__} (model {owner.model.__name__}), but its own "
        f"Meta.model is {filterset_cls._meta.model.__name__}. A filterset's Meta.model "
        f"must be its owner's model - or a base the owner derives from - so the "
        f"filterset's lookups resolve against the owner's queryset. Key "
        f"{filterset_cls.__qualname__} on {owner.model.__name__}, or attach it to a "
        f"{filterset_cls._meta.model.__name__} type."
    )


def _format_orphan_filtersets_error(orphans: list[type]) -> str:
    """Return the canonical orphan-``filter_input_type`` error message.

    Sorted by qualified name for deterministic output. When more than
    one orphan is present, the message uses the multi-orphan lead-in
    mirroring ``_format_unresolved_targets_error``'s shape; the single-
    orphan branch uses the spec-pinned actionable message from spec-027
    #"Bind the owner.".
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


def _format_unregistered_related_target_error(
    filterset_cls: type,
    field_name: str,
    child_filterset: type | None,
) -> str:
    """Return the canonical unregistered-``RelatedFilter``-target finalize message.

    Sibling of ``_format_orphan_filtersets_error`` /
    ``_format_owner_mismatch_error`` above; finalize-time formatters stay
    grouped here so consumer error matching stays grep-stable. Mirrors the
    runtime message raised by ``FilterSet._iter_visibility_steps`` for the
    same misconfiguration so the two surfaces read as one contract.
    """
    child_model = getattr(getattr(child_filterset, "_meta", None), "model", None)
    target_label = getattr(child_model, "__qualname__", "<unresolved>")
    return (
        f"Cannot finalize Django types: FilterSet {filterset_cls.__qualname__} "
        f"declares RelatedFilter {field_name!r} targeting {target_label}, but no "
        f"DjangoType is registered for that model. The related branch's visibility "
        f"scoping runs the target type's get_queryset (spec-027 Decision 8 step 3); "
        f"without a registered target the branch would silently return unfiltered "
        f"rows at request time. Register a DjangoType for {target_label} or remove "
        f"the RelatedFilter."
    )


def _bind_orderset_owner(orderset_cls: type, definition: DjangoTypeDefinition) -> None:
    """Bind ``orderset_cls._owner_definition`` with first-bind / related / idempotency checks.

    First binding writes ``orderset_cls._owner_definition = definition``
    and returns. Re-binding the same ``(orderset_cls, definition)``
    pair is idempotent (supports partial-finalize recovery per
    spec-028 Decision 6). A second, distinct owner triggers the
    related-target-agreement check across every declared
    ``RelatedOrder``.

    Per spec-028 Decision 6 second-paragraph rationale, the order
    side does NOT enforce the filter side's own-PK Relay-identity
    check -- ``ORDER BY id`` against any model uses the column, not
    the GraphQL ID type, so own-PK identity is not an
    owner-dependent axis here.
    """
    _bind_set_owner_common(
        orderset_cls,
        definition,
        get_model=lambda cls: getattr(getattr(cls, "Meta", None), "model", None),
        format_model_mismatch=_format_owner_orderset_model_mismatch_error,
        before_second_owner_check=None,
        related_attr="related_orders",
        format_target_mismatch=_format_owner_ordersets_mismatch_error,
    )


def _format_owner_ordersets_mismatch_error(
    orderset_cls: type,
    previous: DjangoTypeDefinition,
    new: DjangoTypeDefinition,
    field_name: str,
    prev_target: tuple[DjangoTypeDefinition, models.Field] | None,
    new_target: tuple[DjangoTypeDefinition, models.Field] | None,
) -> str:
    """Return the canonical multi-owner-mismatch message for ordersets.

    Sibling of ``_format_owner_mismatch_error`` (filter side); the wording
    names ``OrderSet`` / ``Meta.orderset_class`` so the consumer error
    surface tells the maintainer which sidecar is broken. Grep-stable
    alongside the other ``_format_*`` finalize-error helpers.
    """
    prev_name = prev_target[0].origin.__qualname__ if prev_target is not None else "<unresolved>"
    new_name = new_target[0].origin.__qualname__ if new_target is not None else "<unresolved>"
    return (
        f"OrderSet {orderset_cls.__qualname__} cannot bind to multiple owners with "
        f"diverging targets: {previous.origin.__qualname__} resolves "
        f"{field_name!r} to {prev_name}, but {new.origin.__qualname__} resolves it "
        f"to {new_name}. Declare separate OrderSet subclasses for the diverging "
        "owners (per spec-028 Decision 6)."
    )


def _format_owner_orderset_model_mismatch_error(
    orderset_cls: type,
    owner: DjangoTypeDefinition,
) -> str:
    """Return the first-bind owner/orderset model-mismatch message.

    Fires on the FIRST owner binding when a ``Meta.orderset_class`` is
    keyed on a model unrelated to its owner type's model. Names all four
    entities (owner type, owner model, orderset class, orderset model)
    per spec-028 Revision 4 H2 / Decision 6 so the consumer can realign
    the wiring at finalize time rather than seeing an opaque query-time
    ``FieldError`` once an ``order_by(...)`` lookup runs against the wrong
    model's queryset. Grep-stable alongside the other ``_format_*``
    finalize-error helpers.
    """
    orderset_model = getattr(getattr(orderset_cls, "Meta", None), "model", None)
    orderset_model_name = orderset_model.__name__ if orderset_model is not None else "<unset>"
    return (
        f"OrderSet {orderset_cls.__qualname__} is declared as the orderset_class "
        f"of {owner.origin.__qualname__} (model {owner.model.__name__}), but its own "
        f"Meta.model is {orderset_model_name}. An orderset's Meta.model must be its "
        f"owner's model -- or a base the owner derives from -- so the orderset's "
        f"order_by(...) lookups resolve against the owner's queryset. Key "
        f"{orderset_cls.__qualname__} on {owner.model.__name__}, or attach it to a "
        f"{orderset_model_name} type."
    )


def _format_orphan_ordersets_error(orphans: list[type]) -> str:
    """Return the canonical orphan-``order_input_type`` error message.

    Sorted by qualified name for deterministic output. When more than
    one orphan is present, the message uses the multi-orphan lead-in
    mirroring ``_format_orphan_filtersets_error``'s shape; the single-
    orphan branch uses the spec-028 actionable message.
    """
    if len(orphans) == 1:
        cls = orphans[0]
        return (
            f"OrderSet '{cls.__name__}' is referenced via order_input_type(...) but "
            f"never assigned to a DjangoType via Meta.orderset_class. Add "
            f"'orderset_class = {cls.__name__}' to the relevant DjangoType's Meta."
        )
    lines = [f"  - {cls.__module__}.{cls.__qualname__}" for cls in orphans]
    body = "\n".join(lines)
    return (
        "OrderSets referenced via order_input_type(...) but not wired to any "
        f"DjangoType:\n{body}\n\n"
        "Add 'orderset_class = <Name>' to the relevant DjangoType's Meta for each."
    )


@dataclass(frozen=True)
class _SidecarBindingSpec:
    """Per-family configuration for the shared phase-2.5 binding driver.

    The ordered four-subpass binding skeleton (``_bind_sidecar_sets``) is shared
    by FilterSet and OrderSet (the 0.0.9 DRY pass, ``docs/feedback.md`` Major 2);
    this carries the family differences. ``expand`` runs Layer-4 expansion for
    one set; ``post_expand_audit`` is the optional filter-only
    unregistered-``RelatedFilter``-target walk (``None`` for orders).
    """

    definition_attr: str
    expand_label_noun: str
    related_noun: str
    bind_owner: Callable[[type, DjangoTypeDefinition], None]
    helper_ledger: set[type]
    factory_cls: type
    materialize: Callable[[str, type], None]
    format_orphans: Callable[[list[type]], str]
    expand: Callable[[type], None]
    post_expand_audit: Callable[[list[type]], None] | None


def _expand_filterset(filterset_cls: type) -> None:
    """Layer-4 filterset expansion (resolves lazy ``RelatedFilter`` refs)."""
    filterset_cls.get_filters()


def _expand_orderset(orderset_cls: type) -> None:
    """Layer-4 orderset expansion.

    ``OrderSet.get_fields()`` stores ``RelatedOrder`` instances without eagerly
    resolving their lazy class refs (unlike the filter side's ``get_filters()``
    which calls ``_expand_related_filter`` reading ``f.filterset``), so this
    also reads ``related.orderset`` to force Layer-2 resolution at the
    subpass-2 boundary -- so an unresolved ``RelatedOrder('...')`` rewraps as
    ``ConfigurationError`` with ``__cause__`` preserved here.
    """
    orderset_cls.get_fields()
    for related in getattr(orderset_cls, "related_orders", {}).values():
        _ = related.orderset


def _audit_unregistered_related_filter_targets(wired: list[type]) -> None:
    """Filter-only subpass 2.5: every reachable ``RelatedFilter`` target must be registered.

    A related branch's visibility scoping runs the target type's
    ``get_queryset`` (spec-027 Decision 8 step 3); an unregistered target would
    make the branch unfulfillable even though its input field is materialized
    into the schema, so the misconfiguration surfaces here -- at finalize,
    naming the filterset -- instead of on the first request that activates the
    branch (where ``FilterSet._iter_visibility_steps`` raises the runtime
    sibling of this error). The walk is transitive with a visited set; cyclic
    cross-references (``BookFilter`` <-> ``ShelfFilter``) are legal.
    """
    seen_filtersets: set[type] = set(wired)
    pending_filtersets: list[type] = list(wired)
    while pending_filtersets:
        filterset_cls = pending_filtersets.pop()
        for field_name, related_filter in (
            getattr(filterset_cls, "related_filters", {}) or {}
        ).items():
            child_filterset = related_filter.filterset
            if child_filterset is not None and child_filterset not in seen_filtersets:
                seen_filtersets.add(child_filterset)
                pending_filtersets.append(child_filterset)
            if filterset_cls._target_type_for_related_filter(related_filter) is None:
                raise ConfigurationError(
                    _format_unregistered_related_target_error(
                        filterset_cls,
                        field_name,
                        child_filterset,
                    ),
                )


def _bind_sidecar_sets(spec: _SidecarBindingSpec) -> None:
    """Run the ordered phase-2.5 subpasses for one sidecar family.

    Shared by ``_bind_filtersets`` / ``_bind_ordersets`` (the 0.0.9 DRY pass,
    ``docs/feedback.md`` Major 2). The ordering is load-bearing: every subpass
    MUST complete across all wired types before the next starts so cross-set
    references resolve against bound owners regardless of registration order.

    1. Bind every owner (``spec.bind_owner``) before any expansion runs.
    2. Expand every set (``spec.expand``); ``ImportError`` from an unresolved
       lazy related target and any other exception rewrap as
       ``ConfigurationError`` naming the offending set (uniform finalize-time
       error shape). ``repr(exc)`` keeps the underlying error fully in the
       consumer-visible message and ``from exc`` preserves ``__cause__``.
    3. (Optional) ``spec.post_expand_audit`` -- the filter-only transitive
       unregistered-``RelatedFilter``-target walk.
    4. Orphan validation: helper-referenced sets not wired to any DjangoType
       raise via ``spec.format_orphans``. Runs BEFORE materialization so a
       failure leaves no half-materialized input classes in the namespace.
    5. Materialize every built input class as a module global.
    """
    # Subpass 1: bind every owner before any expansion runs.
    wired: list[type] = []
    for _type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        set_cls = getattr(definition, spec.definition_attr)
        if set_cls is None:
            continue
        spec.bind_owner(set_cls, definition)
        wired.append(set_cls)

    # Subpass 2: expand every set; cross-references now resolve.
    for set_cls in wired:
        # PERF203 (try/except in a loop) is intentional: the per-iteration try
        # attributes the failure to this specific set_cls.
        try:
            spec.expand(set_cls)
        except ImportError as exc:  # noqa: PERF203
            raise ConfigurationError(
                f"Cannot finalize Django types: {spec.expand_label_noun} "
                f"{set_cls.__qualname__} references an unresolved "
                f"{spec.related_noun} target. {exc}",
            ) from exc
        except ConfigurationError:
            raise
        except Exception as exc:
            raise ConfigurationError(
                f"Cannot finalize Django types: {spec.expand_label_noun} "
                f"{set_cls.__qualname__} raised during expansion. {exc!r}",
            ) from exc

    # Subpass 2.5 (filter-only today): unregistered related-target audit.
    if spec.post_expand_audit is not None:
        spec.post_expand_audit(wired)

    # Subpass 3: orphan validation against the helper-tracked set. Runs BEFORE
    # materialization so a failure here doesn't leave half-materialized input
    # classes in the inputs-module namespace.
    wired_set = set(wired)
    orphans = sorted(
        spec.helper_ledger - wired_set,
        key=lambda cls: f"{cls.__module__}.{cls.__qualname__}",
    )
    if orphans:
        raise ConfigurationError(spec.format_orphans(orphans))

    # Subpass 4: materialize every built input class as a module global.
    for set_cls in wired:
        factory = spec.factory_cls(set_cls)
        # Touch ``.arguments`` to drive ``_ensure_built`` (idempotent through
        # the factory's class-level cache); the cache is shared across
        # instances so dependent input classes built by one factory are visible
        # to a sibling factory's materialize loop.
        _ = factory.arguments
        for name, input_cls in factory.input_object_types.items():
            spec.materialize(name, input_cls)


def _bind_ordersets() -> None:
    """Run the four ordered phase-2.5 subpasses for orderset binding.

    Subpass 1 -- bind every owner. Walks every wired definition and
    binds ``orderset_cls._owner_definition`` via
    ``_bind_orderset_owner``. The first-bind model-compat check and
    the related-target-agreement check reject mis-wired orderset_class
    assignments before any subsequent subpass runs.

    Subpass 2 -- expand every orderset. Calls
    ``orderset_cls.get_fields()`` so Layer-4 expansion resolves lazy
    ``RelatedOrder`` refs and cycle guards apply uniformly.
    ``ImportError`` from
    ``LazyRelatedClassMixin.resolve_lazy_class`` is rewrapped as
    ``ConfigurationError`` with ``__cause__`` preserving the
    original. Any other exception rewraps as ``ConfigurationError``
    with ``repr(exc)`` keeping the original class + args in the
    consumer-visible message (uniform finalize-time error shape).

    Subpass 3 -- orphan validation. Compares the OrderSets passed to
    ``order_input_type(...)`` (per Decision 11) against the set of
    OrderSets wired via ``Meta.orderset_class``. Orphans raise
    ``ConfigurationError`` with the actionable suggestion to add the
    missing ``orderset_class = <Name>``. Runs BEFORE materialization
    so an orphan failure leaves no partial state in
    ``_materialized_names`` /
    ``OrderArgumentsFactory.input_object_types``; otherwise a re-run
    of ``finalize_django_types()`` after fixing the orphan would see
    stale ledger entries from the prior failed attempt (mirrors the
    **shipped** filter side's authoritative ordering).

    Subpass 4 -- materialize input classes. Reads
    ``OrderArgumentsFactory(orderset_cls).arguments`` to trigger the
    BFS build (idempotent through the factory's class-level cache),
    then materializes EVERY built class from the factory's
    ``input_object_types`` ledger as a real module global of
    ``orders.inputs`` via ``materialize_input_class(name, cls)``.
    """
    # Local imports: keep ``types/finalizer.py`` independent of the orders
    # package's module-load order. The phase-2.5 binding only runs when a
    # definition declares ``orderset_class``, which only works when the orders
    # subsystem has been imported by the consumer.
    from ..orders import _helper_referenced_ordersets
    from ..orders.factories import OrderArgumentsFactory
    from ..orders.inputs import materialize_input_class

    _bind_sidecar_sets(
        _SidecarBindingSpec(
            definition_attr="orderset_class",
            expand_label_noun="orderset",
            related_noun="related-order",
            bind_owner=_bind_orderset_owner,
            helper_ledger=_helper_referenced_ordersets,
            factory_cls=OrderArgumentsFactory,
            materialize=materialize_input_class,
            format_orphans=_format_orphan_ordersets_error,
            expand=_expand_orderset,
            post_expand_audit=None,
        ),
    )


def _bind_filtersets() -> None:
    """Run the four ordered phase-2.5 subpasses for filterset binding.

    Subpass 1 - bind every owner. Walks every wired definition and
    binds ``filterset_cls._owner_definition`` via
    ``_bind_filterset_owner``. The H2-rev8 strict-equality check
    rejects diverging multi-owner reuse before any subsequent subpass
    runs.

    Subpass 2 - expand every filterset. Calls
    ``filterset_cls.get_filters()`` so Layer-4 expansion resolves lazy
    ``RelatedFilter`` refs and cycle guards apply uniformly. Owner
    binding from subpass 1 is visible to every filterset's owner-aware
    ``filter_for_field`` / ``filter_for_lookup`` overrides regardless
    of which type-cls is iterated first.

    Subpass 3 - orphan validation. Compares the FilterSets passed to
    ``filter_input_type(...)`` (per Decision 11) against the set of
    FilterSets wired via ``Meta.filterset_class``. Orphans raise
    ``ConfigurationError`` per spec-027 #"Bind the owner." with the actionable
    suggestion to add the missing ``filterset_class = <Name>``. Runs
    BEFORE materialization so an orphan failure leaves no partial
    state in ``_materialized_names`` /
    ``FilterArgumentsFactory.input_object_types``; otherwise a re-run
    of ``finalize_django_types()`` after fixing the orphan would see
    stale ledger entries from the prior failed attempt.

    Subpass 4 - materialize input classes. Reads the
    ``FilterArgumentsFactory(filterset_cls).arguments`` property
    (triggers BFS build, idempotent through the factory's class-level
    cache) and materializes EVERY built class from the factory's
    ``input_object_types`` ledger as a real module global of
    ``filters.inputs`` via ``materialize_input_class(name, cls)``. A
    second factory instance for a sibling root sees the cached build
    via the class-level dict.
    """
    # Local imports: keep ``types/finalizer.py`` independent of the filters
    # package's module-load order. The phase-2.5 binding only runs when a
    # definition declares ``filterset_class``, which only works when the filters
    # subsystem has been imported by the consumer.
    from ..filters import _helper_referenced_filtersets
    from ..filters.factories import FilterArgumentsFactory
    from ..filters.inputs import materialize_input_class

    _bind_sidecar_sets(
        _SidecarBindingSpec(
            definition_attr="filterset_class",
            expand_label_noun="filterset",
            related_noun="related-filter",
            bind_owner=_bind_filterset_owner,
            helper_ledger=_helper_referenced_filtersets,
            factory_cls=FilterArgumentsFactory,
            materialize=materialize_input_class,
            format_orphans=_format_orphan_filtersets_error,
            expand=_expand_filterset,
            post_expand_audit=_audit_unregistered_related_filter_targets,
        ),
    )
