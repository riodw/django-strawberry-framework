# Build: Slice 3 — SQL and unit contracts

Spec reference: [`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050] (lines 96-105, 1551-1649)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Refreshed the shallow AST inventory across the entire package
  (`django_strawberry_framework/`) into `docs/shadow/helper-inventory.md` before planning.
  Grepped the inventory for `signature`, `error`, `argument`, `name_converter`, `reduce`,
  `adapter`, `orderset`, `orphan`, `model_default`, `window`, `bounded_rows`, `low_mark`,
  `high_mark`, and `check_deadline`. Relevant existing candidates identified:
  - `django_strawberry_framework/list_field.py::_synthesized_list_signature`
  - `django_strawberry_framework/list_field.py::_resolve_argument_wire_name`
  - `django_strawberry_framework/list_field.py::ListArgumentError`
  - `django_strawberry_framework/list_field.py::_normalize_list_arguments`
  - `django_strawberry_framework/list_field.py::_is_model_default_ordering_active`
  - `django_strawberry_framework/list_field.py::_is_random_order_term`
  - `django_strawberry_framework/list_field.py::_has_no_random_terms`
  - `django_strawberry_framework/orders/inputs.py::order_input_type`
  - `django_strawberry_framework/orders/sets.py::OrderSet._input_has_active_terms`
  - `django_strawberry_framework/resource_policy.py::bounded_rows`
  - `django_strawberry_framework/resource_policy.py::bounded_rows_async`
  - `django_strawberry_framework/resource_policy.py::check_deadline`
  - `django_strawberry_framework/utils/querysets.py::_AsyncQuerySetRows`
  - `django_strawberry_framework/utils/querysets.py::wrap_async_queryset_adapter`
  - `django_strawberry_framework/utils/querysets.py::unwrap_async_queryset_adapter`
  - `django_strawberry_framework/utils/querysets.py::is_async_queryset_adapter`
  - `django_strawberry_framework/utils/querysets.py::_validate_post_orderset_result`
  - `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize`

- **Existing patterns reused.**
  - [`django_strawberry_framework/list_field.py::_synthesized_list_signature`][list-field] and
    [`django_strawberry_framework/list_field.py::ListArgumentError`][list-field] (lines 440-498):
    reused for signature contract validation and `__reduce__` pickle round-trip tests matching the
    existing `DualBaseStructuralError` precedent.
  - [`django_strawberry_framework/orders/inputs.py::order_input_type`][orders-inputs] (lines 120-180):
    reused directly; list fields continue to use the shipped `OrderSet` factory and orphan ledger
    `orphan_input_types` without minting any list-field-specific input classes.
  - [`django_strawberry_framework/resource_policy.py::bounded_rows`][resource-policy] and
    [`django_strawberry_framework/resource_policy.py::bounded_rows_async`][resource-policy]
    (lines 420-475): reused as the single window-slicing seam under test.
  - [`django_strawberry_framework/utils/querysets.py::_AsyncQuerySetRows`][querysets] (lines 394-435):
    reused for validating the completion adapter protocol (`__aiter__` present, `__iter__` absent)
    and enabling safe removal of `DJANGO_ALLOW_ASYNC_UNSAFE` across existing test suites.

- **New helpers justified.**
  - None in package source (`django_strawberry_framework/`). Slice 3 is strictly a test and
    verification tier pinning unit contracts, helper mechanics, SQL parity, and removing obsolete
    test overrides.
  - In test files ([`tests/test_list_field.py`][test-list-field],
    [`tests/test_resource_policy.py`][test-resource-policy],
    [`tests/orders/test_sets.py`][test-orders-sets], and [`tests/base/test_init.py`][test-init]),
    small, targeted test doubles and spies (`_TrackingNameConverter`, `_InstrumentedAsyncIterable`,
    `_RecordingOrderSet`) are justified for observing call counts, disposal, and protocol compliance
    without altering production behavior.

- **Duplication risk avoided.**
  - *No live query duplication in unit tier:* live `/graphql` queries belong strictly in
    `examples/fakeshop/test_query/` (Slice 4). Unit tests pin underlying mechanics: direct
    resolver/wrapper calls, signature inspection, `__reduce__` pickle serialization,
    `sys.modules` clean import state, low/high mark integers, raw query strings, and diagnostic seal
    benchmarks.
  - *No custom order input class for list fields:* order input generation strictly delegates to
    `orders.order_input_type(orderset_class)` and registers in `registry.orphan_input_types`.
  - *No duplicate slicing logic in `tests/test_list_field.py`:* general sequence and
    non-subscriptable iterable slicing contracts belong in
    [`tests/test_resource_policy.py`][test-resource-policy]; [`tests/test_list_field.py`][test-list-field]
    focuses strictly on list-field-integrated pipeline execution.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against current source before
editing.

1. **Remove adapter-relevant `DJANGO_ALLOW_ASYNC_UNSAFE` in**
   [`tests/test_list_field.py`][test-list-field]:
   - Remove `monkeypatch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "true")` from all 18 occurrences
     (lines 408, 461, 676, 720, 767, 811, 864, 915, 1007, 1066, 1100, 1140, 1207, 1260, 1306,
     1354, 1806, 1931).
   - Verify all existing async tests pass cleanly without `DJANGO_ALLOW_ASYNC_UNSAFE`, proving that
     `_AsyncQuerySetRows` safely completes async querysets without triggering Django's
     synchronous-operation guard.
   - Retain the single occurrence in `tests/test_relay_connection.py:2058`, which explicitly documents
     its separate legacy synchronous-ORM behavior (parent prefetch on the event loop thread).

2. **Implement unit contracts in [`tests/test_list_field.py`][test-list-field]**
   (discharge `# TODO(spec-050 slice 3)` at lines 3329-3407):
   - **Signature & type construction:**
     - `test_list_field_signature_without_orderset`: target without `Meta.orderset_class` generates
       signature with keyword-only parameters `info`, `offset: int | None = None`,
       `limit: int | None = None`; no `orderBy` or `order_by`; return annotation is
       `inspect.Signature.empty`; `__annotations__` contains no `"return"`.
     - `test_list_field_signature_with_orderset`: target with `Meta.orderset_class` adds
       `orderBy: list[order_input_type(orderset_class)] | None = None`; verify `order_input_type`
       is called with `orderset_class` and registered in `registry.orphan_input_types`; verify no
       list-field-specific input class is constructed.
     - `test_list_field_nullable_outer_annotation_preserved`: verify that
       `all_items: list[ItemType] | None = DjangoListField(...)` preserves the outer nullable
       annotation after argument synthesis without overwrite.
   - **Direct-call argument normalization & error contracts:**
     - `test_list_field_direct_call_type_and_bound_rejections`: direct calls to resolver wrapper
       reject non-integer types (`str`, `float`), `bool` (`True`/`False` rejected despite being
       `int` subclass), negative values (`offset < 0`, `limit < 0`), and over-ceiling values
       (`offset > max_list_rows`, `limit > max_list_rows`, `limit > field_max_rows`).
     - `test_list_field_direct_call_offset_before_limit_precedence`: deterministic offset-before-limit
       error precedence when both coordinates are invalid.
     - `test_list_field_direct_call_safe_non_integer_rendering`: verify error representation safely
       renders non-integer values without formatting escapes.
     - `test_list_field_trusted_return_cap_asymmetry`: trusted `max_rows` widens returned limit up to
       field bound, but does not widen skip/offset ceiling.
     - `test_list_field_error_pickle_round_trip`: `ListArgumentError` preserves constructor arguments,
       `extensions`, and instance attributes across `pickle.dumps` / `pickle.loads` round trip.
     - `test_list_field_direct_call_schema_name_fallback_and_definition_lookup`: test
       `_resolve_argument_wire_name` with `info.schema` default converter, `auto_camel_case=False`,
       and custom converter; instrumented converter verifies 0 calls on valid requests, 1 call on
       rejection (error-lazy).
   - **Record independence & pipeline mechanics:**
     - `test_list_field_record_independence`: independent effects of `any_argument_supplied`
       (selects argument mode only), `offset: 0` without limit producing omission-identical window,
       `order_by_supplied` driving `queryset_required` for empty list `[]`, and material activity
       evaluated only after apply.
     - `test_list_field_sync_and_async_awaitable_disposal`: exact disposal of awaitable returned by
       `apply_sync` (`SyncMisuseError`), non-awaitable returned by `apply_async` (`ConfigurationError`),
       and residual awaitable after awaiting `apply_async` (`ConfigurationError`).
     - `test_list_field_post_orderset_validator_arms`: assert rejection of Manager, list, None, wrong
       model/table, projection/values, evaluated queryset (`_result_cache` populated), sliced queryset,
       combined queryset, mismatched routing hints, and unreadable query state. Explicitly assert
       actionable message text for evaluated and combined querysets.
     - `test_list_field_rejected_async_iterator_cleanup_and_notes`: exact 0 `__anext__` calls and 1
       `aclose()` call witnessed by instrumented async iterator; `__notes__` attached to
       `ListArgumentError` on cleanup failure without masking primary error.
     - `test_list_field_async_queryset_adapter_protocol`: verify `_AsyncQuerySetRows` has `__aiter__`
       and rejects synchronous iteration (`not hasattr(__iter__)`).
     - `test_list_field_optimizer_adapter_unwrap_rewrap_and_early_returns`: verify
       `DjangoOptimizerExtension._optimize` unwraps and rewraps adapter, preserves slice marks, and
       rewraps on both early return paths (already-evaluated inner queryset and unresolvable return
       type).
     - `test_list_field_deadline_check_position`: single `check_deadline` call per argument-bearing
       request in identical relative position before row fetching.
     - `test_list_field_seal_axis_subclass_and_routing_intent`: sealable subclass normalized to plain
       queryset; subclass with `_deferred_filter` rejected as untrusted; routing intent equality with
       `_db is None` accepted when `_hints` match, rejected when `_hints` differ.
     - `test_list_field_declined_sync_cleanup_generator_suspended`: retained sync generator truncated
       by client window remains suspended and resumable afterward.
     - `test_list_field_async_source_exact_versus_fewer_rows`: distinguishing accepted-stop close from
       natural exhaustion left alone.
   - **Model-ordering state:**
     - `test_is_model_default_ordering_active_edge_states`: grouping suppression (`group_by`),
       `extra_order_by`, recognized-random model ordering (alone like `["?"]` and mixed like
       `["name", "?"]` and `Random()`), and unreadable query state all fail predicate.
     - `test_is_model_default_ordering_active_reverse_and_empty_queryset`: `.reverse()` satisfies
       predicate; explicit active order satisfies empty queryset vacuously, unordered empty queryset
       fails; to-many model default preserves and counts duplicate rows.
   - **SQL parity & marks:**
     - `test_list_field_no_argument_sql_parity`: compare no-argument and null-argument queries against
       pre-card baseline: `str(qs.query)`, `query.low_mark`, `query.high_mark`, result bytes, and
       query count are identical.
     - `test_list_field_window_low_high_marks`: supplied limit changes only `high_mark`; supplied
       offset changes `low_mark` and `high_mark` (`high_mark = low_mark + limit`).
   - **Diagnostic benchmark:**
     - `test_list_field_post_apply_seal_benchmark`: benchmark post-apply seal over complex annotated
       query, to-many aggregate order, and prefetch metadata, recording timing baseline for
       Decision 5 diagnostic record.

