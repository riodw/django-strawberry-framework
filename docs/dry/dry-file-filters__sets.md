# DRY review: `django_strawberry_framework/filters/sets.py`

Status: verified

ITEM_BASELINE: `1ea753fa1a06e8db9f27726075efc3b7e123b7d7`

## System trace

`filters/sets.py` owns Layers 3–4 of the filter pipeline plus the Decision-8 /
M1-of-rev5 named-helper apply decomposition:

- **Declaration / metaclass.** `FilterSetMetaclass` discovers `RelatedFilter`
  declarations via `sets_mixins.collect_related_declarations`, aliases
  `Meta.filter_fields` → `Meta.fields`, and rebuilds `base_filters` when a
  tombstone removes a candidate. `_expand_related_filter` / `get_filters`
  perform Layer-4 path expansion (cycle-safe via `expanded_once`).
- **Field / lookup shape.** `filter_for_field` / `filter_for_lookup` own the
  Decision-4 Relay-vs-scalar conditional; `_lookups_for_field` expands
  per-field `"__all__"`.
- **Apply pipeline.** `apply` / `apply_sync` / `apply_async` with shared
  `_apply_common_prelude` + `_apply_common_finalize`; related-visibility
  derive (`_iter_visibility_steps` + sync/async twins) feeding
  `_apply_related_constraints`; async-only
  `_collect_nested_visibility_querysets_async` stash for nested logic arms;
  permission walk (`_run_permission_checks`) and form validate + `.qs` read
  inside finalize.
- **Q-tree.** `_evaluate_logic_tree` / `_q_for_branch` / leaf filters against
  the django-filter form.

Connected surfaces traced: `utils/querysets.py` (`apply_type_visibility_*`,
now also `run_in_one_sync_boundary`), `utils/permissions.py` (request /
active-branch / permission-walk substrate already shared with orders),
`utils/input_values.py` (`SetInputTraversal`), `sets_mixins.py`,
`filters/inputs.py` (`LOOKUP_NAME_MAP` / `_LOGIC_KEYS` / `_field_specs`),
`orders/sets.py` (sibling apply coloring, thinner — no visibility derive /
form validate), `mutations/resolvers.py` (prior home of the sync-boundary
primitive), root `permissions.py` (`aapply_cascade_permissions`),
`auth/mutations.py` + `schema.py` (consumers of the mutations re-export),
`tests/filters/test_sets.py`, live filter APIs under
`examples/fakeshop/test_query/` (sync Client → `apply_sync` only; async
finalize / nested pre-walk remain unit-tier per
`examples/fakeshop/test_query/README.md`).

Baseline scoped diff for the target was empty at review start.

## Verification

1. **Inlined `sync_to_async(thread_sensitive=True)` vs
   `run_in_one_sync_boundary`.** Confirmed real repeated responsibility.
   Forwarded from the verified `permissions.py` item with accurate call-site
   inventory: `filters/sets.py::apply_async` wraps `_apply_common_finalize`;
   `orders/sets.py::apply_async` wraps `_run_permission_checks`;
   `permissions.py::aapply_cascade_permissions` wraps the sync walk;
   `mutations/resolvers.py` already named the primitive and auth/schema import
   it from there. Importing the mutations definition into filters would create
   a filters→mutations dependency the package does not have today (mutations
   does not import filters; the edge would still be the wrong direction for a
   read-side module). Neutral owner is `utils/querysets.py` (sibling of
   `reject_async_in_sync_context`, cycle-safe substrate). **Accepted and
   implemented** — see Opportunities / Implementation.

2. **Filter/order apply-pipeline family mirror.** Both normalize → permission
   gate → family-specific tail; both already share
   `utils/permissions.py` request/active-input helpers. Orders has no related
   visibility derive, no nested async pre-walk, no django-filter form validate
   / `.qs` materialization — its shared tail is `_apply_orderings`, not
   filter finalize. Further collapsing the two apply graphs would need mode
   flags across distinct contracts. **Rejected at file scope** — folder /
   project may re-check after both family files are verified; this file is
   not the sole owner of a missing shared piece beyond the sync-boundary
   primitive already consolidated.

