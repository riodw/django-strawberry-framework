# Adversarial review: execution-mode identity and refusal-input ownership

Date: 2026-09-17

Reviewed tree: HEAD `918a86e6` plus the current working-tree changes

Scope: [`spec-050`][spec-050], [`build-050`][build-050], the implementation and its permanent
tests, under the repository rules in [`AGENTS.md`][agents]

## Verdict

Not ready to mark DONE. The previous review's five findings are materially fixed: enforcement
authorities are no longer consumer extension entries, refused requests no longer parse or
select from caller input, diagnostic rendering contains hostile values, and streamed budget
bindings transfer their reset obligation to the resume scope. I found two new release-blocking
failures at boundaries those fixes now depend on, plus one permanent-test structure violation.

Neither blocker is an argument-window arithmetic defect. Both are ownership defects:

1. a refused operation has two readers of one potentially single-use transport iterable, and
2. a list resolver infers the GraphQL executor's mode from the ambient event loop even though
   those are independent facts.

I used focused `uv run python` probes only. Per [`AGENTS.md`][agents], I did not run pytest.
The recorded full/default/sharded/floor gates therefore remain owed on the final corrected
tree, exactly as [`build-050`][build-050] already says.

## Confirmed closures from the preceding review

- [`django_strawberry_framework/schema.py::DjangoSchema.get_extensions`][schema] now treats
  direct enforcement entries as declarations and constructs both enforcement authorities
  afresh per operation from `_SchemaEnforcement`. A factory resolving to either authority
  fails closed rather than replacing the package authority.
- [`django_strawberry_framework/schema.py::_refuse_operation_document`][schema] installs a
  package-owned, import-time-parsed document and clears Strawberry's provided operation name.
  Malformed documents and absent, invalid, empty, Unicode, and non-string operation names now
  reach the stable configuration refusal in the tuple/set cases covered by the tests.
- The refused chain retains the resource extension, so document token/depth bounds still
  outrank the configuration refusal.
- Factory diagnostics go through `describe_value`; the newly covered hostile `repr`, `str`,
  `args`, and type-name cases no longer escape while the refusal is being built.
- [`django_strawberry_framework/extensions/operation_state.py::OperationState.rebind_on_resume`][operation-state]
  transfers the arming token to the active resume registrar. The budget remains armed for the
  operation without remaining bound in the driving task between frames.

These closures should stay. The findings below require extending their abstractions, not
rolling them back or adding exception-specific patches.

## P1-1 - the refusal path consumes `allowed_operation_types` before Strawberry does

### Evidence

Strawberry's three public entry points accept
`allowed_operation_types: Iterable[OperationType]`. The execution context retains that object,
and upstream performs one membership test after parsing. The new refusal helper performs its
own membership search first:

```python
allowed = getattr(execution_context, "allowed_operations", ()) or ()
next(document for operation_type, document in _REFUSAL_DOCUMENTS.items()
     if operation_type in allowed)
```

That is correct only for reusable containers. A one-shot iterable is exhausted while the
package chooses its substitute document. Strawberry then tests the selected operation against
the already-consumed iterable and concludes that the operation type is forbidden.

On the reviewed tree, a refused schema and a generator yielding exactly `OperationType.QUERY`
produced:

```text
execute_sync + tuple       -> SCHEMA_CONFIGURATION_UNAVAILABLE
execute_sync + generator   -> raised InvalidOperationTypeError(OperationType.QUERY)
await execute + tuple      -> SCHEMA_CONFIGURATION_UNAVAILABLE
await execute + generator  -> raised InvalidOperationTypeError(OperationType.QUERY)
stream + generator         -> one "queries are not allowed" frame, extensions={}
```

This is not an invalid input that upstream already rejects. The same generator is a valid
value for the annotated public API and a healthy Strawberry operation consumes it only once.
The package introduced the second consumer.

There is a second expression of the same ownership error. `allowed = value or ()` invokes
consumer-defined truthiness. A `list` subclass containing `OperationType.QUERY` whose only
override is a raising `__bool__` succeeds on a healthy `DjangoSchema`; on a refused schema the
same value executes that unrelated dunder and replaces the stable configuration refusal with
a generic masked error. This also contradicts the explicit no-truthiness posture immediately
below in
[`django_strawberry_framework/schema.py::_consumer_extension_entries`][schema].

### Root-cause fix

Make the refusal boundary the single owner of a canonical allowed-operation snapshot:

1. Read `execution_context.allowed_operations` once.
2. Materialize it once into an exact built-in tuple without a truthiness check.
3. Assign that tuple back to `execution_context.allowed_operations` before yielding to
   Strawberry.
4. Select the substitute document from that same tuple.

That makes package selection and upstream authorization read one immutable fact. It also
preserves nested and streamed behavior because the snapshot belongs to the execution context,
not module state or a task-global cache.

