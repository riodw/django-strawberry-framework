# Adversarial review — copied context and resolved-chain authority

Date: 2026-09-16

**Verdict: not release-ready.** The four findings from the preceding review are
substantially fixed: non-weak-referenceable entries are now answered through an
interpreter-owned immutable binding; the unowned assignment queue is gone; the
extension's execution-context carrier no longer strongly owns its operation
state; and nested execution from ordinary teardown/result collection no longer
overwrites the outer optimizer publication.

The new pass found two release blockers beyond those repairs:

1. The weak operation-state carrier is only one of several operation-lifetime
   `ContextVar` values. A child task copies the runner nesting marker, the armed
   resource budget, and the optimizer's mutable stores. Parent token reset does
   not alter that copy. The child therefore retains and reads a completed
   request's state, and a later independent operation in that child is
   misclassified as nested.
2. `DjangoSchema` authenticates the accepted extension *entries* but does not
   validate the resolved chain as one enforcement authority. Two opaque resource
   factories leave two resource extensions active; the last hook to arm wins.
   An invalid factory result escapes as a raw `AttributeError` before the runner
   or masking policy exists.

There are two additional lifecycle defects: a streamed result cannot be closed
from a different task because the runner carries raw `ContextVar` tokens across
`yield`, and a resolver can still retain an arbitrary graph by assigning a
non-`DjangoSchema`-shaped value to a shared extension's compatibility setter.

This review follows [AGENTS.md][agents], including its root-cause and live-test
placement rules. I inspected the complete [spec][spec-050], [build record][build-050],
current implementation, [upstream Strawberry lifecycle][upstream-schema], and the affected tests. I
used focused `uv run python` probes against the working tree. I did not run pytest
or coverage.

## What the latest implementation fixed

The previous findings should not be reopened in their old form:

- [`PrivateMembership`][private-state] now boxes a non-weak-referenceable member
  in a `types.MethodType`. Its `__self__` descriptor resists assignment,
  `object.__setattr__`, deletion, a shadow `__dict__` value, and reinitialization.
  Recall authenticates the box by weak identity and reads the member from that
  same immutable binding.
- The `_Assignment` / `_PENDING_ASSIGNMENTS` protocol has been deleted. A
  `DjangoSchema` engine assignment retains no context before runner creation.
- The per-extension carrier contains a weak reference to `OperationState`, so a
  child task released after the whole request completes no longer keeps the
  `ExecutionContext` alive through that carrier.
- A runner scope now covers result collection, and the optimizer uses the
  runner's nesting answer. Nested execute from `on_operation` teardown preserves
  the outer published plan in the ordinary same-task path.

Those changes are the correct direction. The findings below concern state that
still bypasses that ownership model.

## P1-1 — copied task contexts still carry completed enforcement and optimizer state

### Evidence

[`DjangoExtensionsRunner`][operation-state] weakens only the value stored in each
extension-specific carrier. The other operation-lifetime variables remain strong
values copied verbatim into a child task:

- `_RUNNER_SCOPES` stores `_RunnerScope` directly. It has no weak owner and no
  terminal/closed state.
- [`_active_budget`][resource-policy] stores `_RequestBudget` directly, including the policy,
  deadline, and admission verdict.
- [`_operation_stashes`][optimizer-context] stores `_OperationStore`, which strongly owns the
  optimizer state's `stashes` dictionary.
- `_cache_key_parts_cache`, `_execution_plan_cache`,
  `converted_selections_cache`, `_scoped_relations`, and `_active_strictness`
  likewise store per-execution values directly. The execution-plan memo is
  explicitly allowed to hold request-scoped querysets.

`ContextVar.reset(token)` changes only the context in which the token was
created. It cannot rewrite a context copied into `asyncio.create_task()` before
that reset. Three direct probes reproduce the consequences.

First, a resolver spawned a child, the outer request completed, and the child
then started a new operation on the same schema. The extension state itself was
gone, but the runner marker was not:

```text
outer operation nesting answers     [False]
independent child operation          True
child after its operation            False
```

The final `False` only says the child restored its predecessor. The predecessor
is the stale outer marker, so the next operation in that child will again be
classified as nested. The existing regression named
`test_a_surviving_task_that_starts_its_own_operation_ends_with_nothing_bound`
asserts only `shared.execution_context is None`; it never asks
`operation_is_nested()` and therefore passes over this defect.

