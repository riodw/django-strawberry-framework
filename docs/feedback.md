# Adversarial review: enforcement ownership and execution lifecycle

Verdict: **changes required**. Reviewed the uncommitted production remediation over HEAD
`11928077`, its policy/schema tests and live resource-policy tests, the relevant
[Spec-047][spec-047] contracts, and the [Spec-050 build record][build-050]. This reviews
the working changes, not a claim that HEAD contains them or that every unrelated concurrent
test migration was audited. Criteria: [AGENTS.md][agents], [START.md][start], [GOAL.md][goal],
and the [live-test contract][live-readme].

Evidence comes from fresh `uv run python` probes and source tracing. The policy-mutation and
scalar-stage reproductions also ran over HTTP through `DjangoGraphQLView` and
`django.test.Client`, using an in-memory URL module and `DEBUG=False`. No pytest was run;
no production file or database was edited. The mutation used to assess a test was a
process-local replacement of one method, restored in that process.

## P1-1 — An accepted extension instance still exposes the next request's policy

Locations: `django_strawberry_framework/schema.py::DjangoSchema.extensions`,
`django_strawberry_framework/schema.py::DjangoSchema.get_extensions` ([schema][schema]), and
`django_strawberry_framework/extensions/resource_policy.py::DjangoResourcePolicyExtension._resolved_policy`
([extension][resource-extension]).

The tuple prevents replacing entries, but does not detach or protect its objects. An accepted
`DjangoResourcePolicyExtension` instance is returned unchanged by Strawberry and remains
reachable through `info.schema.extensions`. Its `_policy` is the authority consulted on the
next operation. A resolver can do this without importing the private registry:

```python
extension = next(
    entry for entry in info.schema.extensions
    if isinstance(entry, DjangoResourcePolicyExtension)
)
extension._policy = ResourcePolicy(max_list_rows=999)
```

Verified over HTTP on a schema initially configured with an instance carrying bound 1:

| Request | Result |
| --- | --- |
| `{ rows }` | `{"data": {"rows": ["a"]}}` |
| `{ attack }` | `{"data": {"attack": 1}}` |
| `{ rows }` | `{"data": {"rows": ["a", "b", "c"]}}` |

All three responses were HTTP 200 without errors. The rows resolver uses the actual
`bounded_rows` helper. No extension-list assignment occurs, so the new setter never intervenes.
Strawberry deprecates instance entries, but this package explicitly accepts and newly tests
them; deprecation does not discharge the supported-path invariant.

Root correction: capture package enforcement configuration independently of mutable extension
instances, and ensure operation arming cannot re-read a consumer-reachable instance as policy
authority. Preserve explicit-policy precedence and fresh-per-operation factories; do not
eagerly invoke factories or merely wrap the same objects in another immutable container.
The accepted-instance path needs a genuine private policy snapshot, not another presence check.

Tests: retain replacement-refusal tests, but add an HTTP sequence that mutates the
accepted instance and then requests rows. Check mutation of the stored policy object as well
as replacement of `_policy`, with separate node IDs. This is the remaining branch of the
prior extension-authority defect, not a claim about remote clients installing Python.

## P2-1 — The identity registry now permanently roots some schemas

Locations: `django_strawberry_framework/schema.py::_SchemaEnforcement`,
`django_strawberry_framework/schema.py::_remember_enforcement`, and
`django_strawberry_framework/schema.py::DjangoSchema.extensions` ([schema][schema]).

The registry's key reference is weak, but its value now strongly owns the complete extension
configuration. Extension objects and factories can point back to their schema. That creates
a path from a module-global root back to the weak referent, preventing collection and therefore
preventing the cleanup callback from ever running.

Two independent reproductions:

- An ordinary accepted extension instance acquires `execution_context` during execution.
  That context owns `schema`. After one successful query and deletion of all local owners,
  `gc.collect()` leaves a weak reference to the schema alive. The rooted chain is registry,
  record, extension tuple, extension instance, execution context, schema. It also retains the
  last request context and variables through that execution context.
- A supported schema subclass passes `extensions=[self.make_extension]`, where the bound
  method returns a fresh resource extension. The registry owns that bound method, which owns
  `self`. This schema cannot be collected even before its first request; it uses the
  non-deprecated factory path.

