# Review: `django_strawberry_framework/resource_policy.py`

Status: verified

## Understanding

`ResourcePolicy` owns the immutable, schema-construction budget: document tokens/depth/selections,
collection cost/page/list ceilings, input cardinality/depth/width, relation ids, uploads, scalar
bytes, and the optional cooperative deadline. `resolve_resource_policy` applies the explicit
`DjangoSchema(resource_policy=...)` > live `RESOURCE_POLICY` setting > package-default precedence;
`conf.py::resource_policy_setting` is a thin live reader, while `DjangoSchema` resolves once and
publishes the frozen policy through `DjangoResourcePolicyExtension`.

The extension performs the pre-parse lexer scan and post-parse document/value walk. Its `_ValueBudget`
charges coerced argument shapes before id decoding, queryset construction, or resolver execution.
The walker's list-family classification feeds node-refetch, membership, mutation-relation, and
nested-row limits; uploads are charged after Django materializes their file objects. The context
stash is fail-closed and cleared after each operation.

`bounded_rows` is the shared raw-list seam. `DjangoListField` applies it after queryset
normalization/visibility, preserving lazy QuerySet slicing (`high_mark`/SQL `LIMIT`), while generated
many-side relation resolvers apply it to prefetched or manager-backed rows. The concurrent baseline
already included `bounded_rows_async` and list-field async dispatch for async-only iterables; this
review checked its prefix, closure, dual-protocol QuerySet, trusted widening, and source-error
behavior. Connections clamp explicit/configured `relay_max_results` through
`utils/connections.py::resolve_relay_max_results`; deadline checks also cover the shared connection
head, Relay refetch, and mutation write seams. Optimizer planning receives the already-clamped
connection cap and sees the same visibility-sealed QuerySet.

## Verification

- `git --no-pager diff 682ec25e240aa52999ca058fe3aff05a349c8764 -- django_strawberry_framework/resource_policy.py`
  was empty; the scoped baseline already contained the async helper WIP. The review traced the
  helper's callers and expanded ownership only where the policy invariant crossed into the
  extension/value walker.
- Existing package tests cover policy construction, settings precedence/reload, frozen/dict/object
  contexts, trusted/narrowing semantics, document/value budgets, raw-list limits, deadline seams,
  and connection-shape accounting. Existing live fakeshop tests cover HTTP token/depth/selection/
  alias/cost/value/upload/row/deadline limits, connection-only relation shape, mutation relation
  ids, zero-query rejection, and sync/async error-code parity.
- Scratch `docs/review/temp-tests/resource_policy/contract_edges.py` reproduced the pre-fix
  `TypeError` from an invalid `narrowed(max_page_size="bad")` override and acceptance of infinite/
  NaN/oversized-integer deadlines. It also exercised scalar-to-list value accounting.
- Direct async-iterator probes covered bounded-prefix consumption, `aclose()` after an early cap,
  natural source errors, and cleanup errors without allowing cleanup to mask the source failure.
- Focused validation:
  `uv run pytest tests/test_resource_policy.py examples/fakeshop/test_query/test_resource_policy_api.py --no-cov -q`
  — 120 passed;
  `uv run pytest tests/test_resource_policy.py tests/test_list_field.py --no-cov -q` — 129 passed;
  `uv run pytest tests/base/test_conf.py tests/test_connection.py tests/mutations/test_resolvers.py --no-cov -q`
  — 180 passed.
- `uv run ruff format .` and `uv run ruff check --fix .` passed; scoped `git diff --check` is clean.

## Improvements

### High

None.

### Medium

