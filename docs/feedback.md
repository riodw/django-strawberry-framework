# Adversarial implementation review: spec 050 (fresh pass)

Date: 2026-09-14. Reviewed revision `ab98d240` and the current working tree against
the [specification][spec-050], [GOAL.md][goal], [AGENTS.md][agents], [START.md][start], and the
live-test rules in [the fakeshop test guide][live-readme]. The comparison also covered the local
[Strawberry-Django pagination implementation][strawberry-pagination], the installed
Graphene-Django fields, and the [cookbook schema][cookbook-schema] shape named by the project
instructions. Those upstream projects are migration references only; this package's Meta-first API
remains the contract under review.

No pytest command was run. The repository instructions reserve pytest for an explicit request,
and the current build record itself says the post-remediation default, sharded, and supported-floor
gates are still owed. The behavioral evidence below comes from source inspection and small,
non-pytest probes run against the current checkout.

## Verdict

**Not accepted yet.** The latest round closes the earlier routing, async cancellation, deterministic
async-deadline-test, effective-order-witness, exported-helper-coordinate, and definition-threading
concerns. Two production boundary defects remain: resolver code can replace either request-side
resource-policy seam, and hostile numeric subclasses can escape the typed resource-policy errors.
The test plan also still bundles independent claims into single nodes, and the final gate has not
been rerun after the latest production changes.

## Findings

### P1-1 — the cooperative budget is mutable consumer state and can be widened or cleared

The extension publishes both the frozen policy and a derived absolute deadline through the
consumer-owned `info.context` (the shape-agnostic dispatch in
[`utils/context.py`][context-utils]) in
[`DjangoResourcePolicyExtension.on_operation`][resource-extension] via
[`stash_resource_policy`][resource-policy]. Both exported keys are writable by resolver code:
`policy_from_info` accepts any `ResourcePolicy` currently stashed under `DST_RESOURCE_POLICY`,
while [`check_deadline`][resource-policy] trusts the scalar currently stored under
`DST_RESOURCE_DEADLINE`. Neither seam proves that its value is the one established at operation
start or that the two values still agree.

This is directly exploitable by ordinary resolver code in two independent ways. A minimal probe
stashed `ResourcePolicy(execution_deadline_seconds=0.001)`, replaced `DST_RESOURCE_DEADLINE` with
`time.monotonic() + 3600`, and called `check_deadline`; the check returned normally even though the
configured budget had already been exceeded by the time the next seam was reached. Replacing the
key with `None` has the same effect. A second probe stashed a policy with `max_list_rows=5`, then
had the resolver replace `DST_RESOURCE_POLICY` with `ResourcePolicy(max_list_rows=999)`; the same
bounded list seam returned 999 rows instead of 5. The frozen object is immutable, but the actual
request budget is not: every resolve-time bound derived through `policy_from_info` can be widened
by replacing the context value, bypassing `narrowed()` entirely.

That contradicts spec-047's “one immutable budget” and spec-050's deadline wording: a consumer
resolver can make the request start more work after its budget rather than merely narrow it. It is
also not limited to malicious code; a pre-existing application context key or a middleware/resolver
that reuses a generic string key can accidentally disable or widen the guard for the rest of the
operation. The deadline mutation is the small half of this finding; `DST_RESOURCE_POLICY` is the
larger seam because it carries `max_list_rows`, `max_page_size`, and every document, value, and
rejection limit consulted at resolve time.

**Root-cause correction:** move the authoritative policy and deadline to request-internal state that
resolver code cannot replace (for example, an execution-context-owned immutable budget capsule or a
private context-local token), and have `policy_from_info` / `check_deadline` validate that capsule
rather than trusting consumer-writable values. If the public context seams must remain for
compatibility, make their contents opaque framework tokens, keep the policy and absolute deadline
private, and reject a token whose identity or policy binding does not match the operation. Revisit
spec-047 Decision 2's context-only alternative analysis; the current design has context seams
without an authenticity boundary.

**Required proofs:** add live async HTTP rows where a resolver awaits, attempts to move the deadline
into the future, clears it, installs a non-finite deadline, and replaces the policy with a wider
`ResourcePolicy`; each must still enforce the operation-start policy at a collection seam and return
`RESOURCE_LIMIT_EXCEEDED` with the configured `limit`/`charged` values. Keep the existing
context-restoration tests so the fix does not leak state into an outer execution.

### P2-1 — hostile numeric subclasses escape typed resource-policy boundaries

The positive-integer validator in [`resource_policy.py::_require_positive_int`][resource-policy]
accepts `int` subclasses and immediately evaluates `value < 1`. A hostile subclass can raise from
that comparison, replacing the promised `ConfigurationError` with a raw exception. The same helper
is used by `validate_collection_bound`, so a hostile
[`list_field.py::DjangoListField`][list-field] `max_rows=...` declaration has the same
construction-site escape.