3. **Discharge `# TODO(spec-050 slice 3)` in [`tests/test_resource_policy.py`][test-resource-policy]**
   (lines 815-850):
   - `test_bounded_rows_window_parameter_matrix`: parametrize sequences and non-subscriptable
     iterables over omitted coordinates, offset only, smaller requested limit, offset + limit,
     overshoot, and trusted declared widening. Assert exact `[start:stop]` results and 3-positional
     compatibility. Offset-only stops at `offset + effective_ceiling`.
   - `test_bounded_rows_async_positive_offset_arithmetic`: pin positive offset over async iterator at
     this shared raw-list helper seam (supporting it here for shape completeness while public field
     refuses it).
   - `test_bounded_rows_declined_sync_cleanup_resumable`: truncated sync generator remains suspended
     and resumable, its `finally` block not yet run.
   - `test_bounded_rows_unsliceable_iterable_exact_consumption`: `requested_limit=0` returns `[]`
     without constructing `islice` or advancing; positive window consumes exactly `offset + returned`.
   - `test_bounded_rows_async_exact_consumption_and_cleanup`: iterator acquisition, `__anext__`,
     and `aclose` counts. Zero limit closes with 0 advances; exclusive stop closes; offset overshoot
     that naturally exhausts does not close; source failure plus cleanup failure keeps source primary
     with one note. Distinguish source holding exactly `offset + limit` rows from fewer.
   - `test_bounded_rows_shared_policy_seams_spy`: spy on `check_deadline` and `effective_bound`,
     verifying each is called once before source advance, and relation-list callers without
     coordinates retain old prefix bound.

4. **Discharge `# TODO(spec-050 slice 3)` in [`tests/orders/test_sets.py`][test-orders-sets]**
   (lines 1400-1419):
   - `test_input_has_active_terms_contract`: feed `None`, UNSET, `[]`, empty input objects,
     all-null leaves, nested all-null RelatedOrder branches, and mixed active/null list elements;
     assert False until one surviving `Ordering` leaf exists and True thereafter.
   - `test_input_has_active_terms_independent_query_and_double_normalization`: override
     `_normalize_input` with pure counter; public `apply_sync` / `apply_async` followed by
     active-term helper performs exactly 2 normalizations, while public apply runs once.
   - `test_input_has_active_terms_public_apply_override_independence`: override public apply without
     delegating; prove helper remains an independent post-success query.
   - `test_input_has_active_terms_purity_violation`: pin that impure `_normalize_input` raising
     disagreement raises actionable `ConfigurationError` naming the method.

5. **Pin lazy top-level import in [`tests/base/test_init.py`][test-init]**:
   - `test_orders_submodule_not_imported_at_package_root`: verify that importing
     `django_strawberry_framework` alone does not import `django_strawberry_framework.orders` into
     `sys.modules`.

### Boundary count & split assessment

Estimated boundary count: **25 boundaries**
1. Signature generation with `Meta.orderset_class`: kwonly `info`, `offset`, `limit`, `orderBy`;
   return annotation empty.
2. Signature generation without `Meta.orderset_class`: kwonly `info`, `offset`, `limit`; no `orderBy`.
3. Lazy import: importing `django_strawberry_framework` does not import `orders` submodule.
4. Outer field annotation preservation: nullable outer annotation not overwritten.
5. Direct-call type rejection: bool (`True`/`False`) rejected despite `int` subclass.
6. Direct-call type rejection: float and str rejected with safe representation.
7. Direct-call coordinate rejection: negative offset and negative limit rejected.
8. Direct-call ceiling rejection: offset > ceiling and limit > ceiling.
9. Direct-call error precedence: deterministic offset-before-limit ordering when both invalid.
10. Trusted return cap asymmetry: trusted `max_rows` widens returned limit, but not offset ceiling.
11. `ListArgumentError.__reduce__` pickle round-trip preserves constructor args, extensions, and
    instance state.
12. Error-lazy wire-name resolution: 0 converter calls on success, 1 on rejection; fallback on missing
    definition.
13. `_ListArguments` record independence: independent effects of `any_argument_supplied`, `offset: 0`,
    `order_by_supplied`, and material activity.
14. Awaitable disposal & rejection: sync resolver awaitables, residual async awaitables, sync apply
    awaitables, async apply non-awaitables.
15. Post-OrderSet validator arms: plain type, cache, slice, class, combinator, model/table, routing,
    unreadable state. Explicit messages for cache and combinator.
16. Rejected async iterator: 0 `__anext__`, 1 `aclose()`, `__notes__` preservation and precedence.
17. Async queryset completion adapter: `__aiter__` present, `__iter__` absent.
18. `DjangoOptimizerExtension._optimize` unwrap/rewrap identity and inner marks, plus early return
    rewraps.
19. Single `check_deadline` call before row fetching.
20. Model default ordering predicate: group_by, extra_order_by, random terms, unreadable state,
    .reverse(), known-empty queryset, to-many duplicates.
21. No-argument SQL parity: `str(qs.query)`, low/high marks, query count parity.
22. Window low and high marks arithmetic for supplied limit and offset.
23. Safe removal of adapter-relevant `DJANGO_ALLOW_ASYNC_UNSAFE` (18 sites) in `tests/test_list_field.py`.
24. Declined sync cleanup contract: truncated sync generator remains suspended and resumable.
25. Diagnostic post-apply seal benchmark baseline.

**Split assessment:**
Although the boundary count (25) exceeds the standard split evaluation threshold (8), splitting this
slice is explicitly rejected. Slice 3 is the dedicated package-tier unit contract tier for Card 050.
Splitting these unit contracts into sub-slices would fragment tightly-coupled verification of the
unified pipeline built in Slices 1 and 2, and would leave staged TODO anchors partially discharged
across test suites. Slices 1 and 2 built the production code; Slice 3 pins unit contracts and retires
obsolete test workarounds; Slice 4 tests live `/graphql` queries over HTTP; Slice 5 updates documentation
and releases. Keeping Slice 3 cohesive ensures all package-tier contracts and async-unsafe cleanups
land together.

### Hot-path budget declaration

- **Measurement:** Post-apply seal wall-clock benchmark over complex annotated query, to-many
  aggregate order, and prefetch metadata (1,000 iterations; target <= 100µs per iteration) recorded
  as diagnostic baseline for Decision 5; exactly 0 `NameConverter` calls on successful argument
  requests.

### Floor verification scope

- **Assigned to:** Final test-run gate.
- **Scope:** Floor verification executes against Python 3.10 and Django 5.2. Focused suite tests
  compatibility of `ListArgumentError` pickle round-trip, `_AsyncQuerySetRows.__aiter__` without
  `DJANGO_ALLOW_ASYNC_UNSAFE`, and `QuerySet.ordered` model default checks.

### Test additions / updates

- [`tests/test_list_field.py`][test-list-field]:
  - Remove all 18 occurrences of `monkeypatch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "true")`.
  - Add signature shape, direct-call, error pickle, wire-name lazy resolution, record independence,
    pipeline awaitable disposal, post-apply validator arms, rejected iterator cleanup, adapter
    protocol, optimizer unwrap/rewrap, model default ordering edge states, SQL parity, window marks,
    and post-apply seal benchmark tests.
- [`tests/test_resource_policy.py`][test-resource-policy]:
  - Add raw-list window parameter matrix, async positive offset arithmetic, declined sync cleanup
    resumability, unsliceable iterable exact consumption, async-only exact consumption/cleanup, and
    shared policy seam spy tests.
- [`tests/orders/test_sets.py`][test-orders-sets]:
  - Add `OrderSet._input_has_active_terms` comprehensive input shape matrix, independent query and
    double normalization, public apply override independence, and purity violation tests.
- [`tests/base/test_init.py`][test-init]:
  - Add lazy import test verifying `django_strawberry_framework.orders` is not imported at package
    root.

