# bld-048-remediation: adversarial-review remediation catalog

Status: remediated

Spec: [`docs/spec-048-secure_output_defaults-0_0_17.md`][spec-048]
Extends (does not replace): [`docs/builder/bld-048-final.md`][bld-048-final]
Card: `DONE-048-0.0.17`

Raw `path:NN` refs are permitted in this file (per-cycle artifact); the spec and the code
comments use symbol paths.

## What was wrong and what the fix was

### 1 (HIGH) Subscription results were never masked

`DjangoErrorPolicyExtension` masked only `execution_context.result` at operation teardown.
A subscription delivers one `ExecutionResult` per EVENT through the result source the
transport iterates, and the teardown runs only when the operation ENDS — so every event's
raw exception message reached the wire, and the teardown then rewrote a result nobody read.
Masking was bolted to the wrong seam, not merely missing a case.

Fix, at both seams with one implementation:

- `django_strawberry_framework/extensions/error_policy.py` — masking became three
  module-level seams: `mask_execution_result(result, policy)` (classify + replace + degrade),
  `masking_is_active(policy)` (the `enabled` + `DEBUG` gate), `schema_error_policy(schema)`
  (the guarded policy read). The extension's `_process_result` is now just the assignment.
- `mask_execution_result` **returns** a masked shallow COPY instead of editing in place, and
  returns the identical object when nothing needed masking. The copy is what preserves
  Decision 10's LIFO property on the subscription path: the object the engine assigned to
  `execution_context.result` keeps its `original_error`s for `DjangoDebugExtension`.
- `django_strawberry_framework/consumers.py` — `_stop_aware_results` gained a `schema`
  parameter and masks each yielded result; `_StopAwareSchema.subscribe` passes the REAL
  schema (the policy must be the executing schema's, never a wrapper attribute). The import
  of the masking helpers is function-local: this module's import graph is deliberately
  `strawberry`-free so `routers.py` can import it above its soft-dependency guard.
- Pre-execution errors are untouched by construction — a `PreExecutionError` IS a strawberry
  `ExecutionResult`, and its validation errors carry no `original_error`, so the classifier
  passes them through rather than the shape gate excluding them.

Tests: `tests/test_routers.py` — `EmittedRow` + `Subscription.leaky` (two events, one always
failing nullable field) and two consumer-level rows, one parametrized over both WS protocols.

### 2 (MEDIUM) `allow_unsafe_production` was not validated

`DjangoDebugExtension(allow_unsafe_production="false")` was truthy and ARMED production
disclosure. Now a `ConfigurationError` at construction (`extensions/debug.py::DjangoDebugExtension.__init__`),
following `ErrorPolicy.__post_init__`'s rule and using `describe_value`. Tests cover the
eight non-bool shapes plus the consequence at operation-build time.

### 3 (MEDIUM) No degrade path, and an unguarded policy read

- Masking now degrades **closed** at two levels: one error that cannot be classified or
  replaced becomes the policy message alone (no location, no correlation id — nothing is read
  off the error whose read just failed); a result whose `errors` cannot be read at all
  becomes a single policy-message error with no `data`. Both log with `exc_info`.
- `schema_error_policy` is `isinstance`-guarded, mirroring
  `extensions/resource_policy.py::DjangoResourcePolicyExtension._resolved_policy`. The
  fallback stays `DEFAULT_ERROR_POLICY` (the masking answer). Chosen over raising at schema
  construction because `DjangoSchema` already validates there — the guard exists for a
  consumer subclass or a stray assignment, which construction cannot see.

Note: the assignment in `_process_result` has NO third degrade, and that is deliberate —
both admitted shapes are mutable attribute holders, so it cannot fail; an unreachable
`try` there would be untestable coverage.

### 4 (MEDIUM) Completion-phase classification, and one test pinning a false premise

- Verified: graphql-core wraps every field-phase exception through `located_error`, so a
  resolver exception surfaced via value COMPLETION (non-null propagation, list-item
  completion, scalar `serialize`) arrives with `original_error` set and IS masked. No code
  change was required; the property was undocumented and untested, so it is now stated in
  `_is_unexpected` and pinned live (`examples/fakeshop/test_query/test_error_policy_api.py`:
  `boomNonNull`, `boomItems`).
- `tests/test_error_policy.py::test_an_execution_error_with_no_originating_exception_is_left_alone`
  was DELETED. Its docstring claimed a non-nullable-`null` completion error has no
  `original_error`; graphql-core sets it to the completion `TypeError`, so the row asserted
  a synthetic object's behavior while claiming to cover a real path. Replaced by
  `test_an_async_pre_execution_error_keeps_its_own_message`, which drives the branch's real
  traffic (an async validation failure arriving as `PreExecutionError`).

### 5 (MEDIUM) `_normalize_sequence_spec` refused a frozenset and misnamed the key

`types/base.py::_normalize_sequence_spec` now accepts any non-string `Sequence` **or** `Set`
and takes the key's name for its message (`Meta.exclude` stays the default, so that key's
message is unchanged). All four call sites pass their own key name. `str` stays refused.

