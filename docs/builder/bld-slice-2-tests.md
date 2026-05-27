# Build: Slice 2 — Tests

Spec reference: `docs/spec-020-scalar_map_helper-0_0_7.md` (lines 42–48 for the slice sub-checks; lines 452–509 for the test plan; lines 363–381 for Decision 7 test-placement; lines 436–449 for edge-case pins)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - `tests/test_scalars.py` lines 1-16 — module docstring + existing import block (`subprocess`, `sys`, `Decimal`, `pytest`, `_parse_bigint`/`_serialize_bigint`). Slice 2 widens this block (adds `NewType` from `typing`; adds `strawberry`, `StrawberryConfig`, `ScalarDefinition`, top-level `BigInt`, top-level `strawberry_config`) rather than re-emitting a fresh import block. The existing `import pytest` is reused by the new `pytest.raises(ValueError | TypeError)` blocks. The existing `from django_strawberry_framework import BigInt` use inside `test_bigint_is_importable_from_top_level` (lines 212-221) is preserved as a runtime symbol fetch; the new tests promote `BigInt` to a top-of-file import so the factory and integration tests can reference it without re-importing.
  - `tests/test_scalars.py` lines 18-20, 46-48, 83-85, 120-122, 207-209, 224-226 — banner-comment style (`# ----` / `# Section name` / `# ----`). The new "`strawberry_config()` factory" section uses the same banner shape so the file reads consistently. The factory tests, the `**config_kwargs` passthrough tests, and the two integration tests live under three sub-banners inside that section, mirroring spec lines 475-501.
  - `tests/test_scalars.py::test_bigint_is_importable_from_top_level #"from django_strawberry_framework import BigInt"` — confirms `BigInt` re-exports cleanly today. Slice 2 leans on the same re-export and adds a parallel `strawberry_config` import; no new top-level export shape to validate.
  - `tests/test_scalars.py::test_package_import_does_not_emit_strawberry_deprecation_warning` (lines 229-252) — left UNCHANGED per spec line 45 (the subprocess-with-`-W error::DeprecationWarning` regression now pins the post-migration no-leak contract via the new registration shape rather than via the removed suppression block).
  - `tests/base/test_init.py::test_public_api_surface_is_pinned` (lines 30-44) — Slice 2 appends exactly one element (`"strawberry_config"`) to the pinned tuple at line 44, after `"finalize_django_types"`. Matches the spec line 448 final tuple shape character-for-character. The surrounding test's pinned-tuple structure (one entry per line, trailing comma per COM812 / AGENTS.md line 17) is preserved verbatim.
  - `tests/types/test_converters.py::_introspect_field_type`, `_walk_introspected_type` (lines 463-489) — helper functions reused by every migrated test in the BigInt section. No edit to either helper; the schema-construction line is the only delta inside each test.
  - `tests/types/test_converters.py` BigInt section in-function model declaration pattern (`class BigIntOwner(models.Model): ... class Meta: managed = False, app_label = "test_bigint"`) — reused verbatim per test; Slice 2 does not alter model declarations, only the `strawberry.Schema(query=Query)` → `strawberry.Schema(query=Query, config=strawberry_config())` line.
  - `strawberry.scalar(name="CustomScalar", serialize=str, parse_value=str)` — the spec-pinned shape (spec line 481) for a throwaway consumer scalar used by the merge / passthrough / collision / non-mutation tests. Declared locally per test so each test stays a single pytest item per Decision 7 (spec lines 366-367, "Single pytest item per test; no `pytest.mark.parametrize` fan-out").

- **New helpers justified.**
  - **No module-level test helper extracted.** The eight scalar-map factory tests, the five passthrough tests, and the two integration tests are each short (≤ 10 lines of body) and assert on different facets of the same factory call. A shared `_call_factory(...)` helper would obscure the test boundaries. Per Decision 7's no-`parametrize` policy (spec lines 366-367) and the established `tests/test_scalars.py` style (every existing test is a flat `def test_...():` with inline asserts), no helper is justified.
  - **A locally-declared `CustomScalar = NewType("CustomScalar", str)` and `custom_def = strawberry.scalar(name="CustomScalar", serialize=str, parse_value=str)` pair recurs across four tests** (`test_strawberry_config_merges_extra_scalar_map`, `test_strawberry_config_extra_scalar_map_does_not_mutate_caller_dict`, `test_strawberry_config_independent_call_returns_independent_instance`, `test_strawberry_config_combines_extra_scalar_map_and_config_kwargs`). Each test declares its own pair inside the test body (no module-level fixture) per Decision 7's single-pytest-item-per-test rule. The local declaration is two lines (`CustomScalar = NewType(...)`; `custom_def = strawberry.scalar(...)`) and keeps each test self-contained; consolidating into a `@pytest.fixture` would scatter the test's data across files and frustrate single-test-failure debugging. Worker 2 has discretion to choose between (a) declaring the pair at module level once (DRY-leaning) and (b) declaring it inside each test body (locality-leaning); the spec does not pin either, but the existing file style favors locality. Recommendation: in-test declaration.

- **Duplication risk avoided.**
  - The naive implementation could pin the `ValueError` collision message by exact-string equality. Spec line 483 pins substring assertions (`"BigInt"` AND `"cannot redeclare"`), NOT exact equality, because Worker 2 in Slice 1 split the recourse sentence into two adjacent implicit-concatenation literals for the 110-char line budget (`bld-slice-1-helper_module_and_bigint_redefinition.md` Implementation notes). The runtime message is character-identical to the spec's pinned shape, but a future cosmetic re-wrap should not require a Slice 2 test edit. Worker 2 asserts on substrings only.
  - The naive implementation could assert on `result.auto_camel_case` for `test_strawberry_config_forwards_auto_camel_case_kwarg`. The spec at line 490 EXPLICITLY corrects this — `auto_camel_case` is a dataclass `InitVar` on `StrawberryConfig` (verified at `.venv/lib/python3.10/site-packages/strawberry/schema/config.py::StrawberryConfig #"auto_camel_case: InitVar[bool]"`), and `__post_init__` applies the value to `name_converter.auto_camel_case`, leaving `cfg.auto_camel_case` itself as `None`. Worker 2 asserts on `result.name_converter.auto_camel_case is False` / `is True`, NOT on `result.auto_camel_case`.
  - The naive implementation could parametrize the eight scalar-map tests into one `pytest.mark.parametrize(...)`-driven test. Decision 7 (spec lines 366-367) explicitly forbids parametrize fan-out so the pytest item count matches collection output unambiguously and aligns with the precedent in spec-018 / spec-019. Worker 2 writes 15 flat `def test_...():` functions.
  - The naive implementation could add a third integration test for the `test_bigint_in_input_position_with_null_via_strawberry_config_schema` case. The spec at lines 500-501 pins exactly TWO integration tests (`test_bigint_serializes_int_via_strawberry_config_schema`, `test_bigint_parses_decimal_string_via_strawberry_config_schema`). The null-input behavior is already pinned by `tests/types/test_converters.py::test_bigint_in_input_position_with_null_via_schema_execution` (one of the 10 sites migrated in this slice), so duplicating it in `tests/test_scalars.py` would be defense-in-depth on top of an already-defense-in-depth migration. Worker 2 writes exactly two integration tests.
  - The naive implementation could migrate every `strawberry.Schema(query=Query)` site in `tests/types/test_converters.py` (the file has 30+ sites; see line counts via `grep -n "strawberry.Schema(query=Query)"`). Spec line 47 pins exactly 10 sites — the BigInt-resolving subset of the BigInt-section banner; sites whose schemas resolve to upstream `Int` (`test_big_auto_field_still_maps_to_int` at line 615) or to JSONField / Choice-enum / Relation / Boolean scalars (lines 777+) are explicitly NOT migrated. Worker 2 follows the spec's pinned site list verbatim and does not touch any other `strawberry.Schema(query=Query)` line in the file.
  - The naive implementation could update the existing `test_package_import_does_not_emit_strawberry_deprecation_warning` to point at the new registration path or rename it. Spec line 45 pins that this test is UNCHANGED (the subprocess shape still validates the post-migration no-leak contract). Worker 2 does not touch this test.
  - The naive implementation could rewrite the `tests/test_scalars.py` module docstring from scratch. Spec line 48 pins "preserve the existing delegation sentence" and "APPEND" the new sentence; the suggested rewrite preserves the schema-execution-delegation context and adds the integration-tests acknowledgement. Worker 2 keeps the existing first paragraph verbatim and appends the new sentence per the spec's suggested wording (Worker 2 has discretion on exact phrasing per Decision 7's "Worker 2 has discretion on exact phrasing" allowance).