Controls: a class entry was collectable both before and after execution; an instance entry
was collectable before execution. Thus this is not merely an external probe reference keeping
the schema alive. The new lifecycle test constructs a default schema with class entries and
does not exercise either back-reference.

Root correction: redesign configuration ownership so the global registry does not strongly
own arbitrary extension object graphs. Schema/configuration cycles must remain collectable;
identity validation and assignment integrity are separate concerns from lifetime ownership.
Changing weak-reference callback logic cannot fix a callback that is never eligible to run.
Do not require callers to manually clear request state or unregister schemas to compensate.

Tests: package-level weak-reference lifecycle rows for class, instance-after-execution, and
bound-method factory configurations. Assert that the schema and a request-context sentinel
become unreachable after external owners are dropped. Keep these mechanics package-side;
they cannot be proved by an HTTP response alone.

## P2-2 — Literal scalar parsing precedes the claimed raw-value admission boundary

Locations: `django_strawberry_framework/extensions/resource_policy.py::DjangoResourcePolicyExtension.on_execute`
([extension][resource-extension]); Spec-047's value-source paragraph and Decision 13;
the glossary's [value-budget description][value-budget];
`examples/fakeshop/test_query/test_resource_policy_api.py::test_a_scalar_argument_is_bounded_by_the_shape_the_request_carried`
([live tests][live-resource-tests]).

The corrected variable test is valid, but the documentation generalizes its ordering to all
four input sources. GraphQL validation executes scalar `parse_literal` before `on_execute`.
With the ordinary scalar definition that supplies only `parse_value`, graphql-core's default
literal parser calls that `parse_value` too. Therefore the value budget is not universally
before custom conversion.

Verified with the same scalar parser recording calls, an over-width `[1, 2]`, and width bound 1:

| Input source | Parser calls before typed width rejection |
| --- | --- |
| Supplied variable | 0 |
| Inline literal | 1, carrying `[1, 2]` |
| Variable-definition default | 1, carrying `[1, 2]` |

All three HTTP responses rejected with `RESOURCE_LIMIT_EXCEEDED`, charged 2. The distinction is
work already performed, not whether a resolver ultimately ran. A costly scalar parser can
therefore perform work the new prose says admission prevents. The pre-parse token/depth
limits do not establish the separately configurable container-width or scalar-byte limits.

Root correction: put the raw-value admission needed to protect scalar conversion before
validation can invoke a scalar parser. Reuse the existing value-accounting implementation and
schema metadata; do not run custom parsers to measure their input, parse twice for accounting,
or duplicate GraphQL's entire validator. Preserve accurate malformed-document handling and
one charge per intended argument occurrence. Until that ordering is implemented, the spec and
glossary must not promise rejection before conversion for literals/defaults.

Tests: parameterize supplied variable, inline literal, and variable default, each with parser
call observations outside the guarded code and both admission/rejection verdicts over HTTP.
The current variable-only test cannot prove the all-sources sentence. Update the glossary's
database source when correcting its rendered description, per the repository rules.

## P2-3 — The largest accepted width overflows the new bounded reader

Location: `django_strawberry_framework/extensions/resource_policy.py::_ValueBudget._bounded_members`
([extension][resource-extension]).

`MAX_RESOURCE_BOUND` permits `9223372036854775807`. The new reader passes `limit + 1` as
`islice`'s stop argument, which must fit `sys.maxsize`. On this supported 64-bit interpreter,
that is one too large. Its own argument error is caught and mislabeled as an unmeasurable input.

Verified through `charge_document` with `ResourcePolicy(max_container_width=MAX_RESOURCE_BOUND)`:

| Value | Result |
| --- | --- |
| Exact empty list | Accepted |
| Empty subclass of list, with no overrides | Rejected, charged `9223372036854775808` |
| Same subclass carrying one integer | Same rejection |

The chained cause is `ValueError: Stop argument for islice() must be None or an integer:
0 <= x <= sys.maxsize.` No hostile iterator is needed. The mapping-subclass branch uses the
same helper and therefore the same invalid stop value. This is an in-process input contract
defect, not a claim that decoded JSON produces list subclasses.

