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

from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from strawberry import relay

from ..exceptions import ConfigurationError
from ..mutations.inputs import (
    CREATE,
    PARTIAL,
    relation_input_annotation,
)
from ..registry import register_subsystem_clear, registry
from ..scalars import Upload
from ..types.converters import convert_scalar, scalar_for_field
from ..types.relay import implements_relay_node
from ..utils.inputs import (
    build_strawberry_input_class,
    generated_input_type_name,
    guard_dropped_required,
    iter_input_field_collisions,
    make_input_namespace,
    optional_input_field,
    pascalize_token,
    resolve_effective_fields,
)
from ..utils.strings import graphql_camel_name
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

# The form-input namespace lifecycle trio, single-sited via
# ``utils/inputs.py::make_input_namespace`` (spec-039 P2.2 - the one-ledger shape
# the mutation, form, and serializer flavors share). ``_materialized_names`` is
# the ``name -> input_class`` ledger ``materialize_form_input_class`` writes;
# ``registry.clear()`` (wired in Slice 2) routes through
# ``clear_form_input_namespace`` to reset it - a namespace disjoint from
# ``mutations.inputs`` so the ``036`` ``<Model>Input`` and the form
# ``<FormClass>Input`` never share a module ``__dict__`` slot. The public
# ``materialize_*`` / ``clear_*`` names below stay thin wrappers so callers + tests
# address them unchanged.
_materialized_names, _materialize_input, _clear_input_namespace = make_input_namespace(
    INPUTS_MODULE_PATH,
    "DjangoFormMutation",
)


def materialize_form_input_class(name: str, input_cls: type) -> None:
    """Set ``input_cls`` as a real module global of ``forms.inputs`` under ``name``.

    Thin family wrapper over the ``make_input_namespace`` materializer (which
    delegates to ``utils/inputs.py::materialize_generated_input_class`` pinning
    the form-side module path, family label, and ledger). See that helper for the
    Strawberry ``LazyType.resolve_type`` contract, the ``(name, input_cls)``
    idempotency clause (re-materializing the same class under the same name is a
    no-op, so identical shapes dedupe), and the distinct-class collision raise (a
    second, DIFFERENT class under one name raises ``ConfigurationError`` - the
    spec-038 finalize-time collision raise, including two different form classes
    sharing a ``__name__``, which can never dedupe because they are distinct
    ``form_class`` identities).

    Defined here; called by Slice 2's phase-2.5 bind.
    """
    _materialize_input(name, input_cls)


