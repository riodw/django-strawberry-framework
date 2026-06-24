"""Form-derived ``@strawberry.input`` generation substrate (spec-038 Slice 1).

Pure, finalizer-free machinery: given a Django ``Form`` / ``ModelForm`` class +
an operation kind + the effective field set (after ``Meta.fields`` /
``Meta.exclude``), it builds the ``<FormClass>Input`` (create) /
``<FormClass>PartialInput`` (update) ``@strawberry.input`` classes from the
form's declared ``base_fields``. No metaclass, no resolver, no finalizer wiring
lives here - those are Slice 2 (the ``DjangoFormMutation`` /
``DjangoModelFormMutation`` bases + the phase-2.5 bind) and Slice 3 (the
resolver pipeline). The generators here are callable and unit-testable in
isolation; Slice 2 calls them from the bind.

Generated input classes MUST become real globals of this module because
``strawberry.lazy("django_strawberry_framework.forms.inputs")`` resolves through
``module.__dict__`` (the same contract ``mutations/inputs.py`` /
``orders/inputs.py`` rely on). ``materialize_form_input_class`` /
``clear_form_input_namespace`` own that lifecycle.

The shape is the ``036`` discipline adapted to forms (spec-038 Decision 7):

- The input derives from the **form's declared fields** (``form_class.base_fields``,
  the stable class-level set - read with NO instantiation, so a kwarg-requiring
  form still has a discoverable shape, P2), not the model's editable columns.
- Where a ``ModelForm`` field has a backing model column, the annotation routes
  through the read-side ``convert_scalar`` / ``convert_choices_to_enum`` /
  ``relation_input_annotation`` so the wire contract is symmetric with the read
  ``DjangoType``. A plain ``Form`` field with no column uses
  ``converter.convert_form_field`` (the model-less table). The two key spaces
  (``forms.Field`` / ``models.Field``) stay strictly separate: the column is
  resolved first, then handed to the ``models.Field``-keyed converters.
- Shape identity is ``(form_class, operation_kind, frozenset(effective field
  names))`` keyed on the FORM CLASS OBJECT (not its ``__name__``); the canonical
  ``<FormClass>Input`` / ``<FormClass>PartialInput`` name for the full shape and
  a deterministic shape-derived name for a narrowing. Identical shapes dedupe;
  two distinct shapes on one name raise ``ConfigurationError`` at finalization -
  for free from the ``utils/inputs.py`` materialize ledger.

The materialize / build / camel-name / token-name mechanics are single-sited in
``utils/inputs.py`` / ``mutations/inputs.py``; this module is a thin domain
wrapper, in the spirit of ``mutations/inputs.py``.
"""

from __future__ import annotations

from typing import Any

import strawberry
from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from strawberry import relay

from ..exceptions import ConfigurationError
from ..mutations.inputs import (
    CREATE,
    PARTIAL,
    _pascalize_token,
    relation_input_annotation,
)
from ..registry import registry
from ..scalars import Upload
from ..types.converters import convert_scalar, scalar_for_field
from ..types.relay import implements_relay_node
from ..utils.inputs import (
    build_strawberry_input_class,
    graphql_camel_name,
    materialize_generated_input_class,
    normalize_field_name_sequence,
)
from .converter import (
    FILE,
    RELATION_MULTI,
    RELATION_SINGLE,
    SCALAR,
    FormInputFieldSpec,
    convert_form_field,
)

# Module path the ``strawberry.lazy(...)`` marker references for the FORM input
# namespace; pinned as a single constant so any forward-ref and
# ``materialize_form_input_class`` stay in sync. A namespace distinct from
# ``mutations.inputs`` so the ``036`` ``<Model>Input`` and the form
# ``<FormClass>Input`` never share a module ``__dict__`` slot. Mirrors
# ``mutations/inputs.py::INPUTS_MODULE_PATH``.
INPUTS_MODULE_PATH: str = "django_strawberry_framework.forms.inputs"

