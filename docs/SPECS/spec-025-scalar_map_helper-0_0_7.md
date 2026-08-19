# Spec: Warning-free scalar registration via `StrawberryConfig.scalar_map`

Target release: `0.0.7` (per the [`KANBAN.md`][kanban] card `DONE-025-0.0.7`; this card ships inside the joint `0.0.7` cut and its entries live under the `## [0.0.7] - 2026-05-27` heading in [`CHANGELOG.md`][changelog] — see [Decision 8](#decision-8--version-posture-this-card-ships-inside-the-007-cut)).
Status: shipped (`0.0.7`); implementation complete and committed. The spec is retained at this path as the durable record of the scalar-registration contract. Its deliberative layer — the revision history, every Decision's justification and rejected alternatives, the refused borrowings, and every claim it may no longer make — lives in [`spec-025-scalar_map_helper-0_0_7-rationale.md`][spec-025-rationale].
Owner: package maintainer.
Predecessors: [`docs/SPECS/spec-017-deferred_scalars-0_0_6.md`][spec-017] Decision 1 (the `BigInt` wire-format + `strawberry.scalar(NewType("BigInt", int), ...)` definition that introduced the suppressed deprecation), Decision 6 (the public-export contract for `BigInt`), and Risks (the explicit follow-up callout: "Migration to a `scalar_map`-based design is tracked as a follow-up and will be a real public-API change for consumers using `BigInt` directly"); [`docs/GLOSSARY.md`][glossary] entries [`BigInt scalar`][glossary-bigint-scalar] and [`Specialized scalar conversions`][glossary-specialized-scalar-conversions]; [`CHANGELOG.md`][changelog] `[0.0.6]` `### Notes` line (the literal "Migration to a `scalar_map`-based design is tracked as a follow-up" sentence this card pays down); [`KANBAN.md`][kanban] card `DONE-025-0.0.7`.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`BigInt scalar`][glossary-bigint-scalar] — the scalar this card relocates from the `strawberry.scalar(NewType, ...)` definition path to the `StrawberryConfig.scalar_map` registration path. The wire format (decimal string via `_serialize_bigint`), strict parser (`^(0|-?[1-9][0-9]*)$` regex via `_parse_bigint`), and target Django fields (`BigIntegerField`, `PositiveBigIntegerField`) are preserved verbatim — this card changes the registration mechanism, not the scalar's semantics.
- [`Specialized scalar conversions`][glossary-specialized-scalar-conversions] — the entry that pins `BigIntegerField → BigInt` and `PositiveBigIntegerField → BigInt` in [`django_strawberry_framework/types/converters.py`][converters]; the converter table is untouched by this card because it references the `BigInt` symbol by name and the symbol's import path is unchanged.
- [`Scalar field conversion`][glossary-scalar-field-conversion] — the broader scalar-mapping contract; cited so the reader sees `BigInt` as one entry in a family of package-defined scalars rather than a one-off.
- [`Upload scalar`][glossary-upload-scalar] — the package's other public scalar. It is Strawberry's own `NewType("Upload", bytes)`, already present in Strawberry's `DEFAULT_SCALAR_REGISTRY`, so it is re-exported with **no** `_PACKAGE_SCALAR_MAP` entry and resolves in a schema built with no package config at all. It is cited here as the deliberate contrast with the package-custom `BigInt`, which is absent from that registry and must be bound through the helper this card ships.
- [`DjangoType`][glossary-djangotype] — framing only; consumer-facing types that exercise `BigInt` through the converter table.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — framing only; cited because the consumer migration pattern this card establishes puts `config=strawberry_config()` and `extensions=[...]` side by side on the schema constructor, so it covers the relationship between schema-level config and schema-level extensions.
- [`ConfigurationError`][glossary-configurationerror] — not raised by this card. The conflict-resolution policy in [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions) uses `ValueError` because the collision is a consumer-input mistake at helper-call time, not a `DjangoType`-creation or finalization-time configuration error.
- [`finalize_django_types`][glossary-finalize-django-types] — cited because adding `config=strawberry_config()` to the schema constructor leaves the existing finalization-then-construction order intact.

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule at [`AGENTS.md #"Test placement:"`][agents] (package tests live under `tests/` with `__init__.py` shells in subdirectories like `tests/optimizer/`, example-project non-HTTP tests under `examples/fakeshop/tests/`, live HTTP tests under `examples/fakeshop/test_query/` and no `__init__.py` in either fakeshop test tree); the live-HTTP-priority rule at [`AGENTS.md #"any line reachable via a real GraphQL query against fakeshop"`][agents]; the no-pytest-after-edits rule at [`AGENTS.md #"No pytest after edits"`][agents]; the settings-keys rule at [`AGENTS.md #"Add a settings key only when the feature that needs it lands"`][agents]. **Note:** the CHANGELOG-edit-permission rule at [`AGENTS.md #"No CHANGELOG.md updates unless told"`][agents] prohibits [`CHANGELOG.md`][changelog] edits without explicit permission; [Slice 5](#implementation-plan) grants that permission for this card's `[0.0.7]` entries.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target.
- [`KANBAN.md`][kanban] — card-ID format; column movement at Slice 5; the card body's `docs/spec-scalar_map_helper.md` reference predates the structured `spec-<NNN>-<topic>-<0_0_X>.md` convention and gets rewritten in the same sweep per [Decision 1](#decision-1--spec-filename-and-canonical-naming).
- [`docs/TREE.md`][tree] — tests mirror source one-to-one. The helper lives in [`django_strawberry_framework/scalars.py`][scalars] per [Decision 2](#decision-2--helper-api-shape-and-module-location); the mirror partner is [`tests/test_scalars.py`][test-scalars], which already exists — no new file under `tests/`.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan). Five slices total.

- [ ] Slice 1: Helper module + `BigInt` redefinition
  - [ ] [`django_strawberry_framework/scalars.py`][scalars]: redefine `BigInt` as a bare `NewType("BigInt", int)` (the deprecation-prone wrapping in `strawberry.scalar(NewType, ...)` is removed); add a module-level `_BIGINT_SCALAR_DEFINITION: ScalarDefinition` built via the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload (the `cls is None and name is not None` branch at [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`][scalar] returns a `ScalarDefinition` directly without emitting `DeprecationWarning`); add a module-level `_PACKAGE_SCALAR_MAP: dict[object, ScalarDefinition]` mapping the `BigInt` `NewType` to the definition; add the public `strawberry_config(*, extra_scalar_map: Mapping[object, ScalarDefinition] | None = None, **config_kwargs: Any) -> StrawberryConfig` factory per [Decision 2](#decision-2--helper-api-shape-and-module-location) (keyword-only `extra_scalar_map`, tested with `is None` rather than for truthiness; the mapping's materialization guarded so the factory's `ValueError` cannot be displaced by the caller's exception; arbitrary `**config_kwargs` forwarded to `StrawberryConfig(...)`; `scalar_map=` rejected with `ValueError`) and the private `_safe_scalar_map_key_label` it labels collision keys with; remove the `with warnings.catch_warnings(): warnings.filterwarnings("ignore", message="Passing a class to strawberry.scalar", ...)` block at the bottom of the file per [Decision 6](#decision-6--remove-the-warningscatch_warnings-suppression-block).
    - Import and module surface inside `scalars.py`: ADD `from collections.abc import Mapping`, `from strawberry.schema.config import StrawberryConfig`, `from strawberry.types.scalar import ScalarDefinition`, and `_safe_arg_repr` / `_safe_type_name` from [`django_strawberry_framework/exceptions.py`][exceptions] (the safe-repr helpers the messages use). The module declares an `__all__`; this card adds `"BigInt"` and `"strawberry_config"` to it. KEEP `from typing import Any, NewType` (`Any` is already used by `_parse_bigint(value: Any)` / `_serialize_bigint(value: Any)` and now also annotates `**config_kwargs: Any` on the helper; `NewType` is the bare-redefinition path). REMOVE `import warnings` (no remaining use after the suppression block is dropped per [Decision 6](#decision-6--remove-the-warningscatch_warnings-suppression-block)).
  - [ ] [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]: add `strawberry_config` to the explicit re-export list alongside `BigInt` (the import line stays in the existing `from .scalars import BigInt` group, widened to carry the new name); append `"strawberry_config"` to `__all__` as the **last** element. Python's default `sorted()` for the tuple is ASCII case-sensitive (uppercase 66–90 → underscore 95 → lowercase 97–122), so `"strawberry_config"` (`s` = 115) sorts after every other lowercase initial the tuple carries; the tuple is sorted by that rule (verified at [`django_strawberry_framework/__init__.py #"__all__"`][django-strawberry-framework-init]) and the new element follows it. `BigInt` stays in `__all__` (consistent with the recommended "BigInt as a direct annotation" usage pattern from the card body).
- [ ] Slice 2: Tests
  - [ ] [`tests/test_scalars.py`][test-scalars] (extend): add **one** new test section "`strawberry_config()` factory" with **thirteen** new tests pinning the helper's contract — eight scalar-map tests (`test_strawberry_config_returns_strawberry_config_instance`, `test_strawberry_config_default_scalar_map_includes_bigint`, `test_strawberry_config_accepts_none_extra_scalar_map`, `test_strawberry_config_accepts_empty_extra_scalar_map`, `test_strawberry_config_merges_extra_scalar_map`, `test_strawberry_config_extra_scalar_map_does_not_mutate_caller_dict`, `test_strawberry_config_collision_with_package_scalar_raises_value_error`, `test_strawberry_config_independent_call_returns_independent_instance`) plus five `**config_kwargs` passthrough tests (`test_strawberry_config_forwards_auto_camel_case_kwarg`, `test_strawberry_config_forwards_relay_max_results_kwarg`, `test_strawberry_config_combines_extra_scalar_map_and_config_kwargs`, `test_strawberry_config_rejects_scalar_map_kwarg`, `test_strawberry_config_unknown_kwarg_raises_typeerror_from_upstream`) — see [Test plan](#test-plan) for the per-test contract. Tests use Strawberry's public `StrawberryConfig` / `ScalarDefinition` import surface (`from strawberry.schema.config import StrawberryConfig`; `from strawberry.types.scalar import ScalarDefinition`).
  - [ ] [`tests/test_scalars.py`][test-scalars] (extend): add **two** integration tests pinning that the migrated `BigInt` survives a Strawberry-schema round trip when registered through `strawberry_config()` — `test_bigint_serializes_int_via_strawberry_config_schema` (returns a Python `int` from a resolver annotated with `BigInt`; asserts the response JSON carries the decimal-string serialization), `test_bigint_parses_decimal_string_via_strawberry_config_schema` (accepts a decimal-string argument typed `BigInt`; asserts the resolver receives the parsed `int`). These two tests are the regression pins that catch a future `strawberry.scalar(name=..., ...)` overload signature drift; without them, a registration-path regression would surface only at consumer-build time.
  - [ ] [`tests/test_scalars.py`][test-scalars] (modify): the existing `test_package_import_does_not_emit_strawberry_deprecation_warning` regression at [`tests/test_scalars.py #"test_package_import_does_not_emit_strawberry_deprecation_warning"`][test-scalars] continues to pass UNCHANGED — the post-Slice-1 import path no longer triggers the deprecation at all (the `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload returns a `ScalarDefinition` directly without invoking the `wrap()` body at [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"def wrap(cls: _T) -> ScalarWrapper"`][scalar] that emits the `DeprecationWarning`); the test's `-W error::DeprecationWarning` subprocess shape pins the post-migration no-leak contract without modification.
  - [ ] [`tests/base/test_init.py`][test-init] (modify): update the `test_public_api_surface_is_pinned` assertion to append `"strawberry_config"` as the **last** element of the pinned `__all__` tuple, per [Decision 2](#decision-2--helper-api-shape-and-module-location) and the ASCII-sort convention noted in the Slice 1 bullet.
  - [ ] [`tests/types/test_converters.py`][test-converters] (modify): every `strawberry.Schema(query=Query)` call in the file **whose schema resolves to `BigInt`** is rewritten to `strawberry.Schema(query=Query, config=strawberry_config())`, and `strawberry_config` is added to the file's `from django_strawberry_framework import (...)` block. The sites live in the file's `BigInt scalar` section and are exactly the tests whose schemas expose a `BigIntegerField` / `PositiveBigIntegerField`-backed field or a `BigInt`-annotated resolver. **NOT migrated**, even though it sits under the same section banner: `test_big_auto_field_still_maps_to_int` — its schema asserts the terminal scalar is the upstream `Int`, and the `BigAutoField` resolution path never touches `BigInt`, so it needs no `config=`. The JSONField / Choice-enum / Relation / Boolean sections are likewise untouched. This bullet is the practical surface of the migration broadening pinned in [Decision 5](#decision-5--migration-posture-hard-break-in-alpha): a schema needs `config=strawberry_config()` whenever the [`Specialized scalar conversions`][glossary-specialized-scalar-conversions] converter table at [`django_strawberry_framework/types/converters.py`][converters] resolves one of its fields to `BigInt`, even when nothing in the schema imports or annotates `BigInt` directly. **The site list is not enumerated here**: which cases live in this package file and which live in live `/graphql/` coverage on the fakeshop scalars app is owned by the live-coverage rule at [`AGENTS.md #"any line reachable via a real GraphQL query against fakeshop"`][agents], not by this card — a package-tier `BigInt` case that becomes reachable over HTTP is promoted there, and the migration rule above applies wherever the case lives.
  - [ ] [`tests/test_scalars.py`][test-scalars] (modify docstring): the module docstring currently says schema-execution behavior for `BigInt` lives in [`tests/types/test_converters.py`][test-converters]; rewrite it to acknowledge that this file now ALSO carries two in-process `strawberry.Schema(...)` integration tests for the `strawberry_config()` registration round-trip. Suggested rewrite: keep the existing delegation sentence and append "Additionally, two `strawberry.Schema(query=..., config=strawberry_config())` integration tests pin the post-migration `BigInt` round trip end-to-end (`test_bigint_serializes_int_via_strawberry_config_schema`, `test_bigint_parses_decimal_string_via_strawberry_config_schema`)." so the test layout remains self-describing per the adversarial review's L2.
- [ ] Slice 3: Example-app migration
  - [ ] [`examples/fakeshop/config/schema.py`][schema]: add `config=strawberry_config()` to the project's schema-construction call (the file's sole one) and `strawberry_config` to the existing `from django_strawberry_framework import ...` line. No other change — the constructor class, the roots, and the `extensions=` entry are other cards' business per [Decision 9](#decision-9--example-app-migration-scope).
  - [ ] [`examples/fakeshop/apps/library/schema.py`][schema-library] and [`examples/fakeshop/apps/products/schema.py`][schema-products]: audit only — no edits. Neither constructs a schema, so neither has a `config=` to gain; they reach `BigInt` only indirectly, through the field-to-scalar converter table at [`django_strawberry_framework/types/converters.py #"BigInt,"`][converters]. A fakeshop app that later annotates `BigInt` directly (`id: BigInt`) still needs no consumer-code change, because the symbol's import path is unchanged — only the project-level schema construction carries the registration.
- [ ] Slice 4: Docs
  - [ ] [`docs/README.md`][readme]: add `config=strawberry_config()` to every schema-construction code block in the file, with `strawberry_config` added to each block's imports line — the [Quick start][readme-quick-start] block and both [Schema setup boundary][readme-schema-setup-boundary] examples (the "Wrong order" anti-example and the recommended one change identically, so the only contrast left between them is the placement of `finalize_django_types()` relative to schema construction, which is the pitfall the anti-example exists to illustrate). Blocks that declare types without constructing a schema — the [Relay Node][readme-relay-node] example among them — are not edited: there is no `config=` to add.
  - [ ] [`docs/GLOSSARY.md`][glossary]: update the [`BigInt scalar`][glossary-bigint-scalar] entry body to reflect the new construction pattern — replace the sentence "Strict serializer rejects `bool`, `float`, `str`, `Decimal`, and any non-`int` type with `TypeError`" with the same sentence preserved, AND add a new paragraph: "Consumers register `BigInt` via the [`strawberry_config`](#strawberry_config) factory on their `strawberry.Schema(...)` call: `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[lambda: _optimizer])`. Direct `BigInt` annotations (`category: BigInt`, `@strawberry.field def big_id(self) -> BigInt: ...`) continue to work unchanged at the schema-declaration site; the registration path changes, not the symbol." Add a new top-level glossary entry for `strawberry_config` between the [`Specialized scalar conversions`][glossary-specialized-scalar-conversions] entry and the [Strictness mode][glossary-strictness-mode] entry; new entry body per [Doc updates](#doc-updates). Update the [Public exports][glossary-public-exports] bulleted re-exports list to add `strawberry_config` after `finalize_django_types` (matching the `__all__` ordering — Python ASCII sort puts `strawberry_config` at the end of the lowercase block). Update the alphabetical [Index][glossary-index] table with a new row for `strawberry_config` in alphabetical position and a status of shipped (`0.0.7`), matching the form every other shipped row uses.
  - [ ] [`GOAL.md`][goal]: rewrite the [`schema.py`][goal-schemapy] example block (the astronomy showcase) — add `strawberry_config` to the imports list and `config=strawberry_config()` to the showcase's terminal `strawberry.Schema(...)` call. No other change to the showcase body; the per-stack diff blocks inside the [Migration shape][goal-migration-shape] section (`Coming from graphene-django` / `Coming from strawberry-graphql-django` / `Coming from DRF + django-filter`) are NOT edited because the blocks intentionally show minimal `Meta`-shape diffs and adding the helper would distract from the per-stack migration point. The GOAL `schema.py` is the one place where a consumer's "right shape" example lives end-to-end and should reflect the post-migration pattern.
  - [ ] [`TODAY.md`][today]: rewrite the [What to put in `config/schema.py` today][today-what-to-put-in-configschemapy-today] block to add `strawberry_config()` to the imports and the `strawberry.Schema(...)` call, mirroring the [`docs/README.md`][readme] Quick start update. No other change; the [What's in `products/schema.py` today][today-whats-in-productsschemapy-today] section already does not construct a project-level schema, so no edit is needed there.
  - [ ] [`docs/TREE.md`][tree]: no structural edit. The helper is added to the existing [`django_strawberry_framework/scalars.py`][scalars] module per [Decision 2](#decision-2--helper-api-shape-and-module-location), so the layout enumeration gains no row. The file is rendered by [`scripts/build_tree_md.py`][build-tree] from module docstrings — if the `scalars.py` docstring changes to name the factory, the render carries it; the generated text is never hand-edited.
  - [ ] [`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv`][spec-025-terms]: once the new `## strawberry_config` entry is in place inside [`docs/GLOSSARY.md`][glossary] (the bullet above), add a row `strawberry_config,strawberry_config,The factory function this card introduces; entry created in Slice 4.` to the CSV in alphabetical position. Then re-run [`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`][check-spec-glossary] and confirm it reports `OK: 17 terms`. `StrawberryConfig` (upstream Strawberry) stays out of the CSV — it is not a package glossary term.
- [x] Slice 5: KANBAN + CHANGELOG
  - [x] [`KANBAN.md`][kanban]: move the card to the Done column, keeping its `DONE-025-0.0.7` id (the Done column is maintained in completion order, so a later board renumber may move the number; the id in this spec is the one the card carries). The past-tense Done body summarizes the shipped scope; full wording pinned in [Doc updates](#doc-updates). The card body's `Definition of done` bullet 1 names the spec by its structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming). Update the `### In progress` summary paragraph (anchored at [`KANBAN.md #"### In progress"`][kanban]) to drop the card from the remaining-cards list.
  - [x] [`CHANGELOG.md`][changelog]: **append** to the shared `## [0.0.7] - 2026-05-27` section per [Decision 8](#decision-8--version-posture-this-card-ships-inside-the-007-cut) — one bullet under `### Added` (the `strawberry_config` factory), one under `### Changed` (the breaking registration move), one under `### Removed` (the suppression block). Every `0.0.7` card appends to that one section rather than opening a second `[0.0.7]` heading. Per the CHANGELOG-edit-permission rule at [`AGENTS.md #"No CHANGELOG.md updates unless told"`][agents], this Slice 5 bullet is the explicit `CHANGELOG.md` edit permission. Also remove the literal `[0.0.6]` `### Notes` line "The internal `BigInt` scalar definition uses `strawberry.scalar(NewType, ...)`, which Strawberry deprecates in favor of `StrawberryConfig.scalar_map`. The deprecation warning is suppressed at the definition site so the package import remains clean. Migration to a `scalar_map`-based design is tracked as a follow-up and will be a real public-API change for consumers using `BigInt` directly." at [`CHANGELOG.md`][changelog] — that `Notes` entry advertised the architectural debt this card pays down; with the migration shipped, the placeholder note has served its purpose and removing it keeps the `[0.0.6]` section accurate as a snapshot of what shipped (the `Notes` line is a forward-looking pointer, not a historical fact).
  - [x] Version bump: NOT in this card per [Decision 8](#decision-8--version-posture-this-card-ships-inside-the-007-cut). The bump that closes the joint `0.0.7` cut — [`pyproject.toml`][pyproject]'s `[project].version`, `django_strawberry_framework/__init__.py`'s `__version__`, and `tests/base/test_init.py`'s pinned version assertion, in one atomic commit — belongs to the last card in the bundle.

## Problem statement

`0.0.6` shipped `BigInt` as the package's first public scalar (per [`docs/SPECS/spec-017-deferred_scalars-0_0_6.md`][spec-017] Decision 1; the public-export contract is pinned in [`docs/SPECS/spec-017-deferred_scalars-0_0_6.md`][spec-017] Decision 6). Implementation chose the most-idiomatic-at-the-time Strawberry shape — `strawberry.scalar(NewType("BigInt", int), name="BigInt", serialize=_serialize_bigint, parse_value=_parse_bigint)` — but a later Strawberry release deprecated the class-direct-to-`scalar()` path: every call into `strawberry.scalar(<class-or-NewType>, ...)` now emits `DeprecationWarning("Passing a class to strawberry.scalar() is deprecated. Use StrawberryConfig.scalar_map instead for better type checking support. See: https://strawberry.rocks/docs/types/scalars")` from [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"def wrap(cls: _T) -> ScalarWrapper"`][scalar].

The `0.0.6` shipping fix was to suppress the deprecation at the definition site so consumers importing `django_strawberry_framework` see no warning — see the `with warnings.catch_warnings(): warnings.filterwarnings("ignore", message="Passing a class to strawberry.scalar", ...)` block at the bottom of [`django_strawberry_framework/scalars.py`][scalars]. The suppression is correct triage but it has two architectural costs that this card pays down:

1. **The `0.0.6` `CHANGELOG.md` `### Notes` line carries a literal "tracked as a follow-up" pointer** — every release that ships with the suppression in place is a release that ships with documented technical debt.
2. **Every later package-custom scalar would face the same choice — repeat the suppression hack or migrate to `StrawberryConfig.scalar_map`** — and each one shipped under the suppressed-deprecation pattern multiplies the migration surface. (Not every later scalar is package-custom: [`Upload`][glossary-upload-scalar] is one Strawberry's own `DEFAULT_SCALAR_REGISTRY` already carries, so it needs no registration at all. The cost being paid down here is real for the ones that do.)

The right design (pre-pinned by the [`KANBAN.md`][kanban] card body's "Recommended architectural direction" block) defines `BigInt` on Strawberry's recommended path (a bare `NewType` plus a `ScalarDefinition` produced via the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload at [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`][scalar]) and has consumers compose a package-provided `StrawberryConfig` into their `strawberry.Schema(...)`. The result: no suppression block; no `_warnings.catch_warnings()` pretext; a single registration point a package-custom scalar binds through without any change to the helper's API.

## Current state

The baseline this card starts from — the `0.0.6` surface the [Problem statement](#problem-statement) describes, enumerated so each [Slice checklist](#slice-checklist) item names the thing it replaces. Every bullet below is a statement about that starting surface, not about the shipped result.

- [`django_strawberry_framework/scalars.py`][scalars]: `BigInt` is defined via `strawberry.scalar(NewType("BigInt", int), name="BigInt", ...)` wrapped in a `with warnings.catch_warnings(): warnings.filterwarnings("ignore", message="Passing a class to strawberry.scalar", ...)` block. The strict parser (`_parse_bigint`) and strict serializer (`_serialize_bigint`) are pure functions with no Strawberry coupling.
- [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]: `BigInt` is re-exported via the `from .scalars import BigInt` line (anchored at [`django_strawberry_framework/__init__.py #"from .scalars import BigInt"`][django-strawberry-framework-init]); `__all__` (anchored at [`django_strawberry_framework/__init__.py #"__all__"`][django-strawberry-framework-init]) lists it.
- [`django_strawberry_framework/types/converters.py #"BigInt,"`][converters]: `models.BigIntegerField: BigInt` and `models.PositiveBigIntegerField: BigInt` are pinned in `SCALAR_MAP`. Consumer `DjangoType`s using these field types resolve to `BigInt` automatically through the converter table; no consumer import of `BigInt` is required for that path.
- [`tests/test_scalars.py`][test-scalars]: tests pinning the strict parser / serializer contract (`test_bigint_serializes_int_as_decimal_string`, `test_bigint_rejects_python_bool`, etc.) plus the public-export smoke (`test_bigint_is_importable_from_top_level`) plus the deprecation-suppression regression (`test_package_import_does_not_emit_strawberry_deprecation_warning` at [`tests/test_scalars.py #"test_package_import_does_not_emit_strawberry_deprecation_warning"`][test-scalars]). The deprecation regression test runs `python -W error::DeprecationWarning -c "import django_strawberry_framework"` in a subprocess and asserts the import does not raise.
- [`tests/base/test_init.py`][test-init]: `test_public_api_surface_is_pinned` (anchored at [`tests/base/test_init.py #"test_public_api_surface_is_pinned"`][test-init]) pins `__all__` as an exact-tuple assertion.
- [`examples/fakeshop/config/schema.py`][schema]: constructs the schema the project serves at `/graphql/` — its sole **non-test** schema-construction site — with no `config=` argument. No fakeshop schema imports `BigInt` directly at this point, so the migration reaches the example only through the converter table.
- [`docs/GLOSSARY.md`][glossary]: the [`BigInt scalar`][glossary-bigint-scalar] entry describes the `0.0.6` wire format / parser / serializer but does not document the registration path; the [Public exports][glossary-public-exports] list shows `BigInt` but no helper symbol.
- [`docs/README.md`][readme]: the [Quick start][readme-quick-start] section shows `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])`; the [Relay Node][readme-relay-node] example shows the same shape.
- [`GOAL.md`][goal]: the astronomy showcase [`schema.py`][goal-schemapy] block shows the same shape.
- [`TODAY.md`][today]: the [What to put in `config/schema.py` today][today-what-to-put-in-configschemapy-today] block shows the same shape.
- [`CHANGELOG.md`][changelog]: the `[0.0.6]` `### Notes` line quoted in [Slice 5](#slice-checklist) advertises the architectural debt this card pays down.
- [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023]: the sibling `0.0.7` spec, shipped before this card; its [Decision 9][spec-023-decision-9] is the "joint cut" reference the [Decision 8](#decision-8--version-posture-this-card-ships-inside-the-007-cut) here cites.

## Goals

1. Pay down the suppressed-deprecation debt by moving `BigInt` to Strawberry's recommended `StrawberryConfig.scalar_map` registration path.
2. Establish the one registration point any package-custom scalar binds through, so a later scalar needs no change to `strawberry_config(...)`.
3. Ship the consumer migration as a single-line change at `strawberry.Schema(...)` construction sites — `config=strawberry_config()` added once per schema, no annotation-site changes anywhere.
4. Remove the `warnings.catch_warnings()` block so the package's import surface is clean by construction, not by suppression.
5. Remove the `[0.0.6]` `### Notes` "tracked as a follow-up" line because the follow-up has shipped.

## Non-goals

- Composing Strawberry extensions through this helper. `extensions=` belongs on `strawberry.Schema(query=..., extensions=[...])`, NOT on `StrawberryConfig`. The card body explicitly calls this out and the helper signature deliberately omits an `extra_extensions=` parameter — see [Decision 2](#decision-2--helper-api-shape-and-module-location). If a future card reveals real demand for an extension-bundling helper, it ships as a separate symbol (e.g., `schema_kwargs(...)` returning a kwargs dict) rather than overloading `strawberry_config`.
- Auto-discovery of the package config. A hypothetical Django-settings-backed default like `STRAWBERRY_CONFIG_FACTORY = "django_strawberry_framework.scalars.strawberry_config"` that the package internals consult is deferred; consumers explicitly pass `config=strawberry_config()` per `strawberry.Schema(...)` call. Per the settings-keys rule at [`AGENTS.md #"Add a settings key only when the feature that needs it lands"`][agents], the discovery path is not added until a feature requires it.
- Shipping [`Upload`][glossary-upload-scalar] (or [`DjangoFileType`][glossary-djangofiletype] / [`DjangoImageType`][glossary-djangoimagetype]); that is `DONE-037-0.0.11`. What this card owes the later scalar is a registration point that needs no API change to accommodate it, and the requirement is met two ways: a package-**custom** scalar binds by gaining a `_PACKAGE_SCALAR_MAP` entry, and a scalar Strawberry's own `DEFAULT_SCALAR_REGISTRY` already carries — `Upload` is one — needs **no** entry and resolves in any schema, config or not. Either way `strawberry_config(...)` is untouched.
- A `dst.Schema(...)` wrapper around `strawberry.Schema`. Considered and rejected per [Decision 2](#decision-2--helper-api-shape-and-module-location); shadowing upstream symbols hides the composition.
- A static `SCALAR_MAP` constant the consumer manually splat-merges into their own `StrawberryConfig(scalar_map={...})`. Considered and rejected per [Decision 2](#decision-2--helper-api-shape-and-module-location); pushes `StrawberryConfig(...)` boilerplate onto every consumer.
- Mutating the converter table at [`django_strawberry_framework/types/converters.py`][converters]. The `models.BigIntegerField: BigInt` / `models.PositiveBigIntegerField: BigInt` mappings reference `BigInt` by name; the symbol's import path is unchanged, so the converter table needs no edit.
- Renaming `BigInt`. The symbol's GraphQL name (`BigInt`) and Python identifier (`BigInt`) are preserved verbatim.

## Borrowing posture

This card has no upstream precedent to borrow at the helper-API level — `strawberry-django` does not ship a `StrawberryConfig`-bundling helper; `graphene-django` predates Strawberry. The `StrawberryConfig.scalar_map` registration *mechanism* is the upstream pattern this card adopts, but the package-side factory wrapping it is new.

### From `strawberry-django` — no precedent to borrow

Local source path: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/`. Verified by `grep -rn "StrawberryConfig\|scalar_map" /Users/riordenweber/projects/strawberry-django-main/` — zero matches in the upstream's source. The upstream does not ship package-defined scalars (no `BigInt`, no `Upload` in the strawberry-django source tree), so it has no registration helper to model on. Consumers using `strawberry-django` who need a custom scalar register it themselves via Strawberry's documented path; the package does not bundle one.

### From `graphene-django` — no precedent to borrow

Local source path: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/`. `graphene-django` uses Graphene's `Scalar` subclass mechanism rather than Strawberry's `StrawberryConfig.scalar_map`. The migration target here is Strawberry's idiom; there is no graphene-side analogue to import.

### Explicitly do not borrow

The three shapes the package deliberately does not borrow from itself — a `dst.Schema(...)` wrapper pre-populating `config=`, a public `SCALAR_MAP` constant consumers spread into their own `StrawberryConfig`, and a module-level `STRAWBERRY_DEFAULT_CONFIG` instance — are recorded with the reason each was refused in [`spec-025-scalar_map_helper-0_0_7-rationale.md`][spec-025-rationale] [Borrowing posture][rationale-borrowing].

## User-facing API

The shipped consumer surface adds **one new symbol** — `strawberry_config(*, extra_scalar_map=None, **config_kwargs) -> StrawberryConfig`. The signature is keyword-only on `extra_scalar_map` (no positional form) and forwards every other keyword argument to the upstream [`StrawberryConfig(...)`][config] constructor unchanged. The symbol is re-exported from `django_strawberry_framework` and lives in [`django_strawberry_framework/scalars.py`][scalars] (per [Decision 2](#decision-2--helper-api-shape-and-module-location)).

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

_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)
```

The optimizer entry is a module-level singleton wrapped in a factory (the documented shape — Strawberry runs the callable per request and gets the same instance back, so the instance-bound plan cache survives, and a callable entry emits no deprecation warning). It is orthogonal to this card, which owns `config=` alone.

The returned `StrawberryConfig.scalar_map` carries one entry: `{BigInt: <BigInt ScalarDefinition>}`. Strawberry consults the map at schema-construction time to resolve `BigInt` annotations and assigned-`BigInt` resolvers anywhere in the schema; the consumer writes `id: BigInt` or `@strawberry.field def big_id(self) -> BigInt: ...` exactly as in `0.0.6` and earlier.

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

### Composing with custom `StrawberryConfig` options

Consumers who need to tune any of the other [`StrawberryConfig`][config] fields (`auto_camel_case`, `name_converter`, `default_resolver`, `relay_max_results`, `relay_use_legacy_global_id`, `disable_field_suggestions`, `info_class`, `enable_experimental_incremental_execution`, `batching_config`) pass those keyword arguments directly to `strawberry_config(...)` — the helper forwards them to the upstream constructor:

```python path=null start=null
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(auto_camel_case=False, relay_max_results=200),
    extensions=[lambda: _optimizer],
)
```

Combining `extra_scalar_map=` and `**config_kwargs` works the same way — the keyword-only `extra_scalar_map` selects the scalar-merge path; every other kwarg lands on `StrawberryConfig(...)` unchanged:

```python path=null start=null
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(
        extra_scalar_map={MyULID: _MY_ULID_DEF},
        relay_max_results=200,
    ),
)
```

The single field the helper does NOT forward is `scalar_map`: that field is owned by `strawberry_config(...)` and consumers route additional scalars through `extra_scalar_map=` instead. Passing `scalar_map=` directly raises `ValueError` (see [Error shapes](#error-shapes)) so the consumer cannot accidentally bypass the conflict-resolution policy from [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions).

### Error shapes

- `strawberry_config(extra_scalar_map={BigInt: <some other ScalarDefinition>})` → `ValueError("strawberry_config(extra_scalar_map=...) cannot redeclare package-defined scalars: BigInt. ...")`.
- `strawberry_config(scalar_map={...})` → `ValueError("strawberry_config() owns scalar_map; pass consumer scalars with extra_scalar_map=...")`. The `scalar_map` keyword is rejected even when the value is empty or `None` because the kwarg is structurally owned by the helper, not the value.
- `strawberry_config(extra_scalar_map=<a mapping that raises while being read>)` → `ValueError("strawberry_config(extra_scalar_map=...) must be materializable; got <safe repr>.")`, chained `from` whatever the mapping raised. Materializing the caller's mapping is the factory's first contact with consumer-controlled behavior, so the failure is converted into the factory's own promised exception instead of surfacing as the caller's arbitrary one — the `BaseException` catch is deliberate and covers a `keys()` / `__iter__` / `__eq__` / `__hash__` that raises anything at all.
- `strawberry_config(extra_scalar_map={"not a NewType or class": <ScalarDefinition>})` → no validation; Strawberry's own `StrawberryConfig(scalar_map=...)` consumer ([`strawberry.Schema(...)`](https://strawberry.rocks)) decides whether the key is usable. The factory does NOT pre-validate the shape of `extra_scalar_map` keys because Strawberry's documented contract for `scalar_map` accepts "any type" (per the `Mapping[object, ScalarDefinition]` type at [`.venv/lib/python3.14/site-packages/strawberry/schema/config.py #"scalar_map: Mapping[object, ScalarDefinition]"`][config]); the factory would over-validate by guessing what "any type" means in this context.
- `strawberry_config(unknown_kwarg=True)` → no helper-level validation; the kwarg lands on `StrawberryConfig(...)` and upstream raises its own `TypeError("unexpected keyword argument 'unknown_kwarg'")`. The helper does not pre-list Strawberry's supported kwargs because the supported set is owned by Strawberry and would drift with Strawberry releases.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec's canonical name is the structured **`spec-025-scalar_map_helper-0_0_7.md`**, NOT the `docs/spec-scalar_map_helper.md` the [`KANBAN.md`][kanban] card body's `Definition of done` bullet 1 originally named. This document is that file, currently at [`docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`][spec-025], with its companions in `docs/SPECS/appx/`.

Active-vs-archived path lifecycle (mirroring [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] Decision 1): the **filename** is canonical; the **directory** is not. A reference points at whichever path the file has when the reference is written — `docs/` while the spec is in flight, `docs/SPECS/` once an archive pass has moved it, with `-terms.csv` and `-rationale.md` companions under `docs/SPECS/appx/` — and the archive pass rewrites every reference in one sweep. Nothing in this spec's contract depends on the directory.

Rationale companion — this Decision's justification, its two rejected filename alternatives, and the claims it may no longer make: [Decision 1][rationale-d1].

### Decision 2 — Helper API shape and module location

The helper ships as a **factory function** named `strawberry_config` with signature `def strawberry_config(*, extra_scalar_map: Mapping[object, ScalarDefinition] | None = None, **config_kwargs: Any) -> StrawberryConfig`. The signature is keyword-only on `extra_scalar_map` (the leading `*,` rules out positional invocation) and accepts arbitrary `**config_kwargs` that the helper forwards to the upstream [`StrawberryConfig(...)`][config] constructor unchanged — with one exception: passing `scalar_map=` raises `ValueError` because that field is owned by the helper and consumer scalars go through `extra_scalar_map=` instead. The function lives in **[`django_strawberry_framework/scalars.py`][scalars]**, colocated with the `BigInt` definition it composes. The symbol is re-exported from `django_strawberry_framework` (i.e., available as `from django_strawberry_framework import strawberry_config`).

Rationale companion — this Decision's eight justification bullets and its seven rejected alternatives, including the retracted prediction about how `Upload` would be registered: [Decision 2][rationale-d2].

### Decision 3 — `BigInt` redefinition as bare `NewType` + `ScalarDefinition`

`BigInt` is redefined as a bare `NewType("BigInt", int)`. The Strawberry `ScalarDefinition` is built via the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload — the `cls is None and name is not None` branch at [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`][scalar] — which returns a `ScalarDefinition` directly without invoking the `wrap()` body that emits the `DeprecationWarning`.

Pinned shape (Slice 1):

```python path=null start=null
from typing import Any, NewType
from collections.abc import Mapping

import strawberry
from strawberry.schema.config import StrawberryConfig
from strawberry.types.scalar import ScalarDefinition

from .exceptions import _safe_arg_repr, _safe_type_name

# Wire format: decimal string in, decimal string out. Both bodies normalize
# through the base descriptors (int.__int__, str.__str__, int.__str__) so a
# hostile int / str subclass cannot alter what is accepted or emitted, and
# report rejected inputs through _safe_arg_repr rather than a consumer repr.
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


def strawberry_config(
    *,
    extra_scalar_map: Mapping[object, ScalarDefinition] | None = None,
    **config_kwargs: Any,
) -> StrawberryConfig:
    if "scalar_map" in config_kwargs:
        raise ValueError(
            "strawberry_config() owns scalar_map; pass consumer scalars with extra_scalar_map=..."
        )
    if extra_scalar_map is None:
        extra: dict[object, ScalarDefinition] = {}
    else:
        try:
            extra = dict(extra_scalar_map)
        except BaseException as exc:
            raise ValueError(
                "strawberry_config(extra_scalar_map=...) must be materializable; "
                f"got {_safe_arg_repr(extra_scalar_map)}.",
            ) from exc
    collisions = _PACKAGE_SCALAR_MAP.keys() & extra.keys()
    if collisions:
        raise ValueError(
            "strawberry_config(extra_scalar_map=...) cannot redeclare package-defined scalars: "
            f"{', '.join(sorted(_safe_scalar_map_key_label(k) for k in collisions))}. "
            "Define a Strawberry custom scalar of a different NewType / class to register under a separate key."
        )
    merged: dict[object, ScalarDefinition] = dict(_PACKAGE_SCALAR_MAP)
    merged.update(extra)
    return StrawberryConfig(scalar_map=merged, **config_kwargs)


def _safe_scalar_map_key_label(key: object) -> str:
    """Describe a collision key without trusting consumer-defined metadata."""
    try:
        name = getattr(key, "__name__", None)
    except BaseException:
        name = None
    return name if isinstance(name, str) else _safe_arg_repr(key)
```

Three properties of that body are contract, not incidental spelling:

- **Absent is distinguished from empty by an explicit `is None` test**, never by truthiness. `if extra_scalar_map` would call a consumer-supplied mapping's `__bool__`, so the branch that decides "no extra scalars were passed" would be decided by consumer code.
- **Materializing the caller's mapping is guarded**, and the guard raises the factory's own `ValueError` chained from whatever the mapping raised (see [Error shapes](#error-shapes)). A promised exception boundary that a caller's object can substitute its own exception for is not a boundary.
- **Collision keys are labelled through `_safe_scalar_map_key_label`**, which tolerates a `__name__` descriptor that raises and rejects a `__name__` that is not a `str`. A bare `getattr(k, "__name__", repr(k))` reads hostile metadata twice over: the `getattr` can raise, and `repr` is consumer code too.

The module declares an `__all__` naming its public surface; this card's contribution to it is `BigInt` and `strawberry_config`.

Rationale companion — this Decision's justification, its three rejected alternatives, and the record of every change this Decision has undergone: [Decision 3][rationale-d3].

### Decision 4 — Conflict resolution for `extra_scalar_map` collisions

When a consumer's `extra_scalar_map` contains a key already present in `_PACKAGE_SCALAR_MAP`, `strawberry_config(...)` raises `ValueError("strawberry_config(extra_scalar_map=...) cannot redeclare package-defined scalars: <names>. Define a Strawberry custom scalar of a different NewType / class to register under a separate key.")` — hard error.

`ValueError` is the factory's **only** rejection class, and it covers every way a consumer-supplied `extra_scalar_map` can be refused: the collision above, the structurally-owned `scalar_map=` kwarg, and a mapping that raises while being materialized. That last one is why the uniformity is a contract rather than a coincidence — the mapping is consumer code, so without the materialization guard the factory's rejection class would be whatever the caller's object chose to raise. [`ConfigurationError`][glossary-configurationerror] is deliberately not used: every one of these is a consumer-input mistake at helper-call time, not a `DjangoType`-creation or finalization-time configuration error. The full message set is enumerated in [Error shapes](#error-shapes).

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 4][rationale-d4].

### Decision 5 — Migration posture: hard break in alpha

Any consumer whose schema resolves to `BigInt` after the upgrade — whether through a direct `BigInt` annotation OR through a [`DjangoType`][glossary-djangotype] field backed by `BigIntegerField` / `PositiveBigIntegerField` resolved by the [`Specialized scalar conversions`][glossary-specialized-scalar-conversions] converter table at [`django_strawberry_framework/types/converters.py`][converters] — who doesn't add `config=strawberry_config()` to their `strawberry.Schema(...)` call will see Strawberry schema-construction fail with `Unexpected type '...BigInt'` (or a comparable Strawberry error) at the first schema-build attempt after the upgrade. No deprecation window; no shim that re-registers `BigInt` via the old `strawberry.scalar(NewType, ...)` path; the migration is a single-line consumer change. The migration surface is broader than "consumers who import or annotate `BigInt` directly" because the converter table resolves the field type to `BigInt` for any `DjangoType` backed by the targeted Django integer fields — those consumers must migrate too even if they never reference the `BigInt` symbol in their own code.

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 5][rationale-d5].

### Decision 6 — Remove the `warnings.catch_warnings()` suppression block

The `with warnings.catch_warnings(): warnings.filterwarnings("ignore", message="Passing a class to strawberry.scalar", category=DeprecationWarning)` block at the bottom of [`django_strawberry_framework/scalars.py`][scalars] is removed wholesale, along with the `import warnings` line if no other code in the file uses it (verified — `warnings` is imported only for this block today).

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 6][rationale-d6].

### Decision 7 — Test placement and shape

Tests for `strawberry_config(...)` and the migrated `BigInt` registration path live in the existing [`tests/test_scalars.py`][test-scalars] module — the mirror partner of [`django_strawberry_framework/scalars.py`][scalars] per the [`docs/TREE.md`][tree] mirror rule. No new test file.

This card contributes **fifteen** pytest items to that file: **thirteen** factory tests (eight scalar-map + five `**config_kwargs` passthrough) and **two** schema round-trip integration tests, each enumerated in the [Test plan](#test-plan). Single pytest item per test; no `pytest.mark.parametrize` fan-out, so the contribution matches pytest collection output unambiguously, mirroring [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] Slice 1's no-`parametrize` pin and [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] rev2 M1. The file's pre-existing parser / serializer pins are unchanged; the one edit outside it is the `__all__` assertion in [`tests/base/test_init.py`][test-init]. The file is shared with later scalar work, so its total item count is not this card's to pin — only the fifteen named items are.

**Defense-in-depth note (intentional duplication with `tests/types/test_converters.py`).** The `BigInt`-resolving schema-construction sites in [`tests/types/test_converters.py`][test-converters] also run through the `config=strawberry_config()` registration path, so a registration-layer regression surfaces in both files. The duplication is kept intentionally: `tests/test_scalars.py` is the scalar's mirror partner per [`docs/TREE.md`][tree] and pins the round trip independent of the converter table, so a future restructure of the converter table (e.g. moving the `BigIntegerField → BigInt` mapping into a per-app override surface) does not lose the integration coverage. The two tests cost very little (each is ~10 lines) and the defense-in-depth posture is the same one used by [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] for its `_db` preservation tests.

Rationale companion — this Decision's remaining justification and its three rejected alternatives, one of which a later card reversed: [Decision 7][rationale-d7]. The defense-in-depth note above stays in the spec because it governs what a future DRY pass may delete.

### Decision 8 — Version posture: this card ships inside the `0.0.7` cut

`DONE-025-0.0.7` is one card of a **joint `0.0.7` cut** — seven cards share the one release heading, as [`KANBAN.md`][kanban] records and as [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] [Decision 9][spec-023-decision-9] states for the same bundle. This card's `CHANGELOG.md` entries therefore **append to the shared `## [0.0.7] - 2026-05-27` section** rather than opening a heading of their own: one `### Added` bullet for the factory, one `### Changed` bullet for the breaking registration move, one `### Removed` bullet for the suppression block.

The version bump that closes the cut belongs to the last card to ship in it, NOT to this card. This card touches neither [`pyproject.toml`][pyproject]'s `[project].version`, nor `__version__` at [`django_strawberry_framework/__init__.py #"__version__"`][django-strawberry-framework-init], nor the pinned assertion at [`tests/base/test_init.py #"def test_version"`][test-init].

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 8][rationale-d8].

### Decision 9 — Example-app migration scope

The fakeshop example project is updated in **one place only**: [`examples/fakeshop/config/schema.py`][schema], the schema the project serves at `/graphql/`. That is the site this card's contract names — not a count of the project's schema-construction calls. Which *other* schemas anywhere must carry the registration is owned by [Decision 5](#decision-5--migration-posture-hard-break-in-alpha)'s rule, which applies wherever a `BigInt`-resolving schema is built, and by the code that builds it. This card's edit at the served schema is exactly two lines — `strawberry_config` joins the existing `from django_strawberry_framework import ...` line, and `config=strawberry_config()` joins the constructor call. Everything else about that call belongs to other cards: the constructor class, the query / mutation roots, and the shape of the `extensions=` entry are all outside this card's contract, and the migration is a `config=` addition regardless of what they are.

The per-app schemas at [`examples/fakeshop/apps/library/schema.py`][schema-library] and [`examples/fakeshop/apps/products/schema.py`][schema-products] need no edit — neither constructs a schema; each declares a `@strawberry.type class Query` only. The same holds for every app `schema.py` added later, for the same structural reason: an app `schema.py` contributes a `Query` root and leaves construction to whatever composes it.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 9][rationale-d9].

## Implementation plan

The slice ships as **five slices** aligned with the [Slice checklist](#slice-checklist). Each slice maps to one commit; squashing all five into a single PR is acceptable given the small surface (~120 lines total delta).

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — Helper module + `BigInt` redefinition | [`django_strawberry_framework/scalars.py`][scalars], [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] | 0 | `+30 / -25` (net +5 — replace suppression block with helper + dict; bare-`NewType` redefinition is a one-line swap) |
| 2 — Tests | [`tests/test_scalars.py`][test-scalars] (extend), [`tests/base/test_init.py`][test-init] (one-line edit), [`tests/types/test_converters.py`][test-converters] (BigInt-section schema migrations) | 15 (thirteen factory tests — eight scalar-map + five `**config_kwargs` passthrough — plus two integration tests in `tests/test_scalars.py`; the `test_public_api_surface_is_pinned` assertion in `tests/base/test_init.py` is modified, not new; the BigInt-section schema rewrites in `tests/types/test_converters.py` are modifications, not new tests) | `+200 / -15` |
| 3 — Example-app migration | [`examples/fakeshop/config/schema.py`][schema] | 0 | `+2 / -1` |
| 4 — Docs | [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`GOAL.md`][goal], [`TODAY.md`][today] | 0 | `+50 / -10` |
| 5 — KANBAN + CHANGELOG | [`KANBAN.md`][kanban], [`CHANGELOG.md`][changelog] | 0 | `+25 / -6` (the `-6` includes the removed `[0.0.6]` `### Notes` line plus minor reflow) |

Total expected delta: ~260 lines across five slices.

The five slices must be authored in order. Slice 2 depends on Slice 1 (the tests target the new helper and the migrated `BigInt` shape); Slice 3 depends on Slice 1 + Slice 2 (the example migration uses the helper, and the test suite is what proves it works); Slice 4 depends on Slice 3 (the docs reference the migrated example as the "what to type" canonical reference); Slice 5 depends on Slice 4 (the CHANGELOG entry summarizes the docs + example state).

## Edge cases and constraints

- **Strawberry version with the no-warning overload.** The `cls is None and name is not None` branch at [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`][scalar] exists across the whole range [`pyproject.toml`][pyproject] declares (`strawberry-graphql>=0.316.0`). If a consumer installs a Strawberry old enough to lack the overload — below the declared floor, so outside the supported range — the redefinition fails at package import; the failure mode is loud (`TypeError` at import), not silent. The declared constraint is the contract that ensures the overload exists; changing that constraint is out of scope here.
- **`BigInt` as a `NewType` is not isinstance-checkable.** `isinstance(x, BigInt)` raises `TypeError` because `NewType` is not a class at runtime. Consumer code that does `isinstance(value, BigInt)` would already fail today (this is not a regression introduced by the migration); the package does not document `BigInt` as isinstance-checkable, so no consumer contract is affected.
- **`StrawberryConfig.scalar_map` is a `Mapping`, not a `dict`.** The factory's return type is `StrawberryConfig(scalar_map=<a dict>)`, but the field type accepts any `Mapping`. The implementation builds a fresh `dict` per call so a downstream `StrawberryConfig.scalar_map.update(...)` (if Strawberry ever does that internally — currently it doesn't) doesn't mutate the consumer's `extra_scalar_map`.
- **Independent return value semantics.** Each `strawberry_config(...)` call returns a new `StrawberryConfig` instance with a new `scalar_map` dict. Mutations on the returned object (e.g., `config.scalar_map["X"] = ...`) do NOT leak to the next call's return value. Pinned by `test_strawberry_config_independent_call_returns_independent_instance` in [Test plan](#test-plan).
- **`extra_scalar_map={}` and `extra_scalar_map=None` produce the same `scalar_map`, but not by the same route.** Absence is decided by an explicit `is None` test; an empty mapping takes the materialization branch and yields an empty `dict`. The equivalence is an outcome, never a truthiness test — a mapping's `__bool__` is consumer code and must not decide which branch runs. Pinned by `test_strawberry_config_accepts_none_extra_scalar_map` and `test_strawberry_config_accepts_empty_extra_scalar_map`.
- **An `extra_scalar_map` that raises while being read is refused by the factory, not by the caller's exception.** `dict(extra_scalar_map)` runs consumer code (`keys()`, `__iter__`, `__hash__`, `__eq__`), so it is wrapped and re-raised as the factory's own `ValueError` chained from the original — see [Error shapes](#error-shapes). The catch is `BaseException` on purpose: a boundary that only holds for `Exception` subclasses is not the boundary the factory promises. Pinned by `test_strawberry_config_rejects_unmaterializable_extra_scalar_map`.
- **`extra_scalar_map` mutation post-call.** The factory copies the `extra_scalar_map` dict into the returned `StrawberryConfig` (because the helper builds a new `dict(_PACKAGE_SCALAR_MAP)` and `update(...)`s the extra map into it). A consumer's later mutation of their `extra_scalar_map` does NOT affect the returned `StrawberryConfig`. Pinned by `test_strawberry_config_extra_scalar_map_does_not_mutate_caller_dict`.
- **`**config_kwargs` passthrough semantics.** The helper forwards every kwarg in `**config_kwargs` to `StrawberryConfig(...)` verbatim. No translation, no defaults, no validation beyond the `scalar_map` rejection. The supported kwarg set is whatever Strawberry's `StrawberryConfig` accepts in the pinned version; consumer typos (`relay_max_resluts=200`) surface as the upstream's own `TypeError("unexpected keyword argument 'relay_max_resluts'")`. Pinned by `test_strawberry_config_forwards_auto_camel_case_kwarg`, `test_strawberry_config_forwards_relay_max_results_kwarg`, and `test_strawberry_config_combines_extra_scalar_map_and_config_kwargs`.
- **Underscore-prefixed `StrawberryConfig` kwargs pass through unchanged.** Strawberry's `StrawberryConfig` dataclass declares at least one underscore-prefixed field that is nevertheless a real `__init__` kwarg — e.g., `_unsafe_disable_same_type_validation: bool = False` (at [`.venv/lib/python3.14/site-packages/strawberry/schema/config.py #"_unsafe_disable_same_type_validation"`][config]). The helper does NOT special-case underscore-prefixed kwargs; `strawberry_config(_unsafe_disable_same_type_validation=True)` is forwarded unchanged, and the resulting `StrawberryConfig` carries the value. This is the documented Strawberry contract; the helper does not impose opinions on which upstream fields a consumer chooses to set.
- **`scalar_map=` kwarg is rejected even when empty.** `strawberry_config(scalar_map={})` and `strawberry_config(scalar_map=None)` both raise `ValueError`. The kwarg name is structurally owned by the helper; the rejection is independent of the value. Pinned by `test_strawberry_config_rejects_scalar_map_kwarg`.
- **Keyword-only invocation.** `strawberry_config({BigInt: alt_def})` (positional) raises `TypeError` because the signature begins with `*,`. Consumers must spell `extra_scalar_map=...`. This is a Python-level guarantee, not a helper-level check; no dedicated test is needed.
- **`strawberry.scalar(name=...)` overload — `parse_value` is not auto-defaulted.** On the no-warning `cls is None and name is not None` overload at [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`][scalar], omitting `parse_value=` produces a `ScalarDefinition.parse_value = None`; Strawberry will error at schema-execution time if the scalar is used in input position. The legacy `cls`-passing overload (the deprecated one this card retires) had a different default: `parse_value` would fall back to `cls`. The helper does NOT validate the shape of `ScalarDefinition`s the consumer passes through `extra_scalar_map=` (Strawberry owns that contract); the asymmetry only matters for consumers building their own `strawberry.scalar(...)` definitions on the new overload — they should pass `parse_value=` explicitly even when it's `int` / `str` / a trivial coercion.
- **Collision-error message stability.** The `ValueError` message names each colliding key through `_safe_scalar_map_key_label`, which returns the key's `__name__` when that attribute is present **and** is a `str` — the `NewType` and `class` cases — and otherwise falls back to `_safe_arg_repr`. Both halves of the fallback are load-bearing under Strawberry's `Mapping[object, ScalarDefinition]` contract, which permits any key: a key may have no `__name__` (a bare string or integer), may have a `__name__` **descriptor that raises**, or may have a `__name__` that is not a string. None of those may turn the collision rejection into a different error. The `NewType`-keyed format is pinned by `test_strawberry_config_collision_with_package_scalar_raises_value_error`; the hostile-metadata paths are pinned by `test_strawberry_config_collision_message_survives_hostile_key` and `test_scalar_collision_label_falls_back_when_class_name_metadata_is_unreadable`.
- **`from django_strawberry_framework import strawberry_config` ordering.** The `__init__.py` widens the existing `from .scalars import BigInt` line (anchored at [`django_strawberry_framework/__init__.py #"from .scalars import BigInt"`][django-strawberry-framework-init]) to `from .scalars import BigInt, strawberry_config`. The new symbol is exported from the same module's re-export line; no new import statement is added. `__all__` ordering: `"strawberry_config"` lands as the **last** element of the tuple because Python's default `sorted(...)` is ASCII case-sensitive (uppercase 66–90 → underscore 95 → lowercase 97–122) and `s` (115) sorts after every other lowercase initial the tuple carries. That sort rule is the contract, not any particular tuple contents: the tuple grows with every later public export, and the rule keeps placing `"strawberry_config"` last. The exact tuple is pinned by `test_public_api_surface_is_pinned` in [`tests/base/test_init.py`][test-init], which is where a reader should read it from.
- **`tests/test_scalars.py` item count is not a contract of this card.** This card adds the fifteen named items in the [Test plan](#test-plan) and modifies none of the file's pre-existing ones; the file is shared with later scalar work, so its total is a moving number and pinning it here would only create a claim that goes stale. `test_package_import_does_not_emit_strawberry_deprecation_warning` in particular continues to pass unmodified per [Decision 6](#decision-6--remove-the-warningscatch_warnings-suppression-block).
- **Coverage at 100%.** The factory body adds ~25 production lines (helper definition + `scalar_map`-rejection branch + absent-vs-empty branch + materialization guard + collision-raise branch + merge path + the `_safe_scalar_map_key_label` helper). All branches are covered by Slice 2 tests, the materialization guard by `test_strawberry_config_rejects_unmaterializable_extra_scalar_map` and the label fallbacks by `test_strawberry_config_collision_message_survives_hostile_key` / `test_scalar_collision_label_falls_back_when_class_name_metadata_is_unreadable`: default-path coverage by `test_strawberry_config_default_scalar_map_includes_bigint`, `None`/`{}` cases by `test_strawberry_config_accepts_none_extra_scalar_map` and `test_strawberry_config_accepts_empty_extra_scalar_map`, merge path by `test_strawberry_config_merges_extra_scalar_map`, collision-raise by `test_strawberry_config_collision_with_package_scalar_raises_value_error`, `scalar_map`-rejection by `test_strawberry_config_rejects_scalar_map_kwarg`, passthrough path by `test_strawberry_config_forwards_auto_camel_case_kwarg` / `test_strawberry_config_forwards_relay_max_results_kwarg` / `test_strawberry_config_combines_extra_scalar_map_and_config_kwargs`, unknown-kwarg behavior by `test_strawberry_config_unknown_kwarg_raises_typeerror_from_upstream`. No uncoverable branches; [`pyproject.toml`][pyproject] `[tool.coverage.report] fail_under = 100` continues to pass.

## Test plan

Tests live in [`tests/test_scalars.py`][test-scalars] (extended) per [Decision 7](#decision-7--test-placement-and-shape). Test-tree placement is mandatory; no `tests/test_config.py` is added.

### `tests/test_scalars.py` (extend) — thirteen factory tests + two integration tests

Package tests; system-under-test is `strawberry_config(...)` in [`django_strawberry_framework/scalars.py`][scalars] and the migrated `BigInt` registration shape. **Thirteen** factory tests (eight scalar-map tests + five `**config_kwargs` passthrough tests) + **two** integration tests = fifteen items this card adds to the existing file. Single pytest item per test, no `pytest.mark.parametrize` fan-out so the contribution matches pytest collection output unambiguously.

Three further items in the same file pin the factory's hardened boundaries and belong to the same contract even though they are not among the fifteen: `test_strawberry_config_rejects_unmaterializable_extra_scalar_map` (the materialization guard, [Error shapes](#error-shapes)), `test_strawberry_config_collision_message_survives_hostile_key` and `test_scalar_collision_label_falls_back_when_class_name_metadata_is_unreadable` (the `_safe_scalar_map_key_label` fallbacks, [Decision 3](#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition)). A reader auditing the factory's rejection paths needs all eighteen.

**Imports** (added to the existing import block at the top of [`tests/test_scalars.py`][test-scalars]):

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

#### `**config_kwargs` passthrough tests

These five tests pin the [Decision 2](#decision-2--helper-api-shape-and-module-location) passthrough contract: every keyword argument other than `extra_scalar_map=` is forwarded to upstream `StrawberryConfig(...)` verbatim, and `scalar_map=` is rejected with `ValueError`.

- `test_strawberry_config_forwards_auto_camel_case_kwarg` — calls `strawberry_config(auto_camel_case=False)`; asserts `result.name_converter.auto_camel_case is False`. Also calls `strawberry_config()` (default) and asserts `result.name_converter.auto_camel_case is True` so the test pins both the default and the override. The assertion target is `result.name_converter.auto_camel_case` (not `result.auto_camel_case`) because `auto_camel_case` is declared as a dataclass `InitVar` on `StrawberryConfig`; `StrawberryConfig.__post_init__` applies the value to `name_converter.auto_camel_case` and `cfg.auto_camel_case` itself remains `None`. Pins the passthrough contract for the most-commonly-tuned upstream field.
- `test_strawberry_config_forwards_relay_max_results_kwarg` — calls `strawberry_config(relay_max_results=200)`; asserts `result.relay_max_results == 200`. Pins the passthrough contract for a second, structurally different upstream field (integer, not bool) so the test catches kwarg-typo / single-field bugs that the `auto_camel_case` test alone could miss.
- `test_strawberry_config_combines_extra_scalar_map_and_config_kwargs` — declares `CustomScalar` and `custom_def` as in the merge test; calls `strawberry_config(extra_scalar_map={CustomScalar: custom_def}, relay_max_results=200)`; asserts `result.relay_max_results == 200` AND `BigInt in result.scalar_map` AND `CustomScalar in result.scalar_map`. Pins that both composition paths cooperate on a single call.
- `test_strawberry_config_rejects_scalar_map_kwarg` — calls `strawberry_config(scalar_map={})` inside `pytest.raises(ValueError) as excinfo`; asserts the message contains `"scalar_map"` AND `"extra_scalar_map"`. Also calls `strawberry_config(scalar_map=None)` in a second `pytest.raises(ValueError)` to pin that the rejection is structural (kwarg-name-based), not value-based. Optionally adds a third call using a locally-declared `alt_def = strawberry.scalar(name="AltBigInt", serialize=str, parse_value=int)` and `strawberry_config(scalar_map={BigInt: alt_def})` to pin that a populated dict is also rejected — using only public / locally-declared values keeps the test from depending on the private `_BIGINT_SCALAR_DEFINITION`. Pins [Error shapes](#error-shapes).
- `test_strawberry_config_unknown_kwarg_raises_typeerror_from_upstream` — calls `strawberry_config(this_kwarg_does_not_exist_in_strawberry=True)` inside `pytest.raises(TypeError)`; asserts the exception is raised. Does NOT assert on the exception message (the message comes from upstream `StrawberryConfig.__init__` and would couple the test to Strawberry's error wording). Pins that the helper does NOT swallow unknown kwargs and lets upstream's own error path surface.

#### Integration tests

These two tests build a minimal Strawberry schema that uses `BigInt` and exercise the registration path end-to-end via `schema.execute_sync(...)`. They pin the post-migration round trip so a future regression at the registration layer is caught at the test tier.

- `test_bigint_serializes_int_via_strawberry_config_schema` — declares `@strawberry.type class Q: @strawberry.field def big(self) -> BigInt: return 9_223_372_036_854_775_807` (`int64_max`); constructs `schema = strawberry.Schema(query=Q, config=strawberry_config())`; runs `result = schema.execute_sync("{ big }")`; asserts `result.errors is None` AND `result.data == {"big": "9223372036854775807"}` (decimal string, not int). Pins the wire-format survival contract through the migrated registration path.
- `test_bigint_parses_decimal_string_via_strawberry_config_schema` — declares `@strawberry.type class Q: @strawberry.field def echo(self, value: BigInt) -> BigInt: return value`; constructs `schema = strawberry.Schema(query=Q, config=strawberry_config())`; runs `result = schema.execute_sync('{ echo(value: "9223372036854775807") }')`; asserts `result.errors is None` AND `result.data == {"echo": "9223372036854775807"}`. Pins the parser path through the migrated registration.

### Existing tests — one one-line modification, no other edits

The `test_public_api_surface_is_pinned` assertion in [`tests/base/test_init.py`][test-init] (anchored at [`tests/base/test_init.py #"test_public_api_surface_is_pinned"`][test-init]) is modified to append `"strawberry_config"` as the **last** element of the pinned `__all__` tuple, matching the Python ASCII sort order the tuple follows. Slice 2 commits this edit alongside the new factory tests.

The existing `test_package_import_does_not_emit_strawberry_deprecation_warning` test at [`tests/test_scalars.py #"test_package_import_does_not_emit_strawberry_deprecation_warning"`][test-scalars] is NOT modified — its `python -W error::DeprecationWarning -c "import django_strawberry_framework"` subprocess check still passes because the new registration path no longer triggers the deprecation at all (per [Decision 6](#decision-6--remove-the-warningscatch_warnings-suppression-block)).

Every other test in [`tests/test_scalars.py`][test-scalars] — the strict parser and strict serializer pins, the public-export smoke, the deprecation regression — is unchanged.

## Doc updates

- [`docs/GLOSSARY.md`][glossary]
  - **[Public exports][glossary-public-exports] list update:** add `strawberry_config` to the bulleted re-exports list after `finalize_django_types` (matching the `__all__` ordering — Python's ASCII case-sensitive sort puts `strawberry_config` at the end of the lowercase block).
  - **[Index][glossary-index] table update:** add a new row for `strawberry_config` in alphabetical position with the status shipped (`0.0.7`), matching the `shipped (X.Y.Z)` form every other shipped entry in the table uses.
  - **New entry: `## strawberry_config`** — between [`Specialized scalar conversions`][glossary-specialized-scalar-conversions] and [Strictness mode][glossary-strictness-mode] alphabetically. Body:

    > **Status:** shipped (`0.0.7`).
    >
    > Factory returning a [`StrawberryConfig`](https://strawberry.rocks) pre-populated with the package's `scalar_map` — the registration path consumers use to bind package-defined scalars (today: [`BigInt`](#bigint-scalar)) into their `strawberry.Schema(...)` call.
    >
    > ```python
    > from django_strawberry_framework import strawberry_config
    >
    > _optimizer = DjangoOptimizerExtension()
    > schema = strawberry.Schema(
    >     query=Query,
    >     config=strawberry_config(),
    >     extensions=[lambda: _optimizer],
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
    > Consumers tuning non-scalar `StrawberryConfig` fields (`auto_camel_case`, `relay_max_results`, `name_converter`, etc.) pass those keyword arguments directly — the helper forwards every kwarg other than `extra_scalar_map=` to upstream `StrawberryConfig(...)`:
    >
    > ```python
    > schema = strawberry.Schema(
    >     query=Query,
    >     config=strawberry_config(auto_camel_case=False, relay_max_results=200),
    > )
    > ```
    >
    > The keyword-only `extra_scalar_map=` and the `**config_kwargs` passthrough compose: `strawberry_config(extra_scalar_map={MyULID: my_ulid_definition}, relay_max_results=200)` is supported. The single field the helper refuses to forward is `scalar_map=` (ownership goes through `extra_scalar_map=`); passing `scalar_map=` raises `ValueError`. Collision with a package-defined scalar in `extra_scalar_map` also raises `ValueError`; register the consumer scalar under a different `NewType` / class to keep both. Each call returns a fresh `StrawberryConfig` instance with a fresh `scalar_map` dict; mutations on the returned object do not leak across calls.
    >
    > **See also:** [`BigInt scalar`](#bigint-scalar) · [`Upload scalar`](#upload-scalar) · [`Specialized scalar conversions`](#specialized-scalar-conversions).
  - **[`BigInt scalar`][glossary-bigint-scalar] entry update**: append after the strict-serializer sentence:

    > "Consumers register `BigInt` via the [`strawberry_config`](#strawberry_config) factory on their `strawberry.Schema(...)` call: `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[lambda: _optimizer])` (the optimizer is a module-level singleton wrapped in a factory — see [`DjangoOptimizerExtension`](#djangooptimizerextension)). Direct `BigInt` annotations (`category: BigInt`, `@strawberry.field def big_id(self) -> BigInt: ...`) continue to work unchanged at the schema-declaration site; the registration path changes, not the symbol. The migration applies to any schema that resolves to `BigInt` — including [`DjangoType`](#djangotype) schemas whose fields are backed by `BigIntegerField` or `PositiveBigIntegerField` (resolved to `BigInt` by the [`Specialized scalar conversions`](#specialized-scalar-conversions) converter table) even when the consumer never imports or annotates `BigInt` directly."

- [`docs/README.md`][readme]
  - Rewrite the [Quick start][readme-quick-start] code block to add `strawberry_config` to the import line and `config=strawberry_config()` to the `strawberry.Schema(...)` call.
  - Rewrite every other schema-construction block the same way, including both examples in the [Schema setup boundary][readme-schema-setup-boundary] section: the "Wrong order" anti-example changes identically to the recommended one, so the only remaining contrast between them is the placement of `finalize_django_types()` — the pitfall the anti-example exists to show.
  - A block that declares types without constructing a schema — the [Relay Node][readme-relay-node] example among them — needs no edit; there is no `config=` to add.
  - No change to the surrounding prose; the migration is purely a code-block update.

- [`GOAL.md`][goal]
  - Rewrite the astronomy [`schema.py`][goal-schemapy] example block — add `strawberry_config` to the imports list and `config=strawberry_config()` to the showcase's terminal `strawberry.Schema(...)` call. No other change.
  - The per-stack diff blocks inside the [Migration shape][goal-migration-shape] section (`Coming from graphene-django` / `Coming from strawberry-graphql-django` / `Coming from DRF + django-filter`) are NOT edited — those blocks intentionally show minimal `Meta`-shape diffs and adding a `config=` line would distract from the per-stack migration point. The astronomy showcase (which IS edited) is the one place a consumer sees the "right shape" end-to-end.

- [`TODAY.md`][today]
  - Rewrite the [What to put in `config/schema.py` today][today-what-to-put-in-configschemapy-today] block — add `strawberry_config` to the imports and `config=strawberry_config()` to the `strawberry.Schema(...)` call, mirroring the [`docs/README.md`][readme] Quick start update.
  - No other change; the [What's in `products/schema.py` today][today-whats-in-productsschemapy-today] section does not construct a project-level schema, so no edit is needed there.

- [`docs/TREE.md`][tree]: no structural edit. Per [Decision 2](#decision-2--helper-api-shape-and-module-location) the helper lives in the existing [`django_strawberry_framework/scalars.py`][scalars], so the layout enumeration gains no row. `docs/TREE.md` is rendered by [`scripts/build_tree_md.py`][build-tree] from module docstrings, so the `scalars.py` description tracks whatever that module's docstring says and is never hand-edited here.

- [`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv`][spec-025-terms]: once the [`## strawberry_config`][glossary-strawberry-config] glossary entry exists, add a row `strawberry_config,strawberry_config,The factory function this card introduces; entry created in Slice 4.` to the CSV in alphabetical position. Then re-run [`scripts/check_spec_glossary.py`][check-spec-glossary] and confirm it reports `OK: 17 terms`. `StrawberryConfig` (upstream Strawberry) is NOT added — the CSV holds project-specific terms only.

- [`KANBAN.md`][kanban] (Slice 5)
  - Move the card to the Done column, keeping its `DONE-025-0.0.7` id (the Done column is maintained in completion order, so the number is the board's to assign; this spec pins the body, not the number). Past-tense Done body:

    > "Pinned the package-defined scalar registration path: [`BigInt`][glossary-bigint-scalar] is redefined as a bare `NewType("BigInt", int)` and registered via [`StrawberryConfig.scalar_map`](https://strawberry.rocks) through a new public [`strawberry_config(*, extra_scalar_map=None, **config_kwargs) -> StrawberryConfig`][glossary-strawberry-config] factory exported from `django_strawberry_framework`. The factory is keyword-only on `extra_scalar_map=` and forwards every other kwarg to upstream `StrawberryConfig(...)`, so consumers compose package scalars and custom `StrawberryConfig` options (`auto_camel_case=False`, `relay_max_results=200`, etc.) in one call; passing `scalar_map=` directly raises `ValueError`. Consumers add `config=strawberry_config()` to their `strawberry.Schema(...)` call once; direct `BigInt` annotations work unchanged. The `warnings.catch_warnings()` suppression block in `django_strawberry_framework/scalars.py` is removed because the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload at `.venv/lib/python3.14/site-packages/strawberry/types/scalar.py` returns a `ScalarDefinition` without triggering the `DeprecationWarning`. Tests in `tests/test_scalars.py` cover the factory contract (thirteen tests — eight scalar-map + five `**config_kwargs` passthrough) and the round-trip wire format through a `strawberry.Schema(config=strawberry_config())` (two integration tests); `tests/base/test_init.py`'s `__all__` assertion adds `strawberry_config`; the `BigInt`-resolving schemas in `tests/types/test_converters.py` migrate to `config=strawberry_config()`. `examples/fakeshop/config/schema.py` migrates to the new pattern; `docs/README.md`, `docs/GLOSSARY.md`, `GOAL.md`, and `TODAY.md` schema-construction examples migrate too. Breaking change in alpha (per `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` Decision 6 and the `PositiveBigIntegerField` precedent in `0.0.6`): any schema that resolves to `BigInt` — direct annotations OR converter-backed `BigIntegerField` / `PositiveBigIntegerField` `DjangoType` fields — that doesn't add `config=strawberry_config()` sees Strawberry schema-construction fail with `Unexpected type ...BigInt`. Spec: `spec-025-scalar_map_helper-0_0_7.md`. The version bump that closes the joint `0.0.7` cut is NOT in this card per Decision 8."
  - The card body's `Definition of done` bullet 1 names the spec by its structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), at whatever path the file currently occupies.
  - Update the `### In progress` summary paragraph (anchored at [`KANBAN.md #"### In progress"`][kanban]) to drop the card from the remaining-cards list.

- [`CHANGELOG.md`][changelog] (Slice 5)
  - **Append** to the `## [0.0.7] - 2026-05-27` section's `### Added` subsection (adding the subsection if the section does not yet carry one, placed before `### Changed` per "Keep a Changelog" convention):

    > "`strawberry_config` — factory function (`django_strawberry_framework/scalars.py`) returning a `strawberry.schema.config.StrawberryConfig` pre-populated with the package's `scalar_map`. Consumers compose package-defined scalars into their schema via `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])`. Signature is `strawberry_config(*, extra_scalar_map=None, **config_kwargs)`: keyword-only `extra_scalar_map=` merges consumer-defined scalars (collisions with package defaults raise `ValueError`); every other kwarg is forwarded verbatim to upstream `StrawberryConfig(...)`, so consumers tune `auto_camel_case`, `relay_max_results`, etc. in the same call. Passing `scalar_map=` directly raises `ValueError`. New public export from `django_strawberry_framework`; `__all__` widened. See [`strawberry_config`][glossary-strawberry-config]."
  - **Append** to the same section's `### Changed` subsection:

    > "**Breaking change**: `BigInt` registration moved from `strawberry.scalar(NewType("BigInt", int), name="BigInt", ...)` to the `StrawberryConfig.scalar_map` path. Any schema that resolves to `BigInt` — whether through a direct `BigInt` annotation (`category: BigInt`, `@strawberry.field def x(self) -> BigInt: ...`) OR through a [`DjangoType`][glossary-djangotype] field backed by `BigIntegerField` / `PositiveBigIntegerField` (resolved by the [`Specialized scalar conversions`][glossary-specialized-scalar-conversions] converter table) — must add `config=strawberry_config()` to its `strawberry.Schema(...)` call; Strawberry schema construction will fail with `Unexpected type ...BigInt` without it. The migration applies even to consumers who never import or annotate `BigInt` directly, because the converter table resolves the field type to `BigInt` for them. Matches the `PositiveBigIntegerField → BigInt` precedent in `0.0.6`. Single-line migration:
    >
    > ```diff
    > - schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    > + from django_strawberry_framework import strawberry_config
    > + schema = strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])
    > ```
    >
    > The wire format, parser, serializer, and direct-annotation usage of `BigInt` are unchanged."
  - **Append** to the same section's `### Removed` subsection (adding the subsection if absent, placed after `### Fixed`):

    > "Internal `warnings.catch_warnings()` suppression block in `django_strawberry_framework/scalars.py` that silenced Strawberry's `Passing a class to strawberry.scalar() is deprecated` `DeprecationWarning`. No longer needed — the migrated registration path uses Strawberry's no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload."
  - **Remove** the `[0.0.6]` `### Notes` line at [`CHANGELOG.md`][changelog] (the literal sentence "The internal `BigInt` scalar definition uses `strawberry.scalar(NewType, ...)`, which Strawberry deprecates in favor of `StrawberryConfig.scalar_map`. The deprecation warning is suppressed at the definition site so the package import remains clean. Migration to a `scalar_map`-based design is tracked as a follow-up and will be a real public-API change for consumers using `BigInt` directly."). The `Notes` line advertised the architectural debt this card pays down; with the migration shipped, removing it keeps the `[0.0.6]` section a clean snapshot of what shipped (the `Notes` line was a forward-looking pointer, not a historical fact).
  - The version bump is NOT in this card per [Decision 8](#decision-8--version-posture-this-card-ships-inside-the-007-cut); the last card in the joint `0.0.7` cut bumps [`pyproject.toml`][pyproject], `__version__`, and `tests/base/test_init.py`'s version assertion in one atomic commit.
  - The CHANGELOG-edit-permission rule at [`AGENTS.md #"No CHANGELOG.md updates unless told"`][agents] — this Slice 5 bullet is the explicit instruction.

## Risks and open questions

Each item names a live constraint the shipped contract depends on. The preferred-answer / fallback deliberation each item carried — including two contingencies that are now dead — moved to [`spec-025-scalar_map_helper-0_0_7-rationale.md`][spec-025-rationale] [Deliberation moved from the risks section][rationale-risks].

- **The card shares its `[0.0.7]` heading with six sibling cards.** Its three CHANGELOG bullets append to the one shared `## [0.0.7] - 2026-05-27` section per [Decision 8](#decision-8--version-posture-this-card-ships-inside-the-007-cut); a second `[0.0.7]` heading would split the cut.
- **The spec's canonical name is the structured one.** The `KANBAN.md` card body's original `docs/spec-scalar_map_helper.md` reference predates the `spec-<NNN>-<topic>-<0_0_X>.md` convention; per [Decision 1](#decision-1--spec-filename-and-canonical-naming) the canonical name is the structured filename, at whatever path the file currently occupies.
- **Strawberry's no-warning overload signature stability.** [`strawberry.scalar(name=..., serialize=..., parse_value=...)`](https://strawberry.rocks) returning a `ScalarDefinition` is the documented and recommended path.
- **`isinstance(value, BigInt)` is not supported by `NewType`.** Pre-migration, `BigInt = strawberry.scalar(NewType, ...)` returned a `ScalarWrapper`-shaped object; post-migration, `BigInt` is a bare `NewType` that doesn't support `isinstance` checks.
- **`extra_scalar_map` collisions with later package-defined scalars.** A key becomes collision-prone only when it enters `_PACKAGE_SCALAR_MAP`, and only a scalar the package must *register* ever does: a scalar Strawberry's own `DEFAULT_SCALAR_REGISTRY` already carries needs no entry and can never collide. `Upload` is that second kind, so it added no entry and the map still holds exactly `{BigInt: ...}`. Any genuinely package-custom scalar added later does grow the map, and a consumer who had registered their own definition under that same key would then hit the [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions) hard error — which is the intended loud failure, and is why the map's contents are a documented part of the helper's contract rather than an implementation detail.
- **Strawberry version pin compatibility.** The declared constraint is `"strawberry-graphql>=0.316.0"` at [`pyproject.toml #"strawberry-graphql>="`][pyproject], and that constraint — not any one resolved version — is the contract that guarantees the `cls is None and name is not None` overload exists. The overload predates the floor by a wide margin, so the whole supported range carries it; the reading at [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`][scalar] confirms the top of the range. A future floor raise cannot lose the overload; only an upstream removal could, and that would break the package import loudly.
- **The registration path is exercised over a real request, not only in-process.** Slice 3 migrates the construction call for the schema fakeshop serves at `/graphql/`; the fakeshop models carry `BigIntegerField` / `PositiveBigIntegerField` columns, so a live `/graphql/` query resolves `BigInt` through `config=strawberry_config()` end to end. That live tier, not the in-process schema build, is where a registration regression surfaces first.
- **Suppression-removal regression detection.** The existing `test_package_import_does_not_emit_strawberry_deprecation_warning` test at [`tests/test_scalars.py #"test_package_import_does_not_emit_strawberry_deprecation_warning"`][test-scalars] uses a `-W error::DeprecationWarning` subprocess.

## Out of scope (explicitly tracked elsewhere)

- Composing Strawberry extensions through this helper. `extensions=` belongs on `strawberry.Schema(..., extensions=[...])`, not on `StrawberryConfig`. The card body explicitly excludes this; no follow-up card exists.
- Auto-discovery of the package config via a Django settings key (e.g., `STRAWBERRY_CONFIG_FACTORY = "django_strawberry_framework.scalars.strawberry_config"`). Per the settings-keys rule at [`AGENTS.md #"Add a settings key only when the feature that needs it lands"`][agents], settings keys land with the feature that needs them; no current feature needs auto-discovery.
- Shipping [`Upload`][glossary-upload-scalar]: `DONE-037-0.0.11`. It needs no `_PACKAGE_SCALAR_MAP` entry (Strawberry's `DEFAULT_SCALAR_REGISTRY` already carries it) and no change to the helper this card ships.
- A `dst.Schema(...)` wrapper around `strawberry.Schema`. Excluded by [Decision 2](#decision-2--helper-api-shape-and-module-location); no follow-up card.
- A static `SCALAR_MAP` constant exposed as a public re-export. Excluded by [Decision 2](#decision-2--helper-api-shape-and-module-location); the consumer composition story goes through the factory.
- Modifying the converter table at [`django_strawberry_framework/types/converters.py`][converters]. The `BigIntegerField → BigInt` / `PositiveBigIntegerField → BigInt` entries reference `BigInt` by name; the symbol's import path is unchanged.
- Renaming or aliasing `BigInt`. Out of scope; no follow-up card.
- Multi-database cooperation: [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] — independent shipped sibling.
- AppConfig and Trac #37064 hardening: [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021] and `DONE-024-0.0.7` — independent shipped siblings.
- `DjangoListField`: [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] — independent shipped sibling.
- Schema export management command: [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] — independent shipped sibling.
- [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]: planned for `0.0.9` — unrelated subsystem despite the overlapping word "connection."
- [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] / [`AggregateSet`][glossary-aggregateset] / [`FieldSet`][glossary-fieldset] and the Layer-3 sidecar subsystems: future cards under [`KANBAN.md`][kanban]'s Layer-3 backlog; independent of this card.

## Definition of done

The card is complete when all of the following are true:

1. [`docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`][spec-025] (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion [`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv`][spec-025-terms] anchoring every project-specific term used in the spec body to the matching [`docs/GLOSSARY.md`][glossary] heading (per [`docs/SPECS/NEXT.md`][next] Step 7).
2. [`django_strawberry_framework/scalars.py`][scalars] defines `BigInt = NewType("BigInt", int)` as a bare `NewType`, builds `_BIGINT_SCALAR_DEFINITION: ScalarDefinition` via `strawberry.scalar(name="BigInt", serialize=_serialize_bigint, parse_value=_parse_bigint)`, exposes `_PACKAGE_SCALAR_MAP: dict[object, ScalarDefinition] = {BigInt: _BIGINT_SCALAR_DEFINITION}`, and exposes `strawberry_config(*, extra_scalar_map: Mapping[object, ScalarDefinition] | None = None, **config_kwargs: Any) -> StrawberryConfig` per [Decision 2](#decision-2--helper-api-shape-and-module-location) and [Decision 3](#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition). The signature is keyword-only on `extra_scalar_map` (leading `*,`); `**config_kwargs` is forwarded verbatim to `StrawberryConfig(...)` except for `scalar_map=` which is rejected with `ValueError("strawberry_config() owns scalar_map; pass consumer scalars with extra_scalar_map=...")`. An explicit `is None` test — never a truthiness test — separates an absent `extra_scalar_map` from an empty one, and materializing a supplied mapping is guarded so the factory's `ValueError` cannot be displaced by the caller's exception (per [Error shapes](#error-shapes)). The `with warnings.catch_warnings(): warnings.filterwarnings("ignore", message="Passing a class to strawberry.scalar", ...)` block is removed; `import warnings` is removed if no other code uses it (per [Decision 6](#decision-6--remove-the-warningscatch_warnings-suppression-block)). `_parse_bigint` and `_serialize_bigint` keep the `0.0.6` **wire format** — decimal string in, decimal string out, same accept-sets — which is the part the predecessor contract pins; their bodies are free to harden against hostile `int` / `str` subclasses and unreadable metadata.
3. [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] widens the existing `from .scalars import BigInt` line to re-export `strawberry_config` alongside `BigInt`, and `__all__` gains `"strawberry_config"` as the **last** element of the tuple, matching the Python ASCII-sort convention the tuple follows.
4. [`tests/test_scalars.py`][test-scalars] is extended with the **8 scalar-map factory tests** listed in the [Test plan](#test-plan): `test_strawberry_config_returns_strawberry_config_instance`, `test_strawberry_config_default_scalar_map_includes_bigint`, `test_strawberry_config_accepts_none_extra_scalar_map`, `test_strawberry_config_accepts_empty_extra_scalar_map`, `test_strawberry_config_merges_extra_scalar_map`, `test_strawberry_config_extra_scalar_map_does_not_mutate_caller_dict`, `test_strawberry_config_collision_with_package_scalar_raises_value_error`, `test_strawberry_config_independent_call_returns_independent_instance`; AND the **5 `**config_kwargs` passthrough tests**: `test_strawberry_config_forwards_auto_camel_case_kwarg`, `test_strawberry_config_forwards_relay_max_results_kwarg`, `test_strawberry_config_combines_extra_scalar_map_and_config_kwargs`, `test_strawberry_config_rejects_scalar_map_kwarg`, `test_strawberry_config_unknown_kwarg_raises_typeerror_from_upstream`; AND the **2 integration tests**: `test_bigint_serializes_int_via_strawberry_config_schema`, `test_bigint_parses_decimal_string_via_strawberry_config_schema`. No `pytest.mark.parametrize` fan-out (single pytest item per test); fifteen pytest items contributed to the file.
5. [`tests/test_scalars.py`][test-scalars] `test_package_import_does_not_emit_strawberry_deprecation_warning` is UNCHANGED and continues to pass (the migrated registration path no longer triggers the deprecation at all per [Decision 6](#decision-6--remove-the-warningscatch_warnings-suppression-block)).
6. [`tests/base/test_init.py`][test-init] `test_public_api_surface_is_pinned` carries `"strawberry_config"` as the **last** element of the pinned `__all__` tuple, matching the Python ASCII-sort convention.
6a. [`tests/types/test_converters.py`][test-converters] is migrated: every `strawberry.Schema(query=Query)` call site in the file whose schema resolves to `BigInt` is rewritten to `strawberry.Schema(query=Query, config=strawberry_config())`, and `strawberry_config` joins the file's `from django_strawberry_framework import (...)` block. NOT migrated: `test_big_auto_field_still_maps_to_int` (under the same section banner but resolving to upstream `Int`, never `BigInt`) and every schema in the later sections (JSONField / Choice-enum / Relation / Boolean). The set of `BigInt` cases that live in this package file rather than in live `/graphql/` coverage is owned by the live-coverage rule, not by this card; the migration rule applies wherever a case lives.
6b. [`tests/test_scalars.py`][test-scalars] module docstring is updated to acknowledge that this file now ALSO carries the two `strawberry.Schema(query=..., config=strawberry_config())` integration tests added in Slice 2 (the delegation-to-`tests/types/test_converters.py` sentence is preserved, the new role is appended).
7. [`examples/fakeshop/config/schema.py`][schema] is rewritten per [Decision 9](#decision-9--example-app-migration-scope): `strawberry_config` is added to the existing `from django_strawberry_framework import ...` line and `config=strawberry_config()` is added to the project's schema-construction call. Nothing else about that call is this card's — not the constructor class, not the roots, not the `extensions=` entry.
8. The per-app schemas — [`examples/fakeshop/apps/library/schema.py`][schema-library], [`examples/fakeshop/apps/products/schema.py`][schema-products], and every app `schema.py` added since — are NOT modified: none constructs a schema, so none has a `config=` to gain.
9. [`docs/GLOSSARY.md`][glossary]: the [`BigInt scalar`][glossary-bigint-scalar] entry body carries the new construction-pattern paragraph per [Doc updates](#doc-updates); a new `## strawberry_config` entry exists alphabetically between [`Specialized scalar conversions`][glossary-specialized-scalar-conversions] and [Strictness mode][glossary-strictness-mode] with the body pinned in [Doc updates](#doc-updates); the `Public exports` list and the alphabetical `Index` table carry `strawberry_config`.
9a. [`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv`][spec-025-terms] carries a `strawberry_config,strawberry_config,...` row (added in the same Slice 4 commit that creates the GLOSSARY entry); running [`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`][check-spec-glossary] reports `OK: 17 terms`.
10. Every schema-construction code block in [`docs/README.md`][readme] carries `config=strawberry_config()`, with `strawberry_config` on its `from django_strawberry_framework import ...` line — the [Quick start][readme-quick-start] block and both [Schema setup boundary][readme-schema-setup-boundary] examples, the "Wrong order" anti-example included, so the contrast between them stays the finalize-order pitfall alone. A block that constructs no schema needs no edit.
11. [`GOAL.md`][goal] astronomy showcase [`schema.py`][goal-schemapy] adds `strawberry_config` to the imports and `config=strawberry_config()` to the showcase's terminal `strawberry.Schema(...)` call.
12. [`TODAY.md`][today]'s [What to put in `config/schema.py` today][today-what-to-put-in-configschemapy-today] block mirrors the [`docs/README.md`][readme] Quick start update.
13. This card adds no module under `django_strawberry_framework/` and no file under `tests/` (the helper lands in the existing [`django_strawberry_framework/scalars.py`][scalars]), so it owes [`docs/TREE.md`][tree] no structural edit. `docs/TREE.md` is script-rendered from module docstrings, so any change to the `scalars.py` line follows from the docstring, never from a hand edit.
14. This card edits no consumer-facing primitive name, so it owes the root [`README.md`][readme-repo] no walkthrough change — [`docs/README.md`][readme]'s Quick start is the canonical schema-setup walkthrough. (What the root README says about the `0.0.7` release line is the release notes' business, not this card's.)
15. [`KANBAN.md`][kanban] records the card in the Done column with a past-tense body summarizing the shipped scope per [Doc updates](#doc-updates), and the card body names the spec by its structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming). The card's number is the board's to assign — Done cards are kept in completion order — so this spec pins the body, not the number.
16. [`CHANGELOG.md`][changelog]'s `## [0.0.7] - 2026-05-27` section carries this card's `### Added` bullet (the `strawberry_config` factory), its `### Changed` bullet (breaking-change wording with the before/after diff), and its `### Removed` bullet (the suppression block), appended alongside the sibling cards' bullets in the same shared subsections; the `[0.0.6]` `### Notes` line at [`CHANGELOG.md`][changelog] is removed.
17. The version bump is NOT in this card per [Decision 8](#decision-8--version-posture-this-card-ships-inside-the-007-cut); the last card in the joint `0.0.7` cut bumps [`pyproject.toml`][pyproject], `__version__`, and `tests/base/test_init.py`'s version assertion atomically.
18. This card widens `__all__` by exactly one name (`strawberry_config`) and changes no other public export.
19. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`) — verified by CI's `fail_under = 100` gate, not by the worker locally (mirroring [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] DoD item 9 / [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] rev4 L4 clarifying clause). The worker does NOT run pytest locally; coverage and suite-passing assertion is CI's job after the PR opens.
20. Worker-local validation: `uv run ruff format .` passes and `uv run ruff check --fix .` passes. Per the no-pytest-after-edits rule at [`AGENTS.md #"No pytest after edits"`][agents] ("No pytest after edits; run only when explicitly asked (then `uv run pytest`)"), the worker does NOT run pytest as part of completing this card. Pytest is invoked only by CI or by an explicit maintainer ask; the maintainer-invoked suite-passing command is `uv run pytest --no-cov` (with `--no-cov` opting out of `pytest.ini`'s auto-applied `--cov` so the worker doesn't see CI's `fail_under` gate locally).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[goal-migration-shape]: ../../GOAL.md#migration-shape
[goal-schemapy]: ../../GOAL.md#schemapy
[kanban]: ../../KANBAN.md
[pyproject]: ../../pyproject.toml
[readme-repo]: ../../README.md
[today]: ../../TODAY.md
[today-what-to-put-in-configschemapy-today]: ../../TODAY.md#what-to-put-in-configschemapy-today
[today-whats-in-productsschemapy-today]: ../../TODAY.md#whats-in-productsschemapy-today

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[glossary-aggregateset]: ../GLOSSARY.md#aggregateset
[glossary-bigint-scalar]: ../GLOSSARY.md#bigint-scalar
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: ../GLOSSARY.md#connection-aware-optimizer-planning
[glossary-djangofiletype]: ../GLOSSARY.md#djangofiletype
[glossary-djangoimagetype]: ../GLOSSARY.md#djangoimagetype
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-fieldset]: ../GLOSSARY.md#fieldset
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-index]: ../GLOSSARY.md#index
[glossary-orderset]: ../GLOSSARY.md#orderset
[glossary-public-exports]: ../GLOSSARY.md#public-exports
[glossary-scalar-field-conversion]: ../GLOSSARY.md#scalar-field-conversion
[glossary-specialized-scalar-conversions]: ../GLOSSARY.md#specialized-scalar-conversions
[glossary-strawberry-config]: ../GLOSSARY.md#strawberry_config
[glossary-strictness-mode]: ../GLOSSARY.md#strictness-mode
[glossary-upload-scalar]: ../GLOSSARY.md#upload-scalar
[readme]: ../README.md
[readme-quick-start]: ../README.md#quick-start
[readme-relay-node]: ../README.md#relay-node
[readme-schema-setup-boundary]: ../README.md#schema-setup-boundary
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[next]: NEXT.md
[rationale-borrowing]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#borrowing-posture--explicitly-do-not-borrow
[rationale-d1]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-d2]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-2--helper-api-shape-and-module-location
[rationale-d3]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition
[rationale-d4]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-4--conflict-resolution-for-extra_scalar_map-collisions
[rationale-d5]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-5--migration-posture-hard-break-in-alpha
[rationale-d6]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-6--remove-the-warningscatch_warnings-suppression-block
[rationale-d7]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-7--test-placement-and-shape
[rationale-d8]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-8--version-posture-this-card-ships-inside-the-007-cut
[rationale-d9]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-9--example-app-migration-scope
[rationale-risks]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#deliberation-moved-from-the-risks-section
[spec-017]: spec-017-deferred_scalars-0_0_6.md
[spec-020]: spec-020-list_field-0_0_7.md
[spec-021]: spec-021-apps-0_0_7.md
[spec-022]: spec-022-export_schema-0_0_7.md
[spec-023]: spec-023-multi_db-0_0_7.md
[spec-023-decision-9]: spec-023-multi_db-0_0_7.md#decision-9--joint-007-cut
[spec-025]: spec-025-scalar_map_helper-0_0_7.md
[spec-025-rationale]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md
[spec-025-terms]: appx/spec-025-scalar_map_helper-0_0_7-terms.csv

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[converters]: ../../django_strawberry_framework/types/converters.py
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[scalars]: ../../django_strawberry_framework/scalars.py

<!-- tests/ -->
[test-converters]: ../../tests/types/test_converters.py
[test-init]: ../../tests/base/test_init.py
[test-scalars]: ../../tests/test_scalars.py

<!-- examples/ -->
[schema]: ../../examples/fakeshop/config/schema.py
[schema-library]: ../../examples/fakeshop/apps/library/schema.py
[schema-products]: ../../examples/fakeshop/apps/products/schema.py

<!-- scripts/ -->
[build-tree]: ../../scripts/build_tree_md.py
[check-spec-glossary]: ../../scripts/check_spec_glossary.py

<!-- .venv/ -->
[config]: ../../.venv/lib/python3.14/site-packages/strawberry/schema/config.py
[scalar]: ../../.venv/lib/python3.14/site-packages/strawberry/types/scalar.py

<!-- External -->
