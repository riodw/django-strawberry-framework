# DRY review: folder `django_strawberry_framework/orders/`

Status: verified

## System trace

`orders/` is the six-layer ordering component (spec-028): declarative
`OrderSet` classes become GraphQL `orderBy:` arguments through finalize-time
input materialization and the `apply_sync` / `apply_async` pipeline.

Folder shape:

- `__init__.py` — public re-exports + Decision-11 `order_input_type` + helper
  ledger (`_helper_referenced_ordersets`, clear owner
  `orders.helper_references`).
- `base.py` — `RelatedOrder` (thin `RelatedSetTargetMixin` parameterization).
- `inputs.py` — Decision-9 namespace, `Ordering` enum, converters / builders /
  normalizer, materialize + `clear_order_input_namespace` (clear owner
  `orders.input_namespace`, `before_bind=True`).
- `factories.py` — Layer-5 BFS (`OrderArgumentsFactory`); Layer 6 reserved only
  as a standing deferred Non-goal TODO.
- `sets.py` — `OrderSet` / metaclass, expansion, normalize + permission + apply
  (to-many aggregate path via `_resolve_order_expressions`).

Connected behavior re-traced for this folder pass (not inherited as proven):
`filters/` Layer-5 twin + shipped Layer-6 cache; `sets_mixins` /
`utils/inputs.py` / `utils/input_values.py` / `utils/permissions.py` /
`utils/querysets.py::run_in_one_sync_boundary` / `utils/relations.py`;
finalizer phase 2.5 bind + orphan check; live fakeshop `orderBy:` queries under
`examples/fakeshop/test_query/` and `apps/*/orders.py` + `order_input_type`
resolver sites.

Folder-level axes examined: duplicated policy across modules, state ownership
(helper ledger vs input-namespace clear vs absent Layer-6 cache), competing
helpers, public export flavor vs `filters/`, lifecycle work repeated at several
phases, and filters↔orders mirrors deferred from file reviews.

## Verification

- Item-scoped baseline `cad991ba198a72e35c7fc2d217c205e6ac8b7175`: working
  tree matched baseline for `orders/` at pass start (empty item-scoped diff).
  Concurrent dirt vs HEAD on `orders/{__init__,inputs,sets}.py` is pre-baseline
  WIP (substrate aliases, permission / apply consolidations from file passes) —
  left untouched except the ledger-comment alignment below. Concurrent dirty
  paths outside this item left untouched. Plan checkbox not edited.
- Re-read all five orders sources end-to-end. Grepped package for
  `get_flat_orders`, `_get_concrete_field_names`, `_materialized_names` /
  `delattr`, `register_subsystem_clear` owners under `orders.`,
  `OrderArgumentsFactory`, and `path_traverses_to_many`.
- Compared `filters/` as connected evidence: Layer-5 factory already shares
  `GeneratedInputArgumentsFactory`; Decision-11 helpers already share
  `build_lazy_input_annotation`; materialize/clear already share
  `utils/inputs.py`; related-target / expansion / lifecycle already share
  `sets_mixins`. Layer 6 exists only as a TODO on the order side.
- Independently re-traced assignment-named filters↔orders deferrals from source
  (below). Did not concatenate file artifacts.
- Confirmed `_materialized_names` ledger comment still claimed the clear path
  could `delattr` module globals while `clear_order_input_namespace` /
  `clear_generated_input_namespace` deliberately park classes — the same
  lifecycle ownership prose drift the filters folder pass aligned.
- No focused pytest (comment-only production edit; live `orderBy:` coverage
  already earns apply / materialize behavior under
  `examples/fakeshop/test_query/`). No full pytest.

## Opportunities

### 1. Materialized-ledger clear contract comment (accepted)

- **Repeated responsibility:** Decision-9 clear must empty the name ledger and
  leave materialized input classes parked in `orders.inputs.__dict__` (same
  park-not-`delattr` rule as filters / the shared clear substrate).
- **Sites:** `orders/inputs.py` ledger comment above `_materialized_names`
  (claimed clear-path `delattr`); `clear_order_input_namespace` docstring +
  `utils/inputs.py::clear_generated_input_namespace` (park, do not strip).