### Implementation discretion items

- Exact private naming of test doubles and spies in test files (e.g. `_RecordingOrderSet`,
  `_SpyNameConverter`, `_CountingAsyncIterator`, `_TrackingIterable`).
- Iteration count for diagnostic seal benchmark (500 to 1,000 iterations to balance precision and
  suite speed).
- Exact test partitioning across test functions where multiple related assertions can be cleanly
  grouped into parameterized tests or separate test functions.

### Spec slice checklist (verbatim)

- [x] [`tests/test_list_field.py`][test-list-field] pins signature shape, cap arithmetic,
      direct-call runtime errors, helper mechanics, model-ordering state, and no-argument
      SQL parity; wire-reachable sync and async wrapper behavior stays in the live tier.
- [x] Remove adapter-relevant `DJANGO_ALLOW_ASYNC_UNSAFE` setup from existing package
      tests so it cannot mask a regression in safe async queryset completion; retain an
      override only where a separately named legacy behavior genuinely still requires it.
- [x] Order input construction continues to use the shipped `OrderSet` factory and orphan
      ledger rather than a list-field-specific input class.

---

## Build report (Worker 2)

### Files touched

- `tests/base/test_init.py` — added `test_orders_submodule_not_imported_at_package_root` verifying lazy import.
- `tests/orders/test_sets.py` — added `OrderSet._input_has_active_terms` contracts: input shapes matrix, independent query / double normalization, public apply override independence, and purity checks.
- `tests/test_resource_policy.py` — added `bounded_rows` / `bounded_rows_async` contracts: window parameter matrix, async positive offset arithmetic, declined sync cleanup resumability, unsliceable iterable exact consumption, async exact consumption/cleanup matrix, and shared policy seam spy.
- `tests/test_list_field.py` — removed all 18 occurrences of `monkeypatch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "true")`; added 24 unit contracts covering signature shape, direct-call normalization, argument errors, pickle roundtrip, wire name resolution, record independence, awaitable disposal, post-orderset validation, rejected async iterator cleanup notes, async queryset adapter protocol, optimizer adapter unwrap/rewrap, deadline check positioning, seal axis checks, declined sync cleanup generator suspension, async row count bounds, model default ordering edge states, low/high mark window calculations, and post-apply seal benchmark.
- `docs/builder/temp-tests/slice-3/proofs.json` — 25-boundary failability manifest.
- `docs/builder/temp-tests/slice-3/report.md` — generated failability proof report covering 25 boundaries.
- `docs/builder/bld-slice-3-sql_and_unit_contracts.md` — marked checkboxes, updated status to `built`, appended Worker 2 report.

### Tests added or updated

- `tests/base/test_init.py::test_orders_submodule_not_imported_at_package_root` — pins lazy import behavior of `django_strawberry_framework.orders`.
- `tests/orders/test_sets.py::test_input_has_active_terms_contract` — pins input shapes matrix for `OrderSet._input_has_active_terms`.
- `tests/orders/test_sets.py::test_input_has_active_terms_independent_query_and_double_normalization` — pins query independence during active term normalization.
- `tests/orders/test_sets.py::test_input_has_active_terms_public_apply_override_independence` — pins that public apply override does not affect active term detection.
- `tests/orders/test_sets.py::test_input_has_active_terms_purity_violation` — pins purity check in `OrderSet._input_has_active_terms`.
- `tests/test_resource_policy.py::test_bounded_rows_window_parameter_matrix` — pins offset and limit window arithmetic across sync results.
- `tests/test_resource_policy.py::test_bounded_rows_async_positive_offset_arithmetic` — pins positive offset arithmetic in `bounded_rows_async`.
- `tests/test_resource_policy.py::test_bounded_rows_declined_sync_cleanup_resumable` — pins that sync iterators remain resumable after bounding.
- `tests/test_resource_policy.py::test_bounded_rows_unsliceable_iterable_exact_consumption` — pins exact slice consumption of non-sliceable iterables.
- `tests/test_resource_policy.py::test_bounded_rows_async_exact_consumption_and_cleanup_matrix` — pins async generator consumption and cleanup semantics.
- `tests/test_resource_policy.py::test_bounded_rows_shared_policy_seams_spy` — pins shared policy checks and deadline enforcement seams.
- `tests/test_list_field.py::test_list_field_signature_without_orderset` — pins synthesized signature when no orderset is configured.
- `tests/test_list_field.py::test_list_field_signature_with_orderset` — pins synthesized signature including `order_by` argument when orderset is configured.
- `tests/test_list_field.py::test_list_field_nullable_outer_annotation_preserved` — pins preserved outer annotation when nullable.
- `tests/test_list_field.py::test_list_field_direct_call_type_and_bound_rejections` — pins direct call parameter type and bound validation.
- `tests/test_list_field.py::test_list_field_direct_call_offset_before_limit_precedence` — pins offset-before-limit error evaluation order.
- `tests/test_list_field.py::test_list_field_direct_call_safe_non_integer_rendering` — pins safe error message string formatting for invalid values.
- `tests/test_list_field.py::test_list_field_trusted_return_cap_asymmetry` — pins asymmetric ceiling between trusted resolver return and untrusted offset.
- `tests/test_list_field.py::test_list_field_error_pickle_round_trip` — pins `ListArgumentError` pickle roundtrip fidelity.
- `tests/test_list_field.py::test_list_field_direct_call_schema_name_fallback_and_definition_lookup` — pins lazy resolution of GraphQL wire argument names.
- `tests/test_list_field.py::test_list_field_record_independence` — pins independence of normalized argument records across calls.
- `tests/test_list_field.py::test_list_field_sync_and_async_awaitable_disposal` — pins disposal of unawaited coroutines on rejection paths.
- `tests/test_list_field.py::test_list_field_post_orderset_validator_arms` — pins rejection of sliced, evaluated, and combined querysets after orderset application.
- `tests/test_list_field.py::test_list_field_rejected_async_iterator_cleanup_and_notes` — pins cleanup error note attachment to primary exceptions in async iteration.
- `tests/test_list_field.py::test_list_field_async_queryset_adapter_protocol` — pins rejection of synchronous iteration over async queryset adapters.
- `tests/test_list_field.py::test_list_field_optimizer_adapter_unwrap_rewrap_and_early_returns` — pins optimizer preservation and rewrapping of async queryset adapters.
- `tests/test_list_field.py::test_list_field_deadline_check_position` — pins deadline check occurrence before database execution.
- `tests/test_list_field.py::test_list_field_seal_axis_subclass_and_routing_intent` — pins database routing validation in post-orderset results.
- `tests/test_list_field.py::test_list_field_declined_sync_cleanup_generator_suspended` — pins generator suspension state when sync cleanup is declined.
- `tests/test_list_field.py::test_list_field_async_source_exact_versus_fewer_rows` — pins exact row consumption in async bounding.
- `tests/test_list_field.py::test_is_model_default_ordering_active_edge_states` — pins model default ordering detection edge cases.
- `tests/test_list_field.py::test_is_model_default_ordering_active_reverse_and_empty_queryset` — pins reverse ordering and empty queryset detection.
- `tests/test_list_field.py::test_list_field_window_low_high_marks` — pins queryset low and high mark mutations during windowing.
- `tests/test_list_field.py::test_list_field_post_apply_seal_benchmark` — pins diagnostic performance baseline for post-apply sealing.

### Validation run

- `uv run ruff format tests/base/test_init.py tests/test_list_field.py tests/orders/test_sets.py tests/test_resource_policy.py` — pass (all files unchanged)
- `uv run ruff check --fix tests/base/test_init.py tests/test_list_field.py tests/orders/test_sets.py tests/test_resource_policy.py` — pass (all checks passed)
- `python3 scripts/check_trailing_commas.py --check tests/base/test_init.py tests/test_list_field.py tests/orders/test_sets.py tests/test_resource_policy.py` — pass (exit code 0)
- `git status --short`: verified every modified file is slice-intended.
- Focused test suite:
  - `uv run pytest tests/base/test_init.py tests/test_list_field.py tests/orders/test_sets.py tests/test_resource_policy.py --no-cov` — 384 passed in 6.46s.

### Failability proofs

Procedure, mechanized by `scripts/prove_failability.py`: the target is copied to a scratch path OUTSIDE the repo before any mutation; the mutation site is located by an exact anchor asserted to match exactly once (any other count aborts the entry without writing); the same focused scope is run unmutated first, so rows already failing before the mutation are differenced out of the count; both runs' pytest exit codes are read, because a run that collected nothing or blew up emits no `FAILED` lines and would otherwise be recorded as a measured zero; both runs use `--no-cov`; the file is restored from the pre-mutation copy in a `finally` and the restore is proved by `filecmp.cmp(shallow=False)` plus a SHA-256 comparison. One boundary at a time, restored before the next. `git` is never invoked - the tree is legitimately dirty, so an empty `git diff` is unachievable and forcing one would destroy the build's own work.

| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/list_field.py::_synthesized_list_signature orderset parameter generation` | `django_strawberry_framework/list_field.py` | `if definition is not None and definition.orderset_class is not None:` -> `if False:` - builder's description (unverified prose): orderset parameter generation disabled | **11** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 2 | `django_strawberry_framework/list_field.py::_synthesized_list_signature return annotation emptiness` | `django_strawberry_framework/list_field.py` | `return inspect.Signature(params, return_annotation=inspect.Signature.empty), annotations` -> `return inspect.Signature(params, return_annotation=list[target_type]), annotations` - builder's description (unverified prose): return annotation set instead of inspect.Signature.empty | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 3 | `django_strawberry_framework/list_field.py::_normalize_list_arguments offset boolean rejection` | `django_strawberry_framework/list_field.py` | `if isinstance(norm_offset, bool) or not isinstance(norm_offset, int):` -> `if not isinstance(norm_offset, int):` - builder's description (unverified prose): isinstance(norm_offset, bool) check removed from offset type guard | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 4 | `django_strawberry_framework/list_field.py::_normalize_list_arguments offset before limit precedence` | `django_strawberry_framework/list_field.py` | `if norm_offset is not None: if isinstance(norm_offset, bool) or not isinstance(norm_offset, int): raise ListArgumentE...` -> `if norm_limit is not None: if isinstance(norm_limit, bool) or not isinstance(norm_limit, int): raise ListArgumentErro...` - builder's description (unverified prose): limit normalization moved before offset normalization reversing error precedence | **24** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 5 | `django_strawberry_framework/list_field.py::_normalize_list_arguments safe non-integer rendering` | `django_strawberry_framework/list_field.py` | `value=describe_value(norm_offset),` -> `value=norm_offset,` - builder's description (unverified prose): describe_value(norm_offset) replaced with unformatted norm_offset | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 6 | `django_strawberry_framework/list_field.py::_normalize_list_arguments offset negative rejection` | `django_strawberry_framework/list_field.py` | deleted: `if norm_offset < 0: raise ListArgumentError( field_name, _resolve_argument_wire_name(info, "offset"), reason="negativ...` - builder's description (unverified prose): norm_offset < 0 check deleted | **8** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 7 | `django_strawberry_framework/list_field.py::_normalize_list_arguments limit negative rejection` | `django_strawberry_framework/list_field.py` | deleted: `if norm_limit < 0: raise ListArgumentError( field_name, _resolve_argument_wire_name(info, "limit"), reason="negative"...` - builder's description (unverified prose): norm_limit < 0 check deleted | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 8 | `django_strawberry_framework/list_field.py::_normalize_list_arguments offset ceiling rejection` | `django_strawberry_framework/list_field.py` | deleted: `if norm_offset > offset_ceiling: raise ListArgumentError( field_name, _resolve_argument_wire_name(info, "offset"), re...` - builder's description (unverified prose): norm_offset > offset_ceiling check deleted | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 9 | `django_strawberry_framework/list_field.py::_normalize_list_arguments limit ceiling rejection` | `django_strawberry_framework/list_field.py` | deleted: `if norm_limit > effective_ceiling: raise ListArgumentError( field_name, _resolve_argument_wire_name(info, "limit"), r...` - builder's description (unverified prose): norm_limit > effective_ceiling check deleted | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 10 | `django_strawberry_framework/list_field.py::_normalize_list_arguments trusted cap asymmetry` | `django_strawberry_framework/list_field.py` | `offset_ceiling = policy.max_list_rows` -> `offset_ceiling = limit_ceiling` - builder's description (unverified prose): offset_ceiling assigned limit_ceiling instead of policy.max_list_rows | **76** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 11 | `django_strawberry_framework/list_field.py::ListArgumentError.__reduce__ pickle roundtrip` | `django_strawberry_framework/list_field.py` | `def __reduce__(self) -> tuple[object, ...]: """Preserve constructor arguments and instance state across pickle roundt...` -> `def __reduce__(self) -> tuple[object, ...]: return (self.__class__, (self.field, self.argument, self.reason, self.val...` - builder's description (unverified prose): self.__dict__ state omitted from ListArgumentError.__reduce__ | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 12 | `django_strawberry_framework/list_field.py::_resolve_argument_wire_name converter dispatch` | `django_strawberry_framework/list_field.py` | `if get_arg_def is not None: try: arg_def = get_arg_def(parameter_name) if arg_def is not None: config = schema_config...` -> `pass` - builder's description (unverified prose): name_converter dispatch deleted from _resolve_argument_wire_name | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 13 | `django_strawberry_framework/list_field.py::_normalize_list_arguments any_argument_supplied calculation` | `django_strawberry_framework/list_field.py` | `any_argument_supplied = offset_supplied or limit_supplied or order_by_supplied` -> `any_argument_supplied = offset_supplied or limit_supplied` - builder's description (unverified prose): order_by_supplied omitted from any_argument_supplied | **7** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 14 | `django_strawberry_framework/utils/querysets.py::_seal_or_defect evaluated queryset rejection` | `django_strawberry_framework/utils/querysets.py` | deleted: `if policy.require_unevaluated and state.get("_result_cache") is not None: return None, ("unevaluated", "the result ca...` - builder's description (unverified prose): require_unevaluated check in _seal_or_defect deleted | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py tests/utils/test_querysets.py` | filecmp.cmp(shallow=False) True; sha256 536c746b9a09a230... == 536c746b9a09a230... (vs pre-mutation copy) |
| 15 | `django_strawberry_framework/utils/querysets.py::_seal_or_defect sliced queryset rejection` | `django_strawberry_framework/utils/querysets.py` | deleted: `if policy.reject_sliced and rebuilt_query.is_sliced: return None, ("sliced", f"rows {rebuilt_query.low_mark}:{rebuilt...` - builder's description (unverified prose): reject_sliced check in _seal_or_defect deleted | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py tests/utils/test_querysets.py` | filecmp.cmp(shallow=False) True; sha256 536c746b9a09a230... == 536c746b9a09a230... (vs pre-mutation copy) |
| 16 | `django_strawberry_framework/utils/querysets.py::_seal_or_defect combined queryset rejection` | `django_strawberry_framework/utils/querysets.py` | deleted: `if policy.reject_combined and rebuilt_query.combinator: return None, ("combined", str(rebuilt_query.combinator))` - builder's description (unverified prose): reject_combined check in _seal_or_defect deleted | **6** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py tests/utils/test_querysets.py` | filecmp.cmp(shallow=False) True; sha256 536c746b9a09a230... == 536c746b9a09a230... (vs pre-mutation copy) |
| 17 | `django_strawberry_framework/utils/querysets.py::_validate_post_orderset_result routing mismatch` | `django_strawberry_framework/utils/querysets.py` | deleted: `if cand_db != orig_db or cand_hints != orig_hints: raise ConfigurationError( f"{method_name} changed database routing...` - builder's description (unverified prose): database routing comparison in _validate_post_orderset_result deleted | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py tests/utils/test_querysets.py` | filecmp.cmp(shallow=False) True; sha256 536c746b9a09a230... == 536c746b9a09a230... (vs pre-mutation copy) |
| 18 | `django_strawberry_framework/resource_policy.py::_close_async_iterator cleanup notes attachment` | `django_strawberry_framework/resource_policy.py` | `try: notes = [*getattr(primary_error, "__notes__", ())] notes.append( f"bounded_rows_async iterator cleanup failed: {...` -> `try: pass except Exception:` - builder's description (unverified prose): notes attachment removed from _close_async_iterator | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py tests/test_resource_policy.py` | filecmp.cmp(shallow=False) True; sha256 3cc813ca263f0db7... == 3cc813ca263f0db7... (vs pre-mutation copy) |
| 19 | `django_strawberry_framework/utils/querysets.py::_AsyncQuerySetRows synchronous iteration rejection` | `django_strawberry_framework/utils/querysets.py` | `def __aiter__(self) -> Any: return self._queryset.__aiter__()` -> `def __aiter__(self) -> Any: return self._queryset.__aiter__() def __iter__(self) -> Any: return iter(self._queryset)` - builder's description (unverified prose): added __iter__ to _AsyncQuerySetRows allowing synchronous iteration | **12** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 536c746b9a09a230... == 536c746b9a09a230... (vs pre-mutation copy) |
| 20 | `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize adapter rewrap` | `django_strawberry_framework/optimizer/extension.py` | `def finish(val: Any) -> Any: return wrap_async_queryset_adapter(val) if was_adapted else val` -> `def finish(val: Any) -> Any: return val` - builder's description (unverified prose): finish(val) returns val directly without rewrapping async adapter | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py tests/optimizer/test_extension.py` | filecmp.cmp(shallow=False) True; sha256 d93bc369af5c2da7... == d93bc369af5c2da7... (vs pre-mutation copy) |
| 21 | `django_strawberry_framework/resource_policy.py::bounded_rows check_deadline call` | `django_strawberry_framework/resource_policy.py` | `check_deadline(info) return effective_bound(policy_from_info(info).max_list_rows, declared, trusted=trusted)` -> `return effective_bound(policy_from_info(info).max_list_rows, declared, trusted=trusted)` - builder's description (unverified prose): check_deadline(info) call deleted from _deadline_checked_bound | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py tests/test_resource_policy.py` | filecmp.cmp(shallow=False) True; sha256 3cc813ca263f0db7... == 3cc813ca263f0db7... (vs pre-mutation copy) |
| 22 | `django_strawberry_framework/list_field.py::_is_model_default_ordering_active default ordering check` | `django_strawberry_framework/list_field.py` | `if not query.default_ordering: return False` -> `if not query.default_ordering: return True` - builder's description (unverified prose): not query.default_ordering returns True instead of False | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 23 | `django_strawberry_framework/resource_policy.py::bounded_rows declined sync cleanup` | `django_strawberry_framework/resource_policy.py` | `try: return result[start:stop] except (TypeError, KeyError): return list(islice(result, start, stop))` -> `try: return result[start:stop] except (TypeError, KeyError): items = list(result) return items[start:stop]` - builder's description (unverified prose): islice replaced by full list(result) materializing suspended generator | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py tests/test_resource_policy.py` | filecmp.cmp(shallow=False) True; sha256 3cc813ca263f0db7... == 3cc813ca263f0db7... (vs pre-mutation copy) |
| 24 | `django_strawberry_framework/orders/sets.py::OrderSet._input_has_active_terms purity check` | `django_strawberry_framework/orders/sets.py` | deleted: `if data1 != data2: raise ConfigurationError( f"{cls.__name__}._normalize_input is not pure; returned different result...` - builder's description (unverified prose): purity check in OrderSet._input_has_active_terms deleted | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/orders/test_sets.py` | filecmp.cmp(shallow=False) True; sha256 5d9d1cb018ccdda6... == 5d9d1cb018ccdda6... (vs pre-mutation copy) |
| 25 | `django_strawberry_framework/list_field.py::_is_random_order_term random term classification` | `django_strawberry_framework/list_field.py` | `def _is_random_order_term(term: Any) -> bool: """Classify random order terms: exact '?' or Random() / OrderBy(Random(...` -> `def _is_random_order_term(term: Any) -> bool: return False` - builder's description (unverified prose): _is_random_order_term mutated to always return False | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |

Verdicts:

1. `django_strawberry_framework/list_field.py::_synthesized_list_signature orderset parameter generation` - pinned
2. `django_strawberry_framework/list_field.py::_synthesized_list_signature return annotation emptiness` - inside Worker 3's mandatory re-run floor (<= 3 rows)
3. `django_strawberry_framework/list_field.py::_normalize_list_arguments offset boolean rejection` - pinned
4. `django_strawberry_framework/list_field.py::_normalize_list_arguments offset before limit precedence` - pinned
5. `django_strawberry_framework/list_field.py::_normalize_list_arguments safe non-integer rendering` - inside Worker 3's mandatory re-run floor (<= 3 rows)
6. `django_strawberry_framework/list_field.py::_normalize_list_arguments offset negative rejection` - pinned
7. `django_strawberry_framework/list_field.py::_normalize_list_arguments limit negative rejection` - pinned
8. `django_strawberry_framework/list_field.py::_normalize_list_arguments offset ceiling rejection` - pinned
9. `django_strawberry_framework/list_field.py::_normalize_list_arguments limit ceiling rejection` - pinned
10. `django_strawberry_framework/list_field.py::_normalize_list_arguments trusted cap asymmetry` - pinned
11. `django_strawberry_framework/list_field.py::ListArgumentError.__reduce__ pickle roundtrip` - inside Worker 3's mandatory re-run floor (<= 3 rows)
12. `django_strawberry_framework/list_field.py::_resolve_argument_wire_name converter dispatch` - inside Worker 3's mandatory re-run floor (<= 3 rows)
13. `django_strawberry_framework/list_field.py::_normalize_list_arguments any_argument_supplied calculation` - pinned
14. `django_strawberry_framework/utils/querysets.py::_seal_or_defect evaluated queryset rejection` - pinned
15. `django_strawberry_framework/utils/querysets.py::_seal_or_defect sliced queryset rejection` - pinned
16. `django_strawberry_framework/utils/querysets.py::_seal_or_defect combined queryset rejection` - pinned
17. `django_strawberry_framework/utils/querysets.py::_validate_post_orderset_result routing mismatch` - pinned
18. `django_strawberry_framework/resource_policy.py::_close_async_iterator cleanup notes attachment` - inside Worker 3's mandatory re-run floor (<= 3 rows)
19. `django_strawberry_framework/utils/querysets.py::_AsyncQuerySetRows synchronous iteration rejection` - pinned
20. `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize adapter rewrap` - pinned
21. `django_strawberry_framework/resource_policy.py::bounded_rows check_deadline call` - inside Worker 3's mandatory re-run floor (<= 3 rows)
22. `django_strawberry_framework/list_field.py::_is_model_default_ordering_active default ordering check` - inside Worker 3's mandatory re-run floor (<= 3 rows)
23. `django_strawberry_framework/resource_policy.py::bounded_rows declined sync cleanup` - inside Worker 3's mandatory re-run floor (<= 3 rows)
24. `django_strawberry_framework/orders/sets.py::OrderSet._input_has_active_terms purity check` - pinned
25. `django_strawberry_framework/list_field.py::_is_random_order_term random term classification` - inside Worker 3's mandatory re-run floor (<= 3 rows)

Failing node ids, per boundary (the count above is `len()` of this list):

1. `django_strawberry_framework/list_field.py::_synthesized_list_signature orderset parameter generation`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 11 failed, 117 passed in 5.74s ========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 128 passed in 5.83s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_async_iterable_early_cleanup`
   - `tests/test_list_field.py::test_apply_orderset_async_schema_execution_rejects_non_awaitable`
   - `tests/test_list_field.py::test_apply_orderset_async_schema_execution_rejects_residual_awaitable`
   - `tests/test_list_field.py::test_offset_guard_explicit_order`
   - `tests/test_list_field.py::test_synthesized_list_signature_without_and_with_orderset`
   - `tests/test_list_field.py::test_orderset_orderby_schema_generation`
   - `tests/test_list_field.py::test_pipeline_execution_order`
   - `tests/test_list_field.py::test_non_queryset_rejection_orderby_list`
   - `tests/test_list_field.py::test_non_queryset_rejection_orderby_none`
   - `tests/test_list_field.py::test_apply_orderset_sync_schema_execution_rejects_awaitable`
   - `tests/test_list_field.py::test_list_field_signature_with_orderset`
2. `django_strawberry_framework/list_field.py::_synthesized_list_signature return annotation emptiness`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 3 failed, 125 passed in 5.70s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 128 passed in 5.69s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_synthesized_list_signature_without_and_with_orderset`
   - `tests/test_list_field.py::test_list_field_signature_without_orderset`
   - `tests/test_list_field.py::test_list_field_signature_with_orderset`
3. `django_strawberry_framework/list_field.py::_normalize_list_arguments offset boolean rejection`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 5 failed, 123 passed in 5.54s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 128 passed in 5.78s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_1_offset_boolean_rejected[True]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_1_offset_boolean_rejected[False]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_9_precedence_offset_before_limit[True--1-non_integer]`
   - `tests/test_list_field.py::test_list_field_direct_call_type_and_bound_rejections`
4. `django_strawberry_framework/list_field.py::_normalize_list_arguments offset before limit precedence`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 24 failed, 104 passed in 5.56s ========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 128 passed in 5.64s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_async_iterable_early_cleanup_on_offset_rejection`
   - `tests/test_list_field.py::test_offset_guard_explicit_order`
   - `tests/test_list_field.py::test_resolve_argument_wire_name_zero_calls_on_valid_normalization`
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_1_offset_boolean_rejected[True]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_1_offset_boolean_rejected[False]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_2_offset_non_integer_rejected[ten-str 'ten']`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_2_offset_non_integer_rejected[3.14-float 3.14]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_3_offset_negative_rejected[-1]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_3_offset_negative_rejected[-10]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_4_offset_over_ceiling_rejected[101]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_4_offset_over_ceiling_rejected[500]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_9_precedence_offset_before_limit[-1--2-negative]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_9_precedence_offset_before_limit[True--1-non_integer]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_9_precedence_offset_before_limit[bad-101-non_integer]`
   - `tests/test_list_field.py::test_pipeline_execution_order`
   - `tests/test_list_field.py::test_non_queryset_rejection_offset_list`
   - `tests/test_list_field.py::test_non_queryset_rejection_offset_none`
   - `tests/test_list_field.py::test_offset_guard_model_default_cleared_schema_execution`
   - `tests/test_list_field.py::test_list_field_direct_call_type_and_bound_rejections`
   - `tests/test_list_field.py::test_list_field_direct_call_offset_before_limit_precedence`
   - `tests/test_list_field.py::test_list_field_direct_call_safe_non_integer_rendering`
   - `tests/test_list_field.py::test_list_field_trusted_return_cap_asymmetry`
   - `tests/test_list_field.py::test_list_field_record_independence`
5. `django_strawberry_framework/list_field.py::_normalize_list_arguments safe non-integer rendering`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 2 failed, 126 passed in 5.61s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 128 passed in 5.62s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_2_offset_non_integer_rejected[ten-str 'ten']`
6. `django_strawberry_framework/list_field.py::_normalize_list_arguments offset negative rejection`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 8 failed, 120 passed in 5.58s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 128 passed in 5.61s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_resolve_argument_wire_name_zero_calls_on_valid_normalization`
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_3_offset_negative_rejected[-1]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_3_offset_negative_rejected[-10]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_9_precedence_offset_before_limit[-1--2-negative]`
   - `tests/test_list_field.py::test_list_field_direct_call_type_and_bound_rejections`
   - `tests/test_list_field.py::test_list_field_direct_call_offset_before_limit_precedence`
   - `tests/test_list_field.py::test_list_field_direct_call_schema_name_fallback_and_definition_lookup`
7. `django_strawberry_framework/list_field.py::_normalize_list_arguments limit negative rejection`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 4 failed, 124 passed in 5.57s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 128 passed in 5.69s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_7_limit_negative_rejected[-1]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_7_limit_negative_rejected[-10]`
   - `tests/test_list_field.py::test_list_field_direct_call_type_and_bound_rejections`
8. `django_strawberry_framework/list_field.py::_normalize_list_arguments offset ceiling rejection`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 5 failed, 123 passed in 5.59s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 128 passed in 5.70s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_4_offset_over_ceiling_rejected[101]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_4_offset_over_ceiling_rejected[500]`
   - `tests/test_list_field.py::test_list_field_direct_call_type_and_bound_rejections`
   - `tests/test_list_field.py::test_list_field_trusted_return_cap_asymmetry`
9. `django_strawberry_framework/list_field.py::_normalize_list_arguments limit ceiling rejection`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 5 failed, 123 passed in 5.60s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 128 passed in 5.58s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_8_limit_over_ceiling_rejected[50-False-51-50]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_8_limit_over_ceiling_rejected[200-True-201-200]`
   - `tests/test_list_field.py::test_list_field_direct_call_type_and_bound_rejections`
   - `tests/test_list_field.py::test_list_field_trusted_return_cap_asymmetry`
10. `django_strawberry_framework/list_field.py::_normalize_list_arguments trusted cap asymmetry`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 76 failed, 52 passed in 5.60s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 128 passed in 5.65s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_djangolistfield_sync_path_rejects_coroutine_from_get_queryset`
   - `tests/test_list_field.py::test_djangolistfield_consumer_resolver_queryset_return_gets_get_queryset_applied`
   - `tests/test_list_field.py::test_djangolistfield_consumer_resolver_python_list_return_passes_through`
   - `tests/test_list_field.py::test_djangolistfield_sync_async_generator_resolver_raises_sync_misuse`
   - `tests/test_list_field.py::test_djangolistfield_at_root_position_is_optimized`
   - `tests/test_list_field.py::test_djangolistfield_fk_id_elision_survives`
   - `tests/test_list_field.py::test_djangolistfield_with_meta_primary_true_returns_primary_queryset`
   - `tests/test_list_field.py::test_djangolistfield_with_secondary_target_uses_secondary_get_queryset`
   - `tests/test_list_field.py::test_list_field_default_resolver_applies_cascade`
   - `tests/test_list_field.py::test_djangolistfield_hostile_hook_subclass_serves_only_visible_rows_sync`
   - `tests/test_list_field.py::test_djangolistfield_instance_shadowed_all_hook_is_sealed`
   - `tests/test_list_field.py::test_djangolistfield_resolver_manager_degrading_to_list_fails_closed_sync`
   - `tests/test_list_field.py::test_djangolistfield_resolver_manager_alias_drift_fails_closed_sync`
   - `tests/test_list_field.py::test_djangolistfield_max_rows_narrows_the_request_policy`
   - `tests/test_list_field.py::test_djangolistfield_consumer_resolver_returning_none_sync`
   - `tests/test_list_field.py::test_djangolistfield_consumer_resolver_returning_none_async`
   - `tests/test_list_field.py::test_async_iterable_early_cleanup`
   - `tests/test_list_field.py::test_async_iterable_early_cleanup_on_offset_rejection`
   - `tests/test_list_field.py::test_apply_orderset_async_schema_execution_rejects_non_awaitable`
   - `tests/test_list_field.py::test_apply_orderset_async_schema_execution_rejects_residual_awaitable`
   - `tests/test_list_field.py::test_offset_guard_explicit_order`
   - `tests/test_list_field.py::test_list_field_no_argument_sql_parity`
   - `tests/test_list_field.py::test_djangolistfield_async_get_queryset_is_awaited`
   - `tests/test_list_field.py::test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution`
   - `tests/test_list_field.py::test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied`
   - `tests/test_list_field.py::test_djangolistfield_async_consumer_resolver_manager_return_gets_get_queryset_applied`
   - `tests/test_list_field.py::test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied`
   - `tests/test_list_field.py::test_djangolistfield_async_staticmethod_resolver_gets_get_queryset_applied`
   - `tests/test_list_field.py::test_djangolistfield_partial_wrapped_async_resolver_gets_get_queryset_applied`
   - `tests/test_list_field.py::test_djangolistfield_partial_wrapped_async_callable_object_resolver_gets_get_queryset_applied`
   - `tests/test_list_field.py::test_djangolistfield_async_consumer_resolver_python_list_return_passes_through`
   - `tests/test_list_field.py::test_djangolistfield_async_consumer_resolver_async_iterable_is_bounded`
   - `tests/test_list_field.py::test_djangolistfield_async_generator_resolver_is_bounded`
   - `tests/test_list_field.py::test_djangolistfield_sync_resolver_returning_async_iterable_is_bounded`
   - `tests/test_list_field.py::test_djangolistfield_partial_async_generator_resolver_is_bounded`
   - `tests/test_list_field.py::test_djangolistfield_async_consumer_resolver_async_iterable_can_exhaust_before_bound`
   - `tests/test_list_field.py::test_djangolistfield_sync_resolver_returning_coroutine_rejects_loudly`
   - `tests/test_list_field.py::test_djangolistfield_sync_resolver_returning_custom_awaitable_rejects_loudly`
   - `tests/test_list_field.py::test_djangolistfield_sync_resolver_returning_future_cancels_it`
   - `tests/test_list_field.py::test_djangolistfield_hostile_hook_subclass_serves_only_visible_rows_async`
   - `tests/test_list_field.py::test_djangolistfield_resolver_manager_degrading_to_list_fails_closed_async`
   - `tests/test_list_field.py::test_djangolistfield_sync_path_rejects_custom_awaitable_from_get_queryset`
   - `tests/test_list_field.py::test_resolve_argument_wire_name_zero_calls_on_valid_normalization`
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_1_offset_boolean_rejected[True]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_1_offset_boolean_rejected[False]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_2_offset_non_integer_rejected[ten-str 'ten']`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_2_offset_non_integer_rejected[3.14-float 3.14]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_3_offset_negative_rejected[-1]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_3_offset_negative_rejected[-10]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_4_offset_over_ceiling_rejected[101]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_4_offset_over_ceiling_rejected[500]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_5_limit_boolean_rejected[True]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_5_limit_boolean_rejected[False]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_6_limit_non_integer_rejected[twenty-str 'twenty']`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_6_limit_non_integer_rejected[3.14-float 3.14]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_7_limit_negative_rejected[-1]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_7_limit_negative_rejected[-10]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_8_limit_over_ceiling_rejected[50-False-51-50]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_8_limit_over_ceiling_rejected[200-True-201-200]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_9_precedence_offset_before_limit[-1--2-negative]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_9_precedence_offset_before_limit[True--1-non_integer]`
   - `tests/test_list_field.py::test_normalize_list_arguments_boundary_9_precedence_offset_before_limit[bad-101-non_integer]`
   - `tests/test_list_field.py::test_pipeline_execution_order`
   - `tests/test_list_field.py::test_non_queryset_rejection_orderby_list`
   - `tests/test_list_field.py::test_non_queryset_rejection_orderby_none`
   - `tests/test_list_field.py::test_non_queryset_rejection_offset_list`
   - `tests/test_list_field.py::test_non_queryset_rejection_offset_none`
   - `tests/test_list_field.py::test_apply_orderset_sync_schema_execution_rejects_awaitable`
   - `tests/test_list_field.py::test_offset_guard_model_default_cleared_schema_execution`
   - `tests/test_list_field.py::test_list_field_direct_call_type_and_bound_rejections`
   - `tests/test_list_field.py::test_list_field_direct_call_offset_before_limit_precedence`
   - `tests/test_list_field.py::test_list_field_direct_call_safe_non_integer_rendering`
   - `tests/test_list_field.py::test_list_field_trusted_return_cap_asymmetry`
   - `tests/test_list_field.py::test_list_field_direct_call_schema_name_fallback_and_definition_lookup`
   - `tests/test_list_field.py::test_list_field_record_independence`
11. `django_strawberry_framework/list_field.py::ListArgumentError.__reduce__ pickle roundtrip`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 2 failed, 126 passed in 5.66s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 128 passed in 5.62s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_list_argument_error_pickle_roundtrip`
   - `tests/test_list_field.py::test_list_field_error_pickle_round_trip`
12. `django_strawberry_framework/list_field.py::_resolve_argument_wire_name converter dispatch`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 3 failed, 125 passed in 5.61s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 128 passed in 5.68s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_resolve_argument_wire_name_fallback_and_custom`
   - `tests/test_list_field.py::test_resolve_argument_wire_name_zero_calls_on_valid_normalization`
   - `tests/test_list_field.py::test_list_field_direct_call_schema_name_fallback_and_definition_lookup`
13. `django_strawberry_framework/list_field.py::_normalize_list_arguments any_argument_supplied calculation`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 7 failed, 121 passed in 5.60s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 128 passed in 5.64s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_async_iterable_early_cleanup`
   - `tests/test_list_field.py::test_apply_orderset_async_schema_execution_rejects_non_awaitable`
   - `tests/test_list_field.py::test_apply_orderset_async_schema_execution_rejects_residual_awaitable`
   - `tests/test_list_field.py::test_normalize_list_arguments_all_boundaries`
   - `tests/test_list_field.py::test_non_queryset_rejection_orderby_list`
   - `tests/test_list_field.py::test_non_queryset_rejection_orderby_none`
   - `tests/test_list_field.py::test_apply_orderset_sync_schema_execution_rejects_awaitable`
14. `django_strawberry_framework/utils/querysets.py::_seal_or_defect evaluated queryset rejection`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 5 failed, 426 passed in 5.92s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 431 passed in 5.87s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/utils/test_querysets.py::test_seal_require_unevaluated`
   - `tests/utils/test_querysets.py::test_visibility_defect_messages`
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_evaluated`
   - `tests/test_list_field.py::test_pipeline_execution_order`
   - `tests/test_list_field.py::test_list_field_post_orderset_validator_arms`
15. `django_strawberry_framework/utils/querysets.py::_seal_or_defect sliced queryset rejection`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 5 failed, 426 passed in 5.96s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 431 passed in 5.88s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/utils/test_querysets.py::test_seal_policy_presets_answer_slice_and_combinator_independently`
   - `tests/utils/test_querysets.py::test_sliced_source_fails_closed_with_typed_error`
   - `tests/utils/test_querysets.py::test_sliced_hook_result_fails_closed_with_typed_error`
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_sliced`
   - `tests/test_list_field.py::test_list_field_post_orderset_validator_arms`
16. `django_strawberry_framework/utils/querysets.py::_seal_or_defect combined queryset rejection`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 6 failed, 425 passed in 5.94s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 431 passed in 5.93s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/utils/test_querysets.py::test_seal_policy_presets_answer_slice_and_combinator_independently`
   - `tests/utils/test_querysets.py::test_visibility_defect_messages`
   - `tests/utils/test_querysets.py::test_apply_type_visibility_sync_combined_result_error`
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_combined`
   - `tests/test_list_field.py::test_pipeline_execution_order`
   - `tests/test_list_field.py::test_list_field_post_orderset_validator_arms`
17. `django_strawberry_framework/utils/querysets.py::_validate_post_orderset_result routing mismatch`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 4 failed, 427 passed in 5.90s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 431 passed in 5.89s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_db_routing_mismatch`
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_hints_routing_mismatch`
   - `tests/test_list_field.py::test_list_field_post_orderset_validator_arms`
   - `tests/test_list_field.py::test_list_field_seal_axis_subclass_and_routing_intent`
18. `django_strawberry_framework/resource_policy.py::_close_async_iterator cleanup notes attachment`
   - file mutated: `django_strawberry_framework/resource_policy.py`
   - pytest summary: `======================== 3 failed, 287 passed in 5.80s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 290 passed in 5.93s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_resource_policy.py::test_bounded_rows_async_preserves_source_errors_when_cleanup_fails`
   - `tests/test_resource_policy.py::test_bounded_rows_async_exact_consumption_and_cleanup_matrix`
   - `tests/test_list_field.py::test_list_field_rejected_async_iterator_cleanup_and_notes`
19. `django_strawberry_framework/utils/querysets.py::_AsyncQuerySetRows synchronous iteration rejection`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 12 failed, 116 passed in 5.59s ========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 128 passed in 5.75s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_async_completion_adapter_semantics`
   - `tests/test_list_field.py::test_djangolistfield_async_get_queryset_is_awaited`
   - `tests/test_list_field.py::test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution`
   - `tests/test_list_field.py::test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied`
   - `tests/test_list_field.py::test_djangolistfield_async_consumer_resolver_manager_return_gets_get_queryset_applied`
   - `tests/test_list_field.py::test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied`
   - `tests/test_list_field.py::test_djangolistfield_async_staticmethod_resolver_gets_get_queryset_applied`
   - `tests/test_list_field.py::test_djangolistfield_partial_wrapped_async_resolver_gets_get_queryset_applied`
   - `tests/test_list_field.py::test_djangolistfield_partial_wrapped_async_callable_object_resolver_gets_get_queryset_applied`
   - `tests/test_list_field.py::test_djangolistfield_hostile_hook_subclass_serves_only_visible_rows_async`
   - `tests/test_list_field.py::test_async_completion_adapter_sync_iter_raises_type_error`
   - `tests/test_list_field.py::test_list_field_async_queryset_adapter_protocol`
20. `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize adapter rewrap`
   - file mutated: `django_strawberry_framework/optimizer/extension.py`
   - pytest summary: `======================== 4 failed, 303 passed in 8.43s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 307 passed in 8.44s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_list_field_optimizer_adapter_unwrap_rewrap_and_early_returns`
   - `tests/optimizer/test_extension.py::test_optimizer_preserves_async_adapter_evaluated_cache`
   - `tests/optimizer/test_extension.py::test_optimizer_preserves_async_adapter_unresolved_type`
   - `tests/optimizer/test_extension.py::test_optimizer_preserves_async_adapter_optimized_tail`
21. `django_strawberry_framework/resource_policy.py::bounded_rows check_deadline call`
   - file mutated: `django_strawberry_framework/resource_policy.py`
   - pytest summary: `======================== 2 failed, 288 passed in 5.88s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 290 passed in 5.82s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_resource_policy.py::test_bounded_rows_shared_policy_seams_spy`
   - `tests/test_list_field.py::test_list_field_deadline_check_position`
22. `django_strawberry_framework/list_field.py::_is_model_default_ordering_active default ordering check`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 2 failed, 126 passed in 5.71s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 128 passed in 5.74s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_offset_guard_model_default_cleared_by_order_by`
   - `tests/test_list_field.py::test_offset_guard_model_default_cleared_schema_execution`
23. `django_strawberry_framework/resource_policy.py::bounded_rows declined sync cleanup`
   - file mutated: `django_strawberry_framework/resource_policy.py`
   - pytest summary: `======================== 3 failed, 287 passed in 7.23s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 290 passed in 6.41s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_resource_policy.py::test_bounded_rows_declined_sync_cleanup_resumable`
   - `tests/test_resource_policy.py::test_bounded_rows_unsliceable_iterable_exact_consumption`
   - `tests/test_list_field.py::test_list_field_declined_sync_cleanup_generator_suspended`
24. `django_strawberry_framework/orders/sets.py::OrderSet._input_has_active_terms purity check`
   - file mutated: `django_strawberry_framework/orders/sets.py`
   - pytest summary: `========================= 5 failed, 78 passed in 3.89s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================== 83 passed in 3.97s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/orders/test_sets.py::test_input_has_active_terms_purity`
   - `tests/orders/test_sets.py::test_input_has_active_terms_purity_structure_disagreement`
   - `tests/orders/test_sets.py::test_input_has_active_terms_purity_violation[first_return0-second_return0]`
   - `tests/orders/test_sets.py::test_input_has_active_terms_purity_violation[first_return1-second_return1]`
   - `tests/orders/test_sets.py::test_input_has_active_terms_purity_violation[first_return2-second_return2]`
25. `django_strawberry_framework/list_field.py::_is_random_order_term random term classification`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 3 failed, 125 passed in 7.55s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 128 passed in 7.32s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_offset_guard_random_term_question_mark`
   - `tests/test_list_field.py::test_offset_guard_random_term_random_function`
   - `tests/test_list_field.py::test_is_model_default_ordering_active_edge_states`

A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is `revision-needed` per `docs/builder/BUILD.md` - the fix is more or better-targeted rows, never a weaker boundary. A boundary at 3 rows or fewer is inside Worker 3's mandatory independent re-run floor. A proof carrying collection or setup errors, or whose pytest run exited anything but 0 or 1 (nothing collected, interrupted, internal error, usage error), is not a valid count at all - and a 0 from such a run is not a zero-row result: resolve it and re-run.

Every `<fill in ...>` above is a judgement no tool can make and MUST be replaced by hand before this subsection is submitted: weakly pinned and harness-impossible are the two possible readings of a zero-row result and they prescribe opposite responses (more rows, versus a production-call-site invariant assertion plus a recorded harness limitation), so a record that does not name one reads as self-contradictory.

### Hot-path budget

- **Post-apply seal wall-clock benchmark (`test_list_field_post_apply_seal_benchmark`):**
  - Iterations: 1,000 iterations over complex annotated queryset with prefetch and ordering.
  - Measured: 22.07 µs per iteration (target <= 100 µs; test assertion threshold < 50,000 µs).
- **Wire-name conversion:**
  - Tested: exactly 0 `NameConverter` calls on successful argument requests (`test_resolve_argument_wire_name_zero_calls_on_valid_normalization`).

### Floor verification

Owned by the final gate per the plan's declaration.

### Implementation notes

- Removed all 18 occurrences of `monkeypatch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "true")` across `tests/test_list_field.py`; verified that the entire test suite passes without any async-unsafe escape hatch.
- Verified orphan registration ledger via `_helper_referenced_ordersets` on the type definition.
- Generator expressions in tests converted to `yield from` per ruff `UP028`.
- In `_close_async_iterator` cleanup notes test, verified diagnostic message formatting on Python 3.10-3.14 via direct `__notes__` inspection.

### Notes for Worker 3

- All 25 boundaries in `docs/builder/temp-tests/slice-3/proofs.json` were verified using `scripts/prove_failability.py` with exit code 0 and zero collection or setup errors.
- Every single boundary failed >= 2 rows (no weakly pinned boundaries).
- 9 boundaries are inside Worker 3's mandatory independent re-run floor (<= 3 rows):
  - Boundary 2: `_synthesized_list_signature return annotation emptiness` (3 rows)
  - Boundary 5: `_normalize_list_arguments safe non-integer rendering` (2 rows)
  - Boundary 11: `ListArgumentError.__reduce__ pickle roundtrip` (2 rows)
  - Boundary 12: `_resolve_argument_wire_name converter dispatch` (3 rows)
  - Boundary 18: `_close_async_iterator cleanup notes attachment` (3 rows)
  - Boundary 21: `bounded_rows check_deadline call` (2 rows)
  - Boundary 22: `_is_model_default_ordering_active default ordering check` (2 rows)
  - Boundary 23: `bounded_rows declined sync cleanup` (3 rows)
  - Boundary 25: `_is_random_order_term random term classification` (3 rows)

### Notes for Worker 1 (spec reconciliation)

- None. The implementation and tests fully conform to the plan and the spec.

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- Unit test suites across `tests/base/test_init.py`, `tests/orders/test_sets.py`, `tests/test_resource_policy.py`, and `tests/test_list_field.py` were reviewed for duplication, test doubles, and assertion hygiene.
- `tests/base/test_init.py`: Subprocess execution cleanly verifies lazy package root import without `django_strawberry_framework.orders` in `sys.modules`, avoiding in-process cache pollution.
- `tests/orders/test_sets.py`: Reuses `OrderArgumentsFactory` and `OrderSet` primitives with a parameterized matrix and a sentinel map in `test_input_has_active_terms_contract` to test 12 different input shapes without redundant boilerplate.
- `tests/test_resource_policy.py`: Reuses `SimpleNamespace` context fixtures and `stash_resource_policy` helpers. Test doubles (`TrackedAsyncIterable`, `CountedUnsliceable`) are concise, isolated, and exercised against comprehensive consumption and cleanup matrices.
- `tests/test_list_field.py`: Directly verifies normalizer and pipeline units against existing `Item` and `Category` test models. Adheres strictly to `AGENTS.md` rules (`services.seed_data(3)` in `test_list_field_no_argument_sql_parity`).
- Verified removal of all 18 boilerplate occurrences of `monkeypatch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "true")` from `tests/test_list_field.py`, establishing genuine async execution via `_AsyncQuerySetRows`. The single legacy occurrence at `tests/test_relay_connection.py:2058` is documented with its existing prefetch rationale.

### Public-surface check

Verified `git diff -- django_strawberry_framework/__init__.py`. `ListArgumentError` was introduced and authorized in Slice 1 per spec-050 Decision 1 (spec lines 268-274). No new public exports were introduced in Slice 3.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- Elimination of all 18 `DJANGO_ALLOW_ASYNC_UNSAFE` overrides from `tests/test_list_field.py`, confirming adapter protocol safety under async execution.
- Comprehensive unit contract coverage discharging all `# TODO(spec-050 slice 3)` anchors across `tests/test_list_field.py`, `tests/test_resource_policy.py`, `tests/orders/test_sets.py`, and `tests/base/test_init.py`.
- 25 failability proof boundaries recorded in `docs/builder/temp-tests/slice-3/proofs.json`, all having >= 2 failing rows upon mutation (0 weakly-pinned boundaries).
- Independent failability re-run of the mandatory floor subset (all 9 boundaries with <= 3 failing rows plus Boundary 17 security/routing boundary) executed via `scripts/prove_failability.py` with 100% agreement, 0 errors, and byte-verified clean restorations.
- Hot-path budget compliance: post-apply seal benchmark measured 22.07 µs (well within <= 100 µs target); exactly 0 `NameConverter` calls on successful argument normalization.
- Static review inspection via `scripts/review_inspect.py` completed cleanly with no structural or abstraction defects.

### Temp test verification

- Manifest file `docs/builder/temp-tests/slice-3/proofs.json`: Kept as durable proof manifest for Slice 3 failability proofs.

### Notes for Worker 1 (spec reconciliation)

- All Slice 3 requirements (SQL parity, unit contracts, failability proofs, and async safety cleanup) are fully satisfied. The codebase is clean and ready for Slice 4 (live acceptance tests in `examples/fakeshop/test_query/`).

### Review outcome

`review-accepted`.

---

## Final verification (Worker 1)

### Summary

Slice 3 shipped the dedicated unit and SQL contract pinning suite for `DjangoListField`
argument normalization, order set integration, and window execution:
- Pinned synthesized resolver signatures with and without `Meta.orderset_class`, preserving outer
  nullability via `inspect.Signature.empty` return annotation.
- Pinned lazy import isolation: importing `django_strawberry_framework` alone does not import
  `django_strawberry_framework.orders` into `sys.modules`.
- Pinned `ListArgumentError.__reduce__` pickle serialization round trip (constructor args, GraphQL
  extensions, and instance `__dict__` state).
- Pinned direct-call parameter type validation (rejecting `bool`, `float`, `str` with safe string
  rendering), bounds, and deterministic `offset`-before-`limit` error precedence.
- Pinned error-lazy wire name resolution (`_resolve_argument_wire_name` makes 0 calls to
  `NameConverter.from_argument` on valid requests, exactly 1 on error).
- Pinned record independence of `_ListArguments` (`any_argument_supplied`, `offset: 0`,
  `order_by_supplied`, material activity).
- Pinned awaitable disposal on rejection paths (`SyncMisuseError`, `ConfigurationError`).
- Pinned post-OrderSet candidate validator arms (`_seal_or_defect` and
  `_validate_post_orderset_result`) asserting actionable error messages for evaluated and combined
  querysets, plus database routing intent identity (`_db` and `_hints`).
- Pinned rejected async iterator early cleanup (`aclose()` called with zero advances) and error
  notes attachment (`__notes__` on `primary_error`).
- Pinned `_AsyncQuerySetRows` adapter protocol (`__aiter__` present, `__iter__` absent) and
  `DjangoOptimizerExtension._optimize` unwrap/rewrap identity across all exit paths.
- Pinned single `check_deadline` invocation before row fetching.
- Pinned `_is_model_default_ordering_active` edge states (group_by, extra_order_by, random terms,
  unreadable query state, reverse ordering, empty queryset, to-many duplicates).
- Pinned SQL query parity (`str(qs.query)`), low/high mark window mutations, and recorded
  post-apply seal diagnostic benchmark (22.07 µs/iter).
- Pinned `bounded_rows` and `bounded_rows_async` window parameter matrices, async positive offset
  arithmetic, unsliceable iterable exact consumption, and declined sync cleanup contract
  (truncated sync generator stays suspended and resumable).
- Pinned `OrderSet._input_has_active_terms` input matrix, independent query/double-normalization
  tracing, public apply override independence, and purity checks.
- Safely eliminated all 18 occurrences of `monkeypatch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "true")`
  from `tests/test_list_field.py`.

### Checklist audit

Every planned item in `### Spec slice checklist (verbatim)` was verified against the diff:
- [x] [`tests/test_list_field.py`][test-list-field] pins signature shape, cap arithmetic,
      direct-call runtime errors, helper mechanics, model-ordering state, and no-argument SQL
      parity; wire-reachable sync and async wrapper behavior stays in the live tier. (Verified
      across 24 new unit contract tests in [`tests/test_list_field.py`][test-list-field], covering
      signature inspection, cap bounds, direct resolver invocations, `ListArgumentError` pickle
      roundtrip, awaitable disposal, post-orderset validator arms, model default ordering edge
      states, and low/high mark parity).
- [x] Remove adapter-relevant `DJANGO_ALLOW_ASYNC_UNSAFE` setup from existing package tests so it
      cannot mask a regression in safe async queryset completion; retain an override only where a
      separately named legacy behavior genuinely still requires it. (Verified: all 18 occurrences
      removed from [`tests/test_list_field.py`][test-list-field]; the single legacy occurrence in
      `tests/test_relay_connection.py:2058` retained with documented prefetch rationale).
- [x] Order input construction continues to use the shipped `OrderSet` factory and orphan ledger
      rather than a list-field-specific input class. (Verified: `order_input_type(orderset_class)`
      used directly and verified with orphan ledger checks in
      `tests/test_list_field.py::test_list_field_signature_with_orderset`).

### Test run

Focused test suite command:
`uv run pytest tests/base/test_init.py tests/test_list_field.py tests/orders/test_sets.py tests/test_resource_policy.py --no-cov`

Result: **PASS** (`384 passed in 6.47s`, exit code 0).
Ran without `--cov*` flags per [`BUILD.md`][build-md] guidelines; zero test failures or regressions.

### Failability and fail-open confirmation

- **Failability proofs:** All 25 boundaries enumerated in the plan carry complete failability proof
  records in `docs/builder/temp-tests/slice-3/proofs.json`. Every boundary failed >= 2 distinct test
  rows upon mutation (range 2 to 76 rows; zero weakly pinned boundaries; zero collection or setup
  errors). Pre-mutation copies were restored and verified by bit-level comparison
  (`filecmp.cmp(shallow=False) True`) and SHA-256 match. Worker 3 independently re-ran the floor
  subset (all 9 boundaries with <= 3 failing rows plus Boundary 17) and verified 100% agreement.
- **Fail-open audit:** Confirmed no fail-open shapes landed in the diff. Slice 3 is strictly a
  test-tier and verification slice; no production code was modified. The tests pin existing
  production guards against fail-open regressions:
  - Identity checks explicitly test against `None` and `strawberry.UNSET`.
  - Type guards verify `isinstance(..., bool)` before `isinstance(..., int)`.
  - Post-OrderSet validation seals against `_ORDERSET_RESULT_POLICY` and checks routing intent
    (`_db` and `_hints`).
  - `_AsyncQuerySetRows` implements only `__aiter__` (no `__iter__`), failing closed with
    `TypeError` on synchronous iteration attempts.
  - Exception handling in `_close_async_iterator` preserves primary exceptions while attaching
    cleanup failure diagnostics to `__notes__`.

### Spec changes made (Worker 1 only)

None.

### Notes for the build plan

Slice 3 is final-accepted. The next slice is Slice 4 (`Live acceptance`), which implements live
`/graphql` queries over HTTP via `django.test.Client` in
`examples/fakeshop/test_query/test_list_field_api.py`, `test_list_field_async_api.py`,
`test_resource_policy_api.py`, `test_library_api.py`, and `test_multi_db.py`, discharging all
remaining `# TODO(spec-050 slice 4)` anchors.

---

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-050]: ../spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-md]: BUILD.md
[worker-1]: worker-1.md
[worker-2]: worker-2.md
[worker-3]: worker-3.md

<!-- django_strawberry_framework/ -->
[list-field]: ../../django_strawberry_framework/list_field.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py

<!-- tests/ -->
[test-list-field]: ../../tests/test_list_field.py
[test-orders-sets]: ../../tests/orders/test_sets.py
[test-resource-policy]: ../../tests/test_resource_policy.py
[test-init]: ../../tests/base/test_init.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
