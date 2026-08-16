# DRY review: `django_strawberry_framework/optimizer/nested_planner.py`

Status: verified

## System trace

The target is the **transactional planner for one recognized nested Relay
connection**. The walker normalizes selections and resolves model/type
metadata, then delegates one connection selection to
`plan_connection_relation`. That entry point owns pagination normalization
(plan-time int coercion + shared window-bounds adapters), Decision-6 fallback
classification, child-queryset construction (via walker-injected builders),
fetch-strategy dispatch (`NestedConnectionRequest` + active/hinted strategy),
acceptance bookkeeping (`NestedConnectionPlanResult` / `accepted_response_keys`),
the scalar-only `.only()` projection, keyset cursor-column projection extension,
and the composite-index advisory. It builds a private plan and returns it only
after orchestration completes, so refusal or exception cannot leak partial
directives into the walker's parent plan.

Ownership already delegated out (re-confirmed on present-day source):

- Window bounds / `FetchMode` / sidecar detection → `utils/connections.py`
- Order-entry name/direction parse + explicit-NULLS predicate → `plans.py`
- Relation connector + GenericRelation morph column → `join_taxonomy.classify_relation_join`
- `edges { node }` unwrap + count/`hasNextPage` observers → `selections.py`
- Schema config dig → `utils/typing.schema_config_from_info`
- Strategy registry / unwindowable child QS gate → `nested_fetch.py`
- `_dst_<field>_connection` / per-key `$` namespace → this file (consumed by
  `connection.py` resolve probe)
- Plan-time `_coerce_pagination_int` → this file (walker re-exports for
  argument-comparison; resolve path receives already-coerced Strawberry args)

Connected surfaces re-traced: `walker.py` (sole caller + underscore rebinds),
`nested_fetch.py` / `lateral_fetch.py` / `single_parent_fetch.py` / `plans.py`,
`connection.py` / `utils/connections.py` / `keyset.py`, `join_taxonomy.py`,
`selections.py`, `field_meta.py`. Folder integration `optimizer/` stays out of
scope.

## Verification

- Item baseline `ad9c7d382f04f31fcbc04f4343b3495592f8441b`: target file was
  byte-identical at pass start; present-day ~1548 lines re-read end to end.
- Grepped package-wide for window bounds, `FetchMode`, sidecar kwargs,
  `to_attr` / `_dst_`, nulls placement, connector / content_type columns,
  `unwindowable_child_queryset_reason`, strategy resolve, `last: 0`,
  `relay_max_results`, coerce-pagination, `deferred_loading_of` /
  `_extend_only_projection`, concrete-order helpers, index advisory.
- Compared plan-time adapters (`_connection_window_slice*` /
  `_keyset_window_slice_from_arguments`) to resolve-time
  `connection.py` / `derive_*_window_bounds` consumers: shared bounds owners;
  plan-only coercion and `None`-vs-propagate error locality remain intentional.
- Disproved merging `_concrete_order_columns` with `_concrete_order_terms`
  (skip vs fail-soft `None`), offset with keyset adapters (fork before
  `SliceMetadata`), divergent vs single-window `last: 0` gates (parallel scheme
  arms), and deleting walker rebinds (test/historical seams, not second bodies).
- Accepted two ownership gaps revealed by the fresh pass (below).

## Opportunities

### 1. Explicit-NULLS order-entry predicate on `plans` (accepted)

- **Repeated responsibility:** decide whether an order entry carries explicit
  `nulls_first` / `nulls_last` (non-`None`), as part of the shared
  `deterministic_order` entry vocabulary.
- **Sites:** `nested_planner._has_explicit_nulls_placement` (index-advisory
  UNKNOWN); `connection._keyset_order_ref` (reject for value cursors).
- **Evidence:** both ask the same factual question about an `OrderBy` entry;
  prior sites used `is not None` vs truthy and could drift if the vocabulary
  definition of "explicit" changes. Consequences differ by caller (advisory
  silence vs keyset reject) — same pattern as `order_entry_name_and_direction`.
- **Owner:** `plans.py::order_entry_has_explicit_nulls` beside
  `order_entry_name_and_direction`.
