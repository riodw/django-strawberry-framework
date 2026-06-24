"""The sync + async form-mutation resolver pipeline (spec-038 Slice 3).

The form-flavor write runtime, the sibling of ``mutations/resolvers.py`` (the
``036`` model pipeline). The pipeline is (spec-038 Decision 8):

    (update) locate -> authorize -> decode -> construct + validate-once
            -> write -> (ModelForm) re-fetch -> payload

**Authorize runs BEFORE the relation decode** (matching the ``036`` model path):
the decode issues visibility-scoped ``get_queryset`` queries, so running it
pre-auth would let an unauthorized caller probe related-object visibility by id
(a write-auth denial ``GraphQLError`` vs an in-band relation ``FieldError`` is an
observable distinction). For ``update`` the locate must precede authorize (object
-level perms need the instance), exactly as the model path locates first.

and the form-specific invariants this module owns:

- **The decode produces a FORM-field-keyed ``provided_data`` + a separate
  ``provided_files``** (Decision 8 step 1). A bound Django form is keyed by FORM
  field name (``ItemModelForm(data={"category": pk})``, never ``{"category_id":
  pk}``) and reads uploads from ``files=``, never ``data=``. The Slice-1 reverse
  map (``mutation_cls._input_field_specs``, a list of
  ``converter.FormInputFieldSpec``) routes each provided input attr to its form
  field name + decode ``kind`` (``SCALAR`` / ``RELATION_SINGLE`` /
  ``RELATION_MULTI`` / ``FILE``).

- **The dedicated form relation decoder visibility-checks EVERY branch**
  (Decision 7 / Decision 8 step 1, P1). Each relation id - a ``relay.GlobalID``
  *or* a raw pk - is type-checked (``decode_model_global_id`` for the Relay
  branch, ``_coerce_relation_pk_or_none`` for the raw-pk branch), then **resolved
  to the visible object through the related primary ``DjangoType.get_queryset``**
  (``apply_type_visibility_sync(initial_queryset(...))``), closing the raw-pk
  visibility gap ``036``'s ``_decode_relation_id_set`` leaves (which skips
  visibility on the raw-pk branch). A hidden / wrong-model / uncoercible id is a
  field-keyed ``FieldError`` (hidden and missing indistinguishable, no existence
  leak). The visible object is converted to the form-key value by
  ``to_field_name`` (``obj.serializable_value(field.to_field_name)`` else
  ``obj.pk``) so the bound form validates by the same key it was built on.

- **``update`` reconstructs the full bound payload** (Decision 8 step 4, P1):
  ``data = {**model_to_dict(instance, <the form's non-file fields>),
  **provided_data}``, ``files = provided_files``. ``model_to_dict`` supplies FK
  as pk and M2M as ``[pk]`` under the form field name, so an omitted scalar / FK /
  M2M keeps the located row's value; an omitted file is preserved via the bound
  ``form_class(instance=...)``'s ``initial`` (never re-supplied, never cleared). A
  required non-model extra field stays required in the Slice-1 partial input, so
  it is always present in ``provided_data``.

- **The form is constructed once via the overridable ``get_form`` /
  ``get_form_kwargs`` hooks** (Decision 8 step 4 / Decision 6); ``form.is_valid()``
  runs once. A failure maps ``form.errors`` onto the ``FieldError`` envelope via
  the reused ``validation_error_to_field_errors(ValidationError(
  form.errors.as_data()))`` (the form's ``NON_FIELD_ERRORS`` bucket lands on the
  ``"__all__"`` sentinel ``036`` froze, byte-identically to a model
  ``full_clean()`` failure).

- **Write via ``form.save()`` (``ModelForm``) / ``perform_mutate`` (plain),
  wrapped by the reused ``save_or_field_errors`` ``IntegrityError`` -> envelope
  mapper** (Decision 8 step 5, P1) - one catch, never a top-level ``GraphQLError``
  at the write.

- **The ``ModelForm`` re-fetch rides the ``036`` ``refetch_optimized`` G2 path**
  (Decision 9): by pk WITHOUT the visibility filter, routed through
  ``apply_connection_optimization`` so the spec-035 G2 gate keeps
  ``select_related`` / ``prefetch_related`` and applies NO ``.only(...)`` under the
  mutation operation - it comes for free, no new optimizer code.

- **One ``transaction.atomic()`` boundary; the async path runs the sync body in
  one ``sync_to_async(thread_sensitive=True)`` call** (Decision 8) - the same
  boundary shape ``036`` set, a deliberate same-shape sibling (the body differs,
  so it is a structural parallel, not a call).

- **``SyncMisuseError`` discipline** is inherited from
  ``apply_type_visibility_sync``: a sync form mutation meeting an ``async def
  get_queryset`` (a relation decode or the update locate) closes the coroutine and
  raises.

DRY-FIRST: the locate / authorize / id-decode / re-fetch / payload /
validation-mapper / save-mapper are the promoted ``036`` public helpers, CALLED
not re-implemented. The genuinely net-new code is the visibility-on-every-branch
relation decoder, the ``kind``-split decode, and the partial-update
reconstruction.
"""