Second, an optimizer operation stashed a unique object, spawned a child, and
finished. The parent read no active optimizer value; the child still read the
exact old object before and after running another operation:

```text
parent optimizer value after execute  None
child reads completed operation       True
child after independent execute        True
```

The child also kept a weak-referenceable sentinel alive solely through the
copied optimizer store. Thus the operation-state carrier no longer owns the
request, but the optimizer store can still own request-scoped plans, converted
selections, cache-key values, and querysets for the lifetime of a background
task.

Third, the same shape reaches spec-050's bound directly. The outer schema armed
`max_list_rows=1`; after it completed, the child called `policy_from_info` with a
new context publishing `max_list_rows=7`:

```text
parent armed policy after execute     None
child armed policy                     1
child policy_from_info(new context)    1
```

The child is outside the request that armed `1`, yet the stale private budget
outranks the context actually passed to the helper. Any later direct
`bounded_rows` / `DjangoListField` work in that child therefore answers from the
completed request, contrary to the [spec's definition of done][spec-050-dod] and
the module's own fallback contract.

There is a narrower gap in the newly weak carrier too. A child copy holds a weak
reference, but the runner owns the state through result collection. If that child
runs while async result collection is awaiting, the weak reference still
resolves even though the operation binding in the parent has already unwound.
Weak lifetime is necessary for collection, but it is not proof that this copied
binding is still active.

### Root fix

Token reset cannot be the revocation mechanism. Introduce one package-owned,
revocable operation lease abstraction and make every copied context hold the
lease, not a raw state/store/budget.

The required properties are:

1. A lease has an explicit terminal state. `close()` atomically marks it closed
   and drops every request-owned payload. Every read first verifies the lease is
   open. A child context copied earlier holds the same lease object and therefore
   observes closure immediately. The terminal `_NormalizationLedger.close()` in
   [`orders/sets.py`][orders-sets] is already the repository's correct precedent.
2. The per-extension carrier stores a lease containing a weak reference to the
   runner-owned state, rather than storing that weak reference directly. Closing
   the binding lease makes an old child copy inert even while the runner still
   owns the state for result collection.
3. The runner-scope value is likewise a lease. `operation_is_nested()` treats a
   missing **or closed** lease as no outer operation. Nesting must be determined
   from the active live lease when the runner binding begins, not merely from
   `_RUNNER_SCOPES.get() is not None` when the runner object is constructed.
4. The resource budget is closed before its token is reset. `armed_resource_policy`,
   `admission_rejection`, `policy_from_info`, and `check_deadline` treat a closed
   budget exactly as absent. Closing drops the policy/deadline/verdict references.
5. Consolidate optimizer execution scratch behind one revocable frame instead of
   seven independently reset variables. The frame owns stashes, plan memos,
   converted selections, scoped relations, and strictness; its `close()` clears
   all mutable stores before token reset. Optimizer accessors treat a stale copied
   frame as inactive and fall back exactly as they do when no optimizer operation
   is running.
6. Token reset remains useful for normal nesting, but it restores only live
   predecessors. It is cleanup, not authority. No accessor may infer activity
   from a non-`None` copied `ContextVar` value alone.

Do not fix only `_RUNNER_SCOPES`: that would make the child's later operation
look top-level while leaving its direct resource and optimizer reads stale. Do
not merely weak-reference optimizer dictionaries: the runner may intentionally
stay alive through result collection, and a closed binding must stop answering
before owner collection.

### Required regressions

- Extend [`tests/extensions/test_operation_state.py`][test-operation-state] so a
  surviving child asserts `operation_is_nested() is False` before its own
  operation, records `False` inside it, and remains `False` afterwards.
- While async result collection is deliberately paused, release a resolver child
  and prove the child's copied operation lease is already closed even though the
  runner still owns states for `get_results`.
- In [`tests/test_resource_policy.py`][test-resource-policy], prove a child reads
  no armed policy after owner teardown and that `policy_from_info` honors the new
  context passed to it. Cover an admission verdict and a deadline as well as
  `max_list_rows`.
- In [`tests/optimizer/test_extension.py`][test-optimizer], put unique weakrefable
  sentinels in the stash, execution-plan memo, converted-selection cache, and
  cache-key memo. After teardown, a surviving child must read no stale value and
  every sentinel must be collectible.
- Start a complete second resource/optimizer operation in that child. It must
  publish as a top-level operation, clear its own reused context, and restore to
  no operation afterwards.
- Put the consumer-visible `max_list_rows` and optimizer-publication cases through
  the async live fakeshop surface, following the [live-test rules][live-readme].
  Package tests own only lease mechanics and collectability.

## P1-2 — the resolved extension chain is neither type-checked nor single-authority

### Evidence

[`DjangoSchema.extensions`][schema] now authenticates the exact entries accepted
at construction. That does not authenticate what a callable entry returns on an
operation. `super().get_extensions()` calls every opaque factory and returns the
results; current code then removes at most one automatic policy by position and
passes the rest to Strawberry without validating the resolved population.

Two accepted resource factories demonstrate the authority split. One returns a
policy with `max_aliases=1`, the other `max_aliases=999`. Both resolved resource
extensions survive after the automatic entry is dropped:

```text
entry order     resolved resource extensions   two-alias request
narrow, wide                 2                  accepted, no errors
wide, narrow                 2                  RESOURCE_LIMIT_EXCEEDED (limit 1)
```

This is not the intersection of two declared bounds. Each `on_operation` opens
an `_active_budget` scope, so the last resource hook to arm is the budget every
`on_parse` hook and every resolve-time field seam reads. Reordering unrelated
extension configuration therefore selects which policy controls spec-050's
`limit`, `offset`, and returned-row ceilings. It directly contradicts the
[spec requirement][spec-050-dod] that a consumer factory leave exactly one armed
budget.

The malformed-member case fails earlier and more abruptly. These are accepted at
schema construction because they are callable:

```python
extensions=[lambda: 7]
extensions=[lambda: object()]
```

Both later escape `execute_sync` as a raw `AttributeError` when Strawberry tries
to assign `execution_context`. That assignment loop runs before runner creation
and outside Strawberry's operation error handling, so the automatic error policy
cannot mask it and `_RefusedConfiguration` never runs.

A factory that raises is earlier still: `RuntimeError("factory sentinel")`
escapes directly from `get_extensions`, before there is even a resolved member
to validate. Factory invocation, result typing, and enforcement cardinality are
therefore one admission transaction; handling only the latter two leaves the
same pre-runner disclosure path open.

The constructor message says a factory must return a `SchemaExtension`, but
`_is_resolvable_extension_entry` proves only that the entry is callable. The
missing half is necessarily a resolve-time check; construction cannot safely call
a per-operation factory.

### Root fix

Make `DjangoSchema.get_extensions` an atomic resolved-chain admission boundary:

1. Resolve accepted entries once through upstream inside a containment boundary.
   If factory invocation raises, convert that into the same fail-closed
   configuration refusal. Do not call a factory a second time to inspect it.
2. Before returning any member to Strawberry's assignment loop, require every
   resolved member to be an actual `SchemaExtension` instance using the existing
   exact-type/subclass discipline. A class returned by a factory is not an
   instance and is invalid too.
3. Identify and remove the package-added automatic resource/error entries, then
   require **exactly one** resolved `DjangoResourcePolicyExtension` and exactly
   one resolved `DjangoErrorPolicyExtension`. Multiple consumer entries are an
   ambiguous configuration, not a request-time ordering rule and not policies to
   compose implicitly.
4. Reject known direct duplicates at schema construction for earlier feedback,
   but keep the resolve-time cardinality gate because opaque factories cannot be
   classified before they run.
5. A resolve-time refusal cannot be raised out of `get_extensions`: upstream calls
   it before the protected operation block. Generalize the existing fail-closed
   refusal chain so an invalid member or ambiguous policy population returns only
   the package masking extension plus a configuration-refusal extension. No
   consumer hook and no resolver runs. The response should carry the stable
   schema-configuration code without exposing the bad object's representation or
   exception text.
6. Keep the reason server-side for diagnostics. The wire contract needs one safe
   configuration error, not a serialization of arbitrary factory output.

Do not choose “first wins” or “last wins.” That leaves extension order as an
undocumented policy-widening surface. Do not catch the later assignment error:
by then an invalid member is already inside a chain the package claimed it had
accepted.

### Required regressions

- Direct duplicate resource classes/instances and two opaque factories are all
  rejected. Parametrize both orders with independent IDs; neither request may
  execute.
- Add the equivalent duplicate error-policy rows so masking authority also has
  one owner.
- Factories raising an exception, or returning an integer, plain object,
  extension class, and a value whose `__class__` lies, all produce the stable
  configuration refusal rather than a raw exception.
- A valid slotted factory, bound method, fresh factory, and singleton factory
  remain accepted controls.
- Put the resource cardinality and safe wire refusal in
  [`test_resource_policy_api.py`][live-resource-policy] or the dedicated
  [live isolation module][live-isolation]. The exact resolved-member census stays
  in [`tests/test_schema.py`][test-schema].

## P2-1 — a stream cannot migrate or close across tasks

### Evidence

`_BoundScope.__aenter__` stores raw `ContextVar` tokens and keeps them until the
upstream async operation context exits. Strawberry's `_stream` holds that context
across every yielded frame. Python async iterators may be advanced or closed by a
different task after a yield; the token then belongs to the first task's context
and cannot be reset from the second.

A direct query-stream probe fetched the first frame in a child task and called
`aclose()` from its parent:

```text
first frame   {'hello': 'hi'}, no errors
aclose        ValueError: Token ... was created in a different Context
```

The failure is not limited to runner scope. `DjangoResourcePolicyExtension` and
the optimizer also hold tokens across the operation/execution generator hooks.
Moreover, a second `anext()` in another task resumes extension and resolver code
without the bindings created in the first task, so catching the final reset error
would not make migration correct.

The package's ordinary HTTP/WebSocket drivers currently tend to drive and cancel
one stream in one task, which keeps this below the two blockers above. The public
`DjangoSchema.stream` / `subscribe` result is still an async iterator, and the
package must either preserve upstream's task-portable iterator behavior or state
and safely enforce a task-affinity contract. A raw `ValueError` during cleanup is
neither.

### Root fix

After the revocable lease work in P1-1, make runner binding resume-scoped for
streams:

- Wrap the iterator at the narrow `_stream` seam that already receives the exact
  `DjangoExtensionsRunner`. Each `__anext__`, `athrow`, and `aclose` binds a fresh
  lease in the *calling task* before delegating and closes/resets it before
  returning.
- The long-lived upstream `operation()` manager must detect that the resume scope
  owns the binding and must not leave a raw token spanning a `yield`.
- Resource and optimizer operation data must live in the revocable runner/frame
  state from P1-1, not in independent tokens created on the first resume. Package
  extension teardowns then see the correct state in whichever task performs the
  close.
- Preserve upstream hook order and one `on_operation` enter/exit per stream. The
  wrapper changes where task-local access is bound, not how often hooks run.

If task migration is intentionally unsupported, enforce that decision at the
iterator boundary with a package error **and still make cross-task cancellation
and close release every resource without a token error**. Merely documenting
“same task” does not make disconnect cleanup safe.

Required tests: first-frame/second-frame migration, cross-task `aclose`, closing
while a source is paused, cancellation from another task, and every error path.
Assert resource budget, runner state, optimizer stores, and debug cursor flags are
all terminal afterwards. The direct iterator mechanics belong in package tests;
add a live WebSocket/streaming row only if an actual transport path migrates or
closes the iterator from another task.

## P2-2 — the compatibility setter still accepts resolver-authored state

### Evidence

The pending handoff was correctly removed for a value whose `.schema` is a
`DjangoSchema`. The setter still treats every other value as a raw-Strawberry
compatibility assignment and writes a strong `_compatibility_state` on the shared
extension.

A resolver assigned a new plain object to a singleton extension during a normal
`DjangoSchema` operation. The bound runner state protected the active request,
but after it ended:

```text
request errors                         None
shared.execution_context outside op    forged object
forged object collectible              False
```

Thus a resolver may retain an arbitrary graph for the process lifetime and make
direct readers outside an operation answer with it. The current tamper rows cover
`None` and a forged context naming the real schema; those are precisely the two
values that do *not* take this compatibility branch.

### Root fix

Record, in private identity authority, that an extension has been admitted to a
`DjangoSchema` the first time the engine assigns that schema's context (or when
the package runner resolves it). Once marked package-managed, its setter ignores
**every** later assignment; the runner argument is its only operation-state
authority. This includes `None`, arbitrary objects, raw-schema-shaped forgeries,
and assignments made by surviving child tasks.

