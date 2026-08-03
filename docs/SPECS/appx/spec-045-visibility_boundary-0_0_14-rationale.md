# Rationale: sealed `get_queryset` visibility-boundary policy artifacts (spec-045)

The deliberative layer of [`docs/SPECS/spec-045-visibility_boundary-0_0_14.md`][spec]. The spec
states the contract the [visibility boundary][glossary-visibility-boundary] offers today
and nothing else; this file carries, for each of that spec's numbered decisions, the
alternatives that were rejected and why each lost, every change the decision has
undergone with the round that caused it, and any claim the decision once made and may no
longer make.

Every entry names its spec decision by heading text and anchor, so a reader working
through the spec can look the deliberation up and a reviewer cannot re-litigate a settled
alternative without first reading why it lost.

## Provenance of this record

Two kinds of text sit below, and the distinction matters when auditing it:

- **Moved** — text cut out of the spec in this pass because it was deliberation or
  chronology living in a contract. Each moved passage is marked *(moved from the spec)*
  at its entry.
- **Reconstructed** — deliberation that was never written down in a durable place and is
  rebuilt here from primary sources: the boundary's commit messages and diffs, the
  adversarial-review documents as they stood at those commits (read read-only out of git
  history; the review documents themselves are transient maintainer artifacts and are not
  named here), the surviving docstrings in
  [`django_strawberry_framework/utils/querysets.py`][querysets], and the test names in
  [`tests/utils/test_querysets.py`][queryset-tests] that pin each claim. Each such passage
  is marked *(reconstructed)*.

Nothing here is inferred from the shape of the code alone. Where the record supports that
a round established something but does not say which round, this file says so rather than
inventing an index.

## Round chronology

The boundary's current contract is the product of five adversarial review rounds plus one
architectural root fix. **Only the first three carry an index in any surviving record** —
the retained root note (`get_queryset-visibility-boundary-plan.md`, deleted after it was
superseded) named itself the first-round review and named a second and a third. The two
later rounds are unindexed anywhere; they are identified below by their subject and date,
never by a manufactured number.

| Round | Landed | What it established |
|---|---|---|
| First-round review | `1dd9273a`, 2026-07-17 | An async connection-field residual awaitable skipped visibility; cross-model combined querysets were accepted; an evaluated-result refresh changed the hook-selected database alias. |
| Second-round review | folded into `60998b17` | The method inventory is the wrong abstraction — the leak vector is query STATE and runtime dispatch, not the class's declared methods. Drove the sealed-execution rearchitecture. |
| Third-round review (2026-07-18) | `60998b17`, 2026-07-20 | Four `[P1]` findings + one `[P2]` correctness finding + one `[P2]` policy-artifact finding. Produced spec Decisions 1-6. |
| Raw-SQL round | `49b66922`, 2026-07-21 | Raw-SQL payloads Django hands straight to the adapter (`RawSQL.params`, `ExtraWhere.sqls` / `params`, `Query.extra` / `_extra_select_cache`) were unvalidated. |
| Four-finding round | `bbd216fc`, 2026-07-30 | Expression-owned state must be validated before a genuine accessor reads it; retained container PAYLOADS, not only keys, must be validated; a reference cycle must be rejected rather than accepted as a shared diamond; `_concrete_or_none` must require an actual model class. |
| Canonical-reconstruction root fix | `dfa86f90`, 2026-07-30 | A proven-then-retained node is still the candidate's object, so the sealed query was mutable after sealing. Produced spec Decision 8's reconstruction half. |

Two facts about the chronology are load-bearing for anyone editing the spec:

- The retained root note attributed the first round's fixes to `80527a36`. `git log
  --follow` on [`django_strawberry_framework/utils/querysets.py`][querysets] shows the
  boundary changes in `1dd9273a`, and `80527a36` is an adjacent same-day optimizer commit.
  The note's attribution was wrong; the date it implies was right.
- The comment-hygiene sweep of 2026-07-30 (`ff65666d`, `5a74d803`, `471d4c6b`) normalized
  every in-code review citation to the form `spec-045 Decision N`. There are dozens of
  such citations across [`django_strawberry_framework/utils/querysets.py`][querysets],
  [`django_strawberry_framework/optimizer/walker.py`][walker], and
  [`tests/utils/test_querysets.py`][queryset-tests]. **Decision numbers are therefore a
  package-wide identifier**: renumbering a decision is a source-wide rename, not a
  documentation edit. This is why the reconciliation pass corrected decision bodies in
  place and renumbered nothing.

## Decision 1 — The hook and source objects are untrusted query state, rebuilt into a framework-owned plain `django.db.models.QuerySet`

Spec decision:
[Decision 1][spec-decision-1]
(`#decision-1--the-hook-and-source-objects-are-untrusted-query-state-rebuilt-into-a-framework-owned-plain-djangodbmodelsqueryset`).

**Alternatives rejected.**

- *Keeping the class-level method inventory and returning the consumer object.* Lost to
  zero-SQL probes run by the second- and third-round reviews: an instance-shadowed
  `.all()`, a replaced instance-level `Query.chain`, and subclass `.filter()` / `_values`
  / `.first()` / `.__aiter__()` overrides each erased the visibility predicate or returned
  synthetic rows *after* a class-level inventory had accepted the object. A finite
  inventory can only ever enumerate the overrides it already knows about, and the vector
  is the object's runtime dispatch. *(moved from the spec)*
- *Blacklisting the specific override names the probes used.* Rejected in the third
  round's own required-fix wording: "Do not fix only the literal `chain` name. Any
  instance-level method shadow copied into a mutable execution object recreates the same
  abstraction error." The contract is therefore structural — any `__dict__` key naming a
  callable class attribute — and never a name list. *(reconstructed)*

**Changes the decision has undergone.**

- *Third-round review, `60998b17`.* The decision is that round's product; there is no
  earlier version of it.
- *Four-finding round, `bbd216fc`.* The retained `QuerySet.__dict__` fields the seal
  carries forward (`_db`, `_hints`, `_fields`, `_sticky_filter`, `_for_write`) gained an
  exact-shape gate, [`::_queryset_state_defect`][querysets], because each is later
  subjected to truthiness, a comparison, or a `dict` copy — a consumer `__bool__` /
  `__eq__` / `__iter__` in one of those slots dispatches mid-seal even though the field
  was read out of `__dict__` without dispatch. Reading state without dispatching is not
  the same as *using* it without dispatching, and the original decision conflated the
  two. *(reconstructed)*

**Claims it may no longer make.**

- The decision's "reads that state from the instance `__dict__` … so nothing can run code
  or lie during extraction" is true of extraction and was once read as covering the whole
  seal. It does not: see the `_queryset_state_defect` change above. The spec now states
  the exact-shape gate alongside the non-dispatching read.

## Decision 2 — Fail-closed prove-then-clone AST trust

Spec decision: [Decision 2][spec-decision-2] (`#decision-2--fail-closed-prove-then-clone-ast-trust`).

**Alternatives rejected.**

- *Trusting `type(node).__module__.startswith("django.")` as provenance.* Lost because
  `__module__` is a plain writable class attribute: a consumer class declaring
  `__module__ = "django.evil"` spoofed it outright. Provenance is object identity against
  `sys.modules[module].<qualname>` instead. *(moved from the spec)*
- *Assuming `sql.Query.clone` is dispatch-free, so that proving the outer `Query` type is
  enough.* Disproved by reading Django's own `Query.clone` body: it shallow-copies the
  source `__dict__`, calls `self.where.clone()`, calls `.copy()` on the retained
  containers, `deepcopy`s `select_related`, and defers `as_sql` to compile time. A
  zero-SQL probe kept the outer query exactly `sql.Query`, replaced only its `where` with
  a `WhereNode` subclass whose `clone()` returned an empty node, and watched the
  visibility predicate vanish from the queryset the boundary returned. *(moved from the
  spec)*