def clear_form_input_namespace() -> None:
    """Reset the form-input ledger for a fresh build.

    Clears ``_materialized_names`` (via the ``make_input_namespace`` clear) so
    ``materialize_form_input_class`` re-emits on the next finalize. **Materialized
    class objects are intentionally left parked** in ``forms.inputs.__dict__`` per
    the shared parked-globals lifecycle (see
    ``mutations/inputs.py::clear_mutation_input_namespace``):
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
    _clear_input_namespace()


# Register the form input-namespace clear as a canonical PRE-BIND clear (spec-039
# P1.6): the ``finalize_django_types`` pre-bind reset AND ``TypeRegistry.clear()``
# both iterate ``registry.iter_subsystem_clears()`` and run each row via
# ``_clear_if_importable``, so this clear is single-sited as a static string row
# rather than hand-mirrored in both call sites. Registered at import time of this
# module (the module that owns the clear); idempotent by value under a reload.
register_subsystem_clear(INPUTS_MODULE_PATH, "clear_form_input_namespace")


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
    - each is normalized (bare-string / duplicate rejection);
    - a name in neither ``base_fields`` raises ``ConfigurationError`` naming the
      unknown field (a typo like ``fields = ("emial",)`` fails loud, never
      silently shrinks the input);
    - an empty effective set (``fields = ()``, an ``exclude`` dropping every
      field, or a form with no fields) raises ``ConfigurationError`` (the ``036``
      empty-input guard applied to ``base_fields``).

    Preserves ``base_fields`` declaration order for the non-narrowed and the
    ``exclude`` cases; honors the caller's order for ``fields``.

    The narrowing spine + the pinned error wording are single-sited in
    ``utils/inputs.py::resolve_effective_fields`` (spec-039 M4), shared with the
    serializer flavor; this thin wrapper supplies the form basis (``base_fields``)
    and the form-flavor message knobs (the old ``normalize_form_field_sequence``
    re-binding wrapper folds into the ``seq_flavor`` arg - spec-039 Mn3).
    """
    return resolve_effective_fields(
        get_form_fields(form_class),
        fields=fields,
        exclude=exclude,
        subject=f"DjangoFormMutation for {form_class.__name__}",
        seq_flavor="DjangoFormMutation / DjangoModelFormMutation",
        unknown_noun="unknown form field(s)",
        empty_message=(
            f"DjangoFormMutation input for {form_class.__name__} has no fields; "
            "Meta.fields / Meta.exclude narrowed the form field set to empty (or the "
            "form declares no fields). A form input must define at least one field."
        ),
    )


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

    The narrowed-shape suffix reuses ``utils/inputs.py::pascalize_token`` (the
    injective single-leading-capital token scheme, promoted from
    ``mutations/inputs.py`` - spec-039 Md5) so the bare concatenation of sorted
    field tokens is uniquely decomposable - two distinct field sets never collide on
    one generated name. The suffix rule + the full-vs-narrowed branching are
    single-sited in ``utils/inputs.py::generated_input_type_name`` (spec-039 M6).

    Identity is ``(form_class, operation_kind, frozenset(effective_field_names))``;
    ``operation_kind`` picks the ``Input`` / ``PartialInput`` suffix (a ``FORM``
    sentinel from a plain ``DjangoFormMutation`` falls under the ``Input``
    suffix - it is a create-shaped input).
    """
    token = "".join(pascalize_token(name) for name in sorted(effective_field_names))
    return generated_input_type_name(
        form_class.__name__,
        is_partial=operation_kind == PARTIAL,
        is_full_shape=frozenset(effective_field_names) == frozenset(full_field_names),
        token=token,
    )


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


def _model_less_relation_annotation(
    name: str,
    field: forms.Field,
    form_class: type[forms.BaseForm],
) -> tuple[str, Any]:
    """Map a column-LESS relation form field to its ``(python_attr, annotation)``.

    A plain ``Form`` ``ModelChoiceField`` / ``ModelMultipleChoiceField`` has no
    backing model column, so it cannot reach ``relation_input_annotation`` (which
    is ``models.Field``-keyed). Its related model is its ``queryset.model``; the
    id type follows the SAME Relay-``GlobalID``-vs-raw-pk rule as the model-backed
    path - ``relay.GlobalID`` when the related model's primary ``DjangoType`` is
    Relay-Node-shaped, else the related model's raw pk scalar. The ``<name>_id``
    (single) / ``list[<id>]`` (multi) ``036`` scheme is reused so the wire
    contract is uniform across the model-backed and model-less relation paths.

    A ``ModelChoiceField`` whose ``queryset`` is assigned in ``__init__`` (a valid
    Django idiom) has ``queryset is None`` in the uninstantiated ``base_fields``
    that schema-time discovery reads, so its related model cannot be resolved. That
    is a fail-loud ``ConfigurationError`` naming the form / field rather than a bare
    ``AttributeError`` on ``None.model``, keeping the package's fail-loud contract.
    """
    related_qs = field.queryset
    if related_qs is None:
        raise ConfigurationError(
            f"Form {form_class.__name__!r} field {name!r} is a "
            f"{type(field).__name__} whose queryset is None at class definition. "
            "Schema-time input generation reads base_fields WITHOUT instantiating the "
            "form, so a queryset assigned in __init__ is not visible and the relation "
            "id type cannot be resolved. Declare the field with a concrete queryset "
            "(e.g. ModelChoiceField(queryset=Model.objects.all())), or drop it from "
            "the generated input via Meta.fields / Meta.exclude.",
        )
    related_model = related_qs.model
    primary = registry.get(related_model)
    if primary is not None and implements_relay_node(primary):
        id_scalar: Any = relay.GlobalID
    else:
        id_scalar = scalar_for_field(related_model._meta.pk)
    if isinstance(field, forms.ModelMultipleChoiceField):
        return name, list[id_scalar]
    return f"{name}_id", id_scalar


def _simple_triple(name: str, annotation: Any, kind: str) -> tuple[str, str, Any, str]:
    """Return ``(input_attr, graphql_name, annotation, kind)`` for a NON-relation form field.

    The scalar / file arms of ``_field_triple_and_spec`` all share one shape: the
    input attr IS the form field's own name, and the wire name is its camelCase
    (only a relation remaps to ``<name>_id``). Single-sources that
    ``python_attr = name; graphql_name = graphql_camel_name(name)`` pair so it is
    spelled once rather than in every non-relation arm.
    """
    return name, graphql_camel_name(name), annotation, kind


def _field_triple_and_spec(
    name: str,
    field: forms.Field,
    column: Any,
    type_name: str,
    form_class: type[forms.BaseForm],
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
            python_attr, graphql_name, annotation, kind = _simple_triple(name, Upload, FILE)
        else:
            python_attr, graphql_name, annotation, kind = _simple_triple(
                name,
                convert_scalar(column, type_name, force_nullable=False),
                SCALAR,
            )
    else:
        # Column-less form field: the model-less ``convert_form_field`` table owns
        # the kind; relation / file annotations are finalized here.
        conversion = convert_form_field(field)
        if conversion.kind == FILE:
            python_attr, graphql_name, annotation, kind = _simple_triple(name, Upload, FILE)
        elif conversion.kind in (RELATION_SINGLE, RELATION_MULTI):
            python_attr, annotation = _model_less_relation_annotation(name, field, form_class)
            graphql_name = graphql_camel_name(python_attr)
            kind = conversion.kind
        else:
            python_attr, graphql_name, annotation, kind = _simple_triple(
                name,
                conversion.annotation,
                conversion.kind,
            )

    spec = FormInputFieldSpec(
        input_attr=python_attr,
        graphql_name=graphql_name,
        form_field_name=name,
        kind=kind,
    )
    return python_attr, annotation, spec


def _guard_input_attr_collisions(
    form_class: type[forms.BaseForm],
    field_specs: list[FormInputFieldSpec],
) -> None:
    """Raise if two form fields collide on the generated input attr OR GraphQL name.

    Two distinct ways two form fields collapse to one generated input field, both
    of which ``build_strawberry_input_class`` would resolve by SILENTLY dropping
    one - so both fail loud here (the package's fail-loud contract):

    * ``input_attr`` clash - a relation field ``foo`` remaps to input attr
      ``foo_id`` (the ``036`` scheme), so a form declaring BOTH a relation ``foo``
      AND a field literally named ``foo_id`` produces two specs with
      ``input_attr == "foo_id"``; the second overwrites the first in the
      annotations dict.
    * ``graphql_name`` clash - two distinct field names that default-camel-case to
      ONE GraphQL name (``foo_bar`` + ``fooBar`` -> ``fooBar``). The python attrs
      differ (so the input-attr check above passes), but Strawberry collapses the
      two onto one schema field. Mirrors the read-type guard in
      ``types/finalizer.py::_audit_field_surface``.

    The seen-dict walk + the two collision arms are single-sited in
    ``utils/inputs.py::iter_input_field_collisions`` (DRY review A3); the form
    flavor raises on the FIRST collision (the serializer aggregates instead),
    with byte-stable wording via the threaded form nouns.
    """
    for message in iter_input_field_collisions(
        field_specs,
        subject=f"Form {form_class.__name__!r}",
        field_noun="form fields",
        rename_clause="Rename one of the form fields,",
        name_of=lambda spec: spec.form_field_name,
    ):
        raise ConfigurationError(message)


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
        python_attr, annotation, spec = _field_triple_and_spec(
            name,
            field,
            column,
            type_name,
            form_class,
        )
        field_specs.append(spec)

        # Requiredness: the create input honors ``field.required``; the partial
        # input forces a model-backed field optional but a column-less extra
        # field keeps its declared ``field.required`` (P2). The widening tail
        # (``T | None`` + ``UNSET`` default + ``name=`` alias) is single-sited
        # in ``utils/inputs.py::optional_input_field`` (DRY review A10).
        required = False if (is_partial and column is not None) else field.required
        annotation, field_kwargs = optional_input_field(
            annotation,
            python_attr=python_attr,
            graphql_name=spec.graphql_name,
            widen=not required,
        )
        triples.append((python_attr, annotation, field_kwargs))

    _guard_input_attr_collisions(form_class, field_specs)
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

    The drop-detection (``required - effective - waived``) is single-sited in
    ``utils/inputs.py::guard_dropped_required`` (spec-039 Md1), shared with the
    serializer create guard; the form flavor passes no ``waived`` set (it has no
    injected-field mechanism) and keeps its own pinned error wording.
    """
    guard_dropped_required(
        _required_form_field_names(form_class),
        effective_field_names,
        make_error=lambda dropped: ConfigurationError(
            f"DjangoFormMutation create input for {form_class.__name__} drops required form "
            f"field(s) {dropped!r} via Meta.fields / Meta.exclude; a bound form can "
            "never validate without them. Keep them in the input, or override get_form_kwargs "
            "/ get_form to supply them (which waives this guard).",
        ),
    )


def guard_partial_required_column_less_fields(
    form_class: type[forms.BaseForm],
    effective_field_names: Any,
) -> None:
    """Raise if a partial (update) narrowing drops a required COLUMN-LESS form field (feedback #4).

    The partial counterpart to ``guard_create_required_fields``, but scoped to
    column-less fields ONLY. On update the input maps to ``PARTIAL``: a model-backed
    required field is widened optional and reconstructed from the located row by
    ``_reconstruct_partial_data`` (``model_to_dict`` of the row), so dropping it from
    the input via ``Meta.fields`` / ``Meta.exclude`` is harmless. But a required
    field with NO backing model column - a declarative extra like ``confirm =
    forms.CharField(required=True)`` - cannot be reconstructed from model state
    (``model_to_dict`` only returns columns), so if it is dropped the bound form
    fails its required validation on EVERY request while the schema still finalizes
    cleanly. Reject that at bind, naming the field(s).

    Scoping to ``_model_column_for(...) is None`` is load-bearing: a blanket reuse of
    ``guard_create_required_fields`` here would wrongly reject reconstructable
    model-backed required fields that the partial path legitimately drops. The
    ``get_form_kwargs`` / ``get_form`` waiver (``guard_required=False``) suppresses
    this the same way it suppresses the create guard.
    """
    dropped = sorted(
        name
        for name in _required_form_field_names(form_class)
        if name not in set(effective_field_names) and _model_column_for(form_class, name) is None
    )
    if dropped:
        raise ConfigurationError(
            f"DjangoModelFormMutation update input for {form_class.__name__} drops required "
            f"column-less form field(s) {dropped!r} via Meta.fields / Meta.exclude; they cannot "
            "be reconstructed from the row, so a bound form can never validate without them. Keep "
            "them in the input, or override get_form_kwargs / get_form to supply them (which "
            "waives this guard).",
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
