# Build: Slice 4 — Live acceptance

Spec reference: [`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050] (lines 105-120, 1320-1548)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Inventory refreshed for the whole package in `docs/shadow/helper-inventory.md`. Shapes searched for: `order`, `list_field`, `orderset`, `bounded_rows`, `async`, `view`, `client`, `mount`. Relevant candidates found:
  - `django_strawberry_framework/list_field.py::DjangoListField` — field factory producing the resolver and argument definitions.
  - `django_strawberry_framework/views.py::AsyncDjangoGraphQLView` / `DjangoGraphQLView` — view classes mounted in live acceptance tests.
  - `django_strawberry_framework/orders/sets.py::OrderSet` — public order pipeline and `apply_sync` / `apply_async` dispatch.
  - `django_strawberry_framework/testing/client.py::TestClient` / `AsyncTestClient` — test client helpers.
  - `examples/fakeshop/graphql_client.py::post_graphql` / `graphql_payload` / `assert_graphql_data` / `assert_graphql_success` — shared sync HTTP acceptance helpers.
  - `examples/fakeshop/test_query/conftest.py` — shared schema reload / isolate fixtures.
  - `examples/fakeshop/test_query/test_relations_async_api.py::_post_async` — async view mount and `AsyncClient.post` pattern.
  - `examples/fakeshop/test_query/test_products_visibility_api.py` — holder-pattern schema mount and `override_settings(ROOT_URLCONF=__name__)`.
  - `examples/fakeshop/test_query/test_resource_policy_api.py::_probe_schema` — narrowed policy schema probe pattern.
  - `examples/fakeshop/test_query/test_multi_db.py` — `FAKESHOP_SHARDED=1` holder mount and cross-database query execution.

- **Existing patterns reused.**
  - Module-level schema holder URLconf pattern (`examples/fakeshop/test_query/test_relations_async_api.py:47-56`, `examples/fakeshop/test_query/test_products_visibility_api.py:27-32`):
    `_CURRENT: dict[str, object | None] = {"schema": None}` coupled with `urlpatterns = [path("...", _view)]`,
    `with override_settings(ROOT_URLCONF=__name__): clear_url_caches(); client.post(...)`, and teardown in `finally`
    resetting `_CURRENT["schema"] = None` and calling `clear_url_caches()`. Reused directly for test-local schemas.
  - Live async HTTP testing over `AsyncClient` + `AsyncDjangoGraphQLView` (`examples/fakeshop/test_query/test_relations_async_api.py:89-105`):
    reused for `test_list_field_async_api.py` to test async list completion without `DJANGO_ALLOW_ASYNC_UNSAFE`.
  - Shared sync live HTTP helpers (`examples/fakeshop/graphql_client.py:28-98`):
    `post_graphql`, `graphql_payload`, `assert_graphql_data`, `assert_graphql_success` reused for queries hitting
    the shipped fakeshop `/graphql/` schema endpoint (`allLibraryBranchesViaListField`, etc.).
  - Library-tier inline model creation (`examples/fakeshop/test_query/test_relations_async_api.py:59-87`,
    `examples/fakeshop/apps/library/models.py`):
    following `AGENTS.md` and spec lines 1335-1340, all `Branch`, `Shelf`, `Book`, `Patron`, `MembershipCard` rows are
    created inline with `Model.objects.create(...)`, never importing product seed helpers for library-only rows.
  - Staff context / authentication testing (`examples/fakeshop/apps/library/orders.py:49-65`,
    `examples/fakeshop/apps/library/schema.py:246-256`):
    reusing `client.force_login(staff_user)` / anonymous client requests to exercise permission gates
    (`BranchOrder.check_name_permission`) and visibility filters (`BranchType.get_queryset`).
  - Query capture context (`examples/fakeshop/test_query/test_resource_policy_api.py:53-55`):
    reusing `django.test.utils.CaptureQueriesContext(connection)` to assert 0 row-fetching SQL queries on `limit: 0`
    and on argument rejection.
  - Narrowed resource policy probe schema (`examples/fakeshop/test_query/test_resource_policy_api.py:84-100`):
    reusing `_probe_schema` and existing narrowed endpoint `/rp-rows/` to test `ResourcePolicy` integration.
  - Sharded multi-database execution (`examples/fakeshop/test_query/test_multi_db.py:38-42, 91-101`):
    reusing the `FAKESHOP_SHARDED=1` module gate, `@pytest.mark.django_db(databases=["default", "shard_b"])`, and
    holder mount.

- **New helpers justified.**
  - In `examples/fakeshop/test_query/test_list_field_api.py`:
    - `_post_sync(schema, query, variables=None, client=None)`: test-local helper executing a query against the
      holder-mounted test-local schema using `Client` under `override_settings(ROOT_URLCONF=__name__)`.
    - `_baseline_branches_combined_legacy()`: named baseline helper capturing the pre-card result-or-error, captured
      SQL, and `get_queryset` call count for `branches_combined` when arguments are omitted/null (mandated by
      Decision 11 / Row 22).
    - Conforming and defect-inducing test-local `OrderSet` subclasses (e.g. `_ConformingBranchOrder`,
      `_SubclassReturningBranchOrder`, malformed variants returning sliced/evaluated/combined querysets) to exercise
      public order dispatch and post-apply validation live.
  - In `examples/fakeshop/test_query/test_list_field_async_api.py`:
    - `_post_async(schema, query, variables=None)`: test-local helper executing a query against the holder-mounted
      async schema using `AsyncClient` and `AsyncDjangoGraphQLView`.
    - `_ClosableAsyncIterator`: test-local async iterator carrying an `aclose_called` counter to prove `aclose()`
      invocation without advancing the iterator (since real async generator bodies do not execute `finally` if never
      advanced).
  - No new package-level production helpers, modules, or constants are introduced in Slice 4.

- **Duplication risk avoided.**
  - *No throwaway DjangoType registration:* naive test-local schemas defining `class MyType(DjangoType)` would
    mutate the global registry and cause the acceptance conftest's `_isolate_project_schema_for_acceptance_test`
    identity guard to fail. All test-local fields strictly mount over already-finalized types (`BranchType`,
    `ShelfType`, `GlossaryTermType`, `MembershipCardType`).
  - *No hand-rolled catalog data or misplaced seed imports:* library tests strictly create models inline with
    `Model.objects.create(...)` per `AGENTS.md` and spec lines 1335-1340.
  - *No async posting boilerplate duplication:* single-sited in `_post_async` in `test_list_field_async_api.py`.
  - *No conflation of `aclose()` invocation with generator body finalization:* distinct test cases and distinct
    assertions for iterator `aclose()` (using `_ClosableAsyncIterator` with 0 advances) vs real generator body
    `finally` execution (after at least one item requested).

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against current source before editing.

1. **Implement live sync suite in [`examples/fakeshop/test_query/test_list_field_api.py`][fakeshop-test-list-field-api]**
   (replace stub at lines 1-109):
   - Set up module-level schema holder URLconf:
     - `_CURRENT: dict[str, object | None] = {"schema": None}`
     - `def _graphql_view(request): ... return DjangoGraphQLView.as_view(schema=_CURRENT["schema"])(request)`
     - `urlpatterns = [path("graphql-test/", _graphql_view)]`
     - `def _post_sync(schema, query, variables=None, client=None)` executing under
       `override_settings(ROOT_URLCONF=__name__)` with `clear_url_caches()` in `try...finally`.
   - Seed helpers using inline `models.Branch.objects.create(...)` and `models.Shelf.objects.create(...)`.
   - Implement `_baseline_branches_combined_legacy()` capturing pre-card behavior for `branches_combined`.
   - Implement the 26 live sync test cases specified in spec lines 1355-1456:
     1. `test_shipped_branches_introspection_arguments`: Introspect `allLibraryBranchesViaListField`,
        `allLibraryBranchesViaListFieldNullable`, `allLibraryBranchesViaListFieldManagerResolver`. Verify `offset: Int | None`,
        `limit: Int | None`, `orderBy: [BranchOrderInputType!] | None`.
     2. `test_shipped_branches_staff_ordered_offset_limit`: Staff context,
        `orderBy: [{ name: ASC }, { id: ASC }], offset: 1, limit: 2` returns 2nd and 3rd visible branches.
     3. `test_shipped_branches_anonymous_visibility_before_offset`: Anonymous request,
        `orderBy: [{ city: ASC }, { id: ASC }]`, offset skips only visible branches (restricted branch excluded by
        `BranchType.get_queryset` before offset count).
     4. `test_shipped_branches_order_by_alone`: Staff context, `orderBy: [{ name: ASC }]` arranges entire policy-bounded
        list.
     5. `test_shipped_branches_nonzero_offset_without_order_rejected`: Request with `offset: 1` and no `orderBy` returns
        `LIST_ARGUMENT_INVALID`, `reason="order_required"`.
     6. `test_shipped_branches_offset_bounds_rejected`: `offset: -1` returns `reason="offset_negative"`;
        `offset: MAX_LIST_ROWS + 1` returns `reason="offset_ceiling"`.
     7. `test_shipped_branches_limit_bounds_rejected`: `limit: -1` returns `reason="limit_negative"`;
        `limit: MAX_LIST_ROWS + 1` returns `reason="limit_ceiling"`.
     8. `test_shipped_branches_coercion_failures_and_integral_floats`: Strings, booleans, out-of-range ints, float literals
        produce GraphQL `Int` coercion error with 0 resolver SQL queries; integral float variable (`1.0`) coerces and
        executes.
     9. `test_shipped_branches_limit_zero_short_circuits_sql`: `limit: 0` returns `[]` with 0 row-fetching queries.
     10. `test_shipped_branches_offset_with_limit_zero_precondition`: `offset: 1, limit: 0` without order returns
         `order_required`; with order returns `[]` with 0 row-fetching queries.
     11. `test_holder_trusted_widened_field`: Holder-mounted field with `trusted_max_rows=True, max_rows=MAX_LIST_ROWS + 5`
         returns widened count without client limit; but client `offset: MAX_LIST_ROWS + 1` still rejects against policy
         ceiling.
     12. `test_holder_materialized_and_nullable_none_fields`: `branches_materialized` and `branches_nullable_none` accept
         `limit` and `offset: 0`; positive offset returns `order_required`; non-null `orderBy: []` returns
         `queryset_required`; `branches_nullable_none` preserves `null`.
     13. `test_holder_presliced_configuration_error_under_pass_through`: Under error-policy pass-through fixture,
         `branches_presliced` raises `ConfigurationError` for omitted and active arguments alike.
     14. `test_shipped_branches_empty_order_and_permission_precedence`: Empty list `orderBy: []` or all-null order input
         with `offset: 1` returns `order_required`; anonymous user sending staff-gated `name` order with `offset: 1`
         returns `ORDER_PERMISSION_DENIED` first.
     15. `test_shipped_branches_aggregate_order_no_distinct_in_sql`: Staff context,
         `orderBy: [{ shelves: { code: DESC } }]` plus limit/offset returns 1 row per Branch without `SELECT DISTINCT`
         in SQL.
     16. `test_shipped_branches_error_precedence_pairs`: Both offset and limit negative reports `offset_negative` first;
         `orderBy` + nonzero offset on `branches_materialized` reports `queryset_required`; `orderBy` on `branches_presliced`
         reports visibility error first.
     17. `test_holder_branches_combined_seals`: `branches_combined` with omitted/null arguments preserves baseline; non-null
         argument (even `limit: 0` or `offset: 0`) rejects at source seal with `ConfigurationError`; hook returning
         combined queryset rejects at result seal.
     18. `test_holder_naming_converters`: Schema with `auto_camel_case=False` and schema with custom `NameConverter` prove
         wire names in SDL and `ListArgumentError.argument` follow active converter (`order_by`, custom casing).
     19. `test_holder_model_default_ordering_verdicts`: `branches_default_ordered` over `GlossaryTermType` (whose model has
         `ordering = ["entry_order", "title_sort"]`) accepts `offset: 1` without `orderBy` and with no pk tiebreaker in SQL;
         sibling field calling `.order_by()` flips to `order_required`.
     20. `test_holder_target_without_orderset_or_model_ordering`: Field over `MembershipCardType` (no orderset, no model
         ordering) publishes `offset` and `limit` but NO `orderBy` in SDL; positive offset returns `order_required`.
     21. `test_shipped_branches_offset_alone_bounds`: Offset alone (`offset: 2`, `limit` omitted) returns
         `[2:2 + MAX_LIST_ROWS]`; captured SQL has raised low mark and unchanged policy high mark.
     22. `test_holder_branches_combined_legacy_baseline`: Omitted/all-null request on `branches_combined` matches
         `_baseline_branches_combined_legacy()`.
     23. `test_shipped_branches_independent_aliases`: Single query with two aliases
         `p1: allLibraryBranchesViaListField(offset: 0, limit: 1)` and
         `p2: allLibraryBranchesViaListField(offset: 1, limit: 1)` returns independent pages without shared state.
     24. `test_holder_nullability_propagation_over_none_source`: Nullable outer list and non-null outer list over
         `None`-returning source: both return `null` on limit-only; both error on rejected argument, propagating through
         declared nullability.
     25. `test_holder_orderset_override_returning_queryset_subclass`: Conforming `OrderSet` override returning a `QuerySet`
         subclass derived from sealed input succeeds and normalizes to plain queryset.
     26. (Row 26 sharded database verification implemented in `test_multi_db.py`).

2. **Implement live async suite in [`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async-api]**
   (replace stub at lines 1-102):
   - Set up async holder mount:
     - `_CURRENT: dict[str, object | None] = {"schema": None}`
     - `async def _async_graphql_view(request): ... return await AsyncDjangoGraphQLView.as_view(schema=_CURRENT["schema"])(request)`
     - `urlpatterns = [path("graphql-async/", _async_graphql_view)]`
     - `async def _post_async(schema, query, variables=None)` with `AsyncClient().post("/graphql-async/", ...)` under
       `override_settings(ROOT_URLCONF=__name__)` and `clear_url_caches()` in `finally`.
   - Seed helper `_seed_branches_async()` using inline `Model.objects.create(...)` wrapped in `sync_to_async`.
   - Implement `_ClosableAsyncIterator` with `aclose_called` tracking.
   - Implement test cases (all carrying `@pytest.mark.django_db(transaction=True)` without `DJANGO_ALLOW_ASYNC_UNSAFE`):
     1. `test_async_queryset_completion_default_resolver`: Default resolver over `BranchType` safely completes ordered offset
        page without synchronous-operation errors.
     2. `test_async_queryset_completion_sync_manager_resolver`: Conforming lazy sync resolver returning `Branch.objects`
        completes safely.
     3. `test_async_queryset_completion_sync_queryset_resolver`: Conforming lazy sync resolver returning `Branch.objects.all()`
        completes safely.
     4. `test_async_queryset_completion_async_def_queryset_resolver`: `async def` resolver returning `Branch.objects.all()`
        completes safely.
     5. `test_async_queryset_completion_optimizer_on_and_off`: Repeat queryset completion with `DjangoOptimizerExtension` on
        and off; data matches exactly.
     6. `test_async_pipeline_parity`: Verify `BranchType.get_queryset` visibility precedes order, restricted row is removed
        before offset is counted, and order permission denial serializes before offset guard.
     7. `test_async_generator_cleanup_and_finally_witness`: Async generator returning items: limit-only and `offset: 0`
        serialize list; generator body `finally` witness executes upon accepted stop.
     8. `test_async_iterator_aclose_witness_on_limit_zero_and_rejection`: Using `_ClosableAsyncIterator`, prove `aclose()` is
        invoked with 0 `__anext__` calls on `limit: 0` and on pre-bound rejection (`orderBy` or positive offset).
     9. `test_async_generator_natural_exhaustion_does_not_call_aclose`: Generator with fewer items than requested limit:
        natural exhaustion does NOT invoke `aclose`.
     10. `test_async_error_transport_and_naming`: Assert HTTP 200, exact `data` nullability, complete `extensions` map, and
         `argument` wire spelling under default and custom name converters. Cleanup failures do not displace primary domain
         error.