from __future__ import annotations

from typing import Any

import strawberry
from asgiref.sync import sync_to_async
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms.models import model_to_dict
from strawberry import relay

from ..mutations.resolvers import (
    _coerce_relation_pk_or_none,
    authorize_or_raise,
    build_payload,
    coerce_lookup_id,
    locate_instance,
    not_found_error,
    raw_choice_value,
    refetch_optimized,
    save_or_field_errors,
)
from ..relay import GlobalIDDecode, decode_model_global_id
from ..utils.querysets import apply_type_visibility_sync, initial_queryset
from .converter import FILE, RELATION_MULTI, RELATION_SINGLE, FormInputFieldSpec
from .inputs import get_form_fields

# The async-pipeline recourse appended to a ``SyncMisuseError`` raised when an
# async ``get_queryset`` is met inside the (sync) form pipeline. Mirrors the
# ``036`` ``_MUTATION_ASYNC_RECOURSE`` wording: the whole pipeline runs
# synchronously (under one ``sync_to_async`` worker on the async surface), so an
# ``async def get_queryset`` can never be awaited here.
_FORM_ASYNC_RECOURSE = (
    "A form mutation runs its ORM pipeline synchronously (under one sync_to_async "
    "call on the async surface), so it cannot await an async get_queryset hook; "
    "redefine the target type's get_queryset as a sync method."
)


def _relation_field_error(graphql_name: str) -> Any:
    """Build the uniform invalid / hidden / wrong-model relation ``FieldError``.

    Keys to the input field's GraphQL wire name (``categoryId``) - what the client
    sent - matching the ``036`` relation decode's AR-H4 contract. Hidden, missing,
    wrong-model, and uncoercible all collapse to this one shape (no existence
    leak).
    """
    from ..mutations.inputs import FieldError

    return FieldError(field=graphql_name, messages=[f"Invalid id for relation {graphql_name!r}."])


def _visible_related_object(related_model: type, pk: Any, info: Any) -> Any | None:
    """Resolve the VISIBLE related object by pk through the related primary's ``get_queryset``.

    The visibility-on-every-branch query (the net-new security code). Resolves the
    related model's primary ``DjangoType`` via the registry and runs the SAME
    visibility hook every read surface applies
    (``apply_type_visibility_sync(initial_queryset(...))``), so a writer cannot
    attach a row they could not *see*. Returns the visible object or ``None``
    (hidden / missing - the caller maps ``None`` to the field-keyed ``FieldError``,
    indistinguishable). The decoder needs the OBJECT (to apply ``to_field_name``),
    which the ``036`` ``_relation_visibility_error`` does not return, so it cannot
    call that helper - but it reuses the same primitives so the query shape is
    identical. An ``async def get_queryset`` met here raises ``SyncMisuseError``.

    The related model has a primary type only when a ``GlobalID``-typed relation
    input was generated for it; a raw-pk relation's primary is resolved the same
    way (``registry.get``), and a model with no primary still resolves via the
    default manager scoped by the (no-op) visibility hook.
    """
    from ..registry import registry

    related_type = registry.get(related_model)
    if related_type is None:
        # No primary DjangoType: a raw-pk relation with no Relay-Node target. Scope
        # existence against the default manager (no visibility contract to apply).
        return related_model._default_manager.filter(pk=pk).first()
    queryset = apply_type_visibility_sync(
        related_type,
        initial_queryset(related_type),
        info,
        _FORM_ASYNC_RECOURSE,
    )
    return queryset.filter(pk=pk).first()


