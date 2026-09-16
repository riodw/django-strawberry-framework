# Enforcement extension isolation — root-cause remediation

Date: 2026-09-16

**Verdict: do not release the current tree.** The default `DjangoSchema` path is
not the failing path: its automatic policy classes are constructed per operation.
The release blocker is the documented, accepted path where a framework extension
is an instance or a factory returns the same instance. In that path, Strawberry
shares the object while the package still treats several fields on it as
operation-local or security-relevant.

The correct repair is a single operation-state boundary owned by
`DjangoSchema`, not another collection of `ContextVar` setters on individual
extensions. It must bind framework-owned extension state for the entire runner
lifecycle, restore nested bindings with tokens, and give result collection the
same operation state after normal operation teardown. Separately, extension
membership must accept valid non-weak-referenceable factories without creating a
module-global strong path back to a schema.

This review follows the repository rules in [AGENTS.md][agents]. No production
code was changed and no pytest or coverage run was performed.

## Evidence and scope

Strawberry resolves a direct extension instance unchanged and calls a factory on
each `get_extensions` call. It then assigns `extension.execution_context` on
every resolved member *before* it creates the extension runner. The runner
brackets `on_operation`, parsing, validation, execution, streaming-result hooks,
and result collection on that same member. It neither restores a replaced
attribute nor creates a wrapper for a pass-through instance.

That makes these accepted spellings materially different:

| Entry spelling | Resolved object per operation | Current result |
| --- | --- | --- |
| Automatic policy / package class entry | Fresh instance | Isolated control |
| `lambda: DjangoResourcePolicyExtension(...)` | Fresh instance | Isolated control |
| `DjangoResourcePolicyExtension(...)` | Same instance | Admission and result-state leak |
| `lambda: shared_extension` | Same instance | Same leak; no upstream instance warning |
| `lambda: _optimizer` | Same optimizer cache instance | Context and nested-stash leak |

The automatic deduplication in `DjangoSchema.get_extensions` amplifies the
singleton-factory case. An opaque factory causes the automatic class entry to be
added at construction; at runtime the shared returned policy object wins the
deduplication and removes the fresh automatic instance.

The prior live probes established all of the following for both
`DjangoGraphQLView` and `AsyncDjangoGraphQLView`:

- A shared resource extension with `max_aliases=1` lets the oversized
  `{ a: hello b: hello }` query execute during an overlapping benign query,
  although the same query is rejected before and after the overlap.
- A shared error-policy extension under `DEBUG=False` leaves an unexpected
  resolver exception unmasked during overlap. The fresh-factory and class
  controls preserve the stable message and correlation ID.
- A resolver that performs nested `info.schema.execute_sync("{ hello }")` and
  then raises reproduces the error disclosure without a scheduling race.
- A shared `DjangoDebugExtension` can republish the previous operation's debug
  payload on a later parse failure. Its plain `_payload` and `_snapshots`
  attributes have the same ownership failure as `execution_context`.
- The fakeshop optimizer's documented singleton factory leaves
  `optimizer.execution_context` referring to an inner `execute_sync` document
  after that inner call returns. Its setter calls `ContextVar.set()` but keeps no
  reset token.

The fresh direct probe in this pass found one more consequence. With
`DEBUG=False`, a direct shared `DjangoDebugExtension()` initially withheld its
payload. A resolver set its public `allow_unsafe_production` attribute to
`True`; the next `execute_sync("{ hello }")` response contained
`{"debug": {"sql": [], "exceptions": []}}`. Thus the acknowledgement that
authorizes SQL, exception messages, and tracebacks is mutable by a resolver for
later requests. The current exact-bool constructor check does not protect the
stored decision.

The resource budget itself is already task-local and its accepted policy is
protected off-object. That is why the benign operation is not charged by A. The
defect is that A's later `on_parse` reads B's document through the shared
extension attribute and therefore records no rejection for A. An admission guard
cannot restate a rejection that was never recorded.

