# Adversarial implementation review: spec 050 (fresh pass)

Date: 2026-09-14. Reviewed revision `9eb58a96` and the current implementation against the
[specification][spec-050], the [completed build record][build-050], [GOAL.md][goal],
[AGENTS.md][agents], and the live-test rules in [the fakeshop test guide][live-readme]. This
pass deliberately targets lifecycle, configuration, and operation-selection behavior that the
previous numeric-domain, deadline-mirror, async-cleanup, routing, and definition-threading
reviews did not exercise.

No pytest command was run. The repository instructions reserve pytest for an explicit request.
The build record contains historical green figures, while the probes below are fresh checks
against the current checkout.

## Verdict

**Not accepted yet.** The previously reported deadline-mirror, upload-size, exact-bound,
async-cleanup, routing, and definition-capture defects are fixed in the current code. This pass
found three remaining production/contract issues:

1. the operation budget retains the same mutable `ResourcePolicy` object exposed on the schema,
   so a resolver can widen later fields by editing its `__dict__`;
2. a factory-installed policy extension can be duplicated and overridden, so the default
   extension becomes the active budget; and
3. a named operation can be rejected by the raw-token/depth scan of a different, unselected
   operation, despite the resource-policy specification saying only the named operation is
   charged.

The build record also has contradictory gate-status prose, and none of the three new seams has a
regression test.

## Findings

### P1-1 — the armed budget aliases a publicly mutable policy object

[`begin_resource_budget`][resource-policy] stores the caller's `ResourcePolicy` instance directly
inside `_RequestBudget`. The same instance is deliberately exposed as
`DjangoSchema.resource_policy`, and `ResourcePolicy` is a non-slotted frozen dataclass. The
ordinary assignment guard therefore does not provide an authority boundary: Python code can edit
`schema.resource_policy.__dict__` (or use `object.__setattr__`) without replacing the object.

A two-field synchronous probe demonstrates the bypass:

```text
schema policy: ResourcePolicy(max_list_rows=1)
resolver for the first field: schema.resource_policy.__dict__["max_list_rows"] = 999
second field: DjangoListField(..., limit=2)
result: two rows, no LIST_ARGUMENT_INVALID / RESOURCE_LIMIT_EXCEEDED error
```

The second field reads `budget.policy` through [`policy_from_info`][resource-policy], so it sees
the edited value. This is not a theoretical post-request mutation: a normal resolver can mutate
the object in one sibling field and widen the row bound, page bound, or any other resolve-time
bound used by a later sibling in the same operation. The absolute deadline happens to be copied
to a scalar, but the collection and value policy fields remain live object attributes. This
contradicts spec-047's “immutable and armed for the whole operation” invariant and spec-050's
claim that the ceiling is the budget the operation started with.

The same acceptance path also admits a hostile `ResourcePolicy` subclass. The shared
[`resolve_policy`][utils-policies] helper and the extension's `_resolved_policy` use
`isinstance(...)`, and [`policy_from_info`][resource-policy] does the same. A subclass overriding
`__getattribute__` can return an `int` subclass for `max_list_rows`; a live `limit` request then
raises the subclass's raw comparison exception instead of a typed framework error. Thus the
exact-built-in rule protects values only while the object is read honestly; it does not protect
the object that supplies those values.

**Root-cause correction:** materialize a private operation snapshot at the arm point. The capsule
must contain exact built-in scalar values (or an exact base `ResourcePolicy` copy built through
contained reads), must be the sole source for `policy_from_info`, `check_deadline`, and all
resolve-time bounds, and must not be the public schema object. `on_execute` should use the same
snapshot rather than re-reading `schema.resource_policy`. Require an exact `ResourcePolicy`
instance or safely canonicalize subclasses at schema construction; merely adding `slots=True` or
more `try` blocks leaves the shared-object alias intact.

**Required proofs:** a live sibling-field query that edits `__dict__` and attempts to widen
`max_list_rows`/`max_page_size`; an async equivalent crossing an `await`; and package rows for a
benign and a hostile `ResourcePolicy` subclass. Each must show the operation-start ceiling and a
typed rejection, with no raw consumer exception.

### P1-2 — an extension factory can install two resource policies, with the default overriding the custom one

[`DjangoSchema.__init__`][schema] delegates resource-extension insertion to
`_with_resource_policy_extension`. That helper recognizes only a class or an already-created
instance through `_extension_entry_matches`; a zero-argument factory is intentionally opaque and
therefore causes the automatic `DjangoResourcePolicyExtension` class to be appended as well.

This is a valid Strawberry extension form, not an invalid input. The following probe resolves two
resource extensions:

```text
extensions=[lambda: DjangoResourcePolicyExtension(
    policy=ResourcePolicy(max_list_rows=1),
)]
schema.get_extensions() -> custom resource extension, automatic resource extension
```