def _to_form_key_value(obj: Any, form_field: Any) -> Any:
    """Convert a resolved relation object to its form-key value via ``to_field_name`` (P2 #6).

    A ``ModelChoiceField`` / ``ModelMultipleChoiceField`` with ``to_field_name``
    set validates the bound value against THAT field (``obj.serializable_value(
    to_field_name)``), not the pk; an unset ``to_field_name`` keys by ``obj.pk``.
    So the bound form's ``to_python`` resolves the same value the decode produced.
    """
    to_field_name = getattr(form_field, "to_field_name", None)
    if to_field_name:
        return obj.serializable_value(to_field_name)
    return obj.pk


def _decode_form_relation_single(
    value: Any,
    *,
    graphql_name: str,
    form_field: Any,
    info: Any,
) -> tuple[Any, Any | None]:
    """Decode ONE relation id to its form-key value, visibility-checked (NET-NEW, P1).

    The body: (i) a ``relay.GlobalID`` runs through ``decode_model_global_id``
    against the related model - a non-``OK`` status (decode-failed / wrong-model /
    uncoercible) is a field-keyed ``FieldError``; (ii) a raw pk runs through
    ``_coerce_relation_pk_or_none`` - ``None`` (uncoercible / out of range) is a
    field-keyed ``FieldError``; (iii) for BOTH branches, resolve the VISIBLE object
    via ``_visible_related_object`` - a hidden / missing row is the SAME
    field-keyed ``FieldError`` (closing the raw-pk visibility gap); (iv) convert
    the object to the form key by ``to_field_name``.

    Returns ``(form_key_value, None)`` on success or ``(None, FieldError)``. The
    related model is the form field's ``queryset.model`` (single-sourced off the
    form field for BOTH the model-backed and model-less relation, matching the
    Slice-1 input id basis).

    An explicit ``null`` (or any of the form field's ``empty_values``) is NOT an
    id to decode: it is a clear / no-value. It is passed through unchanged so the
    bound form's OWN validation decides - a required ``ModelChoiceField`` raises
    its field-keyed required error via ``form.is_valid()``, an optional one clears
    to the empty value (``docs/feedback.md`` Finding 4). Treating it as a raw pk
    instead would mis-report a decode-level "Invalid id for relation" error and
    block a legitimate nullable-FK clear.
    """
    if value in form_field.empty_values:
        return value, None
    related_model = form_field.queryset.model
    if isinstance(value, relay.GlobalID):
        result = decode_model_global_id(value, related_model)
        if result.status is not GlobalIDDecode.OK:
            return None, _relation_field_error(graphql_name)
        pk = result.pk
    else:
        pk = _coerce_relation_pk_or_none(related_model, value)
        if pk is None:
            return None, _relation_field_error(graphql_name)

    obj = _visible_related_object(related_model, pk, info)
    if obj is None:
        return None, _relation_field_error(graphql_name)
    return _to_form_key_value(obj, form_field), None


def _decode_form_relation_multi(
    values: Any,
    *,
    graphql_name: str,
    form_field: Any,
    info: Any,
) -> tuple[Any, Any | None]:
    """Decode an M2M ``list[<id>]`` to a list of form-key values, visibility-checked (NET-NEW, P1).

    Maps ``_decode_form_relation_single`` over each element (so every member is
    type-checked, visibility-checked on its own branch, and ``to_field_name``
    converted) and returns the list under the form field name. The first member
    error short-circuits. An empty list is a valid clear.

    An explicit ``null`` (or any of the form field's ``empty_values``, including
    the empty list) clears the M2M: return ``[]`` so the bound form decides
    required-ness (required -> a field-keyed error via ``form.is_valid()``;
    optional -> clear) and ``None`` is NEVER iterated - iterating it would raise a
    top-level ``TypeError`` instead of the field-keyed envelope
    (``docs/feedback.md`` Finding 4).
    """
    if values in form_field.empty_values:
        return [], None
    keys: list[Any] = []
    for value in values:
        key, error = _decode_form_relation_single(
            value,
            graphql_name=graphql_name,
            form_field=form_field,
            info=info,
        )
        if error is not None:
            return None, error
        keys.append(key)
    return keys, None


