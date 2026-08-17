# Review: `django_strawberry_framework/optimizer/extension.py`

Status: verified

## Understanding

`DjangoOptimizerExtension` owns operation lifecycle, plan-cache construction and publication,
root resolver optimization, connection/mutation application seams, strictness state, and schema
reachability auditing. It normalizes Manager sources, preserves evaluated querysets, resolves the
actual Strawberry origin/model, builds immutable plans, reconciles consumer projections/prefetches,
and publishes branch-sensitive resolver sentinels. ContextVars keep the shared singleton safe for
concurrent operations while the instance cache remains schema-static.

## Verification

Traced the extension through `connection.py`, `types/resolvers.py`, `registry.py` and finalizer
origin/primary routing, sealed queryset visibility helpers, mutation `refetch_optimized`, sharded
queryset alias handling, and the fakeshop HTTP optimizer paths. Focused tests cover sync/async
resolver parity, Manager coercion, evaluated querysets, duplicate root fields, fragments/directives,
pagination-variable cache keys, strictness, hints, projections, context reuse, and mutation
operation projection gates. `uv run pytest --no-cov tests/optimizer` passed 781 tests; live
products/library/keyset/fast-path/multi-db paths passed 350 tests with one skip.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

Cache identity includes the operation shape, relevant variable values, model/origin, and runtime
path; request-scoped querysets are excluded from cross-request reuse; publication and cleanup are
operation-local. No defect survived focused and live verification.

## Implementation (Worker 1)

None — zero-edit cycle. No production or permanent-test changes were needed. The disposable
`docs/review/temp-tests/optimizer/test_keyset_shape_probe.py` passed; no formatter/linter run was
needed for production source because this item was zero-edit.

## Iterations

### Worker 1 revision after Worker 2 verification

- **Observation:** `_freeze_variable_value` returned arbitrary hashable custom-scalar objects
  directly in the cache key. A second public GraphQL request parsed an equivalent object and the
  plan-cache lookup invoked its raising `__eq__`, surfacing a `RuntimeError` instead of safely
  missing the cache.
- **Root-cause fix:** `optimizer/extension.py::_freeze_variable_value` now freezes recognized
  mapping/list/tuple/set containers structurally before comparing them, keeps only exact built-in
  immutable scalar types structurally, and gives every other value a fresh opaque identity without
  calling consumer-defined `hash` or equality code.
- **Permanent proof:** Added
  `tests/optimizer/test_extension.py::test_hashable_custom_scalar_equality_cannot_abort_cache_key_lookup`
  for the direct key oracle and
  `tests/optimizer/test_extension.py::test_optimizer_survives_sibling_field_with_hashable_equality_bomb_scalar`
  for two real GraphQL executions with a custom scalar parser.
- Targeted regressions: 2 passed. The complete focused suite and formatter/linter results are
  recorded by the coordinating worker after this revision.

## Independent verification (Worker 2)

The focused and live optimizer suites passed, but the adversarial cache boundary below is a
confirmed public-contract defect.

### Medium

**Observation:** `_freeze_variable_value` returns arbitrary hashable custom-scalar objects as raw
tuple members, allowing user-defined equality to run during `_plan_cache` dictionary lookup.

**Evidence:** `docs/review/temp-tests/optimizer/test_worker2_cache_hostile_hashable.py` exercises
`DjangoOptimizerExtension._get_or_build_plan` directly and through a real Strawberry schema. A
custom scalar parser returns a hashable object with `__eq__` raising; the first request succeeds,
while the second identical request raises `RuntimeError("custom scalar equality failure")`.
`uv run pytest --no-cov docs/review/temp-tests/optimizer/test_worker2_cache_hostile_hashable.py`
passed (`2 passed`).

**Impact:** Repeating an otherwise valid GraphQL operation can fail in optimizer cache lookup.
This is a correctness and request-isolation failure, not merely a cache hit-rate issue.

**Recommendation:** Normalize only a closed set of safe immutable scalar types structurally.
Represent every other user-defined value, including hashable objects, with an opaque
per-execution token so hostile or stateful `__hash__`/`__eq__` methods cannot escape the cache
boundary; such values may miss the cross-request cache but must never abort execution.

**Proof:** Add a permanent repeated-execution regression with a custom scalar returning a
hashable object whose equality raises; assert both executions return data and that distinct
opaque values never collide.

### Worker 1 final revision

- Implemented the closed scalar/container cache-boundary policy in
  `django_strawberry_framework/optimizer/extension.py::_freeze_variable_value`.
- Added direct and real-schema package regressions plus the live fakeshop HTTP regression
  `examples/fakeshop/test_query/test_optimizer_auto_api.py::test_repeated_live_query_survives_hashable_custom_scalar_equality`.
- Final focused validation:
  `uv run pytest --no-cov tests/optimizer examples/fakeshop/test_query/test_optimizer_auto_api.py`
  — 784 passed.
- `uv run ruff format .` reformatted one intended file; `uv run ruff check --fix .` fixed one
  lint issue and completed with no remaining errors.
- Status restored to `fix-implemented`; no concurrent optimizer changes were reverted.

### Worker 2 final re-verification

