# Adversarial review — release hardening

Date: 2026-09-16

Reviewed: the uncommitted implementation above HEAD `1fcc5292`, including the latest
`PrivateMembership` and inherited-policy construction fixes.

**Verdict: one verified P1 operation-isolation defect and one P2 callable-factory
compatibility defect remain.** The two findings from the preceding review are closed by
fresh HTTP verification. The P1 has two independently reproduced consequences: resource
admission bypass and unexpected-error disclosure.

This pass follows the [repository rules][agents] and investigates the lifetime of operation
state, beyond the previous configuration-mutation checks. The package is unreleased; the
recommendations concern getting its release contract correct, without assuming an existing
installed user base. This is a bounded review, not certification of every spec-050 requirement
or of the concurrent test migration.

## P1 — Shared enforcement extensions read another operation's execution context

**Owners:**

- `django_strawberry_framework/schema.py::DjangoSchema.get_extensions`;
- `django_strawberry_framework/extensions/resource_policy.py::DjangoResourcePolicyExtension.on_parse`;
- `django_strawberry_framework/extensions/error_policy.py::DjangoErrorPolicyExtension.on_operation`.

The accepted extension membership and its configuration now survive the previous writes.
However, those protections do not isolate the mutable `execution_context` Strawberry assigns
to every resolved extension. An accepted instance is returned unchanged; a factory may also
return the same instance repeatedly. The resource and error extensions keep that context as
an ordinary instance attribute.

Two operations sharing the object therefore overwrite one another's document, variables,
schema and result reference. The private resource-budget `ContextVar` does not fix this:
the budget can belong to operation A while the document charged against it belongs to B.

### Verified HTTP consequences

Fresh schemas were mounted at `/graphql/` through both `DjangoGraphQLView` and
`AsyncDjangoGraphQLView`. Independent `django.test.Client` requests exercised four
configurations for each policy extension:

| Extension entry | Oversized query during overlap | Unexpected exception during overlap |
| --- | --- | --- |
| Preconstructed instance | Executes successfully | Raw exception message disclosed |
| Factory returning that same instance | Executes successfully | Raw exception message disclosed |
| Factory constructing a fresh instance | Correct typed rejection | Correct masking and correlation ID |
| Extension class | Correct typed rejection | Correct masking and correlation ID |

Both view implementations produced the same results. Every response was HTTP 200.

For resource enforcement, the configured policy was `ResourcePolicy(max_aliases=1)`.
The target document was `{ a: hello b: hello }`, and the benign document was
`{ hello }`.

A consumer operation hook paused A after its resource budget was armed. B then completed
normally, and A resumed. The hook only coordinated events; it never changed the schema,
policy, document, execution context or result. The sync hook waited on a bounded
`threading.Event`; the async hook awaited that event through `asyncio.to_thread`.
Separate Clients drove the overlapping requests.

Observed sequence with either shared spelling:

```text
A alone before overlap -> RESOURCE_LIMIT_EXCEEDED, max_aliases, limit=1, charged=2
B while A is paused    -> {"hello": "world"}
A after B completes    -> {"a": "world", "b": "world"}, no errors
A alone after overlap  -> RESOURCE_LIMIT_EXCEEDED, max_aliases, limit=1, charged=2
```

A's `on_parse` reads B's already-parsed document from the shared extension attribute, so it
never records a rejection for A. The fresh `_AdmissionGuard` consequently has no rejection
to restore. This is separate from the previously closed validation-cache issue.

For error masking, the target resolver raised
`RuntimeError("REVIEW-CONCURRENT-PRIVATE-SENTINEL")`. Under `DEBUG=False`, it was masked
before and after overlap. During overlap, the raw sentinel reached A's response with no
correlation metadata. The shared error extension's teardown consulted B's healthy result,
leaving A's unexpected exception untouched.

The matrix comprised 16 cases and 64 HTTP requests: two policy extensions, two views and
four entry forms, each with serial-before, overlapping A/B, and serial-after observations.
Fresh-entry controls used the identical coordination hook and query shapes.

