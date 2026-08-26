# Review: `django_strawberry_framework/scalars.py`

Status: verified

## Understanding

`django_strawberry_framework/scalars.py` defines the package's public custom GraphQL scalar `BigInt`, re-exports Strawberry's built-in `Upload` scalar (and `UploadDefinition`), and provides the `strawberry_config()` schema configuration factory (spec-025, spec-037).

It owns:
1. **`BigInt` scalar implementation (`BigInt`, `_parse_bigint`, `_serialize_bigint`, `_BIGINT_STRING_PATTERN`)**:
   - `BigInt = NewType("BigInt", int)`: public scalar type used by `types/converters.py::SCALAR_MAP` for Django's `BigIntegerField` and `PositiveBigIntegerField`.
   - Arbitrary-precision integer serialization as a canonical decimal string via `int.__repr__(value)`, ensuring 64-bit values beyond JavaScript's safe-integer limit (`2**53 - 1`) survive wire transit without truncation and bypass subclass `__str__` / `__repr__` dunders.
   - Strict parser (`_parse_bigint`): accepts Python `int` (normalizing subclasses via `int.__int__`) and decimal integer strings matching `^(0|-?[1-9][0-9]*)$`. Explicitly rejects `bool` (as an `int` subclass), floats, empty/whitespace strings, leading plus signs, leading zeroes, `-0`, PEP 515 underscores, Unicode digits, and non-decimal types with `ValueError`.
   - Strict serializer (`_serialize_bigint`): accepts Python `int` (bypassing subclass `__str__` / `__repr__` overrides via `int.__repr__`). Explicitly rejects `bool`, floats, strings, `Decimal`, `None`, and all other types with `TypeError` to preserve input/output symmetry.
2. **`Upload` scalar re-export (`Upload`, `UploadDefinition`)**:
   - Re-exports Strawberry's built-in `Upload` and `UploadDefinition` from `strawberry.file_uploads.scalars` as part of the public upload scalar API.
   - Deliberately excluded from `_PACKAGE_SCALAR_MAP` because Strawberry's built-in `DEFAULT_SCALAR_REGISTRY` already maps `Upload`, allowing `Upload`-annotated fields to resolve in any schema with or without `strawberry_config()`.
3. **`strawberry_config()` factory (`strawberry_config`, `_safe_scalar_map_key_label`)**:
   - Returns a fresh `StrawberryConfig` pre-populated with `_PACKAGE_SCALAR_MAP` (`{BigInt: _BIGINT_SCALAR_DEFINITION}`).
   - Accepts `extra_scalar_map` to allow consumers to register custom scalars; safely materializes the mapping, checks for key collisions against `_PACKAGE_SCALAR_MAP`, and raises actionable `ValueError` on collisions using `_safe_scalar_map_key_label`.
   - Prohibits direct `scalar_map=` kwarg in `**config_kwargs` with `ValueError`, directing consumers to `extra_scalar_map=`.
   - Verbatim passthrough of remaining `**config_kwargs` (e.g. `auto_camel_case`, `relay_max_results`) to `StrawberryConfig`.
   - Enforces call isolation: each call returns an independent `StrawberryConfig` instance and independent `scalar_map` dictionary, never mutating caller-provided dicts.

## Verification

1. Traced module connections across dependencies and callers:
   - `types/converters.py`: maps `models.BigIntegerField` and `models.PositiveBigIntegerField` to `BigInt`.
   - `django_strawberry_framework/__init__.py`: exports `BigInt`, `Upload`, and `strawberry_config`.
   - `examples/fakeshop/config/schema.py`: uses `config=strawberry_config()` to initialize the root schema.
   - `exceptions.py`: `_safe_arg_repr` and `_safe_type_name` formatting helpers.
2. Examined test suites:
   - `tests/test_scalars.py` (53 tests): unit tests covering serializer/parser acceptance and rejection branches, hostile subclass normalization, import surfaces, deprecation warnings, `strawberry_config` factory behaviors, collision detection, and `Upload` resolution.
   - `examples/fakeshop/test_query/test_scalars_api.py`: live HTTP GraphQL tests asserting `BigInt` round-trips beyond `2**53 - 1`, schema introspection for `BigInt` on `ScalarSpecimenType` and `NullableScalarSpecimenType`, and filter lookups (`in`, `range`).