Keep instance-local compatibility state only for an extension that has never
been managed by `DjangoSchema`. The documented raw-`strawberry.Schema` spellings
are a class or a factory that creates a fresh instance, so marking a shared object
package-managed does not remove a supported raw-schema path; sharing that same
instance with a raw schema was already outside the guarantee.

Add arbitrary object, raising `.schema` property, raw-schema context, and
post-request child-task assignments. Each sentinel must be collectible and the
extension must answer `None` outside the package runner.

## Test, specification, and build-record corrections

1. The [spec][spec-050] is right to keep its status “in flight” and its definition
   of done unchecked. Its “exactly one armed budget” requirement currently fails
   for two consumer factories, and its operation-started policy guarantee fails
   in a copied child context.
2. The [build record][build-050] cannot be treated as a delivery gate. Its recorded
   green tree is `207c7328`; current `HEAD` is a later isolation implementation
   and the relevant source/test changes are still uncommitted. The record already
   says later policy work was ungated, but it does not yet name the runner,
   membership, copied-context, or resolved-chain changes now under review. Once
   the findings are fixed, replace the status/gate narrative with one same-tree
   full, sharded, and declared-floor run. Do not append another superseded green
   count beside it.
3. [`Per-operation extension isolation`][glossary-isolation] currently promises
   that a copied child binding reads nothing after the operation. Narrowly true
   for `execution_context` after runner collection, it is false for runner scope,
   resource budget, and optimizer stores. Update it only after the common lease
   exists.