- **Static inspection helper.** Run on three files this slice extends:
  - `tests/test_scalars.py` (252 source lines, no logic — pure test file): ran helper at planning; overview at `docs/shadow/tests__test_scalars.overview.md`. No control-flow hotspots, no Django/ORM markers, 2 repeated string literals (the `int64_max` / `int64_min` decimal strings, already justified by spec-013 wire-format pins). The helper output confirms the existing file's style is flat `def test_...():` with inline asserts — Slice 2's new tests follow the same shape.
  - `tests/types/test_converters.py` (1735 source lines, over the 150-line threshold; under `tests/types/` which is NOT the same as `django_strawberry_framework/types/`, so the path-based trigger does NOT apply — only the line-count threshold). Ran the helper at planning; overview at `docs/shadow/tests__types__test_converters.overview.md`. No new control-flow hotspots introduced by the migration (the 10 affected sites are leaf-level `strawberry.Schema(query=Query)` line edits inside existing test bodies). No new Django/ORM markers, no new TODOs.
  - `tests/base/test_init.py` (44 source lines, below the 150-line threshold) — helper SKIPPED per BUILD.md "When to run the helper during build" criteria. The one-line edit is a single-element append to the pinned tuple; no logic added.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — another worker's pass may have shifted the file since this plan was written.

