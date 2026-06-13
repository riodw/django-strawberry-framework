# feedback3

Scope: fresh pass over `tests/filters`, continuing after `tests/base`.

Rule applied: a package filter test should move to
`examples/fakeshop/test_query/` only when the same behavior is reachable through
the fakeshop `/graphql/` endpoint and the replacement applies the same or
stronger contract pressure. For the library app, use inline
`Model.objects.create(...)` fixtures; do not introduce services for it.

No pytest run for this review.

## High-confidence moves

- `tests/filters/test_sets.py::test_apply_sync_nested_or_branch_applies_related_constraint`
  should move to the live library API suite. The replacement should query
  `allLibraryBranches(filter: { or: [{ shelves: { code: { exact: "match" } } }] })`
  and assert only the branch with the matching shelf returns. That is stronger
  than the package test because it also proves GraphQL input coercion, the real
  `apps.library.filters.BranchFilter`, root visibility, and the HTTP error/data
  envelope.

- `tests/filters/test_sets.py::test_related_filter_on_many_side_relation_returns_each_parent_once`
  should move to a live `allLibraryBranches` test. Seed one branch with two
  matching shelves and another branch without a match, then assert the matching
  branch appears exactly once. With the shipped `BranchFilter.shelves` explicit
  queryset, the matching shelves should use `topic="permanent collection"` so
  the test stresses duplicate-parent prevention rather than the topic boundary.

- `tests/filters/test_sets.py::test_related_filter_answers_identically_direct_and_inside_logic_tree`
  should move to a live query with aliases, for example `direct:
  allLibraryBranches(filter: { shelves: ... })` and `viaAnd:
  allLibraryBranches(filter: { and: [{ shelves: ... }] })`. Assert both aliases
  return identical rows. This keeps the original pressure: direct related
  constraints and logic-tree related constraints must use the same parent-pk
  semantics.

- `tests/filters/test_sets.py::test_q_for_branch_validates_child_form_and_raises_on_malformed_subbranch`
  can move if the live version uses a GraphQL-reachable malformed nested branch.
  Do not use an invalid integer literal, because GraphQL coercion will reject it
  before the filter form. Use the existing custom validator path instead, such
  as `allLibraryPatrons(filter: { and: [{ emailMustHaveAtSign: { exact:
  "bogus" } }] })`, and assert the `FILTER_INVALID` extension and nested field
  error. That preserves the branch-validation contract through the real API.

- `tests/filters/test_sets.py::test_filter_queryset_unions_or_branch` should
  move to a live scalar `or` query on `allLibraryBranches`, with fixtures that
  distinguish the two arms and a non-match. The current live suite covers
  `and` plus `not`, but not a simple scalar `or` union on branches.

## Conditional moves

- `tests/filters/test_sets.py::test_filter_queryset_intersects_and_branch` is
  live-reachable through `allLibraryBranches(filter: { and: [...] })`. Move it
  only if the live replacement keeps the pure two-scalar intersection shape.
  The existing live `test_library_books_filter_combines_and_or_not` is useful
  but not an exact replacement for this simpler `and` contract.

- `tests/filters/test_sets.py::test_apply_sync_filters_against_simple_scalar_input`,
  `tests/filters/test_sets.py::test_apply_sync_passes_through_empty_filter_input`,
  and `tests/filters/test_sets.py::test_apply_sync_raises_graphql_error_on_invalid_input`
  already have stronger live coverage in the library API suite:
  scalar filtering, empty filter input, and invalid form input with
  `FILTER_INVALID`. These package tests can be removed only after coverage is
  confirmed; if retained, treat them as narrow direct-`apply_sync` smoke tests,
  not as the main contract.

- The top-level `HIDE_FLAT_FILTERS` behavior in
  `tests/filters/test_inputs.py::test_build_input_fields_shows_flat_relational_when_hide_flat_filters_false`
  and
  `tests/filters/test_inputs.py::test_build_input_fields_hides_flat_relational_when_hide_flat_filters_true`
  is already represented by
  `examples/fakeshop/test_query/test_library_api.py::test_hide_flat_filters_changes_library_filter_input_shape_over_http`.
  Keep the package tests unless the live introspection test also asserts the
  nested branch remains present and the own scalar fields remain present. The
  package tests currently pin Python-side builder output, not only GraphQL field
  names.

## Keep in package tests

- `tests/filters/test_base.py` should stay. It covers primitive filters,
  `ArrayFilter`, `RangeFilter`, `ListFilter`, `GlobalIDFilter`,
  `GlobalIDMultipleChoiceFilter`, lazy related-class resolution, target
  definition lookup, and global-id strategy validation. Live tests cover the
  consumer-visible GlobalID behavior, but not the primitive class contracts,
  strategy matrix, setter substitution, pass-through branches, or wrong-shape
  unit errors.