- **Evidence:** clear body only `materialized_names.clear()`; stored ledger
  values exist for collision / identity checks, not for module-global teardown.
  A future clear edit that followed the stale comment would break
  `strawberry.lazy(...)` holders across reload fixtures.
- **Owner:** park-not-`delattr` contract already owned by
  `clear_generated_input_namespace`; family ledger comment must describe it.
- **Consolidation:** rewrite the `_materialized_names` comment to match the
  filters ledger wording and the clear docstring (no executable change).
- **Proof:** existing
  `tests/orders/test_inputs.py::test_clear_order_input_namespace_leaves_module_globals_parked`
  pins the contract; no new test required for prose alignment.
- **Risks / non-goals:** do not change clear behavior; do not merge order /
  filter ledgers (Decision 9 disjoint namespaces).

### Rejected / deferred (re-proved)

1. **Extract Layer-6 hashing / `get_orderset_class` shared with filters.**
   Order side has only a standing deferred Non-goal TODO; filters' Layer 6 is
   build-and-test-only with no source consumer. Premature shared owner.
   Defer-with-trigger: when orders ships a real dynamic cache, or the project
   pass revisits cross-family packaging. Re-proved.

2. **Further collapse Decision-9 / Decision-11 family wrappers with
   `filters/`.** Substrate already shared (`build_lazy_input_annotation`,
   materialize/clear, BFS base, related-target mixins). Remaining mirror is
   per-subsystem namespace + ledger ownership. Cross-family packaging needs
   filters as co-owner — recorded for project pass. Not this folder's solo
   consolidation. Re-proved.

3. **Fold `get_flat_orders` into `_apply_orderings` / `normalize_input_value`.**
   Normalize already owns RelatedOrder path flattening; `get_flat_orders` is a
   prefix pass-through (empty prefix in the apply common path). Cookbook /
   spec-028 public surface + package tests pin the helper; collapsing it would
   delete an intentional API seam, not remove a second encoding of the walk.
   Rejected.

4. **Promote `_get_concrete_field_names_for_order` into `sets_mixins`.**
   One concrete `"__all__"` site; cookbook `get_concrete_field_names` is
   intentionally unported until a second family needs it. Mutations'
   `editable_input_fields` is the deliberate opposite selection (writes).
   Premature. Defer.

5. **Dual clear owners (`orders.helper_references` vs
   `orders.input_namespace`).** Intentional: orphan-check ledger vs rebuild
   bookkeeping (`before_bind=True`). Not consolidation candidates.

6. **Public flavor vs `filters/`.** `OrderSetMetaclass` + `Ordering` in
   `__all__`; `OrderArgumentsFactory` stays an advanced import — matches filter
   twin's factory packaging. Consistent.

7. **Permission / request / branch thin wrappers on `OrderSet`.** Already
   delegates to `utils/permissions.py` with family config; classmethod surface
   is FilterSet parity, not a second policy owner.

## Judgment

Folder ownership is already layered correctly after the 0.0.9 substrate
extraction and the file-pass consolidations sitting in the concurrent WIP.
The only folder-visible defect found was lifecycle-ownership prose drift on the
materialized-name ledger — now aligned with the park-not-`delattr` clear
contract. Filters↔orders Layer-6 hashing and Decision-9 packaging remain
deferred for a co-owned project pass. Ready for Worker 2.

## Implementation (Worker 1)

- **Owner chosen:** park-not-`delattr` clear contract (documented at
  `orders/inputs.py::_materialized_names` to match
  `clear_order_input_namespace` / `clear_generated_input_namespace`).
- **Migrated:** stale ledger comment claiming clear-path `delattr` of module
  globals → park-and-overwrite wording (mirrors filters ledger comment).
- **Tests:** none added (existing parked-globals clear test covers the
  contract; comment-only change).
- **Kept separate:** Layer-6 hashing; filters↔orders Decision-9 wrappers;
  `get_flat_orders`; concrete-field-name helper; dual clear ledgers;
  permission thin wrappers.
