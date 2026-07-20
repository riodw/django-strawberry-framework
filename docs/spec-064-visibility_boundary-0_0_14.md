# Spec: Sealed `get_queryset` visibility-boundary policy artifacts — the governing security decisions, spec, and glossary for the framework-owned execution queryset

Built for `0.0.14` (card `DONE-064-0.0.14`). This is a **documentation-only**
slice over an already-landed implementation: commit `60998b17`
("feat(visibility): seal get_queryset hook results into framework-owned
querysets") shipped the sealed [visibility boundary][glossary-visibility-boundary],
and the adversarial review recorded in [`docs/feedback.md`][feedback] closed
every P1/P2 correctness finding in its `## Resolution` (2026-07-20). Only the
policy artifacts — a governing set of numbered security decisions, this spec, a
KANBAN card, and the [glossary][glossary] fold-in — were deferred to a shipping
slice. This card discharges that deferral so the standing documentation matches
the implemented security contract.

Status: **COMPLETE — shipped in `0.0.14` (commit `60998b17`); this card records
the governing artifacts.** The Slice checklist boxes below stay unticked because
the `Status:` line is the completion source of truth (the shipped-spec
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
  - [ ] This spec `docs/spec-064-visibility_boundary-0_0_14.md` and its
        companion `*-terms.csv`.
  - [ ] The five new glossary entries imported via the fakeshop glossary DB and
        `docs/GLOSSARY.md` regenerated (never hand-edited).
  - [ ] `KANBAN.md` / `KANBAN.html` regenerated from the kanban DB with this
        card in Done.
  - [ ] The `[P2]` policy residual in `docs/feedback.md` recorded as closed.

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

- The sealed boundary shipped in commit `60998b17`;
  [`django_strawberry_framework/utils/querysets.py`][querysets] is at 100%
  coverage under the `fail_under = 100` gate.
- Both the source (before the hook) and the hook result (after) are rebuilt into
  a framework-owned plain `django.db.models.QuerySet`; the consumer object is
  never returned.
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
- Close the deferred `[P2]` policy residual in `docs/feedback.md`.

## Non-goals

- **No behavior change.** This card is documentation only; the sealing code
  already shipped and is unchanged by it.
- **No new abstraction adopted here.** Canonical-reconstruction (rebuilding the
  SQL from a validated canonical form rather than proving-then-cloning Django's
  live objects) is flagged as the future root fix, not adopted
  ([Risks](#risks-and-open-questions)).
- **No version bump.** `0.0.14` was already cut by the joint release
  ([Decision 7](#decision-7--no-version-bump-the-0014-cut-already-landed)).

## Borrowing posture

None. The sealed boundary is internal security-boundary hardening with no
upstream peer: neither `graphene-django` nor `strawberry-graphql-django` ships a
comparable framework-owned-execution-queryset primitive, so there is no
borrowing posture to pin. The contract is derived entirely from Django's own
`django.db.models.sql.Query` compile surface and the adversarial review.

## Architectural decisions

The six decisions below are the governing security decisions for the boundary.
Each is pinned to the enforcing symbols in
[`django_strawberry_framework/utils/querysets.py`][querysets] and the tests that
hold it.

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

**Why.** Closes the review's core premise — the method-inventory-is-the-wrong-
abstraction conclusion driving all four P1 findings.

**Alternative rejected.** Keeping the class-level method inventory and returning
the consumer object: disproved by the zero-SQL probes (instance-shadowed `.all()`,
replaced instance-level `Query.chain`, subclass `.filter()` / `_values` /
`.first()` / `.__aiter__()`), each of which erased the predicate after the
inventory passed.

**Enforcing symbols.**
[`utils/querysets.py::_seal_or_defect`][querysets] (the single sealing
primitive: extracts state via `object.__getattribute__`, clones once through the
unbound `sql.Query.clone`, constructs a plain `models.QuerySet`);
[`::_prepared_visibility_source`][querysets] (seals the source before the hook
runs); [`::_normalized_visibility_result`][querysets] (seals the hook result).

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
exact builtin: (a) genuine-Django provenance is proven by OBJECT IDENTITY against
`sys.modules[module].<qualname>`, never the spoofable `__module__` string,
reading `__module__` / `__qualname__` through `type.__getattribute__` so a
consumer metaclass cannot lie; (b) any instance-`__dict__` key naming a callable
class attribute (`chain` / `clone` / `as_sql` / a dynamic `as_<vendor>` emitter /
any) fails closed BEFORE the clone (the [callable shadow
defect][glossary-callable-shadow-defect]); (c) the `where` / `having` trees and
their leaf operands, `annotations` (incl. nested `Func` / `Case` operands and
inner `Subquery` graphs), the `order_by` / `group_by` / `distinct_fields` /
`select` / `values_select` sequences, the `extra_order_by` / `extra_tables`
raw-SQL slots, the `alias_map` joins (and any join's `filtered_relation` resolved
condition), and `select_related` are each walked once under a single recursive
id-memoized traversal; inert parameter leaves terminate by EXACT type (a `str` /
`int` / `datetime` subclass carrying `resolve_expression` is NOT inert).
SQL-template metadata (`template` / `function` / `arg_joiner` / `connector` /
`sql` / `base_template`) present on an instance must be exactly `str`.

**Why.** Closes `[P1]` "The sealed `Query` retains instance-level method
replacements", `[P1]` "Executable objects nested inside an exact `sql.Query` run
during sealing", and the Resolution's named sub-vectors (poisoned `base_table`
cache, spoofed `__module__`, `Func` metadata, `extra_order_by`, dynamic
`as_<vendor>`, combined-queries tuple, subquery inner query).

**Alternative rejected.** Trusting `__module__` strings or an "is `clone`
dispatch-free?" premise — both disproved: `__module__` is a writable class
attribute a consumer metaclass can spoof, and `sql.Query.clone`'s body
demonstrably dispatches `where.clone()` / container `.copy()` and defers
`as_sql` to compile time.

**Enforcing symbols.**
[`utils/querysets.py::_type_is_genuinely_django`][querysets] (object-identity
provenance); [`::_shadow_defect`][querysets] (callable-shadow and `as_<vendor>`
rejection); [`::_expr_graph_defect`][querysets], [`::_where_tree_defect`][querysets],
[`::_join_defect`][querysets], [`::_expr_sequence_defect`][querysets],
[`::_raw_sql_sequence_defect`][querysets], [`::_node_metadata_defect`][querysets],
[`::_select_related_defect`][querysets], [`::_query_container_defect`][querysets],
[`::_query_ast_defect`][querysets], [`::_query_genuineness_defect`][querysets]
(the recursive walk and its helpers);
[`::_base_table_defect`][querysets] (reads the authoritative base table from the
initialized `alias_map`, not the poisonable `base_table` cache).

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests]
hostile-node cases (named in the source docstrings, e.g.
`test_hostile_subquery_inner_query_fails_closed`,
`test_hostile_expression_inside_genuine_subquery_where_fails_closed`); the
connection row-survival case
`tests/test_connection.py::test_connection_query_chain_shadow_hook_is_sealed`
([connection tests][connection-tests]).

### Decision 3 — The identity fast path is removed; hook results are always re-sealed and result caches dropped

**Decision.** Both runners previously skipped result normalization when the hook
returned the exact source object it received. That fast path is gone:
`apply_type_visibility_sync` and `apply_type_visibility_async` ALWAYS re-seal the
hook result through `_normalized_visibility_result` (no `result is queryset`
shortcut). The rebuild never copies `_result_cache`, and `_known_related_objects`
is deliberately dropped, so an injected cached row (synthetic or otherwise)
cannot cross the boundary.

**Why.** Closes `[P1]` "The identity-hook fast path bypasses result sealing and
cache removal" — identity does not prove immutability; a hook holding the sealed
source could mutate `_result_cache` / `_query` / `model` / `_db` and return the
same object.

**Alternative rejected.** Keeping the `result is queryset` fast path as a
performance shortcut — rejected because object identity is not immutability, and
the shortcut is exactly what the mutate-and-return-same-object probe exploited.

**Enforcing symbols.**
[`utils/querysets.py::apply_type_visibility_sync`][querysets] #"No identity fast
path"; [`::apply_type_visibility_async`][querysets] #"No identity fast path";
[`::_seal_or_defect`][querysets] #"Reproduce exactly what" (the rebuild copies
forward MINUS `_result_cache` / `_known_related_objects`).

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests] sync +
async mutate-and-return-same-object regressions (the old identity assertions were
replaced with cache-removal regressions across the sensitive state families).

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

**Why.** Closes `[P1]` "`Prefetch` sealing leaves executable wrappers and
cross-alias child queries" (both the surviving-subclass and the `shard_b` parent /
`default` child divergence).

**Alternative rejected.** Copying the consumer `Prefetch` instance forward (even
after validating its path state) — rejected because a `Prefetch` subclass
overriding `get_current_querysets` substitutes an unsealed child queryset at
fetch time, after any instance-level validation.

**Enforcing symbols.**
[`utils/querysets.py::_rebuilt_prefetch_or_defect`][querysets];
[`::_sealed_prefetch_related_lookups`][querysets];
[`::_seal_or_defect`][querysets] #"effective_alias" (resolves the outer alias and
passes `require_shared_alias`).

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests]
Prefetch-subclass substitution and cross-alias-child cases; the evaluation-level
relation surfaces in [`tests/test_relay_node_field.py`][relay-tests] /
[`tests/test_connection.py`][connection-tests].

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
SQL. A pending `_deferred_filter` on an EXACT plain `QuerySet` is baked onto the
DETACHED clone through the unbound `sql.Query.add_q` after every argument is
proven inert / genuine-Django (the candidate is never mutated); a subclass
carrying a pending filter fails closed.