def _decode_form_data(
    mutation_cls: type,
    data: Any,
    info: Any,
) -> tuple[dict[str, Any], dict[str, Any], Any | None]:
    """Decode the bound input dataclass into ``(provided_data, provided_files, error)`` (NET-NEW).

    Walks the provided input fields (``UNSET`` stripped) and, using the
    bind-stashed per-field reverse map (``mutation_cls._input_field_specs``,
    keyed by input attr), routes each value by ``kind`` to the right FORM-keyed
    place:

    - ``SCALAR`` -> ``provided_data[form_field_name]``, the choice-enum member
      unwrapped to its raw Django value via the reused ``raw_choice_value``.
    - ``RELATION_SINGLE`` / ``RELATION_MULTI`` -> the visibility-checked,
      ``to_field_name``-converted relation value(s) under ``form_field_name``.
    - ``FILE`` -> ``provided_files[form_field_name]`` (NEVER ``data=`` - a bound
      Django form reads uploads from ``files=``).

    A relation decode ``FieldError`` short-circuits. This is net-new because the
    ``036`` ``_decode_relations`` keys on MODEL attrs (``<field>_id`` -> pk) and
    never splits files out; the form decode keys on FORM-field names.
    """
    spec_by_attr: dict[str, FormInputFieldSpec] = {
        spec.input_attr: spec for spec in mutation_cls._input_field_specs
    }
    form_fields = get_form_fields(mutation_cls._mutation_meta.form_class)

    provided_data: dict[str, Any] = {}
    provided_files: dict[str, Any] = {}

    for field in data.__strawberry_definition__.fields:
        python_name = field.python_name
        value = getattr(data, python_name, strawberry.UNSET)
        if value is strawberry.UNSET:
            continue
        spec = spec_by_attr[python_name]
        form_field = form_fields[spec.form_field_name]

        if spec.kind in (RELATION_SINGLE, RELATION_MULTI):
            decoder = (
                _decode_form_relation_multi
                if spec.kind == RELATION_MULTI
                else _decode_form_relation_single
            )
            decoded, error = decoder(
                value,
                graphql_name=spec.graphql_name,
                form_field=form_field,
                info=info,
            )
            if error is not None:
                return {}, {}, error
            provided_data[spec.form_field_name] = decoded
        elif spec.kind == FILE:
            provided_files[spec.form_field_name] = value
        else:
            provided_data[spec.form_field_name] = raw_choice_value(value)

    return provided_data, provided_files, None


def _non_file_form_field_names(mutation_cls: type) -> list[str]:
    """Return the form's non-file DECLARED field names for ``model_to_dict`` reconstruction.

    Derived from the form's FULL declared field set (``get_form_fields``), **not**
    the (possibly narrowed) generated-input reverse map: a ``Meta.fields`` /
    ``Meta.exclude`` narrowing drops the excluded model-backed fields from the
    GraphQL input, but the bound ``ModelForm`` still validates EVERY field it
    declares. Reconstructing only the narrowed input fields would leave an excluded
    required model-backed field (e.g. a narrowed-away ``category``) absent from the
    bound ``data=``, so the form fails its required / composite-uniqueness
    validation against a field the client never narrowed away. Reconstructing from
    ``base_fields`` instead preserves the located row's value for every declared
    field, while the resolver still overlays ONLY the provided input (so the
    excluded fields stay invisible on the wire) - ``docs/feedback.md`` Finding 3.

    A file field's ``model_to_dict`` value is the stored relative path, NOT a
    re-bindable ``data=`` value, so file fields are excluded (an omitted file is
    preserved via the bound form's ``instance=`` ``initial`` instead);
    ``forms.ImageField`` subclasses ``forms.FileField``, so the one ``isinstance``
    catches both. A declared non-model extra field (a ``confirm``) is harmlessly
    included - ``model_to_dict`` ignores any name that is not a model column, and
    a required extra stays required in the partial input so it is always provided.
    """
    form_fields = get_form_fields(mutation_cls._mutation_meta.form_class)
    return [name for name, field in form_fields.items() if not isinstance(field, forms.FileField)]


