"""The sync + async create / update / delete write pipeline (spec-036 Slice 3).

The write-side runtime: one pipeline per operation, in a sync and an async form
(spec-036 Decision 8). The pipeline is

    (update) locate -> authorize -> decode -> validate -> write -> re-fetch/snapshot -> payload

and the load-bearing invariants this module owns:

- **One ``transaction.atomic()`` boundary** wraps authorize -> snapshot, and the
  **async path runs the whole sync ORM pipeline in a single**
  ``sync_to_async(thread_sensitive=True)`` **call** (spec-036 AR-M4): the write,
  its M2M ``.set(...)`` calls, and the payload snapshot are atomic and never
  interleave ORM work with ``await``s.
- **Relation ``GlobalID`` decode is type-checked against the relation's Django
  target model** (spec-036 AR-H4): a well-formed id for the wrong model is a
  ``FieldError`` on that relation field, never coerced cross-model and never a
  raw ``DoesNotExist``. The type-checked id is then **resolved through the
  related model's primary ``DjangoType`` visibility ``get_queryset``** (spec-036
  Decision 10 / feedback P1): a row the caller cannot see is the SAME field-keyed
  ``FieldError`` (hidden and missing indistinguishable, no existence leak), never
  silently attached. Applies to FK, OneToOne, and each M2M id (the M2M set is
  checked in one query). A well-formed id whose ``node_id`` is not a valid pk
  literal for the related column is coerced to "not found" (the same
  ``FieldError``) by the shared ``decode_model_global_id`` primitive before the
  query, never a raw Django ``ValueError`` (feedback CR-1 / DRY-2).
- **``update`` / ``delete`` locate runs through the target type's
  ``get_queryset`` for visibility only** (spec-036 Decision 10): a hidden row is
  not-found, indistinguishable from a genuinely missing row (no existence leak).
  The top-level ``id:`` is itself decoded + type-checked against the mutation's
  target model BEFORE the lookup (a malformed / unresolvable / wrong-model id is
  a ``FieldError`` on ``id``, never coerced to a bare pk - feedback finding-#1),
  and its ``node_id`` is coerced through the target pk field so an uncoercible
  literal is not-found, never a raw Django ``ValueError`` (feedback CR-1).
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
  the row is deleted (spec-036 AR-M5 / Medium-2); the deletion runs against the
  located instance, NOT the returned snapshot, so the snapshot keeps its ``pk`` /
  ``id`` for the delete payload's cache-eviction contract (feedback P1).
- **``SyncMisuseError`` discipline** is inherited from
  ``apply_type_visibility_sync``: a sync mutation meeting an ``async def
  get_queryset`` closes the coroutine and raises (spec-036 Decision 8).

The ``DjangoMutationField`` factory + signature synthesis are the sibling module
``fields.py``. The live products write surface (a products ``Mutation`` +
``config/schema.py`` wiring + the live ``CaptureQueriesContext`` assertion) is
Slice 4, NOT this slice.
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any

import strawberry
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from graphql import GraphQLError
from strawberry import relay

from ..optimizer.extension import (
    apply_connection_optimization,
    mutation_payload_child_selections,
)
from ..registry import registry
from ..relay import GlobalIDDecode, decode_model_global_id
from ..utils.inputs import graphql_camel_name, iter_provided_input_fields
from ..utils.querysets import (
    apply_type_visibility_sync,
    initial_queryset,
    model_for,
    pks_all_present,
    reject_async_in_sync_context,
    related_visibility_queryset,
    stringified_pks_present,
    sync_pipeline_recourse,
    visibility_scoped_related_queryset,
)
from ..utils.relations import is_forward_many_to_many
from .inputs import NON_FIELD_ERROR_KEY, FieldError, payload_object_slot
from .permissions import _PERMISSION_ASYNC_RECOURSE

# The async-pipeline recourse appended to a ``SyncMisuseError`` raised when an
# async ``get_queryset`` is met inside the (sync) ORM pipeline. The whole
# pipeline runs synchronously even on the async surface (it executes inside one
# ``sync_to_async`` worker thread - spec-036 AR-M4), so an ``async def
# get_queryset`` can never be awaited here regardless of operation context; the
# recourse is to make the target hook sync. The sentence is single-sourced across
# the three write flavors via ``sync_pipeline_recourse`` (spec-039 Md2).
_MUTATION_ASYNC_RECOURSE = sync_pipeline_recourse("DjangoMutation")


def run_write_pipeline_sync(
    mutation_cls: type,
    info: Any,
    data: Any,
    id: Any,  # noqa: A002
    *,
    decode_step: Any,
    write_step: Any,
) -> Any:
    """The shared model-backed create / update write orchestration (spec-039 P1.5).

    The single-sited skeleton the model (``_run_create`` / ``_run_update``), the
    ``ModelForm`` (``forms/resolvers.py::_run_modelform_pipeline_sync``), and the
    serializer (``rest_framework/resolvers.py``) write flavors all ride, so the
    ``transaction.atomic()`` boundary + the **authorize-before-decode security
    ordering** is owned in ONE place rather than hand-copied a third time. Scoped to
    **model-backed create / update only** (F6): the ``delete`` snapshot-before-delete
    body (``_run_delete``) and the model-less plain-form body
    (``_run_plain_form_pipeline_sync``) keep their own orchestration (no instance /
    no re-fetch / no object slot).

    The order is the ``036`` / ``038`` security invariant, in ONE place:

    1. open one ``transaction.atomic()``;
    2. (update) ``coerce_lookup_id`` -> ``locate_instance`` -> ``not_found_error``
       through the target type's visibility ``get_queryset`` (a malformed id is a
       ``FieldError`` on ``id``; a hidden / missing row is not-found - no existence
       leak; ``create`` has no locate, ``instance is None``);
    3. **authorize BEFORE decode** (``authorize_or_raise(... instance=instance)``):
       the decode issues visibility-scoped relation queries, so running it pre-auth
       would let an unauthorized caller probe relation visibility by id;
    4. ``decode_step(instance) -> decoded | list[FieldError]`` - the flavor's
       relation-decode + payload build (returns a ``list[FieldError]`` on a decode
       failure, mapped to a null-object payload here);
    5. ``write_step(instance, decoded) -> saved | list[FieldError]`` - the flavor's
       construct / validate / ``save()`` (M2M assignment etc.), returning the saved
       object or a ``list[FieldError]`` on a validation / write failure;
    6. ``refetch_optimized(primary_type, saved.pk, info, force_load=False)`` ->
       ``build_payload`` - the optimizer-planned re-fetch by pk (G2) + the success
       payload.

    ``decode_step`` / ``write_step`` are the ONLY per-flavor seams: the model passes
    a relation-decode + ``setattr`` / construct step and a ``full_clean`` -> ``save``
    -> M2M step; the form passes a form-decode + partial-reconstruction step and a
    ``get_form`` -> ``is_valid`` -> ``form.save`` step; the serializer passes a
    serializer-field-keyed decode step and a ``serializer.is_valid`` -> ``save`` step.
    A step returning a ``list[FieldError]`` short-circuits to a null-object payload AND
    marks the ``transaction.atomic()`` block for rollback (spec-039 H6) - so a
    ``write_step`` that made a partial write and THEN raised a validation error (a
    custom ``serializer.save()`` that inserts a row, then raises) never commits the
    partial write; the error envelope is the no-effect outcome.
    """
    meta = mutation_cls._mutation_meta
    primary_type = mutation_cls._primary_type
    slot = payload_object_slot(primary_type)
    payload_cls = payload_cls_for(mutation_cls)
    is_update = meta.operation == "update"

    with transaction.atomic():

        def _error_payload(errors: list[FieldError]) -> Any:
            """Roll back, then return the null-object error envelope (spec-039 H6).

            A ``FieldError`` envelope means the mutation did NOT succeed, so nothing it
            wrote may persist. A flavor ``write_step`` whose write made a partial change
            and THEN raised a validation error - the custom ``serializer.save()`` that
            inserts a row then raises ``serializers.ValidationError``, mapped to the
            envelope inside this atomic block - would otherwise COMMIT on the normal
            return. Mark the transaction for rollback BEFORE building the payload so the
            partial write is discarded (``build_payload`` runs no ORM query, so it is
            safe after ``set_rollback``). Harmless on the read-only locate / decode
            failure paths (nothing was written), keeping the invariant uniform: an error
            envelope never commits.
            """
            transaction.set_rollback(True)
            return build_payload(payload_cls, slot, None, errors)

        instance = None
        if is_update:
            node_id, id_error = coerce_lookup_id(id, primary_type)
            if id_error is not None:
                return _error_payload([id_error])
            # rev6 #14: an opt-in ``SELECT ... FOR UPDATE`` row lock on the update locate,
            # acquired after visibility filtering and inside this ``transaction.atomic()``
            # boundary. ``meta.select_for_update`` is ``False`` for the model / form flavors.
            instance = locate_instance(
                primary_type,
                node_id,
                info,
                select_for_update=meta.select_for_update,
            )
            if instance is None:
                return _error_payload([not_found_error()])

        # Authorize BEFORE the flavor decode (the security invariant): the decode
        # issues visibility-scoped ``get_queryset`` queries, so running it pre-auth
        # would let an unauthorized caller probe related-object visibility by id.
        authorize_or_raise(mutation_cls, info, meta.operation, data, instance=instance)

        decoded = decode_step(instance)
        if isinstance(decoded, list):
            return _error_payload(decoded)

        saved = write_step(instance, decoded)
        if isinstance(saved, list):
            return _error_payload(saved)

        obj = refetch_optimized(primary_type, saved.pk, info, force_load=False)
        return build_payload(payload_cls, slot, obj, [])


def _decode_relations(
    model: type,
    data: Any,
    info: Any,
    *,
    excluded_input_fields: frozenset[str] = frozenset(),
) -> tuple[dict[str, Any], list[Any], dict[str, Any], FieldError | None]:
    """Decode the provided input fields into model attrs + M2M pk lists (spec-036 Decision 8 step 1).

    Walks the input dataclass's provided fields (``UNSET`` stripped - the
    ``UNSET`` / ``null`` / value tri-state is preserved: ``UNSET`` means
    "omitted", an explicit ``None`` is kept as a provided ``None``). For each
    forward FK / OneToOne ``<field>_id`` whose value is a ``relay.GlobalID``,
    ``_decode_relation_id_set`` (via the shared ``decode_model_global_id``
    primitive) resolves + **type-checks the decoded model against the relation's
    Django target model** (spec-036 AR-H4): a wrong-type id returns a ``FieldError``
    on that relation field, never a cross-model pk lookup and never a raw
    ``DoesNotExist``. The type-checked id is then **resolved through the related
    model's primary type visibility ``get_queryset``** (spec-036 Decision 10 /
    feedback P1): a row the caller cannot see is the same field-keyed
    ``FieldError``, never attached. A raw pk scalar (a non-Relay target) is not
    decoded, but is STILL visibility-checked when the related model has a registered
    (even non-Relay) primary type with a ``get_queryset`` - the model-path
    equivalent of the form decoder's visibility-on-every-branch contract, closing
    the raw-pk visibility gap. With no primary registered there is no contract to
    apply.

    ``excluded_input_fields`` is the spec-040 D6 **exclusion seam**: a provided
    input attr named there (the register flavor's ``password``) is captured into
    the ``excluded_values`` map and skipped BEFORE the relation / scalar / null
    routing, so its raw value never reaches ``model(**scalar_and_fk_attrs)`` -
    while the walk itself (the UNSET-vs-null-vs-value tri-state) stays the ONE
    shared ``iter_provided_input_fields`` pass, never a forked copy. The caller
    (``_model_decode_step``) folds the captured names back into the AR-H2
    provided-marker calculation, so exclusion never silently drops the column
    from ``full_clean`` validation.

    Returns ``(scalar_and_fk_attrs, m2m_assignments, excluded_values, error)``
    where ``scalar_and_fk_attrs`` is the ``{model_attr: value}`` map for
    ``setattr`` / ``Model(**...)`` (FK as ``<field>_id`` -> pk),
    ``m2m_assignments`` is a list of ``(m2m_field_name, [pk, ...])`` deferred to
    the post-save write step (AR-M1), ``excluded_values`` is the captured
    ``{excluded_attr: raw value}`` map (empty for the default no-exclusion walk),
    and ``error`` is the first decode ``FieldError`` or ``None``.
    """
    fk_by_attr, m2m_by_name = _relation_field_index(model)
    scalar_and_fk_attrs: dict[str, Any] = {}
    m2m_assignments: list[Any] = []
    excluded_values: dict[str, Any] = {}

    # The ``UNSET``-strip walk is single-sited in ``iter_provided_input_fields``
    # (spec-039 M2); the per-field kind routing below stays flavor-specific.
    for python_name, value, field in iter_provided_input_fields(data):
        if python_name in excluded_input_fields:
            # The exclusion seam (spec-040 D6): capture the raw provided value and
            # skip every decode branch - the value must never become a model attr.
            excluded_values[python_name] = value
            continue
        # A decode failure keys to the input field's GraphQL name (what the
        # client sent), e.g. ``categoryId`` - distinct from a ``full_clean``
        # error, which keys to the MODEL field name. ``graphql_name`` is the
        # field's wire alias (or ``python_name`` when no alias differs).
        graphql_name = field.graphql_name or graphql_camel_name(python_name)

        m2m_field = m2m_by_name.get(python_name)
        if m2m_field is not None:
            pks, error = _decode_relation_id_list(graphql_name, value, m2m_field, info)
            if error is not None:
                return {}, [], {}, error
            m2m_assignments.append((python_name, pks))
            continue

        fk_field = fk_by_attr.get(python_name)
        if fk_field is not None:
            pk, error = _decode_single_relation_id(graphql_name, value, fk_field, info)
            if error is not None:
                return {}, [], {}, error
            scalar_and_fk_attrs[python_name] = pk
            continue

        null_error = _explicit_null_error(model, python_name, graphql_name, value)
        if null_error is not None:
            return {}, [], {}, null_error
        text_error = _unencodable_text_error(graphql_name, value)
        if text_error is not None:
            return {}, [], {}, text_error
        scalar_and_fk_attrs[python_name] = _make_aware_if_naive(raw_choice_value(value))

    return scalar_and_fk_attrs, m2m_assignments, excluded_values, None


def _explicit_null_error(
    model: type,
    python_name: str,
    field_name: str,
    value: Any,
) -> FieldError | None:
    """Reject an explicit ``null`` on a non-nullable scalar column (feedback - explicit null).

    A provided ``None`` (``UNSET`` is already stripped) on a ``null=False`` column is
    a problem ``full_clean`` does NOT reliably catch: Django's ``clean_fields`` SKIPS a
    ``blank=True`` field whose value is an empty value, and ``None`` is an empty value,
    so a ``blank=True, null=False`` column (e.g. a ``TextField(blank=True)``) slips past
    validation and only fails at ``save()`` as a NOT NULL ``IntegrityError`` - surfacing
    as the generic ``"__all__"`` "A database constraint was violated." with no field
    attribution, after a write was attempted. Reject it at decode as a field-keyed
    ``FieldError`` so the client learns WHICH field, before any DB work. A ``null=True``
    column treats ``None`` as a valid clear and is left alone; a non-scalar attr (FK /
    M2M) is handled by its own branch before this point, so ``python_name`` here is
    always a concrete scalar column of ``model``.
    """
    if value is not None:
        return None
    if model._meta.get_field(python_name).null:
        return None
    return field_error(field_name, "This field cannot be null.", codes="null")


def _make_aware_if_naive(value: Any) -> Any:
    """Make a naive ``datetime`` input timezone-aware under ``USE_TZ`` (feedback - naive datetime).

    Strawberry's ``DateTime`` scalar parses a naive ISO string into a naive
    ``datetime``. Under ``USE_TZ=True`` Django emits a naive-datetime
    ``RuntimeWarning`` at ``save()`` - which a ``-W error`` test config escalates to a
    top-level GraphQL error, and which otherwise silently stores an ambiguous
    wall-clock value interpreted as the default timezone. Coerce a naive ``datetime``
    to the current timezone here (what DRF's ``DateTimeField`` does), so the write is
    unambiguous and warning-free. A ``date`` / ``time`` value is not a ``datetime``
    instance (``date`` is the parent, not the child), and an already-aware ``datetime``
    is left unchanged.
    """
    if settings.USE_TZ and isinstance(value, datetime.datetime) and timezone.is_naive(value):
        return timezone.make_aware(value)
    return value


def _unencodable_text_error(field_name: str, value: Any) -> FieldError | None:
    r"""Reject a string input that cannot be encoded for storage (unpaired surrogate).

    A GraphQL ``String`` can carry lone UTF-16 surrogate code points (e.g. U+D800
    via a JSON ``\ud800`` escape) that are not valid Unicode scalar values and
    cannot be encoded to UTF-8. Such a value would otherwise reach a
    DB-bound operation - ``validate_unique()``'s lookup query (a unique column) or
    ``save()``'s INSERT (any text column) - where the backend raises a raw
    ``UnicodeEncodeError``. That is a ``ValueError`` the resolver does NOT map (it is
    neither the ``ValidationError`` ``full_clean`` raises nor the ``IntegrityError``
    ``save`` raises), so it escapes as a top-level GraphQL error with ``data: null``
    instead of the field-keyed envelope (feedback - surrogate text leak). Reject it
    HERE, at decode, before any DB-bound work, as a ``FieldError`` naming the
    offending input field - the same in-band envelope every other input failure
    returns - so neither the unique-field ``validate_unique`` path nor the plain
    ``save`` path can leak the raw exception. ``str.encode("utf-8")`` is the
    universal storability test: a lone surrogate fails it, while every valid scalar
    value (including an embedded ``NUL``) passes, so this rejects ONLY genuinely
    unstorable text. A non-string value (an int, a JSON dict whose own encoder
    escapes nested surrogates, a choice enum) is passed through unchanged.
    """
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            return field_error(
                field_name,
                "Text contains invalid Unicode (unpaired surrogate code points).",
                codes="invalid",
            )
    return None


def raw_choice_value(value: Any) -> Any:
    """Unwrap a choice-enum member to its raw Django choice value (spec-036 Decision 6).

    A ``choices`` column resolves to the SAME generated Strawberry ``Enum`` on the
    read ``DjangoType`` and the write input (the symmetric wire contract), so the
    client's enum value arrives here as the ENUM MEMBER (e.g.
    ``BookCirculationStatusEnum.available``), not the raw string. The member's
    ``.value`` IS the Django choice value (``convert_choices_to_enum`` maps each
    member to its choice value), so setting the member directly onto the model
    would make ``full_clean()`` reject a perfectly valid choice (the member is not
    ``== "available"``). Unwrapping to ``.value`` feeds Django the raw choice value
    it stores and validates against. A non-enum scalar is passed through unchanged;
    an explicit ``None`` (a provided null) stays ``None``.
    """
    return value.value if isinstance(value, Enum) else value


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
            if is_forward_many_to_many(field):
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


def _decode_relation_id_set(
    field_name: str,
    values: list[Any],
    relation_field: Any,
    info: Any,
) -> tuple[list[Any], FieldError | None]:
    """Decode a list of relation ids to pks: type-check + coerce each, then visibility once (DRY-2).

    The single list-oriented relation decoder both the FK / OneToOne wrapper
    (``_decode_single_relation_id``, a one-element list) and the M2M wrapper
    (``_decode_relation_id_list``) delegate to, so the "type-check against the
    relation target, coerce the pk, then visibility-check the GlobalID set in ONE
    query" contract has a SINGLE implementation.

    Each element: a ``relay.GlobalID`` is run through ``decode_model_global_id``
    against the relation's Django target model - a decode failure, a wrong-model
    id, or an uncoercible ``node_id`` (any non-``OK`` status) is the uniform
    ``relation_field_error`` on ``field_name`` (AR-H4 + feedback CR-1: a wrong-type id
    is never a cross-model lookup, an uncoercible pk is never a raw ``ValueError``).
    A raw pk scalar (a non-Relay-Node target, which has no ``GlobalID`` shape)
    passes through the decode unchanged (there is no ``GlobalID`` to decode), then
    takes the raw-pk relation check below rather than the ``GlobalID`` visibility
    query. The decoded ``GlobalID`` set is visibility-checked in one query (Decision
    10 / feedback P1): a hidden / missing member is the same ``relation_field_error``,
    indistinguishable (no existence leak). A list is homogeneously typed (all
    ``GlobalID`` for a Relay target, all raw pk otherwise), so ``needs_visibility``
    is all-or-nothing and the whole set is checked together.

    A raw-pk set is NOT exempt from the related type's visibility contract: when
    the related model has a registered primary ``DjangoType`` - even a NON-Relay
    one, which has no ``GlobalID`` but can still define a ``get_queryset`` - the set
    is visibility-checked through ``_raw_pk_relation_error``, exactly as the form
    path does (``forms/resolvers.py::_visible_related_object``), closing the
    model-path raw-pk visibility gap. With NO primary type
    registered there is no visibility contract to apply: a raw-pk **M2M** set still
    gets the pre-``.set(...)`` existence check (it is assigned via
    ``instance.<m2m>.set(pks)``, which writes a dangling through-row for any
    nonexistent pk it is handed), while a raw-pk **FK** relies on ``full_clean()``'s
    own FK existence check against the column before ``save()``.
    """
    expected_model = relation_field.related_model
    pks: list[Any] = []
    needs_visibility = False
    for value in values:
        if not isinstance(value, relay.GlobalID):
            pks.append(value)
            continue
        result = decode_model_global_id(value, expected_model)
        if result.status is not GlobalIDDecode.OK:
            return [], relation_field_error(field_name)
        pks.append(result.pk)
        needs_visibility = True
    if needs_visibility:
        error = _relation_visibility_error(field_name, pks, expected_model, info)
        if error is not None:
            return [], error
    elif pks:
        error = _raw_pk_relation_error(field_name, pks, expected_model, relation_field, info)
        if error is not None:
            return [], error
    return pks, None


def _decode_single_relation_id(
    field_name: str,
    value: Any,
    relation_field: Any,
    info: Any,
) -> tuple[Any, FieldError | None]:
    """Decode one FK / OneToOne id via the shared set decoder (DRY-2).

    Wraps the single value in a one-element list, delegates to
    ``_decode_relation_id_set`` (type-check + coerce + visibility), and unwraps the
    single pk. A non-``GlobalID`` value (a raw pk, or an explicit ``None`` clearing
    a nullable FK) passes through the set decoder unchanged.
    """
    pks, error = _decode_relation_id_set(field_name, [value], relation_field, info)
    if error is not None:
        return None, error
    return pks[0], None


def _decode_relation_id_list(
    field_name: str,
    value: Any,
    relation_field: Any,
    info: Any,
) -> tuple[list[Any], FieldError | None]:
    """Decode an M2M ``list[<id>]`` to pks: null-reject, then the shared set decoder (DRY-2).

    The list is the replace-set the post-save step assigns (AR-M1). An explicit
    ``null`` (reachable because the generated optional M2M field is
    ``list[<id>] | None``) is NOT a valid replace-set - it returns a ``FieldError``
    on ``field_name`` (the valid "clear" signal is an empty list ``[]``), rather
    than iterating ``None`` into a resolver exception (feedback P2). A non-null list
    delegates to ``_decode_relation_id_set`` (the same type-check + coerce +
    one-query visibility contract the FK path uses).
    """
    if value is None:
        return [], _relation_null_error(field_name)
    return _decode_relation_id_set(field_name, value, relation_field, info)


def type_check_relation_id(
    value: Any,
    *,
    graphql_name: str,
    related_model: type,
) -> tuple[Any, FieldError | None]:
    """Type-check + coerce ONE relation id to a pk WITHOUT a DB fetch (spec-039 M3).

    The "GlobalID -> ``decode_model_global_id`` (non-``OK`` -> uniform relation
    error) | raw pk -> ``_coerce_relation_pk_or_none`` (``None`` -> uniform relation
    error)" two-branch structural check the three write flavors share. Promoted here
    (from the serializer's cleanly-factored ``_type_check_relation_id``) so the
    single definition of "what counts as a well-formed relation id" is shared: the
    serializer single/multi decoders call it, and the form single decoder calls it
    (keeping only its ``empty_values`` pass-through + ``to_field_name`` reduction on
    top). Neither branch touches the DB - visibility is confirmed separately by the
    caller.

    The model batched decoder (``_decode_relation_id_set``) deliberately does NOT use
    this: its raw-pk half is a set-level all-or-nothing visibility / existence check
    (``_raw_pk_relation_error``), a genuinely different contract; only its GlobalID
    half mirrors the check here. A ``relay.GlobalID`` is decoded against the target
    model (a non-``OK`` status is the uniform ``relation_field_error``); a raw pk is
    coerced through the target pk field (``None`` -> the uniform error).
    """
    if isinstance(value, relay.GlobalID):
        result = decode_model_global_id(value, related_model)
        if result.status is not GlobalIDDecode.OK:
            return None, relation_field_error(graphql_name)
        return result.pk, None
    pk = _coerce_relation_pk_or_none(related_model, value)
    if pk is None:
        return None, relation_field_error(graphql_name)
    return pk, None


def _relation_null_error(field_name: str) -> FieldError:
    """Build the explicit-``null`` M2M ``FieldError`` for ``field_name`` (feedback P2).

    A generated optional M2M field is ``list[<id>] | None``, so a client can send
    an explicit ``null``. ``null`` is not a valid replace-set (the M2M contract is
    replace-on-provide / clear-on-empty / unchanged-on-omit - AR-M1), so it is
    rejected as a field-keyed error naming the clear signal, rather than iterating
    ``None`` into a resolver exception.
    """
    return field_error(
        field_name,
        f"Relation {field_name!r} cannot be null; send an empty list to clear it.",
        codes="null",
    )


def _relation_membership_error(
    field_name: str,
    queryset: Any,
    declared_pks: list[Any],
    query_pks: list[Any],
) -> FieldError | None:
    """Return a relation ``FieldError`` unless every ``declared_pks`` member is present in ``queryset``.

    The single no-existence-leak membership check the three relation guards share -
    visibility on the model path (``_relation_visibility_error``), visibility on the
    raw-pk path (``_raw_pk_relation_error``), and existence on the no-primary raw-pk
    M2M path (``_relation_existence_error``). The ONLY axes that vary are folded into
    the two arguments:

    - ``queryset`` - the visibility-scoped ``get_queryset`` queryset for the two
      visibility checks, the target's ``_default_manager`` for the existence-only
      check.
    - ``declared_pks`` vs ``query_pks`` - the set whose presence is ASSERTED vs. the
      set actually sent to ``pk__in``. They coincide for the already-coerced
      ``GlobalID`` path; for a raw-pk set ``query_pks`` is the coerced subset (an
      uncoercible / out-of-range pk dropped so it never hits the backend), while
      ``declared_pks`` stays the full input - so a dropped pk is absent from the
      present set and fails the subset check, the same not-found relation error a
      hidden / missing pk yields (no existence leak).

    The query + str-coercion (``stringified_pks_present``) and the subset test
    (``pks_all_present``) are single-sited in ``utils/querysets.py`` (spec-039 Md4),
    shared with the serializer M2M decoder.
    """
    present = stringified_pks_present(queryset, query_pks)
    if not pks_all_present(declared_pks, present):
        return relation_field_error(field_name)
    return None


def _relation_visibility_error(
    field_name: str,
    pks: list[Any],
    related_model: type,
    info: Any,
) -> FieldError | None:
    """Confirm every relation pk is visible through the related type's ``get_queryset`` (feedback P1).

    After the AR-H4 type-check, a relation id must also pass the related model's
    **primary** ``DjangoType`` visibility hook - the SAME ``get_queryset`` every
    read surface applies (``apply_type_visibility_sync(initial_queryset(...))``) -
    so a permitted writer cannot attach a row they could not *see* (a private
    ``Category``, a hidden ``Genre``). The ``full_clean`` FK check that runs later
    uses Django's default manager, NOT this visibility queryset, so the check
    belongs here (spec-036 Decision 10).

    The target is resolved via ``registry.get(related_model)`` - the relation's
    canonical **primary** type, NOT the client-named decoded type - so naming a
    more-permissive sibling type in the ``GlobalID`` cannot dodge the primary's
    hook. A ``GlobalID``-typed relation input is only generated when the related
    model HAS a primary Relay-Node type (``mutations/inputs.py``), so this path is
    reached only with a resolvable primary. Hidden and missing are
    indistinguishable (the uniform ``relation_field_error``, no existence leak),
    matching the update/delete locate (``locate_instance``); FK / OneToOne pass a
    one-element list, M2M the whole set (verified in one ``pk__in`` query). An
    ``async def get_queryset`` met here raises ``SyncMisuseError`` (the same sync
    discipline as the locate path).

    The ``pks`` arrive **already coerced** through the resolved type's pk field by
    ``decode_model_global_id`` (the shared DRY-2 primitive), so an uncoercible
    ``node_id`` was already mapped to ``relation_field_error`` upstream and never reaches
    the ``pk__in`` query as a raw Django ``ValueError`` (feedback CR-1). This step
    only confirms visibility.
    """
    related_type = registry.get(related_model)
    queryset = visibility_scoped_related_queryset(related_type, info, _MUTATION_ASYNC_RECOURSE)
    # ``pks`` are already coerced (the GlobalID path), so the asserted + queried sets
    # coincide.
    return _relation_membership_error(field_name, queryset, pks, pks)


def _coerce_relation_pk_or_none(related_model: type, pk: Any) -> Any:
    """Coerce a raw M2M pk through the target's pk field; ``None`` if uncoercible / out of range.

    The raw-pk M2M counterpart to ``relay.py::_coerce_pk_or_none`` (which coerces a
    ``GlobalID`` ``node_id`` through the resolved Strawberry type's id field). A
    raw-pk relation has no Relay-Node type and so no ``resolve_id_attr`` seam: the
    existence query filters on ``pk__in`` directly, so coercion is against
    ``related_model._meta.pk``. Coercion is ``to_python`` **then**
    ``run_validators`` - the same two-step the GlobalID path uses: ``to_python`` is
    a pure cast that does NOT range-check, so a syntactically-numeric but
    out-of-range literal (a pk beyond the backend's signed-64-bit column range)
    would reach ``pk__in`` and raise a raw backend ``OverflowError`` (``Python int
    too large to convert to SQLite INTEGER``); the field's ``integer_field_range``
    Min/MaxValueValidators reject it here as a ``ValidationError`` instead. An
    uncoercible / out-of-range pk is treated as "identifies no row" - excluded from
    the existence query (below) and so absent from the visible set, which makes it
    the same not-found ``relation_field_error`` as a genuinely missing pk, never a
    backend crash (feedback - relation huge-pk crash).
    """
    pk_field = related_model._meta.pk
    try:
        value = pk_field.to_python(pk)
        pk_field.run_validators(value)
    except (ValueError, ValidationError):
        return None
    return value


def _relation_existence_error(
    field_name: str,
    pks: list[Any],
    related_model: type,
) -> FieldError | None:
    """Confirm every raw-pk M2M member exists before the post-save ``.set(...)`` (feedback).

    The raw-pk counterpart to ``_relation_visibility_error``: a non-Relay-Node M2M
    target has no ``GlobalID`` visibility contract, but ``instance.<m2m>.set(pks)``
    writes a through-table row for any pk it is given, so a nonexistent pk would
    create a dangling FK row and return a false success. This confirms existence in
    one query against the target model's **default manager** (existence only, NOT
    the visibility ``get_queryset`` - a raw-pk relation carries no visibility
    contract). A missing member is the uniform ``relation_field_error`` on
    ``field_name``, the same field-keyed envelope the GlobalID path returns, so the
    whole write rolls back inside the transaction rather than persisting a dangling
    row. Used only for raw-pk M2M; the GlobalID path's visibility query already
    confirms existence (a hidden / missing pk is absent from the visible set).

    Each pk is coerced through the target pk field first (``_coerce_relation_pk_or_none``),
    mirroring the coercion the GlobalID path applies via ``decode_model_global_id``:
    an uncoercible / out-of-range pk is dropped from the ``pk__in`` query so it can
    never reach the backend as a raw ``OverflowError`` / ``ValueError``. Because the
    membership check below still compares the FULL input set against the queried
    rows, a dropped pk is absent from ``existing`` and so fails the subset check -
    the same not-found ``relation_field_error`` outcome as a valid-but-missing pk.
    """
    coerced = [
        value
        for value in (_coerce_relation_pk_or_none(related_model, pk) for pk in pks)
        if value is not None
    ]
    # Existence only (no visibility contract): query the default manager. The full
    # input set is asserted against the coerced query set (a dropped pk fails it).
    return _relation_membership_error(field_name, related_model._default_manager, pks, coerced)


def _raw_pk_relation_error(
    field_name: str,
    pks: list[Any],
    related_model: type,
    relation_field: Any,
    info: Any,
) -> FieldError | None:
    """Visibility- or existence-check a RAW-PK relation set before it is attached.

    A raw-pk relation (the related model has no Relay-Node primary, so the input is
    the related pk scalar, not a ``GlobalID``) is NOT automatically exempt from the
    related type's visibility contract. The original decode skipped visibility on
    the raw-pk branch on the premise that "a raw-pk target has no type to scope" -
    but ``registry.get(related_model)`` can return a **non-Relay** primary
    ``DjangoType`` that still defines a ``get_queryset`` (a supported
    configuration; the read surface scopes every list/node through it), in which
    case a writer could otherwise attach a row that hook hides. The form path
    already closes this on every branch (``_visible_related_object``); this is the
    model-path equivalent, so the model and form flavors enforce the SAME relation
    visibility invariant (spec-038 frames the form fix as closing the gap the
    ``036`` model path leaves).

    When a primary type IS registered the pks are visibility-checked through the
    SAME ``apply_type_visibility_sync(initial_queryset(...))`` query the
    ``GlobalID`` branch uses (a hidden / missing member is the uniform
    ``relation_field_error``, indistinguishable - no existence leak). When NO primary is
    registered there is no visibility contract: a raw-pk **M2M** set still needs the
    pre-``.set(...)`` existence check (``_relation_existence_error``), while a raw-pk
    **FK** relies on ``full_clean``'s own FK existence check.

    An explicit ``None`` is NOT a pk to check: on a single FK / OneToOne it is a
    nullable-relation clear (the decoded attr is set to ``NULL``, validated by
    ``full_clean`` for a non-nullable column), so it is dropped from the check and
    passed through. (An M2M never carries a ``None`` element - its list element type
    is non-null, and an explicit whole-list ``null`` is rejected upstream by
    ``_decode_relation_id_list``.)

    Each remaining pk is coerced through the target pk field first
    (``_coerce_relation_pk_or_none``), mirroring the ``GlobalID`` branch's
    ``decode_model_global_id`` coercion: an uncoercible / out-of-range raw pk is
    dropped from the ``pk__in`` query so it can never reach the backend as a raw
    ``OverflowError`` / ``ValueError`` and - absent from the visible set - yields
    the same not-found ``relation_field_error`` a genuinely missing pk does. An ``async
    def get_queryset`` met here raises ``SyncMisuseError`` (the standing sync
    discipline).
    """
    real_pks = [pk for pk in pks if pk is not None]
    if not real_pks:
        return None
    # ``related_visibility_queryset`` single-sites the ``registry.get`` resolve + the
    # visibility-scoping call (spec-039 Md3); ``None`` = no primary type (no
    # visibility contract), whose per-surface tail stays explicit here.
    queryset = related_visibility_queryset(related_model, info, _MUTATION_ASYNC_RECOURSE)
    if queryset is None:
        if getattr(relation_field, "many_to_many", False):
            return _relation_existence_error(field_name, real_pks, related_model)
        return None
    coerced = [
        value
        for value in (_coerce_relation_pk_or_none(related_model, pk) for pk in real_pks)
        if value is not None
    ]
    return _relation_membership_error(field_name, queryset, real_pks, coerced)


def locate_instance(
    target_type: type,
    node_id: Any,
    info: Any,
    *,
    select_for_update: bool = False,
) -> Any | None:
    """Locate an update / delete row through the visibility ``get_queryset`` (spec-036 Decision 10).

    ``apply_type_visibility_sync(target_type, initial_queryset(target_type),
    info).get(pk=node_id)`` - the same visibility queryset every read surface
    uses (and the ``_resolve_node_default`` locate shape). A miss
    (``DoesNotExist``) returns ``None``; the caller maps it to a not-found
    ``FieldError`` on ``id``, indistinguishable from a hidden row (no existence
    leak). An ``async def get_queryset`` met here raises ``SyncMisuseError``
    (``apply_type_visibility_sync`` closes the coroutine first).

    **Optional row lock (spec-039 rev6 #14).** When ``select_for_update`` is True the visible
    queryset is wrapped in ``.select_for_update()`` BEFORE the ``.get(pk=...)`` - so the lock is
    acquired AFTER visibility filtering, inside the pipeline's existing ``transaction.atomic()``
    boundary (the caller runs within it). On a backend without ``SELECT ... FOR UPDATE`` support
    (e.g. sqlite) Django silently skips the clause, so this is safe regardless of backend.
    """
    model = model_for(target_type)
    queryset = apply_type_visibility_sync(
        target_type,
        initial_queryset(target_type),
        info,
        _MUTATION_ASYNC_RECOURSE,
    )
    if select_for_update:
        queryset = queryset.select_for_update()
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


def field_error(path: str, messages: Any, *, codes: Any = None) -> FieldError:
    """Build ONE ``FieldError`` leaf for the shared envelope (spec-039 P2.4 / rev6 #4 / #13).

    The single leaf constructor BOTH the flat Django mapper
    (``validation_error_to_field_errors``) and the recursive DRF serializer
    flattener (``rest_framework/resolvers.py::serializer_errors_to_field_errors``)
    call, so the ``"__all__"`` sentinel + the message-container coercion + the
    structured ``path`` / ``codes`` derivation cannot drift between the two flatteners
    (nor across the three write flavors). An empty ``path`` (a model-wide / non-field
    error) is normalized to the ``NON_FIELD_ERROR_KEY`` sentinel (pinned to Django's
    ``"__all__"`` in ``mutations/inputs.py`` - AR-M3, single source). ``messages`` is
    coerced to a ``list[str]``: a bare string becomes a one-element list, any other
    iterable (a DRF ``ErrorDetail`` list, a tuple) is materialized as a list.

    **Structured ``path`` (rev6 #13):** the dotted ``path`` string is split into segments
    (``items.0.name`` -> ``["items", "0", "name"]``); an empty ``path`` (the root non-field
    error) yields ``[]`` while ``field`` is the ``"__all__"`` sentinel - the documented
    root rule. **Structured ``codes`` (rev6 #4):** the caller passes the DRF
    ``ErrorDetail.code``s / Django ``ValidationError.code``s (or a framework code); ``None``
    yields ``[]``.
    """
    key = path if path else NON_FIELD_ERROR_KEY
    message_list = [messages] if isinstance(messages, str) else [str(m) for m in messages]
    # rev6 #13 root rule: a model-wide / non-field error (an empty path, or the bare
    # ``"__all__"`` sentinel as the WHOLE path - the DRF flattener joins the top-level
    # non-field bucket to exactly that) carries an EMPTY ``path``, while ``field`` stays
    # ``"__all__"``; a NESTED non-field error (``items.0.__all__``) keeps its segments. So
    # the model + serializer flavors agree on the root-non-field shape.
    segments = [] if not path or path == NON_FIELD_ERROR_KEY else path.split(".")
    code_list = [codes] if isinstance(codes, str) else [str(c) for c in codes] if codes else []
    return FieldError(field=key, messages=message_list, codes=code_list, path=segments)


def relation_field_error(graphql_name: str) -> FieldError:
    """Build the uniform invalid / hidden / wrong-model relation ``FieldError`` (spec-039 integration).

    The single leaf constructor for the relation-decode error all three write
    flavors raise - the ``036`` model path (``_decode_relation_id_set`` /
    ``_relation_membership_error``), the ``038`` form decoder, and the ``039``
    serializer decoder all call this DIRECTLY (spec-039 Mn1 folded away the former
    per-flavor ``_relation_error`` / ``_relation_field_error`` aliases). A
    wrong-model, hidden, missing, or uncoercible id all collapse to this one
    field-keyed shape (no existence leak), keyed to the GraphQL wire name the
    client sent (``categoryId``). Siblings the ``field_error`` leaf ctor above so
    the ``"Invalid id for relation ..."`` message + leaf construction are single
    sourced across every flavor (AR-H4).
    """
    return field_error(graphql_name, f"Invalid id for relation {graphql_name!r}.", codes="invalid")


def validation_error_to_field_errors(exc: ValidationError) -> list[FieldError]:
    """Map a Django ``ValidationError`` to the ``FieldError`` envelope (spec-036 Decision 7 / AR-M3).

    Uses ``exc.error_dict`` when present (per-field), keying the model's
    ``NON_FIELD_ERRORS`` bucket to the ``NON_FIELD_ERROR_KEY`` sentinel (pinned to
    ``"__all__"`` in ``mutations/inputs.py`` - AR-M3, single source) so a
    multi-field-constraint error surfaces under ``"__all__"``. Falls back to
    ``exc.messages`` under the sentinel for a non-dict ``ValidationError``. The
    single source for both the ``full_clean()`` failure and the
    ``IntegrityError``-race fallback mapping. Both leaves are built through the
    shared ``field_error`` leaf ctor (P2.4) so the sentinel + message coercion stay
    single-sited with the recursive DRF flattener.
    """
    if hasattr(exc, "error_dict"):
        errors: list[FieldError] = []
        for field_name, field_errors in exc.error_dict.items():
            path = "" if field_name == NON_FIELD_ERRORS else field_name
            messages = [message for error in field_errors for message in error.messages]
            # rev6 #4: preserve each leaf Django ``ValidationError.code`` alongside the
            # message (``error.error_list`` is the flattened leaf list ``error.messages``
            # reads; a ``None`` code is dropped).
            codes = [leaf.code for error in field_errors for leaf in error.error_list if leaf.code]
            errors.append(field_error(path, messages, codes=codes))
        return errors
    codes = [leaf.code for leaf in exc.error_list if leaf.code]
    return [field_error("", list(exc.messages), codes=codes)]


def _integrity_error_field_errors() -> list[FieldError]:
    """Map a save-time ``IntegrityError`` to the ``"__all__"`` envelope (spec-036 Major-2).

    The normal ``UniqueConstraint`` path is caught earlier by ``full_clean()``'s
    ``validate_constraints()`` as a ``ValidationError`` with a clean field mapping
    (Major-2). What reaches HERE is the residual: a constraint violation that beat
    ``validate_constraints()`` - a ``UniqueConstraint`` race, but also a ``NOT
    NULL`` / FK / ``CHECK`` ``IntegrityError`` that ``full_clean`` did not catch on
    the normal path. The catch is ``except IntegrityError`` (broad), so the message
    is the **honest superset** "A database constraint was violated." rather than
    over-claiming "uniqueness" for a violation that may not be a uniqueness one
    (feedback CR-3). As a documented best-effort fallback (covered by a
    mocked-``save()`` test, not a real race), it keys to the ``"__all__"`` sentinel
    - the same model-level bucket ``validate_constraints()`` uses for a multi-field
    constraint. The decoded field set is intentionally not consulted: ``save()``'s
    ``IntegrityError`` carries no reliable cross-backend field mapping, so a
    per-field attribution would be guesswork (feedback CR-3 - dropped the unused
    ``model`` / ``provided_attrs`` params rather than feign a refinement).
    """
    return [field_error("", "A database constraint was violated.", codes="constraint")]


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


def refetch_optimized(
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


def build_payload(
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
    thread_sensitive=True)`` (spec-036 AR-M4). Dispatches on ``meta.operation``: the
    model-backed create / update branches ride the promoted shared
    ``run_write_pipeline_sync`` skeleton (spec-039 P1.5 - the ``transaction.atomic()``
    boundary + authorize-before-decode ordering single-sited across the model, form,
    and serializer flavors), supplying only the model ``decode_step`` / ``write_step``
    callbacks; the ``delete`` branch keeps its own snapshot-before-delete body (F6 -
    no data, no decode, a snapshot re-fetch BEFORE the row is deleted, so it is
    excluded from the create/update skeleton).
    """
    meta = mutation_cls._mutation_meta
    primary_type = mutation_cls._primary_type

    if meta.operation == "delete":
        slot = payload_object_slot(primary_type)
        payload_cls = payload_cls_for(mutation_cls)
        with transaction.atomic():
            return _run_delete(mutation_cls, info, id, primary_type, slot, payload_cls)

    model = model_for(primary_type)
    return run_write_pipeline_sync(
        mutation_cls,
        info,
        data,
        id,
        decode_step=lambda instance: _model_decode_step(model, data, info, instance=instance),
        write_step=lambda instance, decoded: _model_write_step(instance, decoded),
    )


def _model_decode_step(
    model: type,
    data: Any,
    info: Any,
    *,
    instance: Any,
    excluded_input_fields: frozenset[str] = frozenset(),
) -> tuple[Any, ...] | list[FieldError]:
    """The model ``decode_step``: relation-decode + construct / ``setattr`` (spec-039 P1.5).

    Decodes the input relations (the ``036`` ``_decode_relations`` contract:
    type-check + visibility on every branch), then either CONSTRUCTS a fresh
    ``model(**attrs)`` (create, ``instance is None``) or sets the provided attrs on
    the located row (update). Returns ``(constructed_instance, m2m_assignments,
    exclude)`` for the write step, or a ``list[FieldError]`` on a decode failure
    (the skeleton maps it to a null-object payload). ``exclude`` is the AR-H2-aware
    unprovided-field list for BOTH create and update - create excludes unprovided
    fields so their model defaults are not validated (mirroring
    ``Model.objects.create()``), update excludes unprovided fields so an unsent
    column keeps its stored value, both keep validating any unprovided field
    co-participating in a unique constraint with a provided one.

    ``excluded_input_fields`` is the spec-040 D6 exclusion seam (the register
    flavor's ``password``): the named provided attrs are captured OUT of the model
    construction by ``_decode_relations`` (the raw value never becomes a model
    attr) **with their provided-marker preserved** - the captured names are folded
    back into the AR-H2 ``provided`` set below, so the excluded column still
    participates in ``full_clean`` validation (naively popping it pre-walk would
    mark it unprovided and silently drop it from the exclude calculation - the
    spec-040 Revision-7 marker fix). A NON-EMPTY exclusion returns the extended
    tuple ``(target, m2m_assignments, exclude, excluded_values)``; the default
    no-exclusion call keeps the exact historical three-tuple, so the model
    flavor's ``_model_write_step`` contract is byte-unchanged.
    """
    scalar_and_fk_attrs, m2m_assignments, excluded_values, decode_error = _decode_relations(
        model,
        data,
        info,
        excluded_input_fields=excluded_input_fields,
    )
    if decode_error is not None:
        return [decode_error]

    if instance is None:
        target = model(**scalar_and_fk_attrs)
    else:
        target = instance
        for attr, value in scalar_and_fk_attrs.items():
            setattr(target, attr, value)

    provided = _provided_attr_names(model, scalar_and_fk_attrs, m2m_assignments)
    # The exclusion seam preserves the provided-marker (spec-040 D6): an excluded
    # input WAS provided, so it still counts for the AR-H2 exclude calculation.
    provided |= set(excluded_values)
    exclude = _unprovided_exclude(model, provided)
    if excluded_input_fields:
        return target, m2m_assignments, exclude, excluded_values
    return target, m2m_assignments, exclude


def _model_write_step(
    instance: Any,
    decoded: tuple[Any, list[Any], list[str] | None],
) -> Any | list[FieldError]:
    """The model ``write_step``: ``full_clean`` -> ``save`` -> M2M (spec-039 P1.5).

    From validation onward create and update run an IDENTICAL tail (the prior
    ``_validate_save_assign_refetch_payload``): ``full_clean(exclude=...)`` mapped to
    the envelope, ``save()`` (race ``IntegrityError`` into the envelope), then the
    M2M ``.set(...)`` assignment. Returns the saved instance (the skeleton's
    ``refetch_optimized`` re-fetches it by pk under the G2 plan) or a
    ``list[FieldError]`` on a validation / write failure. ``instance`` is the located
    update row (ignored - the constructed target rides in ``decoded`` so create's
    fresh instance is used), kept in the signature for the skeleton's
    ``write_step(instance, decoded)`` contract.
    """
    del instance  # the constructed / mutated target is ``decoded[0]``.
    target, m2m_assignments, exclude = decoded

    clean_errors = _full_clean_or_field_errors(target, exclude=exclude)
    if clean_errors is not None:
        return clean_errors

    write_error = save_or_field_errors(target.save)
    if write_error is not None:
        return write_error
    _assign_m2m(target, m2m_assignments)
    return target


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
    loaded into the instance) BEFORE the row is deleted (spec-036 AR-M5 /
    Medium-2), so the detached in-memory instance's relations survive the row's
    deletion. The re-fetch is by pk without the visibility filter (Medium-1),
    consistent with create / update.

    The deletion runs against the **located instance**, not the returned
    snapshot: Django's ``Model.delete()`` sets ``instance.pk = None`` on the
    object it is called on, so deleting via ``instance`` leaves the snapshot's
    ``pk`` / ``id`` intact for the delete payload's cache-eviction contract
    (feedback P1 - the spec promises the deleted id is preserved). ``instance`` is
    the visibility-located row (guaranteed present here); the snapshot is only the
    optimizer-shaped response object.
    """
    node_id, id_error = coerce_lookup_id(id, primary_type)
    if id_error is not None:
        return build_payload(payload_cls, slot, None, [id_error])
    instance = locate_instance(primary_type, node_id, info)
    if instance is None:
        return build_payload(payload_cls, slot, None, [not_found_error()])

    authorize_or_raise(mutation_cls, info, "delete", data=None, instance=instance)

    snapshot = refetch_optimized(primary_type, instance.pk, info, force_load=True)
    instance.delete()
    return build_payload(payload_cls, slot, snapshot, [])


def authorize_or_raise(
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

    A coroutine return - an ``async def check_permission`` override - is NOT
    silently treated as "allow": a coroutine is truthy, so ``if not coroutine``
    would never deny, letting an async deny-check pass (an authorization bypass,
    feedback). It is closed and raised as a ``SyncMisuseError`` (the async hook
    can never be awaited in this sync pipeline), mirroring ``get_queryset``'s
    discipline. The async-``has_permission`` case is rejected one level down, in
    ``check_permission`` itself.
    """
    allowed = reject_async_in_sync_context(
        mutation_cls().check_permission(info, operation, data, instance),
        owner=mutation_cls.__name__,
        method="check_permission",
        context="mutation",
        recourse=_PERMISSION_ASYNC_RECOURSE,
    )
    if not allowed:
        # The model / ``ModelForm`` flavor names its target model
        # (``_primary_type.__name__``); a plain ``DjangoFormMutation`` carries
        # ``_primary_type is None`` (no object to return - spec-038 Decision 6), so
        # fall back to the mutation class name, keeping ONE auth gate for both
        # flavors (spec-038 Slice 3 plain-form auth-message discretion).
        target_name = getattr(mutation_cls._primary_type, "__name__", mutation_cls.__name__)
        raise GraphQLError(f"Not authorized to {operation} {target_name}.")


def _full_clean_or_field_errors(
    instance: Any,
    *,
    exclude: list[str] | None,
) -> list[FieldError] | None:
    """Run ``full_clean(exclude=...)``; return the mapped ``FieldError``s on failure else ``None``.

    ``full_clean()`` runs ``validate_constraints()``, so a ``UniqueConstraint``
    duplicate is caught here as a ``ValidationError`` BEFORE ``save()`` (Major-2);
    its field-keyed messages populate the envelope (multi-field constraint ->
    ``"__all__"`` sentinel, AR-M3). ``exclude=None`` for create (validate all
    fields); the AR-H2-aware exclude list for update. Returns the
    ``list[FieldError]`` (the model ``write_step`` short-circuits to a null-object
    payload through the shared skeleton) so the payload build stays single-sited in
    ``run_write_pipeline_sync`` (spec-039 P1.5).
    """
    try:
        instance.full_clean(exclude=exclude)
    except ValidationError as exc:
        return validation_error_to_field_errors(exc)
    return None


def save_or_field_errors(save_callable: Any) -> list[FieldError] | None:
    """Run ``save_callable()``; map a race ``IntegrityError`` to the envelope else ``None`` (Major-2).

    Wraps a zero-arg callable rather than a fixed ``instance.save()`` so ONE
    ``IntegrityError`` -> envelope catch (the ``_integrity_error_field_errors``
    message policy, single-sourced) serves every save path: the ``036`` model
    pipeline passes ``instance.save``; the form pipeline passes ``form.save`` (the
    ``ModelForm`` flavor) / a bound ``perform_mutate`` (the plain flavor, spec-038
    Decision 8 step 5). A post-validation ``IntegrityError`` from any of them
    returns the same ``"__all__"`` envelope, never a top-level ``GraphQLError`` at
    the write.
    """
    try:
        save_callable()
    except IntegrityError:
        return _integrity_error_field_errors()
    return None


def coerce_lookup_id(id: Any, target_type: type) -> tuple[Any, FieldError | None]:  # noqa: A002
    """Decode + type-check the update/delete ``id:`` against the target model (feedback #1).

    ``DjangoMutationField`` declares ``id`` as ``strawberry.ID`` - the
    ``node(id: ID!)`` Relay-spec signature the shipped ``DjangoNodeField`` uses
    (``relay.py`` line 287), so the package decodes the GlobalID **server-side**
    rather than letting Strawberry's argument coercion own it. The wire value
    therefore arrives as a base64 GlobalID string; it is run through the shared
    ``decode_model_global_id`` primitive (DRY-2) against the mutation's target
    model - the same decode + model-check + pk-coercion contract the relation
    ``<field>_id`` decode uses, and the identity guard the typed ``DjangoNodeField``
    applies (``relay.py::_check_typed_match``).

    The :class:`GlobalIDDecode` status maps to this surface's two error shapes:

    - ``DECODE_FAILED`` (malformed / unresolvable type, or a raw pk string with no
      GlobalID shape) and ``WRONG_MODEL`` (a well-formed id for the *wrong* model)
      are an **invalid-id** ``FieldError`` on ``id`` BEFORE any pk lookup - no DB
      read, no existence leak, never coerced to a bare pk that would target the
      same-pk row of the right model (feedback #1);
    - ``UNCOERCIBLE_PK`` (a right-type id whose ``node_id`` is not a valid pk
      literal, e.g. ``"abc"`` for an integer pk) is the **not-found** ``FieldError``
      on ``id`` - identifies no row, exactly like the node field returns ``null``,
      never the raw Django ``ValueError`` that would leak the pk column type
      (feedback CR-1).

    Returns ``(pk, None)`` on success or ``(None, FieldError)`` otherwise.
    """
    target_model = model_for(target_type)
    result = decode_model_global_id(id, target_model)
    if result.status in (GlobalIDDecode.DECODE_FAILED, GlobalIDDecode.WRONG_MODEL):
        return None, _invalid_lookup_id_error()
    if result.status is GlobalIDDecode.UNCOERCIBLE_PK:
        return None, not_found_error()
    return result.pk, None


def not_found_error() -> FieldError:
    """Build the not-found ``FieldError`` on ``id`` (hidden or missing - no existence leak)."""
    return field_error("id", "No matching row found.", codes="not_found")


def _invalid_lookup_id_error() -> FieldError:
    """Build the wrong-type / unresolvable ``id`` ``FieldError`` (decided pre-lookup - no existence leak).

    A ``GlobalID`` whose decoded type is not the mutation's target model (or whose
    type cannot be resolved) is rejected here rather than coerced to a bare pk; the
    failure is determined from the id's type slot alone, without a DB read, so it
    reveals nothing about row existence (spec-036 Decision 10 / finding-#1).
    """
    return field_error("id", "Invalid id.", codes="invalid")


def payload_cls_for(mutation_cls: type) -> type:
    """Return the materialized ``<Name>Payload`` class for a bound mutation (all three pipelines).

    The Slice-2 bind stashes the payload class name on the mutation
    (``_payload_type_name``) and materializes the class as a module global of
    ``mutations.inputs``; the resolver reads it from there so the payload type the
    field's lazy ref resolves to and the type the resolver instantiates are the
    same object.

    Promoted (underscore-dropped) so the form pipeline reuses it BY CALL rather than
    re-spelling it: both form flavors materialize their ``<Name>Payload`` into
    ``mutations.inputs`` too (the ``ModelForm`` via the ``036`` ``_bind_mutation``,
    the plain via ``_bind_form_mutation``), so this one ``getattr`` serves the model,
    ``ModelForm``, and plain-form pipelines alike (spec-038 DRY).
    """
    from . import inputs

    return getattr(inputs, mutation_cls._payload_type_name)


async def run_pipeline_async(
    sync_body: Any,
    mutation_cls: type,
    info: Any,
    data: Any,
    id: Any,  # noqa: A002
) -> Any:
    """Run a sync mutation/form pipeline body in one ``sync_to_async(thread_sensitive=True)`` call.

    The shared async boundary both the model (``resolve_mutation_async``) and form
    (``forms/resolvers.py::resolve_form_async``) entries delegate to - the
    byte-identical ``sync_to_async(..., thread_sensitive=True)(mutation_cls, info,
    data, id)`` wrapper, single-sourced so the two flavors cannot drift on the
    boundary contract. ``sync_body`` is the flavor's ``_run_*_pipeline_sync``: it
    runs on ONE worker thread so its ``transaction.atomic()`` + every ORM call never
    interleave with ``await``s (spec-036 AR-M4); a sync ``get_queryset`` runs
    synchronously inside that thread, while an ``async def get_queryset`` raises
    ``SyncMisuseError`` there (no awaiting context - the standing discipline).
    """
    return await run_in_one_sync_boundary(sync_body, mutation_cls, info, data, id)


async def run_in_one_sync_boundary(fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Run ``fn(*args, **kwargs)`` in ONE ``sync_to_async(thread_sensitive=True)`` worker.

    The generic one-boundary primitive (spec-040 D17 / P3): the mutation entry
    (``run_pipeline_async`` above, which keeps its mutation-shaped signature and
    the pinned AR-M4 contract) and the auth fixed-field async dispatchers
    (``auth/mutations.py`` - gate-then-session-work in one worker) share this one
    ``sync_to_async`` call, so the boundary discipline (one worker per resolution,
    ``thread_sensitive=True``, never per-step hops) cannot drift between flavors.
    A ``sync_to_async`` worker is itself a sync context, so the standing
    ``SyncMisuseError`` guards still fire inside ``fn``.
    """
    return await sync_to_async(fn, thread_sensitive=True)(*args, **kwargs)


def make_resolver_entries(sync_body: Any) -> tuple[Any, Any]:
    """Return the ``(resolve_sync, resolve_async)`` module-entry pair for a write flavor (spec-039 M1a).

    The two byte-parallel module-level entries every dispatcher-backed write flavor
    exposes: a sync entry normalizing the ``UNSET``-default ``data`` / ``id`` kwargs
    to ``sync_body``'s positional args, and an async entry running the SAME
    ``sync_body`` through the shared ``run_pipeline_async`` boundary (one
    ``sync_to_async(thread_sensitive=True)`` call). The model flavor
    (``sync_body=_run_pipeline_sync``) and the form flavor
    (``_run_form_pipeline_sync``) take the full pair; the serializer flavor takes
    ONLY the async half (its sync entry is bespoke - it calls
    ``run_write_pipeline_sync`` with decode/write lambdas directly, no
    ``_run_*_pipeline_sync`` dispatcher), discarding the generated sync entry. Each
    factory call produces FRESH functions, so per-flavor identity (the field
    factory's ``resolve_sync.__func__`` comparisons) stays distinct.
    """

    def resolve_sync(
        mutation_cls: type,
        info: Any,
        *,
        data: Any = strawberry.UNSET,
        id: Any = strawberry.UNSET,  # noqa: A002
    ) -> Any:
        """Normalize the ``UNSET``-default kwargs to ``sync_body``'s positional args."""
        return sync_body(mutation_cls, info, data, id)

    async def resolve_async(
        mutation_cls: type,
        info: Any,
        *,
        data: Any = strawberry.UNSET,
        id: Any = strawberry.UNSET,  # noqa: A002
    ) -> Any:
        """Run ``sync_body`` in one ``sync_to_async(thread_sensitive=True)`` call."""
        return await run_pipeline_async(sync_body, mutation_cls, info, data, id)

    return resolve_sync, resolve_async


# The model-flavor module entry points (spec-036 Decision 8), via the shared factory
# (spec-039 M1a). ``resolve_mutation_sync`` normalizes the ``UNSET`` kwargs to
# ``_run_pipeline_sync``; ``resolve_mutation_async`` runs it through the shared async
# boundary. The field factory (``mutations/fields.py``) reads both by name.
resolve_mutation_sync, resolve_mutation_async = make_resolver_entries(_run_pipeline_sync)
