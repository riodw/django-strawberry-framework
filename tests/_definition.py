"""Real ``DjangoTypeDefinition`` records built directly, without declaring or registering a type.

A package seam that takes a ``DjangoTypeDefinition`` reads a few of its slots. ``make_definition``
constructs the dataclass itself over a real model, the empty selection a type with no fields
carries, and only the slots a test varies, so the test hands the seam the real record without
touching the type registry. A test that needs registry-resolved relations or a finalized type
declares a real ``DjangoType`` instead.
"""

from django.db import models

from django_strawberry_framework import DjangoType
from django_strawberry_framework.types.definition import DjangoTypeDefinition


def make_definition(
    model: type[models.Model],
    *,
    origin: type[DjangoType] = DjangoType,
    name: str | None = None,
    cursor_field: tuple[str, ...] | None = None,
    relation_connections: dict[str, str] | None = None,
) -> DjangoTypeDefinition:
    """Build the definition ``origin`` would carry over ``model``, with the given slots set."""
    return DjangoTypeDefinition(
        origin=origin,
        model=model,
        name=name,
        description=None,
        fields_spec=None,
        exclude_spec=None,
        selected_fields=(),
        field_map={},
        optimizer_hints={},
        has_custom_get_queryset=False,
        cursor_field=cursor_field,
        relation_connections=relation_connections,
    )
