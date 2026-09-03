"""The sync + async form-mutation resolver pipeline (spec-038).

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
  pk}``) and reads uploads from ``files=``, never ``data=``. The reverse
  map (``mutation_cls._input_field_specs``, a list of
  ``utils/inputs.py::InputFieldSpec``) routes each provided input attr to its form
  field name + decode ``kind`` (``SCALAR`` / ``RELATION_SINGLE`` /
  ``RELATION_MULTI`` / ``FILE``).

- **The dedicated form relation decoder visibility-checks EVERY branch**
  (Decision 7 / Decision 8 step 1). Each relation id - a ``relay.GlobalID``
  *or* a raw pk - is type-checked (``decode_model_global_id`` for the Relay
  branch, ``_coerce_relation_pk_or_none`` for the raw-pk branch), then **resolved
  to the visible object through the related primary ``DjangoType.get_queryset``**
  (``apply_type_visibility_sync(initial_queryset(...))``). The model flavor's
  batched set decoder now shares ``decode_visible_relation_ids`` (visibility on
  every branch, including raw pk); the form still maps per element because it
  needs the related object for ``to_field_name``. A hidden / wrong-model /
  uncoercible id is a field-keyed ``FieldError`` (hidden and missing
  indistinguishable, no existence leak). The visible object is converted to the
  form-key value by
  ``to_field_name`` (``obj.serializable_value(field.to_field_name)`` else
  ``obj.pk``) so the bound form validates by the same key it was built on.

- **``update`` reconstructs the full bound payload** (Decision 8 step 4): for
  every non-file declared form field the input did not provide, supply the located
  row's value under the form field name, then overlay ``provided_data``; ``files =
  provided_files``. Scalars + a ``to_field_name``-less FK come
  from ``model_to_dict`` (the FK's stored ``attname`` IS the ``to_field`` / pk key the
  bound form resolves), while M2M and a ``ModelChoiceField`` with ``to_field_name`` set
  are reconstructed from the related object(s) as ``to_field_name`` values
  (``_to_form_key_value``) so an omitted relation binds in the SAME shape a provided one
  decodes to (Decision 8). An
  omitted file is preserved via the bound ``form_class(instance=...)``'s ``initial``
  (never re-supplied, never cleared). A required non-model extra field stays
  required in the partial input, so it is always present in
  ``provided_data``. This is a partial-input transport, not partial validation:
  the reconstructed bound ``ModelForm`` revalidates every declared field. An
  omitted value that is already stored but no longer satisfies the current form
  (for example after a validator was tightened) therefore blocks the mutation.
  The caller must supply a valid replacement in the same request, or repair the
  row out of band when the field is excluded from the generated input; the
  framework never silently excludes an invalid untouched field from validation.

- **The form is constructed once via the overridable ``get_form`` /
  ``get_form_kwargs`` hooks** (Decision 8 step 4 / Decision 6); ``form.is_valid()``
  runs once. A failure maps ``form.errors`` onto the ``FieldError`` envelope via
  the reused ``validation_error_to_field_errors(ValidationError(
  form.errors.as_data()))`` (the form's ``NON_FIELD_ERRORS`` bucket lands on the
  ``"__all__"`` sentinel ``036`` froze, byte-identically to a model
  ``full_clean()`` failure).

- **Write via ``form.save()`` (``ModelForm``) / ``perform_mutate`` (plain),
  wrapped by the reused ``save_or_field_errors`` ``IntegrityError`` -> envelope
  mapper** (Decision 8 step 5) - one catch, never a top-level ``GraphQLError``
  at the write.

- **The ``ModelForm`` re-fetch rides the ``036`` ``refetch_optimized`` G2 path**
  (Decision 9): by pk WITHOUT the visibility filter, routed through
  ``apply_connection_optimization`` so the spec-035 G2 gate keeps
  ``select_related`` / ``prefetch_related`` and applies NO ``.only(...)`` under the
  mutation operation - it comes for free, no new optimizer code.

- **One ``transaction.atomic()`` boundary; the async path runs the sync body in
  one ``sync_to_async(thread_sensitive=True)`` call** (Decision 8) - both form
  flavors ride ``run_write_pipeline_sync`` for that boundary, the same skeleton
  the model / serializer / delete paths use.

- **``SyncMisuseError`` discipline** is inherited from
  ``apply_type_visibility_sync``: a sync form mutation meeting an ``async def
  get_queryset`` (a relation decode or the update locate) closes the coroutine and
  raises.

Single-sourced: the locate / authorize / id-decode / re-fetch / payload /
validation-mapper / save-mapper are the promoted ``036`` public helpers, CALLED
not re-implemented. The genuinely net-new code is the visibility-on-every-branch
relation decoder, the ``kind``-split decode, and the partial-update
reconstruction.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django import forms
from django.core.exceptions import FieldDoesNotExist, ObjectDoesNotExist, ValidationError
from django.forms.models import model_to_dict

from ..mutations.resolvers import (
    make_resolver_entries,
    run_write_pipeline_sync,
    save_or_field_errors,
)
from ..utils.querysets import sync_pipeline_recourse
from ..utils.write_transaction import pipeline_write_phase
from ..utils.write_values import (
    decode_field_handlers,
    decode_provided_fields,
    decode_visible_relation,
    relation_field_error,
)

# The async-pipeline recourse appended to a ``SyncMisuseError`` raised when an
# async ``get_queryset`` is met inside the (sync) form pipeline. Mirrors the
# ``036`` ``_MUTATION_ASYNC_RECOURSE`` wording: the whole pipeline runs
# synchronously (under one ``sync_to_async`` worker on the async surface), so an
# ``async def get_queryset`` can never be awaited here.
_FORM_ASYNC_RECOURSE = sync_pipeline_recourse("form mutation")


def _to_form_key_value(obj: Any, form_field: Any) -> Any:
    """Convert a resolved relation object to its form-key value via ``to_field_name``.

    A ``ModelChoiceField`` / ``ModelMultipleChoiceField`` with ``to_field_name``
    set validates the bound value against THAT field (``obj.serializable_value(
    to_field_name)``), not the pk; an unset ``to_field_name`` keys by ``obj.pk``.
    So the bound form's ``to_python`` resolves the same value the decode produced.
    """
    to_field_name = getattr(form_field, "to_field_name", None)
    if to_field_name:
        try:
            if hasattr(obj, "serializable_value"):
                return obj.serializable_value(to_field_name)
        except (AttributeError, FieldDoesNotExist):
            pass
    return getattr(obj, "pk", obj)


def _is_empty_form_value(candidate: Any, form_field: Any) -> bool:
    """Return whether ``candidate`` matches the form field's empty values safely."""
    empty_values = getattr(
        form_field,
        "empty_values",
        (
            None,
            "",
            [],
            (),
            {},
        ),
    )
    try:
        return candidate in empty_values
    except TypeError:
        return False