- **Bare values for declared GraphQL lists were undercharged.**
  - **Observation:** `_ValueBudget.charge` pushed a scalar directly through a `GraphQLList` type
    without charging the synthetic one-item list's family or value-depth level.
  - **Evidence:** GraphQL input coercion accepts a scalar for a list and wraps it. Before the fix,
    a scalar relation-id value could avoid relation-id aggregate/per-mutation accounting, and a
    nested scalar list did not consume its declared list depth.
  - **Impact:** Repeated scalar list references could bypass the cardinality/depth budget even
    though the ORM and mutation pipeline receive the coerced list shape.
  - **Recommendation:** Charge a synthetic width-one container, classify it through the existing
    `_charge_list_family` owner, and add one ancestor-path level before visiting the scalar.
  - **Proof:** `tests/test_resource_policy.py::test_scalar_list_coercion_charges_each_declared_list_level`
    rejects a bare variable at `max_value_depth=1` for `[[String!]]` while accepting it at depth 2.

- **`ResourcePolicy.narrowed` leaked comparison errors and non-finite deadlines were accepted.**
  - **Observation:** `narrowed(max_page_size="bad")` compared the raw override before dataclass
    validation and raised `TypeError`; `execution_deadline_seconds=inf`/`nan` passed the positive
    number check, with infinity effectively disabling the optional budget.
  - **Evidence:** The scratch contract probe reproduced both behaviors. The public contract says
    invalid policies fail with `ConfigurationError`, and every bound is fail-closed except an
    explicit `None` deadline.
  - **Impact:** Deployment/configuration mistakes produced unstable exception types, while a
    non-finite deadline could silently become an unbounded execution policy.
  - **Recommendation:** Build the candidate through `replace()` (thereby invoking the one
    `__post_init__` validator) before comparing narrowing, and require finite deadline numbers.
  - **Proof:** `tests/test_resource_policy.py::test_narrowing_validates_override_domains_before_comparing_them`
    plus the invalid deadline parameterization pin the typed construction failures.

- **Async iterator cleanup could mask the original source failure.**
  - **Observation:** `bounded_rows_async` awaited `aclose()` in `finally` without preserving an
    exception raised by `__anext__`.
  - **Evidence:** A disposable iterator whose `__anext__` raised `ValueError` and whose `aclose`
    raised `RuntimeError` surfaced the cleanup error before the fix.
  - **Impact:** Consumer/source failures were replaced by cleanup failures, obscuring the root cause
    and changing the public GraphQL error observed by async list callers.
  - **Recommendation:** Preserve the source exception as primary, attach cleanup failure as a
    note, and still propagate cleanup failure when iteration itself succeeded.
  - **Proof:** `tests/test_resource_policy.py::test_bounded_rows_async_preserves_source_errors_when_cleanup_fails`
    and `test_bounded_rows_async_closes_after_the_effective_prefix`.

### Low

None.

## Summary

The policy object, settings resolution, context lifecycle, document/value accounting, bounded
QuerySet/list/connection/mutation/optimizer callers, trusted field widening, deadline seams, and
live fakeshop contracts are coherent. Three bounded correctness gaps were fixed at their invariant
owners: scalar-list coercion accounting in the enforcement walker, typed/finite policy validation
in `ResourcePolicy`, and async iterator cleanup precedence in `bounded_rows_async`. No high-severity
finding or unrelated cleanup was justified.

## Implementation (Worker 1)

- Changed `django_strawberry_framework/resource_policy.py` to reject non-finite or non-representable
  deadlines, validate `narrowed()` candidates before comparison, and preserve source exceptions
  while closing bounded async iterators. The existing async helper remains lazy for dual-protocol
  QuerySets and closes async-only iterators after the effective prefix.
- Changed `django_strawberry_framework/extensions/resource_policy.py` so GraphQL's scalar-to-list
  coercion charges a width-one synthetic container, the appropriate list family, and each declared
  list-depth level.
- Added permanent package tests in `tests/test_resource_policy.py` for finite deadline validation,
  typed narrowing failures, scalar nested-list coercion, bounded async closure, and source-error
  precedence.
- Scratch verification: `docs/review/temp-tests/resource_policy/contract_edges.py` showed the
  pre-fix `TypeError`/non-finite acceptance and the corrected typed failures after implementation.