- **Consolidation:** move the predicate; nested planner and keyset order-ref
  both call it (`is not None` contract).
- **Proof:** `tests/optimizer/test_plans.py::TestOrderEntryHasExplicitNulls`;
  existing nulls-UNKNOWN pins in `test_nested_index_advisory.py` and
  `_keyset_order_ref` nulls reject in `test_keyset_connection.py` remain the
  integration tier (deferred pytest).
- **Risks / non-goals:** do not fold `_reverse_order_by`'s nulls *swap* into
  this predicate (mutation vs detection). Do not unify advisory UNKNOWN with
  keyset reject policies.

### 2. Scalar-only GenericRelation morph column via join taxonomy (accepted)

- **Repeated responsibility:** resolve the child `content_type_id` attname a
  `GenericRelation` prefetch attach needs alongside the object-id connector.
- **Sites:** `join_taxonomy._generic_content_type_attname` /
  `RelationJoinDescriptor.content_type_column` (owner);
  `_project_scalar_only_window` re-spelled `content_type_field_name` +
  `get_field(...).attname`.
- **Evidence:** identical derivation; advisory path already consumed
  `join.content_type_column`; scalar-only projection must stay lockstep or a
  rename of the morph field updates one site only.
- **Owner:** `classify_relation_join` / `content_type_column`.
- **Consolidation:** `_project_scalar_only_window` classifies once and takes
  `parent_join_column` + `content_type_column` (drops the local re-derivation;
  `_connector_only_field` remains the walker list-prefetch shim).
- **Proof:** `tests/optimizer/test_walker.py::test_scalar_only_generic_window_projects_content_type_column`
  (deferred pytest).
- **Risks / non-goals:** do not move list-prefetch
  `_ensure_connector_only_fields` content_type policy here — that is walker /
  folder scope (see deferred).

## Judgment

Present-day `nested_planner.py` remains a clean orchestrator over shared window,
join, order, selection, and strategy owners. The fresh pass found two real
vocabulary/ownership gaps (explicit NULLS; GenericRelation morph attname) and
closed them at `plans.py` and `join_taxonomy` respectively. Remaining
similarities are intentional forks, named shims, or walker rebinds — not
competing implementations. Folder-level list-prefetch connector completeness
for GenericRelation is deferred.

## Implementation (Worker 1)

**Owner chosen:**

1. `plans.py::order_entry_has_explicit_nulls` for the shared explicit-NULLS
   order-entry vocabulary gate.
2. `join_taxonomy.classify_relation_join` / `content_type_column` for the
   scalar-only GenericRelation morph column (consumed in
   `_project_scalar_only_window`).

**Migrated:**

- `optimizer/plans.py` — added `order_entry_has_explicit_nulls`.
- `optimizer/nested_planner.py` — dropped `_has_explicit_nulls_placement`;
  `_concrete_order_terms` calls the plans predicate; `_project_scalar_only_window`
  classifies once for connector + content_type; `_connector_only_field`
  docstring updated (walker-only shim).
- `connection.py` — `_keyset_order_ref` uses `order_entry_has_explicit_nulls`.
- `utils/connections.py` — module docstring corrects coerce ownership to
  `nested_planner` (walker re-export noted).
- `tests/optimizer/test_plans.py` — `TestOrderEntryHasExplicitNulls`.
- `tests/optimizer/test_walker.py` —
  `test_scalar_only_generic_window_projects_content_type_column`.

**Kept separate:** offset vs keyset window adapters; planner `None` vs resolver
`100`; `_concrete_order_columns` vs `_concrete_order_terms`; walker underscore
rebinds; `_ensure_connector_only_fields` list-prefetch path; composite-index
advisory body (true owner of that advisory remains this file).

**Validation:** `uv run ruff format .` and `uv run ruff check --fix .`. No
pytest (deferred). Changelog: no (internal ownership; no consumer API change).

**Item-scoped diff statement (from ITEM_BASELINE `ad9c7d38`):**

