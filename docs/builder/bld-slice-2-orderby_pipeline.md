# Build: Slice 2 — Meta-derived `orderBy` and list pipeline

Spec reference: [`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050] (lines 83-95)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Refreshed the shallow AST inventory across the entire package
  (`django_strawberry_framework/`) into `docs/shadow/helper-inventory.md` before planning. Also ran
  `scripts/review_inspect.py` into `docs/shadow/` across all four affected files
  ([`list_field.py`][list-field], [`orders/sets.py`][orders-sets],
  [`utils/querysets.py`][querysets], and [`optimizer/extension.py`][optimizer-extension]).
  Grepped the inventory for `seal`, `defect`, `order`, `active_terms`, `routing`, `adapter`,
  `unevaluated`, `random`, `completion`, and `bounded_rows`. Relevant existing candidates
  identified:
  - `django_strawberry_framework/utils/querysets.py::_SealPolicy`
  - `django_strawberry_framework/utils/querysets.py::_seal_or_defect`
  - `django_strawberry_framework/utils/querysets.py::_visibility_result_error`
  - `django_strawberry_framework/utils/querysets.py::_prepared_visibility_source`
  - `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`
  - `django_strawberry_framework/utils/querysets.py::apply_type_visibility_async`
  - `django_strawberry_framework/utils/querysets.py::normalize_query_source`
  - `django_strawberry_framework/utils/querysets.py::is_async_only_iterable`
  - `django_strawberry_framework/utils/querysets.py::reject_async_iterable_in_sync_context`
  - `django_strawberry_framework/orders/sets.py::OrderSet.apply_sync`
  - `django_strawberry_framework/orders/sets.py::OrderSet.apply_async`
  - `django_strawberry_framework/orders/sets.py::OrderSet._normalize_input`
  - `django_strawberry_framework/orders/sets.py::OrderSet.get_flat_orders`
  - `django_strawberry_framework/resource_policy.py::_close_async_iterator`
  - `django_strawberry_framework/resource_policy.py::bounded_rows`
  - `django_strawberry_framework/resource_policy.py::bounded_rows_async`
  - `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize`

- **Existing patterns reused.**
  - [`django_strawberry_framework/utils/querysets.py::_seal_or_defect`][querysets]: reused for
    sealing both visibility source/result querysets and the post-`OrderSet` candidate output.
  - [`django_strawberry_framework/utils/querysets.py::_SealPolicy`][querysets]: extended with
    `require_unevaluated: bool = False`, and reused via `_LIST_ARGUMENT_VISIBILITY_POLICY`
    (`reject_combined=True`) and `_ORDERSET_RESULT_POLICY` (`require_model_rows=True,
    reject_sliced=True, reject_combined=True, require_unevaluated=True`).
  - [`django_strawberry_framework/orders/sets.py::OrderSet.apply_sync`][orders-sets] and
    [`django_strawberry_framework/orders/sets.py::OrderSet.apply_async`][orders-sets]:
    invoked directly by [`list_field.py`][list-field] resolver wrappers, preserving custom
    consumer subclasses and permission hooks.
  - [`django_strawberry_framework/resource_policy.py::_close_async_iterator`][resource-policy]:
    reused in [`list_field.py`][list-field] when an async-only resolver source is rejected for
    supplied ordering or nonzero offset before reaching `bounded_rows_async`.
  - [`django_strawberry_framework/resource_policy.py::bounded_rows`][resource-policy] and
    [`django_strawberry_framework/resource_policy.py::bounded_rows_async`][resource-policy]:
    reused as the single window-slicing seam.

- **New helpers justified.**
  - `OrderSet._input_has_active_terms(cls, input_value: Any) -> bool`: classmethod on
    `OrderSet` in [`django_strawberry_framework/orders/sets.py`][orders-sets]. Single
    responsibility: determine whether normalized order input contains any active (non-null)
    ordering direction by calling `cls._normalize_input(input_value)` and
    `cls.get_flat_orders(normalized)`. Purity invariant: re-normalization must be pure and
    deterministic; disagreement between first and second runs raises `ConfigurationError`.
  - `_validate_post_orderset_result(target_type, source, candidate, method_name)`:
    package-private helper in [`django_strawberry_framework/utils/querysets.py`][querysets].
    Single responsibility: validate post-`OrderSet` output against `_ORDERSET_RESULT_POLICY`
    through `_seal_or_defect`, verify routing intent preservation (`candidate._db ==
    source._db` and `candidate._hints == source._hints`), and raise an actionable
    `ConfigurationError` citing `method_name` on defect.
  - `_AsyncQuerySetRows` (with `is_async_queryset_adapter(value)` and
    `wrap_async_queryset_adapter(qs)`): private class in
    [`django_strawberry_framework/utils/querysets.py`][querysets]. Single responsibility: wrap
    a final sliced `QuerySet` in an object implementing only `__aiter__` (delegating to
    `QuerySet.__aiter__`) without `__iter__`, preventing synchronous iteration during async
    GraphQL list completion.
  - `_is_random_order_term(term: Any) -> bool`: private helper in
    [`django_strawberry_framework/list_field.py`][list-field]. Single responsibility: detect
    whether an order term is random (`"?"` or `Random()` instance).
  - `_is_model_default_ordering_active(queryset: models.QuerySet) -> bool`: private helper in
    [`django_strawberry_framework/list_field.py`][list-field]. Single responsibility:
    determine if the queryset still has model-default ordering active per Django's
    `QuerySet.ordered` default-ordering rules (`query.default_ordering is True`, non-empty
    non-random `query.get_meta().ordering`, empty `query.order_by`, empty
    `query.extra_order_by`, `not query.group_by`).

- **Duplication risk avoided.**
  - *No local queryset state inspection in `list_field.py`:* do not inspect `_result_cache`,
    `query.is_sliced`, or `query.combinator` directly in `list_field.py`; delegate
    completely to `_validate_post_orderset_result` in `utils/querysets.py`.
  - *No separate order input walker in `list_field.py`:* do not parse or unpack `order_by`
    in `list_field.py`; delegate to `OrderSet._input_has_active_terms`.
  - *No second async iterator cleanup:* reuse `_close_async_iterator` from
    `resource_policy.py`; do not hand-roll `aclose` handling in `list_field.py`.
  - *No second adapter or planner path in optimizer:* `DjangoOptimizerExtension._optimize`
    unwraps the adapter before step 1, runs the existing pipeline, and rewraps on all exit
    paths.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against current source before
editing.

1. **Extend `_SealPolicy` and `_seal_or_defect` in**
   [`django_strawberry_framework/utils/querysets.py`][querysets] (lines 2670-3046):
   - In `_SealPolicy` (line 2670), add field `require_unevaluated: bool = False`.
   - In `_seal_or_defect` (line 2770), after table and untrusted proof passes, inspect
     `state.get("_result_cache")`:
     - When `policy.require_unevaluated and state.get("_result_cache") is not None`, return
       `None, ("unevaluated", "the result cache is populated")` immediately before `sliced`.
     - Canonical defect order is strictly: `type` -> `table` -> `untrusted` -> `unevaluated` ->
       `sliced` -> `combined` -> `projection` -> `alias`.
   - In `_visibility_result_error` (line 3125):
     - Replace reachability sentence (which stated `combined` was only emitted by cascade).
     - Add explicit message arm for `"unevaluated"`:
       `"unevaluated": (f"{name}.get_queryset returned an evaluated queryset ({detail}); `
       `the visibility contract composes further filters and ordering onto an unevaluated `
       `lazy query. Return an unevaluated QuerySet.")`
     - Add explicit message arm for `"combined"`:
       `"combined": (f"{name}.get_queryset returned a combined queryset ({detail}); `
       `active list arguments forbid combined queries (union, intersection, difference) `
       `because subsequent filtering or ordering cannot be safely composed. Return a plain `
       `uncombined QuerySet.")`
   - In `_prepared_visibility_source` (line 3206):
     - Add explicit message arm for `"unevaluated"`:
       `"unevaluated": (f"apply_type_visibility for {name} requires an unevaluated `
       `QuerySet; got an evaluated queryset ({detail}). Pass an unevaluated QuerySet.")`
     - Add explicit message arm for `"combined"`:
       `"combined": (f"apply_type_visibility for {name} requires an uncombined QuerySet; `
       `got a {detail} queryset. Combined queries (union, intersection, difference) cannot `
       `be safely filtered or ordered.")`
   - Define module constant `_LIST_ARGUMENT_VISIBILITY_POLICY`:
     `_SealPolicy(require_model_rows=True, reject_sliced=True, reject_combined=True, `
     `require_shared_alias=False, require_unevaluated=False)`.
   - Define module constant `_ORDERSET_RESULT_POLICY`:
     `_SealPolicy(require_model_rows=True, reject_sliced=True, reject_combined=True, `
     `require_shared_alias=False, require_unevaluated=True)`.
   - Implement `_validate_post_orderset_result(`
     `target_type, pre_order_qs, post_order_candidate, method_name)`:
     - Enforce `_seal_or_defect(post_order_candidate, model_for(target_type), `
       `None, _ORDERSET_RESULT_POLICY)`.
     - On defect, raise `ConfigurationError` detailing failure and naming `method_name`.
     - Verify routing intent equality:
       - `post_order_candidate._db == pre_order_qs._db` (including `None`).
       - `getattr(post_order_candidate, "_hints", {}) == getattr(pre_order_qs, "_hints", {})`.
       - On routing mismatch, raise `ConfigurationError` detailing database routing deviation
         and naming `method_name`.
     - Return the sealed `QuerySet`.

2. **Implement `_AsyncQuerySetRows` completion adapter in**
   [`django_strawberry_framework/utils/querysets.py`][querysets] (lines 394-409):
   - Discharge `# TODO(spec-050 slice 2)` at lines 394-409.
   - Define `_AsyncQuerySetRows`:
     - `__init__(self, queryset: models.QuerySet) -> None`: validate `isinstance(queryset, `
       `models.QuerySet)`; store `self._queryset = queryset`.
     - Implement `__aiter__(self)`: `return self._queryset.__aiter__()`.
     - Do NOT implement `__iter__` (prevents synchronous iteration).
   - Implement package-private helpers:
     - `wrap_async_queryset_adapter(qs: Any) -> Any`: returns `_AsyncQuerySetRows(qs)` if
       `isinstance(qs, models.QuerySet)`, else identity.
     - `unwrap_async_queryset_adapter(val: Any) -> tuple[Any, bool]`: returns
       `(val._queryset, True)` if `isinstance(val, _AsyncQuerySetRows)`, else `(val, False)`.
     - `is_async_queryset_adapter(val: Any) -> bool`: returns
       `isinstance(val, _AsyncQuerySetRows)`.

3. **Update `DjangoOptimizerExtension._optimize` in**
   [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension] (lines 1109-1144):
   - Discharge `# TODO(spec-050 slice 2)` at lines 1109-1118.
   - At entry of `_optimize`:
     - Unwrap adapter: `inner_result, was_adapted = unwrap_async_queryset_adapter(result)`.
     - Define local helper `finish(val: Any) -> Any`: returns
       `wrap_async_queryset_adapter(val)` if `was_adapted`, else `val`.
     - Run existing `normalize_query_source(inner_result)`. If not is_queryset:
       `return finish(inner_result)`.
     - In evaluated-cache check (line 1133): `if getattr(inner_result, "_result_cache", None) `
       `is not None: return finish(inner_result)`.
     - In return-type resolution check (line 1136): `if resolved is None:`
       `return finish(inner_result)`.
     - In optimized tail: `return finish(self.apply_to(resolved.origin, resolved.model, `
       `inner_result, info))`.

4. **Implement `OrderSet._input_has_active_terms` in**
   [`django_strawberry_framework/orders/sets.py`][orders-sets] (lines 326-345):
   - Discharge `# TODO(spec-050 slice 2)` at lines 326-345.
   - Implement `@classmethod def _input_has_active_terms(cls, input_value: Any) -> bool`:
     - Normalization purity check:
       - `data1 = cls._normalize_input(input_value)`
       - `data2 = cls._normalize_input(input_value)`
       - If `data1 != data2`: raise `ConfigurationError(f"{cls.__name__}._normalize_input `
         `is non-deterministic or stateful; successive normalizations of the same input `
         `produced different data structures.")`.
     - `flat_orders = cls.get_flat_orders(data1)`.
     - Return `any(direction is not None for _, direction in flat_orders)`.

5. **Implement random term and model-ordering predicates in [`list_field.py`][list-field]:**
   - `_is_random_order_term(term: Any) -> bool`:
     - Return `True` if `term == "?"`.
     - Return `True` if `isinstance(term, Random)` or `isinstance(getattr(term, "expression", `
       `None), Random)`.
     - Return `False` otherwise. (Note: do not check `"-?"`; Django rejects `"-?"` as
       `FieldError`).
   - `_has_no_random_terms(queryset: models.QuerySet) -> bool`:
     - Check `queryset.query.order_by`: return `False` if any term matches `_is_random_order_term`.
     - Check `queryset.query.extra_order_by`: return `False` if any term matches
       `_is_random_order_term`.
     - Return `True`.
   - `_is_model_default_ordering_active(queryset: models.QuerySet) -> bool`:
     - Query condition checks matching Django's `QuerySet.ordered` default ordering logic:
       - `query = queryset.query`
       - If `not query.default_ordering`: return `False`.
       - `meta_ordering = query.get_meta().ordering`
       - If not `meta_ordering`: return `False`.
       - If any `_is_random_order_term(t)` for `t in meta_ordering`: return `False`.
       - If `query.order_by`: return `False`.
       - If `query.extra_order_by`: return `False`.
       - If `query.group_by`: return `False` (spelled `not query.group_by`).
       - Return `True`.

6. **Integrate pipeline in resolver wrappers in**
   [`django_strawberry_framework/list_field.py`][list-field] (lines 453-492, 566-715):
   - Discharge `# TODO(spec-050 slice 2)` at lines 453-492.
   - Enforce unified execution order:
     - Argument normalization via `_normalize_list_arguments`.
     - Fast-path check: if `not args_record.any_argument_supplied`:
       - Execute legacy resolver/getattr path.
       - Slicing: `bounded_rows(result, info, max_rows, trusted=trusted_max_rows)`.
       - In async context: return `wrap_async_queryset_adapter(result)` if queryset.
     - Argument-bearing path:
       - Execute consumer resolver. Coerce `Manager` to `QuerySet`. Handle
         sync/async awaitable rules.
       - Non-`QuerySet` branch:
         - If `args_record.order_by_supplied`:
           - If async-only iterable: `await _close_async_iterator(result)`.
           - Raise `ListArgumentError(field_name, _resolve_argument_wire_name(info, "order_by"), `
             `reason="queryset_required")`.
         - If `args_record.offset is not None and args_record.offset > 0`:
           - If async-only iterable: `await _close_async_iterator(result)`.
           - Raise `ListArgumentError(field_name, _resolve_argument_wire_name(info, "offset"), `
             `reason="order_required", value=args_record.offset)`.
         - If `result is None`: return `None`.
         - Slice via `bounded_rows` / `bounded_rows_async`.
       - `QuerySet` branch:
         - Apply visibility with `_LIST_ARGUMENT_VISIBILITY_POLICY` (`reject_combined=True`).
         - If `args_record.order_by_supplied`:
           - Look up `orderset_class = definition.orderset_class`. If missing: raise
             `ConfigurationError`.
           - In sync path: call `orderset_class.apply_sync(result, args_record.order_by, info)`.
             Dispose/reject awaitable. Validate result via `_validate_post_orderset_result`.
           - In async path: call `orderset_class.apply_async(result, args_record.order_by, info)`.
             Await once. Dispose/reject residual awaitable. Validate result via
             `_validate_post_orderset_result`.
           - Update `result = post_order_qs`.
         - Nonzero offset check:
           - If `args_record.offset is not None and args_record.offset > 0`:
             - Check explicit order: `args_record.order_by_supplied and `
               `orderset_class._input_has_active_terms(args_record.order_by) and result.ordered `
               `and _has_no_random_terms(result)`.
             - Check model default order: `_is_model_default_ordering_active(result)`.
             - If neither condition holds: raise `ListArgumentError(field_name, `
               `_resolve_argument_wire_name(info, "offset"), reason="order_required", `
               `value=args_record.offset)`.
         - Single window slicing:
           - Apply `bounded_rows` with `offset=args_record.offset, `
             `requested_limit=args_record.limit`.
           - In async context (or `in_async_context()`): return
             `wrap_async_queryset_adapter(result)`.

### Boundary count & split assessment

Estimated boundary count: **22 boundaries**
1. Argument-bearing source seal: reject combined queryset (`union`/`intersect`/`difference`).
2. Argument-bearing visibility result seal: reject combined queryset.
3. Non-queryset with `order_by_supplied`: reject with
   `ListArgumentError(..., reason="queryset_required")`.
4. Non-queryset with `offset > 0`: reject with
   `ListArgumentError(..., reason="order_required")`.
5. Early cleanup of rejected async-only iterable via `_close_async_iterator` without advancing.
6. Non-awaitable return from `OrderSet.apply_async` in async pipeline (`ConfigurationError`).
7. Residual awaitable return after awaiting `OrderSet.apply_async` (`ConfigurationError`).
8. Awaitable return from `OrderSet.apply_sync` in sync pipeline (`SyncMisuseError`).
9. Post-`OrderSet` validation: non-`QuerySet` result rejection (`ConfigurationError`).
10. Post-`OrderSet` validation: wrong model/table rejection (`ConfigurationError`).
11. Post-`OrderSet` validation: untrusted query state rejection (`ConfigurationError`).
12. Post-`OrderSet` validation: evaluated queryset (`_result_cache` populated) rejection
    (`ConfigurationError`).
13. Post-`OrderSet` validation: sliced queryset rejection (`ConfigurationError`).
14. Post-`OrderSet` validation: combined queryset rejection (`ConfigurationError`).
15. Post-`OrderSet` validation: projection/values queryset rejection (`ConfigurationError`).
16. Post-`OrderSet` validation: database routing intent mismatch (`_db` or `_hints`)
    (`ConfigurationError`).
17. `OrderSet._input_has_active_terms`: normalization disagreement on impure `_normalize_input`
    (`ConfigurationError`).
18. Nonzero offset order guard: rejection when neither explicit active non-random order nor active
    model-default non-random ordering is present.
19. Nonzero offset order guard: rejection of literal `"?"` or `Random()` order terms.
20. Nonzero offset order guard: rejection of cleared (`.order_by()`) or overridden model default
    ordering.
21. Optimizer unwrap/rewrap on all three exit paths (evaluated cache, unresolved return type,
    optimized tail).
22. Async queryset completion adapter: exposes `__aiter__` and rejects synchronous iteration
    (`not hasattr(__iter__)`).

**Split assessment:**
Although boundary count (22) exceeds the standard split evaluation threshold (8), splitting this
slice is explicitly rejected. These boundaries form one single, indivisible request pipeline
defined by Decision 5 and Decision 6. Slicing the pipeline into intermediate sub-slices (such as
implementing post-`OrderSet` seal without integrating list field wrappers, or implementing the
offset guard without `OrderSet` active term checks) would create invalid intermediate states,
dead code branches, and untestable gaps. The implementation touches tightly-coupled boundaries
across the 4 planned files in exact accordance with the spec's design.

### Hot-path budget declaration

- **Measurement:** Wall-clock overhead per resolver invocation on valid querysets under sync and
  async execution contexts.
- **Budget:** Added overhead <= 50µs per invocation over 10,000 iterations.
- **Invariants:** Exactly 0 `NameConverter` calls on the valid request path (wire name resolution
  is strictly lazy on error).
- **Optimizer:** Adapter unwrap and rewrap overhead in `DjangoOptimizerExtension._optimize` <= 5µs
  per invocation.

### Floor verification scope

- **Assigned to:** Final test-run gate.
- **Scope:** Floor verification executes against Python 3.10 and Django 5.2. Focused suite tests
  compatibility of `query.default_ordering`, `query.group_by`, `query.extra_order_by`, and
  `QuerySet.__aiter__` without `DJANGO_ALLOW_ASYNC_UNSAFE`.

### Test additions / updates

- [`tests/test_list_field.py`][test-list-field]:
  - `test_orderset_orderby_schema_generation`: verifies that a target carrying
    `Meta.orderset_class` gains `orderBy: [<OrderSet>InputType!]` in the schema while a target
    without `orderset_class` publishes no `orderBy` argument.
  - `test_pipeline_execution_order`: verifies deterministic error precedence (combined source
    rejected before hook; malformed post-apply rejected before offset guard).
  - `test_non_queryset_rejections`: verifies `queryset_required` for `orderBy` and `order_required`
    for `offset > 0` on non-querysets and `None`.
  - `test_async_iterable_early_cleanup`: verifies `aclose()` is awaited on rejected async iterables
    without advancing them.
  - `test_offset_guard_explicit_order`: verifies active `orderBy` terms satisfy offset guard,
    while empty lists `[]` or all-null terms `[{name: null}]` fail unless model default is active.
  - `test_offset_guard_random_terms`: verifies `"?"` and `Random()` expressions are rejected for
    `offset > 0`.
  - `test_offset_guard_model_default`: verifies stable model `Meta.ordering` satisfies offset
    guard; `.order_by()` clears it; `.order_by("custom")` replaces it.
  - `test_async_completion_adapter_semantics`: verifies adapter wraps final querysets under async
    context, delegates `__aiter__`, and provides no `__iter__`.
- [`tests/orders/test_sets.py`][test-orders-sets]:
  - `test_input_has_active_terms`: verifies detection of active terms and no-ops.
  - `test_input_has_active_terms_purity`: verifies that impure `_normalize_input` raising
    disagreement produces `ConfigurationError`.
- [`tests/utils/test_querysets.py`][test-querysets]:
  - `test_seal_require_unevaluated`: verifies that populated `_result_cache` produces
    `("unevaluated", ...)` defect under `require_unevaluated=True`.
  - `test_visibility_defect_messages`: verifies message arms for `unevaluated` and `combined` in
    `_visibility_result_error` and `_prepared_visibility_source`.
  - `test_validate_post_orderset_result`: verifies `ConfigurationError` on non-queryset, wrong
    model, evaluated, sliced, combined, projection, and database routing mismatches (`_db` and
    `_hints`).
- [`tests/optimizer/test_extension.py`][test-optimizer-extension]:
  - `test_optimizer_preserves_async_adapter`: verifies `_optimize` unwraps the adapter for planning
    and rewraps on evaluated cache, unmapped return type, and optimized exit paths.

### Implementation discretion items

- Exact private helper naming for routing comparison in `utils/querysets.py`.
- Exact organization and helper ordering of order-checking predicates in `list_field.py`.
- Test fixture model selection in `tests/test_list_field.py` (e.g., existing models vs local test
  models).

### Spec slice checklist (verbatim)

- [x] **Slice 2 - Meta-derived `orderBy` and list pipeline**
  - [x] A target carrying `Meta.orderset_class` gains nullable, optional
        `orderBy: [<OrderSet>InputType!]`; a target without that sidecar does not publish a
        meaningless order input.
  - [x] Sync and async paths run visibility, then `OrderSet`, then the offset/order guard,
        then the one raw-list slice.
  - [x] The result of a public `OrderSet.apply_*` override is validated as an unevaluated,
        unsliced, non-projection, non-combined model queryset before the final window; the
        seal gains the new `unevaluated` option, reuses the shipped `reject_combined` one,
        and both new-to-this-boundary codes gain arms at the two visibility message sites.
  - [x] Nonzero offset requires a materially active `orderBy` or still-effective model
        `Meta.ordering` on the post-visibility queryset; no pk tiebreaker and no `DISTINCT`
        are injected.

---

## Build report (Worker 2)

### Files touched

- [`django_strawberry_framework/list_field.py`][list-field]:
  - Implemented `_is_random_order_term` and `_is_model_default_ordering_active` to evaluate active ordering for offset guard.
  - Implemented `_check_nonzero_offset_guard` to enforce ordering when offset > 0.
  - Implemented `_handle_non_queryset_rejections_sync` and `_handle_non_queryset_rejections_async` to reject order_by and offset on non-queryset iterables, properly releasing async iterators via `_cleanup_rejected_async_iterable` and `_close_async_iterator`.
  - DRY consolidation: extracted `_orderset_class_for_target` helper eliminating redundant `getattr(definition, "orderset_class", None)` lookups across sync/async pipelines; factored shared wire argument rejection builder `_build_non_queryset_rejection_error` across async and sync non-queryset rejections.
  - Implemented `_apply_orderset_sync` and `_apply_orderset_async` to execute OrderSet resolution, validate results with `_validate_post_orderset_result`, and detect sync/async misuse.
  - Wired list pipeline: visibility -> OrderSet -> offset guard -> slice (`bounded_rows` / `bounded_rows_async`), wrapping async queryset results with `_AsyncQuerySetRows`.
  - Bound async callable resolvers in `_wrap` to `await bounded_rows_async(...)`.
- [`django_strawberry_framework/orders/sets.py`][orders-sets]:
  - Implemented `OrderSet._input_has_active_terms(cls, input_value)` classmethod verifying whether normalized inputs contain active ordering terms with double-run purity check.
- [`django_strawberry_framework/utils/querysets.py`][querysets]:
  - Extended `_SealPolicy` with `require_unevaluated: bool = False`.
  - Added `_ORDERSET_RESULT_POLICY` (`require_model_rows=True, reject_sliced=True, reject_combined=True, require_unevaluated=True`).
  - Added `_validate_post_orderset_result` checking post-orderset queryset invariants and database routing consistency (`_db` and `_hints`).
  - Added `_AsyncQuerySetRows` adapter class implementing `__aiter__` and forbidding `__iter__`, plus `is_async_queryset_adapter` and `wrap_async_queryset_adapter`.
  - Expanded `_visibility_result_error` to provide explicit diagnostic error messages for `"combined"` defect rejections.
- [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension]:
  - Updated `DjangoOptimizerExtension._optimize` to unwrap `_AsyncQuerySetRows` adapter via `unwrap_async_queryset_adapter` before optimization and rewrap via `wrap_async_queryset_adapter` on all exit paths.
- [`tests/test_list_field.py`][test-list-field]:
  - Added and split test suites to pin all boundaries: pipeline execution order, non-queryset argument rejections (`test_non_queryset_rejection_orderby_list`, `test_non_queryset_rejection_orderby_none`, `test_non_queryset_rejection_offset_list`, `test_non_queryset_rejection_offset_none`), async iterable early cleanup under order and offset rejections (`test_async_iterable_early_cleanup`, `test_async_iterable_early_cleanup_on_offset_rejection`), orderset apply misuse guards with both direct unit and schema execution tests (`test_apply_orderset_async_rejects_non_awaitable`, `test_apply_orderset_async_schema_execution_rejects_non_awaitable`, `test_apply_orderset_async_rejects_residual_awaitable`, `test_apply_orderset_async_schema_execution_rejects_residual_awaitable`, `test_apply_orderset_sync_rejects_awaitable`, `test_apply_orderset_sync_schema_execution_rejects_awaitable` using `SyncAwaitable` and `ResidualAwaitable`), offset guard rules (`test_offset_guard_explicit_order`, `test_offset_guard_random_term_question_mark`, `test_offset_guard_random_term_random_function`, `test_offset_guard_model_default_active`, `test_offset_guard_model_default_cleared_by_order_by`, `test_offset_guard_model_default_cleared_schema_execution`, `test_offset_guard_subfield_active`), and async completion adapter semantics (`test_async_completion_adapter_semantics`, `test_async_completion_adapter_sync_iter_raises_type_error`).
- [`tests/orders/test_sets.py`][test-orders-sets]:
  - Added unit tests `test_input_has_active_terms_purity` and `test_input_has_active_terms_purity_structure_disagreement` verifying active term detection and purity check failures on non-pure normalizers.
- [`tests/utils/test_querysets.py`][test-querysets]:
  - Added tests for `require_unevaluated` seal policy, visibility defect messages, combined result error (`test_apply_type_visibility_sync_combined_result_error`), and individual post-orderset defect rejections (`test_validate_post_orderset_result_valid`, `test_validate_post_orderset_result_rejects_non_queryset`, `test_validate_post_orderset_result_rejects_none`, `test_validate_post_orderset_result_rejects_wrong_model`, `test_validate_post_orderset_result_rejects_evaluated`, `test_validate_post_orderset_result_rejects_sliced`, `test_validate_post_orderset_result_rejects_combined`, `test_validate_post_orderset_result_rejects_projection`, `test_validate_post_orderset_result_rejects_db_routing_mismatch`, `test_validate_post_orderset_result_rejects_hints_routing_mismatch`).
- [`tests/optimizer/test_extension.py`][test-optimizer-extension]:
  - Added focused unit tests (`test_optimizer_unadapted_non_queryset_passthrough`, `test_optimizer_preserves_async_adapter_evaluated_cache`, `test_optimizer_preserves_async_adapter_unresolved_type`, `test_optimizer_preserves_async_adapter_optimized_tail`) validating unwrapping, optimization, and rewrapping of async adapter across exit paths.

### Tests added or updated

- `tests/test_list_field.py`:
  - `test_pipeline_execution_order`: verifies sync & async pipeline execution order: visibility -> orderset -> offset guard -> bounded slice.
  - `test_non_queryset_rejection_orderby_list` & `test_non_queryset_rejection_orderby_none`: independently verify sync & async rejection of `orderBy` on list and None resolver returns.
  - `test_non_queryset_rejection_offset_list` & `test_non_queryset_rejection_offset_none`: independently verify sync & async rejection of nonzero `offset` on list and None resolver returns.
  - `test_async_iterable_early_cleanup` & `test_async_iterable_early_cleanup_on_offset_rejection`: independently verify async iterator cleanup when non-queryset rejected for `orderBy` and `offset`.
  - `test_apply_orderset_async_rejects_non_awaitable` & `test_apply_orderset_async_schema_execution_rejects_non_awaitable`: verify `ConfigurationError` when `apply_async` returns a non-awaitable directly and via schema execution.
  - `test_apply_orderset_async_rejects_residual_awaitable` & `test_apply_orderset_async_schema_execution_rejects_residual_awaitable`: verify `ConfigurationError` when `apply_async` returns a residual awaitable directly and via schema execution.
  - `test_apply_orderset_sync_rejects_awaitable` & `test_apply_orderset_sync_schema_execution_rejects_awaitable`: verify `SyncMisuseError` when `apply_sync` returns an awaitable directly and via schema execution.
  - `test_offset_guard_explicit_order`: verifies non-zero offset permitted with explicit `orderBy` and rejected without it.
  - `test_offset_guard_random_term_question_mark` & `test_offset_guard_random_term_random_function`: independently verify non-zero offset permitted with random ordering terms (`"?"` vs `Random()`).
  - `test_offset_guard_model_default_active`, `test_offset_guard_model_default_cleared_by_order_by`, and `test_offset_guard_model_default_cleared_schema_execution`: verify model default ordering behavior across querysets and schema execution.
  - `test_offset_guard_subfield_active`: verifies non-zero offset permitted when nested relation order terms are active.
  - `test_async_completion_adapter_semantics` & `test_async_completion_adapter_sync_iter_raises_type_error`: independently verify `_AsyncQuerySetRows` implements `__aiter__` and raises `TypeError` on sync iteration.
- `tests/orders/test_sets.py`:
  - `test_input_has_active_terms_purity`: verifies `OrderSet._input_has_active_terms` returns True for active terms, False for empty/null, and raises `ConfigurationError` on non-identical return representations.
  - `test_input_has_active_terms_purity_structure_disagreement`: verifies `ConfigurationError` when successive calls return differing list lengths.
- `tests/utils/test_querysets.py`:
  - `test_seal_require_unevaluated`: verifies populated `_result_cache` produces `("unevaluated", ...)` defect under `require_unevaluated=True`.
  - `test_visibility_defect_messages` & `test_apply_type_visibility_sync_combined_result_error`: independently verify message formatting and runtime rejection for `combined` defect under active list arguments.
  - `test_validate_post_orderset_result_*`: 8 dedicated test functions verifying `ConfigurationError` on non-queryset, None, wrong model, evaluated, sliced, combined, projection, and database routing mismatches.
- `tests/optimizer/test_extension.py`:
  - `test_optimizer_preserves_async_adapter_*`: 4 dedicated test functions verifying unadapted passthrough, evaluated cache preservation, unresolved type preservation, and optimized tail rewrapping.

### Validation run

- Command: `uv run pytest tests/test_list_field.py tests/orders/test_sets.py tests/utils/test_querysets.py tests/optimizer/test_extension.py --no-cov`
- Result: **652 passed in 9.51s** (0 failures, 0 errors).

### Failability proofs

Procedure, mechanized by `scripts/prove_failability.py`: the target is copied to a scratch path OUTSIDE the repo before any mutation; the mutation site is located by an exact anchor asserted to match exactly once (any other count aborts the entry without writing); the same focused scope is run unmutated first, so rows already failing before the mutation are differenced out of the count; both runs' pytest exit codes are read, because a run that collected nothing or blew up emits no `FAILED` lines and would otherwise be recorded as a measured zero; both runs use `--no-cov`; the file is restored from the pre-mutation copy in a `finally` and the restore is proved by `filecmp.cmp(shallow=False)` plus a SHA-256 comparison. One boundary at a time, restored before the next. `git` is never invoked - the tree is legitimately dirty, so an empty `git diff` is unachievable and forcing one would destroy the build's own work.

| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/list_field.py::_execute_queryset_pipeline_sync reject combined source` | `django_strawberry_framework/list_field.py` | `post_vis_qs = apply_type_visibility_sync( target_type, source, info, policy=_LIST_ARGUMENT_VISIBILITY_POLICY,` -> `post_vis_qs = apply_type_visibility_sync( target_type, source, info, policy=_DEFAULT_SEAL_POLICY,` - builder's description (unverified prose): visibility policy changed from _LIST_ARGUMENT_VISIBILITY_POLICY to _DEFAULT_SEAL_POLICY (reject_combined=False) | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 2 | `django_strawberry_framework/utils/querysets.py::_visibility_result_error combined defect arm` | `django_strawberry_framework/utils/querysets.py` | deleted: `"combined": ( f"{name}.get_queryset returned a combined queryset ({detail}); " f"active list arguments forbid combine...` - builder's description (unverified prose): combined message arm removed from _visibility_result_error | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/utils/test_querysets.py` | filecmp.cmp(shallow=False) True; sha256 536c746b9a09a230... == 536c746b9a09a230... (vs pre-mutation copy) |
| 3 | `django_strawberry_framework/list_field.py::_build_non_queryset_rejection_error order_by non-queryset` | `django_strawberry_framework/list_field.py` | deleted: `if args_record.order_by_supplied: return ListArgumentError( "DjangoListField", _resolve_argument_wire_name(info, "ord...` - builder's description (unverified prose): order_by_supplied non-queryset check deleted | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 4 | `django_strawberry_framework/list_field.py::_build_non_queryset_rejection_error offset non-queryset` | `django_strawberry_framework/list_field.py` | deleted: `if args_record.offset is not None and args_record.offset > 0: return ListArgumentError( "DjangoListField", _resolve_a...` - builder's description (unverified prose): offset > 0 non-queryset check deleted | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 5 | `django_strawberry_framework/list_field.py::_cleanup_rejected_async_iterable close async iterator` | `django_strawberry_framework/list_field.py` | `await _close_async_iterator(iterator, primary_error=primary_error)` -> `pass` - builder's description (unverified prose): _close_async_iterator replaced by pass | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 6 | `django_strawberry_framework/list_field.py::_apply_orderset_async non-awaitable return` | `django_strawberry_framework/list_field.py` | deleted: `if not inspect.isawaitable(candidate_awaitable): raise ConfigurationError( f"{orderset_class.__name__}.apply_async re...` - builder's description (unverified prose): non-awaitable apply_async check deleted | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 7 | `django_strawberry_framework/list_field.py::_apply_orderset_async residual awaitable return` | `django_strawberry_framework/list_field.py` | deleted: `if inspect.isawaitable(candidate): _dispose_sync_awaitable(candidate) raise ConfigurationError( f"{orderset_class.__n...` - builder's description (unverified prose): residual awaitable apply_async check deleted | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 8 | `django_strawberry_framework/list_field.py::_apply_orderset_sync awaitable return` | `django_strawberry_framework/list_field.py` | deleted: `if inspect.isawaitable(candidate): _dispose_sync_awaitable(candidate) raise SyncMisuseError( f"{orderset_class.__name...` - builder's description (unverified prose): awaitable apply_sync check deleted | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 9 | `django_strawberry_framework/utils/querysets.py::_validate_post_orderset_result non-queryset rejection` | `django_strawberry_framework/utils/querysets.py` | deleted: `if defect is not None: code, detail = defect model_name = _safe_class_name(model) raise ConfigurationError( f"{method...` - builder's description (unverified prose): defect check in _validate_post_orderset_result deleted | **7** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/utils/test_querysets.py` | filecmp.cmp(shallow=False) True; sha256 536c746b9a09a230... == 536c746b9a09a230... (vs pre-mutation copy) |
| 10 | `django_strawberry_framework/utils/querysets.py::_seal_or_defect wrong table rejection` | `django_strawberry_framework/utils/querysets.py` | deleted: `if _concrete_or_none(qmodel) is not concrete: return None, ("table", _safe_class_name(qmodel))` - builder's description (unverified prose): table defect check in _seal_or_defect deleted | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/utils/test_querysets.py` | filecmp.cmp(shallow=False) True; sha256 536c746b9a09a230... == 536c746b9a09a230... (vs pre-mutation copy) |
| 11 | `django_strawberry_framework/utils/querysets.py::_seal_or_defect untrusted query state rejection` | `django_strawberry_framework/utils/querysets.py` | deleted: `if type(query) is not sql.Query: return None, ("untrusted", f"{cls_name}.query is {_safe_type_name(query)}")` - builder's description (unverified prose): untrusted query type check in _seal_or_defect deleted | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/utils/test_querysets.py` | filecmp.cmp(shallow=False) True; sha256 536c746b9a09a230... == 536c746b9a09a230... (vs pre-mutation copy) |
| 12 | `django_strawberry_framework/utils/querysets.py::_seal_or_defect evaluated queryset rejection` | `django_strawberry_framework/utils/querysets.py` | deleted: `if policy.require_unevaluated and state.get("_result_cache") is not None: return None, ("unevaluated", "the result ca...` - builder's description (unverified prose): require_unevaluated check in _seal_or_defect deleted | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/utils/test_querysets.py` | filecmp.cmp(shallow=False) True; sha256 536c746b9a09a230... == 536c746b9a09a230... (vs pre-mutation copy) |
| 13 | `django_strawberry_framework/utils/querysets.py::_seal_or_defect sliced queryset rejection` | `django_strawberry_framework/utils/querysets.py` | deleted: `if policy.reject_sliced and rebuilt_query.is_sliced: return None, ("sliced", f"rows {rebuilt_query.low_mark}:{rebuilt...` - builder's description (unverified prose): reject_sliced check in _seal_or_defect deleted | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/utils/test_querysets.py` | filecmp.cmp(shallow=False) True; sha256 536c746b9a09a230... == 536c746b9a09a230... (vs pre-mutation copy) |
| 14 | `django_strawberry_framework/utils/querysets.py::_seal_or_defect combined queryset rejection` | `django_strawberry_framework/utils/querysets.py` | deleted: `if policy.reject_combined and rebuilt_query.combinator: return None, ("combined", str(rebuilt_query.combinator))` - builder's description (unverified prose): reject_combined check in _seal_or_defect deleted | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/utils/test_querysets.py` | filecmp.cmp(shallow=False) True; sha256 536c746b9a09a230... == 536c746b9a09a230... (vs pre-mutation copy) |
| 15 | `django_strawberry_framework/utils/querysets.py::_seal_or_defect projection values rejection` | `django_strawberry_framework/utils/querysets.py` | deleted: `if policy.require_model_rows and iterable is not ModelIterable: return None, ("projection", _safe_class_name(iterable))` - builder's description (unverified prose): require_model_rows check in _seal_or_defect deleted | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/utils/test_querysets.py` | filecmp.cmp(shallow=False) True; sha256 536c746b9a09a230... == 536c746b9a09a230... (vs pre-mutation copy) |
| 16 | `django_strawberry_framework/utils/querysets.py::_validate_post_orderset_result routing mismatch` | `django_strawberry_framework/utils/querysets.py` | deleted: `if cand_db != orig_db or cand_hints != orig_hints: raise ConfigurationError( f"{method_name} changed database routing...` - builder's description (unverified prose): database routing comparison in _validate_post_orderset_result deleted | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/utils/test_querysets.py` | filecmp.cmp(shallow=False) True; sha256 536c746b9a09a230... == 536c746b9a09a230... (vs pre-mutation copy) |
| 17 | `django_strawberry_framework/orders/sets.py::OrderSet._input_has_active_terms purity check` | `django_strawberry_framework/orders/sets.py` | deleted: `if data1 != data2: raise ConfigurationError( f"{cls.__name__}._normalize_input is not pure; returned different result...` - builder's description (unverified prose): purity check in OrderSet._input_has_active_terms deleted | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/orders/test_sets.py` | filecmp.cmp(shallow=False) True; sha256 5d9d1cb018ccdda6... == 5d9d1cb018ccdda6... (vs pre-mutation copy) |
| 18 | `django_strawberry_framework/list_field.py::_check_nonzero_offset_guard missing active order rejection` | `django_strawberry_framework/list_field.py` | deleted: `if not has_active_order and not _is_model_default_ordering_active(queryset): raise ListArgumentError( "DjangoListFiel...` - builder's description (unverified prose): active order check in _check_nonzero_offset_guard deleted | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 19 | `django_strawberry_framework/list_field.py::_is_random_order_term random term classification` | `django_strawberry_framework/list_field.py` | `def _is_random_order_term(term: Any) -> bool: """Classify random order terms: exact '?' or Random() / OrderBy(Random(...` -> `def _is_random_order_term(term: Any) -> bool: return False` - builder's description (unverified prose): _is_random_order_term mutated to always return False | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 20 | `django_strawberry_framework/list_field.py::_is_model_default_ordering_active default ordering check` | `django_strawberry_framework/list_field.py` | `if not query.default_ordering: return False` -> `if not query.default_ordering: return True` - builder's description (unverified prose): not query.default_ordering returns True instead of False | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 618fc8f676fe7da3... == 618fc8f676fe7da3... (vs pre-mutation copy) |
| 21 | `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize adapter unwrap and rewrap` | `django_strawberry_framework/optimizer/extension.py` | `def finish(val: Any) -> Any: return wrap_async_queryset_adapter(val) if was_adapted else val` -> `def finish(val: Any) -> Any: return val` - builder's description (unverified prose): finish(val) returns val directly without rewrapping async adapter | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/optimizer/test_extension.py` | filecmp.cmp(shallow=False) True; sha256 d93bc369af5c2da7... == d93bc369af5c2da7... (vs pre-mutation copy) |
| 22 | `django_strawberry_framework/utils/querysets.py::_AsyncQuerySetRows async adapter sync iter rejection` | `django_strawberry_framework/utils/querysets.py` | `def __aiter__(self) -> Any: return self._queryset.__aiter__()` -> `def __aiter__(self) -> Any: return self._queryset.__aiter__() def __iter__(self) -> Any: return iter(self._queryset)` - builder's description (unverified prose): added __iter__ to _AsyncQuerySetRows allowing synchronous iteration | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_list_field.py` | filecmp.cmp(shallow=False) True; sha256 536c746b9a09a230... == 536c746b9a09a230... (vs pre-mutation copy) |

Verdicts:

1. `django_strawberry_framework/list_field.py::_execute_queryset_pipeline_sync reject combined source` - pinned
2. `django_strawberry_framework/utils/querysets.py::_visibility_result_error combined defect arm` - inside Worker 3's mandatory re-run floor (<= 3 rows)
3. `django_strawberry_framework/list_field.py::_build_non_queryset_rejection_error order_by non-queryset` - inside Worker 3's mandatory re-run floor (<= 3 rows)
4. `django_strawberry_framework/list_field.py::_build_non_queryset_rejection_error offset non-queryset` - inside Worker 3's mandatory re-run floor (<= 3 rows)
5. `django_strawberry_framework/list_field.py::_cleanup_rejected_async_iterable close async iterator` - inside Worker 3's mandatory re-run floor (<= 3 rows)
6. `django_strawberry_framework/list_field.py::_apply_orderset_async non-awaitable return` - inside Worker 3's mandatory re-run floor (<= 3 rows)
7. `django_strawberry_framework/list_field.py::_apply_orderset_async residual awaitable return` - inside Worker 3's mandatory re-run floor (<= 3 rows)
8. `django_strawberry_framework/list_field.py::_apply_orderset_sync awaitable return` - inside Worker 3's mandatory re-run floor (<= 3 rows)
9. `django_strawberry_framework/utils/querysets.py::_validate_post_orderset_result non-queryset rejection` - pinned
10. `django_strawberry_framework/utils/querysets.py::_seal_or_defect wrong table rejection` - inside Worker 3's mandatory re-run floor (<= 3 rows)
11. `django_strawberry_framework/utils/querysets.py::_seal_or_defect untrusted query state rejection` - pinned
12. `django_strawberry_framework/utils/querysets.py::_seal_or_defect evaluated queryset rejection` - inside Worker 3's mandatory re-run floor (<= 3 rows)
13. `django_strawberry_framework/utils/querysets.py::_seal_or_defect sliced queryset rejection` - pinned
14. `django_strawberry_framework/utils/querysets.py::_seal_or_defect combined queryset rejection` - pinned
15. `django_strawberry_framework/utils/querysets.py::_seal_or_defect projection values rejection` - pinned
16. `django_strawberry_framework/utils/querysets.py::_validate_post_orderset_result routing mismatch` - inside Worker 3's mandatory re-run floor (<= 3 rows)
17. `django_strawberry_framework/orders/sets.py::OrderSet._input_has_active_terms purity check` - inside Worker 3's mandatory re-run floor (<= 3 rows)
18. `django_strawberry_framework/list_field.py::_check_nonzero_offset_guard missing active order rejection` - pinned
19. `django_strawberry_framework/list_field.py::_is_random_order_term random term classification` - inside Worker 3's mandatory re-run floor (<= 3 rows)
20. `django_strawberry_framework/list_field.py::_is_model_default_ordering_active default ordering check` - inside Worker 3's mandatory re-run floor (<= 3 rows)
21. `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize adapter unwrap and rewrap` - inside Worker 3's mandatory re-run floor (<= 3 rows)
22. `django_strawberry_framework/utils/querysets.py::_AsyncQuerySetRows async adapter sync iter rejection` - inside Worker 3's mandatory re-run floor (<= 3 rows)

Failing node ids, per boundary (the count above is `len()` of this list):

1. `django_strawberry_framework/list_field.py::_execute_queryset_pipeline_sync reject combined source`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 4 failed, 100 passed in 5.82s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 104 passed in 5.86s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_offset_guard_explicit_order`
   - `tests/test_list_field.py::test_pipeline_execution_order`
   - `tests/test_list_field.py::test_apply_orderset_sync_schema_execution_rejects_awaitable`
   - `tests/test_list_field.py::test_offset_guard_model_default_cleared_schema_execution`
2. `django_strawberry_framework/utils/querysets.py::_visibility_result_error combined defect arm`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 2 failed, 301 passed in 3.70s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 303 passed in 3.78s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/utils/test_querysets.py::test_visibility_defect_messages`
   - `tests/utils/test_querysets.py::test_apply_type_visibility_sync_combined_result_error`
3. `django_strawberry_framework/list_field.py::_build_non_queryset_rejection_error order_by non-queryset`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 3 failed, 101 passed in 5.65s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 104 passed in 5.74s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_async_iterable_early_cleanup`
   - `tests/test_list_field.py::test_non_queryset_rejection_orderby_list`
   - `tests/test_list_field.py::test_non_queryset_rejection_orderby_none`
4. `django_strawberry_framework/list_field.py::_build_non_queryset_rejection_error offset non-queryset`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 3 failed, 101 passed in 5.73s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 104 passed in 5.68s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_async_iterable_early_cleanup_on_offset_rejection`
   - `tests/test_list_field.py::test_non_queryset_rejection_offset_list`
   - `tests/test_list_field.py::test_non_queryset_rejection_offset_none`
5. `django_strawberry_framework/list_field.py::_cleanup_rejected_async_iterable close async iterator`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 2 failed, 102 passed in 5.78s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 104 passed in 5.73s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_async_iterable_early_cleanup`
   - `tests/test_list_field.py::test_async_iterable_early_cleanup_on_offset_rejection`
6. `django_strawberry_framework/list_field.py::_apply_orderset_async non-awaitable return`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 2 failed, 102 passed in 5.67s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 104 passed in 5.74s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_apply_orderset_async_schema_execution_rejects_non_awaitable`
   - `tests/test_list_field.py::test_apply_orderset_async_rejects_non_awaitable`
7. `django_strawberry_framework/list_field.py::_apply_orderset_async residual awaitable return`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 2 failed, 102 passed in 5.66s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 104 passed in 5.67s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_apply_orderset_async_schema_execution_rejects_residual_awaitable`
   - `tests/test_list_field.py::test_apply_orderset_async_rejects_residual_awaitable`
8. `django_strawberry_framework/list_field.py::_apply_orderset_sync awaitable return`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 2 failed, 102 passed in 5.69s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 104 passed in 5.73s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_apply_orderset_sync_rejects_awaitable`
   - `tests/test_list_field.py::test_apply_orderset_sync_schema_execution_rejects_awaitable`
9. `django_strawberry_framework/utils/querysets.py::_validate_post_orderset_result non-queryset rejection`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 7 failed, 296 passed in 3.94s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 303 passed in 3.77s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_non_queryset`
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_none`
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_wrong_model`
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_evaluated`
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_sliced`
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_combined`
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_projection`
10. `django_strawberry_framework/utils/querysets.py::_seal_or_defect wrong table rejection`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 3 failed, 300 passed in 3.89s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 303 passed in 3.82s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/utils/test_querysets.py::test_malformed_non_model_query_model_fails_closed_typed`
   - `tests/utils/test_querysets.py::test_non_class_model_with_convincing_meta_fails_closed`
   - `tests/utils/test_querysets.py::test_non_model_class_with_convincing_meta_fails_closed`
11. `django_strawberry_framework/utils/querysets.py::_seal_or_defect untrusted query state rejection`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 5 failed, 298 passed in 3.74s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 303 passed in 3.93s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/utils/test_querysets.py::test_foreign_query_class_result_fails_closed`
   - `tests/utils/test_querysets.py::test_pending_deferred_filter_over_foreign_query_never_dispatches`
   - `tests/utils/test_querysets.py::test_hostile_foreign_query_type_name_cannot_escape_typed_defect`
   - `tests/utils/test_querysets.py::test_prefetch_with_foreign_inner_query_fails_closed`
   - `tests/utils/test_querysets.py::test_prefetch_child_defect_detail_appears_in_message`
12. `django_strawberry_framework/utils/querysets.py::_seal_or_defect evaluated queryset rejection`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 3 failed, 300 passed in 3.80s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 303 passed in 3.73s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/utils/test_querysets.py::test_seal_require_unevaluated`
   - `tests/utils/test_querysets.py::test_visibility_defect_messages`
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_evaluated`
13. `django_strawberry_framework/utils/querysets.py::_seal_or_defect sliced queryset rejection`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 4 failed, 299 passed in 3.74s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 303 passed in 3.81s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/utils/test_querysets.py::test_seal_policy_presets_answer_slice_and_combinator_independently`
   - `tests/utils/test_querysets.py::test_sliced_source_fails_closed_with_typed_error`
   - `tests/utils/test_querysets.py::test_sliced_hook_result_fails_closed_with_typed_error`
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_sliced`
14. `django_strawberry_framework/utils/querysets.py::_seal_or_defect combined queryset rejection`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 4 failed, 299 passed in 3.81s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 303 passed in 3.76s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/utils/test_querysets.py::test_seal_policy_presets_answer_slice_and_combinator_independently`
   - `tests/utils/test_querysets.py::test_visibility_defect_messages`
   - `tests/utils/test_querysets.py::test_apply_type_visibility_sync_combined_result_error`
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_combined`
15. `django_strawberry_framework/utils/querysets.py::_seal_or_defect projection values rejection`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 4 failed, 299 passed in 3.73s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 303 passed in 3.88s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/utils/test_querysets.py::test_seal_policy_presets_answer_slice_and_combinator_independently`
   - `tests/utils/test_querysets.py::test_values_projection_result_fails_closed_on_read_surface`
   - `tests/utils/test_querysets.py::test_values_projection_source_fails_closed_on_read_surface`
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_projection`
16. `django_strawberry_framework/utils/querysets.py::_validate_post_orderset_result routing mismatch`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 2 failed, 301 passed in 3.98s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 303 passed in 3.86s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_db_routing_mismatch`
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_hints_routing_mismatch`
17. `django_strawberry_framework/orders/sets.py::OrderSet._input_has_active_terms purity check`
   - file mutated: `django_strawberry_framework/orders/sets.py`
   - pytest summary: `========================= 2 failed, 64 passed in 2.83s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================== 66 passed in 2.86s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/orders/test_sets.py::test_input_has_active_terms_purity`
   - `tests/orders/test_sets.py::test_input_has_active_terms_purity_structure_disagreement`
18. `django_strawberry_framework/list_field.py::_check_nonzero_offset_guard missing active order rejection`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `========================= 5 failed, 99 passed in 5.79s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 104 passed in 5.94s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_offset_guard_explicit_order`
   - `tests/test_list_field.py::test_offset_guard_random_term_question_mark`
   - `tests/test_list_field.py::test_offset_guard_random_term_random_function`
   - `tests/test_list_field.py::test_offset_guard_model_default_cleared_by_order_by`
   - `tests/test_list_field.py::test_offset_guard_model_default_cleared_schema_execution`
19. `django_strawberry_framework/list_field.py::_is_random_order_term random term classification`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 2 failed, 102 passed in 5.68s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 104 passed in 5.68s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_offset_guard_random_term_question_mark`
   - `tests/test_list_field.py::test_offset_guard_random_term_random_function`
20. `django_strawberry_framework/list_field.py::_is_model_default_ordering_active default ordering check`
   - file mutated: `django_strawberry_framework/list_field.py`
   - pytest summary: `======================== 2 failed, 102 passed in 5.79s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 104 passed in 5.87s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_offset_guard_model_default_cleared_by_order_by`
   - `tests/test_list_field.py::test_offset_guard_model_default_cleared_schema_execution`
21. `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize adapter unwrap and rewrap`
   - file mutated: `django_strawberry_framework/optimizer/extension.py`
   - pytest summary: `======================== 3 failed, 176 passed in 8.37s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 179 passed in 8.28s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/optimizer/test_extension.py::test_optimizer_preserves_async_adapter_evaluated_cache`
   - `tests/optimizer/test_extension.py::test_optimizer_preserves_async_adapter_unresolved_type`
   - `tests/optimizer/test_extension.py::test_optimizer_preserves_async_adapter_optimized_tail`
22. `django_strawberry_framework/utils/querysets.py::_AsyncQuerySetRows async adapter sync iter rejection`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 2 failed, 102 passed in 5.70s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 104 passed in 5.68s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_list_field.py::test_async_completion_adapter_semantics`
   - `tests/test_list_field.py::test_async_completion_adapter_sync_iter_raises_type_error`

A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is `revision-needed` per `docs/builder/BUILD.md` - the fix is more or better-targeted rows, never a weaker boundary. A boundary at 3 rows or fewer is inside Worker 3's mandatory independent re-run floor. A proof carrying collection or setup errors, or whose pytest run exited anything but 0 or 1 (nothing collected, interrupted, internal error, usage error), is not a valid count at all - and a 0 from such a run is not a zero-row result: resolve it and re-run.

### Hot-path budget

- **Added overhead per invocation on valid path**:
  - Measurement: 10,000 iterations over valid request path measuring list argument normalization and nonzero offset guard validation.
  - Normalization overhead: **0.52 µs** per invocation.
  - Nonzero offset order guard overhead: **7.52 µs** per invocation.
  - Total added overhead: **~8.04 µs** per invocation (budget <= 50 µs).
- **NameConverter calls on valid request path**: **0 calls** (budget = 0). Argument names and wires are read from pre-cached normalized structures.
- **Adapter unwrap and rewrap overhead in `DjangoOptimizerExtension._optimize`**:
  - Measurement: 10,000 iterations of unwrap and rewrap.
  - Overhead: **0.12 µs** per invocation (budget <= 5 µs).

### Floor verification

Owned by the final gate per the plan's declaration. (`Floor-verification scope: none. Owned by the final test-run gate.`)

### Implementation notes

- **Random term detection**: `_is_random_order_term` in `django_strawberry_framework/list_field.py` identifies exact `'?'` strings or `Random` expressions / `OrderBy(Random(...))` constructs, ensuring non-deterministic orderings are acknowledged as active orderings under nonzero offset.
- **Model default ordering checks**: `_is_model_default_ordering_active` mirrors Django's `QuerySet.ordered` logic by inspecting `query.default_ordering`, non-empty non-random model `Meta.ordering`, empty `query.order_by` and `query.extra_order_by`, and `not query.group_by`. Returns `False` when ordering has been explicitly cleared with `.order_by()`.
- **OrderSet post-validation**: `_validate_post_orderset_result` in `django_strawberry_framework/utils/querysets.py` validates `apply_sync` and `apply_async` outputs with `_seal_or_defect` using `_ORDERSET_RESULT_POLICY` (`require_model_rows=True`, `reject_sliced=True`, `reject_combined=True`, `require_unevaluated=True`). It checks both `_db` routing and `_hints` identity to ensure routing intent is faithfully preserved.
- **Async iterator cleanup**: `_cleanup_rejected_async_iterable` in `django_strawberry_framework/list_field.py` ensures that when an async-only iterable resolver output is rejected (due to supplied `orderBy` or nonzero `offset`), `_close_async_iterator` is invoked to release database cursor and async resources before raising the rejection error, with proper `__notes__` diagnostic chaining on cleanup failure.
- **Async completion adapter**: `_AsyncQuerySetRows` wraps final querysets on the async pipeline path, exposing only `__aiter__` (and raising `TypeError` on `__iter__`), preventing synchronous completion of async list fields while allowing Strawberry async execution to iterate smoothly.

### Notes for Worker 3

- Revision pass complete: addressed all Worker 3 review findings from Slice 2.
- DRY cleanup performed in `django_strawberry_framework/list_field.py`:
  - `_orderset_class_for_target`: factored helper eliminating redundant `getattr(definition, "orderset_class", None)`.
  - `_build_non_queryset_rejection_error`: factored shared error construction across async and sync non-queryset rejections.
- Strengthened all 14 previously weakly pinned boundaries. Every single boundary among all 22 failability boundaries now fails >= 2 distinct test rows with 0 collection/setup errors upon mutation (verified via `scripts/prove_failability.py`).
- Eliminated unawaited coroutine teardown warnings in pytest by using `SyncAwaitable` and `ResidualAwaitable` objects that implement `__await__` protocol without leaving uncollected coroutine handles when misuse checks are mutated out.
- Touched files have passed scoped `ruff format`, `ruff check --fix`, and `scripts/check_trailing_commas.py`.
- Validation suite passes 652/652 tests cleanly with 0 failures and 0 errors.

### Notes for Worker 1 (spec reconciliation)

- None; all Slice 2 specifications matched the implementation without drift or conflicts. Error messages and exception types align with the plan: `ListArgumentError` formats wire argument rejections (`order_required` for nonzero offset without ordering), `SyncMisuseError` catches awaitable returns from `apply_sync`, and `ConfigurationError` catches invalid returns from `apply_async` and post-orderset defects.

---

## Review (Worker 3, pass 1)

### High:

#### Weakly Pinned Failability Proofs (14 of 22 boundaries fail only 1 test row)

Per `docs/builder/BUILD.md` lines 285-293 ("Acceptance rule: weakly pinned is `revision-needed`"):
> "A boundary is weakly pinned when removing it makes 0 or 1 test rows fail, counted as `### What gets recorded` defines a row and at the scope recorded there. Weakly pinned is not accepted:
> - 0 rows fail — nothing pins the boundary at all. The suite cannot tell whether it exists.
> - 1 row fails — the boundary rests on one assertion in one row. A single refactor, fixture change, or skip retires it silently.
> Worker 3 sets `revision-needed` and names the additional rows required. The fix is more (or better-targeted) rows — never a weaker boundary, and never a recorded exception."

Fourteen boundaries in Worker 2's build report failed exactly 1 test row upon mutation:
1. `Boundary 2`: `django_strawberry_framework/utils/querysets.py::_visibility_result_error combined defect arm` (1 row: `tests/utils/test_querysets.py::test_visibility_defect_messages`).
   - *Required fix*: Add an end-to-end list field query test or schema execution test where visibility returns a combined queryset under active list arguments, or test `_visibility_result_error` directly with a distinct hook context, ensuring at least 2 distinct test rows assert this error message.
2. `Boundary 3`: `django_strawberry_framework/list_field.py::_handle_non_queryset_rejections_sync order_by non-queryset` (1 row: `tests/test_list_field.py::test_non_queryset_rejections`).
   - *Required fix*: Split or parameterize non-queryset rejections so `list` return and `None` return are independent test rows, or add a test with an integer/object return asserting `queryset_required`.
3. `Boundary 4`: `django_strawberry_framework/list_field.py::_handle_non_queryset_rejections_sync offset non-queryset` (1 row: `tests/test_list_field.py::test_non_queryset_rejections`).
   - *Required fix*: Split or parameterize non-queryset rejections so `offset > 0` on `list` return and `None` return are separate test rows asserting `order_required`.
4. `Boundary 5`: `django_strawberry_framework/list_field.py::_cleanup_rejected_async_iterable close async iterator` (1 row: `tests/test_list_field.py::test_async_iterable_early_cleanup`).
   - *Required fix*: Add a test row verifying async iterable cleanup when rejected due to `offset > 0` (currently only tested via `orderBy: []`).
5. `Boundary 6`: `django_strawberry_framework/list_field.py::_apply_orderset_async non-awaitable return` (1 row: `tests/test_list_field.py::test_apply_orderset_misuse_guards`).
   - *Required fix*: Add an async schema execution test asserting `ConfigurationError` when `apply_async` returns a non-awaitable, or split misuse guards into dedicated test functions.
6. `Boundary 7`: `django_strawberry_framework/list_field.py::_apply_orderset_async residual awaitable return` (1 row: `tests/test_list_field.py::test_apply_orderset_misuse_guards`).
   - *Required fix*: Add an async schema execution test asserting `ConfigurationError` when `apply_async` returns a coroutine that resolves to another awaitable.
7. `Boundary 8`: `django_strawberry_framework/list_field.py::_apply_orderset_sync awaitable return` (1 row: `tests/test_list_field.py::test_apply_orderset_misuse_guards`).
   - *Required fix*: Add a synchronous schema execution test asserting `SyncMisuseError` when `apply_sync` returns a coroutine.
8. `Boundary 9`: `django_strawberry_framework/utils/querysets.py::_validate_post_orderset_result non-queryset rejection` (1 row: `tests/utils/test_querysets.py::test_validate_post_orderset_result`).
   - *Required fix*: Add a schema execution test in `tests/test_list_field.py` asserting `ConfigurationError` when `OrderSet.apply_sync` returns a non-queryset (e.g., `list` or `dict`).
9. `Boundary 16`: `django_strawberry_framework/utils/querysets.py::_validate_post_orderset_result routing mismatch` (1 row: `tests/utils/test_querysets.py::test_validate_post_orderset_result`).
   - *Required fix*: Add a test asserting `_hints` routing mismatch independently from `_db` routing mismatch, or add a schema execution test verifying routing mismatch rejection.
10. `Boundary 17`: `django_strawberry_framework/orders/sets.py::OrderSet._input_has_active_terms purity check` (1 row: `tests/orders/test_sets.py::test_input_has_active_terms_purity`).
    - *Required fix*: Add a test checking `_input_has_active_terms` purity during list field schema execution with `orderBy`, or test input purity across different input structures (e.g. nested or multiple terms).
11. `Boundary 19`: `django_strawberry_framework/list_field.py::_is_random_order_term random term classification` (1 row: `tests/test_list_field.py::test_offset_guard_random_terms`).
    - *Required fix*: Separate test rows for exact `'?'` string and `Random()` / `OrderBy(Random(...))` expressions.
12. `Boundary 20`: `django_strawberry_framework/list_field.py::_is_model_default_ordering_active default ordering check` (1 row: `tests/test_list_field.py::test_offset_guard_model_default`).
    - *Required fix*: Add an independent test row verifying that calling `.order_by()` (clearing `default_ordering`) with `offset > 0` fails with `order_required`.
13. `Boundary 21`: `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize adapter unwrap and rewrap` (1 row: `tests/optimizer/test_extension.py::test_optimizer_preserves_async_adapter`).
    - *Required fix*: Split the 4 test cases in `test_optimizer_preserves_async_adapter` into distinct test functions, and/or add an end-to-end `await schema.execute` query test through the optimizer.
14. `Boundary 22`: `django_strawberry_framework/utils/querysets.py::_AsyncQuerySetRows async adapter sync iter rejection` (1 row: `tests/test_list_field.py::test_async_completion_adapter_semantics`).
    - *Required fix*: Add a unit test verifying `iter(adapter)` raises `TypeError`, or an execution test asserting synchronous completion fails when an `_AsyncQuerySetRows` instance is encountered.

### Medium:

None.

### Low:

#### Repeated `orderset_class` extraction from type definition

`django_strawberry_framework/list_field.py:537-538`, `565-566`, `644-645`, and `688-689` duplicate the definition and orderset attribute access:
```python
definition = getattr(target_type, "__django_strawberry_definition__", None)
orderset_class = getattr(definition, "orderset_class", None)
```
Recommend extracting a private helper `_orderset_class_for_target(target_type: type) -> type | None` to eliminate the repeated pattern.

#### Duplicated `ListArgumentError` creation in non-queryset rejection handlers

`django_strawberry_framework/list_field.py:489-507` and `515-527` repeat the exact `ListArgumentError` construction for `"queryset_required"` and `"order_required"`. The error creation could be factored into a small helper returning `ListArgumentError | None`.

### DRY findings

- `django_strawberry_framework/list_field.py:537-538`, `565-566`, `644-645`, `688-689`: Repeated 4 times across sync/async apply helpers and execution pipelines. Consolidate into `_orderset_class_for_target(target_type)`.
- `django_strawberry_framework/list_field.py:489-507` and `515-527`: Repeated error instantiation across sync and async non-queryset rejection branches.

### Failability audit & independent re-run

- **Manifest**: 22 proof boundaries recorded in `docs/builder/temp-tests/slice-2/proofs.json`.
- **Mandatory Re-run Floor**: Calculated at 20 boundaries:
  - <= 3 rows: boundaries 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 17, 18, 19, 20, 21, 22 (19 boundaries).
  - Security / isolation: boundary 11 (`untrusted query state rejection`, 5 rows).
- **Execution & Independent Verification**: Re-run all 20 floor boundaries using `scripts/prove_failability.py` across two execution batches:
  - Batch 1 (boundaries 1, 2, 3, 4, 5, 6, 7, 8, 9, 10): 0 collection errors, 0 setup errors, pre-mutation copies restored and verified via SHA-256 and byte comparisons. Node ids matched Worker 2's records exactly.
  - Batch 2 (boundaries 11, 12, 14, 16, 17, 18, 19, 20, 21, 22): 0 collection errors, 0 setup errors, pre-mutation copies restored and verified via SHA-256 and byte comparisons. Node ids matched Worker 2's records exactly.
- **Accepted on Worker 2's Record**:
  - Boundary 13: `_seal_or_defect sliced queryset rejection` (4 rows failed).
  - Boundary 15: `_seal_or_defect projection values rejection` (4 rows failed).
- **Audit Outcome**: 14 of 22 boundaries are weakly pinned (failing only 1 row), triggering mandatory `revision-needed`.

### Hot-path budget verification

- Added overhead per invocation on valid path: ~8.04 µs (budget <= 50 µs).
- NameConverter calls on valid request path: 0 calls (budget = 0).
- Adapter unwrap and rewrap overhead: 0.12 µs (budget <= 5 µs).
- Compliance: Full compliance with all hot-path budget declarations.

### Public-surface check

Confirmed via `git diff -- django_strawberry_framework/__init__.py`: 0 public exports added or modified in Slice 2 (`ListArgumentError` was introduced in Slice 1).

### CHANGELOG sanity (only when the slice touches CHANGELOG.md)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- Clean decoupling: `order_input_type` is imported dynamically inside `_synthesized_list_signature`, avoiding premature `.orders` imports when no `orderset_class` is present.
- Pipeline sequencing strictly enforces visibility -> `OrderSet` -> nonzero offset guard -> single window slice.
- `_validate_post_orderset_result` enforces `_ORDERSET_RESULT_POLICY` (`require_model_rows=True, reject_sliced=True, reject_combined=True, require_unevaluated=True`) and protects database routing identity (`_db` and `_hints`).
- Async completion adapter `_AsyncQuerySetRows` implements only `__aiter__`, preventing synchronous iteration leaks in async resolvers.
- `DjangoOptimizerExtension._optimize` transparently unwraps `_AsyncQuerySetRows` before planning and rewraps on all four return paths.
- Deterministic nonzero offset guard accurately checks `_is_random_order_term` and model default ordering, rejecting random orderings or cleared orderings when `offset > 0`.

### Temp test verification

- Verified proof manifest in `docs/builder/temp-tests/slice-2/proofs.json` with 22 valid anchors matching the tree.
- No temporary review tests require promotion.

### Notes for Worker 1 (spec reconciliation)

- None; all Slice 2 specifications matched Card 050 Decisions 5 and 6 without drift or conflicts.

### Review outcome

`revision-needed` (due to 14 weakly-pinned failability boundaries).

---

## Review (Worker 3, pass 2)

### Findings

No blocking findings. All findings from pass 1 have been completely resolved:
1. All 14 previously weakly-pinned boundaries have been reinforced with independent, dedicated test rows. All 22 boundaries in the slice now fail between 2 and 7 distinct test rows upon mutation.
2. Both DRY consolidation opportunities identified in pass 1 (`_orderset_class_for_target` and `_build_non_queryset_rejection_error`) have been cleanly extracted in [`django_strawberry_framework/list_field.py`][list-field].
3. Unawaited coroutine warnings during mutation runs have been eliminated by introducing `SyncAwaitable` and `ResidualAwaitable` test doubles.

### DRY audit

- **Existence challenge**:
  - `_orderset_class_for_target(target_type)`: Extracted in [`django_strawberry_framework/list_field.py`][list-field], replacing four redundant `getattr(definition, "orderset_class", None)` lookups across `_apply_orderset_sync`, `_apply_orderset_async`, and resolver wrappers.
  - `_build_non_queryset_rejection_error(args_record, info)`: Extracted in [`django_strawberry_framework/list_field.py`][list-field], consolidating wire argument rejection construction between `_handle_non_queryset_rejections_sync` and `_handle_non_queryset_rejections_async`.
- **AST inventory check**:
  - Re-checked the inventory in `docs/shadow/helper-inventory.md`. No new duplicate helper symbols or redundant functions introduced across [`list_field.py`][list-field], [`orders/sets.py`][orders-sets], [`utils/querysets.py`][querysets], or [`optimizer/extension.py`][optimizer-extension].
  - Reused existing `_seal_or_defect` and `_visibility_result_error` machinery with targeted extensions (`require_unevaluated: bool = False`, `_ORDERSET_RESULT_POLICY`, and `"combined"` error formatting).

### Failability audit & independent re-run

- **Mandatory re-run floor calculation**:
  - Per `docs/builder/worker-3.md`, boundaries with $\le 3$ failing rows or boundaries touching security / data isolation require mandatory independent re-runs.
  - Out of 22 boundaries, 15 have $\le 3$ failing rows (Boundaries 2, 3, 4, 5, 6, 7, 8, 10, 12, 16, 17, 19, 20, 21, 22), and Boundary 11 (`_seal_or_defect untrusted query state rejection`, 5 rows) protects query state security/isolation.
  - Total floor boundaries re-run: **16 boundaries** (Boundaries 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 16, 17, 19, 20, 21, 22).
  - Pinned boundaries accepted on Worker 2's record: Boundaries 1 (4 rows), 9 (7 rows), 13 (4 rows), 14 (4 rows), 15 (4 rows), 18 (5 rows) — all $> 3$ failing rows with independent assertions.
- **Independent verification results**:
  - Executed via `scripts/prove_failability.py` against `docs/builder/temp-tests/slice-2/proofs.json` across two scoped batches:
    - Batch 1 (Boundaries 2–8): 7 boundaries tested. All exited with code 1 on mutant run, code 0 on baseline run, 0 collection errors, 0 setup errors.
    - Batch 2 (Boundaries 10, 11, 12, 16, 17, 19, 20, 21, 22): 9 boundaries tested. All exited with code 1 on mutant run, code 0 on baseline run, 0 collection errors, 0 setup errors.
  - Every boundary restored cleanly from its pre-mutation copy with byte-level verification (`filecmp.cmp(shallow=False)` and identical SHA-256 hashes).
- **Pinning assessment**:
  - Boundary 2: 2 failing rows (was 1) — `tests/utils/test_querysets.py::test_visibility_defect_messages`, `tests/utils/test_querysets.py::test_apply_type_visibility_sync_combined_result_error`.
  - Boundary 3: 3 failing rows (was 1) — `tests/test_list_field.py::test_async_iterable_early_cleanup`, `tests/test_list_field.py::test_non_queryset_rejection_orderby_list`, `tests/test_list_field.py::test_non_queryset_rejection_orderby_none`.
  - Boundary 4: 3 failing rows (was 1) — `tests/test_list_field.py::test_async_iterable_early_cleanup_on_offset_rejection`, `tests/test_list_field.py::test_non_queryset_rejection_offset_list`, `tests/test_list_field.py::test_non_queryset_rejection_offset_none`.
  - Boundary 5: 2 failing rows (was 1) — `tests/test_list_field.py::test_async_iterable_early_cleanup`, `tests/test_list_field.py::test_async_iterable_early_cleanup_on_offset_rejection`.
  - Boundary 6: 2 failing rows (was 1) — `tests/test_list_field.py::test_apply_orderset_async_schema_execution_rejects_non_awaitable`, `tests/test_list_field.py::test_apply_orderset_async_rejects_non_awaitable`.
  - Boundary 7: 2 failing rows (was 1) — `tests/test_list_field.py::test_apply_orderset_async_schema_execution_rejects_residual_awaitable`, `tests/test_list_field.py::test_apply_orderset_async_rejects_residual_awaitable`.
  - Boundary 8: 2 failing rows (was 1) — `tests/test_list_field.py::test_apply_orderset_sync_rejects_awaitable`, `tests/test_list_field.py::test_apply_orderset_sync_schema_execution_rejects_awaitable`.
  - Boundary 10: 3 failing rows — `tests/utils/test_querysets.py::test_malformed_non_model_query_model_fails_closed_typed`, `tests/utils/test_querysets.py::test_non_class_model_with_convincing_meta_fails_closed`, `tests/utils/test_querysets.py::test_non_model_class_with_convincing_meta_fails_closed`.
  - Boundary 11: 5 failing rows — `tests/utils/test_querysets.py::test_foreign_query_class_result_fails_closed`, `tests/utils/test_querysets.py::test_pending_deferred_filter_over_foreign_query_never_dispatches`, `tests/utils/test_querysets.py::test_hostile_foreign_query_type_name_cannot_escape_typed_defect`, `tests/utils/test_querysets.py::test_prefetch_with_foreign_inner_query_fails_closed`, `tests/utils/test_querysets.py::test_prefetch_child_defect_detail_appears_in_message`.
  - Boundary 12: 3 failing rows — `tests/utils/test_querysets.py::test_seal_require_unevaluated`, `tests/utils/test_querysets.py::test_visibility_defect_messages`, `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_evaluated`.
  - Boundary 16: 2 failing rows (was 1) — `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_db_routing_mismatch`, `tests/utils/test_querysets.py::test_validate_post_orderset_result_rejects_hints_routing_mismatch`.
  - Boundary 17: 2 failing rows (was 1) — `tests/orders/test_sets.py::test_input_has_active_terms_purity`, `tests/orders/test_sets.py::test_input_has_active_terms_purity_structure_disagreement`.
  - Boundary 19: 2 failing rows (was 1) — `tests/test_list_field.py::test_offset_guard_random_term_question_mark`, `tests/test_list_field.py::test_offset_guard_random_term_random_function`.
  - Boundary 20: 2 failing rows (was 1) — `tests/test_list_field.py::test_offset_guard_model_default_cleared_by_order_by`, `tests/test_list_field.py::test_offset_guard_model_default_cleared_schema_execution`.
  - Boundary 21: 3 failing rows (was 1) — `tests/optimizer/test_extension.py::test_optimizer_preserves_async_adapter_evaluated_cache`, `tests/optimizer/test_extension.py::test_optimizer_preserves_async_adapter_unresolved_type`, `tests/optimizer/test_extension.py::test_optimizer_preserves_async_adapter_optimized_tail`.
  - Boundary 22: 2 failing rows (was 1) — `tests/test_list_field.py::test_async_completion_adapter_semantics`, `tests/test_list_field.py::test_async_completion_adapter_sync_iter_raises_type_error`.
  - **Verdict:** All 22 boundaries now have $\ge 2$ failing rows. Zero weakly-pinned boundaries remain.

### Hot-path budget verification

- Added overhead per invocation on valid path: ~8.04 µs (normalization: 0.52 µs, nonzero offset order guard: 7.52 µs), well within budget $\le 50$ µs.
- NameConverter calls on valid path: exactly 0 calls (wire name resolution is strictly lazy on error).
- Adapter unwrap/rewrap overhead in `DjangoOptimizerExtension._optimize`: ~0.12 µs, well within budget $\le 5$ µs.

### Public-surface check

- Verified diff on `django_strawberry_framework/__init__.py`.
- No new public symbols exported in Slice 2 (`ListArgumentError` was introduced in Slice 1).
- All new pipeline helpers (`_orderset_class_for_target`, `_build_non_queryset_rejection_error`, `_AsyncQuerySetRows`, `_validate_post_orderset_result`, `_is_random_order_term`, `_is_model_default_ordering_active`) are properly private with leading underscores.
- `__all__` export list is clean and intact.

### CHANGELOG sanity (only when the slice touches CHANGELOG.md)

- Not applicable; slice did not touch `CHANGELOG.md`.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

- Verified in-flight spec references to [`spec-050-list_field_arguments-0_0_15.md`][spec-050] (lines 83–95).
- No premature version bump or changes to packaging metadata.

### What looks solid

- Double-run purity check in `OrderSet._input_has_active_terms` detects stateful or non-deterministic input normalizers and fails closed with `ConfigurationError`.
- Clean error differentiation: `ListArgumentError` for client argument defects, `SyncMisuseError` for awaitables returned in synchronous execution, and `ConfigurationError` for invalid OrderSet outputs and routing mismatches.
- Resource-safe early cancellation of async iterators in `_cleanup_rejected_async_iterable` awaiting `aclose()` before raising client argument rejection errors.
- Async completion protection: `_AsyncQuerySetRows` implements only `__aiter__` and raises `TypeError` on `__iter__`, preventing synchronous evaluation leaks in Strawberry GraphQL async execution.

### Temp test verification

- All temporary proof manifests and test files are isolated under `docs/builder/temp-tests/slice-2/`.
- No temporary review tests require promotion.

### Notes for Worker 1 (spec reconciliation)

- None; all Slice 2 specifications matched Card 050 Decisions 5 and 6 without drift or conflicts.

### Review outcome

`review-accepted`

---

## Final verification (Worker 1)

### Summary

Slice 2 ships the meta-derived `orderBy` pipeline and comprehensive list argument execution flow
for `DjangoListField`. Key achievements include:
- Conditional `orderBy: [<OrderSet>InputType!]` synthesis in `_synthesized_list_signature` for
  targets declaring `Meta.orderset_class`, with dynamic import of `order_input_type`.
- Deterministic pipeline execution order: argument normalization -> visibility filtering ->
  `OrderSet` execution -> nonzero offset ordering guard -> bounded window slicing.
- Rejection of `orderBy` and nonzero `offset` on non-queryset returns with resource-safe
  cancellation of async iterators via `_close_async_iterator`.
- Robust post-`OrderSet` validation in `_validate_post_orderset_result` using
  `_ORDERSET_RESULT_POLICY` (`require_model_rows=True`, `reject_sliced=True`,
  `reject_combined=True`, `require_unevaluated=True`) and strict database routing consistency
  verification (`_db` and `_hints`).
- Detection and prevention of sync/async misuse across `OrderSet.apply_sync` and `apply_async`.
- Enforced nonzero offset guard requiring active non-random `orderBy` terms or effective
  model `Meta.ordering` via `_is_model_default_ordering_active` and `_is_random_order_term`.
- Async completion protection via `_AsyncQuerySetRows` adapter exposing only `__aiter__` (and
  forbidding `__iter__`), with transparent unwrap and rewrap in
  `DjangoOptimizerExtension._optimize`.
- Purity enforcement in `OrderSet._input_has_active_terms` with double-run verification.

### Checklist audit

Every planned item in `### Spec slice checklist (verbatim)` was verified against the diff:
- [x] A target carrying `Meta.orderset_class` gains nullable, optional
      `orderBy: [<OrderSet>InputType!]`; a target without that sidecar does not publish a
      meaningless order input. (Verified in `_synthesized_list_signature` and test
      `tests/test_list_field.py::test_orderset_orderby_schema_generation`).
- [x] Sync and async paths run visibility, then `OrderSet`, then the offset/order guard,
      then the one raw-list slice. (Verified in `_execute_queryset_pipeline_sync`,
      `_execute_queryset_pipeline_async`, and test
      `tests/test_list_field.py::test_pipeline_execution_order`).
- [x] The result of a public `OrderSet.apply_*` override is validated as an unevaluated,
      unsliced, non-projection, non-combined model queryset before the final window; the
      seal gains the new `unevaluated` option, reuses the shipped `reject_combined` one,
      and both new-to-this-boundary codes gain arms at the two visibility message sites.
      (Verified in `_validate_post_orderset_result`, `_SealPolicy`, `_seal_or_defect`,
      `_visibility_result_error`, `_prepared_visibility_source`, and test suite in
      `tests/utils/test_querysets.py`).
- [x] Nonzero offset requires a materially active `orderBy` or still-effective model
      `Meta.ordering` on the post-visibility queryset; no pk tiebreaker and no `DISTINCT`
      are injected. (Verified in `_check_nonzero_offset_guard`,
      `_is_model_default_ordering_active`, `_is_random_order_term`,
      `OrderSet._input_has_active_terms`, and test suite in `tests/test_list_field.py`).

### Test run

Focused test suite command:
`uv run pytest tests/test_list_field.py tests/orders/test_sets.py tests/utils/test_querysets.py tests/optimizer/test_extension.py --no-cov`

Result: **PASS** (`652 passed in 9.20s`, exit code 0).
Ran without `--cov*` flags per [`BUILD.md`][build-md] guidelines; zero test failures or regressions.

### Failability and fail-open confirmation

- **Failability proofs:** All 22 boundaries defined in the plan carry complete failability proof
  records in `docs/builder/temp-tests/slice-2/proofs.json`. Confirmed that all 22 boundaries fail
  between 2 and 7 distinct test rows (zero weakly-pinned boundaries <= 1 row). All baseline and
  mutant pytest runs completed with zero collection errors and zero setup errors. Each mutated file
  was proved restored to bit-level identity via `filecmp.cmp(shallow=False)` and SHA-256 digest
  comparison.
- **Fail-open audit:** Audited the working tree diff across
  [`django_strawberry_framework/list_field.py`][list-field],
  [`django_strawberry_framework/orders/sets.py`][orders-sets],
  [`django_strawberry_framework/utils/querysets.py`][querysets], and
  [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension]. Confirmed no
  fail-open shapes landed:
  - Coordinate presence checks explicitly test against `None` and `strawberry.UNSET`, properly
    recognizing `0` and `[]` as supplied values.
  - Early rejection of non-queryset sources with `orderBy` or `offset > 0` cleans up async-only
    iterables via `_close_async_iterator` and `_cleanup_rejected_async_iterable` before raising
    `ListArgumentError`.
  - Sync and async misuse on `OrderSet.apply_sync` (awaitable return) and `apply_async`
    (non-awaitable or residual awaitable return) safely dispose coroutines via
    `_dispose_sync_awaitable` and fail closed with `SyncMisuseError` or `ConfigurationError`.
  - `_validate_post_orderset_result` seals candidate querysets against `_ORDERSET_RESULT_POLICY`
    and strictly validates routing intent (`candidate._db == source._db` and `candidate._hints ==
    source._hints`), raising `ConfigurationError` on any mismatch.
  - `OrderSet._input_has_active_terms` validates normalization purity by running
    `_normalize_input` twice and rejecting stateful or non-deterministic normalizers with
    `ConfigurationError`.
  - `_is_model_default_ordering_active` mirrors Django's `QuerySet.ordered` default ordering logic
    by verifying `query.default_ordering`, checking for non-empty non-random model `Meta.ordering`,
    and verifying absence of `order_by`, `extra_order_by`, or `group_by`. Random terms (`"?"` or
    `Random()`) are strictly classified as non-ordering via `_is_random_order_term`.
  - `_AsyncQuerySetRows` implements only `__aiter__` and defines no `__iter__`, causing synchronous
    iteration in GraphQL execution to fail closed with `TypeError`.
  - `DjangoOptimizerExtension._optimize` unwraps `_AsyncQuerySetRows` before optimization analysis
    and guarantees rewrapping across all exit paths (evaluated cache, unmapped type, optimized).

### Spec changes made (Worker 1 only)

None.

### Notes for the build plan

Slice 2 is final-accepted. The next slice is Slice 3 (`SQL and unit contracts`). All staged TODO
anchors for Slice 2 (`TODO(spec-050 slice 2)`) have been cleanly discharged across the codebase.

---

## Plan (Worker 1, pass 3: gate re-loop)

### Defect and root-cause analysis

During the final test-run gate ([`bld-final.md`][bld-final]), the test sweep surfaced Failure 2 in
[`tests/test_relay_connection.py::test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo`][test-relay-connection]:
- Slice 2 introduced `_AsyncQuerySetRows` ([`django_strawberry_framework/utils/querysets.py::_AsyncQuerySetRows`][querysets])
  as an async-only completion adapter wrapping a final sliced `QuerySet` under async execution.
- By design (Decision 5 of [`spec-050`][spec-050]), `_AsyncQuerySetRows` implements only `__aiter__` and
  deliberately omits `__iter__` to prevent synchronous ORM iteration in an event-loop thread.
- When `DjangoListField` is executed asynchronously with child awaitable resolvers (e.g. `booksConnection(last: 0)`),
  `graphql-core`'s [`graphql/execution/execute.py::ExecutionContext.complete_list_value`][graphql-execute] detects
  that `result` is not a synchronous `is_iterable(result)` and falls into its experimental `AsyncIterable` branch.
- In `complete_list_value`, the inner `async_iterable_to_list` helper runs:
  ```python
  sync_result = [item async for item in async_result]
  return self.complete_list_value(
      return_type, field_nodes, info, path, sync_result
  )
  ```
- Because child fields are awaitable, `self.complete_list_value(..., sync_result)` returns `get_completed_results()`
  (a coroutine object).
- Upstream `async_iterable_to_list` returns this coroutine without checking `self.is_awaitable(completed)` or
  awaiting it, leaking the inner unawaited coroutine into `result.data["objs"]`.
- The caller of `schema.execute` attempts to subscript the result (`result.data["objs"][0]["booksConnection"]`),
  raising `TypeError: 'coroutine' object is not subscriptable` and emitting `RuntimeWarning: coroutine was never awaited`
  (which cascaded into [`test_resource_policy_api.py`][test-resource-policy-api] as an unraisable warning).

### DRY analysis

- **Helper inventory checked.** Refreshed the shallow AST inventory across the entire package
  (`django_strawberry_framework/`) into `docs/shadow/helper-inventory.md` before planning. Also inspected
  [`django_strawberry_framework/_strawberry_patches.py`][strawberry-patches] and
  [`tests/test_strawberry_patches.py`][test-strawberry-patches].
  Candidates identified and evaluated:
  - `_captured_upstream_method(owner, name)`: Reused to capture `ExecutionContext.complete_list_value` cleanly
    across in-process reloads.
  - `_mark_patch_replacement(patched, original)`: Reused to stamp `_patched_complete_list_value` with
    `_PATCH_OWNER_ATTRIBUTE` and `_PATCH_ORIGINAL_ATTRIBUTE`.
  - `_patch_is_installed()`: Reused and extended to assert that `ExecutionContext.complete_list_value` is
    `_patched_complete_list_value`.
  - `_validate_upstream_shape()`: Reused and extended to pin `ExecutionContext.complete_list_value`'s presence,
    callability, and exact `(self, return_type, field_nodes, info, path, result)` parameter signature.
  - `apply()`: Reused to install `_patched_complete_list_value` when `upstream_patches_enabled("strawberry")` is active.
- **Existing patterns reused:**
  - The patch wrapping pattern in `_strawberry_patches.py`: capture original, validate shape/signature at `apply()` time,
    check installation idempotency in `_patch_is_installed()`, stamp wrapper with owner/original metadata.
  - The opt-out pattern: gated under `upstream_patches_enabled("strawberry")` (controlled by
    `APPLY_UPSTREAM_PATCHES`), so consumers pinning an upstream version that fixes this bug or opting out via
    `{"strawberry": False}` can disable the patch without affecting package views.
  - Self-healing idempotency: if a third party mutates or reverts `ExecutionContext.complete_list_value`, the next
    `apply()` detects `_patch_is_installed() is False` and restores all patch members atomically.
- **New helpers justified:**
  - `_patched_complete_list_value`: Single-responsibility delegating wrapper on `ExecutionContext.complete_list_value`.
    When `result` is an `AsyncIterable` (and not a synchronous iterable), it executes `async_iterable_to_list` and
    properly awaits `self.complete_list_value` if it returns an awaitable (`if self.is_awaitable(completed): return await completed`).
    For all other values, it delegates directly to `_original_complete_list_value`.
- **Duplication risk avoided:**
  - Avoid creating a separate patch module or inventing a new settings key. `_strawberry_patches.py` already owns
    GraphQL execution / HTTP handling patches for Strawberry and its execution engine `graphql-core`.
  - No hand-rolled coroutine gathering: delegates to upstream `complete_list_value` for synchronous list completion
    and `is_awaitable` checking, preserving graphql-core's error handling, located errors, and field execution paths.

### Implementation steps

1. In [`django_strawberry_framework/_strawberry_patches.py`][strawberry-patches]:
   - Import `from collections.abc import AsyncIterable` at module scope.
   - In the `try...except ImportError` block, import `ExecutionContext` from `graphql.execution.execute` and
     `is_iterable` from `graphql.pyutils`. In the `except ImportError` fallback, set both to `None`.
   - Capture the upstream method:
     ```python
     _original_complete_list_value = _captured_upstream_method(
         ExecutionContext,
         "complete_list_value",
     )
     ```
   - Define `_patched_complete_list_value`:
     ```python
     def _patched_complete_list_value(
         self: Any,
         return_type: Any,
         field_nodes: Any,
         info: Any,
         path: Any,
         result: Any,
     ) -> Any:
         """Wrapper around ``ExecutionContext.complete_list_value``.

         Fixes an upstream bug in ``graphql-core``'s experimental ``AsyncIterable``
         branch: ``async_iterable_to_list`` calls ``self.complete_list_value`` but
         fails to await it when child field resolvers are awaitable.
         """
         if not is_iterable(result) and isinstance(result, AsyncIterable):
             async def async_iterable_to_list(
                 async_result: AsyncIterable[Any],
             ) -> Any:
                 sync_result = [item async for item in async_result]
                 completed = self.complete_list_value(
                     return_type, field_nodes, info, path, sync_result
                 )
                 if self.is_awaitable(completed):
                     return await completed
                 return completed

             return async_iterable_to_list(result)

         return _original_complete_list_value(
             self, return_type, field_nodes, info, path, result
         )
     ```
   - Mark the replacement:
     ```python
     _mark_patch_replacement(
         _patched_complete_list_value,
         _original_complete_list_value,
     )
     ```
   - Update `_validate_upstream_shape()`:
     - Check `ExecutionContext is None`, `not callable(_original_complete_list_value)`, and `not callable(is_iterable)`
       in the presence check; raise `RuntimeError` on failure.
     - Inspect `_original_complete_list_value` parameter signature: verify `len(parameters) == 6` and all kinds are
       `POSITIONAL_OR_KEYWORD`; raise `RuntimeError` if signature drifts.
   - Update `_patch_is_installed()`:
     - Add check: `and ExecutionContext is not None and ExecutionContext.__dict__.get("complete_list_value") is _patched_complete_list_value`.
   - Update `apply()`:
     - Install `ExecutionContext.complete_list_value = _patched_complete_list_value`.
   - Update module docstrings and method docstrings to describe Gap 4 (unawaited coroutine in `ExecutionContext.complete_list_value`
     for `AsyncIterable` with child awaitable resolvers).

2. In [`tests/test_strawberry_patches.py`][test-strawberry-patches]:
   - Update `test_patch_is_installed_on_base_view` (or rename to reflect all upstream targets):
     assert `ExecutionContext.__dict__["complete_list_value"] is patches._patched_complete_list_value`.
   - Add `test_apply_reinstalls_when_complete_list_value_reverted()`:
     verify that reverting `ExecutionContext.complete_list_value = patches._original_complete_list_value` causes
     `patches._patch_is_installed() is False`, and `patches.apply()` re-installs it.
   - Add `test_apply_fails_loudly_when_execution_context_missing()`:
     mock `ExecutionContext = None` and assert `patches.apply()` raises `RuntimeError` matching `"complete_list_value"`.
   - Add `test_apply_fails_loudly_when_complete_list_value_signature_changes()`:
     mock `_original_complete_list_value` with incorrect arity and assert `patches.apply()` raises `RuntimeError`
     matching `"complete_list_value no longer has the expected"`.
   - Add behavioral tests for `_patched_complete_list_value`:
     - Test with `AsyncIterable` yielding objects whose fields return awaitables: proves `self.is_awaitable(completed)`
       branch awaits the coroutine and returns the completed list rather than an unawaited coroutine.
     - Test with `AsyncIterable` yielding objects whose fields are sync: returns the completed list.
     - Test with synchronous `Iterable` (e.g. list): passes through directly to `_original_complete_list_value`.
   - Update `test_apply_no_ops_when_strawberry_dependency_opted_out` and
     `test_the_gated_workarounds_really_stop_hardening_when_opted_out`:
     preserve and restore `ExecutionContext.complete_list_value`, and verify `{"strawberry": False}` leaves
     `ExecutionContext.complete_list_value` unpatched.

3. Verify [`tests/test_relay_connection.py`][test-relay-connection]:
   - Re-run `tests/test_relay_connection.py::test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo`.
   - Confirm it passes without raising `TypeError: 'coroutine' object is not subscriptable` and without emitting
     `RuntimeWarning: coroutine was never awaited`.
   - Re-run `tests/test_resource_policy_api.py` to confirm the cascaded unraisable warning clears.

### Test additions / updates

- [`tests/test_strawberry_patches.py`][test-strawberry-patches]:
  - `test_patch_is_installed_on_base_view`: updated to check `ExecutionContext.complete_list_value`.
  - `test_apply_reinstalls_when_complete_list_value_reverted`: proves self-healing on partial revert of `complete_list_value`.
  - `test_apply_fails_loudly_when_execution_context_missing`: proves shape validation fails loudly when `ExecutionContext` is missing.
  - `test_apply_fails_loudly_when_complete_list_value_signature_changes`: proves signature validation fails loudly when arity drifts.
  - `test_patched_complete_list_value_awaits_async_iterable_with_awaitable_children`: unit test verifying that an `AsyncIterable` with awaitable children returns an awaited list of resolved values.
  - `test_patched_complete_list_value_handles_sync_children`: unit test verifying `AsyncIterable` with sync children completes cleanly.
  - `test_patched_complete_list_value_delegates_sync_iterable`: unit test verifying synchronous iterables bypass the `async_iterable_to_list` wrapper.
  - `test_apply_no_ops_when_strawberry_dependency_opted_out`: updated to verify `ExecutionContext.complete_list_value` remains unpatched when `{"strawberry": False}`.
- [`tests/test_relay_connection.py`][test-relay-connection]:
  - `test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo`: verified to pass end-to-end under async execution.

### Implementation discretion items

- Worker 2 may structure the unit tests in `tests/test_strawberry_patches.py` either using a lightweight mock `ExecutionContext`
  harness or using a small schema with `execute_sync`/`execute` to exercise `_patched_complete_list_value`.
- Worker 2 may keep or refine the exact wording of the `RuntimeError` in `_validate_upstream_shape` so long as it matches
  the surrounding pattern and names `ExecutionContext.complete_list_value` and `APPLY_UPSTREAM_PATCHES = {"strawberry": False}`.

### Dispatched findings checklist

- [x] Install upstream patch in `django_strawberry_framework/_strawberry_patches.py` for
      `graphql.execution.execute.ExecutionContext.complete_list_value`.
- [x] Gating: ensure the patch is gated by `upstream_patches_enabled("strawberry")` via `conf.py` / `APPLY_UPSTREAM_PATCHES`.
- [x] Self-healing & idempotency: ensure `_patch_is_installed()` and `apply()` handle repeated calls and partial reverts.
- [x] Shape validation: ensure `_validate_upstream_shape()` checks `ExecutionContext` presence and `(self, return_type, field_nodes, info, path, result)` arity.
- [x] Awaiting coroutine: ensure `async_iterable_to_list` checks `if self.is_awaitable(completed): return await completed`
      to resolve nested awaitable resolvers.
- [x] Tests in `tests/test_strawberry_patches.py`: test installation, idempotency, self-healing, shape validation,
      and behavioral completion of `AsyncIterable` with awaitable child resolvers.
- [x] Test verification in `tests/test_relay_connection.py`: confirm
      `test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo` passes cleanly without warnings or errors.

## Build report (Worker 2, pass 3)

### Files touched

- [`django_strawberry_framework/_strawberry_patches.py`][strawberry-patches]
- [`tests/test_strawberry_patches.py`][test-strawberry-patches]
- [`docs/builder/bld-slice-2-orderby_pipeline.md`](bld-slice-2-orderby_pipeline.md)
- [`docs/builder/worker-memory/worker-2.md`][worker-2-memory]

### Tests added or updated

- [`tests/test_strawberry_patches.py`][test-strawberry-patches]:
  - `test_patch_is_installed_on_base_view`: updated to assert `ExecutionContext.__dict__["complete_list_value"] is patches._patched_complete_list_value`.
  - `test_apply_reinstalls_when_complete_list_value_reverted`: proves self-healing on partial revert of `ExecutionContext.complete_list_value`.
  - `test_apply_reinstalls_all_members_when_one_multipart_method_reverted`: updated to verify `ExecutionContext.complete_list_value` stays installed.
  - `test_apply_fails_loudly_when_execution_context_missing`: proves shape validation fails loudly with `RuntimeError` matching `"complete_list_value"` when `ExecutionContext` is missing.
  - `test_apply_fails_loudly_when_is_iterable_missing`: proves shape validation fails loudly when `is_iterable` helper is missing.
  - `test_apply_fails_loudly_when_complete_list_value_signature_changes`: proves signature validation fails loudly when `complete_list_value` arity drifts from 6 parameters.
  - `test_apply_no_ops_when_toggle_disabled`: updated to verify `complete_list_value` remains unpatched when `APPLY_UPSTREAM_PATCHES = False`.
  - `test_apply_no_ops_when_strawberry_dependency_opted_out`: updated to verify `complete_list_value` remains unpatched when `{"strawberry": False}`.
  - `test_the_gated_workarounds_really_stop_hardening_when_opted_out`: updated to verify `complete_list_value` remains unpatched during behavioral opt-out.
  - `test_patched_complete_list_value_awaits_async_iterable_with_awaitable_children`: behavioral test verifying `AsyncIterable` with awaitable child resolvers completes to an awaited list of resolved values.
  - `test_patched_complete_list_value_handles_sync_children`: behavioral test verifying `AsyncIterable` with sync children completes cleanly.
  - `test_patched_complete_list_value_delegates_sync_iterable`: behavioral test verifying synchronous iterables bypass `async_iterable_to_list` and delegate directly.

### Validation run

- `uv run pytest tests/test_strawberry_patches.py --no-cov`: 68 passed in 1.65s.
- `uv run pytest tests/test_relay_connection.py -k "test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo" --no-cov`: 1 passed in 3.02s.
- `uv run pytest tests/test_relay_connection.py --no-cov`: 90 passed in 4.43s.
- `uv run pytest --cov=django_strawberry_framework`: 1445 passed, 2 skipped in 34.39s (100.00% coverage, 4690/4690 statements covered).
- `uv run ruff format` and `uv run ruff check --fix`: all checks passed, 0 errors.
- `python scripts/check_trailing_commas.py --check`: all checks passed.

### Failability proofs

None; this pass introduced no new boundary.

### Notes for Worker 3

- Upstream `graphql-core` `ExecutionContext.complete_list_value` is defensively wrapped and stamped in `_strawberry_patches.py` alongside `BaseView` and `BaseHTTPView` patches.
- The wrapper detects when an `AsyncIterable` is completed and checks `if self.is_awaitable(completed): return await completed`, resolving the issue where nested awaitables returned unawaited coroutines inside async iterable lists.
- Gated by `APPLY_UPSTREAM_PATCHES` under the `"strawberry"` dependency; fully self-healing on partial reverts and validated for shape and parameter arity.
- `test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo` in `tests/test_relay_connection.py` now passes cleanly with 0 warnings.

---

## Review (Worker 3, pass 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- Verified against `docs/shadow/helper-inventory.md` and `_strawberry_patches.py`.
- Reused existing patch lifecycle and testing patterns: `_captured_upstream_method`, `_mark_patch_replacement`, `_patch_is_installed()`, `_validate_upstream_shape()`, and `apply()`.
- Gated under `upstream_patches_enabled("strawberry")` without duplicate settings keys or configuration switches.
- Wrapper delegates non-async-iterables and synchronous iterables directly to `_original_complete_list_value`, avoiding duplicate list completion machinery.

### Failability audit & independent re-run

None; this pass introduced no new boundary.

Pass 3 introduces a defensive wrapper around upstream `graphql-core` `ExecutionContext.complete_list_value` rather than a new package-level contract boundary. All 22 package-level boundaries for Slice 2 were proven and verified in passes 1 and 2.

### Public-surface check

Confirmed via `git diff -- django_strawberry_framework/__init__.py`: 0 public exports added or modified in Pass 3 (`ListArgumentError` was introduced in Slice 1). `__all__` is unchanged.

### CHANGELOG sanity (only when the slice touches CHANGELOG.md)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- The upstream monkeypatch in `django_strawberry_framework/_strawberry_patches.py` cleanly intercepts `ExecutionContext.complete_list_value` when `result` is an `AsyncIterable` and awaits recursive `complete_list_value` execution when child resolvers return awaitables (`if self.is_awaitable(completed): return await completed`).
- `test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo` in `tests/test_relay_connection.py` now executes cleanly end-to-end under async GraphQL execution without `TypeError: 'coroutine' object is not subscriptable` or `RuntimeWarning: coroutine was never awaited`.
- Robust shape validation in `_validate_upstream_shape()` verifies symbol presence, callability, and exact parameter signature (`(self, return_type, field_nodes, info, path, result)`, 6 parameters with `POSITIONAL_OR_KEYWORD`), failing loudly on upstream drift.
- Full self-healing and idempotency in `apply()` and `_patch_is_installed()`: re-entrant `apply()` is a no-op; third-party reverts of `complete_list_value` trigger complete reinstallation.
- Opt-out gating via `APPLY_UPSTREAM_PATCHES = False` or `{"strawberry": False}` prevents installation and leaves `ExecutionContext.complete_list_value` unpatched.
- All 68 tests in `tests/test_strawberry_patches.py` and 90 tests in `tests/test_relay_connection.py` pass cleanly (158 passed in 4.51s, 0 warnings).

### Temp test verification

None required; existing unit tests in `tests/test_strawberry_patches.py` thoroughly cover installation, idempotency, self-healing, shape validation, opt-out gating, and async iterable list completion.

### Notes for Worker 1 (spec reconciliation)

None.

### Review outcome

`review-accepted`

---

## Final verification (Worker 1, pass 3)

### Summary

Pass 3 resolves Failure 2 from the final test-run gate ([`bld-final.md`][bld-final]) by adding a defensive upstream wrapper around `graphql-core`'s `ExecutionContext.complete_list_value` in [`django_strawberry_framework/_strawberry_patches.py`][strawberry-patches]. When `result` is an `AsyncIterable` (and not a synchronous iterable), the patch awaits nested `complete_list_value` execution when child resolvers return awaitables (`if self.is_awaitable(completed): return await completed`). This fixes the upstream issue where nested awaitables returned unawaited coroutines inside async iterable lists, eliminating `TypeError: 'coroutine' object is not subscriptable` and `RuntimeWarning: coroutine was never awaited` during async execution.

### Checklist audit

Audited the `### Dispatched findings checklist` in `## Plan (Worker 1, pass 3: gate re-loop)` against the diff:
- [x] Install upstream patch in `django_strawberry_framework/_strawberry_patches.py` for
      `graphql.execution.execute.ExecutionContext.complete_list_value`. (Verified: wrapper `_patched_complete_list_value` defined, stamped with owner/original attributes, and installed on `ExecutionContext.complete_list_value`).
- [x] Gating: ensure the patch is gated by `upstream_patches_enabled("strawberry")` via `conf.py` / `APPLY_UPSTREAM_PATCHES`. (Verified: `apply()` conditions installation on `upstream_patches_enabled("strawberry")`, and tests verify opt-out leaves `ExecutionContext.complete_list_value` unpatched).
- [x] Self-healing & idempotency: ensure `_patch_is_installed()` and `apply()` handle repeated calls and partial reverts. (Verified: `_patch_is_installed()` checks `ExecutionContext.__dict__.get("complete_list_value") is _patched_complete_list_value`, and partial revert triggers re-installation of all patch members).
- [x] Shape validation: ensure `_validate_upstream_shape()` checks `ExecutionContext` presence and `(self, return_type, field_nodes, info, path, result)` arity. (Verified: validates `ExecutionContext` and `is_iterable` presence/callability and pins the 6 positional-or-keyword parameters).
- [x] Awaiting coroutine: ensure `async_iterable_to_list` checks `if self.is_awaitable(completed): return await completed`
      to resolve nested awaitable resolvers. (Verified: `async_iterable_to_list` awaits `completed` if `self.is_awaitable(completed)`).
- [x] Tests in `tests/test_strawberry_patches.py`: test installation, idempotency, self-healing, shape validation,
      and behavioral completion of `AsyncIterable` with awaitable child resolvers. (Verified: comprehensive suite of 12 tests added/updated covering all lifecycle, shape validation, and execution scenarios).
- [x] Test verification in `tests/test_relay_connection.py`: confirm
      `test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo` passes cleanly without warnings or errors. (Verified: test passes cleanly in 4.54s with 0 warnings).

### Test run

Focused test suite command:
`uv run pytest tests/test_strawberry_patches.py tests/test_relay_connection.py --no-cov`

Result: **PASS** (`158 passed in 4.54s`, exit code 0).
Ran without `--cov*` flags per [`BUILD.md`][build-md] guidelines; zero test failures or regressions.

### AST shadow cleanliness and DRY audit

- Generated AST shadow inspection via `scripts/review_inspect.py django_strawberry_framework/_strawberry_patches.py --output-dir docs/shadow`.
- 0 TODO comments in `_strawberry_patches.py`.
- No new Django/ORM markers or dependencies added.
- Repeated literals check confirmed no unjustified repetition: `complete_list_value` appears only 2 times as the attribute name on `ExecutionContext`.
- Reused established patching lifecycle patterns in `_strawberry_patches.py` without introducing duplicate helpers or settings keys.

### Failability and fail-open confirmation

Pass 3 introduces a defensive wrapper around upstream `graphql-core` `ExecutionContext.complete_list_value` to address upstream behavior under `AsyncIterable` completion, rather than introducing a new package-level contract boundary. All 22 package-level boundaries for Slice 2 remain proven and verified from passes 1 and 2. The implementation fails closed on missing dependencies or signature drift via loud `RuntimeError` at `apply()` time, and safely awaits coroutines rather than leaking them unawaited.

### Spec changes made (Worker 1 only)

None. The upstream execution patch in `_strawberry_patches.py` maintains all normative contracts of [`spec-050`][spec-050] without requiring spec reconciliation.

### Notes for the build plan

Pass 3 of Slice 2 is final-accepted. Failure 2 from [`bld-final.md`][bld-final] is fully resolved.

---

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-050]: ../spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[bld-final]: bld-final.md
[build-md]: BUILD.md
[worker-2-memory]: worker-memory/worker-2.md

<!-- django_strawberry_framework/ -->
[list-field]: ../../django_strawberry_framework/list_field.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[strawberry-patches]: ../../django_strawberry_framework/_strawberry_patches.py

<!-- tests/ -->
[test-list-field]: ../../tests/test_list_field.py
[test-orders-sets]: ../../tests/orders/test_sets.py
[test-optimizer-extension]: ../../tests/optimizer/test_extension.py
[test-querysets]: ../../tests/utils/test_querysets.py
[test-relay-connection]: ../../tests/test_relay_connection.py
[test-strawberry-patches]: ../../tests/test_strawberry_patches.py

<!-- examples/ -->
[test-resource-policy-api]: ../../examples/fakeshop/test_query/test_resource_policy_api.py

<!-- scripts/ -->

<!-- .venv/ -->
[graphql-execute]: ../../.venv/lib/python3.14/site-packages/graphql/execution/execute.py

<!-- External -->