The WebSocket per-event masking result remains correctly routed through
`consumers.py::_stop_aware_results` and `schema.error_policy`; it is not evidence
that the shared HTTP extension attribute is safe. The subscription oversize probe
also remains a pre-execution frame on the installed Strawberry release, not a
confirmed execution bypass.

## P1 — establish one package-owned operation-state boundary

### The boundary and its owner

Add one internal operation-state abstraction, for example
`django_strawberry_framework/extensions/operation_state.py`, and one package
runner used only by `DjangoSchema`. Do not put a new, slightly different
`execution_context` property on resource, error, debug, and optimizer classes.

The abstraction has two responsibilities that must remain separate:

1. **Long-lived extension configuration** belongs to its owning extension or
   schema and is immutable/read-only to resolvers.
2. **One operation's mutable state** belongs to the runner instance created for
   that operation. It contains the engine context and any extension-specific
   scratch state, and is reachable only through a task-local binding while that
   runner is active.

The state object must be created per `(resolved framework extension, runner)`,
not stored in a dictionary on the shared extension and not keyed by an
untrusted extension object's equality or hash. Keep an ordered tuple of
`(extension, state)` pairs or identity-index it with `id()` plus an identity
check. A consumer extension may make `__hash__` or `__eq__` hostile; no state
decision should invoke either.

The operation-bound base should expose `execution_context` as the context in
the state currently bound to that extension. The binding carrier is itself
security-relevant state: do not store its `ContextVar` in an ordinary
`self._current_state` attribute that a resolver can replace or that a second
`__init__` call can recreate. Settle one carrier per extension identity behind
a package-private authority. The authority may strongly retain the
`ContextVar` because that object does not point back to the extension; it must
hold the extension itself only weakly, and every completed binding must reset so
the variable does not retain a request through the task context.

Strawberry's assignment before runner creation is a handoff, not the operation
binding. The setter must push a temporary assignment binding and its token onto
a task-local stack without writing the assigned context into an already-bound
outer operation state. `DjangoSchema.create_extensions_runner` must claim the
exact top assignment for each resolved framework extension, verify that it is
for the runner's exact `ExecutionContext`, and reset that assignment token
*before the factory returns*. The runner creates its state from the context
passed directly to its constructor, not by rereading the temporary fallback.

Resetting the assignment only when `operation()` exits is too late. Upstream
constructs the runner and then builds the middleware manager and other execution
machinery before entering the operation context. A failure in that gap has no
operation `finally` to run. Immediate handoff also gives nested execution the
right transition: the inner assignment briefly overlays the current binding,
runner construction resets it back to the outer state, inner `operation()`
binds its own state, and inner teardown token-resets to the outer state again.
The handoff and rollback path must be all-or-nothing if runner construction
fails partway through multiple framework extensions.

The core shape is:

```python
class _OperationState:
    execution_context: ExecutionContext
    # Extension-specific mutable state belongs in a subclass or private slot.


class _OperationBoundExtension(SchemaExtension):
    # One package-private ContextVar carrier per extension identity. The value
    # is a runner-created _OperationState, never a process-wide last context.

    @property
    def execution_context(self) -> ExecutionContext | None:
        state = _OPERATION_BINDINGS.current(self)
        return None if state is None else state.execution_context

    @execution_context.setter
    def execution_context(self, context: ExecutionContext) -> None:
        # Temporary engine-assignment handoff only. Never mutate `state` here.
        _OPERATION_BINDINGS.assign(self, context)

    def _new_operation_state(self, context: ExecutionContext) -> _OperationState:
        return _OperationState(context)
```

That pseudocode intentionally omits the task-local assignment-token stack and
the runner bind/reset methods. Those are required implementation details, not
optional cleanup: an inner execution in the same task must reset to the outer
state, an exception or cancellation must reset to the predecessor, and separate
threads or tasks must never see one another's state. A process-global or plain
instance list of tokens would recreate the cross-request race in a different
container.

