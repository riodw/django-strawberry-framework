"""The sync + async create / update / delete write pipeline (spec-036 Slice 3).

The write-side runtime: one pipeline per operation, in a sync and an async form
(spec-036 Decision 8). The pipeline is

    decode -> locate -> authorize -> validate -> write -> re-fetch/snapshot -> payload

and the load-bearing invariants this module owns:

- **One ``transaction.atomic()`` boundary** wraps authorize -> snapshot, and the
  **async path runs the whole sync ORM pipeline in a single**
  ``sync_to_async(thread_sensitive=True)`` **call** (spec-036 AR-M4): the write,
  its M2M ``.set(...)`` calls, and the payload snapshot are atomic and never
  interleave ORM work with ``await``s.
- **Relation ``GlobalID`` decode is type-checked against the relation's Django
  target model** (spec-036 AR-H4): a well-formed id for the wrong model is a
  ``FieldError`` on that relation field, never coerced cross-model and never a
  raw ``DoesNotExist``.
- **``update`` / ``delete`` locate runs through the target type's
  ``get_queryset`` for visibility only** (spec-036 Decision 10): a hidden row is
  not-found, indistinguishable from a genuinely missing row (no existence leak).
- **Write authorization is a separate seam** (spec-036 Decision 15): the pipeline
  calls the mutation's ``check_permission`` (which delegates to
  ``Meta.permission_classes``) and maps a ``False`` return to a top-level
  ``GraphQLError`` - before validation for ``create``, after the visibility
  lookup for ``update`` / ``delete``.
- **``full_clean()`` feeds the ``FieldError`` envelope** (spec-036 Decision 7 /
  Decision 8 step 4): a ``ValidationError`` returns a null-object payload, never
  an exception at the GraphQL boundary; on update, ``exclude`` is the unprovided
  field set MINUS any unprovided field co-participating in a constraint with a
  provided field (spec-036 AR-H2). ``full_clean()`` runs ``validate_constraints``,
  so a ``UniqueConstraint`` duplicate is caught here as a ``ValidationError``
  before ``save()`` (Major-2); a multi-field constraint keys to the ``"__all__"``
  sentinel (spec-036 AR-M3). A concurrent-race ``IntegrityError`` at ``save()``
  maps to the same envelope as a documented best-effort fallback.
- **The post-write re-fetch is by pk WITHOUT the visibility filter** (spec-036
  Medium-1) and routes through ``apply_connection_optimization`` so the
  ``spec-035`` G2 gate keeps ``select_related`` / ``prefetch_related`` and applies
  NO ``.only(...)`` deferral under the mutation operation (Decision 9 comes for
  free). ``delete`` materializes the snapshot fully (relations loaded) BEFORE
  ``delete()`` (spec-036 AR-M5 / Medium-2).
- **``SyncMisuseError`` discipline** is inherited from
  ``apply_type_visibility_sync``: a sync mutation meeting an ``async def
  get_queryset`` closes the coroutine and raises (spec-036 Decision 8).

The ``DjangoMutationField`` factory + signature synthesis are the sibling module
``fields.py``. The live products write surface (a products ``Mutation`` +
``config/schema.py`` wiring + the live ``CaptureQueriesContext`` assertion) is
Slice 4, NOT this slice.
"""

from __future__ import annotations

from typing import Any

import strawberry
from asgiref.sync import sync_to_async
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import IntegrityError, transaction
from graphql import GraphQLError
from strawberry import relay

from ..optimizer.extension import (
    apply_connection_optimization,
    mutation_payload_child_selections,
)
from ..types.relay import decode_global_id
from ..utils.inputs import graphql_camel_name
from ..utils.querysets import apply_type_visibility_sync, initial_queryset
from .inputs import NON_FIELD_ERROR_KEY, FieldError, payload_object_slot

# The async-pipeline recourse appended to a ``SyncMisuseError`` raised when an
# async ``get_queryset`` is met inside the (sync) ORM pipeline. The whole
# pipeline runs synchronously even on the async surface (it executes inside one
# ``sync_to_async`` worker thread - spec-036 AR-M4), so an ``async def
# get_queryset`` can never be awaited here regardless of operation context; the
# recourse is to make the target hook sync.
_MUTATION_ASYNC_RECOURSE = (
    "A DjangoMutation runs its ORM pipeline synchronously (under one "
    "sync_to_async call on the async surface), so it cannot await an async "
    "get_queryset hook; redefine the target type's get_queryset as a sync method."
)