Root correction: use a bounded reader whose lookahead counter supports the full declared
policy domain without submitting an out-of-range stop to `islice`. Preserve exactly one
lookahead, no length hints, typed failures for genuinely unreadable inputs, and no unbounded
fallback at the maximum. Do not lower the global policy ceiling to hide a helper mismatch.

Tests: accepted empty and nonempty custom sequences/mappings at the maximum, alongside the
small-bound excess cases. A row proving the maximum reaches SQL does not test this consumer
of the same bound.

## P3-1 — The new poison-advance proof catches its own failure

Location: `tests/test_resource_policy.py::test_a_container_is_not_advanced_once_its_width_is_already_proven`
([package tests][package-resource-tests]).

The generator raises `AssertionError` on its third advance. `_bounded_members` catches every
`Exception` and converts it to `ResourceLimitExceeded(bound, limit, limit + 1)`. At width 1,
that produces exactly the bound and charged value the test asserts. The test therefore passes
when the reader advances into the forbidden position.

Verified by replacing only `return list(islice(members(), limit + 1))` with
`return list(members())` in a process-local copy of the actual method, retaining its actual
exception handler, and calling `charge_document`:

| Reader | Advances | Current test's bound/charged assertions |
| --- | --- | --- |
| Current implementation | 1, 2 | Pass |
| Unbounded mutation | 1, 2, 3; then assertion raised | Pass |

This does not mean the production stop is currently absent: it works at ordinary bounds.
The neighboring finite counting tests provide useful protection too. It means this separately
named proof does not establish its claim, contrary to START's rule that failability evidence
must be observed outside the guard under test.

Root correction: record each advance in a probe-owned log and assert the exact log after the
typed rejection. Keep the poison as a secondary diagnostic, not the only witness. The
unbounded mutation above must fail that external assertion. This is an internal iterator
mechanic, so package test placement is appropriate.

## Verified corrections and limits

- Distinct equal schemas now kept bounds 1 and 999; collecting the first left the second at
  999. The identity-key correction addresses the old equality collision.
- Mutating a retained exact policy after schema construction left a subsequent bounded-row
  query at one row. The intake copy addresses the explicit-object alias.
- Assigning `schema.extensions = []` now raises `ConfigurationError`. The remaining finding
  concerns mutation of an object inside the accepted tuple, not failure of that setter.
- Normal small-width custom-container reads stopped after one excess member. The old eager
  full-copy defect is corrected; the maximum-bound and poison-proof defects above are distinct.
- The raw-variable scalar test now measures the stage it claims for supplied variables. The
  literal/default siblings reveal the remaining overstatement.
- The build record still certifies `207c7328` and explicitly excludes descendants. Default,
  sharded, and the declared seventeen-path floor gate remain unverified for this delivery
  tree. These probes do not establish coverage, full-suite success, or floor parity.
- Post-edit formatting left all 445 Python files unchanged. Repository-wide lint reported
  ten errors in the pre-existing untracked root `models.py` (undefined names, missing
  docstrings/annotation, and commented-out code). No automatic fixes were available; that
  unrelated file was left untouched. This review does not report a clean lint gate.

Fix the shared enforcement ownership/lifetime design first, then the admission-stage and
reader defects, with production changes and their tests together. Preserve the `Meta`-driven
consumer API. Observable request behavior belongs in the live tier; lifetime and iterator
instrumentation belong in package tests with their reachability rationale.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md
[start]: ../START.md

<!-- docs/ -->
[value-budget]: GLOSSARY.md#value-budget-walker

<!-- docs/SPECS/ -->
[spec-047]: SPECS/spec-047-resource_policy-0_0_14.md

<!-- docs/builder/ -->
[build-050]: builder/DONE/build-050-list_field_arguments-0_0_15.md

<!-- django_strawberry_framework/ -->
[resource-extension]: ../django_strawberry_framework/extensions/resource_policy.py
[schema]: ../django_strawberry_framework/schema.py

<!-- tests/ -->
[package-resource-tests]: ../tests/test_resource_policy.py

<!-- examples/ -->
[live-readme]: ../examples/fakeshop/test_query/README.md
[live-resource-tests]: ../examples/fakeshop/test_query/test_resource_policy_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