# The fixed operation-kind sentinel for a plain ``DjangoFormMutation`` (no model
# operation). The ``036`` ``CREATE`` / ``PARTIAL`` constants (reused from
# ``mutations.inputs``) drive the create-vs-partial GENERATOR split; ``FORM`` is
# the shape-identity component a plain ``DjangoFormMutation`` carries in place of
# a ``"create"`` / ``"update"`` model operation, so a plain form's input cache
# key ``(form_class, "form", effective set)`` is well-defined (spec-038
# Decision 7 P2). Slice 2 keys the bind on it; this slice does not branch on it.
FORM: str = "form"

# The create-shaped operation kinds (everything that is NOT ``PARTIAL``): a
# ``DjangoModelFormMutation`` create (``CREATE``) and a plain
# ``DjangoFormMutation`` (``FORM``). The generator's only behavioral split is
# create-shaped vs ``PARTIAL`` (the latter widens model-backed fields to
# optional), so this names the create-shaped set in one place. ``CREATE`` /
# ``PARTIAL`` are re-exported from ``mutations.inputs`` so callers + tests
# address the form generator's full kind vocabulary on this module.
CREATE_SHAPED_KINDS: frozenset[str] = frozenset({CREATE, FORM})

# Ledger of materialized form-input class names. ``materialize_form_input_class``
# writes a ``name -> input_class`` entry; ``registry.clear()`` (wired in Slice 2)
# routes through ``clear_form_input_namespace`` to reset it. Mirrors
# ``mutations/inputs.py::_materialized_names`` but in a disjoint per-subsystem
# namespace.
_materialized_names: dict[str, type] = {}


def materialize_form_input_class(name: str, input_cls: type) -> None:
    """Set ``input_cls`` as a real module global of ``forms.inputs`` under ``name``.

    Thin family wrapper over ``utils/inputs.py::materialize_generated_input_class``
    pinning the form-side module path, family label, and ledger. See that helper
    for the Strawberry ``LazyType.resolve_type`` contract, the ``(name, input_cls)``
    idempotency clause (re-materializing the same class under the same name is a
    no-op, so identical shapes dedupe), and the distinct-class collision raise (a
    second, DIFFERENT class under one name raises ``ConfigurationError`` - the
    spec-038 finalize-time collision raise, including two different form classes
    sharing a ``__name__``, which can never dedupe because they are distinct
    ``form_class`` identities).

    Defined here; called by Slice 2's phase-2.5 bind.
    """
    materialize_generated_input_class(
        name,
        input_cls,
        module_path=INPUTS_MODULE_PATH,
        family_label="DjangoFormMutation",
        ledger=_materialized_names,
    )


def clear_form_input_namespace() -> None:
    """Reset the form-input ledger for a fresh build.

    Clears ``_materialized_names`` so ``materialize_form_input_class`` re-emits
    on the next finalize. **Materialized class objects are intentionally left
    parked** in ``forms.inputs.__dict__`` per the shared parked-globals
    lifecycle (see ``mutations/inputs.py::clear_mutation_input_namespace``):
    ``materialize_form_input_class`` overwrites the module global via ``setattr``
    on the next finalize, so a parked class is replaced in place once the rebuild
    runs. Stripping it via ``delattr`` would break any ``strawberry.lazy(...)``
    LazyType held by a consumer module whose autouse-reload fixture did NOT also
    reload the holder.

    Like ``clear_mutation_input_namespace`` (and unlike the set families' clear),
    this resets only the module-level ledger it owns - the form subsystem has no
    arguments-factory cache and no per-set ``_lifecycle`` binding state. Wired
    into ``registry.clear()`` in Slice 2 (spec-038).
    """
    _materialized_names.clear()


def get_form_fields(form_class: type[forms.BaseForm]) -> dict[str, forms.Field]:
    """Return the form's declared field dict from ``base_fields`` - NO instantiation.

    ``base_fields`` is the class-level declared-fields dict Django's
    ``DeclarativeFieldsMetaclass`` / ``ModelFormMetaclass`` populate at class
    creation (for a ``ModelForm`` it already includes the model-derived fields).
    Reading it needs no ``form_class()`` call, so a form whose ``__init__``
    requires constructor kwargs (``user``, ``request``, a tenant) still has a
    discoverable, request-independent stable field shape (spec-038 Decision 7
    P2 - the kwarg-requiring-form fix). Slice 2's overridable
    ``get_form_fields(cls)`` classmethod on the base delegates here for its
    default; this slice ships the module-level discovery function only.
    """
    return dict(form_class.base_fields)


