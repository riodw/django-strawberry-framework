# Review: `django_strawberry_framework/utils/inputs.py`

Status: fix-implemented

## Understanding

Owns generated Strawberry input construction, field/name collision checks, materialization ledgers, set-family lifecycle clearing, metadata canonicalization, dynamic set caches, write-input shape caches, and provided-field iteration.

## Verification

Traced BFS cycles, parked lazy globals, registry clears, duplicate Python/GraphQL names, ordered versus unordered metadata, alias promotion, required/default field presence, nested write specs, and cache reuse. Utility, filter, order, form, DRF, and mutation input suites passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

Generated input lifecycles and cache identities remain isolated by family and fail loudly on silent schema-field loss.
## Iterations

An additional lifecycle/cache pass found that `django_strawberry_framework/utils/inputs.py::make_hashable_meta_value` recursively followed cyclic or pathologically deep built-in containers until a raw `RecursionError`. Cache-key metadata normalization now tracks the active object path, rejects cycles, and enforces a 64-level container-depth bound with typed `ConfigurationError`s while still accepting shared acyclic subcontainers. Permanent regressions cover all three cases in `tests/utils/test_inputs.py`; filter/order and the 2,220-test integrated caller run passed.

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