**Why.** Closes `[P2]` "`Query.model = None` is accepted and escapes as malformed
SQL" and records the shape-rejection contract the review's "Confirmed
improvements" enumerate.

**Alternative rejected.** A `Query.model` check gated on the query already having
a base table (the pre-fix behavior) — rejected because a query with no base table
and `model = None` escaped the gate and compiled to malformed `SELECT  FROM`.

**Enforcing symbols.**
[`utils/querysets.py::_combined_query_table_defect`][querysets] (unconditional
`Query.model` validation + combined-branch recursion);
[`::_concrete_or_none`][querysets];
[`::_seal_or_defect`][querysets] #"is_sliced" and #"_DJANGO_ITERABLE_CLASSES"
(slice / projection / iterable rejections);
[`::_bake_deferred_filter_or_defect`][querysets] and
[`::_deferred_value_defect`][querysets] (deferred-filter safety); the
`allow_sliced` threading in
[`django_strawberry_framework/optimizer/walker.py #"_build_child_queryset"`][walker]
and the gate
[`django_strawberry_framework/optimizer/nested_fetch.py #"unwindowable_child_queryset_reason"`][nested-fetch].

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests]
shape-defect cases (model-`None`, sliced, values projection, custom iterable,
wrong table, foreign branch, deferred-filter malformed/hostile); the walker
`allow_sliced` path exercised through the nested-connection optimizer tests.