3. **Update [`examples/fakeshop/test_query/test_resource_policy_api.py`][fakeshop-test-resource-policy]**
   (lines 930-940):
   - Add tests against the existing narrowed-policy `/rp-rows/` mount (`MAX_LIST_ROWS = 10`):
     1. `test_list_field_narrowed_by_client_limit_collection_cost_unchanged`: Create Branch rows inline; send smaller client
        `limit: 2`. Assert exactly 2 rows return; pre-execution collection cost charged remains `ResourcePolicy.max_list_rows`
        (10) rather than 2.
     2. `test_list_field_limit_boundary_at_and_above_narrowed_policy`: Against narrowed mount (`MAX_LIST_ROWS`),
        `limit: MAX_LIST_ROWS` succeeds; `limit: MAX_LIST_ROWS + 1` returns `LIST_ARGUMENT_INVALID` with
        `reason="limit_ceiling"` and message referencing the narrowed mount's ceiling.
     3. `test_list_field_offset_boundary_at_and_above_narrowed_policy`: Ordered `offset: MAX_LIST_ROWS` succeeds;
        `offset: MAX_LIST_ROWS + 1` returns `LIST_ARGUMENT_INVALID` with `reason="offset_ceiling"` referencing the narrowed
        policy ceiling.
     4. `test_list_field_zero_queries_on_rejection_and_limit_zero`: Wrap requests in `CaptureQueriesContext(connection)`:
        `limit: 0` and rejected limit/offset perform 0 row-fetching SQL queries.

