# Review: `django_strawberry_framework/optimizer/nested_fetch.py`

Status: verified

## Understanding

This module owns the strategy protocol, request fetch-mode validation, strategy registry and
ContextVar, windowed strategy, auto strategy, and child-queryset safety classification. Strategies
must attach rows under the planner's `to_attr` contract; refusal leaves the relation unplanned and
strictness-visible, while auto selects lateral at fetch time without embedding a database alias in
the plan cache.

## Verification

Traced strategy selection from extension construction and hints through nested planner request
creation, lateral/single-parent wrappers, connection marker/probe/count modes, and alias routing.
Focused nested-fetch, nested-planner, lateral, single-parent, and live auto-strategy tests passed
within the 781 optimizer tests and 350 live paths.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The seam has a stable correctness floor, explicit fallback discipline, and request-local strategy
publication. No source or permanent-test change was justified.

## Implementation (Worker 1)

None — zero-edit cycle. Existing strategy refusal, falsey custom strategy, setting, and
non-Postgres fallback tests provide the no-change proof.

## Independent verification (Worker 2)

Re-read the strategy protocol, request-mode assertions, windowed floor, auto/lateral dispatch,
fetch-time classifier, and ContextVar publication. Focused optimizer tests passed (`781 passed`),
and reachable HTTP optimizer coverage passed (`350 passed, 1 skipped`). No defect was reproduced
in this target; concurrent edits were preserved.

