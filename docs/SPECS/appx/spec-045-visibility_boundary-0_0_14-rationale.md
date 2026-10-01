# Rationale: sealed `get_queryset` visibility-boundary policy artifacts (spec-045)

The deliberative layer of [`docs/SPECS/spec-045-visibility_boundary-0_0_14.md`][spec]. The spec
states the contract the [visibility boundary][glossary-visibility-boundary] offers and
nothing else; this file carries, for each of that spec's numbered decisions, the
alternatives that were rejected and why each lost.

Every entry names its spec decision by heading text and anchor, so a reader working
through the spec can look the deliberation up and a reviewer cannot re-litigate a settled
alternative without first reading why it lost.

Decision numbers are a package-wide identifier: source and test docstrings across
[`django_strawberry_framework/utils/querysets.py`][querysets],
[`django_strawberry_framework/optimizer/walker.py`][walker], and
[`tests/utils/test_querysets.py`][queryset-tests] cite them as `spec-045 Decision N`, so
renumbering a decision is a source-wide rename, not a documentation edit.

## Decision 1 — The hook and source objects are untrusted query state, rebuilt into a framework-owned plain `django.db.models.QuerySet`

Spec decision:
[Decision 1][spec-decision-1]
(`#decision-1--the-hook-and-source-objects-are-untrusted-query-state-rebuilt-into-a-framework-owned-plain-djangodbmodelsqueryset`).

**Alternatives rejected.**

- *Keeping a class-level method inventory and returning the consumer object.* Zero-SQL
  probes defeat it: an instance-shadowed `.all()`, a replaced instance-level
  `Query.chain`, and subclass `.filter()` / `_values` / `.first()` / `.__aiter__()`
  overrides each erase the visibility predicate or return synthetic rows *after* a
  class-level inventory has accepted the object. A finite inventory can only ever
  enumerate the overrides it already knows about, and the vector is the object's runtime
  dispatch.
- *Blacklisting the specific override names the probes used.* Any instance-level method
  shadow copied into a mutable execution object recreates the same abstraction error, so
  fixing only the literal `chain` name fixes nothing. The contract is therefore
  structural — any `__dict__` key naming a callable class attribute — and never a name
  list.
- *Trusting a field once it is read out of `__dict__` without dispatch.* Reading state
  without dispatching is not the same as *using* it without dispatching: each retained
  `QuerySet.__dict__` field is later subjected to truthiness, a comparison, or a `dict`
  copy, so a consumer `__bool__` / `__eq__` / `__iter__` in one of those slots would
  dispatch mid-seal. Hence the exact-shape gate, [`::_queryset_state_defect`][querysets].

## Decision 2 — Fail-closed prove-then-clone AST trust

Spec decision: [Decision 2][spec-decision-2] (`#decision-2--fail-closed-prove-then-clone-ast-trust`).

**Alternatives rejected.**

- *Trusting `type(node).__module__.startswith("django.")` as provenance.* `__module__` is
  a plain writable class attribute: a consumer class declaring `__module__ =
  "django.evil"` spoofs it outright. Provenance is object identity against
  `sys.modules[module].<qualname>` instead.
- *Assuming `sql.Query.clone` is dispatch-free, so that proving the outer `Query` type is
  enough.* Django's own `Query.clone` body shallow-copies the source `__dict__`, calls
  `self.where.clone()`, calls `.copy()` on the retained containers, `deepcopy`s
  `select_related`, and defers `as_sql` to compile time. An outer query kept exactly
  `sql.Query` whose `where` is a `WhereNode` subclass with a `clone()` returning an empty
  node loses the visibility predicate from the queryset the boundary returns.
- *Proving a node genuine and then calling its accessors freely.* A genuine accessor reads
  consumer-controlled state: `Case.get_source_expressions()` expands
  `[*self.cases, self.default]`, so a `list` subclass in `cases` runs its own iterator
  during the proof, early enough to rewrite an already-accepted `where` tree before the
  clone. Every slot an accessor iterates is pinned first
  ([`::_expression_state_defect`][querysets]).
