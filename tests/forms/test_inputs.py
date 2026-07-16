"""Form-derived input tests for the generated ``<FormClass>Input`` / ``PartialInput`` (spec-038).

Covers ``django_strawberry_framework/forms/inputs.py`` (Slice 1 generation
substrate):

- ``get_form_fields`` discovery from ``base_fields`` with NO instantiation (incl.
  a kwarg-requiring form);
- the two generated inputs: ``<FormClass>Input`` (create; requiredness from
  ``field.required``) and ``<FormClass>PartialInput`` (model-backed optional, a
  non-model extra field still required);
- the ``ModelChoiceField`` / ``ModelMultipleChoiceField`` id mapping (Relay-``GlobalID``
  vs raw pk by the target's primary ``DjangoType``, single + multi), the
  ``FileField`` -> ``Upload`` mapping, and the reverse map (``category`` ->
  ``category_id`` / ``categoryId`` / ``relation_single``);
- the ``ChoiceField``-over-model-``choices`` symmetric-enum reuse (proves the
  overlap routes through the read converter, not a parallel table);
- ``Meta.fields`` / ``Meta.exclude`` narrowing + fail-loud, the empty-effective-set
  raise, and the create-required-narrowing guard + its waiver;
- shape-identity dedupe + the distinct-shape / same-``__name__`` collision raise
  via ``materialize_form_input_class``, and module-global materialization.

System-under-test is the generator run against the products ``Item`` / ``Category``
FK fixtures plus package-local fixture models / forms for the M2M, Relay-target,
choices-enum, ``Upload``, and plain-``Form``-only shapes products does not carry
(the spec-038 Slice 1 test plan; products is non-Relay and has no M2M / file /
choices column). Mirrors the ``tests/mutations/test_inputs.py`` fixture posture.
"""

from __future__ import annotations

import itertools
import sys

import pytest
import strawberry
from apps.products import models as product_models
from django import forms
from django.db import models
from strawberry import UNSET, relay
from strawberry.types.base import StrawberryOptional

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.forms.converter import (
    FILE,
    RELATION_MULTI,
    RELATION_SINGLE,
    SCALAR,
)
from django_strawberry_framework.forms.inputs import (
    CREATE,
    FORM,
    INPUTS_MODULE_PATH,
    PARTIAL,
    build_form_input_class,
    build_form_inputs,
    clear_form_input_namespace,
    form_input_type_name,
    get_form_fields,
    guard_partial_required_column_less_fields,
    materialize_form_input_class,
    resolve_effective_form_fields,
)
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry_and_ledger():
    """Reset registry + the form-input ledger so each test starts clean.

    Slice 1 does not wire ``clear_form_input_namespace`` into ``registry.clear()``
    (that is Slice 2), so the ledger is cleared explicitly. ``registry.clear()``
    is still needed because the products ``DjangoType``s and local fixtures
    register themselves on import / declaration.
    """
    registry.clear()
    clear_form_input_namespace()
    yield
    registry.clear()
    clear_form_input_namespace()


_app_label_counter = itertools.count(1)


def _unique_app_label() -> str:
    """Return a unique ``app_label`` per call to avoid Django's re-register warning."""
    return f"test_form_inputs__{next(_app_label_counter)}"


def _field_map(input_cls: type) -> dict[str, object]:
    """Return ``python_name -> StrawberryField`` for a built input class."""
    return {f.python_name: f for f in input_cls.__strawberry_definition__.fields}


def _is_optional(field) -> bool:
    """Return whether a Strawberry field's annotation is ``T | None``."""
    return isinstance(field.type, StrawberryOptional)


def _inner_type(field):
    """Return the inner type of a ``StrawberryOptional`` field, else the type itself."""
    return field.type.of_type if isinstance(field.type, StrawberryOptional) else field.type


def _make_relay_target():
    """A registered Relay-Node-shaped ``DjangoType`` over a fresh model."""

    class RelayTarget(models.Model):
        name = models.TextField()

        class Meta:
            app_label = _unique_app_label()

    class RelayTargetType(DjangoType, relay.Node):
        class Meta:
            model = RelayTarget
            fields = ("id", "name")

    return RelayTarget, RelayTargetType


