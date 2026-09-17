# Rationale: spec-050 — DjangoListField argument surface (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-050-list_field_arguments-0_0_15.md`][spec-050]. The spec is the
contract and states only what is currently true; everything that explains **how it got there**
lives here: the alternatives each decision rejected and why each lost, the derivations that do
not change how a decision is implemented, every change a decision has undergone with the review
round that caused it, and every claim a decision once made and may no longer make.

Created by the `docs/builder/BUILD.md` `## Spec rationale extraction` pass. The text below was
**moved** out of the spec, not copied: it exists here and nowhere else.

## How to read this file

- **One entry per spec decision**, with the decision's own heading and anchor, so a citation
  such as "Decision 1's rejected alternatives" resolves to exactly one place.
- **Worker 3 reads this during review** — it stops a reviewer re-raising a settled alternative,
  and is the reasoning the finished implementation is checked against. **Worker 1 owns it** as
  spec custodian and audits it at final verification. **Worker 2 never reads it**: that is the
  point of the move.
- **Append-only during the build.** A new review round's decisions land in the spec; their
  rejected alternatives, derivations, and retractions append here in the same custodian pass.
- Round attribution: Authored for `0.0.15` (card [`WIP-ALPHA-050-0.0.15`][kanban]). Initial
  specification, independent upstream review, audit reconciliation, implementation-contract
  corrections, live-tier compliance review, and blocking architectural review were reconciled
  in place before pre-flight extraction.
- **Load-bearing carve-outs.** Two things deliberately **stayed** in the spec even though they
  read like deliberation: the parallel builder module cycle guard in [Decision 1][spec-050-d1]
  (reversing the import edge would close a module cycle between `list_field.py` and `connection.py`),
  and the strict pipeline ordering with mechanical validation in [Decision 5][spec-050-d5]
  (visibility must precede ordering, which must precede slicing). When it is unclear whether a
  sentence is deliberation or instruction, it stays.

## Change record

### Specification revision history

*Moved from spec header.*

- **2026-09-01**: Specification, independent upstream review, audit reconciliation,
  implementation-contract corrections, live-tier compliance review against
  [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme], and a blocking
  architectural review answered in place. That pass named the order contract ordered offset
  rather than stable pagination, chose and recorded the universal-`offset` capability rule, split
  the single argument-activity bit into four independent fields, made `ListArgumentError` a root
  export, defined same-route as routing INTENT, replaced an impossible zero-advance
  async-generator finalization assertion, declined the sync cleanup contract explicitly, split
  the sync live suite out of the library application suite, and queued two amendments to the
  parent card. The joint-cut ruling moved from Decision 7 to Decision 12 during the earlier review.
- **2026-09-17**: The completion contract. Decisions 20-22 draw the trust boundary (application
  Python trusted, its documented result contracts validated; the wire and configuration bounded),
  adopt Django's own reachability rule as the admission criterion for a finding against this
  card, align the extension contract with upstream's class-or-factory spelling while stating
  per-operation isolation as the guarantee this package adds, and close the card on one recorded
  gate. Decision 8 gains the evaluation-state carry so a project queryset class costs what
  Django's manager costs. The measurements behind the contract: `utils/querysets.py` at 3,380
  lines when this spec was written and 4,294 at this revision; the package at +4,413/-647 lines
  since the recorded gate, concentrated in four new modules
  (`extensions/operation_state.py`, `utils/private_state.py`, `utils/execution_mode.py`,
  `utils/operation_lease.py`) and in `schema.py` and `resource_policy.py`; the suite from 7,868
  to 8,318 rows; the spec's uses of "refuse" from 9 to 30 and of "hostile" from 2 to 9 while the
  public surface of the feature did not move. Those numbers are why the line is drawn where it is.

### Parent card amendments

*Moved from Decisions 2 and 9.*

- **Universal three-argument Scope sentence:** The card body originally specified three optional
  arguments on every `DjangoListField`. However, ordering comes from the target's
  `orderset_class`, which cannot hold for a type without that sidecar. Slice 5 amends that Scope
  bullet in the KANBAN database to state that `offset` and `limit` are universal, `orderBy` is
  sidecar-conditional, and a published `offset` is a runtime-precondition coordinate
  ([Decision 2][spec-050-d2]).
