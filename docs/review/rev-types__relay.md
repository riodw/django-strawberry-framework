# Review: `django_strawberry_framework/types/relay.py`

Status: verified

## Understanding

This module owns Relay interface application, `is_type_of`, default id/node resolvers, GlobalID strategy validation/encoding/decoding, composite-primary-key checks, and the `SyncMisuseError` re-export. Finalization stamps strategy and id metadata once; node defaults use the shared visibility boundary in sync and async contexts; decode resolves model-label ids through the primary registry type and type-name ids through finalized GraphQL names.

## Verification

- Traced collection-time Relay shape detection into finalizer base injection, resolver installation, GlobalID strategy recording, root Relay fields, testing helpers, and optimizer id projection.
- Checked model/type/type-plus-model/callable/custom strategy behavior, primary routing, malformed and uncoercible ids, duplicate/missing node batches, visibility filtering, async hooks, and inherited concrete Relay classes.
- `uv run pytest --no-cov -q tests/types`: 506 passed.
- Live library Relay HTTP behavior passed as part of the 197-test library suite.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

Relay lifecycle state is frozen at finalization, decode enforcement is strategy-aware, and sync/async visibility behavior is routed through the shared queryset boundary.

## Implementation (Worker 1)

No implementation change was warranted.

## Independent verification (Worker 2)

Relay encoding/decoding and node resolver paths were challenged with malformed inputs, hidden rows, alternate strategies, inherited types, and async execution. No actionable finding emerged.

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
