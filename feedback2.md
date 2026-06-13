# feedback2

Fresh pass starts again from `tests/base` and applies the live-HTTP-first rule
from `examples/fakeshop/test_query/README.md`: if package coverage is reachable
through the fakeshop `/graphql/` endpoint, it should move there only when the
live test applies the same or stronger contract pressure. A package test should
stay when it asserts internal state, exact exception type, query planning,
query count, cache identity, async-only behavior, construction-time validation,
or an otherwise synthetic shape the example project cannot expose.

No pytest run for this review.

## High-confidence moves

These are the best candidates to move or replace with live fakeshop tests. The
package version should be removed only after the live test proves the same
behavior through the real `/graphql/` request path and coverage remains closed.

- `tests/filters/test_sets.py::test_apply_sync_nested_or_branch_applies_related_constraint`
  should move to `examples/fakeshop/test_query/test_library_api.py`. The current
  test is a direct `BranchFilter.apply_sync` behavior check. A live query against
  `allLibraryBranches(filter: { or: [{ shelves: { code: { exact: ... } } }] })`
  would also exercise GraphQL input coercion, root visibility, the real
  `BranchFilter`, and the HTTP response envelope.

- `tests/filters/test_sets.py::test_related_filter_on_many_side_relation_returns_each_parent_once`
  should move to a live `allLibraryBranches` test with one branch owning two
  matching shelves. The important contract is parent de-duplication under a
  to-many related filter, and the HTTP path is stronger than direct
  `apply_sync`.

- `tests/filters/test_sets.py::test_related_filter_answers_identically_direct_and_inside_logic_tree`
  should move to a live query with two aliases, one direct related filter and
  one logically wrapped form, asserting identical rows. That keeps the contract
  pressure on nested input normalization plus SQL behavior.

- `tests/optimizer/test_extension.py::test_b8_consumer_descendant_prefetch_does_not_raise`
  and `tests/optimizer/test_extension.py::test_b8_consumer_exact_plus_descendant_prefetch_does_not_raise`
  are behavior-only acceptance checks: consumer `prefetch_related(...)` must not
  collide with optimizer prefetches. A fakeshop root field that returns the same
  consumer-prefetched queryset and is queried over `/graphql/` would be stronger.
  Keep `test_b8_consumer_plain_string_upgraded_to_optimizer_prefetch` in package
  tests because it inspects the optimized queryset internals.

- `tests/types/test_definition_order_schema.py::test_m2m_schema_shape_builds_with_real_library_models`
  can move to live introspection. The example schema already exposes
  `BookType.genres`, so `/graphql/` can assert the rendered field shape.

- `tests/types/test_definition_order_schema.py::test_relay_declared_type_emits_node_interface_and_global_id`
  can move to live introspection of `GenreType`. The example project already
  exposes Relay `GenreType` ids and the `Node` interface.

- `tests/types/test_definition_order_schema.py::test_mixed_relay_and_non_relay_types_introspect_cleanly`
  can move to live introspection. The library schema has Relay `GenreType` /
  `BookType` and non-Relay `ShelfType`, so the real schema can assert the Relay
  interface does not bleed into non-Relay types.

- `tests/types/test_definition_order.py::test_decorator_relation_field_override_routes_schema_query_through_consumer_resolver`
  is now covered more strongly by
  `examples/fakeshop/test_query/test_library_api.py::test_library_relation_override_shapes_http_response_data`.
  Keep the neighboring package tests that inspect override metadata and class
  mutation; only the schema-execution behavior twin is a move candidate.

- `tests/test_list_field.py::test_djangolistfield_default_resolver_returns_queryset_filtered_by_get_queryset`
  should become or be folded into a live `allLibraryBranchesViaListField` test
  that seeds a `city="restricted"` branch and asserts the anonymous HTTP result
  excludes it. That proves the default resolver applies `BranchType.get_queryset`
  through the real list field.

