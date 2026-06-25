"""Consumer Django forms for the products live form-mutation surface (spec-038 Slice 4).

These are plain Django forms (declared the standard Django way - no package imports
beyond ``django.forms``); ``apps/products/schema.py`` wraps them in the shipped
``DjangoModelFormMutation`` / ``DjangoFormMutation`` bases so the live ``/graphql/``
tests in ``test_query/test_products_api.py`` exercise the form-mutation pipeline end to
end. Four forms cover the spec's Decision-12 live matrix:

* ``ItemModelForm`` - a ``ModelForm`` over ``Item`` carrying ``name`` / ``description`` /
  ``category`` (the FK that drives the ``categoryId``-through-the-form P1 reverse map).
  Its ``clean_name`` rejects a sentinel value for the field-level ``form.errors`` case,
  and the model's ``unique_item_per_category`` constraint surfaces through ``_post_clean``
  as a ``NON_FIELD_ERRORS`` -> ``"__all__"`` entry (the constraint case needs no custom
  ``clean()``). Drives create + update (including partial-update preservation).
* ``ContactForm`` - a model-less plain ``forms.Form`` (a ``CharField`` + an
  ``EmailField``) with a ``clean_subject`` that can fail, for the plain-form
  ``{ ok, errors }`` success / validation-failure shapes.
* ``StampedItemModelForm`` - a ``ModelForm`` over ``Item`` whose ``__init__`` REQUIRES a
  ``user`` kwarg (popped + validated in ``clean()``), for the P2 ``get_form_kwargs``
  override-injects-``user`` case. Schema-time discovery reads ``base_fields`` (no
  instantiation), so the required-kwarg ``__init__`` is fine at bind; the mutation's
  ``get_form_kwargs`` override supplies the ``user`` at runtime.
* ``ItemFileModelForm`` - a ``ModelForm`` over ``Item`` carrying the nullable
  ``attachment`` ``FileField``, for the raw multipart ``Upload`` test (the form's
  converter maps the ``FileField`` -> ``Upload`` and the resolver routes the upload into
  ``files=``).
"""

from django import forms

from .models import Item

# The sentinel value ``ItemModelForm.clean_name`` rejects - drives the field-level
# ``form.errors`` keyed-to-the-form-field live case (a ``clean_<field>`` error).
REJECTED_ITEM_NAME = "__rejected__"


class ItemModelForm(forms.ModelForm):
    """``ModelForm`` over ``Item`` for the create / update / partial-update live matrix.

    ``Meta.fields`` covers ``name`` / ``description`` / ``category`` - the FK
    ``category`` is the field the generated ``categoryId`` input writes through (the P1
    reverse map). ``clean_name`` rejects ``REJECTED_ITEM_NAME`` so a field-level
    ``form.errors`` entry keys to ``name``; the model's ``unique_item_per_category``
    constraint surfaces automatically through ``_post_clean`` -> ``validate_constraints``
    as a ``NON_FIELD_ERRORS`` entry the resolver maps to the ``"__all__"`` sentinel.
    """

    class Meta:
        model = Item
        fields = ("name", "description", "category")

    def clean_name(self):
        name = self.cleaned_data["name"]
        if name == REJECTED_ITEM_NAME:
            raise forms.ValidationError("This name is not allowed.")
        return name


class ContactForm(forms.Form):
    """A model-less plain ``forms.Form`` for the ``DjangoFormMutation`` ``{ ok, errors }`` shapes.

    ``clean_subject`` rejects a blank-after-strip subject so the validation-failure case
    yields a field-keyed ``errors`` entry on ``subject``; otherwise both fields validate
    and the success case returns ``ok: true`` / empty ``errors``. No model column is ever
    written - the form is model-less, so its mutation defines an explicit
    ``Meta.permission_classes`` (no ``DjangoModelPermission`` default applies).
    """

    subject = forms.CharField(max_length=200)
    email = forms.EmailField()

    def clean_subject(self):
        subject = self.cleaned_data["subject"].strip()
        if not subject:
            raise forms.ValidationError("Subject must not be blank.")
        return subject


class PingForm(forms.Form):
    """A trivial model-less ``forms.Form`` for the deny-by-default live test.

    Backs a ``DjangoFormMutation`` that declares NO ``Meta.permission_classes``, so a
    model-less form falls to the ``DenyAll`` deny-by-default posture (spec-038
    Decision 11): the live mutation must reject every caller with a top-level
    authorization error, never run the form.
    """

    message = forms.CharField(max_length=200)


class StampedItemModelForm(forms.ModelForm):
    """``ModelForm`` over ``Item`` whose ``__init__`` REQUIRES a ``user`` kwarg (P2 case).

    Models the construction-hook migration case: the form cannot be instantiated without
    a ``user``, and its ``clean()`` requires ``user.is_authenticated``. Schema-time
    discovery reads ``base_fields`` (no instantiation), so the required-kwarg ``__init__``
    is fine at bind; the mutation's ``get_form_kwargs`` override injects
    ``user=info.context.request.user`` at runtime. The injected user stamps the created
    row's ``description`` so the test can pin that the user actually reached the form.
    """

    class Meta:
        model = Item
        fields = ("name", "category")

    def __init__(self, *args, user=None, **kwargs):
        self._user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        if self._user is None or not self._user.is_authenticated:
            raise forms.ValidationError("An authenticated user is required.")
        return cleaned

    def save(self, commit=True):
        item = super().save(commit=False)
        item.description = f"stamped by {self._user.username}"
        if commit:
            item.save()
        return item


class ItemFileModelForm(forms.ModelForm):
    """``ModelForm`` over ``Item`` carrying the nullable ``attachment`` ``FileField``.

    The file-form for the raw multipart ``Upload`` test: the converter maps the
    ``attachment`` ``FileField`` to the ``Upload`` scalar on input, and the resolver
    routes the uploaded value into the form's ``files=`` (never ``data=``). ``name`` and
    ``category`` are also carried so a valid create is reachable.
    """

    class Meta:
        model = Item
        fields = ("name", "category", "attachment")
