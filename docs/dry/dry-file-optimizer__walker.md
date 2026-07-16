# DRY review: `django_strawberry_framework/optimizer/walker.py`

Status: verified

## System trace

The target owns **selection-tree → `OptimizationPlan` planning**: walk
normalized GraphQL selections, resolve model/type/field namespaces, apply
Meta `OptimizerHint`s, emit `select_related` / `Prefetch` / `.only()` /
FK-id elisions / planned-resolver keys, and hand nested Relay connections
to `nested_planner` behind an atomic merge.

Owned responsibility:

- root `plan_optimizations` / `plan_relation` public planning entry;
- operation-wide G2 `enable_only` gate (`_enable_only_for_operation`)
  threaded once through every walk recursion;
- dual-contract field_map consumption (`FieldMeta | raw Django field` from
  `_resolve_field_map`) for scalar projection, relation dispatch, and
  FK-id elision;
- hint application (`_apply_hint`) — plan mutation, to_attr gates,
  rebase, force-select/prefetch routing;
- alias merge + per-response-key argument bookkeeping
  (`_merge_aliased_selections` / `_aliased_arguments_diverge` /
  conflict flag) consumed by nested-connection planning;
- B8 path→resolver-key ledgers for select and prefetch;
- nested-connection seam: inject walker-owned callables into
  `plan_connection_relation` so the private planner cannot import this
  module (cycle avoidance).

Connected behavior examined:

- `optimizer/field_meta.py` — stamp writer (`_from_field_shape`) and,
  after this pass, dual-contract readers `can_elide_fk_id` /
  `target_pk_name_of`;
- `optimizer/hints.py` — value type + `hint_is_skip`; apply stays here;
- `optimizer/plans.py` — plan shape, append helpers, finalize/merge;
- `optimizer/selections.py` — fragment/directive/response-key primitives
  (consumed via underscore aliases for historical test imports);
- `optimizer/nested_planner.py` — evidence only for connection
  delegation / callback injection (fresh review; not rewritten);
- `optimizer/join_taxonomy.py` — connector column via
  `_connector_only_field` shim;
- `optimizer/extension.py` — calls `plan_optimizations` /
  `plan_relation`; schema-name helper stays separate from walker's
  `_schema_name_converter` (different return contract);
- `types/resolvers.py` — `_field_meta_for_resolver` parallel dual-path
  that always returns `FieldMeta` (resolver-time, not field_map);
- `utils/relations.py` / `utils/querysets.py` — cardinality + visibility;
- Pins: `tests/optimizer/test_walker.py`, `test_field_meta.py`,
  extension/hints suites; live HTTP FK-id elision already earned in
  `examples/fakeshop/test_query/test_scalars_api.py`.
- Baseline `196e0ce41a953671ec91512ba58cb6c0bbd0b1f3`; concurrent dirty
  optimizer / docs / examples paths left untouched.

## Verification

Searches / reads:

- Full `walker.py` (~1457 lines) + field_meta dual-contract slots +
  hints apply deferral + nested_planner injection seam;
- `rg` for `_can_elide_fk_id` / `_target_pk_name` / `_apply_hint` /
  path-resolver ledgers / `RelationWalkContext` (absent);
- Deferred notes from verified `field_meta` / `hints` artifacts and the
  historical argument-bundle trigger (re-evaluated on present source,
  not imported as findings);
- Focused pins (5 passed): dual-contract readers + select-path ledger +
  id-only elision plan shape. Live elision HTTP coverage already exists;
  stamped-`None` contract is package-internal only.

Rejected / deferred candidates:

1. **Move `_apply_hint` onto `OptimizerHint` methods.** Rejected —
   apply mutates plan, enforces to_attr / consumer-assigned gates,
   rebases Prefetch lookups, and re-dispatches through
   `_dispatch_single_relation`. Value-type domain vs walker planning
   domain; `hint_is_skip` already single-sources skip predicate.

2. **Fold per-relation argument bundle into `RelationWalkContext`.**
   Deferred (trigger unmet) — shared
   `(plan, prefix, info, runtime_paths, resolver_identities, enable_only)`
   still threads through select/prefetch/hint/connection sites;
   `enable_only` remains the newest shared member. No further
   per-relation context member has landed. Dataclass would be
   net-neutral readability today; revisit when the next shared member
   appears (walker-internal / folder-scoped type).

3. **Share `_schema_name_converter` with extension
   `_strawberry_schema_from_info`.** Rejected — extension returns the
   Strawberry schema object; walker digs to `name_converter`. Hoisting
   a shared info→schema helper would be folder-scope and must not create
   walker→extension edges.

4. **Delete walker underscore aliases of `selections` /
   nested_planner helpers.** Deferred — test-import and historical
   private-import compatibility; selections sibling already parked this.

5. **Inline nested_planner callback injection** (pass module functions
   without kwargs). Rejected — intentional seam to keep nested_planner
   free of a walker import cycle.

## Opportunities

1. **Dual-contract FK-id / target-pk readers belong on `FieldMeta`.**

   - **Repeated responsibility:** `FieldMeta | raw Django field` slot
     reads for `fk_id_elision_eligible` and `target_pk_name`, with rebuild
     through `_from_field_shape` / model `_meta` for unstamped shapes.
   - **Sites:** former walker `_can_elide_fk_id` / `_target_pk_name`;
     stamp writer `FieldMeta._from_field_shape` / module `_target_pk_name`.
   - **Evidence:** elision rebuild already called
     `FieldMeta._from_field_shape`; walker's `_target_pk_name` used
     `getattr(..., None)` then rebuild, which treats stamped `None` as
     unstamped and can raise on a meta-less related-model stand-in.
     Bool elision slot is never ambiguous on `FieldMeta`; nullable
     `target_pk_name` requires `isinstance(FieldMeta)`.
   - **Owner:** `FieldMeta.can_elide_fk_id` /
     `FieldMeta.target_pk_name_of`.
   - **Consolidation:** classmethods own the dual-contract read;
     walker helpers become one-line delegates for local naming /
     historical call sites.
   - **Proof:** `tests/optimizer/test_field_meta.py` dual-contract pins
     (including stamped-`None`); existing walker / live HTTP elision
     pins remain the behavioral surface.
   - **Risks / non-goals:** module `_target_pk_name(model)` stays the
     defensive model helper; resolvers' `_field_meta_for_resolver`
     always returns `FieldMeta` and does not need these readers.

