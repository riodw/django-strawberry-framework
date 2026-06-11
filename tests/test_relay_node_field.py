"""Staged test home for the spec-032 root refetch fields (Slices 2 and 4).

Mirrors the new top-level ``django_strawberry_framework/relay.py`` (the
card-named two-file split over a strict ``docs/TREE.md`` mirror -
``docs/spec-032-full_relay-0_0_9.md`` Decision 11). Tests land with their
owning slice; the staged lists below are removed by the change that ships
each slice (the ``AGENTS.md`` design-doc anchor discipline).
"""

# TODO(spec-032-full_relay-0_0_9 Slice 2): Root-field package coverage
# (Decisions 3/4/5; package twins keep `fail_under = 100` green until the
# Slice-6 fakeshop activation makes the live copies the canonical surface).
#
#   test_bare_node_field_resolves_model_label_id / ..._type_name_id
#     node(id:) decodes both payload shapes per the target's recorded
#     strategy and returns the right concrete type (is_type_of dispatch).
#   test_typed_node_field_resolves_target / test_typed_node_field_mismatch_raises
#     typed single-node form: row for a matching id; GraphQLError naming
#     expected/received types for a mismatched one.
#   test_typed_nodes_field_resolves_targets / test_typed_nodes_field_mismatch_raises
#     typed BATCH form (DjangoNodesField(GenreType)): resolves matching ids;
#     ANY wrong-type id fails the whole field with the expected/received
#     GraphQLError (Revision 6 P2 - previously untested DoD surface).
#   test_node_hidden_row_returns_null / test_node_missing_row_returns_null
#     both through a get_queryset-filtered fixture type; plus
#   test_node_null_paths_issue_equal_queries
#     the no-existence-oracle query-count pin (hidden and missing share one
#     queryset code path; assertNumQueries equality).
#   test_node_malformed_id_graphql_error
#     malformed base64 / unresolvable label / strategy-forbidden shape each
#     surface GLOBALID_INVALID, never a raw ConfigurationError.
#   test_nodes_preserves_input_order_with_null_holes
#   test_nodes_batches_per_type        (query-count: one per distinct type)
#   test_nodes_duplicate_ids           (each position gets its row)
#   test_nodes_empty_list              (ids: [] -> [] with zero queries)
#   test_nodes_malformed_id_mid_batch
#     a malformed id among well-formed ones fails the WHOLE field with
#     GLOBALID_INVALID ([Node]! nulls the enclosing data), not a null hole.
#   test_node_field_without_node_types_raises_at_finalize
#     the ledger check fires with "node lookup configured but no Node types
#     registered."; registry.clear() resets the ledger.
#   test_node_async_context / test_nodes_async_context
#     async execution paths (the nodes resolver returns ONE gathering
#     coroutine - per-call in_async_context() dispatch).
#   test_node_sync_async_get_queryset_raises_sync_misuse
#     the SyncMisuseError pass-through, unchanged from the resolve_node
#     defaults.
#   test_public_exports
#     DjangoNodeField / DjangoNodesField importable from the package root.

# TODO(spec-032-full_relay-0_0_9 Slice 4): Permission-integration package
# fixtures (live copies land with Slice 6's activation):
#   - node(id:) for a get_queryset-hidden row -> null, not an error;
#   - hidden-row and missing-row paths issue the SAME query count (no
#     existence oracle);
#   - nodes(ids:) mixing visible / hidden / missing ids puts nulls in the
#     right positions.