```text
git diff ad9c7d382f04f31fcbc04f4343b3495592f8441b -- \
  django_strawberry_framework/optimizer/nested_planner.py \
  django_strawberry_framework/optimizer/plans.py \
  django_strawberry_framework/connection.py \
  django_strawberry_framework/utils/connections.py \
  tests/optimizer/test_plans.py \
  tests/optimizer/test_walker.py \
  docs/dry/dry-file-optimizer__nested_planner.md
```

(~99 insertions / 33 deletions across those paths at handoff.)

**Deferred findings:**

1. `_ensure_connector_only_fields` (walker) still appends only
   `parent_join_column`, not `content_type_column`, for GenericRelation list
   prefetches — folder / walker item.
2. Deferred pytest for the new permanent tests above.

**Strongest rejected candidates:** merge concrete-order siblings; unify
offset/keyset adapters; delete walker rebinds; fold reverse-order nulls *swap*
into the new predicate; absorb folder splits into this file.

**Ready for W2:** yes.

## Iterations

### Fresh pass note

Plan checkbox was still OPEN while Status said `verified`. This Worker 1 pass
re-reviewed present-day source without seeding findings from the prior body.
Live Status / System trace / Verification / Opportunities / Judgment /
Implementation above supersede the prior top-level prose. Prior reasoning is
preserved below as audit trail only.

### Prior verified pass (schema dig + edges/node)

## System trace

The target is the **transactional planner for one recognized nested Relay
connection**. The general walker normalizes selections and resolves
model/type metadata, then delegates a single connection selection to
`plan_connection_relation`, which owns pagination normalization, Decision-6
fallback classification, child-queryset construction, fetch-strategy dispatch,
and acceptance bookkeeping. It builds a private `NestedConnectionPlanResult`
and returns it only after orchestration completes, so a refusal or exception
cannot leak partial directives into the walker's parent plan.

The file already delegates most cross-module invariants to their owners and
keeps only thin, intentionally-named shims:

- `_connector_only_field` -> `join_taxonomy.classify_relation_join`
  (`parent_join_column`), kept under the historical name for its two callers
  and the direct test-double pins.
- `_order_entry_field_name` -> `plans.order_entry_name_and_direction`
  (name half of the shared entry parser).
- `_connection_window_slice*` -> `utils/connections.derive_connection_window_bounds`;
  `_keyset_window_slice_from_arguments` -> `derive_keyset_window_bounds` +
  the canonical keyset codec, so plan-time and resolve-time windows agree by
  construction.
- `_relation_connection_to_attr` / `_relation_connection_to_attr_for_key` own
  the `_dst_` namespace literals shared with the resolve-side probe in
  `connection.py`.

Connected behavior re-traced for this pass (not inherited as proven):

- `optimizer/walker.py` — the sole planner caller; re-exports several
  nested_planner helpers under underscore aliases (`_relay_max_results_from_info`,
  `_relation_connection_to_attr*`) as a test-import / historical seam.
- `optimizer/selections.py` — the AST + converted selection-walk substrate;
  owns `connection_node_children` (the Relay `edges { node }` composition) and
  the count / `hasNextPage` observers this planner consumes.
- `optimizer/extension.py` — the middleware layer that hands the walker the raw
  graphql-core `info`; previously carried its own copy of the Strawberry
  schema-wrapper dig (`_strawberry_schema_from_*`) and its own root-seam
  `edges { node }` extractor.
- `utils/connections.py` — window-bounds contracts and
  `resolve_relay_max_results` (the resolve-time cap, terminal `100`).
- `utils/typing.py` — the new cycle-safe home of the Strawberry-private
  `_strawberry_schema` / `.config` digs.
- `nested_fetch.py` / `lateral_fetch.py` — the strategy seam consuming the
  planned `NestedConnectionRequest`s.
- Pins: `tests/optimizer/test_walker.py` (planner window shapes, the
  `relay_max_results` `None` contract, divergent-alias windows),
  `tests/optimizer/test_selections.py` (the shared `edges { node }` unwrap),
  live nested-connection HTTP under `examples/fakeshop/test_query/`.

