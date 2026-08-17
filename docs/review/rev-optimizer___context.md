# Review: `django_strawberry_framework/optimizer/_context.py`

Status: verified

## Understanding

`_context.py` owns the optimizer stash-key vocabulary and the start-of-execution reset. The
extension publishes plans, FK-id elisions, strictness resolver keys, lookup paths, and the
strictness mode; generated relation resolvers read the same keys through `utils/context.py`.
`clear_optimizer_context` removes exactly those keys so a reused GraphQL `context_value` cannot
carry state between operations.

## Verification

Read the complete module and traced `DjangoOptimizerExtension.on_execute`, context helpers,
`types/resolvers.py`, connection fallback publication, and mutation refetch execution. Focused
tests cover object, dict, slots-mapping, frozen mapping, immutable `QueryDict`, and reused-context
cases. `uv run pytest --no-cov tests/optimizer` passed 781 tests; live optimizer paths passed
350 tests with one expected skip. A disposable keyset-shape probe under
`docs/review/temp-tests/optimizer/` also passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The keys are single-sourced, reset scope is explicit, and read/write dispatch matches every
optimizer publisher and resolver consumer. No source or permanent-test change was justified.

## Implementation (Worker 1)

None — zero-edit cycle. The complete source/test trace, focused package suite (781 passed), live
optimizer suite (350 passed, 1 skipped), and disposable probe provide the no-change proof.

## Independent verification (Worker 2)

Re-read the context key vocabulary, reset dispatch, extension lifecycle, resolver consumers, and
reused-context paths. `uv run pytest --no-cov tests/optimizer examples/fakeshop/test_query/test_optimizer_auto_api.py`
passed (`781 passed`), and the reachable HTTP optimizer suites passed (`350 passed, 1 skipped`).
No defect was reproduced in this target.