- **Card Definition of done `LIMIT/OFFSET` row:** The card's original phrasing "LIMIT/OFFSET
  present exactly when supplied" is false against shipped behavior: no-argument raw lists already
  carry a policy LIMIT through `bounded_rows` and have since [`spec-047`][spec-047]. Slice 5 amends
  that card DoD row in the KANBAN database to the shipped contract: omission preserves the
  existing policy LIMIT unchanged, a smaller client limit lowers the high mark, and a positive
  offset raises the low mark ([Decision 9][spec-050-d9]).

## Deliberation that belonged to no single decision

### Borrowing posture — what was deliberately not borrowed and why

*Moved from Borrowing posture.*

- **From `graphene-django` connection semantics:** Refuses Relay cursor conversion, `before`
  composition, and connection-wide publication. Graphene pops `offset`, combines it with `after`,
  and converts the result back to a Relay offset cursor; `connection_resolver` additionally
  rejects `before` plus `offset`. Those make a skip look like a cursor while retaining skip
  instability. The package borrows only the discoverable spelling `offset: Int` on the flat-list
  field.
- **From `strawberry-graphql-django` pagination:** Refuses silent max-limit clamp, negative-limit
  unbounded spelling, generated result envelope, decorator surface, and nested raw-list window.
  Upstream's negative spelling reaches an unbounded tail when its maximum-limit clamp is
  disabled, which is the shipped default; when configured, the clamp silently rewrites that
  spelling to the maximum. Both behaviors are refused here. This package has a fail-closed
  resource policy, a Meta-class public API, and connections for nested windows.
- **From this package's connection field:** Refuses importing the connection's filter input,
  total-order tiebreaker, cursor codec, [`ConnectionExtension`][connection], or page-size rules.
  Reuses only the lazy sidecar signature synthesis mechanism and the `order_input_type` helper.

### Risks and open questions — the fallback positions

*Moved from Risks and open questions.* The spec keeps each risk and its preferred answer; the
pre-planned fallbacks, should a real consumer need appear, are:

- **The card's universal-three-argument sentence conflicts with its Meta-derived-order requirement:**
  Fallback if the maintainer insists on literal universal publication: explicitly choose and card
  a dynamic `OrderSet` policy first; do not ship JSON or a dummy input as an invisible workaround.
- **GraphQL coercion errors cannot carry the package runtime code:** Fallback if one code is
  mandatory: a future schema-wide audited error-normalization feature, not a weakened scalar
  local to this field.
- **Active order does not prove uniqueness, so the delivered contract is weaker than the words "stable subset" suggest:**
  Fallback: a future opt-in deterministic list-order policy; never silently append pk in this card.
- **The sync early-exit cleanup contract is declined, not solved:** Fallback once evidence shows
  retained sync generators leak in practice: one shared sync `close()` contract at the same
  bounding seam, carded separately because it changes shipped relation-list behavior.
- **Document collection-cost accounting and the runtime coordinate ceilings are two different budgets and now visibly disagree:**
  Fallback if the divergence becomes unacceptable to the resource-policy threat model: field
  metadata consumed by the walker, with its own evidence; never argument-name matching.
- **Nested `DjangoListField` usage has a shipped glossary promise this card neither keeps nor retracts:**
  Fallback: a deliberate deprecation card that pays the compatibility cost explicitly.
- **`max_list_rows` may be too small as a migration offset ceiling:** Fallback after evidence: add
  a distinct `ResourcePolicy.max_list_offset` bound in a dedicated policy change with its own
  document cost semantics.
- **Ordering an already-sliced consumer queryset is a migration trap:** Fallback: require the
  consumer resolver to return an unsliced base queryset; there is no safe filter/reorder-after-slice
  mode and no identity-hook exception.
- **Arbitrary custom `OrderSet.apply_*` code can discard visibility predicates:** Fallback if a
  future product requires enforcement against consumer code itself: redesign `OrderSet` to return
  a declarative order plan; do not claim predicate-lineage proof from arbitrary Python.
- **Django combined querysets do not compose uniformly with order and optimizer operations:**
  Fallback after Django/optimizer support exists: card the combinator-aware behavior and SQL
  matrix explicitly.
- **A review with no admission criterion has no last round:** Fallback if the maintainer wants a
  stricter posture for one surface: card it under the adversarial suite [`GOAL.md`][goal] names
  for `0.1.x`, with its own threat model and its own evidence; a DONE card is not reopened for it.
- **Upstream is retiring the instance spelling Decision 15 reads as a declaration:** Fallback
  when upstream removes instance entries: the ladder row goes with them and no shim re-admits the
  spelling; a consumer on that spelling migrates to the class or factory upstream documents.