def _decode_form_relation_single(
    value: Any,
    *,
    graphql_name: str,
    related_model: Any,
    form_field: Any,
    info: Any,
) -> tuple[Any, Any | None]:
    """Decode ONE relation id to its form-key value, visibility-checked.

    The form coloring of the shared
    ``utils/write_values.py::decode_visible_relation`` spine:
    type-check + pk coercion -> visible object (a hidden / missing / wrong-model
    / uncoercible id is the uniform field-keyed ``FieldError``, closing the
    raw-pk visibility gap) -> the form-key projection via ``to_field_name``
    (``_to_form_key_value``). The ``related_model`` is the target the
    build recorded on the reverse-map spec (``InputFieldSpec.related_model``),
    from the SAME basis the generated id type used (the backing column's
    ``related_model`` for a ``ModelForm`` column, else the form field's
    ``queryset.model``). It is NOT re-derived from ``form_field.queryset.model``
    here: the decode reads the CLASS-level ``base_fields`` field, whose
    ``queryset`` is ``None`` under the request-scoped-choices idiom (a FK declared
    ``ModelChoiceField(queryset=None)`` that assigns the queryset in ``__init__``),
    which would crash with a bare ``AttributeError`` on ``None.model``. The
    ``form_field`` is still consulted for ``empty_values`` (the skip) and
    ``to_field_name`` (the projection), both class-level and queryset-independent.

    An explicit ``null`` (or any of the form field's ``empty_values``) is NOT an
    id to decode: it is a clear / no-value, skipped through UNCHANGED so the
    bound form's OWN validation decides - a required ``ModelChoiceField`` raises
    its field-keyed required error via ``form.is_valid()``, an optional one clears
    to the empty value (spec-038 Decision 8 step 1). Treating it as a raw pk
    instead would mis-report a decode-level "Invalid id for relation" error and
    block a legitimate nullable-FK clear.
    """
    return decode_visible_relation(
        value,
        graphql_name=graphql_name,
        related_model=related_model,
        info=info,
        async_recourse=_FORM_ASYNC_RECOURSE,
        skip=lambda candidate: _is_empty_form_value(candidate, form_field),
        project=lambda obj: _to_form_key_value(obj, form_field),
    )


