"""Pending relation records for definition-order-independent ``DjangoType`` finalization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import models

from ..utils.relations import RelationKind


@dataclass(frozen=True)
class PendingRelation:
    """Relation field whose target ``DjangoType`` was not registered during collection."""

    source_type: type
    source_model: type[models.Model]
    field_name: str
    django_field: Any
    related_model: type[models.Model]
    relation_kind: RelationKind
    nullable: bool


class PendingRelationAnnotation:
    """Sentinel annotation rewritten before ``strawberry.type`` sees the class."""
