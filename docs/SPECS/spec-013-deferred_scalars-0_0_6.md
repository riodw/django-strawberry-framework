# Spec: Deferred scalar conversions

Target release: `0.0.6`.
Status: draft (revision 10, post-feedback2 re-review).
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [Scalar field conversion][glossary-scalar-field-conversion], [Specialized scalar conversions][glossary-specialized-scalar-conversions], [`BigInt` scalar][glossary-bigint-scalar]), [`KANBAN.md`][kanban] card `DONE-013-0.0.6`.
Card line: ["Add `BigInt` scalar with string serialization and `int` parsing. Add `JSONField` mapping to Strawberry JSON. Add `HStoreField` where available. Add `ArrayField` recursion through `field.base_field`. Use synthetic unmanaged test models where fakeshop does not naturally exercise the fields. Keep coverage at 100%."][kanban]

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft.
- **Revision 2** (post-pass-1 review) — HStore `JSON`; sentinel-guarded `isinstance`; fake-field-class test doubles; `HStoreField` moved into a sentinel branch; GraphQL 32-bit `Int` boundary recast as primary driver; `PositiveBigIntegerField` mapped to `BigInt`; `SCALAR_MAP` value-type widened to `Any`; `schema.execute_sync` required for every public mapping; CHANGELOG permission granted.
- **Revision 3** (post-pass-2 review) — Release-alignment quartet expanded; `_FakeArrayField` metadata propagation; explicit `_resolve_*_field()` helper tests; `PositiveBigIntegerField` MRO rationale corrected; `BigAutoField` recourse sequenced behind WIP-ALPHA-015; `IntValueTooLargeError` → observable `GraphQLError` shape; `BigInt` redefined using `NewType` (later proven insufficient — see revision 4).
- **Revision 4** (post-pass-3 review) — Strawberry deprecation warning accepted for `0.0.6`; strict `BigInt` parser introduced; test layout matched to `docs/TREE.md` mirror rule; atomic version bump expanded to a *quintet*; KANBAN card body to be rewritten (not just status-flipped); `GLOSSARY.md` BigInt entry update made explicit.
- **Revision 5** (post-pass-4 review) — Strict parser tightened with `re.fullmatch(r"^(0|-?[1-9][0-9]*)$", value)` (rejects `"1_000"`, `"+1"`, `"１２"`, `"01"`, `"-0"`); `scalar_map` follow-up rationale corrected; float-rejection sentence fixed (`int(1.9) == 1` is the silent-truncation bug).
- **Revision 6** (post-sr-dev review) — `managed = False` requirement and explicit `monkeypatch.setattr(converters, "_*_FIELD_CLS", ...)` step pinned in Decision 7; redundant inner `_ARRAY_FIELD_CLS is not None` removed; outer `choices` on `ArrayField` rejected with `ConfigurationError`; `T | None` hedge dropped (verified on Python 3.10+); Slice 5 split into Slice 5 (atomic version-bump quintet) and Slice 6 (docs/KANBAN/CHANGELOG/archive) — now six slices; `__all__` exact tuple text pinned; deprecation-warning emission test added (later replaced in revision 7); inline KANBAN Done-card body drafted; explicit `docs/GLOSSARY.md #"PostgreSQL HStoreField → dict[str, str | None]"` deletion target; plus polish for L1–L4, L6, L7, and 9 missing tests.
- **Revision 7** (post-second-pass review) — Seven structural changes plus polish:
  1. **B1**: `BigInt` definition wrapped in a tightly scoped `warnings.catch_warnings()` filter so Strawberry's class-direct-to-`scalar()` `DeprecationWarning` does **not** escape to consumers at package-import time. Previously, importing `django_strawberry_framework` (or anything from it) leaked the warning; under `-W error::DeprecationWarning`, the import failed entirely. Revision 6's `test_bigint_scalar_definition_emits_strawberry_deprecation_warning` is replaced with `test_package_import_does_not_emit_strawberry_deprecation_warning`, which forces a re-import under `warnings.catch_warnings(record=True)` and asserts no Strawberry deprecation escapes. CHANGELOG entry restructured accordingly. The suppression is intentional debt for `0.0.6`; the warning-free design is roadmapped as `WIP-ALPHA-020-0.0.7 — Warning-free scalar registration via StrawberryConfig.scalar_map`, added in Slice 6.
  2. **B2**: New strict serializer `_serialize_bigint(value: Any) -> str` replaces `serialize=str`. Rejects `bool`, `float`, `str`, `Decimal`, and any non-`int` type with `TypeError`. Three new unit tests (`test_bigint_serialize_rejects_bool`, `test_bigint_serialize_rejects_float`, `test_bigint_serialize_rejects_non_int_types`) plus a schema-execution test (`test_bigint_resolver_returning_bool_raises_via_schema_execution`) pin the output side's strictness symmetric with the input parser.
  3. **H1**: Decision 6 + Risks rewritten to state the migration contract honestly. The previous claim that "the public `BigInt` symbol stays the same — only the internal definition mechanism changes" was too strong: under `scalar_map`, `BigInt` may need to become a bare `NewType`, and consumers using it directly will need to merge a package-provided `StrawberryConfig` into their `strawberry.Schema(...)`. For `0.0.6`, `BigInt` is a `ScalarWrapper` usable directly; the warning-free migration is an open public-API change tracked as a follow-up.
  4. **H2**: Two missing parser tests added — `test_bigint_parses_python_zero` (`_parse_bigint(0) == 0`) and `test_bigint_parses_signed_int64_max_string` (pins the int64-max boundary the API table claims). The "sized for 64-bit values" phrasing is replaced with "typically used to map Django's 64-bit integer fields (`BigIntegerField`, `PositiveBigIntegerField`)" — the scalar is technically arbitrary-precision (Python `int`) but is sized in practice by its source columns.
  5. **H3**: New "Schema test fixture pattern" subsection under Decision 7 — spells out the recipe (autouse `registry.clear()` from `conftest.py`, synthetic model with `managed = False; app_label = "tests"`, sentinel monkey-patch *before* `DjangoType` declaration, `finalize_django_types()` after, `strawberry.Schema(...)` then `schema.execute_sync(...)`).
  6. **M2**: Current state section drops the stale "20 Django field classes" count (actual is 26) — replaced with "covers Django's standard scalar field classes" so the count cannot go stale.
  7. **M3**: GraphQL overflow message references rephrased throughout as "message containing `Int cannot represent non 32-bit signed integer value`" rather than as exact-constructor `GraphQLError("...")` literals. The live error includes a value suffix.

  Polish (M4, L3): HStore real-postgres test assertion tightened to also exercise a resolver returning `{"k1": "v", "k2": None}` via `schema.execute_sync`. CHANGELOG `Known issues` entry replaced with a `Notes` entry documenting the suppressed internal deprecation (consumers see no warning; entry preserves the design context for future maintainers).