- `tests/test_connection.py::test_total_count_counts_post_filter_pre_slice_when_selected`,
  `tests/test_connection.py::test_total_count_not_counted_when_not_selected`,
  `tests/test_connection.py::test_first_and_last_graphql_error_through_schema`,
  and `tests/test_connection.py::test_connection_resolver_sync_dispatch` now
  have live root-connection pressure available through
  `allLibraryGenresConnection`. The package file's header still says
  `DjangoConnectionField` is not live-reachable; that comment is stale because
  the example schema ships `all_library_genres_connection:
  DjangoConnection[GenreType] = DjangoConnectionField(GenreType)`.

- `tests/test_relay_connection.py::test_relation_connection_first_zero`,
  `tests/test_relay_connection.py::test_relation_connection_first_overrun`,
  `tests/test_relay_connection.py::test_relation_connection_stale_after_no_error`,
  `tests/test_relay_connection.py::test_relation_connection_first_and_last_rejected`,
  `tests/test_relay_connection.py::test_relation_connection_page_info_four_fields`,
  `tests/test_relay_connection.py::test_relation_connection_has_next_page_when_edges_unrequested`,
  and `tests/test_relay_connection.py::test_relation_connection_backward_pagination_last_before`
  can now be promoted to live tests through `allLibraryShelves { booksConnection
  ... }` or an equivalent shipped relation-connection field. The current package
  comment says the fakeshop graph lacks the cardinality fixture until Slice 6,
  but `ShelfType` now exposes `books`, `BookType` is Relay-shaped, and the live
  schema can exercise the synthesized relation connection over HTTP.

## Candidates with conditions

These can move only if the live replacement keeps the extra assertion pressure.
Otherwise keep the package tests.

- `tests/filters/test_sets.py::test_apply_sync_filters_against_simple_scalar_input`,
  `tests/filters/test_sets.py::test_apply_sync_passes_through_empty_filter_input`,
  and `tests/filters/test_sets.py::test_apply_sync_raises_graphql_error_on_invalid_input`
  are already represented by stronger live filter tests in the library suite.
  They can be deleted from package tests if coverage stays closed. If they are
  kept, they should be treated as narrow unit pins for `apply_sync`, not as the
  primary contract.

- `tests/filters/test_sets.py::test_filter_queryset_intersects_and_branch` and
  `tests/filters/test_sets.py::test_filter_queryset_unions_or_branch` are
  live-reachable through `allLibraryBranches`. Move them only if the replacement
  asserts the distinct logic-tree shape, not just "some filter worked".

- `tests/types/test_definition_order.py::test_annotation_only_scalar_override_survives_strawberry_finalization`
  and `tests/types/test_definition_order.py::test_auto_annotation_survives_strawberry_finalization`
  are candidates only if the live suite introspects the exact
  `OverriddenScalarSpecimenType` field shapes. The current live override test
  proves HTTP resolution behavior, but not necessarily the same schema-shape
  assertions.

- `tests/test_list_field.py::test_djangolistfield_non_nullable_outer_default_via_consumer_annotation`
  appears superseded by the live nullable/non-nullable list-field introspection
  test. Delete the package twin only if the live assertion remains explicit
  about the non-null outer wrapper on `allLibraryBranchesViaListField`.

- `tests/test_relay_node_field.py::test_typed_node_field_resolves_target`,
  `tests/test_relay_node_field.py::test_typed_node_field_mismatch_raises`,
  `tests/test_relay_node_field.py::test_node_hidden_row_returns_null`, and the
  plain malformed-id arm of
  `tests/test_relay_node_field.py::test_node_malformed_id_graphql_error` have
  live twins in the library API tests. Keep or split the package tests where
  they assert extra non-live shapes, such as synthetic model-label/type-strategy
  routing, extra malformed id variants, query-count side channels, custom
  `NodeID` attributes, or multi-type routing over one Django model.

## Keep in package tests

- `tests/base` stays as-is. `test_conf.py` covers settings normalization,
  signal reloading, missing-key behavior, and recursion/error branches.
  `test_init.py` covers package exports/version/logger surface. None of this is
  reachable from `/graphql/`, and the folder obeys the rule that `tests/base`
  contains only `test_init.py` and `test_conf.py`.