- `tests/filters/test_factories.py` should stay. The tests assert BFS traversal,
  cycle handling, de-duplication, input class identity, collision errors,
  dynamic filterset caching, cache-key normalization, reserved-kwarg stripping,
  and LazyType/annotation shape. A live query can prove that a built input type
  works; it cannot prove these factory invariants.

- `tests/filters/test_finalizer.py` should stay. These tests cover phase-2.5
  owner binding, multi-owner compatibility, orphan helper references,
  materialization into module globals, namespace clearing, unresolved related
  filter errors, unregistered target walks, and error wrapping. Those are
  schema construction and registry invariants; a successful live schema is too
  late to exercise most of the failure modes.

- Most of `tests/filters/test_inputs.py` should stay. Lookup-name maps,
  logic-field construction, input dataclass construction, field-spec ledgers,
  annotation conversion, normalization of enums/GlobalIDs/ranges/lists,
  helper reference tracking, string casing helpers, form-field scalar mapping,
  and unimportable-submodule cleanup are package internals.

- Keep
  `tests/filters/test_inputs.py::test_build_input_fields_hides_deep_multi_hop_flat_relational_when_true`
  and
  `tests/filters/test_inputs.py::test_build_input_fields_keeps_non_relatedfilter_flat_traversal_visible_when_true`.
  The current live library filter shape does not cover the deep multi-hop guard
  or the explicit non-`RelatedFilter` traversal exception.

- Keep the permission and request-context tests in
  `tests/filters/test_sets.py`: `_run_permission_checks` active-field
  selection, related-branch recursion, logical-branch recursion, de-duplication,
  depth caps, overrideable `_MAX_LOGIC_DEPTH`, and
  `test_evaluate_logic_tree_preserves_request_context`. They stress internal
  traversal and request propagation, not just row selection.

- Keep
  `tests/filters/test_sets.py::test_permission_checks_run_only_through_apply_entrypoint`.
  It compares the legal `apply_sync` path with direct construction plus `.qs`;
  live GraphQL can only exercise the legal entrypoint.

- Keep `_apply_related_constraints` direct-helper tests that inspect SQL shape,
  inactive-branch behavior, model mismatch, proxy mismatch, and constructor
  ordering:
  `test_apply_related_constraints_runs_active_branch_only`,
  `test_apply_related_constraints_model_mismatch_raises_configuration_error`,
  `test_apply_related_constraints_proxy_model_is_rejected`, and
  `test_apply_sync_passes_constrained_queryset_to_filterset_instance`.
  Live tests can prove visible row behavior, but they cannot prove the helper's
  prechecks or that the constrained queryset is passed into the filterset
  constructor before `.qs` is read.

- Keep `tests/filters/test_sets.py::test_dict_operator_bag_filters_through_apply_sync`
  and the operator-bag normalization tests. Live GraphQL uses Strawberry input
  objects and GraphQL field aliases; the dict-shaped Python operator bag is a
  direct API path.

- Keep the active-branch-without-registered-target tests. A correctly built
  fakeshop schema has registered targets, so live GraphQL should never expose
  that misconfiguration.

- Keep all async filter tests in package tests:
  `test_apply_async_filters_against_scalar_input`,
  `test_derive_related_visibility_querysets_async_scopes_active_branch`,
  `test_apply_async_nested_or_branch_with_async_get_queryset_does_not_raise_sync_misuse`,
  `test_apply_async_runs_permission_checks_off_event_loop_thread`, and
  `test_apply_async_collect_nested_visibility_querysets_pre_derives_or_branch`.
  The fakeshop `/graphql/` view is sync, so moving these would weaken or miss
  the async branches.

## Live replacement notes

- Put moved tests in `examples/fakeshop/test_query/test_library_api.py` and send
  requests with `django.test.Client` to `/graphql/`.

- For branch/shelf related-filter tests, remember that the real
  `BranchFilter.shelves` has `queryset=Shelf.objects.filter(topic="permanent
  collection")`. Fixtures must account for that or the test will accidentally
  stress the topic boundary instead of the intended related-filter behavior.

- For every moved filter test, assert both `response.status_code == 200` and the
  absence or presence of `errors` as appropriate. The stronger contract is not
  just that a code line runs; it is that the real API returns the correct data or
  error shape under the actual schema.

- Do not move filter factory/finalizer tests just because the generated input
  type is reachable live. The live suite should own consumer behavior; package
  tests should continue to own construction invariants, cache identity, and
  failure-mode precision.