- Focused tests and formatter/linter results are recorded above; no full test suite was run.
- Rejected findings: no additional settings-cache change was needed because `conf.Settings` already
  reloads live replacements/deletions and the focused `test_conf.py` suite passes; no extra list,
  connection, mutation, or optimizer seam was added because existing shared callers already route
  through `bounded_rows`, `resolve_relay_max_results`, and the documented deadline checks.
- Changelog: no entry requested; this is an alpha resource-boundary correctness hardening.

## Independent verification (Worker 2)

- Replayed each accepted pre-fix defect independently from the baseline:
  `narrowed(max_page_size="bad")` raised `TypeError` before candidate validation;
  `inf`, `nan`, and an oversized integer deadline passed the old positive-number
  predicate; a bare scalar for `[[String!]]` kept the old ancestor path and passed
  `max_value_depth=1`; and a source `ValueError` plus failing `aclose()` surfaced the
  cleanup `RuntimeError`. The current implementation instead returns typed
  `ConfigurationError`s, rejects the scalar at `max_value_depth`, and preserves the
  source error with a cleanup note.
- Direct current probes covered async prefix consumption and `aclose()`, successful
  cleanup failure propagation, natural exhaustion without an unnecessary close, and
  dual-protocol Django `QuerySet` laziness (`high_mark` set and `_result_cache` still
  `None` for both `bounded_rows` and `bounded_rows_async`). The live context probe
  confirmed settings/constructor precedence and monotonic deadline behavior.
- Focused validation passed:
  `uv run pytest tests/test_resource_policy.py examples/fakeshop/test_query/test_resource_policy_api.py --no-cov -q`
  (121 passed);
  `uv run pytest tests/test_resource_policy.py tests/test_list_field.py --no-cov -q`
  (130 passed);
  `uv run pytest tests/base/test_conf.py tests/test_connection.py tests/mutations/test_resolvers.py --no-cov -q`
  (180 passed); and
  `uv run pytest tests/test_relay_node_field.py tests/test_relay_connection.py tests/optimizer/test_extension.py --no-cov -q`
  (285 passed). The scoped baseline diff contains only
  `resource_policy.py`, `extensions/resource_policy.py`, and
  `tests/test_resource_policy.py`; `git diff --check` is clean.
- **Revision needed — expired deadlines bypass model-less plain-form writes.**
  `forms/resolvers.py::_run_plain_form_pipeline_sync` opens
  `transaction.atomic()` and enters `pipeline_write_phase()` around
  `perform_mutate`, but never calls `resource_policy.py::check_deadline`. The
  plain-form contract permits ORM work in that hook, as permanently demonstrated by
  `tests/forms/test_resolvers.py::test_plain_form_perform_mutate_may_write_inside_the_write_phase`;
  the fakeshop Kanban `DjangoFormMutation` classes use the same service-backed write
  window. A disposable real `DjangoSchema` probe at
  `docs/review/temp-tests/resource_policy/plain_form_deadline.py` configured
  `execution_deadline_seconds=0.000001`, executed a plain-form `perform_mutate`
  that created a `Category`, and returned `ok=True` with captured SQL. This
  contradicts the artifact/spec exclusion claiming the model-less path has no
  database seam. Add the deadline check immediately before that plain-form
  transaction opens, with a permanent live or package test proving the expired
  write performs no ORM work; then re-run the focused mutation/deadline suites.

## Iterations

### Worker 1 revision after Worker 2 verification

- Reproduced the finding with the disposable plain-form probe and traced the owner boundary:
  `forms/resolvers.py::_run_plain_form_pipeline_sync` is the model-less pipeline used by both
  `resolve_form_sync` and the shared `run_pipeline_async` wrapper. Unlike the model-backed
  `mutations/resolvers.py::run_write_pipeline_sync`, it opened its own transaction without
  `check_deadline`.
- Added `check_deadline(info)` immediately before `require_managed_write`/`transaction.atomic()` in
  `_run_plain_form_pipeline_sync`. The async form entry uses that same sync body in its
  thread-sensitive worker, so sync and async plain forms now share the guard without a second
  deadline implementation.