def normalize_form_field_sequence(value: Any, *, label: str = "fields") -> tuple[str, ...] | None:
    """Return ``Meta.fields`` / ``Meta.exclude`` as a tuple of names, or ``None``.

    The form-flavor entry point: delegates to the shared
    ``utils/inputs.py::normalize_field_name_sequence`` (spec-038 integration pass,
    Finding I1 - the consolidation of this and ``mutations/sets.py::_normalize_field_sequence``
    once both sites existed and were accepted) with the form-mutation flavor label,
    so the bare-string and duplicate-name ``ConfigurationError`` messages stay
    byte-identical to the pre-consolidation form wording. The field-existence
    basis (a name not in ``form_class.base_fields``) is checked separately in
    ``resolve_effective_form_fields``.

    ``None`` means "unset". A bare string is rejected (it would iterate as
    characters); a duplicate name is rejected (it would collapse silently when
    the effective set is taken as a ``frozenset``). ``label`` names which key
    (``fields`` / ``exclude``) is at fault.
    """
    return normalize_field_name_sequence(
        value,
        label=label,
        flavor="DjangoFormMutation / DjangoModelFormMutation",
    )


def resolve_effective_form_fields(
    form_class: type[forms.BaseForm],
    *,
    fields: Any = None,
    exclude: Any = None,
) -> dict[str, forms.Field]:
    """Return the effective ``{name: forms.Field}`` dict after ``fields`` / ``exclude``.

    Normalizes + fail-loud validates the narrowing against the form's
    ``base_fields`` (spec-038 Decision 7 P3):

    - ``fields`` and ``exclude`` are mutually exclusive;
    - each is normalized (bare-string / duplicate rejection) via
      ``normalize_form_field_sequence``;
    - a name in neither ``base_fields`` raises ``ConfigurationError`` naming the
      unknown field (a typo like ``fields = ("emial",)`` fails loud, never
      silently shrinks the input);
    - an empty effective set (``fields = ()``, an ``exclude`` dropping every
      field, or a form with no fields) raises ``ConfigurationError`` (the ``036``
      empty-input guard applied to ``base_fields``).

    Preserves ``base_fields`` declaration order for the non-narrowed and the
    ``exclude`` cases; honors the caller's order for ``fields``.
    """
    fields = normalize_form_field_sequence(fields, label="fields")
    exclude = normalize_form_field_sequence(exclude, label="exclude")
    if fields is not None and exclude is not None:
        raise ConfigurationError(
            f"DjangoFormMutation for {form_class.__name__} declares both `fields` and `exclude`; "
            "supply at most one.",
        )

    base = get_form_fields(form_class)
    if fields is not None:
        unknown = [name for name in fields if name not in base]
        if unknown:
            raise ConfigurationError(
                f"DjangoFormMutation for {form_class.__name__} declares `fields` naming "
                f"unknown form field(s): {sorted(unknown)!r}.",
            )
        effective = {name: base[name] for name in fields}
    elif exclude is not None:
        unknown = [name for name in exclude if name not in base]
        if unknown:
            raise ConfigurationError(
                f"DjangoFormMutation for {form_class.__name__} declares `exclude` naming "
                f"unknown form field(s): {sorted(unknown)!r}.",
            )
        excluded = set(exclude)
        effective = {name: field for name, field in base.items() if name not in excluded}
    else:
        effective = dict(base)

    if not effective:
        raise ConfigurationError(
            f"DjangoFormMutation input for {form_class.__name__} has no fields; "
            "Meta.fields / Meta.exclude narrowed the form field set to empty (or the "
            "form declares no fields). A form input must define at least one field.",
        )
    return effective


