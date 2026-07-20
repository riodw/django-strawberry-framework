# Adversarial review: sealed `get_queryset` visibility boundary

## Verdict

**Not ready to commit, push, or release.** The local rearchitecture correctly drops the
consumer `QuerySet` subclass, rejects several malformed shapes, recursively handles the
ordinary `Prefetch(queryset=...)` case, and expands representative surface coverage. The
seal is not yet an execution boundary, however: executable state still survives inside
the cloned `Query`, the identity-hook optimization skips result sealing entirely, and
some `Prefetch` objects and cross-database child queries pass through unchanged.

Read-only Django probes reproduced direct predicate loss, synthetic cached-row return,
consumer code dispatch during `Query.clone()`, executable `Prefetch` survival, and a
cross-alias prefetch child. Two newly added regressions for the `Query.chain` case are
therefore inconsistent with the implementation and should fail once the relevant test
modules run.

Review target: every tracked local change against `HEAD` in the shared queryset boundary,
cascade integration, list/connection/Relay integrations, tests, and standing
documentation. The untracked auth-session plan is a separate planning artifact and has
no runtime implementation to review. This review overwrites only `docs/feedback.md`.
The mandatory repository-wide formatter also reformatted the already-dirty
`tests/utils/test_querysets.py`; no semantic test edit was made by the review.

## Release-blocking findings

### [P1] The sealed `Query` retains instance-level method replacements

Affected symbols:

- [`django_strawberry_framework/utils/querysets.py::_seal_or_defect`][querysets]
- [`django_strawberry_framework/permissions.py::_validated_target_subquery`][permissions]
- [`django_strawberry_framework/types/relay.py::_apply_node_filter`][relay-types]
- [`django_strawberry_framework/connection.py::_finalize_queryset`][connection]

`_seal_or_defect` calls the unbound `sql.Query.clone(query)`, but Django's implementation
begins by shallow-copying the complete `Query.__dict__`. An instance attribute named
`chain` is therefore copied into the new exact `sql.Query`. The first ordinary operation
on the supposedly sealed queryset (`filter`, `values`, `values_list`, `order_by`,
`only`, slicing, and many others) reaches `QuerySet._clone()`, which dispatches through
that copied `query.chain` attribute.

A zero-SQL probe returned a queryset with a real `is_private=False` predicate and an
instance-level `query.chain` that returned an unfiltered `Query`. The boundary returned
an exact plain `QuerySet`, but the replacement remained:

```text
sealed type: django.db.models.query.QuerySet
"chain" in sealed.query.__dict__: True
sealed SQL:       ... WHERE NOT "products_category"."is_private"
after values_list: SELECT "products_category"."name" ... FROM "products_category"
```

The next framework transform erased the visibility predicate. Relay id filtering,
connection ordering/slicing, filter/order sets, optimizer projection, and cascade
re-projection all perform such transforms after visibility, so this is a direct
system-wide escape.

The new tests
[`tests/utils/test_querysets.py::test_query_chain_shadow_hook_serves_only_visible_rows_sync`][queryset-tests]
and
[`tests/test_connection.py::test_connection_query_chain_shadow_hook_is_sealed`][connection-tests]
expect the opposite behavior. Their own setup installs this exact replacement, and their
next `values_list`/connection transform dispatches it.

Required root fix:

- Do not carry arbitrary callable entries from the source `Query.__dict__` into the
  execution query. The trusted object must not retain any instance attribute capable of
  shadowing `Query` behavior after the seal.
- Make the proof cover every later transform through the object actually returned to
  callers; invoking one trusted method during construction is insufficient if the clone
  still contains an executable shadow.
- Add a structural assertion that the sealed query contains no callable shadow for any
  class behavior, plus row-survival tests through Relay filtering, cascade `.values()`,
  connection ordering/slicing/counting, and optimizer transforms.
- Do not fix only the literal `chain` name. Any instance-level method shadow copied into
  a mutable execution object recreates the same abstraction error.

### [P1] The identity-hook fast path bypasses result sealing and cache removal

Affected symbols:

- [`django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`][querysets]
- [`django_strawberry_framework/utils/querysets.py::apply_type_visibility_async`][querysets]

Both runners skip `_normalized_visibility_result` whenever the hook returns the exact
source object it received. Identity does not prove immutability. The hook has held the
sealed source and can mutate `_query`, `model`, `_db`, `_iterable_class`, prefetch state,
or `_result_cache` before returning it. Every result-side table, alias, projection,
iterable, query-class, and cache guarantee is skipped in this branch.

