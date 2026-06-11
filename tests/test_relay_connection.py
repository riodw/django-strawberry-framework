"""Staged test home for the spec-032 relation-as-Connection upgrade (Slices 3-4).

Covers the ``Meta.relation_shapes`` Phase-2.5 synthesis surface plus the
package-internal halves of the cursor-conformance matrix
(``docs/spec-032-full_relay-0_0_9.md`` Decisions 6/7/9; Decision 11 pins the
card-named two-file split). The ``Meta``-key *validation* tests sit with the
other Meta validation in ``tests/types/test_base.py``. Staged lists below are
removed by the change that ships each slice.
"""

# TODO(spec-032-full_relay-0_0_9 Slice 3): Synthesis coverage (Decision 6).
#   test_default_both_synthesizes_connection_sibling
#     an eligible reverse-FK / forward-M2M / reverse-M2M relation gains
#     <field>Connection alongside the list field (SDL assertion).
#   test_shape_connection_suppresses_list / test_shape_list_suppresses_connection
#   test_non_node_target_silently_list_only      (implicit default)
#   test_non_node_target_explicit_raises         (explicit "connection"/"both")
#   test_consumer_overridden_relation_skipped
#     a consumer-authored relation is never upgraded under the implicit
#     default (no relation_shapes entry for it).
#   test_generated_name_collision_raises
#     a model field / consumer attribute named <field>_connection.
#   test_generated_name_graphql_camel_collision_raises
#     a consumer-authored booksConnection attribute collides with a generated
#     books_connection on the default-camel-cased GraphQL surface even though
#     the Python names differ (Revision 3 P3).
#   test_synthesized_connection_carries_sidecar_args_and_total_count
#     filter: / orderBy: from the TARGET's sidecars; totalCount iff the
#     target's Meta.connection opts in (type-level contract).
#   test_synthesized_connection_runs_target_get_queryset
#     visibility filtering inside the nested connection.

# TODO(spec-032-full_relay-0_0_9 Slice 4): Package-internal conformance
# mirrors on cardinality fixtures the fakeshop graph lacks (the live primary
# copies run in examples/fakeshop/test_query/test_library_api.py against the
# shipped allLibraryGenresConnection - the test_query README coverage rule):
#   - the synthesized-relation run of the matrix (first: 0; overrun first;
#     stale-after no-error ONLY - offset cursors, no positional-stability
#     assertion; first+last rejection; pageInfo four-field correctness incl.
#     hasNextPage on a pageInfo-only query; backward last/before) against a
#     reverse-FK relation connection and the narrowed "connection" shape.
