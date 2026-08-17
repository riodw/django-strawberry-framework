# Spec: Deferred scalar conversions

Target release: `0.0.6`.
Status: shipped in `0.0.6`.
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [Scalar field conversion][glossary-scalar-field-conversion], [Specialized scalar conversions][glossary-specialized-scalar-conversions], [`BigInt` scalar][glossary-bigint-scalar]), [`KANBAN.md`][kanban] card `DONE-017-0.0.6`.
Card line: ["Add `BigInt` scalar with string serialization and `int` parsing. Add `JSONField` mapping to Strawberry JSON. Add `HStoreField` where available. Add `ArrayField` recursion through `field.base_field`. Use synthetic unmanaged test models where fakeshop does not naturally exercise the fields. Keep coverage at 100%."][kanban]

Deliberation, rejected alternatives, and the record of every change this spec's decisions have undergone live in [`spec-017-deferred_scalars-0_0_6-rationale.md`][spec-017-rationale]. This file states only the contract that holds at `HEAD`.

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
- [Scalar field override semantics][glossary-scalar-field-override-semantics] — the sibling `0.0.6` card (`DONE-019-0.0.6`). It supplies the consumer recourse for the `BigAutoField` mapping this card leaves at `int`.

Project conventions to follow:

- [`AGENTS.md`][agents] — schema testing via `schema.execute_sync`. **Note:** `AGENTS.md` prohibits `CHANGELOG.md` edits without explicit permission; [Slice 6](#slice-6--docs-kanban-changelog-archive) grants that permission.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; release-bump checklist.
- [`KANBAN.md`][kanban] — Card ID format; column movement at Slice 6.
- [`docs/TREE.md`][tree] — package layout convention; tests mirror source one-to-one.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan).