4. **Update [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db]**
   (lines 104-124):
   - Discharge `# TODO(spec-050 slice 4)`:
     - Implement `test_post_orderset_routing_mismatch_rejected_on_sharded_db`:
       - Under `FAKESHOP_SHARDED=1` and `@pytest.mark.django_db(databases=["default", "shard_b"])`.
       - Seed rows on both `default` and `shard_b`.
       - Override `BranchOrder.apply_sync` to return a queryset routed to `default` when given a `shard_b` source. Live HTTP
         query sending `orderBy` fails with actionable `ConfigurationError` citing `OrderSet.apply_sync` and routing mismatch.
       - Also test the harder invariant: candidate whose `_db` is `None` on both sides but whose `_hints` differ from the
         sealed source's is rejected.

5. **Update [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme]**:
   - Add `test_list_field_api.py` (dedicated sync suite) and `test_list_field_async_api.py` (async suite) to the enumeration
     of live acceptance test suites.
   - Widen the opening paragraph's governing rule to document the execution-color exemption (async view/client boundary)
     from the shared `graphql_client.py` helpers.

6. **Validate Kanban tracked path constants**:
   - Verify that `test_list_field_api.py` and `test_list_field_async_api.py` are present in
     [`examples/fakeshop/apps/kanban/constants.py`][fakeshop-kanban-constants].
   - Run `scripts/build_kanban_tracked_path_constants.py` if needed.

### Test additions / updates

- **`examples/fakeshop/test_query/test_list_field_api.py`** (new suite replacing stub, 26 cases):
  - `test_shipped_branches_introspection_arguments`: assert `offset`, `limit`, `orderBy` exist on `allLibraryBranchesViaListField`.
  - `test_shipped_branches_staff_ordered_offset_limit`: assert exact 2nd and 3rd visible branches returned.
  - `test_shipped_branches_anonymous_visibility_before_offset`: assert restricted branch excluded before offset is counted.
  - `test_shipped_branches_order_by_alone`: assert whole list ordered by `name`.
  - `test_shipped_branches_nonzero_offset_without_order_rejected`: assert `LIST_ARGUMENT_INVALID` / `order_required`.
  - `test_shipped_branches_offset_bounds_rejected`: assert negative and over-ceiling offset rejections.
  - `test_shipped_branches_limit_bounds_rejected`: assert negative and over-ceiling limit rejections.
  - `test_shipped_branches_coercion_failures_and_integral_floats`: assert coercion errors yield 0 SQL, integral float executes.
  - `test_shipped_branches_limit_zero_short_circuits_sql`: assert `[]` with 0 row-fetching queries.
  - `test_shipped_branches_offset_with_limit_zero_precondition`: assert order required even with `limit: 0`.
  - `test_holder_trusted_widened_field`: assert trusted max_rows widens return but not offset ceiling.
  - `test_holder_materialized_and_nullable_none_fields`: assert limit and offset 0 work, positive offset / orderBy rejected.
  - `test_holder_presliced_configuration_error_under_pass_through`: assert `ConfigurationError` under pass-through gate.
  - `test_shipped_branches_empty_order_and_permission_precedence`: assert permission denial precedes offset rejection.
  - `test_shipped_branches_aggregate_order_no_distinct_in_sql`: assert 1 row per Branch without `DISTINCT`.
  - `test_shipped_branches_error_precedence_pairs`: assert offset before limit, queryset before order, visibility before order.
  - `test_holder_branches_combined_seals`: assert non-null argument rejects at source seal, hook combination at result seal.
  - `test_holder_naming_converters`: assert SDL wire names and error arguments follow active converter.
  - `test_holder_model_default_ordering_verdicts`: assert default ordering satisfies offset, `.order_by()` flips to rejection.
  - `test_holder_target_without_orderset_or_model_ordering`: assert no `orderBy` in SDL, positive offset rejected.
  - `test_shipped_branches_offset_alone_bounds`: assert `[offset:offset + MAX_LIST_ROWS]` in data and SQL marks.
  - `test_holder_branches_combined_legacy_baseline`: assert omitted/null matches baseline helper.
  - `test_shipped_branches_independent_aliases`: assert multiple aliases return independent pages.
  - `test_holder_nullability_propagation_over_none_source`: assert limit-only returns null, rejection propagates error.
  - `test_holder_orderset_override_returning_queryset_subclass`: assert QuerySet subclass normalizes to plain queryset.

- **`examples/fakeshop/test_query/test_list_field_async_api.py`** (new suite replacing stub, 10 cases):
  - `test_async_queryset_completion_default_resolver`: assert default resolver completes safely without sync-unsafe error.
  - `test_async_queryset_completion_sync_manager_resolver`: assert lazy sync manager completes safely.
  - `test_async_queryset_completion_sync_queryset_resolver`: assert lazy sync queryset completes safely.
  - `test_async_queryset_completion_async_def_queryset_resolver`: assert `async def` resolver completes safely.
  - `test_async_queryset_completion_optimizer_on_and_off`: assert identical data with and without optimizer.
  - `test_async_pipeline_parity`: assert visibility -> order -> window ordering in async execution.
  - `test_async_generator_cleanup_and_finally_witness`: assert async generator `finally` runs on accepted stop.
  - `test_async_iterator_aclose_witness_on_limit_zero_and_rejection`: assert `aclose()` invoked with 0 `__anext__` calls.
  - `test_async_generator_natural_exhaustion_does_not_call_aclose`: assert `aclose()` not called on natural exhaustion.
  - `test_async_error_transport_and_naming`: assert complete GraphQL error envelope and active converter argument names.

- **`examples/fakeshop/test_query/test_resource_policy_api.py`** (4 new cases):
  - `test_list_field_narrowed_by_client_limit_collection_cost_unchanged`: assert client limit narrows rows, collection cost unchanged.
  - `test_list_field_limit_boundary_at_and_above_narrowed_policy`: assert boundary at and above narrowed limit ceiling.
  - `test_list_field_offset_boundary_at_and_above_narrowed_policy`: assert boundary at and above narrowed offset ceiling.
  - `test_list_field_zero_queries_on_rejection_and_limit_zero`: assert 0 row-fetching SQL queries on refusal and `limit: 0`.

- **`examples/fakeshop/test_query/test_multi_db.py`** (1 new case):
  - `test_post_orderset_routing_mismatch_rejected_on_sharded_db`: assert `ConfigurationError` on `_db` and `_hints` mismatch.

### Implementation discretion items

- Number of branches and shelves seeded in test fixtures: 4 or 5 branches with 2 shelves each is sufficient to test pages.
- Specific helper names for URLconf holder mounting and post requests (`_post_sync`, `_post_async`).
- Order of test function definitions within the modules.
- Exact query naming in GraphQL document templates.

### Spec slice checklist (verbatim)

- [x] A dedicated `examples/fakeshop/test_query/test_list_field_api.py` drives the sync
      surface over `/graphql/`: ordered offset pages, `orderBy` lists,
      visibility-before-order, limit/cap/error cases, converter naming, and the exceptional
      holder-mounted source shapes. It is the sync counterpart of the async suite rather
      than nineteen more rows inside the broad library application suite.
- [x] [`examples/fakeshop/test_query/test_resource_policy_api.py`][fakeshop-test-resource-policy]
      pins request-policy narrowing over the same field surface.