def _decode_relations(
    model: type,
    data: Any,
) -> tuple[dict[str, Any], list[Any], FieldError | None]:
    """Decode the provided input fields into model attrs + M2M pk lists (spec-036 Decision 8 step 1).

    Walks the input dataclass's provided fields (``UNSET`` stripped - the
    ``UNSET`` / ``null`` / value tri-state is preserved: ``UNSET`` means
    "omitted", an explicit ``None`` is kept as a provided ``None``). For each
    forward FK / OneToOne ``<field>_id`` whose value is a ``relay.GlobalID``,
    ``decode_global_id`` resolves ``(target_type, node_id)`` and the decoded
    target model is **type-checked against the relation's Django target model**
    (spec-036 AR-H4): a wrong-type id returns a ``FieldError`` on that relation
    field, never a cross-model pk lookup and never a raw ``DoesNotExist``. A raw
    pk scalar (a non-Relay target) is passed through unchanged - no decode runs.

    Returns ``(scalar_and_fk_attrs, m2m_assignments, error)`` where
    ``scalar_and_fk_attrs`` is the ``{model_attr: value}`` map for ``setattr`` /
    ``Model(**...)`` (FK as ``<field>_id`` -> pk), ``m2m_assignments`` is a list
    of ``(m2m_field_name, [pk, ...])`` deferred to the post-save write step
    (AR-M1), and ``error`` is the first decode ``FieldError`` or ``None``.
    """
    fk_by_attr, m2m_by_name = _relation_field_index(model)
    scalar_and_fk_attrs: dict[str, Any] = {}
    m2m_assignments: list[Any] = []

    for field in data.__strawberry_definition__.fields:
        python_name = field.python_name
        value = getattr(data, python_name, strawberry.UNSET)
        if value is strawberry.UNSET:
            continue

        # A decode failure keys to the input field's GraphQL name (what the
        # client sent), e.g. ``categoryId`` - distinct from a ``full_clean``
        # error, which keys to the MODEL field name. ``graphql_name`` is the
        # field's wire alias (or ``python_name`` when no alias differs).
        graphql_name = field.graphql_name or graphql_camel_name(python_name)

        m2m_field = m2m_by_name.get(python_name)
        if m2m_field is not None:
            pks, error = _decode_relation_id_list(graphql_name, value, m2m_field)
            if error is not None:
                return {}, [], error
            m2m_assignments.append((python_name, pks))
            continue

        fk_field = fk_by_attr.get(python_name)
        if fk_field is not None:
            pk, error = _decode_single_relation_id(graphql_name, value, fk_field)
            if error is not None:
                return {}, [], error
            scalar_and_fk_attrs[python_name] = pk
            continue

        scalar_and_fk_attrs[python_name] = value

    return scalar_and_fk_attrs, m2m_assignments, None


def _relation_field_index(model: type) -> tuple[dict[str, Any], dict[str, Any]]:
    """Index a model's forward FK/OneToOne (by ``<field>_id`` attr) and M2M (by name).

    Single-sources the input-attr-to-relation-field mapping the generator's
    naming scheme implies (``<field>_id`` for forward FK / OneToOne, the plain
    field name for M2M - ``mutations/inputs.py::relation_input_annotation``), so
    the decode reads the same scheme the input was built from, AND so the
    partial-update provided-field mapping (``_provided_attr_names``) can reverse a
    ``<field>_id`` attr back to its model field name from the index rather than by
    a blind string-suffix strip (which would mangle a *scalar* field literally
    named ``<x>_id``, e.g. ``library.TaggedItem.object_id``).

    A forward FK / OneToOne is keyed by its ``<field>_id`` input attr. The guard
    requires a **concrete DB column** (``column is not None``) and a non-``None``
    ``related_model`` so a *virtual* relation - a ``GenericForeignKey`` reports
    ``is_relation=True`` with ``column=None`` and ``related_model=None`` - is
    never indexed as a decode-able FK (spec-036 L3-1). The generator already
    excludes virtual relations from the input, so this only hardens the index
    against ever mis-mapping one.
    """
    fk_by_attr: dict[str, Any] = {}
    m2m_by_name: dict[str, Any] = {}
    for field in model._meta.get_fields():
        if getattr(field, "many_to_many", False):
            if getattr(field, "concrete", False) or not field.auto_created:
                m2m_by_name[field.name] = field
        elif _is_forward_concrete_relation(field):
            fk_by_attr[f"{field.name}_id"] = field
    return fk_by_attr, m2m_by_name