4. Resource-policy and optimizer module docs say token reset prevents leakage to
   the next operation. State explicitly that closure/tombstoning, not reset, is
   what invalidates copied contexts; reset restores nesting in the owner context.
5. Keep live tests focused on wire behavior and one case per parametrized node ID.
   Do not move task/GC mechanics into the live suite, and do not leave a
   consumer-visible bound, masking, or optimizer-publication claim package-only.

## Release conditions

Do not mark spec-050 done until all of these hold on one gated tree:

- Every operation-lifetime value copied into a child task becomes terminal when
  its owner scope ends. A later independent operation is top-level, publishes its
  own optimizer state, and reads its own resource policy.
- Closing a stream from another task cannot produce a raw token error, retain an
  operation, or leave a debug/resource/optimizer scope active.
- The resolved extension chain contains actual `SchemaExtension` instances and
  exactly one resource and one error authority before Strawberry's assignment
  loop sees it. Invalid or ambiguous factory output fails closed on the wire.
- A package-managed extension cannot acquire compatibility state from resolver or
  background-task assignments of any shape.
- The required package mechanics and live outcomes are covered in the test tiers
  mandated by [AGENTS.md][agents], with no loop-bundled live cases.
- Standing docs describe leases and resolved-chain admission rather than claiming
  that token reset alone invalidates copied contexts.
