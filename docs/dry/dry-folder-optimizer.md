# DRY review: folder `django_strawberry_framework/optimizer/`

Status: verified

## System trace

`optimizer/` is one selection-driven queryset planning component: walk the
GraphQL selection tree → build an `OptimizationPlan` → apply
`select_related` / `prefetch_related` / windowed (or lateral / single-parent)
nested-connection fetches so relation resolvers do not N+1.

Present-day folder (~9512 lines, 14 modules) — fresh inventory, not the older
twelve-module plan list:

- `__init__.py` — public `DjangoOptimizerExtension` + package `logger`.
- `_context.py` — optimizer stash key vocabulary + start-of-execution clear.
- `extension.py` — SchemaExtension lifecycle, plan cache, root/connection apply,
  schema audit, cache-key AST walks.
- `field_meta.py` — relation-shape snapshot + dual-contract FK-id / target-pk.
- `hints.py` — `OptimizerHint` + `hint_is_skip`.
- `join_taxonomy.py` — `classify_relation_join` / `RelationJoinDescriptor`
  (partition, connector, morph, lateral shape, attach-complete columns).
- `selections.py` — AST + converted-selection adapters (fragment / directive /
  edges→node).
- `plans.py` — `OptimizationPlan`, window pagination, order/lookup helpers,
  B8 prune/diff.
- `walker.py` — selection walk + list/select/prefetch; delegates nested Relay
  connections; list-prefetch attach projection via
  `_ensure_connector_only_fields`.
- `nested_planner.py` — transactional nested-connection planner (Decision-6
  fallbacks, windows, strategy dispatch, scalar-only projection, index
  advisory).
- `nested_fetch.py` — strategy protocol, windowed/auto, unwindowable child gate.
- `lateral_fetch.py` — Postgres LATERAL backend + shared fetch-recognition
  primitives (`window_predicate_signature`, `_parent_in_values`, …).
- `single_parent_fetch.py` — runtime len==1 windowed fast path (reuses lateral
  recognition helpers; `DIRECT_FK` only).
- `predicates.py` — row-preserving `EXISTS` / `attach_exists` (FilterSet /
  search-fields consumers; no selection/plan coupling).

Lifecycle ownership (walk → plan → apply):

1. **Walk** — `extension` → `walker.plan_optimizations` → relation dispatch;
   nested Relay → `nested_planner.plan_connection_relation`.
2. **Plan** — `OptimizationPlan` + join taxonomy; strategy selection in
   `nested_fetch` / hints; window floor in `plans.apply_window_pagination`.
3. **Apply / fetch** — root `plan.apply`; nested Prefetch querysets; fetch-time
   lateral / single-parent recognition; resolve probes in `connection.py`.

Connected surfaces re-traced: `connection.py`, `keyset.py`,
`utils/connections.py`, `types/relay.py` / resolvers, `utils/typing.py`
(schema dig already owned), `filters/sets.py` (predicates), package
`tests/optimizer/`, library generic-connection acceptance tests.

Folder axes: attach-column completeness across projection writers; competing
fetch-recognition layers (lateral vs single-parent); predicates placement;
public export flavor; prior file-pass deferral
(`_ensure_connector_only_fields` GenericRelation morph).

## Verification

- ITEM_BASELINE `55e80be0b13e5a4416454d5fe53edfd29cc050cb`: optimizer tree at
  baseline already included `predicates.py` + `single_parent_fetch.py`;
  item-scoped diff empty at pass start. Concurrent dirt ignored. Plan
  checkbox not edited.
- Re-read all 14 present-day modules end-to-end. Independently evaluated the
  nested_planner-deferred GenericRelation list-prefetch gap (not
  rubber-stamped).
- Django `GenericRelatedObjectManager.get_prefetch_querysets` builds
  `rel_obj_attr` as `(object_id, content_type_id)` — both halves must survive
  any `.only()` mask. Scalar-only windows already projected both; walker
  `_ensure_connector_only_fields` appended only `parent_join_column` via the
  `_connector_only_field` shim, so list-prefetch and
  `edges { node { … } }` generic connections omitted `content_type_id`.
- Grepped attach / connector / content_type / recognition / reserved-alias /
  schema dig sites across the folder. Prior schema dig consolidation still
  holds (owner `utils/typing`).
- No pytest this pass (deferred). Permanent pins added under
  `tests/optimizer/`. Ruff format + check after edits.

## Opportunities

### 1. Prefetch-attach column completeness on join descriptor (accepted)