The narrowing path has a second copy of the problem: [`ResourcePolicy.narrowed`][resource-policy]
compares the preserved override value with `>` after `replace(...)`. A hostile positive subclass
can therefore raise a raw exception while the code is deciding whether a valid narrowing widens the
bound. More subtly, a benign-comparison subclass can pass construction and remain stored on the
frozen policy. When any bound rejects, `_ValueBudget._reject` passes that original object to
`ResourceLimitExceeded`; its f-strings and `extensions` payload format both `limit` and `charged`,
so a hostile `__format__` hook can turn any resource rejection into a raw `RuntimeError`, not just a
deadline-expiry error. Finally, a valid `float` subclass can survive `_is_valid_deadline`; its
reflected `__radd__` can even make `time.monotonic() + deadline` become `nan` during
[`stash_resource_policy`][resource-policy], so an accepted policy can silently disarm its own
deadline before `check_deadline` runs.

Current probes produced:

```text
ResourcePolicy(max_list_rows=BombInt(5))                  -> RuntimeError: lt bomb
ResourcePolicy(max_list_rows=2).narrowed(max_list_rows=BombInt(3))
                                                          -> RuntimeError: lt bomb
expired policy with CeilBomb(1.0)                        -> RuntimeError: ceil bomb
ResourcePolicy(max_list_rows=FmtInt(2)); rejected bound -> RuntimeError: format bomb
accepted float subclass stashed; derived deadline    -> nan; check_deadline passed
```

The existing hostile-deadline test in [`tests/test_resource_policy.py`][test-resource-policy] only
covers a subclass whose comparison raises during construction; it does not cover a valid subclass
reaching narrowing or expired-error rendering. The direct list-argument boundary in
[`tests/test_list_field.py`][test-list-field] is hardened with exact-int checks, but the policy and
field configuration boundaries are not.

**Root-cause correction:** canonicalize policy and field-bound numerics to exact built-in values at
the construction boundary, or reject all numeric subclasses with a typed `ConfigurationError`
before any comparison, arithmetic, or formatting. Store only built-in `int` / `float` values on a
policy and on field configuration so `narrowed`, deadline arithmetic, and GraphQL error
serialization cannot dispatch consumer dunders. This boundary canonicalization closes the
reflected-`__radd__` deadline case and the error-rendering case at the same time; adding scattered
`try` blocks around every later comparison is an inconsistent and incomplete containment posture.
Add package tests for hostile integer construction, hostile integer narrowing, a valid hostile float
that reaches expiry and deadline derivation, a hostile `max_rows` declaration, and a valid
comparison-but-hostile-format bound that reaches each relevant rejection family. The tests must
assert the typed error, not merely that “some exception” was raised.

### P2-2 — non-finite deadline values in the exported context key fail open

[`check_deadline`][resource-policy] checks only `isinstance(deadline, (int, float))` and then
compares it with `time.monotonic()`. It does not apply the same finiteness rule that
`ResourcePolicy.__post_init__` applies to configured deadlines. A numeric value manually placed in
the consumer context as `float("nan")` or `float("inf")` therefore returns without a rejection:

```text
DST_RESOURCE_DEADLINE = nan   -> check_deadline passed
DST_RESOURCE_DEADLINE = inf   -> check_deadline passed
DST_RESOURCE_DEADLINE = -inf  -> ResourceLimitExceeded
```

The key is exported and consumer-writable, which makes this the observable half of P1-1 rather than
an academic constructor case. The premise that a configured policy cannot create these values is
also false: an accepted `float` subclass with a reflected `__radd__` can turn the
`time.monotonic() + deadline` result into `nan` inside `stash_resource_policy`; the policy is
accepted, its derived deadline is `nan`, and the expired check passes. A malformed numeric stash is
neither “absent” nor “non-numeric”; treating it as a future deadline silently disables a guard whose
documented stance is fail closed.

**Required correction:** canonicalize the deadline field to an exact built-in `float` before
deriving the absolute deadline; this closes both the reflected-subclass and construction-boundary
holes. Once the authoritative deadline state is protected as described above, also reject any
numeric value in a compatibility seam that is not finite before comparing it. Add direct tests for
`nan`, `+inf`, and `-inf`, an accepted hostile float whose derived deadline would otherwise be
`nan`, and a live mutation control proving a resolver cannot install any of them to bypass the
configured budget.

### P2-3 — the final verification gate is explicitly still owed

The current [build record][build-050] and the specification both state that the last green figures
were measured before the latest production changes and that the default, `FAKESHOP_SHARDED=1`, and
supported-floor runs must be rerun. The build plan still has its final test-run item unchecked. No
fresh coverage, sharded routing, structural, or floor result can therefore be used as evidence that
the cancellation, routing, and deadline changes preserve the repository's 100% package gate.

