# Review: `django_strawberry_framework/utils/querysets.py`

Status: verified

## Understanding

Owns manager/source normalization, sync/async visibility-hook execution, the sealed execution queryset, query-graph provenance/reconstruction, deferred-filter baking, prefetch sealing, alias pinning, relation visibility checks, field coercion, and one sync-worker boundaries.

## Verification

Read every public caller and challenged evaluated sources, custom QuerySet/Manager methods, foreign models and combined queries, projections, deferred filters, hostile expression graphs, prefetch subclasses/caches, sliced children, database aliases, async hooks/residual awaitables, and unoptimized manual prefetches. `tests/utils/test_querysets.py`, optimizer/connection/type callers, and the disposable real GraphQL manual-prefetch probe passed. No source or cache identity bypass was reproduced.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The visibility boundary rebuilds trusted lazy query state and applies the target hook consistently across optimized, unoptimized, sync, async, relation, and write-pipeline paths.

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
