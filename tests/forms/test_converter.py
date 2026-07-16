"""Converter tests for the form-field -> Strawberry annotation registry (spec-038 Slice 1).

Covers ``django_strawberry_framework/forms/converter.py``:

- ``convert_form_field`` scalar mappings + required-ness for every supported
  ``forms.Field`` class (text-like -> ``str``, the numeric / temporal / uuid /
  multi-choice cases, ``NullBooleanField`` -> ``bool | None``);
- the fail-loud dispatch: a bare ``forms.Field`` -> ``str``, a known subclass
  (``EmailField``) mapping via the MRO walk, and a custom ``forms.Field``
  subclass with no supported ancestor raising ``ConfigurationError`` (the
  load-bearing no-catch-all assertion);
- the relation / file kind flags (``ModelChoiceField`` / ``ModelMultipleChoiceField``
  / ``FileField`` / ``ImageField``) the input builder finalizes.

The relation id-type (Relay-``GlobalID`` vs raw pk, single + multi) is pinned at
the input-build site (the converter returns only the ``kind`` for relations), so
that assertion lives in ``test_inputs.py`` where the id type is finalized.
"""

from __future__ import annotations

import datetime
import decimal
import uuid

import pytest
import strawberry
from django import forms

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.forms.converter import (
    FILE,
    RELATION_MULTI,
    RELATION_SINGLE,
    SCALAR,
    FormInputFieldSpec,
    convert_form_field,
)


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        (forms.CharField(), str),
        (forms.EmailField(), str),
        (forms.SlugField(), str),
        # ``assume_scheme="https"`` is required across Django 5.2-6.0: 5.x emits a
        # RemovedInDjango60Warning without it (the http->https default flip), which the
        # suite's -W error turns into a collection error; 6.0 accepts the argument and
        # already defaults to https. Passing it explicitly is version-agnostic and the
        # converter maps URLField -> str regardless of scheme.
        (forms.URLField(assume_scheme="https"), str),
        (forms.RegexField(regex=r".*"), str),
        (forms.ChoiceField(), str),
        (forms.Field(), str),
        (forms.IntegerField(), int),
        (forms.FloatField(), float),
        (forms.DecimalField(), decimal.Decimal),
        (forms.BooleanField(), bool),
        (forms.UUIDField(), uuid.UUID),
        (forms.DateField(), datetime.date),
        (forms.DateTimeField(), datetime.datetime),
        (forms.TimeField(), datetime.time),
        (forms.MultipleChoiceField(), list[str]),
    ],
)
def test_scalar_field_annotations(field, expected):
    """Each supported scalar form field maps to its Strawberry annotation, kind ``scalar``."""
    conversion = convert_form_field(field)
    assert conversion.annotation == expected
    assert conversion.kind == SCALAR


def test_null_boolean_field_is_optional_bool():
    """``NullBooleanField`` -> ``bool | None``, always optional (graphene parity).

    Django's ``NullBooleanField.validate`` is a no-op, so ``field.required`` is
    meaningless for form validation. GraphQL also cannot express a required
    nullable input; baking ``bool | None`` with ``required=True`` (Django's
    default) produced SDL ``Boolean`` without a default, so clients could omit
    the field per the schema and then hit a Strawberry ``TypeError``. Force
    ``required=False`` regardless of ``field.required``.
    """
    conversion = convert_form_field(forms.NullBooleanField())
    assert conversion.annotation == (bool | None)
    assert conversion.kind == SCALAR
    assert conversion.required is False
    assert convert_form_field(forms.NullBooleanField(required=True)).required is False
    assert convert_form_field(forms.NullBooleanField(required=False)).required is False


def test_json_field_maps_to_json_scalar_not_charfield_str():
    """``JSONField`` subclasses ``CharField`` but must resolve to ``JSON``, not ``str``.

    Without an explicit registry row the MRO walk would hit ``CharField`` ->
    ``str`` and the generated input would reject object / array literals that
    Django's form field (and the serializer / model scalar tables) accept.
    """
    conversion = convert_form_field(forms.JSONField())
    assert conversion.annotation is strawberry.scalars.JSON
    assert conversion.kind == SCALAR