### A nested query reproduces disclosure without a scheduling race

An additional eight HTTP requests covered both views and all four entry forms with this
resolver shape:

```python
@strawberry.field
def nested_failure(self, info: strawberry.Info) -> str:
    inner = info.schema.execute_sync("{ hello }", context_value=info.context)
    assert inner.errors is None
    raise RuntimeError("REVIEW-NESTED-PRIVATE-SENTINEL")
```

The shared instance and shared-returning factory exposed the sentinel. The class and fresh
factory returned the configured safe message and correlation ID.

The inner execution replaces the same instance attribute and does not restore the outer
context. On outer teardown, the error extension processes the completed inner result.
This reproduction uses no extra extension, mutation of internals, patch or concurrency gate.

### Why this belongs in the release gate

The current code and [spec-047][spec-047] explicitly accept resource-extension instances and
factory entries. Strawberry 0.324.0 warns for direct instances but still executes them. A
singleton-returning factory emits no such warning and takes the same unsafe path.

The automatic class configuration passed the controls; the finding is conditional on a shared
policy extension. It is not evidence that every default installation leaks. It is also not
attributed to the latest membership patch: that patch preserves membership, while this defect
concerns the state of an accepted member during execution.

The [extension-isolation glossary entry][extension-isolation] already distinguishes the
optimizer's intentionally shared configuration/cache from operation state. Locally,
`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.execution_context`
uses a `ContextVar` specifically to prevent this shared-instance race. The policy extensions
have not applied the same distinction.

### Root correction

Give enforcement hooks a binding to their own operation's execution context for the entire
lifecycle. Keep accepted policy configuration separate from that binding. Cover both resource
admission and error masking in the production correction.

Reuse or extract the relevant operation-context abstraction with the optimizer where
appropriate, rather than adding separate context-storage conventions to each extension.
The existing optimizer descriptor is useful prior art, but copying its setter alone does
not prove nested-execution restoration: task-local storage still gets overwritten by a
nested operation in the same task. Bind and restore at the actual operation lifecycle,
including exceptional exit and cancellation, or provide independent operation instances
whose context cannot be overwritten.

Capturing a context only in `on_parse` or error teardown is too late. Also account for
consumer hooks that yield before a policy hook starts. Do not repair only direct-instance
registration; a factory returning the same object reproduces the same failure.

Keep existing accepted-policy immutability, per-operation factory invocation and schema
collectability. Avoid blind copying of arbitrary consumer extension objects or sharing their
mutable request state under a new wrapper.

### Required regression evidence

Place the observable protections in the live HTTP tier, following [its rules][live-readme].
Parametrize independent node IDs for view, entry form and claimed protection. Synchronize
with bounded events and release them in `finally`; use no timing sleeps.

For admission, assert the expected typed rejection and an external resolver/execution witness
that remains untouched. For masking, assert the raw sentinel is absent, the configured message
is present and the correlation ID survives. Check the benign request's response too. Retain
serial controls, fresh-instance controls and the nested-query case. Include a recovery request
after exceptions/cancellation to establish that cleanup did not strand operation state.

The new authority and sequential factory tests do not exercise overlapping or nested
execution. Passing them therefore does not establish this invariant.

## P2 — Membership authentication rejects a valid callable factory without weak-reference support

**Owners:**
`django_strawberry_framework/utils/private_state.py::PrivateMembership.accept` and
`django_strawberry_framework/schema.py::DjangoSchema.extensions`.

`accept` takes `weakref.ref(member)` for every entry. The setter and its new package test
justify this with the claim that every class, instance or factory Strawberry accepts supports
weak references. That claim is false for an ordinary callable object with slots:

```python
class ExtensionFactory:
    __slots__ = ()

    def __call__(self):
        return ProbeExtension()
```

Using the same factory and a valid `SchemaExtension` subclass:

```text
strawberry.Schema(..., extensions=[factory])
    -> builds; { hello } returns {"hello": "world"}

DjangoSchema(..., extensions=[factory])
    -> ConfigurationError: ... contains an entry that cannot be held
```