def _is_forward_concrete_relation(field: Any) -> bool:
    """Return whether ``field`` is a forward FK / OneToOne with a real DB column (spec-036 L3-1).

    A concrete forward relation has both a non-``None`` ``column`` (a real DB
    column - a ``GenericForeignKey`` reports ``column=None``) and a non-``None``
    ``related_model`` (the type the relation id is checked against - a
    ``GenericForeignKey`` reports ``related_model=None``). This excludes virtual
    relations from the FK index so a scalar field that merely *ends in* ``_id`` is
    never reverse-mapped to a non-existent relation field.
    """
    if not getattr(field, "is_relation", False):
        return False
    return getattr(field, "column", None) is not None and field.related_model is not None


def _decode_single_relation_id(
    field_name: str,
    value: Any,
    relation_field: Any,
) -> tuple[Any, FieldError | None]:
    """Decode one FK / OneToOne id to a pk, type-checking a ``GlobalID`` (spec-036 AR-H4).

    A ``relay.GlobalID`` is decoded via ``decode_global_id`` and its resolved
    target model must be the relation's Django target model; a wrong-type id (or
    a malformed one - ``decode_global_id`` raises ``ConfigurationError``) returns
    a ``FieldError`` on ``field_name``, never a cross-model pk lookup. A raw pk
    scalar (the non-Relay-target case) passes through unchanged.
    """
    if not isinstance(value, relay.GlobalID):
        return value, None
    error = _wrong_type_field_error(field_name, value, relation_field)
    if error is not None:
        return None, error
    return value.node_id, None


def _decode_relation_id_list(
    field_name: str,
    value: Any,
    relation_field: Any,
) -> tuple[list[Any], FieldError | None]:
    """Decode an M2M ``list[<id>]`` to a list of pks, type-checking each ``GlobalID``.

    The list is the replace-set the post-save step assigns (AR-M1); each element
    is decoded by the same ``_decode_single_relation_id`` rule, so a wrong-type
    ``GlobalID`` anywhere in the list returns a ``FieldError`` on ``field_name``.
    """
    pks: list[Any] = []
    for element in value:
        pk, error = _decode_single_relation_id(field_name, element, relation_field)
        if error is not None:
            return [], error
        pks.append(pk)
    return pks, None


def _wrong_type_field_error(
    field_name: str,
    gid: relay.GlobalID,
    relation_field: Any,
) -> FieldError | None:
    """Return a wrong-type ``FieldError`` for a relation ``GlobalID``, or ``None`` (spec-036 AR-H4).

    ``decode_global_id`` resolves the id to its ``DjangoType``; the resolved
    type's model must be the relation's ``related_model``. Mirrors the identity
    check ``relay.py::_check_typed_match`` does for the typed node field, but
    against the relation target model rather than a node-field target, and yields
    a field-keyed ``FieldError`` (NOT a top-level ``GraphQLError``). A malformed
    id surfaces as a ``FieldError`` too (``decode_global_id`` raises
    ``ConfigurationError``), so a relation-id failure is uniformly field-keyed.
    """
    target_model = relation_field.related_model
    try:
        resolved_type, _node_id = decode_global_id(gid)
    except Exception:
        return _relation_error(field_name)
    resolved_model = resolved_type.__django_strawberry_definition__.model
    if resolved_model is not target_model:
        return _relation_error(field_name)
    return None


def _relation_error(field_name: str) -> FieldError:
    """Build the uniform wrong/invalid relation-id ``FieldError`` for ``field_name``."""
    return FieldError(
        field=field_name,
        messages=[f"Invalid id for relation {field_name!r}."],
    )