Two folder-visible lockstep rules still spelled locally in this file at the
item baseline are the subject of this pass: the Strawberry schema/config dig
and the Relay `edges { node }` composition. Both are consolidated to their true
owners; nothing else in the file is a competing implementation.

## Verification

- Item baseline for the standing diff is `4d46e634` (the commit preceding this
  consolidation slice). The nested_planner changes are hunk-split across two
  commits (see **Scope** below); the reasoning here covers the full change set.
- Re-read `nested_planner.py` end to end and its two live consumers
  (`walker.py`, `connection.py`) plus the two owners it now delegates to
  (`utils/typing.py`, `selections.py`).
- Grepped the package for `_strawberry_schema`, `getattr(..., "config"`,
  `getattr(..., "relay_max_results"`, `getattr(..., "name_converter"`,
  `named_children(`, `connection_node_children`, and the walker re-export
  aliases.
- Confirmed `_relay_max_results_from_info` was a byte-identical getattr chain
  to `walker._schema_name_converter`, `connections.resolve_relay_max_results`,
  and `extension._strawberry_schema_from_*` before the move — same brittle
  private attribute, must change together, cycle-blocked from importing
  extension (extension imports walker imports nested_planner).
- Confirmed `_connection_node_selections`'s inline `edges`/`node` fan-out was a
  re-spelling of `selections.connection_node_children` (the same
  `named_children("edges")` -> per-key `response_key` prefix ->
  `named_children("node")` -> `node_children_with_runtime_prefix` composition
  the root seam in `extension.py` also duplicated).
- Confirmed the planner's `None`-on-missing-config policy is deliberately
  distinct from the resolver's terminal `100` (see **Opportunity 1**,
  risks/non-goals).

## Scope (hunk split across two commits)

nested_planner is hunk-split; this report reflects the FULL change set and
names where each hunk lands:

- **Commit 9 — `refactor(optimizer): centralize Strawberry schema config
  access`.** The `from ..utils.typing import schema_config_from_info` import and
  `_relay_max_results_from_info` delegating to it (Opportunity 1). This report
  is authored and committed with that slice.
- **Commit 10 — `refactor(optimizer): consolidate selection traversal and
  lifecycle state`.** The `selections` import change (drop the local
  `named_children` / `response_key` / `node_children_with_runtime_prefix`
  aliases, add `connection_node_children`) and `_connection_node_selections`
  becoming a one-line adapter (Opportunity 2). The plan checkbox for this item
  and the folder item close with that slice.

## Opportunities

### 1. Strawberry schema/config dig on `utils.typing` (accepted — Commit 9)

- **Repeated responsibility:** read Strawberry's private
  `schema._strawberry_schema.config` (with a `schema.config` fallback) from a
  plan-time graphql-core `info` whose `.schema` is a bare `GraphQLSchema` with
  no `.config`.
- **Sites:** `nested_planner._relay_max_results_from_info`;
  `walker._schema_name_converter`; `connections.resolve_relay_max_results`;
  `extension._strawberry_schema_from_*` (the schema-wrapper half).
- **Evidence:** byte-identical getattr chains; the same brittle private
  attribute name; all must change together if Strawberry renames the backref.
  Extension cannot own the dig without creating a `walker -> extension` or
  `connections -> optimizer` import cycle.
- **Owner:** `utils/typing.py::schema_config_from_info` (plus the
  `strawberry_schema_from_schema` / `strawberry_schema_from_info` wrapper
  helpers the extension consumes directly).
- **Consolidation:** `_relay_max_results_from_info` becomes
  `getattr(schema_config_from_info(info), "relay_max_results", None)`; the dig's
  wrapped-then-direct preference lives in one place.
- **Proof:** `tests/utils/test_typing.py::test_schema_config_from_info_prefers_wrapped_then_direct`,
  `test_schema_config_from_info_explicit_none_wrapped_falls_back_to_direct`
  (the value-is-`None` fallthrough), `test_strawberry_schema_from_info_and_schema`;
  existing `tests/optimizer/test_walker.py` planner-`None` pins remain the
  integration tier.