Do not solve this by appending `QUERY`, replacing an empty iterable with the defaults, or
catching `InvalidOperationTypeError`. A genuinely empty/forbidden transport policy must remain
forbidden. The fix is canonical ownership of what the caller supplied, not widening it or
masking the downstream symptom.

### Required regression proof

Add direct schema-API rows in [`tests/test_schema.py`][test-schema]:

- a one-shot iterable yielding query survives `execute_sync`, `execute`, and `stream` and all
  three retain `SCHEMA_CONFIGURATION_UNAVAILABLE`;
- mutation and subscription substitute selection work from one-shot iterables, so the fix is
  not accidentally query-only;
- a counting iterable is traversed once and the stored execution-context value is the exact
  built-in tuple afterward;
- a reusable sequence with hostile `__bool__` is never truth-tested;
- an actually empty iterable still follows Strawberry's operation-type refusal contract and
  is not silently widened.

This is a package/direct-API boundary; the Django views provide stable built-in operation-type
sets, so a synthetic HTTP row would not add reachability evidence.

## P1-2 - `DjangoListField` confuses an active event loop with async GraphQL execution

### Evidence

[`django_strawberry_framework/list_field.py::DjangoListField`][list-field] chooses the default
resolver pipeline with `in_async_context()`. Its synchronous consumer-resolver branch repeats
the same decision when choosing the final queryset representation. The code comment claims
this lets one field work under both `schema.execute_sync` and `await schema.execute`.

Those APIs and ambient loop state are not the same axis. `execute_sync` is callable while an
event loop is running, including from a nested operation inside an async resolver. In that
case `in_async_context()` is true, so a default list field returns the async pipeline's
coroutine to Strawberry's synchronous executor. Strawberry cancels the top-level awaitable and
returns its generic synchronous-completion error; inner coroutines are left unawaited.

I reproduced this first against fakeshop's shipped schema and then against a minimal schema
with no optimizer extension. In the isolated case:

```text
schema.execute_sync("{ __typename }") inside asyncio.run
    -> {"__typename": "Query"}, no errors

schema.execute_sync("{ rows { name } }") inside the same loop
    -> data=None
    -> "GraphQL execution failed to complete synchronously."
```

The fakeshop reproduction additionally emitted unawaited-coroutine warnings from GraphQL
field completion, the optimizer and `_execute_queryset_pipeline_async`. The control query
proves the failure is introduced by list-field dispatch rather than by `execute_sync` merely
being invoked under a loop. Removing the optimizer proves the optimizer is not its root.

This is inside spec-050's scope. The card introduced the async-only queryset adapter and
promises that async queryset completion is selected correctly while no-argument synchronous
behavior remains unchanged. The present predicate cannot state either promise when executor
mode and loop presence disagree. It is also reachable over real HTTP: an async GraphQL
operation can run a resolver that starts a nested `info.schema.execute_sync(...)`, a nesting
shape the new operation-state architecture explicitly supports.

### Root-cause fix

Represent GraphQL execution mode as operation state. Do not add another list-field-local
`ContextVar`, and do not infer the mode from whether Python happens to have a running loop.

The existing runner boundary is the DRY owner:

1. [`django_strawberry_framework/schema.py::DjangoSchema.get_extensions`][schema] receives the
   authoritative `sync` flag for every operation. Carry that fact into a fresh package-owned
   per-operation marker in the admitted and refused chains.
2. [`django_strawberry_framework/schema.py::DjangoSchema.create_extensions_runner`][schema]
   turns it into a runner-owned operation-mode lease, alongside the runner scope already owned
   by [`DjangoExtensionsRunner`][operation-state].
3. Bind/reset it for the operation, result collection, every streamed frame, and every stream
   resume. Nested operations must token-reset to the outer mode; copied contexts must read
   nothing after the owning lease closes.
4. Expose one package-private query such as `current_operation_mode()` and use it wherever the
   question is *which GraphQL executor is driving this resolver*.
5. In `DjangoListField`, select the async pipeline only for an async operation. For a sync
   operation under a running event loop, raise a typed `SyncMisuseError` before constructing a
   coroutine or async-only adapter, with recourse to `await schema.execute(...)` or move the
   synchronous call to a worker thread. Silently blocking the event-loop thread is not an
   acceptable fallback.

Execution mode and ambient-loop safety remain two facts. Some current
`in_async_context()` calls genuinely guard Django ORM access; others are executor dispatch.
Classify the complete census in `auth/mutations.py`, `mutations/fields.py`, `relay.py`,
`types/relay.py`, `types/resolvers.py`, `connection.py`, `list_field.py`, and `schema.py`, then
migrate only the operation-mode readers to the canonical helper. Otherwise fixing the list
field alone leaves sibling field factories with the same false predicate and two definitions
of execution color.