3. **Sync/async visibility-derive sibling pair
   (`_derive_related_visibility_querysets_sync` /
   `_derive_related_visibility_querysets_async`).** Bodies already share
   `_iter_visibility_steps`; they differ only in awaiting
   `apply_type_visibility_async` vs sync + `apply_async` vs `apply_sync`
   child recursion. Collapsing further would invent a coloring helper that
   obscures the Decision-8 sync/async split without a third site to migrate.
   **Rejected** — intentional colored twins with the shared iterator already
   extracted.

4. **Obsolete `_read_qs`.** Production `apply_async` no longer wraps a bare
   `.qs` getter; finalize owns perm + validate + `.qs`. The helper was
   uncalled from production, carried a stale docstring claiming
   `sync_to_async(_read_qs)`, and only tests exercised it (two of which used
   it as a `.qs` trigger). **Deleted** as an obsolete parallel path, not
   abstracted.

5. **`testing/client.py` `sync_to_async(force_login/logout)`.** Session
   bracket I/O for the test client — not the consumer-hook one-boundary
   resolution contract. **Rejected** as unrelated.

## Opportunities

### 1. Promote `run_in_one_sync_boundary` to `utils/querysets.py` and migrate inlined sites

- **Repeated responsibility:** run a sync callable in exactly one
  `sync_to_async(thread_sensitive=True)` worker call (off-event-loop boundary
  for consumer-overridable sync hooks).
- **Sites:** definition formerly in `mutations/resolvers.py`; inlined at
  `filters/sets.py::FilterSet.apply_async` (`_apply_common_finalize`),
  `orders/sets.py::OrderSet.apply_async` (`_run_permission_checks`),
  `permissions.py::aapply_cascade_permissions`; consumers already calling the
  named primitive via mutations re-export: `auth/mutations.py`, `schema.py`.
- **Evidence:** byte-identical wrapper shape; identical rationale in each
  docstring; package already treated the mutations definition as
  cross-module reusable (auth). Read-side sites could not import mutations
  without wrong-direction layering.
- **Owner:** `utils/querysets.py::run_in_one_sync_boundary`.
- **Consolidation:** define once in utils; import + re-export from
  `mutations/resolvers.py` (preserve auth/schema import path; auth file left
  untouched — concurrent dirty); migrate filters / orders / permissions call
  sites; delete obsolete `_read_qs`.
- **Proof:** `tests/utils/test_querysets.py::test_run_in_one_sync_boundary_is_single_sourced_from_utils`
  (mutations re-export identity);
  `test_run_in_one_sync_boundary_runs_callable_off_event_loop`; existing
  `tests/filters/test_sets.py::test_apply_async_runs_permission_checks_off_event_loop_thread`
  and orders / cascade off-loop pins keep the behavioral contract. Live
  GraphQL tests already cover sync `apply_sync` paths; async finalize remains
  unit-tier (sync HTTP Client).
- **Risks / non-goals:** do not fold filter finalize / order permission /
  cascade walk *bodies* into the boundary primitive — only the worker wrap.
  Auth import path kept on mutations for concurrent-WIP safety.

## Judgment

The filter apply pipeline is already well-factored internally (prelude /
finalize / shared visibility iterator). The one system-owned duplication this
file participated in was the generic sync-boundary wrapper; consolidating it
at `utils/querysets.py` and migrating every confirmed production site is the
root-cause fix. Filter/order pipeline shape and the colored visibility twins
remain intentionally separate.

## Implementation (Worker 1)

- **Owner chosen:** `utils/querysets.py::run_in_one_sync_boundary`.
- **Migrated:** `mutations/resolvers.py` (definition → import/re-export);
  `filters/sets.py::apply_async`; `orders/sets.py::apply_async`;
  `permissions.py::aapply_cascade_permissions`. Deleted `_read_qs`.
- **Left on mutations import path (no edit):** `auth/mutations.py` (concurrent
  dirty), `schema.py` (re-export still works).
- **Tests:** identity + off-loop primitive pins in `tests/utils/test_querysets.py`;
  filter async off-loop docstring updated; `_read_qs` unit test removed;
  logic-tree tests trigger via `fs.qs`.
- **Validation:** `uv run ruff format .` and `uv run ruff check --fix .`
  clean. Full pytest not run (Worker 1 file item).
- **Changelog:** no — internal DRY ownership move, no public API change
  (mutations re-export preserved).