### The runner, not extension hooks, owns lifetime

Override `DjangoSchema.create_extensions_runner` to return a package subclass of
Strawberry's `SchemaExtensionsRunner`. It receives the exact resolved extension
list and the exact `ExecutionContext` after Strawberry's assignment loop, so it
is the only central point that can cover classes, accepted instances, and
singleton-returning factories without calling a factory twice.

Its operation wrapper must do the following in this order:

1. Select only framework extensions derived from `_OperationBoundExtension`.
   Do not wrap, copy, or proxy arbitrary consumer extensions.
2. Claim and immediately reset each selected extension's exact pre-runner
   assignment token. If any claim or state construction fails, restore every
   claimed binding before propagating the error.
3. Create one state object for each selected resolved extension from the
   runner's direct context argument and retain the ordered `(extension, state)`
   pairs on the runner.
4. At `operation()` entry, bind all retained states before entering
   Strawberry's upstream context manager.
5. Enter the upstream manager. This covers `on_operation`, parsing,
   validation, execution, resolver-middleware execution, and every normal
   exception path.
6. In `finally`, exit the upstream manager first so LIFO extension teardowns
   still see their own operation state, then reset every binding token in
   reverse order. Both synchronous and asynchronous `__exit__` paths need this
   rule.

The wrapper must implement both the sync and async context-manager protocols.
A sync-generator hook can run during asynchronous execution, so two separate
implementations that each make a slightly different binding decision will drift.
Use one token-management primitive and two thin protocol adapters.

Result collection needs a second, short binding scope. Strawberry calls
`get_extensions_results_sync()` after normal sync operation teardown, and its
async equivalent can occur both inside an early-return operation scope and
after a normal one. The custom runner must bind the same runner-owned state
around both result methods. Otherwise debug state either disappears after
teardown or is put back on the shared extension to make `get_results` work.

The streaming runner survives for the lifetime of the async generator. Its
operation binding must therefore remain active until the generator completes or
is closed; cancellation and `aclose()` must follow the same `finally` reset.
Bind around `on_stream_result` as well, even though it normally executes inside
the operation scope, so the runner contract is complete rather than dependent
on one upstream call ordering.

Do not implement the fix by overriding `DjangoSchema.execute` and
`execute_sync` alone. That misses `stream`/`subscribe`, duplicates upstream
control flow, and is vulnerable to early returns whose result hooks run at a
different point. Do not implement it by copying the optimizer's current setter:
`ContextVar.set()` without a token reset fixes cross-task overwrites but leaves
the nested execution's value current after the inner operation returns.

The assignment handoff applies only when the assigned context belongs to a
`DjangoSchema`, because only that schema will create the package runner that can
claim it. Preserve the documented raw-`strawberry.Schema` class/fresh-factory
path with an instance-local compatibility state on that fresh extension. Do not
put an unreset, per-instance `ContextVar` into a long-lived task merely to serve
that compatibility path: Python task contexts retain variables that have been
set even after the extension's ordinary references disappear. A raw Strawberry
shared instance remains explicitly outside the isolation guarantee; a fresh
class/factory entry remains functional and collectable.

### Apply the boundary to each package extension

| Extension | Long-lived state | Per-operation state that must move behind the runner binding |
| --- | --- | --- |
| `DjangoResourcePolicyExtension` | Accepted explicit policy | `execution_context`; resource budget remains its existing tokenized operation state |
| `DjangoErrorPolicyExtension` | Schema-owned error policy | `execution_context` and completed result access |
| `DjangoDebugExtension` | Production-disclosure acknowledgement | `execution_context`, snapshots, and response payload |
| `DjangoOptimizerExtension` | Cache, strictness, nested strategy | `execution_context`, active execution bookkeeping, and request-local optimizer stashes |