A read-only probe used an empty source query, inserted an unsaved private object into
the received queryset's `_result_cache`, and returned that same queryset. The sync
boundary returned it verbatim, and normal iteration served `synthetic-hidden` without
executing the empty SQL. The async runner has the identical branch.

This also contradicts the standing claim that cached rows never cross the visibility
boundary. The added identity tests prove only object identity; they lock in the bypass
rather than a security invariant.

Required root fix:

- Remove the identity fast path and always seal the hook result after consumer code has
  returned. The second seal is the point that drops result caches and validates all
  post-hook state.
- If a performance fast path is retained, restrict it to a provably unoverridden package
  default hook and prove that no consumer code ran between source sealing and return.
  `result is queryset` alone is not such proof.
- Replace the identity assertions with sync/async regressions that mutate each sensitive
  state family and prove either a fresh safe seal or a typed failure.

### [P1] Executable objects nested inside an exact `sql.Query` run during sealing

Affected symbols:

- [`django_strawberry_framework/utils/querysets.py::_seal_or_defect`][querysets]
- [`django_strawberry_framework/utils/querysets.py::_combined_query_table_defect`][querysets]

Checking `type(query) is sql.Query` does not make the query graph exact or inert.
`sql.Query.clone(query)` calls `self.where.clone()`, recursively clones combined
branches, deep-copies `select_related`, and shallow-copies annotations, aliases, joins,
expressions, and other embedded objects. Those nodes can be consumer subclasses with
overridden clone/compile behavior.

A zero-SQL probe kept the outer query as the exact Django `sql.Query`, replaced only its
`where` node with a `WhereNode` subclass whose `clone()` returned an empty node, and
returned a queryset carrying `is_private=False`. `_seal_or_defect` accepted it and
dispatched the consumer clone method. The visibility predicate was gone in the queryset
returned by the boundary:

```sql
SELECT ... FROM "products_category"
```

The current statement that every state read is non-dispatching and that consumer code
never runs across the boundary is therefore false even before later framework code uses
the returned queryset.

Required root fix:

- Define and enforce a supported query-AST contract, not only an outer `Query` class
  check. Every node Django clones or later compiles must either be a trusted Django
  implementation or be rejected as unsealable.
- Apply the same recursive rule to combined branches, `where` trees, alias/join objects,
  annotations/expressions, and nested subqueries. A custom node must not execute while
  the code is still deciding whether it is trusted.
- If the package intentionally supports consumer-defined expressions/lookups, narrow the
  documented guarantee accordingly and establish a safe, explicit extension protocol;
  silently treating arbitrary executable AST nodes as inert state is not sound.
- Add a predicate-survival test using a custom nested node whose clone attempts to widen
  the query, plus a compile-time custom-node probe.

### [P1] `Prefetch` sealing leaves executable wrappers and cross-alias child queries

Affected symbols:

- [`django_strawberry_framework/utils/querysets.py::_sealed_prefetch_related_lookups`][querysets]
- [`django_strawberry_framework/utils/querysets.py::_seal_or_defect`][querysets]
- [`django_strawberry_framework/types/resolvers.py::_make_relation_resolver`][type-resolvers]

There are two independent defects in the recursive prefetch path.

First, a `Prefetch` is rebuilt as an exact Django object only when its stored `queryset`
is non-`None`. A consumer `Prefetch` subclass with `queryset=None` is appended unchanged.
Django later calls methods such as `get_current_querysets()` on that same object while
prefetching. A read-only probe showed a `HostilePrefetch("items")` surviving the seal as
`HostilePrefetch`; its overridden `get_current_querysets()` remained executable. That
method can substitute an unsealed child queryset at fetch time. Non-`Prefetch` entries
are also passed through without requiring an exact `str`, so arbitrary lookup objects or
`str` subclasses retain method dispatch.

Second, child querysets are recursively sealed with `required_alias=None`. A source
explicitly pinned to `shard_b` with `Prefetch("items", queryset=Item.objects.using(
"default"))` emerged with exactly that split:

```text
outer alias: shard_b
prefetch child alias: default
```

Django deliberately supports explicit cross-database prefetching. That means this is not
merely inert metadata: overlapping relation keys can populate a shard-B parent with
rows read from the default database, and the generated many-side resolver consumes the
prefetch cache directly. The shared boundary's pinned-alias guarantee currently stops at
the outer query.

Required root fix:

