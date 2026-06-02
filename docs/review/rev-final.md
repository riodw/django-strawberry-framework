# Review: final test-run gate (`uv run pytest`)

Status: revision-needed

## Command

```
uv run pytest
```

Run from repo root. Full sweep across all three test trees per AGENTS.md rule 6 (`tests/`, `examples/fakeshop/apps/<app>/tests/`, `examples/fakeshop/test_query/`).

## Summary line (source of truth)

```
===== 4 failed, 1175 passed, 3 skipped, 61 warnings, 108 errors in 40.29s ======
```

Gate result: **revision-needed**. The summary line carries a non-zero `failed` count (4) AND a non-zero `errors` count (108). Per `worker-1.md` "Coverage-gate vs test-failure": only a `failed` count, a collection error, or a test-assertion error flips the gate — both triggers fire here, and neither is coverage-shortfall noise.

## Failing tests (4)

```
FAILED examples/fakeshop/test_query/test_glossary_api.py::test_filter_glossary_terms_by_status_key
FAILED examples/fakeshop/test_query/test_glossary_api.py::test_filter_glossary_terms_by_spec_mention_and_select_edges
FAILED examples/fakeshop/test_query/test_glossary_api.py::test_glossary_documents_are_shared_board_docs_scoped_to_glossary_namespace
FAILED examples/fakeshop/apps/kanban/tests/test_admin.py::test_card_admin_exposes_list_display_and_inlines
```

### Confirmed root cause for `test_card_admin_exposes_list_display_and_inlines`

```
E       AssertionError: assert 4 == 3
E        +  where 4 = len([<class 'apps.kanban.admin.CardItemInline'>, <class 'apps.kanban.admin.ParityClaimInline'>, <class 'apps.kanban.admin.CardReferenceInline'>, <class 'apps.kanban.admin.CardGlossaryTermInline'>])

examples/fakeshop/apps/kanban/tests/test_admin.py:35: AssertionError
```

