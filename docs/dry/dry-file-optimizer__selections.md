# DRY review: `django_strawberry_framework/optimizer/selections.py`

Status: verified

## System trace

The target owns the **selection-tree traversal substrate** shared by the
optimizer's two GraphQL selection shapes:

- **AST adapter** — `ast_child_selections`, `resolve_unvisited_fragment`
  (name or `(name, depth)` visit key), `directive_variable_names`, plus the
  anonymous-safe AST→converted bridge (`ast_to_converted_selections`,
  `converted_selections_cache`, `prime_selected_fields`).
- **Converted-selection adapter** — fragment/directive/response-key policy
  (`is_fragment`, `should_include`, `response_key` / `response_keys`,
  `included_field_selections`, `named_children`), runtime-prefix cloning
  (`with_runtime_prefix`, `node_children_with_runtime_prefix`), Relay
  `edges { node }` unwrap (`connection_node_children`), and count /
  `hasNextPage` observability walks (`direct_child_selected`,
  `connection_total_count_selected`, `connection_has_next_page_selected`,
  `connection_count_required`).

Connected behavior examined:

- `optimizer/extension.py` — cache-key AST walks, reachable-fragment
  collection, root connection extractor, mutation payload extractor,
  `on_execute` memo install for `converted_selections_cache`; previously
  held a near-duplicate depth-keyed fragment resolve (migrated here).
- `optimizer/walker.py` — plan building; consumes converted helpers via
  underscore aliases (test-compat seam).
- `optimizer/nested_planner.py` — nested connection windows; thin
  `connection_node_children` adapter (from extension DRY); calls the two
  count observers separately for probe vs count.
- `connection.py` — `prime_selected_fields`, resolve-time
  `connection_total_count_selected` /
  `connection_has_next_page_selected` (same walks as plan-time).
- Pins: `tests/optimizer/test_selections.py`; deep coverage in
  `test_extension.py` / `test_walker.py` / `test_connection.py` and live
  anonymous-inline / nested-connection HTTP under
  `examples/fakeshop/test_query/`.

`connection_node_children` already owned here at ITEM_BASELINE (extension
DRY). Module is the intentional consolidation point for selection walking;
this pass is a fresh review of remaining cross-site drift.

## Verification

Searches / audit:

- Reverse imports limited to `extension`, `walker`, `nested_planner`,
  `connection`, and `tests/optimizer/test_selections.py`.
- `export_dry_review.py audit --target …/selections.py`: 18 definitions;
  no other production reimplementation of converted fragment/directive
  walks or `edges { node }` composition.
- `_unvisited_fragment_at_depth` in `extension.py` was byte-equivalent to
  `resolve_unvisited_fragment` except the visit key (`(name, depth)` vs
  `name`); both encode the same resolve + cycle-guard contract.
- `ast_to_converted_selections` re-spelled `selection_set.selections`
  access instead of calling `ast_child_selections`.
- `connection_count_required` has no production call site (planner needs
  the two observers separately); still the named OR of those observers
  and the unit-test contract pin — not dead duplication of a second walk.

Rejected / deferred:

1. **Unify AST `directive_variable_names` with converted `should_include`.**
   Disproved: AST extracts *variable names* for cache keys; converted
   evaluates already-resolved booleans. Same directive names, different
   contracts and change axes.

2. **Generic `named_path_children` / `slot_child_selections` folding
   mutation payload unwrap into `connection_node_children`.** Deferred
   (extension review + WP-C): mutation is one-level payload slot, not the
   Relay edges/node invariant; mode-shaped path helper would hide distinct
   GraphQL shapes.

3. **Inline `nested_planner._connection_node_selections`.** Rejected: one-line
   Decision-9 seam naming the nested unwrap; not a second implementation.

4. **Delete walker/extension underscore aliases.** Deferred: test-import
   compatibility; bodies already live here (folder / WP-C).