- [ ] Slice 1: `BigInt` scalar + 64-bit integer field mappings
  - [ ] Add `django_strawberry_framework/scalars.py` defining `_parse_bigint`, `_serialize_bigint`, and `BigInt` per [Decision 1](#decision-1--bigint-wire-format-and-target-fields). Importing `django_strawberry_framework` must emit no Strawberry `DeprecationWarning`.
  - [ ] Re-export `BigInt` from `django_strawberry_framework/__init__.py`. **Exact `__all__` tuple after the change**:
    ```python
    __all__ = (
        "BigInt",
        "[DjangoOptimizerExtension][glossary-djangooptimizerextension]",
        "DjangoType",
        "[OptimizerHint][glossary-optimizerhint]",
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
    - Warning-free import (B1 coverage):
      - [ ] `test_package_import_does_not_emit_strawberry_deprecation_warning` — **subprocess-based** test running `python -W error::DeprecationWarning -c "import django_strawberry_framework"`, asserts `returncode == 0`. See [Decision 7](#decision-7--test-strategy) for the implementation pattern and why `importlib.reload` is *not* used. Catches a future refactor that reintroduces a deprecated `strawberry.scalar(...)` overload on the package's import path.
  - [ ] Field-mapping tests (all via schema execution; package-tier tests follow the [Schema test fixture pattern](#decision-7--test-strategy), live-tier tests hit `/graphql/` over HTTP per [Decision 7](#decision-7--test-strategy)):
    - [ ] `examples/fakeshop/test_query/test_scalars_api.py::test_scalar_specimen_introspects_bigint_scalar_for_both_fields` — `BigIntegerField` and `PositiveBigIntegerField` (the **changed** mapping) each introspecting as `BigInt` in both the non-null and nullable shapes
    - [ ] `tests/types/test_converters.py::test_big_auto_field_still_maps_to_int`
    - [ ] `examples/fakeshop/test_query/test_scalars_api.py::test_scalar_specimen_every_field_wire_format_over_http` — `BigInt` query results serialize as decimal strings past the JS safe-integer boundary
    - [ ] `examples/fakeshop/test_query/test_scalars_api.py::test_scalar_specimen_bigint_input_decimal_string_argument_over_http`
    - [ ] `examples/fakeshop/test_query/test_scalars_api.py::test_scalar_specimen_bigint_input_int_literal_argument_over_http`
    - [ ] `tests/types/test_converters.py::test_bigint_in_input_position_with_null_via_schema_execution`
    - [ ] `tests/types/test_converters.py::test_bigint_rejects_bool_argument_via_schema_execution` — confirms input parser fires through the schema path
    - [ ] `tests/types/test_converters.py::test_bigint_rejects_float_argument_via_schema_execution`
    - [ ] `tests/types/test_converters.py::test_bigint_resolver_returning_bool_raises_via_schema_execution` — B2 fix: confirms `_serialize_bigint` rejects non-`int` resolver return values at the schema boundary
- [ ] Slice 2: `JSONField` mapping
  - [ ] Add `models.JSONField: strawberry.scalars.JSON` to `SCALAR_MAP`
  - [ ] Drop the `JSONField` half of the JSON / HStore TODO comment
  - [ ] Tests at the live `/graphql/` tier in `examples/fakeshop/test_query/test_scalars_api.py`
    - [ ] `test_scalar_specimen_introspects_json_scalar_in_both_shapes` — `JSONField` introspects as `JSON` in both the non-null and nullable shapes
    - [ ] `test_scalar_specimen_every_field_wire_format_over_http` — a mixed-primitive dict (string, int, list, JSON `null`, nested bool) round-trips verbatim
- [ ] Slice 3: `ArrayField` recursion (sentinel-based)
  - [ ] Add the module-level sentinel `_ARRAY_FIELD_CLS`, soft-imported through the package's shared optional-import owner per [Decision 4](#decision-4--soft-import-via-module-level-sentinels)
  - [ ] Add `convert_scalar` branch guarded by `_ARRAY_FIELD_CLS is not None and isinstance(field, _ARRAY_FIELD_CLS)` per [Decision 2](#decision-2--arrayfield-dimensionality-cap-and-outer-choices-rejection)
  - [ ] Reject outer `choices` on `ArrayField` with `ConfigurationError` per [Decision 2](#decision-2--arrayfield-dimensionality-cap-and-outer-choices-rejection)
  - [ ] Drop the `ArrayField` TODO comment
  - [ ] Add fake-field test double `_FakeArrayField(models.Field)` in `tests/types/test_converters.py` per [Decision 7](#decision-7--test-strategy); test models hosting it declare `class Meta: managed = False; app_label = "tests"` so Django's system checks pass.
  - [ ] Each `_FakeArrayField`-based test calls `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)` *before* declaring the `DjangoType`. (See the [Schema test fixture pattern](#decision-7--test-strategy).)
  - [ ] Tests in `tests/types/test_converters.py`:
    - Soft-import branch coverage: owned by the shared helper's own tests (`tests/utils/test_imports.py`), not duplicated here — see [Decision 4](#decision-4--soft-import-via-module-level-sentinels).
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
  - [ ] Add the module-level sentinel `_HSTORE_FIELD_CLS`, soft-imported through the package's shared optional-import owner per [Decision 4](#decision-4--soft-import-via-module-level-sentinels)
  - [ ] Add `convert_scalar` branch guarded by `_HSTORE_FIELD_CLS is not None and isinstance(field, _HSTORE_FIELD_CLS)` returning `strawberry.scalars.JSON` per [Decision 5](#decision-5--hstorefield-wire-shape)
  - [ ] Reject outer `choices` on `HStoreField` with `ConfigurationError` per [Decision 5](#decision-5--hstorefield-wire-shape) (H1 fix — consistent with `ArrayField` outer-`choices` rejection in Decision 2)
  - [ ] **Do not** add `HStoreField` to `SCALAR_MAP`
  - [ ] Drop the `HStoreField` half of the JSON / HStore TODO comment
  - [ ] Add fake-field test double `_FakeHStoreField(models.Field)` in `tests/types/test_converters.py`; test models hosting it declare `class Meta: managed = False; app_label = "tests"`
  - [ ] Each `_FakeHStoreField`-based test calls `monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)` *before* declaring the `DjangoType`.
  - [ ] Tests in `tests/types/test_converters.py`:
    - Soft-import branch coverage: owned by the shared helper's own tests (`tests/utils/test_imports.py`), not duplicated here — see [Decision 4](#decision-4--soft-import-via-module-level-sentinels).
    - Sentinel-branch coverage (via `_FakeHStoreField`):
      - [ ] `test_hstore_field_maps_to_json_scalar_via_fake_sentinel`
      - [ ] `test_hstore_field_nullable_via_fake_sentinel`
      - [ ] `test_hstore_field_resolver_dict_serializes_via_schema_execution` — resolver returns a hand-built `dict` (no DB persistence; SQLite cannot store HStore values); test name clarifies this is a serializer-level test
      - [ ] `test_hstore_field_resolver_dict_with_none_value_via_schema_execution` — resolver returns `{"k1": "v", "k2": None}`; pins that `JSON` accepts `None` values inside the dict (mirrors `HStoreField`'s native `dict[str, str | None]` shape)
      - [ ] `test_hstore_field_outer_choices_rejected_via_fake_sentinel` — declares `_FakeHStoreField(choices=[("a", "A")])`; asserts `ConfigurationError` is raised at type creation (H1 fix)
      - [ ] `test_hstore_field_sentinel_none_path` — monkey-patch sentinel to `None`
  - [ ] Optional gated test: `test_real_hstore_field_compatible_with_strawberry` — `pytest.importorskip("django.contrib.postgres.fields")`; declares a `DjangoType` with `HStoreField()` on a `managed = False` model, calls `finalize_django_types()`, introspects the schema, asserts the field type is `JSON!` (introspection chain: `NON_NULL → SCALAR { name: "JSON" }`; walk the `kind / ofType` structure explicitly), **and** exercises a resolver returning `{"k1": "v", "k2": None}` via `schema.execute_sync`, asserting the dict shape including the `None` value is preserved in the response.
- [ ] Slice 5: Atomic version-bump quintet (single commit). The quintet covers the programmatically-checked version sites — `pyproject.toml`, `__init__.py`, `tests/base/test_init.py`'s pinned `__version__`, the `docs/GLOSSARY.md` "Current package version" line, and `uv.lock` — where staleness causes CI or introspection failures. The two consumer-facing version strings (`README.md #", single-maintainer, alpha-quality."` and `docs/README.md #"**Shipped today**"`) land in Slice 6, so the tree carries a deliberate version-string gap between Slice 5 landing and Slice 6 closing. The PyPI publish gate in [Definition of done](#definition-of-done) forbids publishing inside that gap.
  - [ ] `pyproject.toml` — `version = "0.0.5"` → `version = "0.0.6"`
  - [ ] `django_strawberry_framework/__init__.py` — `__version__ = "0.0.5"` → `__version__ = "0.0.6"`
  - [ ] `tests/base/test_init.py` — update pinned `__version__` assertion to `"0.0.6"`
  - [ ] `docs/GLOSSARY.md` — update "Current package version: `0.0.5`" line to `0.0.6`
  - [ ] `uv.lock` — re-lock with `uv lock`; the lockfile's package-version line moves from `0.0.5` to `0.0.6`
