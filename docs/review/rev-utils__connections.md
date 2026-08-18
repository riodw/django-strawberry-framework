# Review: `django_strawberry_framework/utils/connections.py`

Status: verified

## Understanding

Owns the shared connection sidecar vocabulary, offset/keyset window derivation, fetch-mode classification, marker/probe splitting, and Relay page-size ceilings consumed by the optimizer planner and connection resolver.

## Verification

Read the planner and resolver consumers, including divergent response-key windows, windowed and lateral renderers, keyset fallback, request resource-policy caps, malformed cursors, inverted intervals, and first-zero/overshot markers. `tests/utils/test_connections.py`, `tests/test_keyset.py`, optimizer tests, and connection tests passed. The integrated utility/caller run passed 2,212 tests.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

Plan-time and resolve-time pagination contracts remain single-sited and agree across offset, keyset, sidecar, marker, probe, and fallback shapes.

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