`CardAdmin.inlines` has grown a fourth inline (`CardGlossaryTermInline`) — the test assertion still pins 3. Test-side update needed (assert 4 plus an `assert CardGlossaryTermInline in card_admin.inlines` parity bullet, or whatever the apps/kanban folder's test convention prefers).

## Erroring tests (108)

108 tests under `examples/fakeshop/test_query/` raise a setup-time `IntegrityError` during fixture loading. Representative traceback (sampled from `test_filter_cards_by_status_key_via_related_filter`):

```
django.db.utils.IntegrityError: UNIQUE constraint failed: kanban_boarddockind.key

INSERT INTO "kanban_boarddockind" ("created_date", "updated_date", "key", "label", "order")
VALUES (?, ?, ?, ?, ?) RETURNING "kanban_boarddockind"."id"
params = (..., ..., 'glossary', 'Glossary', 0)
```

Every error in the sweep shares the same shape — the test setup tries to `INSERT` a `BoardDocKind` row with `key='glossary'` and trips the UNIQUE constraint on `kanban_boarddockind.key`. This points at either (a) a seed-data helper inserting `('glossary', ...)` twice, (b) a data migration that already inserted the row colliding with the seed helper, or (c) a fixture promoted into a base/shared seed without removing it from a per-test seed.

Full erroring-test list (108):

```
examples/fakeshop/test_query/test_kanban_api.py::test_filter_cards_by_status_key_via_related_filter
examples/fakeshop/test_query/test_kanban_api.py::test_filter_cards_by_own_pk_relay_global_id_in
examples/fakeshop/test_query/test_kanban_api.py::test_filter_non_relay_card_items_by_plain_integer_id_in
examples/fakeshop/test_query/test_kanban_api.py::test_select_card_glossary_terms_and_filter_by_term_anchor
examples/fakeshop/test_query/test_kanban_api.py::test_filter_cards_by_own_pk_relay_id_isnull_coerces_boolean
examples/fakeshop/test_query/test_kanban_api.py::test_filter_non_relay_card_items_by_plain_integer_id_exact
examples/fakeshop/test_query/test_kanban_api.py::test_filter_cards_by_m2m_through_parity_key
examples/fakeshop/test_query/test_kanban_api.py::test_filter_cards_by_self_referential_dependency
examples/fakeshop/test_query/test_kanban_api.py::test_filter_and_select_normalized_card_references
examples/fakeshop/test_query/test_kanban_api.py::test_select_m2m_through_parity_claims_with_edge_level
examples/fakeshop/test_query/test_kanban_api.py::test_select_o2o_spec_uuid_side_table_and_timestamps
examples/fakeshop/test_query/test_kanban_api.py::test_reverse_fk_from_lookup_status_to_cards
examples/fakeshop/test_query/test_kanban_api.py::test_select_board_docs_and_lookup_roots_for_static_dashboard
examples/fakeshop/test_query/test_kanban_api.py::test_filter_cards_logical_or_across_statuses
examples/fakeshop/test_query/test_kanban_api.py::test_filter_cards_logical_not_scalar
examples/fakeshop/test_query/test_kanban_api.py::test_filter_cards_logical_and_number_range
examples/fakeshop/test_query/test_kanban_api.py::test_filter_cards_by_title_icontains
examples/fakeshop/test_query/test_kanban_api.py::test_filter_cards_by_number_gt
examples/fakeshop/test_query/test_kanban_api.py::test_filter_cards_by_milestone_key
examples/fakeshop/test_query/test_kanban_api.py::test_filter_cards_by_related_size_rank_numeric_lookup
examples/fakeshop/test_query/test_kanban_api.py::test_filter_cards_by_items_text_reverse_fk_related_filter
examples/fakeshop/test_query/test_kanban_api.py::test_filter_cards_combined_related_and_scalar
examples/fakeshop/test_query/test_kanban_api.py::test_filter_cards_empty_result
examples/fakeshop/test_query/test_kanban_api.py::test_select_multi_fk_fanout_and_second_hop
examples/fakeshop/test_query/test_kanban_api.py::test_select_self_referential_dependents_reverse
examples/fakeshop/test_query/test_kanban_api.py::test_reverse_m2m_from_upstream_to_cards
examples/fakeshop/test_query/test_kanban_api.py::test_select_lookup_uuid_side_table
examples/fakeshop/test_query/test_kanban_api.py::test_relative_size_two_reverse_sets_cards_and_cards_high
examples/fakeshop/test_query/test_kanban_api.py::test_select_labels_m2m
examples/fakeshop/test_query/test_library_api.py::test_library_branch_shelf_book_loan_graph_over_http
examples/fakeshop/test_query/test_library_api.py::test_library_patron_card_and_genre_reverse_paths_over_http
examples/fakeshop/test_query/test_library_api.py::test_library_patron_bigint_lifetime_fines_over_http
examples/fakeshop/test_query/test_library_api.py::test_library_optimizer_selects_book_shelf_in_http_query
examples/fakeshop/test_query/test_library_api.py::test_library_reverse_fk_and_m2m_prefetch_sql_shape_over_http
examples/fakeshop/test_query/test_library_api.py::test_library_choice_enum_and_nullable_subtitle_are_deliberate_http_contracts
examples/fakeshop/test_query/test_library_api.py::test_library_consumer_prefetched_queryset_cooperates_with_optimizer_over_http
examples/fakeshop/test_query/test_library_api.py::test_library_optimizer_hints_are_observable_over_http
examples/fakeshop/test_query/test_library_api.py::test_library_relation_override_shapes_http_response_data
examples/fakeshop/test_query/test_library_api.py::test_library_branches_via_djangolistfield_optimized_nested_selection
examples/fakeshop/test_query/test_library_api.py::test_library_branches_via_djangolistfield_consumer_manager_resolver_over_http
examples/fakeshop/test_query/test_library_api.py::test_library_relay_node_global_id_round_trips
examples/fakeshop/test_query/test_library_api.py::test_library_branches_filter_by_name_icontains
examples/fakeshop/test_query/test_library_api.py::test_library_branches_empty_filter_input_is_noop_over_http
examples/fakeshop/test_query/test_library_api.py::test_library_branches_not_filter_respects_root_visibility_over_http
examples/fakeshop/test_query/test_library_api.py::test_library_books_filter_by_choice_enum
examples/fakeshop/test_query/test_library_api.py::test_library_books_filter_by_choice_enum_in
examples/fakeshop/test_query/test_library_api.py::test_library_books_filter_by_non_relay_fk_scalar_id
examples/fakeshop/test_query/test_library_api.py::test_library_books_filter_by_relay_m2m_global_id
examples/fakeshop/test_query/test_library_api.py::test_library_genres_filter_by_relay_own_pk_global_id_in_list
examples/fakeshop/test_query/test_library_api.py::test_library_genres_filter_by_relay_own_pk_global_id_in_rejects_wrong_type
examples/fakeshop/test_query/test_library_api.py::test_library_branches_filter_by_reverse_fk_lookup
examples/fakeshop/test_query/test_library_api.py::test_library_books_filter_combines_and_or_not
examples/fakeshop/test_query/test_library_api.py::test_library_books_filter_preserves_optimizer_cooperation
examples/fakeshop/test_query/test_library_api.py::test_library_branches_filter_respects_related_queryset_boundary_on_parent
examples/fakeshop/test_query/test_library_api.py::test_book_genres_uses_absolute_import_path_related_filter
examples/fakeshop/test_query/test_library_api.py::test_nested_related_filter_honors_target_get_queryset
examples/fakeshop/test_query/test_library_api.py::test_apply_raises_graphqlerror_on_invalid_filter_input
examples/fakeshop/test_query/test_library_api.py::test_apply_passes_graphql_enum_coercion_before_form_validation
examples/fakeshop/test_query/test_library_api.py::test_root_get_queryset_runs_before_filter_apply
examples/fakeshop/test_query/test_library_api.py::test_relay_global_id_filter_rejects_wrong_type_name
examples/fakeshop/test_query/test_library_api.py::test_library_branches_order_by_name_asc
examples/fakeshop/test_query/test_library_api.py::test_library_books_order_by_subtitle_desc_nulls_last
examples/fakeshop/test_query/test_library_api.py::test_library_books_order_by_forward_fk_relation
examples/fakeshop/test_query/test_library_api.py::test_library_branches_order_by_reverse_fk_relation
examples/fakeshop/test_query/test_library_api.py::test_library_books_order_by_m2m_absolute_import_path
examples/fakeshop/test_query/test_library_api.py::test_library_books_filter_and_order_compose
examples/fakeshop/test_query/test_library_api.py::test_library_books_order_preserves_optimizer_cooperation
examples/fakeshop/test_query/test_library_api.py::test_root_get_queryset_runs_before_order_apply
examples/fakeshop/test_query/test_library_api.py::test_order_check_permission_denies_for_active_field
examples/fakeshop/test_query/test_library_api.py::test_order_check_permission_quiet_for_inactive_field
examples/fakeshop/test_query/test_library_api.py::test_order_check_permission_denies_active_related_branch
examples/fakeshop/test_query/test_library_api.py::test_library_books_order_by_multi_field_priority
examples/fakeshop/test_query/test_library_api.py::test_library_books_order_by_flat_shorthand_path
examples/fakeshop/test_query/test_library_api.py::test_library_branches_order_empty_list_and_null_direction_no_op
examples/fakeshop/test_query/test_products_api.py::test_products_categories_filter_by_name_exact_as_staff
examples/fakeshop/test_query/test_products_api.py::test_products_categories_filter_by_name_denied_for_anonymous
examples/fakeshop/test_query/test_products_api.py::test_products_categories_name_permission_fires_for_non_exact_lookup
examples/fakeshop/test_query/test_products_api.py::test_products_items_related_category_name_permission_fires_for_anonymous
examples/fakeshop/test_query/test_products_api.py::test_products_categories_filter_by_relay_own_pk_global_id_in
examples/fakeshop/test_query/test_products_api.py::test_products_categories_filter_by_starts_with_via_all_lookups
examples/fakeshop/test_query/test_products_api.py::test_products_items_filter_by_related_category_global_id
examples/fakeshop/test_query/test_scalars_api.py::test_scalar_specimen_every_field_wire_format_over_http
examples/fakeshop/test_query/test_scalars_api.py::test_scalar_specimen_bigint_negative_signed_round_trip
examples/fakeshop/test_query/test_scalars_api.py::test_scalar_specimen_bigint_zero_serializes_as_string
examples/fakeshop/test_query/test_scalars_api.py::test_filter_specimens_by_bigint_in_accepts_64bit_values
examples/fakeshop/test_query/test_scalars_api.py::test_scalar_specimen_self_referential_parent_children_over_http
examples/fakeshop/test_query/test_scalars_api.py::test_scalar_specimen_introspects_bigint_scalar_for_both_fields
examples/fakeshop/test_query/test_scalars_api.py::test_scalar_specimen_introspects_json_scalar_in_both_shapes
examples/fakeshop/test_query/test_scalars_api.py::test_nullable_scalar_specimen_all_null_wire_format_over_http
examples/fakeshop/test_query/test_scalars_api.py::test_nullable_scalar_specimen_partner_fk_linkage_over_http
examples/fakeshop/test_query/test_scalars_api.py::test_scalar_specimen_nullable_partners_reverse_relation_over_http
examples/fakeshop/test_query/test_scalars_api.py::test_scalars_set_null_ondelete_detaches_partner_in_http_query
examples/fakeshop/test_query/test_scalars_api.py::test_scalar_specimen_bigint_input_decimal_string_argument_over_http
examples/fakeshop/test_query/test_scalars_api.py::test_scalar_specimen_bigint_input_int_literal_argument_over_http
examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_select_related_on_self_fk_in_http_query
examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_prefetch_related_on_reverse_self_fk_in_http_query
examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_fk_id_elision_for_self_fk_in_http_query
examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_no_fk_id_elision_when_extra_scalar_selected_in_http_query
examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_fk_id_elision_for_each_alias_in_http_query
examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_o6_downgrade_to_prefetch_for_custom_get_queryset_in_http_query
examples/fakeshop/test_query/test_scalars_api.py::test_scalars_custom_get_queryset_filters_inactive_tag_to_null_in_http_query
examples/fakeshop/test_query/test_scalars_api.py::test_scalars_tagged_specimens_reverse_fk_in_http_query
examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_coerces_manager_to_queryset_in_http_query
examples/fakeshop/test_query/test_scalars_filter_api.py::test_scalars_filter_by_label_icontains
examples/fakeshop/test_query/test_scalars_filter_api.py::test_scalars_filter_by_flag_exact
examples/fakeshop/test_query/test_scalars_filter_api.py::test_scalars_filter_by_non_relay_pk_in_list
examples/fakeshop/test_query/test_scalars_filter_api.py::test_scalars_filter_by_related_tag_label
examples/fakeshop/test_query/test_library_api.py::test_hide_flat_filters_changes_library_filter_input_shape_over_http
```

The error mode is uniform — single shared seed/migration bug, not 108 independent regressions. One fix likely clears the whole 108-test cohort.

## Notes

- **Coverage-shortfall (informational only; does NOT flip the gate).** `pytest-cov` reports `FAIL Required test coverage of 100.0% not reached. Total coverage: 51.32%` at the end of the run. This is the expected `--cov-fail-under` shortfall message that the gate explicitly ignores per `worker-1.md` "Coverage-gate vs test-failure: read the summary line, not the exit code". The shortfall is the natural consequence of 108 setup-time errors leaving most of the package unexercised — once the seed-data IntegrityError is fixed and the kanban admin assertion is updated, coverage will jump back up. Recorded here as a follow-up signal for the maintainer.
- **Active-plan / source-version mismatch carries over from project pass.** Per `rev-django_strawberry_framework.md::M1`: plan is `0.0.7`, source is pinned to `0.0.8`. The gate ran against `0.0.8` source on the `0.0.7` plan; result is unaffected (the gate is version-agnostic) but the plan-vs-source mismatch is Worker 0's closeout responsibility.
- **Concurrent maintainer work attribution.** Per AGENTS.md rule 33: post-baseline maintainer commits visible in `git log` (`02ed085`, `c540a42`, `a55de94`, `8c2ecca`, `56c2d89`) added kanban admin features and example-project sharded-DB tooling. The `CardGlossaryTermInline` addition + the `BoardDocKind` seed conflict both originate in this concurrent stream. The owning cycle item per `worker-1.md` "Final test-run gate job" #6 ("Worker 0 will dispatch the owning cycle item again") is the apps/kanban example fixtures + the kanban admin assertion — NOT a `django_strawberry_framework/` source defect.
- **Two folder-pass checklist items are still unchecked in `review-0_0_7.md`** (`rev-filters.md` and `rev-testing.md` per `:66` and `:82`), but Worker 0's spawn prompt explicitly named `rev-final.md` as this cycle item. The gate ran as instructed; the unchecked folder passes are Worker 0's dispatch sequencing concern.
