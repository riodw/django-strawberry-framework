# DRY review: folder `django_strawberry_framework/optimizer/`

Status: verified

## System trace

`optimizer/` is the selection-driven queryset planning component: one schema
extension walks the GraphQL selection tree, builds an `OptimizationPlan`, and
applies `select_related` / `prefetch_related` / windowed (or lateral) nested
connection fetches so relation resolvers do not N+1.

Folder shape (including `nested_planner.py`, present on disk but not a separate
plan item — treated as a folder member):

- `__init__.py` — public `DjangoOptimizerExtension` + package `logger` re-export.
- `_context.py` — object/dict/frozen context get/stash/clear + stash key set.
- `extension.py` — SchemaExtension lifecycle, plan cache, root/connection apply
  seam, schema audit, cache-key AST walks.
- `field_meta.py` — relation-shape snapshot + dual-contract FK-id / target-pk
  readers.
- `hints.py` — `OptimizerHint` + `hint_is_skip`.
- `join_taxonomy.py` — one `classify_relation_join` for window partition,
  connector column, and lateral join shape.
- `selections.py` — AST + converted-selection adapters (fragment / directive /
  edges→node).
- `plans.py` — `OptimizationPlan`, window pagination, order/lookup helpers,
  B8 prune/diff.
- `walker.py` — selection walk + list/select/prefetch planning; delegates nested
  Relay connections.
- `nested_planner.py` — transactional nested-connection planner (Decision-6
  fallbacks, divergent aliases, keyset/offset windows, strategy dispatch).
- `nested_fetch.py` — strategy protocol, windowed/auto strategies, unwindowable
  child-queryset gate.
- `lateral_fetch.py` — Postgres LATERAL backend on the shared window floor.

Connected behavior re-traced for this folder pass (not inherited as proven):
`connection.py` (`to_attr` probes, resolve-from-window); `types/resolvers.py`
(strictness / FK-id elision reads); `utils/connections.py` (window bounds /
`resolve_relay_max_results`); `utils/querysets.py` (`normalize_query_source`);
`utils/typing.py` (type unwrap + new schema digs); package `tests/optimizer/`;
live nested-connection coverage under `examples/fakeshop/test_query/`.

Folder-level axes examined: duplicated policy across modules; state ownership
(ContextVars published from `on_execute`, plan cache instance-bound, context
stash keys); competing helper layers (join taxonomy vs historical shims;
selections vs extension/walker adapters); public export flavor; lifecycle work
at plan vs fetch vs resolve; file-pass deferrals explicitly handed to this folder
pass (`_strawberry_schema` dig).

## Verification

- Item-scoped baseline `c702abf859a0490daaebd8f7eb03017ed454799c`: working
  tree matched baseline for `optimizer/` at pass start (empty item-scoped
  diff). Concurrent dirt vs HEAD on optimizer modules and other packages is
  pre-baseline / other-session WIP — left untouched except the sites this
  consolidation migrates. Plan checkbox not edited.
- Re-read all twelve optimizer sources end-to-end (including
  `nested_planner.py`). Grepped package for `_strawberry_schema`,
  `schema_config`, `relay_max_results`, `_relation_connection_to_attr`,
  `classify_relation_join`, `_connector_only_field`,
  `connection_node_children`, `assert_window_fetch_mode_for`, and walker
  re-export aliases of nested_planner helpers.
- Confirmed edges→node composition already has one owner
  (`selections.connection_node_children`); join facts already have one owner
  (`join_taxonomy.classify_relation_join`) with historical raise/name shims in
  `plans.window_partition_for_prefetch` and
  `nested_planner._connector_only_field`.
- Confirmed three identical config digs
  (`nested_planner._relay_max_results_from_info`,
  `walker._schema_name_converter`,
  `utils/connections.resolve_relay_max_results`) plus extension's schema-wrapper
  digs — cycle-blocked from importing extension; file passes deferred ownership
  here.
- Preserved intentional None-vs-100 split: planner returns `None` (engine
  default); `resolve_relay_max_results` terminals at `100`. Same dig, different
  missing-config policy (pinned by `tests/optimizer/test_walker.py` and
  `tests/test_keyset.py`).