## Decision entries

### Decision 1 — synthesize one resolver signature; do not widen consumer resolvers

Spec: [Decision 1][spec-050-d1].

*Moved — alternatives rejected:*

- **Forwarding arguments to consumer resolvers:** Rejected because it would break every existing
  two-parameter resolver (`resolver(root, info)`) and would split the package contract between
  default and consumer fields.
- **Inspecting consumer signatures and forwarding only accepted names:** Rejected because
  behavior would change when a parameter is renamed and because the package, not the consumer,
  must own validation and slice ordering.

### Decision 2 — sidecar-conditional `orderBy` is the only truthful Meta-first surface

Spec: [Decision 2][spec-050-d2].

*Moved — alternatives rejected for `orderBy`:*

- **Auto-generating an `OrderSet` from every model:** Would reverse a standing public decision,
  expose relation and column choices the consumer never approved, and create different ordering
  inputs for the same `DjangoType` depending on which field factory referenced it.
- **A JSON argument:** Would erase schema validation and the discoverable `Ordering` enum.
- **An empty placeholder input / dummy field:** An empty placeholder input is invalid GraphQL,
  while a dummy field or always-rejected enum would publish a capability that cannot succeed.
- **Requiring every `DjangoListField` target to declare `Meta.orderset_class`:** Would be a
  breaking change to the existing pagination-independent field.

*Moved — capability rules rejected for `offset`:*

- **Publishing `offset` only where a declared order source exists:** Rejected because that source
  may be a model `Meta.ordering` that a consumer resolver clears at runtime, so the argument's
  presence still would not predict its usability — it would move the dishonesty into SDL instead
  of removing it.
- **Accepting a resolver's own `.order_by(...)` as a documented contract:** Rejected because
  hidden order cannot explain to a client why one field accepts offset and an otherwise-identical
  one does not.
- **Explicit Meta-first stable-order declaration:** A genuine third option, but deferred rather
  than refused — it is a new public Meta key, and belongs in its own card with its own parity
  evidence.

### Decision 4 — `max_list_rows` also bounds skip; trusted widening does not

Spec: [Decision 4][spec-050-d4].

*Moved — alternatives rejected:*

- **A dedicated `max_list_offset` setting:** The two limits protect the same raw-list operation,
  the card explicitly prefers deriving the ceiling, and a new setting would add deployment
  surface before evidence shows the limits need to differ.
- **Requiring `offset + limit <= max_list_rows`:** Would make the accepted `limit` depend on
  `offset`, turn an otherwise-valid page into an error as it moves forward, and make the
  explicitly accepted `offset == max_list_rows` useful only with `limit: 0`.
- **Teaching the collection-cost walker to infer semantics from argument spelling (`_collection_rows` name matching):**
  The walker remains schema-generic with no trustworthy marker distinguishing this factory's
  validated `limit` from an unrelated consumer argument of the same name; inferring semantics from
  spelling would undercharge arbitrary lists.

*Moved — derivation of coordinate ceilings vs scan budgets and collection-cost fixed estimate:*

- `max_list_rows` retains a returned/materialized-row meaning on the return dimension and is
  reused as a separate accepted-skip ceiling. Both are accepted coordinate ceilings, not scan
  budgets: they bound what a client may ask for, never what the backend plan does to satisfy it.
  Even a small offset can force a sort or a large scan of a filtered relation, a to-many aggregate
  order can add `GROUP BY`, and high offsets commonly degrade with table size. The request deadline
  does not close that gap either: `check_deadline` is one cooperative pre-fetch check, so it can
  refuse to start a query and cannot interrupt one already dispatched.
- The pre-execution collection-cost walker charge is a schema-generic fixed estimate, not a
  conservative upper bound. It overcharges when a field or a client narrows below the policy, and
  undercharges when positive offset admits up to another `max_list_rows` of logical skip work, or
  when `trusted_max_rows=True` returns more rows than charged. The accepted logical window is still
  bounded (`offset + returned <= 2P` untrusted, `P + F` trusted), but enforced at runtime, not by
  document accounting.

### Decision 5 — validate, then visibility, ordering, and exactly one slice

Spec: [Decision 5][spec-050-d5].

*Moved — alternatives rejected:*

- **Resolved-alias equality as the routing invariant:** Rejected because computing it calls a
  consumer router mid-validation; intent equality (`_db` plus `_hints`) is stricter,
  deterministic, and dispatches no consumer code.
