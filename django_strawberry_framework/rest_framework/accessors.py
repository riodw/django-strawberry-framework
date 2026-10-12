"""Typed reads of the DRF attributes djangorestframework-stubs declares with bare generics.

djangorestframework-stubs spells ``Serializer.fields`` (a ``BindingDict`` over a
bare ``Field``), ``Serializer._declared_fields``, ``Serializer.get_fields()``,
``ManyRelatedField.child_relation``, ``ListField.child`` and ``Serializer.errors``
(a bare ``ReturnDict``) with
unparametrized generics, so every direct read is partially Unknown to the type
checker. Each read is spelled here once, under the all-``Any`` parametrization the
package's ``DRFField`` alias already uses (DRF's stub generics are invariant, so it
is the one form every field takes), and the package and its tests go through these
functions instead of the attribute.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework import serializers

if TYPE_CHECKING:
    from collections.abc import Mapping

    from typing_extensions import TypeIs

    from .serializer_converter import DRFField, DRFRelatedField, DRFSerializer

__all__ = (
    "base_fields",
    "bound_fields",
    "child_relation_of",
    "declared_fields_of",
    "is_drf_field",
    "is_serializer",
    "list_child_of",
    "serializer_errors",
)


def bound_fields(serializer: DRFSerializer) -> Mapping[str, DRFField]:
    """Return ``serializer.fields``: the serializer's bound fields, by field name."""
    return serializer.fields


def declared_fields_of(serializer_class: type[DRFSerializer]) -> Mapping[str, DRFField]:
    """Return ``serializer_class._declared_fields``: the fields its class body declares."""
    # basedpyright: drf-stubs types ``_declared_fields`` as ``dict[str, Field]`` over the bare
    # generic ``Field``, so the read is partially Unknown
    return serializer_class._declared_fields  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]


def base_fields(parent: DRFSerializer) -> dict[str, DRFField]:
    """Return ``parent.get_fields()``: the fields a ``get_fields`` override extends.

    A ``get_fields`` override passes ``super()``, so the returned dict is the one the
    next class in the MRO builds, fresh per call, which the override may add to or
    drop from.
    """
    # basedpyright: drf-stubs types ``Serializer.get_fields`` as ``dict[str, Field]`` over the
    # bare generic ``Field``, so the read is partially Unknown
    return parent.get_fields()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]


def child_relation_of(field: serializers.ManyRelatedField) -> DRFRelatedField:
    """Return ``field.child_relation``: the single relation a ``many=True`` field wraps."""
    # basedpyright: drf-stubs types ``child_relation`` as the bare generic ``RelatedField``
    return field.child_relation  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]


def list_child_of(field: serializers.ListField) -> DRFField:
    """Return ``field.child``: the field each element of a ``ListField`` is validated by."""
    # basedpyright: drf-stubs types ``ListField.child`` as the bare generic ``Field``
    return field.child  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]


def serializer_errors(serializer: DRFSerializer) -> object:
    """Return ``serializer.errors``: DRF's nested error tree, read as the ``object`` it is walked as."""
    # basedpyright: drf-stubs types ``Serializer.errors`` as the bare ``ReturnDict``
    return serializer.errors  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]


def is_serializer(value: object) -> TypeIs[DRFSerializer]:
    """Return whether ``value`` is a DRF ``serializers.Serializer`` (its class declares fields)."""
    return isinstance(value, serializers.Serializer)


def is_drf_field(value: object) -> TypeIs[DRFField]:
    """Return whether ``value`` is a DRF ``serializers.Field`` (any serializer or field)."""
    return isinstance(value, serializers.Field)