- **Risks / non-goals:** do NOT unify the planner's `None` (engine default
  applies downstream) with the keyset resolver's terminal `100`
  (`_RELAY_MAX_RESULTS_DEFAULT`). Same dig, different missing-config policy: the
  planner defers to `SliceMetadata`'s own fallback, the resolver cannot and must
  supply the numeric cap. The attribute READ (`relay_max_results` vs
  `name_converter`) on the shared config object is not a second dig to fold.

### 2. Relay `edges { node }` composition on `selections` (accepted — Commit 10)

- **Repeated responsibility:** unwrap a connection selection's
  `edges { node { ... } }` into node-level child selections carrying the
  connection-aware runtime prefixes (for strictness / FK-id-elision resolver
  keys), with an empty list for a scalar-only (`pageInfo` / `totalCount`)
  selection.
- **Sites:** `nested_planner._connection_node_selections` (nested windows);
  `extension._connection_node_child_selections` (root apply seam);
  `selections.connection_node_children` (already the owner at baseline).
- **Evidence:** the same `named_children("edges")` -> `response_key` prefix
  fan-out -> `named_children("node")` -> `node_children_with_runtime_prefix`
  composition, re-spelled per site; they must stay lockstep so root apply and
  nested planning derive identical prefixes / strictness keys.
- **Owner:** `optimizer/selections.py::connection_node_children`.
- **Consolidation:** `_connection_node_selections` becomes a one-line adapter
  (`return connection_node_children(sel, runtime_prefixes=runtime_paths)`),
  preserving the Decision-9 name and the Decision-6 scalar-only `[]` contract;
  the local `named_children` / `response_key` /
  `node_children_with_runtime_prefix` imports are dropped.
- **Proof:** `tests/optimizer/test_selections.py` composition + empty-shape
  pins; existing nested-connection HTTP suites remain the integration tier.
- **Risks / non-goals:** keep the one-line seam and its Decision-9 docstring —
  it is the nested-planner's named entry into the shared unwrap, not a second
  implementation. The mutation payload extractor (one-level slot) stays
  separate.

## Judgment

The file was already a clean orchestrator delegating windows, joins, ordering,
and `to_attr` namespaces to their owners. The two remaining folder-visible
lockstep rules still spelled locally — the Strawberry schema/config dig and the
`edges { node }` composition — are consolidated to `utils/typing.py` and
`selections.py` respectively. Everything else (the connector / order-entry /
`to_attr` shims, the Decision-6 fallback ladder, the keyset/offset window fork,
the divergent-alias scheme) is intentional single-sited orchestration or a
load-bearing named shim, not duplication.

### Rejected / deferred (re-proved)

1. **Fold `_connector_only_field` / `_order_entry_field_name` into call sites.**
   Rejected — already one-line shims over `classify_relation_join` /
   `order_entry_name_and_direction`; the names and test-double pins are
   load-bearing.
2. **Inline the `_connection_node_selections` adapter.** Rejected — one-line
   Decision-9 seam naming the nested unwrap; not a second implementation.
3. **Delete walker underscore re-exports of nested_planner helpers.** Deferred
   — test-import and historical private-import compatibility; rebinds, not
   competing implementations.
4. **Unify the offset and keyset window adapters
   (`_connection_window_slice_from_arguments` /
   `_keyset_window_slice_from_arguments`).** Rejected — they fork BEFORE the
   offset engine (`SliceMetadata` cannot parse a value cursor); different bound
   derivations and error vocabularies (`GraphQLError` for a tampered cursor).
5. **Merge the planner `None` and resolver `100` missing-config policies.**
   Rejected — phase-distinct (see Opportunity 1 risks); unifying breaks
   `tests/optimizer/test_walker.py` / `tests/test_keyset.py`.

## Implementation (Worker 1)

**Owner chosen:**

1. `utils/typing.py::schema_config_from_info` as the sole info-based Strawberry
   schema/config dig (Commit 9).
2. `selections.connection_node_children` as the sole `edges { node }`
   composition; `_connection_node_selections` is a one-line adapter (Commit 10).

**Migrated:**