def _reconstruct_partial_data(
    mutation_cls: type,
    instance: Any,
    provided_data: dict[str, Any],
) -> dict[str, Any]:
    """Reconstruct the full bound ``data=`` for a partial ``ModelForm`` update (NET-NEW, P1).

    ``data = {**model_to_dict(instance, fields=<non-file form fields>),
    **provided_data}`` - ``model_to_dict`` supplies FK as pk and M2M as ``[pk]``
    under the form field name, so an omitted scalar / FK / M2M keeps the located
    row's value while a provided field overrides it. The ``unique_*`` constraint
    therefore validates on a one-field change (the unchanged co-member comes from
    ``model_to_dict``). Net-new: the ``036`` update does ``setattr`` on the located
    instance, not a ``model_to_dict`` payload reconstruction.
    """
    base = model_to_dict(instance, fields=_non_file_form_field_names(mutation_cls))
    return {**base, **provided_data}


def _form_payload_cls(mutation_cls: type) -> type:
    """Return the materialized ``<Name>Payload`` class for a bound form mutation.

    Both flavors' payloads materialize into ``mutations.inputs`` (the ``ModelForm``
    via the ``036`` ``_bind_mutation``, the plain via ``_bind_form_mutation``'s
    ``materialize_mutation_input_class``) - the INPUT (``data:``) lives in
    ``forms.inputs``, but the PAYLOAD lives in ``mutations.inputs`` for BOTH, so
    the resolver reads it from there (the ``036`` ``_payload_cls_for`` shape).
    """
    from ..mutations import inputs

    return getattr(inputs, mutation_cls._payload_type_name)


def _form_errors_to_field_errors(form: Any) -> list[Any]:
    """Map a failed form's ``form.errors`` onto the ``FieldError`` envelope.

    Reuses the ``036`` ``validation_error_to_field_errors`` over a
    ``ValidationError(form.errors.as_data())``: ``as_data()`` yields the
    ``{field: [ValidationError, ...]}`` shape the mapper's ``error_dict`` branch
    consumes, so the form's ``NON_FIELD_ERRORS`` bucket keys to the ``"__all__"``
    sentinel byte-identically to a model ``full_clean()`` failure (Decision 8
    step 4). No parallel mapper.
    """
    from ..mutations.resolvers import validation_error_to_field_errors

    return validation_error_to_field_errors(ValidationError(form.errors.as_data()))


def _run_modelform_pipeline_sync(
    mutation_cls: type,
    info: Any,
    data: Any,
    id: Any,  # noqa: A002
) -> Any:
    """The ``ModelForm`` flavor body (locate -> authorize -> decode -> validate -> save -> refetch)."""
    from ..mutations.inputs import payload_object_slot

    meta = mutation_cls._mutation_meta
    primary_type = mutation_cls._primary_type
    slot = payload_object_slot(primary_type)
    payload_cls = _form_payload_cls(mutation_cls)
    is_update = meta.operation == "update"

    with transaction.atomic():
        instance = None
        if is_update:
            node_id, id_error = coerce_lookup_id(id, primary_type)
            if id_error is not None:
                return build_payload(payload_cls, slot, None, [id_error])
            instance = locate_instance(primary_type, node_id, info)
            if instance is None:
                return build_payload(payload_cls, slot, None, [not_found_error()])

        # Authorize BEFORE decoding relations: the decode issues visibility-scoped
        # ``get_queryset`` queries, so running it pre-auth would let an unauthorized
        # caller probe related-object visibility by id (denial vs relation FieldError).
        # Matches the ``036`` model path's locate -> authorize -> decode order.
        authorize_or_raise(mutation_cls, info, meta.operation, data, instance=instance)

        provided_data, provided_files, decode_error = _decode_form_data(mutation_cls, data, info)
        if decode_error is not None:
            return build_payload(payload_cls, slot, None, [decode_error])

        if is_update:
            form_data = _reconstruct_partial_data(mutation_cls, instance, provided_data)
        else:
            form_data = provided_data
        form = mutation_cls().get_form(
            info,
            data=form_data,
            files=provided_files,
            instance=instance,
        )

        if not form.is_valid():
            return build_payload(payload_cls, slot, None, _form_errors_to_field_errors(form))

        write_error = save_or_field_errors(form.save)
        if write_error is not None:
            return build_payload(payload_cls, slot, None, write_error)

        obj = refetch_optimized(primary_type, form.instance.pk, info, force_load=False)
        return build_payload(payload_cls, slot, obj, [])