- *Checking a retained container's type and keys only.* `Query.clone`'s `.copy()` calls
  are shallow, so payload objects survive into the clone; an `int` subclass stored as an
  `alias_refcount` value has its arithmetic invoked through `Query.ref_alias` /
  `unref_alias` by ordinary downstream `.filter()` composition, and that callback can
  drop the visibility predicate. Payloads are pinned to their complete Django shape
  ([`::_query_payload_defect`][querysets]).
- *One `seen` identity set for the walk.* It cannot distinguish a completed shared node
  from a node still being visited, so a self-referential list, dict, `Q`, or expression
  graph would be accepted, and cloning or compiling it resurfaces as a raw
  `RecursionError` past the typed contract. The walk is three-state instead
  ([`::_GraphWalk`][querysets], [`::_WalkState`][querysets],
  [`::_walk_short_circuit`][querysets]).
- *Supporting consumer-defined expressions and lookups behind a vetted allowlist.* An
  allowlist is a per-type audit surface that grows with every consumer expression and
  buys a capability a consumer can already reach by expressing the predicate through
  genuine Django primitives. The guarantee is narrowed instead: a genuinely custom `Func`
  or `Lookup` fails closed as `untrusted`. A future allowlist remains the named fallback
  if that constraint ever proves too tight.
- *Extending the walk one dispatch site at a time as each new one is reported.* Rejected
  in favour of canonical reconstruction; the argument is recorded under Decision 8.

The inert-leaf test ([`::_is_inert_value`][querysets]) is exact-type, deliberately; a
direct lookup right-hand side is a different rule (admitted on plain-data ancestry and
normalized, Decision 8), which is why binding a `TextChoices` member to a visibility
filter seals.

## Decision 3 — The identity fast path is removed; hook results are always re-sealed and result caches dropped

Spec decision:
[Decision 3][spec-decision-3]
(`#decision-3--the-identity-fast-path-is-removed-hook-results-are-always-re-sealed-and-result-caches-dropped`).

**Alternatives rejected.**

- *Keeping `result is queryset` as a performance shortcut.* A hook given an empty source
  query can insert an unsaved private object into the received queryset's
  `_result_cache` and return that same queryset; an identity shortcut returns it
  verbatim and normal iteration serves the synthetic row without executing the empty
  SQL. Object identity proves that no *other* object was returned; it proves nothing
  about the object, which the hook has held and can mutate.
- *Restricting the fast path to a provably unoverridden package-default hook.* The proof
  obligation (that no consumer code ran between source sealing and return) is larger
  than the second seal it would save, and the boundary already pays the seal cost on the
  source side.
