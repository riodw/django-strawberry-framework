# DRY review: `django_strawberry_framework/filters/factories.py`

Status: verified

ITEM_BASELINE: `d398c8dc4a977bc0969607de907908f36c52240a`

## System trace

`filters/factories.py` owns two layers of the filter pipeline, with sharply
different consumption status:

1. **Layer 5 — `FilterArgumentsFactory`.** Thin family subclass of
   `utils/inputs.py::GeneratedInputArgumentsFactory`. Supplies the seven
   family hook attrs (`input_object_types`, `_type_filterset_registry`,
   `_collision_registry_attr`, labels, related-attr names) plus
   `_build_input_triples`, which concatenates
   `filters/inputs.py::_build_input_fields` with
   `filters/inputs.py::_build_logic_fields` (`and_` / `or_` / `not_`). BFS
   walk, collision check, idempotent cache, and subclass-rejection guard live
   in the shared base — not here.

2. **Layer 6 — dynamic-FilterSet cache.** `_dynamic_filterset_cache`,
   `_RESERVED_FACTORY_KEYS`, `_make_hashable`, `_normalize_meta_for_factory`,
   `_make_cache_key`, `_create_dynamic_filterset_class`, and
   `get_filterset_class`. Builds a synthetic `FilterSet` from a Meta-shaped
   dict when no explicit class is supplied, collapsing equivalent meta onto
   one generated class (duplicate-`__name__` collision break-glass). **No
   production caller:** `connection.py::DjangoConnectionField` reads the
   already-resolved `Meta.filterset_class` sidecar; auto-generation from
   `Meta.fields` remains a standing deferred Non-goal (spec-027). Surface is
   build-and-test-only (`tests/filters/test_factories.py`).

**Callers / lifecycle.** Finalizer phase 2.5
(`types/finalizer.py::_bind_filtersets` subpass 4) constructs
`FilterArgumentsFactory(filterset_cls).arguments` and materializes
`input_object_types` via `filters/inputs.py::materialize_input_class`.
`filters/inputs.py::clear_filter_input_namespace` (registered
`register_subsystem_clear(owner="filters.input_namespace")`) clears the BFS
caches through `utils/inputs.py::clear_generated_input_namespace`. The
Layer-6 dict has **no** `registry.clear()` hook by documented design (keys
embed model identity; stale entries after model rebuild are test-isolation
only). Test autouse fixtures clear `_dynamic_filterset_cache` explicitly.

**Sibling.** `orders/factories.py::OrderArgumentsFactory` is the Layer-5
twin (same base, no operator bag — Spec Decision 8). Orders Layer 6 is a
TODO-anchored deferred non-goal: symbols `_dynamic_orderset_cache` /
`get_orderset_class` are reserved in comments only — **no implementation**.

**Live path.** Explicit-`filterset_class` GraphQL queries
(`examples/fakeshop/test_query/` library/products filter suites) exercise
Layer 5 through finalize → factory → materialized inputs. Layer 6 cannot
earn a live `/graphql` line until a consumer exists.

## Verification

- Item-scoped diff vs baseline was empty before this pass
  (`git diff d398c8dc4a977bc0969607de907908f36c52240a -- django_strawberry_framework/filters/factories.py`).
  Concurrent dirty paths under `filters/` and elsewhere left untouched.
- Confirmed `FilterArgumentsFactory` / `OrderArgumentsFactory` are already
  parameterizations of one BFS owner in `utils/inputs.py`; folding the
  `_build_input_triples` hooks would erase the filter-only operator bag
  (Spec Decision 8) or force a mode flag.
- Package-wide search: `_make_hashable` / `_make_cache_key` /
  `get_filterset_class` / `_dynamic_filterset_cache` appear only in this
  module (+ tests + the orders TODO comment naming the reserved twin).
  No second concrete Layer-6 implementation exists.
- Compared `_make_hashable` to
  `optimizer/extension.py::_hashable_variable_value` /
  `_freeze_variable_value`: both use `repr`-sorted unordered containers, but
  contracts diverge — Meta cache identity (preserve list/tuple order, no type
  tags, no opaque/cycle tokens) vs GraphQL variable plan-cache identity
  (tagged scalars/containers, opaque fallback, cycle detection). Different
  reasons to change; must not share a helper.
- Compared `_normalize_meta_for_factory`'s `filter_fields` handling to
  `filters/sets.py::FilterSetMetaclass.__new__`: metaclass promotes the
  synonym onto a class `Meta` when `fields` is absent; factory must
  canonicalize a **dict** before cache keying (promote or drop so the alias
  cannot split a cache slot via extras). Same alias name, different surfaces
  and failure modes — factory path cannot defer to the metaclass alone.
- Confirmed Layer-6 cache has no clear hook while BFS caches do: documented
  accepted lifecycle (M-filters-3), not an accidental second policy. Adding a
  clear now would be lifecycle polish for an unconsumed surface, not a DRY
  consolidation with a twin owner.
- Confirmed `_normalize_meta_for_factory` vs `_make_cache_key` set/frozenset
  branches overlap as intentional defense-in-depth (`_make_cache_key` is also
  called directly from tests without normalize).
- No `get_filterset_class` / `AutoFilter` usage under `examples/`.

## Opportunities