A plain `strawberry.Schema` does not use the package runner. State its fallback contract
explicitly: either retain ambient dispatch there as a documented limitation or require
`DjangoSchema` for authoritative mode. Do not imply that the runner-owned guarantee extends to
a schema that never creates that runner.

### Required regression proof

- Package/direct rows prove all three states separately: `execute_sync` outside a loop,
  `await execute` inside a loop, and `execute_sync` inside a loop. The third must produce the
  chosen typed contract with warnings promoted to errors, not Strawberry's generic completion
  failure and not an orphaned coroutine.
- Repeat the disagreement case for the default resolver and a synchronous consumer resolver
  returning a queryset; they currently reach the wrong representation through different call
  sites.
- Operation-state rows prove nested mode restoration, exception/cancellation teardown, a
  copied context after lease closure, and streamed resume in another task.
- Because the nested disagreement is reachable through the async Django view, add a real
  `/graphql-async/` acceptance row under
  [`examples/fakeshop/test_query/`][test-query-readme]: an outer async operation invokes a
  nested synchronous operation selecting a `DjangoListField`, and the response asserts the
  selected public contract. A package-only test is insufficient for that reachability claim.
- Keep the existing optimizer-on/off async HTTP rows. They prove safe completion during a
  genuinely async operation and are not substitutes for the disagreement row.

## P2-1 - the security architecture added after the dated revision is not specified

The top of [`spec-050`][spec-050] still identifies its latest revision as 2026-09-13 and
summarizes cleanup precedence, proof determinism, offset ordering, async cleanup, and metadata
integrity. The later operation-state, authority-ownership, refused-document, diagnostic, and
resume-binding work is largely absent from the numbered decisions and rationale. One dense
Definition-of-done clause covers enforcement authority; ledger closure covers only part of
the lifetime work. [`build-050`][build-050] has a better summary, but explicitly says the
remediation reasoning is not restated there and points readers to code docstrings.

That leaves the most security-sensitive architecture in the card without a complete design
record. It is already causing review drift: the allowed-operation double-read above is a new
invariant of the refused-document design, yet the spec never states who owns the iterable or
that upstream must read the same canonical value.

Before closing the card, add a compact post-implementation decision section to the spec (with
derivation in its rationale) that records:

- configuration authority versus operation state;
- admission of classes, instances, fresh factories, and singleton factories;
- runner/lease lifetime across operation, result collection and stream resumes;
- refused-request document, selector, and allowed-operation snapshot ownership;
- the exact stable refusal guarantees and the transport-policy exception for a genuinely
  forbidden operation type;
- canonical execution-mode ownership and the raw-`strawberry.Schema` boundary after P1-2.

Then update the Revision summary and add explicit Definition-of-done rows for both P1 fixes.
The build record should cite those spec decisions rather than making code docstrings the only
place the design can be reconstructed.

## P3-1 - a new permanent test bundles three independent attacks in one node

[`tests/extensions/test_operation_state.py::test_a_resolver_cannot_replace_the_binding_carrier_or_rerun_the_constructor`][test-operation-state]
loops over three independent attacks: descriptor assignment, direct `__dict__` injection, and
constructor rerun. This is exactly the matrix shape forbidden by
[`examples/fakeshop/test_query/README.md`][test-query-readme]: no loop in a test body, every
case gets its own node id with `ids=`. A failure currently reports only the aggregate test and
can prevent later attacks from running.

Move the attack descriptions to a module-level parameter table and execute one attack per
test node, with explicit ids. Build a fresh shared extension and schema per parameter so no
attempt can affect another. The stream frame loops are sequential lifecycle assertions and do
not need mechanical splitting; this finding is limited to the independent tamper matrix.

## Release conditions after these fixes

1. Fix P1-1 at the refusal input-ownership boundary and add the direct three-API proof.
2. Fix P1-2 with one runner-owned execution-mode abstraction, audit its semantic call sites,
   and add both package lifecycle proof and the live async nested-operation row.
3. Bring the spec/rationale/build traceability up to the architecture that now ships.
4. Split the independent tamper matrix into separately identified nodes.
5. Run formatting, lint, structural/link/citation checks, then full default, sharded, and the
   complete declared-floor scope on one final identified tree at 100% package coverage.

Until step 5 is recorded, the checked historical gate in [`build-050`][build-050] remains
evidence for `207c7328`, not for this descendant working tree.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md

<!-- docs/ -->
[spec-050]: spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-050]: builder/DONE/build-050-list_field_arguments-0_0_15.md

<!-- django_strawberry_framework/ -->
[list-field]: ../django_strawberry_framework/list_field.py
[operation-state]: ../django_strawberry_framework/extensions/operation_state.py
[schema]: ../django_strawberry_framework/schema.py

<!-- tests/ -->
[test-operation-state]: ../tests/extensions/test_operation_state.py
[test-schema]: ../tests/test_schema.py

<!-- examples/ -->
[test-query-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
