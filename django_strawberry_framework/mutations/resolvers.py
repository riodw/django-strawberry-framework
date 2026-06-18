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
import inspect
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
from ..utils.inputs import graphql_camel_name
from ..utils.querysets import SyncMisuseError, apply_type_visibility_sync, initial_queryset
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

# The recourse appended to a ``SyncMisuseError`` raised when a permission hook
# (``check_permission`` / a ``permission_classes`` entry's ``has_permission``)
# returns a coroutine. Write authorization runs synchronously in the same sync
# pipeline (spec-036 Decision 15), so an async permission hook can never be
# awaited here - and silently treating its truthy coroutine as "allow" is an
# authorization BYPASS (feedback - async permission bypass). It is rejected
# loud, the same discipline ``apply_type_visibility_sync`` applies to an async
# ``get_queryset``.
_PERMISSION_ASYNC_RECOURSE = (
    "A DjangoMutation runs its permission check synchronously, so it cannot await "
    "an async permission hook; redefine has_permission / check_permission as a sync "
    "method returning a bool."
)


def _decode_relations(
    model: type,
    data: Any,
    info: Any,
) -> tuple[dict[str, Any], list[Any], FieldError | None]:
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
    ``FieldError``, never attached. A raw pk scalar (a non-Relay target) is passed
    through unchanged - no decode and
    no visibility check (there is no Relay-Node target type to scope it).

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
            pks, error = _decode_relation_id_list(graphql_name, value, m2m_field, info)
            if error is not None:
                return {}, [], error
            m2m_assignments.append((python_name, pks))
            continue

        fk_field = fk_by_attr.get(python_name)
        if fk_field is not None:
            pk, error = _decode_single_relation_id(graphql_name, value, fk_field, info)
            if error is not None:
                return {}, [], error
            scalar_and_fk_attrs[python_name] = pk
            continue

        null_error = _explicit_null_error(model, python_name, graphql_name, value)
        if null_error is not None:
            return {}, [], null_error
        text_error = _unencodable_text_error(graphql_name, value)
        if text_error is not None:
            return {}, [], text_error
        scalar_and_fk_attrs[python_name] = _make_aware_if_naive(_raw_choice_value(value))

    return scalar_and_fk_attrs, m2m_assignments, None


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
    return FieldError(field=field_name, messages=["This field cannot be null."])


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
            return FieldError(
                field=field_name,
                messages=["Text contains invalid Unicode (unpaired surrogate code points)."],
            )
    return None


def _raw_choice_value(value: Any) -> Any:
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
    ``_relation_error`` on ``field_name`` (AR-H4 + feedback CR-1: a wrong-type id
    is never a cross-model lookup, an uncoercible pk is never a raw ``ValueError``).
    A raw pk scalar (a non-Relay-Node target, which has no ``GlobalID`` shape)
    passes through unchanged - no decode, no coercion, no visibility hook to apply.
    The decoded ``GlobalID`` set is then visibility-checked in one query (Decision
    10 / feedback P1): a hidden / missing member is the same ``_relation_error``,
    indistinguishable (no existence leak). A list is homogeneously typed (all
    ``GlobalID`` for a Relay target, all raw pk otherwise), so ``needs_visibility``
    is all-or-nothing and the whole coerced set is checked together.

    A raw-pk **M2M** set carries no ``GlobalID`` visibility contract, but it is
    still assigned post-save via ``instance.<m2m>.set(pks)``, which writes
    through-table rows for WHATEVER pks it is handed - a nonexistent pk produces a
    dangling through row (an invalid FK SQLite flags at teardown) and a false
    "success" (feedback - raw-pk M2M accepts nonexistent ids). So a raw-pk M2M set
    is existence-checked in one query before the assignment. A raw-pk FK needs no
    such check: ``full_clean()`` validates FK existence against the column before
    ``save()``; M2M is the only relation written outside ``full_clean``.
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
            return [], _relation_error(field_name)
        pks.append(result.pk)
        needs_visibility = True
    if needs_visibility:
        error = _relation_visibility_error(field_name, pks, expected_model, info)
        if error is not None:
            return [], error
    elif pks and getattr(relation_field, "many_to_many", False):
        error = _relation_existence_error(field_name, pks, expected_model)
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


def _relation_error(field_name: str) -> FieldError:
    """Build the uniform wrong/invalid/hidden relation-id ``FieldError`` for ``field_name``."""
    return FieldError(
        field=field_name,
        messages=[f"Invalid id for relation {field_name!r}."],
    )


