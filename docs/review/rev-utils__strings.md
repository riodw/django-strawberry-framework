# Review: `django_strawberry_framework/utils/strings.py`

Status: fix-implemented

## Understanding

Owns GraphQL camel-case conversion, snake-case reversal, Pascal-case type naming, no-token validation, and lookup-path flattening.

## Verification

Checked acronyms, digit boundaries, leading/trailing/repeated underscores, empty tokens, cache behavior, string subclasses, generated input names, permission method names, and aggregate aliases. `tests/utils/test_strings.py` and generated-input caller suites passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

Naming transforms preserve the distinctions required by GraphQL field/type names and Django lookup paths.
## Iterations

An additional metamorphic pass found two shared naming invariants that were not actually guaranteed:

- `django_strawberry_framework/utils/strings.py::graphql_camel_name` followed by `snake_case` misdecoded legal names with adjacent one-letter segments such as `a_a_a`, returning `a_aa`. The codec now emits a reserved `__x` marker for that ambiguity, and `snake_case` consumes it without changing ordinary camel/acronym or repeated-underscore forms.
- `django_strawberry_framework/utils/strings.py::flatten_lookup_path` was not idempotent for repeated lookup separators and could leave `LOOKUP_SEP` in generated identifiers after one pass. It now normalizes to a fixed point.

The codec round-trip sweep covered 5,460 legal underscore/digit/letter combinations with zero failures. `tests/utils/test_strings.py` passed 26 tests, and the final downstream utility/filter/order/optimizer/type/live-visibility suite passed 2,627 tests after both adjustments. Strawberry accepted the reserved `__x` GraphQL name in a direct schema probe.

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
