"""Cross-cutting helpers shared by every subsystem - relation shapes, string casing, and type unwrapping.

Subpackage structure mirrors the convention both `graphene_django/utils/`
and `strawberry_django/utils/` converge on: focused submodules per
concern rather than a single 500-line `utils.py`. Includes, among others:

- ``relations`` - Django relation-shape classification
  (``relation_kind``, ``RelationKind``, ``is_many_side_relation_kind``).
- ``strings`` - case conversion (``snake_case``, ``pascal_case``).
- ``typing`` - Strawberry / Python / GraphQL type unwrapping
  (``unwrap_graphql_type``, ``unwrap_return_type``) plus ``is_async_callable``.
- ``connections`` - the connection window-bounds / sidecar-kwarg contracts.
- ``inputs`` / ``permissions`` - the generated-input and active-input
  permission substrates shared by the filter / order families.
- ``input_values`` - the neutral set-input traversal substrate
  (``iter_active_fields`` / ``is_inactive_value`` / ``iter_input_items``)
  the filter / order normalizers and the permission walkers all consume. It
  landed in the 0.0.9 DRY pass (``docs/feedback.md`` Major 1), single-siting the
  dict-vs-dataclass walk, the ``None`` / ``UNSET`` active-input rule, and the
  leaf / related / logic classification each surface previously spelled inline.
- ``querysets`` - the query-source + ``DjangoType.get_queryset`` visibility
  contract (``initial_queryset`` / ``normalize_query_source`` /
  ``apply_type_visibility_*`` / ``SyncMisuseError``). It landed in the 0.0.9
  DRY pass (``docs/feedback.md`` Major 1), consolidating the Manager-coercion
  and sync/async visibility routing each resolver surface previously spelled
  inline (so each subsystem no longer keeps its own).
"""

from .relations import RelationKind, is_many_side_relation_kind, relation_kind
from .strings import pascal_case, snake_case
from .typing import unwrap_graphql_type, unwrap_return_type

__all__ = (
    "RelationKind",
    "is_many_side_relation_kind",
    "pascal_case",
    "relation_kind",
    "snake_case",
    "unwrap_graphql_type",
    "unwrap_return_type",
)