Adding only `"__weakref__"` to the factory's slots makes `DjangoSchema` accept it and execute
the query. Thus the failure is the new storage requirement, not an invalid extension return,
invalid schema, missing Django settings or an incorrect callable signature.

This is a startup compatibility defect in the documented callable surface, not an admission
bypass. No existing production deployment is assumed.

### Root correction and tests

Separate acceptance of a supported extension entry from whether the original object supports
weak references. The ownership/authentication representation should be able to retain an
opaque callable with the schema's lifetime and verify the accepted entry without requiring
the consumer to add Python memory-layout features.

Any intermediary holder must authenticate the entry it supplies, not merely its own identity;
otherwise it restores the previous carrier-content flaw. Retain the tests for mutation,
loss of the only strong reference, and bound-factory/schema collection. Do not globally root
a callable graph that can point back at its schema.

Add the valid slotted callable as a construction regression in the package tier, with a
weak-reference-capable callable as its control. The existing
`tests/test_schema.py::test_an_extension_entry_the_schema_cannot_hold_as_accepted_is_refused`
only supplies tuples, strings and integers. Those invalid entries cannot establish that all
valid factories are accepted; its docstring also repeats the false universal claim.
Keep real callable execution covered through the live view when the correction lands.

## Closures verified in this pass

Fresh HTTP probes made 34 requests across both package views:

- Replacing `_django_extensions` with an empty tuple or a wider-policy factory tuple
  preserved the accepted class entries: later requests stayed at one row and unexpected
  errors stayed masked.
- Removing the sole strong hold on an anonymous, narrow-policy factory yielded
  `SCHEMA_CONFIGURATION_UNAVAILABLE` on the next request. It did not fall back to wider
  schema defaults.
- Re-running the constructor of either an explicitly configured or an inheriting accepted
  resource extension raised `ConfigurationError`; subsequent requests retained one row.

The old mutable carrier no longer exists. The constructor guard now records the inheriting
configuration as constructed. These close the two previous findings at their root.

Separate weak-reference/GC probes executed a query and then collected both the schema and
a request-context sentinel for automatic class entries, a resource-extension instance, and a
schema-bound factory. The previous global-retention regression did not reproduce.

The validation-cache fix was not re-certified in this pass. Its earlier successful evidence
remains in the preceding review history; the new admission failure above requires a shared
extension and is explained by a different mechanism.

## Scope, repository alignment and completion

The review used 106 fresh HTTP requests, additional standalone construction/GC probes, and
a same-event-loop async overlap probe. Installed versions: Strawberry 0.324.0,
graphql-core 3.2.8, Django 6.1. The concurrency HTTP probes used two Clients in separate
threads; the async views therefore ran on separate event loops. The additional direct async
probe reproduced resource bypass with two tasks in one loop.

The [GOAL][goal] and local Graphene recipes cookbook continue to support the existing
Meta-first public surface; neither finding calls for a decorator API, new settings or new
list-argument semantics. Upstream source comparisons included Strawberry's extension
resolution/context assignment, strawberry_django's optimizer ContextVar lifecycle, and
graphene_django's request-local validation/execution flow. The package's own optimizer is
the closest existing implementation precedent for the isolation correction.

No production implementation was edited, no pytest or coverage run was requested/performed,
and no floor environment or WebSocket transport was certified. The probes used temporary
in-memory URL configurations and no model/database writes. Existing concurrent changes
were preserved.

The [build record][build-050] explicitly ties its historical green figures to older trees and
still owes the full declared floor scope at delivery. After the two corrections, the final
full, sharded and declared-floor gates must run against the delivery tree when authorized.
The P1 is the release blocker; the P2 should be resolved before claiming the full callable
extension surface.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md

<!-- docs/ -->
[extension-isolation]: GLOSSARY.md#per-operation-extension-isolation

<!-- docs/SPECS/ -->
[spec-047]: SPECS/spec-047-resource_policy-0_0_14.md

<!-- docs/builder/ -->
[build-050]: builder/DONE/build-050-list_field_arguments-0_0_15.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[live-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