- Rebuild every `Prefetch` as the exact Django class, including the `queryset=None` case,
  and accept only exact string lookup entries. Validate copied path/to-attribute state
  before it enters the rebuilt object.
- Determine the outer effective alias before recursively sealing prefetch children and
  thread that requirement into each child. An explicitly divergent child must fail
  closed; an unrouted child should inherit the outer pinned alias.
- For an unpinned outer read, document and test the intended routing rule explicitly.
  Cross-database relation hydration must not happen as an accidental side effect of
  passing `None` to the child seal.
- Add evaluation-level regressions proving that a `Prefetch` subclass cannot substitute
  a queryset and that a pinned parent cannot hydrate related rows from another alias.

## Additional correctness finding

### [P2] `Query.model = None` is accepted and escapes as malformed SQL

Affected symbols:

- [`django_strawberry_framework/utils/querysets.py::_combined_query_table_defect`][querysets]
- [`django_strawberry_framework/utils/querysets.py::_seal_or_defect`][querysets]

`_combined_query_table_defect` validates `Query.model` only when it is non-`None`, even
though an outer model-row queryset requires a model-bearing select query. A hook result
whose public `QuerySet.model` remained `Category` but whose exact `sql.Query.model` was
set to `None` passed the seal. Stringifying the accepted result produced:

```sql
SELECT  FROM "products_category" WHERE "products_category"."name" = x
```

Evaluation then fails with a backend syntax error rather than the boundary's typed
`ConfigurationError`. This contradicts the helper's own documentation that a missing or
malformed query model fails closed as a table defect.

Required fix: require every outer and combined select query to carry a valid Django
model whose concrete model matches the registered concrete model. Add source and result
regressions for `None`, a non-model object, and a branch missing its model.

## Documentation and verification gaps

### [P2] The standing guarantee and historical note declare the unsafe boundary complete

Affected documentation and tests:

- [`docs/README.md`][docs-readme]
- `get_queryset-visibility-boundary-plan.md` (root historical note, since retired;
  recoverable from git history)
- [`tests/utils/test_querysets.py`][queryset-tests]
- [`tests/test_connection.py`][connection-tests]

The README says consumer executable behavior is never dispatched and every downstream
operation therefore runs on the sealed queryset. The probes above disprove both claims.
The rewritten root note also says the sealed rearchitecture superseded the prior review,
while its stated current source of truth is this feedback file; after this review it must
not describe the implementation as complete.

The test additions are broad and close many previous gaps, but the two `Query.chain`
row-survival tests assert behavior the code does not provide. The identity tests also
assert the unsafe optimization instead of cache removal. In addition, existing
symbol-qualified comments still point to the removed source substring
`normalize_query_source #"source = source.all()"` in the fakeshop schema and live API
tests; those anchors are stale under the current implementation.

Required work:

- Keep the shipped documentation on the prior, narrower contract until every P1 above is
  fixed and its surface tests pass.
- Update the historical note to identify this as an open third-round review, or replace
  it only after the new review is resolved.
- Repair the contradictory tests and stale symbol anchors in the same implementation
  change.
- Add the governing numbered security decision/KANBAN/spec and glossary update required
  by repository policy for a change to accepted queryset shapes, identity/cache
  behavior, aliases, errors, and query execution. The local diff still changes only the
  README and a historical root artifact.

## Confirmed improvements

- Hook/source `QuerySet` subclass identity is dropped in the ordinary non-identity path;
  downstream `QuerySet` method overrides such as `filter`, `_values`, `first`, and
  `__aiter__` no longer survive at the outer queryset layer.
- Managers that degrade to non-querysets or change their explicit alias fail closed.
- Read surfaces reject genuine values projections, custom row iterables, slices, wrong
  concrete models/tables, foreign outer query classes, and foreign combined-query
  branches.
- The frozen base-table and recursive combined-table checks close the previously
  reported public-model spoof and cross-model union paths for ordinary query graphs.
- Normal non-identity evaluated querysets are rebuilt without `_result_cache`, and hints
  receive a fresh mapping.
- Async nested/residual awaitables remain single-sited and fail closed with cleanup.
- Cascade retains its local grouping, combinator, slice, distinct, target-column-shadow,
  alias, cycle, and `ContextVar` cleanup checks while using the shared boundary.
- Added list, connection, Relay, cascade, and shared-helper tests materially improve the
  propagation matrix even though the blockers above keep the current set from landing.

## Review method and limits

