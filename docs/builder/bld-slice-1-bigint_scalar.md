# Build: Slice 1 — `BigInt` scalar + 64-bit integer field mappings

Spec reference: `docs/spec-deferred_scalars.md` (Slice checklist lines 74-138, Decision 1 lines 380-494, Decision 6 lines 579-592, Decision 7 lines 594-705, Decision 8 lines 708-710, User-facing API lines 712-729, Test plan categories 1-10 + 17 lines 786-803)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - `convert_scalar` MRO walk and null-widening branch in `django_strawberry_framework/types/converters.py:79-126`. Adding `BigIntegerField`/`PositiveBigIntegerField` entries to `SCALAR_MAP` (`converters.py:49-76`) automatically inherits both the choice-substitution branch (line 122) and the `T | None` widening branch (line 124) — no new logic is added inside `convert_scalar` itself for Slice 1.
  - Public-surface re-export pattern in `django_strawberry_framework/__init__.py:18-33`. The existing `__all__` tuple is alphabetized (verified by inspection: `DjangoOptimizerExtension`, `DjangoType`, `OptimizerHint`, `__version__`, `auto`, `finalize_django_types`); inserting `"BigInt"` keeps that ordering. The new `from .scalars import BigInt  # noqa: E402` import follows the same `noqa: E402` pattern already used at lines 18-22 (logger-first, subpackage imports second).
  - `__all__` pin test pattern in `tests/base/test_init.py:30-42`. The test compares against a `set(...)` literal, so adding `"BigInt"` to that set is the entire test-side change. Symmetric assertion already covers "no silent widening" — no new test file needed for the pin.
  - Test-isolation autouse fixture `_isolate_registry` at `tests/types/test_converters.py:37-47`. Per Decision 7's "Schema test fixture pattern" preamble (spec lines 637-639), new tests added inside `test_converters.py` inherit this autouse fixture automatically; no `conftest.py` work is required.
  - Synthetic-model-with-`app_label` pattern at `tests/types/test_converters.py:50-76` (session-scoped fixture) and `tests/types/test_converters.py:364-368` / `397-401` (in-function model declaration with `class Meta: app_label = "test_choice_enums"`). Slice 1 uses the in-function pattern — every BigInt mapping test pairs a synthetic model declaration with the `DjangoType` declaration in the same test function. Use a per-test or shared `app_label = "test_bigint"` (or similar) to keep the synthetic apps separated from the choice-enum fixtures.
  - The `convert_scalar(field, "OwnerType")` invocation pattern at `tests/types/test_converters.py:371` and `:384` is the existing precedent for testing scalar field mappings at the unit level (without going through `schema.execute_sync`). For Slice 1, the **field-mapping tests** named in the spec (`test_big_integer_field_maps_to_bigint_in_schema`, `test_positive_big_integer_field_maps_to_bigint_in_schema`, `test_big_auto_field_still_maps_to_int`, `test_big_integer_field_nullable_in_schema`) are spec-required to run via `schema.execute_sync` — they introspect the **generated GraphQL schema** to confirm the field is exposed as `BigInt` / `BigInt!` / `BigInt | None`. See Decision 7's "Schema test fixture pattern" (spec lines 637-657, especially step 6).