- **Revision 8** (post-sr-dev pass-2) — Three structural fixes plus a batch of accuracy and polish updates:
  1. **H1**: Decision 5 gained explicit HStoreField branch pseudocode (mirrors Decision 2's shape) with a documented policy: `choices` on the outer `HStoreField` are rejected with `ConfigurationError`, consistent with the ArrayField outer-`choices` rejection. New test `test_hstore_field_outer_choices_rejected_via_fake_sentinel` added to Slice 4.
  2. **H2**: The deprecation-suppression regression test was using `importlib.reload(django_strawberry_framework)`, which (as the sr dev verified) does not reload submodules — so `scalars.py`'s `with warnings.catch_warnings()` block runs once on first import and the reload skips it, making the test pass even when the suppression is removed. Replaced with a **subprocess-based test** that runs `python -W error::DeprecationWarning -c "import django_strawberry_framework"` and asserts exit code 0. Clean process isolation, no `sys.modules` munging, tests the real consumer experience.
  3. **H3**: The claim that `tests/types/conftest.py` provides the autouse `registry.clear()` fixture is wrong — no such file exists. Each test file (`tests/types/test_converters.py::_isolate_registry`, `tests/types/test_definition_order.py::_isolate_registry`, etc.) declares its own `@pytest.fixture(autouse=True) def _isolate_registry()`. Decision 7's preamble rewritten to describe the actual reality and the in-file inheritance pattern.

  Accuracy and polish (M1, M2, M3, M4, M5, M6, M7, L1, L3, L5, L7, L8, L10): in-function vs session-fixture-pattern note added to Decision 7; `catch_warnings()` thread-safety caveat added to Risks; custom `from_db_value` edge case added to Edge cases; Slice 5 preamble notes the deliberate version-string gap with Slice 6; new test `test_bigint_is_importable_from_top_level` added to Slice 1; DoD item gates PyPI publish on Slice 6 closure; gated real-postgres tests gained a note about walking the introspection `kind/ofType` chain explicitly; escaped `\"0\"` in the Slice 6 BigInt entry text replaced with `"0"`; Slice 6 preamble notes it's the largest commit and may warrant a draft PR; Decision 6 committed explicitly to the factory-pattern direction (per `WIP-ALPHA-020-0.0.7`); parser-rejects-None test gained a docstring note that Strawberry strips null before `parse_value` for nullable inputs; Risks bullet on `test_converters.py` size now includes the actual baseline (~420 lines → ~1100 after this card); "BigInt arbitrary-precision" framing trimmed to one canonical place (Decision 1) with pointers from Edge cases and Risks.
- **Revision 9** (post-sr-dev pass-3) — Four polish items from a third sr dev pass plus six low-severity tightenings; no blockers, no high-severity items in this pass:
  1. **M1**: The renumber-option clause in Slice 6 (suggesting consumers could renumber `TODO-ALPHA-020` through `044` → `021` through `045` to insert the new card at NNN 020 with cluster-adjacency) is **removed entirely**. Multi-file cascading rename across 5+ files and ~50+ string sites with stale-link risk for any external doc/PR/CHANGELOG citing a card NNN. Slice 6 now simply says "append at NNN 045" with the rationale that KANBAN groups by version, not by NNN.
  2. **M2**: Archive step now strips the inline `WIP-ALPHA-020-0.0.7` card body before archiving, replacing it with a `See KANBAN.md` pointer. Prevents drift between the archived spec and the evolving KANBAN card.
  3. **M3**: Decision 6's "Committed architectural direction" softened to "Recommended starting point" — the follow-up spec author can react to new info (e.g., Strawberry adding first-class scalar registration in a future version) without overriding a prior commitment.
  4. **M4**: Slice 6 preamble adds a 6a/6b split option as fallback if reviewer feedback flags the commit size during the PR.

  Polish (L1, L2, L4, L5, L6): BigInt import smoke test softened to `BigInt is not None` only — drops the `isinstance(BigInt, strawberry.types.scalar.ScalarWrapper)` assertion since `ScalarWrapper` is an undocumented internal Strawberry path; schema-execution tests downstream catch deeper regressions with stronger signal. TODO-045's "Files likely touched" list hedged with "(subject to the follow-up spec settling final locations)". Subprocess deprecation-suppression test gained a docstring comment explaining `sys.executable` is the venv's Python under `uv run pytest`. Decision 7's "Synthetic-model declaration patterns" cross-references the upstream `app_label = "tests"` requirement explicitly. TODO-045's "Hard break in alpha" decision softened to "Recommended posture" tone — the follow-up spec author can revisit after surveying real `0.0.6` consumer adoption.
- **Revision 10** (post-feedback2 re-review) — A separate reviewer's pass on revision 8 surfaced one rendering bug, three API/contract corrections, and four polish items. (One of the reviewer's findings — the renumber-option footgun — was already addressed in rev 9 as M1.) Seven new fixes:
  1. **H1 (rendering)**: The verbatim `WIP-ALPHA-020-0.0.7` body in Slice 6 used a ` ```markdown ` outer fence containing a ` ```python ` inner fence. The inner triple backticks close the outer block prematurely in markdown rendering, so the verbatim body was not actually safe to copy. Switched the outer fence to four backticks (` ````markdown `) so the inner Python snippet renders as intended.
  2. **M1 (API correctness)**: Removed `extra_extensions=None` from the recommended `strawberry_config(...)` signature in Decision 6 and the TODO-045 card body. Strawberry's extensions are passed to `strawberry.Schema(..., extensions=[...])`, not into `StrawberryConfig` — a factory returning `StrawberryConfig` cannot meaningfully accept `extra_extensions`. The follow-up spec can introduce a separate helper (returning a schema-construction bundle, not a `StrawberryConfig`) if extension composition becomes a real need.
  3. **M2 (internal consistency)**: TODO-045 body had two contradictions — (a) "BigInt stays usable as a direct annotation" conflicted with "BigInt may or may not stay in `__all__`" in the DoD; (b) "Recommended posture: hard break in alpha" conflicted with "compatibility shim for `0.0.6` consumers" listed as an open design question. Resolved (a) by committing to `BigInt` staying in `__all__` (consistent with the direct-annotation recommendation); kept (b) consistent by framing the open question as "deprecation-window details" rather than a yes/no on the shim.
  4. **M3 (stale reference)**: Test plan category 17 still described the deprecation-suppression regression as `package import under warnings.catch_warnings(record=True)`. Updated to match the subprocess-based mechanism pinned in Decision 7 (rev 8).
  5. **L1 (consistency)**: HStore outer-`choices` rejection (added to Decision 5 in rev 8) was missing from the Goals, Non-goals, and User-facing API table. All three updated so the policy is discoverable without reading Decision 5.
  6. **L2 (accuracy)**: The `managed = False` rationale in Decision 7 was inaccurate — the reviewer verified locally that bare `models.Field` subclasses don't trigger `Model.check()` warnings regardless of `managed`. Rewrote the rationale to the actual purpose: avoiding migration implications and reminding implementers to instantiate test models directly (not via `objects.create()`).
  7. **L3 (clarity)**: Dropped the unexplained `dst.` shorthand alias from the `strawberry_config(...)` references in Decision 6 and the TODO-045 body. The spec uses `django_strawberry_framework` imports directly elsewhere; introducing an unexplained alias was an inconsistency.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoType`][glossary-djangotype] — the base class whose field-conversion table this card extends.
- [Scalar field conversion][glossary-scalar-field-conversion] — the shipped scalar coverage and the **subclass MRO walk** that the spec's [Edge cases](#edge-cases-and-constraints) section relies on.
- [Specialized scalar conversions][glossary-specialized-scalar-conversions] — the planned umbrella entry this card flips from `planned for 0.0.6` to `shipped (0.0.6)`.
- [`BigInt` scalar][glossary-bigint-scalar] — the new public scalar this card introduces.
- [`ConfigurationError`][glossary-configurationerror] — raised for unsupported fields, nested `ArrayField`, and outer `choices` on `ArrayField`.
- [`Meta.exclude`][glossary-metaexclude] — consumer-side recourse named in the existing unsupported-field error message.
- [`finalize_django_types`][glossary-finalize-django-types] — where the new annotations land. The [Schema test fixture pattern](#decision-7--test-strategy) requires every test that defines a synthetic `DjangoType` to call this.
- [Choice enum generation][glossary-choice-enum-generation] — `ArrayField(CharField(choices=...))` on the *base field* is the tested edge case; outer `choices` on `ArrayField` is rejected.
- [Scalar field override semantics][glossary-scalar-field-override-semantics] — planned for `0.0.6` (WIP-ALPHA-015). The `BigAutoField` deferral depends on that contract.

Project conventions to follow:

- [`AGENTS.md`][agents] — schema testing via `schema.execute_sync`. **Note:** `AGENTS.md` prohibits `CHANGELOG.md` edits without explicit permission; [Slice 6](#slice-6--docs-kanban-changelog-archive) grants that permission.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; release-bump checklist.
- [`KANBAN.md`][kanban] — Card ID format; column movement at Slice 6.
- [`docs/TREE.md`][tree] — package layout convention; tests mirror source one-to-one.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan).

- [ ] Slice 1: `BigInt` scalar + 64-bit integer field mappings
  - [ ] Add `django_strawberry_framework/scalars.py` defining `_parse_bigint`, `_serialize_bigint`, and `BigInt` per [Decision 1](#decision-1--bigint-wire-format-and-target-fields). The `BigInt` definition is wrapped in `warnings.catch_warnings()` + `filterwarnings("ignore", message="Passing a class to strawberry.scalar", category=DeprecationWarning)` so Strawberry's class-direct-to-`scalar()` deprecation does not escape to consumers at import time (B1 fix).
  - [ ] Re-export `BigInt` from `django_strawberry_framework/__init__.py`. **Exact `__all__` tuple after the change**:
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
  - [ ] Update `tests/base/test_init.py`'s pinned `__all__` assertion to include `"BigInt"` matching the tuple above.
  - [ ] Add `models.BigIntegerField: BigInt` to `SCALAR_MAP`.
  - [ ] Change `models.PositiveBigIntegerField: int` → `models.PositiveBigIntegerField: BigInt` in `SCALAR_MAP`.
  - [ ] Widen `SCALAR_MAP`'s declared value type to `dict[type[models.Field], Any]` per [Decision 8](#decision-8--scalar_map-value-type-widening).
  - [ ] Drop the `BigInt` TODO comment in `types/converters.py`.
  - [ ] Scalar wire-format and parser tests in `tests/test_scalars.py` (new file):
    - Serializer (B2 coverage):
      - [ ] `test_bigint_serializes_int_as_decimal_string`
      - [ ] `test_bigint_serializes_zero` — `_serialize_bigint(0)` → `"0"` (covers the `int.__bool__ is False` edge)
      - [ ] `test_bigint_serializes_negative_int_as_decimal_string`
      - [ ] `test_bigint_serializes_signed_int64_min` — `_serialize_bigint(-2**63)` → `"-9223372036854775808"` (pins the int64-min boundary)
      - [ ] `test_bigint_serializes_signed_int64_max` — `_serialize_bigint(2**63 - 1)` → `"9223372036854775807"` (pins the int64-max boundary)
      - [ ] `test_bigint_serialize_rejects_bool` — `True` and `False` both raise `TypeError` (B2 fix)
      - [ ] `test_bigint_serialize_rejects_float` — `1.9`, `0.0` raise `TypeError` (B2 fix)
      - [ ] `test_bigint_serialize_rejects_non_int_types` — `str`, `Decimal`, `None`, custom object all raise `TypeError` (B2 fix)
    - Parser positive cases:
      - [ ] `test_bigint_parses_python_int`
      - [ ] `test_bigint_parses_python_zero` — `_parse_bigint(0)` → `0` (H2 fix: pins the int-zero branch)
      - [ ] `test_bigint_parses_decimal_string_to_int`
      - [ ] `test_bigint_parses_negative_decimal_string_to_int`
      - [ ] `test_bigint_parses_zero_string` — `_parse_bigint("0")` → `0` (pins the regex's `(0|...)` first alternative)
      - [ ] `test_bigint_parses_signed_int64_min_string` — `_parse_bigint("-9223372036854775808")` → `-9223372036854775808` (H2 fix: pins the int64-min boundary)
      - [ ] `test_bigint_parses_signed_int64_max_string` — `_parse_bigint("9223372036854775807")` → `9223372036854775807` (H2 fix: pins the int64-max boundary)
    - Parser negative cases:
      - [ ] `test_bigint_rejects_python_bool` — both `True` and `False`
      - [ ] `test_bigint_rejects_python_float` — `1.9`, `0.0`, `-1.0` (silent-truncation guard: `int(1.9) == 1` would otherwise slip through)
      - [ ] `test_bigint_rejects_empty_string`
      - [ ] `test_bigint_rejects_whitespace_padded_string` — `" 123 "`, `"\t123"`
      - [ ] `test_bigint_rejects_non_decimal_string` — `"abc"`, `"1.9"`, `"1e3"`, `"0x10"`
      - [ ] `test_bigint_rejects_underscore_separator` — `"1_000"`, `"-1_000"`
      - [ ] `test_bigint_rejects_leading_plus` — `"+1"`, `"+0"`
      - [ ] `test_bigint_rejects_unicode_decimal_digits` — `"１２"`, `"-１"`
      - [ ] `test_bigint_rejects_leading_zeroes` — `"01"`, `"007"`, `"-01"`
      - [ ] `test_bigint_rejects_negative_zero` — `"-0"`
      - [ ] `test_bigint_rejects_none` — unit-level test. Note: Strawberry strips `null` before calling `parse_value` for nullable input positions, so this code path is reachable only through (a) non-nullable inputs where Strawberry catches `None` before `_parse_bigint` runs and (b) direct unit-test calls. Tested for defense in depth so a future reader doesn't try to remove the parser's `None` check as "unreachable".
    - Public-export smoke (M5 coverage):
      - [ ] `test_bigint_is_importable_from_top_level` — `from django_strawberry_framework import BigInt`; assert `BigInt is not None`. Cheap insurance against an `__init__.py` import-order regression. **Type-shape assertions intentionally avoided**: `strawberry.types.scalar.ScalarWrapper` is an undocumented internal Strawberry path that could refactor without breaking documented behavior; the schema-execution tests downstream catch any "BigInt isn't actually usable as a scalar" regression with stronger signal.
    - Deprecation suppression (B1 coverage):
      - [ ] `test_package_import_does_not_emit_strawberry_deprecation_warning` — **subprocess-based** test running `python -W error::DeprecationWarning -c "import django_strawberry_framework"`, asserts `returncode == 0`. See [Decision 7](#decision-7--test-strategy) for the implementation pattern and why `importlib.reload` is *not* used. Catches both (a) future refactors that accidentally remove the suppression filter and (b) Strawberry tightening the deprecation into a hard error.
  - [ ] Field-mapping tests in `tests/types/test_converters.py` (extending the existing file; all via `schema.execute_sync`; follow the [Schema test fixture pattern](#decision-7--test-strategy)):
    - [ ] `test_big_integer_field_maps_to_bigint_in_schema`
    - [ ] `test_big_integer_field_nullable_in_schema`
    - [ ] `test_positive_big_integer_field_maps_to_bigint_in_schema` — pins the **changed** behavior
    - [ ] `test_big_auto_field_still_maps_to_int`
    - [ ] `test_bigint_serializes_query_result_as_string_via_schema_execution`
    - [ ] `test_bigint_parses_string_argument_via_schema_execution`
    - [ ] `test_bigint_parses_int_argument_via_schema_execution`
    - [ ] `test_bigint_in_input_position_with_null_via_schema_execution`
    - [ ] `test_bigint_rejects_bool_argument_via_schema_execution` — confirms input parser fires through the schema path
    - [ ] `test_bigint_rejects_float_argument_via_schema_execution`
    - [ ] `test_bigint_resolver_returning_bool_raises_via_schema_execution` — B2 fix: confirms `_serialize_bigint` rejects non-`int` resolver return values at the schema boundary
- [ ] Slice 2: `JSONField` mapping
  - [ ] Add `models.JSONField: strawberry.scalars.JSON` to `SCALAR_MAP`
  - [ ] Drop the `JSONField` half of the JSON / HStore TODO comment
  - [ ] Tests in `tests/types/test_converters.py`
    - [ ] `test_json_field_maps_to_json_scalar_in_schema`
    - [ ] `test_json_field_nullable_in_schema`
    - [ ] `test_json_field_round_trips_dict_via_schema_execution`
- [ ] Slice 3: `ArrayField` recursion (sentinel-based)
  - [ ] Add `_resolve_array_field()` helper and module-level sentinel `_ARRAY_FIELD_CLS = _resolve_array_field()` per [Decision 4](#decision-4--lazy-import-via-module-level-sentinels)
  - [ ] Add `convert_scalar` branch guarded by `_ARRAY_FIELD_CLS is not None and isinstance(field, _ARRAY_FIELD_CLS)` per [Decision 2](#decision-2--arrayfield-dimensionality-cap-and-outer-choices-rejection)
  - [ ] Reject outer `choices` on `ArrayField` with `ConfigurationError` per [Decision 2](#decision-2--arrayfield-dimensionality-cap-and-outer-choices-rejection)
  - [ ] Drop the `ArrayField` TODO comment
  - [ ] Add fake-field test double `_FakeArrayField(models.Field)` in `tests/types/test_converters.py` per [Decision 7](#decision-7--test-strategy); test models hosting it declare `class Meta: managed = False; app_label = "tests"` so Django's system checks pass.
  - [ ] Each `_FakeArrayField`-based test calls `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)` *before* declaring the `DjangoType`. (See the [Schema test fixture pattern](#decision-7--test-strategy).)
  - [ ] Tests in `tests/types/test_converters.py`:
    - Helper-resolver coverage:
      - [ ] `test_resolve_array_field_returns_class_when_postgres_fields_importable`
      - [ ] `test_resolve_array_field_returns_none_when_postgres_fields_unimportable`
    - Sentinel-branch coverage (via `_FakeArrayField`):
      - [ ] `test_array_field_of_int_maps_to_list_int_via_fake_sentinel`
      - [ ] `test_array_field_of_char_maps_to_list_str_via_fake_sentinel`
      - [ ] `test_array_field_nullable_inner_via_fake_sentinel`
      - [ ] `test_array_field_outer_nullable_via_fake_sentinel`
      - [ ] `test_array_field_multidim_rejected_via_fake_sentinel`
      - [ ] `test_array_field_choices_inner_via_fake_sentinel`
      - [ ] `test_array_field_outer_choices_rejected_via_fake_sentinel`
      - [ ] `test_array_field_base_field_unsupported_type_raises`
      - [ ] `test_array_field_sentinel_none_path`
  - [ ] Optional gated test: `test_real_array_field_compatible_with_strawberry` — `pytest.importorskip("django.contrib.postgres.fields")`; declares a `DjangoType` with `ArrayField(IntegerField())` on a `managed = False` model, calls `finalize_django_types()`, introspects the schema via `__type`, asserts the field type is `[Int!]!`. **Introspection navigation note:** GraphQL introspection returns a nested `kind / ofType` chain (`NON_NULL → LIST → NON_NULL → SCALAR { name: "Int" }` for `[Int!]!`); walk it explicitly rather than asserting on `field.type.name` (which is `None` for wrapping types).
- [ ] Slice 4: `HStoreField` conditional registration via sentinel + `strawberry.scalars.JSON` target
  - [ ] Add `_resolve_hstore_field()` helper and module-level sentinel `_HSTORE_FIELD_CLS` per [Decision 4](#decision-4--lazy-import-via-module-level-sentinels)
  - [ ] Add `convert_scalar` branch guarded by `_HSTORE_FIELD_CLS is not None and isinstance(field, _HSTORE_FIELD_CLS)` returning `strawberry.scalars.JSON` per [Decision 5](#decision-5--hstorefield-wire-shape)
  - [ ] Reject outer `choices` on `HStoreField` with `ConfigurationError` per [Decision 5](#decision-5--hstorefield-wire-shape) (H1 fix — consistent with `ArrayField` outer-`choices` rejection in Decision 2)
  - [ ] **Do not** add `HStoreField` to `SCALAR_MAP`
  - [ ] Drop the `HStoreField` half of the JSON / HStore TODO comment
  - [ ] Add fake-field test double `_FakeHStoreField(models.Field)` in `tests/types/test_converters.py`; test models hosting it declare `class Meta: managed = False; app_label = "tests"`
  - [ ] Each `_FakeHStoreField`-based test calls `monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)` *before* declaring the `DjangoType`.
  - [ ] Tests in `tests/types/test_converters.py`:
    - Helper-resolver coverage:
      - [ ] `test_resolve_hstore_field_returns_class_when_postgres_fields_importable`
      - [ ] `test_resolve_hstore_field_returns_none_when_postgres_fields_unimportable`
    - Sentinel-branch coverage (via `_FakeHStoreField`):
      - [ ] `test_hstore_field_maps_to_json_scalar_via_fake_sentinel`
      - [ ] `test_hstore_field_nullable_via_fake_sentinel`
      - [ ] `test_hstore_field_resolver_dict_serializes_via_schema_execution` — resolver returns a hand-built `dict` (no DB persistence; SQLite cannot store HStore values); test name clarifies this is a serializer-level test
      - [ ] `test_hstore_field_resolver_dict_with_none_value_via_schema_execution` — resolver returns `{"k1": "v", "k2": None}`; pins that `JSON` accepts `None` values inside the dict (mirrors `HStoreField`'s native `dict[str, str | None]` shape)
      - [ ] `test_hstore_field_outer_choices_rejected_via_fake_sentinel` — declares `_FakeHStoreField(choices=[("a", "A")])`; asserts `ConfigurationError` is raised at type creation (H1 fix)
      - [ ] `test_hstore_field_sentinel_none_path` — monkey-patch sentinel to `None`
  - [ ] Optional gated test: `test_real_hstore_field_compatible_with_strawberry` — `pytest.importorskip("django.contrib.postgres.fields")`; declares a `DjangoType` with `HStoreField()` on a `managed = False` model, calls `finalize_django_types()`, introspects the schema, asserts the field type is `JSON!` (introspection chain: `NON_NULL → SCALAR { name: "JSON" }`; walk the `kind / ofType` structure explicitly), **and** exercises a resolver returning `{"k1": "v", "k2": None}` via `schema.execute_sync`, asserting the dict shape including the `None` value is preserved in the response.
- [ ] Slice 5: Atomic version-bump quintet (single commit). **Deliberate scope note:** the quintet covers programmatically-checked version sites — `pyproject.toml`, `__init__.py`, `tests/base/test_init.py`'s pinned `__version__`, the `docs/GLOSSARY.md` "Current package version" line, and `uv.lock`. The two consumer-facing version strings (`README.md #", single-maintainer, alpha-quality."` and `docs/README.md #"**Shipped today**"`) are deferred to Slice 6 so the atomic-bump commit stays scoped to sites where staleness causes CI / introspection failures. The result is a controlled inconsistency between Slice 5 landing and Slice 6 closing: PyPI metadata reads `0.0.6` but `README.md` / `docs/README.md` still say `0.0.5`. The PyPI publish gate in [Definition of done](#definition-of-done) closes this gap.
  - [ ] `pyproject.toml` — `version = "0.0.5"` → `version = "0.0.6"`
  - [ ] `django_strawberry_framework/__init__.py` — `__version__ = "0.0.5"` → `__version__ = "0.0.6"`
  - [ ] `tests/base/test_init.py` — update pinned `__version__` assertion to `"0.0.6"`
  - [ ] `docs/GLOSSARY.md` — update "Current package version: `0.0.5`" line to `0.0.6`
  - [ ] `uv.lock` — re-lock with `uv lock`; the lockfile's package-version line moves from `0.0.5` to `0.0.6`