None — Layer 5 is already single-sited at
`utils/inputs.py::GeneratedInputArgumentsFactory`; this file correctly owns
only filter-family hooks and the (sole, unconsumed) Layer-6 dynamic-FilterSet
cache. The strongest near-duplicate — model-keyed Meta hashing
(`_make_hashable` / `_make_cache_key`) — has no twin implementation yet
(`orders/factories.py` still defers Layer 6). Extracting hashing into
`utils/inputs.py` from a single concrete site would be speculative
abstraction. Trace that candidate for the `filters/` folder pass and the
project pass; consolidate only when orders ships a real
`get_orderset_class` + `_dynamic_orderset_cache`, or when a card makes this
file the mandated shared owner ahead of that twin.

## Judgment

Zero-edit. The file's live responsibility (BFS family hooks) is already
DRY against the shared base; its deferred responsibility (Layer-6 cache) is
the only concrete implementation of that shape in the package. Cross-family
cache-hashing consolidation is evidence for later integration passes, not a
change warranted from this file alone. Ready for Worker 2.

## Implementation (Worker 1)

No source changes. Item-scoped diff against
`d398c8dc4a977bc0969607de907908f36c52240a` for
`django_strawberry_framework/filters/factories.py` remains empty (re-checked
after writing this artifact). Only new path for this item is this artifact.

**Strongest rejected / deferred**

- **Extract `_make_hashable` / `_make_cache_key` to `utils/inputs.py` now.**
  Rejected: one concrete site; orders Layer 6 unshipped; premature shared
  owner. Defer-with-trigger: when `orders/factories.py` gains a real
  `get_orderset_class` + `_dynamic_orderset_cache`, or folder/project pass
  mandates a shared helper with both consumers in hand.
- **Merge `FilterArgumentsFactory._build_input_triples` with the order
  twin.** Rejected: operator bag is genuine Spec Decision 8 divergence;
  mode-flagged shared hook would obscure ownership.
- **Merge `_make_hashable` with optimizer variable freezing.** Rejected:
  different cache-identity contracts (Meta vs GraphQL variables).
- **Wire `_dynamic_filterset_cache.clear()` into
  `clear_filter_input_namespace`.** Rejected as DRY work: documented
  intentional no-hook; no production consumer; not duplicated policy with a
  second site that clears differently. Lifecycle nicety for a future
  consumer, not this review's consolidation.
- **Deduplicate `filter_fields` alias with `FilterSetMetaclass`.** Rejected:
  class-Meta promotion vs dict cache-key canonicalization are distinct
  contracts; factory strip-when-both-present is required for cache collapse.

**Tests.** None added — behavior unchanged. Layer 5 already covered by
package `tests/filters/test_factories.py` and live filter queries under
`examples/fakeshop/test_query/`. Layer 6 remains package-test-only (no
earnable live GraphQL path). `ruff format` / `ruff check --fix` not run —
no production or test edits. No changelog. Plan checkbox left untouched
(Worker 2 closes the item). Status `fix-implemented` as a proved zero-edit
handoff.

**Blockers:** none.

## Independent verification (Worker 2)

Re-traced `filters/factories.py` end-to-end: Layer-5
`FilterArgumentsFactory` hooks → `utils/inputs.py::GeneratedInputArgumentsFactory`
BFS; Layer-6 `get_filterset_class` / `_dynamic_filterset_cache` / hashing;
`types/finalizer.py::_bind_filtersets` subpass 4; `connection.py` reading
`Meta.filterset_class` (never `get_filterset_class`); orders twin
(`orders/factories.py` Layer-5 live, Layer-6 TODO-only); optimizer
`_freeze_variable_value`; `FilterSetMetaclass` `filter_fields` promotion;
package + test importers of Layer-6 symbols.

**Scoped diff.** Empty vs `ITEM_BASELINE`
`d398c8dc4a977bc0969607de907908f36c52240a` for
`django_strawberry_framework/filters/factories.py` (re-confirmed).

**Layer-6 cache-hashing deferral (challenged).** Extracting
`_make_hashable` / `_make_cache_key` to `utils/inputs.py` now still fails
the consolidate-when-sites-share-contract test: package search finds one
concrete Layer-6 implementation; `orders/factories.py` only reserves
`_dynamic_orderset_cache` / `get_orderset_class` in a standing deferred
non-goal comment. A shared owner with a single consumer would be
speculative abstraction. Defer-with-trigger stands — folder/project pass
or a real orders Layer-6 ship. Not revision-needed.

**Rejected candidates (re-checked).**

- Merge `_build_input_triples` with `OrderArgumentsFactory`: still wrong —
  filter operator bag vs Spec Decision 8 no-bag is genuine divergence.
- Merge `_make_hashable` with optimizer variable freezing: still wrong —
  Meta identity (order-preserving seq, untagged leaves) vs tagged
  scalars/containers + opaque/cycle tokens; different change axes.
- Wire `_dynamic_filterset_cache.clear()` into
  `clear_filter_input_namespace`: still not DRY work — documented
  intentional no-hook; no second clear-policy site; unconsumed surface.
- Deduplicate `filter_fields` with `FilterSetMetaclass`: still wrong —
  class-Meta promote-when-absent vs dict canonicalize-for-cache (including
  drop-when-both-present) are distinct surfaces.

**Missed opportunities searched.** No second production `get_filterset_class`
/ `AutoFilter` / `_dynamic_filterset_cache` path; not in public
`filters/__init__` re-exports; no `examples/` consumer; other
`key=repr` / cache-key sites (`mutations`/`forms`/`rest_framework` shape
caches, `write_transaction` walk) key different domains. Normalize vs
`_make_cache_key` set branches remain defense-in-depth plus Meta order
stability for `type(...)` generation — not a mergeable twin owner.

**Disposition.** Zero-edit judgment holds. Status → `verified`. Plan item
checked. No production edits. No commit. Blockers: none.