### 6 (LOW) L8 / L10 / L11 / L12

- **L8** `_MAX_PAYLOAD_CHARS` → `_MAX_PAYLOAD_TEXT_CHARS`. The budget counts `_row_cost`,
  i.e. the rows' variable-length STRING values only — not keys, punctuation, or numbers. The
  name and both docs now say so, and the spec table row matches. Value unchanged (262144).
- **L10** The two-phase degrade in `_build_payload` was verified against the code and is
  now documented truthfully and asymmetrically: SQL collection keeps the rows serialized
  before the failure (`list.extend` appends as it iterates, including partway through the
  failing snapshot), exception collection degrades to `[]` because `_collect_exceptions`
  builds its own list and leaves nothing to salvage. The budget order (exceptions before SQL)
  is documented as a second, independent ordering, plus the consequence that a degraded
  exception list hands the whole budget to SQL.
  Also corrected: the spec's "a payload whose very first row already exceeds the budget
  admits that one row" edge case is UNREACHABLE — the per-row caps bound one row to ~20K
  characters against a 262144 budget — so the bullet now says so instead of describing a
  fallback the code does not have (the code `break`s).
- **L11** `MediaSpecimenWithPathType` STAYS in the shipped aggregate schema
  (`examples/fakeshop/apps/scalars/schema.py`). It is the stronger arrangement: the
  per-column claim only means something against a schema where an un-opted column sits beside
  an opted-in one. Live coverage confirmed present and sufficient in
  `examples/fakeshop/test_query/test_uploads_api.py`
  (`test_filesystem_path_opt_in_is_absent_unless_declared_over_http`,
  `test_opted_in_filesystem_path_resolves_over_http`,
  `test_default_file_output_objects_expose_no_filesystem_path_over_http`). The spec's
  "a probe type in a probe schema covers the opt-in" prose was the false half and was
  corrected; the test-plan file names (`test_secure_output_api.py`, `test_debug_gate_api.py`)
  were also corrected to the files that actually carry the rows.
- **L12** Decision 1's fourth bullet claimed the Python subclassing keeps a consumer's
  fragment on `DjangoFileType` matching an opted-in field. False: Python inheritance is not
  GraphQL subtyping, and the four types are four unrelated SDL objects. The true rationale
  (one definition of the shared members and their resolvers; future improvements reach both
  shapes) replaced it, with the SDL consequence stated and cross-referenced to Decision 4's
  migration note.

## Decisions taken during remediation

- **Masking lives in `extensions/error_policy.py`, not in `error_policy.py`.** The policy
  module stays the object + resolution; the extension module stays the application. Moving
  the classifier would have contradicted the spec's own DRY table for no gain, and
  `consumers.py` importing an extension module function-locally is the same shape it already
  uses for `channels.auth`.
- **Per-event masking copies rather than mutates.** An in-place rewrite would have been one
  line shorter and would have silently emptied `DjangoDebugExtension`'s exception rows for
  every subscription.
- **The `DEBUG` gate is read per event, the policy resolved per subscription.** The policy is
  immutable and its schema outlives the socket; the setting is legitimately overridable.

## Deferred / out of scope

- **Non-WebSocket subscription transports.** The package's own subscription seam is the
  Channels consumer result source. If a future card exposes subscriptions over HTTP
  (multipart / SSE) through a package-owned view, that transport needs the same
  `mask_execution_result` call at its own per-event delivery point. Nothing in the package
  serves subscriptions over HTTP today.
- **A consumer who builds a plain `strawberry.channels.GraphQLWSConsumer` themselves** gets
  no per-event masking: the seam is installed by
  `consumers.py::build_revalidating_consumer_class`, which the package router builds. This is
  the same boundary the operation-stop protocol already has, and it is the documented reason
  the package router is the supported mount.
- **`examples/fakeshop` has no subscription app**, so the subscription rows are consumer-tier
  in `tests/test_routers.py` rather than live-tier. A fakeshop subscription surface would be
  its own card; the live tier cannot reach a WebSocket through `django.test.Client`.
- The 26-item catalog in [`docs/builder/bld-048-final.md`][bld-048-final] is unchanged except
  where an item above supersedes it (its payload-cap and masking-seam items now read against
  the renamed constant and the two-seam application).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-048]: ../SPECS/spec-048-secure_output_defaults-0_0_17.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[bld-048-final]: bld-048-final.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
