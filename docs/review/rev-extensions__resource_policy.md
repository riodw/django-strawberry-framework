# Review: `django_strawberry_framework/extensions/resource_policy.py`

Status: verified

## Understanding

`DjangoResourcePolicyExtension` enforces the resolved immutable `ResourcePolicy`
in three stages: a lexer-based pre-parse token/depth scan, an iterative
validated-document walk that charges selections/aliases/collection cost, and an
iterative coerced-value walk that charges input nodes, nesting, widths,
membership/node/relation ids, nested rows, uploads, and scalar bytes. It stashes
the policy and monotonic deadline in the request context at operation start and
restores prior values or clears absent keys in a `finally` block.

The value walker is type-directed, charges GraphQL's scalar-to-list coercion as a
synthetic one-item list, and cycle-guards only ancestor references by identity.
The document walker expands fragments per spread site, handles introspection
meta-fields, detects Relay connection shape structurally, and skips only
untyped/unknown branches that validation itself owns. `on_execute` charges before
resolver execution; resource rejections remain typed GraphQL errors on the
ordinary execution path.

## Verification

- Traced the extension through `resource_policy.py`, `schema.py`, list/connection/
  Relay/mutation callers, context helpers, and the live fakeshop policy mounts.
- Reviewed pre-parse lexer failure handling, fragment-cycle guards, introspection
  accounting, scalar/list coercion, variable reuse, upload measurement,
  deadline/context cleanup, QuerySet/list bounds, async iterator closure, and
  per-field narrowing.
- `uv run pytest tests/test_resource_policy.py --no-cov` passed as part of the
  combined 197-test package extension run.
- `uv run pytest examples/fakeshop/test_query/test_error_policy_api.py
  examples/fakeshop/test_query/test_resource_policy_api.py --no-cov -q` passed
  53 live tests combined.
- Compile and Ruff checks passed for the extension modules and related tests.
- Existing concurrent changes in `extensions/resource_policy.py` and
  `tests/test_resource_policy.py` were preserved.

## Improvements

### High
- **Nested operations cleared the outer policy and deadline.**
  - **Observation:** `on_operation()` stashed its policy and unconditionally
    called `clear_resource_context()` in `finally`. An inner schema execution
    sharing the outer `info.context` therefore erased the outer policy instead
    of restoring it.
  - **Evidence:** Independent sync and async probes with an outer
    `max_list_rows=1` policy showed the policy changing to the default
    `max_list_rows=100` after an inner schema call; `bounded_rows()` then
    returned all rows. A configured deadline was erased as well.
  - **Impact:** Nested schema execution could widen subsequent outer collection
    work and bypass a deployment's configured resource ceiling.
  - **Recommendation:** Snapshot both context keys before stashing and restore
    each prior value (or clear only when it was absent) in `finally`.
  - **Proof:** `tests/test_resource_policy.py::test_nested_sync_schema_restores_the_outer_policy_and_deadline`
    and `test_nested_async_schema_restores_the_outer_policy_and_deadline`.

### Medium

None.

### Low

None.

## Summary

The resource-policy extension's pre-parse boundary, iterative document/value
accounting, coercion semantics, cycle handling, context lifecycle, deadlines,
collection bounds, and live transport behavior are coherent. The nested
resource-context lifecycle defect was fixed at the operation boundary.

## Implementation (Worker 1)

- Changed `resource_policy.py` to snapshot and restore both policy context keys
  around each operation, preserving nested outer state.
- Added sync and async nested-schema regressions covering row caps and deadlines.
- Preserved the pre-existing scalar-list accounting, finite-deadline, narrowing,
  and async bounded-row hardening already present in the working tree.
- No changelog entry was requested.

## Independent verification (Worker 2)

- Re-traced all three budget stages and confirmed context clearing survives
  pre-parse rejection and execution failures.
- Independently reproduced the sync and async nested-context cap bypass before
  the fix, including deadline erasure.
- Re-ran the package extension suite after the fix: 203 tests passed, and the
  post-fix live extension suites passed serially: 65 tests.
- No additional resource-policy finding remains.
