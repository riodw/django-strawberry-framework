# Spec: Warning-free scalar registration via `StrawberryConfig.scalar_map`

Target release: `0.0.7` (per the [`KANBAN.md`](../KANBAN.md) card `WIP-ALPHA-020-0.0.7`; the card tag predates the 2026-05-23 `0.0.7` cut and this card now lands under the `[Unreleased]` area in [`CHANGELOG.md`](../CHANGELOG.md) on the way to the next patch — see [Decision 8](#decision-8--version-posture-cut-already-shipped-this-card-lands-under-unreleased)).
Status: in flight — Slice 1 unstarted at the time of writing.
Owner: package maintainer.
Predecessors: [`docs/SPECS/spec-013-deferred_scalars-0_0_6.md`](SPECS/spec-013-deferred_scalars-0_0_6.md) Decision 1 (the `BigInt` wire-format + `strawberry.scalar(NewType("BigInt", int), ...)` definition that introduced the suppressed deprecation), Decision 6 (the public-export contract for `BigInt`), and Risks (the explicit follow-up callout: "Migration to a `scalar_map`-based design is tracked as a follow-up and will be a real public-API change for consumers using `BigInt` directly"); [`docs/GLOSSARY.md`](GLOSSARY.md) entries [`BigInt scalar`](GLOSSARY.md#bigint-scalar) and [`Specialized scalar conversions`](GLOSSARY.md#specialized-scalar-conversions); [`CHANGELOG.md`](../CHANGELOG.md) `[0.0.6]` `### Notes` line (the literal "Migration to a `scalar_map`-based design is tracked as a follow-up" sentence this card pays down); [`KANBAN.md`](../KANBAN.md) card `WIP-ALPHA-020-0.0.7`.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft. Pins the canonical spec filename ([Decision 1](#decision-1--spec-filename-and-canonical-naming)), the helper API shape and module location ([Decision 2](#decision-2--helper-api-shape-and-module-location)), the `BigInt` redefinition as a bare `NewType` with the `ScalarDefinition` produced by `strawberry.scalar(name=..., serialize=..., parse_value=...)` (the no-warning overload at [`.venv/lib/python3.10/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`](../.venv/lib/python3.10/site-packages/strawberry/types/scalar.py)) ([Decision 3](#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition)), the conflict-resolution policy for `extra_scalar_map` collisions ([Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions)), the hard-break-in-alpha migration posture ([Decision 5](#decision-5--migration-posture-hard-break-in-alpha)), the suppression-removal contract ([Decision 6](#decision-6--remove-the-warningscatch_warnings-suppression-block)), the test placement strategy ([Decision 7](#decision-7--test-placement-and-shape)), the version posture for a post-cut card ([Decision 8](#decision-8--version-posture-cut-already-shipped-this-card-lands-under-unreleased)), and the example-app migration scope ([Decision 9](#decision-9--example-app-migration-scope)). Out of scope: composing extensions through this helper (the card body already calls this out — `extensions=` belongs on `strawberry.Schema(...)`, not `StrawberryConfig`; a future "schema-construction bundle" helper is a separate card if real demand surfaces); auto-discovery of the package config (a Django `settings`-backed default `STRAWBERRY_CONFIG_FACTORY = "django_strawberry_framework.scalars.strawberry_config"` shortcut) — deferred until the discovery story is needed; promoting `Upload` (the next package-defined scalar, planned for `0.0.11` per [`docs/GLOSSARY.md#upload-scalar`](GLOSSARY.md#upload-scalar)) — that card consumes this card's helper without modifying it.

## Key glossary references

> **Note (terms CSV completeness):** [`docs/spec-020-scalar_map_helper-0_0_7-terms.csv`](spec-020-scalar_map_helper-0_0_7-terms.csv) deliberately omits one term used throughout this spec: `strawberry_config`. The companion [`docs/GLOSSARY.md`](GLOSSARY.md) entry is created in [Slice 4](#implementation-plan) ([Doc updates](#doc-updates) pins the entry body); until that slice lands, the term has no glossary anchor to link, so it cannot be CSV-listed without failing the [`scripts/check_spec_glossary.py`](../scripts/check_spec_glossary.py) check. The companion `StrawberryConfig` symbol is upstream Strawberry (no package GLOSSARY entry; documented at [strawberry.rocks](https://strawberry.rocks)) and is also intentionally absent from the CSV for the same reason.

Skim these [`docs/GLOSSARY.md`](GLOSSARY.md) entries first — they anchor the vocabulary used throughout the spec:

- [`BigInt scalar`](GLOSSARY.md#bigint-scalar) — the scalar this card relocates from the `strawberry.scalar(NewType, ...)` definition path to the `StrawberryConfig.scalar_map` registration path. The wire format (decimal string via `_serialize_bigint`), strict parser (`^(0|-?[1-9][0-9]*)$` regex via `_parse_bigint`), and target Django fields (`BigIntegerField`, `PositiveBigIntegerField`) are preserved verbatim — this card changes the registration mechanism, not the scalar's semantics.
- [`Specialized scalar conversions`](GLOSSARY.md#specialized-scalar-conversions) — the entry that pins `BigIntegerField → BigInt` and `PositiveBigIntegerField → BigInt` in [`django_strawberry_framework/types/converters.py`](../django_strawberry_framework/types/converters.py); the converter table is untouched by this card because it references the `BigInt` symbol by name and the symbol's import path is unchanged.
- [`Scalar field conversion`](GLOSSARY.md#scalar-field-conversion) — the broader scalar-mapping contract; cited so the reader sees `BigInt` as one entry in a family of package-defined scalars rather than a one-off.
- [`Upload scalar`](GLOSSARY.md#upload-scalar) — the next package-defined scalar (planned for `0.0.11`). The helper this card ships is the registration point `Upload` will reuse; mentioning it here pins the forward-compatibility contract.
- [`DjangoType`](GLOSSARY.md#djangotype) — framing only; consumer-facing types that exercise `BigInt` through the converter table.
- [`DjangoOptimizerExtension`](GLOSSARY.md#djangooptimizerextension) — framing only; cited because the consumer migration pattern this card establishes (`config=strawberry_config(), extensions=[DjangoOptimizerExtension()]` side-by-side on `strawberry.Schema(...)`) covers the relationship between schema-level config and schema-level extensions.
- [`ConfigurationError`](GLOSSARY.md#configurationerror) — not raised by this card. The conflict-resolution policy in [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions) uses `ValueError` because the collision is a consumer-input mistake at helper-call time, not a `DjangoType`-creation or finalization-time configuration error.
- [`finalize_django_types`](GLOSSARY.md#finalize_django_types) — cited because the consumer-facing migration sequence (`strawberry.Schema(query=..., config=strawberry_config(), extensions=[DjangoOptimizerExtension()])` after `finalize_django_types()`) leaves the existing finalization-then-Schema order intact.

Project conventions to follow:

- [`AGENTS.md`](../AGENTS.md) — the test-placement rule at [`AGENTS.md #"package tests live under"`](../AGENTS.md) (package tests live under `tests/` with `__init__.py` shells in subdirectories like `tests/optimizer/`, example-project non-HTTP tests under `examples/fakeshop/tests/`, live HTTP tests under `examples/fakeshop/test_query/` and no `__init__.py` in either fakeshop test tree); the live-HTTP-priority rule at [`AGENTS.md #"any coverage line achievable via a real GraphQL query"`](../AGENTS.md); the no-pytest-after-edits rule at [`AGENTS.md #"Do not run pytest after edits"`](../AGENTS.md); the settings-keys rule at [`AGENTS.md #"Add settings keys only when the feature that needs them lands"`](../AGENTS.md). **Note:** the CHANGELOG-edit-permission rule at [`AGENTS.md #"Do not update CHANGELOG.md unless explicitly instructed"`](../AGENTS.md) prohibits [`CHANGELOG.md`](../CHANGELOG.md) edits without explicit permission; [Slice 5](#implementation-plan) grants that permission for this card's `[Unreleased]` entries.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — 100% coverage target.
- [`KANBAN.md`](../KANBAN.md) — card-ID format; column movement at Slice 5; the card body's `docs/spec-scalar_map_helper.md` reference predates the structured `spec-<NNN>-<topic>-<0_0_X>.md` convention and gets rewritten in the same sweep per [Decision 1](#decision-1--spec-filename-and-canonical-naming).
- [`docs/TREE.md`](TREE.md) — tests mirror source one-to-one. The helper lives in [`django_strawberry_framework/scalars.py`](../django_strawberry_framework/scalars.py) per [Decision 2](#decision-2--helper-api-shape-and-module-location); the mirror partner is [`tests/test_scalars.py`](../tests/test_scalars.py), which already exists — no new file under `tests/`.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan). Five slices total.

- [ ] Slice 1: Helper module + `BigInt` redefinition
  - [ ] [`django_strawberry_framework/scalars.py`](../django_strawberry_framework/scalars.py): redefine `BigInt` as a bare `NewType("BigInt", int)` (the deprecation-prone wrapping in `strawberry.scalar(NewType, ...)` is removed); add a module-level `_BIGINT_SCALAR_DEFINITION: ScalarDefinition` built via the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload (the `cls is None and name is not None` branch at [`.venv/lib/python3.10/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`](../.venv/lib/python3.10/site-packages/strawberry/types/scalar.py) returns a `ScalarDefinition` directly without emitting `DeprecationWarning`); add a module-level `_PACKAGE_SCALAR_MAP: dict[object, ScalarDefinition]` mapping the `BigInt` `NewType` to the definition; add the public `strawberry_config(extra_scalar_map: Mapping[object, ScalarDefinition] | None = None) -> StrawberryConfig` factory per [Decision 2](#decision-2--helper-api-shape-and-module-location); remove the `with warnings.catch_warnings(): warnings.filterwarnings("ignore", message="Passing a class to strawberry.scalar", ...)` block at the bottom of the file per [Decision 6](#decision-6--remove-the-warningscatch_warnings-suppression-block).
  - [ ] [`django_strawberry_framework/__init__.py`](../django_strawberry_framework/__init__.py): add `strawberry_config` to the explicit re-export list immediately after `BigInt` (the import line stays in the existing `from .scalars import BigInt` group, widened to `from .scalars import BigInt, strawberry_config`); add `"strawberry_config"` to `__all__` in the alphabetical position between `"OptimizerHint"` and `"__version__"`. `BigInt` stays in `__all__` (consistent with the recommended "BigInt as a direct annotation" usage pattern from the card body).
- [ ] Slice 2: Tests
  - [ ] [`tests/test_scalars.py`](../tests/test_scalars.py) (extend): add **one** new test section "`strawberry_config()` factory" with **eight** new tests pinning the helper's contract — `test_strawberry_config_returns_strawberry_config_instance`, `test_strawberry_config_default_scalar_map_includes_bigint`, `test_strawberry_config_accepts_none_extra_scalar_map`, `test_strawberry_config_accepts_empty_extra_scalar_map`, `test_strawberry_config_merges_extra_scalar_map`, `test_strawberry_config_extra_scalar_map_does_not_mutate_caller_dict`, `test_strawberry_config_collision_with_package_scalar_raises_value_error`, `test_strawberry_config_independent_call_returns_independent_instance` — see [Test plan](#test-plan) for the per-test contract. Tests use Strawberry's public `StrawberryConfig` / `ScalarDefinition` import surface (`from strawberry.schema.config import StrawberryConfig`; `from strawberry.types.scalar import ScalarDefinition`).
  - [ ] [`tests/test_scalars.py`](../tests/test_scalars.py) (extend): add **two** integration tests pinning that the migrated `BigInt` survives a Strawberry-schema round trip when registered through `strawberry_config()` — `test_bigint_serializes_int_via_strawberry_config_schema` (returns a Python `int` from a resolver annotated with `BigInt`; asserts the response JSON carries the decimal-string serialization), `test_bigint_parses_decimal_string_via_strawberry_config_schema` (accepts a decimal-string argument typed `BigInt`; asserts the resolver receives the parsed `int`). These two tests are the regression pins that catch a future `strawberry.scalar(name=..., ...)` overload signature drift; without them, a registration-path regression would surface only at consumer-build time.
  - [ ] [`tests/test_scalars.py`](../tests/test_scalars.py) (modify): the existing `test_package_import_does_not_emit_strawberry_deprecation_warning` regression at [`tests/test_scalars.py #"test_package_import_does_not_emit_strawberry_deprecation_warning"`](../tests/test_scalars.py) continues to pass UNCHANGED — the post-Slice-1 import path no longer triggers the deprecation at all (the `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload returns a `ScalarDefinition` directly without invoking the `wrap()` body at [`.venv/lib/python3.10/site-packages/strawberry/types/scalar.py #"def wrap(cls: _T) -> ScalarWrapper"`](../.venv/lib/python3.10/site-packages/strawberry/types/scalar.py) that emits the `DeprecationWarning`); the test's `-W error::DeprecationWarning` subprocess shape pins the post-migration no-leak contract without modification.
  - [ ] [`tests/base/test_init.py`](../tests/base/test_init.py) (modify): update the `test_public_api_surface_is_pinned` assertion to insert `"strawberry_config"` between `"OptimizerHint"` and `"__version__"` in the pinned `__all__` tuple per [Decision 2](#decision-2--helper-api-shape-and-module-location).
  - [ ] [`tests/types/test_converters.py`](../tests/types/test_converters.py) (modify): every `strawberry.Schema(query=Query)` call inside the `# BigInt scalar — schema-execution field-mapping tests (Slice 1)` section is rewritten to `strawberry.Schema(query=Query, config=strawberry_config())`. The section starts at the `# BigInt scalar — schema-execution field-mapping tests` banner and ends at the `# JSONField -> strawberry.scalars.JSON schema-execution tests` banner; 11 schema-construction sites are migrated in this section (`test_big_integer_field_maps_to_bigint_in_schema`, `test_big_integer_field_nullable_in_schema`, `test_positive_big_integer_field_maps_to_bigint_in_schema`, `test_big_auto_field_still_maps_to_int`, `test_bigint_serializes_query_result_as_string_via_schema_execution`, `test_bigint_parses_string_argument_via_schema_execution`, `test_bigint_parses_int_argument_via_schema_execution`, `test_bigint_in_input_position_with_null_via_schema_execution`, `test_bigint_rejects_bool_argument_via_schema_execution`, `test_bigint_rejects_float_argument_via_schema_execution`, `test_bigint_resolver_returning_bool_raises_via_schema_execution`). The import line `from django_strawberry_framework import BigInt, DjangoType, finalize_django_types` is widened to add `strawberry_config`. Schemas outside the BigInt section that do NOT involve a [`BigInt`](GLOSSARY.md#bigint-scalar) field (the `BigAutoField → ID`-mapping test and the JSONField / Choice-enum / Relation / Boolean tests in later sections) are NOT migrated — they don't carry a package-defined scalar through `scalar_map`, so Strawberry resolves the schema with the upstream defaults. This bullet is the practical surface of the migration broadening pinned in [Decision 5](#decision-5--migration-posture-hard-break-in-alpha): consumer-facing schemas with `BigIntegerField` / `PositiveBigIntegerField`-backed `DjangoType` fields need `config=strawberry_config()` even when they never import or annotate `BigInt` directly, because the [`Specialized scalar conversions`](GLOSSARY.md#specialized-scalar-conversions) converter table at [`django_strawberry_framework/types/converters.py`](../django_strawberry_framework/types/converters.py) resolves the field to `BigInt` for them.
  - [ ] [`tests/test_scalars.py`](../tests/test_scalars.py) (modify docstring): the module docstring currently says schema-execution behavior for `BigInt` lives in [`tests/types/test_converters.py`](../tests/types/test_converters.py); rewrite it to acknowledge that this file now ALSO carries two in-process `strawberry.Schema(...)` integration tests for the `strawberry_config()` registration round-trip. Suggested rewrite: keep the existing delegation sentence and append "Additionally, two `strawberry.Schema(query=..., config=strawberry_config())` integration tests pin the post-migration `BigInt` round trip end-to-end (`test_bigint_serializes_int_via_strawberry_config_schema`, `test_bigint_parses_decimal_string_via_strawberry_config_schema`)." so the test layout remains self-describing per [L2 in feedback](feedback.md).
- [ ] Slice 3: Example-app migration
  - [ ] [`examples/fakeshop/config/schema.py`](../examples/fakeshop/config/schema.py): rewrite the `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])` call (the file's sole `strawberry.Schema(` invocation, anchored at [`examples/fakeshop/config/schema.py #"strawberry.Schema(query=Query"`](../examples/fakeshop/config/schema.py)) to `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])`. Add `strawberry_config` to the existing `from django_strawberry_framework import ...` line. No other change.
  - [ ] [`examples/fakeshop/apps/library/schema.py`](../examples/fakeshop/apps/library/schema.py) and [`examples/fakeshop/apps/products/schema.py`](../examples/fakeshop/apps/products/schema.py): audit only — no edits expected. The example app schemas reference `BigInt` indirectly via the Django field-to-scalar converter table at [`django_strawberry_framework/types/converters.py #"BigInt,"`](../django_strawberry_framework/types/converters.py); they do not import the symbol directly today (verified via `grep -n "BigInt" examples/fakeshop/`, which currently returns no matches per the Step-5 grep). If a future card uses `BigInt` directly in a fakeshop schema (e.g., explicit `id: BigInt` annotations), no consumer code changes are needed because the symbol's import path is unchanged.
- [ ] Slice 4: Docs
  - [ ] [`docs/README.md`](README.md): rewrite the [Quick start](README.md#quick-start) code block (the `strawberry.Schema(...)` example) to add `config=strawberry_config()` to the constructor call, with `strawberry_config` added to the imports line. Also rewrite the [Relay Node](README.md#relay-node) example (which constructs a schema with `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])` near the end of its block) the same way. The "Wrong order" anti-example inside the [Schema setup boundary](README.md#schema-setup-boundary) section is rewritten in the same shape so the contrast still illustrates the finalize-order pitfall without omitting the new `config=` argument.
  - [ ] [`docs/GLOSSARY.md`](GLOSSARY.md): update the [`BigInt scalar`](GLOSSARY.md#bigint-scalar) entry body to reflect the new construction pattern — replace the sentence "Strict serializer rejects `bool`, `float`, `str`, `Decimal`, and any non-`int` type with `TypeError`" with the same sentence preserved, AND add a new paragraph: "Consumers register `BigInt` via the `strawberry_config()` factory (new in [Unreleased] — see [`strawberry_config`](#strawberry_config)) on their `strawberry.Schema(...)` call: `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])`. Direct `BigInt` annotations (`category: BigInt`, `@strawberry.field def big_id(self) -> BigInt: ...`) continue to work unchanged at the schema-declaration site; the registration path changes, not the symbol." Add a new top-level glossary entry for `strawberry_config` between the [`Specialized scalar conversions`](GLOSSARY.md#specialized-scalar-conversions) entry and the [Strictness mode](GLOSSARY.md#strictness-mode) entry; new entry body per [Doc updates](#doc-updates). Update the [Public exports](GLOSSARY.md#public-exports) bulleted re-exports list to add `strawberry_config` between `OptimizerHint` and `finalize_django_types`. Update the alphabetical [Index](GLOSSARY.md#index) table with a new row for `strawberry_config` in alphabetical position and a status of `shipped ([Unreleased])` (Risks calls out the placeholder-vs-real version posture; this is the same posture spec-019 uses post-cut).
  - [ ] [`GOAL.md`](../GOAL.md): rewrite the [`schema.py`](../GOAL.md#schemapy) example block (the astronomy showcase) — add `strawberry_config` to the imports list and `config=strawberry_config()` to the showcase's terminal `strawberry.Schema(...)` call (anchored at [`GOAL.md #"strawberry.Schema(query=Query"`](../GOAL.md)). No other change to the showcase body; the per-stack diff blocks inside the [Migration shape](../GOAL.md#migration-shape) section (`Coming from graphene-django` / `Coming from strawberry-graphql-django` / `Coming from DRF + django-filter`) are NOT edited because the blocks intentionally show minimal `Meta`-shape diffs and adding the helper would distract from the per-stack migration point. The GOAL `schema.py` is the one place where a consumer's "right shape" example lives end-to-end and should reflect the post-migration pattern.
  - [ ] [`TODAY.md`](../TODAY.md): rewrite the [What to put in `examples/fakeshop/config/schema.py` today](../TODAY.md#what-to-put-in-examplesfakeshopconfigschemapy-today) block to add `strawberry_config()` to the imports and the `strawberry.Schema(...)` call, mirroring the [`docs/README.md`](README.md) Quick start update. No other change; the [What's in `examples/fakeshop/apps/products/schema.py` today](../TODAY.md#whats-in-examplesfakeshopappsproductsschemapy-today) section already does not construct a project-level schema, so no edit is needed there.
  - [ ] [`docs/TREE.md`](TREE.md): no edit. The helper is added to the existing [`django_strawberry_framework/scalars.py`](../django_strawberry_framework/scalars.py) module per [Decision 2](#decision-2--helper-api-shape-and-module-location); no new file under `django_strawberry_framework/` and no new test file under `tests/`. The current-on-disk-layout enumeration in `docs/TREE.md` already mentions `scalars.py` (at [`docs/TREE.md #"scalars.py"`](TREE.md), `"scalars.py # \`BigInt\` public scalar"`); the entry stays as-is since the file's role is unchanged.
- [ ] Slice 5: KANBAN + CHANGELOG
  - [ ] [`KANBAN.md`](../KANBAN.md): move `WIP-ALPHA-020-0.0.7` to the Done column with the next available `DONE-NNN-0.0.7` id (the column-move pass renumbers as usual; the next available id is determined at merge time, not pinned in this spec). The past-tense Done body summarizes the shipped scope; full wording pinned in [Doc updates](#doc-updates). Update the card body's `Definition of done` bullet 1 (`docs/spec-scalar_map_helper.md` → `docs/SPECS/spec-020-scalar_map_helper-0_0_7.md` after the Step-8 archive pass per [Decision 1](#decision-1--spec-filename-and-canonical-naming)). Update the `### In progress` summary paragraph (anchored at [`KANBAN.md #"### In progress"`](../KANBAN.md)) to remove `WIP-ALPHA-020-0.0.7` from the remaining-cards list once this card moves to Done.
  - [ ] [`CHANGELOG.md`](../CHANGELOG.md): **append** to the existing `[Unreleased]` `### Changed` subsection (existing changes there are non-breaking; this card's breaking-but-alpha-OK migration adds the fourth bullet) AND `### Removed` (for the suppression block removal) AND `### Added` (for the `strawberry_config` factory). Per the CHANGELOG-edit-permission rule at [`AGENTS.md #"Do not update CHANGELOG.md unless explicitly instructed"`](../AGENTS.md), this Slice 5 bullet is the explicit `CHANGELOG.md` edit permission. Also remove the literal `[0.0.6]` `### Notes` line "The internal `BigInt` scalar definition uses `strawberry.scalar(NewType, ...)`, which Strawberry deprecates in favor of `StrawberryConfig.scalar_map`. The deprecation warning is suppressed at the definition site so the package import remains clean. Migration to a `scalar_map`-based design is tracked as a follow-up and will be a real public-API change for consumers using `BigInt` directly." at [`CHANGELOG.md #"Migration to a"`](../CHANGELOG.md) — that `Notes` entry advertised the architectural debt this card pays down; with the migration shipped, the placeholder note has served its purpose and removing it keeps the `[0.0.6]` section accurate as a snapshot of what shipped (the `Notes` line is a forward-looking pointer, not a historical fact).
  - [ ] Version bump: NOT in this card per [Decision 8](#decision-8--version-posture-cut-already-shipped-this-card-lands-under-unreleased). The `[Unreleased]` `### Added` / `### Changed` / `### Removed` bullets accumulate against an unbumped `__version__ = "0.0.7"` until a future maintainer-led cut promotes them to `[0.0.8]` and bumps `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, and `tests/base/test_init.py`'s pinned version assertion in one atomic commit. This card does NOT do the bump.

## Problem statement

`0.0.6` shipped `BigInt` as the package's first public scalar (per [`docs/SPECS/spec-013-deferred_scalars-0_0_6.md`](SPECS/spec-013-deferred_scalars-0_0_6.md) Decision 1; the public-export contract is pinned in [`docs/SPECS/spec-013-deferred_scalars-0_0_6.md`](SPECS/spec-013-deferred_scalars-0_0_6.md) Decision 6). Implementation chose the most-idiomatic-at-the-time Strawberry shape — `strawberry.scalar(NewType("BigInt", int), name="BigInt", serialize=_serialize_bigint, parse_value=_parse_bigint)` — but a later Strawberry release deprecated the class-direct-to-`scalar()` path: every call into `strawberry.scalar(<class-or-NewType>, ...)` now emits `DeprecationWarning("Passing a class to strawberry.scalar() is deprecated. Use StrawberryConfig.scalar_map instead for better type checking support. See: https://strawberry.rocks/docs/types/scalars")` from [`.venv/lib/python3.10/site-packages/strawberry/types/scalar.py #"def wrap(cls: _T) -> ScalarWrapper"`](../.venv/lib/python3.10/site-packages/strawberry/types/scalar.py).

The `0.0.6` shipping fix was to suppress the deprecation at the definition site so consumers importing `django_strawberry_framework` see no warning — see the `with warnings.catch_warnings(): warnings.filterwarnings("ignore", message="Passing a class to strawberry.scalar", ...)` block at the bottom of [`django_strawberry_framework/scalars.py`](../django_strawberry_framework/scalars.py). The suppression is correct triage but it has two architectural costs that this card pays down:

1. **The `0.0.6` `CHANGELOG.md` `### Notes` line carries a literal "tracked as a follow-up" pointer** — every release that ships with the suppression in place is a release that ships with documented technical debt.
2. **`Upload` (`TODO-ALPHA-028-0.0.11`, planned for `0.0.11` per [`docs/GLOSSARY.md#upload-scalar`](GLOSSARY.md#upload-scalar)) and any future package-defined scalar would have to choose between repeating the suppression hack or migrating to `StrawberryConfig.scalar_map`** — every additional scalar the package ships under the suppressed-deprecation pattern multiplies the migration surface this card has to pay down later.

The right design (pre-pinned by the [`KANBAN.md`](../KANBAN.md) card body's "Recommended architectural direction" block) defines `BigInt` on Strawberry's recommended path (a bare `NewType` plus a `ScalarDefinition` produced via the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload at [`.venv/lib/python3.10/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`](../.venv/lib/python3.10/site-packages/strawberry/types/scalar.py)) and has consumers compose a package-provided `StrawberryConfig` into their `strawberry.Schema(...)`. The result: no suppression block; no `_warnings.catch_warnings()` pretext; a single registration point that any future package-defined scalar slots into without API change.

## Current state

- [`django_strawberry_framework/scalars.py`](../django_strawberry_framework/scalars.py): `BigInt` is defined via `strawberry.scalar(NewType("BigInt", int), name="BigInt", ...)` wrapped in a `with warnings.catch_warnings(): warnings.filterwarnings("ignore", message="Passing a class to strawberry.scalar", ...)` block. The strict parser (`_parse_bigint`) and strict serializer (`_serialize_bigint`) are pure functions with no Strawberry coupling.
- [`django_strawberry_framework/__init__.py`](../django_strawberry_framework/__init__.py): `BigInt` is re-exported via the `from .scalars import BigInt` line (anchored at [`django_strawberry_framework/__init__.py #"from .scalars import BigInt"`](../django_strawberry_framework/__init__.py)); `__all__` (anchored at [`django_strawberry_framework/__init__.py #"__all__"`](../django_strawberry_framework/__init__.py)) lists it.
- [`django_strawberry_framework/types/converters.py #"BigInt,"`](../django_strawberry_framework/types/converters.py): `models.BigIntegerField: BigInt` and `models.PositiveBigIntegerField: BigInt` are pinned in `SCALAR_MAP`. Consumer `DjangoType`s using these field types resolve to `BigInt` automatically through the converter table; no consumer import of `BigInt` is required for that path.
- [`tests/test_scalars.py`](../tests/test_scalars.py): 22+ tests pinning the strict parser / serializer contract (`test_bigint_serializes_int_as_decimal_string`, `test_bigint_rejects_python_bool`, etc.) plus the public-export smoke (`test_bigint_is_importable_from_top_level`) plus the deprecation-suppression regression (`test_package_import_does_not_emit_strawberry_deprecation_warning` at [`tests/test_scalars.py #"test_package_import_does_not_emit_strawberry_deprecation_warning"`](../tests/test_scalars.py)). The deprecation regression test runs `python -W error::DeprecationWarning -c "import django_strawberry_framework"` in a subprocess and asserts the import does not raise.
- [`tests/base/test_init.py`](../tests/base/test_init.py): `test_public_api_surface_is_pinned` (anchored at [`tests/base/test_init.py #"test_public_api_surface_is_pinned"`](../tests/base/test_init.py)) pins `__all__` as an exact-tuple assertion.
- [`examples/fakeshop/config/schema.py`](../examples/fakeshop/config/schema.py): constructs the project schema via `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])` (the file's sole `strawberry.Schema(` invocation, anchored at [`examples/fakeshop/config/schema.py #"strawberry.Schema(query=Query"`](../examples/fakeshop/config/schema.py)) — no `config=` argument. The fakeshop schemas do not import `BigInt` directly today (verified via `grep -n "BigInt" examples/fakeshop/` — no matches).
- [`docs/GLOSSARY.md`](GLOSSARY.md): the [`BigInt scalar`](GLOSSARY.md#bigint-scalar) entry describes the `0.0.6` wire format / parser / serializer but does not document the registration path; the [Public exports](GLOSSARY.md#public-exports) list shows `BigInt` but no helper symbol.
- [`docs/README.md`](README.md): the [Quick start](README.md#quick-start) section shows `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])`; the [Relay Node](README.md#relay-node) example shows the same shape.
- [`GOAL.md`](../GOAL.md): the astronomy showcase [`schema.py`](../GOAL.md#schemapy) block shows the same shape.
- [`TODAY.md`](../TODAY.md): the [What to put in `examples/fakeshop/config/schema.py` today](../TODAY.md#what-to-put-in-examplesfakeshopconfigschemapy-today) block shows the same shape.
- [`CHANGELOG.md #"Migration to a"`](../CHANGELOG.md): the `[0.0.6]` `### Notes` line (anchored at the `"Migration to a"` substring above) advertises the architectural debt this card pays down.
- [`docs/SPECS/spec-019-multi_db-0_0_7.md`](SPECS/spec-019-multi_db-0_0_7.md): the sibling `0.0.7` spec, shipped before this card; its [Decision 9](SPECS/spec-019-multi_db-0_0_7.md#decision-9--joint-0_0_7-cut) is the "joint cut" reference the [Decision 8](#decision-8--version-posture-cut-already-shipped-this-card-lands-under-unreleased) here cites.

## Goals

1. Pay down the suppressed-deprecation debt by moving `BigInt` to Strawberry's recommended `StrawberryConfig.scalar_map` registration path.
2. Establish the registration helper any future package-defined scalar (`Upload`, `TODO-ALPHA-028-0.0.11`) reuses without API change.
3. Ship the consumer migration as a single-line change at `strawberry.Schema(...)` construction sites — `config=strawberry_config()` added once per schema, no annotation-site changes anywhere.
4. Remove the `warnings.catch_warnings()` block so the package's import surface is clean by construction, not by suppression.
5. Remove the `[0.0.6]` `### Notes` "tracked as a follow-up" line because the follow-up has shipped.

## Non-goals

- Composing Strawberry extensions through this helper. `extensions=` belongs on `strawberry.Schema(query=..., extensions=[...])`, NOT on `StrawberryConfig`. The card body explicitly calls this out and the helper signature deliberately omits an `extra_extensions=` parameter — see [Decision 2](#decision-2--helper-api-shape-and-module-location). If a future card reveals real demand for an extension-bundling helper, it ships as a separate symbol (e.g., `schema_kwargs(...)` returning a kwargs dict) rather than overloading `strawberry_config`.
- Auto-discovery of the package config. A hypothetical Django-settings-backed default like `STRAWBERRY_CONFIG_FACTORY = "django_strawberry_framework.scalars.strawberry_config"` that the package internals consult is deferred; consumers explicitly pass `config=strawberry_config()` per `strawberry.Schema(...)` call. Per the settings-keys rule at [`AGENTS.md #"Add settings keys only when the feature that needs them lands"`](../AGENTS.md), the discovery path is not added until a feature requires it.
- Promoting [`Upload`](GLOSSARY.md#upload-scalar) early. [`Upload`](GLOSSARY.md#upload-scalar) (and [`DjangoFileType`](GLOSSARY.md#djangofiletype) / [`DjangoImageType`](GLOSSARY.md#djangoimagetype)) is `TODO-ALPHA-028-0.0.11`, planned for `0.0.11`. This card's helper is built so the `Upload` card slots in by appending to `_PACKAGE_SCALAR_MAP` and re-exporting `Upload` from `__init__.py` — no other change to `strawberry_config(...)` is needed.
- A `dst.Schema(...)` wrapper around `strawberry.Schema`. Considered and rejected per [Decision 2](#decision-2--helper-api-shape-and-module-location); shadowing upstream symbols hides the composition.
- A static `SCALAR_MAP` constant the consumer manually splat-merges into their own `StrawberryConfig(scalar_map={...})`. Considered and rejected per [Decision 2](#decision-2--helper-api-shape-and-module-location); pushes `StrawberryConfig(...)` boilerplate onto every consumer.
- Mutating the converter table at [`django_strawberry_framework/types/converters.py`](../django_strawberry_framework/types/converters.py). The `models.BigIntegerField: BigInt` / `models.PositiveBigIntegerField: BigInt` mappings reference `BigInt` by name; the symbol's import path is unchanged, so the converter table needs no edit.
- Renaming `BigInt`. The symbol's GraphQL name (`BigInt`) and Python identifier (`BigInt`) are preserved verbatim.

## Borrowing posture

This card has no upstream precedent to borrow at the helper-API level — `strawberry-django` does not ship a `StrawberryConfig`-bundling helper; `graphene-django` predates Strawberry. The `StrawberryConfig.scalar_map` registration *mechanism* is the upstream pattern this card adopts, but the package-side factory wrapping it is new.

### From `strawberry-django` — no precedent to borrow

Local source path: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/`. Verified by `grep -rn "StrawberryConfig\|scalar_map" /Users/riordenweber/projects/strawberry-django-main/` — zero matches in the upstream's source. The upstream does not ship package-defined scalars (no `BigInt`, no `Upload` in the strawberry-django source tree), so it has no registration helper to model on. Consumers using `strawberry-django` who need a custom scalar register it themselves via Strawberry's documented path; the package does not bundle one.

### From `graphene-django` — no precedent to borrow

Local source path: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/`. `graphene-django` uses Graphene's `Scalar` subclass mechanism rather than Strawberry's `StrawberryConfig.scalar_map`. The migration target here is Strawberry's idiom; there is no graphene-side analogue to import.

### Explicitly do not borrow

- A `dst.Schema(query=..., ...)` wrapper that pre-populates `config=`. Rejected: shadows the upstream `strawberry.Schema` symbol, hides composition, and creates an opaque "what is this returning?" question for every consumer. Compare: the package already ships `DjangoOptimizerExtension` as an extension consumers pass via the `extensions=[...]` kwarg explicitly; the same posture (explicit composition, not wrapped construction) extends to the config kwarg.
- A static `SCALAR_MAP: dict[object, ScalarDefinition]` re-export consumers `**`-spread into their own `StrawberryConfig`. Rejected: forces every consumer to spell out `StrawberryConfig(scalar_map={**SCALAR_MAP, ...})`, with the spread pattern being unidiomatic at consumer-write time and the conflict-resolution policy (silently override or raise) becoming the consumer's responsibility. The factory keeps that policy in one place — see [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions).
- A package-level `STRAWBERRY_DEFAULT_CONFIG: StrawberryConfig` module-level constant. Rejected: a single module-level `StrawberryConfig` instance would be shared mutable state across every consumer schema; mutations to the `scalar_map` of one schema's `StrawberryConfig` would leak to every other. The factory returns a fresh instance per call so call sites are independent — see [Decision 2](#decision-2--helper-api-shape-and-module-location).

## User-facing API

The shipped consumer surface adds **one new symbol** — `strawberry_config(extra_scalar_map=None) -> StrawberryConfig`. The symbol is re-exported from `django_strawberry_framework` and lives in [`django_strawberry_framework/scalars.py`](../django_strawberry_framework/scalars.py) (per [Decision 2](#decision-2--helper-api-shape-and-module-location)).

### Default usage — package scalars only

```python path=null start=null
import strawberry

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    finalize_django_types,
    strawberry_config,
)

# ... import every module that declares DjangoType subclasses ...

finalize_django_types()

schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[DjangoOptimizerExtension()],
)
```

The returned `StrawberryConfig.scalar_map` carries one entry today: `{BigInt: <BigInt ScalarDefinition>}`. Strawberry consults the map at schema-construction time to resolve `BigInt` annotations and assigned-`BigInt` resolvers anywhere in the schema; the consumer writes `id: BigInt` or `@strawberry.field def big_id(self) -> BigInt: ...` exactly as in `0.0.6` and earlier.

### Composing with consumer-defined scalars

```python path=null start=null
from typing import NewType
import strawberry
from django_strawberry_framework import strawberry_config

MyULID = NewType("MyULID", str)
_MY_ULID_DEF = strawberry.scalar(name="MyULID", serialize=str, parse_value=str)

schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(extra_scalar_map={MyULID: _MY_ULID_DEF}),
)
```

The factory merges `extra_scalar_map` over the package's defaults. Collision policy: if a key in `extra_scalar_map` is already in `_PACKAGE_SCALAR_MAP`, the factory raises `ValueError` with a message naming the colliding keys and the supported recourse (define a Strawberry scalar under a different `NewType` / class to register under a separate key) — see [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions).

### Error shapes

- `strawberry_config(extra_scalar_map={BigInt: <some other ScalarDefinition>})` → `ValueError("strawberry_config(extra_scalar_map=...) cannot redeclare package-defined scalars: BigInt. ...")`.
- `strawberry_config(extra_scalar_map={"not a NewType or class": <ScalarDefinition>})` → no validation; Strawberry's own `StrawberryConfig(scalar_map=...)` consumer ([`strawberry.Schema(...)`](https://strawberry.rocks)) decides whether the key is usable. The factory does NOT pre-validate the shape of `extra_scalar_map` keys because Strawberry's documented contract for `scalar_map` accepts "any type" (per the `Mapping[object, ScalarDefinition]` type at [`.venv/lib/python3.10/site-packages/strawberry/schema/config.py #"scalar_map: Mapping[object, ScalarDefinition]"`](../.venv/lib/python3.10/site-packages/strawberry/schema/config.py)); the factory would over-validate by guessing what "any type" means in this context.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/spec-020-scalar_map_helper-0_0_7.md`** (this document), NOT `docs/spec-scalar_map_helper.md` as the [`KANBAN.md`](../KANBAN.md) card body's `Definition of done` bullet 1 names it.

Justification:

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`](SPECS/NEXT.md) Step 6 and proven by every recent spec ([`docs/SPECS/spec-014-meta_primary-0_0_6.md`](SPECS/spec-014-meta_primary-0_0_6.md), [`docs/SPECS/spec-015-consumer_overrides_scalar-0_0_6.md`](SPECS/spec-015-consumer_overrides_scalar-0_0_6.md), [`docs/SPECS/spec-016-list_field-0_0_7.md`](SPECS/spec-016-list_field-0_0_7.md), [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md), [`docs/SPECS/spec-018-export_schema-0_0_7.md`](SPECS/spec-018-export_schema-0_0_7.md), [`docs/SPECS/spec-019-multi_db-0_0_7.md`](SPECS/spec-019-multi_db-0_0_7.md)) bakes the card's NNN and target patch into the filename. The card body's `docs/spec-scalar_map_helper.md` predates that convention and would land an unnumbered spec next to a numbered cohort, breaking the alphabetical archive ordering at `docs/SPECS/`.
- The Slice 5 [`KANBAN.md`](../KANBAN.md) update overwrites the stale `docs/spec-scalar_map_helper.md` reference in the card body to point at the canonical name, so the cross-reference resolves after archival (per [Step 8 of NEXT.md](SPECS/NEXT.md#step-8--archive-prior-specs-and-update-cross-references)).
- This Decision is enforcement, not innovation: the convention is already pinned in [`docs/SPECS/NEXT.md`](SPECS/NEXT.md) Step 6 and observed by every spec from 014 forward.

Alternatives considered (and rejected):

- **Honor the card body verbatim with `docs/spec-scalar_map_helper.md`.** Rejected: diverges from the structured naming convention; forces a Step-8 archive rename anyway; would not match the [`KANBAN.md`](../KANBAN.md) sibling cards' filenames.
- **Use a longer topic slug like `strawberry_config_factory`.** Rejected: longer than necessary; `scalar_map_helper` already names the architectural intent and matches the card body's recommended filename minus the `docs/spec-` prefix.

Active-vs-archived path lifecycle (mirroring [`docs/SPECS/spec-019-multi_db-0_0_7.md`](SPECS/spec-019-multi_db-0_0_7.md) Decision 1, rev3 R10 — simplified): references point at whichever path the file actually has at the time the reference is written. While this spec is at `docs/spec-020-scalar_map_helper-0_0_7.md`, every reference uses that path; after a future archive pass moves it under `docs/SPECS/`, references use the archived path; the Slice 5 [`KANBAN.md`](../KANBAN.md) Done body uses whichever path is current when the Done-body edit lands.

### Decision 2 — Helper API shape and module location

The helper ships as a **factory function** named `strawberry_config` with signature `def strawberry_config(extra_scalar_map: Mapping[object, ScalarDefinition] | None = None) -> StrawberryConfig`. The function lives in **[`django_strawberry_framework/scalars.py`](../django_strawberry_framework/scalars.py)**, colocated with the `BigInt` definition it composes. The symbol is re-exported from `django_strawberry_framework` (i.e., available as `from django_strawberry_framework import strawberry_config`).

Justification:

- **Factory over static constant.** A factory function returns a fresh `StrawberryConfig` per call, so two schemas (e.g., the main app schema plus a debug-tools admin schema) get independent `StrawberryConfig` instances and one's mutations cannot leak to the other. A static `STRAWBERRY_CONFIG: StrawberryConfig` module-level constant would share mutable state across every call site.
- **Factory over class wrapper.** Wrapping `strawberry.Schema(...)` (e.g., `dst.Schema(query=..., ...)`) shadows the upstream symbol and hides composition. The factory returns a `StrawberryConfig` and the consumer composes it into their own `strawberry.Schema(query=..., config=strawberry_config(), extensions=[...])` call — same posture as `DjangoOptimizerExtension()` being composed via `extensions=[...]`.
- **`extra_scalar_map=` parameter only.** Strawberry's `StrawberryConfig` has many fields ([`auto_camel_case`, `name_converter`, `default_resolver`, `relay_max_results`, `relay_use_legacy_global_id`, `disable_field_suggestions`, `info_class`, `enable_experimental_incremental_execution`, `scalar_map`, `batching_config`](../.venv/lib/python3.10/site-packages/strawberry/schema/config.py)); the only one this card has an opinion on is `scalar_map`. Consumers who want to set `auto_camel_case=False` or `relay_max_results=200` construct their own `StrawberryConfig(...)` and merge the package's `scalar_map` via `extra_scalar_map=` (which is what the helper exists for). The package does NOT impose opinions on the other fields.
- **`extra_extensions=` deliberately omitted.** Strawberry extensions go to `strawberry.Schema(..., extensions=[...])`, not into `StrawberryConfig`. The card body calls this out explicitly. If a future card reveals real demand for extension-bundling, it ships as a separate helper (e.g., `schema_kwargs(...)` returning a dict of `{"config": ..., "extensions": [...]}`) rather than overloading this one.
- **Module location: [`scalars.py`](../django_strawberry_framework/scalars.py) (NOT a new `config.py`).** Cohesion: everything BigInt-related lives in one module. The factory's body is small (~10 lines), and the package's existing flat-module layout already mirrors `strawberry-django`'s shape (`apps.py`, `arguments.py`, `descriptors.py`, etc.). A new module would also be ambiguously named relative to the existing `conf.py` (the settings-reader for `DJANGO_STRAWBERRY_FRAMEWORK`); two `conf.py` / `config.py` files would be a maintenance hazard. When `Upload` lands (`TODO-ALPHA-028-0.0.11`), its `ScalarDefinition` joins the same module's `_PACKAGE_SCALAR_MAP` dict — no additional file proliferation.
- **Type signature.** `Mapping[object, ScalarDefinition] | None`. `Mapping` matches Strawberry's own `StrawberryConfig.scalar_map: Mapping[object, ScalarDefinition]` shape at [`.venv/lib/python3.10/site-packages/strawberry/schema/config.py #"scalar_map: Mapping[object, ScalarDefinition]"`](../.venv/lib/python3.10/site-packages/strawberry/schema/config.py); `object` keeps the key type as broad as Strawberry's contract; `| None` lets callers omit the parameter entirely.

Alternatives considered (and rejected):

- **`django_strawberry_framework/config.py` (new module).** Rejected: ambiguity with the existing [`conf.py`](../django_strawberry_framework/conf.py) (the `DJANGO_STRAWBERRY_FRAMEWORK` settings reader); two modules differing only in vowels invite consumer error and reader confusion.
- **`django_strawberry_framework/__init__.py` (top-level only — no separate module).** Rejected: bloats the entry-point with implementation. The existing `__init__.py` is the public-surface manifest (re-exports and `__all__`); the helper's body belongs next to the scalar it composes.
- **`django_strawberry_framework/schema.py` (new module).** Rejected: name collides conceptually with `strawberry.Schema`; would suggest the helper does more than build a `StrawberryConfig`.
- **`strawberry_config(*, scalar_map=None)` (keyword-only, no `extra_` prefix).** Rejected: a bare `scalar_map=` parameter implies "this REPLACES the package's defaults"; `extra_scalar_map=` makes the merge-not-replace intent explicit.
- **`strawberry_config(*, replace_scalar_map=None, extra_scalar_map=None)` (two parameters).** Rejected: introduces a "replace mode" the package has no business supporting — replacing `BigInt`'s registration would silently break the `BigIntegerField → BigInt` converter table.

### Decision 3 — `BigInt` redefinition as bare `NewType` + `ScalarDefinition`

`BigInt` is redefined as a bare `NewType("BigInt", int)`. The Strawberry `ScalarDefinition` is built via the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload — the `cls is None and name is not None` branch at [`.venv/lib/python3.10/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`](../.venv/lib/python3.10/site-packages/strawberry/types/scalar.py) — which returns a `ScalarDefinition` directly without invoking the `wrap()` body that emits the `DeprecationWarning`.

Pinned shape (Slice 1):

```python path=null start=null
from typing import Any, NewType
from collections.abc import Mapping

import strawberry
from strawberry.schema.config import StrawberryConfig
from strawberry.types.scalar import ScalarDefinition

# Parser and serializer unchanged from 0.0.6.
def _parse_bigint(value: Any) -> int: ...
def _serialize_bigint(value: Any) -> str: ...

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

Justification:

- The `strawberry.scalar(cls=None, name=...)` overload returns a `ScalarDefinition` directly and does NOT emit the `DeprecationWarning`. Verified at [`.venv/lib/python3.10/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`](../.venv/lib/python3.10/site-packages/strawberry/types/scalar.py): the branch is `return ScalarDefinition(name=name, description=..., specified_by_url=..., serialize=serialize, parse_literal=parse_literal, parse_value=parse_value, directives=..., origin=None, ...)`. The deprecation-emitting `wrap()` body at [`.venv/lib/python3.10/site-packages/strawberry/types/scalar.py #"def wrap(cls: _T) -> ScalarWrapper"`](../.venv/lib/python3.10/site-packages/strawberry/types/scalar.py) is the `cls is not None` path.
- The bare `NewType("BigInt", int)` keeps `BigInt` usable as a direct Python annotation — `id: BigInt` and `def f(x: BigInt) -> BigInt: ...` work as type hints because `NewType` is a transparent identity at runtime. Strawberry resolves the `NewType` to the registered `ScalarDefinition` via `StrawberryConfig.scalar_map` at schema-construction time.
- The wire format, parser, and serializer logic are preserved verbatim — `_parse_bigint` and `_serialize_bigint` are unchanged from `0.0.6`. The only change at the Python level is the structure that wraps them.

Alternatives considered (and rejected):

- **`BigInt = strawberry.scalar(NewType("BigInt", int), name=..., ...)` plus an unconditional `warnings.filterwarnings("ignore", ...)` in `scalars.py`.** Rejected: re-suppression of the deprecation defeats the card's purpose.
- **Use Strawberry's `Annotated[int, strawberry.argument(...)]` shape.** Rejected: `argument(...)` annotates parameters, not types; doesn't match `BigInt`'s "type used in annotations" role.
- **Subclass `int` for `BigInt` and bind the scalar definition to the subclass.** Rejected: `int` subclasses are heavier than `NewType` (real Python class with `__instancecheck__` cost), and `bool` issues at parse time (`isinstance(value, BigIntSubclass)` and `isinstance(value, bool)` interact awkwardly because `bool` is an `int` subclass). The bare `NewType` is the lighter, more idiomatic shape.

### Decision 4 — Conflict resolution for `extra_scalar_map` collisions

When a consumer's `extra_scalar_map` contains a key already present in `_PACKAGE_SCALAR_MAP`, `strawberry_config(...)` raises `ValueError("strawberry_config(extra_scalar_map=...) cannot redeclare package-defined scalars: <names>. Define a Strawberry custom scalar of a different NewType / class to register under a separate key.")` — hard error.

Justification:

- The collision is a consumer-input mistake at helper-call time, not a `DjangoType`-creation or finalization-time error. `ValueError` is the standard library's "function received an unsuitable argument" exception; using `ConfigurationError` (the package's own type-creation / finalization error class) would be inconsistent with what that exception class signals.
- Silently overriding the package default would let a consumer accidentally re-register `BigInt` to a different `ScalarDefinition` (e.g., one that serializes as a JSON integer instead of a decimal string), breaking the `BigIntegerField → BigInt` wire-format contract that the [`docs/SPECS/spec-013-deferred_scalars-0_0_6.md`](SPECS/spec-013-deferred_scalars-0_0_6.md) Decision 1 pins. Silent override is the worst-of-both: it does what the consumer typed but breaks the contract they didn't realize they were touching.
- Override-with-warning is the worst-of-both in a different way: the schema still builds with potentially-broken semantics, and the warning is easy to miss in CI / dev terminal output. Hard error catches the mistake at helper-call time, before schema construction even starts.
- The error message names the offending key(s) so the consumer can identify which mapping to drop, and explicitly states the supported recourse (use a different key — a custom `NewType` or class — for the consumer scalar that's currently colliding).

Alternatives considered (and rejected):

- **Silent override.** Rejected: catches no mistakes; the consumer never knows they replaced a package default.
- **Override with `UserWarning`.** Rejected: easy to miss; the schema still ships with overridden semantics.
- **Two-flag API: `strawberry_config(extra_scalar_map=..., allow_override=False)` defaulting to hard error.** Rejected: adds a complication to support a use case (intentional override) that the [Decision 2](#decision-2--helper-api-shape-and-module-location) "no replace mode" boundary already excludes.

### Decision 5 — Migration posture: hard break in alpha

Any consumer whose schema resolves to `BigInt` after the upgrade — whether through a direct `BigInt` annotation OR through a [`DjangoType`](GLOSSARY.md#djangotype) field backed by `BigIntegerField` / `PositiveBigIntegerField` resolved by the [`Specialized scalar conversions`](GLOSSARY.md#specialized-scalar-conversions) converter table at [`django_strawberry_framework/types/converters.py`](../django_strawberry_framework/types/converters.py) — who doesn't add `config=strawberry_config()` to their `strawberry.Schema(...)` call will see Strawberry schema-construction fail with `Unexpected type '...BigInt'` (or a comparable Strawberry error) at the first schema-build attempt after the upgrade. No deprecation window; no shim that re-registers `BigInt` via the old `strawberry.scalar(NewType, ...)` path; the migration is a single-line consumer change. The migration surface is broader than "consumers who import or annotate `BigInt` directly" because the converter table resolves the field type to `BigInt` for any `DjangoType` backed by the targeted Django integer fields — those consumers must migrate too even if they never reference the `BigInt` symbol in their own code.

Justification:

- Matches the `PositiveBigIntegerField` precedent in `0.0.6` (per [`docs/SPECS/spec-013-deferred_scalars-0_0_6.md`](SPECS/spec-013-deferred_scalars-0_0_6.md) Decision 1, which switched `PositiveBigIntegerField` from `int` to `BigInt` — a breaking wire-format change shipped as a single Changed entry in `[0.0.6]`). The package's alpha-quality status (per [`README.md`](../README.md): "single-maintainer, alpha-quality. Fine for internal tools and prototypes; not production") makes hard breaks the right default while consumers are early.
- Long deprecation windows are appropriate at `1.0.0`, not during alpha. The [`docs/GLOSSARY.md`](GLOSSARY.md) status legend already pins: "The `1.0.0` release is the API-freeze boundary; after `1.0.0` ships, strict semantic versioning applies to every entry below." Pre-`1.0.0`, the contract is "names are stable, semantics evolve."
- The consumer migration is one line: add `config=strawberry_config()` (with the import) to the `strawberry.Schema(...)` call. The CHANGELOG entry under Slice 5 carries the explicit before/after block.
- Surveying real `0.0.6` consumer adoption of `BigInt` before deciding the posture is the [`KANBAN.md`](../KANBAN.md) card body's "if real consumer demand" branch — but the package is single-maintainer-alpha and there is no consumer survey to consult; the right default is to apply the precedent (`PositiveBigIntegerField` in `0.0.6`) verbatim.

Alternatives considered (and rejected):

- **One-release `DeprecationWarning` from the package.** Rejected: would require keeping the old `strawberry.scalar(NewType, ...)` path alongside the new one for one release, doubling the surface and the test load; consumers who ignore `DeprecationWarning` get a louder break later anyway.
- **`BigInt` keeps the wrapped shape; introduce `strawberry_config()` as a no-op helper consumers can opt into early.** Rejected: ships the suppression block for another release and defers the architectural cleanup the card exists to do; misses the "stop carrying the architectural debt" point.
- **Provide a `legacy_bigint()` compat helper consumers can swap in.** Rejected: every "compat helper" added during alpha is one more thing to deprecate at `1.0.0`; the boundary is "alpha-quality means consumers update their schema-construction call when the package updates."

### Decision 6 — Remove the `warnings.catch_warnings()` suppression block

The `with warnings.catch_warnings(): warnings.filterwarnings("ignore", message="Passing a class to strawberry.scalar", category=DeprecationWarning)` block at the bottom of [`django_strawberry_framework/scalars.py`](../django_strawberry_framework/scalars.py) is removed wholesale, along with the `import warnings` line if no other code in the file uses it (verified — `warnings` is imported only for this block today).

Justification:

- The `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload that Slice 1 switches to does NOT trigger the `DeprecationWarning` (per [Decision 3](#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition) — verified at the Strawberry source); the suppression is no longer load-bearing.
- Keeping the suppression around "just in case" would be a documentation hazard: a future contributor reading the file would not be able to distinguish "this is here because of a real deprecation that fires" from "this is dead code from a prior migration." Removing it makes the file's contract explicit: post-migration, the import path is clean by construction.
- The existing `test_package_import_does_not_emit_strawberry_deprecation_warning` regression at [`tests/test_scalars.py #"test_package_import_does_not_emit_strawberry_deprecation_warning"`](../tests/test_scalars.py) continues to pass UNCHANGED (the test runs `python -W error::DeprecationWarning -c "import django_strawberry_framework"` and asserts the subprocess exits cleanly); the test now pins the no-leak contract via the migrated registration shape rather than via the suppression block. If the suppression is accidentally restored alongside a regression in the no-warning overload, the test still catches the underlying problem.

Alternatives considered (and rejected):

- **Leave the suppression block in place defensively.** Rejected: dead code is a maintenance hazard; the package's own regression test enforces the contract regardless.
- **Replace the suppression with a comment.** Rejected: code is the source of truth; a comment that points at a removed suppression is documentation of nothing.

### Decision 7 — Test placement and shape

New tests for `strawberry_config(...)` and the migrated `BigInt` registration path extend the existing [`tests/test_scalars.py`](../tests/test_scalars.py) module — the mirror partner of [`django_strawberry_framework/scalars.py`](../django_strawberry_framework/scalars.py) per the [`docs/TREE.md`](TREE.md) mirror rule. No new test file.

Test count: **eight** new factory tests + **two** new integration tests = ten new pytest items added to `tests/test_scalars.py`. The existing 22+ tests in the file are unchanged except the `__all__` assertion that lives in `tests/base/test_init.py` (one-line edit). Single pytest item per test; no `pytest.mark.parametrize` fan-out so the count matches pytest collection output unambiguously, mirroring [`docs/SPECS/spec-019-multi_db-0_0_7.md`](SPECS/spec-019-multi_db-0_0_7.md) Slice 1's no-`parametrize` pin and [`docs/SPECS/spec-018-export_schema-0_0_7.md`](SPECS/spec-018-export_schema-0_0_7.md) rev2 M1.

Justification:

- The new code under test lives in [`django_strawberry_framework/scalars.py`](../django_strawberry_framework/scalars.py) (one module); its mirror partner is `tests/test_scalars.py` (one file). Adding a new `tests/test_config.py` would violate the mirror rule because no `django_strawberry_framework/config.py` exists (and per [Decision 2](#decision-2--helper-api-shape-and-module-location), no such module is introduced).
- Adding the factory tests to the existing file keeps related test logic close: the `BigInt` parser / serializer tests and the `strawberry_config()` registration tests both ride on the same imports and same `ScalarDefinition` shape.
- Live HTTP coverage (per the live-HTTP-priority rule at [`AGENTS.md #"any coverage line achievable via a real GraphQL query"`](../AGENTS.md)) is earned indirectly through Slice 3's [`examples/fakeshop/config/schema.py`](../examples/fakeshop/config/schema.py) migration: every existing `examples/fakeshop/test_query/test_*.py` test that exercises the project schema also exercises the helper (because `config=strawberry_config()` is now called at module-import time when the project schema is constructed). A schema-construction failure in the helper would break every live HTTP test that imports the schema, so the integration is exercised end-to-end without adding new `test_query/` test files. This matches [`docs/SPECS/spec-019-multi_db-0_0_7.md`](SPECS/spec-019-multi_db-0_0_7.md) Decision 6's transitive-coverage posture for axis 2 (`OptimizationPlan.apply` `_db` preservation verified by the live HTTP test seeded-rows assertion).
- The two integration tests in `tests/test_scalars.py` — `test_bigint_serializes_int_via_strawberry_config_schema` and `test_bigint_parses_decimal_string_via_strawberry_config_schema` — pin the schema-execution path in-process so a regression at the schema-construction layer is caught before the fakeshop tree runs. They construct a minimal `strawberry.Schema(query=..., config=strawberry_config())` with a `BigInt`-annotated resolver, run a query / mutation through `schema.execute_sync(...)`, and assert on the JSON output.

Alternatives considered (and rejected):

- **New `tests/test_config.py` next to a new `django_strawberry_framework/config.py`.** Rejected per [Decision 2](#decision-2--helper-api-shape-and-module-location) (no new module).
- **Move the new tests into `tests/base/test_conf.py` because `conf.py` is the closest existing "configuration" module.** Rejected: `tests/base/test_conf.py` covers the `DJANGO_STRAWBERRY_FRAMEWORK` settings reader; the helper has no settings dependency.
- **Add a live HTTP test in `examples/fakeshop/test_query/test_scalars.py` (new file) that exercises a `BigInt`-annotated resolver through `/graphql/`.** Rejected for `0.0.7`: the example project does not currently use `BigInt` directly (no `BigIntegerField` in the fakeshop models per the Step-5 grep). Adding a fakeshop model column just to exercise the helper is gold-plating; the in-process integration tests catch the registration-path regression at the same coverage tier.

### Decision 8 — Version posture: cut already shipped, this card lands under `[Unreleased]`

`0.0.7` already shipped on 2026-05-23 (per the [`CHANGELOG.md #"## [0.0.7] - 2026-05-23"`](../CHANGELOG.md) heading); the `__version__` is pinned at `0.0.7` (per [`django_strawberry_framework/__init__.py #"__version__"`](../django_strawberry_framework/__init__.py) and [`tests/base/test_init.py #"test_version"`](../tests/base/test_init.py)). The `WIP-ALPHA-020-0.0.7` card tag predates the cut; the card is the only `0.0.7`-tagged WIP card remaining (per [Step 3](#step-3--read-the-kanban) — only one WIP card in the `## In progress` column).

This card's `CHANGELOG.md` entries land under `[Unreleased]`, NOT under `[0.0.7]`. The version bump from `0.0.7 → 0.0.8` is owned by whichever card ships last in the next cut bundle, NOT this card.

Justification:

- The `[Unreleased]` section in [`CHANGELOG.md`](../CHANGELOG.md) (anchored at [`CHANGELOG.md #"## [Unreleased]"`](../CHANGELOG.md)) already accumulates entries for the next patch — Changed bullets for the `manage.py export_schema` UX cleanup, a Fixed bullet for OSError wrapping. Per "Keep a Changelog" convention (followed by this repo), the section is the natural home for any new entry that lands after `[0.0.7]` was sealed.
- The card body does NOT request a version bump. `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s pinned version assertion are explicitly excluded from Slice 5 — per [`KANBAN.md #"The last \`0.0.7\` card to ship owns the version bump"`](../KANBAN.md) (interpreted forward: the last card to ship under any future cut owns its bump). The bump from `0.0.7 → 0.0.8` is a future-cut decision.
- This card IS breaking-but-alpha-OK (per [Decision 5](#decision-5--migration-posture-hard-break-in-alpha)). A breaking change joining `[Unreleased]` does NOT automatically force a version bump on this card — the cut decision is when, the bump decision is who.
- The spec filename uses `0_0_7` per the card tag (`spec-020-scalar_map_helper-0_0_7.md`) because the card is `WIP-ALPHA-020-0.0.7`. If a future maintainer re-tags the card to `WIP-ALPHA-020-0.0.8` (because it ended up in the 0.0.8 cut), the spec file moves with the rename — see [Risks](#risks-and-open-questions) entry 1.

Alternatives considered (and rejected):

- **This card bumps `__version__` to `0.0.8` and seals `[Unreleased]` under a new `[0.0.8]` heading.** Rejected: ship order is determined by which card a maintainer picks up next, not by topical fit; pinning the bump to a specific card creates a sequencing constraint that has no engineering justification. Same posture as [`docs/SPECS/spec-019-multi_db-0_0_7.md`](SPECS/spec-019-multi_db-0_0_7.md) Decision 9.
- **Rename the card to `WIP-ALPHA-020-0.0.8` in [`KANBAN.md`](../KANBAN.md) as part of this card.** Rejected: out of scope (the spec's boundary forbids editing [`KANBAN.md`](../KANBAN.md) outside the Slice 5 column move and spec-reference rewrite); the card-tag-vs-cut mismatch is a [`KANBAN.md`](../KANBAN.md) housekeeping concern resolved by whichever maintainer cuts `0.0.8`.
- **Add a separate `TODO-ALPHA-XXX-0.0.8 — 0.0.8 release cut` card to [`KANBAN.md`](../KANBAN.md) that owns the bump.** Rejected per [`docs/SPECS/spec-019-multi_db-0_0_7.md`](SPECS/spec-019-multi_db-0_0_7.md) Decision 9's "the 'last card to ship' policy is workable as-is" precedent.

### Decision 9 — Example-app migration scope

The fakeshop example project is updated in **one place only**: [`examples/fakeshop/config/schema.py`](../examples/fakeshop/config/schema.py) — its sole `strawberry.Schema(` invocation (anchored at [`examples/fakeshop/config/schema.py #"strawberry.Schema(query=Query"`](../examples/fakeshop/config/schema.py)) — the `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])` call becomes `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])` with `strawberry_config` added to the existing `from django_strawberry_framework import ...` line. The per-app schemas at [`examples/fakeshop/apps/library/schema.py`](../examples/fakeshop/apps/library/schema.py) and [`examples/fakeshop/apps/products/schema.py`](../examples/fakeshop/apps/products/schema.py) are NOT modified — they do not construct a `strawberry.Schema(...)` themselves (verified: each app's `schema.py` declares a `@strawberry.type class Query` only; the project-level `config/schema.py` is the one place schema construction happens).

Justification:

- The migration's surface for the example app is exactly one `strawberry.Schema(...)` call. Touching more than that one site is gold-plating.
- The fakeshop models do not use `BigIntegerField` or `PositiveBigIntegerField` today (verified via `grep -rn "BigInt" examples/fakeshop/` — no matches). The example schema does not currently exercise `BigInt` at all; the migration of the `Schema(...)` call is a forward-looking demonstration of the new pattern, not a regression-driven change.
- Adding a fakeshop model column that uses `BigIntegerField` just to exercise `BigInt` through the new helper is out of scope for this card — the helper's correctness is exercised by the in-process integration tests in `tests/test_scalars.py` (per [Decision 7](#decision-7--test-placement-and-shape)).
- Same posture as [`docs/SPECS/spec-019-multi_db-0_0_7.md`](SPECS/spec-019-multi_db-0_0_7.md) Decision 4 (the fakeshop schemas are NOT decorated with multi-db routing because routing is consumer-shaped) and [`docs/SPECS/spec-016-list_field-0_0_7.md`](SPECS/spec-016-list_field-0_0_7.md) Decision 9 (the fakeshop `DjangoListField` demonstration was added as a *sibling* root field rather than rewriting existing schema entries) and [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) Decision 7 (no fakeshop `INSTALLED_APPS` change for the AppConfig card).

Alternatives considered (and rejected):

- **Add a `BigIntegerField` column to a fakeshop model and a corresponding `id: BigInt`-style query in the schema to exercise the round-trip live.** Rejected: out of scope; the helper's correctness is exercised by the in-process tests, and adding a model column is a model-shape decision that belongs in its own card if there is real fakeshop demand for it.
- **Skip the [`examples/fakeshop/config/schema.py`](../examples/fakeshop/config/schema.py) update because the fakeshop schemas don't use `BigInt`.** Rejected: the example project is the package's primary documentation surface for "what consumer code looks like"; leaving it on the pre-migration pattern would confuse readers who copy from it.

## Implementation plan

The slice ships as **five slices** aligned with the [Slice checklist](#slice-checklist). Each slice maps to one commit; squashing all five into a single PR is acceptable given the small surface (~120 lines total delta).

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — Helper module + `BigInt` redefinition | [`django_strawberry_framework/scalars.py`](../django_strawberry_framework/scalars.py), [`django_strawberry_framework/__init__.py`](../django_strawberry_framework/__init__.py) | 0 | `+30 / -25` (net +5 — replace suppression block with helper + dict; bare-`NewType` redefinition is a one-line swap) |
| 2 — Tests | [`tests/test_scalars.py`](../tests/test_scalars.py) (extend), [`tests/base/test_init.py`](../tests/base/test_init.py) (one-line edit) | 10 (eight factory tests + two integration tests in `tests/test_scalars.py`; the `test_public_api_surface_is_pinned` assertion in `tests/base/test_init.py` is modified, not new) | `+150 / -2` |
| 3 — Example-app migration | [`examples/fakeshop/config/schema.py`](../examples/fakeshop/config/schema.py) | 0 | `+2 / -1` |
| 4 — Docs | [`docs/README.md`](README.md), [`docs/GLOSSARY.md`](GLOSSARY.md), [`GOAL.md`](../GOAL.md), [`TODAY.md`](../TODAY.md) | 0 | `+50 / -10` |
| 5 — KANBAN + CHANGELOG | [`KANBAN.md`](../KANBAN.md), [`CHANGELOG.md`](../CHANGELOG.md) | 0 | `+25 / -6` (the `-6` includes the removed `[0.0.6]` `### Notes` line plus minor reflow) |

Total expected delta: ~260 lines across five slices.

The five slices must be authored in order. Slice 2 depends on Slice 1 (the tests target the new helper and the migrated `BigInt` shape); Slice 3 depends on Slice 1 + Slice 2 (the example migration uses the helper, and the test suite is what proves it works); Slice 4 depends on Slice 3 (the docs reference the migrated example as the "what to type" canonical reference); Slice 5 depends on Slice 4 (the CHANGELOG entry summarizes the docs + example state).

## Edge cases and constraints

- **Strawberry version with the no-warning overload.** Verified at [`.venv/lib/python3.10/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`](../.venv/lib/python3.10/site-packages/strawberry/types/scalar.py) that the package's pinned Strawberry version (whichever `pyproject.toml` resolves) supports the `cls is None and name is not None` branch. If a consumer pins an older Strawberry that lacks the overload, Slice 1's redefinition fails at package import — the failure mode is loud (TypeError at import), not silent. The package's [`pyproject.toml`](../pyproject.toml) Strawberry version constraint is the contract that ensures the overload exists; any change to that constraint is out of scope here.
- **`BigInt` as a `NewType` is not isinstance-checkable.** `isinstance(x, BigInt)` raises `TypeError` because `NewType` is not a class at runtime. Consumer code that does `isinstance(value, BigInt)` would already fail today (this is not a regression introduced by the migration); the package does not document `BigInt` as isinstance-checkable, so no consumer contract is affected.
- **`StrawberryConfig.scalar_map` is a `Mapping`, not a `dict`.** The factory's return type is `StrawberryConfig(scalar_map=<a dict>)`, but the field type accepts any `Mapping`. The implementation builds a fresh `dict` per call so a downstream `StrawberryConfig.scalar_map.update(...)` (if Strawberry ever does that internally — currently it doesn't) doesn't mutate the consumer's `extra_scalar_map`.
- **Independent return value semantics.** Each `strawberry_config(...)` call returns a new `StrawberryConfig` instance with a new `scalar_map` dict. Mutations on the returned object (e.g., `config.scalar_map["X"] = ...`) do NOT leak to the next call's return value. Pinned by `test_strawberry_config_independent_call_returns_independent_instance` in [Test plan](#test-plan).
- **`extra_scalar_map={}` is equivalent to `extra_scalar_map=None`.** Both produce the package-default-only `scalar_map`. Pinned by `test_strawberry_config_accepts_empty_extra_scalar_map`.
- **`extra_scalar_map` mutation post-call.** The factory copies the `extra_scalar_map` dict into the returned `StrawberryConfig` (because `dict(scalar_map) | dict(extra_scalar_map)` builds a new dict). A consumer's later mutation of their `extra_scalar_map` does NOT affect the returned `StrawberryConfig`. Pinned by `test_strawberry_config_extra_scalar_map_does_not_mutate_caller_dict`.
- **Collision-error message stability.** The `ValueError` message names the colliding keys' `__name__` attribute when the key is a `NewType` (per Python's `NewType` convention of carrying a `__name__`). For `class`-keyed scalars (uncommon but supported by Strawberry's `Mapping[object, ScalarDefinition]` contract), the `__name__` lookup still works. The message format is pinned by `test_strawberry_config_collision_with_package_scalar_raises_value_error`.
- **`from django_strawberry_framework import strawberry_config` ordering.** The `__init__.py` widens the existing `from .scalars import BigInt` line (anchored at [`django_strawberry_framework/__init__.py #"from .scalars import BigInt"`](../django_strawberry_framework/__init__.py)) to `from .scalars import BigInt, strawberry_config`. The new symbol is exported from the same module's re-export line, no new import statement is added. `__all__` ordering: `"strawberry_config"` lands between `"OptimizerHint"` and `"__version__"` alphabetically (so `__all__` reads: `"BigInt", "DjangoListField", "DjangoOptimizerExtension", "DjangoType", "OptimizerHint", "strawberry_config", "__version__", "auto", "finalize_django_types"`).
- **`tests/test_scalars.py` test count.** The file currently carries 22+ tests (counted by `grep -c "^def test_" tests/test_scalars.py`); post-Slice-2 it carries 22+10 = 32+ tests. The existing `test_package_import_does_not_emit_strawberry_deprecation_warning` continues to pass without modification per [Decision 6](#decision-6--remove-the-warningscatch_warnings-suppression-block); the count and the assertion are intact.
- **Coverage at 100%.** The new factory body adds ~10 production lines (helper definition + collision-raise branch). All branches are covered by Slice 2 tests: default-path coverage by `test_strawberry_config_default_scalar_map_includes_bigint`, `None`/`{}` cases by `test_strawberry_config_accepts_none_extra_scalar_map` and `test_strawberry_config_accepts_empty_extra_scalar_map`, merge path by `test_strawberry_config_merges_extra_scalar_map`, collision-raise by `test_strawberry_config_collision_with_package_scalar_raises_value_error`. No uncoverable branches; [`pyproject.toml`](../pyproject.toml) `[tool.coverage.report] fail_under = 100` continues to pass.

## Test plan

Tests live in [`tests/test_scalars.py`](../tests/test_scalars.py) (extended) per [Decision 7](#decision-7--test-placement-and-shape). Test-tree placement is mandatory; no `tests/test_config.py` is added.

### `tests/test_scalars.py` (extend) — eight factory tests + two integration tests

Package tests; system-under-test is `strawberry_config(...)` in [`django_strawberry_framework/scalars.py`](../django_strawberry_framework/scalars.py) and the migrated `BigInt` registration shape. **Eight** factory tests + **two** integration tests = ten new tests added to the existing file. Single pytest item per test, no `pytest.mark.parametrize` fan-out so the count matches pytest collection output unambiguously.

**Imports** (added to the existing import block at the top of [`tests/test_scalars.py`](../tests/test_scalars.py)):

```python path=null start=null
from typing import NewType

import pytest
import strawberry
from strawberry.schema.config import StrawberryConfig
from strawberry.types.scalar import ScalarDefinition

from django_strawberry_framework import BigInt, strawberry_config
```

The `pytest` import is used by the collision test's `pytest.raises(ValueError)` block; the rest of the imports are used by the factory and integration tests as written below. Slice 2 runs `uv run ruff check --fix .` over the file; if any of the listed imports turn out unused at write time (ruff's `F401`), the worker drops the unused row rather than adding a use-only-in-comment to defeat the check.

#### Factory tests

- `test_strawberry_config_returns_strawberry_config_instance` — calls `strawberry_config()` with no arguments; asserts `isinstance(result, StrawberryConfig)`. Pins the return-type contract from [Decision 2](#decision-2--helper-api-shape-and-module-location).
- `test_strawberry_config_default_scalar_map_includes_bigint` — calls `strawberry_config()` with no arguments; asserts `BigInt in result.scalar_map` AND `isinstance(result.scalar_map[BigInt], ScalarDefinition)` AND `result.scalar_map[BigInt].name == "BigInt"`. Pins the package-default scalar registration from [Decision 3](#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition).
- `test_strawberry_config_accepts_none_extra_scalar_map` — calls `strawberry_config(extra_scalar_map=None)` explicitly; asserts `len(result.scalar_map) == 1` AND `BigInt in result.scalar_map`. Pins that explicit `None` is identical to the no-argument default.
- `test_strawberry_config_accepts_empty_extra_scalar_map` — calls `strawberry_config(extra_scalar_map={})`; asserts `len(result.scalar_map) == 1` AND `BigInt in result.scalar_map`. Pins that empty-dict is identical to `None` ([Edge cases](#edge-cases-and-constraints)).
- `test_strawberry_config_merges_extra_scalar_map` — declares `CustomScalar = NewType("CustomScalar", str)` AND `custom_def = strawberry.scalar(name="CustomScalar", serialize=str, parse_value=str)`; calls `strawberry_config(extra_scalar_map={CustomScalar: custom_def})`; asserts `len(result.scalar_map) == 2` AND both `BigInt` and `CustomScalar` are present AND `result.scalar_map[CustomScalar] is custom_def`. Pins the merge contract from [Decision 2](#decision-2--helper-api-shape-and-module-location).
- `test_strawberry_config_extra_scalar_map_does_not_mutate_caller_dict` — declares `caller_dict = {CustomScalar: custom_def}` AND a frozen reference `before = dict(caller_dict)`; calls `strawberry_config(extra_scalar_map=caller_dict)`; asserts `caller_dict == before` (caller dict unchanged). Pins the no-side-effect contract from [Edge cases](#edge-cases-and-constraints).
- `test_strawberry_config_collision_with_package_scalar_raises_value_error` — declares `alt_def = strawberry.scalar(name="AltBigInt", serialize=str, parse_value=int)`; calls `strawberry_config(extra_scalar_map={BigInt: alt_def})` inside `pytest.raises(ValueError) as excinfo`; asserts the exception message contains `"BigInt"` AND the substring `"cannot redeclare"`. Pins the hard-error policy from [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions).
- `test_strawberry_config_independent_call_returns_independent_instance` — calls `strawberry_config()` twice into `c1, c2`; asserts `c1 is not c2` AND `c1.scalar_map is not c2.scalar_map`. Mutates `c1.scalar_map[CustomScalar] = custom_def` then asserts `CustomScalar not in c2.scalar_map`. Pins the per-call-fresh-instance contract from [Edge cases](#edge-cases-and-constraints).

#### Integration tests

These two tests build a minimal Strawberry schema that uses `BigInt` and exercise the registration path end-to-end via `schema.execute_sync(...)`. They pin the post-migration round trip so a future regression at the registration layer is caught at the test tier.

- `test_bigint_serializes_int_via_strawberry_config_schema` — declares `@strawberry.type class Q: @strawberry.field def big(self) -> BigInt: return 9_223_372_036_854_775_807` (`int64_max`); constructs `schema = strawberry.Schema(query=Q, config=strawberry_config())`; runs `result = schema.execute_sync("{ big }")`; asserts `result.errors is None` AND `result.data == {"big": "9223372036854775807"}` (decimal string, not int). Pins the wire-format survival contract through the migrated registration path.
- `test_bigint_parses_decimal_string_via_strawberry_config_schema` — declares `@strawberry.type class Q: @strawberry.field def echo(self, value: BigInt) -> BigInt: return value`; constructs `schema = strawberry.Schema(query=Q, config=strawberry_config())`; runs `result = schema.execute_sync('{ echo(value: "9223372036854775807") }')`; asserts `result.errors is None` AND `result.data == {"echo": "9223372036854775807"}`. Pins the parser path through the migrated registration.

### Existing tests — one one-line modification, no other edits

The `test_public_api_surface_is_pinned` assertion in [`tests/base/test_init.py`](../tests/base/test_init.py) (anchored at [`tests/base/test_init.py #"test_public_api_surface_is_pinned"`](../tests/base/test_init.py)) is modified to insert `"strawberry_config"` between `"OptimizerHint"` and `"__version__"` in the pinned `__all__` tuple. Slice 2 commits this edit alongside the new factory tests.

The existing `test_package_import_does_not_emit_strawberry_deprecation_warning` test at [`tests/test_scalars.py #"test_package_import_does_not_emit_strawberry_deprecation_warning"`](../tests/test_scalars.py) is NOT modified — its `python -W error::DeprecationWarning -c "import django_strawberry_framework"` subprocess check still passes because the new registration path no longer triggers the deprecation at all (per [Decision 6](#decision-6--remove-the-warningscatch_warnings-suppression-block)).

All other tests in [`tests/test_scalars.py`](../tests/test_scalars.py) (the 22+ parser / serializer pins) are unchanged.

## Doc updates

- [`docs/GLOSSARY.md`](GLOSSARY.md)
  - **[Public exports](GLOSSARY.md#public-exports) list update:** add `strawberry_config` to the bulleted re-exports list, between `OptimizerHint` and `finalize_django_types` (alphabetical placement matches `__all__`).
  - **[Index](GLOSSARY.md#index) table update:** add a new row `| [strawberry_config](#strawberry_config) | shipped ([Unreleased]) |` in alphabetical position. Note: the Index table uses `shipped (X.Y.Z)` for shipped entries; for the post-cut [Unreleased] case (this card), the status text uses the literal `shipped ([Unreleased])` placeholder to be promoted by the maintainer at the next cut.
  - **New entry: `## strawberry_config`** — between [`Specialized scalar conversions`](GLOSSARY.md#specialized-scalar-conversions) and [Strictness mode](GLOSSARY.md#strictness-mode) alphabetically. Body:

    > **Status:** shipped ([Unreleased]).
    >
    > Factory returning a [`StrawberryConfig`](https://strawberry.rocks) pre-populated with the package's `scalar_map` — the registration path consumers use to bind package-defined scalars (today: [`BigInt`](#bigint-scalar); next: [`Upload`](#upload-scalar) in `0.0.11`) into their `strawberry.Schema(...)` call.
    >
    > ```python
    > from django_strawberry_framework import strawberry_config
    >
    > schema = strawberry.Schema(
    >     query=Query,
    >     config=strawberry_config(),
    >     extensions=[DjangoOptimizerExtension()],
    > )
    > ```
    >
    > Consumers composing custom scalars on top pass them via `extra_scalar_map=`:
    >
    > ```python
    > MyULID = NewType("MyULID", str)
    > schema = strawberry.Schema(
    >     query=Query,
    >     config=strawberry_config(extra_scalar_map={MyULID: my_ulid_definition}),
    > )
    > ```
    >
    > Collision with a package-defined scalar in `extra_scalar_map` raises `ValueError` (the factory does not silently override package defaults); register the consumer scalar under a different `NewType` / class to keep both. Each call returns a fresh `StrawberryConfig` instance with a fresh `scalar_map` dict; mutations on the returned object do not leak across calls.
    >
    > **See also:** [`BigInt scalar`](#bigint-scalar) · [`Upload scalar`](#upload-scalar) · [`Specialized scalar conversions`](#specialized-scalar-conversions).
  - **[`BigInt scalar`](GLOSSARY.md#bigint-scalar) entry update**: append after the strict-serializer sentence:

    > "Consumers register `BigInt` via the [`strawberry_config`](#strawberry_config) factory on their `strawberry.Schema(...)` call: `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])`. Direct `BigInt` annotations (`category: BigInt`, `@strawberry.field def big_id(self) -> BigInt: ...`) continue to work unchanged at the schema-declaration site; the registration path changes, not the symbol. The migration applies to any schema that resolves to `BigInt` — including [`DjangoType`](#djangotype) schemas whose fields are backed by `BigIntegerField` or `PositiveBigIntegerField` (resolved to `BigInt` by the [`Specialized scalar conversions`](#specialized-scalar-conversions) converter table) even when the consumer never imports or annotates `BigInt` directly."

- [`docs/README.md`](README.md)
  - Rewrite the [Quick start](README.md#quick-start) code block to add `strawberry_config` to the import line and `config=strawberry_config()` to the `strawberry.Schema(...)` call.
  - Rewrite the [Relay Node](README.md#relay-node) example the same way (the example constructs a schema near the end of its block).
  - Rewrite the "Wrong order" anti-example inside the [Schema setup boundary](README.md#schema-setup-boundary) section to mirror the new shape so the contrast still illustrates the finalize-order pitfall.
  - No change to the surrounding prose; the migration is purely a code-block update.

- [`GOAL.md`](../GOAL.md)
  - Rewrite the astronomy [`schema.py`](../GOAL.md#schemapy) example block — add `strawberry_config` to the imports list and `config=strawberry_config()` to the showcase's terminal `strawberry.Schema(...)` call (anchored at [`GOAL.md #"strawberry.Schema(query=Query"`](../GOAL.md)). No other change.
  - The per-stack diff blocks inside the [Migration shape](../GOAL.md#migration-shape) section (`Coming from graphene-django` / `Coming from strawberry-graphql-django` / `Coming from DRF + django-filter`) are NOT edited — those blocks intentionally show minimal `Meta`-shape diffs and adding a `config=` line would distract from the per-stack migration point. The astronomy showcase (which IS edited) is the one place a consumer sees the "right shape" end-to-end.

- [`TODAY.md`](../TODAY.md)
  - Rewrite the [What to put in `examples/fakeshop/config/schema.py` today](../TODAY.md#what-to-put-in-examplesfakeshopconfigschemapy-today) block — add `strawberry_config` to the imports and `config=strawberry_config()` to the `strawberry.Schema(...)` call, mirroring the [`docs/README.md`](README.md) Quick start update.
  - No other change; the [What's in `examples/fakeshop/apps/products/schema.py` today](../TODAY.md#whats-in-examplesfakeshopappsproductsschemapy-today) section does not construct a project-level schema, so no edit is needed there.

- [`docs/TREE.md`](TREE.md): no edit. Per [Decision 2](#decision-2--helper-api-shape-and-module-location), the helper lives in the existing [`django_strawberry_framework/scalars.py`](../django_strawberry_framework/scalars.py); no new file under `django_strawberry_framework/` and no new test file under `tests/`. The current-on-disk-layout enumeration (anchored at [`docs/TREE.md #"scalars.py"`](TREE.md)) already mentions `scalars.py` — the entry stays as-is.

- [`KANBAN.md`](../KANBAN.md) (Slice 5)
  - Move `WIP-ALPHA-020-0.0.7` to the Done column with the next available `DONE-NNN-0.0.7` id (the column-move pass renumbers as usual; the next available id is determined at merge time, not pinned in this spec). Past-tense Done body:

    > "Pinned the package-defined scalar registration path: [`BigInt`](docs/GLOSSARY.md#bigint-scalar) is redefined as a bare `NewType("BigInt", int)` and registered via [`StrawberryConfig.scalar_map`](https://strawberry.rocks) through a new public [`strawberry_config(extra_scalar_map=None) -> StrawberryConfig`](docs/GLOSSARY.md#strawberry_config) factory exported from `django_strawberry_framework`. Consumers add `config=strawberry_config()` to their `strawberry.Schema(...)` call once; direct `BigInt` annotations work unchanged. The `warnings.catch_warnings()` suppression block in `django_strawberry_framework/scalars.py` is removed because the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload at `.venv/lib/python3.10/site-packages/strawberry/types/scalar.py` returns a `ScalarDefinition` without triggering the `DeprecationWarning`. Tests in `tests/test_scalars.py` cover the factory contract (eight tests) and the round-trip wire format through a `strawberry.Schema(config=strawberry_config())` (two integration tests); `tests/base/test_init.py`'s `__all__` assertion adds `strawberry_config`. `examples/fakeshop/config/schema.py` migrates to the new pattern; `docs/README.md`, `docs/GLOSSARY.md`, `GOAL.md`, and `TODAY.md` schema-construction examples migrate too. Breaking change in alpha (per `docs/SPECS/spec-013-deferred_scalars-0_0_6.md` Decision 6 and the `PositiveBigIntegerField` precedent in `0.0.6`): consumers using `BigInt` directly in `0.0.6` who don't add `config=strawberry_config()` see Strawberry schema-construction fail with `Unexpected type ...BigInt`. Spec: `docs/spec-020-scalar_map_helper-0_0_7.md`. The version bump from `0.0.7 → 0.0.8` is NOT in this card per Decision 8."
  - Update the card body's `Definition of done` bullet 1 (`docs/spec-scalar_map_helper.md` → `docs/SPECS/spec-020-scalar_map_helper-0_0_7.md` after the Step-8 archive pass per [Decision 1](#decision-1--spec-filename-and-canonical-naming)).
  - Update the `### In progress` summary paragraph (anchored at [`KANBAN.md #"### In progress"`](../KANBAN.md)) to remove `WIP-ALPHA-020-0.0.7` from the remaining-cards list once this card moves to Done.

- [`CHANGELOG.md`](../CHANGELOG.md) (Slice 5)
  - **Append** to the existing `[Unreleased]` `### Added` subsection:

    > "`strawberry_config` — factory function (`django_strawberry_framework/scalars.py`) returning a `strawberry.schema.config.StrawberryConfig` pre-populated with the package's `scalar_map`. Consumers compose package-defined scalars into their schema via `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])`. Accepts an optional `extra_scalar_map=` parameter to merge consumer-defined scalars; collisions with package defaults raise `ValueError`. New public export from `django_strawberry_framework`; `__all__` widened. See [`strawberry_config`](docs/GLOSSARY.md#strawberry_config)."
  - **Append** to the existing `[Unreleased]` `### Changed` subsection:

    > "**Breaking change**: `BigInt` registration moved from `strawberry.scalar(NewType("BigInt", int), name="BigInt", ...)` to the `StrawberryConfig.scalar_map` path. Any schema that resolves to `BigInt` — whether through a direct `BigInt` annotation (`category: BigInt`, `@strawberry.field def x(self) -> BigInt: ...`) OR through a [`DjangoType`](docs/GLOSSARY.md#djangotype) field backed by `BigIntegerField` / `PositiveBigIntegerField` (resolved by the [`Specialized scalar conversions`](docs/GLOSSARY.md#specialized-scalar-conversions) converter table) — must add `config=strawberry_config()` to its `strawberry.Schema(...)` call; Strawberry schema construction will fail with `Unexpected type ...BigInt` without it. The migration applies even to consumers who never import or annotate `BigInt` directly, because the converter table resolves the field type to `BigInt` for them. Matches the `PositiveBigIntegerField → BigInt` precedent in `0.0.6`. Single-line migration:
    >
    > ```diff
    > - schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    > + from django_strawberry_framework import strawberry_config
    > + schema = strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])
    > ```
    >
    > The wire format, parser, serializer, and direct-annotation usage of `BigInt` are unchanged."
  - **Append** to the existing `[Unreleased]` `### Removed` subsection (the subsection currently does not exist under `[Unreleased]`; add it if absent):

    > "Internal `warnings.catch_warnings()` suppression block in `django_strawberry_framework/scalars.py` that silenced Strawberry's `Passing a class to strawberry.scalar() is deprecated` `DeprecationWarning`. No longer needed — the migrated registration path uses Strawberry's no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload."
  - **Remove** the `[0.0.6]` `### Notes` line at [`CHANGELOG.md #"Migration to a"`](../CHANGELOG.md) (the literal sentence "The internal `BigInt` scalar definition uses `strawberry.scalar(NewType, ...)`, which Strawberry deprecates in favor of `StrawberryConfig.scalar_map`. The deprecation warning is suppressed at the definition site so the package import remains clean. Migration to a `scalar_map`-based design is tracked as a follow-up and will be a real public-API change for consumers using `BigInt` directly."). The `Notes` line advertised the architectural debt this card pays down; with the migration shipped, removing it keeps the `[0.0.6]` section a clean snapshot of what shipped (the `Notes` line was a forward-looking pointer, not a historical fact).
  - The version bump is NOT in this card per [Decision 8](#decision-8--version-posture-cut-already-shipped-this-card-lands-under-unreleased); a future cut promotes `[Unreleased]` to `[0.0.8]` and bumps `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s version assertion in one atomic commit.
  - The CHANGELOG-edit-permission rule at [`AGENTS.md #"Do not update CHANGELOG.md unless explicitly instructed"`](../AGENTS.md) — this Slice 5 bullet is the explicit instruction.

## Risks and open questions

Each item names a preferred answer for the current cut and a fallback if implementation reveals the preferred answer is wrong.

- **`WIP-ALPHA-020-0.0.7` card-tag versus the already-cut `[0.0.7]` heading.** The card's tag predates the 2026-05-23 `0.0.7` cut; the card now lands under `[Unreleased]` per [Decision 8](#decision-8--version-posture-cut-already-shipped-this-card-lands-under-unreleased). Preferred answer: the spec filename uses `0_0_7` per the card tag (`spec-020-scalar_map_helper-0_0_7.md`); the `CHANGELOG.md` entry uses `[Unreleased]`; the [`KANBAN.md`](../KANBAN.md) maintainer reconciles the tag-vs-cut mismatch when they cut `0.0.8` (re-tagging the card body and the spec filename to `0_0_8` is a one-line edit that does not affect any production behavior). Fallback: if the maintainer decides to ship the spec under a `WIP-ALPHA-020-0.0.8` tag before Slice 5 lands, the spec filename moves to `docs/spec-020-scalar_map_helper-0_0_8.md` in the same commit; production-code surface is unaffected because the spec's content is version-agnostic except for the filename.
- **`KANBAN.md` card body names `docs/spec-scalar_map_helper.md`; spec ships as `docs/spec-020-scalar_map_helper-0_0_7.md`.** Per [Decision 1](#decision-1--spec-filename-and-canonical-naming), the canonical name is the structured one. Preferred answer: Slice 5 rewrites the card body's `Definition of done` bullet 1 to point at the structured name; the Step-8 archive pass at the end of the NEXT.md flow propagates the rename to any other cross-references. Fallback: if a future agent confused by the rename creates a second `docs/spec-scalar_map_helper.md`, the structured filename's content takes precedence; the stray file is deleted in a follow-up cleanup card.
- **Strawberry's no-warning overload signature stability.** [`strawberry.scalar(name=..., serialize=..., parse_value=...)`](https://strawberry.rocks) returning a `ScalarDefinition` is the documented and recommended path. Preferred answer: the package pins Strawberry to a version that supports this overload via [`pyproject.toml`](../pyproject.toml); a regression in the overload signature is caught by `test_strawberry_config_default_scalar_map_includes_bigint` (and the wider `test_bigint_*` parser/serializer suite) at CI time. Fallback: if Strawberry deprecates the no-class overload in a future release (extremely unlikely; it's the documented replacement for the old deprecated overload), the package re-evaluates — but pinning Strawberry's recommended path is the right answer today.
- **`isinstance(value, BigInt)` is not supported by `NewType`.** Pre-migration, `BigInt = strawberry.scalar(NewType, ...)` returned a `ScalarWrapper`-shaped object; post-migration, `BigInt` is a bare `NewType` that doesn't support `isinstance` checks. Preferred answer: this is not a regression — consumers should not have been calling `isinstance(x, BigInt)` because `NewType` runtime semantics are documented at the Python typing level. The package does NOT advertise `BigInt` as isinstance-checkable in any [`docs/GLOSSARY.md`](GLOSSARY.md) entry. Fallback: if real consumer breakage surfaces (extremely unlikely for an alpha package's first-defined scalar), a follow-up card could add an `is_bigint(value) -> bool` helper, but `0.0.7` does not need it.
- **`extra_scalar_map` collisions with future package-defined scalars.** When `Upload` (`TODO-ALPHA-028-0.0.11`) ships in `0.0.11`, `_PACKAGE_SCALAR_MAP` grows a second entry. A consumer who passed `extra_scalar_map={Upload: <their custom def>}` in `0.0.11` would suddenly hit the [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions) hard-error wall — but only if they used `Upload` (the symbol) as their key, which they couldn't have done in `0.0.7` because `Upload` doesn't exist yet. Preferred answer: this is a non-issue today; the `Upload` card will document the addition in its own CHANGELOG entry and the collision-error message names the offending key clearly. Fallback: none needed; the consumer collision space is empty by construction in `0.0.7`.
- **Strawberry version pin compatibility.** Verified at [`.venv/lib/python3.10/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`](../.venv/lib/python3.10/site-packages/strawberry/types/scalar.py) that the package's currently-resolved Strawberry version supports the `cls is None and name is not None` overload. Preferred answer: this is the documented Strawberry path; the package's `pyproject.toml` Strawberry constraint already requires a version where this exists. Fallback: if [`pyproject.toml`](../pyproject.toml) is updated post-merge to allow an older Strawberry, the Slice 2 tests catch the regression at CI time.
- **The example fakeshop schema does not exercise `BigInt`.** Slice 3 migrates the schema-construction call but the fakeshop models do not include `BigIntegerField` / `PositiveBigIntegerField`. Preferred answer: the helper's correctness is exercised by the in-process integration tests in `tests/test_scalars.py` per [Decision 7](#decision-7--test-placement-and-shape) — `test_bigint_serializes_int_via_strawberry_config_schema` and `test_bigint_parses_decimal_string_via_strawberry_config_schema` construct an in-process schema that exercises the round trip; the live HTTP path is exercised transitively (every fakeshop test that imports `config.schema` runs the helper at module-import time). Fallback: a future card may add a `BigIntegerField` column to a fakeshop model and a `BigInt`-annotated resolver to a fakeshop app schema, but that is a model-shape decision outside this card's scope.
- **Suppression-removal regression detection.** The existing `test_package_import_does_not_emit_strawberry_deprecation_warning` test at [`tests/test_scalars.py #"test_package_import_does_not_emit_strawberry_deprecation_warning"`](../tests/test_scalars.py) uses a `-W error::DeprecationWarning` subprocess. Preferred answer: post-migration, the test continues to pass because the new registration path does not emit the warning at all; the test pins the contract regardless of which mechanism (suppression or no-warning overload) produces a clean import. Fallback: if a future Strawberry change reintroduces a deprecation along the `strawberry.scalar(name=..., ...)` overload path, the regression test catches it at CI time and the package adapts in a follow-up card.

## Out of scope (explicitly tracked elsewhere)

- Composing Strawberry extensions through this helper. `extensions=` belongs on `strawberry.Schema(..., extensions=[...])`, not on `StrawberryConfig`. The card body explicitly excludes this; no follow-up card exists.
- Auto-discovery of the package config via a Django settings key (e.g., `STRAWBERRY_CONFIG_FACTORY = "django_strawberry_framework.scalars.strawberry_config"`). Per the settings-keys rule at [`AGENTS.md #"Add settings keys only when the feature that needs them lands"`](../AGENTS.md), settings keys land with the feature that needs them; no current feature needs auto-discovery.
- Promoting [`Upload`](GLOSSARY.md#upload-scalar) (planned for `0.0.11`) early. `Upload` is `TODO-ALPHA-028-0.0.11`; the helper this card ships is the registration point `Upload` reuses without modification.
- A `dst.Schema(...)` wrapper around `strawberry.Schema`. Excluded by [Decision 2](#decision-2--helper-api-shape-and-module-location); no follow-up card.
- A static `SCALAR_MAP` constant exposed as a public re-export. Excluded by [Decision 2](#decision-2--helper-api-shape-and-module-location); the consumer composition story goes through the factory.
- Modifying the converter table at [`django_strawberry_framework/types/converters.py`](../django_strawberry_framework/types/converters.py). The `BigIntegerField → BigInt` / `PositiveBigIntegerField → BigInt` entries reference `BigInt` by name; the symbol's import path is unchanged.
- Renaming or aliasing `BigInt`. Out of scope; no follow-up card.
- Multi-database cooperation: [`docs/SPECS/spec-019-multi_db-0_0_7.md`](SPECS/spec-019-multi_db-0_0_7.md) — independent shipped sibling.
- AppConfig and Trac #37064 hardening: [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) and `DONE-046-0.0.7` — independent shipped siblings.
- `DjangoListField`: [`docs/SPECS/spec-016-list_field-0_0_7.md`](SPECS/spec-016-list_field-0_0_7.md) — independent shipped sibling.
- Schema export management command: [`docs/SPECS/spec-018-export_schema-0_0_7.md`](SPECS/spec-018-export_schema-0_0_7.md) — independent shipped sibling.
- [Connection-aware optimizer planning](GLOSSARY.md#connection-aware-optimizer-planning): planned for `0.0.9` — unrelated subsystem despite the overlapping word "connection."
- [`FilterSet`](GLOSSARY.md#filterset) / [`OrderSet`](GLOSSARY.md#orderset) / [`AggregateSet`](GLOSSARY.md#aggregateset) / [`FieldSet`](GLOSSARY.md#fieldset) and the Layer-3 sidecar subsystems: future cards under [`KANBAN.md`](../KANBAN.md)'s Layer-3 backlog; independent of this card.

## Definition of done

The card is complete when all of the following are true:

1. [`docs/spec-020-scalar_map_helper-0_0_7.md`](spec-020-scalar_map_helper-0_0_7.md) (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion [`docs/spec-020-scalar_map_helper-0_0_7-terms.csv`](spec-020-scalar_map_helper-0_0_7-terms.csv) anchoring every project-specific term used in the spec body to the matching [`docs/GLOSSARY.md`](GLOSSARY.md) heading (per [`docs/SPECS/NEXT.md`](SPECS/NEXT.md) Step 7).
2. [`django_strawberry_framework/scalars.py`](../django_strawberry_framework/scalars.py) defines `BigInt = NewType("BigInt", int)` as a bare `NewType`, builds `_BIGINT_SCALAR_DEFINITION: ScalarDefinition` via `strawberry.scalar(name="BigInt", serialize=_serialize_bigint, parse_value=_parse_bigint)`, exposes `_PACKAGE_SCALAR_MAP: dict[object, ScalarDefinition] = {BigInt: _BIGINT_SCALAR_DEFINITION}`, and exposes `strawberry_config(extra_scalar_map: Mapping[object, ScalarDefinition] | None = None) -> StrawberryConfig` per [Decision 2](#decision-2--helper-api-shape-and-module-location) and [Decision 3](#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition). The `with warnings.catch_warnings(): warnings.filterwarnings("ignore", message="Passing a class to strawberry.scalar", ...)` block is removed; `import warnings` is removed if no other code uses it (per [Decision 6](#decision-6--remove-the-warningscatch_warnings-suppression-block)). `_parse_bigint` and `_serialize_bigint` are unchanged from `0.0.6`.
3. [`django_strawberry_framework/__init__.py`](../django_strawberry_framework/__init__.py) widens the existing `from .scalars import BigInt` line to `from .scalars import BigInt, strawberry_config`; `__all__` adds `"strawberry_config"` in alphabetical position between `"OptimizerHint"` and `"__version__"`.
4. [`tests/test_scalars.py`](../tests/test_scalars.py) is extended with the **8 factory tests** listed in the [Test plan](#test-plan): `test_strawberry_config_returns_strawberry_config_instance`, `test_strawberry_config_default_scalar_map_includes_bigint`, `test_strawberry_config_accepts_none_extra_scalar_map`, `test_strawberry_config_accepts_empty_extra_scalar_map`, `test_strawberry_config_merges_extra_scalar_map`, `test_strawberry_config_extra_scalar_map_does_not_mutate_caller_dict`, `test_strawberry_config_collision_with_package_scalar_raises_value_error`, `test_strawberry_config_independent_call_returns_independent_instance`. AND the **2 integration tests** listed in the [Test plan](#test-plan): `test_bigint_serializes_int_via_strawberry_config_schema`, `test_bigint_parses_decimal_string_via_strawberry_config_schema`. No `pytest.mark.parametrize` fan-out (single pytest item per test); ten pytest items total added to the file.
5. [`tests/test_scalars.py`](../tests/test_scalars.py) `test_package_import_does_not_emit_strawberry_deprecation_warning` is UNCHANGED and continues to pass (the migrated registration path no longer triggers the deprecation at all per [Decision 6](#decision-6--remove-the-warningscatch_warnings-suppression-block)).
6. [`tests/base/test_init.py`](../tests/base/test_init.py) `test_public_api_surface_is_pinned` inserts `"strawberry_config"` between `"OptimizerHint"` and `"__version__"` in the pinned `__all__` tuple.
6a. [`tests/types/test_converters.py`](../tests/types/test_converters.py) is migrated: every `strawberry.Schema(query=Query)` call inside the `BigInt scalar — schema-execution field-mapping tests` section is rewritten to `strawberry.Schema(query=Query, config=strawberry_config())` (11 sites); the file's import line adds `strawberry_config` to the `from django_strawberry_framework import ...` line. Schemas in non-BigInt sections (JSONField / Choice-enum / Relation / Boolean / BigAuto-as-ID tests) are NOT migrated.
6b. [`tests/test_scalars.py`](../tests/test_scalars.py) module docstring is updated to acknowledge that this file now ALSO carries the two `strawberry.Schema(query=..., config=strawberry_config())` integration tests added in Slice 2 (the delegation-to-`tests/types/test_converters.py` sentence is preserved, the new role is appended).
7. [`examples/fakeshop/config/schema.py`](../examples/fakeshop/config/schema.py) is rewritten per [Decision 9](#decision-9--example-app-migration-scope): `strawberry_config` is added to the existing `from django_strawberry_framework import ...` line; `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])` becomes `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])`. No other change.
8. [`examples/fakeshop/apps/library/schema.py`](../examples/fakeshop/apps/library/schema.py) and [`examples/fakeshop/apps/products/schema.py`](../examples/fakeshop/apps/products/schema.py) are NOT modified (audit-only — neither file constructs a `strawberry.Schema(...)`).
9. [`docs/GLOSSARY.md`](GLOSSARY.md): the [`BigInt scalar`](GLOSSARY.md#bigint-scalar) entry body carries the new construction-pattern paragraph per [Doc updates](#doc-updates); a new `## strawberry_config` entry exists alphabetically between [`Specialized scalar conversions`](GLOSSARY.md#specialized-scalar-conversions) and [Strictness mode](GLOSSARY.md#strictness-mode) with the body pinned in [Doc updates](#doc-updates); the `Public exports` list and the alphabetical `Index` table carry `strawberry_config`.
10. [`docs/README.md`](README.md) Quick start and Relay Node code blocks add `config=strawberry_config()` to the `strawberry.Schema(...)` call (with the import on the `from django_strawberry_framework import ...` line); the "Wrong order" anti-example mirrors the new shape.
11. [`GOAL.md`](../GOAL.md) astronomy showcase [`schema.py`](../GOAL.md#schemapy) adds `strawberry_config` to the imports and `config=strawberry_config()` to the showcase's terminal `strawberry.Schema(...)` call (anchored at [`GOAL.md #"strawberry.Schema(query=Query"`](../GOAL.md)).
12. [`TODAY.md`](../TODAY.md) "What to put in `examples/fakeshop/config/schema.py` today" block mirrors the [`docs/README.md`](README.md) Quick start update.
13. [`docs/TREE.md`](TREE.md) is NOT edited per [Doc updates](#doc-updates).
14. [`README.md`](../README.md) is NOT edited (no consumer-facing primitive renaming; the [`docs/README.md`](README.md) Quick start is the canonical schema-setup walkthrough).
15. [`KANBAN.md`](../KANBAN.md) records the card as `DONE-NNN-0.0.7` (moved from `WIP-ALPHA-020-0.0.7` in Slice 5) with a past-tense body summarizing the shipped scope per [Doc updates](#doc-updates); the `Definition of done` bullet 1 in the card body points at the structured spec filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming).
16. [`CHANGELOG.md`](../CHANGELOG.md) `[Unreleased]` carries the new `### Added` bullet (`strawberry_config` factory), the new `### Changed` bullet (breaking-change wording with before/after diff), the new `### Removed` bullet (suppression block); the `[0.0.6]` `### Notes` line at [`CHANGELOG.md #"Migration to a"`](../CHANGELOG.md) is removed.
17. The version bump is NOT in this card per [Decision 8](#decision-8--version-posture-cut-already-shipped-this-card-lands-under-unreleased); a future cut promotes `[Unreleased]` to `[0.0.8]` and bumps `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s version assertion atomically.
18. `__all__` widened by exactly one name (`strawberry_config`); no other public-export changes.
19. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`) — verified by CI's `fail_under = 100` gate, not by the worker locally (mirroring [`docs/SPECS/spec-019-multi_db-0_0_7.md`](SPECS/spec-019-multi_db-0_0_7.md) DoD item 9 / [`docs/SPECS/spec-018-export_schema-0_0_7.md`](SPECS/spec-018-export_schema-0_0_7.md) rev4 L4 clarifying clause). The worker does NOT run pytest locally; coverage and suite-passing assertion is CI's job after the PR opens.
20. Worker-local validation: `uv run ruff format .` passes and `uv run ruff check --fix .` passes. Per the no-pytest-after-edits rule at [`AGENTS.md #"Do not run pytest after edits"`](../AGENTS.md) ("Do not run pytest after edits; run only when explicitly asked"), the worker does NOT run pytest as part of completing this card. Pytest is invoked only by CI or by an explicit maintainer ask; the maintainer-invoked suite-passing command is `uv run pytest --no-cov` (with `--no-cov` opting out of `pytest.ini`'s auto-applied `--cov` so the worker doesn't see CI's `fail_under` gate locally).
