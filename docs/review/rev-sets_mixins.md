# Review: `django_strawberry_framework/sets_mixins.py`

Status: verified

## Understanding

`sets_mixins.py` is the neutral owner for the shared FilterSet/OrderSet substrate:

- `ClassBasedTypeNameMixin.type_name_for` supplies root and field-path GraphQL input names. `filters/inputs.py`, `orders/inputs.py`, and the shared generated-input factory call it rather than rebuilding the naming rule.
- `LazyRelatedClassMixin` and `RelatedSetTargetMixin` resolve class objects, absolute import paths, same-module names, and zero-argument callable references. `filters/base.py::RelatedFilter` and `orders/base.py::RelatedOrder` provide only family-named wrappers and storage slots.
- `collect_related_declarations` reconciles each metaclass's declaration map with direct-base precedence, class-body overrides, and tombstones, then binds each surviving declaration to its owner.
- `expanded_once` isolates each class's expansion cache and re-entry guard through `__dict__`; `should_cache_expansion` prevents caching before related targets resolve. `FilterSet.get_filters` additionally publishes its candidate metadata snapshot under the same gate.
- `SetLifecycleAttrs` is consumed by `utils/inputs.py::clear_generated_input_namespace`, so `registry.clear()` removes each family's owner, cache, guard, and filter snapshot attributes together.

The finalizer binds all sidecar owners before expansion, then expands and materializes resolver input classes. Filter and order resolver callers run their own `apply_sync` / `apply_async` pipelines after visibility hooks; active-input permission dispatch, relation visibility, ORM predicates, and GraphQL error envelopes remain owned by those set modules and the finalizer rather than being duplicated here. Unresolved lazy references preserve `ImportError` at the primitive boundary and are wrapped as `ConfigurationError` by finalization.

## Verification

- `git --no-pager diff 00b080c3f227061fd13f8bc4876bcb88fffa3a50 -- django_strawberry_framework/sets_mixins.py` is empty; the target has no scoped source change to implement.
- Disposable probe `docs/review/temp-tests/sets_mixins/probe.py` passed for naming guards, callable lazy resolution, first-owner idempotency, direct-base precedence, cache hit behavior, and lifecycle attribute naming.
- Focused package tests passed:
  `tests/filters/test_sets.py::test_collect_related_declarations_honors_base_tombstone`,
  `tests/orders/test_base.py::test_related_order_bind_orderset_is_idempotent`,
  `tests/orders/test_base.py::test_related_order_accepts_unqualified_name_in_same_module`,
  `tests/orders/test_composition.py::test_filter_and_order_share_lazy_related_class_mixin_via_neutral_module`,
  `tests/orders/test_sets.py::test_metaclass_none_removal_survives_diamond_inheritance`,
  `tests/orders/test_sets.py::test_orderset_get_fields_caches_on_resolved_related_orders`,
  `tests/orders/test_sets.py::test_orderset_get_fields_does_not_cache_with_unresolved_string_target`,
  `tests/orders/test_inputs.py::test_clear_order_input_namespace_resets_orderset_subclass_binding_state`,
  `tests/filters/test_inputs.py::test_type_name_for_raises_for_no_word_character_field_path`, and
  `tests/filters/test_finalizer.py::test_registry_clear_clears_filter_input_namespace_and_helper_set`.
- Focused live GraphQL tests passed for scalar and absolute-path filters, nested visibility, forward-FK ordering, reverse-FK ordering, and optimizer cooperation in `examples/fakeshop/test_query/test_library_api.py`.
- Existing sync/async tests and callers were traced through `FilterSet.apply_sync` / `apply_async` and `OrderSet.apply_sync` / `apply_async`; no shared helper branch changes behavior between those paths.

## Improvements

### High

None.

### Medium

None.

### Low

None. No new duplication was found: the apparent near-matches in mutation/form naming, CLI imports, queryset lifecycle teardown, and shape-keyed input caches have different contracts and owners.

## Summary

The shared mixins correctly centralize naming, lazy related-target resolution, declaration collection, expansion caching, and lifecycle reset without leaking filter/order-specific policy into the neutral module. Direct probes, focused package tests, and representative live GraphQL paths support a zero-edit result.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files:** only this fresh review artifact. `django_strawberry_framework/sets_mixins.py` remains unchanged against the assigned baseline.
- **Permanent tests:** no production behavior changed, so no permanent test was added. Existing tests already pin the accepted contracts listed above.
- **Scratch/focused verification:** the disposable probe passed; all listed focused package and live GraphQL tests passed with `--no-cov`.
- **Formatter/linter:** not run because no source or test file was edited.
- **Rejected findings:** the collector's `inherit_from_bases` variation reflects the real upstream-metaclass difference; `forms/sets.py` naming and `mutations/sets.py` caches do not share this field-path expansion contract; `utils/imports.py` and management command import helpers do not provide this mixin's bound-module fallback or callable dispatch. None warranted a cross-file change.
- **Changelog:** not warranted for a zero-edit review.

## Independent verification (Worker 2)

- Re-read `sets_mixins.py` end to end and traced both consumers through `filters/base.py`, `filters/sets.py`, `filters/inputs.py`, `orders/base.py`, `orders/sets.py`, `orders/inputs.py`, both argument factories, `types/finalizer.py`, `utils/inputs.py`, `utils/permissions.py`, and the connection resolver pipeline. Owner binding, declaration precedence/tombstones, lazy class resolution, expansion guards/caches, generated-input naming, lifecycle reset, active permission dispatch, relation visibility, sync/async apply paths, and GraphQL error envelopes remain correctly owned by their family/shared utility callers.
- Independently proved the assigned scoped diff is empty: the working and baseline blob hashes for `django_strawberry_framework/sets_mixins.py` are both `4864c24ff3589a3c728c7b82052d938a0c329c02`; `git diff 00b080c3f227061fd13f8bc4876bcb88fffa3a50 -- django_strawberry_framework/sets_mixins.py` reports no paths.
- `uv run python docs/review/temp-tests/sets_mixins/probe.py` passed. The 13 artifact-listed focused package tests passed with `--no-cov`, covering naming guards, callable and unqualified lazy targets, neutral-mixin identity, declaration tombstones/diamonds, resolved/unresolved cache gates, and filter/order namespace reset.
- Additional focused tests passed with `--no-cov`: filter sync/async candidate behavior; active and nested permission dispatch (including dedup and denial); invalid-input `GraphQLError` envelopes; active related constraints and unregistered-target rejection; order async execution, sync-to-async permission dispatch, dedup, null/empty no-op behavior, and row-preserving to-many aggregation.
- Representative live `/graphql` HTTP tests passed with `--no-cov` for scalar and absolute-path filters, nested target visibility, forward-FK and reverse-FK ordering, and filter/order optimizer cooperation.
- Tried to disprove the zero-edit result through rejected consolidation candidates. The filter/order collector's inheritance switch is required by their different upstream metaclasses; forms and mutations use distinct field/input/cache contracts; import helpers and management-command imports do not share bound-module lazy resolution or set expansion state. No correctness, lifecycle, permission, sync/async, error-envelope, or DRY finding remains. No source, permanent test, or `CHANGELOG.md` file was edited.
