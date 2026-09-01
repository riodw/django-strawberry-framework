# Critical architectural review: `DjangoListField` arguments

- Target: [`spec-050-list_field_arguments-0_0_15.md`][spec-050]
- Card: [`WIP-ALPHA-050-0.0.15`][kanban]
- Review posture: pre-implementation, against the current repository and upstream source
- Verdict: **not implementation-ready until the blocking decisions below are resolved**

## Executive finding

The specification has a strong ownership model: one synthesized signature, one resource-policy
window, visibility before order, one final slice, a Meta-derived `OrderSet`, no connection
semantics, and an async-only representation that keeps the root queryset lazy for the optimizer.
Those are the correct large seams.

The remaining problems are not mainly missing pseudocode. Several promises are stronger than the
mechanisms can prove, and a few test requirements are impossible under Python's iterator semantics.
The most important issues are:

1. An "active order" is not a stable or repeatable page when the order contains ties, yet the
   problem statement and goals repeatedly promise stability.
2. A universally published positive `offset` can be permanently unusable on a target with neither
   `Meta.orderset_class` nor effective model `Meta.ordering`.
3. The spec calls `offset: 0` semantically identical to omission, then deliberately makes it reject
   combined querysets that omission accepts.
4. The async test plan expects an unstarted async generator's `finally` witness to run after zero
   advances. `aclose()` on an unstarted async generator does not enter its body, so that witness is
   impossible.
5. The proposed same-route proof compares explicit database alias state but not routing hints; two
   unrouted querysets can both have `_db is None` and still resolve to different databases.
6. The resource-policy text calls collection-cost accounting conservative even though offset work
   is uncharged and a trusted field can return more rows than the walker charges.

Production work should wait until the specification makes explicit choices for these items.

## 1. Inconsistencies and contradictions

### B1 - "Stable subset" conflicts with the explicit refusal to require total order

The problem statement says clients need a stable subset, Goal 4 describes repeatable pagination,
and Decision 6 repeatedly calls the accepted order a stable-page guarantee. Decision 7 then states
that ties are accepted, uniqueness is not proven, and no primary-key tiebreaker is appended.

Those statements cannot all be true. Ordering by `city` alone is deterministic as an ordering
expression but does not determine which tied row falls on either side of an offset boundary.
Concurrent inserts make the problem worse, but no concurrency is required: the database is free to
return tied rows in either order between equivalent executions.

The existing connection deliberately solves a different problem by making its effective order
total in `django_strawberry_framework/connection.py::_finalize_queryset`. The list field may
reasonably refuse that behavior, but then the contract must say **ordered offset**, not stable or
repeatable pagination. Django 6.1 has a `QuerySet.totally_ordered` helper for common field cases,
but the package also supports Django 5.2 and arbitrary expressions, so that version-specific helper
is not a portable substitute for a declared policy.

Required correction: choose one of these contracts and use it consistently throughout the spec,
glossary, docstring plan, tests, and migration wording:

- Require a recognized total order and reject ties that cannot be proven safe.
- Append a deterministic terminal term, accepting the semantic change.
- Keep the current active-order guard but stop claiming stability or repeatability; document that a
  unique final term is a consumer obligation and that the framework does not enforce it.

The third choice best matches the card's stated minimal shape, but it is a weaker product guarantee
than the current problem statement claims.

### B2 - Universal `offset` can advertise a permanently unusable capability

Decision 2 correctly makes `orderBy` conditional on `Meta.orderset_class`. Decision 6 rejects a
resolver's explicit `.order_by(...)` as hidden evidence and accepts only active `orderBy` or still-
effective model `Meta.ordering`. Therefore a target with neither an `OrderSet` nor model default
ordering publishes `offset: Int`, but every positive value must fail with `order_required`.

This is the same introspection-honesty problem Decision 2 uses to reject a dummy `orderBy`, only
shifted onto `offset`. It is also more restrictive than the current architecture's consumer-
resolver seam: a schema author may already return an intentionally ordered queryset, but the new
surface refuses to recognize it.

The parent card still says all three arguments surface on every `DjangoListField`, while the spec
publishes only two on targets without an order sidecar. That board/spec disagreement must be
resolved in the source card rather than left as a qualification buried in Decision 2.

Required correction: explicitly choose and test one capability rule:

- publish positive-offset capability only when the target has a declared order source;
- accept a sealed queryset's effective non-random order as a documented resolver contract; or
- add an explicit Meta-first stable-order declaration for list fields.