def form_input_type_name(
    form_class: type[forms.BaseForm],
    operation_kind: str,
    effective_field_names: tuple[str, ...],
    *,
    full_field_names: tuple[str, ...],
) -> str:
    """Return the generated input-class name for a form shape (spec-038 Decision 7 P1).

    The canonical full shape takes the stable ``<FormClass>Input`` /
    ``<FormClass>PartialInput`` name; a narrowed shape (``Meta.fields`` /
    ``Meta.exclude``) takes a deterministic shape-derived name so two NARROWINGS
    to the same effective set produce the same name (dedupe via the materialize
    ledger) while a different shape produces a different name.

    The narrowed-shape suffix reuses ``mutations/inputs.py::_pascalize_token``
    (the injective single-leading-capital token scheme) so the bare
    concatenation of sorted field tokens is uniquely decomposable - two distinct
    field sets never collide on one generated name. Reused rather than re-spelt
    (the token scheme is subtle + injectivity-critical); the consolidation of the
    token primitive into ``utils/inputs.py`` is flagged for the integration pass.

    Identity is ``(form_class, operation_kind, frozenset(effective_field_names))``;
    ``operation_kind`` picks the ``Input`` / ``PartialInput`` suffix (a ``FORM``
    sentinel from a plain ``DjangoFormMutation`` falls under the ``Input``
    suffix - it is a create-shaped input).
    """
    base = form_class.__name__
    suffix = "PartialInput" if operation_kind == PARTIAL else "Input"
    if frozenset(effective_field_names) == frozenset(full_field_names):
        return f"{base}{suffix}"
    token = "".join(_pascalize_token(name) for name in sorted(effective_field_names))
    return f"{base}{token}{suffix}"


def _model_column_for(form_class: type[forms.BaseForm], name: str) -> Any:
    """Return the backing model column for a ``ModelForm`` field ``name``, or ``None``.

    A ``ModelForm`` exposes its model via ``_meta.model``; a field with a backing
    concrete column resolves through ``model._meta.get_field(name)``. A plain
    ``Form`` (no ``_meta.model``), or a ``ModelForm`` extra field that declares no
    model column (a ``confirm``, a captcha), yields ``None`` - the caller routes
    it through the model-less ``convert_form_field`` table instead. The two key
    spaces stay separate: only a resolved ``models.Field`` ever reaches the
    read-side converters (spec-038 Decision 7).
    """
    meta = getattr(form_class, "_meta", None)
    model = getattr(meta, "model", None)
    if model is None:
        return None
    try:
        return model._meta.get_field(name)
    except FieldDoesNotExist:
        return None


def _model_less_relation_annotation(name: str, field: forms.Field) -> tuple[str, Any]:
    """Map a column-LESS relation form field to its ``(python_attr, annotation)``.

    A plain ``Form`` ``ModelChoiceField`` / ``ModelMultipleChoiceField`` has no
    backing model column, so it cannot reach ``relation_input_annotation`` (which
    is ``models.Field``-keyed). Its related model is its ``queryset.model``; the
    id type follows the SAME Relay-``GlobalID``-vs-raw-pk rule as the model-backed
    path - ``relay.GlobalID`` when the related model's primary ``DjangoType`` is
    Relay-Node-shaped, else the related model's raw pk scalar. The ``<name>_id``
    (single) / ``list[<id>]`` (multi) ``036`` scheme is reused so the wire
    contract is uniform across the model-backed and model-less relation paths.
    """
    related_model = field.queryset.model
    primary = registry.get(related_model)
    if primary is not None and implements_relay_node(primary):
        id_scalar: Any = relay.GlobalID
    else:
        id_scalar = scalar_for_field(related_model._meta.pk)
    if isinstance(field, forms.ModelMultipleChoiceField):
        return name, list[id_scalar]
    return f"{name}_id", id_scalar