def _make_non_relay_target():
    """A registered non-Relay ``DjangoType`` over a fresh model (raw int pk)."""

    class PlainTarget(models.Model):
        name = models.TextField()

        class Meta:
            app_label = _unique_app_label()

    class PlainTargetType(DjangoType):
        class Meta:
            model = PlainTarget
            fields = ("id", "name")

    return PlainTarget, PlainTargetType


# ---------------------------------------------------------------------------
# Module-path constant
# ---------------------------------------------------------------------------


def test_inputs_module_path_constant():
    """The hoisted constant matches the actual dotted path of ``forms/inputs.py``."""
    assert INPUTS_MODULE_PATH == "django_strawberry_framework.forms.inputs"


# ---------------------------------------------------------------------------
# get_form_fields - discovery from base_fields, NO instantiation
# ---------------------------------------------------------------------------


def test_get_form_fields_reads_base_fields():
    """Discovery returns the form's declared field dict in declaration order."""

    class SimpleForm(forms.Form):
        name = forms.CharField()
        age = forms.IntegerField()

    discovered = get_form_fields(SimpleForm)
    assert list(discovered) == ["name", "age"]
    assert isinstance(discovered["name"], forms.CharField)


def test_get_form_fields_does_not_instantiate_kwarg_requiring_form():
    """A form whose ``__init__`` requires a kwarg still yields a shape via ``base_fields``.

    Reading ``base_fields`` (the class-level declared-fields dict) needs no
    ``KwargForm()`` call, so a migrated form requiring ``user`` / ``request`` /
    a tenant still has a discoverable, request-independent stable shape (P2).
    """

    class KwargForm(forms.Form):
        email = forms.EmailField()

        def __init__(self, *args, user, **kwargs):
            # No-arg instantiation would raise TypeError (missing ``user``); the
            # discovery never instantiates, so the shape is still readable.
            super().__init__(*args, **kwargs)
            self.user = user

    discovered = get_form_fields(KwargForm)
    assert list(discovered) == ["email"]
    with pytest.raises(TypeError):
        KwargForm()  # proves the form genuinely cannot be instantiated no-arg


# ---------------------------------------------------------------------------
# The two generated inputs - create + partial requiredness
# ---------------------------------------------------------------------------


def _item_model_form():
    """A ``ModelForm`` over products ``Item`` with a non-model required ``confirm`` extra."""

    class ItemModelForm(forms.ModelForm):
        confirm = forms.BooleanField(required=True)

        class Meta:
            model = product_models.Item
            fields = ("name", "category", "is_private")

    return ItemModelForm


def test_create_input_required_and_optional_shapes():
    """``<FormClass>Input``: required fields non-optional, optional fields ``| None`` + UNSET."""
    cre, _, _, _ = build_form_inputs(_item_model_form(), operation_kind=CREATE)
    assert cre.__name__ == "ItemModelFormInput"
    fields = _field_map(cre)

    # ``name`` (required TextField) is non-optional.
    assert not _is_optional(fields["name"])
    assert _inner_type(fields["name"]) is str

    # The FK ``category`` -> ``category_id`` / ``categoryId``, required.
    assert not _is_optional(fields["category_id"])
    assert fields["category_id"].graphql_name == "categoryId"

    # The non-model required ``confirm`` is required in create.
    assert not _is_optional(fields["confirm"])

    # ``is_private`` (BooleanField, not required) is optional + UNSET.
    assert _is_optional(fields["is_private"])
    assert fields["is_private"].default is UNSET


def test_partial_input_model_backed_optional_extra_field_still_required():
    """``<FormClass>PartialInput``: model-backed fields optional, a required extra stays required."""
    _, _, par, _ = build_form_inputs(_item_model_form(), operation_kind=CREATE)
    assert par.__name__ == "ItemModelFormPartialInput"
    fields = _field_map(par)

    # Model-backed fields are forced optional + UNSET in the partial input.
    for name in ("name", "category_id", "is_private"):
        assert _is_optional(fields[name]), name
        assert fields[name].default is UNSET, name

    # The non-model required ``confirm`` keeps its declared ``field.required``
    # (P2 - the load-bearing partial assertion).
    assert not _is_optional(fields["confirm"])