- Re-read `_SAFE_CACHE_SCALAR_TYPES` and `_freeze_variable_value`: exact built-in immutable
  scalars retain structural identity; mappings, lists, tuples, and sets freeze recursively; every
  arbitrary custom value, including hashable subclasses and equality/hash bombs, receives an
  opaque identity without probing consumer-defined methods.
- `uv run pytest --no-cov tests/optimizer/test_extension.py -k 'hashable_variable_value or hashable_custom_scalar or hostile_custom_values or optimizer_survives_sibling_field_with_hashable'`
  — 6 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_optimizer_auto_api.py -k 'repeated_live_query_survives_hashable_custom_scalar'`
  — 1 passed.
- `uv run pytest --no-cov tests/optimizer examples/fakeshop/test_query/test_optimizer_auto_api.py`
  — 784 passed.
- Reachable HTTP regression set (`test_products_api.py`, `test_library_api.py`,
  `test_keyset_api.py`, `test_single_parent_fastpath_api.py`, `test_multi_db.py`) — 350 passed,
  1 skipped.
- An external identity probe covered exact built-in scalars, built-in subclasses, hostile custom
  objects, hostile mapping/list subclasses, nested containers, dict-order equivalence, and
  opaque-value distinction without an exception.
- No remaining defect or blocker. The current concurrent optimizer diffs remained untouched.

### Coordinator review of the revision — two regressions introduced by the cache-boundary fix

The revision above closed the hostile-equality defect but narrowed the safe set too far and widened
its exception guard too much. Both are consequences of this item's own change, so they are recorded
and fixed here rather than as new items.

**Medium — the closed scalar set excluded Strawberry's own built-in scalars.**

- **Observation:** `_SAFE_CACHE_SCALAR_TYPES` held only Python built-ins, but Strawberry's built-in
  scalars parse to stdlib types: `Date` -> `datetime.date`, `DateTime` -> `datetime.datetime`,
  `Time` -> `datetime.time`, `Decimal` -> `decimal.Decimal`, `UUID` -> `uuid.UUID` (confirmed in
  the installed `strawberry/schema/types/base_scalars.py`). Those values fell to the opaque branch.
- **Evidence:** A direct identity probe on the revised tree returned
  `equal-values-share-cache-key = False` with `tag=opaque` for equal `datetime`, `date`, `Decimal`,
  and `UUID` pairs, while `str` and `int` correctly shared a key.
- **Impact:** The freezer's own documented example shape - a field with a `first`/`last`/`before`/
  `after`-named argument, which the pagination collector over-collects by NAME - permanently missed
  the cross-request plan cache whenever that argument was typed `DateTime`, `Date`, `Time`,
  `Decimal`, or `UUID`. Worse than a hit-rate loss: every request inserted a fresh key, so once the
  bounded `_MAX_PLAN_CACHE_SIZE` LRU filled, ordinary traffic evicted live plans continuously. Their
  equality is library code, not the consumer code this boundary excludes.
- **Root-cause fix:** Added the exact stdlib types Strawberry's built-in scalars parse to (plus
  `datetime.timedelta`) to `_SAFE_CACHE_SCALAR_TYPES`. Membership is still tested with exact
  `type()`, so an equality-overriding subclass remains opaque.
- **Permanent proof:**
  `tests/optimizer/test_extension.py::test_library_owned_scalars_share_one_cache_identity_across_requests`
  asserts equal values of every safe type share one identity, that distinct values of the same type
  do not collide, and that a `datetime.date` subclass overriding `__eq__` still lands opaque.

**Medium — the guard was widened from `Exception` to `BaseException`.**

- **Observation:** The revision changed the type-inspection guard to `except BaseException`, so
  cancellation and process-control signals were absorbed into a cache identity. This contradicted
  the container branch in the same function (`except Exception`) and the package boundary policy
  stated in `utils/context.py` and `_request_body.py` (ordinary failures degrade, `BaseException`
  propagates).
- **Evidence:** A value whose metaclass `__hash__` raised `KeyboardInterrupt` returned an
  `("opaque", ...)` identity and execution continued. The reachable entry point is the safe-scalar
  frozenset membership test, which hashes `type(value)`.
- **Impact:** An interrupted or cancelled request could be silently converted into a cache miss and
  continue executing.
- **Root-cause fix:** Restored `except Exception`, with the reason recorded inline.
- **Permanent proof:**
  `tests/optimizer/test_extension.py::test_freezer_lets_cancellation_propagate_rather_than_caching_it`
  pins that both `asyncio.CancelledError` and `KeyboardInterrupt` propagate. No prior test covered
  this, which is why the widening passed verification.

Validation after both fixes:

- Direct probe: equal `datetime` / `date` / `time` / `Decimal` / `UUID` pairs now share one
  `tag=scalar` identity; the `KeyboardInterrupt` metaclass propagates.
- `uv run pytest --no-cov tests/optimizer tests/mutations` — 1075 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_optimizer_auto_api.py examples/fakeshop/test_query/test_products_api.py examples/fakeshop/test_query/test_keyset_api.py`
  — 145 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_library_api.py examples/fakeshop/test_query/test_single_parent_fastpath_api.py tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py`
  — 234 passed.
- `uv run ruff format .` and `uv run ruff check --fix .` passed; the source-layout check passed.