- **A fresh pagination helper that calls `bounded_rows` and then slices:** Rejected because it
  would either double-slice or apply offset after truncating the source. The shipped seam runs
  the other way: `bounded_rows` delegates down to the private window seam, which slices once
  with the bound already known, and nothing sits above the exported helper re-slicing its
  output.
- **In-coroutine list materialization (`many_resolver` pattern):** The generated relation resolver
  in `many_resolver` materializes inside its own coroutine (`[row async for row in bounded]`) and
  hands graphql-core a plain list. That is correct for a relation, which is a leaf of an
  already-planned parent query. It is wrong for a root list: the root plan is applied to the value
  the resolver returns, so materializing before returning would hand `DjangoOptimizerExtension` a
  list with no queryset left to plan, silently dropping root-list optimization on every async
  request while every assertion about rows and SQL still passed.

*Moved — derivation on the cost of the third seal:*

- Deep recursive query-graph validation and canonical reconstruction occurs twice in the
  visibility boundary (source and hook result), and a supplied `orderBy` adds a third full walk
  and rebuild of every annotation, subquery, `Prefetch` tree, and expression node. The cost is
  accepted because the alternative is trusting arbitrary public override output, but it is paid
  on every argument-bearing request that supplies an order.

### Decision 6 — nonzero offset requires a materially active order

Spec: [Decision 6][spec-050-d6].

*Moved — alternatives rejected:*

- **Silently accepting unordered offset (Graphene-Django):** Database default order can change
  between requests, query plans, or backends. Graphene-Django's connection accepts offset without
  an ordering precondition, producing nondeterministic results.
- **Silently injecting `order_by("pk")` (Strawberry-GraphQL-Django):** Silently injecting
  primary-key tiebreakers changes SQL and usurps a consumer ordering choice; the no-argument fast
  path additionally must remain byte-identical. Unlike a connection, a list mints no cursor that
  requires a package-owned total order.

### Decision 7 — active order is not total order; no pk tiebreaker is appended

Spec: [Decision 7][spec-050-d7].

*Moved — alternatives rejected:*

- **Requiring a provably total order and rejecting unprovable ties:** Infeasible over arbitrary
  Django expressions and backend-dependent even where possible.
- **Appending a deterministic terminal term:** Semantic change to requested order priority that
  would break no-argument SQL parity. Keeping the active-order guard while declining the stronger
  promise makes a unique final term a consumer documentation recommendation rather than framework
  enforcement.

### Decision 8 — queryset and iterable sources have explicit, different capabilities

Spec: [Decision 8][spec-050-d8].

*Moved — alternatives rejected:*

- **Short-circuiting `None` after numeric-domain validation:** Capability check outranks null
  propagation; an unsupported argument must not succeed merely because the underlying field
  resolved to `None`.
- **Adding an early-exit `close()` on sync iterators for `0.0.15`:** `bounded_rows` is also the
  shipped bound for every generated relation list; closing a consumer's retained generator would
  be an observable behavior change on callers this card promises not to touch.
- **Directly reading `source.query.is_sliced` or importing the private seal in list field:**
  Would duplicate or weaken the shared hardened classifier in the visibility boundary.
- **Treating `isinstance(value, QuerySet)` as proof that the package owns the slice:** It is not
  a proof of anything. `isinstance` falls back to the value's own `__class__`, so a non-queryset
  can select the SQL-slice arm; and even when the answer is true, the subscript that follows is
  the subclass's `__getitem__`. The universal raw-list ceiling was then a call the bounded
  object decided the result of, reachable through a real relation over a real request.
- **Exact type plus `islice` as the whole fix:** Restores the row ceiling and loses the SQL one.
  A project queryset class returned by a custom manager is ordinary Django, and demoting every
  one of them to a counted Python truncation would fetch the whole relation to discard its tail
  - trading a wire-level bound for a database-level regression.
- **Rejecting every `QuerySet` subclass outright:** `Manager.from_queryset` and
  `QuerySet.as_manager` are the documented way to give a model its own queryset class, so this
  would refuse ordinary Django. The seal already answers the real question - can this state be
  faithfully rebuilt - and only the states it cannot rebuild fail closed.
- **A second, cheaper rebuild primitive for this seam:** Two rebuilds proving different things
  is how one of them comes to prove less. The shared sealer is reused with its own policy
  instead, switching off only the axes that guard a RECOMPOSITION, because nothing recomposes
  here - one `[start:stop]` is taken, and Django takes it on a sliced query and on a combinator
  alike.
