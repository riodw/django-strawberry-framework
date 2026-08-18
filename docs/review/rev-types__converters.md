# Review: `django_strawberry_framework/types/converters.py`

Status: verified

## Understanding

This module owns Django-field-to-GraphQL conversion. `SCALAR_MAP` and `scalar_for_field` serve scalar and filter-input conversion; `FIELD_OUTPUT_TYPE_MAP` and `convert_field_output` exclusively serve read-side file/image objects; choices become cached Strawberry enums; PostgreSQL containers use their dedicated conversion paths; and `resolved_relation_annotation` renders cardinality and nullability after final relation binding.

## Verification

- Traced scalar conversion through `types/base.py::_build_annotations`, filters input conversion, enum registry caching, and PostgreSQL optional-field handling.
- Traced file/image output through generated parent/subfield resolvers, storage failure guards, `Meta.filesystem_path_fields`, nullability overrides, and live GraphQL selections.
- Traced relation annotations through pending finalization and `FieldMeta` cardinality metadata.
- `uv run pytest --no-cov -q tests/types`: 506 passed.
- Live library HTTP 197 passed and products/scalars/uploads HTTP 156 passed, including scalar, choice, file, image, and path opt-in behavior.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

Conversion responsibilities are separated between scalar/filter inputs and structured read outputs, with enum caching and relation rendering aligned with downstream resolver and finalizer contracts.

## Implementation (Worker 1)

No production or permanent-test change was warranted.

## Independent verification (Worker 2)

The converter was challenged through unsupported fields, choice-enum generation, nullable output, PostgreSQL branches, storage failures, and live GraphQL output. No defect or worthwhile owner-level improvement was found.

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