- [ ] Slice 6: Docs, KANBAN, CHANGELOG, archive (separate commit; may follow Slice 5 by any interval). **Size note:** this is the largest commit of the six - ~7 files with substantive markdown rewrites (including the verbatim `DONE-017-0.0.6` body for `KANBAN.md`). Consider opening as a draft PR via `gh pr create --draft` for staged review before merge. **Optional fallback:** if reviewer feedback flags the commit size during the PR, split into Slice 6a (shipped-state propagation: the `DONE-017-0.0.6` body + `docs/GLOSSARY.md` + `docs/README.md` + root `README.md` + `docs/TREE.md` + `TODAY.md` + `CHANGELOG.md` + spec archive) and Slice 6b (forward-look: the `DONE-025-0.0.7` card creation in `KANBAN.md`). The shipped-state half is reviewable independently from the forward-look half.
  - [ ] Root `README.md` - update the package-version line (`README.md #", single-maintainer, alpha-quality."`) to the release this card ships in
  - [ ] `docs/README.md` - update the "Shipped today" line (`docs/README.md #"**Shipped today**"`) to the release this card ships in; **move specialized scalar conversions out of the "Coming in `0.1.0`" callouts** into shipped/current-capability text
  - [ ] `docs/TREE.md` - add `django_strawberry_framework/scalars.py` to the current package layout (near `converters.py` under `docs/TREE.md #"## django_strawberry_framework (current on-disk layout)"`) and to the target package layout (near `docs/TREE.md #"## django_strawberry_framework (target package layout)"`)
  - [ ] `docs/GLOSSARY.md` entries updated. `docs/GLOSSARY.md` is **generated** from the fakeshop glossary app's database (`scripts/build_glossary_md.py`): edit the database and re-render, never hand-edit the rendered markdown.
    - [Specialized scalar conversions][glossary-specialized-scalar-conversions] -> `shipped (0.0.6)`. **Replace the existing line at `docs/GLOSSARY.md #"PostgreSQL HStoreField"`** with `PostgreSQL HStoreField -> strawberry.scalars.JSON (soft-registered, only when django.contrib.postgres.fields imports successfully)`. Update the `PositiveBigIntegerField` bullet to read `-> BigInt`.
    - [`BigInt` scalar][glossary-bigint-scalar] -> `shipped (0.0.6)`. **Entry text** (drop-in for the dev): "JSON-safe scalar typically used to map Django's 64-bit integer fields `BigIntegerField` and `PositiveBigIntegerField` (not `BigAutoField`). Technically arbitrary-precision: serialized via Python `str(int_value)`, which handles any `int`. Wire format is a decimal string to survive GraphQL's signed 32-bit `Int` boundary (executing a query returning an `int`-annotated value past `2**31 - 1` raises a `GraphQLError` with message containing `Int cannot represent non 32-bit signed integer value`). Strict parser accepts Python `int` (excluding `bool`) and strings matching `^(0|-?[1-9][0-9]*)$` - plain ASCII decimal, optional leading minus for non-zero, no leading zeroes (except `"0"` itself), no underscores, no plus sign, no Unicode digits. Strict serializer rejects `bool`, `float`, `str`, `Decimal`, and any non-`int` type with `TypeError`. Part of [Specialized scalar conversions](#specialized-scalar-conversions)."
    - [Scalar field conversion][glossary-scalar-field-conversion] -> add the new field-type bullets; note the `PositiveBigIntegerField` change.
    - [Index][glossary-index] -> update status badges for the two flipped entries.
    - [Public exports][glossary-public-exports] -> add `BigInt`. Importing the package emits no Strawberry deprecation warning.
  - [ ] `TODAY.md` - expand the "What fakeshop model fields work today" section with the four new scalars.
  - [ ] `KANBAN.md` - flip the card to `DONE-017-0.0.6` and give it the shipped-state body. `KANBAN.md` is **generated** from the fakeshop kanban app's database (`scripts/build_kanban_md.py`): edit the database and re-render.
  - [ ] `KANBAN.md` - also **add the follow-up card** for warning-free scalar registration via `StrawberryConfig.scalar_map` to the To-Do Alpha column, in the `0.0.7` cluster. **Append at the next available NNN**; the NNN sequence does not need to be contiguous within a version cluster, because `KANBAN.md` groups by version, not by NNN. That card shipped as `DONE-025-0.0.7` (spec: [`spec-025-scalar_map_helper-0_0_7.md`][spec-025]); see `KANBAN.md` for its current body rather than reproducing it here, so this spec cannot drift against the live card.
  - [ ] `CHANGELOG.md` - `[Unreleased]` entries (**permission granted by this spec**, overriding [`AGENTS.md`][agents]'s default prohibition):
    - `Added`: `BigInt` (public export), `JSONField -> JSON` and `HStoreField -> JSON` mappings, `ArrayField` recursion.
    - `Changed`: `PositiveBigIntegerField` mapping switched from `int` to `BigInt` (breaking wire-format change).
  - [ ] Archive this spec to `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` and its `-terms.csv` / `-rationale.md` companions to `docs/SPECS/appx/`.

## Problem statement

[`docs/GLOSSARY.md`'s Scalar field conversion entry][glossary-scalar-field-conversion] advertises broad Django scalar coverage but explicitly defers four: plain `BigIntegerField`, `JSONField`, PostgreSQL `ArrayField`, and PostgreSQL `HStoreField`. The deferral has lived in `types/converters.py` as three TODO comments (in the `types/converters.py::SCALAR_MAP` neighborhood). This card converts those TODOs into shipped behavior.

Five constraints shape the design:

1. **`BigInt` has to survive GraphQL's `Int` boundary.** GraphQL's standard `Int` is **signed 32-bit** (range `-2_147_483_648` to `2_147_483_647`). Executing a query that returns an `int`-annotated field whose value exceeds that range yields a `GraphQLError` with message containing `Int cannot represent non 32-bit signed integer value` (the live error appends the offending value) — before the value reaches a JavaScript client. JavaScript's 53-bit precision limit is the secondary justification.
2. **`ArrayField` and `HStoreField` are PostgreSQL-only.** The dev environment does not include a postgres driver, so `django.contrib.postgres.fields` fails to import at module load time.
3. **`HStoreField` cannot be expressed as a typed map in GraphQL.** Strawberry rejects `dict[str, str | None]`. The annotation has to go through `strawberry.scalars.JSON`.
4. **Strawberry's `strawberry.scalar(...)` API is in a deprecated state for the "pass a class" pattern.** Both `strawberry.scalar(int, ...)` and `strawberry.scalar(NewType("BigInt", int), ...)` emit `DeprecationWarning: Passing a class to strawberry.scalar() is deprecated. Use StrawberryConfig.scalar_map instead...`. The package must therefore define `BigInt` on the non-deprecated path: a bare `NewType` plus a `ScalarDefinition` built from the `name=`-only `strawberry.scalar(...)` overload, registered through a package-provided `StrawberryConfig`. Importing `django_strawberry_framework` must emit no Strawberry `DeprecationWarning`. See [Decision 1](#decision-1--bigint-wire-format-and-target-fields) and [Decision 6](#decision-6--bigint-public-export-status-and-registration-contract).
5. **Public scalar discipline.** A public scalar needs strict parsing **and** strict serialization. `serialize=str` would accept any object (including `True`, `1.9`, `Decimal(...)`) and silently stringify it — schemas could emit values the parser would reject. This card ships both `_parse_bigint` (input) and `_serialize_bigint` (output) with symmetric strictness.

## Goals

- Map `BigIntegerField` → `BigInt` and `PositiveBigIntegerField` → `BigInt`.
- Map `JSONField` → `strawberry.scalars.JSON`.
- Map `ArrayField(base_field)` → `list[converted_base_field_type]`, sentinel-guarded.
- Reject outer `choices` on `ArrayField` and nested `ArrayField` with `ConfigurationError`. Reject outer `choices` on `HStoreField` with `ConfigurationError` (symmetric with the ArrayField rejection — HStore's dict shape has no enum-able GraphQL representation; see [Decision 5](#decision-5--hstorefield-wire-shape)).
- Map `HStoreField` → `strawberry.scalars.JSON`, sentinel-guarded.
- Add `BigInt` to the package's public surface with both strict parser and strict serializer, defined on Strawberry's non-deprecated registration path so the package import emits no `DeprecationWarning`.
- Widen `SCALAR_MAP`'s declared value type to `dict[type[models.Field], Any]`.
- 100% coverage on the new conversion paths.

## Non-goals

- **No new `Meta` key.**
- **No filter / order / aggregate input shapes for the new scalars.**
- **No multi-dimensional `ArrayField` support.**
- **No outer `choices` on `ArrayField` or `HStoreField`.** Both rejected with `ConfigurationError` — declare `choices` on `base_field` for ArrayField element-level enum, or model the constrained shape with a separate field for HStore.
- **No dedicated `HStore` scalar.**
- **No change to `BigAutoField`'s mapping.** Stays `int`; the consumer recourse for a PK past the 32-bit boundary is the annotation override shipped by the sibling card `DONE-019-0.0.6` ([Scalar field override semantics][glossary-scalar-field-override-semantics]).
- **No postgres driver added to dev dependencies.**
- **No consumer-facing schema-configuration surface beyond the `strawberry_config()` factory.** Extension composition, settings-backed auto-discovery of the config, and a deprecation shim for a pre-`scalar_map` `BigInt` spelling are all out of scope; see [`spec-025-scalar_map_helper-0_0_7.md`][spec-025].
- **No int64 range enforcement on `BigInt`.** The scalar is technically arbitrary-precision (Python `int` plus regex-validated decimal strings) — it accepts values past `2**63 - 1` even though the Django source columns top out there. Range enforcement at the scalar level is a separate concern (out of scope; consumers wanting a hard 64-bit cap can validate in their resolver or `clean` method).

## Architectural decisions

### Decision 1 — `BigInt` wire format and target fields

`BigInt` serializes as a **decimal string** at the wire and parses through a strict validator. Definition lives in `django_strawberry_framework/scalars.py`:

```python
# django_strawberry_framework/scalars.py
import re
from typing import Any, NewType

import strawberry
from strawberry.types.scalar import ScalarDefinition


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


# `BigInt` is a BARE NewType. Passing a class or NewType directly to
# strawberry.scalar(...) emits `DeprecationWarning: Passing a class to
# strawberry.scalar() is deprecated. Use StrawberryConfig.scalar_map
# instead...`, so the ScalarDefinition is built from the `name=`-only
# overload (no `cls` argument) and bound to the NewType through the
# package scalar map that `strawberry_config()` merges into a consumer's
# `strawberry.Schema(...)`. See Decision 6 for the registration contract.
BigInt = NewType("BigInt", int)

_BIGINT_SCALAR_DEFINITION: ScalarDefinition = strawberry.scalar(
    name="BigInt",
    serialize=_serialize_bigint,
    parse_value=_parse_bigint,
)

_PACKAGE_SCALAR_MAP: dict[object, ScalarDefinition] = {
    BigInt: _BIGINT_SCALAR_DEFINITION,
}
```

**Why `BigInt` exists at all:** GraphQL's `Int` is a signed 32-bit scalar. Executing a query that returns an `int`-annotated field whose value exceeds `2**31 - 1` yields a `GraphQLError` with message containing `Int cannot represent non 32-bit signed integer value`.

**The parser must reject rather than coerce.** `bool` is rejected before the `int` check because `bool` subclasses `int`; `float` is rejected outright because `int(1.9) == 1` truncates silently. The regex is deliberately narrower than `int(str)`, so `"1_000"`, `"+1"`, `"01"`, `"-0"`, and Unicode-digit strings raise instead of parsing.

**The serializer must be as strict as the parser.** `_serialize_bigint` raises `TypeError` for any non-`int` resolver return so a schema cannot emit a value its own parser would reject; the GraphQL boundary surfaces that as an error.

**Range:** `BigInt` is technically arbitrary-precision (Python `int` plus regex-validated decimal strings, with no upper bound check). In practice it is *used to map* Django's 64-bit integer fields, so the API table targets `BigIntegerField` and `PositiveBigIntegerField`. Consumers needing a hard 64-bit range cap can validate in their resolver.

Target Django fields:

- `BigIntegerField` → `BigInt` (new). Always.
- `PositiveBigIntegerField` → `BigInt` (changed from `int`). Explicit `SCALAR_MAP` entry for regression protection.
- `BigAutoField` → `int` (preserved) for PK wire-format stability. The consumer recourse for a PK past the `2**31` boundary is the annotation override shipped by the sibling card `DONE-019-0.0.6` ([Scalar field override semantics][glossary-scalar-field-override-semantics]).

### Decision 2 — `ArrayField` dimensionality cap and outer-`choices` rejection

Reject nested arrays and outer `choices` at type creation with `ConfigurationError`. `ArrayField(IntegerField())` works; `ArrayField(ArrayField(IntegerField()))` and `ArrayField(IntegerField(), choices=[...])` both raise.

```python
# in convert_scalar, before the SCALAR_MAP walk. ``effective_null`` is the
# tri-state ``force_nullable`` override collapsed to one boolean; see the
# nullability-override note below.
if _ARRAY_FIELD_CLS is not None and isinstance(field, _ARRAY_FIELD_CLS):
    if isinstance(field.base_field, _ARRAY_FIELD_CLS):
        raise ConfigurationError(
            f"Nested ArrayField on {_field_label(field)} is not supported.",
        )
    if _field_has_choices(field):
        raise ConfigurationError(
            f"ArrayField on {_field_label(field)} declares choices on the outer "
            f"field; outer-array choices are ambiguous at the GraphQL boundary. Declare choices "
            f"on base_field for element-level enum, or use FilterSet.",
        )
    inner = convert_scalar(field.base_field, type_name)
    result = list[inner]
    return result | None if effective_null else result
```

`_field_label(field)` and `_field_has_choices(field)` are the module's guarded metadata readers: they render `Model.field` for diagnostics and read the choices flag without letting a hostile field descriptor's exception escape as something other than a `ConfigurationError`. Interpolating `field.model.__name__` / `field.name` directly, or testing `field.choices` as a bare truth value, reintroduces that escape.

**Choice handling on `base_field` is inherited automatically:** the recursive `convert_scalar(field.base_field, type_name)` call re-enters and hits the existing choices branch, producing `list[<TypeName><FieldName>Enum]`. The outer-`choices` rejection only fires for the outer `ArrayField` itself.

`null=True` semantics: outer `null=True` → `list[T] | None`; inner `null=True` → `list[T | None]`; both → `list[T | None] | None`.

**Nullability override.** `convert_scalar` takes a keyword-only `force_nullable: bool | None = None` tri-state (the `Meta.nullable_overrides` / `Meta.required_overrides` seam). It is collapsed once, at the top of the function, into `effective_null = field.null if force_nullable is None else force_nullable`, and every outer widening site in this Decision and in [Decision 5](#decision-5--hstorefield-wire-shape) reads `effective_null`. The recursive `base_field` call above is deliberately left `force_nullable`-**unset**, so the outer override never reaches the inner element: inner nullability continues to follow `base_field.null`.

### Decision 3 — `JSONField` target type

Map `models.JSONField` → `strawberry.scalars.JSON`.

### Decision 4 — Soft import via module-level sentinels

Both postgres-only field classes are soft-imported once at module load into module-level sentinels, through the package's single optional-import owner (`django_strawberry_framework/utils/imports.py::import_attr_if_importable`) rather than a hand-rolled `try` / `except ImportError` per field:

```python
_ARRAY_FIELD_CLS: type[models.Field] | None = import_attr_if_importable(
    "django.contrib.postgres.fields",
    "ArrayField",
)
_HSTORE_FIELD_CLS: type[models.Field] | None = import_attr_if_importable(
    "django.contrib.postgres.fields",
    "HStoreField",
)
```

The helper's contract is what the sentinels rely on: `None` when `django.contrib.postgres.fields` is unimportable (so package import still succeeds on a dev environment with no postgres driver), and a loud `AttributeError` if that module *is* importable but lacks the named class — a broken environment that must fail rather than silently degrade into an unregistered field type.

Module-load assignment only exercises one branch per environment, so the importable / unimportable branch pair is covered **once**, at the helper, in `tests/utils/test_imports.py`. This module owns no soft-import branch of its own and must not grow a second copy of that coverage.

### Decision 5 — `HStoreField` wire shape

Map `HStoreField` → `strawberry.scalars.JSON`. Strawberry rejects `dict[str, str | None]` as an annotation. `HStoreField` is **not** added to `SCALAR_MAP`; instead it gets a sentinel-guarded branch in `convert_scalar`, mirroring Decision 2's shape:

```python
# in convert_scalar, after the ArrayField branch, before the SCALAR_MAP walk:
if _HSTORE_FIELD_CLS is not None and isinstance(field, _HSTORE_FIELD_CLS):
    if _field_has_choices(field):
        raise ConfigurationError(
            f"HStoreField on {_field_label(field)} declares choices; "
            f"HStore stores a dict[str, str | None] with no enum-able shape at the "
            f"GraphQL boundary. Drop the choices declaration or model the constrained "
            f"shape with a separate field.",
        )
    py_type = strawberry.scalars.JSON
    return py_type | None if effective_null else py_type
```

Django accepts `choices` on an `HStoreField` syntactically (for admin / form widget purposes), but the constraint is form-only and is not enforced at the column level — so a silently-ignored declaration would produce a schema emitting values the consumer did not expect. The rejection is symmetric with the `ArrayField` outer-`choices` rejection in [Decision 2](#decision-2--arrayfield-dimensionality-cap-and-outer-choices-rejection) and forces the consumer to model the constrained shape explicitly.

### Decision 6 — `BigInt` public-export status and registration contract

`BigInt` is a public export (`from django_strawberry_framework import BigInt`). [`docs/GLOSSARY.md`'s Public exports][glossary-public-exports] entry carries the symbol, and the pinned `__all__` assertion in `tests/base/test_init.py` includes it.

**Registration contract.** `BigInt` is a bare `NewType("BigInt", int)`. The scalar behavior lives in a separate `ScalarDefinition` bound to that `NewType` through the package scalar map, and a consumer reaches it by passing the package-provided config into their schema:

```python
import strawberry
from django_strawberry_framework import BigInt, strawberry_config

schema = strawberry.Schema(query=Query, config=strawberry_config())
```

A `BigInt` annotation in a schema built **without** `config=strawberry_config()` fails schema construction with `Unexpected type '...BigInt'`. That is the deliberate consequence of staying off Strawberry's deprecated class-direct-to-`scalar()` path: the annotation is inert until the scalar map registers it, rather than silently resolving to something else.

**Import-time warning posture:** importing `django_strawberry_framework` - directly or transitively - emits no Strawberry `DeprecationWarning`, and the package imports cleanly under `-W error::DeprecationWarning`. `test_package_import_does_not_emit_strawberry_deprecation_warning` pins that contract.

The [`strawberry_config`][glossary-strawberry-config] factory's own surface - the keyword-only `extra_scalar_map`, the `ValueError` on a key collision with a package-defined scalar, and the `**config_kwargs` passthrough - is specified by [`spec-025-scalar_map_helper-0_0_7.md`][spec-025], not here. This spec owns only the requirement that `BigInt` resolve through it.

### Decision 7 — Test strategy

**Test file layout** (mirrors [`docs/TREE.md`][tree]):

- `tests/test_scalars.py` (new) — scalar wire-format, strict-parser, and strict-serializer tests for `BigInt`, plus the warning-free-import regression test. Mirrors the flat `django_strawberry_framework/scalars.py`.
- `tests/types/test_converters.py` (extended) — the sentinel-swap field-mapping tests and the package-internal schema-execution tests. Mirrors `django_strawberry_framework/types/converters.py`.
- `examples/fakeshop/test_query/test_scalars_api.py` — the live `/graphql/` tier. Any mapping reachable from a real query against fakeshop is pinned HERE (per [`AGENTS.md`][agents]); the `apps.scalars` app carries the `ScalarSpecimen` / `NullableScalarSpecimen` pair whose `payload` (`JSONField`), `signed_big` (`BigIntegerField`), and `unsigned_big` (`PositiveBigIntegerField`) columns exercise every mapping this card adds that a SQLite-backed example can reach. `ArrayField` / `HStoreField` are postgres-only and stay at the package tier behind fake sentinels.

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

**Soft-import branch coverage** is NOT written here. Both sentinels resolve through the shared `utils/imports.py::import_attr_if_importable`, whose importable / unimportable / missing-attribute branches are covered once in `tests/utils/test_imports.py` (`sys.modules[name] = None` is the documented way to force the `ImportError` leg). Duplicating that pair against the converter's sentinels would test the helper twice and this module not at all.

**Warning-free-import regression test** (`test_package_import_does_not_emit_strawberry_deprecation_warning`): uses **subprocess isolation** rather than an in-process `importlib.reload`. `importlib.reload(django_strawberry_framework)` does not reload submodules - the reload finds `django_strawberry_framework.scalars` cached in `sys.modules` and never re-executes the scalar-definition line, so a reload-based test observes zero warnings whether or not the definition is on Strawberry's deprecated path, and cannot fail. The robust mechanism:

```python
def test_package_import_does_not_emit_strawberry_deprecation_warning():
    """Pin that the package import surface is clean of Strawberry's
    class-direct-to-scalar() DeprecationWarning. Subprocess isolation avoids
    the importlib.reload-doesn't-reload-submodules trap.

    sys.executable is the venv's Python under `uv run pytest`, so the
    subprocess inherits the editable package install - no PATH / PYTHONPATH
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

Returns exit code 0 while the package's scalar definitions stay off Strawberry's deprecated overloads; returns non-zero the moment one is reintroduced on the import path, or Strawberry tightens a deprecation the package still trips into a hard error. No `sys.modules` munging, no `__warningregistry__` worries.

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

Public exports gain `BigInt`. **Importing the package emits no Strawberry deprecation warning.** A `BigInt` annotation resolves only in a schema built with `config=strawberry_config()`; see [Decision 6](#decision-6--bigint-public-export-status-and-registration-contract).

## Implementation plan

Six slices, each landing in a separate commit:

### Slice 1 — `BigInt` scalar + 64-bit integer field mappings

Files: `django_strawberry_framework/scalars.py` (new — defines `_parse_bigint`, `_serialize_bigint`, `BigInt`, and the scalar definition / package scalar map), `django_strawberry_framework/__init__.py`, `tests/base/test_init.py` (`__all__` pin), `django_strawberry_framework/types/converters.py` (SCALAR_MAP entries, annotation widening, TODO removal), `tests/test_scalars.py` (new — parser, serializer, warning-free-import tests), `tests/types/test_converters.py` and `examples/fakeshop/test_query/test_scalars_api.py` (field-mapping tests via schema execution).

### Slice 2 — `JSONField` mapping

Files: `django_strawberry_framework/types/converters.py`, `tests/types/test_converters.py`.

### Slice 3 — `ArrayField` recursion (sentinel-based)

Files: `django_strawberry_framework/types/converters.py` (sentinel + branch + outer-`choices` rejection), `tests/types/test_converters.py` (`_FakeArrayField` double + tests).

### Slice 4 — `HStoreField` conditional registration via sentinel

Files: `django_strawberry_framework/types/converters.py` (sentinel + branch returning `JSON`), `tests/types/test_converters.py` (`_FakeHStoreField` double + tests).

### Slice 5 — Atomic version-bump quintet

Single commit; five files: `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `docs/GLOSSARY.md` package-version line, `uv.lock`.

### Slice 6 — Docs, KANBAN, CHANGELOG, archive

Separate commit. Files: root `README.md`, `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md` (entries beyond the version line), `TODAY.md`, `KANBAN.md` (move + verbatim body), `CHANGELOG.md` (`Added` / `Changed` / `Notes`), `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` (archive this spec).

## Edge cases and constraints

- **`BigAutoField` stays mapped to `int`.** A PK past the `2**31` boundary is handled by the consumer annotation override (`DONE-019-0.0.6`), not by this card.
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
- **Custom `from_db_value` on a `BigIntegerField` subclass.** If a consumer subclasses `BigIntegerField` and overrides `from_db_value` to return a non-`int` Python value (e.g. a domain type like a money object), `_serialize_bigint` raises `TypeError` at the schema boundary — a behavioral change from a permissive `serialize=str` (which would have silently stringified the domain object via `__str__`). Not a regression of shipped behavior (`BigInt` is new in `0.0.6`), but worth documenting so consumers hitting this have a referenceable "we did this deliberately." Recourse: keep the column type-pure at the GraphQL boundary, or override the scalar annotation on the affected field via [Scalar field override semantics][glossary-scalar-field-override-semantics] (`DONE-019-0.0.6`).

## Test plan

Two test files, both run unconditionally:

- **`tests/test_scalars.py`** (new) — `BigInt` wire-format, strict-parser, strict-serializer, and warning-free-import tests. Django setup not required for the parser/serializer unit tests; the import test runs a subprocess.
- **`tests/types/test_converters.py`** (extended) — the sentinel-guarded `ArrayField` / `HStoreField` mappings (postgres-only, unreachable from a real fakeshop query) and the package-internal reject paths, via the [Schema test fixture pattern](#decision-7--test-strategy).
- **`examples/fakeshop/test_query/test_scalars_api.py`** — the live `/graphql/` tier for every mapping a real fakeshop query reaches: `BigInt` and `JSON` annotation shape via introspection, nullable widening, wire round-trip, and string-form / int-form argument parsing.

Per [`AGENTS.md`][agents], every new public field mapping has at least one schema-execution test, and any mapping reachable from a real query against fakeshop is pinned at the live tier rather than by a synthetic package-tier substitute. Strict-parser and strict-serializer unit tests live in `tests/test_scalars.py`; reject paths also fire through schema execution in `tests/types/test_converters.py` to confirm strictness survives Strawberry's pipeline.

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
12. Soft-import branch coverage — owned by `tests/utils/test_imports.py`, not repeated here ([Decision 4](#decision-4--soft-import-via-module-level-sentinels)).
13. Choice composition on `base_field` of `_FakeArrayField`.
14. Outer-`choices` rejection on `_FakeArrayField`.
15. `base_field`-unsupported-type propagation through the recursive call.
16. Dimensionality rejection.
17. **Warning-free-import regression** — subprocess invocation `python -W error::DeprecationWarning -c "import django_strawberry_framework"` returns exit code 0 (no Strawberry class-direct-to-`scalar()` warning escapes the package import). Subprocess isolation avoids the `importlib.reload`-doesn't-reload-submodules trap; see [Decision 7](#decision-7--test-strategy).
18. HStore-with-`None`-value resolver test.
19. Optional real-postgres compatibility — `pytest.importorskip("django.contrib.postgres.fields")`; ArrayField introspects as `[Int!]!`; HStoreField introspects as `JSON!` AND resolver returning `{"k1": "v", "k2": None}` serializes through `schema.execute_sync` with the dict shape (including the `None`) preserved.

Coverage target: 100%.

## Doc updates

Per the slice checklist's Slice 6, which carries the verbatim [`BigInt` scalar][glossary-bigint-scalar] glossary entry text as a drop-in. The `KANBAN.md` card body is not reproduced here: `KANBAN.md` is generated from the fakeshop kanban database, and a verbatim copy in the spec would drift against the live card.

## Out of scope (explicitly tracked elsewhere)

- Filter input shapes — [`FilterSet`][glossary-filterset], DONE-027-0.0.8.
- Mutation input types for `BigInt` — [Mutations subsystem][glossary-djangomutation], DONE-036-0.0.11.
- Multi-database routing — [Multi-database cooperation][glossary-multi-database-cooperation], DONE-023-0.0.7.
- Multi-dimensional `ArrayField`.
- Dedicated `HStore` scalar.
- `BigAutoField` → `BigInt`.
- Consumer-facing scalar annotation overrides — DONE-019-0.0.6.
- The `strawberry_config()` factory's own surface (`extra_scalar_map`, collision policy, `**config_kwargs`) — [`spec-025-scalar_map_helper-0_0_7.md`][spec-025], `DONE-025-0.0.7`.
- Additional package-defined scalars slotting into the same package scalar map - [`Upload`][glossary-upload-scalar], `DONE-037-0.0.11`.
- `BigInt64`-bounded variant of `BigInt`.

## Definition of done

- All six slices land per the [Slice checklist](#slice-checklist).
- Test suite green, coverage at 100%.
- All TODO comments for deferred scalars removed.
- `SCALAR_MAP`'s value type annotation widened to `Any`.
- Atomic version-bump quintet aligned at `0.0.6`.
- Root `README.md`, `docs/README.md`, `docs/TREE.md`, `TODAY.md`, `CHANGELOG.md`, and `KANBAN.md` (the `DONE-017-0.0.6` body, plus the follow-up scalar-registration card in To-Do) all reflect shipped state.
- `docs/GLOSSARY.md` updated entries: [Specialized scalar conversions][glossary-specialized-scalar-conversions], [`BigInt` scalar][glossary-bigint-scalar], [Scalar field conversion][glossary-scalar-field-conversion], [Index][glossary-index], [Public exports][glossary-public-exports].
- `BigInt` strict parser **and strict serializer** unit-tested in `tests/test_scalars.py` and exercised at schema-execution level in `tests/types/test_converters.py`.
- Warning-free import pinned via `test_package_import_does_not_emit_strawberry_deprecation_warning` (subprocess-based).
- `ArrayField` outer-`choices` rejection tested.
- `HStoreField` outer-`choices` rejection tested.
- `BigInt` top-level import smoke-tested (`test_bigint_is_importable_from_top_level`).
- Spec archived to `docs/SPECS/spec-017-deferred_scalars-0_0_6.md`, with its `-terms.csv` and `-rationale.md` companions at `docs/SPECS/appx/`.
- **PyPI publish gate** — do not `uv publish` the `0.0.6` distribution until Slice 6 closes. Published artifacts must not ship with stale `README.md` / `docs/README.md` / `CHANGELOG.md` / `KANBAN.md` (the controlled inconsistency between Slice 5 and Slice 6 stays inside the repo; PyPI sees the consistent end-state).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[contributing]: ../../CONTRIBUTING.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary-bigint-scalar]: ../GLOSSARY.md#bigint-scalar
[glossary-choice-enum-generation]: ../GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-djangomutation]: ../GLOSSARY.md#djangomutation
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-index]: ../GLOSSARY.md#index
[glossary-metaexclude]: ../GLOSSARY.md#metaexclude
[glossary-multi-database-cooperation]: ../GLOSSARY.md#multi-database-cooperation
[glossary-optimizerhint]: ../GLOSSARY.md#optimizerhint
[glossary-public-exports]: ../GLOSSARY.md#public-exports
[glossary-scalar-field-conversion]: ../GLOSSARY.md#scalar-field-conversion
[glossary-scalar-field-override-semantics]: ../GLOSSARY.md#scalar-field-override-semantics
[glossary-specialized-scalar-conversions]: ../GLOSSARY.md#specialized-scalar-conversions
[glossary-strawberry-config]: ../GLOSSARY.md#strawberry_config
[glossary-upload-scalar]: ../GLOSSARY.md#upload-scalar
[glossary]: ../GLOSSARY.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-017-rationale]: appx/spec-017-deferred_scalars-0_0_6-rationale.md
[spec-025]: spec-025-scalar_map_helper-0_0_7.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