If universal `offset` is retained despite being unusable on some fields, the SDL and docs must call
this a runtime precondition rather than claiming every field is pagination-capable.

### B3 - `offset: 0` is both identity and behavior-changing

The user-facing API says `offset=0` is semantically identical to omission except for validation.
Decision 5 and the edge-case list say any non-null argument activates combined-query rejection,
including `offset: 0`, `limit: 0`, and `orderBy: []`, while all-null/omitted input preserves legacy
combined behavior.

Therefore at least `offset: 0` is not semantically identical to omission. An empty or all-null order
list is also described as a no-op by the shipped `OrderSet` contract, yet it changes source
admissibility and can fail before the no-op order pipeline runs. `limit` equal to the existing
effective cap can likewise produce the same window while changing the combined-query verdict.

Required correction: either qualify the identity claim as applying only to ordinary composable
querysets, or split the normalized record into separate concepts such as `was_supplied`,
`changes_window`, and `requires_queryset_composition`. Do not use one `has_active_arguments` bit for
validation, legacy fast-path selection, combined-query rejection, and order capability; those are
different questions.

### B4 - The parent card's SQL requirement remains false after the spec's reinterpretation

The parent card requires SQL `LIMIT`/`OFFSET` to be present exactly when supplied. The shipped
resource policy already applies a `LIMIT` to every raw list through
`django_strawberry_framework/resource_policy.py::bounded_rows`, including when the client supplies
no arguments. The spec correctly recognizes that fact and reinterprets the card as low/high-mark
parity, but the authoritative card remains unchanged.

Required correction: amend the card wording to say omission preserves the existing policy `LIMIT`,
a smaller client limit lowers the high mark, and positive offset raises the low mark. A spec cannot
silently redefine its parent DoD while leaving the board to demand the opposite result.

### H1 - "Exact plain QuerySet" is ambiguous and may break valid custom QuerySets

Decision 5 says a custom `OrderSet.apply_*` result must be an exact plain `QuerySet`. The shared seal
in `django_strawberry_framework/utils/querysets.py::_seal_or_defect` currently accepts sealable
`QuerySet` subclasses and rebuilds them into a framework-owned plain `QuerySet`; that is a central
architectural feature, not an accident.

The TODO pseudocode appears to preserve that pattern, while the prose can be read as rejecting the
candidate merely because it is a subclass. Those are different compatibility contracts.

Required correction: say either "a sealable QuerySet whose successful sealed output is exact and
plain" or explicitly require rejection of every subclass and explain the regression. Reusing the
existing seal strongly favors the former.

### H2 - Nested usage is narrowed without reconciling shipped documentation

The non-goals call `DjangoListField` a root-only supported factory and place manually assigned nested
usage outside the public contract. The shipped glossary currently says nested non-root usage is
functional but not root-optimized. The new text therefore narrows a documented behavior without a
deprecation or compatibility decision.

Required correction: preserve no-argument nested behavior and state whether the new arguments are
supported there, or explicitly deprecate the old documented promise. "Nested pagination remains a
connection concern" does not by itself resolve the existing functional nested-list contract.

### H3 - Async-safety claims are broader than the adapter can guarantee

The async-only adapter fixes a real framework bug: graphql-core checks synchronous iterability before
its async-iterable fallback, and a bare Django `QuerySet` therefore enters synchronous completion.
The adapter correctly prevents that final framework-owned iteration.

It cannot prevent a plain `def` consumer resolver or synchronous `get_queryset` hook from calling
`list(qs)`, `exists()`, `count()`, or other synchronous ORM methods while already executing on the
event-loop thread. The spec deliberately preserves callable-color behavior for those hooks.

Required correction: scope every safety claim to **framework-owned final queryset completion**.
Do not promise that the field prevents arbitrary synchronous ORM work inside consumer code. The
async acceptance suite should include a conforming lazy sync resolver, not imply that an evaluating
sync resolver is made safe by the adapter.

### H4 - `ListArgumentError` has an unresolved public/private contract

The spec gives `ListArgumentError` a stable name, glossary entry, pickle contract, and wire behavior,
but calls it internal and omits `django_strawberry_framework/__init__.py` from the implementation
plan. Comparable named errors such as `ResourceLimitExceeded` and `SyncMisuseError` are exported from
the package root.

Required correction: decide whether consumers may import and catch `ListArgumentError` directly.
If yes, add the root export and its governance tests. If no, say the supported catch surface is
`GraphQLError` / `DjangoStrawberryFrameworkError` plus `extensions.code`, and do not present the
concrete class as public API.