- **Validation:** `uv run ruff format` + `uv run ruff check --fix` after
  edits. No focused pytest. No full pytest.
- **Changelog:** no — comment-only lifecycle prose; no public API change.
- **Concurrent paths preserved:** edit only in `orders/inputs.py` (ledger
  comment) and this artifact. Pre-existing WIP under
  `orders/{__init__,sets}.py` and other packages left alone. Plan checkbox
  not touched.

## Independent verification (Worker 2)

Re-traced `orders/` as one component (all five modules + Decision-11 helper,
Layer-5 factory, deferred Layer-6 TODO, dual clear owners, apply /
permission / normalize pipeline) against connected `filters/`,
`utils/inputs.py`, `utils/permissions.py`, `utils/relations.py`, and
`sets_mixins`. Did not treat Worker 1 findings as proven. Item-scoped diff
vs `cad991ba198a72e35c7fc2d217c205e6ac8b7175` is comment-only in
`orders/inputs.py` (ledger prose); concurrent WIP vs HEAD on
`orders/{__init__,sets}.py` left untouched.

**Challenged Opportunity 1 (ledger comment consolidation).** Confirmed
lifecycle-ownership prose drift: baseline ledger comment claimed clear-path
`delattr` of module globals; `clear_order_input_namespace` /
`clear_generated_input_namespace` only `materialized_names.clear()` and park
classes. Current comment matches the filters ledger contract (park +
`setattr` overwrite; `delattr` breaks `strawberry.lazy(...)` holders) and
the clear docstring. Orders wording also notes ledger values exist for
identity-compare — accurate, not a second clear rule. Existing
`tests/orders/test_inputs.py::test_clear_order_input_namespace_leaves_module_globals_parked`
pins park-not-`delattr`; comment-only change needs no new test. Accepted.

**Challenged deferred filters↔orders items.**

1. **Layer-6 hashing / `get_orderset_class`.** Orders ships only the Decision
   12 TODO; filters' `_make_hashable` / `get_filterset_class` /
   `_dynamic_filterset_cache` remain build-and-test-only with no source
   consumer (`DjangoConnectionField` uses explicit `Meta.*_class`). No
   shared owner to extract yet. Deferral stands.

2. **Decision-9 / Decision-11 packaging collapse.** Substrate already shared
   (`build_lazy_input_annotation`, materialize/clear, BFS base,
   related-target / lifecycle mixins). Remaining mirror is per-subsystem
   namespace + ledger ownership (Decision 9). Needs filters as co-owner —
   project pass, not this folder alone. Deferral stands.

**Challenged rejected / kept-separate items.**

- **`get_flat_orders`:** normalize owns RelatedOrder path flattening;
  `get_flat_orders` is cookbook-shaped prefix pass-through (empty prefix in
  apply). Package tests pin both pass-through and prefix. Not a second walk
  encoding. Rejection stands.
- **`_get_concrete_field_names_for_order` → `sets_mixins`:** one `"__all__"`
  consumer; `sets_mixins` documents cookbook helper as intentionally
  unported until a second family needs it; mutations'
  `editable_input_fields` is the write-side opposite selection. Premature.
  Rejection stands.
- **Dual clear owners** (`orders.helper_references` vs
  `orders.input_namespace` / `before_bind=True`): orphan-check vs rebuild
  bookkeeping — intentional. Rejection stands.
- **Public flavor vs `filters/`:** `OrderSetMetaclass` + `Ordering` in
  `__all__`; factory advanced-import — matches filter twin. Rejection stands.
- **Permission thin wrappers:** delegate to `utils/permissions.py` with
  family config; FilterSet parity surface. Rejection stands.

**Missed folder consolidations searched.** Grepped for competing path walks,
second Layer-6 caches, leftover clear-path `delattr` claims, dual materialize
ledgers, and apply-pipeline double encodings inside `orders/`. No
filters-style competing helper (cf. `_model_field_for_filter`) exists here:
column `"__all__"` walk, to-many fan-out (`path_traverses_to_many`), and
normalize/apply already have single owners. No additional folder opportunity
found.

**Disposition:** Status → verified. Plan checkbox marked `[x]`. No production
edits. No commit.