- `django_strawberry_framework/optimizer/nested_planner.py` —
  `_relay_max_results_from_info` delegates to `schema_config_from_info`
  (docstring updated to name the shared owner and the `None`-vs-`100` split);
  `_connection_node_selections` thin-adapts `connection_node_children`; dropped
  the local `named_children` / `response_key` / `node_children_with_runtime_prefix`
  imports.
- Owners edited by the sibling items: `utils/typing.py` (dig helpers),
  `utils/connections.py` / `walker.py` / `extension.py` (call-site migration),
  `selections.py` (composition already owned there).
- `tests/utils/test_typing.py` — dig pins incl. the explicit-`None` fallthrough.

**Kept separate:** planner `None` vs resolver terminal `100`; offset vs keyset
window adapters; connector / order-entry / `to_attr` shims; walker underscore
re-exports; mutation payload extractor.

**Validation:** `uv run ruff format` + `uv run ruff check --fix` +
`scripts/check_trailing_commas.py` on edited paths. No full pytest. Changelog:
no (internal ownership move, no consumer-facing API change).

**Item-scoped paths for Worker 2:**

```text
git diff 4d46e634 -- \
  django_strawberry_framework/optimizer/nested_planner.py \
  django_strawberry_framework/utils/typing.py \
  django_strawberry_framework/optimizer/selections.py \
  tests/utils/test_typing.py \
  docs/dry/dry-file-optimizer__nested_planner.md
```

## Independent verification (Worker 2)

Re-traced `nested_planner.py` as the transactional nested-connection planner
against final source (working tree at the Commit 9/10 slice), through its
caller (`walker.py`), the two owners it delegates to (`utils/typing.py`,
`selections.py`), and the resolve-side probe (`connection.py`). No production
edits by Worker 2.

### Challenge 1 — schema/config dig on `utils.typing`

**Upheld.** `rg '_strawberry_schema'` over `django_strawberry_framework/`
finds the raw getattr traversal ONLY in `utils/typing.py`; every other hit is a
CALL to the aliased helper (`extension.py`) or a docstring/comment. The plan-time
`_relay_max_results_from_info`, the resolve-time
`connections.resolve_relay_max_results`, and `walker._schema_name_converter`
all read the shared config object through `schema_config_from_info`. Owner on
`utils/typing` is cycle-safe (walker / connections / nested_planner cannot import
extension). The dig's wrapped-then-direct preference matches the pre-move triple.

### Challenge 2 — `None` vs terminal `100` kept distinct

**Upheld.** `_relay_max_results_from_info` returns
`getattr(schema_config_from_info(info), "relay_max_results", None)` — `None` when
no config, so `SliceMetadata.from_arguments` applies the engine default.
`resolve_relay_max_results` returns `cap if cap is not None else 100`
(`_RELAY_MAX_RESULTS_DEFAULT`). Same dig, forked missing-config policy. Merging
would blur the plan-time / resolve-time fork and break the walker / keyset pins.

### Challenge 3 — `edges { node }` composition on `selections`

**Upheld.** `_connection_node_selections` is a one-line adapter over
`connection_node_children`; the local `named_children` / `response_key` /
`node_children_with_runtime_prefix` imports are gone. `rg 'named_children\('`
shows the `edges`/`node` fan-out lives only inside
`selections.connection_node_children`. The nested seam preserves Decision-6
scalar-only `[]` and the Decision-9 name. Mutation payload extractor correctly
separate.

### Adjacent digs re-checked — not this item

- `extension.py` `getattr(schema, "_schema", None)` is the graphql-core inner
  schema (`_schema`, a different private attribute for reachable-type walking),
  not the `_strawberry_schema` backref; out of scope.
- `management/commands/inspect_django_type.py` reads
  `getattr(schema_object, "config", None)` off a Strawberry `Schema` OBJECT in
  hand (and `scalar_map`), not from an `info`; a different shape (no
  `_strawberry_schema` unwrap), owned by that command. Not a missed
  consolidation for this item.

### Rejected candidates — re-challenged, kept

1. connector / order-entry shims — thin, load-bearing names / pins.
2. inline `_connection_node_selections` — one-line Decision-9 seam.
3. walker underscore re-exports — rebinds, not implementations.
4. offset vs keyset window adapters — fork before the offset engine.
5. planner `None` vs resolver `100` — phase-distinct policy.