## 2. Missing edge cases

### B5 - The proposed zero-advance async-generator finalization test is impossible

The spec and async TODO require `limit: 0` and pre-bound rejection to perform zero `__anext__` calls
while still proving an async generator's body-level `finally` witness ran. Python does not enter an
async generator body when `aclose()` is called before its first advance, so neither its setup nor its
`finally` block executes. Advancing it to make the witness observable would violate the zero-
consumption guarantee.

Required correction:

- Use a custom async iterator whose externally implemented `aclose()` increments a counter for
  zero-limit and pre-bound rejection tests.
- Use a real async generator's `finally` witness only after at least one item has been requested.
- Distinguish "`aclose()` was invoked" from "the generator body finalized" in the prose.

The HTTP suite also cannot observe a cleanup diagnostic stored only in `BaseException.__notes__`.
That exact note belongs in the package tier unless a test-only error formatter deliberately exposes
it. Live HTTP should prove that the primary `ListArgumentError` remains the serialized error.

### H5 - Sync iterable truncation has no cleanup contract

The DoD promises that sequences, iterables, and async-only iterables are bounded without leaking.
The plan adds explicit `aclose()` behavior only for async iterators. A retained sync generator
consumed through `list(islice(generator, start, stop))` remains suspended after the accepted stop;
its `finally` block does not run until somebody closes or exhausts it.

Required correction: either add one shared sync early-exit `close()` contract and tests, or narrow the
DoD so leak-free cleanup is promised only for async-only sources. Relying on CPython reference
counting is not a cross-runtime resource-management contract and fails whenever the caller retains
the generator.

### H6 - Same-route validation ignores routing hints

The proposed post-order seal promises the same effective database route and emphasizes that
`None` must match `None`. Django's `QuerySet.db` resolves an unrouted queryset through the database
router using both model and `_hints`. Two querysets can therefore both carry `_db is None` while
different hints select different aliases. The current seal validates hint shape and preserves hints,
but the TODO does not require equality with the pre-order source.

Required correction: define whether the invariant is the same explicit alias, the same routing
intent (`_db` plus canonical hints), or the same resolved alias. Then enforce exactly that invariant.
The sharded live test must include an unrouted/hint-driven mismatch, not only `.using("default")`
versus `.using("shard_b")`.

### H7 - Nullable `None` precedence needs a product decision

A nullable resolver returning `None` preserves `None` for `limit` and zero offset, but the same
source raises `order_required` for positive offset and `queryset_required` for any non-null
`orderBy`, including an empty list. This is specified, but it is surprising GraphQL null propagation:
clients that always send pagination variables can turn a legitimate nullable result into an error.

Required correction: explicitly justify this as capability validation that outranks nullable result
propagation, or short-circuit `None` after numeric-domain validation. Add a paired live test showing
the chosen behavior for nullable and non-null outer list annotations.

### H8 - The async live pseudocode contradicts the public iterable rule

Decision 8 rejects every positive offset on an opaque async-only iterable because it cannot prove
order. The async TODO also says an async generator should exercise an "offset/limit" accepted window,
then later says nonzero offset must be rejected. The lower resource-policy helper should support
offset arithmetic for shape completeness, but the public list field should not accept it under the
current order rule.

Required correction: make the live async generator success case limit-only or `offset: 0`, and keep
positive-offset arithmetic for async iterators in `tests/test_resource_policy.py`.

### Additional cases that should be pinned

| Scenario | Why it matters | Required tier |
| --- | --- | --- |
| Target with no `OrderSet` and no model default ordering | Exposes the universal-but-unusable positive-offset decision | Live HTTP plus construction introspection |
| Target with no `OrderSet` but stable model ordering | Proves offset can be useful without publishing `orderBy` | Live HTTP |
| Offset only, with limit omitted | Proves `[offset:offset + effective_ceiling]`, not only the combined example | Live HTTP and resource-policy unit |
| Omitted arguments, explicit `null`, and semantically neutral zero/empty values on the same combined source | Pins the disputed identity/legacy boundary | Live HTTP |
| Combined legacy control | "Preserves legacy behavior" must name the exact pre-card data or error, not merely avoid the new error | Live HTTP baseline fixture |
| Unrouted candidate with changed routing hints | Closes the same-route hole not covered by explicit `.using(...)` | Sharded live HTTP plus package mechanic |
| Sealable `QuerySet` subclass returned by a custom `OrderSet` | Resolves the exact-plain ambiguity | Package tier, with live success if supported |
| Retained sync generator truncated before exhaustion | Proves or explicitly declines sync cleanup | Resource-policy unit |
| Async source with exactly `offset + limit` rows versus fewer rows | Distinguishes accepted-stop close from observed natural exhaustion | Resource-policy unit |
| Two aliases of the same field with different windows | Pins independent low/high marks and prevents accidental shared state | Live HTTP |
| Custom `NameConverter` reused concurrently | Detects unsafe runtime converter mutation if names are recomputed per error | Package concurrency mechanic or build-time caching test |
| Django 5.2 and latest-Django ordering internals | The predicate reads private query state whose shape spans the supported matrix | Existing CI matrix, called out in the spec |

