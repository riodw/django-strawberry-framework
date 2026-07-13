# Review: `django_strawberry_framework/optimizer/walker.py`

Status: resolved

## Understanding

`plan_optimizations` converts one normalized GraphQL selection tree into an immutable
`OptimizationPlan`. The core walk maps selected scalar fields to `.only()`, single relations to
`select_related`, many or visibility-scoped relations to `Prefetch`, and publishes resolver-path
identities used by strictness and FK-id elision.

At the reviewed baseline, the same file also owned nested-connection planning: alias merging,
pagination normalization, offset/keyset window derivation, child-queryset safety checks, query
projection, fetch-strategy dispatch, and conditional absorption of child metadata. The resulting
plan is cached and applied by
`optimizer/extension.py`; generated relation and connection resolvers consume its prefetched rows,
resolver identities, and window annotations. `FieldMeta`, the registry, selection helpers, join
taxonomy, queryset visibility, `nested_fetch.py`, `plans.py`, `connection.py`, and `keyset.py` are
therefore part of the target's correctness boundary.

Representative paths traced were scalar and relation planning, custom `get_queryset` downgrade,
consumer-owned relations and hints, plan finalization/cache hand-off, divergent connection aliases,
offset and keyset pagination, windowed/lateral strategy dispatch, and strictness metadata. The
package and live keyset/connection tests substantially exercise these paths.

## Verification

- `uv run pytest -q --no-cov tests/optimizer/test_walker.py`: 166 passed. This establishes that the
  existing focused walker contract is green at the supplied baseline.
- `docs/review/temp-tests/optimizer__walker/test_declining_strategy.py` installs a strategy whose
  `plan(request, plan)` appends `"leaked_column"` and then returns `False`. The probe failed because
  the returned plan retained `only_fields=("leaked_column",)` while `prefetch_related` and
  `planned_resolver_keys` stayed empty. The paired existing refusal test passed because its strategy
  returns `False` without first mutating the plan. The focused two-test invocation also reported the
  expected repository coverage-gate failure because it intentionally ran only two tests; this was
  not a full-gate run.
- Read the live keyset acceptance cases in
  `examples/fakeshop/test_query/test_keyset_api.py`, the connection acceptance cases in
  `examples/fakeshop/test_query/test_library_api.py`, and the package tests around walker, plan,
  selection, nested-fetch, lateral, and keyset behavior. They prove the built-in strategies and
  mainstream planner paths, but none challenges a declining strategy after partial mutation.
## Resolution

- Extracted strategy-independent nested-connection orchestration and its connection-only helpers
  into
  `django_strawberry_framework/optimizer/nested_planner.py::plan_connection_relation`.
  `django_strawberry_framework/optimizer/walker.py::_plan_connection_relation` is now a narrow
  delegation boundary that merges the returned result once.
- Added `django_strawberry_framework/optimizer/plans.py::OptimizationPlan.merge_from` and
  `django_strawberry_framework/optimizer/plans.py::OptimizationPlan.merge_metadata_from` as the
  centralized commit operations for every construction-time directive and metadata field.
- Every fetch strategy now receives a fresh candidate `OptimizationPlan`. A refusal discards that
  candidate, an exception propagates before the walker sees a result, and only an accepted
  candidate is merged into the isolated component plan. The parent therefore remains unchanged
  for both refusal and exceptions.
- Added regression contracts that dirty every supported plan field before refusing, accepting, or
  raising. They prove full discard, exactly-once duplicate-collapsing acceptance, byte-identical
  parent state after exceptions, full-plan merge coverage, metadata-only child absorption, and
  finalized-plan rejection.
- `uv run ruff format .` and `uv run ruff check --fix .` pass. Structural verification also proved
  AST parity for every mechanically moved helper, legacy private-import compatibility, Python
  compilation, and full-field merge behavior. Pytest was not run under repository policy.

## Improvements

### High

None.

### Medium

#### A declining fetch strategy can corrupt the supposedly unplanned parent plan

- **Resolution:** Resolved by the isolated component result, per-strategy candidate plans, and
  centralized plan merges described above.
- **Observation:** `optimizer/walker.py::_plan_connection_relation` passes the live parent plan to
  `active_strategy().plan(request, plan)`. It treats a `False` return as a transactional refusal,
  but it cannot undo directives the strategy appended before returning.
- **Evidence:** The disposable probe appended one invalid projection and returned `False`; the
  finalized parent plan retained that projection without the connection prefetch or resolver keys.
  This contradicts `optimizer/nested_fetch.py::NestedConnectionStrategy.plan`, whose contract says
  `False` leaves the selection unplanned.
- **Impact:** A custom strategy can decline an unsupported window yet leak a query, projection,
  partial prefetch, or other plan mutation. Execution may then fail or do unwanted work, while
  strictness still treats the relation itself as unplanned. The outcome depends on callback
  implementation order rather than the advertised boolean verdict.
- **Recommendation:** Make strategy planning transactional at the owner boundary. Give each strategy
  a fresh per-request `OptimizationPlan` (or have it return an immutable directive/result object),
  and merge that result into the parent only when the strategy accepts. Rejection and exceptions
  must leave the parent byte-for-byte unchanged. Centralize the merge operation so all current and
  future directive metadata is handled together.
- **Proof:** Promote the disposable probe to `tests/optimizer/test_nested_fetch.py` or
  `tests/optimizer/test_walker.py`: a strategy mutates every supported directive/metadata field and
  returns `False`; assert the parent is identical to the pre-dispatch snapshot and strictness sees
  the connection as unplanned. Add an accepting companion proving the same temporary result is
  merged exactly once.

### Low

#### Nested-connection orchestration has outgrown the general selection walker

- **Resolution:** Resolved by extracting the private nested planner while retaining the walker as
  the traversal and delegation owner.
- **Observation:** The 2,107-line module owns both the general model-field walk and a second planner
  spanning connection alias reconciliation, pagination, keyset decoding, projection, fetch-strategy
  requests, and acceptance bookkeeping. `optimizer/walker.py::_plan_connection_relation` alone
  coordinates all those policies.
- **Evidence:** The nested-connection section depends directly on `connection.py`, `keyset.py`,
  `utils/connections.py`, `join_taxonomy.py`, `nested_fetch.py`, and `plans.py`; its tests occupy most
  of the latter half of the 4,837-line walker test module. The transactional-refusal defect above
  occurs at this ownership seam.
- **Impact:** Adding a connection backend or cursor mode requires changing the general walker and
  reasoning about a long sequence of mutation/no-leakage rules. This raises the chance that a new
  fallback path updates query directives without matching strictness or cache metadata.
- **Recommendation:** Extract a private nested-connection planner component that receives the
  normalized selection and relation context and returns an explicit accepted/refused plan result.
  Keep `walker.py` responsible for model-field traversal and delegation; keep strategy mechanics in
  `nested_fetch.py`. The extraction should make the transactional boundary above structural rather
  than comment-enforced, without changing the public API.
- **Proof:** Move the connection-specific unit tests beside the extracted component, retain the full
  walker suite as integration coverage, and prove byte-equivalent plans for offset/keyset,
  shared/divergent aliases, both built-in strategies, and every refusal class.

## Summary

The confirmed strategy-refusal defect is closed: rejection and exceptions cannot mutate the parent,
accepted candidate plans merge exactly once, and the ownership split now makes the transactional
boundary structural. The existing walker suite remains the integration contract; the new
regressions pin the extension seam directly.

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
