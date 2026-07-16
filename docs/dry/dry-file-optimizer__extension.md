# DRY review: `django_strawberry_framework/optimizer/extension.py`

Status: verified

## System trace

The target owns the **optimizer execution lifecycle** for a Strawberry schema:
root-gated resolve middleware, plan-cache identity and LRU, per-execution
ContextVar memos, publish of plan / strictness sentinels onto `info.context`,
schema-reachability audit, and the connection / mutation cooperation seam
(`apply_connection_optimization` + selection extractors).

Owned responsibility:

- `on_execute` — clear reused context stashes; publish active extension
  instance, nested-fetch strategy, and per-execution caches; reset on exit;
- `resolve` / `_optimize` — root gate, Manager→QuerySet coerce
  (`normalize_query_source`), evaluated-queryset guard, return-type→model
  resolve, then `apply_to`;
- `apply_to` / `_get_or_build_plan` / `_build_cache_key` — single
  plan-build-and-apply tail shared by middleware and connection/mutation
  callers; document + variable cache-key families; cross-request and
  per-execution plan memos;
- `_publish_plan_to_context` / `_stash_union` — publish policy (last-wins plan
  introspection; union + subset early-out for correctness sentinels under
  nested FALLBACK re-entry, spec-033 Decision 8);
- module-level cache-key AST walks, selection extractors, and
  `check_schema` reachability audit.

Connected behavior examined:

- `optimizer/_context.py` — get/stash/clear for `dst_optimizer_*` keys (verified
  sibling; `_stash_union` correctly deferred here as publish policy);
- `optimizer/selections.py` — AST / converted-selection substrate; now also
  owns `connection_node_children` (edges->node composition);
- `optimizer/walker.py` / `plans.py` / `nested_fetch.py` — plan build, apply,
  prune/diff, strategy ContextVar;
- `optimizer/nested_planner.py` — evidence only; nested `edges { node }` unwrap
  migrated onto the shared selections owner;
- `connection.py` / `mutations/resolvers.py` — call
  `apply_connection_optimization` with connection vs mutation extractors;
- `types/resolvers.py` — reads published sentinels via `get_context_value`;
- `utils/querysets.py::normalize_query_source` — shared Manager/queryset gate;
- upstream `strawberry_django/optimizer.py` — same root-gate / ContextVar
  *shape*, different enablement and no `info.context` sentinel contract;
- Pins: `tests/optimizer/test_extension.py`, `tests/optimizer/test_selections.py`
  (new `connection_node_children` pins), live connection / nested FALLBACK
  coverage in `examples/fakeshop/test_query/` and `tests/test_connection.py`.

Baseline-scoped diff before this item was empty for the target; concurrent
dirty paths under other optimizer / forms / filters modules left untouched.

## Verification

Searches:

- Production readers of `_optimizer_active`: **none** (only set/reset in
  `on_execute` and one lifecycle unit test). `_active_optimizer` already
  encodes the same lifecycle (`None` vs instance) and is the sole production
  discovery handle for `apply_connection_optimization`.
- `edges` / `node` / `named_children` composition: duplicated in
  `extension._connection_node_child_selections` and
  `nested_planner._connection_node_selections` with identical prefix
  accumulation rules; leaf helpers already lived in `selections.py`.
- `_stash_union` / publish: only this module; correctly uses `_context`
  get/stash (sibling review).
- `_strawberry_schema_from_*` vs inline `getattr(..., "_strawberry_schema")`
  in nested_planner / walker / `utils/connections`: same private attribute,
  different fallbacks and consumers (type lookup vs `.config`); cycle-blocked
  from importing extension.
- Optional `export_dry_review.py audit --target …/extension.py --stdout`:
  37 definitions; reverse imports match extension consumers + heavy
  `test_extension.py` pins. Static similarity alone did not justify further
  helpers (cache LRU twins, thin family wrappers, finalized-* fallbacks).

Rejected / deferred candidates (tried to disprove shared ownership):

1. **Move `_stash_union` into `_context.py`.** Deferred / rejected as generic
   key access: union-with-subset-early-out is **publish policy** for nested
   FALLBACK re-entry, not object/dict/frozen dispatch. Stays on the extension
   (confirmed with sibling `_context` review).

2. **Unify mutation payload extractor with edges->node via a generic
   `named_path_children(path_names=...)`.** Deferred: mutation is a one-level
   payload slot, not the Relay edges/node invariant that must stay lockstep
   with nested planning. Parameterizing path depth would add a mode-shaped
   helper for one extra call site without removing a second edges/node
   implementation (already consolidated).

