# Review: `django_strawberry_framework/types/resolvers.py`

Status: verified

## Understanding

The resolver module attaches cardinality-aware relation resolvers and file/image parent resolvers during finalization. It owns strictness-aware N+1 probes, accessor-vs-field-name handling for reverse relations, FK-id elision with deferred-column safety, resource-policy bounds for raw many-side lists, and storage-safe file parent resolution. Consumer-assigned fields are excluded at attachment time.

## Verification

- Traced forward/reverse FK, OneToOne, M2M, reverse-accessor, file/image, FK-id-elision, optimizer strictness, and resource-policy paths into `FieldMeta`, `utils.relations`, optimizer context, and live schema execution.
- Checked prefetched cache recognition, deferred FK fallback, router database selection, reverse OneToOne absence, consumer resolver preservation, and storage failure boundaries.
- `uv run pytest --no-cov -q tests/types`: 506 passed.
- Live library HTTP 197 passed; products/scalars/uploads HTTP 156 passed.
- Second-pass runtime audit: `tests/types` 511 passed; sync and async live
  visibility regressions passed; relation-heavy library/products live suites
  passed 316 combined.

## Improvements

### High

None.

### Medium
**Observation:** Generated relation resolvers returned related rows directly
without applying a target type's custom `get_queryset` when no optimizer
extension was installed. The optimizer normally masked this by filtering child
prefetch querysets, making the resolver safe only under one schema wiring.

**Evidence:** A real-schema query returned a private `Item` through
`CategoryType.items` while `ItemType.get_queryset` filtered private rows. The
same query returned an empty relation after the fix. Sync and async HTTP
regressions cover the no-optimizer path; optimizer-backed query-count tests
remain unchanged.

**Impact:** Consumers could expose rows their target `DjangoType` explicitly
excluded simply by omitting the optional optimizer extension. Forward,
reverse-one-to-one, many-side, and FK-id-stub paths shared the bypass risk.

**Recommendation:** Resolve the registered target type during relation-resolver
construction. For custom target hooks, scope unoptimized querysets through the
shared sync/async visibility boundary; trust prefetched objects only when the
optimizer owns the current execution (including no-context executions tracked
by its execution ``ContextVar``). Preserve default identity fast paths and
resource bounds.

**Proof:** `types/resolvers.py` now owns the runtime check. Permanent package
coverage and `examples/fakeshop/test_query/test_products_visibility_api.py`
cover sync and async HTTP execution; existing optimizer query-count tests prove
there are no redundant queries for filtered prefetches.

### Low

None.

## Summary

Resolver attachment and runtime relation behavior now align with the collected
metadata and optimizer contracts, including target visibility in unoptimized
relations, strictness-visible fallback for unsafe FK-id elision, and preserved
optimizer query counts.

## Implementation (Worker 1)

No implementation change was warranted.

## Independent verification (Worker 2)

The runtime resolver paths were independently challenged through package and live
tests. The second pass found and fixed the unoptimized target-visibility
bypass; no additional correctness, security, or ownership defect was found.

## Iterations

### Second-pass runtime isolation audit — 2026-08-17

Audited relation values from request execution rather than schema construction:
custom target visibility, prefetched caches, forward/reverse relation paths,
FK-id stubs, resource bounds, database aliases, and sync/async execution. Found
and fixed the unoptimized target-visibility bypass. A separate concurrent
`connection.py` NameError blocked one unrelated products optimizer test; that
file was not modified.

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