def _locate_instance(target_type: type, node_id: Any, info: Any) -> Any | None:
    """Locate an update / delete row through the visibility ``get_queryset`` (spec-036 Decision 10).

    ``apply_type_visibility_sync(target_type, initial_queryset(target_type),
    info).get(pk=node_id)`` - the same visibility queryset every read surface
    uses (and the ``_resolve_node_default`` locate shape). A miss
    (``DoesNotExist``) returns ``None``; the caller maps it to a not-found
    ``FieldError`` on ``id``, indistinguishable from a hidden row (no existence
    leak). An ``async def get_queryset`` met here raises ``SyncMisuseError``
    (``apply_type_visibility_sync`` closes the coroutine first).
    """
    model = target_type.__django_strawberry_definition__.model
    queryset = apply_type_visibility_sync(
        target_type,
        initial_queryset(target_type),
        info,
        _MUTATION_ASYNC_RECOURSE,
    )
    try:
        return queryset.get(pk=node_id)
    except model.DoesNotExist:
        return None


def _provided_attr_names(
    model: type,
    scalar_and_fk_attrs: dict[str, Any],
    m2m_assignments: list[Any],
) -> set[str]:
    """Return the model field names a partial input provided (for the AR-H2 exclude carve-out).

    Maps each decoded ``<field>_id`` FK attr back to its model field name
    (``category_id`` -> ``category``) so ``_unprovided_exclude`` reasons over
    model field names, and includes provided M2M field names.

    The FK-to-field reversal uses the model's **relation field index**
    (``_relation_field_index``) as the source of truth - a ``<field>_id`` attr is
    mapped to its relation field name ONLY when the index confirms it is a forward
    FK / OneToOne. A blind string-suffix strip (``attr[:-3] if
    attr.endswith("_id")``) would mangle a *scalar* model field literally named
    ``<x>_id`` (e.g. ``library.TaggedItem.object_id``) to ``<x>``, so the real
    scalar field would read as unprovided, be added to the ``full_clean(exclude=
    ...)`` set, and skip validation - surfacing later as a mis-labeled
    ``IntegrityError`` (spec-036 M3-1). Scalar attrs (including any ending in
    ``_id``) therefore stay under their real name.
    """
    fk_by_attr, _m2m_by_name = _relation_field_index(model)
    names: set[str] = set()
    for attr in scalar_and_fk_attrs:
        fk_field = fk_by_attr.get(attr)
        names.add(fk_field.name if fk_field is not None else attr)
    for m2m_name, _pks in m2m_assignments:
        names.add(m2m_name)
    return names


def _unprovided_exclude(model: type, provided_attrs: set[str]) -> list[str]:
    """Compute the ``full_clean(exclude=...)`` set for a partial update (spec-036 AR-H2).

    The set of model fields the ``PartialInput`` did NOT provide, **minus any
    unprovided field co-participating in a ``UniqueConstraint`` /
    ``unique_together`` / ``unique`` check with a *provided* field**. So a
    ``name``-only update still validates ``unique_item_per_category`` (the
    unprovided ``category`` is co-constrained with the provided ``name``, so it is
    NOT excluded), while a genuinely-unrelated unprovided field stays excluded
    (DRF ``partial=True`` parity - an unsent, unconstrained field never raises a
    spurious ``FieldError``).

    Reads ``model._meta.constraints`` (``UniqueConstraint`` only),
    ``model._meta.unique_together``, and per-field ``field.unique`` to find the
    constraint groups; a group with a provided member pins its other members out
    of the exclude set.
    """
    all_field_names = {
        field.name for field in model._meta.get_fields() if hasattr(field, "column")
    }
    unprovided = all_field_names - provided_attrs

    keep_validating: set[str] = set()
    for group in _unique_constraint_groups(model):
        if group & provided_attrs:
            keep_validating |= group

    return sorted(unprovided - keep_validating)


def _unique_constraint_groups(model: type) -> list[set[str]]:
    """Return every uniqueness group's field-name set (spec-036 AR-H2 input).

    A group is the set of fields that participate in one uniqueness check: each
    ``UniqueConstraint`` in ``Meta.constraints``, each ``Meta.unique_together``
    tuple, and each single-field ``field.unique`` column (a 1-element group). The
    AR-H2 carve-out keeps any unprovided member of a group whose other members
    were provided.
    """
    groups: list[set[str]] = []
    for constraint in model._meta.constraints:
        fields = getattr(constraint, "fields", None)
        if fields:
            groups.append(set(fields))
    groups.extend(set(together) for together in model._meta.unique_together)
    groups.extend(
        {field.name}
        for field in model._meta.get_fields()
        if hasattr(field, "column") and getattr(field, "unique", False) and not field.primary_key
    )
    return groups