- [x] A test-local [`AsyncDjangoGraphQLView`][glossary-djangographqlview] mount proves safe
      async queryset completion,
      configured argument names, async iterable cleanup, and async pipeline parity over
      HTTP without `DJANGO_ALLOW_ASYNC_UNSAFE`.
- [x] Add the new async live-test path to the card's predicted files, then regenerate the
      tracked-path constants after the path is in the index so governance sees the file.
- [x] Add the new suite and its shared-helper exemption to
      [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme].

### Boundary count and split analysis

- **Contract verification points:** 34 live contract verification points across 4 test modules:
  - 25 sync cases in `test_list_field_api.py`
  - 10 async cases in `test_list_field_async_api.py`
  - 4 resource policy cases in `test_resource_policy_api.py`
  - 1 sharded multi-db case in `test_multi_db.py`
- **New production boundaries:** 0. This is a test-only live acceptance slice; all package-level production boundaries were implemented and unit-verified in Slices 1-3.
- **Answer to split trigger question:**
  *Why should Slice 4 remain unified instead of splitting?*
  Slice 4 is titled "Live acceptance". Its deliverables are the live test suites that prove the end-to-end integration over HTTP of all contracts built in Slices 1-3. Splitting live acceptance across multiple slices would break the coherence of the live validation tier: `test_list_field_api.py` (sync) and `test_list_field_async_api.py` (async) are explicitly paired counterparts that share the same fakeshop models and domain logic; `test_resource_policy_api.py` integrates the list field with the existing live resource policy test suite; `test_multi_db.py` provides the sharded database verification; and the README/constants bookkeeping completes the tier integration. Splitting them into separate slices would create artificial churn and intermediate states where the live tier is only half-covered and governance constants are in limbo. Therefore, Slice 4 remains a single, cohesive live acceptance slice.

### Hot-path budget

Hot-path budget: Not applicable; plan declares no hot path (Slice 4 is live HTTP acceptance tests).

### Floor verification

Floor verification scope: None; package production boundaries were established in Slices 1-3, and full CI / final gate owns multi-version matrix verification.

---

## Build report (Worker 2)

### Files touched