- **Running the full seal on every source:** The exact queryset is the common case by an
  enormous margin, and a per-parent-row recursive validation would turn nested relation lists
  into an N+1 validation cost for a rebuild that would return an equivalent object. It is
  returned unchanged instead, and only the untrusted shape pays.
- **Reading the relation cache's `_result_cache` with `getattr` after normalizing:** The read is
  the same consumer dispatch point the slice was. The rows come out of Django's own slot on an
  exact queryset or not at all; a subclass answers no cached rows and costs one query.

### Decision 9 — no-argument sync behavior takes the old branch; async only adapts completion

Spec: [Decision 9][spec-050-d9].

*Moved — derivation of card DoD amendment:*

- The card's original Scope and Definition of done phrasing ("LIMIT/OFFSET present exactly when
  supplied") was false against shipped behavior: no-argument raw lists already carry a policy
  LIMIT through `bounded_rows` since [`spec-047`][spec-047]. Slice 5 amends the card DoD row in
  the KANBAN database to state the shipped contract: omission preserves the existing policy
  LIMIT unchanged, a smaller client limit lowers the high mark, and a positive offset raises the
  low mark.

### Decision 10 — coercion errors stay GraphQL-owned; runtime domain errors are package-owned

Spec: [Decision 10][spec-050-d10].

*Moved — alternatives rejected:*

- **A custom stricter integer scalar:** The card explicitly asks for `Int` SDL, and over-ceiling
  validation still needs request context unavailable to scalar coercion.
- **A schema extension rewriting all `Int` coercion errors:** Overbroad and unable to reliably
  identify which argument failed after validation.

### Decision 12 — the version bump belongs to the `0.0.15` joint cut

Spec: [Decision 12][spec-050-d12].

*Moved — derivation:*

- Card 050 targets `0.0.15` alongside 051, 052, and 053. Card 053 ([`spec-053`][spec-053]) owns
  the [joint version cut][glossary-joint-version-cut], release documentation, and `__version__`
  edit. Touching version literals in card 050 would violate the joint-cut protocol.

### Decision 13 — graphql-core workarounds have a dependency-owned lifecycle

Spec: [Decision 13][spec-050-d13].

*Decision:* Put the `ExecutionContext.complete_list_value` delegator in its own
`_graphql_core_patches.py` module and gate it with the canonical `graphql_core` dependency key.

*Why:* The patched callable, upstream release cadence, retirement signal, and consumer opt-out
all belong to graphql-core. Strawberry happens to invoke that executor, but its HTTP-view patch
has a different owner and a different retirement condition. One module and gate per patched
dependency keeps disabling or retiring either workaround from silently changing the other.

*Rejected:* Keeping the executor wrapper in `_strawberry_patches.py` because graphql-core is a
transitive Strawberry dependency. That makes dependency topology decide lifecycle ownership,
couples unrelated escape hatches, and lets an HTTP-view opt-out restore an executor bug.

### Decision 14 — configuration authority is schema state; everything per-request is operation state

Spec: [Decision 14][spec-050-d14].

*Rejected:* Holding per-operation state on the extension instance. Strawberry resolves two of
the three accepted entry spellings to the SAME object for every operation, so one slot is
written by two requests: a nested `info.schema.execute_sync(...)` leaves the inner document in
it, and two overlapping requests leave whichever assigned last. The charge then lands on a
benign document while the oversized one executes, and the mask lands on a result that is not
the one going to the client.

*Rejected:* Making the engine's `execution_context` assignment the authority. It would have to
survive a consumer entry's setter raising midway through that loop - a failure with no package
teardown to run, because no runner exists yet - and it is writable from a resolver, which can
forge a context naming the real schema as often as it likes.

### Decision 15 — an enforcement authority is a declaration, never an extension entry

Spec: [Decision 15][spec-050-d15].

*Rejected:* Deduplicating by identity - accepting an entry that IS the package's extension and
dropping the automatic one. Identity evidence authenticates the object, not what it will do on
the next operation, and the three spellings that keep identity while changing behavior (a
stateful factory, a closure over a mutable cell, a singleton selector) are exactly the ones a
resolver can reach through `info.schema.extensions`.

*Rejected:* Admitting a subclass on the grounds that it passes every inheritance check. That is
the point: a single-role subclass can override the one hook that masks or charges while
answering every census correctly, and one class can inherit from both roles, in which case
method resolution runs one hook and the other authority is present in name only.