3. **Share `_strawberry_schema_from_info` with nested_planner / walker /
   connections.** Rejected for this pass: extension helpers return the schema
   wrapper (or input) for `get_type_by_name`; other sites want `.config` with
   different fallbacks. Moving them needs a cycle-safe owner outside
   extension→walker; folder pass can revisit.

4. **Merge `_MAX_PLAN_CACHE_SIZE` and `_MAX_DOC_KEY_CACHE_SIZE` (both 256).**
   Rejected: independent LRU bounds that happen to match; coupling would force
   unrelated caches to resize together.

5. **Extract shared OrderedDict LRU get/promote/evict helper for plan + doc
   caches.** Rejected: tiny pattern; a helper obscures two caches with
   different keys, values, and miss paths.

6. **Retire `_collect_directive_var_names` /
   `_collect_nested_pagination_var_names` thin wrappers.** Rejected: production
   uses the union collector; family wrappers are intentional test seams that
   pin Decision 7 isolation without a second walk implementation.

7. **Collapse `_publish_plan_to_context` finalized-* None fallbacks into plan
   methods.** Deferred to `plans.py` ownership: after `finalize()` /
   prune/diff the fields are set; the fallbacks defend unfinalized
   direct/test plans. Not a second publish policy.

8. **Retarget upstream strawberry-django ContextVar optimizer state.**
   Disproved: intentional architecture split (this package's resolver-visible
   `info.context` sentinels vs upstream enablement ContextVars).

9. **Retire extension re-export of `_stash_on_context` / selection underscore
   aliases.** Deferred: test-import compatibility; canonical bodies already
   live in `_context` / `selections`.

## Opportunities

### 1. Single active-optimizer lifecycle signal

- **Repeated responsibility:** "is the optimizer installed for this
  execution?" tracked by two ContextVars (`_optimizer_active: bool` and
  `_active_optimizer: instance | None`) with the same `on_execute` lifetime.
- **Sites:** `extension.py` set/reset; `apply_connection_optimization` (reads
  only `_active_optimizer`); `tests/optimizer/test_extension.py`
  lifecycle pin.
- **Evidence:** production never reads the boolean; `_active_optimizer is not
  None` is a strict superset of the boolean's information.
- **Owner:** `_active_optimizer` on this module.
- **Consolidation:** delete `_optimizer_active`; pin the lifecycle test on
  `_active_optimizer` identity.
- **Proof:** updated `test_on_execute_sets_and_resets_context_var`; existing
  `test_apply_connection_optimization_uses_active_optimizer_cache` and live
  connection short-circuit pins.
- **Risks / non-goals:** not exported in `__all__`; no public API change.

### 2. Single `edges { node }` selection unwrap

- **Repeated responsibility:** descend `edges` → `node`, accumulate response-key
  runtime prefixes, clone node children for the walker (fragment- and
  directive-aware).
- **Sites:** `extension._connection_node_child_selections`;
  `nested_planner._connection_node_selections` (evidence module, same rule).
- **Evidence:** identical composition; leaf helpers already in `selections.py`;
  module docstring already claimed this ownership; drift would desync root
  apply vs nested planning prefixes / strictness keys.
- **Owner:** `optimizer/selections.py::connection_node_children`.
- **Consolidation:** implement once; extension extractor supplies
  `runtime_path_from_info`; nested_planner becomes a one-line adapter.
- **Proof:** new `tests/optimizer/test_selections.py` pins (unwrap + empty
  scalar-only); existing nested-connection / `apply_connection_optimization`
  suites and live FALLBACK HTTP tests remain the integration tier.
- **Risks / non-goals:** mutation payload slot extractor stays separate
  (different GraphQL shape).

## Judgment

Two consolidations warranted and implemented: obsolete boolean lifecycle
ContextVar removed in favor of `_active_optimizer`, and the Relay
`edges { node }` composition moved to its true owner in `selections.py`.
Publish/union policy, cache-key walks, and `apply_to` remain correctly
single-sited here. Ready for Worker 2.

## Implementation (Worker 1)

**Owner chosen:**

1. `_active_optimizer` as sole on_execute active-instance / active-lifecycle
   signal.
2. `selections.connection_node_children` as sole edges->node composition.

**Migrated:**

- `django_strawberry_framework/optimizer/extension.py` — removed
  `_optimizer_active`; connection extractor delegates to
  `connection_node_children`.