- [`examples/fakeshop/test_query/test_list_field_api.py`][fakeshop-test-list-field-api] — Replaced placeholder stub with full 25-case sync HTTP acceptance suite covering ordered offset pages, `orderBy` lists, visibility-before-order, limit/offset boundary conditions, zero-short-circuit, name converter wire spellings, and exceptional holder schemas.
- [`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async-api] — Replaced placeholder stub with full 10-case async HTTP acceptance suite covering safe queryset completion under `AsyncDjangoGraphQLView` without `DJANGO_ALLOW_ASYNC_UNSAFE`, optimizer preservation, async iterable cleanup (`aclose` and generator `finally`), error envelopes, and parity.
- [`examples/fakeshop/test_query/test_resource_policy_api.py`][fakeshop-test-resource-policy] — Added 4 live HTTP tests under narrowed `/rp-rows/` mount asserting collection cost stability under client limits, ceiling rejection at boundary and above, and zero row SQL queries on rejection and `limit: 0`.
- [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db] — Discharged `# TODO(spec-050 slice 4)` by adding `test_post_orderset_routing_mismatch_rejected_on_sharded_db` and `test_post_orderset_hints_routing_mismatch_rejected_on_sharded_db` proving post-orderset routing mismatch (`_db` and `_hints` when `_db` is `None` on both sides) is rejected with actionable `ConfigurationError`.
- [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme] — Verified documentation of both new test suites (`test_list_field_api.py` and `test_list_field_async_api.py`) and governing execution-color exemption for async view mounts.

### Tests added or updated

- `examples/fakeshop/test_query/test_list_field_api.py`:
  - `test_shipped_branches_introspection_arguments`
  - `test_shipped_branches_staff_ordered_offset_limit`
  - `test_shipped_branches_anonymous_visibility_before_offset`
  - `test_shipped_branches_order_by_alone`
  - `test_shipped_branches_nonzero_offset_without_order_rejected`
  - `test_shipped_branches_offset_bounds_rejected`
  - `test_shipped_branches_limit_bounds_rejected`
  - `test_shipped_branches_coercion_failures_and_integral_floats`
  - `test_shipped_branches_limit_zero_short_circuits_sql`
  - `test_shipped_branches_offset_with_limit_zero_precondition`
  - `test_holder_trusted_widened_field`
  - `test_holder_materialized_and_nullable_none_fields`
  - `test_holder_presliced_configuration_error_under_pass_through`
  - `test_shipped_branches_empty_order_and_permission_precedence`
  - `test_shipped_branches_aggregate_order_no_distinct_in_sql`
  - `test_shipped_branches_error_precedence_pairs`
  - `test_holder_branches_combined_seals`
  - `test_holder_naming_converters`
  - `test_holder_model_default_ordering_verdicts`
  - `test_holder_target_without_orderset_or_model_ordering`
  - `test_shipped_branches_offset_alone_bounds`
  - `test_holder_branches_combined_legacy_baseline`
  - `test_shipped_branches_independent_aliases`
  - `test_holder_nullability_propagation_over_none_source`
  - `test_holder_orderset_override_returning_queryset_subclass`
- `examples/fakeshop/test_query/test_list_field_async_api.py`:
  - `test_async_queryset_completion_default_resolver`
  - `test_async_queryset_completion_sync_manager_resolver`
  - `test_async_queryset_completion_sync_queryset_resolver`
  - `test_async_queryset_completion_async_def_queryset_resolver`
  - `test_async_queryset_completion_optimizer_on_and_off`
  - `test_async_pipeline_parity`
  - `test_async_generator_cleanup_and_finally_witness`
  - `test_async_iterator_aclose_witness_on_limit_zero_and_rejection`
  - `test_async_generator_natural_exhaustion_does_not_call_aclose`
  - `test_async_error_transport_and_naming`
- `examples/fakeshop/test_query/test_resource_policy_api.py`:
  - `test_list_argument_smaller_limit_serializes_subset_and_charges_full_collection_cost`
  - `test_list_argument_limit_at_and_over_narrowed_policy_ceiling`
  - `test_list_argument_offset_at_and_over_narrowed_policy_ceiling`
  - `test_list_argument_rejections_and_limit_zero_perform_no_sql`
- `examples/fakeshop/test_query/test_multi_db.py`:
  - `test_post_orderset_routing_mismatch_rejected_on_sharded_db`
  - `test_post_orderset_hints_routing_mismatch_rejected_on_sharded_db`

### Validation run

- Non-sharded test suite:
  `uv run pytest examples/fakeshop/test_query/test_list_field_api.py examples/fakeshop/test_query/test_list_field_async_api.py examples/fakeshop/test_query/test_resource_policy_api.py --no-cov`
  Result: 89 passed in 14.49s.
- Sharded test suite:
  `FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop/test_query/test_multi_db.py --no-cov`
  Result: 12 passed in 7.99s.
- Linter and formatting:
  `uv run ruff format examples/fakeshop/test_query/test_list_field_api.py examples/fakeshop/test_query/test_list_field_async_api.py examples/fakeshop/test_query/test_resource_policy_api.py examples/fakeshop/test_query/test_multi_db.py`
  `uv run ruff check examples/fakeshop/test_query/test_list_field_api.py examples/fakeshop/test_query/test_list_field_async_api.py examples/fakeshop/test_query/test_resource_policy_api.py examples/fakeshop/test_query/test_multi_db.py`
  `uv run python scripts/check_trailing_commas.py`
  Result: All clean, 0 errors, 0 files modified.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

- Hot-path budget: Not applicable (test-only acceptance tier slice).

### Floor verification

- Floor verification: Ran with Python 3.14.2 and Django 6.1 (local environment). Multi-version matrix verification is owned by CI.

### Implementation notes

- Holder schemas were mounted dynamically over `DjangoGraphQLView` (sync) and `AsyncDjangoGraphQLView` (async) using the established `_CURRENT` dictionary and `override_settings(ROOT_URLCONF=__name__)` pattern with URL cache clearing in `finally` blocks.
- Tested `DjangoOptimizerExtension` cleanly as an extension class passed to schema configuration.
- Ensured that `constants.py` in `apps/kanban` already tracks `test_list_field_api.py` and `test_list_field_async_api.py`.
- Revision pass: Discharged Worker 3 review findings by adding `_build_list_field_hints_mismatch_schema` and `test_post_orderset_hints_routing_mismatch_rejected_on_sharded_db` in `examples/fakeshop/test_query/test_multi_db.py` to prove the harder half of spec row 26 (`_db` is `None` on both sides, `_hints` differ from sealed source's), and updated failability proofs format per ARTIFACT.md.

---

## Review (Worker 3)

### High:

None.

### Medium:

#### Incomplete Live Invariant for Sharded Database Routing Mismatch (`test_multi_db.py`)

- **Location**: [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db] lines 143-182.
- **Why it matters**:
  - Spec requirement (Row 26 of Live HTTP tier, [`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050] line 1452): "Under `FAKESHOP_SHARDED=1`, the same-route invariant is proven on its HARDER half: an override returning a candidate whose `_db` is `None` on both sides but whose `_hints` differ from the sealed source's is rejected, alongside the existing explicit `.using("default")` versus `.using("shard_b")` mismatch. An explicit-alias row alone would leave routing-intent equality unpinned."
  - Plan requirement (line 213, and checklist line 275): "Also test the harder invariant: candidate whose `_db` is `None` on both sides but whose `_hints` differ from the sealed source's is rejected."
  - Build report claim (line 331): Worker 2 claimed `test_post_orderset_routing_mismatch_rejected_on_sharded_db` proves post-orderset routing mismatch (`_db` / `_hints`), and checked off box line 275 (`- [x] test_post_orderset_routing_mismatch_rejected_on_sharded_db: assert ConfigurationError on _db and _hints mismatch`).
  - However, inspection of [`test_post_orderset_routing_mismatch_rejected_on_sharded_db`][fakeshop-test-multi-db] reveals it only tests `expected db='shard_b'`, `got db='default'`. The harder half of row 26—where `_db` is `None` on both sides and `_hints` differ (e.g., `expected hints={'instance': ...}, got hints={'instance': ...}`)—is completely absent from `test_multi_db.py`.
- **Recommended change**:
  - Add a dedicated test or test case in [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db] under `FAKESHOP_SHARDED=1` where:
    1. The list field resolver returns an unrouted queryset carrying `_hints` (e.g., `qs = models.Branch.objects.all(); qs._hints = {"instance": 1}; return qs`), so `_db` is `None`.
    2. `BranchOrder.apply_sync` returns a candidate whose `_db` is also `None` but whose `_hints` differ (e.g., `ordered = queryset.order_by("name"); ordered._hints = {"instance": 2}; return ordered`).
    3. Over live HTTP (`/graphql/` or holder mount), requesting `orderBy` is rejected with `ConfigurationError` citing `OrderSet.apply_sync changed database routing intent` and the expected vs actual hints.

### Low:

#### Build Report Failability Proof Block Format Divergence

- **Location**: This document, lines 395-403.
- **Why it matters**:
  - Worker 2 recorded test debugging notes ("Failed initially when...") under `### Failability proofs`.
  - Slice 4 is a test-only live acceptance tier that introduced 0 new production boundaries in `django_strawberry_framework/`.
  - Per [`docs/builder/ARTIFACT.md`][artifact-md] line 80 and [`docs/builder/BUILD.md`][build-md] lines 249-251: when no new boundaries are introduced, the subsection should record `None; this pass introduced no new boundary.`.
- **Recommended change**:
  - In Worker 2's re-pass build report, note `None; this pass introduced no new boundary.` under `### Failability proofs`.

### DRY findings

- **Holder URLs and views**: Both [`test_list_field_api.py`][fakeshop-test-list-field-api] and [`test_list_field_async_api.py`][fakeshop-test-list-field-async-api] use the established module-level `_CURRENT` dictionary and test-local views (`_graphql_view` and `_async_graphql_view`). Teardowns are properly scoped in `try...finally` blocks with `clear_url_caches()`.
- **Inline model creation**: All test modules use inline `Model.objects.create(...)` in full compliance with `AGENTS.md` (no product seed helpers used for library or glossary models).
- **Async iterator cleanup**: `_ClosableAsyncIterator` in [`test_list_field_async_api.py`][fakeshop-test-list-field-async-api] is cleanly decoupled from actual execution logic and avoids mock classes.
- **Existence challenge**: None; no unnecessary abstraction was introduced.

### Public-surface check

- Ran `git diff -- django_strawberry_framework/__init__.py`.
- Confirmed `__all__` and package root re-exports are untouched by Slice 4. (`ListArgumentError` was introduced in Slice 1 per spec).

### CHANGELOG sanity (only when the slice touches CHANGELOG.md)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

- Verified [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme]: accurately documents [`test_list_field_api.py`][fakeshop-test-list-field-api] (sync contract) and [`test_list_field_async_api.py`][fakeshop-test-list-field-async-api] (async contract), and explains why the async suite is exempt from `graphql_client.py`.
- Verified [`examples/fakeshop/apps/kanban/constants.py`][fakeshop-kanban-constants]: both test files are tracked in `ACCEPTED_TEST_QUERY_MODULES`.

### What looks solid

- Live HTTP sync test coverage in [`test_list_field_api.py`][fakeshop-test-list-field-api] is exemplary: covers all 25 rows from the spec (introspection, visibility before offset, bounds, coercion short-circuits, trusted widened fields, presliced rejections, precedence pairs, combined seals, naming converters, model default ordering, independent aliases, nullability propagation, and custom QuerySet subclass normalization).
- Live HTTP async test coverage in [`test_list_field_async_api.py`][fakeshop-test-list-field-async-api] thoroughly verifies `AsyncDjangoGraphQLView` without `DJANGO_ALLOW_ASYNC_UNSAFE`, testing sync/async managers/resolvers, optimizer on/off parity, visibility pipeline order, generator `finally` cleanup, `aclose()` invocation with 0 next calls on limit 0 and rejections, natural exhaustion, and error transport.
- Resource policy test coverage in [`test_resource_policy_api.py`][fakeshop-test-resource-policy] cleanly exercises the 4 resource policy interactions: pre-execution collection cost charging `max_list_rows`, policy ceiling rejection, and 0 SQL query execution on refusal and limit 0.

### Temp test verification

- None; no temporary tests were created under `docs/builder/temp-tests/slice-4/`. All inspections and verifications were performed against the live test suites directly.

### Notes for Worker 1 (spec reconciliation)

- None. Spec row 26 is unambiguous; Worker 2 simply needs to add the missing `_hints` test case in `test_multi_db.py`.

### Review outcome

`revision-needed`

---

## Review (Worker 3, pass 2)

### Findings

No blocking findings. Both findings from pass 1 have been completely resolved:
1. **Medium Finding Resolved (Sharded Database Routing Hints Mismatch)**: Worker 2 added `_build_list_field_hints_mismatch_schema` and `test_post_orderset_hints_routing_mismatch_rejected_on_sharded_db` in [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db]. This verifies the harder half of spec row 26: both the sealed list field source and the candidate queryset returned by `BranchOrder.apply_sync` have `_db is None`, but their `_hints` differ (`{'instance': 1}` vs `{'instance': 2}`). Over live HTTP under `FAKESHOP_SHARDED=1`, the query fails closed with `ConfigurationError` citing `OrderSet.apply_sync changed database routing intent` and the expected vs actual hints.
2. **Low Finding Resolved (Failability Proofs Formatting)**: Worker 2 formatted `### Failability proofs` in the build report as `None; this pass introduced no new boundary.` in strict compliance with `ARTIFACT.md`.

### DRY findings

- **Existence challenge**: No redundant abstractions, unused helpers, or unnecessary indirection layers introduced. Test-local fixtures in `test_multi_db.py`, `test_list_field_api.py`, and `test_list_field_async_api.py` are scoped, isolated, and properly cleared.
- **AST inventory check**: Confirmed no duplicate helper symbols or misplaced utilities across the live acceptance test modules.

### Failability audit

- Slice 4 is a test-only live acceptance tier that introduced 0 new production boundaries in `django_strawberry_framework/`.
- Worker 2 correctly recorded `None; this pass introduced no new boundary.` under `### Failability proofs`.
- Zero failability proofs required for re-run.

### Hot-path budget verification

- Not applicable; test-only acceptance tier slice.

### Public-surface check

- Verified via `git diff -- django_strawberry_framework/__init__.py`.
- 0 public exports added or modified in Slice 4 (`ListArgumentError` was introduced and exported in Slice 1).

### CHANGELOG sanity (only when the slice touches CHANGELOG.md)

- Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

- Verified [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme]: accurately documents `test_list_field_api.py` and `test_list_field_async_api.py` and explains the async client exemption.
- Verified [`examples/fakeshop/apps/kanban/constants.py`][fakeshop-kanban-constants]: tracks both new test modules in `ACCEPTED_TEST_QUERY_MODULES`.

### What looks solid

- Complete end-to-end verification of Row 26 in `test_multi_db.py`: both the explicit database alias mismatch (`shard_b` vs `default`) and the unrouted hints mismatch (`_db is None` on both sides with differing `_hints`) are fully proven over live HTTP under `FAKESHOP_SHARDED=1`.
- Clean test execution across both test modes:
  - Sharded test suite (`FAKESHOP_SHARDED=1`): 12 passed in 8.03s.
  - Non-sharded test suite: 89 passed in 14.53s.
- Zero warnings, zero leaks, and complete absence of `DJANGO_ALLOW_ASYNC_UNSAFE` in live async tests.

### Temp test verification

- None; no temporary tests were created under `docs/builder/temp-tests/slice-4/`.

### Notes for Worker 1 (spec reconciliation)

- None; all Slice 4 requirements are fulfilled without drift or open items. Ready for final verification.

### Review outcome

`review-accepted`

---

## Final verification (Worker 1)

### Summary

Slice 4 ships the live HTTP acceptance tier for `DjangoListField` argument handling, proving end-to-end integration over real Django + Strawberry HTTP requests across both sync and async execution models:
- **Sync live HTTP suite** in [`examples/fakeshop/test_query/test_list_field_api.py`][fakeshop-test-list-field-api] (25 tests replacing the placeholder stub): verified SDL argument publication, staff ordered offset/limit pagination, anonymous visibility precedence before offset, order-by alone with staff permissions, nonzero offset order requirement, offset/limit ceiling and sign bounds, GraphQL Int coercion failure short-circuits (0 SQL), limit 0 short-circuit (0 SQL), offset with limit 0 precondition, trusted return widening asymmetry, materialized and nullable-None exceptional source handling, presliced source configuration errors under pass-through, empty order input and permission error precedence, aggregate order without SQL `SELECT DISTINCT`, explicit error precedence pairs, combined source and hook result seals, default and custom `NameConverter` wire spellings, model default ordering acceptance/rejection, targets without orderset or model ordering, offset-alone window bounds, legacy combined source baseline matching, independent field aliases, nullability propagation, and custom QuerySet subclass normalization.
- **Async live HTTP suite** in [`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async-api] (10 tests replacing the placeholder stub): verified safe async queryset completion under `AsyncDjangoGraphQLView` + `AsyncClient` without setting `DJANGO_ALLOW_ASYNC_UNSAFE`, lazy sync manager and queryset resolvers, async def resolver, optimizer on/off parity, visibility/order/window pipeline parity, async generator `finally` cleanup witness, `_ClosableAsyncIterator` `aclose()` invocation with 0 next calls on limit 0 and argument rejection, natural generator exhaustion without `aclose()`, and error envelope transport.
- **Request policy narrowing** in [`examples/fakeshop/test_query/test_resource_policy_api.py`][fakeshop-test-resource-policy] (4 tests): verified client limit subsets do not lower charged collection cost (`max_list_rows`), limit and offset boundaries reject over narrowed mount ceilings, and 0 row-fetching queries are executed on refusal and `limit: 0`.
- **Sharded multi-database routing validation** in [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db] (2 tests under `FAKESHOP_SHARDED=1`): verified post-OrderSet routing mismatch rejection for both explicit database routing (`shard_b` vs `default`) and the harder invariant where `_db` is `None` on both sides but `_hints` differ (`{'instance': 1}` vs `{'instance': 2}`).
- **Documentation and governance**: documented the dedicated test suites and async client exemption in [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme], and confirmed tracking in [`examples/fakeshop/apps/kanban/constants.py`][fakeshop-kanban-constants].

### Checklist audit

Every planned item in `### Spec slice checklist (verbatim)` was verified against the diff:
- [x] A dedicated `examples/fakeshop/test_query/test_list_field_api.py` drives the sync surface over `/graphql/`: ordered offset pages, `orderBy` lists, visibility-before-order, limit/cap/error cases, converter naming, and the exceptional holder-mounted source shapes. It is the sync counterpart of the async suite rather than nineteen more rows inside the broad library application suite. (Verified across 25 live sync HTTP tests in [`examples/fakeshop/test_query/test_list_field_api.py`][fakeshop-test-list-field-api]).
- [x] [`examples/fakeshop/test_query/test_resource_policy_api.py`][fakeshop-test-resource-policy] pins request-policy narrowing over the same field surface. (Verified across 4 live HTTP tests in [`examples/fakeshop/test_query/test_resource_policy_api.py`][fakeshop-test-resource-policy]).
- [x] A test-local [`AsyncDjangoGraphQLView`][glossary-djangographqlview] mount proves safe async queryset completion, configured argument names, async iterable cleanup, and async pipeline parity over HTTP without `DJANGO_ALLOW_ASYNC_UNSAFE`. (Verified across 10 live async HTTP tests in [`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async-api]).
- [x] Add the new async live-test path to the card's predicted files, then regenerate the tracked-path constants after the path is in the index so governance sees the file. (Verified: both `test_list_field_api.py` and `test_list_field_async_api.py` are tracked in `ACCEPTED_TEST_QUERY_MODULES` in [`examples/fakeshop/apps/kanban/constants.py`][fakeshop-kanban-constants]).
- [x] Add the new suite and its shared-helper exemption to [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme]. (Verified: documented in [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme] lines 5 and 15).

### Test run

Focused test suite commands:
1. Non-sharded live acceptance suite:
   `uv run pytest examples/fakeshop/test_query/test_list_field_api.py examples/fakeshop/test_query/test_list_field_async_api.py examples/fakeshop/test_query/test_resource_policy_api.py --no-cov`
   Result: **PASS** (`89 passed in 14.49s`, exit code 0).
2. Sharded multi-database live acceptance suite:
   `FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop/test_query/test_multi_db.py --no-cov`
   Result: **PASS** (`12 passed in 7.96s`, exit code 0).

Both suites executed without `--cov*` flags per [`BUILD.md`][build-md] guidelines; zero test failures or regressions.

### Failability and fail-open confirmation

- **Failability proofs:** Slice 4 is a test-only live acceptance tier that introduced 0 new production boundaries in `django_strawberry_framework/`. Worker 2's build report correctly records `None; this pass introduced no new boundary.` in compliance with [`ARTIFACT.md`][artifact-md] line 80 and [`BUILD.md`][build-md] lines 249-251.
- **Fail-open audit:** Confirmed no fail-open shapes landed in the diff. Slice 4 strictly added acceptance tests and documentation. The new tests verify that production guards fail closed over HTTP:
  - Argument validations reject invalid shapes with `LIST_ARGUMENT_INVALID` and HTTP 200 GraphQL error envelopes.
  - Sliced and combined querysets fail closed with `ConfigurationError` at source and result seals.
  - Multi-database routing mismatches for `_db` and unrouted `_hints` fail closed with `ConfigurationError`.
  - Non-awaitable and coroutine resolver returns fail closed under native async execution without `DJANGO_ALLOW_ASYNC_UNSAFE`.
  - All test queries perform strict exact assertions on payload structures, error codes, and SQL query counts.

### Spec changes made (Worker 1 only)

None.

### Notes for the build plan

Slice 4 is final-accepted. All implementation and contract verification slices (Slices 1-4) are now complete. The next and final in-spec slice is Slice 5 (`Documentation fold-in`), which will:
- Update the list-field docstring and shipped-surface descriptions in `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, and `README.md`.
- Update `ResourcePolicy` and bounding-helper docstrings to distinguish returned/skip ceilings from total database rows scanned.
- Sweep and eliminate all remaining staged `# TODO(spec-050 ...)` anchors across the codebase (including `resource_policy.py`, `list_field.py`, `test_library_api.py`, and `docs/README.md`).
- Update KANBAN cards for Card 050 completion.

---

## Plan (Worker 1, pass 2: gate re-loop)

### Defect and root-cause analysis

During the final test-run gate ([`bld-final.md`][bld-final]), the full test sweep surfaced
Failure 1 in
[`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`][test-ci-governance]:
```text
AssertionError: forbidden DjangoOptimizerExtension extensions= form(s) in active source:
  examples/fakeshop/test_query/test_list_field_async_api.py:242: bare class in a sequence: DjangoOptimizerExtension
  Use a factory over a singleton scoped to that construction site: optimizer = DjangoOptimizerExtension(...) then extensions=[lambda: optimizer]
```

#### Root cause
- In Slice 4, [`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async-api]
  introduced:
  ```python
  schema_opt = DjangoSchema(
      query=_BranchQuery,
      config=strawberry_config(),
      extensions=[DjangoOptimizerExtension],
  )
  ```
- Per `spec-029` Decision 3 and [`tests/test_ci_governance.py`][test-ci-governance], bare class
  `extensions=[DjangoOptimizerExtension]` is forbidden across all active test and application sources.
  Strawberry's `Schema.get_extensions` instantiates a fresh extension instance on every GraphQL
  operation when given a class entry in `extensions=`, causing the optimizer's instance-level
  plan cache (`self._plan_cache`) to have a zero hit rate in production.
- CI governance statically checks the AST of all active `.py` sources via
  `_forbidden_optimizer_entries` and rejects both:
  1. Bare classes in sequences: `extensions=[DjangoOptimizerExtension]`.
  2. Lambdas that construct new instances: `extensions=[lambda: DjangoOptimizerExtension(...)]`.
- The required, conforming pattern across the codebase is a singleton instance bound to a factory
  lambda:
  ```python
  optimizer = DjangoOptimizerExtension()
  schema_opt = DjangoSchema(
      query=_BranchQuery,
      config=strawberry_config(),
      extensions=[lambda: optimizer],
  )
  ```

#### Architectural note on `ExecutionResourcePolicy`
- Gate report [`bld-final.md`][bld-final] line 71 included an incidental mention of
  `DjangoOptimizerExtension(ExecutionResourcePolicy(max_list_rows=10))`.
- Worker 2 must note the following architectural facts:
  1. No class named `ExecutionResourcePolicy` exists in `django_strawberry_framework` (the
     canonical resource policy class is `ResourcePolicy` in
     `django_strawberry_framework.resource_policy`).
  2. `DjangoOptimizerExtension.__init__` accepts
     `(strictness: str = "off", *, execution_context: Any = None, nested_connection_strategy: StrategySelection | None = None)`.
     Passing a non-string or policy object as the first positional argument fails validation at
     construction with `ValueError: strictness must be 'off', 'warn', or 'raise'`.
  3. In `django_strawberry_framework`, request resource policies are configured on
     `DjangoSchema(..., resource_policy=...)`, not on extensions.
  4. In `test_async_queryset_completion_optimizer_on_and_off`, the test query executes `limit: 2`
     against 3 seeded branch rows, which is well within the default `ResourcePolicy` limit
     (`max_list_rows=100`). No custom resource policy is required.
  5. The exact and conforming fix is therefore `optimizer = DjangoOptimizerExtension()` followed by
     `extensions=[lambda: optimizer]`.

### DRY analysis

- **Helper inventory checked.** Shallow AST inventory across `django_strawberry_framework/`
  verified in `docs/shadow/helper-inventory.md`. Existing patterns reviewed:
  - `examples/fakeshop/test_query/test_products_visibility_api.py:159, 192`:
    `optimizer = DjangoOptimizerExtension()`, `extensions=[lambda: optimizer]`.
  - `examples/fakeshop/test_query/test_optimizer_auto_api.py:145`:
    `optimizer = DjangoOptimizerExtension()`, `extensions=[lambda: optimizer]`.
  - `examples/fakeshop/test_query/test_multi_db.py:289, 326, 367`:
    `optimizer = DjangoOptimizerExtension()`, `extensions=[lambda: optimizer]`.
  - `examples/fakeshop/test_query/README.md:23`: documents the standard schema extension pattern:
    `DjangoSchema(..., extensions=[lambda: _optimizer]) over a module-level _optimizer = DjangoOptimizerExtension() singleton`.
- **Existing patterns reused.** Reusing the standard singleton factory lambda pattern
  `optimizer = DjangoOptimizerExtension()`, `extensions=[lambda: optimizer]`.
- **New helpers justified.** None; this is a test-local fix restoring conformance with
  established project conventions and CI governance.
- **Duplication risk avoided.** No unnecessary wrapper classes, redundant policy overrides, or
  extraneous imports introduced.

### Implementation steps

1. In [`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async-api]:
   - Locate `test_async_queryset_completion_optimizer_on_and_off` (around line 239).
   - Before constructing `schema_opt`, instantiate the optimizer extension:
     ```python
     optimizer = DjangoOptimizerExtension()
     ```
   - Update `schema_opt` construction to pass the factory lambda:
     ```python
     schema_opt = DjangoSchema(
         query=_BranchQuery,
         config=strawberry_config(),
         extensions=[lambda: optimizer],
     )
     ```
   - Verify that imports in `examples/fakeshop/test_query/test_list_field_async_api.py` remain clean
     and minimal (no unused imports added).

2. Format and lint:
   - Run `python scripts/check_trailing_commas.py examples/fakeshop/test_query/test_list_field_async_api.py`.
   - Run `uv run ruff check --fix examples/fakeshop/test_query/test_list_field_async_api.py`.
   - Run `uv run ruff format examples/fakeshop/test_query/test_list_field_async_api.py`.

3. Test verification:
   - Run CI governance test:
     `uv run pytest tests/test_ci_governance.py -k "test_no_active_source_uses_a_forbidden_optimizer_extensions_form" --no-cov`
   - Run async list field test suite:
     `uv run pytest examples/fakeshop/test_query/test_list_field_async_api.py --no-cov`

### Test additions / updates

- [`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async-api]:
  - `test_async_queryset_completion_optimizer_on_and_off`: updated to use conforming factory form
    `extensions=[lambda: optimizer]`.
- [`tests/test_ci_governance.py`][test-ci-governance]:
  - `test_no_active_source_uses_a_forbidden_optimizer_extensions_form`: verified to pass with
    0 forbidden entries across active test sources.

### Implementation discretion items

- Worker 2 may instantiate `optimizer = DjangoOptimizerExtension()` locally inside
  `test_async_queryset_completion_optimizer_on_and_off` immediately before `schema_opt` construction.

### Dispatched findings checklist

- [x] In [`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async-api]
      in `test_async_queryset_completion_optimizer_on_and_off`: define
      `optimizer = DjangoOptimizerExtension()` and pass `extensions=[lambda: optimizer]` to
      `DjangoSchema`.
- [x] Verify
      `uv run pytest tests/test_ci_governance.py -k "test_no_active_source_uses_a_forbidden_optimizer_extensions_form" --no-cov`
      passes cleanly.
- [x] Verify `uv run pytest examples/fakeshop/test_query/test_list_field_async_api.py --no-cov`
      passes cleanly.
- [x] Format and lint with `python scripts/check_trailing_commas.py` and `uv run ruff format` /
      `ruff check`.

---

## Build report (Worker 2, pass 2)

### Files touched

- [`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async-api] — in `test_async_queryset_completion_optimizer_on_and_off`, replaced bare class `extensions=[DjangoOptimizerExtension]` with conforming singleton factory lambda `optimizer = DjangoOptimizerExtension()` and `extensions=[lambda: optimizer]`, resolving CI governance violation in `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`.

### Tests added or updated

- [`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async-api] — `test_async_queryset_completion_optimizer_on_and_off` updated to pass singleton optimizer factory lambda to `DjangoSchema`.

### Validation run

- `uv run ruff format examples/fakeshop/test_query/test_list_field_async_api.py` — passed (1 file left unchanged).
- `uv run ruff check --fix examples/fakeshop/test_query/test_list_field_async_api.py` — passed (0 errors).
- `python scripts/check_trailing_commas.py examples/fakeshop/test_query/test_list_field_async_api.py` — passed (0 files modified).
- `uv run pytest tests/test_ci_governance.py -k "test_no_active_source_uses_a_forbidden_optimizer_extensions_form" --no-cov` — passed (1 passed in 3.05s).
- `uv run pytest examples/fakeshop/test_query/test_list_field_async_api.py --no-cov` — passed (10 passed in 5.18s).

### Failability proofs

None; this pass introduced no new boundary.

### Notes for Worker 3

- Resolved the sole governance failure from `bld-final.md` (Failure 1).
- Conformed to spec-029 Decision 3 and `tests/test_ci_governance.py`: bare class extension sequence `extensions=[DjangoOptimizerExtension]` was replaced by local instance singleton factory `optimizer = DjangoOptimizerExtension()` and `extensions=[lambda: optimizer]`.
- No new production boundaries or helpers were introduced.

---

## Review (Worker 3, pass 2)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- Verified against `examples/fakeshop/test_query/` patterns and `tests/test_ci_governance.py`.
- Reused established singleton optimizer pattern `optimizer = DjangoOptimizerExtension()` and `extensions=[lambda: optimizer]` matching `test_products_visibility_api.py`, `test_optimizer_auto_api.py`, and `test_multi_db.py`.
- Existence challenge: No redundant abstractions, helper classes, or extra layers introduced. The fix is a minimal, test-local replacement restoring conformance with `spec-029` Decision 3 and CI governance.

### Failability audit

- Pass 2 of the gate re-loop is a test-only fix in `examples/fakeshop/test_query/test_list_field_async_api.py` that introduced 0 new production boundaries or fail-open behaviors.
- Worker 2 correctly recorded `None; this pass introduced no new boundary.` under `### Failability proofs`.
- Zero failability proofs required.

### Hot-path budget verification

- Not applicable; test-only acceptance tier slice.

### Public-surface check

- Confirmed via `git diff -- django_strawberry_framework/__init__.py`: 0 public exports added or modified in Pass 2. `ListArgumentError` was exported in Slice 1 per spec. `__all__` is unchanged.

### CHANGELOG sanity (only when the slice touches CHANGELOG.md)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; this gate re-loop pass only modified test code in `examples/fakeshop/test_query/test_list_field_async_api.py`.

### What looks solid

- Conforming factory lambda form `optimizer = DjangoOptimizerExtension()` and `extensions=[lambda: optimizer]` satisfies `spec-029` Decision 3 and passes CI governance without regressing operation-level plan caching.
- CI governance test `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form` passes cleanly (1 passed in 3.21s).
- Full async acceptance suite `examples/fakeshop/test_query/test_list_field_async_api.py` passes cleanly (10 passed in 5.12s) without `DJANGO_ALLOW_ASYNC_UNSAFE`.
- Code formatting and trailing commas are clean.

### Temp test verification

- None required; verification directly covered by permanent CI governance and async acceptance test suites.

### Notes for Worker 1 (spec reconciliation)

- None; Failure 1 from `bld-final.md` is fully resolved and verified. Ready for Worker 1 final verification (pass 2).

### Review outcome

`review-accepted`

---

## Final verification (Worker 1, pass 2)

### Summary

Pass 2 of Slice 4 resolves Failure 1 from the final test-run gate ([`bld-final.md`][bld-final]) by updating `test_async_queryset_completion_optimizer_on_and_off` in [`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async-api]. The test previously used a bare class sequence `extensions=[DjangoOptimizerExtension]`, which violates CI governance ([`tests/test_ci_governance.py`][test-ci-governance]) and `spec-029` Decision 3 because Strawberry instantiates a fresh extension instance per operation, zeroing the optimizer's instance-level plan cache hit rate. Worker 2 replaced the bare class with a singleton instance factory lambda `optimizer = DjangoOptimizerExtension()` and `extensions=[lambda: optimizer]`, restoring full conformance with project conventions and CI governance without regressing list field async acceptance coverage.

### Checklist audit

Audited the `### Dispatched findings checklist` in `## Plan (Worker 1, pass 2: gate re-loop)` against the diff:
- [x] In [`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async-api]
      in `test_async_queryset_completion_optimizer_on_and_off`: define
      `optimizer = DjangoOptimizerExtension()` and pass `extensions=[lambda: optimizer]` to
      `DjangoSchema`. (Verified: singleton instance `optimizer = DjangoOptimizerExtension()` instantiated and factory lambda `extensions=[lambda: optimizer]` passed to `DjangoSchema` in `test_async_queryset_completion_optimizer_on_and_off`).
- [x] Verify
      `uv run pytest tests/test_ci_governance.py -k "test_no_active_source_uses_a_forbidden_optimizer_extensions_form" --no-cov`
      passes cleanly. (Verified: passes cleanly in 3.13s with 0 forbidden entries across active sources).
- [x] Verify `uv run pytest examples/fakeshop/test_query/test_list_field_async_api.py --no-cov`
      passes cleanly. (Verified: all 10 async live acceptance tests pass in 5.14s with 0 errors and 0 warnings).
- [x] Format and lint with `python scripts/check_trailing_commas.py` and `uv run ruff format` /
      `ruff check`. (Verified: trailing comma script and ruff checks pass with 0 errors and 0 files modified).

### Test run

Focused test suite commands:
1. CI governance extension form verification:
   `uv run pytest tests/test_ci_governance.py -k "test_no_active_source_uses_a_forbidden_optimizer_extensions_form" --no-cov`
   Result: **PASS** (`1 passed in 3.13s`, exit code 0).
2. Live async list field acceptance suite:
   `uv run pytest examples/fakeshop/test_query/test_list_field_async_api.py --no-cov`
   Result: **PASS** (`10 passed in 5.14s`, exit code 0).

Both test runs executed without `--cov*` flags per [`BUILD.md`][build-md] guidelines; zero test failures or regressions.

### DRY check and code quality audit

- Verified against `examples/fakeshop/test_query/` patterns and `tests/test_ci_governance.py`.
- Reused the standard singleton extension factory lambda pattern `optimizer = DjangoOptimizerExtension()` with `extensions=[lambda: optimizer]` matching `test_products_visibility_api.py`, `test_optimizer_auto_api.py`, and `test_multi_db.py`.
- Confirmed no redundant helper abstractions, wrapper classes, or unnecessary imports were introduced.
- Verified absence of `ExecutionResourcePolicy` references (which does not exist; canonical class is `ResourcePolicy`), confirming the test operates safely within the default policy boundary.

### Failability and fail-open confirmation

- Pass 2 is a test-only fix in `examples/fakeshop/test_query/test_list_field_async_api.py` addressing CI governance conformance. It introduced 0 new production boundaries or fail-open shapes.
- Worker 2 correctly recorded `None; this pass introduced no new boundary.` under `### Failability proofs` in compliance with [`ARTIFACT.md`][artifact-md] and [`BUILD.md`][build-md].
- Zero failability proofs required.

### Spec changes made (Worker 1 only)

None. The conforming factory lambda form preserves all normative contracts of [`spec-050`][spec-050] without requiring spec reconciliation.

### Notes for the build plan

Pass 2 of Slice 4 is final-accepted. Failure 1 from [`bld-final.md`][bld-final] is fully resolved. With both gate re-loop fixes accepted (Failure 1 in Slice 4 and Failure 2 in Slice 2), the final test-run gate may be re-executed.

---

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-050]: ../spec-050-list_field_arguments-0_0_15.md
[glossary-djangographqlview]: ../GLOSSARY.md#djangographqlview

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[artifact-md]: ARTIFACT.md
[bld-final]: bld-final.md
[build-md]: BUILD.md
[worker-1]: worker-1.md
[worker-2]: worker-2.md
[worker-3]: worker-3.md

<!-- django_strawberry_framework/ -->
[list-field]: ../../django_strawberry_framework/list_field.py
[views]: ../../django_strawberry_framework/views.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py

<!-- tests/ -->
[test-ci-governance]: ../../tests/test_ci_governance.py

<!-- examples/ -->
[fakeshop-test-list-field-api]: ../../examples/fakeshop/test_query/test_list_field_api.py
[fakeshop-test-list-field-async-api]: ../../examples/fakeshop/test_query/test_list_field_async_api.py
[fakeshop-test-resource-policy]: ../../examples/fakeshop/test_query/test_resource_policy_api.py
[fakeshop-test-multi-db]: ../../examples/fakeshop/test_query/test_multi_db.py
[fakeshop-test-query-readme]: ../../examples/fakeshop/test_query/README.md
[fakeshop-kanban-constants]: ../../examples/fakeshop/apps/kanban/constants.py

<!-- scripts/ -->
[build-kanban-tracked-paths]: ../../scripts/build_kanban_tracked_path_constants.py

<!-- .venv/ -->

<!-- External -->