- No full pytest. Focused helper tests added under `tests/utils/test_typing.py`
  (not earnable as a distinct live GraphQL assertion beyond existing
  nested-connection suite). Ruff format + check after edits.

## Opportunities

### 1. Strawberry schema / config dig on `utils.typing` (accepted)

- **Repeated responsibility:** read Strawberry's private
  `schema._strawberry_schema` (and optionally `.config`) from plan-time
  graphql-core `info` and resolve-time Strawberry `Info`.
- **Sites:** `extension._strawberry_schema_from_*` (wrapper);
  `nested_planner._relay_max_results_from_info`; `walker._schema_name_converter`;
  `utils/connections.resolve_relay_max_results`.
- **Evidence:** byte-identical getattr chains; same brittle attribute; must
  change together if Strawberry renames the backref; extension cannot own the
  dig without creating walker→extension or connections→optimizer edges.
- **Owner:** `utils/typing.py::strawberry_schema_from_schema`,
  `strawberry_schema_from_info`, `schema_config_from_info`.
- **Consolidation:** move digs to `utils/typing.py`; extension imports under
  historical underscore aliases; planner/walker/connections call
  `schema_config_from_info` and keep their distinct missing-config policies.
- **Proof:** `tests/utils/test_typing.py::test_strawberry_schema_from_info_and_schema`,
  `test_schema_config_from_info_prefers_wrapped_then_direct`; existing
  `test_relay_max_results_from_optimizer_info_shapes` and
  `test_resolve_relay_max_results_precedence`.
- **Risks / non-goals:** do not unify None (planner) with terminal 100
  (keyset resolver); do not put the owner on `extension` (import cycle).

## Judgment

Folder ownership is otherwise clear after prior file-pass consolidations
(selections substrate, join taxonomy, nested_fetch strategy seam, FieldMeta
dual-contract readers, context stash helpers). The one folder-visible lockstep
rule still spelled three ways was the Strawberry schema/config dig; that now
has a cycle-safe owner. Remaining parallels are intentional shims, test-compat
aliases, or phase-distinct policies (plan None vs resolve 100; windowed floor vs
lateral SQL).

### Rejected / deferred (re-proved)

1. **Delete walker underscore aliases of nested_planner / selections helpers.**
   Deferred — test-import and historical private-import compatibility; not
   competing implementations.

2. **Inline nested_planner callback injection** (pass walker functions without
   kwargs). Rejected — intentional seam keeping nested_planner free of a walker
   import cycle.

3. **Fold `_connector_only_field` / `window_partition_for_prefetch` into call
   sites.** Rejected — already shims over `classify_relation_join`; names and
   raise contracts are load-bearing for tests and historical callers.

4. **Merge `NestedConnectionRequest` and `LateralWindowSpec`
   `assert_window_fetch_mode_for` calls into one constructor.** Rejected —
   shared helper already owns the rule; each boundary must enforce it for its
   own type.

5. **Generic `named_path_children` unifying mutation payload extractor with
   edges→node.** Rejected — mutation is one payload slot; Relay edges/node is a
   distinct invariant already owned by `connection_node_children`.

6. **Walker walk-context dataclass for shared
   `(plan, prefix, info, …)` threading.** Deferred — still net-neutral
   readability; revisit when the next shared member lands.

7. **Move `_stash_union` into `_context.py`.** Rejected — publish/union policy
   for nested FALLBACK re-entry, not context access-mode dispatch.

## Implementation (Worker 1)

- **Owner chosen:** `django_strawberry_framework/utils/typing.py`
  (`strawberry_schema_from_schema`, `strawberry_schema_from_info`,
  `schema_config_from_info`).
- **Migrated sites:** `optimizer/extension.py` (aliases to shared helpers);
  `optimizer/nested_planner.py::_relay_max_results_from_info`;
  `optimizer/walker.py::_schema_name_converter`;
  `utils/connections.py::resolve_relay_max_results`.
- **Tests / docs:** `tests/utils/test_typing.py` new pins; `utils/__init__.py`
  docstring note. No CHANGELOG (not authorized).
- **Behavior kept separate:** planner `None` vs resolver terminal `100` on
  missing config.
