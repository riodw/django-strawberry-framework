# DRY review: `django_strawberry_framework/orders/base.py`

Status: verified

## System trace

`orders/base.py` owns one consumer-facing primitive: `RelatedOrder`, the
nested-path ordering declaration (spec-028 Layer 2). It stores a possibly-lazy
target orderset (`_orderset`), an optional ORM `field_name`, and exposes
family-named bind / resolve surfaces (`bind_orderset`, `.orderset` get/set).

Owner-bind and lazy target resolution are not re-implemented here. The class
inherits `sets_mixins.py::RelatedSetTargetMixin` (itself on
`LazyRelatedClassMixin`), parameterizes `_target_attr="_orderset"` /
`_owner_attr="bound_orderset"`, and keeps thin wrappers over `_bind_owner` /
`_resolved_target` / `_set_target`. Import is sibling from the neutral
`sets_mixins` module (spec-028 H1) — never through `filters.base`.

Callers and connected sites examined:

- `orders/sets.py::OrderSetMetaclass` collects via
  `collect_related_declarations(..., declaration_type=RelatedOrder,
  collection_attr="related_orders", inherit_from_bases=True)`; the collector
  binds with `_bind_owner` (not the public `bind_orderset` name).
- `orders/sets.py::OrderSet` expansion / apply walks `related_orders` and
  `RelatedOrder.field_name` / `.orderset` for nested order paths and
  permission double-dispatch.
- `orders/inputs.py` / factories use `field_name or top_name` for related
  source paths; `orders/__init__.py` re-exports `RelatedOrder`.
- Twin: `filters/base.py::RelatedFilter` — same mixin slots under
  `("_filterset", "bound_filterset")`, plus `ModelChoiceFilter` inheritance,
  `lookups=` rejection, and `get_queryset` auto-derive. No third
  `Related*` production class exists yet (`RelatedAggregate` is glossary /
  KANBAN only).
- Tests: `tests/orders/test_base.py` (class / absolute / unqualified targets,
  bind idempotency, mixin home in `sets_mixins`, setter); composition tests
  pin `LazyRelatedClassMixin` object identity across filter and order.
- Live usage: fakeshop library `RelatedOrder` branches in
  `examples/fakeshop/test_query/test_library_api.py`.

Item-scoped baseline diff
(`58f488ae6213eba4be6f175a5eb1ebef7b536d35` →
`django_strawberry_framework/orders/base.py`) was empty before and after this
pass. No production or test edits.

## Verification

- Re-read `RelatedOrder` against `RelatedFilter` and `RelatedSetTargetMixin`
  side by side. Bind idempotency, lazy resolve + re-store, and target setter
  are single-sited on the mixin; each family only supplies attr names and
  public method/property names.
- Grepped package-wide for `RelatedOrder` / `bind_orderset` / `_bind_owner` /
  `RelatedSetTargetMixin` / parallel `class Related*` definitions. Only the
  two family wrappers inherit the mixin; metaclass collection already uses
  the shared `collect_related_declarations` owner.
- Disproved further extraction of `bind_*` / `.*set` into the mixin via
  name-parameterized descriptors or dynamic method injection: that would hide
  the cookbook public surface behind mode flags and couple independent
  GraphQL argument names (`filterset` vs `orderset`) without a second
  behavioral owner.
- Disproved sharing `__init__` / `field_name` with `RelatedFilter`: order is
  a plain declaration object; filter is a `ModelChoiceFilter` with queryset /
  form / `lookups=` contracts. `field_name` on the order side is a simple
  optional slot; on the filter side it comes from django-filter. Same English
  name, different ownership.
- Disproved importing `LazyRelatedClassMixin` through `filters.base` for
  “one import path”: that re-couples Layer-3 packages and contradicts
  spec-028 H1 / the existing `test_related_order_imports_lazy_mixin_from_sets_mixins_not_filters_base` pin.
- Rejected lifting RelatedFilter’s long silent-no-op / unqualified-string
  caveat prose onto `RelatedOrder` as a DRY fix: documentation parity is not
  duplicated code responsibility; mixin docstring already states the shared
  bind/resolve contract.
- Confirmed no AggregateSet / FieldSet related-declaration fork has landed
  that would re-copy this file’s body.

## Opportunities

None — the only cross-family responsibility this file once shared with
`RelatedFilter` (idempotent owner bind + lazy target resolve) already lives
on `sets_mixins.py::RelatedSetTargetMixin`. Remaining lines are the
order-family public surface (`RelatedOrder`, `bind_orderset`, `.orderset`,
`field_name`) and intentional divergence from the filter twin
(`ModelChoiceFilter` / queryset / `lookups=`). Further packaging of family
wrappers is a folder/project concern for a future third set family, not a
second owner inside `orders/base.py`.

## Judgment

Zero-edit. `orders/base.py` is already the thin family wrapper the prior
sets_mixins consolidation intended. Strongest rejected candidate: collapsing
`RelatedOrder` / `RelatedFilter` public wrappers further into the mixin —
same contract axis already owned; remaining differences are family API and
filter-only ModelChoice behavior. Ready for Worker 2.

## Independent verification (Worker 2)

Scoped diff
`58f488ae6213eba4be6f175a5eb1ebef7b536d35` →
`django_strawberry_framework/orders/base.py` is empty (confirmed).

Re-traced `RelatedOrder` against `sets_mixins.py::RelatedSetTargetMixin` and
`filters/base.py::RelatedFilter`. Bind idempotency, lazy resolve + re-store,
and target setter are single-sited on the mixin; this file only parameterizes
`("_orderset", "bound_orderset")` and exposes `bind_orderset` / `.orderset`.
Metaclass collection calls `_bind_owner` via `collect_related_declarations`;
inputs/factories consume `.orderset` / `field_name` without re-implementing
resolve. Package grep shows only the two family wrappers inherit the mixin;
`RelatedAggregate` remains glossary/KANBAN only.

Challenges to rejected candidates (all held):

- Further folding `bind_*` / `.*set` into the mixin (descriptors /
  `__init_subclass__` injection): would hide the cookbook public names and
  couple independent GraphQL argument vocabularies without a second behavioral
  owner. Prior project-pass forward (dry-0_0_11) already owns any future
  third-family packaging; not an `orders/base.py` edit.
- Sharing `__init__` / `field_name` with `RelatedFilter`: order is a plain
  declaration; filter is `ModelChoiceFilter` with queryset / form / `lookups=`
  contracts. Same English name, different ownership.
- Importing `LazyRelatedClassMixin` through `filters.base`: contradicts
  spec-028 H1 and `test_related_order_imports_lazy_mixin_from_sets_mixins_not_filters_base`.
- Lifting RelatedFilter’s silent-no-op / unqualified-string caveat prose onto
  `RelatedOrder`: that caveat documents mixin behavior that already applies
  here; copying docs is not duplicated code responsibility.
- Disposed (out of this file’s scope): `OrderSetMetaclass` docstring still says
  bind “via `bind_orderset`” while the collector calls `_bind_owner` — wording
  drift in `orders/sets.py`, not residual duplication in `orders/base.py`.

Missed consolidation search: none found. Zero-edit judgment stands.
