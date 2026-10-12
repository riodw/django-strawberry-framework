"""Shared builders for the optimizer test package.

One home for the ``NestedConnectionRequest`` builder both strategy test modules
(``test_nested_fetch.py`` / ``test_lateral_fetch.py``) parameterize: a new field
on the request dataclass then touches this one builder instead of per-module
copies. ``filter_prefetch_queryset`` is Django's own prefetch filter, which the
lateral and single-parent strategy modules apply to a planned queryset.
"""

import dataclasses
from collections.abc import Sequence
from typing import TypeVar

from django.db import models
from django.db.models.fields import related_descriptors

from django_strawberry_framework.optimizer.join_taxonomy import classify_relation_join
from django_strawberry_framework.optimizer.nested_fetch import NestedConnectionRequest

_QuerySetT = TypeVar("_QuerySetT", bound="models.QuerySet[models.Model, object]")


def filter_prefetch_queryset(
    queryset: _QuerySetT,
    field_name: str,
    instances: Sequence[models.Model],
) -> _QuerySetT:
    """Django's own prefetch filter: ``queryset`` narrowed to the rows of ``instances``."""
    # basedpyright: django-stubs omits _filter_prefetch_queryset from
    # django.db.models.fields.related_descriptors, where Django defines it
    filtered = related_descriptors._filter_prefetch_queryset(queryset, field_name, instances)  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(filtered, type(queryset))
    return filtered


def nested_connection_request(
    field_owner: type[models.Model],
    field_name: str,
    **overrides: object,
) -> NestedConnectionRequest:
    """A minimal valid ``NestedConnectionRequest`` for one relation field.

    Defaults mirror what the walker would hand a strategy for a bare
    ``first: 2`` nested connection over ``field_owner.<field_name>``: the
    related model's plain queryset, the relation's real join descriptor, a
    ``pk`` deterministic order, and the ``_dst_<field>_connection`` attach
    contract. Any field is overridable per test via ``overrides``.
    """
    field = field_owner._meta.get_field(field_name)
    assert isinstance(field, models.Field | models.ForeignObjectRel)
    child_model = field.related_model
    assert isinstance(child_model, type)
    default = NestedConnectionRequest(
        django_field=field,
        relation_field_name=field_name,
        prefix="",
        child_queryset=child_model._default_manager.all(),
        join=classify_relation_join(field),
        order_by=("pk",),
        offset=0,
        limit=2,
        reverse=False,
        with_total_count=True,
        to_attr=f"_dst_{field_name}_connection",
        lookup=field_name,
    )
    return dataclasses.replace(default, **overrides)