1. **`tests/test_scalars.py` — widen imports.**
   - Replace the existing import block at `tests/test_scalars.py` lines 10-16 to add the new imports. Final shape (the spec's pinned import block at spec lines 462-471):
     - Existing: `import subprocess` (line 10), `import sys` (line 11), `from decimal import Decimal` (line 12), blank line, `import pytest` (line 14), blank line, `from django_strawberry_framework.scalars import _parse_bigint, _serialize_bigint` (line 16).
     - Add: `from typing import NewType` (after `from decimal import Decimal`; stdlib block).
     - Add: `import strawberry` (third-party block, after `import pytest`).
     - Add: `from strawberry.schema.config import StrawberryConfig` (third-party block).
     - Add: `from strawberry.types.scalar import ScalarDefinition` (third-party block).
     - Widen: `from django_strawberry_framework.scalars import _parse_bigint, _serialize_bigint` line stays; ADD a separate first-party import line `from django_strawberry_framework import BigInt, strawberry_config` to surface the public symbols the new tests reference. The pre-existing inline `from django_strawberry_framework import BigInt` inside `test_bigint_is_importable_from_top_level` (line 219) stays as-is — the test deliberately uses an in-function import to pin the import-time contract.
   - Discretion: Worker 2 chooses the per-import-line ordering inside the third-party block; ruff format's import sorter may rewrite. Whatever ruff format settles on is acceptable.

2. **`tests/test_scalars.py` — rewrite the module docstring (spec line 48).**
   - Edit the existing module docstring at lines 1-8. PRESERVE the existing delegation sentence (the current docstring's "Wire-level / schema-execution behavior lives in ``tests/types/test_converters.py`` per the [`docs/TREE.md`](../docs/TREE.md) mirror rule (scalar internals here; converter dispatch there).").
   - APPEND a new sentence acknowledging the two new integration tests. Spec line 48's suggested rewrite: `"Additionally, two strawberry.Schema(query=..., config=strawberry_config()) integration tests pin the post-migration BigInt round trip end-to-end (test_bigint_serializes_int_via_strawberry_config_schema, test_bigint_parses_decimal_string_via_strawberry_config_schema)."`. Worker 2 has discretion on exact phrasing (Decision 7); the contract is "the docstring acknowledges the two integration tests live in this file."

3. **`tests/test_scalars.py` — add the new "`strawberry_config()` factory" section at the bottom of the file.**
   - Append the new section AFTER `test_package_import_does_not_emit_strawberry_deprecation_warning` (current line 252). The section uses the same banner-comment style as existing sections (lines 18-20 / 46-48 / etc.):
     ```
     # ---------------------------------------------------------------------------
     # strawberry_config() factory — scalar-map tests
     # ---------------------------------------------------------------------------
     ```
   - Inside the section, write the eight scalar-map factory tests in spec order (spec lines 477-484). Each test is a flat `def test_strawberry_config_<...>():` with body ≤ 10 lines; assertions match the spec's per-test contracts verbatim. See "Test additions / updates" below for the per-test list.

4. **`tests/test_scalars.py` — add the `**config_kwargs` passthrough sub-section.**
   - After the eight scalar-map tests, append a second banner:
     ```
     # ---------------------------------------------------------------------------
     # strawberry_config() factory — **config_kwargs passthrough tests
     # ---------------------------------------------------------------------------
     ```
   - Write the five passthrough tests in spec order (spec lines 490-494). Critical: `test_strawberry_config_forwards_auto_camel_case_kwarg` asserts on `result.name_converter.auto_camel_case` (NOT `result.auto_camel_case`) per spec line 490 — verified against upstream at `.venv/lib/python3.10/site-packages/strawberry/schema/config.py::StrawberryConfig.__post_init__ #"self.name_converter.auto_camel_case = auto_camel_case"` (line 56 of the upstream file).

5. **`tests/test_scalars.py` — add the integration-tests sub-section.**
   - After the five passthrough tests, append a third banner:
     ```
     # ---------------------------------------------------------------------------
     # strawberry_config() factory — integration tests (schema round-trip)
     # ---------------------------------------------------------------------------
     ```
   - Write the two integration tests in spec order (spec lines 500-501). Each constructs a minimal `strawberry.Schema(query=..., config=strawberry_config())` with a `BigInt`-annotated resolver, runs `schema.execute_sync(...)`, and asserts on the JSON response. See "Test additions / updates" for the per-test contract.

6. **`tests/base/test_init.py` — append `"strawberry_config"` to the pinned `__all__` tuple.**
   - At `tests/base/test_init.py::test_public_api_surface_is_pinned #"finalize_django_types"` (current line 43), add `"strawberry_config",` as a new tuple element after `"finalize_django_types",` and before the closing `)` on line 44. The final tuple matches the spec's pinned shape at spec line 448:
     ```python
     assert django_strawberry_framework.__all__ == (
         "BigInt",
         "DjangoListField",
         "DjangoOptimizerExtension",
         "DjangoType",
         "OptimizerHint",
         "__version__",
         "auto",
         "finalize_django_types",
         "strawberry_config",
     )
     ```
   - This closes the expected-failure handoff from Slice 1 (per Slice 1 artifact `### Notes for Worker 3` / final verification's focused pytest run: 31 passed, 1 expected-fail).

7. **`tests/types/test_converters.py` — widen the import line.**
   - At `tests/types/test_converters.py #"from django_strawberry_framework import BigInt, DjangoType, finalize_django_types"`, widen to `from django_strawberry_framework import BigInt, DjangoType, finalize_django_types, strawberry_config`. Verify against the current file before editing — the import line currently reads `from django_strawberry_framework import BigInt, DjangoType, finalize_django_types` (verified via `grep -n "from django_strawberry_framework import" tests/types/test_converters.py`).
   - The new symbol's alphabetical position is at the end (`f` < `s`); ruff's import sorter may rewrite. Whatever ruff settles on is acceptable.

8. **`tests/types/test_converters.py` — migrate the 10 BigInt-section schema sites.**
   - At each of the 10 sites pinned by spec line 47, change `schema = strawberry.Schema(query=Query)` → `schema = strawberry.Schema(query=Query, config=strawberry_config())`. The 10 sites and their current line numbers (verified via `grep -n "strawberry.Schema(query=Query)" tests/types/test_converters.py` filtered to the BigInt section between lines 452-776):
     - `test_big_integer_field_maps_to_bigint_in_schema` (current line 546)
     - `test_big_integer_field_nullable_in_schema` (current line 578)
     - `test_positive_big_integer_field_maps_to_bigint_in_schema` (current line 607)
     - `test_bigint_serializes_query_result_as_string_via_schema_execution` (current line 670)
     - `test_bigint_parses_string_argument_via_schema_execution` (current line 685)
     - `test_bigint_parses_int_argument_via_schema_execution` (current line 702)
     - `test_bigint_in_input_position_with_null_via_schema_execution` (current line 719)
     - `test_bigint_rejects_bool_argument_via_schema_execution` (current line 734)
     - `test_bigint_rejects_float_argument_via_schema_execution` (current line 749)
     - `test_bigint_resolver_returning_bool_raises_via_schema_execution` (current line 766)
   - **NOT migrated** (sentinel guard against accidental over-migration): `test_big_auto_field_still_maps_to_int` (current line 639) lives inside the BigInt section banner but its schema resolves to upstream `Int` (`assert terminal["name"] == "Int"` at current line 644); the `BigAutoField → ID` resolution path never touches `BigInt`. Worker 2 visually confirms the assertion target before deciding to migrate each site — any test whose terminal scalar name is `"Int"` or `"JSON"` is NOT migrated.
   - **NOT migrated** (section boundary): every `strawberry.Schema(query=Query)` site at or after current line 812 is in the JSONField / Choice-enum / Relation / Boolean sections per spec line 47 ("The JSONField/Choice-enum/Relation/Boolean tests in later sections are likewise not migrated").

9. **Formatting sweep.** After all edits, Worker 2 runs `uv run ruff format .` and `uv run ruff check --fix .` per `AGENTS.md` line 15 / `START.md` line 26. The 110-char line length applies — the longest expected new lines are the `strawberry.Schema(query=Query, config=strawberry_config())` migration lines in `tests/types/test_converters.py` (62 characters; well under 110). The new factory-test bodies are short and well within the budget. If ruff format rewraps any line, that is fine; the contract is the test behavior, not the source layout.

10. **Validation run.** Per AGENTS.md line 14 / START.md line 24 ("Do not run `pytest` after every change"), Worker 2 does not run the full suite. Worker 2 MAY run a focused invocation against the new tests + the migrated tests to confirm pass/fail at the per-test level:
    ```shell
    uv run pytest --no-cov tests/test_scalars.py tests/base/test_init.py tests/types/test_converters.py
    ```
    The `--no-cov` flag is REQUIRED per BUILD.md "Coverage is the maintainer's gate, not a worker's tool" + Worker 1 role file "no `--cov*` flags". Worker 2 records the focused run's exit code in the build report's `### Validation run` block. No coverage flag may appear in the command.

### Test additions / updates

Per spec lines 475-501 verbatim. Each test is one pytest item (no parametrize). Test list with one-line contract:

**Eight scalar-map factory tests** (spec lines 477-484):

- `test_strawberry_config_returns_strawberry_config_instance` — pins `isinstance(strawberry_config(), StrawberryConfig)`; the return-type contract from Decision 2.
- `test_strawberry_config_default_scalar_map_includes_bigint` — pins `BigInt in result.scalar_map`, `isinstance(result.scalar_map[BigInt], ScalarDefinition)`, `result.scalar_map[BigInt].name == "BigInt"`; the package-default registration from Decision 3.
- `test_strawberry_config_accepts_none_extra_scalar_map` — pins that explicit `extra_scalar_map=None` is identical to the no-argument default (`len(result.scalar_map) == 1`; `BigInt in result.scalar_map`).
- `test_strawberry_config_accepts_empty_extra_scalar_map` — pins that `extra_scalar_map={}` is identical to `None` (edge case at spec line 440).
- `test_strawberry_config_merges_extra_scalar_map` — declares local `CustomScalar = NewType("CustomScalar", str)` and `custom_def = strawberry.scalar(name="CustomScalar", serialize=str, parse_value=str)`; asserts `len(result.scalar_map) == 2`, both `BigInt` and `CustomScalar` present, `result.scalar_map[CustomScalar] is custom_def`. Pins the merge contract from Decision 2.
- `test_strawberry_config_extra_scalar_map_does_not_mutate_caller_dict` — declares `caller_dict = {CustomScalar: custom_def}` and `before = dict(caller_dict)`; calls factory; asserts `caller_dict == before`. Pins the no-side-effect contract from spec line 441.
- `test_strawberry_config_collision_with_package_scalar_raises_value_error` — declares `alt_def = strawberry.scalar(name="AltBigInt", serialize=str, parse_value=int)`; calls factory with `extra_scalar_map={BigInt: alt_def}` inside `pytest.raises(ValueError) as excinfo`; asserts the exception message contains substring `"BigInt"` AND substring `"cannot redeclare"`. Per "DRY analysis" above, substring-only — NO exact-string equality (the recourse sentence is wrapped across two source-literal lines per Slice 1's implementation notes).
- `test_strawberry_config_independent_call_returns_independent_instance` — calls factory twice into `c1, c2`; asserts `c1 is not c2` AND `c1.scalar_map is not c2.scalar_map`. Mutates `c1.scalar_map[CustomScalar] = custom_def` and asserts `CustomScalar not in c2.scalar_map`. Pins the per-call-fresh-instance contract from spec line 439.

**Five `**config_kwargs` passthrough tests** (spec lines 490-494):

- `test_strawberry_config_forwards_auto_camel_case_kwarg` — calls `strawberry_config(auto_camel_case=False)` and asserts `result.name_converter.auto_camel_case is False`; also calls `strawberry_config()` (default) and asserts `result.name_converter.auto_camel_case is True`. Assertion target is `result.name_converter.auto_camel_case` (NOT `result.auto_camel_case`) because `auto_camel_case` is a dataclass `InitVar` per upstream at `.venv/lib/python3.10/site-packages/strawberry/schema/config.py::StrawberryConfig #"auto_camel_case: InitVar[bool]"`. The `NameConverter.__init__` default is `auto_camel_case=True` (verified at `.venv/lib/python3.10/site-packages/strawberry/schema/name_converter.py::NameConverter.__init__ #"auto_camel_case: bool = True"`), so the no-arg default branch of the test holds.
- `test_strawberry_config_forwards_relay_max_results_kwarg` — calls `strawberry_config(relay_max_results=200)`; asserts `result.relay_max_results == 200`. Pins the passthrough for a structurally different (integer, not bool) upstream field.
- `test_strawberry_config_combines_extra_scalar_map_and_config_kwargs` — declares local `CustomScalar` / `custom_def` pair; calls `strawberry_config(extra_scalar_map={CustomScalar: custom_def}, relay_max_results=200)`; asserts `result.relay_max_results == 200` AND `BigInt in result.scalar_map` AND `CustomScalar in result.scalar_map`. Pins cooperative composition.
- `test_strawberry_config_rejects_scalar_map_kwarg` — calls `strawberry_config(scalar_map={})` inside `pytest.raises(ValueError) as excinfo`; asserts message contains `"scalar_map"` AND `"extra_scalar_map"`. Also calls `strawberry_config(scalar_map=None)` in a second `pytest.raises(ValueError)` (pins structural rejection — kwarg-name-based, not value-based). Optionally adds a third `pytest.raises(ValueError)` with a populated `scalar_map={BigInt: alt_def}` (where `alt_def = strawberry.scalar(name="AltBigInt", serialize=str, parse_value=int)` is locally declared) to pin that populated dicts are also rejected. The optional third call is Worker 2's discretion (spec line 493: "Optionally adds a third call"); recommendation: include it for branch coverage of the rejection path against populated input.
- `test_strawberry_config_unknown_kwarg_raises_typeerror_from_upstream` — calls `strawberry_config(this_kwarg_does_not_exist_in_strawberry=True)` inside `pytest.raises(TypeError)`; asserts the exception is raised. Does NOT assert on the exception message (the message comes from upstream `StrawberryConfig.__init__` and would couple the test to Strawberry's error wording). Pins the helper does NOT swallow unknown kwargs.

**Two integration tests** (spec lines 500-501):

- `test_bigint_serializes_int_via_strawberry_config_schema` — declares `@strawberry.type class Q: @strawberry.field def big(self) -> BigInt: return 9_223_372_036_854_775_807` (`int64_max`); constructs `schema = strawberry.Schema(query=Q, config=strawberry_config())`; runs `result = schema.execute_sync("{ big }")`; asserts `result.errors is None` AND `result.data == {"big": "9223372036854775807"}` (decimal string, NOT int). Pins the wire-format survival through the migrated registration path.
- `test_bigint_parses_decimal_string_via_strawberry_config_schema` — declares `@strawberry.type class Q: @strawberry.field def echo(self, value: BigInt) -> BigInt: return value`; constructs `schema = strawberry.Schema(query=Q, config=strawberry_config())`; runs `result = schema.execute_sync('{ echo(value: "9223372036854775807") }')`; asserts `result.errors is None` AND `result.data == {"echo": "9223372036854775807"}`. Pins the parser path through the migrated registration.

**One-line edit to `tests/base/test_init.py::test_public_api_surface_is_pinned`** (spec line 46): append `"strawberry_config",` to the pinned tuple at line 44 of the file, after `"finalize_django_types",`. Trailing comma preserved per COM812.

**Ten schema-construction migrations in `tests/types/test_converters.py`** (spec line 47): change `schema = strawberry.Schema(query=Query)` → `schema = strawberry.Schema(query=Query, config=strawberry_config())` at the 10 named tests inside the `# BigInt scalar — schema-execution field-mapping tests` section (current line 452 banner). The import line widens to include `strawberry_config`. NOT migrated: `test_big_auto_field_still_maps_to_int` (line 615; resolves to upstream `Int`, not `BigInt`); every later section (`# JSONField -> ...` banner at line 777 onward).

**Module-docstring update in `tests/test_scalars.py`** (spec line 48): preserve the existing delegation sentence (current docstring's "Wire-level / schema-execution behavior lives in `tests/types/test_converters.py` per the `docs/TREE.md` mirror rule"); append a new sentence acknowledging the two integration tests now live in this file. Spec's suggested rewrite supplied; Worker 2 has discretion on exact phrasing per Decision 7.

### Implementation discretion items

These are choices Worker 1 has assessed and decided are at Worker 2's discretion. None are architectural questions; each has two (or more) equally valid shapes and the spec does not pin one over the other.

1. **Exact phrasing of the appended docstring sentence in `tests/test_scalars.py`.** Decision 7 (spec line 48) explicitly grants Worker 2 discretion: "Worker 2 has discretion on exact phrasing." The contract is "the docstring acknowledges the two `strawberry_config()` integration tests now live in this file." The spec's suggested wording is a starting point; Worker 2 may reword for flow as long as the named test list and the new responsibility ("this file now ALSO carries two integration tests") survive.

2. **Test ordering within each sub-section.** The spec lists the tests in a particular order (scalar-map: returns-instance → default-includes-bigint → none → empty → merges → no-mutate-caller → collision → independent; passthrough: auto_camel_case → relay_max_results → combined → rejects-scalar_map → unknown-kwarg). Worker 2 follows this order because it reads top-down from simplest assertion to most-composed. If Worker 2 reaches a layout where (say) `pytest.raises` setup is awkward, the order can be adjusted, but the recommendation is to follow the spec's order verbatim.

3. **Local-declaration vs module-level `CustomScalar = NewType("CustomScalar", str)` and `custom_def`.** Four tests share this pair. The recommendation (per DRY analysis above) is to declare locally per test — the file's existing style is flat, self-contained tests. Worker 2 may consolidate to a module-level declaration if they find the local repetition reads as noise; the spec does not legislate either. If consolidated, the declarations land between the existing import block and the first scalar-map test, with a small banner comment naming them.

4. **Whether the optional third `pytest.raises(ValueError)` for `test_strawberry_config_rejects_scalar_map_kwarg` is included.** Spec line 493 makes the third call optional ("Optionally adds a third call"). Recommendation: include it to pin that the `scalar_map=` rejection is purely structural (kwarg-name-based) regardless of payload — `{}`, `None`, and a populated `{BigInt: alt_def}` all raise. Worker 2 may drop the third call if they prefer the test stays at two `raises` blocks; the contract (`pytest.raises(ValueError)` on `scalar_map=` kwarg) is the same either way.

5. **Banner comments for the three new sub-sections in `tests/test_scalars.py`.** The existing file's banner style uses three `# ----` lines per banner (current lines 18-20, 46-48, etc.). The new "strawberry_config() factory" section subdivides into three sub-sections (scalar-map / passthrough / integration). Worker 2 may either (a) write three independent top-level banners or (b) write one top-level banner with three smaller sub-banners. Recommendation: three independent top-level banners — matches the existing file style and groups the 15 tests into self-describing chunks. Either shape passes ruff format.

6. **The `assert result.scalar_map[BigInt].name == "BigInt"` assertion in `test_strawberry_config_default_scalar_map_includes_bigint`.** The spec at line 478 pins this assertion against `ScalarDefinition.name`. Worker 2 may additionally pin `result.scalar_map[BigInt].serialize is _serialize_bigint` and `result.scalar_map[BigInt].parse_value is _parse_bigint` (using the existing `from django_strawberry_framework.scalars import _parse_bigint, _serialize_bigint` import) for stronger identity assertions; the spec doesn't forbid this and it's a one-line addition. Recommendation: stick with the spec's pinned assertion (just `.name == "BigInt"`); the parser/serializer identity is already pinned by the existing 22+ parser/serializer tests in the file.

7. **Whether to factor `pytest.raises(ValueError) as excinfo; assert "..." in str(excinfo.value)` into a small helper.** Two tests share this shape (`test_strawberry_config_collision_with_package_scalar_raises_value_error` and `test_strawberry_config_rejects_scalar_map_kwarg`). Recommendation: inline both; consolidating into a `_assert_value_error_contains(...)` helper would add a file-local symbol for two call sites, and the inline shape reads cleaner against the spec's per-test contracts.

### Spec slice checklist (verbatim)

The following sub-checklist is copied verbatim from `docs/spec-020-scalar_map_helper-0_0_7.md` lines 42–48. Worker 1 ticks each `- [x]` during final verification as the contract lands.

- [x] Slice 2: Tests
  - [x] [`tests/test_scalars.py`](../tests/test_scalars.py) (extend): add **one** new test section "`strawberry_config()` factory" with **thirteen** new tests pinning the helper's contract — eight scalar-map tests (`test_strawberry_config_returns_strawberry_config_instance`, `test_strawberry_config_default_scalar_map_includes_bigint`, `test_strawberry_config_accepts_none_extra_scalar_map`, `test_strawberry_config_accepts_empty_extra_scalar_map`, `test_strawberry_config_merges_extra_scalar_map`, `test_strawberry_config_extra_scalar_map_does_not_mutate_caller_dict`, `test_strawberry_config_collision_with_package_scalar_raises_value_error`, `test_strawberry_config_independent_call_returns_independent_instance`) plus five `**config_kwargs` passthrough tests (`test_strawberry_config_forwards_auto_camel_case_kwarg`, `test_strawberry_config_forwards_relay_max_results_kwarg`, `test_strawberry_config_combines_extra_scalar_map_and_config_kwargs`, `test_strawberry_config_rejects_scalar_map_kwarg`, `test_strawberry_config_unknown_kwarg_raises_typeerror_from_upstream`) — see [Test plan](#test-plan) for the per-test contract. Tests use Strawberry's public `StrawberryConfig` / `ScalarDefinition` import surface (`from strawberry.schema.config import StrawberryConfig`; `from strawberry.types.scalar import ScalarDefinition`).
  - [x] [`tests/test_scalars.py`](../tests/test_scalars.py) (extend): add **two** integration tests pinning that the migrated `BigInt` survives a Strawberry-schema round trip when registered through `strawberry_config()` — `test_bigint_serializes_int_via_strawberry_config_schema` (returns a Python `int` from a resolver annotated with `BigInt`; asserts the response JSON carries the decimal-string serialization), `test_bigint_parses_decimal_string_via_strawberry_config_schema` (accepts a decimal-string argument typed `BigInt`; asserts the resolver receives the parsed `int`). These two tests are the regression pins that catch a future `strawberry.scalar(name=..., ...)` overload signature drift; without them, a registration-path regression would surface only at consumer-build time.
  - [x] [`tests/test_scalars.py`](../tests/test_scalars.py) (modify): the existing `test_package_import_does_not_emit_strawberry_deprecation_warning` regression at [`tests/test_scalars.py #"test_package_import_does_not_emit_strawberry_deprecation_warning"`](../tests/test_scalars.py) continues to pass UNCHANGED — the post-Slice-1 import path no longer triggers the deprecation at all (the `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload returns a `ScalarDefinition` directly without invoking the `wrap()` body at [`.venv/lib/python3.10/site-packages/strawberry/types/scalar.py #"def wrap(cls: _T) -> ScalarWrapper"`](../.venv/lib/python3.10/site-packages/strawberry/types/scalar.py) that emits the `DeprecationWarning`); the test's `-W error::DeprecationWarning` subprocess shape pins the post-migration no-leak contract without modification.
  - [x] [`tests/base/test_init.py`](../tests/base/test_init.py) (modify): update the `test_public_api_surface_is_pinned` assertion to append `"strawberry_config"` as the **last** element of the pinned `__all__` tuple (after `"finalize_django_types"`) per [Decision 2](#decision-2--helper-api-shape-and-module-location) and the ASCII-sort convention noted in the Slice 1 bullet.
  - [x] [`tests/types/test_converters.py`](../tests/types/test_converters.py) (modify): every `strawberry.Schema(query=Query)` call inside the `# BigInt scalar — schema-execution field-mapping tests (Slice 1)` section **whose schema resolves to `BigInt`** is rewritten to `strawberry.Schema(query=Query, config=strawberry_config())`. The section starts at the `# BigInt scalar — schema-execution field-mapping tests` banner and ends at the `# JSONField -> strawberry.scalars.JSON schema-execution tests` banner; **10** schema-construction sites are migrated in this section: (1) `test_big_integer_field_maps_to_bigint_in_schema`, (2) `test_big_integer_field_nullable_in_schema`, (3) `test_positive_big_integer_field_maps_to_bigint_in_schema`, (4) `test_bigint_serializes_query_result_as_string_via_schema_execution`, (5) `test_bigint_parses_string_argument_via_schema_execution`, (6) `test_bigint_parses_int_argument_via_schema_execution`, (7) `test_bigint_in_input_position_with_null_via_schema_execution`, (8) `test_bigint_rejects_bool_argument_via_schema_execution`, (9) `test_bigint_rejects_float_argument_via_schema_execution`, (10) `test_bigint_resolver_returning_bool_raises_via_schema_execution`. The import line `from django_strawberry_framework import BigInt, DjangoType, finalize_django_types` is widened to add `strawberry_config`. **NOT migrated** (even though it lives inside the BigInt section banner): `test_big_auto_field_still_maps_to_int` — its schema asserts `terminal["name"] == "Int"` (the upstream `Int` scalar, not `BigInt`); the `BigAutoField → ID` resolution path never touches `BigInt` and therefore needs no `config=strawberry_config()`. The JSONField / Choice-enum / Relation / Boolean tests in later sections are likewise not migrated. This bullet is the practical surface of the migration broadening pinned in [Decision 5](#decision-5--migration-posture-hard-break-in-alpha): consumer-facing schemas with `BigIntegerField` / `PositiveBigIntegerField`-backed `DjangoType` fields need `config=strawberry_config()` even when they never import or annotate `BigInt` directly, because the [`Specialized scalar conversions`](GLOSSARY.md#specialized-scalar-conversions) converter table at [`django_strawberry_framework/types/converters.py`](../django_strawberry_framework/types/converters.py) resolves the field to `BigInt` for them.
  - [x] [`tests/test_scalars.py`](../tests/test_scalars.py) (modify docstring): the module docstring currently says schema-execution behavior for `BigInt` lives in [`tests/types/test_converters.py`](../tests/types/test_converters.py); rewrite it to acknowledge that this file now ALSO carries two in-process `strawberry.Schema(...)` integration tests for the `strawberry_config()` registration round-trip. Suggested rewrite: keep the existing delegation sentence and append "Additionally, two `strawberry.Schema(query=..., config=strawberry_config())` integration tests pin the post-migration `BigInt` round trip end-to-end (`test_bigint_serializes_int_via_strawberry_config_schema`, `test_bigint_parses_decimal_string_via_strawberry_config_schema`)." so the test layout remains self-describing per [L2 in feedback](feedback.md).

---

## Build report (Worker 2)

### Files touched

- `tests/test_scalars.py` — Widened imports (added `from typing import NewType`; `import strawberry`; `from strawberry.schema.config import StrawberryConfig`; `from strawberry.types.scalar import ScalarDefinition`; `from django_strawberry_framework import BigInt, strawberry_config`). Appended the new "`strawberry_config()` factory" test section at the end of the file with three banner-comment sub-sections (scalar-map tests, `**config_kwargs` passthrough tests, integration tests) carrying 15 new tests total. Rewrote the module docstring to add a sentence acknowledging the two new integration tests now live in this file (preserving the existing delegation sentence to `tests/types/test_converters.py`).
- `tests/base/test_init.py` — One-line edit: appended `"strawberry_config",` as the last element of the pinned `__all__` tuple in `test_public_api_surface_is_pinned`, after `"finalize_django_types",` (closes the expected-failure handoff from Slice 1).
- `tests/types/test_converters.py` — Widened the `from django_strawberry_framework import ...` line to add `strawberry_config`. Migrated 10 schema-construction sites inside the `# BigInt scalar — schema-execution field-mapping tests` section from `strawberry.Schema(query=Query)` to `strawberry.Schema(query=Query, config=strawberry_config())`. The 10 migrated sites match the spec's pinned list verbatim. `test_big_auto_field_still_maps_to_int` (line 639) is NOT migrated (resolves to upstream `Int`, not `BigInt`); the JSONField / Choice-enum / Relation / Boolean sections starting at the line-777 banner are NOT migrated.

### Tests added or updated

Eight scalar-map factory tests (spec lines 477-484):

- `tests/test_scalars.py::test_strawberry_config_returns_strawberry_config_instance` — pins `isinstance(strawberry_config(), StrawberryConfig)`.
- `tests/test_scalars.py::test_strawberry_config_default_scalar_map_includes_bigint` — pins `BigInt in cfg.scalar_map`, `isinstance(cfg.scalar_map[BigInt], ScalarDefinition)`, and `cfg.scalar_map[BigInt].name == "BigInt"`.
- `tests/test_scalars.py::test_strawberry_config_accepts_none_extra_scalar_map` — pins that explicit `extra_scalar_map=None` matches the no-arg default.
- `tests/test_scalars.py::test_strawberry_config_accepts_empty_extra_scalar_map` — pins that `extra_scalar_map={}` matches `extra_scalar_map=None`.
- `tests/test_scalars.py::test_strawberry_config_merges_extra_scalar_map` — declares a locally-scoped `CustomScalar = NewType("CustomScalar", str)` and `custom_def = strawberry.scalar(name="CustomScalar", ...)`; asserts both `BigInt` and `CustomScalar` land in the merged map and the consumer's `ScalarDefinition` survives identity-check.
- `tests/test_scalars.py::test_strawberry_config_extra_scalar_map_does_not_mutate_caller_dict` — captures a `before = dict(caller_dict)` snapshot and asserts the caller dict is byte-identical post-call.
- `tests/test_scalars.py::test_strawberry_config_collision_with_package_scalar_raises_value_error` — substring assertions on the `ValueError` message (`"BigInt"` AND `"cannot redeclare"`); no exact-string equality (the Slice 1 implementation line-wrapped the recourse sentence across two adjacent implicit-concatenation literals).
- `tests/test_scalars.py::test_strawberry_config_independent_call_returns_independent_instance` — asserts `c1 is not c2` and `c1.scalar_map is not c2.scalar_map`; mutates `c1.scalar_map[CustomScalar] = custom_def` and asserts the mutation does not leak to `c2`.

Five `**config_kwargs` passthrough tests (spec lines 490-494):

- `tests/test_scalars.py::test_strawberry_config_forwards_auto_camel_case_kwarg` — assertion target is `result.name_converter.auto_camel_case` (NOT `result.auto_camel_case`) per spec line 490 (the `InitVar` pin verified against upstream `StrawberryConfig.__post_init__`); pins both the `auto_camel_case=False` override and the no-arg `True` default.
- `tests/test_scalars.py::test_strawberry_config_forwards_relay_max_results_kwarg` — pins `cfg.relay_max_results == 200` for a structurally-different (integer) upstream field.
- `tests/test_scalars.py::test_strawberry_config_combines_extra_scalar_map_and_config_kwargs` — pins cooperative composition of `extra_scalar_map=` and `**config_kwargs` on a single call.
- `tests/test_scalars.py::test_strawberry_config_rejects_scalar_map_kwarg` — three `pytest.raises(ValueError)` blocks (`scalar_map={}`, `scalar_map=None`, `scalar_map={BigInt: alt_def}`); first block additionally asserts the message contains substrings `"scalar_map"` AND `"extra_scalar_map"`. Third block (populated dict) included per Worker 1's discretion-item recommendation.
- `tests/test_scalars.py::test_strawberry_config_unknown_kwarg_raises_typeerror_from_upstream` — `pytest.raises(TypeError)` with no message assertion (per spec line 494 — the message comes from upstream and must not be coupled to a specific wording).

Two integration tests (spec lines 500-501):

- `tests/test_scalars.py::test_bigint_serializes_int_via_strawberry_config_schema` — minimal `@strawberry.type class Q` with a `BigInt`-returning resolver returning `int64_max`; constructs `strawberry.Schema(query=Q, config=strawberry_config())`; asserts `result.data == {"big": "9223372036854775807"}`.
- `tests/test_scalars.py::test_bigint_parses_decimal_string_via_strawberry_config_schema` — minimal echo resolver typed `BigInt`; asserts the decimal-string argument round-trips.

One-line modification (spec line 46):

- `tests/base/test_init.py::test_public_api_surface_is_pinned` — appended `"strawberry_config"` to the pinned tuple after `"finalize_django_types"`.

Ten schema-construction migrations in `tests/types/test_converters.py` (spec line 47):

- `test_big_integer_field_maps_to_bigint_in_schema`
- `test_big_integer_field_nullable_in_schema`
- `test_positive_big_integer_field_maps_to_bigint_in_schema`
- `test_bigint_serializes_query_result_as_string_via_schema_execution`
- `test_bigint_parses_string_argument_via_schema_execution`
- `test_bigint_parses_int_argument_via_schema_execution`
- `test_bigint_in_input_position_with_null_via_schema_execution`
- `test_bigint_rejects_bool_argument_via_schema_execution`
- `test_bigint_rejects_float_argument_via_schema_execution`
- `test_bigint_resolver_returning_bool_raises_via_schema_execution`

Module-docstring update (spec line 48):

- `tests/test_scalars.py` — preserved the existing delegation sentence (the "Wire-level / schema-execution behavior lives in `tests/types/test_converters.py`..." paragraph) and appended a new sentence acknowledging the two `strawberry_config()` integration tests now live in this file, naming them by full test-function name (`test_bigint_serializes_int_via_strawberry_config_schema`, `test_bigint_parses_decimal_string_via_strawberry_config_schema`).

### Validation run

- `uv run ruff format .` — pass (118 files left unchanged; one COM812-vs-formatter warning is pre-existing repo configuration noise unrelated to this slice).
- `uv run ruff check --fix .` — pass (`All checks passed!`).
- `git status --short` after both ruff invocations:
  - `M django_strawberry_framework/__init__.py` — pre-existing Slice 1 change (uncommitted maintainer working tree); NOT slice-intended for Slice 2. Left alone per `AGENTS.md` line 32 (the cycle is mid-flight and Slice 1 has not been committed yet).
  - `M django_strawberry_framework/scalars.py` — pre-existing Slice 1 change; NOT slice-intended for Slice 2. Left alone.
  - `M docs/spec-020-scalar_map_helper-0_0_7.md` — pre-existing Slice 1 spec revision (Worker 1 final-verification edit); NOT slice-intended for Slice 2. Left alone.
  - `M tests/base/test_init.py` — slice-intended (one-line `__all__` tuple edit).
  - `M tests/test_scalars.py` — slice-intended (15 new tests + import widening + docstring rewrite).
  - `M tests/types/test_converters.py` — slice-intended (import widen + 10 schema-site migrations).
  - `?? docs/builder/bld-slice-1-helper_module_and_bigint_redefinition.md` — pre-existing Slice 1 artifact (untracked).
  - `?? docs/builder/bld-slice-2-tests.md` — this artifact (untracked).
  - `?? docs/builder/build-020-scalar_map_helper-0_0_7.md` — pre-existing build plan (untracked).
  - No unrelated tool churn introduced by ruff in this pass; no `git checkout -- <path>` needed.
- Focused test run (Plan step 10): `uv run pytest --no-cov tests/test_scalars.py tests/base/test_init.py tests/types/test_converters.py` — pass (103 passed, 2 skipped, 0 failed). All 15 new factory/passthrough/integration tests pass; the migrated 10 schema sites in `tests/types/test_converters.py` continue to pass post-migration; the `test_public_api_surface_is_pinned` assertion in `tests/base/test_init.py` passes against the appended `"strawberry_config"` element. The two skipped tests (`test_real_array_field_compatible_with_strawberry`, `test_real_hstore_field_compatible_with_strawberry`) are pre-existing PostgreSQL-only fixtures unrelated to this slice. `--no-cov` is the only `--cov*`-shaped flag used (opts OUT of `pytest.ini`'s auto-applied `--cov` per BUILD.md "Coverage is the maintainer's gate, not a worker's tool").

### Implementation notes

- **In-test (not module-level) declaration of `CustomScalar = NewType("CustomScalar", str)` and `custom_def = strawberry.scalar(name="CustomScalar", ...)`.** Four tests share this pair (merge, no-mutate-caller, independent-instance, combined-with-kwargs). Chose in-test declaration over a module-level fixture per Plan discretion item 3 — keeps each test self-contained, matches the existing `tests/test_scalars.py` style of flat `def test_...()` with inline declarations, and avoids the cost of scattering test data across the file for four single-line uses. Single-pytest-item-per-test under Decision 7 still holds.
- **Optional third `pytest.raises(ValueError)` in `test_strawberry_config_rejects_scalar_map_kwarg`.** Included the populated-dict case (`scalar_map={BigInt: alt_def}` with a locally-declared `alt_def`) per Plan discretion item 4's recommendation — pins that the `scalar_map=` rejection is purely structural (kwarg-name-based), not value-based. The locally-declared `alt_def` uses Strawberry's public scalar API; no dependence on the private `_BIGINT_SCALAR_DEFINITION`.
- **Three independent top-level banner comments for the new sub-sections** (scalar-map, passthrough, integration). Chose this shape over a single top-level banner with three smaller sub-banners per Plan discretion item 5 — matches the existing file's banner cadence (every existing section is one `# ----`-bracketed banner).
- **Did NOT pin `result.scalar_map[BigInt].serialize is _serialize_bigint` / `.parse_value is _parse_bigint`** in `test_strawberry_config_default_scalar_map_includes_bigint`. The spec at line 478 pins only `.name == "BigInt"`; the parser/serializer identity is already pinned by the 22+ existing parser/serializer tests in the file. Stricter assertions would be defense-in-depth but would couple the test to `ScalarDefinition`'s internal attribute names — kept the assertion at the spec's pinned shape.
- **Docstring rewrite preserves the existing first paragraph verbatim** and appends a second paragraph naming the two new integration tests by full function name. Chose to integrate the new sentence into the same paragraph (single docstring paragraph) rather than emit a second blank-line-separated paragraph — ruff format settled on this shape, and it keeps the docstring compact while still being self-describing.

### Notes for Worker 3

- All 15 new tests live in `tests/test_scalars.py` after the existing `test_package_import_does_not_emit_strawberry_deprecation_warning` test. The new code starts at the bottom of the file under three banner-comment sub-sections.
- The shadow file `docs/shadow/tests__test_scalars.overview.md` from Worker 1's planning pass was NOT re-run after Slice 2's edits because the new content is pure test logic (no Django/ORM markers, no control-flow hotspots). Re-running the helper is unnecessary; the diff is the contract.
- The 10 BigInt-section schema migrations in `tests/types/test_converters.py` are line-level edits inside existing test bodies — no new test items, no new model declarations, no new assertions. The only delta per site is the `, config=strawberry_config()` kwarg added to `strawberry.Schema(query=Query)`. `test_big_auto_field_still_maps_to_int` (which lives inside the BigInt section banner but asserts on the upstream `Int` scalar) is correctly NOT migrated.
- The `test_strawberry_config_collision_with_package_scalar_raises_value_error` test uses substring assertions (`"BigInt"` AND `"cannot redeclare"`), NOT exact-string equality. The Slice 1 implementation notes flagged that the recourse sentence was split across two adjacent implicit-concatenation literals for the 110-char line budget — substring-only assertions keep this test resilient to future cosmetic re-wraps.
- The `test_strawberry_config_forwards_auto_camel_case_kwarg` test asserts on `result.name_converter.auto_camel_case` (NOT `result.auto_camel_case`) per spec line 490 — the `auto_camel_case` field is a dataclass `InitVar` on `StrawberryConfig` and `__post_init__` applies the value to `name_converter.auto_camel_case`, leaving `cfg.auto_camel_case` as `None`.
- No `pytest.mark.parametrize` used (Decision 7 forbids it for the new tests); every test is a flat `def test_...():` with inline assertions matching pytest collection 1:1.

### Notes for Worker 1 (spec reconciliation)

None. Slice 2 landed verbatim against Worker 1's plan and the spec's pinned shape. The 15 new tests, the one-line `__all__` edit, the 10 schema-site migrations, and the module-docstring rewrite all match the spec's contract. No plan-vs-implementation drift; no spec ambiguity surfaced during build.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- Static-helper re-run on `tests/test_scalars.py` (the +178-line addition triggers the 50-line-outside-package threshold) at `docs/shadow/tests__test_scalars.overview.md`: 0 control-flow hotspots, 0 Django/ORM markers, 0 TODOs. Repeated string literals surfaced: `CustomScalar` x8 (2 declarations per test x 4 tests), `9223372036854775807` x4 (2 occurrences each in 2 integration tests, the wire-format pin from spec-013), `-9223372036854775808` x2 (pre-existing), `AltBigInt` x2 (locally declared per the 2 tests that need it). All four are explicitly permitted by the Plan's DRY-analysis discretion item 3 (`CustomScalar` local declarations) and by the spec's wire-format requirement (the int64-max literals). No DRY findings.
- The `pytest.raises(ValueError) as excinfo; assert "..." in str(excinfo.value)` shape appears at `tests/test_scalars.py::test_strawberry_config_collision_with_package_scalar_raises_value_error` and `tests/test_scalars.py::test_strawberry_config_rejects_scalar_map_kwarg`. Plan discretion item 7 ruled inline over a `_assert_value_error_contains(...)` helper for two call sites; Worker 2 followed the recommendation. Two-site inlining is the maximally-readable shape here. No DRY finding.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` shows the Slice 1 widening (`from .scalars import BigInt, strawberry_config` and the `"strawberry_config"` append to `__all__`). That diff is already `final-accepted` under Slice 1 and is out-of-scope for Slice 2 review per the cumulative-diff trap noted in `worker-3.md`. Slice 2 itself does not modify `django_strawberry_framework/__init__.py` — the three Slice-2 files (`tests/test_scalars.py`, `tests/base/test_init.py`, `tests/types/test_converters.py`) leave the public-surface manifest untouched.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- Test counts match the spec exactly. `grep -c '^def test_strawberry_config' tests/test_scalars.py` returns 13 (8 scalar-map + 5 passthrough); the two integration tests match by full function name (`test_bigint_serializes_int_via_strawberry_config_schema`, `test_bigint_parses_decimal_string_via_strawberry_config_schema`). 13 + 2 = 15 new tests. No `pytest.mark.parametrize` used; flat `def test_...():` shape preserved per Decision 7.
- `test_strawberry_config_forwards_auto_camel_case_kwarg` asserts on `result.name_converter.auto_camel_case` (NOT `result.auto_camel_case`) at `tests/test_scalars.py` lines 350 and 352, exactly matching spec line 490's pinned shape. Pins both the override (`False`) and the default-true branch (`is True`). The focused run `uv run pytest --no-cov tests/test_scalars.py::test_strawberry_config_forwards_auto_camel_case_kwarg` passes — confirms the upstream `InitVar` / `__post_init__` indirection is correctly traversed.
- `test_strawberry_config_collision_with_package_scalar_raises_value_error` uses substring assertions (`"BigInt" in message` AND `"cannot redeclare" in message`) at `tests/test_scalars.py` lines 322-324 — does NOT pin the exact wording. Resilient to the Slice-1 line-wrap of the recourse sentence across two adjacent implicit-concatenation literals.
- `test_strawberry_config_rejects_scalar_map_kwarg` covers all three rejection paths: `scalar_map={}`, `scalar_map=None`, and `scalar_map={BigInt: alt_def}` — first block additionally pins the message contains `"scalar_map"` AND `"extra_scalar_map"`. The structural-rejection contract (kwarg-name-based, not value-based) is fully exercised.
- `test_strawberry_config_unknown_kwarg_raises_typeerror_from_upstream` uses `pytest.raises(TypeError)` with NO message assertion — spec line 494's "Does NOT assert on the exception message" requirement honored; the test stays decoupled from upstream's wording.
- Both integration tests build a minimal `@strawberry.type class Q` with a `BigInt`-typed resolver, construct `strawberry.Schema(query=Q, config=strawberry_config())`, run `schema.execute_sync(...)`, and assert on BOTH `result.errors is None` AND `result.data == {...}`. Focused run confirms both pass.
- `tests/base/test_init.py` diff is exactly one line: `"strawberry_config",` appended as the LAST element of the pinned tuple after `"finalize_django_types",` (line 44 of the post-edit file). Trailing comma per COM812. Focused run `uv run pytest --no-cov tests/base/test_init.py::test_public_api_surface_is_pinned` passes.
- `tests/types/test_converters.py` migration shape verified: `grep -n "strawberry.Schema(query=Query, config=strawberry_config())" tests/types/test_converters.py | wc -l` returns 10. Inspecting each migrated site against the spec's named list: all 10 spec-named tests (`test_big_integer_field_maps_to_bigint_in_schema` at line 543, `test_big_integer_field_nullable_in_schema` at line 575, `test_positive_big_integer_field_maps_to_bigint_in_schema` at line 604, `test_bigint_serializes_query_result_as_string_via_schema_execution` at line 667, `test_bigint_parses_string_argument_via_schema_execution` at line 682, `test_bigint_parses_int_argument_via_schema_execution` at line 699, `test_bigint_in_input_position_with_null_via_schema_execution` at line 716, `test_bigint_rejects_bool_argument_via_schema_execution` at line 731, `test_bigint_rejects_float_argument_via_schema_execution` at line 746, `test_bigint_resolver_returning_bool_raises_via_schema_execution` at line 763) have the kwarg added.
- `test_big_auto_field_still_maps_to_int` at `tests/types/test_converters.py` line 615 (schema construction at line 639) is correctly UNMIGRATED — the assertion at line 644 (`assert terminal["name"] == "Int"`) confirms it resolves to upstream `Int`. Focused run passes.
- The remaining 17 unmigrated `strawberry.Schema(query=Query)` sites in `tests/types/test_converters.py` (verified by `grep -n` — lines 227, 639, 812, 844, 875, 945, 980, 1018, 1055, 1136, 1244, 1320, 1353, 1390, 1425, 1509, 1638, 1686) all live outside the BigInt section or in `test_big_auto_field_still_maps_to_int`; the JSONField banner at line 776/777 marks the section boundary correctly. No accidental over-migration.
- Module-docstring rewrite at `tests/test_scalars.py` lines 1-12 PRESERVES the existing delegation paragraph (the `Wire-level / schema-execution behavior lives in tests/types/test_converters.py` sentence remains at lines 5-7) and APPENDS the new sentence at lines 8-11 naming both integration tests by full function name. Spec line 48 satisfied.
- No private symbol imports. `grep -n "_BIGINT_SCALAR_DEFINITION\|_PACKAGE_SCALAR_MAP" tests/test_scalars.py tests/base/test_init.py tests/types/test_converters.py` returns nothing. The pre-existing `from django_strawberry_framework.scalars import _parse_bigint, _serialize_bigint` at `tests/test_scalars.py` line 25 is unchanged and is not introduced by this slice. Tests use the public `BigInt`, `strawberry_config`, `StrawberryConfig`, `ScalarDefinition` surface.
- The 13 new factory tests cover every branch identified in spec line 450 (default path, `None` / `{}` cases, merge, collision-raise, `scalar_map`-rejection, passthrough success, unknown-kwarg). Reading the diff against Decision 4 (collision policy) and Decision 2 (factory passthrough) confirms no decision-required behavior is silently un-tested.
- Plan's `### Spec slice checklist (verbatim)` walk: all 6 sub-checks are addressed in the diff — (1) thirteen factory tests added, (2) two integration tests added, (3) `test_package_import_does_not_emit_strawberry_deprecation_warning` left UNCHANGED (verified by reading lines 238-261 — no diff in the test body), (4) `tests/base/test_init.py` `__all__` widened, (5) `tests/types/test_converters.py` 10-site migration plus import widening, (6) `tests/test_scalars.py` docstring updated. Nothing silently un-addressed.

### Temp test verification

No temp tests created under `docs/builder/temp-tests/<slice>/` during review. The implementation diff is small (3 files; 190 lines) and matches the plan + spec verbatim; spot-checks via focused `uv run pytest --no-cov ...` (without coverage flags, per BUILD.md) on six high-leverage tests + the `__all__` pin + 3 representative converter sites + the unmigrated sentinel test (10 total focused tests run) confirmed pass at the test tier. Worker 3 ran the static helper on `tests/test_scalars.py` per the BUILD.md "50+ lines outside `django_strawberry_framework/`" threshold; overview at `docs/shadow/tests__test_scalars.overview.md`.

### Notes for Worker 1 (spec reconciliation)

None. The slice's diff is a verbatim landing of the spec's pinned tests + migrations + docstring shape. No spec ambiguity surfaced.

### Review outcome

`review-accepted`. All 15 new tests, the one-line `__all__` append, the 10 schema-site migrations, and the module-docstring rewrite match the spec contract; no High/Medium/Low findings; DRY findings none; public-surface untouched by this slice; focused pytest spot-checks pass. Setting top-level `Status:` to `review-accepted`.

---

## Final verification (Worker 1)

- **Spec slice checklist:** all six sub-bullets in the Plan's `### Spec slice checklist (verbatim)` are ticked `- [x]`. Walked each against the diff: (1) thirteen factory tests present at `tests/test_scalars.py` lines 269–399 (8 scalar-map + 5 passthrough, verified by `grep -c '^def test_strawberry_config' tests/test_scalars.py` returning 13); (2) two integration tests present at `tests/test_scalars.py` lines 403, 418 (verified by `grep -n '^def test_bigint_serializes_int_via_strawberry_config_schema\|^def test_bigint_parses_decimal_string_via_strawberry_config_schema'`); (3) `test_package_import_does_not_emit_strawberry_deprecation_warning` is unchanged in the slice diff (`git diff tests/test_scalars.py` shows only additions + the docstring rewrite — no diff lines touching the deprecation regression test body); (4) `tests/base/test_init.py` `__all__` tuple appended with `"strawberry_config",` as the last element (one-line diff confirmed); (5) `tests/types/test_converters.py` carries exactly 10 occurrences of `strawberry.Schema(query=Query, config=strawberry_config())` (verified by grep count `10`) inside the BigInt section, and the import line widened to include `strawberry_config`; (6) `tests/test_scalars.py` module docstring preserved the existing delegation sentence and appended the new sentence naming both integration tests.
- **DRY check across this slice and prior accepted slices (Slice 1):** Worker 3's diff-stat is +178 lines in `tests/test_scalars.py` (pure test logic; no Django/ORM markers, no control-flow hotspots per the helper rerun at `docs/shadow/tests__test_scalars.overview.md`). Repeated literals surfaced — `CustomScalar` (x8), `9223372036854775807` (x4 across two integration tests, spec-013 wire-format pin), `AltBigInt` (x2 for the local `alt_def` declarations) — are all spec-permitted by Decision 7's per-test locality rule (spec lines 366–367 forbid `parametrize` fan-out and the existing file style favors flat, self-contained tests). The 10-site converter migration is mechanical `strawberry.Schema(query=Query, config=strawberry_config())` substitution and introduces no new helper or repeated structural pattern beyond what Slice 1 already pinned. No new cross-slice duplication; nothing to consolidate.
- **Existing tests still pass:** `uv run pytest --no-cov tests/test_scalars.py tests/base/test_init.py tests/types/test_converters.py` → exit code 0; 103 passed, 2 skipped, 0 failed (the 2 skipped are pre-existing PostgreSQL-only fixtures `test_real_array_field_compatible_with_strawberry` and `test_real_hstore_field_compatible_with_strawberry`, unrelated to this slice). `test_public_api_surface_is_pinned` PASSES post-Slice-2 (Slice 1's expected-failure handoff is closed). The 15 new tests pass. The 10 migrated `tests/types/test_converters.py` sites pass. `--no-cov` is the only `--cov*`-shaped flag used (opts OUT of `pytest.ini`'s auto-applied `--cov`).
- **Spec reconciliation:** none required for the slice contract. Spec status-line refresh applied at the start of this pass — line 4 ("Slice 1 shipped; Slices 2–5 remain.") was stale post-Slice-2 review-accepted; corrected to "Slices 1–2 shipped (helper module + `BigInt` redefinition; tests); Slices 3–5 remain." per the Worker 1 spec status-line re-verification rule (`worker-1.md #"Spec status-line re-verification (every Worker 1 spawn)"`). No other spec edits — Worker 2's build report records no notes for spec reconciliation, Worker 3's review surfaced no notes for spec reconciliation, and the Plan's spec-line-42–48 contract landed verbatim.
- **Final status:** `final-accepted`.

### Summary

Slice 2 shipped the test surface for the `strawberry_config()` factory and the `BigInt` registration migration. 15 new tests landed in `tests/test_scalars.py` (8 scalar-map factory tests + 5 `**config_kwargs` passthrough tests + 2 in-process `strawberry.Schema(..., config=strawberry_config())` integration tests covering the round trip end-to-end). The pinned `__all__` tuple in `tests/base/test_init.py` was widened by one element (`"strawberry_config"`), closing Slice 1's expected-failure handoff. 10 `BigInt`-resolving schema-construction sites inside the `# BigInt scalar — schema-execution field-mapping tests` section of `tests/types/test_converters.py` were migrated to pass `config=strawberry_config()`, exercising Decision 5's "consumer schemas with `BigIntegerField` / `PositiveBigIntegerField`-backed `DjangoType` fields need `config=strawberry_config()` even when they never import `BigInt` directly" migration-broadening pin. The `tests/test_scalars.py` module docstring was rewritten to preserve the existing delegation sentence and append acknowledgement of the two new integration tests. The pre-existing `test_package_import_does_not_emit_strawberry_deprecation_warning` regression remains UNCHANGED and continues to pass — now pinning the post-migration no-leak contract through the bare `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload rather than the removed suppression block. Focused pytest run: 103 passed, 2 skipped (pre-existing PostgreSQL-only fixtures), 0 failed.

### Spec changes made (Worker 1 only)

- `docs/spec-020-scalar_map_helper-0_0_7.md` line 4 — status-line refresh from "Slice 1 shipped (helper module + `BigInt` redefinition); Slices 2–5 remain." to "Slices 1–2 shipped (helper module + `BigInt` redefinition; tests); Slices 3–5 remain." Reason: Slice 2 has now landed and review-accepted; the prior status line was stale per the Worker 1 spec status-line re-verification rule.