- [ ] Slice 6: Docs, KANBAN, CHANGELOG, archive (separate commit; may follow Slice 5 by any interval). **Size note:** this is the largest commit of the six — ~7 files with substantive markdown rewrites (including the verbatim DONE-013 body + the verbatim TODO-045 body for KANBAN.md). Consider opening as a draft PR via `gh pr create --draft` for staged review before merge. **Optional fallback:** if reviewer feedback flags the commit size during the PR, split into Slice 6a (shipped-state propagation: DONE-013 body + `docs/GLOSSARY.md` + `docs/README.md` + root `README.md` + `docs/TREE.md` + `TODAY.md` + `CHANGELOG.md` + spec archive) and Slice 6b (forward-look: `WIP-ALPHA-020-0.0.7` card creation in `KANBAN.md`). The shipped-state half is reviewable independently from the forward-look half.
  - [ ] Root `README.md` — update the package-version line (`README.md #", single-maintainer, alpha-quality."`) from `0.0.5` to `0.0.6`
  - [ ] `docs/README.md` — update the "shipped today is `0.0.5`" line (`docs/README.md #"**Shipped today**"`) to `0.0.6`; **move specialized scalar conversions out of the "Coming in `0.1.0`" callouts (`docs/README.md #"Coming in `0.1.0`"`)** into shipped/current-capability text
  - [ ] `docs/TREE.md` — add `django_strawberry_framework/scalars.py` to the current package layout (near `converters.py` under `docs/TREE.md #"## django_strawberry_framework (current on-disk layout)"`) and to the target package layout (near `docs/TREE.md #"## django_strawberry_framework (target package layout)"`)
  - [ ] `docs/GLOSSARY.md` entries updated:
    - [Specialized scalar conversions][glossary-specialized-scalar-conversions] → `shipped (0.0.6)`. **Replace the existing line at `docs/GLOSSARY.md #"PostgreSQL HStoreField → dict[str, str | None]"`** (currently reads `PostgreSQL HStoreField → dict[str, str | None] (soft-registered, only when django.contrib.postgres is installed)`) with `PostgreSQL HStoreField → strawberry.scalars.JSON (soft-registered, only when django.contrib.postgres.fields imports successfully)`. Update the `PositiveBigIntegerField` bullet to read `→ BigInt`.
    - [`BigInt` scalar][glossary-bigint-scalar] → `shipped (0.0.6)`. **Entry text** (drop-in for the dev): "JSON-safe scalar typically used to map Django's 64-bit integer fields `BigIntegerField` and `PositiveBigIntegerField` (not `BigAutoField`). Technically arbitrary-precision: serialized via Python `str(int_value)`, which handles any `int`. Wire format is a decimal string to survive GraphQL's signed 32-bit `Int` boundary (executing a query returning an `int`-annotated value past `2**31 - 1` raises a `GraphQLError` with message containing `Int cannot represent non 32-bit signed integer value`). Strict parser accepts Python `int` (excluding `bool`) and strings matching `^(0|-?[1-9][0-9]*)$` — plain ASCII decimal, optional leading minus for non-zero, no leading zeroes (except `"0"` itself), no underscores, no plus sign, no Unicode digits. Strict serializer rejects `bool`, `float`, `str`, `Decimal`, and any non-`int` type with `TypeError`. Part of [Specialized scalar conversions](#specialized-scalar-conversions)."
    - [Scalar field conversion][glossary-scalar-field-conversion] → add the new field-type bullets; note the `PositiveBigIntegerField` change.
    - [Index][glossary-index] → update status badges for the two flipped entries.
    - [Public exports][glossary-public-exports] → add `BigInt`. Note: the import path is now clean — no Strawberry deprecation warning escapes (the deprecation is suppressed at the definition site in `scalars.py`).
  - [ ] `TODAY.md` — expand the "What fakeshop model fields work today" section with the four new scalars.
  - [ ] `KANBAN.md` — move `DONE-013-0.0.6` → `DONE-013-0.0.6`. **Drop in the verbatim body below**:

    ```markdown
    ### DONE-013-0.0.6 — Deferred scalar conversions

    Slice-by-slice scope (per `docs/SPECS/spec-013-deferred_scalars-0_0_6.md`):

    - Public `BigInt` scalar (`django_strawberry_framework/scalars.py`, `NewType`-based) with the Strawberry class-direct-to-`scalar()` `DeprecationWarning` suppressed at the definition site so consumers see no warning at import time.
    - Strict `BigInt` parser via regex `^(0|-?[1-9][0-9]*)$` — rejects `bool`, `float`, empty / whitespace-padded strings, non-decimal strings, underscores, plus signs, leading zeroes, `-0`, and Unicode digits.
    - Strict `BigInt` serializer — rejects `bool`, `float`, `str`, `Decimal`, and any non-`int` type with `TypeError`.
    - `BigIntegerField → BigInt` and `PositiveBigIntegerField → BigInt` in `SCALAR_MAP`. `BigAutoField` preserved as `int` (no current-day override recourse; wait for WIP-ALPHA-015).
    - `JSONField → strawberry.scalars.JSON` in `SCALAR_MAP`.
    - `ArrayField` and `HStoreField` mapped via sentinel-guarded branches in `convert_scalar`. `HStoreField` not added to `SCALAR_MAP`.
    - `ArrayField` rejects nested arrays and outer `choices` with `ConfigurationError`.
    - `SCALAR_MAP`'s declared value type widened from `dict[type[models.Field], type]` to `dict[type[models.Field], Any]`.
    - `BigInt` added to `django_strawberry_framework.__all__`; `tests/base/test_init.py`'s pinned `__all__` and `__version__` assertions updated.
    - Atomic version-bump quintet: `pyproject.toml`, `__init__.py`, `tests/base/test_init.py`, `docs/GLOSSARY.md` package-version line, `uv.lock`.
    - 100% coverage via `tests/test_scalars.py` (new flat file) and `tests/types/test_converters.py` (extended). Includes a `test_package_import_does_not_emit_strawberry_deprecation_warning` guard so future regressions to the suppression are explicit.
    - Docs: `docs/GLOSSARY.md`, `docs/README.md`, `README.md`, `docs/TREE.md`, `TODAY.md`, `CHANGELOG.md`.

    Design notes carried into `0.0.6`:

    - The internal Strawberry deprecation about passing a class (or `NewType`) to `strawberry.scalar(...)` is suppressed at the definition site (tight `warnings.catch_warnings()` filter). The package import surface is therefore clean. Migration to a `StrawberryConfig.scalar_map`-based design is roadmapped as `WIP-ALPHA-020-0.0.7` — that path is a real public-API change (consumers using `BigInt` directly will merge a package-provided `StrawberryConfig` into their `strawberry.Schema(...)`), not an internal-only refactor.
    ```
  - [ ] `KANBAN.md` — also **add the new card** `WIP-ALPHA-020-0.0.7` to the "To Do - Alpha (0.1.0)" column, in the 0.0.7 cluster (after `WIP-ALPHA-019-0.0.7 — Multi-database cooperation contract`). **Append at NNN 045** (the next available identifier; current max is `TODO-STABLE-046-1.0.0`). NNN sequence does not need to be contiguous within a version cluster — KANBAN's grouping is by version, not by NNN, so appending at NNN 045 with target `0.0.7` is the correct shape. (A previous draft of this spec offered a "renumber 020-044 → 021-045" option for NNN cluster-adjacency; that path is a multi-file cascading rename across 5+ files and 50+ string sites with stale-link risk for any external doc/PR/CHANGELOG citing a card NNN. Don't do it.) **Drop in the verbatim body below** (four-backtick outer fence so the inner Python code block renders correctly):

    > "See `KANBAN.md` for the current `WIP-ALPHA-020-0.0.7` card body — the verbatim drop-in below was used for the initial card creation in this commit and may be out of date once the follow-up spec evolves the card."

  - [ ] `CHANGELOG.md` — `[Unreleased]` entries (**permission granted by this spec**, overriding [`AGENTS.md`][agents]'s default prohibition):
    - `Added`: `BigInt` (public export), `JSONField → JSON` and `HStoreField → JSON` mappings, `ArrayField` recursion.
    - `Changed`: `PositiveBigIntegerField` mapping switched from `int` to `BigInt` (breaking wire-format change).
    - `Notes`: "The internal `BigInt` scalar definition uses `strawberry.scalar(NewType, ...)`, which Strawberry deprecates in favor of `StrawberryConfig.scalar_map`. The deprecation warning is suppressed at the definition site so the package import remains clean. Migration to a `scalar_map`-based design is tracked as a follow-up and will be a real public-API change for consumers using `BigInt` directly."
  - [ ] **Before archiving**, strip the inline `WIP-ALPHA-020-0.0.7` card body from this spec's Slice 6 (the fenced ` ```markdown ` block above) and replace it with a one-line pointer:

    > "See `KANBAN.md` for the current `WIP-ALPHA-020-0.0.7` card body — the verbatim drop-in below was used for the initial card creation in this commit and may be out of date once the follow-up spec evolves the card."

    This prevents the archived spec from drifting against the live `KANBAN.md` card as the follow-up card's body evolves (open design questions resolve, additional context lands). The inline `DONE-013-0.0.6` body above can stay — it's a historical record of what shipped, not a live evolving card.
  - [ ] Archive this spec to `docs/SPECS/spec-013-deferred_scalars-0_0_6.md`.

## Problem statement

[`docs/GLOSSARY.md`'s Scalar field conversion entry][glossary-scalar-field-conversion] advertises broad Django scalar coverage but explicitly defers four: plain `BigIntegerField`, `JSONField`, PostgreSQL `ArrayField`, and PostgreSQL `HStoreField`. The deferral has lived in `types/converters.py` as three TODO comments (in the `types/converters.py::SCALAR_MAP` neighborhood). This card converts those TODOs into shipped behavior.

Five constraints shape the design:

1. **`BigInt` has to survive GraphQL's `Int` boundary.** GraphQL's standard `Int` is **signed 32-bit** (range `-2_147_483_648` to `2_147_483_647`). Executing a query that returns an `int`-annotated field whose value exceeds that range yields a `GraphQLError` with message containing `Int cannot represent non 32-bit signed integer value` (the live error appends the offending value) — before the value reaches a JavaScript client. JavaScript's 53-bit precision limit is the secondary justification.
2. **`ArrayField` and `HStoreField` are PostgreSQL-only.** The dev environment does not include a postgres driver, so `django.contrib.postgres.fields` fails to import at module load time.
3. **`HStoreField` cannot be expressed as a typed map in GraphQL.** Strawberry rejects `dict[str, str | None]`. The annotation has to go through `strawberry.scalars.JSON`.
4. **Strawberry's `strawberry.scalar(...)` API is in a deprecated state for the "pass a class" pattern.** Both `strawberry.scalar(int, ...)` and `strawberry.scalar(NewType("BigInt", int), ...)` emit `DeprecationWarning: Passing a class to strawberry.scalar() is deprecated. Use StrawberryConfig.scalar_map instead...`. The recommended replacement (`scalar_map`) *can* be selective when keyed by a dedicated `NewType` — verified by probe. The blocker for adopting `scalar_map` here is that it requires package-owned schema configuration: consumers cannot use `BigInt` as a direct annotation without merging a package-provided `StrawberryConfig` into their own `strawberry.Schema(...)`. That touches `docs/README.md` quickstart, `GOAL.md` schema setup, and the public-API story. Out of scope for this card; the deprecation is **suppressed at the `BigInt` definition site** in `scalars.py` (tight `warnings.catch_warnings()` filter) so consumers see no warning at import time. Migration to `scalar_map` is tracked as a follow-up.
5. **Public scalar discipline.** A public scalar needs strict parsing **and** strict serialization. `serialize=str` would accept any object (including `True`, `1.9`, `Decimal(...)`) and silently stringify it — schemas could emit values the parser would reject. This card ships both `_parse_bigint` (input) and `_serialize_bigint` (output) with symmetric strictness.

## Current state

`SCALAR_MAP` (`django_strawberry_framework/types/converters.py::SCALAR_MAP`) is a flat `dict[type[models.Field], type]` covering Django's standard scalar field classes. `convert_scalar` walks `type(field).__mro__` and returns the matched type, optionally widening to `T | None` and replacing with a generated `Enum` when `field.choices` is present.

Three TODO blocks near `types/converters.py::SCALAR_MAP` mark the deferred work. The current `SCALAR_MAP` entry for `PositiveBigIntegerField: int` is **technically incorrect** — `PositiveBigIntegerField` is a 64-bit field whose values can exceed GraphQL's 32-bit `Int` range.

No `BigInt` symbol exists yet. No public scalars module exists. No `tests/test_scalars.py` file exists.

## Goals

- Map `BigIntegerField` → `BigInt` and `PositiveBigIntegerField` → `BigInt`.
- Map `JSONField` → `strawberry.scalars.JSON`.
- Map `ArrayField(base_field)` → `list[converted_base_field_type]`, sentinel-guarded.
- Reject outer `choices` on `ArrayField` and nested `ArrayField` with `ConfigurationError`. Reject outer `choices` on `HStoreField` with `ConfigurationError` (symmetric with the ArrayField rejection — HStore's dict shape has no enum-able GraphQL representation; see [Decision 5](#decision-5--hstorefield-wire-shape)).
- Map `HStoreField` → `strawberry.scalars.JSON`, sentinel-guarded.
- Add `BigInt` to the package's public surface with both strict parser and strict serializer. Suppress Strawberry's class-direct-to-`scalar()` `DeprecationWarning` at the definition site so the package import remains clean.
- Widen `SCALAR_MAP`'s declared value type to `dict[type[models.Field], Any]`.
- 100% coverage on the new conversion paths.

## Non-goals

- **No new `Meta` key.**
- **No filter / order / aggregate input shapes for the new scalars.**
- **No multi-dimensional `ArrayField` support.**
- **No outer `choices` on `ArrayField` or `HStoreField`.** Both rejected with `ConfigurationError` — declare `choices` on `base_field` for ArrayField element-level enum, or model the constrained shape with a separate field for HStore.
- **No dedicated `HStore` scalar.**
- **No change to `BigAutoField`'s mapping.** Stays `int`; no current-day recourse — wait for WIP-ALPHA-015.
- **No postgres driver added to dev dependencies.**
- **No `StrawberryConfig.scalar_map` integration in this card.** Tracked as a follow-up; would be a real public-API change for consumers using `BigInt` directly. See [Risks](#risks-and-open-questions).
- **No int64 range enforcement on `BigInt`.** The scalar is technically arbitrary-precision (Python `int` plus regex-validated decimal strings) — it accepts values past `2**63 - 1` even though the Django source columns top out there. Range enforcement at the scalar level is a separate concern (out of scope; consumers wanting a hard 64-bit cap can validate in their resolver or `clean` method).

## Architectural decisions

### Decision 1 — `BigInt` wire format and target fields

`BigInt` serializes as a **decimal string** at the wire and parses through a strict validator. Definition lives in `django_strawberry_framework/scalars.py`:

```python
# django_strawberry_framework/scalars.py
import re
import warnings
from typing import Any, NewType

import strawberry


# Plain ASCII decimal, optional ASCII minus for non-zero values, no leading
# zeroes except "0" itself. Rejects underscores (PEP 515), plus signs, Unicode
# decimal digits, hex / octal / scientific notation, and whitespace.
_BIGINT_STRING_PATTERN = re.compile(r"^(0|-?[1-9][0-9]*)$")


def _parse_bigint(value: Any) -> int:
    """Strict BigInt parser.

    Accepts:
        - Python int (excluding bool)
        - Decimal integer strings matching ``^(0|-?[1-9][0-9]*)$``.

    Rejects (with ValueError):
        - bool (True / False) — bool subclasses int; explicit reject
        - float (1.9, 0.0, -1.0) — would otherwise truncate via int()
        - empty / whitespace-padded strings
        - underscore-separated digits ("1_000")
        - leading-plus strings ("+1")
        - leading-zero strings ("01", "007")
        - "-0" (regex permits "0" only)
        - Unicode decimal digits ("１２")
        - non-decimal strings ("abc", "1.9", "1e3", "0x10")
        - None and other types
    """
    if isinstance(value, bool):
        raise ValueError("BigInt does not accept boolean values")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if not _BIGINT_STRING_PATTERN.fullmatch(value):
            raise ValueError(
                f"BigInt requires a plain ASCII decimal integer string "
                f"(optional leading minus for non-zero, no leading zeroes, "
                f"no underscores, no plus sign, no Unicode digits); got {value!r}"
            )
        return int(value)
    raise ValueError(f"BigInt cannot parse {type(value).__name__}")


def _serialize_bigint(value: Any) -> str:
    """Strict BigInt serializer.

    Accepts:
        - Python int (excluding bool)

    Rejects (with TypeError):
        - bool (True / False) — bool subclasses int; explicit reject
        - float, str, Decimal, None, custom objects, anything else

    Strict on the output side too because BigInt is a public scalar — a
    permissive `serialize=str` would let a schema emit values the parser
    rejects, breaking the input/output symmetry contract.
    """
    if isinstance(value, bool):
        raise TypeError(f"BigInt cannot serialize bool value {value!r}")
    if isinstance(value, int):
        return str(value)
    raise TypeError(f"BigInt cannot serialize {type(value).__name__}")


# Strawberry emits `DeprecationWarning: Passing a class to strawberry.scalar() is
# deprecated. Use StrawberryConfig.scalar_map instead...` whenever a class or
# NewType-backed type is passed directly to strawberry.scalar(...). The
# warning-free migration is roadmapped as WIP-ALPHA-020-0.0.7 (Warning-free
# scalar registration via StrawberryConfig.scalar_map). That card will introduce
# a package-side `strawberry_config(...)` factory and remove this suppression
# block entirely. For 0.0.6, the deprecation is suppressed at the definition
# site so consumers importing django_strawberry_framework see no warning. A
# regression test (test_package_import_does_not_emit_strawberry_deprecation_warning)
# pins the no-leak contract; if the suppression is accidentally removed or
# Strawberry tightens the deprecation, the test catches it.
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message="Passing a class to strawberry.scalar",
        category=DeprecationWarning,
    )
    BigInt = strawberry.scalar(
        NewType("BigInt", int),
        name="BigInt",
        serialize=_serialize_bigint,
        parse_value=_parse_bigint,
    )
```

Primary justification for `BigInt`: **GraphQL's `Int` is a signed 32-bit scalar.** Executing a query that returns an `int`-annotated field whose value exceeds `2**31 - 1` yields a `GraphQLError` with message containing `Int cannot represent non 32-bit signed integer value`.

Why the strict parser: `parse_value=int` is too permissive — `int(True) == 1`, `int(False) == 0`, and `int(1.9) == 1` (silent truncation). The regex `^(0|-?[1-9][0-9]*)$` is also stricter than `int(str)`: it rejects `"1_000"`, `"+1"`, `"01"`, `"-0"`, and Unicode-digit strings.

Why the strict serializer: `serialize=str` would accept `True`/`1.9`/`Decimal(...)`/arbitrary objects and stringify them. A schema would emit values the parser rejects, breaking input/output symmetry. `_serialize_bigint` raises `TypeError` for non-`int` resolver returns; the GraphQL boundary surfaces that as an error.

Why the deprecation suppression: Strawberry's class-direct-to-`scalar()` `DeprecationWarning` is an internal Strawberry concern about how the scalar is defined. The consumer-facing `BigInt` symbol and its wire behavior are unaffected. Letting the warning escape would mean every consumer importing `django_strawberry_framework` (even those who never use `BigInt`) sees the warning, and consumers running under `-W error::DeprecationWarning` cannot import the package at all. Tight scoping at the definition site keeps the public surface clean.

**Range:** `BigInt` is technically arbitrary-precision (Python `int` plus regex-validated decimal strings, with no upper bound check). In practice it is *used to map* Django's 64-bit integer fields, so the API table targets `BigIntegerField` and `PositiveBigIntegerField`. Consumers needing a hard 64-bit range cap can validate in their resolver.

Target Django fields:

- `BigIntegerField` → `BigInt` (new). Always.
- `PositiveBigIntegerField` → `BigInt` (changed from `int`). Explicit `SCALAR_MAP` entry for regression protection.
- `BigAutoField` → `int` (preserved). No current-day consumer recourse for the `2**31` boundary — wait for [Scalar field override semantics][glossary-scalar-field-override-semantics].

### Decision 2 — `ArrayField` dimensionality cap and outer-`choices` rejection

Reject nested arrays and outer `choices` at type creation with `ConfigurationError`. `ArrayField(IntegerField())` works; `ArrayField(ArrayField(IntegerField()))` and `ArrayField(IntegerField(), choices=[...])` both raise.

```python
# in convert_scalar, before the SCALAR_MAP walk:
if _ARRAY_FIELD_CLS is not None and isinstance(field, _ARRAY_FIELD_CLS):
    if isinstance(field.base_field, _ARRAY_FIELD_CLS):
        raise ConfigurationError(
            f"Nested ArrayField on {field.model.__name__}.{field.name} is not supported."
        )
    if field.choices:
        raise ConfigurationError(
            f"ArrayField on {field.model.__name__}.{field.name} declares choices on the outer "
            f"field; outer-array choices are ambiguous at the GraphQL boundary. Declare choices "
            f"on base_field for element-level enum, or use FilterSet."
        )
    inner = convert_scalar(field.base_field, type_name)
    result = list[inner]
    return result | None if field.null else result
```

**Choice handling on `base_field` is inherited automatically:** the recursive `convert_scalar(field.base_field, type_name)` call re-enters and hits the existing `if field.choices` branch, producing `list[<TypeName><FieldName>Enum]`. The outer-`choices` rejection only fires for the outer `ArrayField` itself.

`null=True` semantics: outer `null=True` → `list[T] | None`; inner `null=True` → `list[T | None]`; both → `list[T | None] | None`.

### Decision 3 — `JSONField` target type

Map `models.JSONField` → `strawberry.scalars.JSON`.

### Decision 4 — Lazy import via module-level sentinels

```python
def _resolve_array_field() -> type[models.Field] | None:
    try:
        from django.contrib.postgres.fields import ArrayField
    except ImportError:
        return None
    return ArrayField


def _resolve_hstore_field() -> type[models.Field] | None:
    try:
        from django.contrib.postgres.fields import HStoreField
    except ImportError:
        return None
    return HStoreField


_ARRAY_FIELD_CLS: type[models.Field] | None = _resolve_array_field()
_HSTORE_FIELD_CLS: type[models.Field] | None = _resolve_hstore_field()
```

Module-load assignment only exercises one branch per environment. Helper-resolver tests via `sys.modules` manipulation cover the other branch unconditionally.

### Decision 5 — `HStoreField` wire shape

Map `HStoreField` → `strawberry.scalars.JSON`. Strawberry rejects `dict[str, str | None]` as an annotation. `HStoreField` is **not** added to `SCALAR_MAP`; instead it gets a sentinel-guarded branch in `convert_scalar`, mirroring Decision 2's shape:

```python
# in convert_scalar, after the ArrayField branch, before the SCALAR_MAP walk:
if _HSTORE_FIELD_CLS is not None and isinstance(field, _HSTORE_FIELD_CLS):
    if field.choices:
        # HStoreField stores a dict[str, str | None]; choices on the outer field
        # would constrain "which dict values are allowed", which has no clean
        # GraphQL representation (the wire shape is JSON, not an enum-able scalar).
        # Reject for the same reason ArrayField outer-choices are rejected in
        # Decision 2 — loud over silent, consistent with the package's posture.
        raise ConfigurationError(
            f"HStoreField on {field.model.__name__}.{field.name} declares choices; "
            f"HStore stores a dict[str, str | None] with no enum-able shape at the "
            f"GraphQL boundary. Drop the choices declaration or model the constrained "
            f"shape with a separate field."
        )
    py_type = strawberry.scalars.JSON
    return py_type | None if field.null else py_type
```

**Why reject `choices` rather than ignore:**

- Consistent with the ArrayField outer-`choices` rejection (Decision 2).
- Loud over silent: ambiguous configuration surfaces at type-creation time instead of producing a schema that emits values the consumer didn't expect.
- Django allows declaring `choices` on `HStoreField` syntactically (for admin/form widget purposes), but the constraint is form-only — not enforced at the column level. The rejection forces the consumer to model the constrained shape explicitly.

### Decision 6 — `BigInt` public-export status and migration contract

`BigInt` becomes a public export (`from django_strawberry_framework import BigInt`). [`docs/GLOSSARY.md`'s Public exports][glossary-public-exports] entry gains the new symbol. The pinned `__all__` assertion in `tests/base/test_init.py` is updated in Slice 1.

**Import-time warning posture:** Strawberry's class-direct-to-`scalar()` `DeprecationWarning` is **suppressed at the definition site** in `scalars.py` (tight `warnings.catch_warnings()` filter). Consumers importing the package — directly or transitively — see no warning. The suppression is documented in code comments and verified by `test_package_import_does_not_emit_strawberry_deprecation_warning`.

**Migration contract for the warning-free follow-up.** This is the honest version (revision 7 correction):

- *In `0.0.6`*: `BigInt` is a Strawberry `ScalarWrapper` (the return value of `strawberry.scalar(NewType(...))`). It works as a direct field annotation without any schema config — `category: BigInt` in a `DjangoType` or `@strawberry.field` works as-is.
- *In the warning-free follow-up* (post-`0.0.6`, when the package provides a `StrawberryConfig` helper): `BigInt` may become a bare `NewType` (or stay as a `ScalarWrapper` exported alongside a config helper). Consumers using `BigInt` directly will need to merge a package-provided `StrawberryConfig(scalar_map={...})` into their `strawberry.Schema(...)` call. A bare `NewType("BigInt", int)` annotation without `scalar_map` fails Strawberry schema construction with `Unexpected type '...BigInt'` — verified by probe.

The follow-up is a **real public-API migration**, not an internal-only refactor. The package will need to document the migration step (deprecation period, a config-merge helper, a stable annotation path), which is exactly why the warning-free design needs its own spec rather than being folded into this card. Roadmapped as `WIP-ALPHA-020-0.0.7 — Warning-free scalar registration via StrawberryConfig.scalar_map` (added to KANBAN in Slice 6 of this card).

**Recommended starting point** for the follow-up (final shape settled in TODO-ALPHA-045's own spec; this spec author has thought through alternatives and pinned a vetted direction, but the follow-up author may react to new information — e.g., Strawberry adding first-class scalar-registration support, or implementation revealing that conflict-resolution forces a different API shape): a **factory function** `strawberry_config(extra_scalar_map=None) -> StrawberryConfig` returning a composed `StrawberryConfig` pre-populated with the package's scalar map. `BigInt` stays usable as a direct annotation. Composable with consumer extras (factory accepts `extra_scalar_map=...`). Forward-extensible for future package scalars (`Upload` from TODO-ALPHA-027 slots into the factory's internal map automatically). Consumer migration is a single-line change: add `config=strawberry_config()` to existing `strawberry.Schema(query=Query, ...)` calls. The TODO-ALPHA-045 card body — drafted verbatim in Slice 6 of this spec — explores this direction and enumerates the open design questions (helper module name, conflict-resolution behavior for colliding scalar-map keys, deprecation-window shape) for the follow-up spec to settle. (Note: `extra_extensions=` is deliberately *not* part of the factory signature — Strawberry extensions are passed to `strawberry.Schema(..., extensions=[...])`, not into `StrawberryConfig`. If extension composition becomes a real need, that's a separate helper returning a schema-construction bundle, not a `StrawberryConfig`.)

### Decision 7 — Test strategy

**Test file layout** (mirrors [`docs/TREE.md`][tree]):

- `tests/test_scalars.py` (new) — scalar wire-format, strict-parser, and strict-serializer tests for `BigInt`, plus the deprecation-suppression regression test. Mirrors the flat `django_strawberry_framework/scalars.py`.
- `tests/types/test_converters.py` (extended) — all field-mapping tests including sentinel-swap and `sys.modules` helper-resolver tests. Mirrors `django_strawberry_framework/types/converters.py`.

**Fake field doubles** (in `tests/types/test_converters.py`):

```python
class _FakeArrayField(models.Field):
    """Test double for ArrayField that does not require django.contrib.postgres.

    Mirrors Django's real ArrayField metadata propagation so base_field has
    model and name attributes when convert_scalar recurses into it. Required
    because convert_choices_to_enum reads field.model.__name__ and field.name
    to build enum_name = f"{type_name}{pascal_case(field.name)}Enum".
    """
    def __init__(self, base_field, **kwargs):
        super().__init__(**kwargs)
        self.base_field = base_field

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        self.base_field.set_attributes_from_name(name)
        self.base_field.model = cls


class _FakeHStoreField(models.Field):
    """Test double for HStoreField that does not require django.contrib.postgres.

    Tests must call
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)
    before declaring a DjangoType using this field; otherwise convert_scalar's
    HStore branch never dispatches.
    """
    pass
```

**Test-model `Meta` requirement**: every test model hosting `_FakeArrayField` or `_FakeHStoreField` declares `class Meta: managed = False; app_label = "tests"` (or a unique `app_label` per fixture — see "Synthetic-model declaration patterns" below for the pytest-xdist fallback). The `managed = False` flag tells Django the model has no migrated table: no migration is implied, and `MyModel.objects.create(...)` would fail at the database boundary. Implementers must instantiate test rows directly (`MyModel(field=value)`) — the spec's reasoning is the test-only-Python-shape contract, not a system-checks workaround. (A bare `models.Field` subclass with no `db_type` doesn't actually trigger `Model._meta.check()` warnings regardless of `managed`; the previous draft of this rationale was incorrect on that detail.)

**Sentinel-swap requirement**: every `_FakeArrayField` / `_FakeHStoreField`-based test must call `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)` (or `_HSTORE_FIELD_CLS`) *before* declaring the `DjangoType`. Without the swap, `convert_scalar` falls through to the unsupported-field `ConfigurationError`.

**Schema test fixture pattern** (the recipe every new schema-execution test follows):

Each existing test file under `tests/types/` declares its own `@pytest.fixture(autouse=True) def _isolate_registry()` that runs `registry.clear()` on entry and exit — see `tests/types/test_converters.py::_isolate_registry` (the file the new tests are added to), `tests/types/test_definition_order.py::_isolate_registry`, and `tests/types/test_resolvers.py::_isolate_registry`. There is **no shared `conftest.py`** for these fixtures. New tests added to an existing file inherit the autouse fixture automatically; new files must declare their own copy.

**Synthetic-model declaration patterns** (M1 — two precedents exist; pick deliberately):

- **In-function model declaration** — `tests/optimizer/test_walker.py::test_plan_relay_id_projects_attname_when_pk_is_relation #"class UserTarget(models.Model)"` declares model classes inside test functions with `class Meta: app_label = "tests"; managed = False`. This pattern works for sentinel-swap tests because `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)` and the type declaration can sit in the same function, keeping the swap and the conversion-trigger adjacent.
- **Session-scoped fixture** — `tests/types/test_converters.py::choice_fixture_model` uses a session-scoped `choice_fixture_model` fixture with a unique `app_label` (`"test_choice_enums"`) per fixture. Avoids Django "Model already registered" warnings under pytest-xdist or `--forked` re-collection.

For this card's tests, the in-function pattern is the natural fit: every fake-field test pairs a `monkeypatch.setattr` with a `DjangoType` declaration in the same function. Use unique-`app_label`-per-test (`app_label = "test_bigint"`, `app_label = "test_arrayfield"`, etc.) only if pytest-xdist warnings surface during CI.

Beyond fixtures and model patterns, every schema-execution test follows this sequence:

1. **Define synthetic test models** at module level (or inside the test, if the model is test-local). Test-only models declare `class Meta: managed = False; app_label = "tests"`.
2. **Apply sentinel monkey-patches** (where relevant) BEFORE declaring the `DjangoType` — `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)` etc. The converter's sentinel-guard branch checks the patched value at type-creation time.
3. **Define the `DjangoType` subclass** referencing the synthetic model. This registers it in the pending-types collection.
4. **Call `finalize_django_types()`** to resolve pending relations and apply the `strawberry.type` decoration. This is **mandatory** — without it, the `DjangoType` is not a usable Strawberry type, and `strawberry.Schema(...)` raises.
5. **Build the schema** with a `Query` root that exposes the type (typically a `@strawberry.field` returning a list or single instance via a hand-built resolver).
6. **Execute** via `schema.execute_sync("query { ... }")` and assert on `result.data` / `result.errors`.

Tests that need real model rows instantiate them directly (`MyModel(field=value)`) — `MyModel.objects.create(...)` would attempt a DB write on a non-migrated table. Tests that need a real table can use `connection.schema_editor()` to create/drop one in setup/teardown, but that's rarely needed for converter / scalar coverage.

**Helper-resolver tests** for `_resolve_*_field()` use `sys.modules` manipulation:

```python
def test_resolve_array_field_returns_class_when_postgres_fields_importable(monkeypatch):
    import sys
    import types as _types
    fake = _types.ModuleType("django.contrib.postgres.fields")
    fake.ArrayField = _FakeArrayField
    monkeypatch.setitem(sys.modules, "django.contrib.postgres.fields", fake)
    from django_strawberry_framework.types.converters import _resolve_array_field
    assert _resolve_array_field() is _FakeArrayField


def test_resolve_array_field_returns_none_when_postgres_fields_unimportable(monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, "django.contrib.postgres.fields", None)
    from django_strawberry_framework.types.converters import _resolve_array_field
    assert _resolve_array_field() is None
```

**Deprecation-suppression regression test** (`test_package_import_does_not_emit_strawberry_deprecation_warning`): uses **subprocess isolation** to avoid the `importlib.reload`-doesn't-reload-submodules trap (the `with warnings.catch_warnings()` block in `scalars.py` only executes on first import; reloading the top-level package finds `django_strawberry_framework.scalars` cached in `sys.modules` and skips the suppression-wrapped line, so an in-process reload-based test would observe zero warnings even if the suppression were removed). The robust mechanism:

```python
def test_package_import_does_not_emit_strawberry_deprecation_warning():
    """Pin that the package import surface is clean of Strawberry's
    class-direct-to-scalar() DeprecationWarning. Subprocess isolation avoids
    the importlib.reload-doesn't-reload-submodules trap.

    sys.executable is the venv's Python under `uv run pytest`, so the
    subprocess inherits the editable package install — no PATH / PYTHONPATH
    munging needed.
    """
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "-W", "error::DeprecationWarning", "-c",
         "import django_strawberry_framework"],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, (
        f"Importing the package under -W error::DeprecationWarning failed:\n"
        f"stderr: {result.stderr}"
    )
```

Returns exit code 0 with the spec's suppression pattern in place; returns non-zero if the suppression is removed or Strawberry tightens the deprecation into a hard error. Verified by the sr dev's local probe. No `sys.modules` munging, no `__warningregistry__` worries.

Coverage target: 100%.

### Decision 8 — `SCALAR_MAP` value type widening

Change `SCALAR_MAP`'s declared value type from `dict[type[models.Field], type]` to `dict[type[models.Field], Any]`. `strawberry.scalars.JSON` and `BigInt` are not plain `type`s — they're `NewType`-backed scalar wrappers.

## User-facing API

After this card ships, [`docs/GLOSSARY.md`'s Scalar field conversion entry][glossary-scalar-field-conversion] gains four new mappings and one changed mapping:

| Django field | Generated annotation | Notes |
|---|---|---|
| `BigIntegerField` | `BigInt` | **New.** Public scalar; string wire format; strict parser + serializer. |
| `PositiveBigIntegerField` | `BigInt` | **Changed** from `int`. Previous mapping triggered the GraphQL 32-bit `Int` error (message containing `Int cannot represent non 32-bit signed integer value`) past `2**31 - 1`. |
| `JSONField` | `strawberry.scalars.JSON` | **New.** |
| `ArrayField(IntegerField())` | `list[int]` | **New.** Postgres contrib soft-required. |
| `ArrayField(IntegerField(null=True))` | `list[int \| None]` | |
| `ArrayField(IntegerField(), null=True)` | `list[int] \| None` | |
| `ArrayField(IntegerField(), choices=[...])` | `ConfigurationError` | Outer `choices` rejected. |
| `HStoreField` | `strawberry.scalars.JSON` | **New.** Postgres contrib soft-required. |
| `HStoreField(choices=[...])` | `ConfigurationError` | Outer `choices` rejected (symmetric with ArrayField). |
| `BigAutoField` | `int` (unchanged) | Preserved for PK wire-format stability. |

Public exports gain `BigInt`. **Importing the package emits no Strawberry deprecation warning** — the warning is suppressed at the `BigInt` definition site (revision 7 fix). The internal use of `strawberry.scalar(NewType, ...)` is a Strawberry-internal concern; the consumer-facing `BigInt` symbol is unaffected.

## Implementation plan

Six slices, each landing in a separate commit:

### Slice 1 — `BigInt` scalar + 64-bit integer field mappings

Files: `django_strawberry_framework/scalars.py` (new — defines `_parse_bigint`, `_serialize_bigint`, and the `warnings.catch_warnings()`-wrapped `BigInt`), `django_strawberry_framework/__init__.py`, `tests/base/test_init.py` (`__all__` pin), `django_strawberry_framework/types/converters.py` (SCALAR_MAP entries, annotation widening, TODO removal), `tests/test_scalars.py` (new — parser, serializer, deprecation-suppression tests), `tests/types/test_converters.py` (extended — field-mapping tests via `schema.execute_sync`).

### Slice 2 — `JSONField` mapping

Files: `django_strawberry_framework/types/converters.py`, `tests/types/test_converters.py`.

### Slice 3 — `ArrayField` recursion (sentinel-based)

Files: `django_strawberry_framework/types/converters.py` (sentinel + branch + outer-`choices` rejection), `tests/types/test_converters.py` (`_FakeArrayField` double + tests).

### Slice 4 — `HStoreField` conditional registration via sentinel

Files: `django_strawberry_framework/types/converters.py` (sentinel + branch returning `JSON`), `tests/types/test_converters.py` (`_FakeHStoreField` double + tests).

### Slice 5 — Atomic version-bump quintet

Single commit; five files: `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `docs/GLOSSARY.md` package-version line, `uv.lock`.

### Slice 6 — Docs, KANBAN, CHANGELOG, archive

Separate commit. Files: root `README.md`, `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md` (entries beyond the version line), `TODAY.md`, `KANBAN.md` (move + verbatim body), `CHANGELOG.md` (`Added` / `Changed` / `Notes`), `docs/SPECS/spec-013-deferred_scalars-0_0_6.md` (archive this spec).

## Edge cases and constraints

- **`BigAutoField` stays mapped to `int`.** No current-day recourse for the `2**31` boundary.
- **`PositiveBigIntegerField` mapping changes.** Breaking wire-format change; documented in CHANGELOG.
- **`PositiveSmallIntegerField` and `PositiveIntegerField` stay `int`.** Ranges fit within GraphQL's 32-bit `Int`.
- **`PositiveBigIntegerField` MRO.** Explicit entry kept for regression protection; the MRO walk would already resolve correctly via `BigIntegerField: BigInt`.
- **`ArrayField` with `choices` on `base_field`** — handled by the recursive `convert_scalar` call.
- **`ArrayField` with `choices` on the outer field** — rejected with `ConfigurationError`.
- **`JSONField` with custom `encoder`.** Annotation is `JSON` regardless.
- **MRO walk for subclasses.** `ArrayField` / `HStoreField` are checked via sentinel guards *before* the MRO walk.
- **`from __future__ import annotations`.** New annotations survive stringified module imports.
- **`SCALAR_MAP` annotation widened.** Per Decision 8.
- **Strict parser tradeoffs.** Regex narrower than `int(str)` — predictability over leniency.
- **Strict serializer tradeoffs.** Resolver returning a non-`int` value raises at the schema boundary instead of silently stringifying. Consumers wanting permissive output can wrap the serializer at their layer; the package surface stays strict.
- **`BigInt` is arbitrary-precision** — see [Decision 1](#decision-1--bigint-wire-format-and-target-fields) for the canonical framing.
- **Custom `from_db_value` on a `BigIntegerField` subclass.** If a consumer subclasses `BigIntegerField` and overrides `from_db_value` to return a non-`int` Python value (e.g. a domain type like a money object), `_serialize_bigint` raises `TypeError` at the schema boundary — a behavioral change from a permissive `serialize=str` (which would have silently stringified the domain object via `__str__`). Not a regression of shipped behavior (`BigInt` is new in `0.0.6`), but worth documenting so consumers hitting this have a referenceable "we did this deliberately." Recourse: keep the column type-pure at the GraphQL boundary, or override the scalar annotation on the affected field once [Scalar field override semantics][glossary-scalar-field-override-semantics] (WIP-ALPHA-015) ships.

## Test plan

Two test files, both run unconditionally:

- **`tests/test_scalars.py`** (new) — `BigInt` wire-format, strict-parser, strict-serializer, and deprecation-suppression tests. Django setup not required for the parser/serializer unit tests; the deprecation test forces a re-import of the package.
- **`tests/types/test_converters.py`** (extended) — all field-mapping tests via the [Schema test fixture pattern](#decision-7--test-strategy), plus helper-resolver tests via `sys.modules` manipulation.

Per [`AGENTS.md`][agents], every new public field mapping has at least one `schema.execute_sync` test. Strict-parser and strict-serializer unit tests live in `tests/test_scalars.py`; reject paths also fire through schema execution in `tests/types/test_converters.py` to confirm strictness survives Strawberry's pipeline.

Test categories:

1. Scalar wire format (serializer round-trip including `0`, int64-min, int64-max).
2. Strict serializer positive cases (`int`, including zero, negative, int64-boundary values).
3. Strict serializer negative cases (`bool`, `float`, `str`, `Decimal`, `None`, custom object).
4. Strict parser positive cases (`int`, including zero, decimal strings including zero, int64-min/max strings).
5. Strict parser negative cases (bool, float, empty / whitespace-padded, non-decimal, underscores, leading-plus, leading-zero, `-0`, Unicode digits, None).
6. Annotation generation via schema introspection.
7. `null=True` widening via schema introspection.
8. Wire-level round-trip via `schema.execute_sync` (including `null` input position).
9. Inbound parsing via `schema.execute_sync` (string-form + int-form + null + reject paths).
10. Outbound serialization via `schema.execute_sync` (resolver returning `bool` raises).
11. Sentinel branch coverage via fake field classes + monkey-patched sentinels.
12. Helper-resolver branch coverage via `sys.modules` manipulation.
13. Choice composition on `base_field` of `_FakeArrayField`.
14. Outer-`choices` rejection on `_FakeArrayField`.
15. `base_field`-unsupported-type propagation through the recursive call.
16. Dimensionality rejection.
17. **Deprecation-suppression regression** — subprocess invocation `python -W error::DeprecationWarning -c "import django_strawberry_framework"` returns exit code 0 (no Strawberry class-direct-to-`scalar()` warning escapes the package import). Subprocess isolation avoids the `importlib.reload`-doesn't-reload-submodules trap; see [Decision 7](#decision-7--test-strategy).
18. HStore-with-`None`-value resolver test.
19. Optional real-postgres compatibility — `pytest.importorskip("django.contrib.postgres.fields")`; ArrayField introspects as `[Int!]!`; HStoreField introspects as `JSON!` AND resolver returning `{"k1": "v", "k2": None}` serializes through `schema.execute_sync` with the dict shape (including the `None`) preserved.

Coverage target: 100%.

## Doc updates

Per the slice checklist's Slice 6. The verbatim `BigInt` entry text and the verbatim `DONE-013-0.0.6` KANBAN body are drafted inline in the Slice 6 checklist.

## Risks and open questions

- **Strawberry deprecation suppressed at the `BigInt` definition site.** Tight `warnings.catch_warnings()` filter. Consumers see no warning at import time. A regression test (`test_package_import_does_not_emit_strawberry_deprecation_warning`, subprocess-based) catches both (a) accidental removal of the filter and (b) Strawberry tightening the deprecation into a hard error. Migration to `StrawberryConfig.scalar_map` is roadmapped as **`WIP-ALPHA-020-0.0.7 — Warning-free scalar registration via StrawberryConfig.scalar_map`** (added to KANBAN in Slice 6). **Thread-safety caveat:** Python docs note that `warnings.catch_warnings()` is *not* thread-safe. The package's use of it is single-threaded module-load (`scalars.py` first-import), protected by the CPython import lock, so this does not affect runtime. A future re-architecture that imports `scalars.py` from a worker thread (rare, but possible under hot-reload tools like `django-stubs`'s runserver or `pytest-watch`) would need to revisit.
- **`scalar_map` follow-up is a real public-API migration, not an internal refactor.** Under `scalar_map`, consumers using `BigInt` as a direct annotation will need to merge a package-provided `StrawberryConfig` into their `strawberry.Schema(...)`. A bare `NewType("BigInt", int)` without `scalar_map` fails Strawberry schema construction (verified by probe). The `WIP-ALPHA-020-0.0.7` card body — drafted inline in this spec's Slice 6 — explores the recommended architectural direction (factory function `strawberry_config(...)`, `BigInt` stays usable as a direct annotation, composable with consumer extras, forward-extensible for future package scalars). The follow-up will produce its own spec settling final design details, deprecation window, and migration guide.
- **`PositiveBigIntegerField` wire-format change.** Breaking for any current consumer; acceptable in alpha; documented in CHANGELOG. Override recourse arrives with WIP-ALPHA-015.
- **`BigAutoField` deliberately deferred.** PKs near `2**31` will hit GraphQL's `Int` boundary. No current-day recourse.
- **`HStoreField` and `JSONField` share `JSON`.** Schema clients cannot distinguish them at the GraphQL type level. Future dedicated `HStore` scalar possible.
- **`BigInt` name collision with Apollo Federation.** Post-`1.0.0` concern.
- **`BigInt` arbitrary precision** — see [Decision 1](#decision-1--bigint-wire-format-and-target-fields) for the canonical framing. If a real consumer needs a 64-bit-bounded variant, a follow-up card can add `BigInt64` or similar.
- **`ArrayField` of `DecimalField`.** Untested by this card; relies on inheritance from existing `DecimalField` tests + the recursion test.
- **Multi-dimensional `ArrayField`.** Rejected; lift in a future card if needed.
- **`T | None` syntax for `NewType` / `ScalarWrapper`.** Verified working on Python 3.10+ (`NewType.__or__` added alongside PEP 604; CI gates this).
- **`sys.modules` manipulation in helper-resolver tests.** `sys.modules[name] = None` forces `ImportError` — documented Python behavior, low risk.
- **Strict serializer tradeoffs.** Symmetric with the strict parser. Public-scalar discipline. See Decision 1.
- **`tests/types/test_converters.py` size growth.** This card adds ~28 tests (~700 lines) to a file currently at ~420 lines, bringing it to roughly ~1100 lines after Slice 4. If the file later exceeds ~1500 lines, file a follow-up to extend the [`docs/TREE.md`][tree] mirror rule with a concern-specific test-file convention (e.g., `tests/types/test_converters_scalars.py`).

## Out of scope (explicitly tracked elsewhere)

- Filter input shapes — [`FilterSet`][glossary-filterset], TODO-ALPHA-021-0.0.8.
- Mutation input types for `BigInt` — [Mutations subsystem][glossary-djangomutation], TODO-ALPHA-028-0.0.11.
- Multi-database routing — [Multi-database cooperation][glossary-multi-database-cooperation], WIP-ALPHA-019-0.0.7.
- Multi-dimensional `ArrayField`.
- Dedicated `HStore` scalar.
- `BigAutoField` → `BigInt`.
- Consumer-facing scalar annotation overrides — DONE-015-0.0.6.
- Strawberry-deprecation-free `BigInt` definition (via `StrawberryConfig.scalar_map` + a package-provided config helper) — roadmapped as `WIP-ALPHA-020-0.0.7`.
- `BigInt64`-bounded variant of `BigInt`.

## Definition of done

- All six slices land per the [Slice checklist](#slice-checklist).
- Test suite green, coverage at 100%.
- All TODO comments for deferred scalars removed.
- `SCALAR_MAP`'s value type annotation widened to `Any`.
- Atomic version-bump quintet aligned at `0.0.6`.
- Root `README.md`, `docs/README.md`, `docs/TREE.md`, `TODAY.md`, `CHANGELOG.md`, `KANBAN.md` (with both the verbatim `DONE-013-0.0.6` body AND the new `WIP-ALPHA-020-0.0.7` card body added to To-Do) all reflect shipped state.
- `docs/GLOSSARY.md` updated entries: [Specialized scalar conversions][glossary-specialized-scalar-conversions], [`BigInt` scalar][glossary-bigint-scalar], [Scalar field conversion][glossary-scalar-field-conversion], [Index][glossary-index], [Public exports][glossary-public-exports].
- `BigInt` strict parser **and strict serializer** unit-tested in `tests/test_scalars.py` and exercised at schema-execution level in `tests/types/test_converters.py`.
- Deprecation-suppression pinned via `test_package_import_does_not_emit_strawberry_deprecation_warning` (subprocess-based).
- `ArrayField` outer-`choices` rejection tested.
- `HStoreField` outer-`choices` rejection tested.
- `BigInt` top-level import smoke-tested (`test_bigint_is_importable_from_top_level`).
- Spec archived to `docs/SPECS/spec-013-deferred_scalars-0_0_6.md`.
- **PyPI publish gate** — do not `uv publish` the `0.0.6` distribution until Slice 6 closes. Published artifacts must not ship with stale `README.md` / `docs/README.md` / `CHANGELOG.md` / `KANBAN.md` (the controlled inconsistency between Slice 5 and Slice 6 stays inside the repo; PyPI sees the consistent end-state).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[contributing]: ../../CONTRIBUTING.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[glossary-bigint-scalar]: ../GLOSSARY.md#bigint-scalar
[glossary-choice-enum-generation]: ../GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-djangomutation]: ../GLOSSARY.md#djangomutation
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-index]: ../GLOSSARY.md#index
[glossary-metaexclude]: ../GLOSSARY.md#metaexclude
[glossary-multi-database-cooperation]: ../GLOSSARY.md#multi-database-cooperation
[glossary-public-exports]: ../GLOSSARY.md#public-exports
[glossary-scalar-field-conversion]: ../GLOSSARY.md#scalar-field-conversion
[glossary-scalar-field-override-semantics]: ../GLOSSARY.md#scalar-field-override-semantics
[glossary-specialized-scalar-conversions]: ../GLOSSARY.md#specialized-scalar-conversions
[tree]: ../TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