`_AdmissionGuard` and `_RefusedConfiguration` are created fresh by
`DjangoSchema.get_extensions`, so they do not need the shared-instance
machinery. They still run inside the runner and continue to read the operation's
real engine context.

For the debug extension, replace the class/instance `_payload` and `_snapshots`
storage with a debug-specific operation state. `get_results` must read the state
that the custom runner temporarily rebinds; it must never read a last completed
payload from the shared extension object. A parse or validation response must
therefore have no debug payload, even after a previous successful shared-object
request.

For the production acknowledgement, settle the exact built-in bool into a
private authority at construction and have `_disclosure_permitted` read only
that authority. Reject a second `__init__` call, just as the resource extension
does. A compatibility property may expose the accepted bool, but it must be a
copy/read-only view; assigning to an ordinary `allow_unsafe_production`
attribute or injecting one in `__dict__` must not affect enforcement. This is a
security configuration, not a request-local preference.

The optimizer needs two corrections. First, make it an operation-bound
extension so the shared plan-cache object regains the outer context after nested
execution. Second, remove optimizer correctness stashes from a shared
`info.context` object while an optimizer operation is active. The current
`on_execute` clears and reuses `DST_OPTIMIZER_*` keys on that object, so even a
perfect `execution_context` reset leaves an inner operation able to erase or
replace the outer operation's plan, planned-relation, FK-elision, lookup-path,
and strictness values.

Give the optimizer operation state its own mapping and make the optimizer's
internal read/write facade prefer that mapping for the current operation. The
generated resolvers and `DjangoOptimizerExtension._stash_union` should use that
facade rather than `utils.context.py` directly. Preserve the existing generic
context helpers as fallback behavior for direct, unmanaged helper callers if
that compatibility is needed, but do not use an outer resolver's mutable
`context_value` as the authoritative store during a managed execution. Existing
`ContextVar` reset pairs for active optimizer, strategy, strictness, selection
memos, and scoped relations should remain tokenized; the new state mapping
closes the remaining direct-object seam.

Audit the optimizer's long-lived settings at the same time. Its documented
singleton has mutable `strictness`, `nested_connection_strategy`, and a
re-runnable constructor. Store the settled configuration behind private
authority or an equivalent protected immutable record, and keep the plan cache
as the only intentional shared mutable structure. A resolver must not be able
to change future requests from strict to off, replace the strategy a cache was
keyed for, or replace the extension's context variables by calling `__init__`
again.

### Raw Strawberry schemas and documentation

This runner can protect `DjangoSchema` because it owns the runner factory. A
plain `strawberry.Schema` does not call that factory, so the package cannot
truthfully promise that a shared extension instance is operation-isolated there.
Do not conceal that limitation with a partial extension-local workaround.

The implementation must nevertheless preserve the supported fresh-entry path
for a plain Strawberry schema. When Strawberry assigns a context whose schema is
not `DjangoSchema`, create/read the extension's instance-local compatibility
state; class and fresh-factory entries make that state operation-local by object
lifetime. Do not enqueue a runner handoff that no package runner will ever
claim, and do not make the raw compatibility path the fallback for a failed or
missing `DjangoSchema` handoff.

Update `DjangoResourcePolicyExtension`'s plain-Strawberry example to use a
fresh factory:

```python
extensions=[lambda: DjangoResourcePolicyExtension(policy=ResourcePolicy(max_depth=8))]
```

Do not show `extensions=[DjangoResourcePolicyExtension(...)]`. Align any
error-policy and debug documentation with the same rule: raw Strawberry callers
use a class when zero-argument construction is enough or a factory that creates
a new extension on every call. The optimizer remains the explicit exception
because its cache is intentionally shared, and it is safe only through the
`DjangoSchema` operation-state runner described above.

