# Review: `django_strawberry_framework/utils/context.py`

Status: verified

## Understanding

Owns defensive object/dict/mapping context reads, writes, and deletes shared by optimizer and resource-policy stashes. Missing, frozen, and ordinary access failures degrade to bounded defaults without swallowing process-control `BaseException` values.

## Verification

Traced reused request contexts, dict subclasses, slots-backed mappings, hostile descriptors, frozen mappings, `QueryDict`, optimizer clearing, and resource-policy restoration. `tests/utils/test_context.py`, optimizer context tests, and resource-policy extension tests passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

Context dispatch is symmetric where it should be and intentionally has narrower write/delete exception handling than reads; sequential-operation isolation remains intact.

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