def _decode_form_relation_multi(
    values: Any,
    *,
    graphql_name: str,
    related_model: Any,
    form_field: Any,
    info: Any,
) -> tuple[Any, Any | None]:
    """Decode an M2M ``list[<id>]`` to a list of form-key values, visibility-checked (NET-NEW).

    Maps ``_decode_form_relation_single`` over each element (so every member is
    type-checked, visibility-checked on its own branch, and ``to_field_name``
    converted) and returns the list under the form field name. The first member
    error short-circuits. An empty list is a valid clear.

    An explicit ``null`` (or any of the form field's ``empty_values``, including
    the empty list) clears the M2M: return ``[]`` so the bound form decides
    required-ness (required -> a field-keyed error via ``form.is_valid()``;
    optional -> clear) and ``None`` is NEVER iterated - iterating it would raise a
    top-level ``TypeError`` instead of the field-keyed envelope
    (spec-038 Decision 8 step 1).

    This DIVERGES, deliberately, from the model ``DjangoMutation`` path, which
    rejects an explicit ``null`` M2M with a field-keyed error
    (``mutations/resolvers.py::_relation_null_error`` - "use ``[]`` to clear, not
    ``null``"). A bound ``ModelForm`` follows Django form semantics, where an empty
    value clears an optional M2M (and a required one errors), so the form flavor
    honors the form's own required-ness rather than imposing the model path's
    stricter "null is never a valid replace-set" stance (spec-038 Decision 8 step 1).
    """
    if _is_empty_form_value(values, form_field):
        return [], None
    if isinstance(
        values,
        (
            str,
            bytes,
            bytearray,
            memoryview,
            Mapping,
        ),
    ):
        return None, relation_field_error(graphql_name)
    try:
        provided_values = list(values)
    except BaseException:
        return None, relation_field_error(graphql_name)
    keys: list[Any] = []
    for value in provided_values:
        key, error = _decode_form_relation_single(
            value,
            graphql_name=graphql_name,
            related_model=related_model,
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

    - ``SCALAR`` -> ``provided_data[target_name]``, through the shared
      scalar leaf ``decode_scalar_leaf`` (invalid-Unicode preflight +
      choice-enum unwrap).
    - ``RELATION_SINGLE`` / ``RELATION_MULTI`` -> the visibility-checked,
      ``to_field_name``-converted relation value(s) under ``target_name``.
    - ``FILE`` -> ``provided_files[target_name]`` (NEVER ``data=`` - a bound
      Django form reads uploads from ``files=``).

    A relation decode ``FieldError`` short-circuits. The reverse-map build + the
    ``UNSET``-strip walk + the kind dispatch are single-sited in
    ``utils/write_values.py::decode_provided_fields``; the SCALAR / RELATION /
    FILE store-into-dest handlers are the shared ``decode_field_handlers``
    factories. Flavor coloring stays in the relation decoders (``empty_values``
    skip + ``to_field_name``) and in ``file_dest=provided_files`` (Django
    ``files=``, never ``data=``).
    """
    form_fields = dict(mutation_cls.get_form_fields())

    provided_data: dict[str, Any] = {}
    provided_files: dict[str, Any] = {}
    handlers, scalar_handler = decode_field_handlers(
        provided_data,
        info=info,
        single=_decode_form_relation_single,
        multi=_decode_form_relation_multi,
        file_dest=provided_files,
        extra=lambda spec: {"form_field": form_fields.get(spec.target_name)},
    )
    error = decode_provided_fields(
        mutation_cls._input_field_specs,
        data,
        handlers=handlers,
        scalar_handler=scalar_handler,
    )
    if error is not None:
        return {}, {}, error
    return provided_data, provided_files, None


def _reconstruct_partial_data(
    mutation_cls: type,
    instance: Any,
    provided_data: dict[str, Any],
) -> dict[str, Any]:
    """Reconstruct the full bound ``data=`` for a partial ``ModelForm`` update (NET-NEW).

    For every non-file declared form field NOT overridden by ``provided_data``,
    supply the located row's value under the form field name, then overlay
    ``provided_data``; ``files`` is supplied separately and an omitted file is
    preserved via the bound ``form_class(instance=...)``'s ``initial``. The result
    lets the bound form validate a one-field change against the row's other
    (unchanged) values - e.g. a ``unique_together`` co-member comes from the row,
    not the input. That full-form validation is deliberate: if an unchanged stored
    value no longer passes the form's current validators, the mutation fails without
    writing any field. The client must include a valid replacement in the same
    partial input (or the consumer must repair the row out of band if narrowing
    excluded that field); untouched fields are not silently exempted.

    Two reconstruction shapes, each matching what the DECODE produces for a PROVIDED
    field so an omitted field binds byte-compatibly with a provided one:

    - **Scalars + plain FK / OneToOne** come from ``model_to_dict``: a FK's value is
      its ``attname`` (the stored ``to_field`` value - the pk by default, or the
      ``ForeignKey(to_field=...)`` value), which is exactly the key the bound
      ``ModelChoiceField`` resolves and what ``_to_form_key_value`` produces for a
      provided FK. So a ``to_field_name``-LESS FK / scalar needs no special handling.
    - **A ``ModelChoiceField`` with ``to_field_name`` set** is reconstructed from the
      related object via ``_to_form_key_value`` (the ``to_field_name`` value), NOT
      ``model_to_dict`` (which yields the pk / model ``to_field`` value). The bound
      form validates that single FK against ``to_field_name`` (``queryset.get(
      <to_field_name>=value)``), so a ``model_to_dict`` pk would fail ``to_python``
      for an OMITTED unchanged FK while a PROVIDED unchanged FK (decoded to the
      ``to_field_name`` value) passes - the same omitted-vs-provided inconsistency
      the M2M branch already fixes. Gated on ``to_field_name`` so the
      common ``to_field_name``-less FK keeps its cheap ``model_to_dict`` path (no
      per-FK related-object fetch); a nullable FK whose row value is ``None`` falls
      through to ``model_to_dict`` (the form's empty value), never
      ``_to_form_key_value(None, ...)``.
    - **M2M** is reconstructed as a list of ``_to_form_key_value(obj, form_field)``
      (the ``to_field_name`` value, default ``obj.pk``) - NOT ``model_to_dict``'s
      list of related INSTANCES. For a ``ModelMultipleChoiceField`` with
      ``to_field_name`` set, the bound form looks members up by THAT key, so a
      ``model_to_dict`` (instance) shape would fail validation for an omitted M2M
      while a PROVIDED list (decoded to ``to_field_name`` values) passes - an
      omitted-vs-provided inconsistency (spec-038 Decision 8 step 4). Only a
      form field that is a real forward M2M on the model is reconstructed this way;
      a non-model extra is left to ``model_to_dict`` (which ignores non-columns).

    Reconstruction reads the form's FULL declared field set (``get_form_fields``),
    NOT the (possibly narrowed) generated input: a ``Meta.fields`` / ``Meta.exclude``
    narrowing drops excluded model-backed fields from the GraphQL input, but the
    bound ``ModelForm`` still validates EVERY field it declares, so an excluded
    required field (e.g. a narrowed-away ``category``) must still be reconstructed
    from the located row. A file field's ``model_to_dict`` value
    is the stored relative path, not a re-bindable ``data=`` value, so file fields
    are excluded (``forms.ImageField`` subclasses ``forms.FileField``, so the one
    ``isinstance`` catches both). Net-new vs. ``036``: the model update does
    ``setattr`` on the located instance, not a bound-data reconstruction.
    """
    model = mutation_cls._mutation_meta.model
    form_fields = dict(mutation_cls.get_form_fields())
    m2m_field_names = {field.name for field in model._meta.many_to_many}
    fk_field_names = {
        field.name for field in model._meta.concrete_fields if getattr(field, "is_relation", False)
    }

    m2m_data: dict[str, Any] = {}
    relation_data: dict[str, Any] = {}
    scalar_names: list[str] = []
    for name, form_field in form_fields.items():
        if name in provided_data or isinstance(form_field, forms.FileField):
            continue
        if isinstance(form_field, forms.ModelMultipleChoiceField) and name in m2m_field_names:
            try:
                related_objs = getattr(instance, name).all()
                m2m_data[name] = [_to_form_key_value(obj, form_field) for obj in related_objs]
            except (AttributeError, ObjectDoesNotExist):
                pass
        elif (
            isinstance(form_field, forms.ModelChoiceField)
            and not isinstance(form_field, forms.ModelMultipleChoiceField)
            and form_field.to_field_name
            and name in fk_field_names
        ):
            try:
                related = getattr(instance, name, None)
            except (AttributeError, ObjectDoesNotExist):
                related = None
            if related is not None:
                relation_data[name] = _to_form_key_value(related, form_field)
            else:
                scalar_names.append(name)
        else:
            scalar_names.append(name)

    base = model_to_dict(instance, fields=scalar_names)
    return {
        **base,
        **m2m_data,
        **relation_data,
        **provided_data,
    }


def _form_errors_to_field_errors(form: Any) -> list[Any]:
    """Map a failed form's ``form.errors`` onto the ``FieldError`` envelope.

    Reuses the ``036`` ``validation_error_to_field_errors`` over a
    ``ValidationError(form.errors.as_data())``: ``as_data()`` yields the
    ``{field: [ValidationError, ...]}`` shape the mapper's ``error_dict`` branch
    consumes, so the form's ``NON_FIELD_ERRORS`` bucket keys to the ``"__all__"``
    sentinel byte-identically to a model ``full_clean()`` failure (Decision 8
    step 4). No parallel mapper.
    """
    from ..utils.errors import validation_error_to_field_errors

    return validation_error_to_field_errors(ValidationError(form.errors.as_data()))


def _modelform_decode_step(
    mutation_cls: type,
    data: Any,
    info: Any,
    *,
    instance: Any,
) -> tuple[dict[str, Any], dict[str, Any]] | list[Any]:
    """The form ``decode_step``: form-decode + (ModelForm update) partial reconstruction.

    Decodes the bound input into a FORM-field-keyed ``(provided_data,
    provided_files)`` (the ``038`` ``_decode_form_data`` contract: visibility on
    every relation branch), then - for update - reconstructs the full bound
    ``data=`` so a one-field change validates against the row's unchanged values.
    A plain form has no located instance, so reconstruction is skipped. Returns
    ``(form_data, provided_files)`` for the write step, or a ``list[FieldError]``
    on a decode failure (the shared skeleton maps it to the error envelope).
    """
    provided_data, provided_files, decode_error = _decode_form_data(mutation_cls, data, info)
    if decode_error is not None:
        return [decode_error]
    if instance is not None:
        form_data = _reconstruct_partial_data(mutation_cls, instance, provided_data)
    else:
        form_data = provided_data
    return form_data, provided_files


def _bound_form_or_field_errors(
    holder: Any,
    info: Any,
    decoded: tuple[dict[str, Any], dict[str, Any]],
    *,
    instance: Any,
) -> tuple[Any, list[Any] | None]:
    """Construct the bound form and run ``is_valid()`` once (both form flavors).

    Returns ``(form, None)`` on success or ``(None, errors)`` on a validation
    failure. The persist hook (``form.save`` vs ``perform_mutate``) stays at the
    caller so ModelForm can return ``form.instance`` while a plain ``Form`` has
    no instance slot.
    """
    form_data, provided_files = decoded
    form = holder.get_form(info, data=form_data, files=provided_files, instance=instance)
    if not form.is_valid():
        return None, _form_errors_to_field_errors(form)
    return form, None


def _modelform_write_step(
    mutation_cls: type,
    info: Any,
    instance: Any,
    decoded: tuple[dict[str, Any], dict[str, Any]],
) -> Any | list[Any]:
    """The ``ModelForm`` ``write_step``: ``get_form`` -> ``is_valid`` -> ``form.save``.

    Constructs the form via the overridable ``get_form`` hook over the decoded bound
    data, runs ``is_valid()`` once (a failure maps ``form.errors`` onto the envelope
    via the reused ``validation_error_to_field_errors``), then writes via
    ``form.save()`` wrapped by the reused ``save_or_field_errors`` ``IntegrityError``
    mapper. Returns the saved instance (the skeleton's ``refetch_optimized``
    re-fetches it by pk under the G2 plan) or a ``list[FieldError]`` on a validation
    / write failure.
    """
    form, errors = _bound_form_or_field_errors(
        mutation_cls(),
        info,
        decoded,
        instance=instance,
    )
    if errors is not None:
        return errors

    # The pinned-alias WRITE phase opens for exactly ``form.save()``: the form
    # construction + ``is_valid()`` above are database-read-only under the
    # pipeline's phased alias guard.
    with pipeline_write_phase():
        write_error = save_or_field_errors(form.save)
    if write_error is not None:
        return write_error
    return form.instance


def _plain_form_write_step(
    mutation_cls: type,
    info: Any,
    decoded: tuple[dict[str, Any], dict[str, Any]],
) -> Any | list[Any]:
    """The plain-form ``write_step``: ``get_form`` -> ``is_valid`` -> ``perform_mutate``.

    Same construct/validate helper as ModelForm; the persist hook is
    ``perform_mutate`` (default ``form.save()`` if present, else no-op). Returns
    a non-list sentinel on success so the skeleton's model-less tail builds
    ``{ ok: true }``.
    """
    holder = mutation_cls()
    form, errors = _bound_form_or_field_errors(
        holder,
        info,
        decoded,
        instance=None,
    )
    if errors is not None:
        return errors

    # ``perform_mutate`` is the only write window (mirrors ``form.save`` /
    # ``serializer.save`` / ``instance.delete`` on the other flavors).
    with pipeline_write_phase():
        write_error = save_or_field_errors(
            lambda: holder.perform_mutate(form, info),
        )
    if write_error is not None:
        return write_error
    return True


def _run_form_pipeline_sync(
    mutation_cls: type,
    info: Any,
    data: Any,
    id: Any,  # noqa: A002
) -> Any:
    """The form-flavor rider of ``run_write_pipeline_sync`` (both form bases).

    ONE skeleton call serves both bases - the ``transaction.atomic()`` boundary
    + the locate preamble + the authorize-before-decode security ordering + the
    payload tail are single-sited in the skeleton, and the two form flavors
    share the form ``decode_step`` (form decode + partial reconstruction)
    verbatim. The ONLY divergence is the ``write_step``, picked on
    ``mutation_cls._primary_type``:

    - the ``ModelForm`` flavor (a real primary type) runs ``get_form`` ->
      ``is_valid`` -> ``form.save`` and the skeleton's optimizer re-fetch tail;
    - the plain ``DjangoFormMutation`` (``_primary_type is None``) has no row to
      locate, no object slot, and no re-fetch - the skeleton skips the locate
      and builds the ``{ ok, errors }`` payload while this flavor's write step
      runs ``perform_mutate``.

    This is the single sync body the async path wraps in one
    ``sync_to_async(thread_sensitive=True)`` call.
    """
    if mutation_cls._primary_type is None:

        def write_step(_instance: Any, decoded: Any) -> Any:
            return _plain_form_write_step(mutation_cls, info, decoded)
    else:

        def write_step(instance: Any, decoded: Any) -> Any:
            return _modelform_write_step(mutation_cls, info, instance, decoded)

    return run_write_pipeline_sync(
        mutation_cls,
        info,
        data,
        id,
        decode_step=lambda instance: _modelform_decode_step(
            mutation_cls,
            data,
            info,
            instance=instance,
        ),
        write_step=write_step,
    )


# The form-flavor module entry points (spec-038 Decision 8), via the shared factory
# (spec-039 M1a - single-sourced with the model flavor). ``resolve_form_sync``
# normalizes the ``UNSET``-default kwargs to ``_run_form_pipeline_sync`` (the plain
# flavor never passes ``id``, so it defaults to ``UNSET`` and the plain body ignores
# it); ``resolve_form_async`` runs the same body through the shared
# ``run_pipeline_async`` boundary (one ``sync_to_async(thread_sensitive=True)`` call,
# so the ``transaction.atomic()`` + every ORM call run on one worker thread). Both
# form bases' ``resolve_sync`` / ``resolve_async`` seams delegate here by name.
resolve_form_sync, resolve_form_async = make_resolver_entries(_run_form_pipeline_sync)