### Decision 6 — Typed `ConfigurationError` fail-closed error contract

**Decision.** Every defect surfaces as a typed
[`ConfigurationError`][glossary-configurationerror] (never a raw backend
`OperationalError`, `TypeError`, `AttributeError`, or unclosed coroutine). Defect
codes run the one canonical ordering `type` -> `table` -> `untrusted` ->
`sliced` -> `projection` -> `alias`, each mapped to bespoke consumer-facing
wording; a caller-supplied `render_error` seam lets the cascade keep its
path-rich per-edge prose. The sync boundary reserves the
[`SyncMisuseError`][glossary-syncmisuseerror] subclass (`ConfigurationError` +
`RuntimeError`) for an async hook met in a sync context; the async runner rejects
a nested awaitable after one await.

**Why.** Records the error contract the changed surface introduces, keeping
`ConfigurationError` as the single typed boundary error.

**Alternative rejected.** Letting backend / interpreter exceptions propagate
(the pre-fix behavior for several defects) — rejected because an
`OperationalError` from malformed SQL leaks nothing actionable to the consumer
and is not a fail-closed contract.

**Enforcing symbols.**
[`utils/querysets.py::_visibility_result_error`][querysets] (defect-code ->
`ConfigurationError` mapping + `render_error` seam);
[`::_prepared_visibility_source`][querysets] (source-side typed errors);
[`::SyncMisuseError`][querysets] and [`::reject_async_in_sync_context`][querysets];
[`django_strawberry_framework/exceptions.py::ConfigurationError`][exceptions].

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests] per-code
error-message assertions; [`tests/test_permissions.py`][permissions-tests] for
the cascade `render_error` path.

### Decision 7 — No version bump: the `0.0.14` cut already landed

**Decision.** This card carries none of the version quintet. `0.0.14` was cut by
the joint release commit `6a86d21f` ("release: 0.0.14 joint cut"), which shipped
the sealed boundary (commit `60998b17`) alongside its sibling `0.0.14` cards. A
follow-on documentation card at an already-cut patch line owns no bump; the
`pyproject.toml` `[project].version`, `django_strawberry_framework/__init__.py`
`__version__`, and `tests/base/test_init.py` are untouched here.