*Rejected:* Calling factories at construction so they could be typed there. It breaks the
fresh-per-operation lifecycle the optimizer's documented singleton-in-a-factory depends on, and
what a factory returns next is decided after the entry was accepted anyway.

### Decision 16 — the runner owns every binding, for the operation's whole lifetime

Spec: [Decision 16][spec-050-d16].

*Rejected:* A plain `ContextVar` holding the state, with token reset as the whole protocol.
`asyncio.create_task` copies the context at creation and a token reset rewrites only the
context the token was made in, so a resolver's background task outliving the request goes on
reading the finished operation's context, variables and result - and holds them alive. The lease
is what a copied context observes instead.

*Rejected:* Binding only around the operation scope. Upstream collects extension results AFTER
the synchronous operation teardown has unwound, and drives a streamed operation's frames from
whatever task holds the iterator, so both would read for no operation at all.

*Rejected:* Promising the raw-`strawberry.Schema` path the same isolation. That schema never
calls the package's runner factory, so the guarantee would be a claim with nothing behind it
for a shared instance; a class entry and a fresh factory are operation-local there because the
object is.

### Decision 17 — a refused request's document, selector and transport policy are all package-owned

Spec: [Decision 17][spec-050-d17].

*Rejected:* Publishing the refusal after the parse. It would make the claim true only of
documents that happen to be well formed: a syntax error is raised out of the parse itself and
upstream answers with it before any statement after the hook's `yield` runs.

*Rejected:* Copying the requested operation name onto the substitute document when it matches
GraphQL's `Name` grammar. That leaves the request's own name authoritative for upstream's
lookup for every name that does not match - and for one that does but names no operation - so
the refusal is replaced by an operation-lookup failure raised out of the synchronous API, or
rendered into the first frame of a stream.

*Rejected:* Parsing a fresh substitute document per refused request. The refusal exists so a
broken deployment runs nothing; a parser it runs on its own constant is still a parser running,
and nothing validates or executes the substitutes, so one object per operation type answers
every refused request of that type.

*Rejected:* Reading the transport policy where the substitute is selected and leaving the
caller's object in place for upstream. `allowed_operation_types` is annotated
`Iterable[OperationType]`, a generator is a valid value for it, and a healthy operation consumes
it exactly once - so the refusal became the second consumer and upstream read an exhausted
iterable.

*Rejected:* `allowed = value or ()` as the normalization. Truthiness is a consumer-defined
dunder invoked on the request path of a schema already known to be broken, and it contradicts
the no-truthiness posture the accepted-entry reader takes one function away.

### Decision 18 — the refusal is stable, and the transport's own policy is the one exception

Spec: [Decision 18][spec-050-d18].

*Rejected:* Dropping the resource extension from the refused chain because "nothing runs
anyway". The refusal is a statement about a document that already arrived; the pre-parse token
and depth scan is the only thing between an unauthenticated caller and graphql-core's recursive
parser, so a broken configuration would have traded fail-closed for an endpoint with no ceiling.

*Rejected:* Appending `QUERY` to an empty transport policy, substituting the default set, or
catching the operation-type refusal. A transport that allows nothing is a deployment decision,
and widening it would make a broken configuration the one shape that accepts what the transport
forbids.

*Rejected:* Interpolating the refused name, document text or factory exception into the
published message. Those are consumer strings whose own `__repr__` is consumer code; the wire
gets the stable code and the deployment's log gets the description.

### Decision 19 — execution mode is operation state; the ambient event loop is a different fact

Spec: [Decision 19][spec-050-d19].

*Rejected:* Keeping `strawberry.utils.inspect.in_async_context` as the dispatch predicate. It
answers whether a loop is running in this thread, which is the right question for ORM safety and
the wrong one for executor dispatch; the two disagree precisely where the package supports
nesting a synchronous operation inside an asynchronous one.

*Rejected:* A list-field-local `ContextVar`. The same false predicate sits in every sibling
field factory and relation resolver, so a field-local fix would leave two definitions of
execution color in the package and the defect in all the other ones.

*Rejected:* Blocking the event-loop thread - taking the synchronous branch under a running loop
and letting Django raise. The error names none of the cause, arrives from the ORM rather than
from the call that caused it, and a partially completed operation is worse than a refusal.

