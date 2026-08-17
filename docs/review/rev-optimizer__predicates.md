# Review: `django_strawberry_framework/optimizer/predicates.py`

Status: verified

## Understanding

`predicates.py` owns only the row-preserving `Exists` attachment primitive used by relational
filters/search infrastructure. It builds an alias against a same-model, same-database correlated
inner queryset and leaves boolean placement and predicate semantics to callers.

## Verification

Traced `correlated_inner_root` and `attach_exists` through filter applicators, alias collision
handling, evaluated outer querysets, combined-query guards, database aliases, and the package
predicate tests. The predicate-focused tests passed in the 781 optimizer test run; no live
optimizer path changes this invariant.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The primitive preserves outer row multiplicity and fails closed on model/alias/combined-query
misuse without owning caller semantics. No change was needed.

## Implementation (Worker 1)

None — zero-edit cycle. Existing predicate and multi-database tests prove the no-change result.

## Independent verification (Worker 2)

Re-read correlated `Exists` construction and traced model/alias/combinator guards, evaluated outer
querysets, and shard routing. Focused optimizer tests passed (`781 passed`), and reachable HTTP
optimizer coverage passed (`350 passed, 1 skipped`). No defect was reproduced in this target.