def test_plain_form_only_field_included_in_input():
    """A plain ``Form`` field (no model column) appears in the input (derives from the form)."""

    class ContactForm(forms.Form):
        name = forms.CharField()
        captcha = forms.CharField(required=False)

    cre, _, _, _ = build_form_inputs(ContactForm, operation_kind=FORM)
    fields = _field_map(cre)
    assert set(fields) == {"name", "captcha"}
    assert not _is_optional(fields["name"])
    assert _is_optional(fields["captcha"])


def test_null_boolean_field_is_optional_even_when_django_required():
    """Default ``NullBooleanField(required=True)`` is still optional + UNSET in the input.

    Converter forces ``required=False`` (Django validate is a no-op; GraphQL cannot
    express required-nullable). The build site must honor ``conversion.required``
    so omitting the field does not TypeError after GraphQL validation allows it.
    """

    class FlagForm(forms.Form):
        flag = forms.NullBooleanField()  # Django default required=True
        name = forms.CharField()

    cre, _, _, _ = build_form_inputs(FlagForm, operation_kind=FORM)
    fields = _field_map(cre)
    assert _is_optional(fields["flag"])
    assert fields["flag"].default is UNSET
    assert not _is_optional(fields["name"])


def test_non_null_column_backed_null_boolean_stays_required():
    """Model validation makes a required NullBooleanField over ``null=False`` non-null."""

    class Flags(models.Model):
        flag = models.BooleanField(null=False)
        name = models.CharField(max_length=20)

        class Meta:
            app_label = _unique_app_label()

    class FlagsForm(forms.ModelForm):
        flag = forms.NullBooleanField(required=True)

        class Meta:
            model = Flags
            fields = ("flag", "name")

    cre, _, _, _ = build_form_inputs(FlagsForm, operation_kind=CREATE)
    fields = _field_map(cre)
    assert not _is_optional(fields["flag"])
    with pytest.raises(ConfigurationError, match=r"drops required form field.*flag"):
        build_form_inputs(
            FlagsForm,
            operation_kind=CREATE,
            fields=("name",),
        )


def test_column_backed_null_boolean_is_optional():
    """A ``NullBooleanField`` backed by a nullable model column is optional too.

    The requiredness rule must apply on EVERY conversion path, not just the
    model-less one: a ``ModelForm`` field whose backing column resolves still
    routes through the shared ``form_field_required`` helper, so a Django
    ``required=True`` ``NullBooleanField`` over a column widens to ``| None`` +
    ``UNSET`` rather than compiling a required field (the pre-fix column-backed
    path used raw ``field.required`` and emitted it required).
    """

    class Flags(models.Model):
        flag = models.BooleanField(null=True)

        class Meta:
            app_label = _unique_app_label()

    class FlagsForm(forms.ModelForm):
        flag = forms.NullBooleanField()  # Django default required=True

        class Meta:
            model = Flags
            fields = ("flag",)

    cre, _, _, _ = build_form_inputs(FlagsForm, operation_kind=CREATE)
    fields = _field_map(cre)
    assert _is_optional(fields["flag"])
    assert fields["flag"].default is UNSET


def test_create_guard_ignores_django_required_null_boolean():
    """A Django-``required=True`` ``NullBooleanField`` is not create-required.

    Narrowing it out of the input must NOT trip the create-required guard - the
    field is optional in the schema and a bound form validates without it.
    """

    class FlagForm(forms.Form):
        flag = forms.NullBooleanField()  # Django default required=True
        name = forms.CharField()

    cre, _, _, _ = build_form_inputs(FlagForm, operation_kind=FORM, fields=("name",))
    assert set(_field_map(cre)) == {"name"}


def test_json_field_maps_to_json_scalar_in_input():
    """A plain ``Form`` ``JSONField`` maps to ``strawberry.scalars.JSON``, not ``str``."""

    class PayloadForm(forms.Form):
        payload = forms.JSONField()

    cre, specs, _, _ = build_form_inputs(PayloadForm, operation_kind=FORM)
    fields = _field_map(cre)
    assert _inner_type(fields["payload"]) is strawberry.scalars.JSON
    assert next(s for s in specs if s.form_field_name == "payload").kind == SCALAR


# ---------------------------------------------------------------------------
# Relation id mapping - Relay vs raw pk, single + multi
# ---------------------------------------------------------------------------


