# Review: `django_strawberry_framework/types/`

Status: verified

## Understanding

The folder forms one lifecycle component: `base.py` collects and validates `DjangoType` declarations; `definition.py` stores canonical metadata; `relations.py` parks unresolved relations; `converters.py` maps Django fields; `finalizer.py` resolves and decorates the graph; `resolvers.py` attaches runtime relation/file behavior; `relay.py` supplies Relay identity and visibility-aware node behavior; and `__init__.py` exposes only the intended type/finalization facade.

## Verification

- Re-read all eight modules and the connected registry, optimizer, connection, list-field, queryset, relation, filter, order, mutation, form, auth, testing, and fakeshop schema paths.
- Confirmed state ownership across collection, finalization, registry clearing, Strawberry decoration, sidecar materialization, Relay strategy snapshots, and generated connection teardown.
- Rechecked the existing folder DRY review. New correctness evidence
  superseded only its rejection of a settled-surface owner; Relay predicates,
  relation/file skip sets, and visibility paths remain intentionally separate.
- `uv run pytest --no-cov -q tests/types`: 506 passed.
- Live GraphQL HTTP verification passed: library 197; products/scalars/uploads 156.
- Second pass: package 510 passed; repeated live HTTP verification passed
  library 197 and products/scalars/uploads 156.
- Runtime-isolation pass: package 511 passed; sync/async visibility regressions
  passed; relation-heavy library/products live suites passed 316 combined.

## Improvements

### High

None.

### Medium
The finalizer reconstructed GraphQL fields from selected Django fields rather
than the settled class surface. That caused false collision/empty-surface
failures after Relay or relation-shape suppression and missed explicit
Strawberry GraphQL names. The root fix is
`django_strawberry_framework/types/finalizer.py::_field_surface_names`, with
permanent package regressions.

Generated relation resolvers also bypassed a target type's custom
`get_queryset` when no optimizer extension was installed. The fix applies the
shared visibility boundary to unoptimized relations while preserving
optimizer-filtered caches and default-hook fast paths. Sync and async live
regressions cover the behavior.

### Low

None.

## Summary

The component retains a coherent collect → convert → pending → finalize →
resolve/Relay → facade lifecycle. The second pass corrected one finalizer-owned
surface-mapping defect without changing the surrounding phase architecture.

## Implementation (Worker 1)

No production or permanent-test change was warranted. Existing concurrent source/test edits were preserved.

## Independent verification (Worker 2)

The integrated lifecycle and public consumer paths were independently re-traced and verified by focused package and live HTTP suites. No revision is required.

## Iterations

### Second-pass adversarial audit — 2026-08-17

Re-audited all eight modules and their registry, optimizer, connection, Relay,
sidecar, and runtime resolver boundaries. Confirmed one Medium finalizer defect
in settled field-surface ownership, implemented the root fix, and expanded the
package suite from 506 to 510 tests. No additional converter, relation,
GlobalID, sync/async, file-storage, teardown, or facade defect was reproduced.

### Runtime-isolation pass — 2026-08-17

The different-angle audit found one additional Medium visibility defect in
`types/resolvers.py`, fixed it at the generated relation boundary, and added
sync/async live HTTP coverage. The types suite now passes 511 tests. Resource
bounds, database routing, deferred FK handling, Relay node visibility, and
cache lifecycle were challenged without another reproducible defect.

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
