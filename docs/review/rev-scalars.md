# Review: `django_strawberry_framework/scalars.py`

Status: verified

## Understanding

`scalars.py` owns the package's custom `BigInt` scalar, Strawberry's built-in
`Upload` re-export, and the `strawberry_config()` factory. `BigInt` is a bare
`NewType` registered through a `ScalarDefinition` in `_PACKAGE_SCALAR_MAP`;
`_parse_bigint` accepts non-boolean Python integers and strict ASCII decimal
strings, while `_serialize_bigint` accepts only non-boolean Python integers and
always emits a decimal string. `strawberry_config()` returns a fresh
`StrawberryConfig`, merges consumer definitions through `extra_scalar_map`, and
rejects package-key collisions and direct `scalar_map=` ownership conflicts.

The package converter table in `types/converters.py` maps
`BigIntegerField` / `PositiveBigIntegerField` to `BigInt`, `JSONField` to
Strawberry `JSON`, and soft-imported PostgreSQL `ArrayField` / `HStoreField`
through sentinel branches. Choice-enum conversion, nullability, and unsupported
field diagnostics remain owned by the converter module rather than duplicated
in `scalars.py`. File/image read output and filesystem-path exposure are owned
by the converter/resolver layers; mutation, form, and DRF input builders each
map file/image inputs to the same built-in `Upload` scalar.

The fakeshop aggregate schema calls `strawberry_config()` before schema
construction. Its live scalar tests exercise JSON, UUID, date/time, decimal,
BigInt, nullable values, choice/filter input, file/image output, Upload
multipart input, and filesystem-path opt-in over `/graphql/`. Package tests
cover the PostgreSQL sentinel branches with isolated field doubles because the
SQLite fakeshop cannot persist those PostgreSQL-only columns.

## Verification

- `git --no-pager diff e76b4bab180ff22d45605814b3f9048eb710f9e8 -- django_strawberry_framework/scalars.py tests/test_scalars.py examples/fakeshop/test_query/test_scalars_api.py examples/fakeshop/test_query/test_scalars_filter_api.py` was empty; the target and its permanent tests had no baseline or concurrent edits.
- `uv run pytest tests/test_scalars.py --no-cov` passed: 48 tests.
- `uv run pytest tests/types/test_converters.py tests/test_scalars.py --no-cov` passed: 113 tests, covering BigInt, JSON, choices, nullable branches, ArrayField/HStoreField sentinels, and file/image output.
- `uv run pytest examples/fakeshop/test_query/test_scalars_api.py examples/fakeshop/test_query/test_scalars_filter_api.py examples/fakeshop/test_query/test_uploads_api.py --no-cov` passed: 43 live HTTP tests, including scalar wire formats, filter input, nullable columns, Upload multipart requests, and filesystem-path policy.
- `docs/review/temp-tests/scalars/probe_registration.py` passed `uv run ruff format`, `uv run ruff check --fix`, and `uv run python`: strict parser edge values, custom-map merge/collision errors, Upload registration, and sync/async BigInt execution all behaved as specified.
- Direct probes confirmed invalid BigInt resolver output raises a GraphQL error in both `execute_sync` and async `execute`, while nullable `BigInt` `None` serializes as GraphQL `null`.
- A broader mixed run also encountered one failure in the concurrently modified `tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol`; it concerns serializer-shape identity and is outside this target. No concurrent file was changed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The scalar implementation is internally coherent and its connected contracts
are covered at the strongest reachable tiers: live GraphQL HTTP for fakeshop
behavior and focused package tests for PostgreSQL-only and framework-internal
branches. No root-cause defect or worthwhile scalar-specific design change was
found, so this is a zero-edit cycle.

## Implementation (Worker 1)

None — zero-edit cycle.

- No production or permanent-test files were changed; the scoped target remains
  byte-for-byte unchanged from the review baseline.
- The ignored scratch probe at
  `docs/review/temp-tests/scalars/probe_registration.py` records the additional
  sync/async and custom-registration verification and passed formatting/linting.
- The broader serializer-input failure was preserved as concurrent,
  out-of-scope work; no workaround or test-only change was introduced.
- `CHANGELOG.md` was not touched; this zero-edit result does not merit a release
  note.

## Independent verification (Worker 2)

- The scoped baseline diff is empty for `django_strawberry_framework/scalars.py`,
  `tests/test_scalars.py`, and the connected live scalar/filter/upload test files:
  `git diff e76b4bab180ff22d45605814b3f9048eb710f9e8 -- <paths>` produced no output.
- Re-traced the package scalar map and connected converter/resolver contracts:
  JSON, UUID, date/time, decimal, strict BigInt parse/serialize and nullability;
  ArrayField/HStoreField sentinel dispatch and rejection branches; choice enum
  sanitization/cache/collision errors; FileField/ImageField output and storage
  guards; built-in Upload input mapping; and per-column filesystem-path opt-in.
  No production or permanent-test edits are needed.
- Focused verification passed: `uv run pytest tests/test_scalars.py --no-cov`
  (48 passed) and `uv run pytest tests/types/test_converters.py
  tests/types/test_resolvers.py --no-cov` (104 passed). Live HTTP verification
  passed: `uv run pytest examples/fakeshop/test_query/test_scalars_api.py
  examples/fakeshop/test_query/test_scalars_filter_api.py
  examples/fakeshop/test_query/test_uploads_api.py --no-cov` (43 passed).
- An independent custom probe passed strict parser/serializer edge rejection,
  custom-map merge and package-key collision errors, and synchronous plus
  asynchronous BigInt schema execution. Rejected design candidates were also
  checked: Upload remains Strawberry's default-registry scalar rather than a
  duplicate package map/wrapper, and the config factory remains fresh,
  explicit, and collision-owning.
- The Worker 1 artifact references
  `docs/review/temp-tests/scalars/probe_registration.py`, but that ignored
  scratch file is not present in this checkout; the inline probe above supplied
  the same independent evidence without creating a durable scratch file.
- The known unrelated concurrent failure remains unchanged:
  `uv run pytest tests/rest_framework/test_inputs.py --no-cov` reports
  `test_dedupe_serializer_input_shape_is_sole_cache_protocol` failing on
  serializer-class identity (`1 failed, 76 passed`). It is outside item 19 and
  was not absorbed or modified.

Zero-edit item 19 is complete and independently verified.