def test_fk_to_non_relay_products_target_uses_raw_pk_id():
    """The products ``Item.category`` FK (non-Relay ``CategoryType``) becomes a raw pk id."""
    cre, specs, _, _ = build_form_inputs(_item_model_form(), operation_kind=CREATE)
    fields = _field_map(cre)
    # CategoryType is non-Relay, so the id is the raw pk scalar (int), not GlobalID.
    assert _inner_type(fields["category_id"]) is int
    # Reverse map: input attr -> form field name + kind.
    cat_spec = next(s for s in specs if s.form_field_name == "category")
    assert cat_spec.input_attr == "category_id"
    assert cat_spec.graphql_name == "categoryId"
    assert cat_spec.kind == RELATION_SINGLE


def test_model_choice_field_to_relay_target_uses_globalid():
    """A model-less ``ModelChoiceField`` to a Relay primary becomes ``<name>_id: GlobalID``."""
    relay_target, _ = _make_relay_target()

    class PickForm(forms.Form):
        target = forms.ModelChoiceField(queryset=relay_target.objects.all())

    cre, specs, _, _ = build_form_inputs(PickForm, operation_kind=FORM)
    fields = _field_map(cre)
    assert _inner_type(fields["target_id"]) is relay.GlobalID
    spec = next(s for s in specs if s.form_field_name == "target")
    assert spec.input_attr == "target_id"
    assert spec.kind == RELATION_SINGLE


def test_model_choice_field_to_non_relay_target_uses_raw_pk():
    """A model-less ``ModelChoiceField`` to a non-Relay primary becomes a raw pk id."""
    plain_target, _ = _make_non_relay_target()

    class PickForm(forms.Form):
        target = forms.ModelChoiceField(queryset=plain_target.objects.all())

    cre, _, _, _ = build_form_inputs(PickForm, operation_kind=FORM)
    fields = _field_map(cre)
    assert _inner_type(fields["target_id"]) is int


def test_model_multiple_choice_field_to_relay_target_is_list_of_globalid():
    """A ``ModelMultipleChoiceField`` to a Relay primary becomes ``list[GlobalID]``, kind multi."""
    relay_target, _ = _make_relay_target()

    class PickManyForm(forms.Form):
        targets = forms.ModelMultipleChoiceField(queryset=relay_target.objects.all())

    cre, specs, _, _ = build_form_inputs(PickManyForm, operation_kind=FORM)
    fields = _field_map(cre)
    inner = _inner_type(fields["targets"])
    assert inner == list[relay.GlobalID]
    spec = next(s for s in specs if s.form_field_name == "targets")
    assert spec.input_attr == "targets"
    assert spec.kind == RELATION_MULTI


def test_model_multiple_choice_field_to_non_relay_target_is_list_of_raw_pk():
    """A ``ModelMultipleChoiceField`` to a non-Relay primary becomes ``list[<raw pk>]``."""
    plain_target, _ = _make_non_relay_target()

    class PickManyForm(forms.Form):
        targets = forms.ModelMultipleChoiceField(queryset=plain_target.objects.all())

    cre, _, _, _ = build_form_inputs(PickManyForm, operation_kind=FORM)
    fields = _field_map(cre)
    assert _inner_type(fields["targets"]) == list[int]


# ---------------------------------------------------------------------------
# FileField -> Upload, kind file
# ---------------------------------------------------------------------------


def test_file_field_maps_to_upload():
    """A plain ``Form`` ``FileField`` maps to ``Upload`` with kind ``file``."""
    from django_strawberry_framework.scalars import Upload

    class AvatarForm(forms.Form):
        avatar = forms.FileField()

    cre, specs, _, _ = build_form_inputs(AvatarForm, operation_kind=FORM)
    fields = _field_map(cre)
    assert _inner_type(fields["avatar"]) is Upload
    spec = next(s for s in specs if s.form_field_name == "avatar")
    assert spec.kind == FILE


# ---------------------------------------------------------------------------
# ChoiceField over a ModelForm model's choices -> the SAME read-side enum
# ---------------------------------------------------------------------------


