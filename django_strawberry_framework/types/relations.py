"""Pending relation records for definition-order-independent ``DjangoType`` finalization.

``_build_annotations`` (``types/base.py::_build_annotations``) records a ``PendingRelation``
for every auto-synthesized relation field and installs ``PendingRelationAnnotation`` as its
annotation, whether or not the target ``DjangoType`` is registered yet, so the relation binds
to the target model's primary type whatever order the types are declared in.
``finalize_django_types`` (``types/finalizer.py::finalize_django_types``) replaces each
sentinel with ``resolved_relation_annotation`` and hands the resolved records back to
``TypeRegistry.discard_pending``.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.db import models


@dataclass(frozen=True, eq=False)
class PendingRelation:
    """Auto-synthesized relation field awaiting its target ``DjangoType`` at finalization.

    Constructed by ``_build_annotations`` (``types/base.py::_build_annotations``) for every
    auto-synthesized relation field, registered target or not; resolved by
    ``finalize_django_types`` (``types/finalizer.py::finalize_django_types``) after every
    ``DjangoType`` has registered.

    Records compare and hash by identity (``eq=False``): two records built from the same
    values stay distinct, a record hashes whatever ``django_field`` holds, and
    ``TypeRegistry.discard_pending()`` removes exactly the instances finalization hands back.

    ``field_name`` is the raw Django ``field.name`` as stored on the model, the same string
    that keys ``DjangoTypeDefinition.field_map``; finalization reads the relation's
    ``FieldMeta`` (cardinality, nullability) from that map, so the record carries none of it.
    """

    source_type: type
    source_model: type[models.Model]
    field_name: str
    django_field: models.Field | models.ForeignObjectRel
    related_model: type[models.Model]


class _PendingRelationAnnotationMeta(type):
    """Metaclass that gives the sentinel a useful schema-construction error repr."""

    def __repr__(cls) -> str:
        return (
            "<unfinalized DjangoType relation; call finalize_django_types() before constructing "
            "strawberry.Schema>"
        )


class PendingRelationAnnotation(metaclass=_PendingRelationAnnotationMeta):
    """Sentinel annotation ``finalize_django_types()`` replaces before ``strawberry.type`` runs.

    Strawberry meets it only when a ``DjangoType`` is decorated with ``strawberry.type`` before
    finalization ran; ``_PendingRelationAnnotationMeta`` then makes the schema-construction
    ``TypeError`` name the missing ``finalize_django_types()`` call instead of printing
    ``<class '...PendingRelationAnnotation'>``.
    """