def _validation_error_to_field_errors(exc: ValidationError) -> list[FieldError]:
    """Map a Django ``ValidationError`` to the ``FieldError`` envelope (spec-036 Decision 7 / AR-M3).

    Uses ``exc.error_dict`` when present (per-field), keying the model's
    ``NON_FIELD_ERRORS`` bucket to the ``NON_FIELD_ERROR_KEY`` sentinel (pinned to
    ``"__all__"`` in ``mutations/inputs.py`` - AR-M3, single source) so a
    multi-field-constraint error surfaces under ``"__all__"``. Falls back to
    ``exc.messages`` under the sentinel for a non-dict ``ValidationError``. The
    single source for both the ``full_clean()`` failure and the
    ``IntegrityError``-race fallback mapping.
    """
    if hasattr(exc, "error_dict"):
        errors: list[FieldError] = []
        for field_name, field_errors in exc.error_dict.items():
            key = NON_FIELD_ERROR_KEY if field_name == NON_FIELD_ERRORS else field_name
            messages = [message for error in field_errors for message in error.messages]
            errors.append(FieldError(field=key, messages=messages))
        return errors
    return [FieldError(field=NON_FIELD_ERROR_KEY, messages=list(exc.messages))]


def _integrity_error_field_errors(model: type, provided_attrs: set[str]) -> list[FieldError]:
    """Map a save-time ``IntegrityError`` race to the constraint fields (spec-036 Major-2).

    A ``UniqueConstraint`` race that beat ``full_clean()``'s
    ``validate_constraints()`` surfaces at ``save()`` as a backend-specific
    ``IntegrityError`` with no clean field mapping. As a documented best-effort
    fallback (not the normal unique path - covered by a mocked-``save()`` test),
    the pipeline keys it to the ``"__all__"`` sentinel: the race is a constraint
    violation, and the sentinel is the same model-level bucket
    ``validate_constraints()`` would have used for a multi-field constraint.
    """
    del model, provided_attrs  # reserved for a future per-constraint refinement.
    return [
        FieldError(
            field=NON_FIELD_ERROR_KEY,
            messages=["A uniqueness constraint was violated."],
        ),
    ]


def _assign_m2m(instance: Any, m2m_assignments: list[Any]) -> None:
    """Assign provided M2M relations on a saved instance (spec-036 AR-M1).

    For each provided ``(m2m_field_name, [pk, ...])``: ``instance.<m2m>.set([
    ...])`` replaces the entire relation set (a provided empty list clears it);
    an omitted M2M field is never in ``m2m_assignments`` so it is left unchanged.
    Related objects resolve through the target model's default manager (the pks
    decoded in step 1). Runs inside the transaction, after ``save()``.
    """
    for m2m_name, pks in m2m_assignments:
        getattr(instance, m2m_name).set(pks)


def _refetch_optimized(
    target_type: type,
    pk: Any,
    info: Any,
    *,
    force_load: bool,
) -> Any | None:
    """Re-fetch the written row by pk + optimizer plan (spec-036 Decision 9 / Medium-1).

    ``qs = initial_queryset(target_type).filter(pk=pk)`` - **by pk, WITHOUT the
    visibility ``get_queryset`` filter** (Medium-1, the deliberate GOAL crit-4
    exception: the actor just wrote the row, so round-tripping their own write is
    not an existence leak). Routes through ``apply_connection_optimization`` so
    the active optimizer plans the response selection; because the operation is a
    ``MUTATION``, the spec-035 G2 gate keeps ``select_related`` /
    ``prefetch_related`` and applies NO ``.only(...)`` - Decision 9 comes for free.

    ``force_load=True`` (the delete path, AR-M5 / Medium-2) materializes the
    snapshot fully BEFORE the row is deleted: evaluating the queryset loads
    ``select_related`` joins and populates ``_prefetched_objects_cache`` for
    ``prefetch_related`` children, so the detached instance's relations survive
    the row's deletion. ``force_load=False`` (create / update) returns
    ``qs.first()`` directly.

    The response selection nests the node type under the payload's ``node`` /
    ``result`` slot, so the optimizer's selection extractor is the slot-aware
    ``mutation_payload_child_selections(slot)`` rather than the connection
    ``edges { node }`` navigator - so the walker plans ``select_related`` /
    ``prefetch_related`` for the actual response shape.
    """
    slot = payload_object_slot(target_type)
    queryset = initial_queryset(target_type).filter(pk=pk)
    queryset = apply_connection_optimization(
        target_type,
        queryset,
        info,
        selection_extractor=mutation_payload_child_selections(slot),
    )
    if force_load:
        rows = list(queryset)
        return rows[0] if rows else None
    return queryset.first()