def test_choices_modelform_field_resolves_to_read_side_enum():
    """A ``ModelForm`` field over a model ``choices`` column reuses the read converter's enum.

    Proves the model-backed overlap routes through ``convert_scalar`` /
    ``convert_choices_to_enum`` (the symmetric wire contract), not a parallel
    form-field table (spec-038 Decision 7 - the over-DRY-into-drift guard).
    """
    from django_strawberry_framework.types.converters import convert_choices_to_enum

    class Widget(models.Model):
        status = models.TextField(choices=[("a", "A"), ("b", "B")])

        class Meta:
            app_label = _unique_app_label()

    class WidgetType(DjangoType):
        class Meta:
            model = Widget
            fields = ("id", "status")

    class WidgetForm(forms.ModelForm):
        class Meta:
            model = Widget
            fields = ("status",)

    cre, _, _, _ = build_form_inputs(WidgetForm, operation_kind=CREATE)
    fields = _field_map(cre)
    read_enum = convert_choices_to_enum(Widget._meta.get_field("status"), "WidgetType")
    # The generated input field uses the IDENTICAL enum object the read DjangoType
    # synthesizes (cached per column on the model field), not a parallel ``str``
    # mapping. Strawberry wraps the enum class in a ``StrawberryEnumDefinition`` on
    # the resolved field type, so compare its ``wrapped_cls`` against the raw enum
    # ``convert_choices_to_enum`` returns - same object proves the symmetric reuse.
    assert _inner_type(fields["status"]).wrapped_cls is read_enum


# ---------------------------------------------------------------------------
# Meta.fields / Meta.exclude narrowing + fail-loud
# ---------------------------------------------------------------------------


def test_fields_narrowing_omits_dropped_field():
    """``Meta.fields`` narrows the input to the named fields."""
    cre, _, _, _ = build_form_inputs(
        _item_model_form(),
        operation_kind=CREATE,
        fields=(
            "name",
            "category",
            "is_private",
            "confirm",
        ),
        guard_required=False,
    )
    fields = _field_map(cre)
    assert "is_private" in fields
    cre2, _, _, _ = build_form_inputs(
        _item_model_form(),
        operation_kind=CREATE,
        exclude=("is_private",),
        guard_required=False,
    )
    assert "is_private" not in _field_map(cre2)


def test_meta_fields_rejects_bare_string():
    """A bare-string ``Meta.fields`` raises (it would iterate as characters)."""
    with pytest.raises(ConfigurationError, match="bare string"):
        resolve_effective_form_fields(_item_model_form(), fields="name")


def test_meta_fields_rejects_duplicates():
    """A duplicate field name raises."""
    with pytest.raises(ConfigurationError, match="duplicate field"):
        resolve_effective_form_fields(_item_model_form(), fields=("name", "name"))


def test_meta_fields_rejects_unknown_name():
    """An unknown name (a typo) raises naming the unknown field."""
    with pytest.raises(ConfigurationError, match="unknown form field"):
        resolve_effective_form_fields(_item_model_form(), fields=("emial",))


def test_meta_fields_and_exclude_mutually_exclusive():
    """Declaring both ``fields`` and ``exclude`` raises."""
    with pytest.raises(ConfigurationError, match="both `fields` and `exclude`"):
        resolve_effective_form_fields(
            _item_model_form(),
            fields=("name",),
            exclude=("category",),
        )


def test_empty_effective_field_set_raises():
    """An ``exclude`` dropping every field (empty effective set) raises."""
    with pytest.raises(ConfigurationError, match="has no fields"):
        resolve_effective_form_fields(
            _item_model_form(),
            exclude=(
                "name",
                "category",
                "is_private",
                "confirm",
            ),
        )


def test_empty_fields_tuple_raises():
    """A ``fields = ()`` (empty effective set) raises."""
    with pytest.raises(ConfigurationError, match="has no fields"):
        resolve_effective_form_fields(_item_model_form(), fields=())


def test_fieldless_form_raises():
    """A form with no declared fields raises (empty effective set)."""

    class EmptyForm(forms.Form):
        pass

    with pytest.raises(ConfigurationError, match="has no fields"):
        resolve_effective_form_fields(EmptyForm)


# ---------------------------------------------------------------------------
# Create-required-narrowing guard + waiver
# ---------------------------------------------------------------------------


def test_create_guard_rejects_dropping_required_field_via_fields():
    """A create ``Meta.fields`` dropping a required form field raises naming it."""
    with pytest.raises(ConfigurationError, match="confirm"):
        # ``confirm`` is required; narrowing to only ``name`` drops it.
        build_form_inputs(_item_model_form(), operation_kind=CREATE, fields=("name", "category"))