5. **Delete `connection_count_required` as unused.** Rejected: single named
   observability OR; planner intentionally splits observers for the
   count-free probe. Keep as composition API + pin.

6. **Polymorphic interface fragment classifier (TODO in
   `included_field_selections`).** Deferred to BACKLOG card; no production
   abstract-return entry yet.

## Opportunities

### 1. Keyed `resolve_unvisited_fragment` (AST fragment resolve once)

- **Repeated responsibility:** resolve a `FragmentSpreadNode` to its
  definition and mark a visit key so sibling/cyclic spreads are no-ops.
- **Sites:** `selections.resolve_unvisited_fragment` (name key);
  `extension._unvisited_fragment_at_depth` (`(name, depth)` key).
- **Evidence:** identical guard structure; only visit-key shape differs;
  both walks must stay aligned on missing-name / undefined-fragment /
  mutation-of-visited-set behavior (Decision 7 depth sensitivity).
- **Owner:** `optimizer/selections.py::resolve_unvisited_fragment`.
- **Consolidation:** optional `depth=` kwarg — omit → name key; supply →
  `(name, depth)`. Extension cache-var walk calls with `depth=`;
  reachable-fragment walk keeps the default. Delete
  `_unvisited_fragment_at_depth`.
- **Proof:** existing name-only pin; new
  `test_resolve_unvisited_fragment_depth_keys_visits_per_spread_site`;
  extension Decision-7 pagination / fragment suites remain the
  integration tier.
- **Risks / non-goals:** walk *policy* (when to pass depth) stays in
  extension; not a polymorphic AST/converted unifier.

### 2. Converter child iteration via `ast_child_selections`

- **Repeated responsibility:** read an AST node's selection-set children
  (including “no selection_set → empty”).
- **Sites:** `ast_child_selections`; three
  `getattr(...selection_set, "selections", [])` sites inside
  `ast_to_converted_selections`.
- **Evidence:** same null/empty contract; converter is the other AST
  consumer of child iteration in this module.
- **Owner:** `ast_child_selections`.
- **Consolidation:** `_convert` recurses through `ast_child_selections`.
- **Proof:** existing converter / anonymous-inline / memo pins; no new
  live pin earnable (behavior-identical).
- **Risks / non-goals:** none — faithful mirror of Strawberry conversion
  unchanged for non-anonymous shapes.

## Judgment

This module was already the DRY home for selection walking
(`connection_node_children`, converted helpers, count observers). The
remaining real drift was the depth-keyed fragment resolve still living in
`extension.py` as a near-copy, plus the converter bypassing
`ast_child_selections`. Both consolidated here. Ready for Worker 2.

## Implementation (Worker 1)

**Owner chosen:**

1. `selections.resolve_unvisited_fragment` as sole AST fragment-spread
   resolve + visit-key guard (optional `depth=`).
2. `ast_child_selections` as sole AST child-iteration helper used by the
   converter recursion.

**Migrated:**

- `django_strawberry_framework/optimizer/selections.py` — keyed resolve;
  converter uses `ast_child_selections`; module docstring updated.
- `django_strawberry_framework/optimizer/extension.py` — deleted
  `_unvisited_fragment_at_depth`; cache-var walk calls
  `resolve_unvisited_fragment(..., depth=child_depth)`; dropped unused
  `FragmentSpreadNode` import.
- `tests/optimizer/test_selections.py` — permanent depth-key pin.

**Kept separate:** AST vs converted directive adapters; mutation payload
extractor; nested_planner thin adapter; underscore aliases;
`connection_count_required` composition API; polymorphic classifier TODO.

**Validation:** `uv run ruff format` + `uv run ruff check --fix` +
`scripts/check_trailing_commas.py` on edited paths. No full pytest.
Changelog: no (internal DRY; not requested).

**Item-scoped paths for Worker 2:**