Update the [extension-isolation glossary entry][extension-isolation]. Its
current guarantee says each operation gets a distinct stateful extension
instance, which is false for the accepted instance and singleton-factory paths.
The corrected guarantee should name operation-local **state** for
framework-managed extensions under `DjangoSchema`, while preserving the
optimizer's intentional cross-request cache.

## P2 — accept non-weak-referenceable callable factories without leaking schemas

`PrivateMembership.accept` currently takes `weakref.ref()` of every accepted
entry. A callable factory with `__slots__ = ()` is valid for
`strawberry.Schema`, but `DjangoSchema` turns it into `ConfigurationError` solely
because it cannot be weak-referenced. Adding `"__weakref__"` to that callable's
slots makes the schema work, proving this is not an invalid callable surface.

Do not solve this by globally holding every entry strongly. A bound factory or
extension can point back at its schema; a module-global record that strongly
holds it forms a root `global -> entry -> schema`, retaining the schema and its
last execution context forever.

Use a hybrid, schema-lifetime holder instead:

1. Materialize the accepted entries exactly once.
2. For each weak-referenceable entry, retain the current per-member weak
   evidence. This preserves the current ability to detect a disappeared entry
   without rooting it globally.
3. Put non-weak-referenceable entries in a private, sealed holder that the
   schema itself holds under its private membership attribute. The global table
   keeps a weak reference to that holder and a weak reference to the owner, not
   a strong reference to either.
4. Record each entry's position and either its direct member weak reference or
   its sealed-holder position. On recall, reconstruct only from that evidence;
   never read a replacement sequence from `owner.__dict__`.
5. If a non-weak-referenceable entry's holder no longer resolves, return
   `None` and let `DjangoSchema.get_extensions` fail closed with
   `SCHEMA_CONFIGURATION_UNAVAILABLE`. Never substitute a schema default or a
   rewritten entry.

The holder must expose no mutable membership API and must seal its stored tuple
after initialization. This is important: weak evidence for a carrier says
nothing about entries inside a carrier whose contents ordinary consumer code can
replace. The read path validates the original holder identity and returns its
sealed accepted members, not whatever a later schema attribute write supplies.

The hybrid design retains the existing behavior for weak-referenceable entries:
writing over the owner attribute cannot nominate new entries, and an accepted
class or externally retained entry can still be resolved. For the exceptional
non-weak-referenceable entry, losing the schema-owned sealed holder is an
unrecoverable loss of the only accepted evidence and must fail closed. Neither
path creates a global strong reference to the consumer callable graph.

Remove the false claim that all supported extension entries support weak
references from the schema setter and its tests. The user-facing error should
reject only entries Strawberry itself cannot accept, not a valid callable whose
memory layout happens not to support weak references.

## Required regression suite

Use real GraphQL behavior and independent parameterized node IDs. The live-tier
rule in [the test-query README][live-readme] forbids a case loop inside one test;
each entry form, view, and asserted protection needs an `ids=` value.

### Live HTTP resource and error cases

Place resource admission coverage in
`examples/fakeshop/test_query/test_resource_policy_api.py` and error disclosure
coverage in `examples/fakeshop/test_query/test_error_policy_api.py`, using
purpose-built mounted schemas where the default schema cannot express the
shared-entry spelling.

- Cover class, fresh factory, direct shared instance, and singleton-returning
  factory through both sync and async Django GraphQL views.
- Pause A only after resource arming using bounded events; run B; release A in
  `finally`. Do not use sleeps and do not mutate the policy, execution context,
  extension list, or result in the coordination hook.
- Assert the shared-instance and singleton-factory rows reject exactly like the
  fresh controls after the fix: code `RESOURCE_LIMIT_EXCEEDED`, the expected
  bound, and no resolver/execution witness from the oversized query.
- Under `DEBUG=False`, assert the raw exception sentinel never appears, the
  configured safe message does appear, and a correlation identifier is present.
  Exercise both overlapping requests and a resolver with nested
  `info.schema.execute_sync`; then make one normal request to prove cleanup.

