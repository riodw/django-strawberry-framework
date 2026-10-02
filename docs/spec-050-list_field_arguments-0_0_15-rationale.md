# Rationale: spec-050 — DjangoListField argument surface (deliberation and rejected alternatives)

Deliberative companion to [`spec-050-list_field_arguments-0_0_15.md`][spec-050]. The spec is the
contract; this file holds the alternatives each decision rejected and why each lost, and the
derivations that do not change how a decision is implemented.

## How to read this file

- **One entry per spec decision**, with the decision's own heading and anchor, so a citation
  such as "Decision 1's rejected alternatives" resolves to exactly one place.
- **Load-bearing carve-outs.** Two things deliberately stay in the spec even though they
  read like deliberation: the parallel builder module cycle guard in [Decision 1][spec-050-d1]
  (reversing the import edge would close a module cycle between `list_field.py` and `connection.py`),
  and the strict pipeline ordering with mechanical validation in [Decision 5][spec-050-d5]
  (visibility must precede ordering, which must precede slicing). When it is unclear whether a
  sentence is deliberation or instruction, it stays in the spec.

## Deliberation that belonged to no single decision

### Borrowing posture — what was deliberately not borrowed and why

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

The spec keeps each risk and its preferred answer; the fallbacks, should a real consumer need
appear, are:

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
  Fallback for a combined shape the primary-key rewrite cannot represent, should a real consumer
  need it: card that combinator-aware behavior and its SQL matrix explicitly; until then the shape
  fails closed.
- **A review with no admission criterion has no last round:** Fallback if the maintainer wants a
  stricter posture for one surface: card it under the adversarial suite [`GOAL.md`][goal] names
  for `0.1.x`, with its own threat model and its own evidence; a DONE card is not reopened for it.
- **Upstream is retiring the instance spelling Decision 15 reads as a declaration:** Fallback
  when upstream removes instance entries: the ladder row goes with them and no shim re-admits the
  spelling; a consumer on that spelling migrates to the class or factory upstream documents.

## Decision entries

### Decision 1 — synthesize one resolver signature; do not widen consumer resolvers

Spec: [Decision 1][spec-050-d1].

*Alternatives rejected:*

- **Forwarding arguments to consumer resolvers:** Rejected because it would break every existing
  two-parameter resolver (`resolver(root, info)`) and would split the package contract between
  default and consumer fields.
- **Inspecting consumer signatures and forwarding only accepted names:** Rejected because
  behavior would change when a parameter is renamed and because the package, not the consumer,
  must own validation and slice ordering.

### Decision 2 — sidecar-conditional `orderBy` is the only truthful Meta-first surface

Spec: [Decision 2][spec-050-d2].

*Alternatives rejected for `orderBy`:*

- **Auto-generating an `OrderSet` from every model:** Would reverse a standing public decision,
  expose relation and column choices the consumer never approved, and create different ordering
  inputs for the same `DjangoType` depending on which field factory referenced it.
- **A JSON argument:** Would erase schema validation and the discoverable `Ordering` enum.
- **An empty placeholder input / dummy field:** An empty placeholder input is invalid GraphQL,
  while a dummy field or always-rejected enum would publish a capability that cannot succeed.
- **Requiring every `DjangoListField` target to declare `Meta.orderset_class`:** Would be a
  breaking change to the existing pagination-independent field.

*Capability rules rejected for `offset`:*

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

*Alternatives rejected:*

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

*Derivation of coordinate ceilings vs scan budgets and collection-cost fixed estimate:*

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

*Alternatives rejected:*

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

*Derivation on the cost of the third seal:*

- Deep recursive query-graph validation and canonical reconstruction occurs twice in the
  visibility boundary (source and hook result), and a supplied `orderBy` adds a third full walk
  and rebuild of every annotation, subquery, `Prefetch` tree, and expression node. The cost is
  accepted because the alternative is trusting arbitrary public override output, but it is paid
  on every argument-bearing request that supplies an order.

### Decision 6 — nonzero offset requires a materially active order

Spec: [Decision 6][spec-050-d6].

*Alternatives rejected:*

- **Silently accepting unordered offset (Graphene-Django):** Database default order can change
  between requests, query plans, or backends. Graphene-Django's connection accepts offset without
  an ordering precondition, producing nondeterministic results.
- **Silently injecting `order_by("pk")` (Strawberry-GraphQL-Django):** Silently injecting
  primary-key tiebreakers changes SQL and usurps a consumer ordering choice; the no-argument fast
  path additionally must remain byte-identical. Unlike a connection, a list mints no cursor that
  requires a package-owned total order.
