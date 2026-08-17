# Review: `django_strawberry_framework/optimizer/join_taxonomy.py`

Status: verified

## Understanding

The join taxonomy is the single relation-shape classifier consumed by windowed, lateral,
single-parent, projection, and index-advisory code. It resolves direct-FK, through-table M2M,
reverse one-to-one, and GenericRelation partition/attach columns while failing closed on malformed
descriptors.

## Verification

Read the complete classifier and traced raw Django relation descriptors for forward/reverse FK,
M2M, reverse O2O, GenericRelation, self-relations, MTI links, and relation-field test doubles.
Focused taxonomy, field metadata, nested-fetch, lateral, index-advisory, and live library tests
passed as part of the 781 optimizer tests and 350 live optimizer-path tests.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

All consumers use the same guarded relation facts; malformed metadata degrades to unwindowable
rather than guessing. No source or permanent-test change was justified.

## Implementation (Worker 1)

None — zero-edit cycle. The existing adversarial truth/accessor matrix and live relation coverage
earned the no-change result.

## Independent verification (Worker 2)

Re-read the shared relation classifier and traced direct FK, reverse FK/O2O, M2M through-table,
GenericRelation morph/attach columns, and malformed descriptor fallbacks. Focused optimizer tests
passed (`781 passed`), with reachable HTTP optimizer coverage passing (`350 passed, 1 skipped`).
No defect was reproduced in this target.