- After implementation edits, run the mandated formatter and lint fixer. Run
  pytest/coverage only when explicitly authorized, and record full/default,
  sharded, and floor evidence against the same final tree.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md

<!-- docs/ -->
[glossary-isolation]: GLOSSARY.md#per-operation-extension-isolation
[spec-050]: spec-050-list_field_arguments-0_0_15.md
[spec-050-dod]: spec-050-list_field_arguments-0_0_15.md#definition-of-done

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-050]: builder/DONE/build-050-list_field_arguments-0_0_15.md

<!-- django_strawberry_framework/ -->
[operation-state]: ../django_strawberry_framework/extensions/operation_state.py
[optimizer-context]: ../django_strawberry_framework/optimizer/_context.py
[orders-sets]: ../django_strawberry_framework/orders/sets.py
[private-state]: ../django_strawberry_framework/utils/private_state.py
[resource-policy]: ../django_strawberry_framework/resource_policy.py
[schema]: ../django_strawberry_framework/schema.py

<!-- tests/ -->
[test-operation-state]: ../tests/extensions/test_operation_state.py
[test-optimizer]: ../tests/optimizer/test_extension.py
[test-resource-policy]: ../tests/test_resource_policy.py
[test-schema]: ../tests/test_schema.py

<!-- examples/ -->
[live-isolation]: ../examples/fakeshop/test_query/test_extension_isolation_api.py
[live-readme]: ../examples/fakeshop/test_query/README.md
[live-resource-policy]: ../examples/fakeshop/test_query/test_resource_policy_api.py

<!-- scripts/ -->

<!-- .venv/ -->
[upstream-schema]: ../.venv/lib/python3.14/site-packages/strawberry/schema/schema.py

<!-- External -->
