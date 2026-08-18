# Review: `django_strawberry_framework/rest_framework/`

Status: verified

## Understanding

The package is a soft-DRF boundary: root package import and star import remain DRF-free, while named serializer surfaces resolve lazily. `sets.py` validates and binds serializer mutations; `inputs.py` generates lazy module-global input classes and reverse maps; `serializer_converter.py` defines the schema conversion contract; `resolvers.py` performs authorize-before-decode writes with frozen hooks, alias-pinned relation validation, sync/async parity, and optimizer-planned response re-fetch; `hook_context.py` owns immutable hook context/upload metadata.

## Verification

Read all five source modules, root `__init__.py` lazy exports, shared mutation/queryset/transaction helpers, fakeshop serializers/schema, package tests, and live products GraphQL tests. Baseline `2d34c332d9374c7c519dfffee61dfb18779cc963` had no scoped rest_framework changes. A focused probe reproduced scalar schema/runtime drift; all other audited boundaries were challenged by existing direct/live coverage.

## Improvements

### High

None.

### Medium

**Observation:** The integrated schema-generation/runtime-validation boundary did not carry or enforce scalar annotation and requiredness identity; only broad field kind was checked.  
**Evidence:** A schema scalar `str` and runtime DRF `IntegerField` passed `_assert_schema_runtime_agreement` before this cycle. The gap crossed `inputs.py` descriptor generation and `resolvers.py` runtime enforcement, so no single original module fully owned it.  
**Impact:** Introspection could promise a shape that the serializer did not implement, causing late validation failures and making custom schema-time field hooks unsafe to use.  
**Recommendation:** Make the generated reverse-map descriptor the immutable source of emitted annotation/effective requiredness, include injected fields' base annotation, and fail closed in the resolver before validation when runtime conversion or nullability/requiredness differs.  
**Proof:** New generated/injected drift regressions, existing agreement tests, 405 focused package tests, and 19 live `/graphql/` serializer tests.

### Low

None.

## Summary

The package integration now enforces shape agreement at the owning runtime boundary while preserving its existing soft-import, namespace, authorization, upload, transaction, and sync/async contracts.

## Implementation (Worker 1)

Changed `utils/inputs.py::InputFieldSpec`, `rest_framework/inputs.py`, `rest_framework/resolvers.py`, and `tests/rest_framework/test_resolvers.py`. The fix records generated/injected annotation metadata and checks runtime converter output plus effective requiredness before DRF validation. Validation passed: `uv run ruff format .`; `uv run ruff check --fix .`; `uv run pytest tests/rest_framework --no-cov` (405 passed); `uv run pytest examples/fakeshop/test_query/test_products_api.py -k 'serializer' --no-cov` (19 passed). No changelog entry is warranted. Unrelated concurrent dirty files, including `types/*` and `tests/types/*` surfaced by the mandated formatter, were preserved and are outside this review.

## Independent verification (Worker 2)

Status: verified. Re-traced all six `rest_framework/` modules, root lazy exports, shared write-pipeline/queryset/transaction callers, fakeshop serializer mutations, package tests, and live GraphQL tests against baseline `2d34c332d9374c7c519dfffee61dfb18779cc963`. The implementation is sound: soft-import and star-export laziness, namespace/cache reset, source/requiredness/nullability metadata, custom converter and choice-enum agreement, injected fields, nested opt-in/cycle/depth, authorization-before-decode, frozen hook/upload context, sync/async boundaries, alias pinning, rollback, and folder integration all remained coherent.

Evidence:
- `uv run pytest tests/rest_framework/test_soft_dependency.py tests/rest_framework/test_inputs.py tests/rest_framework/test_sets.py tests/rest_framework/test_converter.py tests/rest_framework/test_resolvers.py --no-cov` — 405 passed.
- `uv run pytest examples/fakeshop/test_query/test_products_api.py -k 'serializer' --no-cov` — 19 passed.
- `uv run pytest tests/rest_framework/test_resolvers.py -k 'async or alias or transaction or authorization or authorize or decode or upload or hook or frozen or source or relation_queryset or save_result or attestation or validator' --no-cov` — 78 passed.
- `uv run pytest tests/rest_framework/test_converter.py tests/rest_framework/test_inputs.py -k 'choice or custom or required or nullable or null or source or injected or nested or cycle or depth or namespace or materializ or cache' --no-cov` — 62 passed.
- Scratch probes under `docs/review/temp-tests/rest_framework/` independently proved choice and registered-custom annotation drift rejection plus ledger/parked-global reset — 4 passed.

No revision is needed; the rest_framework checklist can be checked.
