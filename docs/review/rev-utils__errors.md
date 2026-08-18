# Review: `django_strawberry_framework/utils/errors.py`

Status: fix-implemented

## Understanding

Owns the flavor-neutral `FieldError` leaf, relation-id error, Django validation mapper, integrity-conflict envelope, safe text conversion, and nested dotted-path joining used by model, form, serializer, and auth writes.

## Verification

Traced root versus nested `__all__`, message/code normalization, hostile validation metadata, non-field errors, integrity races, and serializer recursive flattening. Utility, form, DRF, mutation, and auth tests passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

All write flavors share one safe error-leaf construction and preserve the documented root/nested path distinction.
## Iterations

An additional hostile-shape pass found that `django_strawberry_framework/utils/errors.py::validation_error_to_field_errors` returned no leaves for `ValidationError({})` and emitted a leaf with no messages for other empty shapes. A caught validation failure could therefore produce a null mutation node with an empty or content-free error envelope. The mapper now emits one `__all__` or field-keyed `invalid` fallback leaf whenever Django supplies no details. `tests/utils/test_errors.py::test_validation_error_mapper_never_returns_an_empty_envelope` covers empty dict, list, and per-field forms; the 2,220-test utility/caller/live integration run passed.

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