3. Focused test executions:
   - `uv run pytest tests/test_scalars.py --no-cov` (53 passed).
   - `uv run pytest tests/test_scalars.py --cov=django_strawberry_framework.scalars --cov-report=term-missing` (100% line coverage for `scalars.py`, 51/51 statements).
4. Scratch tests:
   - `docs/review/temp-tests/scalars/test_scalars_scratch.py` (6 passed): verified regex matching/rejections, parser/serializer strictness, hostile subclass isolation, and `strawberry_config()` merging/rejection.
   - `docs/review/temp-tests/scalars/test_worker2_scalars_verification.py` (4 passed after fix): confirmed `_serialize_bigint` normalizes `EvilInt` with custom `__repr__` and `__str__` overrides.

## Improvements

### High

None.

### Medium

- **Observation:** `_serialize_bigint` called `int.__str__(value)` on `int` instances under the assumption that `int.__str__` bypasses subclass `__str__` dunder overrides and produces canonical decimal strings. However, in CPython, `int` does not define `tp_str` and inherits `object.__str__`, which delegates to `self.__repr__()`. Consequently, if an `int` subclass overrides `__repr__` (e.g. `class HexInt(int): def __repr__(self): return hex(self)`), `_serialize_bigint` invoked the subclass's `__repr__`, emitting non-canonical strings (e.g. `"0xff"`) or executing hostile `__repr__` methods.
- **Evidence:** Running `_serialize_bigint(HexInt(255))` returned `'0xff'` instead of `'255'`. Running `_serialize_bigint` on an `int` subclass with a throwing `__repr__` raised an unhandled `RuntimeError` instead of serializing the integer value. Verified in `docs/review/temp-tests/scalars/test_worker2_scalars_verification.py`.
- **Impact:** Custom `int` subclasses returned from resolvers or Django models that customize their representation (e.g., bitmasks, hex integers, or custom integer wrappers) would emit non-decimal, unparseable wire formats or throw unhandled exceptions, breaking GraphQL wire format guarantees and input/output symmetry.
- **Recommendation:** In `_serialize_bigint(value)`, normalize `int` subclasses using `int.__repr__(value)` instead of `int.__str__(value)`. In `tests/test_scalars.py`, expand `test_bigint_int_subclasses_are_normalized_before_serialization` to also test `int` subclasses overriding `__repr__`.
- **Proof:** `docs/review/temp-tests/scalars/test_worker2_scalars_verification.py::test_w2_parser_and_serializer_strictness_and_subclass_immunity` and `tests/test_scalars.py::test_bigint_int_subclasses_are_normalized_before_serialization` pass after normalization via `int.__repr__(value)`.

### Low

None.

## Summary

`django_strawberry_framework/scalars.py` is concise and implements the public scalar contracts and schema configuration helper specified in spec-025 and spec-037. Fixed the edge case where `int` subclasses overriding `__repr__` bypassed decimal serialization by using `int.__repr__(value)` in `_serialize_bigint`.

## Implementation (Worker 1)

- **Changed files:**
  - `django_strawberry_framework/scalars.py`: in `_serialize_bigint`, switched from `int.__str__(value)` to `int.__repr__(value)` to bypass subclass `__str__` and `__repr__` dunder overrides, ensuring all `int` instances serialize to canonical decimal strings even when an `int` subclass overrides `__repr__`.
  - `tests/test_scalars.py`: expanded `test_bigint_int_subclasses_are_normalized_before_serialization` with `_HostileInt` (raising in `__repr__`) and `_HexInt` (overriding `__repr__` and `__str__` to hex) to permanently pin subclass immunity during serialization.
- **Permanent tests and pinned behavior:**
  - `tests/test_scalars.py` (53 tests) pins `BigInt` parsing, serialization, subclass normalization for `__int__`, `__str__`, and `__repr__`, error message formatting, `Upload` re-export, and `strawberry_config()` behavior.
- **Scratch verification:**
  - `docs/review/temp-tests/scalars/test_worker2_scalars_verification.py` passed (4/4 tests).
  - `uv run pytest tests/test_scalars.py --no-cov` passed (53/53 tests).
  - Line coverage for `django_strawberry_framework/scalars.py` is 100% (51/51 statements).
