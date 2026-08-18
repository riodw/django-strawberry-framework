# Review: `django_strawberry_framework/utils/permissions.py`

Status: verified

## Understanding

Owns request decoding for Django and Channels contexts, auth-alias discovery, active-input permission traversal, flat relation-gate parity, class-level deduplication, and bounded related-branch recursion.

## Verification

Traced HTTP/Channels request shapes, divergent auth/read aliases, empty permission declarations, active-only gates, nested related branches, flat relation lookups, logical branches, async gate misuse, and recursion limits. Permission, filter, order, mutation, and Channels caller tests passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

Permission traversal applies the same active-input and target-gate policy to filter/order surfaces without widening the request-context or authorization boundary.

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
