# Review: `django_strawberry_framework/filters/base.py`

Status: verified

## Understanding

`filters/base.py` owns the Layer 1/2 filter primitives: typed/list/array/range filters, integer `in`/`range` safety wrappers, Relay `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter`, and the consumer-facing `RelatedFilter`. `filters/sets.py::FilterSet.filter_for_field` / `filter_for_lookup` select these classes; `filters/inputs.py::convert_filter_to_input_annotation` and `normalize_input_value` define their Strawberry/form shapes; `types/finalizer.py::_audit_globalid_filter_strategies` and owner binding establish the target definition and GlobalID strategy before schema use. `FilterSet.apply_sync` / `apply_async` then run the filters after visibility and related-queryset composition, while the optimizer receives the resulting queryset.

The GlobalID path decodes the Relay payload, validates the strategy-specific type name, rejects malformed and empty IDs, then applies the decoded ID to the Django lookup. Fakeshop Relay filtersets exercise own-PK and related GlobalID filters through live `/graphql/` requests (`examples/fakeshop/apps/products/filters.py`, `examples/fakeshop/apps/library/filters.py`, and their live query tests). The non-Relay integer `in`/`range` paths use the same field-coercion utility for backend-overflow safety. `RelatedFilter` lazy target resolution and queryset derivation are consumed by the recursive visibility/filter pipeline in `filters/sets.py`; `orders/base.py::RelatedOrder` is the sibling surface over the shared set-target mixin.

Upstream `graphene_django`'s GlobalID primitive decodes and delegates directly, but this package's Relay refetch boundary already proves a stronger contract in `django_strawberry_framework/relay.py::_coerce_pk_or_none`: a correctly shaped ID whose value cannot be prepared for the target field is treated as missing/invalid before ORM evaluation. The filter boundary had the parse/type checks but not that final field-value check.

## Verification

- Compared the target with dispatch baseline `4fd9bd048aa9fbdd881bb4e822b884a4a33d7370`; `base.py` was identical before this review.
- Read the full target, connected filter input/set/finalizer code, order twin, queryset coercion/visibility utilities, Relay encode/decode/refetch paths, fakeshop filter declarations/live queries, package tests, specs, and upstream `django-filter` / `graphene_django` implementations.
- Baseline focused validation before edits: `uv run pytest tests/filters/test_base.py --no-cov` — 89 passed.
- A live Django/GraphQL probe using a valid `library.genre:<non-integer>` GlobalID reproduced the defect: Django leaked `Field 'id' expected a number but got 'not-an-int'.` from queryset compilation.
- After the fix, the same live probe returned HTTP 200 with `extensions.code == "GLOBALID_INVALID"` and no ORM lookup for the invalid PK value.
- After edits: `uv run ruff format .`, `uv run ruff check --fix .`, `python -m py_compile django_strawberry_framework/filters/base.py examples/fakeshop/test_query/test_library_api.py`, and `git diff --check` all passed. Per repository instruction, pytest was not run after edits.

## Improvements

### High

None.

### Medium

#### Invalid typed GlobalID primary keys reached Django as raw values

- **Observation:** `_decode_and_validate_global_id` validated the GlobalID payload and target strategy but returned the decoded `node_id` string without coercing it against the resolved target model's primary-key field.
- **Evidence:** A live `allLibraryGenres(filter: { id: { exact: <valid library.genre:not-an-int ID> } })` query reached Django and raised `ValueError: Field 'id' expected a number but got 'not-an-int'.` The existing Relay node path already uses `utils/querysets.py::coerce_field_value_or_none` through `relay.py::_coerce_pk_or_none` to stop this class of error before ORM work.
- **Impact:** A correctly typed but invalid client value escaped the filter's documented `GLOBALID_INVALID` boundary and leaked a raw Django conversion error. Integer, UUID, and out-of-range IDs could similarly fail during query compilation instead of producing the stable coded GraphQL error.
- **Recommendation:** At the GlobalID filter decode boundary, when owner/target resolution supplies a real Django model field, coerce the decoded ID through the shared `coerce_field_value_or_none` utility. Reject an uncoercible result with `GraphQLError(..., extensions={"code": "GLOBALID_INVALID"})` before selecting the marked/unmarked queryset predicate; retain the existing node-id-only fallback for unbound unit filters.
- **Proof:** Implemented in `filters/base.py::_decode_and_validate_global_id`; added live acceptance coverage in `examples/fakeshop/test_query/test_library_api.py::test_library_genres_filter_typed_global_id_with_invalid_pk_raises_globalid_invalid`. Existing indexed malformed/empty/mixed GlobalID tests continue to cover the multi-value path, which uses the same decoder.