- Inspected the complete tracked local diff against `HEAD` and traced every package-owned
  `get_queryset`, visibility-runner, query-source-normalization, Relay, list, connection,
  filter, optimizer, mutation, form, DRF, and cascade consumer.
- Read the installed Django `Query.clone`, `WhereNode.clone`, `QuerySet._clone`, and
  `QuerySet._chain` implementations used by this environment.
- Ran read-only local Django probes for copied `Query.chain` dispatch, identity-hook
  result-cache injection, nested `WhereNode.clone` predicate loss, surviving `Prefetch`
  subclasses, prefetch alias divergence, and missing `Query.model` handling.
- Ran the repository-mandated Ruff formatting/lint commands and `git diff --check` after
  writing this review.
- Did not run pytest because repository policy requires explicit maintainer instruction.

## Resolution

Closed 2026-07-20. Each finding above is resolved in the sealed boundary; the
verifying regressions pass and `django_strawberry_framework/utils/querysets.py` is
at 100% coverage.

- **[P1] Instance-level method shadows on the sealed `Query`.** Closed by
  `_shadow_defect` (called on the query instance from `_combined_query_table_defect`
  and on every embedded node from the recursive walk): any `__dict__` key naming a
  callable class attribute — `chain` / `clone` / any — fails closed BEFORE
  `sql.Query.clone` runs, so no callable shadow rides the clone's shallow `__dict__`
  copy into the rebuilt query. `_seal_or_defect` proves the whole graph trusted, then
  clones. The two flagged row-survival tests were reframed to the fail-closed contract
  (`test_query_chain_shadow_hook_fails_closed_sync` /
  `test_connection_query_chain_shadow_hook_is_sealed`) and pass.
- **[P1] Identity-hook fast path.** Removed: `apply_type_visibility_sync` /
  `apply_type_visibility_async` always re-seal the hook result through
  `_normalized_visibility_result` (no `result is queryset` shortcut), so an injected
  `_result_cache` cannot cross the boundary.
- **[P1] Executable nodes nested inside an exact `sql.Query`.** `_query_ast_defect`
  (`where`/`having` trees and leaf operands, annotations, sequences, `alias_map` joins
  + `filtered_relation`, `select_related`) runs inside `_combined_query_table_defect`
  BEFORE `sql.Query.clone`; a `WhereNode` subclass or a shadowed `clone`/`as_sql` on an
  exact node fails closed first.
- **[P1] `Prefetch` wrappers + cross-alias children.** `_rebuilt_prefetch_or_defect`
  rebuilds EVERY `Prefetch` (including `queryset=None`) as the exact Django class and
  accepts only exact-`str` lookups; `_sealed_prefetch_related_lookups` threads the
  outer effective alias into each child seal with `require_shared_alias=True` (divergent
  child fails closed; unrouted child inherits the outer alias, including when the outer
  is unrouted).
- **[P2] `Query.model = None`.** `_combined_query_table_defect` validates
  `Query.model` unconditionally via `_concrete_or_none` (a `None`/non-model model fails
  closed as a `table` defect) on the outer and every combined branch.
- **Test / wording fixes.** `_shadow_defect` now distinguishes the canonical `as_sql`
  emitter ("shadows the '…' method") from a dynamically-resolved `as_<vendor>` emitter
  ("… compiler method"); the deferred-plain-model-instance test uses the real
  reverse-relation shape (`Item` filtered by `{"category": Category(pk=7)}`).
- **Optimizer walker slice path.** `apply_type_visibility_sync` /
  `_prepared_visibility_source` / `_normalized_visibility_result` gained an
  `allow_sliced` param; `walker.py::_build_child_queryset` passes `allow_sliced=True`
  so the nested-connection degrade-to-unplanned path
  (`nested_fetch.py::unwindowable_child_queryset_reason`) is not pre-empted, while every
  recomposing surface keeps the slice rejection.
- **Docs / anchors.** `docs/README.md`'s boundary paragraph reflects the now-true
  guarantees; the stale `normalize_query_source #"source = source.all()"` anchors now
  point at `#"_coerced_manager_queryset(source)"`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[docs-readme]: README.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

[connection]: ../django_strawberry_framework/connection.py
[permissions]: ../django_strawberry_framework/permissions.py
[querysets]: ../django_strawberry_framework/utils/querysets.py
[relay-types]: ../django_strawberry_framework/types/relay.py
[type-resolvers]: ../django_strawberry_framework/types/resolvers.py

<!-- tests/ -->

[connection-tests]: ../tests/test_connection.py
[queryset-tests]: ../tests/utils/test_querysets.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
