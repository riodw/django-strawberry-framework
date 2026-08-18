# Review: `django_strawberry_framework/utils/converters.py`

Status: verified

## Understanding

Owns ordered conversion prechecks, most-specific registered MRO dispatch, typed fallthrough, conversion factories, and the finished-conversion adapter shared by form, DRF serializer, and filter conversion paths.

## Verification

Traced relation/file/multi-choice precedence, exact base-field continuation through `MRO_CONTINUE`, scalar subclass inheritance, unsupported-field errors, and the separate form/serializer registry key spaces. `tests/utils/test_converters.py` and the integrated filter/form/DRF suites passed. Existing concurrent edits in this module were preserved.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The shared dispatcher preserves flavor-specific prechecks while preventing unsupported fields from silently falling through to a scalar catch-all.

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