### Low

None.

## Summary

The target's filter primitives, empty-input semantics, strategy-aware GlobalID validation, non-pk `to_field` handling, queryset composition, and sync/async callers are otherwise coherent and covered by package plus fakeshop live tests. One input-boundary correctness defect was confirmed and fixed: resolved GlobalID node IDs are now field-coerced before Django lookup compilation, preserving the coded invalid-input contract.

## Implementation (Worker 1)

- **Status:** `fix-implemented`.
- **Production change:** `django_strawberry_framework/filters/base.py::_decode_and_validate_global_id` now uses the resolved target model's real primary-key `models.Field` and `utils/querysets.py::coerce_field_value_or_none`; invalid values raise `GLOBALID_INVALID` with list-index context when applicable, while unbound test filters preserve node-id-only fallback.
- **Permanent test:** `examples/fakeshop/test_query/test_library_api.py::test_library_genres_filter_typed_global_id_with_invalid_pk_raises_globalid_invalid` exercises the consumer-visible `/graphql/` endpoint.
- **Unchanged dispositions:** no changes to the already-correct empty-list contracts, integer overflow guards, non-pk `to_field` marker, `RelatedFilter`/`RelatedOrder` shared target machinery, or async visibility pipeline. No changelog update is warranted for this error-boundary hardening.
- **Scoped diff vs dispatch baseline:** only `django_strawberry_framework/filters/base.py` and `examples/fakeshop/test_query/test_library_api.py` contain Worker 1 changes. All unrelated dirty files were preserved.

## Independent verification (Worker 2)

- **Disposition:** verified; no revision-needed defect found.
- Re-traced `_decode_and_validate_global_id`, both GlobalID filter callers, `FilterSet` Relay filter generation, finalizer owner binding, the shared field coercer, non-pk `to_field` marker, and the live `/graphql/` schema path. The new coercion runs after strategy/type/empty-id validation and before any ORM predicate; valid integer IDs become `int`, valid UUID IDs become `UUID`, and unbound filters retain raw node-id-only fallback.
- `uv run pytest tests/filters/test_base.py --no-cov` — 89 passed. This covers strategy acceptance/rejection, malformed and wrong-type IDs, list index diagnostics, empty-list omission/match-none/complement semantics, and non-pk `to_field` single/multi predicates.
- `uv run pytest examples/fakeshop/test_query/test_library_api.py -k 'library_genres_filter_typed_global_id_with_invalid_pk_raises_globalid_invalid or library_genres_filter_malformed_own_pk_global_id_in_names_index or library_genres_filter_empty_id_scalar_global_id_raises_globalid_invalid' --no-cov` — 3 passed.
- `uv run pytest examples/fakeshop/test_query/test_library_api.py -k 'library_books_filter_by_relay_m2m_global_id or library_genres_filter_by_relay_own_pk_global_id_in_list or library_genres_filter_by_relay_own_pk_global_id_in_rejects_wrong_type or library_genres_filter_malformed_own_pk_global_id_in_names_index or library_genres_filter_empty_id_in_list_raises_globalid_invalid_at_index_0 or library_genres_filter_mixed_empty_id_in_list_rejects_whole_input_at_index_1' --no-cov` — 6 passed.
- A standalone Django probe against real `Genre` and UUID primary-key fields confirmed valid coercion, invalid-PK `GLOBALID_INVALID` before ORM evaluation, wrong typed-ID rejection, unbound fallback, list index reporting, and `[]` match-none semantics.
- **Scope proof:** compared the target and connected paths against dispatch baseline `4fd9bd048aa9fbdd881bb4e822b884a4a33d7370`; the accepted target change is limited to `django_strawberry_framework/filters/base.py` plus its live regression test in `examples/fakeshop/test_query/test_library_api.py`. Existing concurrent changes in unrelated source/test paths were not adopted or modified by this verification.
