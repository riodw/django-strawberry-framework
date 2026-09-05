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
  would either double-slice or apply offset after truncating the source.
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

<!-- LINK DEFINITIONS -->

<!-- Root -->
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
