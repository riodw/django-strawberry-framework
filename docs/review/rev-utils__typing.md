# Review: `django_strawberry_framework/utils/typing.py`

Status: verified

## Understanding

Owns Strawberry/GraphQL wrapper unwrapping, bounded type-container peeling, sync/async callable and async-generator detection, and schema/config extraction across Strawberry and graphql-core `Info` shapes.

## Verification

Checked callable instances, partials, staticmethod descriptors, async generators, cyclic/deep wrapper stacks, bare generic lists, `None`, direct versus wrapped schema config, and planner/field-factory consumers. `tests/utils/test_typing.py`, connection, optimizer, and type suites passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

Async dispatch and wrapper handling remain bounded and consistent across field factories, optimizer planning, and connection execution.

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