## 3. Configuration, performance, laziness, and thread-safety risks

### P1 - Collection-cost accounting is not conservative for every accepted request

The spec says the document walker remains conservative by charging
`ResourcePolicy.max_list_rows`. That is only an overcharge when a field or client narrows below the
policy. It under-describes work in two accepted cases:

- Positive offset adds up to another `max_list_rows` of logical skip work, but the collection-cost
  walker charges only the return dimension.
- `trusted_max_rows=True` with `max_rows > policy.max_list_rows` can return more rows than the walker
  charges. This divergence already exists for omission, but the spec must not call it conservative.

The runtime ceiling still bounds the new coordinate, so this is not an unbounded request. It is,
however, a real mismatch between the execution-resource-policy narrative and the work admitted.
Physical database scans may be larger still because filtering, ordering, and offset execution are
backend-plan dependent.

Required correction: describe the charge as a schema-generic fixed estimate, not a conservative
upper bound. Record the maximum untrusted logical window as `offset + returned rows <= 2P`, and the
trusted case as `P + F`. If that mismatch is unacceptable for the resource-policy threat model, the
root fix is field metadata consumed by the document walker, not argument-name guessing.

### P2 - A third full queryset seal is expensive on every supplied `orderBy`

The visibility boundary already performs deep, recursive query-graph validation and canonical
reconstruction before and after `get_queryset`. Post-`OrderSet` validation proposes another complete
seal so arbitrary public overrides cannot return evaluated, projected, combined, or cross-model
state. That is defensible, but it is not a cheap `isinstance` guard: complex annotations,
subqueries, `Prefetch` trees, and expression graphs are walked and rebuilt again.

Required correction: acknowledge the cost explicitly and benchmark at least a complex annotated
query, a to-many aggregate order, and a queryset with prefetch metadata. Keep the full seal for
overridable public methods unless evidence supports a safe fast path; do not silently duplicate its
state reads in `list_field.py`.

### P3 - Order input is normalized twice and custom overrides may observe that

The spec deliberately calls `_normalize_input` once inside public apply and again inside
`_input_has_active_terms`. This preserves the public apply override, but it retroactively requires a
private overridable helper to be pure and deterministic. A stateful override can produce different
application and activity verdicts, and a public `apply_*` override that intentionally implements a
different input interpretation can still be contradicted by the base helper after it succeeds.

Required correction: treat this as an explicit compatibility constraint, not merely a test counter.
Prefer one immutable normalized-order record if the public API can evolve without bypassing
overrides. If double normalization remains, cap its input through the existing value policy, document
the purity requirement on the method itself, and test disagreeing overrides fail with an actionable
configuration error rather than an incidental order verdict.

### P4 - Wire-name conversion should be lazy and preferably build-time

Wire names are needed only when constructing an error. Re-running a schema's custom
`NameConverter.from_argument` on every successful resolver invocation adds redundant work and invokes
a shared custom converter concurrently at runtime, even though custom converters are normally used
during schema construction. A stateful or non-thread-safe converter could return a spelling different
from the already-built schema.

Required correction: resolve the wire name only on an error path, or cache the Python-to-wire mapping
when Strawberry builds the field. If runtime recomputation remains, explicitly require name converters
to be deterministic and thread-safe and test that contract.

### P5 - Limit zero does not make an eager consumer cheap

The spec correctly notes that a materialized list may already have fetched all rows before the window
is applied. The same is true for a consumer resolver that performs a query internally before returning
a sequence. `limit: 0` validates before calling the resolver but still invokes it and can therefore do
arbitrary work.

Required correction: keep the guarantee narrowly stated as no framework-owned source advancement or
row-fetch query after the resolver returns. Do not document `limit: 0` as zero database work without
qualifying consumer side effects, visibility hooks, permission checks, and the independent document
budget.

