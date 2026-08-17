# Review: `django_strawberry_framework/optimizer/selections.py`

Status: verified

## Understanding

`selections.py` is the shared AST and converted-selection substrate. It owns anonymous-safe
conversion, per-execution conversion caching, fragment/directive inclusion, response-key
preservation, connection `edges { node }` unwrapping, runtime prefixes, and direct
`totalCount`/`hasNextPage` observability.

## Verification

Traced the adapters against Strawberry's selected-field classes, GraphQL fragment validation,
anonymous inline fragments, aliases, directives, connection planner/runtime parity, root cache
variable walks, and mutation payload selection extraction. Focused selection, extension, walker,
connection, and live anonymous-fragment tests passed; the optimizer-focused suite totaled 781
passes.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The two adapters intentionally share policy without crossing dependency direction, and the
per-execution cache is reset with the extension lifecycle. No defect was reproduced.

## Implementation (Worker 1)

None — zero-edit cycle. Existing fragment/directive/alias/cache and live connection tests provide
the evidence; no formatting/linting was needed for this item.

## Independent verification (Worker 2)

Re-read AST and converted-selection adapters, anonymous fragments, directives, aliases, response
keys, connection unwraps, and per-execution conversion caches. Focused optimizer tests passed
(`781 passed`), with reachable HTTP optimizer coverage passing (`350 passed, 1 skipped`). No
defect was reproduced in this target.