- `tests/management` stays in package tests. The happy-path command behavior
  belongs in example in-process command tests, but the package tests here cover
  import/path failures, command error messages, and unresolvable forward refs,
  not HTTP API behavior.

- `tests/orders` should mostly stay. The live library suite already covers the
  consumer order contract over HTTP. The remaining package tests inspect
  factories, normalization ledgers, expression shape, aggregate shape, async
  branches, permission dedupe, `get_flat_orders`, and composition internals.

- `tests/testing` stays. The wrap and Relay helper tests exercise public testing
  utilities, not behavior the fakeshop API reaches by itself.

- `tests/utils` stays. These are helper contracts for connection windows,
  generated input state, permissions, queryset normalization, relation
  classification, strings, and typing.

- `tests/test_registry.py` stays. It is registry state-machine coverage:
  pending relations, atomic finalize failures, primary selection, unregister,
  cache eviction, and audit behavior. Live GraphQL queries can observe only
  final schema behavior, not these invariants.

- `tests/test_apps.py` and `tests/test_django_patches.py` stay. They pin package
  app registration and the Django test-case patch, which are not fakeshop API
  contracts.

- Most of `tests/types/test_converters.py` stays. BigInt round trips already
  moved to live scalar tests, but the remaining parser/serializer failures,
  PostgreSQL-only `ArrayField` / `HStoreField` converter rows, synthetic choice
  enum collisions, and nullability-force conversion branches are not real
  SQLite fakeshop HTTP paths.

- Most of `tests/types/test_relay_interfaces.py` stays. It asserts interface
  installation, resolver injection, custom/global id strategy validation,
  decode/encode routing, async resolver behavior, composite pk gates, callable
  setting validation, and routing audits. Live root node tests are the consumer
  contract; these package tests are the machinery.

- Most of `tests/test_connection.py` stays even though the header needs
  updating. Generated connection-type caching, direct subclass generation,
  `_total_count_requested` fragment recursion, guard helpers, non-queryset
  iterable error paths, async count attachment, default ordering internals,
  max-result config, optimizer planning, deterministic pk tiebreakers, and cache
  reset hooks are package internals.

- Most of `tests/test_relay_connection.py` stays. The fast-path, strictness,
  fallback, SQL/query-count, window annotation, distinct fallback, and cached
  plan assertions are stronger in package tests than they would be as ordinary
  live row assertions. The new working-tree test
  `tests/test_relay_connection.py::test_async_fast_path_ambiguous_empty_falls_back_for_total_count_and_pageinfo`
  should stay package-side because the sync fakeshop GraphQL view cannot drive
  that async fallback branch.

- Most of `tests/test_relay_node_field.py` stays. Bare/multi-type routing,
  custom `NodeID` attributes, `_coerce_pk_or_none`, `_stamp_node_type`, typed
  batch mismatch semantics, exact query-count side-channel checks,
  construction/finalize guards, async schema execution, custom
  `resolve_nodes`, generator returns, wrong-length errors, sync misuse, and
  public exports are not stronger through live fakeshop HTTP.

## Cleanup notes

- Several comments are now stale and should be corrected when touching the
  files:
  - `tests/test_connection.py` still says `DjangoConnectionField` is not yet
    reachable from live `/graphql/`.
  - `tests/test_relay_connection.py` still says several relation-connection
    fixtures are unavailable until Slice 6, even though the library schema now
    exposes shipped relation-connection surfaces.
  - `tests/test_relay_node_field.py` says live copies are canonical, but the
    file still contains many package twins. That is acceptable for the internal
    cases above, but behavior-only twins should be split or retired.

- For every move, the acceptance test should live in
  `examples/fakeshop/test_query/` and use `django.test.Client` against
  `/graphql/`. Do not move these to `examples/fakeshop/tests/` unless the
  behavior is not actually reachable through the live GraphQL endpoint.

- Do not treat line coverage as sufficient. The replacement live test must
  preserve the contract being stressed: de-duplication, visibility boundaries,
  GraphQL input coercion, response error shape, pagination identity, or
  optimizer interaction as applicable.
