"""Pending relation records for definition-order-independent ``DjangoType`` finalization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import models

from ..utils.relations import RelationKind


@dataclass(frozen=True)
class PendingRelation:
    """Relation field whose target ``DjangoType`` was not registered during collection.

    Fields must remain hashable because ``TypeRegistry.discard_pending()`` builds
    ``set(resolved)`` when removing records after successful finalization.
    """

    source_type: type
    source_model: type[models.Model]
    field_name: str
    django_field: Any
    related_model: type[models.Model]
    relation_kind: RelationKind
    nullable: bool


class _PendingRelationAnnotationMeta(type):
    """Metaclass that gives the sentinel a useful schema-construction error repr."""

    def __repr__(cls) -> str:
        return (
            "<unfinalized DjangoType relation; call finalize_django_types() before constructing "
            "strawberry.Schema>"
        )


class PendingRelationAnnotation(metaclass=_PendingRelationAnnotationMeta):
    """Sentinel annotation rewritten before ``strawberry.type`` sees the class."""