- **Classifying a string term from the name as written:** A relation name in a string is not a
  column. [`SQLCompiler.find_ordering_name`][django-compiler] replaces a path ending on a
  relation with the related model's own `Meta.ordering`, so a classifier that stops once a name
  resolves to a field certifies a default it never read and serves a positive offset over a
  result set the database re-shuffles. Reading the name as far as the compiler reads it is the
  same rule the annotation and `extra` steps already follow, one indirection further.
- **Treating a node as transparent because its children are readable:** Django publishes no
  such contract. `Func`, `Transform`, `Aggregate` and `Window` all emit SQL of their own around
  their sources, and any expression can be subclassed with an `as_sql` that emits anything -
  so a rule reading "has source expressions, therefore orders by them" certifies a one-class
  project expression spelling `RANDOM()` over a column, and a project transform registered on a
  built-in field does the same inside a predicate. Both reach the wire through `Meta.ordering`
  and a plain `offset` request. The replacement is an explicit list of approved forms matched by
  exact type, which inverts the exposure: a form nobody listed costs a refused request, where an
  unlisted volatile class cost a silently re-shuffled page. Exact type rather than `isinstance`
  is the load-bearing half - a subclass of a pure function is a different `as_sql` wearing an
  approved name.
- **Reading only the value side of a predicate:** A comparison has two operands and both are
  compiled. A classifier that reads the value alone accepts `When(coin__gt=0.5)` over a random
  alias while refusing `order_by("coin")`, which makes the predicate a spelling that buys what
  the direct one is denied - the guard's rule is about the SQL the rows are ordered by, and a
  bypass reachable by rewriting the same order as a condition is not a narrower rule but a
  missing one.
- **Reading an expression reference through that same expansion:** It is the mirror error, and
  it refuses requests Django answers deterministically. Only strings reach
  `find_ordering_name`; [`Query.resolve_ref`][django-query] resolves an `F` to a column and
  never consults the related model's ordering, so `F("branch").asc()` is the foreign key order
  and classifying it like the string `"branch"` would reject a page over a stable column
  because a model it never orders by declares `Random()`. One resolution rule for both
  spellings is wrong in one direction or the other; the compiler's two rules are the contract.
- **Admitting the two reference forms by `isinstance`:** It leaves the approved list exact
  everywhere except at the two arms that run first. `F` and `Q` carry no `as_sql`, so what a
  subclass of either substitutes is `resolve_expression` - the compiler receives whatever that
  returns, while the classifier is still reading a column name or a set of children that never
  reach the statement. `Meta.ordering = (VolatileF("code"),)` is an ordinary model declaration,
  and `Case(When(VolatileQ(code__gt=...), ...))` wraps the same substitution in a composition
  the spec approves, so both serve a positive offset over a re-shuffled result set. Exact type
  at every arm is one rule; exact type at the arms that happen to be reached last is a boundary
  with a door in it.
- **Deciding a term's form from its own Python type before asking whether it resolves:**
  [`_order_by_pairs`][django-compiler] asks for `resolve_expression` first and reads a term as a
  string only when it has none, so a `str` subclass carrying that method is an expression to
  Django and a field path to a classifier that tests for `str` first. The two readings disagree
  about the whole statement, not about a detail of it. Dispatching in the compiler's own order
  costs nothing and removes the disagreement: a name that resolves is classified as what it
  resolves to.

### Decision 7 — active order is not total order; no pk tiebreaker is appended

Spec: [Decision 7][spec-050-d7].

*Alternatives rejected:*

- **Requiring a provably total order and rejecting unprovable ties:** Infeasible over arbitrary
  Django expressions and backend-dependent even where possible.
- **Appending a deterministic terminal term:** Semantic change to requested order priority that
  would break no-argument SQL parity. Keeping the active-order guard while declining the stronger
  promise makes a unique final term a consumer documentation recommendation rather than framework
  enforcement.

### Decision 8 — queryset and iterable sources have explicit, different capabilities

Spec: [Decision 8][spec-050-d8].

*Alternatives rejected:*

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
  exact queryset this package owns, never through an attribute lookup a subclass answers; a
  subclass source reaches that slot by being rebuilt, and the rebuild brings its rows with it.

