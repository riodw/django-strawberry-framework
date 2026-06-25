"""``DjangoFormMutation`` / ``DjangoModelFormMutation`` bases, ``Meta`` validation, and the bind (spec-038 Slice 2).

Covers ``django_strawberry_framework/forms/sets.py``:

- the two-flavor ``Meta`` validation matrix at class creation (missing /
  wrong-type ``form_class``; a ``ModelForm`` on the plain base rejected naming
  ``DjangoModelFormMutation``; a non-``ModelForm`` on ``DjangoModelFormMutation``;
  a ``ModelForm`` with no resolvable model; ``operation = "delete"`` rejected on
  the ``ModelForm`` base; ANY ``operation`` rejected on the plain base;
  ``form_class`` accepted as a known key; ``fields`` + ``exclude`` both set;
  unknown key; the unknown-name narrowing routed through the Slice-1 machinery);
- plain-form input dedupe via the ``"form"`` sentinel;
- declaration registration (the ``ModelForm`` flavor in the ``DjangoMutation``
  registry, the plain flavor in the disjoint plain-form registry, abstract bases
  nowhere, post-finalize rejected);
- the phase-2.5 bind - both paths (the ``DjangoMutation``-ride for the
  ``ModelForm`` flavor through the ``build_input`` seam into ``forms.inputs``, and
  the ``bind_form_mutations()`` path for the plain flavor with the pinned
  ``{ ok errors }`` payload);
- the no-registered-primary-type finalize error for ``DjangoModelFormMutation``.

System-under-test is the bases / metaclasses / validation / bind, run against the
products ``Item`` / ``Category`` FK fixtures + package-local form fixtures (a
``ModelForm`` over ``Item``, a plain ``Form``, a ``ModelForm`` with no model).
Mirrors the ``tests/mutations/test_sets.py`` + ``tests/forms/test_inputs.py``
fixture posture.
"""

from __future__ import annotations

import itertools
import sys

import pytest
import strawberry
from apps.products import models as product_models
from django import forms