*Rejected:* Falling back to the synchronous branch silently when the mode is unknown. The one
place the mode is unknown is a plain `strawberry.Schema`, where ambient dispatch is what
upstream already does and what the documented spelling relies on; inventing a different answer
there would change a working path for schemas the runner was never asked to own.

*Derivation:* The `sync` flag `get_extensions` receives is the authoritative statement -
`execute_sync` is the only entry point that sets it, and `execute`, `stream` and `subscribe` all
leave it false. Nothing upstream carries that flag from `get_extensions` to
`create_extensions_runner`, and recording it on the schema would be the one-slot-two-operations
defect Decision 14 exists to close, so it travels as a member of the chain built for that one
operation.

### Decision 20 — application code is trusted, the wire is not; a finding is admitted by reachability

Spec: [Decision 20][spec-050-d20].

*Decision:* Adopt Django's reachability rule as this package's own admission criterion, name the
three trust levels, and keep the shipped hardening for the ordinary-mistake class it guards.

*Why:* The hardening had a legitimate job each time - cross-request error disclosure, a budget
charged to the wrong document, a nested operation corrupting the optimizer's frame, a bound
read from an object a resolver could overwrite - and each of those is reachable from ordinary
application code under ordinary load. What had no finish line was the threat model: once a
consumer's own Python counts as an adversary, every repair of one construction exposes the next
(a `__class__` that lies, a `__getitem__` that ignores its slice, a `__bool__` that raises), and
the spec grows a refusal vocabulary faster than the feature grows. Django's security policy
already draws the line this package needs, and a package running on Django cannot honestly
promise more than Django does about code inside the same process.

*Rejected:* Treating application Python as hostile. It is unenforceable - in-process code can
import, monkeypatch and rebind any package name - so every check it motivates is a check the
adversary it imagines steps around, and each one costs a real consumer a refusal path to learn.

*Rejected:* An architectural rewrite before DONE - one `ContextVar`, fresh adapters per
operation, a separately shared optimizer cache, deletion of the membership and refusal
machinery - judged by how much it deletes. The four new modules each carry a guarantee ordinary
code needs (nesting, concurrency, streaming resumption, masking the right operation), the
regression suite holds those guarantees, and a rewrite would spend the suite to reach a shape
that is smaller by assertion rather than by evidence. Consolidation follows the DRY flow where
duplication is demonstrated; it is not mandated by line count.

*Rejected:* Dropping the shipped hardening back to the feature as first implemented. The
original was simpler partly because it missed failure modes the suite now pins.

### Decision 21 — the extension contract is upstream's; per-operation isolation is the guarantee this package adds

Spec: [Decision 21][spec-050-d21].

*Decision:* Document upstream's class-or-factory spellings, inherit upstream's deprecation of
the instance spelling, and state per-operation isolation of the package's own extensions as an
addition this package owns and tests.

*Why:* The optimizer recipe in [`GOAL.md`][goal] and the shipped docs is a singleton inside a
factory - exactly the shape upstream's guide warns shares request state. The runner makes that
shape safe for the package's extensions, which is a guarantee worth stating as this package's
own; presenting it as upstream behavior would be false, and presenting instance entries as a
package-defined declaration would build on a spelling upstream is removing.

*Rejected:* Package-defined instance semantics beyond the compatibility reading. A meaning of
`extensions=[MyExtension()]` that only `DjangoSchema` has is a migration trap on the day upstream
drops the spelling.

*Rejected:* Presenting "move the authority instance into a factory" as the migration off the
deprecated spelling. Decision 15 refuses a factory that resolves to an authority, so that advice
would walk a consumer from a working compatibility path into a refused operation; the migration
is the `resource_policy=` / `error_policy=` keyword, which is where enforcement is declared.

*Rejected:* Authenticating or containing a third-party extension's object graph. Its lifecycle is
upstream's, its attributes are its author's, and the package can no more make them thread-safe
than it can make a resolver's globals thread-safe. The package isolates what it wrote.

*Already settled elsewhere:* Reusing upstream's `MaxTokensLimiter`, `MaxAliasesLimiter` and
`QueryDepthLimiter` instead of the package's one extension is answered in
[`spec-047`][spec-047]'s borrowing posture and is not reopened here.

### Decision 22 — the card closes on one recorded gate; a closed contract reopens only for a broken row

Spec: [Decision 22][spec-050-d22].

*Decision:* One gate, one tree, one record naming the commit; a finite list of owed work before
it; a new card rather than a reopened one afterwards.