*Fact behind the pending-predicate admission:* Django's
`RelatedManager._apply_rel_filters` sets `_defer_next_filter` and then calls
`.filter(**core_filters)`, whose `_filter_or_exclude` stores the `(negate, args, kwargs)` tuple on
`self._chain()` — an object of the CANDIDATE's class. So **every** relation queryset carries a
pending `_deferred_filter`, on an exact `QuerySet` and on a `Manager.from_queryset` class alike
(the same relation built both ways carries the identical tuple). A seal that refused a subclass
carrying that state would refuse a `Manager.from_queryset` relation at the raw-list row source
and at the visibility boundary, and Decision 8's promise that a sealable project queryset class
keeps its `LIMIT` would be unreachable for the relation case. The seal therefore proves the
tuple's values and bakes it onto the detached clone
(`django_strawberry_framework/utils/querysets.py::_bake_deferred_filter_or_defect`).

*Rejected — refusing `Manager.from_queryset` relations as unsupported:* It is the documented way
to give a model its own queryset class, so this refuses ordinary Django on a false premise about
Django. Decision 20 names that shape as standard application code the package answers for.

*Rejected — re-querying the relation instead of carrying its rows:* The cached rows are already
in memory. Re-fetching them costs one query per parent row, and on the prefetched branch of the
generated many-side resolver it returns an unevaluated rebuilt source that graphql-core iterates
on the event loop under async, where Django raises `SynchronousOnlyOperation`. The alternative is
therefore not only a cost: it breaks the async relation outright.

*Failability:* with the carry removed,
`examples/fakeshop/test_query/test_resource_policy_api.py::test_a_project_queryset_class_relation_costs_two_prefetch_queries`
counts 4 queries where it pins 2, and
`examples/fakeshop/test_query/test_resource_policy_api.py::test_a_project_queryset_class_relation_answers_the_same_rows_when_awaited`
answers `data: null`.

*Rejected — mounting the live proof on a shape that never reaches the branch:* replacing the
reverse relation manager's queryset class. The optimizer seeds the generated `Prefetch` child
from the related model's `_default_manager.all()`, and Django's `prefetch_one_level` caches
`manager._apply_rel_filters(lookup.queryset._chain())`, so that mount leaves an exact `QuerySet`
in the cache. Measured: 2 queries and rows returned, identical to the unmounted control — a row
that passes while exercising nothing. The proof mounts the model's default manager instead.

*Rejected — confining the admission to a `_SealPolicy` axis on the raw-list row source:* It would
leave the same project shape refused at the visibility boundary, where it is equally reachable,
so it is a knowingly partial fix. It would also encode two admission rules for one state slot
with no mechanical difference between them: the bake dispatches no candidate code and proves the
same things whichever surface calls it, whereas every existing axis names a real difference (what
the rows are, whether the surface recomposes, which connection, whether the surface demanded the
result). Sealability is one rule, defined once.

*Why the `negate` slot takes an exact-`bool` check:* the bake's contract is that it runs only
genuine Django machinery over pre-proven arguments, and `negate` is the one slot in the tuple that
would otherwise reach consumer code — `~predicate if negate else predicate` truth-tests it, so a
planted object's `__bool__` would decide whether the predicate is negated. Pinning it completes a
proof the `tuple` / `dict` / `list` checks beside it already perform, rather than opening a new
threat model.

### Decision 9 — no-argument sync behavior takes the old branch; async only adapts completion

Spec: [Decision 9][spec-050-d9].

*Derivation of the LIMIT/OFFSET contract:*

- "LIMIT/OFFSET present exactly when supplied" does not describe a raw list: no-argument raw lists
  carry a policy LIMIT through `bounded_rows` ([`spec-047`][spec-047]). The contract is: omission
  preserves the existing policy LIMIT unchanged, a smaller client limit lowers the high mark, and a
  positive offset raises the low mark.

### Decision 10 — coercion errors stay GraphQL-owned; runtime domain errors are package-owned

Spec: [Decision 10][spec-050-d10].

*Alternatives rejected:*

- **A custom stricter integer scalar:** The card explicitly asks for `Int` SDL, and over-ceiling
  validation still needs request context unavailable to scalar coercion.
- **A schema extension rewriting all `Int` coercion errors:** Overbroad and unable to reliably
  identify which argument failed after validation.

### Decision 12 — the version bump belongs to the `0.0.15` joint cut

Spec: [Decision 12][spec-050-d12].

*Derivation:*