def _relation_null_error(field_name: str) -> FieldError:
    """Build the explicit-``null`` M2M ``FieldError`` for ``field_name`` (feedback P2).

    A generated optional M2M field is ``list[<id>] | None``, so a client can send
    an explicit ``null``. ``null`` is not a valid replace-set (the M2M contract is
    replace-on-provide / clear-on-empty / unchanged-on-omit - AR-M1), so it is
    rejected as a field-keyed error naming the clear signal, rather than iterating
    ``None`` into a resolver exception.
    """
    return FieldError(
        field=field_name,
        messages=[f"Relation {field_name!r} cannot be null; send an empty list to clear it."],
    )


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
    indistinguishable (the uniform ``_relation_error``, no existence leak),
    matching the update/delete locate (``_locate_instance``); FK / OneToOne pass a
    one-element list, M2M the whole set (verified in one ``pk__in`` query). An
    ``async def get_queryset`` met here raises ``SyncMisuseError`` (the same sync
    discipline as the locate path).

    The ``pks`` arrive **already coerced** through the resolved type's pk field by
    ``decode_model_global_id`` (the shared DRY-2 primitive), so an uncoercible
    ``node_id`` was already mapped to ``_relation_error`` upstream and never reaches
    the ``pk__in`` query as a raw Django ``ValueError`` (feedback CR-1). This step
    only confirms visibility.
    """
    related_type = registry.get(related_model)
    queryset = apply_type_visibility_sync(
        related_type,
        initial_queryset(related_type),
        info,
        _MUTATION_ASYNC_RECOURSE,
    )
    visible = {str(pk) for pk in queryset.filter(pk__in=pks).values_list("pk", flat=True)}
    if not {str(pk) for pk in pks} <= visible:
        return _relation_error(field_name)
    return None


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
    contract). A missing member is the uniform ``_relation_error`` on
    ``field_name``, the same field-keyed envelope the GlobalID path returns, so the
    whole write rolls back inside the transaction rather than persisting a dangling
    row. Used only for raw-pk M2M; the GlobalID path's visibility query already
    confirms existence (a hidden / missing pk is absent from the visible set).
    """
    existing = {
        str(pk)
        for pk in related_model._default_manager.filter(pk__in=pks).values_list("pk", flat=True)
    }
    if not {str(pk) for pk in pks} <= existing:
        return _relation_error(field_name)
    return None


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
    return [
        FieldError(
            field=NON_FIELD_ERROR_KEY,
            messages=["A database constraint was violated."],
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


def _validate_save_assign_refetch_payload(
    instance: Any,
    *,
    exclude: list[str] | None,
    m2m_assignments: list[Any],
    primary_type: type,
    info: Any,
    slot: str,
    payload_cls: type,
) -> Any:
    """The shared create / update write-finalization tail (spec-036 Decision 8 / DRY-3).

    ``create`` and ``update`` necessarily differ in their PRELUDE (authorization
    placement, instance construction vs. visibility-located + ``setattr``, and the
    partial-update ``exclude`` calculation), but from validation onward they run an
    IDENTICAL tail: ``full_clean(exclude=...)`` into the envelope, ``save()`` (race
    ``IntegrityError`` into the envelope), M2M assignment, the optimizer-planned
    re-fetch by pk, and the success payload. Single-sourcing it here means a future
    change to write finalization, save-error mapping, M2M timing, or the post-write
    re-fetch is made ONCE rather than patched in both branches. ``exclude`` is the
    AR-H2-aware unprovided-field list for BOTH create and update: create excludes
    unprovided fields so their model defaults are not validated (mirroring
    ``Model.objects.create()``), update excludes unprovided fields so an unsent
    column keeps its stored value - both keep validating any unprovided field
    co-participating in a unique constraint with a provided one.
    """
    error_payload = _full_clean_or_payload(
        instance,
        exclude=exclude,
        slot=slot,
        payload_cls=payload_cls,
    )
    if error_payload is not None:
        return error_payload

    write_error = _save_or_field_errors(instance)
    if write_error is not None:
        return _build_payload(payload_cls, slot, None, write_error)
    _assign_m2m(instance, m2m_assignments)

    obj = _refetch_optimized(primary_type, instance.pk, info, force_load=False)
    return _build_payload(payload_cls, slot, obj, [])


def _run_create(
    mutation_cls: type,
    info: Any,
    data: Any,
    model: type,
    primary_type: type,
    slot: str,
    payload_cls: type,
) -> Any:
    """The ``create`` branch: authorize -> build -> [validate -> save -> M2M -> re-fetch -> payload].

    ``full_clean`` excludes the fields the input did NOT provide (the AR-H2-aware
    set, minus any unprovided field co-participating in a unique constraint with a
    provided field). An unprovided field gets its MODEL default, which
    ``Model.objects.create()`` applies WITHOUT validation; validating it here is
    stricter than the contract and rejects a legitimate omission - e.g. a
    ``JSONField(default=dict)`` (``blank=False``) fails ``full_clean`` ("cannot be
    blank") on its own empty default when omitted (feedback - empty-value defaults).
    Excluding unprovided fields mirrors ``create()`` while still validating every
    PROVIDED value and every uniqueness constraint a provided field touches. A
    genuinely required field (no default, ``null=False``, ``blank=False``) is
    input-required, so it can never be unprovided here.
    """
    _authorize_or_raise(mutation_cls, info, "create", data, instance=None)

    scalar_and_fk_attrs, m2m_assignments, decode_error = _decode_relations(model, data, info)
    if decode_error is not None:
        return _build_payload(payload_cls, slot, None, [decode_error])

    instance = model(**scalar_and_fk_attrs)
    provided = _provided_attr_names(model, scalar_and_fk_attrs, m2m_assignments)
    exclude = _unprovided_exclude(model, provided)
    return _validate_save_assign_refetch_payload(
        instance,
        exclude=exclude,
        m2m_assignments=m2m_assignments,
        primary_type=primary_type,
        info=info,
        slot=slot,
        payload_cls=payload_cls,
    )


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
    """The ``update`` branch: locate -> authorize -> set provided -> [validate -> save -> re-fetch]."""
    node_id, id_error = _coerce_lookup_id(id, primary_type)
    if id_error is not None:
        return _build_payload(payload_cls, slot, None, [id_error])
    instance = _locate_instance(primary_type, node_id, info)
    if instance is None:
        return _build_payload(payload_cls, slot, None, [_not_found_error()])

    _authorize_or_raise(mutation_cls, info, "update", data, instance=instance)

    scalar_and_fk_attrs, m2m_assignments, decode_error = _decode_relations(model, data, info)
    if decode_error is not None:
        return _build_payload(payload_cls, slot, None, [decode_error])

    for attr, value in scalar_and_fk_attrs.items():
        setattr(instance, attr, value)

    provided = _provided_attr_names(model, scalar_and_fk_attrs, m2m_assignments)
    exclude = _unprovided_exclude(model, provided)
    return _validate_save_assign_refetch_payload(
        instance,
        exclude=exclude,
        m2m_assignments=m2m_assignments,
        primary_type=primary_type,
        info=info,
        slot=slot,
        payload_cls=payload_cls,
    )


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
    node_id, id_error = _coerce_lookup_id(id, primary_type)
    if id_error is not None:
        return _build_payload(payload_cls, slot, None, [id_error])
    instance = _locate_instance(primary_type, node_id, info)
    if instance is None:
        return _build_payload(payload_cls, slot, None, [_not_found_error()])

    _authorize_or_raise(mutation_cls, info, "delete", data=None, instance=instance)

    snapshot = _refetch_optimized(primary_type, instance.pk, info, force_load=True)
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

    A coroutine return - an ``async def check_permission`` override - is NOT
    silently treated as "allow": a coroutine is truthy, so ``if not coroutine``
    would never deny, letting an async deny-check pass (an authorization bypass,
    feedback). It is closed and raised as a ``SyncMisuseError`` (the async hook
    can never be awaited in this sync pipeline), mirroring ``get_queryset``'s
    discipline. The async-``has_permission`` case is rejected one level down, in
    ``check_permission`` itself.
    """
    allowed = mutation_cls().check_permission(info, operation, data, instance)
    if inspect.iscoroutine(allowed):
        allowed.close()
        raise SyncMisuseError(
            f"{mutation_cls.__name__}.check_permission returned a coroutine in a sync "
            f"mutation context. {_PERMISSION_ASYNC_RECOURSE}",
        )
    if not allowed:
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


def _save_or_field_errors(instance: Any) -> list[FieldError] | None:
    """``save()`` the instance; map a race ``IntegrityError`` to the envelope else ``None`` (Major-2)."""
    try:
        instance.save()
    except IntegrityError:
        return _integrity_error_field_errors()
    return None


def _coerce_lookup_id(id: Any, target_type: type) -> tuple[Any, FieldError | None]:  # noqa: A002
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
    target_model = target_type.__django_strawberry_definition__.model
    result = decode_model_global_id(id, target_model)
    if result.status in (GlobalIDDecode.DECODE_FAILED, GlobalIDDecode.WRONG_MODEL):
        return None, _invalid_lookup_id_error()
    if result.status is GlobalIDDecode.UNCOERCIBLE_PK:
        return None, _not_found_error()
    return result.pk, None


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