- **Rejected retained:** filter/order apply-graph merge; further visibility
  twin collapse; test-client `sync_to_async` login bracket.

## Independent verification (Worker 2)

Re-traced the one-boundary contract from baseline
`1ea753fa1a06e8db9f27726075efc3b7e123b7d7` through the scoped diff and current
call graph. Confirmed one shared responsibility: run a sync callable in exactly
one `sync_to_async(thread_sensitive=True)` worker so consumer-overridable sync
hooks (permission, form/filter body, cascade walk, mutation/form pipeline,
session auth, schema atomic enter/exit) stay off the event loop with
non-drifting boundary discipline. That is not the filter finalize body, the
order permission body, or the cascade walk — only the worker wrap; those
payloads correctly remain at their owners.

**Owner challenge (utils vs mutations).** Keeping the definition under
`mutations/resolvers.py` would force read-side modules (`filters/`, `orders/`,
root `permissions.py`) into a root→mutations import the package does not
otherwise take. `utils/querysets.py` already owns the sibling sync/async
discipline (`reject_async_in_sync_context` / `SyncMisuseError`), is cycle-safe
for types/relay, and is already imported by every migrated site. Name stretch
("querysets" hosting a generic boundary) is real but weaker than the layering
bug of a mutations owner; no clearer existing module without inventing a
one-symbol package. **Owner choice stands.**

**Call-site migration.** Production invocations of the contract now resolve
only through `utils/querysets.py::run_in_one_sync_boundary` (sole
`sync_to_async(..., thread_sensitive=True)` call expression under
`django_strawberry_framework/`). Migrated: `filters/sets.py::apply_async`,
`orders/sets.py::apply_async`, `permissions.py::aapply_cascade_permissions`,
`mutations/resolvers.py` (definition → import + namespace re-export). Forms /
rest_framework continue via `run_pipeline_async` → the shared primitive.
`schema.py` and `auth/mutations.py` still import from
`mutations.resolvers` and resolve the same object (`is` identity pinned in
`tests/utils/test_querysets.py`). No leftover inlined
`sync_to_async(..., thread_sensitive=True)` duplicates of this contract.

**Rejected candidates re-challenged.**

1. **Filter/order apply-pipeline merge.** Orders: request → permission →
   `_apply_orderings` (no visibility derive, no form validate, no `.qs`).
   Filters: visibility derive → prelude → finalize (perm + validate + `.qs`)
   plus async-only nested stash. Shared substrate already in
   `utils/permissions.py`. Further collapse needs mode flags across distinct
   contracts. **Rejection stands.**

2. **Visibility sync/async twins.** Bodies share `_iter_visibility_steps`;
   differ only in `apply_type_visibility_*` + child `apply_*` coloring. No
   third site; a coloring helper would obscure Decision-8 without reducing
   change axes. **Rejection stands.**

3. **`testing/client.py` login bracket.** Separate `sync_to_async` calls for
   test-client session I/O (no explicit `thread_sensitive`, two hops, not
   consumer-hook resolution). **Rejection stands.**

**`_read_qs` deletion.** Baseline helper was only a `.qs` attribute-read
wrapper for an obsolete `sync_to_async(_read_qs)` story; production
`apply_async` already routes through `_apply_common_finalize` (perm + validate
+ `.qs`). No production callers remain; tests that used it as a `.qs` trigger
now read `fs.qs` directly; dedicated unit test removed. **Safe delete, not a
missed abstraction.**

**Tests / placement.** Primitive identity + off-loop pins live in
`tests/utils/test_querysets.py` (package owner). Filter async off-loop
behavioral pin remains in `tests/filters/test_sets.py`. Live HTTP still covers
sync `apply_sync` only — async finalize unit-tier is consistent with
`examples/fakeshop/test_query/README.md`. No orphan `_read_qs` imports.

**Disposed non-blockers.** Mid-module docstring in `utils/querysets.py` still
says the module "owns only the source normalization + the colored visibility
calls" after the top paragraph added the boundary — polish for a later pass,
does not undermine ownership or migration. GLOSSARY cascade prose still names
the asgiref mechanism rather than the helper; behaviorally accurate, not a
duplicate implementation.

**Verdict:** complete. Status → verified; plan item checked.
