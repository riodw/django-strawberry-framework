# DRY review: `django_strawberry_framework/optimizer/join_taxonomy.py`

Status: verified

## System trace

The target owns the **parent/child join-condition taxonomy** for nested-
connection fetch planning: one classification per raw Django relation
field/rel into a frozen `RelationJoinDescriptor`, plus the
`LateralJoinShape` enum and the exported `WINDOWABLE_RELATION_KINDS` set.

Owned responsibility:

- one join shape per relation (`DIRECT_FK` / `THROUGH_TABLE` /
  `UNSUPPORTED`) instead of per-consumer `relation_kind` string checks;
- one windowable-kind membership set + `partition_expr` (parent-side
  `PARTITION BY` key from `remote_field.attname or remote_field.name`);
- one `parent_join_column` (child-side prefetch-attach connector);
- one `through_model` + resolved through-link field pair
  (`parent_link_field` / `through_child_field`) for M2M / lateral SQL;
- classifier never raises — callers own fallback / raise posture
  (notably `window_partition_for_prefetch`'s dual `OptimizerError`
  messages).

Connected behavior examined:

- `utils/relations.py` — owns GraphQL/runtime `relation_kind`; this
  module consumes it and adds join-derived facts. Not a twin classifier.
- `optimizer/plans.py::window_partition_for_prefetch` — historical raise-
  contract shim over `classify_relation_join` + `partition_expr`.
- `optimizer/nested_planner.py::_connector_only_field` — historical shim
  over `parent_join_column`; also classifies once for nested-connection
  strategy requests (`join=classify_relation_join(raw_relation_field)`).
- `optimizer/nested_fetch.py::NestedConnectionRequest` — carries the
  descriptor; windowed attach reads `partition_expr`.
- `optimizer/lateral_fetch.py` — reads `lateral_shape` /
  `parent_link_field` / `through_child_field` only (no re-walk of
  `remote_field` / `m2m_*_field_name`).
- `optimizer/walker.py::_ensure_connector_only_fields` — list-prefetch
  projection via the connector shim; sibling item still open.
- `optimizer/field_meta.py` — snapshots connector attnames for synthetic
  doubles / elision; intentionally does **not** own join classification
  (needs live `remote_field` / through naming). Sibling verified
  zero-edit on that boundary.
- Pins: `tests/optimizer/test_join_taxonomy.py`; shim pins in
  `test_plans.py` / `test_walker.py`; builders in
  `tests/optimizer/_builders.py`; live nested-connection / M2M partition
  HTTP coverage in `examples/fakeshop/test_query/test_library_api.py`
  (and keyset/products siblings). Behavior unchanged by this pass — no
  new live pin earnable for a constant-export consolidation.
- Baseline
  `git diff 3894dc4c98e71bc62540dac68e60d3272a14795f -- …/join_taxonomy.py`
  was empty before this pass. Concurrent dirty optimizer siblings left
  untouched.

## Verification

Searches:

- `classify_relation_join` / `RelationJoinDescriptor` / `LateralJoinShape`
  / `partition_expr` / `parent_join_column` / `parent_link_field` /
  `through_child_field` / `_connector_only_field` /
  `window_partition_for_prefetch` — production join derivation is
  single-sited here; consumers are shims or descriptor readers.
- Optional `export_dry_review.py audit --target …/join_taxonomy.py`:
  7 definitions; reverse imports match plans / nested_planner /
  nested_fetch / lateral_fetch / tests. No exact-duplicate production
  bodies for the classifier helpers.
- Confirmed lockstep drift: `plans.py` re-listed
  `("many", "reverse_many_to_one", "reverse_one_to_one")` for its
  wrong-kind raise while the classifier used a private frozenset of the
  same members. Adding a new windowable kind to the classifier alone
  would make the shim raise incorrectly despite a resolved
  `partition_expr`.

Rejected / deferred candidates:

1. **Inline / delete the two historical shims**
   (`window_partition_for_prefetch`, `_connector_only_field`).
   Rejected: they own raise-logging contracts and call-site names pinned
   by tests; both already delegate to this module. Removing them is API
   churn without a second rule owner.

2. **Fold join facts into `FieldMeta` slots.** Disproved (matches
   field_meta review): classification needs live `remote_field` /
   through naming FieldMeta does not snapshot; FieldMeta's
   `reverse_connector_attname` / `target_field_attname` are synthetic-
   double fallbacks for this classifier, not a parallel taxonomy.

3. **Compose `WINDOWABLE_RELATION_KINDS` from
   `MANY_SIDE_RELATION_KINDS | {reverse_one_to_one}`.** Rejected:
   GraphQL list cardinality and fetch windowability are related but
   distinct axes; coupling them would make a future many-side-but-
   unwindowable kind impossible without splitting again. Explicit set
   stays at the join owner.

4. **Rewrite `_parent_join_column` to dispatch solely on `kind`
   (drop `one_to_many` / `many_to_many` flag reads).** Deferred: current
   flag+kind mix preserves the documented synthetic-double contract;
   stock Django fields already agree. Revisit only with a dedicated
   double-contract pin sweep (walker sibling touches the same shims).

5. **Thread already-classified `join` into
   `_project_scalar_only_window` to avoid a second `classify_relation_join`
   call on the scalar-only nested path.** Deferred: uses the owner
   twice, does not re-encode the rule; nested_planner micro-pass, not a
   join_taxonomy ownership bug.

## Opportunities

### 1. Single windowable-kind membership set for classifier + raise shim

- **Repeated responsibility:** which `RelationKind` values admit a
  windowed parent partition (membership before partition resolution).
