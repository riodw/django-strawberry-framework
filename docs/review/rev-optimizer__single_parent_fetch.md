# Review: `django_strawberry_framework/optimizer/single_parent_fetch.py`

Status: verified

## Understanding

The single-parent wrapper is a runtime optimization over the windowed strategy. It captures a
plan-time direct-FK, count-free, forward, bounded-first-page spec, recognizes only a single
prefetch parent id with unchanged annotations/order/projection/select-related state, executes a
plain filtered `LIMIT`, synthesizes row numbers, and otherwise delegates to the windowed body.

## Verification

Traced spec eligibility and fetch recognition through Django prefetch injection, custom visibility
querysets, nested prefetches, sharding aliases, probe rows, deferred projection, and
`connection.py` marker consumption. Focused single-parent/lateral/nested-fetch tests and live
single-parent HTTP tests passed; the complete optimizer-focused run passed 781 tests and live
optimizer paths passed 350 with one skip.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The fast path is strictly performance-only: every uncertain or ineligible state falls back to the
same windowed query, preserving relation cardinality and page semantics. No change was justified.

## Implementation (Worker 1)

None — zero-edit cycle. Existing refusal matrix, row synthesis, nested-prefetch, setting toggle,
and fallback tests establish the no-change proof.

## Independent verification (Worker 2)

Re-read single-parent eligibility and fetch-time recognition, duplicate/NULL parent ids,
projection/select-related signatures, nested prefetch behavior, setting toggles, and fallback
parity. Focused optimizer tests passed (`781 passed`), and reachable HTTP optimizer coverage
passed (`350 passed, 1 skipped`). No defect was reproduced in this target; concurrent source edits
were preserved.