def _field_triple_and_spec(
    name: str,
    field: forms.Field,
    column: Any,
    type_name: str,
) -> tuple[str, Any, FormInputFieldSpec]:
    """Resolve one form field to its ``(python_attr, base_annotation, FormInputFieldSpec)``.

    A ``ModelForm`` field with a backing column routes through the read-side
    converters (keyed on the resolved ``models.Field``): a relation column ->
    ``relation_input_annotation`` (``<name>_id`` / ``categoryId`` + the
    Relay-vs-raw-pk id type, ``relation_single`` / ``relation_multi``); a
    file/image column -> ``Upload`` (``file``); else ``convert_scalar`` (the
    symmetric enum for ``choices``, ``scalar``). A column-less field (a plain
    ``Form`` field or a ``ModelForm`` extra field) uses
    ``converter.convert_form_field`` (the model-less table) for the kind, and the
    relation / file annotations are finalized here (where ``Upload`` and the
    model-less relation id-type are known).

    Returns the BASE (non-optional) annotation; the create/partial requiredness
    widening is applied by the caller. The returned ``FormInputFieldSpec`` records
    the reverse map the Slice 3 resolver consults - ``form_field_name`` is always
    the form's declared name, never the ``<name>_id`` relation attr, because a
    bound Django form is keyed by form-field name.
    """
    if column is not None:
        # ModelForm field with a backing model column: route the ``models.Field``
        # through the read-side converters so the wire contract is symmetric with
        # the read ``DjangoType``.
        if getattr(column, "is_relation", False):
            python_attr, graphql_name, annotation = relation_input_annotation(
                column,
                related_primary_type=registry.get(column.related_model),
            )
            kind = RELATION_MULTI if getattr(column, "many_to_many", False) else RELATION_SINGLE
        elif isinstance(column, (models.FileField, models.ImageField)):
            python_attr = name
            graphql_name = graphql_camel_name(python_attr)
            annotation = Upload
            kind = FILE
        else:
            python_attr = name
            graphql_name = graphql_camel_name(python_attr)
            annotation = convert_scalar(column, type_name, force_nullable=False)
            kind = SCALAR
    else:
        # Column-less form field: the model-less ``convert_form_field`` table owns
        # the kind; relation / file annotations are finalized here.
        conversion = convert_form_field(field)
        kind = conversion.kind
        if kind == FILE:
            python_attr = name
            graphql_name = graphql_camel_name(python_attr)
            annotation = Upload
        elif kind in (RELATION_SINGLE, RELATION_MULTI):
            python_attr, annotation = _model_less_relation_annotation(name, field)
            graphql_name = graphql_camel_name(python_attr)
        else:
            python_attr = name
            graphql_name = graphql_camel_name(python_attr)
            annotation = conversion.annotation

    spec = FormInputFieldSpec(
        input_attr=python_attr,
        graphql_name=graphql_name,
        form_field_name=name,
        kind=kind,
    )
    return python_attr, annotation, spec


def build_form_input_class(
    form_class: type[forms.BaseForm],
    *,
    operation_kind: str,
    fields: Any = None,
    exclude: Any = None,
) -> tuple[type, list[FormInputFieldSpec]]:
    """Build ONE ``@strawberry.input`` class from a form's declared fields.

    ``operation_kind`` is ``CREATE`` / ``FORM`` (the create-shaped input - each
    field's requiredness from ``field.required``, graphene-django parity) or
    ``PARTIAL`` (the update-shaped input). In the partial input, model-backed
    fields are forced optional (Slice 3's reconstruction supplies them from the
    located row), but a **non-model extra field keeps its declared
    ``field.required``** (spec-038 Decision 7 P2 - so a required ``confirm`` stays
    required on update). Optional fields widen ``annotation | None`` + a
    ``strawberry.UNSET`` default, the ``036`` shape.

    Returns ``(input_cls, field_specs)`` - the UNMATERIALIZED
    ``@strawberry.input`` class and the per-field reverse-map records. Slice 2's
    phase-2.5 bind calls ``materialize_form_input_class`` to pin the class as a
    module global.
    """
    effective = resolve_effective_form_fields(form_class, fields=fields, exclude=exclude)
    full_field_names = tuple(get_form_fields(form_class))
    type_name = form_input_type_name(
        form_class,
        operation_kind,
        tuple(effective),
        full_field_names=full_field_names,
    )
    is_partial = operation_kind == PARTIAL

    triples: list[tuple[str, Any, dict[str, Any]]] = []
    field_specs: list[FormInputFieldSpec] = []
    for name, field in effective.items():
        column = _model_column_for(form_class, name)
        python_attr, annotation, spec = _field_triple_and_spec(name, field, column, type_name)
        field_specs.append(spec)

        # Requiredness: the create input honors ``field.required``; the partial
        # input forces a model-backed field optional but a column-less extra
        # field keeps its declared ``field.required`` (P2).
        required = False if (is_partial and column is not None) else field.required

        field_kwargs: dict[str, Any] = {}
        if python_attr != spec.graphql_name:
            field_kwargs["name"] = spec.graphql_name
        if not required:
            annotation = annotation | None
            field_kwargs["default"] = strawberry.UNSET
        triples.append((python_attr, annotation, field_kwargs))

    input_cls = build_strawberry_input_class(type_name, triples)
    return input_cls, field_specs