- *Supporting consumer-defined expressions and lookups behind a vetted allowlist.* Raised
  by the third-round review as one of two acceptable answers ("If the package
  intentionally supports consumer-defined expressions/lookups, narrow the documented
  guarantee accordingly and establish a safe, explicit extension protocol"). The other
  answer was taken: the guarantee is narrowed and a genuinely custom `Func` or `Lookup`
  fails closed as `untrusted`. An allowlist lost on cost — it is a per-type audit surface
  that grows with every consumer expression and buys a capability a consumer can already
  reach by expressing the predicate through genuine Django primitives. A future allowlist
  of vetted consumer expression types remains the named fallback if that constraint ever
  proves too tight. *(moved from the spec's former "Risks and open questions")*
- *Extending the walk one dispatch site at a time as each new one is reported.* Rejected
  in favour of canonical reconstruction; the argument is recorded under Decision 8.

**Changes the decision has undergone.**

- *Third-round review, `60998b17`.* Original form: prove every compiler-reachable node
  genuine and unshadowed, prove every cloned container an exact builtin, then clone.
- *Raw-SQL round, `49b66922`.* The walk did not reach the payloads Django hands straight
  to the adapter. `RawSQL.params`, `ExtraWhere.sqls` / `params`, and the `Query.extra` /
  `_extra_select_cache` entries were added under the same exact-inert-shape rule
  ([`::_raw_sql_params_defect`][querysets], [`::_raw_sql_node_defect`][querysets],
  [`::_raw_sql_sequence_defect`][querysets]), so a hostile SQL object or parameter cannot
  defer its dispatch to compilation or backend adaptation. This round shipped with a few
  negative branches on the new helpers uncovered — the suite sat at 99.95% — by explicit
  maintainer direction; the module is back under the `fail_under = 100` gate.
- *Four-finding round, `bbd216fc`.* Three separate corrections to the walk:
  - Calling a genuine accessor is not dispatch-free, because the accessor reads
    consumer-controlled state. Django's exact `Case.get_source_expressions()` expands
    `[*self.cases, self.default]`, so a `list` subclass planted in `cases` runs its own
    iterator *during the proof* — after the outer `where` tree has already been accepted,
    which is early enough for that iterator to rewrite the accepted tree before
    `sql.Query.clone` runs. Every slot a genuine accessor iterates, unpacks, or slices is
    now pinned to the exact builtin sequence before the accessor is invoked
    ([`::_expression_state_defect`][querysets]).
  - Container type and keys are not the container's shape. `Query.clone`'s `.copy()`
    calls are shallow, so every payload object inside a retained container survives into
    the sealed query. An `int` subclass stored as an `alias_refcount` value has its
    arithmetic invoked by ordinary downstream `.filter()` composition, through
    `Query.ref_alias` / `unref_alias`, and that callback can rewrite the sealed `where`
    tree before the new predicate is added — dropping the visibility predicate from a
    queryset that had already passed the seal. Payloads are now pinned to their complete
    Django shape ([`::_query_payload_defect`][querysets]).
  - One `seen` identity set cannot distinguish a completed shared node from a node
    currently being visited, so a self-referential list, dict, `Q`, or expression graph
    was accepted as trusted. Django never produces a cyclic query graph, and cloning or
    compiling one resurfaces as a raw `RecursionError` past the typed contract. The walk
    became three-state ([`::_GraphWalk`][querysets], [`::_WalkState`][querysets],
    [`::_walk_short_circuit`][querysets]): a node reached while still active is an
    `untrusted` cycle, a node reached after complete validation is a legitimate shared
    diamond. The two tests that had asserted `None` for a self-referential graph were
    re-pinned to require a typed defect.
- *Canonical-reconstruction root fix, `dfa86f90`.* The proof stayed; what follows it
  changed. See Decision 8.

**Claims it may no longer make.**

- **The decision may no longer describe the proven clone as the end state.** Until
  `dfa86f90` the sealed query *was* the candidate's object graph, proven safe and then
  shallow-cloned. It is now a framework-owned rebuild: the clone is canonically
  reconstructed before it is handed back. A reader who takes prove-then-clone as the whole
  seal will conclude the sealed query shares the candidate's leaves, which was true and is
  not. The spec's Decision 2 now names reconstruction as the step that follows the proof
  and points at Decision 8 for it.
- The decision's earlier framing treated an exact `str` / `int` / `datetime` subclass as
  a potential *node* requiring genuine-Django provenance. That is still how the inert-leaf
  test works ([`::_is_inert_value`][querysets] is exact-type, deliberately), but a direct
  lookup right-hand side is now admitted on plain-data *ancestry* and normalized rather
  than rejected — see Decision 8. The two rules are not in conflict, and the spec now
  distinguishes them explicitly, because reading only Decision 2 previously implied that
  binding a `TextChoices` member to a visibility filter failed closed. It does not.

## Decision 3 — The identity fast path is removed; hook results are always re-sealed and result caches dropped

Spec decision:
[Decision 3][spec-decision-3]
(`#decision-3--the-identity-fast-path-is-removed-hook-results-are-always-re-sealed-and-result-caches-dropped`).

**Alternatives rejected.**

- *Keeping `result is queryset` as a performance shortcut.* Lost to a read-only probe: an
  empty source query, an unsaved private object inserted into the received queryset's
  `_result_cache`, and that same queryset returned. The sync boundary returned it verbatim
  and normal iteration served the synthetic row without executing the empty SQL. Object
  identity proves that no *other* object was returned; it proves nothing about the object,
  which the hook has held and can mutate. *(moved from the spec)*
- *Restricting the fast path to a provably unoverridden package-default hook.* Offered by
  the third-round review as a conditional ("If a performance fast path is retained,
  restrict it to a provably unoverridden package default hook and prove that no consumer
  code ran between source sealing and return"). Not taken: the proof obligation is larger
  than the second seal it would save, and the boundary already pays the seal cost on the
  source side. *(reconstructed)*
- *Copying `_known_related_objects` forward for correctness.* Rejected: a fresh fetch is
  always correct, whereas copying an untrusted related-object cache could pre-seed
  synthetic related instances that bypass the related type's own visibility hook. The
  cache is optional state, so dropping it costs nothing but a refetch. *(reconstructed
  from [`::_seal_or_defect`][querysets] #"Reproduce exactly what")*

**Changes the decision has undergone.**

- *Third-round review, `60998b17`.* The decision is that round's product. The tests that
  had asserted the identity shortcut were replaced with sync and async
  mutate-and-return-the-same-object regressions across the sensitive state families.
- No later round has touched it.

**Claims it may no longer make.** None. The decision as the spec states it is what the
code does: [`::apply_type_visibility_sync`][querysets] and
[`::apply_type_visibility_async`][querysets] each carry the "No identity fast path"
comment and route unconditionally through [`::_normalized_visibility_result`][querysets],
and the rebuild in [`::_seal_or_defect`][querysets] copies neither `_result_cache` nor
`_known_related_objects`.

## Decision 4 — `Prefetch` rebuild as an exact Django class + alias threading with `require_shared_alias`

Spec decision:
[Decision 4][spec-decision-4]
(`#decision-4--prefetch-rebuild-as-an-exact-django-class--alias-threading-with-require_shared_alias`).

**Alternatives rejected.**

- *Copying the consumer `Prefetch` instance forward after validating its path state.*
  Lost because a `Prefetch` subclass overriding `get_current_querysets` substitutes an
  unsealed child queryset at *fetch* time, long after any instance-level validation ran. A
  read-only probe watched a `HostilePrefetch("items")` survive the seal as
  `HostilePrefetch` with its override intact. *(moved from the spec)*
- *Rebuilding only the `queryset is not None` case.* This was the pre-fix behavior, not a
  considered alternative, and the third round named it as the defect: a consumer
  `Prefetch` subclass with `queryset=None` was appended unchanged. Every entry is rebuilt
  now, `queryset=None` included. *(reconstructed)*
- *Leaving the child seal at `required_alias=None`.* Rejected because Django deliberately
  supports explicit cross-database prefetching, so an unpinned child is not inert
  metadata: a `shard_b` parent with `Prefetch("items", queryset=Item.objects.using(
  "default"))` emerged with exactly that split, and overlapping relation keys can populate
  a shard-B parent with rows read from the default database while the generated many-side
  resolver consumes the prefetch cache directly. *(moved from the spec)*
- *Treating an unrouted parent as licence for a routed child.* Rejected as the subtler
  half of the same finding: the review asked for the unpinned-outer-read rule to be
  "document[ed] and test[ed] explicitly" rather than left as a side effect of passing
  `None` down. The rule chosen is symmetric — an unrouted parent forces an unrouted child,
  and an unrouted child inherits the parent's alias. *(reconstructed)*

**Changes the decision has undergone.**

- *Third-round review, `60998b17`.* The decision is that round's product.
- No later round has touched it. `allow_sliced=True` on the child seal is original to it:
  a top-N-per-parent prefetch queryset is legal and nothing refilters it, so the slice
  rejection's premise does not hold one edge down.

**Claims it may no longer make.** None.

## Decision 5 — Queryset-shape rejections + unconditional `Query.model`

Spec decision: [Decision 5][spec-decision-5] (`#decision-5--queryset-shape-rejections--unconditional-querymodel`).

**Alternatives rejected.**

- *Gating the `Query.model` check on the query already having a base table* (the pre-fix
  behavior). Lost because a query with no base table and `model = None` escaped the gate
  and compiled to `SELECT  FROM "products_category" WHERE …`, surfacing as a backend
  syntax error rather than the boundary's typed `ConfigurationError`. *(moved from the
  spec)*
- *Testing `_iterable_class` membership with `in` on a frozenset.* Rejected because `in`
  hashes the candidate, dispatching a consumer metaclass `__hash__` / `__eq__` at exactly
  the moment the boundary is deciding whether to trust it. Membership is `is` identity
  against `_DJANGO_ITERABLE_CLASSES`. *(moved from the spec)*
- *Duck-typing `_meta.concrete_model` in `_concrete_or_none`.* Rejected in the
  four-finding round: an object exposing a convincing `_meta.concrete_model` passed the
  public `QuerySet.model` check and was then installed as `sealed.model`, even when the
  SQL-bearing `Query.model` was the real registered model. Every downstream reader treats
  `queryset.model` as a model *class*, so the malformed state escaped the typed boundary
  and failed later through missing class attributes or consumer attribute access. Class-ness
  and model ancestry are now proven before any metadata is read, which also means a
  consumer `_meta` property never runs. *(reconstructed)*
- *Resolving a pending `_deferred_filter` through Django's `QuerySet.query` getter.*
  Rejected: that getter's `_filter_or_exclude_inplace` / `add_q` are instance-shadowable
  and its `resolve_expression` dispatch would run a consumer expression mid-bake. The bake
  runs the unbound `sql.Query.add_q` against the detached clone instead, over arguments
  proven inert or genuine-Django first, and never mutates the candidate. *(moved from the
  spec)*

**Changes the decision has undergone.**

- *Third-round review, `60998b17`.* The decision is that round's product: the shape
  rejections plus unconditional `Query.model` validation on the outer query and every
  combined branch.
- *Four-finding round, `bbd216fc`.* `_concrete_or_none` tightened from duck-typing to a
  real model-class requirement (above).
- *Floor compatibility, `8af55482`, 2026-07-23.* The deferred-filter bake rejects the
  kwargs Django itself prohibits in `Q.__init__` (`_connector`, `_negated`). Django 6.0
  exposes them as a module-level `PROHIBITED_FILTER_KWARGS`; Django 5.2, the declared
  floor, rejects the same names inline with no constant, so the import is guarded and the
  frozenset mirrored verbatim. The gate therefore behaves identically at the floor. This
  is a compatibility change, not a contract change, and it is the one place in the module
  whose correctness depends on a Django version difference.

**Claims it may no longer make.** None. The six defect codes the decision and the spec's
`## Error shapes` table name all exist, and each default message reproduces the wording
column.

## Decision 6 — Typed `ConfigurationError` fail-closed error contract

Spec decision: [Decision 6][spec-decision-6] (`#decision-6--typed-configurationerror-fail-closed-error-contract`).

**Alternatives rejected.**

- *Letting backend and interpreter exceptions propagate* (the pre-fix behavior for several
  defects). Rejected because an `OperationalError` from malformed SQL leaks nothing
  actionable to the consumer and is not a fail-closed contract — the caller cannot
  distinguish a configuration mistake from a database outage. *(moved from the spec)*
- *A distinct exception class per defect code.* Not taken; `ConfigurationError` stays the
  single typed boundary error and the code selects bespoke wording, with
  [`::SyncMisuseError`][querysets] the one subclass and only because it must also be
  catchable as `RuntimeError` for consumers catching that after the `FilterSet.apply`
  rethrow. Adding six classes would put a taxonomy in the public surface that no consumer
  asked to branch on. *(reconstructed from
  [`::_visibility_result_error`][querysets] and [`::SyncMisuseError`][querysets])*
- *Rendering the cascade's path-rich per-edge prose inside the shared boundary.*
  Rejected in favour of a caller-supplied `render_error` seam, so the shared checker owns
  the codes and the caller owns its own wording rather than the boundary accumulating
  per-caller message branches. *(reconstructed from
  [`::_visibility_result_error`][querysets])*

**Changes the decision has undergone.**

- *Third-round review, `60998b17`.* The decision is that round's product, including the
  wording split in [`::_shadow_defect`][querysets] between the canonical `as_sql` emitter
  ("shadows the `'…'` method") and a dynamically-resolved `as_<vendor>` emitter ("shadows
  the `'…'` compiler method").
- *Comment-hygiene sweep, `5a74d803`, 2026-07-30.* Four user-facing `ConfigurationError`
  messages dropped trailing review shorthand while keeping their spec/decision contract
  pointers. The messages the spec's wording column quotes are the post-sweep ones.

**Claims it may no longer make.**

- The decision states the codes "run the one canonical ordering `type` -> `table` ->
  `untrusted` -> `sliced` -> `projection` -> `alias`". That ordering has one documented
  exception, which the decision did not carry: the outer exact-`sql.Query` check emits
  `untrusted` *before* the combinator table walk can emit `table`, because the walk reads
  query attributes through ordinary attribute access and only a proven-genuine
  `sql.Query` may be walked. The spec now states the exception where it states the order.

## Decision 7 — No version bump: the `0.0.14` cut already landed

Spec decision: [Decision 7][spec-decision-7] (`#decision-7--no-version-bump-the-0014-cut-already-landed`).

**Alternatives rejected.**

- *Treating this card as the joint-cut owner (the lone-card version-bump shape).*
  Rejected because the `0.0.14` cut demonstrably already landed, in `6a86d21f`, before this
  documentation card was authored. *(moved from the spec)*

**Changes the decision has undergone.** None.

**Claims it may no longer make.** None. `pyproject.toml` `[project].version`,
`django_strawberry_framework/__init__.py` `__version__`, and `tests/base/test_init.py` are
untouched by this card and by every round of its closeout.

## Decision 8 — Threat model: a mistaken hook, not an in-process adversary; canonical reconstruction terminates the dispatch-path expansion

Spec decision:
[Decision 8][spec-decision-8]
(`#decision-8--threat-model-a-mistaken-hook-not-an-in-process-adversary-canonical-reconstruction-terminates-the-dispatch-path-expansion`).

This decision was authored after the `0.0.14` cut, once the pattern in the review rounds
became the problem rather than the findings. It is the only decision in the spec whose
subject is the review loop itself.

**Alternatives rejected.**

- *Keeping the boundary open to every crafted-object finding and extending the recursive
  walk each time.* Lost on two grounds at once. Django's compile surface is open-ended, so
  the search never terminates; and each round adds seal latency and a per-Django-version
  maintenance surface. Without a stated threat model every crafted-object report reads as
  a `[P1]`, which is the whack-a-mole the spec had already warned about under
  [prove-then-clone AST trust][glossary-prove-then-clone-ast-trust]. Naming the model
  converts an unbounded review loop into a decidable question. *(moved from the spec)*
- *Reverting the post-`0.0.14` hardening as over-engineering.* Rejected because canonical
  reconstruction fixes an OWNERSHIP defect that non-adversarial code reaches too — a
  retained leaf could flip the sealed predicate after sealing — so it earns its cost
  independently of the threat model. *(moved from the spec)*
- *Rebuilding nodes through their own `clone()` or `copy()`.* Rejected: Django's
  expression `copy()` is a shallow `copy.copy`, so it would keep sharing the child graph,
  which is the entire point of the exercise. *(reconstructed from `dfa86f90` and
  [`::_reconstructed_value`][querysets])*
- *Rebuilding nodes through `deepcopy`.* Refused outright: a direct lookup right-hand side
  is consumer plain data whose `__deepcopy__` / `__reduce__` would dispatch consumer code
  while the seal is still assembling the sealed query. Reconstruction uses
  `object.__new__` plus a raw `__dict__` transfer, so the base allocator runs no `__new__`
  override, no `__init__`, and no descriptor. *(reconstructed from `dfa86f90` and
  [`::_reconstructed_value`][querysets])*
- *Admitting a direct lookup right-hand side on exact type, as the inert-leaf rule does.*
  Rejected because real schemas bind `TextChoices` members and `Decimal` / `UUID` / date
  subclasses; an exact-type rule fails closed on ordinary consumer code. The live example
  tier — unchanged at 830 passing rows across `dfa86f90` — is the fail-close canary for
  exactly this, since a rule too strict for `TextChoices` members or model instances in
  foreign-key position would break real queries there. *(reconstructed from `dfa86f90`)*
- *Retaining an admitted plain-data subclass by reference, since it defines no attribute
  hook.* Rejected: the absence of an attribute hook does not stop Django or the database
  adapter from calling an ordinary overridden `__str__`, `__int__` or `__conform__` on a
  bound parameter, and no enumeration of those methods can be complete. Each admitted
  plain-data subclass is rebuilt as an exact inert value through its base type's own
  descriptors and C slots. *(moved from the spec)*
- *Discovering a lookup's operands through `get_source_expressions()`.* Rejected on two
  counts: it first calls `rhs_is_direct_value()`, whose `hasattr(rhs, "as_sql")` runs an
  arbitrary consumer attribute hook during the proof itself, and it then returns `lhs`
  alone for a direct right-hand side, so the value the adapter later binds left the
  boundary entirely unproven. Operands are read from raw instance state and the
  right-hand side classified with `inspect.getattr_static`, which reproduces the resolution
  order Django's own `hasattr` uses while invoking nothing. *(reconstructed from
  `dfa86f90`, [`::_lookup_operands_defect`][querysets],
  [`::_static_attr_present`][querysets])*

**Changes the decision has undergone.**

- *Canonical-reconstruction root fix, `dfa86f90`, 2026-07-30.* The decision's
  reconstruction half is that commit. Note that the four-finding round had already named
  it: its first finding said a per-expression state inventory "is still version-sensitive,
  so the stronger fix is the canonical reconstruction identified in spec-045". The spec had
  flagged reconstruction as the future root fix before any round asked for it; the round
  that could not be closed without it is what forced it.
- *Same commit.* Two further slots joined the contract, both discovered while
  reconstruction was being built rather than reported by a round: a `Func` routes surplus
  constructor keywords into `self.extra` rather than onto the named template slots, and
  `as_sql` merges that mapping straight into the format context, so a `Func` carrying an
  object under `extra["function"]` sealed cleanly and then dispatched that object's
  `__str__` during SQL formatting ([`::_template_params_defect`][querysets]); and a
  lookup's operands moved off `get_source_expressions()` (above).
- *Measured cost, `dfa86f90`.* Sealing costs roughly 1.7x on simple and medium queries
  and 2.3x on an annotation-heavy shape — "the price of owning the graph rather than
  borrowing it", recorded in the commit that introduced it. The spec carries the numbers
  as part of the argument against per-finding walk expansion.

**Claims it may no longer make.**

- **The decision may no longer claim that both bound-parameter residuals are "closed by
  normalization".** As shipped it named two previously-open questions — what a bound
  `Lookup.rhs` may be, and the unvalidated `Value.value` in the same category — and said
  normalization plus the threat model closed both. Only the first is closed that way. A
  `Lookup`'s right-hand side is validated by [`::_direct_rhs_defect`][querysets] and then
  normalized by [`::_normalized_bound_value`][querysets]. `Value.value` is neither: a
  `Value`'s `get_source_expressions()` returns `[]`, so the graph walk never reaches the
  slot, and [`::_normalized_bound_value`][querysets] returns an object that descends from
  no plain-data base *unchanged*. A read-only probe against the boundary at HEAD sealed
  `Category.objects.filter(is_private=False).annotate(probe=Value(<arbitrary object>))`
  with no defect and found the arbitrary object still in the sealed query **by identity**.
  Under Decision 8's own threat model that is out of scope — binding a non-plain-data
  object into a `Value` is a crafted-object path, it reaches only an adapter dispatch site,
  and the value is bound as a `%s` parameter so it cannot alter SQL structure. But it is
  *not* closed by normalization, and it means the sealed query can still share a mutable
  consumer object in a bound-value slot. The spec now states the retention set exactly
  instead of claiming that no bound parameter's methods are consumer-owned.
- The same correction narrows the decision's summary sentence. "So the sealed query
  carries no consumer-owned AST, no consumer-owned container, and no bound parameter whose
  methods are not the interpreter's own" is true of the first two clauses and, as above,
  not of the third in every slot. The spec now says what stays shared, and why each item
  in that set is inert or deliberately retained.

## Deliberation that belonged to no single decision

*(moved from the spec's `## Risks and open questions`, `## Non-goals`, and `## Out of
scope`, all of which narrated a resolved architectural argument in the future or flagged
tense.)*

**"Prove-then-clone is whack-a-mole over Django's compile surface."** The architectural
note the card raised, and it stood: proving-then-cloning Django's live objects is a moving
target because every Django version can add a new compiler-reachable slot, and a
proven-then-retained node stays mutable through the candidate's own reference. The flagged
root fix was canonical reconstruction; the rejected fallback was to keep extending the
recursive walk per finding. Both are now settled under Decision 8, and the spec states the
resulting contract rather than the argument.

**"Canonical reconstruction is flagged, not adopted."** True when the card was authored
and false since `dfa86f90`. The spec's `## Non-goals` and `## Out of scope` carried the
flagged-but-not-adopted framing in the future tense after the work had landed, which left
a reader reconstructing what is currently true by applying a chronology. The framing is
here; the spec states the adopted contract.

**Why the bound-parameter residuals were not carried to a further card.** They were
recorded as subsumed by Decision 8 rather than deferred, on the reasoning that a bound
parameter may be any plain-data value because the sealed query binds an exact inert copy
of it. That reasoning holds for a `Lookup`'s right-hand side and not for `Value.value`;
see Decision 8's claims section. The residual is therefore live, bounded by the threat
model, and named in the closeout record rather than silently closed.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[glossary-prove-then-clone-ast-trust]: ../../GLOSSARY.md#prove-then-clone-ast-trust
[glossary-visibility-boundary]: ../../GLOSSARY.md#visibility-boundary

<!-- docs/SPECS/ -->

[spec]: ../spec-045-visibility_boundary-0_0_14.md
[spec-decision-1]: ../spec-045-visibility_boundary-0_0_14.md#decision-1--the-hook-and-source-objects-are-untrusted-query-state-rebuilt-into-a-framework-owned-plain-djangodbmodelsqueryset
[spec-decision-2]: ../spec-045-visibility_boundary-0_0_14.md#decision-2--fail-closed-prove-then-clone-ast-trust
[spec-decision-3]: ../spec-045-visibility_boundary-0_0_14.md#decision-3--the-identity-fast-path-is-removed-hook-results-are-always-re-sealed-and-result-caches-dropped
[spec-decision-4]: ../spec-045-visibility_boundary-0_0_14.md#decision-4--prefetch-rebuild-as-an-exact-django-class--alias-threading-with-require_shared_alias
[spec-decision-5]: ../spec-045-visibility_boundary-0_0_14.md#decision-5--queryset-shape-rejections--unconditional-querymodel
[spec-decision-6]: ../spec-045-visibility_boundary-0_0_14.md#decision-6--typed-configurationerror-fail-closed-error-contract
[spec-decision-7]: ../spec-045-visibility_boundary-0_0_14.md#decision-7--no-version-bump-the-0014-cut-already-landed
[spec-decision-8]: ../spec-045-visibility_boundary-0_0_14.md#decision-8--threat-model-a-mistaken-hook-not-an-in-process-adversary-canonical-reconstruction-terminates-the-dispatch-path-expansion

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

[querysets]: ../../../django_strawberry_framework/utils/querysets.py
[walker]: ../../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

[queryset-tests]: ../../../tests/utils/test_querysets.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