- Card 050 targets `0.0.15` alongside 051, 052, and 053. Card 053 ([`spec-053`][spec-053]) owns
  the [joint version cut][glossary-joint-version-cut] and its release documentation; `__version__`
  already reads `0.0.15` for the open development line. Touching version literals in card 050
  would violate the joint-cut protocol.

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

*Rejected:* An architectural rewrite - one `ContextVar`, fresh adapters per
operation, a separately shared optimizer cache, deletion of the membership and refusal
machinery - judged by how much it deletes. The four operation-state modules
(`extensions/operation_state.py`, `utils/private_state.py`, `utils/execution_mode.py`,
`utils/operation_lease.py`) each carry a guarantee ordinary code needs (nesting, concurrency,
streaming resumption, masking the right operation), the regression suite holds those
guarantees, and a rewrite would spend the suite to reach a shape that is smaller by assertion
rather than by evidence. Consolidation follows the DRY flow where
duplication is demonstrated; it is not mandated by line count.

*Rejected:* Dropping the shipped hardening back to a simpler first implementation. It is
simpler partly because it misses failure modes the suite pins.

*Separated, not absorbed — the connection field's sidecar seam.*
The rule this decision's trust table states for application code is that the package validates
mechanically what it can establish about a hook's RESULT, and a hook's result contract does not
depend on which field called it; two fields invoking one public method and validating it
differently is that rule broken. The row at stake is [`spec-030`][spec-030] Decision 7's "later
steps can only narrow" upper bound on the connection pipeline, which an override that widens,
re-routes, pre-evaluates, slices or combines its return would otherwise defeat.

Both sidecar returns run one seal.
[`django_strawberry_framework/utils/querysets.py::apply_orderset_sync`][utils-querysets] /
[`::apply_orderset_async`][utils-querysets], called from both
[`django_strawberry_framework/list_field.py`][list-field] and
[`django_strawberry_framework/connection.py::_pipeline_sync`][connection] /
[`::_pipeline_async`][connection], and `utils/querysets.py::apply_filterset_sync` /
`::apply_filterset_async`, called from both `connection.py` pipelines, all run
`django_strawberry_framework/utils/querysets.py::_apply_sidecar_sync` or its async twin under the
one `_SIDECAR_RESULT_POLICY`. Both fields therefore freeze the same routing intent before the
consumer override receives the queryset and validate what it hands back on the same result
axes - lazy, model rows of the captured model, unsliced, a combinator served as its primary-key
set, same routing - before any
later step, including the Relay window, sees it. The visibility seal runs under the one default
policy on both fields, whether or not a sidecar input is supplied.

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

*Decision:* One candidate implementation commit, one gate and review over that exact tree, and
one evidence-only follow-up commit naming the candidate parent; a finite list of owed work before
the candidate; the candidate carries the final board transition, and closure is recognized only
by the follow-up; a new card rather than a reopened one afterwards.

*Why:* A gate graded at one tree says nothing about the next, so a record that is re-cited beside
later edits is not evidence. The candidate commit gives the suites and review one immutable tree;
the follow-up record can then name that parent without the impossible self-reference of a record
that tries to name its own commit. Running the structural and documentation checks on the
follow-up proves only that evidence record's integrity, not that the full suites ran on it.
Naming the owed work makes the finish line something a reader can check rather than a feeling that
the reviews have stopped. Keeping the pre-candidate checkout WIP while placing the board
transition inside the candidate makes the status change part of the gated tree without pretending
the evidence record already exists. The placement is fixed rather than permitted: the follow-up
changes one file, so a transition the candidate merely might carry is one that no commit in the
sequence is obliged to make.

*Rejected:* Recording the gate after each remediation. Each record certified a tree that the
next edits left behind, and the figures travelled forward beside code they did not cover.

*Rejected:* An open-ended review loop with no admission criterion. Decision 20 supplies the
criterion; this decision supplies the stop.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../GOAL.md

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
[spec-030]: SPECS/spec-030-connection_field-0_0_9.md
[spec-047]: SPECS/spec-047-resource_policy-0_0_14.md
[spec-053]: SPECS/spec-053-boundary_dry_squeeze-0_0_15.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../django_strawberry_framework/connection.py
[list-field]: ../django_strawberry_framework/list_field.py
[utils-querysets]: ../django_strawberry_framework/utils/querysets.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->
[django-compiler]: ../.venv/lib/python3.14/site-packages/django/db/models/sql/compiler.py
[django-query]: ../.venv/lib/python3.14/site-packages/django/db/models/sql/query.py

<!-- External -->