This is a release-blocking evidence gap, not a request to paper over failures with a test-only
change. After the two production corrections, rerun the required format/lint/structural checks and
the three identified test tiers on one identified tree; record exit status and exact counts in the
build artifact. Until that happens, “implementation complete” is not an independently verified
claim.

### P3-1 — live test nodes still bundle independent claims contrary to the repository contract

The live guide requires one claim per node id and says to parametrize rather than loop. The current
spec-050 suites still combine failures that can regress independently:

- [`test_shipped_branches_coercion_failures_and_integral_floats`][sync-list-tests] loops over
  string, boolean, and float variables, then adds a float literal and an integral-float success
  case under one node.
- [`test_shipped_branches_empty_order_and_permission_precedence`][sync-list-tests] asserts two
  different empty-order forms and a permission-precedence form in one node.
- [`test_shipped_branches_error_precedence_pairs`][sync-list-tests] carries three unrelated
  precedence claims (numeric ordering, materialized source, and pre-sliced source) in one node.
- [`test_holder_branches_post_orderset_malformed_result_matrix`][sync-list-tests] drives ten
  malformed `OrderSet` results through one helper/test body; a failure in an early arm prevents the
  remaining defect classes from running.
- The async sibling repeats the pattern in
  [`test_async_queryset_completion_optimizer_on_and_off`][async-list-tests],
  [`test_async_error_transport_and_naming`][async-list-tests], and the context-preservation rows.
- [`test_async_holder_branches_post_orderset_seals`][async-list-tests] is a numbered five-defect
  `apply_async` matrix in one node, the exact async twin of
  `test_holder_branches_post_orderset_malformed_result_matrix`.

An AST census of the two live modules finds 14 loop-in-test-body cases without parametrization.
Several are legitimate seeding, SQL, or census loops, so the rule is not “split every loop”;
independent behavioral claims must still own distinct node ids. The async holder matrix above is a
clear missed case under that rule.

These are not equivalent-data censuses: each arm protects a different boundary or precedence rule.
One-node bundling weakens failability accounting and makes a green row unable to show which claim
would fail when its boundary is removed.

**Required correction:** split distinct invariants into separately named tests, or use
`pytest.mark.parametrize(..., ids=[...])` so every case has its own node id. Keep the exact GraphQL
error/SQL assertions with the case that owns them; retain a must-not control beside each scoped
positive claim.

## Closed checks from this pass

The following earlier concerns were re-checked and are not open findings:

- [`utils/querysets.py::_snapshot_routing_intent`][querysets] resolves an effective alias before a
  public `OrderSet` override and the accepted seal is pinned to that alias; in-place routing edits
  no longer move the completed read.
- Async cleanup now demotes only ordinary `Exception` failures; cancellation and other control
  `BaseException` signals propagate from both cleanup seams.
- The live async deadline row crosses an actual resolver `await`, uses a wide deterministic budget,
  and proves zero advancement plus exactly one close for the default and zero-limit windows.
- The async effective-order row records compiler-built SQL, so dormant random terms are not accepted
  on a lucky row value alone.
- `bounded_rows` and `bounded_rows_async` no longer accept client coordinates; the private window
  seam is the only coordinate-bearing path.
- The optimizer's nested planner, synthesized relation connections, and connection cache now carry
  the captured registry definition rather than re-reading the target class at request time.
- The spec's DRY paragraph intentionally says argument-bearing visibility uses `reject-combined` at
  both source and result seals; the adjacent em-dash clause supplies the message-arm requirement.
  This wording was re-read against the implementation and is not a finding.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md
[start]: ../START.md

<!-- docs/ -->
[spec-050]: spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-050]: builder/DONE/build-050-list_field_arguments-0_0_15.md

<!-- django_strawberry_framework/ -->
[context-utils]: ../django_strawberry_framework/utils/context.py
[list-field]: ../django_strawberry_framework/list_field.py
[querysets]: ../django_strawberry_framework/utils/querysets.py
[resource-extension]: ../django_strawberry_framework/extensions/resource_policy.py
[resource-policy]: ../django_strawberry_framework/resource_policy.py

<!-- tests/ -->
[test-list-field]: ../tests/test_list_field.py
[test-resource-policy]: ../tests/test_resource_policy.py

<!-- examples/ -->
[async-list-tests]: ../examples/fakeshop/test_query/test_list_field_async_api.py
[live-readme]: ../examples/fakeshop/test_query/README.md
[sync-list-tests]: ../examples/fakeshop/test_query/test_list_field_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[cookbook-schema]: ../../django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py
[strawberry-pagination]: ../../strawberry-django-main/strawberry_django/pagination.py