def _build_payload(
    payload_cls: type,
    slot: str,
    obj: Any,
    errors: list[FieldError],
) -> Any:
    """Instantiate a ``<Name>Payload`` with ``obj`` in the uniform slot + ``errors`` (spec-036 Decision 7).

    The single source for the success (``obj`` set, ``errors`` empty) and error
    (``obj`` ``None``, ``errors`` populated) envelope returns. ``slot`` is
    ``payload_object_slot(primary_type)`` - ``"node"`` for a Relay-Node target,
    ``"result"`` otherwise (recomputed, never re-derived - the discretion-item
    choice).
    """
    return payload_cls(**{slot: obj, "errors": errors})


def _run_pipeline_sync(
    mutation_cls: type,
    info: Any,
    data: Any,
    id: Any,  # noqa: A002
) -> Any:
    """Run the synchronous decode -> ... -> payload pipeline inside one ``transaction.atomic()``.

    The single sync body the async path wraps in ``sync_to_async(...,
    thread_sensitive=True)`` (spec-036 AR-M4). Dispatches on ``meta.operation`` to
    the create / update / delete branch; authorize -> snapshot run inside one
    ``transaction.atomic()`` so a failure after ``save()`` (relation assignment or
    the snapshot) rolls the write back.
    """
    meta = mutation_cls._mutation_meta
    primary_type = mutation_cls._primary_type
    model = primary_type.__django_strawberry_definition__.model
    slot = payload_object_slot(primary_type)
    payload_cls = _payload_cls_for(mutation_cls)

    with transaction.atomic():
        if meta.operation == "create":
            return _run_create(mutation_cls, info, data, model, primary_type, slot, payload_cls)
        if meta.operation == "update":
            return _run_update(
                mutation_cls,
                info,
                data,
                id,
                model,
                primary_type,
                slot,
                payload_cls,
            )
        return _run_delete(mutation_cls, info, id, primary_type, slot, payload_cls)


def _run_create(
    mutation_cls: type,
    info: Any,
    data: Any,
    model: type,
    primary_type: type,
    slot: str,
    payload_cls: type,
) -> Any:
    """The ``create`` branch: authorize -> build -> full_clean -> save -> M2M -> re-fetch -> payload."""
    _authorize_or_raise(mutation_cls, info, "create", data, instance=None)

    scalar_and_fk_attrs, m2m_assignments, decode_error = _decode_relations(model, data)
    if decode_error is not None:
        return _build_payload(payload_cls, slot, None, [decode_error])

    instance = model(**scalar_and_fk_attrs)
    error_payload = _full_clean_or_payload(
        instance,
        exclude=None,
        slot=slot,
        payload_cls=payload_cls,
    )
    if error_payload is not None:
        return error_payload

    write_error = _save_or_field_errors(instance, model, set(scalar_and_fk_attrs))
    if write_error is not None:
        return _build_payload(payload_cls, slot, None, write_error)
    _assign_m2m(instance, m2m_assignments)

    obj = _refetch_optimized(primary_type, instance.pk, info, force_load=False)
    return _build_payload(payload_cls, slot, obj, [])


def _run_update(
    mutation_cls: type,
    info: Any,
    data: Any,
    id: Any,  # noqa: A002
    model: type,
    primary_type: type,
    slot: str,
    payload_cls: type,
) -> Any:
    """The ``update`` branch: locate -> authorize -> set provided -> full_clean -> save -> re-fetch."""
    node_id, id_error = _coerce_lookup_id(id, primary_type)
    if id_error is not None:
        return _build_payload(payload_cls, slot, None, [id_error])
    instance = _locate_instance(primary_type, node_id, info)
    if instance is None:
        return _build_payload(payload_cls, slot, None, [_not_found_error()])

    _authorize_or_raise(mutation_cls, info, "update", data, instance=instance)

    scalar_and_fk_attrs, m2m_assignments, decode_error = _decode_relations(model, data)
    if decode_error is not None:
        return _build_payload(payload_cls, slot, None, [decode_error])

    for attr, value in scalar_and_fk_attrs.items():
        setattr(instance, attr, value)

    provided = _provided_attr_names(model, scalar_and_fk_attrs, m2m_assignments)
    exclude = _unprovided_exclude(model, provided)
    error_payload = _full_clean_or_payload(
        instance,
        exclude=exclude,
        slot=slot,
        payload_cls=payload_cls,
    )
    if error_payload is not None:
        return error_payload

    write_error = _save_or_field_errors(instance, model, provided)
    if write_error is not None:
        return _build_payload(payload_cls, slot, None, write_error)
    _assign_m2m(instance, m2m_assignments)

    obj = _refetch_optimized(primary_type, instance.pk, info, force_load=False)
    return _build_payload(payload_cls, slot, obj, [])


