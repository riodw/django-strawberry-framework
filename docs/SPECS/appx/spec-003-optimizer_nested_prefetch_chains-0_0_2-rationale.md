# Rationale: spec-003 — Optimizer O4 nested prefetch chains (deliberation, rejected alternatives)

Deliberative companion to [`spec-003-optimizer_nested_prefetch_chains-0_0_2.md`][spec-003]. The spec
is the contract; this file records why nested planning is shaped as it is. The spec has no numbered
Decisions, so each entry is keyed to a spec section.

## Plan shape

Spec: [Plan shape][spec-003-current].

- **The spec lists only the bags O4 owns.** The dataclass carries more (per-path resolver-key ledgers
  owned by [`spec-033`][spec-033], and the frozen membership sets
  `django_strawberry_framework/optimizer/plans.py::OptimizationPlan.finalize` publishes). Enumerating
  every field would be a symbol map of another spec's contract, which goes stale in one copy.
- **The planner signature is not published.** Later specs add keyword parameters; what this spec
  owns is the two starting conditions: an empty Django prefix and the root field's own runtime path.
- **Why the root runtime path is the root field's response key.** The resolver rebuilds its half of
  the key from `info.path`, which includes the field being resolved. A walker starting from an empty
  runtime path would emit `EntryType.item@item` against a resolver asking for
  `EntryType.item@allEntries.item`; every elision and strictness key would miss, and nothing would
  raise.
- **Why `Prefetch` objects rather than string chains.** A child queryset with its own projection,
  elisions, visibility hook, or nested branches needs a queryset to carry them; a string lookup has
  none. A `Prefetch` is emitted uniformly so B8 diffing reads one shape (`prefetch_to`).

## Same-query recursion

Spec: [Same-query recursion for single-valued paths][spec-003-samequery].

- **The FK-column append precedes the elision short-circuit.** An elided branch plans no join and its
  resolver reads the source row's FK column, so appending after the short-circuit leaves the column
  unprojected and reintroduces the N+1 the elision removes. The wire result is identical either way,
  so only an absolute query count at two parent cardinalities can tell them apart.
- **The branch is a named helper behind a dispatcher, not an inline arm of the selection walk.** The
  walk has a select arm, a prefetch arm, a connection arm, and hint overrides; one function carrying
  all of them is unreadable. Directive lists share the public `append_unique` helpers so every
  producer applies the same dedup.

## Prefetch-boundary recursion

Spec: [Prefetch-boundary recursion for many-side and downgraded paths][spec-003-prefetch].

- **The parent-side link-column append.** A forward relation reaching this branch (downgraded by
  O6, or forced by `force_prefetch`) is matched by Django reading its carrier columns off each parent
  (`<field>_id`, a one-column `ForeignObject`'s `from_fields` column); a reverse, M2M or generic
  relation whose link targets non-pk source columns (a `to_field`, a `ForeignObject`'s `to_fields`, a
  through FK's `to_field`) is attached by Django reading those columns off each parent. Leaving either
  out of the parent projection costs a deferred load per parent row. A link onto the source pk
  appends nothing, since every projection loads the pk. The append is
  `django_strawberry_framework/optimizer/walker.py::_record_relation_access`, shared with the
  same-query branch.
- **The `Prefetch` lookup segment is the instance accessor.** Django's `prefetch_related` resolves a
  lookup by `getattr` on the instance, so a reverse relation declared without `related_name` (field
  name `book`, accessor `book_set`) is reachable only under the accessor. The field name, the
  intuitive choice, raises `AttributeError: ... invalid parameter to prefetch_related()`. Plan keys,
  resolver identities, and `select_related` paths stay in field-name vocabulary.
- **The planner does not call `get_queryset` itself.** Every framework-side invocation routes through
  the shared visibility boundary ([`spec-045`][spec-045]), so sealing, degradation, and the
  sliced-queryset allowance are decided at one seam.
- **No connector injection when the child plan projected nothing.** With no child `only()`, Django
  fetches full rows and the connectors come for free; an unconditional inject would turn a full-row
  fetch into a one-column projection.
- **The parent is marked uncacheable before the child is built.** A child build that degrades instead
  of completing must still leave the parent uncacheable, or a request-scoped visibility result is
  cached.
- **The connector rules live in the join taxonomy.** The nested planner and the walker read one
  source of truth for which columns each cardinality needs
  (`django_strawberry_framework/optimizer/join_taxonomy.py::RelationJoinDescriptor`), and the
  taxonomy reads a link's carrier and target columns from one reader
  (`django_strawberry_framework/utils/relations.py::relation_link`), because a relation's `attname`
  is a column only for a `ForeignKey`.

## Hints are leaf operations

Spec: [Implementation design][spec-003-design].

A consumer-supplied `Prefetch` carries the consumer's own queryset, projection, and nested prefetches,
so recursing into it would overwrite the source of truth. A hint otherwise chooses which of the two
recursion paths a relation takes and never changes what that path does. `force_select` is rejected for
a many-side relation (Django cannot join it) and yields to O6, because a hint cannot suppress a
visibility hook.

## Lookup-path flattening

Spec: [Lookup-path flattening][spec-003-flattening].

`lookup_paths` recurses to arbitrary depth because B8 diffs every nested level, and it is kept
separate from resolver keys because the two answer different questions. Reads of Django's private
`_prefetch_related_lookups` go through one named reader,
`django_strawberry_framework/optimizer/plans.py::_consumer_prefetch_lookups`, so one call site depends
on that contract.

## Resolver sentinel keys

Spec: [Resolver sentinel keys][spec-003-sentinel] and
[Lookup paths vs resolver sentinel keys][spec-003-lookup-vs-key].

- **One shared key implementation.** Only the walker sees merged selections before planning, and only
  the resolver can rebuild the runtime branch from `info.path`; that asymmetry is in inputs, not in
  the format. Two mirrored private formatters held in step by an instruction drift on the first edit
  to one side, so `django_strawberry_framework/optimizer/plans.py::resolver_key` and
  `::runtime_path_from_info` are imported by both.
- **No separate elision predicate on the resolver side.** The forward resolver walks `info.path` once
  for both the B2 elision check and the B3 strictness check; a predicate per check would walk the
  same linked list twice per resolved field on the hot path.
- **One identity per response key.** A merged selection reachable under several response keys keeps
  every alias, so the walker records one key per key; collapsing them would let one branch's elision
  serve another's.

## B1 plan cache

Spec: [Implementation design][spec-003-design].

Cacheability propagates in the single absorb step the parent performs
(`django_strawberry_framework/optimizer/plans.py::OptimizationPlan.merge_metadata_from`), not at each
call site, so a new absorb site cannot forget it.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-003]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md
[spec-003-current]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md#plan-shape
[spec-003-design]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md#implementation-design
[spec-003-flattening]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md#lookup-path-flattening
[spec-003-lookup-vs-key]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md#lookup-paths-vs-resolver-sentinel-keys
[spec-003-prefetch]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md#prefetch-boundary-recursion-for-many-side-and-downgraded-paths
[spec-003-samequery]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md#same-query-recursion-for-single-valued-paths
[spec-003-sentinel]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md#resolver-sentinel-keys
[spec-033]: ../spec-033-connection_optimizer-0_0_9.md
[spec-045]: ../spec-045-visibility_boundary-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
