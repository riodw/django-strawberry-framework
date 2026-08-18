# Review: `django_strawberry_framework/utils/input_values.py`

Status: verified

## Understanding

Owns dict/dataclass input traversal, inactive-value classification, top-level order-list flattening, and leaf/related/logical field classification shared by filter and order permissions and normalizers.

## Verification

Traced `None` versus `strawberry.UNSET`, empty inputs, malformed dataclass metadata, hostile field reads, related declaration lookup, logical-field exclusion, and repeated order-list elements. Filter/order permission and input tests passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

Active-input semantics remain centralized without collapsing the distinct omit/null contract used by write decoders.

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