- `django_strawberry_framework/optimizer/selections.py` — added
  `connection_node_children`; docstring updated.
- `django_strawberry_framework/optimizer/nested_planner.py` —
  `_connection_node_selections` thin-adapts the shared helper; dropped
  unused named_children / response_key / node_children imports.
- `tests/optimizer/test_extension.py` — lifecycle pin → `_active_optimizer`.
- `tests/optimizer/test_selections.py` — permanent composition + empty-shape
  pins.

**Kept separate:** `_stash_union` publish policy; mutation payload extractor;
schema-private getattr sites outside this module; plan/doc LRU sizes;
directive/pagination collector test seams; `_stash_on_context` re-export.

**Validation:** `uv run ruff format` + `uv run ruff check --fix` +
`scripts/check_trailing_commas.py` on edited paths. No full pytest (per
Worker 1 rules). Changelog: no (internal DRY; not requested).

**Item-scoped paths for Worker 2:**

```text
git diff e813d828f81ac4e5cbd34ed35535b2e188f19116 -- \
  django_strawberry_framework/optimizer/extension.py \
  django_strawberry_framework/optimizer/selections.py \
  django_strawberry_framework/optimizer/nested_planner.py \
  tests/optimizer/test_extension.py \
  tests/optimizer/test_selections.py \
  docs/dry/dry-file-optimizer__extension.md
```

## Independent verification (Worker 2)

Re-traced `extension.py` as the optimizer execution lifecycle owner (root-gated
resolve, plan-cache identity/LRU, per-execution ContextVar memos, context
publish, `apply_connection_optimization` seam). Scoped diff matches the claimed
migrated paths only; concurrent dirty trees outside that scope left alone.

### Challenge 1 — drop `_optimizer_active`

Tried to break the claim that the boolean was redundant with
`_active_optimizer`. Production discovery is only `_active_optimizer.get()` in
`apply_connection_optimization`; `rg` over `*.py` finds **zero** remaining
`_optimizer_active` references. `on_execute` set/reset of the boolean was the
sole write site; the only reader was the lifecycle unit test, now pinned on
instance identity (`is None` / `is ext` / `is None`). Presence of a non-`None`
instance is a strict information superset of the old bool for this lifecycle
(never set to a non-self sentinel). Consolidation stands; private
underscore name, not in `__all__`.

### Challenge 2 — `connection_node_children` as sole edges→node unwrap

Compared old extension / nested_planner bodies to
`selections.connection_node_children`: same `named_children("edges")` →
`response_key` prefix fan-out → `named_children("node")` →
`node_children_with_runtime_prefix` composition. Extension now supplies only
`runtime_path_from_info` as a one-prefix tuple; nested_planner is a one-line
adapter preserving Decision 6 scalar-only / Decision 9 docs. Production
`named_children(..., "edges")` composition exists only inside
`connection_node_children`. Mutation payload extractor correctly stays separate
(one-level `<slot>`, different GraphQL shape). Owner in `selections.py` is
clearer than duplicated composition at two call sites that must stay lockstep
for prefix / strictness keys.

### `_stash_union` deferral

Confirmed: union + subset early-out is nested-FALLBACK **publish policy**
(Decision 8), not object/dict/frozen dispatch. `_context.py` correctly owns
get/stash/clear shape handling; moving union there would smuggle optimizer
publish semantics into a generic context adapter. Existing pins
(`test_stash_union_skips_restash_when_subset`, non-set overwrite defensive)
remain on the extension. Deferral stands.

### Leftovers / duplicates

- No leftover `_optimizer_active`.
- No duplicate edges→node unwrap outside `selections.connection_node_children`.
- Rejected candidates 3–9 (schema getattr, LRU twins, thin family wrappers,
  finalized-* fallbacks, upstream ContextVar retarget, underscore re-exports)
  re-checked; still not shared-responsibility consolidations for this item.

### Tests

- Lifecycle pin updated; `test_apply_connection_optimization_uses_active_optimizer_cache`
  still exercises `_active_optimizer`.
- New composition + empty-shape pins in `test_selections.py`.
- Focused run: all four pins passed
  (`test_on_execute_sets_and_resets_context_var`, both
  `connection_node_children` tests, `test_stash_union_skips_restash_when_subset`).

### Missed opportunities

None that warrant revision. Nested one-line adapter and mutation extractor
separation are intentional. Remaining deferred items are correctly parked for
folder / other owners.

**Disposition:** verified. Plan item checked.