The automatic class is entered inside the factory-produced extension. Its default policy becomes
the active `_active_budget`, so an ordered `DjangoListField` request with `offset=2` succeeds even
though the consumer's factory explicitly configured `max_list_rows=1`. The custom extension may
still charge its own document walk, which makes the result dependent on extension ordering rather
than on the policy the schema author supplied. The helper's docstring warns that factories are
“opaque”, but the public schema constructor does not reject or otherwise make this behavior safe;
the result is a silent policy downgrade.

**Root-cause correction:** apply the same runtime deduplication already used for the error-policy
factory. Resolve the extension list once per operation, detect any resolved
`DjangoResourcePolicyExtension`, and remove only the automatic instance while preserving the
consumer factory and ordering. Alternatively, explicitly reject a factory that produces this
extension with a typed configuration error; silently adding a second authority is not acceptable.

**Required proofs:** add a schema-level test for class, instance, and factory forms. For the
factory form, assert exactly one resource extension is active and that restrictive row/deadline
settings are enforced through a real list-field request. Add a control proving an unrelated
factory still receives the automatic extension.

### P2-1 — the named-operation contract does not hold for the pre-parse token/depth scan

[`DjangoResourcePolicyExtension.on_operation`][resource-extension] calls
`scan_document_text(policy, execution_context.query)` with the entire raw document. The scanner
has no operation-name argument and therefore counts every lexical token and every structural
delimiter in every operation before graphql-core selects the requested one. The later
[`charge_document`][resource-extension] walk does filter by `operation_name`, so the two halves
disagree.

A direct schema probe used `ResourcePolicy(max_document_tokens=10)`:

```graphql
query Small { a }
query Big { b c b c b c b c b c b c b c b c }
```

Executing with `operation_name="Small"` returns
`ResourceLimitExceeded(bound="max_document_tokens")` before `Small` runs. Removing `Big`, or
raising the token ceiling, allows the same named operation to execute. This is an avoidable
denial-of-service vector for clients that legitimately send a persisted document containing
several operations, and it contradicts spec-047's edge-case statement that only the named
operation is charged.

There is a real design distinction here: token/depth limits are intentionally pre-parse, so a
scanner cannot generally know the selected operation without first parsing the document it is
supposed to protect. If the intended contract is “the whole request document is bounded before
parse”, the spec must say that explicitly and exempt `max_document_tokens`/`max_depth` from the
named-operation rule. If the named-operation rule is intended to cover these bounds too, the
current pre-parse architecture cannot satisfy it and needs a different framing/segmentation
strategy.

**Required correction:** choose and document one meaning, then add a regression pair: selected
small operation plus oversized unselected operation, and the same document with the request-level
token/depth contract made explicit. The test must assert whether rejection is intentionally
request-wide or operation-specific rather than leaving the mismatch implicit.

### P3-1 — the build record's gate status is self-contradictory

The opening status sentence in the [build record][build-050] says “The gate is owed” and describes
the implementation as through the ninth review, while `## Final gate record` says the tenth-round
production changes were measured at `207c7328` with green default, sharded, floor, structural, and
citation results. The current `HEAD` is the docs-only descendant `9eb58a96`, so the code is still
the gated tree, but a maintainer cannot tell from the surviving status line whether the gate is
complete or pending.

**Required correction:** rewrite the opening status to state one unambiguous state (final gate
GREEN at the recorded tree, or gate owed) and identify the docs-only descendant if that matters.
Do not leave two mutually exclusive release-readiness claims in the only surviving build artifact.

## Test and documentation gaps

- No package or live test covers mutation of the exposed policy object's `__dict__` between two
  sibling fields, so the “frozen” claim has no authority-boundary proof.
- No schema test covers a resource-policy factory, even though the repository already tests custom
  error-policy factories; the duplicate-extension downgrade is therefore unpinned.
- No test states whether `max_document_tokens` and `max_depth` are request-wide or selected-
  operation bounds when `operationName` is supplied.
- The new tests should remain in the repository's live-first shape: use a real fakeshop HTTP field
  for row/deadline behavior and package tests only for construction and extension-list mechanics,
  following [the fakeshop test guide][live-readme].

## Checks run

- `ruff format --check`: 444 files already formatted.
- `ruff check`: all checks passed (the existing COM812 warning only).
- Spec glossary check: 43 terms, all resolved.
- Trailing-comma structural check: passed.
- Python compilation: passed.
- Citation check: 1010 citations resolved.
- Pytest was intentionally not run under [AGENTS.md][agents].

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
[list-field]: ../django_strawberry_framework/list_field.py
[resource-extension]: ../django_strawberry_framework/extensions/resource_policy.py
[resource-policy]: ../django_strawberry_framework/resource_policy.py
[schema]: ../django_strawberry_framework/schema.py
[utils-policies]: ../django_strawberry_framework/utils/policies.py

<!-- tests/ -->

<!-- examples/ -->
[live-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
