"""``FieldMeta`` — precomputed Django field metadata for the optimizer walker.

``FieldMeta`` is the canonical single source of truth for relation
shape across the package: ``is_relation``, cardinality flags
(``many_to_many`` / ``one_to_many`` / ``one_to_one``), ``attname``,
``related_model``, and the FK target columns. Every consumer of
"relation cardinality + nullable + attname" should read from a
``FieldMeta`` instance (via ``DjangoTypeDefinition.field_map`` or a
fresh ``FieldMeta.from_django_field(...)`` call) rather than
re-deriving the shape through raw ``getattr`` on a Django field
descriptor. Three sites currently re-derive the shape and carry
``TODO(spec-fieldmeta-ssot)`` cross-references back to this module:
``types/resolvers.py:_make_relation_resolver``,
``types/converters.py:resolved_relation_annotation``, and
``types/base.py:_record_pending_relation``. Migrating those readers
to ``FieldMeta`` is tracked as a folder-level DRY follow-up; the
anchors stay in place until the migration ships.

Built once per ``DjangoType`` at class-creation time (in
``__init_subclass__``) and stored canonically on
``DjangoTypeDefinition.field_map``. The legacy
``cls._optimizer_field_map`` mirror remains for the 0.0.x line while the
optimizer reads from the definition-backed metadata. The O2 walker reads
the cached map instead of calling ``model._meta.get_fields()`` on every
walk, eliminating per-request Django introspection overhead.

TODO(spec-fieldmeta-mirror-retirement): the ``cls._optimizer_field_map``
mirror written in ``django_strawberry_framework/types/base.py`` is
retained for the 0.0.x line for backward compatibility with the
walker's pre-definition reads; remove the mirror writer and this
docstring paragraph in the same change that ships the retirement
slice. The walker still reads ``cls._optimizer_field_map`` today
(``optimizer/walker.py:_resolve_field_map``); ``BACKLOG-014`` in
``KANBAN.md`` tracks the move to
``registry.get_definition(type_cls).field_map`` and enumerates the
five ``TODO(spec-fieldmeta-mirror-retirement)`` anchor sites that
close with it. The sibling ``TODO(spec-fieldmeta-ssot)`` family
(three reader sites that re-derive relation shape) is tracked under
``BACKLOG-013`` in the same file.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from django_strawberry_framework.exceptions import OptimizerError

if TYPE_CHECKING:  # pragma: no cover
    from django.db import models


@runtime_checkable
class _DjangoFieldLike(Protocol):
    """Structural contract for the inputs ``from_django_field`` accepts.

    Every Django ``Field`` and reverse-relation descriptor surfaced by
    ``Model._meta.get_field`` / ``Model._meta.get_fields`` guarantees
    ``name`` and ``is_relation``; the remaining attributes
    (``many_to_many``, ``attname``, ``target_field``, ``field``, ...)
    are read defensively with ``getattr`` defaults so the four documented
    input shapes (forward field, reverse FK, M2M, O2O) all build cleanly
    without per-shape branching.
    """

    name: str
    is_relation: bool


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
    def from_django_field(cls, field: _DjangoFieldLike) -> FieldMeta:
        """Build a ``FieldMeta`` from a Django field descriptor.

        ``field.name`` and ``field.is_relation`` are the two load-bearing
        attributes every Django ``Field`` / reverse-relation descriptor
        guarantees; the rest are read with ``getattr`` defaults so
        forward fields, reverse relations, and the various M2M shapes
        all build cleanly without per-shape branching.

        Raises:
            OptimizerError: if ``field`` does not expose the two
                required attributes ``name`` and ``is_relation``. The
                explicit guard converts an otherwise late
                ``AttributeError`` deep inside the optimizer walker
                into a typed, call-site failure naming the bad input.
        """
        if not hasattr(field, "name") or not hasattr(field, "is_relation"):
            raise OptimizerError(
                f"FieldMeta.from_django_field expected a Django field descriptor "
                f"exposing 'name' and 'is_relation'; got {field!r}",
            )
        # Read ``target_field`` once — it is consulted twice below to
        # extract both ``name`` and ``attname``.
        target_field = getattr(field, "target_field", None)
        return cls(
            name=field.name,
            is_relation=bool(field.is_relation),
            many_to_many=bool(getattr(field, "many_to_many", False)),
            one_to_many=bool(getattr(field, "one_to_many", False)),
            one_to_one=bool(getattr(field, "one_to_one", False)),
            related_model=getattr(field, "related_model", None),
            attname=getattr(field, "attname", None),
            target_field_name=getattr(target_field, "name", None),
            target_field_attname=getattr(target_field, "attname", None),
            reverse_connector_attname=getattr(getattr(field, "field", None), "attname", None),
            auto_created=bool(getattr(field, "auto_created", False)),
        )
