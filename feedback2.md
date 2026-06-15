# tests/optimizer review

Scope: fresh pass over `tests/optimizer`, continuing after `tests/management`.
The same-or-stronger rule matters more here than in most folders: many optimizer
lines are already reached by live fakeshop `/graphql/` tests, but the package
tests often assert exact plan state, cache keys, context stashes, or defensive
helper branches that are not observable from HTTP. Those should not move merely
because a line is reachable.

No pytest was run.

## High-confidence moves

Move these B8 behavior-only collision tests out of
`tests/optimizer/test_extension.py` if the live replacement is made through a
real fakeshop resolver returning a consumer-prefetched queryset:

- `test_b8_consumer_descendant_prefetch_does_not_raise`
- `test_b8_consumer_exact_plus_descendant_prefetch_does_not_raise`

Both currently build a synthetic in-process schema and assert only that the
GraphQL operation succeeds and returns data. A live fakeshop test can apply
stronger pressure by going through `/graphql/`, the configured project schema,
the URL/view/request stack, and real query-count assertions.

A good live shape is the library app, because it already has hand-written
consumer resolver roots and relation depth:

- add/use a resolver returning `Genre.objects.prefetch_related("books__loans")`;
- query `allLibrary...Genres { name books { title loans { note } } }`;
- assert HTTP 200, no errors, expected nested data, and a flat query count;
- add the exact-plus-descendant variant with
  `prefetch_related("books", "books__loans")`.

That preserves the original contract, and strengthens it: the bug was a real
consumer queryset collision, so the example project should prove the public API
does not crash or regress into per-row prefetch behavior.

## Conditional moves

`tests/optimizer/test_extension.py::test_b8_consumer_plain_string_upgraded_to_optimizer_prefetch`
can move only if the live test asserts the important behavior, not just "no
errors". The package test currently inspects the diffed queryset and proves the
consumer's plain `"items"` string is replaced by the optimizer's nested
`Prefetch`. A live replacement should instead make that implementation detail
observable:

- resolver returns a queryset with a plain consumer prefetch for the parent
  relation, for example `Genre.objects.prefetch_related("books")`;
- query deeper than the consumer prefetch, for example
  `books { title loans { note } }`;
- assert the query count is flat: root genres query, one books prefetch, one
  loans prefetch, not one loan query per book.

If the replacement only asserts successful data, keep the package test. Success
alone would not prove the optimizer upgraded the prefetch rather than dropping
its nested work.

`tests/optimizer/test_extension.py::test_b8_consumer_prefetch_object_suppresses_optimizer_entry`
can move only with an observable consumer-`Prefetch` contract. The package test
currently proves the optimized queryset keeps exactly the consumer's `Prefetch`
object. A live replacement would need a custom consumer `Prefetch` queryset whose
effect is visible in the GraphQL response, for example a filtered `books`
prefetch where the response must include only the consumer-visible subset. If
the live test cannot make the consumer queryset effect visible, keep the package
plan/diff assertion.

`tests/optimizer/test_extension.py::test_optimizer_skips_when_no_relations_selected`
and `tests/optimizer/test_extension.py::test_optimizer_applies_only_for_selected_scalars`
are only worth moving if the live test asserts SQL projection, not just one
query. A scalar-only live query with one SQL statement is weak because it would
usually pass even without optimizer planning. A stronger live version would
select a single scalar over HTTP and assert the captured SQL projects only the
selected column plus required connector/pk columns. Without that SQL projection
assertion, leave these in `tests/optimizer`.

## Already live; keep package siblings

These behaviors already have live fakeshop HTTP coverage, and the package tests
should remain because they assert plan/cache state that HTTP cannot expose:

- Manager coercion:
  `examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_coerces_manager_to_queryset_in_http_query`
  covers behavior; keep
  `tests/optimizer/test_extension.py::test_optimize_coerces_manager_through_all_records_cache_miss`
  for the cache-miss proof.
- Duplicate root field merging:
  `examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_merges_duplicate_root_field_nodes_over_http`
  covers behavior; keep
  `tests/optimizer/test_extension.py::test_optimizer_plans_merged_duplicate_root_field_nodes_plan_shape`
  for the merged plan key.
- FK id elision and its guards:
  the scalars live tests cover id-only, alias, extra-scalar, sibling-root, and
  custom-`get_queryset` behavior; keep the package tests that assert
  `plan.select_related`, `plan.only_fields`, `plan.fk_id_elisions`, and
  `ctx.dst_optimizer_fk_id_elisions`.
