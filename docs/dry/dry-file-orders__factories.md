# DRY review: `django_strawberry_framework/orders/factories.py`

Status: verified

## System trace

`orders/factories.py` owns Layer 5 of the orders input pipeline only: the
thin `OrderArgumentsFactory` parameterization of
`utils/inputs.py::GeneratedInputArgumentsFactory`. The subclass supplies
order-family class caches (`input_object_types`, `_type_orderset_registry`),
family hook attrs (`_collision_registry_attr`, labels, related-order attr
names), and `_build_input_triples` → `orders/inputs.py::_build_input_fields`
(no `and_` / `or_` / `not_` bag; Spec Decision 8).

Build-only. Materialization is finalizer phase 2.5 /
`orders/inputs.py::materialize_input_class`. Cache clear is
`orders/inputs.py::clear_order_input_namespace` →
`utils/inputs.py::clear_generated_input_namespace` (registered on
`registry.clear`). Callers: `types/finalizer.py` (phase 2.5 BFS trigger),
package tests under `tests/orders/`, and composition tests that assert both
factories' namespaces. Not re-exported from `orders/__init__.py` (parity with
`FilterArgumentsFactory`).

Layer 6 (`_dynamic_orderset_cache` / `get_orderset_class`) is a standing
deferred non-goal (spec-028 Decision 12). Symbols exist only in module
docstring + TODO comment. `connection.py::DjangoConnectionField` applies
ordering from the already-resolved `Meta.orderset_class` sidecar
(`definition.orderset_class.apply_*`); no auto-OrderSet path.

Sibling: `filters/factories.py` — Layer 5 twin already shares
`GeneratedInputArgumentsFactory`; Layer 6 is concrete there
(`get_filterset_class` + hashing helpers) but still has no production caller
(connection also reads `Meta.filterset_class` directly). Live GraphQL order
coverage already exists under `examples/fakeshop/test_query/` (library /
scalars order paths); this file has no new consolidation to prove there.

Item-scoped baseline diff for the target is empty
(`git diff 1fcb3dcfcc17c63139f1a500379f02f82862a6f7 -- …/orders/factories.py`).

## Verification

- Read complete `orders/factories.py`, `filters/factories.py`, and
  `utils/inputs.py::GeneratedInputArgumentsFactory` (BFS, collision,
  empty-input guard, `__init_subclass__` rejection).
- Confirmed `get_orderset_class` / `_dynamic_orderset_cache` appear only as
  deferred comments in `orders/factories.py` — no definitions, no imports.
- Confirmed `get_filterset_class` has no production importers outside
  `filters/factories.py` (tests-only consumption).
- Confirmed `connection.py` never imports `orders.factories` and never
  synthesizes an OrderSet from model/fields meta.
- Compared filter vs order `_build_input_triples`: filter splices
  `_build_logic_fields`; order returns field triples only — intentional
  family divergence, already expressed as the shared base's NotImplemented
  hook.
- Compared `filters/factories.py::_make_hashable` to
  `optimizer/extension.py::_hashable_variable_value`: both recurse into
  containers with `repr`-sorted unordered branches, but contracts differ
  (Meta cache keys vs tagged GraphQL variable freezing with opaque/cycle
  tokens). Not the same responsibility.
- Package search: no second order-side Layer-6 cache or hashing twin.

## Opportunities

None — Layer 5 is already single-sited in `GeneratedInputArgumentsFactory`;
the only historically deferred cross-family extraction (Layer-6 Meta-cache
hashing) still has no orders twin to merge with.

### Strongest rejected / deferred candidates

1. **Extract `_make_hashable` / `_make_cache_key` into `utils/inputs.py` now.**
   Deferred (trigger unfired). Filters owns the only concrete
   `(model, fields_key, extra)` cache keying. Orders still reserves
   `get_orderset_class` + `_dynamic_orderset_cache` in comments only.
   Trigger: a card that ships a real orders Layer-6 implementation (or a
   folder/project pass that finds a second concrete Meta-cache consumer).
   Until then a shared helper would invent a second owner for a single site.

2. **Merge `_build_input_triples` bodies / collapse family subclasses further.**
   Rejected. Remaining subclass surface is the required per-family cache
   namespaces plus the Decision-8 operator-bag vs no-bag hook. Further
   folding needs mode flags or erases the distinct collision registries.

3. **Ship `get_orderset_class` now to “complete the twin” for hashing DRY.**
   Rejected. Spec-028 Decision 12 + connection-field design chose explicit
   `Meta.orderset_class`. Inventing an unconsumed Layer 6 to force hashing
   consolidation is the opposite of root-cause ownership.

4. **Merge Meta hashing with optimizer variable freezing.**
   Rejected. Different inputs, tags, failure modes, and change axes.

5. **Drop the unused `TYPE_CHECKING` `django.db.models` import.**
   Rejected as unrelated micro-cleanup; it is an explicit filter-side parity
   stub (`noqa: F401`), not a duplicated rule.

## Judgment

Proved zero-edit. `OrderArgumentsFactory` is the intended thin family
wrapper over the shared BFS owner. Filters Layer-6 hashing consolidation
remains correctly deferred: the orders Layer-6 twin does **not** exist yet,
and connection ordering continues to use explicit `Meta.orderset_class`.
Ready for Worker 2 independent verification.

## Independent verification (Worker 2)

Re-traced Layer 5 ownership through `OrderArgumentsFactory` →
`GeneratedInputArgumentsFactory` → finalizer phase 2.5 /
`materialize_input_class` / `clear_order_input_namespace`, and Layer 6
deferral through connection + filter twin + reserved TODO symbols.

**Scoped diff.** Empty vs `ITEM_BASELINE`
`1fcb3dcfcc17c63139f1a500379f02f82862a6f7`: working-tree blob
`a5bb9c9ee7295567b7edae3e208d114ea159f01d` equals
`1fcb3dcf…:django_strawberry_framework/orders/factories.py`. No production
edits in this item.

**Layer-6 challenge (deferral).** Confirmed `get_orderset_class` and
`_dynamic_orderset_cache` still have **no definitions** anywhere under
`django_strawberry_framework/` — only the module docstring + bottom TODO in
this file. `connection.py` has zero matches for `factories` /
`get_orderset_class` / `get_filterset_class`; sync/async order paths call
`definition.orderset_class.apply_*` only. Filter-side `get_filterset_class`
remains tests-only (definition in `filters/factories.py`; no production
importer). Shipping an orders Layer 6 now would invent an unconsumed twin
solely to force hashing extraction — rejected. Deferral stands.

**Missed-consolidation search.** Package search for Meta-cache hashing,
second order Layer-6 path, and BFS reimplementation outside
`GeneratedInputArgumentsFactory`: none found. Rejected Worker-1 candidates
re-checked and disposed:

1. Extract `_make_hashable` / `_make_cache_key` now — still one concrete
   site (`filters/factories.py`); trigger unfired.
2. Further collapse family `_build_input_triples` — Decision-8 operator-bag
   divergence + distinct collision registries remain real.
3. Merge Meta hashing with
   `optimizer/extension.py::_hashable_variable_value` — tagged
   scalar/container identity + opaque/cycle tokens vs untagged Meta keying;
   different change axes.
4. Drop `TYPE_CHECKING` `models` stub — parity marker, not a shared rule.

**Call sites.** Production importers of `orders.factories` remain
`types/finalizer.py` (BFS trigger) and the string path in
`orders/inputs.py::clear_order_input_namespace`; not re-exported from
`orders/__init__.py` (parity with filters).

**Verdict.** Zero-edit claim holds. Status → verified; plan item checked.