import django_strawberry_framework
from django_strawberry_framework import (
    DjangoFormMutation,
    DjangoModelFormMutation,
    DjangoModelPermission,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.forms import (
    DjangoFormMutation as DjangoFormMutationFromForms,
)
from django_strawberry_framework.forms import (
    DjangoModelFormMutation as DjangoModelFormMutationFromForms,
)
from django_strawberry_framework.forms.inputs import CREATE
from django_strawberry_framework.forms.inputs import (
    INPUTS_MODULE_PATH as FORMS_INPUTS_MODULE_PATH,
)
from django_strawberry_framework.forms.inputs import (
    _materialized_names as form_materialized_names,
)
from django_strawberry_framework.forms.sets import (
    _cached_build_form_input,
    _form_mutation_registry,
    clear_form_shape_build_cache,
    iter_form_mutations,
)
from django_strawberry_framework.mutations.inputs import (
    _materialized_names as mutation_materialized_names,
)
from django_strawberry_framework.mutations.permissions import DenyAll
from django_strawberry_framework.mutations.sets import iter_mutations
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Reset the registry (now co-clearing the form-input ledger + the plain-form registry).

    ``registry.clear()`` is wired this slice to co-clear
    ``clear_form_input_namespace`` (the form-input + form-payload globals ledger)
    and ``clear_form_mutation_registry`` (the plain-form declaration registry), so
    a single ``registry.clear()`` resets every form-side ledger (and the mutation
    ledgers the ``ModelForm`` flavor rides). The products ``DjangoType``s register
    on import, so the clear is needed before/after.
    """
    registry.clear()
    yield
    registry.clear()


_app_label_counter = itertools.count(1)


def _unique_app_label() -> str:
    """Return a unique ``app_label`` per call to avoid Django's re-register warning."""
    return f"test_form_sets__{next(_app_label_counter)}"


def _item_model_form():
    """A ``ModelForm`` over products ``Item`` (the ``ModelForm`` flavor fixture)."""

    class ItemModelForm(forms.ModelForm):
        class Meta:
            model = product_models.Item
            fields = ("name", "category", "is_private")

    return ItemModelForm


def _contact_form():
    """A plain ``forms.Form`` (no model column) - the plain-flavor fixture."""

    class ContactForm(forms.Form):
        message = forms.CharField()

    return ContactForm


def _declare_products_primaries():
    """Register primary ``DjangoType``s for ``Item`` + ``Category`` (Relay-shaped)."""

    class CategoryT(DjangoType, strawberry.relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    class ItemT(DjangoType, strawberry.relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    return CategoryT, ItemT


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


def test_bases_exported_from_package_root():
    """Both bases are re-exported from the package root + are in ``__all__``."""
    assert django_strawberry_framework.DjangoFormMutation is DjangoFormMutationFromForms
    assert django_strawberry_framework.DjangoModelFormMutation is DjangoModelFormMutationFromForms
    assert "DjangoFormMutation" in django_strawberry_framework.__all__
    assert "DjangoModelFormMutation" in django_strawberry_framework.__all__


# ---------------------------------------------------------------------------
# Meta validation matrix - missing / wrong-type form_class
# ---------------------------------------------------------------------------


def test_modelform_missing_form_class_raises():
    """A ``DjangoModelFormMutation`` with no ``Meta.form_class`` raises naming the key."""
    with pytest.raises(ConfigurationError, match="declares no form_class"):

        class CreateItem(DjangoModelFormMutation):
            class Meta:
                operation = "create"


def test_plain_form_missing_form_class_raises():
    """A ``DjangoFormMutation`` with no ``Meta.form_class`` raises naming the key."""
    with pytest.raises(ConfigurationError, match="declares no form_class"):

        class Submit(DjangoFormMutation):
            class Meta:
                pass


def test_modelform_with_plain_form_raises():
    """A plain ``forms.Form`` on ``DjangoModelFormMutation`` raises (must be a ModelForm)."""
    form_cls = _contact_form()
    with pytest.raises(ConfigurationError, match="must be a forms.ModelForm subclass"):

        class CreateThing(DjangoModelFormMutation):
            class Meta:
                form_class = form_cls
                operation = "create"


def test_plain_base_with_modelform_raises_naming_modelform_base():
    """A ``ModelForm`` on the plain ``DjangoFormMutation`` base raises naming the ModelForm base.

    The ``issubclass(form_class, forms.ModelForm)``-first check (Edge case P2): the
    targeted message names ``DjangoModelFormMutation`` as the correct base, not a
    generic "not a Form" message.
    """
    form_cls = _item_model_form()
    with pytest.raises(ConfigurationError, match="use DjangoModelFormMutation"):

        class Submit(DjangoFormMutation):
            class Meta:
                form_class = form_cls


def test_plain_base_form_class_not_a_form_raises():
    """A non-``Form`` value on the plain base raises the general type gate."""

    class NotAForm:
        pass

    with pytest.raises(ConfigurationError, match="must be a forms.Form subclass"):

        class Submit(DjangoFormMutation):
            class Meta:
                form_class = NotAForm


def test_modelform_with_no_resolvable_model_raises():
    """A ``ModelForm`` whose ``_meta.model`` is unset raises a clean config error, not AttributeError.

    A ``ModelForm`` declaring only ``fields`` with no ``Meta.model`` resolves no
    model; the form ``_validate_meta`` raises a ``ConfigurationError`` rather than
    letting ``form_class._meta.model`` surface a raw ``AttributeError``.
    """

    class NoModelForm(forms.ModelForm):
        name = forms.CharField()

    with pytest.raises(ConfigurationError, match="resolves no model"):

        class CreateThing(DjangoModelFormMutation):
            class Meta:
                form_class = NoModelForm
                operation = "create"


# ---------------------------------------------------------------------------
# Meta validation matrix - operation rules (P2 split)
# ---------------------------------------------------------------------------


def test_modelform_delete_operation_rejected():
    """``operation = "delete"`` on ``DjangoModelFormMutation`` is rejected (no form delete)."""
    form_cls = _item_model_form()
    with pytest.raises(ConfigurationError, match="operation must be one of"):

        class DeleteItem(DjangoModelFormMutation):
            class Meta:
                form_class = form_cls
                operation = "delete"


def test_modelform_missing_operation_rejected():
    """A missing ``operation`` on the ``ModelForm`` base is rejected (``None`` invalid)."""
    form_cls = _item_model_form()
    with pytest.raises(ConfigurationError, match="operation must be one of"):

        class CreateItem(DjangoModelFormMutation):
            class Meta:
                form_class = form_cls


@pytest.mark.parametrize(
    "operation",
    [
        "create",
        "update",
        "delete",
        "upsert",
        # An explicit ``operation = None`` is rejected by KEY PRESENCE, not value
        # (docs/feedback.md Finding 5): the fixed ``"form"`` sentinel accepts no
        # copied ``Meta.operation`` key, even one set to ``None``.
        None,
    ],
)
def test_plain_base_rejects_any_operation(operation):
    """The plain ``DjangoFormMutation`` base rejects ANY ``Meta.operation`` (P2 / Decision 10)."""
    form_cls = _contact_form()
    declared_operation = operation  # bind to a local: a class body cannot read the param name.
    with pytest.raises(ConfigurationError, match="operation is not supported"):

        class Submit(DjangoFormMutation):
            class Meta:
                form_class = form_cls
                operation = declared_operation


# ---------------------------------------------------------------------------
# Meta validation matrix - allowed keys + narrowing
# ---------------------------------------------------------------------------


def test_modelform_form_class_accepted_as_known_key():
    """A valid ``DjangoModelFormMutation`` declaration does not raise; the snapshot is stamped."""
    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"

    assert CreateItem._mutation_meta.form_class is form_cls
    assert CreateItem._mutation_meta.model is product_models.Item
    assert CreateItem._mutation_meta.operation == "create"


def test_plain_form_class_accepted_as_known_key():
    """A valid ``DjangoFormMutation`` declaration does not raise; the snapshot uses the sentinel."""
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = form_cls

    assert Submit._mutation_meta.form_class is form_cls
    assert Submit._mutation_meta.model is None
    assert Submit._mutation_meta.operation == "form"
    # An unset ``permission_classes`` defaults to deny-by-default for the plain
    # flavor - it cannot inherit the model-permission default (Finding 1).
    assert Submit._mutation_meta.permission_classes == [DenyAll]


def test_plain_form_unset_permission_classes_defaults_to_deny_all():
    """A plain form with no ``permission_classes`` defaults to ``[DenyAll]`` (Finding 1).

    A model-less form cannot inherit ``DjangoModelPermission`` (it reads a model
    the plain flavor never resolves), so the safe default is deny-by-default rather
    than a request-time crash.
    """
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = form_cls

    assert Submit._mutation_meta.permission_classes == [DenyAll]


def test_plain_form_empty_permission_classes_is_allow_any_opt_out():
    """An explicit ``permission_classes = []`` on a plain form is preserved (allow-any opt-out)."""
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = form_cls
            permission_classes = []

    assert Submit._mutation_meta.permission_classes == []


def test_modelform_unset_permission_classes_keeps_model_permission_default():
    """The ModelForm flavor still defaults to ``[DjangoModelPermission]`` (no regression, Finding 1)."""
    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"

    assert CreateItem._mutation_meta.permission_classes == [DjangoModelPermission]


def test_modelform_unknown_meta_key_raises():
    """A stray ``Meta`` key on the ``ModelForm`` base raises the typo guard."""
    form_cls = _item_model_form()
    with pytest.raises(ConfigurationError, match="unknown keys"):

        class CreateItem(DjangoModelFormMutation):
            class Meta:
                form_class = form_cls
                operation = "create"
                widget = "nope"


def test_plain_form_model_key_is_unknown():
    """``model`` is NOT an allowed plain-form key (it dropped from the form allowed set)."""
    form_cls = _contact_form()
    with pytest.raises(ConfigurationError, match="unknown keys"):

        class Submit(DjangoFormMutation):
            class Meta:
                form_class = form_cls
                model = product_models.Item


def test_modelform_fields_and_exclude_both_raises():
    """Declaring both ``fields`` and ``exclude`` on the ``ModelForm`` base raises."""
    form_cls = _item_model_form()
    with pytest.raises(ConfigurationError, match="both `fields` and `exclude`"):

        class CreateItem(DjangoModelFormMutation):
            class Meta:
                form_class = form_cls
                operation = "create"
                fields = ("name",)
                exclude = ("category",)


def test_plain_form_fields_and_exclude_both_raises():
    """Declaring both ``fields`` and ``exclude`` on the plain base raises."""

    class MultiForm(forms.Form):
        a = forms.CharField()
        b = forms.CharField()

    with pytest.raises(ConfigurationError, match="both `fields` and `exclude`"):

        class Submit(DjangoFormMutation):
            class Meta:
                form_class = MultiForm
                fields = ("a",)
                exclude = ("b",)


def test_modelform_unknown_field_name_routes_through_slice1_narrowing():
    """An unknown ``Meta.fields`` name routes through the Slice-1 narrowing fail-loud."""
    form_cls = _item_model_form()
    with pytest.raises(ConfigurationError, match="unknown form field"):

        class CreateItem(DjangoModelFormMutation):
            class Meta:
                form_class = form_cls
                operation = "create"
                fields = ("definitely_not_a_field",)


def test_cached_build_form_input_runs_required_guard_per_declaration():
    """A cached narrowed shape does NOT let a later declaration bypass the create-required guard (Finding 5).

    The per-shape build cache is keyed by ``(form_class, operation_kind, effective
    set)`` - NOT by ``guard_required``. So a WAIVING mutation
    (``guard_required=False``, having overridden ``get_form_kwargs`` / ``get_form``)
    that materializes a narrowed shape FIRST must not poison the cache for a later
    NON-waiving mutation over the same form + effective set: the guard is tied to
    each declaration, not to whichever class built the shape first. Pre-fix, the
    second call returned the cached value and silently skipped the guard.
    """

    class _RequiredExtraForm(forms.ModelForm):
        confirm = forms.CharField()  # required, no model column - dropped by the narrowing below

        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    clear_form_shape_build_cache()
    # The waiving declaration narrows `confirm` away and builds without the guard.
    waived_cls, _specs = _cached_build_form_input(
        _RequiredExtraForm,
        operation_kind=CREATE,
        fields=("name", "category"),
        exclude=None,
        guard_required=False,
    )
    assert waived_cls is not None  # the waiver built + cached the narrowed shape

    # A later NON-waiving declaration over the SAME form + effective set must STILL
    # raise (the guard runs per-declaration, before the cache lookup), not silently
    # reuse the waived shape.
    with pytest.raises(ConfigurationError, match="confirm"):
        _cached_build_form_input(
            _RequiredExtraForm,
            operation_kind=CREATE,
            fields=("name", "category"),
            exclude=None,
            guard_required=True,
        )


# ---------------------------------------------------------------------------
# permission_classes default
# ---------------------------------------------------------------------------


def test_modelform_permission_classes_default():
    """An unset ``permission_classes`` resolves to ``[DjangoModelPermission]`` (the ModelForm base)."""
    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"

    assert CreateItem._mutation_meta.permission_classes == [DjangoModelPermission]


def test_plain_form_permission_classes_explicit_opt_out():
    """A plain form may opt out with an explicit ``[]`` (the AllowAny posture)."""
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = form_cls
            permission_classes = []

    assert Submit._mutation_meta.permission_classes == []


# ---------------------------------------------------------------------------
# Declaration registration (disjoint ledgers)
# ---------------------------------------------------------------------------


def test_modelform_registers_in_mutation_registry():
    """A concrete ``DjangoModelFormMutation`` rides the ``DjangoMutation`` declaration registry."""
    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"

    assert CreateItem in iter_mutations()
    assert CreateItem not in iter_form_mutations()


def test_plain_form_registers_in_disjoint_form_registry():
    """A concrete ``DjangoFormMutation`` records in the disjoint plain-form registry only."""
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = form_cls

    assert Submit in iter_form_mutations()
    assert Submit not in iter_mutations()


def test_abstract_bases_register_nowhere():
    """The abstract ``DjangoFormMutation`` / ``DjangoModelFormMutation`` bases register nowhere."""
    assert DjangoModelFormMutation not in iter_mutations()
    assert DjangoFormMutation not in iter_form_mutations()


def test_plain_form_registration_is_idempotent():
    """Re-recording the same plain class (identity) does not double-register."""
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = form_cls

    from django_strawberry_framework.forms.sets import register_form_mutation

    register_form_mutation(Submit)
    assert _form_mutation_registry.count(Submit) == 1


def test_plain_form_late_declaration_after_finalize_raises():
    """Declaring a plain form after ``finalize_django_types()`` raises naming the flavor."""

    class ItemType(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    finalize_django_types()
    with pytest.raises(ConfigurationError, match="DjangoFormMutation .* after finalization"):

        class Submit(DjangoFormMutation):
            class Meta:
                form_class = _contact_form()


# ---------------------------------------------------------------------------
# Phase-2.5 bind - both paths
# ---------------------------------------------------------------------------


def test_modelform_bind_materializes_form_input_into_forms_namespace():
    """The ``ModelForm`` flavor binds via the ``DjangoMutation`` path through the ``build_input`` seam.

    The form-derived input materializes into ``forms.inputs`` (NOT
    ``mutations.inputs``), and the model-backed ``<Name>Payload`` materializes into
    ``mutations.inputs`` (the ``DjangoMutation`` payload path, with a ``node`` /
    ``result`` slot).
    """
    _declare_products_primaries()
    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"

    assert form_materialized_names == {}
    finalize_django_types()

    forms_module = sys.modules[FORMS_INPUTS_MODULE_PATH]
    # The form-derived input lives in forms.inputs, NOT mutations.inputs.
    assert "ItemModelFormInput" in form_materialized_names
    assert "ItemModelFormInput" not in mutation_materialized_names
    assert CreateItem._input_class is form_materialized_names["ItemModelFormInput"]
    assert forms_module.ItemModelFormInput is form_materialized_names["ItemModelFormInput"]

    # The payload is model-backed (rides the DjangoMutation payload path).
    assert "CreateItemPayload" in mutation_materialized_names
    assert CreateItem._payload_type_name == "CreateItemPayload"
    assert CreateItem._primary_type is not None
    payload = mutation_materialized_names["CreateItemPayload"]
    slots = {f.python_name for f in payload.__strawberry_definition__.fields}
    assert "errors" in slots
    assert "node" in slots  # Item is Relay-shaped -> node slot


def test_plain_form_bind_materializes_input_and_ok_errors_payload():
    """The plain flavor binds via ``bind_form_mutations()`` with a pinned ``{ ok errors }`` payload."""
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = form_cls

    finalize_django_types()

    # The form-derived input materialized.
    assert "ContactFormInput" in form_materialized_names
    assert Submit._input_class is form_materialized_names["ContactFormInput"]
    # The pinned model-less payload has EXACTLY ok + errors, no object slot.
    assert Submit._payload_type_name == "SubmitPayload"
    assert Submit._primary_type is None
    payload = mutation_materialized_names["SubmitPayload"]
    slots = {f.python_name for f in payload.__strawberry_definition__.fields}
    assert slots == {"ok", "errors"}


def test_plain_form_input_dedupes_via_form_sentinel():
    """Two plain mutations over the SAME form + effective set dedupe to one input class.

    The ``"form"`` sentinel shape identity (Decision 7 P2): both build the same
    ``<FormClass>Input`` shape, so the materialize ledger dedupes to one class
    object (idempotent re-materialize, no AR-M6 collision raise).
    """
    form_cls = _contact_form()

    class SubmitA(DjangoFormMutation):
        class Meta:
            form_class = form_cls

    class SubmitB(DjangoFormMutation):
        class Meta:
            form_class = form_cls

    finalize_django_types()

    assert "ContactFormInput" in form_materialized_names
    # Both resolve to the SAME deduped input class object.
    assert SubmitA._input_class is SubmitB._input_class
    assert SubmitA._input_class is form_materialized_names["ContactFormInput"]


def test_modelform_no_registered_primary_type_raises_at_finalize():
    """A ``DjangoModelFormMutation`` whose model has no registered ``DjangoType`` raises at finalize.

    No primary type for the model means the mutation has no type to return - the
    reused ``_resolve_primary_type`` path raises the "no registered DjangoType" /
    "no type to return" error.
    """
    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"

    # No DjangoType declared for Item this build.
    with pytest.raises(ConfigurationError, match="no registered DjangoType|no type to return"):
        finalize_django_types()


def test_plain_form_default_perform_mutate_calls_form_save():
    """The default ``perform_mutate`` calls ``form.save()`` when the plain form defines one.

    A plain ``forms.Form`` has no ``save`` by default (the no-op path); a form that
    DOES define one has it invoked by the default ``perform_mutate`` hook.
    """
    called = {}

    class SavingForm(forms.Form):
        message = forms.CharField()

        def save(self):
            called["saved"] = True

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = SavingForm
            permission_classes = []

    Submit().perform_mutate(SavingForm(data={"message": "x"}), info=None)
    assert called["saved"] is True