def test_create_guard_rejects_dropping_required_field_via_exclude():
    """A create ``Meta.exclude`` dropping a required form field raises naming it."""
    with pytest.raises(ConfigurationError, match="confirm"):
        build_form_inputs(_item_model_form(), operation_kind=CREATE, exclude=("confirm",))


def test_create_guard_waiver_does_not_raise():
    """``guard_required=False`` (the get_form_kwargs-override waiver) builds without raising."""
    cre, _, _, _ = build_form_inputs(
        _item_model_form(),
        operation_kind=CREATE,
        fields=("name", "category"),
        guard_required=False,
    )
    assert "confirm" not in _field_map(cre)


def test_partial_guard_rejects_dropping_required_column_less_field():
    """A partial (update) narrowing dropping a required COLUMN-LESS field raises naming it (feedback #4).

    ``confirm`` is a non-model required extra; on update it cannot be reconstructed
    from the row (``model_to_dict`` only returns columns), so dropping it would
    finalize a form that fails required-validation on every request. The effective
    set here keeps only the model-backed fields, dropping ``confirm``.
    """
    effective = resolve_effective_form_fields(_item_model_form(), exclude=("confirm",))
    with pytest.raises(ConfigurationError, match="confirm"):
        guard_partial_required_column_less_fields(_item_model_form(), effective)


def test_partial_guard_allows_dropping_model_backed_required_field():
    """Dropping a MODEL-BACKED required field on update does NOT raise (feedback #4 scoping).

    The load-bearing column-less scoping: ``name`` is a required model column, so the
    partial path widens it optional and reconstructs it from the located row - dropping
    it from the input is harmless and must NOT trip the guard (a blanket reuse of the
    create guard would wrongly reject it). Only ``confirm`` (column-less) would.
    """
    # Drop the model-backed required ``name`` but keep the column-less required ``confirm``.
    effective = resolve_effective_form_fields(_item_model_form(), exclude=("name",))
    guard_partial_required_column_less_fields(_item_model_form(), effective)  # no raise


def test_exclude_naming_unknown_field_raises():
    """``Meta.exclude`` naming a field not on the form raises the Slice-1 narrowing fail-loud."""
    with pytest.raises(ConfigurationError, match="unknown form field"):
        build_form_inputs(
            _item_model_form(),
            operation_kind=CREATE,
            exclude=("definitely_not_a_field",),
        )


def test_excluded_unsupported_field_is_never_converted():
    """An unsupported custom field excluded via ``Meta.fields`` is never converted.

    Required-field discovery walks the FULL declared set, so it must decide
    requiredness as a pure attribute read (``form_field_required``) and never
    call ``convert_form_field`` on a field the mutation excluded - otherwise the
    converter's raising fallthrough for an unsupported type would crash the build
    for a field the consumer deliberately kept out of the schema.
    """

    class Unsupported(forms.Field):
        """A custom field type the converter has no mapping for."""

    class WeirdForm(forms.Form):
        name = forms.CharField()
        weird = Unsupported(required=False)

    cre, _, _, _ = build_form_inputs(WeirdForm, operation_kind=FORM, fields=("name",))
    assert set(_field_map(cre)) == {"name"}


# ---------------------------------------------------------------------------
# Shape identity, naming, dedupe, collision
# ---------------------------------------------------------------------------


def test_narrowed_shapes_get_distinct_names():
    """Two different narrowings of one form produce distinct shape-derived names."""
    form_cls = _item_model_form()
    full = tuple(get_form_fields(form_cls))
    n1 = form_input_type_name(form_cls, CREATE, ("name", "category"), full_field_names=full)
    n2 = form_input_type_name(form_cls, CREATE, ("name", "is_private"), full_field_names=full)
    assert n1 != n2
    # Two narrowings to the SAME effective set produce the SAME name (dedupe basis).
    n3 = form_input_type_name(form_cls, CREATE, ("category", "name"), full_field_names=full)
    assert n1 == n3


def test_canonical_name_for_full_shape():
    """The full effective shape takes the stable ``<FormClass>Input`` / ``PartialInput`` name."""
    form_cls = _item_model_form()
    full = tuple(get_form_fields(form_cls))
    assert (
        form_input_type_name(form_cls, CREATE, full, full_field_names=full) == "ItemModelFormInput"
    )
    assert (
        form_input_type_name(form_cls, PARTIAL, full, full_field_names=full)
        == "ItemModelFormPartialInput"
    )


