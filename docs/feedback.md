## Spec 033 Review

Overall: the spec is directionally right and the glossary validation passes
(`uv run python scripts/check_spec_glossary.py --spec docs/spec-033-connection_optimizer-0_0_9.md`).
The current draft still has several design blockers that should be fixed before
implementation starts, because they change the foundation slices rather than
individual tests.

### P1 - Fast path is assigned to the wrong layer

Decision 5 says [`connection.py::_build_relation_connection_resolver`][connection]
should probe `root._dst_<field>_connection` and "build the connection from the
rows." That is not compatible with Strawberry's connection wrapper. Strawberry's
`ConnectionExtension.resolve` calls the field resolver, treats its return value
as the node iterable, and then calls the generated connection class's
`resolve_connection`; the resolver is not expected to return a connection
instance. Returning a prebuilt connection from the resolver would make
`ConnectionExtension` pass that connection object back through
`resolve_connection` as if it were an iterable of nodes.

The fix is to move the connection-building fast path into the generated
connection class path, or introduce a small internal sentinel/list wrapper that
the generated connection class consumes. The synthesized relation resolver may
return the annotated `to_attr` rows when present, but the edge/pageInfo/totalCount
construction needs to happen in the `DjangoConnection.resolve_connection` /
generated `<TypeName>Connection.resolve_connection` layer, where the real Relay
pagination arguments and edge class are already available. Add a through-schema
test that executes the real `relay.connection` field and proves the fast path is
not only a direct helper call.

### P1 - Divergent aliases cannot be detected after today's merge

Decision 6 requires aliased duplicate nested connections with different
pagination arguments to fall back. Today
[`optimizer/walker.py::_merge_aliased_selections`][walker] merges same-field
selections by field name, preserves all response keys, and keeps only the first
selection's `arguments` when aliases differ. The debug log explicitly says a
future argument-aware optimizer must change that merge. If Slice 1 adds
`_plan_connection_relation` after the current merge, the planner cannot know
that `a: booksConnection(first: 2)` and `b: booksConnection(first: 5)` diverged;
it will plan one window from the first argument set and mark both aliases as
planned.

Make argument preservation a Slice 1 foundation task before window planning.
Either keep connection selections unmerged until after pagination classification,
or store per-response-key argument payloads on the merged selection. The
fallback tests need to assert the wrong plan is absent (`Prefetch` and planned
resolver key), not merely that the query still resolves.

### P1 - The window partition key is under-specified for M2M

Decision 4 repeatedly says "partition by the relation connector column", but the
implementation plan does not define how that connector is derived for each
relation kind. Reverse FK can partition by the child table's FK column. Forward
and reverse M2M cannot safely partition by the child primary key; they need the
through-table parent-side key that Django's prefetch join uses to attach rows to
each parent. This is not a corner case: the planned live library proof is mostly
M2M (`Genre.booksConnection` and `Book.genresConnection`), so the first SQL-shape
slice depends on this being exact.

Add a named helper to the spec, for example
`window_partition_for_prefetch(field)`, with explicit behavior for reverse FK,
forward M2M, reverse M2M, and unsupported relation kinds. The tests should cover
two parents sharing at least one child across an M2M relation; that is the shape
that exposes an accidental child-pk partition because both parents would receive
the same global child page instead of their own per-parent page.

### P1 - Zero-row windows cannot supply `totalCount` or full `pageInfo`

The spec currently says `first: 0` yields an empty window and that `totalCount`
is `0` "by construction." That contradicts the shipped connection contract:
`first: 0` over a non-empty set still reports the pre-slice `totalCount`, and
the existing live root test pins `hasNextPage: true` with `endCursor: null`.
The same problem occurs for any paginated window that returns no rows even
though the parent has related rows, such as an `after` cursor past the end.
With no annotated row in the `to_attr` list, `_dst_total_count` and row-number
metadata are unavailable.

The spec needs an explicit zero-row metadata strategy before claiming "zero
extra queries" for nested `totalCount`. Viable root-cause options are: overfetch
one metadata row when the requested edge window is empty, add a separate
parent-keyed count/exists prefetch for metadata, or deliberately fall back to
the per-parent pipeline for zero-row windows that request `pageInfo` or
`totalCount`. What should not ship is `totalCount: 0` for `first: 0` over a
non-empty relation.

### P2 - Nested connection optimization must not clobber the parent strictness context

The current connection pipeline calls
[`optimizer/extension.py::apply_connection_optimization`][extension], which
publishes `DST_OPTIMIZER_PLAN`, `DST_OPTIMIZER_PLANNED`, and related sentinels
onto the shared `info.context`. A fallback nested connection still runs that
pipeline per parent. Once Slice 4 starts checking strictness for the connection
access itself, the fallback path can still overwrite the parent field's planned
set with the child connection's plan, especially under `"warn"` where execution
continues after the warning.

The spec should require scoped publish/restore semantics for nested connection
pipeline runs, or a context shape that is keyed by runtime path instead of a
single global sentinel set. Add a test where a warn-mode fallback nested
connection is followed by a parent-level relation sibling that was planned by
the root plan. It should not warn or raise; without context scoping, this is the
case likely to fail because the nested child plan overwrote the parent plan's
sentinels.

### P2 - Cache-key depth through fragments needs one more rule

Decision 7's "non-root field nodes" rule is correct, but fragment traversal
needs to preserve response-path depth, not raw fragment-definition nesting. A
root connection selected inside a fragment on `Query` is still a root field and
its `first: $n` variable should stay out of the key. A nested connection selected
inside a fragment on the parent node is still nested and its pagination variable
must be included.

Add the root-fragment negative test alongside the planned fragment-carried
nested-variable positive test. Without it, a syntactic traversal of reachable
fragment definitions can accidentally re-fragment root connection cache entries,
which is exactly what Decision 7 is trying to avoid.

## Smaller Notes

- Decision 5 should say the fast path uses the generated edge class's
  `resolve_edge(..., cursor=<zero_based_offset>)` rather than manually naming a
  cursor prefix. That keeps the cursor prefix owned by Strawberry's edge type.
- The spec should explicitly preserve the existing `first` + `last` guard
  ordering when the planner computes `SliceMetadata` at plan time. Planning must
  not introduce a different error surface or duplicate guard.
- Add a test for a `"both"` relation where the list sibling and connection
  sibling are selected together and a consumer already has a plain accessor
  prefetch. The `to_attr` prefetch must coexist with the accessor prefetch
  through [`optimizer/plans.py::diff_plan_for_queryset`][plans].

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../django_strawberry_framework/connection.py
[extension]: ../django_strawberry_framework/optimizer/extension.py
[plans]: ../django_strawberry_framework/optimizer/plans.py
[walker]: ../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