- Added `tests/forms/test_resolvers.py::test_plain_form_expired_deadline_rejects_before_perform_mutate_write`.
  It builds a real `DjangoSchema` with a mutable request context and an expired positive deadline,
  proves the typed `RESOURCE_LIMIT_EXCEEDED` error, confirms `perform_mutate` did not run, and
  rejects ORM DML while allowing the execution-context's outer transaction cleanup statements.
- Focused validation:
  `uv run pytest tests/forms/test_resolvers.py tests/test_resource_policy.py examples/fakeshop/test_query/test_resource_policy_api.py --no-cov -q`
  — 172 passed;
  `uv run pytest tests/forms/test_resolvers.py::test_plain_form_expired_deadline_rejects_before_perform_mutate_write --no-cov -q`
  — 1 passed.
- `uv run ruff format .` and `uv run ruff check --fix .` passed; the final scoped diff is clean.
- Changelog: no entry requested; this closes a missed deadline seam in the alpha write surface.

### Independent verification (Worker 2, pass 2)

- The requested baseline `682ec25e240aa52999ca058fe3aff05a349c8764e` is not a valid
  40-character Git object (it is 41 characters), and
  `git --no-pager diff 682ec25e240aa52999ca058fe3aff05a349c8764e -- ...` returns
  `fatal: bad revision`. I preserved the dirty concurrent worktree and instead checked
  the current item-17 target diff against `HEAD`; it contains only
  `resource_policy.py`, `extensions/resource_policy.py`, `forms/resolvers.py`, and
  their two permanent test files.
- Re-verified every accepted defect through the permanent tests and current code:
  finite and oversized integer deadlines reject as `ConfigurationError`;
  invalid `narrowed()` overrides reject before comparison;
  scalar-to-list coercion charges a synthetic width-one container, list family, and
  each declared list level; and sync/async bounded rows preserve the effective prefix,
  close early, keep dual-protocol QuerySets lazy/sliced, propagate successful cleanup
  failures, and keep a source exception primary with cleanup failure attached as a note.
- Re-traced the new plain-form seam. Both sync `resolve_form_sync` and async
  `resolve_form_async` converge on `_run_plain_form_pipeline_sync`, where
  `check_deadline(info)` runs before `require_managed_write`, `transaction.atomic()`,
  and `perform_mutate`. The permanent sync regression test returns
  `RESOURCE_LIMIT_EXCEEDED`, never calls `perform_mutate`, and captures no model DML;
  a disposable async `DjangoSchema` probe confirms the same error code and no
  `Category` write.
- Proved the permanent test is load-bearing: an in-process pytest-plugin probe
  monkeypatched only `forms.resolvers.check_deadline` to a no-op, ran
  `tests/forms/test_resolvers.py::test_plain_form_expired_deadline_rejects_before_perform_mutate_write`,
  and exited 1 because the mutation returned `{'submit': {'ok': True, 'errors': []}}`
  instead of `data is None`.
- Focused/live validation passed:
  `uv run pytest tests/test_resource_policy.py tests/test_list_field.py tests/forms/test_resolvers.py examples/fakeshop/test_query/test_resource_policy_api.py --no-cov -q`
  — 216 passed;
  `uv run pytest tests/test_connection.py tests/test_relay_node_field.py tests/test_relay_connection.py tests/mutations/test_resolvers.py --no-cov -q`
  — 264 passed;
  `uv run pytest tests/base/test_conf.py tests/test_error_policy.py tests/optimizer/test_extension.py --no-cov -q`
  — 245 passed; and disposable async/plain-form probes — 4 passed.
  `python -m py_compile` over all three target modules and both permanent test files
  passed, and scoped `git diff --check` passed.
- Prior rejected findings remain disposed: settings reload/precedence is covered by
  `tests/base/test_conf.py`; existing shared list, connection, mutation, and optimizer
  callers already enforce the policy, so no duplicate seam was added. No further
  correctness or scope finding remains.