def _required_form_field_names(form_class: type[forms.BaseForm]) -> set[str]:
    """Return the names of every declared form field whose ``field.required`` is True."""
    return {name for name, field in get_form_fields(form_class).items() if field.required}


def guard_create_required_fields(
    form_class: type[forms.BaseForm],
    effective_field_names: Any,
) -> None:
    """Raise if a create-shaped narrowing drops a still-declared required form field (P2).

    A bound form fails required-validation for any ``field.required`` field absent
    from its bound ``data=``, so a create whose effective field set (after
    ``Meta.fields`` / ``Meta.exclude``) omits a still-declared required form field
    would compile to a schema that looks valid but can never succeed. This raises
    ``ConfigurationError`` naming the dropped required field(s), covering both
    ``Meta.fields`` and ``Meta.exclude``.

    Factored out of ``build_form_inputs`` so the bind's per-shape build cache
    (``forms/sets.py::_cached_build_form_input``) can run it PER mutation
    DECLARATION rather than only on the first build of a given shape: the cache key
    excludes ``guard_required``, so a waiving mutation (``guard_required=False``,
    having overridden ``get_form_kwargs`` / ``get_form``) that materializes a
    narrowed shape FIRST must not suppress the guard for a later non-waiving
    mutation reusing the same cached shape. The guard is tied to the declaration,
    not the built input shape (spec-038 Decision 7 P2, the create-required guard).
    """
    dropped_required = sorted(_required_form_field_names(form_class) - set(effective_field_names))
    if dropped_required:
        raise ConfigurationError(
            f"DjangoFormMutation create input for {form_class.__name__} drops required form "
            f"field(s) {dropped_required!r} via Meta.fields / Meta.exclude; a bound form can "
            "never validate without them. Keep them in the input, or override get_form_kwargs "
            "/ get_form to supply them (which waives this guard).",
        )


def build_form_inputs(
    form_class: type[forms.BaseForm],
    *,
    operation_kind: str = FORM,
    fields: Any = None,
    exclude: Any = None,
    guard_required: bool = True,
) -> tuple[type, list[FormInputFieldSpec], type, list[FormInputFieldSpec]]:
    """Build BOTH the create + partial inputs for a form, with the create-required guard.

    Single entry point producing ``(<FormClass>Input, create_specs,
    <FormClass>PartialInput, partial_specs)``. The create input's
    ``operation_kind`` is the caller's (``CREATE`` for a ``DjangoModelFormMutation``
    create, or the ``FORM`` sentinel for a plain ``DjangoFormMutation``); the
    partial input is always ``PARTIAL``.

    **The create-required-narrowing guard (spec-038 Decision 7 P2).** A bound
    form fails required-validation for any ``field.required`` field absent from
    its bound ``data=``, so a create whose effective field set (after
    ``Meta.fields`` / ``Meta.exclude``) omits a still-declared required form field
    would compile to a schema that looks valid but can never succeed. When
    ``guard_required`` is True this raises ``ConfigurationError`` naming the
    dropped required field(s), covering both ``Meta.fields`` and ``Meta.exclude``.
    The waiver (``guard_required=False``) is the ``get_form_kwargs`` /
    ``get_form`` override escape hatch (Slice 2/3): when the consumer overrides
    that hook the guard cannot know which fields the override injects, so it
    trusts the explicit override - surfaced here as an explicit parameter so
    Slice 2 can pass ``guard_required=False``, never hard-coded always-on.
    """
    effective = resolve_effective_form_fields(form_class, fields=fields, exclude=exclude)
    if guard_required:
        guard_create_required_fields(form_class, effective)

    create_cls, create_specs = build_form_input_class(
        form_class,
        operation_kind=operation_kind,
        fields=fields,
        exclude=exclude,
    )
    partial_cls, partial_specs = build_form_input_class(
        form_class,
        operation_kind=PARTIAL,
        fields=fields,
        exclude=exclude,
    )
    return create_cls, create_specs, partial_cls, partial_specs