```text
git diff acb59ba3f3134b1137511fd05d952183e7821800 -- \
  django_strawberry_framework/optimizer/selections.py \
  django_strawberry_framework/optimizer/extension.py \
  tests/optimizer/test_selections.py \
  docs/dry/dry-file-optimizer__selections.md
```

## Independent verification (Worker 2)

Re-traced `selections.py` as the AST + converted selection-walk substrate through
`extension` (cache-var / reachable-fragment walks, root connection extractor),
`nested_planner` (thin edges→node adapter), `connection.py` (count observers),
and `walker` underscore aliases. Item-scoped diff matches the claimed migration:
`_unvisited_fragment_at_depth` deleted; depth-sensitive walk calls
`resolve_unvisited_fragment(..., depth=child_depth)`; converter recurses via
`ast_child_selections`; new depth-key pin added. No production edits by Worker 2.

### Challenge 1 — keyed `resolve_unvisited_fragment`

**Upheld.** Both baseline bodies were the same resolve + cycle-guard contract;
only the visit-key shape differed (`name` vs `(name, depth)`). Optional
`depth=` is a visit-key parameter of one rule, not a mode flag reconciling
distinct policies: name-only remains the default (reachable-fragment /
`_unvisited_fragment_definition` alias), and `depth=0` correctly uses
`(name, 0)` via the `None` sentinel rather than collapsing to name-only.
Walk *policy* (when to pass depth) stays in `extension._walk_cache_relevant_vars`.
No remaining production reimplementation of the guard.

### Challenge 2 — converter recursion via `ast_child_selections`

**Upheld.** The three baseline
`getattr(...selection_set, "selections", [])` sites shared the same
null/empty child-iteration contract as `ast_child_selections`. Scratch
equivalence on nested field / leaf / fragment-definition bodies: child lists
match after list-wrapping the tuple. Converter output shape unchanged
(`_convert` still returns a fresh list of Strawberry dataclasses); tuple vs
list input is iteration-only. Module is the correct owner — converter is the
other in-module AST consumer of child iteration.

### `connection_node_children` preserved

Confirmed at ITEM_BASELINE and unchanged in this diff. Still the sole
edges→node composition; `extension._connection_node_child_selections` and
`nested_planner._connection_node_selections` only supply path prefixes /
Decision-9 naming. No second unwrap elsewhere under `django_strawberry_framework/`.

### Rejected candidates (disposed)

1. **AST `directive_variable_names` ↔ converted `should_include`.** Upheld
   separate: variable-*name* extraction for cache keys vs already-resolved
   boolean evaluation. Same directive names, different contracts.
2. **Generic path helper folding mutation payload into
   `connection_node_children`.** Upheld separate: one-level payload slot vs
   Relay edges→node + runtime-prefix walk.
3. **Inline `nested_planner` adapter.** Upheld keep: one-line Decision-9 seam,
   not a second implementation.
4. **Delete walker/extension underscore aliases.** Upheld defer: test-import
   compatibility; bodies already live here.
5. **Delete `connection_count_required`.** Upheld keep: named OR of the two
   observers; planner intentionally splits them for the count-free probe;
   composition API + unit pin, not a second walk.
6. **Polymorphic fragment classifier TODO.** Upheld defer: BACKLOG; no
   abstract-return production entry yet.

### Tests / proof

- Permanent pins: name-only resolve, new
  `test_resolve_unvisited_fragment_depth_keys_visits_per_spread_site`,
  `ast_child_selections`, `connection_node_children`, converter memo.
- Focused pytest (5 pins): passed.
- Scratch: converter-child equivalence + `depth=0` sentinel; Decision-7
  integration remains in `tests/optimizer/test_extension.py`.

### Missed opportunities

None material for this target. No leftover
`selection_set.selections` getattr in production; no parallel fragment-resolve
guard; aliases are rebinds only. Further alias / mutation-path / polymorphic
work correctly deferred to folder / WP-C / BACKLOG.

**Outcome:** verified. Plan item checked.