def _run_delete(
    mutation_cls: type,
    info: Any,
    id: Any,  # noqa: A002
    primary_type: type,
    slot: str,
    payload_cls: type,
) -> Any:
    """The ``delete`` branch: locate -> authorize -> snapshot-before-delete -> delete -> payload.

    The snapshot is the optimizer-planned re-fetch fully materialized (relations
    loaded into the instance) BEFORE ``delete()`` (spec-036 AR-M5 / Medium-2), so
    the detached in-memory instance's relations survive the row's deletion. The
    re-fetch is by pk without the visibility filter (Medium-1), consistent with
    create / update.
    """
    node_id, id_error = _coerce_lookup_id(id, primary_type)
    if id_error is not None:
        return _build_payload(payload_cls, slot, None, [id_error])
    instance = _locate_instance(primary_type, node_id, info)
    if instance is None:
        return _build_payload(payload_cls, slot, None, [_not_found_error()])

    _authorize_or_raise(mutation_cls, info, "delete", data=None, instance=instance)

    snapshot = _refetch_optimized(primary_type, instance.pk, info, force_load=True)
    if snapshot is not None:
        snapshot.delete()
    else:
        instance.delete()
    return _build_payload(payload_cls, slot, snapshot, [])


def _authorize_or_raise(
    mutation_cls: type,
    info: Any,
    operation: str,
    data: Any,
    *,
    instance: Any,
) -> None:
    """Run ``check_permission``; a ``False`` return raises a top-level ``GraphQLError`` (Decision 15).

    Delegates to the Slice-2 ``check_permission`` method (which iterates
    ``Meta.permission_classes``); the resolver only maps a denial to a raised
    ``GraphQLError`` (the authorization-failure surface, distinct from the
    field-keyed validation envelope - AR-H3 / Decision 15). The mutation instance
    is constructed once so an object-level ``check_permission`` override can hold
    per-request state.
    """
    if not mutation_cls().check_permission(info, operation, data, instance):
        raise GraphQLError(
            f"Not authorized to {operation} {mutation_cls._primary_type.__name__}.",
        )


def _full_clean_or_payload(
    instance: Any,
    *,
    exclude: list[str] | None,
    slot: str,
    payload_cls: type,
) -> Any | None:
    """Run ``full_clean(exclude=...)``; return a null-object payload on ``ValidationError`` else ``None``.

    ``full_clean()`` runs ``validate_constraints()``, so a ``UniqueConstraint``
    duplicate is caught here as a ``ValidationError`` BEFORE ``save()`` (Major-2);
    its field-keyed messages populate the envelope (multi-field constraint ->
    ``"__all__"`` sentinel, AR-M3). ``exclude=None`` for create (validate all
    fields); the AR-H2-aware exclude list for update.
    """
    try:
        instance.full_clean(exclude=exclude)
    except ValidationError as exc:
        return _build_payload(payload_cls, slot, None, _validation_error_to_field_errors(exc))
    return None


def _save_or_field_errors(
    instance: Any,
    model: type,
    provided_attrs: set[str],
) -> list[FieldError] | None:
    """``save()`` the instance; map a race ``IntegrityError`` to the envelope else ``None`` (Major-2)."""
    try:
        instance.save()
    except IntegrityError:
        return _integrity_error_field_errors(model, provided_attrs)
    return None


