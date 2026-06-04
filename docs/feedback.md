# Feedback

The order-test relocation is complete at the same-or-stronger contract level.

- `tests/orders` coverage was removed only where a real fakeshop `/graphql/` test now
  exercises the public behavior more directly.
- Live coverage now includes nested order permission through products, all NULLS ordering
  directions through library row order, and `fields="__all__"` order-input shape through
  kanban schema introspection.
- The remaining `tests/orders` cases are intentionally package-internal: async behavior,
  factory/materialization/finalizer lifecycle, request-shape errors, cache state, and
  permission dedup counts.

Unrelated dirty files remain outside this feedback item.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