- Custom `get_queryset` downgrade:
  the scalars live tests cover the two-query public behavior and visibility; keep
  package tests that prove the plan is uncacheable and uses `Prefetch`.
- Filter/order cooperation with optimizer:
  library live tests cover relation query counts after filtering and ordering;
  keep package tests that assert the underlying plan mechanics.
- Nested connection windows:
  library live tests cover nested connection pagination, total counts, visibility,
  list/connection sibling coexistence, and query-count flatness; keep package
  tests that assert cache-key variables, window annotations, partition columns,
  resolver keys, and fallback sentinel unions.
- Multi-db:
  `examples/fakeshop/test_query/test_multi_db.py` covers the routed resolver
  behavior; keep `tests/optimizer/test_multi_db.py` for the consumer-provided
  `OptimizerHint.prefetch(Prefetch(queryset=...using("shard_b")))` alias
  preservation that is intentionally plan-level.

## Keep in package tests

Keep `tests/optimizer/test_hints.py`. `OptimizerHint` construction, equality,
immutability, invalid flag combinations, and `Prefetch` value validation are
pure package API contracts. A live GraphQL query can observe some hint effects,
but it cannot replace the dataclass contract.

Keep `tests/optimizer/test_field_meta.py`. `FieldMeta.from_django_field` and
definition-owned `field_map` metadata are the optimizer's precomputed substrate.
The live suite indirectly depends on that metadata, but it cannot assert
accessor names, nullable relation classification, frozen metadata, or rejection
of malformed field-like objects.

Keep `tests/optimizer/test_definition_order.py`. The fakeshop schema already
exercises awkward declaration order, but these tests pin finalization-time
planning decisions, cyclic target registration, and annotation-only relation
override metadata. Those are registry/walker contracts, not HTTP contracts.

Keep `tests/optimizer/test_selections.py`. These are shared AST and converted
selection traversal primitives: fragment dedupe, directive variables,
response-key merging, runtime prefixes, and `totalCount` detection. Live tests
prove the composed system works; these tests prevent a future helper drift where
one caller sees different traversal semantics than another.

Keep most of `tests/optimizer/test_walker.py`. The walker is intentionally tested
as a pure planner against synthetic selections because it exposes exact internal
decisions: select vs prefetch dispatch, alias merges, directive handling,
runtime prefixes, FK-id elision keys, nested `Prefetch` structure, hint
precedence, connection-window planning, fallback reasons, cacheability, and
secondary-type resolution. Live tests should cover representative behavior, but
moving these would erase the reason each decision failed in a regression.

Keep `tests/optimizer/test_plans.py`. `OptimizationPlan` is a small internal data
structure with behavior around finalization, lookup-path flattening,
queryset-diffing, `only()` preservation, deterministic ordering, and window SQL
helpers. HTTP can validate outcomes, but it cannot safely replace these focused
method contracts.

Keep `tests/optimizer/test_relay_id_projection.py`. Ordinary Relay id behavior
is already live in products/library tests, but this module asserts projection and
lazy-load invariants, including a custom primary-key model created with
`schema_editor`. That custom-pk shape is not part of the fakeshop model surface
and should stay package-level unless the example project intentionally gains a
real custom-pk model.

Keep these `tests/optimizer/test_extension.py` groups package-internal:

- return-type resolver defensive branches;
- non-root resolver bypass;
- async resolver parity, because fakeshop `/graphql/` is sync;
- empty `field_nodes` and monkeypatched empty-plan branches;
- `on_execute` `ContextVar` lifecycle;
- cache hit/miss/eviction/key-shape tests;
- directive and pagination variable collectors;
- strictness sentinel publishing and warning/raise edge cases;
- `_will_lazy_load_*` helper branches;
- schema audit reachable-type traversal and missing-target warnings;
- context stash variants for dicts, mappings, read-only contexts, and hostile
  mapping errors;
- extension constructor surface and Strawberry `execution_context` compatibility;
- `hint_is_skip` shape dispatch;
- secondary-type cache and schema-audit dedupe;
- `apply_connection_optimization` active-cache reuse;
- nested fallback publish union tests.

Those are either impossible to trigger through the configured fakeshop HTTP
schema, or the HTTP version would be weaker because it could not inspect the
state that makes the contract meaningful.

## Cleanup note

`tests/optimizer/test_extension.py` still has a TODO block for spec-033 cache-key
hygiene even though the listed tests now exist below it. That is not a placement
issue, but it is stale feedback for future readers. Remove or rewrite it when
touching this file for the B8 moves.