### Debug, optimizer, stream, and lifetime cases

- Add a debug case with a shared instance: successful operation then parse
  failure. The latter has no `extensions.debug`; it must never reuse the earlier
  payload object or its content. Retain the class/fresh-factory control.
- Add a production debug-acknowledgement case under `DEBUG=False`: a resolver
  attempts to mutate the shared extension's acknowledgement, then a later
  request still receives no debug extension payload. Include an acknowledged,
  deliberately configured control so the test proves the diagnostic itself is
  not accidentally disabled.
- Add a nested optimizer case through the documented singleton factory. After
  inner `execute_sync` returns, the outer resolver must still observe its own
  execution context and its own plan/planned-relation/FK-elision/strictness
  state. A post-inner optimizer operation must preserve outer behavior. Also
  assert the next independent request begins with no inherited state.
- Add a pre-operation setup-failure case. Use a consumer extension whose
  middleware capability check raises after `create_extensions_runner` returns
  but before `operation()` is entered. Assert the assigned request context and
  a context sentinel are collectable, the shared framework extension has no
  current state afterward, and a later normal request starts clean. This is the
  regression that proves assignment cleanup happens during runner handoff
  rather than depending on operation teardown.
- Attempt to replace the operation-binding carrier through the shared extension
  and rerun its constructor from a resolver. Neither action may replace the
  package-private carrier, alter the current request's state, or influence the
  next request. Keep this distinct from the long-lived configuration-tamper
  rows: it protects the mechanism that carries operation state itself.
- Cover cancellation and generator close on the `stream`/`subscribe` path.
  The package runner's state must reset after the async generator is closed and
  the next operation must have no stale payload, policy budget, optimizer state,
  or context pointer. Put transport-specific work beside the existing consumer
  transport tests when the HTTP-only live tier cannot drive the stream seam.
- Retain the collection proofs: after operation completion and collection, both
  schema and request-context sentinels must be collectable for automatic class
  entries, direct instances, a bound factory, and the new slotted callable
  factory. The slotted case is the regression that prevents a hidden global
  strong hold.

### Package-level construction cases

In `tests/test_schema.py`, construct and execute a `DjangoSchema` with a
valid slotted callable factory and with a weak-referenceable control factory.
Both must execute. Retain the invalid tuple/string/integer cases, but do not
present them as proof that valid factory support is exhaustive.

Add membership tampering cases for a mixed weak-referenceable/slotted entry
list. A rewritten attribute must never run an unaccepted entry; the weak-entry
path must retain the accepted original when evidence still resolves, while the
lost sealed-holder path must return the typed unavailable-configuration refusal.

## Completion conditions

Before the card is marked done, the delivery tree needs all of the following:

- No framework extension keeps engine context or request scratch state in a
  shared ordinary instance attribute.
- The operation-binding carrier is authenticated package-private state; neither
  attribute replacement nor constructor replay can replace it.
- Strawberry's pre-runner assignment is claimed and reset during runner
  creation, including partial-construction and pre-operation setup failures.
- Runner bindings cover sync execution, async execution, early errors, nested
  execution, streaming results, cancellation, and result collection.
- Debug acknowledgement and optimizer singleton configuration cannot be changed
  by a resolver for a later request.
- Raw `strawberry.Schema` documentation prescribes fresh policy/debug
  extension construction; `DjangoSchema` is the documented isolation boundary
  for the optimizer singleton.
- The valid slotted factory works without a global retention path, and all
  failed membership recovery paths fail closed.
- The live and package regressions above pass, followed by the declared default,
  sharded, and floor delivery gates when authorized.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md

<!-- docs/ -->
[extension-isolation]: GLOSSARY.md#per-operation-extension-isolation

<!-- docs/SPECS/ -->
[spec-047]: SPECS/spec-047-resource_policy-0_0_14.md
[spec-048]: SPECS/spec-048-secure_output_defaults-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[live-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