def _run_plain_form_pipeline_sync(mutation_cls: type, info: Any, data: Any) -> Any:
    """The plain ``DjangoFormMutation`` body: authorize -> decode -> validate -> write -> ``{ ok errors }``.

    No ``id`` (no row to locate), no object slot (no ``DjangoType`` to return), no
    re-fetch. The payload is the pinned ``{ ok errors }`` shape, instantiated
    directly (NOT via ``build_payload``, which keys on ``slot``). The write is
    ``perform_mutate`` (default ``form.save()`` if present, else no-op), wrapped by
    the same ``save_or_field_errors`` ``IntegrityError`` mapper.
    """
    payload_cls = _form_payload_cls(mutation_cls)

    with transaction.atomic():
        # Authorize BEFORE decoding (see the ModelForm body): a plain form with a
        # ``ModelChoiceField`` would otherwise let an unauthorized caller probe
        # relation visibility pre-auth.
        authorize_or_raise(
            mutation_cls,
            info,
            mutation_cls._mutation_meta.operation,
            data,
            instance=None,
        )

        provided_data, provided_files, decode_error = _decode_form_data(mutation_cls, data, info)
        if decode_error is not None:
            return payload_cls(ok=False, errors=[decode_error])

        instance = mutation_cls()
        form = instance.get_form(info, data=provided_data, files=provided_files, instance=None)

        if not form.is_valid():
            return payload_cls(ok=False, errors=_form_errors_to_field_errors(form))

        write_error = save_or_field_errors(lambda: instance.perform_mutate(form, info))
        if write_error is not None:
            return payload_cls(ok=False, errors=write_error)

        return payload_cls(ok=True, errors=[])


def _run_form_pipeline_sync(
    mutation_cls: type,
    info: Any,
    data: Any,
    id: Any,  # noqa: A002
) -> Any:
    """Dispatch to the ``ModelForm`` vs plain-form sync body (one ``transaction.atomic()`` each).

    Branches on ``mutation_cls._primary_type is None`` (the plain
    ``DjangoFormMutation`` carries ``None``; the ``ModelForm`` flavor a real
    primary type). The single sync body the async path wraps in one
    ``sync_to_async(thread_sensitive=True)`` call.
    """
    if mutation_cls._primary_type is None:
        return _run_plain_form_pipeline_sync(mutation_cls, info, data)
    return _run_modelform_pipeline_sync(mutation_cls, info, data, id)


def resolve_form_sync(
    mutation_cls: type,
    info: Any,
    *,
    data: Any = strawberry.UNSET,
    id: Any = strawberry.UNSET,  # noqa: A002
) -> Any:
    """Sync form-pipeline entry the form bases' ``resolve_sync`` delegates to (spec-038 Decision 8).

    The form-flavor parallel of ``mutations/resolvers.py::resolve_mutation_sync``:
    a thin public entry normalizing the ``UNSET``-default kwargs to the body's
    positional args. The plain flavor never passes ``id`` (its ``resolve_sync``
    signature has no ``id`` param), so it defaults to ``UNSET`` and the plain body
    ignores it.
    """
    return _run_form_pipeline_sync(mutation_cls, info, data, id)


async def resolve_form_async(
    mutation_cls: type,
    info: Any,
    *,
    data: Any = strawberry.UNSET,
    id: Any = strawberry.UNSET,  # noqa: A002
) -> Any:
    """Async form-pipeline entry: the sync body in one ``sync_to_async(thread_sensitive=True)`` (Decision 8).

    Does NOT re-implement the pipeline - it wraps the SAME
    ``_run_form_pipeline_sync`` body (the same boundary shape ``036`` set) so the
    ``transaction.atomic()`` + every ORM call run on one worker thread under
    Django's async-safety contract, never interleaving ORM work with ``await``s. A
    sync ``get_queryset`` runs synchronously inside the thread; an ``async def
    get_queryset`` raises ``SyncMisuseError`` there.
    """
    return await sync_to_async(_run_form_pipeline_sync, thread_sensitive=True)(
        mutation_cls,
        info,
        data,
        id,
    )