- *Copying `_known_related_objects` forward for correctness.* A fresh fetch is always
  correct, whereas copying an untrusted related-object cache could pre-seed synthetic
  related instances that bypass the related type's own visibility hook. The cache is
  optional state, so dropping it costs nothing but a refetch
  ([`::_seal_or_defect`][querysets] #"Reproduce exactly what").

## Decision 4 — `Prefetch` rebuild as an exact Django class + alias threading with `require_shared_alias`

Spec decision:
[Decision 4][spec-decision-4]
(`#decision-4--prefetch-rebuild-as-an-exact-django-class--alias-threading-with-require_shared_alias`).

**Alternatives rejected.**

- *Copying the consumer `Prefetch` instance forward after validating its path state.* A
  `Prefetch` subclass overriding `get_current_querysets` substitutes an unsealed child
  queryset at *fetch* time, long after any instance-level validation ran.
- *Rebuilding only the `queryset is not None` case.* A consumer `Prefetch` subclass with
  `queryset=None` would then be appended unchanged, keeping its override. Every entry is
  rebuilt, `queryset=None` included.
- *Leaving the child seal unpinned.* Django deliberately supports explicit cross-database
  prefetching, so an unpinned child is not inert metadata: a `shard_b` parent with
  `Prefetch("items", queryset=Item.objects.using("default"))` splits one resolution across
  two databases, and overlapping relation keys can populate a shard-B parent with rows
  read from the default database while the generated many-side resolver consumes the
  prefetch cache directly.
- *Treating an unrouted parent as licence for a routed child.* The rule is symmetric and
  explicit rather than a side effect of passing `None` down: an unrouted parent forces an
  unrouted child, and an unrouted child inherits the parent's alias.
- *Rejecting a sliced consumer `Prefetch` child.* A top-N-per-parent prefetch queryset is
  legal Django, the slice is the consumer's own call, and nothing in this package
  recomposes onto it, so the slice rejection's premise does not hold one edge down.

## Decision 5 — Queryset-shape rejections + unconditional `Query.model`

Spec decision: [Decision 5][spec-decision-5] (`#decision-5--queryset-shape-rejections--unconditional-querymodel`).

**Alternatives rejected.**

- *Gating the `Query.model` check on the query already having a base table.* A query with
  no base table and `model = None` escapes the gate and compiles to
  `SELECT  FROM "products_category" WHERE …`, surfacing as a backend syntax error rather
  than the boundary's typed `ConfigurationError`.
- *Testing `_iterable_class` membership with `in` on a frozenset.* `in` hashes the
  candidate, dispatching a consumer metaclass `__hash__` / `__eq__` at exactly the moment
  the boundary is deciding whether to trust it. Membership is `is` identity against
  `_DJANGO_ITERABLE_CLASSES`.
- *Duck-typing `_meta.concrete_model` in `_concrete_or_none`.* An object exposing a
  convincing `_meta.concrete_model` would pass the public `QuerySet.model` check and be
  installed as `sealed.model`, even when the SQL-bearing `Query.model` is the real
  registered model. Every downstream reader treats `queryset.model` as a model *class*, so
  the malformed state would escape the typed boundary and fail later through missing
  class attributes or consumer attribute access. Class-ness and model ancestry are proven
  before any metadata is read, which also means a consumer `_meta` property never runs.
- *Resolving a pending `_deferred_filter` through Django's `QuerySet.query` getter.* That
  getter's `_filter_or_exclude_inplace` / `add_q` are instance-shadowable and its
  `resolve_expression` dispatch would run a consumer expression mid-bake. The bake runs
  the unbound `sql.Query.add_q` against the detached clone instead, over arguments proven
  inert or genuine-Django first, and never mutates the candidate.

## Decision 6 — Typed `ConfigurationError` fail-closed error contract

Spec decision: [Decision 6][spec-decision-6] (`#decision-6--typed-configurationerror-fail-closed-error-contract`).

**Alternatives rejected.**

- *Letting backend and interpreter exceptions propagate.* An `OperationalError` from
  malformed SQL leaks nothing actionable to the consumer and is not a fail-closed
  contract: the caller cannot distinguish a configuration mistake from a database outage.
- *A distinct exception class per defect code.* `ConfigurationError` stays the single
  typed boundary error and the code selects bespoke wording, with
  [`::SyncMisuseError`][querysets] the one subclass and only because it must also be
  catchable as `RuntimeError` for consumers catching that after the `FilterSet.apply`
  rethrow. A class per code would put a taxonomy in the public surface that no consumer
  asked to branch on.
- *Rendering the cascade's path-rich per-edge prose inside the shared boundary.* A
  caller-supplied `render_error` seam lets the shared checker own the codes and the
  caller own its wording, rather than the boundary accumulating per-caller message
  branches ([`::_visibility_result_error`][querysets]).
- *Ending each message ladder in an unconditional branch for its last code.* A code added
  to the seal without an arm at a site would then MISLABEL the rejection instead of
  failing loudly. Dispatch is exhaustive ([`::_defect_message`][querysets]): an
  unrendered code says it is a framework defect.

## Decision 7 — No version bump: the `0.0.14` cut already landed

Spec decision: [Decision 7][spec-decision-7] (`#decision-7--no-version-bump-the-0014-cut-already-landed`).

**Alternatives rejected.**

- *Treating this card as the release-cut owner (the lone-card version-bump shape).* The
  `0.0.14` release this card documents was already cut, so a documentation card at that
  patch line owns no bump.

## Decision 8 — Threat model: a mistaken hook, not an in-process adversary; canonical reconstruction terminates the dispatch-path expansion

Spec decision:
[Decision 8][spec-decision-8]
(`#decision-8--threat-model-a-mistaken-hook-not-an-in-process-adversary-canonical-reconstruction-terminates-the-dispatch-path-expansion`).

**Alternatives rejected.**

- *Keeping the boundary open to every crafted-object finding and extending the recursive
  walk each time.* Proving-then-cloning Django's live objects is a moving target: every
  Django version can add a compiler-reachable slot, so the search never terminates, and
  each extension adds seal latency and a per-Django-version maintenance surface. Without a
  stated threat model every crafted-object report reads as a blocker, which is the
  whack-a-mole [prove-then-clone AST trust][glossary-prove-then-clone-ast-trust] alone
  cannot escape. Naming the model converts an unbounded review loop into a decidable
  question.
- *Dropping canonical reconstruction as over-engineering.* A proven-then-retained node is
  still the candidate's object, so the sealed query would stay mutable after sealing: a
  retained leaf could flip the sealed predicate, an OWNERSHIP defect non-adversarial code
  reaches too. Reconstruction earns its cost independently of the threat model.
- *Rebuilding nodes through their own `clone()` or `copy()`.* Django's expression `copy()`
  is a shallow `copy.copy`, so it would keep sharing the child graph, which is the entire
  point of the exercise ([`::_reconstructed_value`][querysets]).
- *Rebuilding nodes through `deepcopy`.* A direct lookup right-hand side is consumer plain
  data whose `__deepcopy__` / `__reduce__` would dispatch consumer code while the seal is
  still assembling the sealed query. Reconstruction uses `object.__new__` plus a raw
  `__dict__` transfer, so the base allocator runs no `__new__` override, no `__init__`,
  and no descriptor.
- *Admitting a direct lookup right-hand side on exact type, as the inert-leaf rule does.*
  Real schemas bind `TextChoices` members and `Decimal` / `UUID` / date subclasses; an
  exact-type rule fails closed on ordinary consumer code, and the live example tier would
  break on it.
- *Retaining an admitted plain-data subclass by reference, since it defines no attribute
  hook.* The absence of an attribute hook does not stop Django or the database adapter
  from calling an ordinary overridden `__str__`, `__int__` or `__conform__` on a bound
  parameter, and no enumeration of those methods can be complete. Each admitted
  plain-data subclass is rebuilt as an exact inert value through its base type's own
  descriptors and C slots ([`::_normalized_bound_value`][querysets]).
- *Retaining any other bound payload (an opaque object in `Value.value`, a mapping key)
  by reference.* The graph proofs never enumerate those slots, so retaining it would leave
  the sealed query sharing a mutable consumer object. The ownership decision is made at
  reconstruction, where every retained object is decided: a payload that reduces to no
  exact inert value and is not trusted schema fails closed as `untrusted`.
- *Discovering a lookup's operands through `get_source_expressions()`.* It first calls
  `rhs_is_direct_value()`, whose `hasattr(rhs, "as_sql")` runs an arbitrary consumer
  attribute hook during the proof itself, and it then returns `lhs` alone for a direct
  right-hand side, so the value the adapter later binds would leave the boundary unproven.
  Operands are read from raw instance state and the right-hand side classified with
  `inspect.getattr_static`, which reproduces the resolution order Django's own `hasattr`
  uses while invoking nothing ([`::_lookup_operands_defect`][querysets],
  [`::_static_attr_present`][querysets]).
- *Leaving a `Func`'s surplus `extra` template mapping unvalidated.* A `Func` routes
  surplus constructor keywords into `self.extra`, and `as_sql` merges that mapping
  straight into the format context, so an object under `extra["function"]` would dispatch
  its `__str__` during SQL formatting ([`::_template_params_defect`][querysets]).

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
