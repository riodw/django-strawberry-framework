# Review: `django_strawberry_framework/optimizer/`

Status: verified

## Understanding

The optimizer folder is a layered pipeline: `selections.py` and `field_meta.py` normalize GraphQL
and Django metadata; `walker.py` emits immutable `plans.py` directives; `nested_planner.py`
classifies connection windows and delegates to `nested_fetch.py` strategies; `lateral_fetch.py`
and `single_parent_fetch.py` are optional performance layers over the windowed floor; `extension.py`
owns lifecycle/cache/context publication; and `predicates.py` remains an isolated row-preserving
ORM utility. `types/resolvers.py`, `connection.py`, mutation/form re-fetch paths, registry/finalizer,
sealed queryset visibility, and database routing consume the folder's shared contracts.

## Verification

The complete non-`__init__.py` source set and optimizer tests were read. Integration tracing covered
cache/request isolation, sync/async dispatch, relation cardinality and accessors, ORM projections
and aliases, custom `get_queryset`, keyset/offset/window/lateral fallbacks, strictness, mutation
payload re-fetches, GenericRelation morph handling, sharded aliases, and public strategy/hint seams.
`uv run pytest --no-cov tests/optimizer examples/fakeshop/test_query/test_optimizer_auto_api.py`
passed 781 tests. Live HTTP coverage through products, library, keyset, single-parent fast path,
and multi-database suites passed 350 tests with one skip. A disposable keyset Q-tree probe under
`docs/review/temp-tests/optimizer/` passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

No cross-file defect was confirmed. Plan metadata, runtime resolver keys, context lifecycle,
strategy fallbacks, queryset alias behavior, and mutation/connection integration agree across the
folder. This is a zero-edit integration pass.

## Implementation (Worker 1)

None — zero-edit folder cycle. No production or permanent-test changes were justified. The
untracked disposable probe remains under `docs/review/temp-tests/optimizer/`; no full suite was run.

## Iterations

### Worker 1 revision after Worker 2 verification

- The folder integration pass found one cache-boundary defect spanning `extension.py` and the
  public GraphQL execution path: arbitrary hashable custom scalar values could execute a hostile
  `__eq__` during a later plan-cache lookup.
- The owning fix is in `optimizer/extension.py`; container values are structurally frozen,
  exact built-in scalars retain reuse, and all other custom values use opaque per-value identities.
- Permanent direct and real GraphQL regressions were added under `tests/optimizer/test_extension.py`;
  both targeted tests pass. No concurrent optimizer files were reverted or folded into this
  revision.

## Independent verification (Worker 2)

Status is `revision-needed`: the focused and live suites pass, but an adversarial custom-scalar
cache probe found one folder-level public-contract defect in `extension.py`.

### Medium

**Observation:** The plan-cache key path preserves arbitrary hashable custom-scalar objects as raw
values, so cache lookup depends on user-defined equality behavior.

**Evidence:** `docs/review/temp-tests/optimizer/test_worker2_cache_hostile_hashable.py` uses a real
GraphQL schema whose custom scalar parser returns a hashable object whose `__eq__` raises. The
first execution succeeds; the second identical execution fails while comparing the plan-cache key.
The disposable probe passed with `uv run pytest --no-cov docs/review/temp-tests/optimizer/test_worker2_cache_hostile_hashable.py` (`2 passed`).

**Impact:** A valid custom scalar can turn a repeat request into a top-level resolver failure
instead of a safe cache miss, violating cache/request isolation and the extension's documented
acceptance of arbitrary custom-scalar values.

**Recommendation:** At the cache boundary, whitelist only immutable built-in scalar
representations whose hash/equality behavior is controlled; convert arbitrary user-defined
hashable values to opaque per-execution tokens (or an equally exception-safe identity) so
untrusted `__hash__`/`__eq__` implementations can only cause a cache miss, never abort lookup.

**Proof:** Add a permanent repeated-execution regression using a custom scalar parser that returns a
hashable object with raising equality, and assert both executions complete without an optimizer
error while distinct values do not share a plan.

### Worker 1 final revision

- The cache-boundary fix is implemented at `optimizer/extension.py`, with structural freezing for
  recognized containers, exact built-in scalar reuse, and opaque identities for arbitrary custom
  values.
- Permanent package and live fakeshop regressions now cover direct key comparison and repeated
  public GraphQL execution.
- Final focused validation passed: 784 optimizer/package-live tests; formatter and lint completed
  successfully. The folder artifact is restored to `fix-implemented`.

### Worker 2 final re-verification

- Independently inspected the closed cache identity policy: exact built-in immutable scalar types
  reuse structurally, supported containers freeze recursively, and arbitrary custom values become
  opaque identities without invoking consumer hash/equality code.
- Focused optimizer/package-live run: `uv run pytest --no-cov tests/optimizer
  examples/fakeshop/test_query/test_optimizer_auto_api.py` — 784 passed.
- Reachable products/library/keyset/single-parent/multi-database HTTP run — 350 passed, 1 skipped.
- Direct cache identity subset — 6 passed; live hostile custom-scalar regression — 1 passed.
- External identity probe covered scalar subclasses, hostile objects/container subclasses,
  nested structural containers, equivalent mapping order, and opaque-value separation.
- No remaining defect or blocker; concurrent source diffs were preserved.