- **Sites:** private frozenset in `join_taxonomy.py` (classifier);
  hardcoded 3-tuple in `plans.py::window_partition_for_prefetch`
  (wrong-kind vs unresolved-partition raise split).
- **Evidence:** identical members; shim cannot use
  `descriptor.windowable` alone because that AND-merges kind membership
  with partition resolution, collapsing the two historical error
  messages. Sites must change together when a new windowable kind lands.
- **Owner:** `optimizer/join_taxonomy.py` (export
  `WINDOWABLE_RELATION_KINDS`).
- **Consolidation:** rename/export the frozenset as
  `WINDOWABLE_RELATION_KINDS: frozenset[RelationKind]`; shim imports and
  membership-tests that set; classifier uses the same name.
- **Proof:** existing dual-raise pins in
  `tests/optimizer/test_plans.py::TestWindowPartitionForPrefetch`; new
  membership pin in `tests/optimizer/test_join_taxonomy.py`; live
  nested-connection partition behavior already covered under
  `examples/fakeshop/test_query/` (unchanged).
- **Risks / non-goals:** shim raise messages and never-raise classifier
  contract stay distinct; do not fold GraphQL `MANY_SIDE_RELATION_KINDS`
  into this set.

## Judgment

Historical join-derivation twins are already consolidated at this
module; consumers correctly read or shim. One remaining lockstep set
(windowable kinds) is exported and wired through the plans shim.
Ready for Worker 2.

## Implementation (Worker 1)

- **Owner chosen:** `optimizer/join_taxonomy.py::WINDOWABLE_RELATION_KINDS`
  (was private `_WINDOWABLE_KINDS`).
- **Migrated sites:**
  - `join_taxonomy.py` — public typed frozenset; classifier membership.
  - `plans.py::window_partition_for_prefetch` — imports and uses the set
    for the wrong-kind raise branch.
  - `tests/optimizer/test_join_taxonomy.py` — membership pin documenting
    the shim import contract.
- **Behavior kept separate:** dual `OptimizerError` messages on the shim;
  classifier still never raises; connector / FieldMeta / shim surfaces
  untouched beyond the kind-set import.
- **Validation:** `uv run ruff format .` and `uv run ruff check --fix .`
  after edits. No full pytest (per cycle rules). No changelog
  (internal ownership clarity; behavior unchanged).
- **Rejected findings:** see Verification — shims, FieldMeta fold,
  MANY_SIDE composition, kind-only connector dispatch, re-classify
  micro-pass.
- **Item-scoped diff vs baseline:** `join_taxonomy.py`, `plans.py`,
  `tests/optimizer/test_join_taxonomy.py`, and this artifact.

## Independent verification (Worker 2)

Re-traced ownership from `classify_relation_join` through
`window_partition_for_prefetch`, `nested_planner` (`join.windowable` gate +
`_connector_only_field` shim), `nested_fetch` / `lateral_fetch` descriptor
readers, `utils/relations.py::relation_kind` / `MANY_SIDE_RELATION_KINDS`, and
`FieldMeta` connector attnames. Item-scoped diff matches the claimed
constant-export consolidation only.

**WINDOWABLE_RELATION_KINDS consolidation — confirmed.** The historical
lockstep was real: classifier membership and the shim's wrong-kind raise
listed the same three `RelationKind` values. `descriptor.windowable` cannot
replace that membership test — it AND-merges kind membership with
`partition_expr` resolution, collapsing the two `OptimizerError` messages
pinned in `TestWindowPartitionForPrefetch`. Exporting the frozenset from the
join owner and importing it in the shim is the narrow correct fix; typing as
`frozenset[RelationKind]` is a strictness improvement over the old
`frozenset[str]`.

**Classifier ↔ plans alignment — confirmed.** Classifier:
`kind in WINDOWABLE_RELATION_KINDS` → optional `_partition_expr` →
`windowable = membership and partition is not None`. Shim: membership fail →
wrong-kind raise; else `partition_expr is None` → unresolved raise; else
return expression. `nested_planner` correctly consumes the AND-merged
`join.windowable` for plan-or-fallback (one message, not dual raise). No
other production site re-lists the three kinds for window/partition policy.

**Rejected candidates — all hold.**

1. **Keep shims** — they own raise/log contracts and pinned names; both
   already delegate. Deleting them is API churn, not a second rule owner.
2. **FieldMeta fold** — classification still needs live `remote_field` /
   through naming FieldMeta does not snapshot.
3. **Compose from `MANY_SIDE_RELATION_KINDS | {reverse_one_to_one}`** —
   GraphQL list cardinality ≠ fetch windowability. `reverse_one_to_one` is
   the live counterexample (windowable, not many-side). Coupling would force
   a future many-side-but-unwindowable kind to split again.
4. **Kind-only `_parent_join_column`** — correctly deferred; synthetic-double
   flag contract is out of this item's constant-export scope.
5. **Thread `join` into `_project_scalar_only_window`** — re-uses the owner,
   does not re-encode the rule; nested_planner micro-pass.

**Missed opportunities (disposed, not blocking):** a
`plans.WINDOWABLE_RELATION_KINDS is WINDOWABLE_RELATION_KINDS` identity pin
would harden import-site drift beyond the membership value pin; package
`optimizer/__init__` re-export is unnecessary for this internal contract.
Neither changes the ownership judgment.

**Tests:** `uv run pytest tests/optimizer/test_join_taxonomy.py
tests/optimizer/test_plans.py::TestWindowPartitionForPrefetch` — 14 passed
(partial-suite coverage gate irrelevant). Membership pin + dual-raise pins
cover the consolidated contract.

No production edits by Worker 2. No commit.