def test_required_ness_reflects_field_required():
    """``required`` mirrors ``field.required`` for both states (non-NullBoolean)."""
    assert convert_form_field(forms.CharField(required=True)).required is True
    assert convert_form_field(forms.CharField(required=False)).required is False


def test_email_field_maps_via_mro_under_charfield():
    """A known subclass (``EmailField``) resolves to its ``CharField`` parent's scalar."""
    # EmailField is not its own entry in the scalar table; the MRO walk reaches
    # CharField -> str. This is the parity behavior the spec mandates.
    assert convert_form_field(forms.EmailField()).annotation is str


def test_float_and_decimal_do_not_collapse_to_integer_parent():
    """``FloatField`` / ``DecimalField`` subclass ``IntegerField`` but keep their own scalar.

    A naive "first ``isinstance`` wins" walk over an ``IntegerField``-first
    registry would mis-map both to ``int``; the ``type(field).__mro__`` walk
    visits the field's own class first so each resolves correctly.
    """
    assert convert_form_field(forms.FloatField()).annotation is float
    assert convert_form_field(forms.DecimalField()).annotation is decimal.Decimal
    # UUIDField subclasses CharField - same hazard, same guard.
    assert convert_form_field(forms.UUIDField()).annotation is uuid.UUID


# ---------------------------------------------------------------------------
# Relation / file kind flags (annotation finalized at the input-build site)
# ---------------------------------------------------------------------------


def test_model_choice_field_is_relation_single():
    """``ModelChoiceField`` -> kind ``relation_single`` (annotation finalized at build site).

    The converter only reads ``field.required`` and returns the relation ``kind``
    (the id annotation is finalized at the input-build site over a real model's
    primary ``DjangoType``), so a ``queryset=None`` field suffices here; the
    Relay-vs-raw-pk id-type assertions live in ``test_inputs.py``.
    """
    field = forms.ModelChoiceField(queryset=None)
    conversion = convert_form_field(field)
    assert conversion.kind == RELATION_SINGLE
    assert conversion.annotation is None


def test_model_multiple_choice_field_is_relation_multi():
    """``ModelMultipleChoiceField`` -> kind ``relation_multi`` (precedes the single check)."""
    field = forms.ModelMultipleChoiceField(queryset=None)
    conversion = convert_form_field(field)
    assert conversion.kind == RELATION_MULTI
    assert conversion.annotation is None


def test_file_and_image_fields_are_file_kind():
    """``FileField`` / ``ImageField`` -> kind ``file`` (the ``Upload`` annotation is build-site)."""
    assert convert_form_field(forms.FileField()).kind == FILE
    assert convert_form_field(forms.ImageField()).kind == FILE


# ---------------------------------------------------------------------------
# Fail-loud dispatch - no base-Field catch-all (the load-bearing P2 assertion)
# ---------------------------------------------------------------------------


def test_bare_field_maps_to_str_as_exact_type_special_case():
    """A bare ``forms.Field`` is an exact-type special case -> ``str`` (not a catch-all)."""
    conversion = convert_form_field(forms.Field())
    assert conversion.annotation is str
    assert conversion.kind == SCALAR


def test_unknown_custom_field_subclass_raises():
    """A custom ``forms.Field`` subclass with no supported ancestor raises ``ConfigurationError``.

    This is the catch-all-shadowing regression: if a base-``forms.Field`` -> ``str``
    entry were registered, this custom field would silently become ``String``
    instead of failing loud. The raise proves no such catch-all exists.
    """

    class CustomField(forms.Field):
        pass

    with pytest.raises(ConfigurationError, match="Unsupported form field type 'CustomField'"):
        convert_form_field(CustomField())


# ---------------------------------------------------------------------------
# FormInputFieldSpec - the per-input-field reverse-map record
# ---------------------------------------------------------------------------


def test_form_input_field_spec_is_frozen_record():
    """The reverse-map record carries input_attr / graphql_name / form_field_name / kind."""
    spec = FormInputFieldSpec(
        input_attr="category_id",
        graphql_name="categoryId",
        form_field_name="category",
        kind=RELATION_SINGLE,
    )
    assert spec.input_attr == "category_id"
    assert spec.graphql_name == "categoryId"
    assert spec.form_field_name == "category"
    assert spec.kind == RELATION_SINGLE
    with pytest.raises((AttributeError, TypeError)):
        spec.kind = SCALAR  # frozen