- **New helpers justified.**
  - **New module `django_strawberry_framework/scalars.py`.** Single responsibility: define the package's public scalars. Today only `BigInt` lives there; the spec's roadmap explicitly anticipates future scalars (Decision 6's `strawberry_config(...)` factory, `Upload` for TODO-ALPHA-027). A flat top-level module is the right shape per `docs/TREE.md`'s mirror rule — the existing flat top-level package files (`registry.py`, `exceptions.py`, `conf.py`) are the precedent. The module exports `BigInt`; internal helpers `_parse_bigint`, `_serialize_bigint`, and the module-level regex `_BIGINT_STRING_PATTERN` are leading-underscore-prefixed so they are excluded from any future `from .scalars import *` surface.
  - **No new helper inside `converters.py`.** The MRO walk + null-widening branch already covers `BigIntegerField` and `PositiveBigIntegerField` once their `SCALAR_MAP` entries land. Slice 1 only adds rows to the dict; no branching logic changes.
  - **New test file `tests/test_scalars.py`.** Flat-test mirror of the flat `django_strawberry_framework/scalars.py` per `docs/TREE.md`'s one-to-one mirror rule. Houses parser, serializer, top-level-import smoke, and subprocess-based deprecation-suppression tests — all of which are scalar-module concerns rather than converter concerns. No Django setup is required for the parser/serializer unit tests; the deprecation-suppression test spawns a subprocess that does its own import.
  - **Justifying the split between `tests/test_scalars.py` and `tests/types/test_converters.py`.** The split is **load-bearing** because of the spec's mirror-rule (Decision 7 lines 596-599): wire-format / parser / serializer tests live with the scalar module; field-mapping tests via `schema.execute_sync` live with the converter module. Without the split, a single file would mix two concerns (scalar internals vs. converter dispatch) and force the spec's mirror rule into a special-case.

- **Duplication risk avoided.**
  - **Risk #1: a generic `_int_to_string_scalar(name, *, parse_value, serialize)` helper is *not* extracted in Slice 1.** Slice 1 ships exactly one strict-string-encoded scalar (`BigInt`). The follow-up TODO-ALPHA-045 spec may rebuild the registration mechanism entirely, and an extracted helper now would be premature DRY — see Decision 6 lines 579-592 on the post-0.0.6 migration. If `0.0.6.x` ever adds a second string-encoded scalar (e.g., a separate `BigInt64` variant from Risks line 821, or `Upload`), extracting `_decimal_string_scalar(...)` becomes the right move. Recording the condition here so a future slice / spec can act on it.
  - **Risk #2: re-implementing the regex in Python form (`if value.startswith("+")`, `if value.startswith("0") and len(value) > 1`, etc.).** Spec Decision 1 pins the parser as a single `re.fullmatch(_BIGINT_STRING_PATTERN, value)` against `r"^(0|-?[1-9][0-9]*)$"`. The pattern is the contract. Implementation must use the spec's regex verbatim; per-test enumeration of rejection cases (`test_bigint_rejects_underscore_separator`, `test_bigint_rejects_leading_plus`, etc.) keeps the regex's coverage explicit rather than re-deriving the rejection rules in Python branching.
  - **Risk #3: the deprecation-suppression `with warnings.catch_warnings()` block being duplicated.** It lives in exactly one place — wrapping the `BigInt = strawberry.scalar(...)` definition in `scalars.py` (spec lines 465-476). Slice 4's `HStoreField` branch returns `strawberry.scalars.JSON` (a Strawberry-shipped scalar, not a package-defined one) and Slice 2's `JSONField` mapping uses the same, so no second suppression site is needed. Recorded so future scalar additions (Slice 3 / 4 / a `0.1.x` `Upload` slice) know the suppression filter is a single-site concern.
  - **Risk #4: the `BigInt`-from-`scalars.py` import being repeated in `__init__.py` and in `converters.py`.** Both legitimately import `BigInt`: `__init__.py` re-exports it; `converters.py` references it as a `SCALAR_MAP` value. These are two distinct call sites with different responsibilities (public surface vs. internal mapping). Not a duplication; the alternative (importing in only one site and re-exporting from there) would couple the converter's internal `SCALAR_MAP` to the public-export module, which is a worse shape.
  - **Risk #5: `tests/test_scalars.py` re-importing `BigInt` for every test.** Use one top-level `from django_strawberry_framework.scalars import BigInt, _parse_bigint, _serialize_bigint` import; tests reference the bound names. The top-level-import smoke test (`test_bigint_is_importable_from_top_level`) uses `from django_strawberry_framework import BigInt` explicitly because *that* re-import path is the contract being pinned.

- **Static helper observations** (from `docs/builder/shadow/django_strawberry_framework__types__converters.overview.md`): the file has three TODO comments at lines 32-47 (the `BigInt` / `ArrayField` / `JSONField` block). Slice 1 removes **only** the `BigInt` TODO (lines 32-39); Slice 2 removes the `JSONField` half of lines 45-47; Slices 3 and 4 remove the `ArrayField` TODO (lines 41-43) and the `HStoreField` half of lines 45-47 respectively. The overview's **Repeated string literals** section is `None.`, so there is no cross-file literal DRY signal to act on at this slice. The control-flow hotspots (`convert_scalar` 48 lines / 5 branches; `convert_choices_to_enum` 69 lines / 8 branches) are unchanged by Slice 1.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — another worker's pass may have shifted the file since this plan was written.

1. **Create `django_strawberry_framework/scalars.py`** (new file). Use the spec's verbatim definition at `docs/spec-deferred_scalars.md:385-477` (Decision 1, the entire `import re / import warnings / from typing import Any, NewType / import strawberry` header through the `warnings.catch_warnings()`-wrapped `BigInt = strawberry.scalar(...)` block). Do not paraphrase, re-derive, or simplify — the regex, the docstring rejection lists, the suppression filter's `message="Passing a class to strawberry.scalar"` substring, and the `_serialize_bigint` strict reject order are all spec contract.
   - Module docstring: a short paragraph anchoring the module's responsibility ("Public scalars defined by django-strawberry-framework. Today: `BigInt`. Future scalars land here.") — implementer's discretion on exact wording.

2. **Re-export `BigInt` from `django_strawberry_framework/__init__.py`** (`__init__.py:22-33`).
   - Add `from .scalars import BigInt  # noqa: E402` after the existing `from .types import ...` line at `__init__.py:22`. The `noqa: E402` follows the precedent at lines 18-22 (logger must be created first).
   - Insert `"BigInt"` into the `__all__` tuple at line 26-33 in alphabetical position (first member, before `"DjangoOptimizerExtension"`). The exact tuple is pinned in the spec at `docs/spec-deferred_scalars.md:78-87` — implementer must match that order exactly so the `tests/base/test_init.py` set-equality assertion passes.

3. **Update `tests/base/test_init.py`'s pinned `__all__` assertion** at `tests/base/test_init.py:35-42`. Add `"BigInt"` to the set literal. The set is unordered for assertion purposes but kept alphabetized for readability per the existing pattern.

4. **Extend `SCALAR_MAP` in `django_strawberry_framework/types/converters.py`** (`converters.py:49-76`):
   - Add `models.BigIntegerField: BigInt,` — placement: after `models.IntegerField: int,` (line 60) so 64-bit integer types cluster together (integer types are currently grouped lines 60-64). Implementer's discretion on exact line.
   - Change `models.PositiveBigIntegerField: int,` (line 64) → `models.PositiveBigIntegerField: BigInt,` per Decision 1 (spec line 492-493).
   - **Verify `BigAutoField` (line 51) stays mapped to `int`.** Per Decision 1 (spec line 493), no change.
   - Widen the dict's value-type annotation (`converters.py:49`): `SCALAR_MAP: dict[type[models.Field], type] = {` → `SCALAR_MAP: dict[type[models.Field], Any] = {`. Per Decision 8 (spec lines 708-710). `Any` is already imported on `converters.py:21`.
   - Add `from ..scalars import BigInt` to the imports block at `converters.py:23-30`. Place it after `from ..registry import registry` (line 28) and before `from ..utils.strings import pascal_case` (line 29) to keep first-party imports lexically grouped — implementer's discretion on exact placement within the first-party block.

5. **Remove the `BigInt` TODO comment** at `converters.py:32-39`. Do NOT remove lines 41-47 (the `ArrayField` and `JSONField`/`HStoreField` TODOs) — those are Slices 2, 3, 4.

6. **Create `tests/test_scalars.py`** (new file). Test list per the Slice 1 checklist at `docs/spec-deferred_scalars.md:93-127`:
   - **Serializer tests** (8 tests, spec lines 95-102):
     - `test_bigint_serializes_int_as_decimal_string`
     - `test_bigint_serializes_zero` — pins `_serialize_bigint(0) == "0"`
     - `test_bigint_serializes_negative_int_as_decimal_string`
     - `test_bigint_serializes_signed_int64_min` — `_serialize_bigint(-2**63) == "-9223372036854775808"`
     - `test_bigint_serializes_signed_int64_max` — `_serialize_bigint(2**63 - 1) == "9223372036854775807"`
     - `test_bigint_serialize_rejects_bool` — `True` and `False` both raise `TypeError`
     - `test_bigint_serialize_rejects_float` — `1.9`, `0.0` raise `TypeError`
     - `test_bigint_serialize_rejects_non_int_types` — `str`, `Decimal`, `None`, custom object all raise `TypeError`
   - **Parser positive cases** (7 tests, spec lines 104-110):
     - `test_bigint_parses_python_int`
     - `test_bigint_parses_python_zero` — `_parse_bigint(0) == 0`
     - `test_bigint_parses_decimal_string_to_int`
     - `test_bigint_parses_negative_decimal_string_to_int`
     - `test_bigint_parses_zero_string` — `_parse_bigint("0") == 0`
     - `test_bigint_parses_signed_int64_min_string` — pins `-9223372036854775808`
     - `test_bigint_parses_signed_int64_max_string` — pins `9223372036854775807`
   - **Parser negative cases** (10 tests, spec lines 112-122):
     - `test_bigint_rejects_python_bool` — both `True` and `False`
     - `test_bigint_rejects_python_float` — `1.9`, `0.0`, `-1.0`
     - `test_bigint_rejects_empty_string`
     - `test_bigint_rejects_whitespace_padded_string` — `" 123 "`, `"\t123"`
     - `test_bigint_rejects_non_decimal_string` — `"abc"`, `"1.9"`, `"1e3"`, `"0x10"`
     - `test_bigint_rejects_underscore_separator` — `"1_000"`, `"-1_000"`
     - `test_bigint_rejects_leading_plus` — `"+1"`, `"+0"`
     - `test_bigint_rejects_unicode_decimal_digits` — `"１２"`, `"-１"`
     - `test_bigint_rejects_leading_zeroes` — `"01"`, `"007"`, `"-01"`
     - `test_bigint_rejects_negative_zero` — `"-0"`
     - `test_bigint_rejects_none` — with docstring per spec line 122 explaining the path is reachable only through (a) non-nullable inputs and (b) direct unit-test calls.
   - **Public-export smoke** (1 test, spec lines 124-125):
     - `test_bigint_is_importable_from_top_level` — `from django_strawberry_framework import BigInt; assert BigInt is not None`.
   - **Deprecation suppression** (1 test, spec lines 126-127, and Decision 7 lines 679-704):
     - `test_package_import_does_not_emit_strawberry_deprecation_warning` — **subprocess-based**, runs `python -W error::DeprecationWarning -c "import django_strawberry_framework"` and asserts `returncode == 0`. Use the exact subprocess invocation from Decision 7's example block at spec lines 682-702.
   - **Imports at the top of `tests/test_scalars.py`**: `import subprocess`, `import sys`, `from decimal import Decimal`, `import pytest`, `from django_strawberry_framework import BigInt as _BigInt  # noqa: F401  # smoke-import target` (lazy-imported inside `test_bigint_is_importable_from_top_level` if importing at module level would cause Django setup issues; implementer's discretion), `from django_strawberry_framework.scalars import _parse_bigint, _serialize_bigint`. Note: do not import `BigInt` from `django_strawberry_framework.scalars` at top-level if doing so would trigger Django app-loading before pytest-django sets `DJANGO_SETTINGS_MODULE` — verify by running the focused test once during Worker 2's pass. The spec's existing tests (`tests/base/test_init.py`) already import from the top-level package without issue, so this is likely fine, but Worker 2 should confirm.

7. **Extend `tests/types/test_converters.py`** with the field-mapping tests at `docs/spec-deferred_scalars.md:127-138`. Eleven tests, all via `schema.execute_sync` per Decision 7's "Schema test fixture pattern" (spec lines 637-657):
   - `test_big_integer_field_maps_to_bigint_in_schema`
   - `test_big_integer_field_nullable_in_schema`
   - `test_positive_big_integer_field_maps_to_bigint_in_schema` — pins the changed behavior
   - `test_big_auto_field_still_maps_to_int`
   - `test_bigint_serializes_query_result_as_string_via_schema_execution`
   - `test_bigint_parses_string_argument_via_schema_execution`
   - `test_bigint_parses_int_argument_via_schema_execution`
   - `test_bigint_in_input_position_with_null_via_schema_execution`
   - `test_bigint_rejects_bool_argument_via_schema_execution`
   - `test_bigint_rejects_float_argument_via_schema_execution`
   - `test_bigint_resolver_returning_bool_raises_via_schema_execution`

   Pattern per test (spec lines 648-657):
   1. Define a synthetic Django model at module level (e.g., `_BigIntFixture`) with the relevant `BigIntegerField` / `PositiveBigIntegerField` / `BigAutoField` columns and `class Meta: managed = False; app_label = "test_bigint"`. One shared fixture model can host every field (one column per field type) — consolidate to keep the synthetic-app footprint small. Or use multiple smaller models if the per-test reasoning is clearer; implementer's discretion.
   2. Declare a `DjangoType` subclass over the fixture inside the test function (or via a module-level fixture if many tests share the shape — discretion).
   3. Call `finalize_django_types()`.
   4. Build a `strawberry.Schema` with a `Query` root exposing the type via a `@strawberry.field` resolver.
   5. For introspection tests: query `__type(name: "...") { fields { name type { kind name ofType { kind name } } } }` and walk the `kind / ofType` chain — note Decision 3 lines 167 + Decision 7 lines 805 warn that wrapping types (`NON_NULL`, `LIST`) have `name: None`, so introspection must navigate the chain explicitly.
   6. For wire-level round-trip tests: execute a query like `query { bigIntField }` against a resolver returning `2**62`; assert `result.data["bigIntField"] == "4611686018427387904"`.
   7. For input-position tests: execute a query like `query($val: BigInt!) { echo(val: $val) }` against a resolver that returns `val`; assert string/int variants accepted, bool/float variants rejected.
   8. The `test_bigint_resolver_returning_bool_raises_via_schema_execution` test: define a resolver returning `True` annotated as `BigInt`, execute, assert `result.errors` is non-empty and a `TypeError`-shaped exception surfaces. The exact GraphQL error wording is brittle; assert on `len(result.errors) > 0` and ideally on `"BigInt cannot serialize bool"` substring (from `_serialize_bigint`'s message at spec line 448).
   - The `_isolate_registry` autouse fixture at `test_converters.py:37-47` already covers registry-clear-on-enter/exit so the new tests get isolation for free.
   - Per Decision 7's M2 note (spec lines 641-646), the in-function model + sentinel-swap pattern is the natural fit — no need to introduce session-scoped fixtures unless pytest-xdist warnings surface.

### Test additions / updates

All tests are spec-required; see "Implementation steps" #6 and #7 for the full list. Summary by file:

- **`tests/test_scalars.py` (new)**: 27 tests total — 8 serializer + 7 parser-positive + 11 parser-negative + 1 top-level-import smoke + 1 subprocess-based deprecation-suppression. Assertion shapes:
  - Serializer positive: `_serialize_bigint(value) == expected_string`
  - Serializer negative: `with pytest.raises(TypeError): _serialize_bigint(value)`
  - Parser positive: `_parse_bigint(value) == expected_int`
  - Parser negative: `with pytest.raises(ValueError): _parse_bigint(value)` (the spec docstring at lines 406-417 pins `ValueError` as the reject signal)
  - Top-level-import smoke: `from django_strawberry_framework import BigInt; assert BigInt is not None` — type-shape assertions intentionally avoided per spec line 124-125.
  - Subprocess deprecation-suppression: `result = subprocess.run([sys.executable, "-W", "error::DeprecationWarning", "-c", "import django_strawberry_framework"], ...); assert result.returncode == 0, f"...{result.stderr}"`. Use the exact `timeout=15` from spec line 696.

- **`tests/types/test_converters.py` (extended)**: 11 schema-execution field-mapping tests added per the spec checklist at lines 127-138. All run via `schema.execute_sync(...)`. The existing autouse `_isolate_registry` fixture at lines 37-47 supplies registry cleanup; new tests inherit automatically. Assertion shapes:
  - Schema-shape tests: walk `__type` introspection's `kind / ofType` chain; assert `kind == "SCALAR"`, `name == "BigInt"` at the terminal level.
  - Wire-level tests: assert `result.data[...] == expected_string` for outbound; `result.data[...] == expected_int` for inbound through a resolver that returns its argument.
  - Reject-at-schema-boundary tests: assert `result.errors` is non-empty; ideally also assert on a substring of the error message (e.g., `"BigInt cannot serialize bool"`) — note GraphQL wraps custom exceptions in `GraphQLError` and the wrapping wording may shift between Strawberry versions, so prefer asserting on the message substring rather than the exception type. Implementer's discretion if the substring proves brittle in practice.

- **`tests/base/test_init.py` (extended)**: one-line update to the set literal at lines 35-42 — add `"BigInt"` to the set.

- **No temp/scratch tests anticipated.** The 11 schema-execution tests are spec-required and live as permanent tests in `tests/types/test_converters.py`. If Worker 3 needs `docs/builder/temp-tests/slice-1-bigint_scalar/` scratch to probe an edge case (e.g., a Strawberry version that emits a different deprecation message), record it as a temp-test disposition per Worker 3's brief — but no temp tests are pre-flagged here.

### Implementation discretion items

- **`tests/test_scalars.py`**: top-level `from django_strawberry_framework import BigInt` vs. lazy `import` inside the smoke test. Worker 2 picks based on whether top-level import triggers Django app-loading before pytest-django setup; functionally equivalent. The spec doesn't pin this.

- **Test-model declaration style for the 11 schema-execution tests in `tests/types/test_converters.py`**: one consolidated synthetic model hosting `BigIntegerField` + `PositiveBigIntegerField` + `BigAutoField` columns vs. per-test `class _BigIntFoo(models.Model): ...` declarations. Worker 2 picks based on which produces clearer test reading; the spec's Decision 7 M2 note (lines 641-646) explicitly leaves this to the implementer ("two precedents exist; pick deliberately"). The consolidated-model shape is the natural fit when a single fixture covers most tests; an in-function pattern shines when a test has unique field shape. Either is acceptable; do not introduce a session-scoped fixture unless pytest-xdist warnings surface.

- **Choice of `app_label` for the synthetic fixture**: `"test_bigint"` is suggested by the spec at line 646, but Worker 2 may pick a more specific value (e.g., `"test_scalars_bigint"`) if it improves grep-discoverability. The constraint is that it must not collide with `"test_choice_enums"` (the existing fixture's `app_label`).

- **`SCALAR_MAP` row placement for `models.BigIntegerField: BigInt,`**: anywhere within the integer-types cluster (current lines 60-64). The spec does not pin row order; Worker 2 picks the order that reads cleanest with the surrounding rows.

- **`from ..scalars import BigInt` placement in `converters.py`**: within the first-party imports block (current lines 26-30). The exact line is implementer's discretion.

- **Module docstring wording for the new `scalars.py`**: a one-paragraph description anchoring the file's responsibility. The spec doesn't pin exact wording.

- **Substring assertions in the reject-at-schema-boundary tests**: whether to assert on the exact `_serialize_bigint` message substring (`"BigInt cannot serialize bool"`) or only on `len(result.errors) > 0`. Worker 2 picks based on what survives Strawberry's `GraphQLError` wrapping in the current Strawberry version; document the choice in the build report.

Items NOT delegated (architectural; resolvable from spec or escalated if not):

- The `BigInt` definition mechanism (`strawberry.scalar(NewType(...))` with `warnings.catch_warnings()` filter) — pinned by Decision 1 verbatim, no discretion.
- The `_BIGINT_STRING_PATTERN` regex (`r"^(0|-?[1-9][0-9]*)$"`) — pinned by Decision 1, no discretion.
- The `_serialize_bigint` strict reject order (bool → int return → TypeError) — pinned by Decision 1 lines 433-451, no discretion.
- The `__all__` tuple exact membership and order — pinned by spec lines 78-87, no discretion.
- The split between `tests/test_scalars.py` and `tests/types/test_converters.py` (parser/serializer/smoke vs. schema-execution field mappings) — pinned by Decision 7 lines 596-599, no discretion.
- The subprocess-based deprecation-suppression test mechanism — pinned by Decision 7 lines 679-704 and explicitly contrasted against `importlib.reload`, no discretion.

### Notes for Worker 1 (final-verification self-handoff)

- After Worker 2 implements and Worker 3 reviews, re-check the **spec's status line** (`Status: draft (revision 10, post-feedback2 re-review)`). If the build cycle moves the spec from draft to shipped at Slice 6 archival, that transition is recorded in Slice 6's artifact, not Slice 1's. For Slice 1, the status line is accurate as drafted.
- Re-verify during final verification that no new `__all__` member was added to `django_strawberry_framework/__init__.py` beyond `"BigInt"`. The Slice 1 contract is exactly +1 public symbol.
- Spec lines 583, 716-729, and the FEATURES.md "Public exports" entry (FEATURES.md lines 22-31) all need to be consistent with each other after Slice 1+6. Slice 1 lands the code change; Slice 6 lands the FEATURES.md update. Confirm at integration pass that the cross-slice text is consistent.
- The TODO comment removal at `converters.py:32-39` should leave the surrounding TODOs (ArrayField, JSON/HStore) **untouched**. If Worker 2's diff also touches those TODOs, that is plan-vs-implementation drift and Worker 1 must reject during final verification.
- Carry-forward to Slice 3 / 4 planning: the sentinel-guarded branches in those slices land **inside** `convert_scalar`, not in a separate helper module. They follow Decision 4's sentinel pattern (spec lines 525-548) which is structurally distinct from Slice 1's flat-module `BigInt` pattern. No shared helper is anticipated, but Slice 3 and Slice 4 do share the `_FakeArrayField` / `_FakeHStoreField` test-double idiom — that's a Decision 7 contract, not a Slice-1 concern.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/scalars.py` — **new file**. Defines `_BIGINT_STRING_PATTERN`, `_parse_bigint`, `_serialize_bigint`, and the `warnings.catch_warnings()`-wrapped `BigInt = strawberry.scalar(NewType("BigInt", int), ...)`. Copied verbatim from spec Decision 1 (lines 385-477). Module docstring describes the file's responsibility plus a one-paragraph framing of `BigInt`'s arbitrary-precision nature and wire-format rationale.
- `django_strawberry_framework/__init__.py` — added `from .scalars import BigInt  # noqa: E402` after the optimizer hints import and before the types import; inserted `"BigInt"` as the first member of the `__all__` tuple (alphabetized).
- `tests/base/test_init.py` — added `"BigInt"` to the pinned `__all__` set literal in `test_public_api_surface_is_pinned`.
- `django_strawberry_framework/types/converters.py` — removed the `BigInt` TODO comment block (former lines 32-39); added `from ..scalars import BigInt` to the first-party imports; widened `SCALAR_MAP`'s annotation to `dict[type[models.Field], Any]` per Decision 8; inserted `models.BigIntegerField: BigInt,` after `models.IntegerField: int,`; changed `models.PositiveBigIntegerField: int,` to `models.PositiveBigIntegerField: BigInt,`. Left the `ArrayField` and `JSONField/HStoreField` TODOs untouched (Slices 2-4).
- `tests/test_scalars.py` — **new file**. 27 tests: 8 serializer (positive + negative), 7 parser positive, 11 parser negative, 1 top-level-import smoke, 1 subprocess-based deprecation-suppression regression.
- `tests/types/test_converters.py` — imported `BigInt, finalize_django_types` from the top-level package; added a `_walk_introspected_type` helper and a `_introspect_field_type` helper at the file's BigInt section. Added 11 schema-execution field-mapping tests per Slice 1 spec (lines 127-138).

### Tests added or updated

- `tests/test_scalars.py::test_bigint_serializes_int_as_decimal_string` — `_serialize_bigint(42) == "42"`.
- `tests/test_scalars.py::test_bigint_serializes_zero` — pins the `int.__bool__ is False` edge.
- `tests/test_scalars.py::test_bigint_serializes_negative_int_as_decimal_string` — negative integer round-trip.
- `tests/test_scalars.py::test_bigint_serializes_signed_int64_min` — pins int64-min boundary.
- `tests/test_scalars.py::test_bigint_serializes_signed_int64_max` — pins int64-max boundary.
- `tests/test_scalars.py::test_bigint_serialize_rejects_bool` — `True`/`False` raise `TypeError`.
- `tests/test_scalars.py::test_bigint_serialize_rejects_float` — `1.9`, `0.0` raise `TypeError`.
- `tests/test_scalars.py::test_bigint_serialize_rejects_non_int_types` — `str`, `Decimal`, `None`, custom obj all raise `TypeError`.
- `tests/test_scalars.py::test_bigint_parses_python_int` — `_parse_bigint(42) == 42`.
- `tests/test_scalars.py::test_bigint_parses_python_zero` — pins int-zero branch.
- `tests/test_scalars.py::test_bigint_parses_decimal_string_to_int` — string-form happy path.
- `tests/test_scalars.py::test_bigint_parses_negative_decimal_string_to_int` — negative string.
- `tests/test_scalars.py::test_bigint_parses_zero_string` — pins regex `(0|...)` first alternative.
- `tests/test_scalars.py::test_bigint_parses_signed_int64_min_string` — int64-min as string.
- `tests/test_scalars.py::test_bigint_parses_signed_int64_max_string` — int64-max as string.
- `tests/test_scalars.py::test_bigint_rejects_python_bool` — both bool values raise `ValueError`.
- `tests/test_scalars.py::test_bigint_rejects_python_float` — silent-truncation guard.
- `tests/test_scalars.py::test_bigint_rejects_empty_string` — empty string raises.
- `tests/test_scalars.py::test_bigint_rejects_whitespace_padded_string` — whitespace rejected.
- `tests/test_scalars.py::test_bigint_rejects_non_decimal_string` — `"abc"`, `"1.9"`, `"1e3"`, `"0x10"`.
- `tests/test_scalars.py::test_bigint_rejects_underscore_separator` — PEP-515 rejected.
- `tests/test_scalars.py::test_bigint_rejects_leading_plus` — `"+1"`, `"+0"`.
- `tests/test_scalars.py::test_bigint_rejects_unicode_decimal_digits` — `"１２"`, `"-１"`.
- `tests/test_scalars.py::test_bigint_rejects_leading_zeroes` — `"01"`, `"007"`, `"-01"`.
- `tests/test_scalars.py::test_bigint_rejects_negative_zero` — `"-0"`.
- `tests/test_scalars.py::test_bigint_rejects_none` — `None` raises; defense-in-depth docstring per spec.
- `tests/test_scalars.py::test_bigint_is_importable_from_top_level` — pins `from django_strawberry_framework import BigInt` succeeds.
- `tests/test_scalars.py::test_package_import_does_not_emit_strawberry_deprecation_warning` — subprocess test, exit code 0 under `-W error::DeprecationWarning`.
- `tests/base/test_init.py::test_public_api_surface_is_pinned` — extended set literal with `"BigInt"`.
- `tests/types/test_converters.py::test_big_integer_field_maps_to_bigint_in_schema` — `BigIntegerField` non-null appears as `BigInt!`.
- `tests/types/test_converters.py::test_big_integer_field_nullable_in_schema` — `BigIntegerField(null=True)` appears as `BigInt`.
- `tests/types/test_converters.py::test_positive_big_integer_field_maps_to_bigint_in_schema` — pins the changed `PositiveBigIntegerField → BigInt` behavior.
- `tests/types/test_converters.py::test_big_auto_field_still_maps_to_int` — `BigAutoField` still maps to `Int`.
- `tests/types/test_converters.py::test_bigint_serializes_query_result_as_string_via_schema_execution` — resolver returning `2**62` round-trips as `"4611686018427387904"`.
- `tests/types/test_converters.py::test_bigint_parses_string_argument_via_schema_execution` — string-form `BigInt!` argument round-trip.
- `tests/types/test_converters.py::test_bigint_parses_int_argument_via_schema_execution` — int-literal argument round-trip.
- `tests/types/test_converters.py::test_bigint_in_input_position_with_null_via_schema_execution` — nullable `BigInt` argument accepts `null` (Strawberry strips before parser).
- `tests/types/test_converters.py::test_bigint_rejects_bool_argument_via_schema_execution` — `bool` literal rejected at schema boundary.
- `tests/types/test_converters.py::test_bigint_rejects_float_argument_via_schema_execution` — `float` literal rejected at schema boundary.
- `tests/types/test_converters.py::test_bigint_resolver_returning_bool_raises_via_schema_execution` — resolver returning `True` surfaces `"BigInt cannot serialize bool"` substring in `result.errors`.

### Validation run

- `uv run ruff format .` — pass (99 files left unchanged on final run).
- `uv run ruff check .` — pass (All checks passed!).
- Focused tests (no `--cov*` flags):
  - `uv run pytest tests/types/test_converters.py tests/test_scalars.py tests/base/test_init.py --no-cov -q` — 57 passed. Two pre-existing warnings remain (unrelated `_Owner` model reuse in lines 364-403 of `test_converters.py`); no new warnings from Slice 1 code.

### Implementation notes

- **Test model naming for schema-execution tests** (in `tests/types/test_converters.py`): chose distinct PascalCase, non-underscore-prefixed model and type names per test (`BigIntOwner`/`BigIntOwnerType`, `BigIntNullableOwner`/`BigIntNullableOwnerType`, `PosBigIntOwner`/`PosBigIntOwnerType`, `BigAutoOwner`/`BigAutoOwnerType`, `BigIntQueryOwner`/`BigIntQueryOwnerType`). Why this shape: an underscore-prefixed class name like `_OwnerType` is preserved verbatim as the GraphQL type name by Strawberry's `to_camel_case`, but GraphQL `__type(name: "_OwnerType")` introspection returns the wrapping type cleanly only when names are valid identifiers without leading underscores. The plan permitted unique-`app_label`-per-test only on pytest-xdist warning; instead I solved the schema-introspection lookup by varying *class* names per test while keeping a single shared `app_label = "test_bigint"`. The existing in-file `_Owner` symbols (lines 364-403) are non-schema MRO unit tests and remain untouched.
- **`_introspect_field_type` / `_walk_introspected_type` helpers**: factored out the introspection query and the `kind/ofType` chain walk to keep each schema-shape test compact. Decision 7 (spec line 167) explicitly warns wrapping types have `name: None` so the helper walks until `ofType is None`. Why this shape: the alternative (asserting an exact-shape `dict` per test) would have repeated the chain literal across 4 tests; the helper makes the assertion target what each test cares about (terminal `SCALAR`/`name`) without hard-coding wrapper-shape literals.
- **`test_bigint_in_input_position_with_null_via_schema_execution`**: the resolver returns a plain `str` (`"null"` or `str(val)`), not a `BigInt`, because the test cares about the inbound parser receiving `None` rather than the outbound serializer. Returning `BigInt` would force the outbound serializer to fire on the `"null"` literal string and break with TypeError. Why this shape: the spec's test name pins the input-position contract; using `-> str` keeps the test focused on that contract without entangling the outbound path.
- **GraphQL field-name camelCase translation**: `PositiveBigIntegerField` field `big_pos` introspects as `bigPos` (Strawberry's default snake-to-camel transform). The introspection helper lookup uses `bigPos`, not `big_pos`, accordingly. Why this shape: the camelCase translation is Strawberry's default and the spec did not pin alternate config; matching the wire-side name keeps the test honest about what the schema actually exposes.
- **Terminal-introspection assertion shape**: assert separately on `terminal["kind"] == "SCALAR"` and `terminal["name"] == "BigInt"` (vs. dict-equality on `{"kind": "SCALAR", "name": "BigInt"}`). Why this shape: the introspection payload also carries `"ofType": None` at the terminal; dict-equality would break on the extra key. Decomposing into per-key asserts keeps the test robust without listing every key.
- **Subprocess deprecation test substring**: the suppression filter matches on the prefix `"Passing a class to strawberry.scalar"` per spec Decision 1 lines 466-469. Verified the subprocess test passes locally (returns 0 under `-W error::DeprecationWarning`).
- **Test ordering inside `tests/types/test_converters.py`**: appended the 11 BigInt schema-execution tests after the existing MRO subclass-resolution tests with a section comment marking the boundary. Helpers (`_walk_introspected_type`, `_introspect_field_type`) sit at the top of the BigInt section so they're adjacent to their callers.

### Notes for Worker 3

- No `scripts/review_inspect.py` shadow file was used during this pass — the slice's logic surface (a flat new module with two pure helpers + one assignment block; two-row `SCALAR_MAP` mutation; one TODO removal) fits the "no review-worthy logic" hint in BUILD.md's helper-skip rule. Worker 3 may choose to run the helper regardless given the new file `scalars.py` is +102 LOC.
- Focused tests run (without `--cov*` flags): `uv run pytest tests/types/test_converters.py tests/test_scalars.py tests/base/test_init.py --no-cov -q` → 57 passed. The two remaining warnings about `test_choice_enums._owner` are pre-existing (caused by tests at lines 364-403 reusing the `_Owner` class name across functions in the same `app_label`); they predate this slice.
- The schema-execution tests use **distinct PascalCase model + type names per test** with a shared `app_label = "test_bigint"`. The plan permitted in-function declaration with unique-`app_label`-per-test as a fallback; I went one level finer (unique class names) so introspection lookup by GraphQL type name resolves cleanly. See "Implementation notes" entry on test model naming for the rationale.
- The introspection query helper traverses up to 3 levels of `ofType` nesting. `BigInt!` is two levels (`NON_NULL → SCALAR`); `BigInt` (nullable) is one level (`SCALAR`). Slice 3's `list[T]` cases will need a fourth level of nesting — Slice 3's plan should re-evaluate or extend the helper.

### Notes for Worker 1 (spec reconciliation)

- **No spec drift discovered.** The plan's verbatim-Decision-1 code, the in-function synthetic-model pattern, the autouse `_isolate_registry` inheritance, and the subprocess deprecation test all worked as specified.
- **Minor naming choice (not drift, recorded for transparency)**: Decision 7 example at spec line 646 suggests `app_label = "test_bigint"` and the in-function model declaration style. The plan permitted unique class names; my implementation uses **per-test unique class names + a shared `app_label = "test_bigint"`** rather than per-test unique `app_label`s. This is the natural fit when each test needs a different field-shape but they all share a slice's conceptual namespace. If pytest-xdist warnings surface later, splitting the shared `app_label` per test is a cheap follow-up.
- **GraphQL field-name camelCase translation surfaced once** (`big_pos → bigPos` on `PositiveBigIntegerField`). Spec did not explicitly pin Strawberry's snake-to-camel default in the test recipe; not a gap since it's Strawberry's documented default, but Worker 1 may want to anchor the test recipe with one line clarifying the camelCase translation so future field-mapping tests for snake_case columns (e.g., Slice 3's `ArrayField` with multi-word column names) don't trip on it.
- **Spec Decision 7 fixture pattern step 4 (`finalize_django_types()`) is mandatory** — confirmed: omitting it causes Strawberry's `Schema(...)` to raise during construction (the `DjangoType` is not yet a Strawberry type). The 11 schema-execution tests all call it explicitly before `strawberry.Schema(...)`. No spec edit needed.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

#### `test_bigint_rejects_*` parser-negative tests use bare `pytest.raises(ValueError)` without `match=`

Eleven parser-negative tests in `tests/test_scalars.py:125-204` catch `ValueError` without a `match=` substring. The spec docstring (`scalars.py:32-42`) lists distinct reject reasons; `match=` strings would pin each branch to the message it produces (e.g. `match="does not accept boolean"` for bool, `match="cannot parse"` for unknown types, `match="requires a plain ASCII decimal"` for regex misses). Without `match=`, a regression that accidentally collapsed two error paths into one (e.g. `_parse_bigint(None)` falling through into the string-regex branch and raising a different message) would still pass the bool/float tests as long as some `ValueError` is raised. The cost of adding `match=` is one short string per test; the upside is that each test pins exactly which `raise` site fired.

```tests/test_scalars.py:125-130
def test_bigint_rejects_python_bool():
    """Both ``True`` and ``False`` raise ``ValueError``."""
    with pytest.raises(ValueError):
        _parse_bigint(True)
    with pytest.raises(ValueError):
        _parse_bigint(False)
```

Recommendation: optional polish. Worker 2 may either add `match=` substrings (matching the three distinct `ValueError(...)` message-shapes in `scalars.py:44-56`) or leave as-is and rely on the diversity of inputs (`True`, `1.9`, `"abc"`, `None`, etc.) to surface a regression. Test_scalars.py is a unit-test file with no DB cost, so the protection is cheap regardless. Not a rejection-grade finding because the diversity of inputs across the 11 negative tests already triangulates the reject paths in practice.

#### `test_bigint_rejects_bool_argument_via_schema_execution` and sibling reject tests only assert `len(result.errors) > 0`

Tests at `tests/types/test_converters.py:651-678` (bool + float schema-boundary rejects) assert `result.errors is not None` and `len(result.errors) > 0` without pinning the error wording or which side (parser vs serializer) fired. The companion `test_bigint_resolver_returning_bool_raises_via_schema_execution` at lines 681-699 does substring-assert on `"BigInt cannot serialize bool"` (the serializer message). The parser-side equivalent would assert on `"BigInt does not accept boolean values"` / `"BigInt cannot parse float"`. As-is, a regression that swapped the parser branch with the serializer one (or stopped firing the parser entirely and let bool/float fall through to a downstream coercion error in the resolver) would still leave `result.errors` non-empty. Adding the parser-message substring would tighten symmetry with the outbound test.

Recommendation: optional polish. The implementer's discretion item in the plan ("substring assertions in the reject-at-schema-boundary tests") explicitly grants Worker 2 leeway here; the outbound test already does the substring check, so the inbound asymmetry is a small consistency gap, not a contract bug.

### DRY findings

- **Slice-1 BigInt schema-execution tests share the synthetic-model + DjangoType + Query trio shape.** Tests at `tests/types/test_converters.py:449-570` (the four introspection-shape tests) repeat the four-step pattern: declare a `models.Model` subclass with `managed = False; app_label = "test_bigint"`, declare a `DjangoType` over it, call `finalize_django_types()`, build a one-field `Query`, introspect via `_introspect_field_type`. The repetition is structural (each test needs its own model + DjangoType + Query because the schema's `__type` name varies per test, and the `_isolate_registry` autouse fixture forces fresh registration each time) — extracting a `_make_one_field_schema(model_cls, field_name)` helper would tighten ~80 lines into ~30 but would also hide the model-declaration step that the spec (Decision 7) names as a reading-time discipline ("test models declare `class Meta: managed = False; app_label = ...`"). Recording as a deferred DRY candidate for the cross-slice integration pass: if Slices 2-4 repeat the same shape with ArrayField / HStoreField / JSONField models, a shared helper is worth extracting then.
- **Repeated string literals in `tests/types/test_converters.py`** (from the shadow overview): `"test_bigint"` (5x), `"NON_NULL"` (3x), `"4611686018427387904"` (2x). The `"test_bigint"` repetition is the `app_label` shared across BigInt-section models — promoting to a module-level constant (`_BIGINT_APP_LABEL = "test_bigint"`) would be a small DRY win but also a small readability hit (test models reading the literal inline is conventional in Django test code). The `"4611686018427387904"` literal lives in two tests both pinning `2**62`'s decimal form; deriving via `str(2**62)` in one of them would centralize the magic-number definition. None of these rise to a finding; recording so Slices 2-4 can keep the same pattern (or, if multiple slices add ~10 `app_label` repetitions across the file, a module-level constants block becomes the move).
- **`_BIGINT_STRING_PATTERN` is referenced only once inside `_parse_bigint`.** The plan called it out as a module-level constant for clarity; this is correct shape — the pattern is the contract Decision 1 pins, and pulling it out into a named constant makes future readers see the contract at the top of the file. Not a finding; recording as a deliberate non-DRY-violation (the alternative — inlining the regex in `_parse_bigint`'s body — would obscure the contract).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` adds exactly one new symbol (`BigInt`) to the import block and to the `__all__` tuple. The exact tuple after the change matches the spec's pinned `__all__` at `docs/spec-deferred_scalars.md:78-87`:

```python
__all__ = (
    "BigInt",
    "DjangoOptimizerExtension",
    "DjangoType",
    "OptimizerHint",
    "__version__",
    "auto",
    "finalize_django_types",
)
```

Authorized by the active spec; alphabetical ordering preserved. No silent surface widening.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### Scope-creep / collateral change check

Two files outside Slice 1's named scope appear in the working tree:

- `examples/fakeshop/apps/products/schema.py:147` — collapses `"description",   #` (three spaces) to `"description",  #` (two spaces) before the inline comment. Pure formatting.
- `examples/fakeshop/tests/test_schema.py:43-44, 68-69` — reflows two long-line constructor calls to multi-line form with trailing commas (the COM812 / line-length-110 pair).

Both are auto-applied by `uv run ruff format .`, which `AGENTS.md` mandates after every edit ("Run `uv run ruff format .` and `uv run ruff check --fix .` after every edit"). They are rule-driven collateral, not silent scope creep, and they contain no semantic change (verified by diff inspection: comment-indent only on `schema.py`; argument-reflow only on `test_schema.py`). Accept silently.

### What looks solid

- **Spec-verbatim `scalars.py`.** The new file at `django_strawberry_framework/scalars.py:1-103` is a near-letter-for-letter implementation of Decision 1 (spec lines 385-477): the regex `^(0|-?[1-9][0-9]*)$`, the strict parser reject order (bool → int → str-regex → fallthrough-ValueError), the strict serializer reject order (bool → int → fallthrough-TypeError), the `warnings.catch_warnings()` filter scoped tightly around the `BigInt = strawberry.scalar(...)` block, the suppression filter's `message="Passing a class to strawberry.scalar"` prefix. The docstrings include the spec's full reject-list enumerations so a future reader can verify the implementation against the contract without leaving the file.
- **Test coverage walks the spec checklist line-by-line.** All 28 tests named in the Slice 1 checklist at spec lines 93-127 are present in `tests/test_scalars.py` with the exact names called out by the spec, plus all 11 schema-execution tests at spec lines 127-138 are present in `tests/types/test_converters.py` with the exact names. The reject-paths cover every behavior Decision 1's parser docstring enumerates (bool, float, empty/whitespace-padded, non-decimal, underscores, leading-plus, leading-zero, `-0`, Unicode digits, None) plus the int64 boundary pins on both sides.
- **The subprocess-based deprecation regression test correctly avoids the `importlib.reload` trap** (spec lines 679-704). Verified the subprocess invocation matches spec lines 691-702 exactly: `[sys.executable, "-W", "error::DeprecationWarning", "-c", "import django_strawberry_framework"]` with `timeout=15` and a `result.returncode == 0` assertion whose failure message surfaces the stderr.
- **The `_introspect_field_type` / `_walk_introspected_type` helpers** at `tests/types/test_converters.py:420-446` are the right shape — they factor the introspection query and the wrapping-type chain walk so each schema-shape test only asserts what it cares about (terminal `kind` + `name`). Decision 7's "introspection navigation note" (spec line 167) is honored: wrapping types have `name: None`, so the helper walks until `ofType is None`.
- **The two TODO comments preserved at `converters.py:33-39`** (ArrayField and JSONField/HStoreField) are exactly the right scope discipline — those are Slices 2-4 work and the plan explicitly forbade touching them in Slice 1. No accidental cleanup.
- **`SCALAR_MAP` annotation widened to `Any`** (Decision 8) lands in the same change as the first non-`type` value (`BigInt`, a `ScalarWrapper`). No annotation lies; the widening is justified by the value it admits.

### Temp test verification

No temp test files were created during this review. The 27-test parser/serializer surface plus 11 schema-execution tests cover every spec-decision branch by direct reading; no behavior was unclear enough to need a probe. `docs/builder/temp-tests/slice-1-bigint_scalar/` was not used and remains empty.

### Notes for Worker 1 (spec reconciliation)

- **No spec edits needed for Slice 1.** Worker 2's "Notes for Worker 1" already flagged the GraphQL camelCase translation observation as a possible test-recipe clarification for Slices 3-4; that is a Worker 1 judgment call at the integration pass, not a Slice-1 contract gap.
- **The `_make_one_field_schema(...)` helper-extraction question** (under DRY findings above) is the right kind of decision for the cross-slice integration pass: if Slices 2-4 land with the same four-step shape (synthetic model → DjangoType → finalize → one-field Query), the integration pass is the natural moment to hoist the helper. Worker 1 may want to anchor that with a TODO note in Slice 1's artifact for itself.
- **Two pre-existing warnings about `test_choice_enums._owner` model re-registration** (mentioned in Worker 2's build report) are unrelated to Slice 1; they predate this change and trigger from `test_convert_scalar_subclass_with_null_widens_through_mro_resolution` / `test_convert_scalar_unknown_field_type_still_raises` re-using the `_Owner` class name. Out of scope for Slice 1 but worth noting if the integration pass aims at a clean warnings-summary line.
- **The shadow overview's "Repeated string literals" section for `scalars.py`** is `None.`, which is the expected shape for a 103-line module with one new symbol. No cross-file DRY pressure to act on at this slice.

### Review outcome

`review-accepted`. The slice implements Decision 1 verbatim, ships the spec-enumerated 28 + 11 tests, preserves Slices 2-4's TODO scope discipline, and contains exactly one new public symbol (authorized by the spec). The two Low findings are optional polish that the plan's "Implementation discretion items" explicitly delegated to Worker 2; neither rises to a contract gap or a behavior regression. Set artifact `Status:` to `review-accepted`.

---

## Final verification (Worker 1)

### DRY check across this slice and prior accepted slices

No prior accepted slices exist; this is a slice-local DRY pass per the build cycle.

Cross-checked against the shadow overviews under `docs/builder/shadow/`:

- `django_strawberry_framework__scalars.overview.md` — new module, 103 lines (Symbols: `_BIGINT_STRING_PATTERN`, `_parse_bigint`, `_serialize_bigint`, module-level `BigInt` assignment). Repeated string literals section is `None.`, confirming the planning DRY-risk #1 (no premature `_decimal_string_scalar(...)` extraction) and #3 (single-site suppression filter) hold in the shipped code.
- `django_strawberry_framework__types__converters.overview.md` — the BigInt TODO at the former lines 32-39 is gone; the ArrayField TODO (lines 41-43) and JSONField/HStoreField TODO (lines 45-47) are preserved, as required for Slices 2-4. The `SCALAR_MAP` mutation is two rows; `convert_scalar`'s branch structure is unchanged (49 lines / 5 branches, same hotspot signature as pre-slice).
- `tests__test_scalars.overview.md` — 27 tests, one new file with no cross-file repeated literals.
- `tests__types__test_converters.overview.md` — 11 BigInt-section schema-execution tests added with shared helpers `_walk_introspected_type` / `_introspect_field_type` (Worker 3's DRY finding noted this consolidation prevented the otherwise-likely chain-walk literal repetition across the 4 introspection tests).

Worker 3's three "DRY findings" entries are all deferred-to-integration-pass candidates, not slice-1 rejections:

1. The `_make_one_field_schema(...)` helper extraction is correctly deferred — slice-1 alone does not justify the helper, but if Slices 2-4 repeat the synthetic-model + DjangoType + Query trio shape, the integration pass is the natural moment to hoist it.
2. The `"test_bigint"` `app_label` literal repetition (5x) is small and conventional — recording as a watchpoint for Slices 2-4.
3. `"4611686018427387904"` magic-number literal (2x) is two occurrences in adjacent tests; not a finding.

No new duplication introduced relative to existing helpers in `types/converters.py`, `__init__.py`, or `tests/base/test_init.py`.

### Existing tests still pass

`uv run pytest tests/test_scalars.py tests/types/test_converters.py tests/base/test_init.py -x` — 57 passed, 2 pre-existing warnings (unrelated `test_choice_enums._owner` model re-registration from `test_convert_scalar_subclass_with_null_widens_through_mro_resolution` / `test_convert_scalar_unknown_field_type_still_raises`; these predate Slice 1 and were already called out by Worker 2 and Worker 3). No `--cov*` flags used. Focused run is green; the full sweep is deferred to the final test-run gate per BUILD.md.

### Spec reconciliation

No spec edit required. Reviewed:

- Spec status line (`Status: draft (revision 10, post-feedback2 re-review)`) accurately describes the spec's lifecycle relative to this slice; archival is Slice 6's job.
- Worker 2's `### Notes for Worker 1 (spec reconciliation)` section flags: no drift discovered; per-test unique class names (vs unique `app_label`) is a transparent naming choice within Decision 7's leeway; GraphQL camelCase translation is Strawberry's documented default and does not need spec anchoring at this slice.
- Worker 3's `### Notes for Worker 1 (spec reconciliation)` section flags: no spec edits for Slice 1; the helper-extraction question belongs to the cross-slice integration pass.
- Spec lines 78-87 (the pinned `__all__` tuple) match the shipped `__init__.py:25-33` and `tests/base/test_init.py:35-43` set literal exactly.
- The two `examples/fakeshop/...` files in the diff are ruff-format collateral per AGENTS.md's standing rule (verified by inspection: comment-spacing-only on `apps/products/schema.py`, COM812-driven multi-line reflow on `tests/test_schema.py`). Worker 3 already accepted them under "Scope-creep / collateral change check." No spec implications.
- The `M docs/builder/BUILD.md` is the pre-flight-baseline workflow refinement; ignored per the task brief.

### Final status

`final-accepted`. Artifact `Status:` line updated to `final-accepted` at the top of this file.

### Summary

Slice 1 shipped the `BigInt` scalar end-to-end: new module `django_strawberry_framework/scalars.py` with the strict `_parse_bigint` (regex `^(0|-?[1-9][0-9]*)$`) and `_serialize_bigint` (strict reject on `bool`, `float`, and all non-`int` types), `warnings.catch_warnings()`-scoped suppression of Strawberry's class-to-`scalar()` `DeprecationWarning`, public re-export through `__init__.py` (`"BigInt"` added to `__all__` in alphabetized position), `models.BigIntegerField: BigInt` plus `models.PositiveBigIntegerField: BigInt` (the latter changed from `int`) in `SCALAR_MAP`, `SCALAR_MAP`'s annotation widened to `dict[type[models.Field], Any]` per Decision 8, and the legacy `BigInt` TODO removed from `converters.py` (Slices 2-4 TODOs preserved). 38 tests added: 27 in the new `tests/test_scalars.py` (8 serializer + 7 parser-positive + 11 parser-negative + 1 top-level-import smoke + 1 subprocess-based deprecation-suppression regression) and 11 schema-execution field-mapping tests in `tests/types/test_converters.py`. `tests/base/test_init.py`'s pinned `__all__` set literal extended with `"BigInt"`. All 57 focused tests pass.

### Spec changes made (Worker 1 only)

None.
