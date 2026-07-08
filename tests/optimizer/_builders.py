"""Shared builders for the optimizer test package.

One home for the ``NestedConnectionRequest`` builder both strategy test modules
(``test_nested_fetch.py`` / ``test_lateral_fetch.py``) parameterize: a new field
on the request dataclass then touches this one builder instead of per-module
copies.
"""

from typing import Any

from django_strawberry_framework.optimizer.join_taxonomy import classify_relation_join
from django_strawberry_framework.optimizer.nested_fetch import NestedConnectionRequest


def nested_connection_request(
    field_owner: type,
    field_name: str,
    **overrides: Any,
) -> NestedConnectionRequest:
    """A minimal valid ``NestedConnectionRequest`` for one relation field.

    Defaults mirror what the walker would hand a strategy for a bare
    ``first: 2`` nested connection over ``field_owner.<field_name>``: the
    related model's plain queryset, the relation's real join descriptor, a
    ``pk`` deterministic order, and the ``_dst_<field>_connection`` attach
    contract. Any field is overridable per test via ``overrides``.
    """
    field = field_owner._meta.get_field(field_name)
    child_model = field.related_model
    values: dict[str, Any] = {
        "django_field": field,
        "relation_field_name": field_name,
        "prefix": "",
        "child_queryset": child_model.objects.all(),
        "join": classify_relation_join(field),
        "order_by": ("pk",),
        "offset": 0,
        "limit": 2,
        "reverse": False,
        "with_total_count": True,
        "to_attr": f"_dst_{field_name}_connection",
        "lookup": field_name,
    }
    values.update(overrides)
    return NestedConnectionRequest(**values)
