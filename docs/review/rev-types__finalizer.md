# Review: `django_strawberry_framework/types/finalizer.py`

Status: verified

## Understanding

`finalize_django_types()` is the build gate. It snapshots and validates GlobalID settings, audits primary ambiguity, resolves pending relations, attaches generated relation/file resolvers, injects interfaces and Relay defaults, validates keyset columns, synthesizes relation connections, audits model-label routing, binds optional mutation/form/auth/filter/order sidecars, audits the GraphQL field surface, decorates each type with Strawberry, and marks the registry finalized. Phase 1 is failure-atomic; later phases support bounded retry via per-definition state and registered teardown artifacts.

## Verification

- Re-read all finalizer phases and traced their ordering into registry state, Strawberry class mutation, connection synthesis, sidecar materialization, and `registry.clear()` teardown.
- Checked retry behavior after unresolved targets, ambiguity, relation-connection, GlobalID, field-surface, and sidecar failures.
- Confirmed the existing DRY record independently rejected the prior same-file field-surface extraction and found no folder-level consolidation to reintroduce.
- `uv run pytest --no-cov -q tests/types`: 506 passed.
- Live library HTTP 197 passed and products/scalars/uploads HTTP 156 passed.
- Existing concurrent edits in this file and `tests/types/test_finalizer.py` were preserved; no source/test changes were made in this review.
- Second pass: `uv run pytest --no-cov -q tests/types`: 510 passed.
- Second-pass live HTTP verification repeated successfully: library 197;
  products/scalars/uploads 156.

## Improvements

### High

None.

### Medium
**Observation:** `_audit_field_surface` and the relation-connection collision
guard treated every selected Django field as emitted and ignored inherited and
explicitly named Strawberry fields.

**Evidence:** Disposable probes showed that a Relay-suppressed `legacy_id`
column falsely collided with a legitimate `legacyId` field, a generated
`items_connection` falsely collided with a suppressed primary-key column, and a
Relay-only type with `Meta.fields = ()` was falsely rejected as empty. The
opposite gap also existed: an explicit `@strawberry.field(name="fooBar")` was not
compared by its emitted name.

**Impact:** Valid Relay schemas could not finalize, while a real explicit-name
collision could reach Strawberry's late or silent collision behavior.

**Recommendation:** Own one settled pre-decoration surface mapping in
`django_strawberry_framework/types/finalizer.py::_field_surface_names`. Build it
from inherited Strawberry definitions, current annotations, and assigned
Strawberry fields; let own GraphQL names override inherited interface fields;
exclude model-selection metadata that suppression removed.

**Proof:** Permanent regressions in
`tests/types/test_definition_order.py::test_relay_suppressed_pk_does_not_collide_with_real_consumer_field`,
`tests/types/test_definition_order.py::test_relation_connection_does_not_collide_with_relay_suppressed_pk`,
`tests/types/test_definition_order.py::test_relay_interface_field_prevents_false_empty_surface`,
and `tests/types/test_definition_order.py::test_explicit_graphql_field_name_collision_raises`
cover the corrected boundaries; existing consumer `relay.NodeID` tests protect
inherited-field override precedence.

### Low

None.

## Summary

The phase boundaries and retry/teardown contracts remain sound. The second pass
corrected field-surface ownership so build-time collision checks now operate on
what Strawberry will emit rather than on model-selection metadata.

## Implementation (Worker 1)

No implementation change was warranted. Concurrent `finalizer.py` and test edits were left untouched.

## Independent verification (Worker 2)

The finalizer was re-traced from collection through Strawberry schema construction and live fakeshop reload paths. Focused and live verification passed with no actionable finding.

## Iterations

### Second-pass adversarial audit — 2026-08-17

The maintainer requested an additional direct audit because this package is
critical. The settled-surface probes disproved the prior selected-field union:
selection and emission diverge after Relay and connection-only suppression.
Implemented `_field_surface_names`, added four permanent regressions, and
preserved the existing `relay.NodeID` override contract. `tests/types` now
passes 510 tests.

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