*Why:* A gate graded at one tree says nothing about the next, so a record that is re-cited beside
later edits is not evidence. Recording once at the final tree is the only record that certifies
the code it names, and naming the owed work makes the finish line something a reader can check
rather than a feeling that the reviews have stopped.

*Rejected:* Recording the gate after each remediation. Each record certified a tree that the
next edits left behind, and the figures travelled forward beside code they did not cover.

*Rejected:* An open-ended review loop with no admission criterion. Decision 20 supplies the
criterion; this decision supplies the stop.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md

<!-- docs/ -->
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[spec-050]: spec-050-list_field_arguments-0_0_15.md
[spec-050-d1]: spec-050-list_field_arguments-0_0_15.md#decision-1--synthesize-one-resolver-signature-do-not-widen-consumer-resolvers
[spec-050-d2]: spec-050-list_field_arguments-0_0_15.md#decision-2--sidecar-conditional-orderby-is-the-only-truthful-meta-first-surface
[spec-050-d4]: spec-050-list_field_arguments-0_0_15.md#decision-4--max_list_rows-also-bounds-skip-trusted-widening-does-not
[spec-050-d5]: spec-050-list_field_arguments-0_0_15.md#decision-5--validate-then-visibility-ordering-and-exactly-one-slice
[spec-050-d6]: spec-050-list_field_arguments-0_0_15.md#decision-6--nonzero-offset-requires-a-materially-active-order
[spec-050-d7]: spec-050-list_field_arguments-0_0_15.md#decision-7--active-order-is-not-total-order-no-pk-tiebreaker-is-appended
[spec-050-d8]: spec-050-list_field_arguments-0_0_15.md#decision-8--queryset-and-iterable-sources-have-explicit-different-capabilities
[spec-050-d9]: spec-050-list_field_arguments-0_0_15.md#decision-9--no-argument-sync-behavior-takes-the-old-branch-async-only-adapts-completion
[spec-050-d10]: spec-050-list_field_arguments-0_0_15.md#decision-10--coercion-errors-stay-graphql-owned-runtime-domain-errors-are-package-owned
[spec-050-d12]: spec-050-list_field_arguments-0_0_15.md#decision-12--the-version-bump-belongs-to-the-0015-joint-cut
[spec-050-d13]: spec-050-list_field_arguments-0_0_15.md#decision-13--graphql-core-workarounds-have-a-dependency-owned-lifecycle
[spec-050-d14]: spec-050-list_field_arguments-0_0_15.md#decision-14--configuration-authority-is-schema-state-everything-per-request-is-operation-state
[spec-050-d15]: spec-050-list_field_arguments-0_0_15.md#decision-15--an-enforcement-authority-is-a-declaration-never-an-extension-entry
[spec-050-d16]: spec-050-list_field_arguments-0_0_15.md#decision-16--the-runner-owns-every-binding-for-the-operations-whole-lifetime
[spec-050-d17]: spec-050-list_field_arguments-0_0_15.md#decision-17--a-refused-requests-document-selector-and-transport-policy-are-all-package-owned
[spec-050-d18]: spec-050-list_field_arguments-0_0_15.md#decision-18--the-refusal-is-stable-and-the-transports-own-policy-is-the-one-exception
[spec-050-d19]: spec-050-list_field_arguments-0_0_15.md#decision-19--execution-mode-is-operation-state-the-ambient-event-loop-is-a-different-fact
[spec-050-d20]: spec-050-list_field_arguments-0_0_15.md#decision-20--application-code-is-trusted-the-wire-is-not-a-finding-is-admitted-by-reachability
[spec-050-d21]: spec-050-list_field_arguments-0_0_15.md#decision-21--the-extension-contract-is-upstreams-per-operation-isolation-is-the-guarantee-this-package-adds
[spec-050-d22]: spec-050-list_field_arguments-0_0_15.md#decision-22--the-card-closes-on-one-recorded-gate-a-closed-contract-reopens-only-for-a-broken-row

<!-- docs/SPECS/ -->
[spec-020]: SPECS/spec-020-list_field-0_0_7.md
[spec-028]: SPECS/spec-028-orders-0_0_8.md
[spec-030]: SPECS/spec-030-connection_field-0_0_9.md
[spec-047]: SPECS/spec-047-resource_policy-0_0_14.md
[spec-053]: SPECS/spec-053-boundary_dry_squeeze-0_0_15.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../django_strawberry_framework/connection.py

<!-- tests/ -->

<!-- examples/ -->
[fakeshop-test-query-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