def _coerce_lookup_id(id: Any, target_type: type) -> tuple[Any, FieldError | None]:  # noqa: A002
    """Coerce the ``id:`` to a pk, type-checking a ``GlobalID`` against the target (spec-036 Decision 10).

    ``DjangoMutationField`` declares ``id`` as the raw ``strawberry.ID`` string
    (the ``DjangoNodeField`` server-side-decode precedent), so the value arrives as
    a wire-form base64 GlobalID string (or, defensively, a decoded
    ``relay.GlobalID`` / a raw pk). A decoded ``GlobalID`` is **type-checked against
    the mutation's target model** - the same identity guard the typed
    ``DjangoNodeField`` applies (``relay.py::_check_typed_match``) and the AR-H4
    relation decode applies to ``<field>_id``: a well-formed id for the *wrong*
    model (or an unresolvable type) returns a ``FieldError`` on ``id`` BEFORE any
    pk lookup, never silently coerced to a bare pk that would target the same-pk
    row of the right model. A raw pk string carries no type slot and passes through
    unchecked (Django coerces it on the ``.get(pk=...)`` lookup).

    Returns ``(node_id, None)`` on success or ``(None, FieldError)`` for a
    wrong-type / unresolvable ``GlobalID``.
    """
    gid = id
    if isinstance(id, str):
        try:
            gid = relay.GlobalID.from_id(id)
        except ValueError:
            return id, None  # a raw pk string - no GlobalID type slot to check
    if not isinstance(gid, relay.GlobalID):
        return gid, None
    target_model = target_type.__django_strawberry_definition__.model
    try:
        resolved_type, node_id = decode_global_id(gid)
    except Exception:
        return None, _invalid_lookup_id_error()
    if resolved_type.__django_strawberry_definition__.model is not target_model:
        return None, _invalid_lookup_id_error()
    return node_id, None


def _not_found_error() -> FieldError:
    """Build the not-found ``FieldError`` on ``id`` (hidden or missing - no existence leak)."""
    return FieldError(field="id", messages=["No matching row found."])


def _invalid_lookup_id_error() -> FieldError:
    """Build the wrong-type / unresolvable ``id`` ``FieldError`` (decided pre-lookup - no existence leak).

    A ``GlobalID`` whose decoded type is not the mutation's target model (or whose
    type cannot be resolved) is rejected here rather than coerced to a bare pk; the
    failure is determined from the id's type slot alone, without a DB read, so it
    reveals nothing about row existence (spec-036 Decision 10 / finding-#1).
    """
    return FieldError(field="id", messages=["Invalid id."])


def _payload_cls_for(mutation_cls: type) -> type:
    """Return the materialized ``<Name>Payload`` class for a bound mutation.

    The Slice-2 bind stashes the payload class name on the mutation
    (``_payload_type_name``) and materializes the class as a module global of
    ``mutations.inputs``; the resolver reads it from there so the payload type the
    field's lazy ref resolves to and the type the resolver instantiates are the
    same object.
    """
    from . import inputs

    return getattr(inputs, mutation_cls._payload_type_name)


def resolve_mutation_sync(
    mutation_cls: type,
    info: Any,
    *,
    data: Any = strawberry.UNSET,
    id: Any = strawberry.UNSET,  # noqa: A002
) -> Any:
    """Sync pipeline entry the field's sync branch calls (spec-036 Decision 8).

    A thin public alias for ``_run_pipeline_sync`` (normalizing the
    ``UNSET``-default kwargs to the body's positional args) so the field factory
    has a stable sync entry point distinct from the async one.
    """
    return _run_pipeline_sync(mutation_cls, info, data, id)


async def resolve_mutation_async(
    mutation_cls: type,
    info: Any,
    *,
    data: Any = strawberry.UNSET,
    id: Any = strawberry.UNSET,  # noqa: A002
) -> Any:
    """Async pipeline entry: the sync body in one ``sync_to_async(thread_sensitive=True)`` (spec-036 AR-M4).

    Does NOT re-implement the pipeline - it wraps the SAME ``_run_pipeline_sync``
    body so the ``transaction.atomic()`` + every ORM call run on one worker thread
    under Django's async-safety contract, never interleaving ORM work with
    ``await``s. A sync ``get_queryset`` runs synchronously inside the thread; an
    ``async def get_queryset`` raises ``SyncMisuseError`` there (no awaiting
    context - the standing discipline).
    """
    return await sync_to_async(_run_pipeline_sync, thread_sensitive=True)(
        mutation_cls,
        info,
        data,
        id,
    )