2. **Select-path B8 ledger twin of `_record_prefetch_path_keys`.**

   - **Repeated responsibility:** append-unique resolver keys onto a
     path→keys plan ledger.
   - **Sites:** `_record_prefetch_path_keys`; inline
     `select_path_resolver_keys` update in `_plan_select_relation`.
   - **Evidence:** same empty-guard + dedupe append; select path omitted
     the shared helper while prefetch had one.
   - **Owner:** walker `_record_path_resolver_keys` + thin
     prefetch/select wrappers.
   - **Consolidation:** one ledger primitive; both path families call it.
   - **Proof:** `test_record_select_path_keys_appends_unique_identities`
     + existing empty-prefetch pin.
   - **Risks / non-goals:** ledger maps stay distinct plan fields
     (different prune consumers).

## Judgment

Two consolidations implemented at true owners. Deferred argument-bundle
dataclass and `_apply_hint` relocation remain correctly parked. Ready for
Worker 2.

## Implementation (Worker 1)

- **Owner chosen:** `FieldMeta` for dual-contract slot readers; walker for
  B8 path-ledger primitive.
- **Migrated:**
  - `field_meta.py`: `FieldMeta.can_elide_fk_id`,
    `FieldMeta.target_pk_name_of` (isinstance-trust for stamped `None`);
  - `walker.py`: `_can_elide_fk_id` / `_target_pk_name` delegate;
    `_record_path_resolver_keys` + `_record_select_path_keys`;
    `_plan_select_relation` uses select-path helper;
  - tests: dual-contract pins in `test_field_meta.py`; select-path ledger
    pin in `test_walker.py`.
- **Kept separate:** `_apply_hint` on walker; nested_planner callback
  injection; selections/nested_planner underscore aliases;
  `RelationWalkContext` (trigger unmet); extension schema helpers.
- **Validation:** `uv run ruff format .` + `uv run ruff check --fix .`;
  focused pytest 5/5 passed (full-suite coverage gate not run — not
  final gate). Live FK-id elision HTTP suite already exists; new pins
  are package-level dual-contract / ledger contracts.
- **Changelog:** no — internal ownership / correctness of adapters;
  no public API change requiring changelog without maintainer ask.
- **Ready for Worker 2:** yes.

## Independent verification (Worker 2)

Re-traced selection→plan ownership through `field_meta` dual-contract
readers, walker adapters, `_plan_select_relation` / `_plan_prefetch_relation`
B8 ledgers, `_apply_hint`, and nested_planner injection. Scoped diff vs
`196e0ce41a953671ec91512ba58cb6c0bbd0b1f3` matches the claimed two
consolidations only (plus permanent pins).

Challenged consolidations:

1. **Dual-contract readers on `FieldMeta` (stamped-`None` especially).**
   Confirmed shared responsibility: walker `field_map` is
   `FieldMeta | raw Django field`; stamp writer is
   `_from_field_shape` / module `_target_pk_name(model)`. Old walker
   `_target_pk_name` used `getattr`-then-rebuild, so stamped `None` was
   treated as unstamped and raised `AttributeError` on a meta-less
   `related_model` stand-in (scratch-proved). New
   `FieldMeta.target_pk_name_of` uses `isinstance(FieldMeta)` and trusts
   stamped `None`. Divergent case `FieldMeta(related_model=RealModel,
   target_pk_name=None)` would old-rebuild to `"id"` and new-return
   `None` — stamper never produces that shape (`target_pk_name is None`
   iff related model lacks resolvable `_meta`; elision bool also False).
   Duck-typed non-`FieldMeta` still treats `None` as unstamped and uses
   the defensive model helper (no raise). `can_elide_fk_id` isinstance
   path is isomorphic for the always-bool slot. Thin walker delegates
   remain correct local adapters. Pins cover both contracts.

2. **B8 path-key recording unified.** Confirmed identical empty-guard +
   dedupe-append; select path previously inlined what prefetch already
   helperized. `_record_path_resolver_keys` + thin select/prefetch
   wrappers; ledger maps stay distinct plan fields (prune consumers
   differ). `plans.merge_from` path-key loops are merge-phase, not a
   missed twin of the record primitive.

Deferred / rejected (still correct):

- **`RelationWalkContext`** — absent; trigger unmet (`enable_only` still
  newest shared member; bundle still threaded at select/prefetch/hint/
  connection sites).
- **`_apply_hint` on walker** — stays; mutates plan, enforces to_attr /
  consumer-assigned gates, rebases Prefetch, re-dispatches — not
  `OptimizerHint` value-type domain.
- Nested_planner callback injection and selections underscore aliases —
  intentional seams; not absorbed.

Missed opportunities: none material for this target. Optional wording
drift in `utils.relations.has_composite_pk` (still names "two" elision
paths) is docstring-only and belongs with a relations/folder pass, not
this item.

Validation: focused pins 5/5 passed (coverage gate expected-fail on
narrow run). Scratch proved old raise vs new `None` for stamped-`None`
+ meta-less stand-in.

Verdict: verified.