def test_identical_shape_dedupes_via_ledger():
    """Materializing the same class twice under one name is a no-op (identical shapes dedupe)."""
    cre, _, _, _ = build_form_inputs(_item_model_form(), operation_kind=CREATE)
    materialize_form_input_class("ItemModelFormInput", cre)
    materialize_form_input_class("ItemModelFormInput", cre)  # idempotent, no raise
    assert sys.modules[INPUTS_MODULE_PATH].ItemModelFormInput is cre


def test_distinct_shapes_colliding_on_one_name_raise():
    """Two DISTINCT classes under one name raise ``ConfigurationError`` (the collision raise)."""
    cre_a, _ = build_form_input_class(_item_model_form(), operation_kind=CREATE)

    class OtherForm(forms.Form):
        x = forms.CharField()

    cre_b, _ = build_form_input_class(OtherForm, operation_kind=FORM)
    materialize_form_input_class("CollidingInput", cre_a)
    with pytest.raises(ConfigurationError, match="DjangoFormMutation"):
        materialize_form_input_class("CollidingInput", cre_b)


def test_two_forms_sharing_name_always_collide():
    """Two DIFFERENT form classes with the same ``__name__`` always collide (never dedupe).

    Distinct ``form_class`` identities never dedupe (dedupe is only within one
    ``form_class`` + effective set), so two ``<__name__>Input`` from different
    classes raise even if their field shapes happen to match.
    """

    def _make_named_form():
        class SharedName(forms.Form):
            a = forms.CharField()

        return SharedName

    form_a = _make_named_form()
    form_b = _make_named_form()
    assert form_a.__name__ == form_b.__name__ == "SharedName"
    assert form_a is not form_b

    cre_a, _ = build_form_input_class(form_a, operation_kind=FORM)
    cre_b, _ = build_form_input_class(form_b, operation_kind=FORM)
    materialize_form_input_class("SharedNameInput", cre_a)
    with pytest.raises(ConfigurationError, match="DjangoFormMutation"):
        materialize_form_input_class("SharedNameInput", cre_b)


# ---------------------------------------------------------------------------
# Module-global materialization
# ---------------------------------------------------------------------------


def test_materialized_input_is_module_global():
    """A materialized input class is a real global of ``forms.inputs`` (the lazy-ref contract)."""
    cre, _, _, _ = build_form_inputs(_item_model_form(), operation_kind=CREATE)
    materialize_form_input_class("ItemModelFormInput", cre)
    assert sys.modules[INPUTS_MODULE_PATH].ItemModelFormInput is cre


# ---------------------------------------------------------------------------
# Reverse map - scalar identity + kind constants
# ---------------------------------------------------------------------------


def test_scalar_reverse_map_is_identity():
    """A plain scalar field's reverse map is identity (``name`` -> ``name``, kind scalar)."""
    _, specs, _, _ = build_form_inputs(_item_model_form(), operation_kind=CREATE)
    name_spec = next(s for s in specs if s.form_field_name == "name")
    assert name_spec.input_attr == "name"
    assert name_spec.graphql_name == "name"
    assert name_spec.kind == SCALAR


# ---------------------------------------------------------------------------
# Fail-loud guards - input-attr collision + None-queryset relation
# ---------------------------------------------------------------------------


def test_relation_id_attr_collision_is_fail_loud():
    """A relation ``target`` (-> ``target_id``) colliding with a field literally named
    ``target_id`` raises ``ConfigurationError`` rather than silently dropping one input.

    Both generate ``input_attr == "target_id"``; ``build_strawberry_input_class`` would
    write the second over the first in its annotations dict, losing a field. The package
    is fail-loud, so the assembled-attr collision is caught and named instead.
    """
    plain_target, _ = _make_non_relay_target()

    class CollidingForm(forms.Form):
        target = forms.ModelChoiceField(queryset=plain_target.objects.all())
        target_id = forms.CharField()

    with pytest.raises(ConfigurationError) as exc:
        build_form_inputs(CollidingForm, operation_kind=FORM)
    message = str(exc.value)
    assert "target_id" in message
    assert "'target'" in message
    assert "collide" in message