### P6 - Offset is bounded but can still be expensive

`max_list_rows` bounds the accepted coordinate, not database scan work. Even a small offset can force
sorting or scanning a large filtered relation; to-many aggregate order can add `GROUP BY`; and a high
offset commonly degrades with table size. The spec acknowledges physical scans in one paragraph but
still uses "work budget" language elsewhere as if the coordinate bounded the plan.

Required correction: use "accepted coordinate ceiling" consistently. Keep the existing deadline as
one cooperative pre-fetch check, but do not imply it can interrupt a query after dispatch.

### Thread-safety assessment

The proposed immutable argument record, per-result async adapter, and local optimizer unwrap/rewrap
state do not introduce shared mutable request state. The existing optimizer's operation state remains
ContextVar-backed. The two thread-safety concerns are narrower:

- runtime calls into a shared custom name converter, addressed in P4; and
- class-level `OrderSet` normalization/spec ledgers, which must be fully materialized at finalization
  before concurrent execution, as the current sidecar architecture already expects.

No new global cache should be introduced for argument values, normalized order data, querysets, or
wire errors.

### Redundant-validation assessment

The spec is correct to avoid validating client numeric domains again inside `bounded_rows*`; those
helpers should receive already-validated coordinates. It is also correct to keep one
`check_deadline` call in `_raw_list_bound`. The redundant work that remains intentional and must be
justified is:

- the post-order full seal after the two visibility seals; and
- double order normalization.

Those operations protect different override boundaries, so they must not be merged casually, but the
spec should stop describing the pipeline as if all checks were constant-time.

## 4. Test and documentation gaps against the live-tier guide

### What is aligned