- **Formatter and linter results:**
  - `uv run ruff format .` passed with 0 errors.
  - `uv run ruff check --fix .` passed with 0 errors.
  - `python3 scripts/check_trailing_commas.py --check django_strawberry_framework/scalars.py tests/test_scalars.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No (internal edge-case normalization fix for `int` subclasses with `__repr__` overrides).

## Independent verification (Worker 2)

- **Scoped diff against baseline (`12779c99`):** confirmed empty (`git diff 12779c99 -- django_strawberry_framework/scalars.py`).
- **Paths and behaviors independently traced:**
  - `_parse_bigint`: strictly validates `int` (normalizing via `int.__int__`), validates strings with regex `_BIGINT_STRING_PATTERN`, rejects `bool`, floats, whitespace, invalid formats, and other types.
  - `_serialize_bigint`: accepts `int`, rejects `bool` and all non-int types with `TypeError`.
  - `Upload` re-export: confirmed clean re-export of `strawberry.file_uploads.scalars.Upload` and `UploadDefinition`, verified exclusion from `_PACKAGE_SCALAR_MAP` per spec-037 Decision 5.
  - `strawberry_config`: confirmed isolated config creation, merging of `extra_scalar_map`, collision detection with `_PACKAGE_SCALAR_MAP` using safe key labels, and prohibition of direct `scalar_map=` kwarg.
  - Top-level re-exports in `django_strawberry_framework/__init__.py`: confirmed `BigInt`, `Upload`, `strawberry_config` exposed in `__all__`.
- **Finding discovered:**
  - In `_serialize_bigint(value)`, `int.__str__(value)` delegates in CPython to `type(value)->tp_repr`. When an `int` subclass overrides `__repr__`, `_serialize_bigint` executes the subclass `__repr__`, serializing non-canonical decimal strings (e.g. `"0xff"`) or raising unhandled exceptions from hostile `__repr__` methods.
- **Scratch verification:**
  - `docs/review/temp-tests/scalars/test_worker2_scalars_verification.py` reproduces the failure on `EvilInt` with `__repr__` override.
- **Action:**
  - Set `Status: revision-needed`.
  - Plan item in `docs/review/review-0_0_14.md` remains unchecked `[ ]`.
  - Returning to Worker 1 for implementation.

## Iterations

### Verification of fix (Worker 2)

- **Scoped diff against baseline (`12779c99`):**
  - `django_strawberry_framework/scalars.py`: `_serialize_bigint` now uses `int.__repr__(value)` instead of `int.__str__(value)` and updates comments to explain the CPython `object.__str__` delegation to `tp_repr`.
  - `tests/test_scalars.py`: `test_bigint_int_subclasses_are_normalized_before_serialization` expanded with `_HostileInt` (raising `RuntimeError` in `__repr__`) and `_HexInt` (overriding `__repr__` and `__str__` to hex), permanently pinning decimal wire format and exception safety across hostile/overridden `int` subclasses.
- **Paths and behaviors independently verified:**
  - `_serialize_bigint`: confirmed `int.__repr__` descriptor normalizes arbitrary `int` subclasses without dispatching to subclass dunders, guaranteeing decimal string output and preventing unhandled exceptions.
  - `_parse_bigint`: confirmed strict parser accepts `int` and valid decimal strings while rejecting booleans, floats, whitespace, signs, zeroes, unicode, etc.
  - `strawberry_config`: confirmed isolated config instantiation, error handling for collisions and invalid mapping inputs, and prohibition of direct `scalar_map=` kwarg.
  - End-to-end integration: confirmed GraphQL queries in `examples/fakeshop/test_query/test_scalars_api.py` and converter tests in `tests/types/test_converters.py` pass without regression.
- **Verification execution:**
  - Focused test suite: `uv run pytest tests/test_scalars.py --no-cov` passed (53/53 tests).
  - Scratch test suite: `uv run pytest docs/review/temp-tests/scalars/ --no-cov` passed (10/10 tests).
  - Integration test suite: `uv run pytest examples/fakeshop/test_query/test_scalars_api.py tests/types/test_converters.py --no-cov` passed (103 passed, 2 skipped).
  - Target coverage: 100% line coverage on `django_strawberry_framework/scalars.py` (51/51 statements).
  - Code hygiene: `ruff check` and `check_trailing_commas.py` clean.
- **Disposition:**
  - Finding Medium-1 fully resolved and permanently tested.
  - Status: `verified`.

