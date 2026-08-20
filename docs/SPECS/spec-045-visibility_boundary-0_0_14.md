# Spec: Sealed `get_queryset` visibility-boundary policy artifacts — the governing security decisions, spec, and glossary for the framework-owned execution queryset

Built for `0.0.14` (card `DONE-045-0.0.14`). This is a **documentation-only**
slice over an already-landed implementation: commit `60998b17`
("feat(visibility): seal get_queryset hook results into framework-owned
querysets") shipped the sealed [visibility boundary][glossary-visibility-boundary].
Only the policy artifacts — a governing set of numbered security decisions, this
spec, a KANBAN card, and the [glossary][glossary] fold-in — were deferred to a
shipping slice. This card discharges that deferral so the standing documentation
matches the implemented security contract.

Decisions 1–6 and 8 below state the boundary's contract as it stands; Decision 7
records release bookkeeping. Every rejected alternative, every change a decision
has undergone, and every claim a decision may no longer make live in the
deliberative companion [`docs/SPECS/appx/spec-045-visibility_boundary-0_0_14-rationale.md`][rationale].

Status: **COMPLETE — shipped in `0.0.14` (commit `60998b17`); this card records
the governing artifacts, which describe the boundary as it now stands including
its post-`0.0.14` hardening.** The Slice checklist boxes below stay unticked
because the `Status:` line is the completion source of truth (the shipped-spec
convention); the code they describe already landed.

No version bump is owned here: `0.0.14` was cut by the joint release commit
`6a86d21f` ("release: 0.0.14 joint cut"), so this follow-on documentation card
at the same patch line carries none of the version quintet
([Decision 7](#decision-7--no-version-bump-the-0014-cut-already-landed)).

Permission caveat: `AGENTS.md` prohibits `CHANGELOG.md` edits without explicit
permission. This card ships no `CHANGELOG.md` entry — the behavior it documents
already shipped under the `0.0.14` release entry the joint cut wrote — so no
slice here touches it.

---

## Key glossary references

Terms this spec relies on (statuses per [`docs/GLOSSARY.md`][glossary]):

- [Sealed execution queryset][glossary-sealed-execution-queryset],
  [Visibility boundary][glossary-visibility-boundary],
  [Prove-then-clone AST trust][glossary-prove-then-clone-ast-trust],
  [Callable shadow defect][glossary-callable-shadow-defect],
  [Prefetch alias threading][glossary-prefetch-alias-threading] — the five terms
  this card authors, naming the hardened contract's moving parts.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] — the
  consumer seam whose source and result the boundary now seals.
- [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — the cascade
  caller that composes over the same boundary and supplies the `render_error`
  seam.
- [`ConfigurationError`][glossary-configurationerror],
  [`SyncMisuseError`][glossary-syncmisuseerror] — the single typed fail-closed
  boundary error and its sync-context subclass.

## Slice checklist

A single documentation slice; the code shipped in commit `60998b17`.

- [ ] **Slice 1 — Policy artifacts for the sealed boundary**
  - [ ] Numbered security decisions (below) covering the changed contract:
        untrusted-object rebuild, prove-then-clone AST trust,
        identity-fast-path removal, `Prefetch` rebuild + alias threading,
        queryset-shape rejections, and the typed error contract.
  - [ ] This spec `docs/SPECS/spec-045-visibility_boundary-0_0_14.md` and its
        companions `*-terms.csv` and `*-rationale.md`.
  - [ ] The five new glossary entries imported via the fakeshop glossary DB and
        `docs/GLOSSARY.md` regenerated (never hand-edited).
  - [ ] `KANBAN.md` / `KANBAN.html` regenerated from the kanban DB with this
        card in Done.
  - [ ] The prior `[P2]` policy-artifact residual recorded as closed here.

## Problem statement

The sealed boundary began as a method-inventory check: it validated a finite
list of method overrides on the consumer `QuerySet` *class* and, if the class
looked clean, returned the consumer object unchanged. The adversarial review
established that **the method inventory is the wrong abstraction** — the leak
vector is not the class's declared methods but the query STATE and the object's
runtime dispatch. Zero-SQL probes drove the point home: an instance-shadowed
`.all()`, a replaced instance-level `Query.chain`, and subclass `.filter()` /
`_values` / `.first()` / `.__aiter__()` each erased the visibility predicate or
returned synthetic rows *after* a class-level inventory had accepted the object.
A `get_queryset` mistake is a data-leak bug, so the boundary must not trust the
consumer object at all.

## Current state

- The sealed boundary shipped in commit `60998b17` and
  [`django_strawberry_framework/utils/querysets.py`][querysets] is covered under
  the repository's `fail_under = 100` gate.
- Both the source (before the hook) and the hook result (after) are rebuilt into
  a framework-owned plain `django.db.models.QuerySet`; the consumer object is
  never returned, and the rebuilt query's whole state is canonically
  reconstructed so it shares no mutable object with the candidate graph
  ([Decision 8](#decision-8--threat-model-a-mistaken-hook-not-an-in-process-adversary-canonical-reconstruction-terminates-the-dispatch-path-expansion)).
- Every non-sealable shape fails closed with a typed
  [`ConfigurationError`][glossary-configurationerror] (or
  [`SyncMisuseError`][glossary-syncmisuseerror] for an async hook in a sync
  context) — never a raw backend `OperationalError`, `TypeError`,
  `AttributeError`, or an unclosed coroutine.
- The sync and async runners share one preparation primitive
  (`_prepared_visibility_source`) and one normalization primitive
  (`_normalized_visibility_result`) so the two colored paths cannot drift.

## Goals

- Record the governing numbered security decisions for the accepted queryset
  shapes, identity/cache behavior, aliases, errors, and query execution the
  sealed boundary changed.
- Author the five glossary terms naming the contract's moving parts, and relink
  the four existing terms the contract composes with.
- Close the deferred `[P2]` policy-artifact residual in this durable spec.

## Non-goals

- **No behavior change.** This card is documentation only; the boundary's code
  ships independently of it and is unchanged by it.
- **No version bump.** `0.0.14` was already cut by the joint release
  ([Decision 7](#decision-7--no-version-bump-the-0014-cut-already-landed)).

## Borrowing posture

None. The sealed boundary is internal security-boundary hardening with no
upstream peer: neither `graphene-django` nor `strawberry-graphql-django` ships a
comparable framework-owned-execution-queryset primitive, so there is no
borrowing posture to pin. The contract is derived entirely from Django's own
`django.db.models.sql.Query` compile surface and the adversarial review.

## Architectural decisions

Decisions 1–6 and 8 below are the governing security decisions for the boundary
— 1–6 the shape of the seal, 8 the threat model that bounds it and the canonical
reconstruction that terminates it; Decision 7 records release bookkeeping. Each
is pinned to the enforcing symbols in
[`django_strawberry_framework/utils/querysets.py`][querysets] and the tests that
hold it.

Decision numbers are load-bearing beyond this document: source and test
docstrings across the package cite them in the form `spec-045 Decision N`.
Renumbering a decision is a package-wide rename, not a documentation edit.

### Decision 1 — The hook and source objects are untrusted query state, rebuilt into a framework-owned plain `django.db.models.QuerySet`

**Decision.** The boundary no longer validates a finite inventory of method
overrides on the consumer `QuerySet` class and returns the consumer object. It
treats both the source queryset (before the hook) and the hook's return value as
untrusted query STATE: it reads that state from the instance `__dict__` via
`object.__getattribute__` (so a custom `__getattribute__`, an instance-shadowed
attribute, or a redefined `query` / `_query` descriptor cannot run code or lie
during extraction), validates it, then rebuilds a fresh framework-owned plain
`django.db.models.QuerySet` from the validated state. It NEVER returns the
consumer object. Preserved: SQL query state (filters, annotations, joins,
ordering, combinators, values projection), database routing / hints, and
prefetch metadata. Dropped: the consumer's executable override dispatch (the
subclass identity), which is the leak vector.

Reading state without dispatch is not the same as USING it without dispatch, so
every `QuerySet.__dict__` field the seal carries forward — `_db`, `_hints`,
`_fields`, `_sticky_filter`, `_for_write` — is pinned to the exact shape Django
stores before any truthiness test, comparison, or `dict` copy runs on it: `_db`
`None` or an exact `str`, `_hints` `None` or an exact `dict` with exact-`str`
keys, `_fields` `None` or an exact `tuple` / `list` of exact-`str` names,
`_sticky_filter` / `_for_write` `None` or an exact `bool`. `_hints` is copied
into a fresh dict rather than shared, so the untrusted object retains no
routing-control surface on the sealed queryset.

**Enforcing symbols.**
[`utils/querysets.py::_seal_or_defect`][querysets] (the single sealing
primitive: extracts state via `object.__getattribute__`, clones once through the
unbound `sql.Query.clone`, constructs a plain `models.QuerySet`);
[`::_queryset_state_defect`][querysets] (the retained-state exact-shape gate);
[`::_prepared_visibility_source`][querysets] (seals the source before the hook
runs); [`::_normalized_visibility_result`][querysets] (seals the hook result).

**Deliberation.** The rejected class-level method inventory, the rejected
name-blacklist fix, and this decision's change history are recorded in the
[rationale companion][rationale].

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests] (the
shared seal / rebuild suite) plus the row-survival surfaces in
[`tests/test_relay_node_field.py`][relay-tests],
[`tests/test_connection.py`][connection-tests], and
[`tests/test_list_field.py`][list-tests].

### Decision 2 — Fail-closed prove-then-clone AST trust

**Decision.** `sql.Query.clone` is NOT a no-dispatch boundary: it shallow-copies
the source `__dict__`, calls `self.where.clone()`, `.copy()` on containers,
`deepcopy`s `select_related`, and the compiler later dispatches each node's
`as_sql`. So before the clone the boundary proves EVERY compiler-reachable node
is a genuine, unshadowed Django implementation and every cloned container an
exact builtin. The proof is a PRECONDITION of the clone, not the end of the
seal: the clone is then canonically reconstructed into framework-owned objects
([Decision 8](#decision-8--threat-model-a-mistaken-hook-not-an-in-process-adversary-canonical-reconstruction-terminates-the-dispatch-path-expansion)),
so the proven graph is never what the sealed query executes over.

The proof: (a) genuine-Django provenance is proven by OBJECT IDENTITY against
`sys.modules[module].<qualname>`, never the spoofable `__module__` string,
reading `__module__` / `__qualname__` through `type.__getattribute__` so a
consumer metaclass cannot lie; (b) any instance-`__dict__` key naming a callable
class attribute (`chain` / `clone` / `as_sql` / a dynamic `as_<vendor>` emitter /
any) fails closed BEFORE the clone (the [callable shadow
defect][glossary-callable-shadow-defect]). This rejection is STRUCTURAL and never
a named-method blacklist: the rule is "any `__dict__` key naming a callable class
attribute", so no method name is privileged and a shadow on a method nobody
enumerated fails closed identically; (c) the `where` / `having` trees and
their leaf operands, `annotations` (incl. nested `Func` / `Case` operands and
inner `Subquery` graphs), the `order_by` / `group_by` / `distinct_fields` /
`select` / `values_select` sequences, the `extra_order_by` / `extra_tables`
raw-SQL slots, `Query.extra` select payloads, `ExtraWhere` fragments, `RawSQL`
parameters, the `alias_map` joins (and any join's `filtered_relation` resolved
condition), and `select_related` are each walked once under a single recursive
id-memoized traversal; inert parameter leaves terminate by EXACT type (a `str` /
`int` / `datetime` subclass carrying `resolve_expression` is NOT inert).
SQL-template metadata (`template` / `function` / `arg_joiner` / `connector` /
`sql` / `base_template`) present on an instance must be exactly `str`, and an
expression's open-ended `extra` template mapping must be an exact `dict` of
exact-`str` keys and exact inert scalar values.

Three further properties the walk must hold, each of which a narrower reading of
"prove the node genuine" does not supply:

- **Expression-owned state is proven before the accessor that reads it runs.** A
  genuine Django accessor is not dispatch-free, because it reads
  consumer-controlled state: `Case.get_source_expressions()` expands
  `[*self.cases, self.default]`, so a `list` subclass in `cases` would run its own
  iterator during the proof — early enough to rewrite an already-accepted `where`
  tree before the clone. Every slot a genuine accessor iterates, unpacks, or
  slices (`source_expressions` / `cases` / `targets` / `sources`) is pinned to the
  exact builtin sequence first.
- **Retained containers are proven by payload, not only by type and key.**
  `sql.Query.clone`'s `.copy()` calls are shallow, so every object inside a
  retained container survives into the sealed query and is handed to Django's own
  bookkeeping — an `int` subclass stored as an `alias_refcount` value has its
  arithmetic invoked by ordinary downstream `.filter()` composition, and that
  callback can rewrite the sealed `where` tree before the new predicate is added.
  Alias refcounts must be exact `int`, external-alias flags exact `bool`,
  `table_map` entries exact lists of exact-`str` aliases, set members exact `str`,
  and `_filtered_relations` values genuine and unshadowed.
- **A reference cycle is untrusted state, not a shared diamond.** The walk is
  three-state: a node reached while still being visited closes a cycle and fails
  closed; a node reached after complete validation is a legitimate shared
  reference and is accepted. Django never builds a cyclic query graph, and cloning
  or compiling one would escape as a raw `RecursionError` past the typed contract.

**Enforcing symbols.**
[`utils/querysets.py::_type_is_genuinely_django`][querysets] (object-identity
provenance); [`::_shadow_defect`][querysets] (callable-shadow and `as_<vendor>`
rejection); [`::_expr_graph_defect`][querysets], [`::_where_tree_defect`][querysets],
[`::_join_defect`][querysets], [`::_expr_sequence_defect`][querysets],
[`::_raw_sql_sequence_defect`][querysets], [`::_raw_sql_node_defect`][querysets],
[`::_raw_sql_params_defect`][querysets] (the raw-SQL payloads Django hands
straight to the adapter); [`::_node_metadata_defect`][querysets] and
[`::_template_params_defect`][querysets] (SQL-template metadata and the `extra`
mapping); [`::_expression_state_defect`][querysets] (expression-owned state
proven before the accessor runs); [`::_select_related_defect`][querysets],
[`::_query_container_defect`][querysets] and [`::_query_payload_defect`][querysets]
(retained containers and their payloads);
[`::_query_ast_defect`][querysets], [`::_query_genuineness_defect`][querysets],
[`::_genuine_node_defect`][querysets], [`::_container_defect`][querysets]
(the recursive walk and its helpers); [`::_GraphWalk`][querysets],
[`::_WalkState`][querysets] and [`::_walk_short_circuit`][querysets] (the
three-state cycle rejection);
[`::_base_table_defect`][querysets] (reads the authoritative base table from the
initialized `alias_map`, not the poisonable `base_table` cache).

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests]
hostile-node cases (named in the source docstrings, e.g.
`test_hostile_subquery_inner_query_fails_closed`,
`test_hostile_expression_inside_genuine_subquery_where_fails_closed`,
`test_query_shadow_defect_is_name_agnostic`,
`test_func_extra_template_parameter_object_fails_closed`); the
connection row-survival case
`tests/test_connection.py::test_connection_query_chain_shadow_hook_is_sealed`
([connection tests][connection-tests]).

**Deliberation.** The rejected `__module__`-string provenance, the rejected
"`clone` is dispatch-free" premise, the rejected vetted-expression allowlist, and
the three later rounds that added the properties above are recorded in the
[rationale companion][rationale].

### Decision 3 — The identity fast path is removed; hook results are always re-sealed and result caches dropped

**Decision.** Both runners previously skipped result normalization when the hook
returned the exact source object it received. That fast path is gone:
`apply_type_visibility_sync` and `apply_type_visibility_async` ALWAYS re-seal the
hook result through `_normalized_visibility_result` (no `result is queryset`
shortcut). The rebuild never copies `_result_cache`, and `_known_related_objects`
is deliberately dropped, so an injected cached row (synthetic or otherwise)
cannot cross the boundary. Object identity is not immutability: a hook holding the
sealed source can mutate `_result_cache` / `_query` / `model` / `_db` and return
the same object, so identity licenses no shortcut.

**Enforcing symbols.**
[`utils/querysets.py::apply_type_visibility_sync`][querysets] #"No identity fast path";
[`::apply_type_visibility_async`][querysets] #"No identity fast path";
[`::_seal_or_defect`][querysets] #"Reproduce exactly what" (the rebuild copies
forward MINUS `_result_cache` / `_known_related_objects`).

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests] sync +
async mutate-and-return-same-object regressions across the sensitive state
families.

**Deliberation.** The rejected identity shortcut, the rejected
unoverridden-default-hook narrowing, and the reason
`_known_related_objects` is dropped rather than copied are recorded in the
[rationale companion][rationale].

### Decision 4 — `Prefetch` rebuild as an exact Django class + alias threading with `require_shared_alias`

**Decision.** Every `Prefetch` entry — including the `queryset=None` case — is
rebuilt from scratch as an exact `django.db.models.Prefetch` (via
`Prefetch.__new__`, copying only the exact-`str` / `None` path state
`prefetch_through` / `prefetch_to` / `to_attr`), so a consumer `Prefetch`
subclass cannot survive with an executable `get_current_querysets` override.
Non-`Prefetch` lookup entries must be EXACTLY `str`. Each inner queryset is
recursively sealed through `_seal_or_defect`; the outer effective alias is
threaded into the child seal with `require_shared_alias=True` so a child
explicitly routed off a DIFFERENT alias fails closed, and — critically — when the
outer alias is UNRESOLVED (`None`, an unrouted parent) an explicitly routed child
also fails closed, while an unrouted child inherits the outer alias. The child
seal runs `allow_sliced=True` (a top-N-per-parent prefetch queryset is legal and
nothing refilters it) with `require_model_rows` still in force. This is
[Prefetch alias threading][glossary-prefetch-alias-threading].

**Enforcing symbols.**
[`utils/querysets.py::_rebuilt_prefetch_or_defect`][querysets];
[`::_sealed_prefetch_related_lookups`][querysets];
[`::_seal_or_defect`][querysets] #"effective_alias" (resolves the outer alias and
passes `require_shared_alias`).

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests]
Prefetch-subclass substitution and cross-alias-child cases; the evaluation-level
relation surfaces in [`tests/test_relay_node_field.py`][relay-tests] /
[`tests/test_connection.py`][connection-tests].

**Deliberation.** The rejected copy-the-consumer-`Prefetch` alternative, the
rejected unpinned child seal, and the symmetric unrouted-parent rule are recorded
in the [rationale companion][rationale].

### Decision 5 — Queryset-shape rejections + unconditional `Query.model`

**Decision.** The seal fails closed on: a sliced query on every recomposing read
surface (`sliced` defect; `allow_sliced=True` suppresses ONLY this rejection for
the prefetch child and the optimizer walker's degrade-to-unplanned nested path); a
non-`ModelIterable` `_iterable_class` on model-row surfaces (`projection` defect,
membership tested by object identity against `_DJANGO_ITERABLE_CLASSES`, never
`in` on a frozenset which would hash the candidate); a foreign `_query` type or a
foreign `combined_queries` branch, a foreign row iterable, an unresolvable /
malformed deferred filter, or an unsealable prefetch child (`untrusted` defect); a
contributing table that is not the registered concrete table (`table` defect).
`Query.model` is now validated UNCONDITIONALLY via `_concrete_or_none` on the
outer query and every combined branch — a `None` or non-model `Query.model` fails
closed as a `table` defect instead of escaping as `SELECT  FROM ...` malformed
SQL. `_concrete_or_none` requires an actual Django MODEL CLASS before it reads any
metadata — duck-typing an object that merely exposes `_meta.concrete_model` let
malformed state be installed as the sealed queryset's `.model`, which every
downstream reader treats as a model class — so class-ness and model ancestry are
proven before a consumer `_meta` / `concrete_model` descriptor could run.

A pending `_deferred_filter` on an EXACT plain `QuerySet` is baked onto the
DETACHED clone through the unbound `sql.Query.add_q` after every argument is
proven inert / genuine-Django (the candidate is never mutated); a subclass
carrying a pending filter fails closed, as does a malformed shape Django never
produces — a non-3-tuple, non-`dict` kwargs, non-sequence args, a non-`str` kwarg
key, or a kwarg naming one of the `models.Q.__init__` internals Django itself
prohibits in a filter call (`_connector` / `_negated`). Django 6.0 exposes those
names as `django.db.models.query.PROHIBITED_FILTER_KWARGS`; the declared
`Django>=5.2` floor rejects the same names inline with no module-level constant,
so the import is guarded and the frozenset mirrored verbatim and the gate behaves
identically at the floor.

**Enforcing symbols.**
[`utils/querysets.py::_combined_query_table_defect`][querysets] (unconditional
`Query.model` validation + combined-branch recursion);
[`::_concrete_or_none`][querysets];
[`::_seal_or_defect`][querysets] #"is_sliced" and #"_DJANGO_ITERABLE_CLASSES"
(slice / projection / iterable rejections);
[`::_bake_deferred_filter_or_defect`][querysets] and
[`::_deferred_value_defect`][querysets] (deferred-filter safety); the
`allow_sliced` threading in
[`django_strawberry_framework/optimizer/walker.py::_build_child_queryset`][walker]
and the gate
[`django_strawberry_framework/optimizer/nested_fetch.py::unwindowable_child_queryset_reason`][nested-fetch].

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests]
shape-defect cases (model-`None`, a non-model class and an object both exposing a
convincing `_meta.concrete_model`, sliced, values projection, custom iterable,
wrong table, foreign branch, deferred-filter malformed/hostile); the walker
`allow_sliced` path exercised through the nested-connection optimizer tests.

**Deliberation.** The rejected base-table-gated `Query.model` check, the rejected
`in`-on-a-frozenset membership test, the rejected duck-typed `_concrete_or_none`,
and the rejected use of Django's `QuerySet.query` getter to resolve a deferred
filter are recorded in the [rationale companion][rationale].

### Decision 6 — Typed `ConfigurationError` fail-closed error contract

**Decision.** Every defect surfaces as a typed
[`ConfigurationError`][glossary-configurationerror] (never a raw backend
`OperationalError`, `TypeError`, `AttributeError`, or unclosed coroutine). Defect
codes run the one canonical ordering `type` -> `table` -> `untrusted` ->
`sliced` -> `projection` -> `alias`, each mapped to bespoke consumer-facing
wording, with ONE documented exception: the outer exact-`sql.Query` check emits
`untrusted` BEFORE the combinator table walk can emit `table`, because that walk
reads query attributes through ordinary attribute access and only a
proven-genuine `sql.Query` may be walked. A caller-supplied `render_error` seam
lets the cascade keep its path-rich per-edge prose. The sync boundary reserves the
[`SyncMisuseError`][glossary-syncmisuseerror] subclass (`ConfigurationError` +
`RuntimeError`) for an async hook met in a sync context; the async runner rejects
a nested awaitable after one await.

**Enforcing symbols.**
[`utils/querysets.py::_visibility_result_error`][querysets] (defect-code ->
`ConfigurationError` mapping + `render_error` seam);
[`::_prepared_visibility_source`][querysets] (source-side typed errors);
[`::SyncMisuseError`][querysets] and [`::reject_async_in_sync_context`][querysets];
[`django_strawberry_framework/exceptions.py::ConfigurationError`][exceptions].

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests] per-code
error-message assertions; [`tests/test_permissions.py`][permissions-tests] for
the cascade `render_error` path.

**Deliberation.** The rejected propagate-backend-exceptions behavior, the rejected
per-code exception taxonomy, and the reason the cascade's prose lives behind a
`render_error` seam rather than inside the shared checker are recorded in the
[rationale companion][rationale].

### Decision 7 — No version bump: the `0.0.14` cut already landed

**Decision.** This card carries none of the version quintet. `0.0.14` was cut by
the joint release commit `6a86d21f` ("release: 0.0.14 joint cut"), which shipped
the sealed boundary (commit `60998b17`) alongside its sibling `0.0.14` cards. A
follow-on documentation card at an already-cut patch line owns no bump; the
`pyproject.toml` `[project].version`, `django_strawberry_framework/__init__.py`
`__version__`, and `tests/base/test_init.py` are untouched here.

**Deliberation.** The rejected joint-cut-owner shape is recorded in the
[rationale companion][rationale].

### Decision 8 — Threat model: a mistaken hook, not an in-process adversary; canonical reconstruction terminates the dispatch-path expansion

**Decision.** The [visibility boundary][glossary-visibility-boundary] defends
against a consumer [`get_queryset` visibility
hook][glossary-get_queryset-visibility-hook] that is **wrong**, not against an
attacker who is already executing arbitrary Python inside the server process.

*In scope* — any query state the framework cannot prove it owns: a dropped or
rewritten visibility predicate, a foreign or instance-shadowed queryset /
`Query` object, a contributing table or `Query.model` that is not the registered
concrete one, a sliced or `.values()` shape on a recomposing surface, an
injected `_result_cache`, a re-routed alias, an unprovable node anywhere in the
compiler-reachable graph, and any mutable AST node or payload container the
sealed query would otherwise SHARE with the candidate graph.

*Out of scope* — a consumer who deliberately crafts an object to reach a Django
or database-adapter dispatch site. That party already runs code in the process:
they can rewrite the compiler, the ORM, or this boundary itself, so no walk
performed inside the same interpreter is a trust boundary against them. This is
the same stance the framework already takes on process-wide monkeypatching,
which is unsupported by contract for exactly this reason.

**Consequently the boundary is CLOSED to further dispatch-path expansion.** A
newly identified way for a deliberately crafted object to reach `__str__`,
`__index__`, an adapter hook, or any other dispatch site is **not** a defect of
this boundary and does not justify widening the walk. What still does justify a
change: a path reachable by ORDINARY consumer code that loses the visibility
predicate or returns rows the hook excluded; a Django release adding a
compiler-reachable slot that LEGITIMATE queries populate; or a demonstrated
row-visibility leak.

The mechanism that makes this termination sound — rather than a decision to stop
looking — is **canonical reconstruction**. The sealed query is not the candidate's
object graph proven safe; it is a framework-owned rebuild. After the graph proofs
pass, every mutable builtin container and every genuine Django AST node in the
clone's state is re-instantiated as a fresh object of its own proven class through
`object.__new__` and refilled slot by slot from the validated state, under an
identity memo so a node reached twice rebuilds once and the sealed graph keeps the
candidate's sharing topology. Reconstruction never calls a node's own `clone()` /
`copy()` (shallow — it would keep sharing the children) and never `deepcopy`
(it would dispatch a consumer value's `__deepcopy__` / `__reduce__` mid-seal).
Each admitted plain-data bound value is normalized to an EXACT inert value (a
`TextChoices` member becomes an exact `str`, a `date` subclass an exact
`datetime.date`), read through the base type's own descriptors and C slots so
neither an overridden dunder nor a property shadowing a field name can run during
normalization. A subclass that cannot be reduced to an exact inert value fails
closed as an `untrusted` defect.

**What the sealed query still shares with the candidate, exhaustively.** The
sealed query holds no consumer-owned AST node and no consumer-owned mutable
container. What it shares is:

- exact inert scalar leaves — bound parameters the adapter renders as `%s`, whose
  every method is the interpreter's own;
- the trusted schema: `models.Field` instances and model classes, which are the
  queried model's own definitions rather than state the hook injected, and whose
  rebuild would detach the compiler from the model's own descriptors;
- a `models.Model` instance in bound-value position, which IS the bound value and
  from which Django's own code extracts a pk;
- a bound-value slot the graph proofs do not route through the direct-lookup rule
  — an expression's own plain-data payload, `Value.value` being the instance. A
  `Value`'s `get_source_expressions()` returns no children, so the walk never
  reaches that slot, and normalization replaces only a value descending from a
  plain-data base; anything else in it is retained by reference. Reaching this
  requires binding a non-plain-data object into an expression payload, which is a
  crafted-object path and therefore out of scope above; the value is bound as a
  `%s` parameter and cannot alter SQL structure. It is recorded here rather than
  claimed closed.

A direct `Lookup` right-hand side is NOT in that list: it is validated
(`_direct_rhs_defect` — an inert leaf, a plain container of them, or a value that
defines no attribute hook of its own and descends from a plain-data base) and then
normalized, so what the sealed query binds there is a framework-owned exact value.

**Cost.** Canonical reconstruction measured roughly 1.7x on simple and medium
queries and 2.3x on an annotation-heavy shape, against sealing without it.

**Enforcing symbols.** [`utils/querysets.py::_rebuild_query_payloads`][querysets]
(the reconstruction pass over the clone's state);
[`::_reconstructed_value`][querysets] and
[`::_is_reconstructable_node`][querysets] (the rebuild-versus-retain policy);
[`::_reconstruction_defect`][querysets] (keeps reconstruction inside the typed
fail-closed contract); [`::_normalized_bound_value`][querysets] and
`::_BOUND_VALUE_NORMALIZERS` (exact-value normalization through base-type
descriptors); [`::_lookup_operands_defect`][querysets],
[`::_direct_rhs_defect`][querysets], [`::_rhs_hook_defect`][querysets] and
[`::_static_attr_present`][querysets] (a lookup's operands read from raw state
instead of its own discovery accessor); [`::_template_params_defect`][querysets]
(the `extra` template mapping `as_sql` interpolates).

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests]:
`test_mutating_a_candidate_where_leaf_cannot_change_the_sealed_predicate` and its
annotation / filtered-relation / raw-SQL-parameter / `bytearray` siblings,
`test_sealed_query_shares_no_ast_node_with_the_candidate`,
`test_sealed_query_retains_its_schema_objects_by_reference`,
`test_lookup_direct_rhs_date_subclass_normalizes_to_exact_date`,
`test_lookup_direct_rhs_attribute_hook_never_dispatches`, and
`test_func_extra_template_parameter_object_fails_closed`.

**Deliberation.** The rejected per-finding walk expansion, the rejected revert of
the post-`0.0.14` hardening, the rejected `clone()` / `copy()` / `deepcopy` rebuild
strategies, the rejected exact-type admission rule for a bound value, and the
rejected use of `get_source_expressions()` to discover a lookup's operands are
recorded in the [rationale companion][rationale], together with the history of the
bound-parameter residual above.

## Error shapes

The defect-code table the shared checker emits, in the canonical evaluation order
[Decision 6](#decision-6--typed-configurationerror-fail-closed-error-contract)
states (including its one documented exception, the outer exact-`sql.Query`
`untrusted` check preceding the `table` walk), each rendered by
[`::_visibility_result_error`][querysets] (or the caller's `render_error` seam):

| Code | Fails when | Consumer-facing wording (default) |
|---|---|---|
| `type` | hook returned a non-QuerySet/Manager (list, generator, `None`) | "must return a QuerySet or Manager of `<Model>` rows" |
| `table` | contributing table is not the registered concrete table, or `Query.model` is `None`/non-model | "composes over `<Model>`'s concrete table" |
| `untrusted` | foreign `Query` class, foreign row iterable, unresolved deferred filter, unsealable prefetch child | "cannot be sealed into a framework-owned execution queryset" |
| `sliced` | sliced query on a recomposing read surface | "Django forbids refiltering or reordering a sliced query" |
| `projection` | non-`ModelIterable` `_iterable_class` on a model-row surface | "composes over `<Model>` model rows, not a `.values()` projection" |
| `alias` | child routed off an alias that differs from the pinned resolution | "cannot re-route a pinned resolution; remove the `.using(...)` call" |

## Test plan

The seal / row-survival matrix that already ships (maintainer-invoked gates only,
per `AGENTS.md`):

- [`tests/utils/test_querysets.py`][queryset-tests] — the shared seal / rebuild
  suite: provenance, callable-shadow, expression-graph, container, shape-defect,
  deferred-filter, prefetch alias-threading, per-code error-message, and sync +
  async cache-removal cases.
- [`tests/test_relay_node_field.py`][relay-tests],
  [`tests/test_connection.py`][connection-tests],
  [`tests/test_list_field.py`][list-tests] — evaluation-level row-survival
  surfaces (the sealed boundary must not drop legitimate rows).
- [`tests/test_permissions.py`][permissions-tests] — the cascade `render_error`
  path.
- `django_strawberry_framework/utils/querysets.py` sits inside the repository's
  `fail_under = 100` coverage gate, so every branch the decisions above add is
  covered or the gate fails.

## Doc updates

This card's Slice 1 doc set (the only surface it touches):

- `docs/GLOSSARY.md` via the glossary DB + re-render (never hand-edited): the
  five new terms authored, the four existing terms relinked.
- `KANBAN.md` / `KANBAN.html` via the kanban DB + re-render: this card in Done
  with its glossary links.
- The prior `[P2]` policy-artifact residual recorded as closed in this spec.
- This spec and its two companions,
  `docs/SPECS/appx/spec-045-visibility_boundary-0_0_14-terms.csv` (glossary terms) and
  [`docs/SPECS/appx/spec-045-visibility_boundary-0_0_14-rationale.md`][rationale] (the
  deliberative layer).

`README.md`, `docs/README.md`, `docs/TREE.md`, `GOAL.md`, `TODAY.md`, and
`CHANGELOG.md` are untouched: the boundary is internal security-boundary
hardening with no consumer-visible surface change, and the `0.0.14` release entry
already shipped.

## Constraints on the supported query surface

These are deliberate constraints of the contract above, not defects:

- **Consumer-defined expressions and lookups are unsupported across the
  boundary.** A genuinely custom `Func` or `Lookup` fails closed as `untrusted`. A
  consumer needing a custom expression in a visibility filter expresses it through
  genuine Django primitives. The constraint is documented here and in the
  [prove-then-clone AST trust][glossary-prove-then-clone-ast-trust] glossary entry.
- **The boundary is closed to further dispatch-path expansion** on the terms
  [Decision 8](#decision-8--threat-model-a-mistaken-hook-not-an-in-process-adversary-canonical-reconstruction-terminates-the-dispatch-path-expansion)
  states, which also names what still does justify a change.
- **One bound-value slot is retained rather than normalized** — an expression's own
  plain-data payload, `Value.value` being the instance — for the reasons and with
  the bounds Decision 8 records.

## Out of scope (explicitly tracked elsewhere)

- Any behavior change to the boundary — this card is documentation only; the
  boundary's code ships in its own commits, `60998b17` onward.
- A future allowlist of vetted consumer expression types, should the
  custom-expression constraint above ever prove too tight. No card carries it.

## Definition of done

- [ ] Numbered security decisions authored (above) covering the changed
      contract: untrusted-object rebuild, prove-then-clone AST trust,
      identity-fast-path removal, `Prefetch` rebuild + alias threading,
      queryset-shape rejections, and the typed error contract.
- [ ] Spec `docs/SPECS/spec-045-visibility_boundary-0_0_14.md` authored with its
      companions `*-terms.csv` and `*-rationale.md`.
- [ ] The five new glossary entries imported via the fakeshop glossary DB and
      `docs/GLOSSARY.md` regenerated.
- [ ] `KANBAN.md` / `KANBAN.html` regenerated from the kanban DB with this card
      in Done.
- [ ] The prior `[P2]` policy-artifact residual recorded as closed here.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[glossary]: ../GLOSSARY.md
[glossary-apply_cascade_permissions]: ../GLOSSARY.md#apply_cascade_permissions
[glossary-callable-shadow-defect]: ../GLOSSARY.md#callable-shadow-defect
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-get_queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-prefetch-alias-threading]: ../GLOSSARY.md#prefetch-alias-threading
[glossary-prove-then-clone-ast-trust]: ../GLOSSARY.md#prove-then-clone-ast-trust
[glossary-sealed-execution-queryset]: ../GLOSSARY.md#sealed-execution-queryset
[glossary-syncmisuseerror]: ../GLOSSARY.md#syncmisuseerror
[glossary-visibility-boundary]: ../GLOSSARY.md#visibility-boundary

<!-- docs/SPECS/ -->

[rationale]: appx/spec-045-visibility_boundary-0_0_14-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

[exceptions]: ../../django_strawberry_framework/exceptions.py
[nested-fetch]: ../../django_strawberry_framework/optimizer/nested_fetch.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

[connection-tests]: ../../tests/test_connection.py
[list-tests]: ../../tests/test_list_field.py
[permissions-tests]: ../../tests/test_permissions.py
[queryset-tests]: ../../tests/utils/test_querysets.py
[relay-tests]: ../../tests/test_relay_node_field.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