The test plan correctly follows the core rules in
[`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme]:

- consumer-visible behavior is driven through real `/graphql/` HTTP requests;
- library rows are created inline instead of importing products seed helpers;
- exceptional schemas use holder mounts and the shared full-schema reload discipline;
- async completion uses `AsyncClient` plus `AsyncDjangoGraphQLView` and explicitly documents why the
  synchronous shared request helper cannot be used;
- sharded routing stays behind `FAKESHOP_SHARDED=1` in `test_multi_db.py`;
- package tests are reserved for pickle mechanics, protocol identity, impossible optimizer exits,
  and hostile query states that cannot be produced by the public schema.

### G1 - The current async README exemption needs a broader rule, not a one-off sentence

The guide's opening paragraph currently says raw request-envelope subjects are the reason to bypass
the shared helper. The new suite bypasses it for execution color, not raw-envelope testing. The Slice
5 TODO mentions the exception but should update the governing paragraph so future async feature
suites inherit a general rule: use the shared helper unless the test specifically requires an async
view/client boundary or a raw transport shape it cannot express.

### G2 - Do not assert private exception notes through ordinary HTTP JSON

The async TODO asks live HTTP to assert a cleanup-failure diagnostic note. The production GraphQL JSON
error envelope does not serialize `BaseException.__notes__`. Keep exact note content and precedence in
the package tier; live HTTP should assert the complete public extensions and that cleanup failure did
not replace the domain error.

### G3 - The sync live plan is too large for `test_library_api.py`

`test_library_api.py` is already the broad library application suite. Adding all nineteen rows,
multiple converter schemas, combined/presliced sources, and malformed `OrderSet` overrides there will
make a field-factory feature difficult to discover and maintain. The live-tier guide permits
cross-cutting suites.

Recommendation: create a dedicated `examples/fakeshop/test_query/test_list_field_api.py` for the sync
surface and retain `test_list_field_async_api.py` for its async color. Both may use the registered
library types and inline library models. If the plan intentionally keeps the tests in
`test_library_api.py`, the README suite description must enumerate the new responsibility explicitly.

### G4 - "Legacy combined behavior" needs an exact baseline oracle

The test plan says omission/all-null preserves legacy behavior but does not specify whether that
holder returns data or raises the existing visibility/Django error. A combined Branch queryset can
interact with `BranchType.get_queryset` filtering before pagination, so "not the new rejection" is not
a sufficient oracle.

Required correction: capture the pre-card result or error in a named baseline helper and assert the
same class, message policy, data, SQL, and hook call count after the change.

### G5 - The supported-version matrix must be named in the test plan

The implementation depends on private or semi-private behavior in Django query state, Strawberry
argument definitions/name conversion, and graphql-core list completion. The repository CI spans
Django 5.2 through latest and Python 3.10 through 3.14, while the spec's source links point at the
single local Python 3.14 environment.

Required correction: state that the new live async completion, model-order predicate, seal axis, and
argument-signature tests must pass on the existing minimum/latest CI matrix. A local 3.14 proof is
evidence, not the supported-version contract.

### G6 - Keep live-first placement exact

Several proposed package tests duplicate behavior that is wire-reachable. The package tier may assert
internal identity and exact call counts, but the following final branches must also remain live:

- every public `ListArgumentError.reason`;
- custom name-converter spelling;
- both model-default order verdicts;
- active order permission before offset rejection;
- combined source and hook-result errors;
- post-order evaluated/projection/combined/wrong-model result classification;
- optimizer-on/off async queryset completion.

This division should be written into each test TODO so coverage does not drift back into package-only
execution during implementation.

### G7 - Isolation and seed discipline must remain visible in the new modules

Every async ORM test needs `@pytest.mark.django_db(transaction=True)`. Test-local types must use
already-registered app `DjangoType`s, schema holders and URL caches must reset in `finally`, and the
shared [`schema_reload.py`][schema-reload] workflow must remain the only full-registry rebuild owner.
Library-only rows use inline model creation. Any future mixed products/auth row must begin with the
required `seed_data(N)` or `create_users(N)` call.

## Recommended specification corrections before implementation

1. Rewrite the order guarantee so it either proves total order or stops promising stable/repeatable
   pages.
2. Resolve the universal-offset/unavailable-order capability problem and update the parent card's
   universal-three-argument sentence.
3. Replace the single active-argument bit with distinct supplied/material/composition concepts, or
   explicitly qualify the zero/empty identity claims.
4. Correct the parent card's SQL DoD to preserve the existing policy `LIMIT` on omission.
5. Define same-route enforcement across `_db`, routing hints, and router resolution; add an unrouted
   sharded test.
6. Replace impossible zero-advance async-generator `finally` assertions with custom iterator
   `aclose()` witnesses, and keep private exception-note assertions out of ordinary HTTP JSON.
7. Add or explicitly decline a sync iterable `close()` contract.
8. Narrow async-safety language to framework-owned final queryset completion.
9. Decide the `ListArgumentError` export/catch contract.
10. Reconcile nested non-root behavior with the shipped glossary.
11. Describe collection cost as a fixed schema-generic estimate and state the actual untrusted and
    trusted logical window bounds.
12. Make wire-name resolution error-lazy or build-time; document any runtime converter concurrency
    requirement.
13. Clarify that a sealable `QuerySet` subclass is normalized to a plain output, unless rejecting it
    is an intentional breaking decision.
14. Add the missing matrix cases and supported-version CI statement from this review.
15. Prefer a dedicated sync live suite so the field feature remains discoverable and its async twin
    has a clear counterpart.

## Sound decisions to retain

The critical findings do not invalidate the whole design. These decisions are architecturally sound
and should survive the correction pass:

- `offset` and `limit` belong to `DjangoListField`, not Relay connections.
- `orderBy` should reuse `Meta.orderset_class`, `order_input_type`, and public `OrderSet.apply_*`.
- Consumer resolvers should remain `(root, info)`; the factory owns its new arguments.
- Numeric validation should precede consumer resolver side effects.
- Visibility must run before ordering, and the one window must run last.
- Client limits should reject above the effective ceiling rather than silently clamp.
- Trusted return widening must not silently widen the accepted offset coordinate.
- No primary-key tiebreaker or `DISTINCT` should be injected unless the order contract is consciously
  changed.
- Queryset, sequence, sync iterable, and async-only iterable arithmetic belongs in the one resource-
  policy bounding seam.
- The async-only queryset representation is the right way to preserve root optimizer access while
  forcing graphql-core onto async completion.
- Optimizer unwrapping must rewrap every return path, including evaluated and unresolved-type exits.
- The no-argument sync branch should retain exact shipped SQL and resolver behavior.
- Wire-reachable behavior belongs in the fakeshop HTTP tier, with package tests only for genuinely
  unmountable mechanics.

After the blocking decisions and impossible tests are corrected, the specification will have a
coherent implementation path without requiring a second pagination abstraction.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../KANBAN.md

<!-- docs/ -->
[spec-050]: spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[fakeshop-test-query-readme]: ../examples/fakeshop/test_query/README.md
[schema-reload]: ../examples/fakeshop/schema_reload.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