def test_camel_case_graphql_name_collision_is_fail_loud():
    """Two fields whose names default-camel-case to ONE GraphQL name raise rather than
    silently dropping one input.

    ``foo_bar`` and ``fooBar`` produce DISTINCT input attrs (so the input-attr guard
    passes) but the SAME ``graphql_name`` ``fooBar``; Strawberry would collapse the two
    onto one schema field. The graphql-name guard catches and names them, mirroring the
    read-type guard ``types/finalizer.py::_audit_field_surface``.
    """

    class CamelCollideForm(forms.Form):
        foo_bar = forms.IntegerField()
        fooBar = forms.IntegerField()  # noqa: N815 - intentional collision fixture

    with pytest.raises(ConfigurationError) as exc:
        build_form_inputs(CamelCollideForm, operation_kind=FORM)
    message = str(exc.value)
    assert "fooBar" in message
    assert "collide" in message


def test_extra_field_shadowing_reverse_relation_stays_scalar():
    """An extra ModelForm field reusing a reverse-accessor name stays on the scalar path.

    ``model._meta.get_field("items")`` resolves ``Category.items`` (a reverse
    ``ManyToOneRel``). Treating that as a backing column would emit ``itemsId`` /
    ``relation_single`` for a declared ``CharField`` extra. ``_model_column_for``
    must ignore ``ForeignObjectRel`` so the extra routes through ``convert_form_field``.
    """
    from apps.products.models import Category

    rev = Category._meta.get_field("items")
    assert rev.is_relation and not rev.concrete

    class CategoryForm(forms.ModelForm):
        items = forms.CharField()

        class Meta:
            model = Category
            fields = ("name", "items")

    cre, specs = build_form_input_class(CategoryForm, operation_kind=CREATE)
    items_spec = next(s for s in specs if s.form_field_name == "items")
    assert items_spec.input_attr == "items"
    assert items_spec.graphql_name == "items"
    assert items_spec.kind == SCALAR
    assert items_spec.related_model is None
    fields = _field_map(cre)
    assert "items" in fields
    assert "items_id" not in fields
    assert not _is_optional(fields["items"])


def test_digit_boundary_form_fields_survive_distinct_in_sdl():
    """``field_2`` / ``field2`` both appear on the generated form input (shared pin path).

    Package ``graphql_camel_name`` keeps them distinct; ``build_strawberry_input_class``
    pins every wire name so Strawberry's converter cannot collapse ``field_2`` onto
    ``field2``. Forms route through that shared builder - this locks the form flavor.
    """

    class DigitForm(forms.Form):
        field_2 = forms.IntegerField()
        field2 = forms.IntegerField()

    cre, specs = build_form_input_class(DigitForm, operation_kind=FORM)
    assert {(s.input_attr, s.graphql_name) for s in specs} == {
        ("field_2", "field_2"),
        ("field2", "field2"),
    }

    def _probe(inp) -> int:
        return 1

    _probe.__annotations__ = {"inp": cre, "return": int}

    @strawberry.type
    class Query:
        probe: int = strawberry.field(resolver=_probe)

    from django_strawberry_framework.scalars import strawberry_config

    schema = strawberry.Schema(query=Query, config=strawberry_config())
    sdl = schema.as_str()
    block = sdl[sdl.index("input DigitFormInput") :]
    block = block[: block.index("}")]
    assert "field_2:" in block
    assert "field2:" in block


def test_model_choice_field_with_none_queryset_is_fail_loud():
    """A model-less ``ModelChoiceField(queryset=None)`` (the queryset-in-``__init__`` idiom)
    raises a diagnosable ``ConfigurationError`` at schema build, not a bare ``AttributeError``.

    Schema-time discovery reads ``base_fields`` without instantiating the form, so a
    ``queryset`` assigned in ``__init__`` is ``None`` here and the related model cannot be
    resolved; the guard names the form / field rather than failing on ``None.model``.
    """

    class LateQuerysetForm(forms.Form):
        target = forms.ModelChoiceField(queryset=None)

    with pytest.raises(ConfigurationError) as exc:
        build_form_inputs(LateQuerysetForm, operation_kind=FORM)
    message = str(exc.value)
    assert "LateQuerysetForm" in message
    assert "'target'" in message
    assert "queryset is None" in message