- **Repeated responsibility:** which child columns Django's prefetch attach
  reads must be projected under `.only()` (connector + GenericRelation morph).
- **Sites:** `RelationJoinDescriptor` facts (`parent_join_column`,
  `content_type_column`); `_project_scalar_only_window` (already both);
  `_ensure_connector_only_fields` (was connector-only — list-prefetch and
  nested-connection node-selection child plans).
- **Evidence:** same attach key; scalar-only fix comments name the N+1 /
  async hazard; node-selection path shares `_build_prefetch_child_queryset_from_base`
  → `_ensure_connector_only_fields` and missed the morph half; acceptance
  suite pins query-count only for scalar-only, not for `node { tag }`.
- **Owner:** `join_taxonomy.RelationJoinDescriptor.prefetch_attach_columns`.
- **Consolidation:** derived attach-complete tuple on the descriptor; walker
  and scalar-only projection both iterate it; `_connector_only_field` stays
  the historical single-column shim for test pins.
- **Proof:** `test_ensure_connector_only_fields_adds_generic_content_type`,
  `test_generic_connection_node_selection_projects_content_type_column`,
  join-taxonomy `prefetch_attach_columns` pin; existing scalar-only generic
  pins remain.
- **Risks / non-goals:** do not change index-advisory equality order
  (morph-first); do not inject plan-time morph WHERE (alias-late stays
  Django's); empty `only_fields` still means full-row load (no append).

## Judgment

Folder ownership remains clear after file-pass consolidations plus the prior
schema dig. The one folder-visible lockstep gap on present-day source was
prefetch-attach completeness for GenericRelation across projection writers —
now one derived property on the join descriptor. New modules
(`predicates.py`, `single_parent_fetch.py`) do not introduce competing policy
layers inside the folder.

### Rejected / deferred (this pass)

1. **Unify lateral + single-parent WHERE recognizers into one function.**
   Rejected — already share `window_predicate_signature` / `_parent_in_values`
   / `_is_window_qual` / `_select_columns` / `_deduplicate_parent_ids`; lateral
   still needs keyset + visibility arms single-parent deliberately omits.
   Folding would need mode flags.

2. **Extract shared QuerySet rebind helper for `LateralQuerySet` /
   `SingleParentWindowQuerySet`.** Rejected — parallel `_clone` /
   `_dst_window_signature` shape, different specs and fetch bodies; unifying
   obscures ownership.

3. **Move `predicates.py` out of optimizer/ (filters-owned).** Deferred —
   lives here for `OptimizerError` family coherence and to keep request values
   out of the plan cache; no second EXISTS implementation inside the folder.
   Project pass may revisit package placement.

4. **Delete walker underscore aliases / fold `_connector_only_field` into
   call sites.** Deferred / rejected as before — compat aliases and
   load-bearing shim names; attach completeness now bypasses the shim.

5. **Walker walk-context dataclass; `_stash_union` into `_context.py`;
   generic `named_path_children`; dual `assert_window_fetch_mode_for`.**
   Re-proved rejected/deferred — same contracts as the prior folder pass.

6. **Re-open schema dig / None-vs-100.** Rejected — already owned;
   policies intentionally distinct.

## Implementation (Worker 1)

- **Owner chosen:** `RelationJoinDescriptor.prefetch_attach_columns` in
  `optimizer/join_taxonomy.py`.
- **Migrated sites:** `walker._ensure_connector_only_fields`;
  `nested_planner._project_scalar_only_window`; `_connector_only_field`
  docstring (shim remains `parent_join_column` only).
- **Tests:** `tests/optimizer/test_join_taxonomy.py` attach-columns pin;
  `tests/optimizer/test_walker.py`
  `test_ensure_connector_only_fields_adds_generic_content_type`,
  `test_generic_connection_node_selection_projects_content_type_column`.
- **Behavior kept separate:** index-advisory equality prefix order; alias-late
  morph WHERE; empty-`only_fields` full-row path; lateral vs single-parent
  recognition arms.
- **Validation:** `uv run ruff format .` + `ruff check --fix .` on edited
  paths. Pytest deferred (maintainer gate).
- **Changelog:** no — internal projection completeness; no consumer API change.
- **Item-scoped diff vs `55e80be0…`:** `join_taxonomy.py`, `walker.py`,
  `nested_planner.py`, `tests/optimizer/test_join_taxonomy.py`,
  `tests/optimizer/test_walker.py`, this artifact.
- Ready for Worker 2. Plan checkbox left for W2.

## Iterations

### Fresh folder pass note (Worker 1)

Plan checkbox was still OPEN while Status said `verified`. This pass treated
present-day disk (14 modules, ~9512 lines) as a fresh folder integration and
did not seed findings from the prior verified body. Live Status / System
trace / Verification / Opportunities / Judgment / Implementation above
supersede the prior top-level prose. Prior reasoning preserved below as
audit trail only.

### Prior verified pass (schema dig consolidation)

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

Folder-level axes examined: duplicated policy split across modules; state
ownership (ContextVars published from `on_execute`, plan cache instance-bound,
context stash keys); competing helper layers (join taxonomy vs historical
shims; selections vs extension/walker adapters); public export flavor;
lifecycle work at plan vs fetch vs resolve; file-pass deferrals explicitly
handed to this folder pass (`_strawberry_schema` dig).

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

## Independent verification (Worker 2)

Re-traced present-day `optimizer/` (all 14 modules) against ITEM_BASELINE
`55e80be0b13e5a4416454d5fe53edfd29cc050cb` and the item-scoped diff
(`join_taxonomy.py` / `walker.py` / `nested_planner.py` /
`tests/optimizer/test_join_taxonomy.py` / `tests/optimizer/test_walker.py` /
this artifact). No production edits. Pytest deferred.

### prefetch_attach_columns consolidation — accepted

- Both projection writers now iterate
  `RelationJoinDescriptor.prefetch_attach_columns`:
  `walker._ensure_connector_only_fields` and
  `nested_planner._project_scalar_only_window`. Shared contract is
  attach-complete `.only()` columns (connector + GenericRelation morph), not
  the morph-first index-advisory equality prefix (still spelled separately in
  `_advise_composite_index` from `content_type_column` then
  `parent_join_column`).
- Django `GenericRelatedObjectManager.get_prefetch_querysets` builds
  `rel_obj_attr` as `(object_id, content_type_id)` — both halves must survive
  any `.only()` mask. Pre-fix walker path appended only
  `_connector_only_field` / `parent_join_column`, so list-prefetch and
  `edges { node { … } }` generic connections omitted the morph half; scalar-
  only already had both. Gap closed at the descriptor.
- Morph attname derivation remains solely in
  `join_taxonomy._generic_content_type_attname`. No leftover
  `content_type_field_name` + `get_field` re-spell in projection writers.
  `_connector_only_field` stays the historical single-column shim
  (`parent_join_column` only); attach completeness correctly bypasses it.
- Owner is clearer: the descriptor already owned the facts; the derived
  property states the attach-complete set once. Empty `only_fields` still
  means full-row load (no append); alias-late morph WHERE stays Django's.

### Rejected candidates — re-challenged, kept

1. Unify lateral + single-parent WHERE recognizers — already share
   `window_predicate_signature` / `_parent_in_values` / `_is_window_qual` /
   `_select_columns` / `_deduplicate_parent_ids`; lateral still needs keyset
   + visibility arms single-parent omits. Folding needs mode flags.
2. Shared QuerySet rebind for `LateralQuerySet` /
   `SingleParentWindowQuerySet` — parallel `_clone` /
   `_dst_window_signature` shape, different specs and fetch bodies.
3. Move `predicates.py` out of optimizer/ — no second EXISTS inside the
   folder; `OptimizerError` family + FilterSet consumer; project pass may
   revisit placement.
4. Delete walker underscore aliases / fold `_connector_only_field` — compat
   / load-bearing shim names; attach completeness no longer goes through the
   shim.
5. Walker walk-context dataclass; `_stash_union` into `_context.py`;
   generic `named_path_children`; dual `assert_window_fetch_mode_for` —
   same contracts as prior pass.
6. Schema dig / None-vs-100 — already owned outside the folder;
   policies intentionally distinct.

### Missed folder-level consolidations

Searched attach/connector/content_type projection sites, lateral vs
single-parent recognition, predicates vs plans, extension vs walker
lifecycle, and prior schema-dig ownership. No further folder-owned
lockstep rule beyond attach-complete projection. Index-advisory morph-first
order is a distinct contract from attach-key order and correctly stays
separate. `predicates.py` / `single_parent_fetch.py` do not introduce
competing policy layers.

### Item-scoped diff

Only the six claimed paths; no unrelated concurrent absorption.

### Disposition

All accepted and rejected findings disposed. Status → verified; plan
checkbox marked.

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