**Alternative rejected.** Treating this card as the joint-cut owner (the
lone-card version-bump shape) — rejected because the `0.0.14` cut demonstrably
already landed before this documentation card was authored.

## Error shapes

The defect-code table the shared checker emits, in canonical evaluation order,
each rendered by [`::_visibility_result_error`][querysets] (or the caller's
`render_error` seam):

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
- `django_strawberry_framework/utils/querysets.py` at 100% under
  `fail_under = 100`.

## Doc updates

This card's Slice 1 doc set (the only surface it touches):

- `docs/GLOSSARY.md` via the glossary DB + re-render (never hand-edited): the
  five new terms authored, the four existing terms relinked.
- `KANBAN.md` / `KANBAN.html` via the kanban DB + re-render: this card in Done
  with its glossary links.
- `docs/feedback.md` `[P2]` policy residual recorded as closed.
- This spec and its companion `docs/spec-064-visibility_boundary-0_0_14-terms.csv`.

`README.md`, `docs/README.md`, `docs/TREE.md`, `GOAL.md`, `TODAY.md`, and
`CHANGELOG.md` are untouched: the boundary is internal security-boundary
hardening with no consumer-visible surface change, and the `0.0.14` release entry
already shipped.

## Risks and open questions

- **Prove-then-clone is whack-a-mole over Django's compile surface.** The review's
  architectural note stands: proving-then-cloning Django's live objects is a
  moving target because every Django version can add a new compiler-reachable
  slot. The flagged future root fix is **canonical reconstruction** — deriving a
  validated canonical description of the intended query and rebuilding the SQL
  from that, rather than trusting Django's object graph and cloning it. Preferred
  answer for a future card: adopt canonical reconstruction once the boundary's
  surface is stable; fallback: keep extending the recursive walk as Django's
  compile surface grows. Not adopted in `0.0.14`.
- **Consumer-defined expressions / lookups are unsupported across the boundary.**
  A genuinely custom `Func` or `Lookup` fails closed as `untrusted`. This is a
  deliberate constraint, not a bug — a consumer needing a custom expression in a
  visibility filter must express it through genuine Django primitives. Preferred
  answer: document the constraint (this spec + the [prove-then-clone AST
  trust][glossary-prove-then-clone-ast-trust] glossary entry); fallback: a future
  allowlist of vetted consumer expression types, explicitly out of scope here.

## Out of scope (explicitly tracked elsewhere)

- Canonical-reconstruction rearchitecture — flagged above as the future root fix;
  no card yet.
- Any behavior change to the boundary — this card is documentation only; the
  code shipped in commit `60998b17`.

## Definition of done

- [ ] Numbered security decisions authored (above) covering the changed
      contract: untrusted-object rebuild, prove-then-clone AST trust,
      identity-fast-path removal, `Prefetch` rebuild + alias threading,
      queryset-shape rejections, and the typed error contract.
- [ ] Spec `docs/spec-064-visibility_boundary-0_0_14.md` authored with its
      companion `*-terms.csv`.
- [ ] The five new glossary entries imported via the fakeshop glossary DB and
      `docs/GLOSSARY.md` regenerated.
- [ ] `KANBAN.md` / `KANBAN.html` regenerated from the kanban DB with this card
      in Done.
- [ ] The `[P2]` policy residual in `docs/feedback.md` recorded as closed.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[feedback]: feedback.md
[glossary]: GLOSSARY.md
[glossary-sealed-execution-queryset]: GLOSSARY.md#sealed-execution-queryset
[glossary-visibility-boundary]: GLOSSARY.md#visibility-boundary
[glossary-prove-then-clone-ast-trust]: GLOSSARY.md#prove-then-clone-ast-trust
[glossary-callable-shadow-defect]: GLOSSARY.md#callable-shadow-defect
[glossary-prefetch-alias-threading]: GLOSSARY.md#prefetch-alias-threading
[glossary-get_queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-apply_cascade_permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-syncmisuseerror]: GLOSSARY.md#syncmisuseerror

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

[querysets]: ../django_strawberry_framework/utils/querysets.py
[exceptions]: ../django_strawberry_framework/exceptions.py
[walker]: ../django_strawberry_framework/optimizer/walker.py
[nested-fetch]: ../django_strawberry_framework/optimizer/nested_fetch.py

<!-- tests/ -->

[queryset-tests]: ../tests/utils/test_querysets.py
[relay-tests]: ../tests/test_relay_node_field.py
[connection-tests]: ../tests/test_connection.py
[list-tests]: ../tests/test_list_field.py
[permissions-tests]: ../tests/test_permissions.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