- **Validation:** ruff format + check. No full pytest.
- **Rejected findings:** listed above; no further production edits.
- **Changelog:** no — internal ownership move, no consumer-facing API change.
- Ready for Worker 2 independent verification.

## Independent verification (Worker 2)

Re-traced `optimizer/` as one component (all twelve modules including
`nested_planner.py`) against ITEM_BASELINE
`c702abf859a0490daaebd8f7eb03017ed454799c` and the item-scoped diff
(`extension.py` / `nested_planner.py` / `walker.py` /
`utils/typing.py` / `utils/connections.py` / `utils/__init__.py` /
`tests/utils/test_typing.py`). No production edits.

### schema_config consolidation — accepted

- Package-wide `_strawberry_schema` getattr chains now live only in
  `utils/typing.py`. Migrated callers: extension (historical underscore
  aliases), `nested_planner._relay_max_results_from_info`,
  `walker._schema_name_converter`, `connections.resolve_relay_max_results`.
- Owner on `utils/typing` is cycle-safe (walker/connections cannot import
  extension). Slight smell that digs are not type-unwrapping, but they are
  Strawberry-private contract helpers beside existing unwraps — clearer than
  a mode-flag helper on `connections` or a new module for three functions.
- Dig preference (wrapped config, then bare `schema.config`, else `None`)
  matches the pre-move triple; call sites keep distinct missing-config
  policies on top.

### None vs terminal 100 — challenged, kept distinct

- `SliceMetadata.from_arguments(max_results=None)` re-reads
  `info.schema.config.relay_max_results`. Plan-time bare `GraphQLSchema` has
  no `.config`, so the dig must supply the numeric cap when present.
- Scratch: bare schema + `max_results=None` → `AttributeError`; bare + `100`
  works; resolve-time `schema.config` + `None` applies that config.
- Because `schema_config_from_info` already tries both config paths, dig
  `None` means SliceMetadata's own fallback also fails on plan-time bare
  schema. Docstring "engine default applies downstream" is therefore only
  accurate when a config object exists (production wrapped schema, or
  resolve-time Info / `_fake_info`). Degenerate no-config stubs pin helper
  `None` and are not a live planning path.
- Keyset `resolve_relay_max_results` cannot defer to SliceMetadata and must
  terminal at `100`. Unifying the policies would blur that fork and break
  `test_relay_max_results_from_optimizer_info_shapes` /
  `test_resolve_relay_max_results_precedence`. Split stands.

### Rejected candidates — re-challenged, kept

1. Walker underscore aliases of nested_planner / selections — re-exports only;
   not competing implementations.
2. nested_planner callback injection — keeps nested_planner free of a walker
   import cycle; intentional seam.
3. `_connector_only_field` / `window_partition_for_prefetch` — thin shims over
   `classify_relation_join` with load-bearing names / raise contracts.
4. Dual `assert_window_fetch_mode_for` on `NestedConnectionRequest` /
   `LateralWindowSpec` — shared rule, per-type boundary enforcement.
5. Generic `named_path_children` with mutation payload — distinct invariants;
   edges→node already owned by `connection_node_children`.
6. Walker walk-context dataclass — still net-neutral readability.
7. `_stash_union` into `_context.py` — publish/union policy for nested
   FALLBACK re-entry, not context access-mode dispatch.

### Missed folder-level consolidations

Searched remaining `_strawberry_schema` / `schema.config` digs, join-taxonomy
shims, edges→node adapters, window-fetch-mode asserts, stash helpers, and
walker re-export aliases. No further folder-owned lockstep rule beyond the
accepted dig. Attribute reads (`relay_max_results` vs `name_converter`) on
the shared config object are not a second dig to fold.

### Tests

`uv run pytest` on
`test_strawberry_schema_from_info_and_schema`,
`test_schema_config_from_info_prefers_wrapped_then_direct`,
`test_relay_max_results_from_optimizer_info_shapes`,
`test_resolve_relay_max_results_precedence` — 4 passed (coverage gate N/A
for focused run).

### Disposition

All accepted and rejected findings disposed. Status → verified; plan checkbox
marked.

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