### Tests

Focused pins: `test_schema_config_from_info_prefers_wrapped_then_direct`,
`test_schema_config_from_info_explicit_none_wrapped_falls_back_to_direct`,
`test_strawberry_schema_from_info_and_schema`, and the
`connection_node_children` composition pins in `test_selections.py`. Planner
`None` and divergent-alias windows stay pinned in `test_walker.py`. No full
pytest.

### Missed opportunities

None material for this target. No leftover raw `_strawberry_schema` traversal
outside `utils/typing.py`; no duplicate `edges { node }` unwrap outside
`selections.connection_node_children`; remaining shims and forks are
intentional.

**Disposition:** verified. Full change set covered; the plan checkbox for this
item closes with the Commit 10 selection slice that lands the second hunk.

## Independent verification (Worker 2)

Re-traced `nested_planner.py` as the transactional nested-connection planner
against present-day source and the item-scoped diff from baseline
`ad9c7d382f04f31fcbc04f4343b3495592f8441b`. No production edits by Worker 2.
Scoped paths match W1's claim exactly (nested_planner / plans / connection /
utils/connections / two permanent tests / this artifact) — no unrelated
concurrent cleanup absorbed.

### Challenge 1 — explicit-NULLS vocabulary on `plans`

**Upheld.** Baseline had two predicates with the same factual question and
divergent definitions: nested_planner `_has_explicit_nulls_placement` used
`is not None`; `connection._keyset_order_ref` used truthy `or`. Present-day:
`_has_explicit_nulls_placement` is gone; both call sites import
`plans.order_entry_has_explicit_nulls` (`is not None`). `rg` finds no leftover
private duplicate. Owner sits beside `order_entry_name_and_direction` — same
`deterministic_order` entry vocabulary, one reason to change. Callers keep
distinct consequences (advisory UNKNOWN via `_concrete_order_terms` → `None`
vs keyset reject → `None` from `_keyset_order_ref`).

### Challenge 2 — scalar-only GenericRelation morph via join taxonomy

**Upheld.** Baseline `_project_scalar_only_window` re-derived the morph column
via `content_type_field_name` + `get_field(...).attname` while the composite-
index advisory already consumed `join.content_type_column`. Present-day: one
`classify_relation_join`; connector and morph both come from the descriptor.
Package `content_type_field_name` + `get_field` derivation for this attname
lives only in `join_taxonomy._generic_content_type_attname`. `_connector_only_field`
correctly remains the walker list-prefetch shim (parent_join only).

### Challenge 3 — rejected / deferred kept separate

**Upheld.**

1. `_concrete_order_columns` vs `_concrete_order_terms` — skip vs fail-soft
   `None`; different contracts.
2. Offset vs keyset window adapters — fork before `SliceMetadata`.
3. Walker underscore rebinds — rebinds, not second bodies.
4. `_reverse_order_by` nulls *swap* — mutation (`if nulls_first or nulls_last`
   then swap), not the detection predicate; folding would blur detection vs
   reverse semantics.
5. `_ensure_connector_only_fields` still appends only
   `_connector_only_field` / `parent_join_column` — deferred to walker /
   folder as claimed (read present-day walker body).
6. `utils/connections.py` docstring — corrects coerce ownership to
   `nested_planner` (walker re-export); item-scoped doc fix, not drive-by.

### Proof / deferred

Permanent pins present: `TestOrderEntryHasExplicitNulls`;
`test_scalar_only_generic_window_projects_content_type_column`. Integration
pins remain in `test_nested_index_advisory.py` / `test_keyset_connection.py`.
Pytest deferred per cycle rules. Optional strengthening (not a blocker): pin
`nulls_first=False` so the `is not None` vs truthy axis cannot regress while
still passing the `True`-only unit cases.

### Missed opportunities

None material for this target. No leftover private NULLS predicate; no
re-spelled GenericRelation morph attname outside `join_taxonomy`.

**Disposition:** verified. Plan checkbox marked `[x]`.


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
