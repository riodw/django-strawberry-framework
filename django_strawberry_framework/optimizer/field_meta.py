"""``FieldMeta`` — precomputed Django field metadata for the optimizer walker.

Built once per ``DjangoType`` at class-creation time (in
``__init_subclass__``) and stashed as ``cls._optimizer_field_map``.
The O2 walker reads the cached map instead of calling
``model._meta.get_fields()`` on every walk, eliminating per-request
Django introspection overhead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from django.db import models


@dataclass(frozen=True, slots=True)
class FieldMeta:
    """Lightweight snapshot of a Django field's optimizer-relevant attributes.

    Attributes:
        name: The Django field name (snake_case).
        is_relation: Whether the field is a relation.
        many_to_many: ``True`` for M2M fields.
        one_to_many: ``True`` for reverse FK fields.
        one_to_one: ``True`` for OneToOne fields (forward or reverse).
        related_model: The target model class for relations, or ``None``.
        attname: The DB column name (e.g., ``category_id`` for a FK).
            ``None`` for reverse relations and non-FK fields.
        target_field_name: The target model field name a FK points at,
            or ``None`` for non-FK fields.
        target_field_attname: The target model column attname a FK
            points at, preserving non-PK ``to_field`` connector rules.
        reverse_connector_attname: For reverse FK relations, the forward
            FK column on the related model that points back to the
            parent model.
        auto_created: ``True`` for reverse-side auto-created fields.
    """

    name: str
    is_relation: bool = False
    many_to_many: bool = False
    one_to_many: bool = False
    one_to_one: bool = False
    related_model: type[models.Model] | None = None
    attname: str | None = None
    target_field_name: str | None = None
    target_field_attname: str | None = None
    reverse_connector_attname: str | None = None
    auto_created: bool = False

    @classmethod
    def from_django_field(cls, field: object) -> FieldMeta:
        """Build a ``FieldMeta`` from a Django field object.

        ``field.name`` and ``field.is_relation`` are accessed directly
        because every Django ``Field`` / reverse-relation descriptor
        guarantees them; the rest are read with ``getattr`` defaults so
        forward fields, reverse relations, and the various M2M shapes
        all build cleanly without per-shape branching.
        """
        return cls(
            name=field.name,
            is_relation=bool(field.is_relation),
            many_to_many=bool(getattr(field, "many_to_many", False)),
            one_to_many=bool(getattr(field, "one_to_many", False)),
            one_to_one=bool(getattr(field, "one_to_one", False)),
            related_model=getattr(field, "related_model", None),
            attname=getattr(field, "attname", None),
            target_field_name=getattr(getattr(field, "target_field", None), "name", None),
            target_field_attname=getattr(getattr(field, "target_field", None), "attname", None),
            reverse_connector_attname=getattr(getattr(field, "field", None), "attname", None),
            auto_created=bool(getattr(field, "auto_created", False)),
        )
