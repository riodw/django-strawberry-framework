"""Tests for the shared fail-loud converter-dispatch skeleton (``utils/converters.py``, spec-039).

``convert_with_mro`` single-sites the ordered-precheck -> MRO-walk ->
raising-fallthrough control flow both ``forms/converter.py`` and
``rest_framework/serializer_converter.py`` ride. These tests pin the skeleton in
isolation (flavor-free) so the no-silent-catch-all contract is verified once at
its owner:

- a precheck match wins (and runs in order; a precheck for a parent class
  precedes the scalar walk over a child);
- the MRO registry resolves the MOST-specific class regardless of insertion
  order;
- an unhandled field calls the ``fallthrough_error_factory`` and raises.

A second section pins the scalar-table VALUE-shape factory
(``make_scalar_converter`` / ``make_kind_converter`` / ``finish_field_conversion``)
both write converters ride without merging their field-class key spaces.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from django import forms
from rest_framework import serializers

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.forms import converter as form_converter
from django_strawberry_framework.rest_framework import serializer_converter as ser_converter
from django_strawberry_framework.utils.converters import (
    convert_with_mro,
    finish_field_conversion,
    make_kind_converter,
    make_scalar_converter,
)
from django_strawberry_framework.utils.inputs import FILE, SCALAR, FieldConversionBase


class _Base:
    pass


class _Child(_Base):
    pass


def test_precheck_match_wins_over_registry():
    """An ``isinstance`` precheck match returns before the scalar registry walk runs.

    ``_Child`` subclasses ``_Base``; a precheck on ``_Base`` must win even though
    ``_Child`` is also in the registry (the more-specific kind detection precedes
    the walk - the relation/file/multi-choice ordering both flavors rely on).
    """
    field = _Child()
    result = convert_with_mro(
        field,
        isinstance_prechecks=[(_Base, lambda _f: "precheck-won")],
        scalar_registry={_Child: "registry-value"},
        fallthrough_error_factory=lambda _f: AssertionError("should not raise"),
    )
    assert result == "precheck-won"


def test_prechecks_run_in_order():
    """The FIRST matching precheck wins (ordered, not most-specific)."""
    field = _Child()
    result = convert_with_mro(
        field,
        isinstance_prechecks=[(_Child, lambda _f: "first"), (_Base, lambda _f: "second")],
        scalar_registry={},
        fallthrough_error_factory=lambda _f: AssertionError("should not raise"),
    )
    assert result == "first"


def test_precheck_returning_none_continues_to_walk():
    """A precheck handler returning ``None`` lets the skeleton continue to the registry walk.

    This is the bare-``forms.Field`` exact-type pattern: a precheck that matches by
    ``isinstance`` but returns ``None`` for the non-exact case falls through to the
    scalar walk rather than short-circuiting.
    """
    field = _Child()
    result = convert_with_mro(
        field,
        isinstance_prechecks=[(_Base, lambda _f: None)],
        scalar_registry={_Child: "registry-value"},
        fallthrough_error_factory=lambda _f: AssertionError("should not raise"),
    )
    assert result == "registry-value"


def test_mro_walk_resolves_most_specific_class():
    """The MRO walk resolves the field's OWN class before a registered parent.

    ``_Child`` and ``_Base`` are both registered; the walk visits ``_Child`` first
    (the field's own class), so it resolves to ``_Child``'s value regardless of
    insertion order (the ``FloatField`` / ``DecimalField`` non-collapse guarantee).
    """
    field = _Child()
    # Insert the parent FIRST to prove insertion order does not decide the winner.
    result = convert_with_mro(
        field,
        isinstance_prechecks=[],
        scalar_registry={_Base: "base-value", _Child: "child-value"},
        fallthrough_error_factory=lambda _f: AssertionError("should not raise"),
    )
    assert result == "child-value"


def test_mro_walk_resolves_unregistered_subclass_to_parent():
    """An UNregistered subclass resolves to its registered parent's value (the EmailField-under-CharField shape)."""
    field = _Child()
    result = convert_with_mro(
        field,
        isinstance_prechecks=[],
        scalar_registry={_Base: "base-value"},  # only the parent is registered
        fallthrough_error_factory=lambda _f: AssertionError("should not raise"),
    )
    assert result == "base-value"


def test_unhandled_field_raises_via_factory():
    """A field matched by neither path calls ``fallthrough_error_factory`` and raises it.

    The load-bearing no-catch-all contract: there is NO base-class fallback that
    silently coerces an unknown field; the factory's exception is raised.
    """

    class _Unrelated:
        pass

    def _factory(field):
        return ValueError(f"unsupported: {type(field).__name__}")

    with pytest.raises(ValueError, match="unsupported: _Unrelated"):
        convert_with_mro(
            _Unrelated(),
            isinstance_prechecks=[(_Base, lambda _f: "won't match")],
            scalar_registry={_Child: "won't match"},
            fallthrough_error_factory=_factory,
        )


def test_mro_walk_bypasses_hostile_field_metaclass_attribute_access():
    """A hostile ``__getattribute__`` cannot replace typed converter failure."""

    class HostileMeta(type):
        def __getattribute__(cls, name):
            if name == "__mro__":
                raise RuntimeError("mro descriptor failed")
            return super().__getattribute__(name)

    class HostileFormField(forms.Field, metaclass=HostileMeta):
        pass

    class HostileSerializerField(serializers.Field, metaclass=HostileMeta):
        pass

    hostile_form = object.__new__(HostileFormField)
    hostile_serializer = object.__new__(HostileSerializerField)
    hostile_serializer.field_name = "hostile"

    with pytest.raises(ConfigurationError, match="Unsupported form field type"):
        form_converter.convert_form_field(hostile_form)
    with pytest.raises(ConfigurationError, match="Unsupported serializer field type"):
        ser_converter.convert_serializer_field(hostile_serializer)


def test_mro_walk_bypasses_hostile_field_metaclass_hashing():
    """A hostile class hash cannot abort the registry walk."""

    class HostileMeta(type):
        def __hash__(cls):
            raise RuntimeError("class hash failed")

    class HostileFormField(forms.Field, metaclass=HostileMeta):
        pass

    hostile_form = object.__new__(HostileFormField)
    with pytest.raises(ConfigurationError, match="Unsupported form field type"):
        form_converter.convert_form_field(hostile_form)


# ---------------------------------------------------------------------------
# Scalar-table VALUE shape (make_scalar_converter / finish_field_conversion)
# ---------------------------------------------------------------------------


class _Conv(FieldConversionBase):
    __slots__ = ()


def test_make_scalar_converter_defaults_to_field_required():
    """Omitted ``required_of`` reads ``field.required`` (the serializer default)."""
    convert = make_scalar_converter(_Conv, str)
    result = convert(SimpleNamespace(required=True))
    assert isinstance(result, _Conv)
    assert result.annotation is str
    assert result.kind == SCALAR
    assert result.required is True


def test_make_scalar_converter_uses_required_of_when_given():
    """``required_of`` is the form NullBoolean seam: it wins over ``field.required``."""
    convert = make_scalar_converter(_Conv, bool | None, required_of=lambda _f: False)
    result = convert(SimpleNamespace(required=True))
    assert result.annotation == (bool | None)
    assert result.kind == SCALAR
    assert result.required is False


def test_make_kind_converter_emits_fixed_kind_and_annotation():
    """Kind prechecks (file / multi-choice) share the same closure as scalar rows."""
    convert = make_kind_converter(_Conv, FILE)
    result = convert(SimpleNamespace(required=False))
    assert result.annotation is None
    assert result.kind == FILE
    assert result.required is False

    listed = make_kind_converter(_Conv, SCALAR, annotation=list[str])
    listed_result = listed(SimpleNamespace(required=True))
    assert listed_result.annotation == list[str]
    assert listed_result.kind == SCALAR


def test_finish_field_conversion_returns_instance_or_invokes_callable():
    """Precheck hits are instances; registry hits are callables that still need ``field``."""
    inst = _Conv(annotation=str, required=True)
    assert finish_field_conversion(inst, object()) is inst

    called: list[object] = []

    def _convert(field: object) -> _Conv:
        called.append(field)
        return inst

    sentinel = object()
    assert finish_field_conversion(_convert, sentinel) is inst
    assert called == [sentinel]


def test_form_and_serializer_scalar_tables_ride_make_scalar_converter():
    """Both write-flavor CharField rows are ``make_scalar_converter`` closures.

    The KEY spaces stay separate (``forms.CharField`` vs
    ``serializers.CharField``); the VALUE shape is the one factory, so a
    requiredness / annotation-construction fix lands once.
    """
    shared = make_scalar_converter(FieldConversionBase, str).__code__
    assert form_converter._SCALAR_FORM_FIELDS[forms.CharField].__code__ is shared
    assert ser_converter._BUILTIN_SCALAR_CONVERTERS[serializers.CharField].__code__ is shared

    form_hit = form_converter._SCALAR_FORM_FIELDS[forms.CharField](forms.CharField(required=True))
    ser_hit = ser_converter._BUILTIN_SCALAR_CONVERTERS[serializers.CharField](
        serializers.CharField(),
    )
    assert isinstance(form_hit, form_converter.FormFieldConversion)
    assert isinstance(ser_hit, ser_converter.SerializerFieldConversion)
    assert form_hit.annotation is str
    assert ser_hit.annotation is str
    assert form_hit.kind == ser_hit.kind == SCALAR


def test_form_and_serializer_file_prechecks_ride_make_kind_converter():
    """File-kind prechecks on both flavors are ``make_kind_converter`` closures."""
    shared = make_kind_converter(FieldConversionBase, FILE).__code__
    assert form_converter._CONVERT_FILE.__code__ is shared
    assert ser_converter._CONVERT_FILE.__code__ is shared
    assert (
        form_converter._CONVERT_FILE.__code__
        is make_scalar_converter(
            FieldConversionBase,
            str,
        ).__code__
    )
