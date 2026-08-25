# DRY review: `django_strawberry_framework/forms/__init__.py`

Status: verified

## System trace

`django_strawberry_framework/forms/__init__.py` is the public export facade and package entry point for the framework's Django Form and ModelForm mutation write subsystem ([spec-038][spec-038]). It defines the subpackage's public API surface via `__all__`, re-exporting the declarative base classes for form-driven mutations defined in [`django_strawberry_framework/forms/sets.py`][forms-sets]:

1. **Subpackage Public Facade & Public Surface:**
   - [`DjangoFormMutation`][forms-sets]: The declarative base class for plain, non-model `django.forms.Form` mutations ([spec-038][spec-038] Decisions 1, 2). It binds a form class to a mutation payload returning `{ ok: bool, errors: list[FieldError] | None }`, handling form instantiation, validation (`form.is_valid()`), and custom execution hooks (`perform_mutate`).
   - [`DjangoModelFormMutation`][forms-sets]: The declarative base class for `django.forms.ModelForm` mutations ([spec-038][spec-038] Decisions 1, 2). It integrates form validation with Django model lifecycle handling (`form.save()`), model permissions, instance resolution, optimizer re-fetching, and typed GraphQL return payloads.
   - Public export definition: [`__all__`][forms-init] binds the explicit 2-tuple `("DjangoFormMutation", "DjangoModelFormMutation")`.

2. **Package-Root Export & Re-Export Wiring:**
   - Both [`DjangoFormMutation`][forms-sets] and [`DjangoModelFormMutation`][forms-sets] are re-exported at the package root [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] and included in the top-level `__all__` ([spec-038][spec-038] Decision 4, [`tests/base/test_init.py`][test-base-init]).
   - Consumers can import both classes from either `django_strawberry_framework` or `django_strawberry_framework.forms`.

3. **Subsystem Architecture & Encapsulation Boundary:**
   The `django_strawberry_framework.forms` subpackage follows a four-module structure mirroring the write-side architecture of `mutations/` and `rest_framework/` ([spec-038][spec-038] Decision 4):
   - [`forms/sets.py`][forms-sets]: Defines [`DjangoFormMutation`][forms-sets], [`DjangoModelFormMutation`][forms-sets], metaclasses, `Meta` options validation (`_validate_meta`), declaration registration (`_form_mutation_registry`), and the phase 2.5 finalizer bind seam (`bind_form_mutations()`).
   - [`forms/converter.py`][forms-converter]: Defines the `django.forms.Field` converter registry (`convert_form_field`) mapping Django form fields to Strawberry input types, along with decoding kind constants (`INPUT_KIND_SCALAR`, `INPUT_KIND_RELATION`, etc.).
   - [`forms/inputs.py`][forms-inputs]: Implements `<FormClass>Input` and `<FormClass>PartialInput` generation from `form.base_fields` / `form.declared_fields`, wrapping the shared `utils/inputs.py` materialization ledger under `INPUTS_MODULE_PATH` (`django_strawberry_framework.forms.inputs`).
   - [`forms/resolvers.py`][forms-resolvers]: Implements synchronous and asynchronous mutation resolution pipelines (`resolve_form_mutation_sync`, `resolve_form_mutation_async`, `resolve_model_form_mutation_sync`, `resolve_model_form_mutation_async`), error dictionary extraction (`form.errors` -> `FieldError`), instance saving, and optimizer pre-fetching.
   - **Deliberate non-export of compiler internals:** Low-level functions (such as `convert_form_field`, `build_form_input_class`, `bind_form_mutations`, and resolver functions) are deliberately excluded from `forms/__init__.py::__all__` per [spec-038][spec-038] Decision 4. Consumers interact solely with the declarative class bases, while the finalizer and schema builder import subsystem internals directly from their respective modules.

Connected behavior examined:
- [`django_strawberry_framework/forms/sets.py`][forms-sets]: Canonical implementation of `DjangoFormMutation` and `DjangoModelFormMutation`.
- [`django_strawberry_framework/forms/converter.py`][forms-converter]: Form field conversion registry.
- [`django_strawberry_framework/forms/inputs.py`][forms-inputs]: Form-derived input type factory and materialization ledger.
- [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers]: Sync and async execution pipelines for form mutations.
- [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]: Top-level framework facade re-exporting `DjangoFormMutation` and `DjangoModelFormMutation`.
- [`django_strawberry_framework/mutations/__init__.py`][mutations-init]: Sibling mutation subsystem facade for model-driven mutations (`DjangoMutation`, `DjangoMutationField`, `FieldError`, `DjangoModelPermission`).
- [`django_strawberry_framework/rest_framework/__init__.py`][rest-framework-init]: Sibling mutation subsystem facade for DRF serializer mutations (`SerializerMutation`).
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Phase 2.5 schema finalizer executing `bind_form_mutations()`.
- [`django_strawberry_framework/registry.py`][registry]: Global registry maintaining subsystem lifecycle clearing hooks for form input namespace and mutation registries.
- [`tests/base/test_init.py`][test-base-init]: Validates package-root and subpackage `__all__` lists and tests export identity.
- [`tests/forms/test_sets.py`][test-forms-sets], [`tests/forms/test_converter.py`][test-forms-converter], [`tests/forms/test_inputs.py`][test-forms-inputs], [`tests/forms/test_resolvers.py`][test-forms-resolvers]: Comprehensive test suite for form mutations.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/forms/__init__.py --include-constants`):
- Parsed 1 target file, 31 lines, 1 constant/module variable ([`__all__`][forms-init]), 2 imported class symbols ([`DjangoFormMutation`][forms-sets], [`DjangoModelFormMutation`][forms-sets]).
- Confirmed zero execution logic, zero helper functions, zero side effects on import, and zero internal mutable state in `forms/__init__.py`.
- Verified reverse references across the codebase, tests, and documentation.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   The framework provides three write mutation flavors: model mutations ([`mutations/__init__.py`][mutations-init]), form mutations ([`forms/__init__.py`][forms-init]), and DRF serializer mutations ([`rest_framework/__init__.py`][rest-framework-init]).
   - `forms/__init__.py` and `mutations/__init__.py` both use eager imports and static typed `__all__` tuples to expose their declarative mutation bases.
   - `forms/__init__.py` depends only on Django core (`django.forms`), a hard requirement of the repository, and therefore requires no soft-dependency guarding (unlike `rest_framework/__init__.py`, which gates imports behind `require_drf()`).
   - Query set-family facades ([`filters/__init__.py`][filters-init], [`orders/__init__.py`][orders-init]) define forward-reference helper functions (`filter_input_type`, `order_input_type`) for custom query resolvers. Mutations do not need forward-reference resolver helpers because mutation fields are synthesized during schema finalization via `bind_form_mutations()` and declarative metaclasses.
   - Shared write and input mechanics are single-sited: input materialization and deduplication are unified in [`django_strawberry_framework/utils/inputs.py`][utils-inputs], declaration registries are built via `make_declaration_registry` in [`django_strawberry_framework/forms/sets.py`][forms-sets], and subsystem clearing is registered in [`django_strawberry_framework/registry.py`][registry].
2. **Sync and async twins:**
   Zero duplication. As a pure export facade, `forms/__init__.py` contains no callable code or sync/async branching. Synchronous and asynchronous resolution twins (`resolve_form_mutation_sync` vs `resolve_form_mutation_async`) are implemented in [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers], sharing form validation, error extraction, and payload formatting logic.
3. **Derived rather than repeated knowledge:**
   `__all__` is derived directly from the canonical class definitions in `forms/sets.py`. The top-level package [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] re-exports `DjangoFormMutation` and `DjangoModelFormMutation` directly from `.forms`, preserving exact symbol identity without re-declaring types. The module docstring summarizes the four-module architecture without re-specifying underlying class configurations.
4. **Inverse and round-trip pairs:**
   Declaration and schema binding pairing: `DjangoFormMutation` and `DjangoModelFormMutation` declarations register with `_form_mutation_registry` upon class definition; phase 2.5 finalization ([`django_strawberry_framework/types/finalizer.py`][types-finalizer]) calls `bind_form_mutations()` to bind input types, arguments, and return types into Strawberry schema fields.
   Test lifecycle pairing: `registry.clear()` flushes all form-related ledgers (`clear_form_input_namespace`, `clear_form_mutation_registry`, `clear_form_shape_build_cache`) to ensure clean isolation between test runs.
5. **Contracts restated in another medium:**
   The forms subpackage public export contract is codified across:
   - Code: [`django_strawberry_framework/forms/__init__.py`][forms-init], [`django_strawberry_framework/forms/sets.py`][forms-sets], [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init], [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/registry.py`][registry];
   - Specifications: [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038] (Decisions 1, 2, 4, 6, 12);
   - Test suites: [`tests/base/test_init.py`][test-base-init], [`tests/forms/test_sets.py`][test-forms-sets], [`tests/forms/test_converter.py`][test-forms-converter], [`tests/forms/test_inputs.py`][test-forms-inputs], [`tests/forms/test_resolvers.py`][test-forms-resolvers], [`tests/mutations/test_sets.py`][test-mutations-sets];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Adding a new public form mutation base, e.g. `DjangoWizardFormMutation`):** Introduce a new form-driven mutation base class in `forms/sets.py` and expose it on the subpackage API.
  - *Sites that must move:* Exactly 1 site in this facade: [`django_strawberry_framework/forms/__init__.py`][forms-init] (import from `.sets` and append to `__all__`).
  - *Site count:* 1.
- **Posited change 2 (Renaming or deprecating an exported mutation base class):** Rename an existing mutation base class across the forms subpackage.
  - *Sites that must move:* Exactly 1 site in this facade: [`django_strawberry_framework/forms/__init__.py`][forms-init] (import statement and `__all__` tuple).
  - *Site count:* 1.
- **Posited change 3 (Modifying form field conversion or adding new field support):** Change the conversion mapping of a `forms.Field` type to Strawberry GraphQL types.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/forms/converter.py`][forms-converter] (`convert_form_field`). Zero edits in `forms/__init__.py`.
  - *Site count:* 1.
- **Posited change 4 (Altering form input shape materialization or naming conventions):** Change how `<FormClass>Input` names or fields are synthesized.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/forms/inputs.py`][forms-inputs] or [`django_strawberry_framework/utils/inputs.py`][utils-inputs]. Zero edits in `forms/__init__.py`.
  - *Site count:* 1.

### Rejected candidates

1. **Re-exporting `convert_form_field`, `build_form_input_class`, or resolvers from `forms/__init__.py`:**
   - Disproved per [spec-038][spec-038] Decision 4. Exposing lower-level conversion functions and resolver execution pipelines in `forms/__init__.py::__all__` would pollute the public consumer interface with internal compiler machinery. Consumers write declarative `DjangoFormMutation` and `DjangoModelFormMutation` classes; schema binding and resolvers are handled automatically during finalization.
2. **Merging form mutations directly into `mutations/__init__.py` without a dedicated `forms/` subpackage:**
   - Disproved per [spec-038][spec-038] Decision 4. Django `Form` and `ModelForm` handling involves distinct field discovery (`base_fields`), validation lifecycle (`is_valid()`), error formats (`form.errors`), and non-model mutation pipelines. Isolating form-specific logic under `django_strawberry_framework/forms/` provides clean subsystem modularity matching `mutations/` and `rest_framework/`.
3. **Using dynamic soft-dependency loading (`__getattr__`) in `forms/__init__.py`:**
   - Disproved. `django.forms` is an integral part of the core Django framework. Because Django is a required dependency of `django-strawberry-framework`, eager static imports in `forms/__init__.py` are standard and avoid unnecessary dynamic lookup overhead.

## Opportunities

None — `django_strawberry_framework/forms/__init__.py` is a clean, 31-line public export facade. It exports `DjangoFormMutation` and `DjangoModelFormMutation` with high precision, preserves strict encapsulation of subsystem compiler internals, and introduces zero duplicate logic or unowned invariants.

## Judgment

Zero-edit review. `django_strawberry_framework/forms/__init__.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/forms/__init__.py --review docs/dry/dry-file-forms____init__.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent verification conducted by Worker 2 for `django_strawberry_framework/forms/__init__.py`.

### Independent behavioral trace and boundary challenge

1. **Subpackage Facade Contract and Export Boundary:**
   - Re-exports [`DjangoFormMutation`][forms-sets] and [`DjangoModelFormMutation`][forms-sets] from `django_strawberry_framework/forms/sets.py`, accurately bounding the public API surface in [`__all__`][forms-init] as a 2-tuple.
   - Verified that internal compiler mechanics, converter functions ([`forms/converter.py`][forms-converter]), input materialization builders ([`forms/inputs.py`][forms-inputs]), mutation registration/binding hooks ([`forms/sets.py`][forms-sets]), and execution pipelines ([`forms/resolvers.py`][forms-resolvers]) are strictly encapsulated within their respective modules and deliberately excluded from `__all__` per [spec-038][spec-038] Decision 4.
   - Verified top-level re-export in [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] and export identity validation in [`tests/base/test_init.py`][test-base-init].

2. **Cross-Subsystem Flavor Symmetry and Absence of Forward-Ref Helpers:**
   - Compared against query-side set facades ([`filters/__init__.py`][filters-init], [`orders/__init__.py`][orders-init]) and sibling write-side mutation facades ([`mutations/__init__.py`][mutations-init], [`rest_framework/__init__.py`][rest-framework-init]).
   - Query set families require consumer forward-reference helpers (`filter_input_type`, `order_input_type`) for manual resolver annotations. In contrast, form mutations follow a declarative class-based paradigm where input generation and schema field synthesis occur automatically during phase 2.5 finalization via `bind_form_mutations()`. No forward-reference helpers or module-level reference ledgers are needed in `forms/__init__.py`.
   - Django forms are core dependencies, unlike DRF serializers which require soft-dependency gating (`require_drf()`); eager static imports in `forms/__init__.py` are appropriate.

3. **Duplication Probing Matrix and Single-Edit-Site Counts:**
   - Re-audited all 5 axes of the probing matrix and confirmed zero duplication across policy, execution paths, derived knowledge, inverse pairs, and medium representations.
   - Confirmed single-edit-site counts across all posited architectural changes (adding mutation bases, renaming exports, changing converter mappings, or updating input materialization).

4. **Verification Tooling & Test Suite Run:**
   - Ran `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/forms/__init__.py --review docs/dry/dry-file-forms____init__.md --include-constants` — 100% target coverage confirmed.
   - Ran forms test suite (`tests/forms/`) and init test suite (`tests/base/test_init.py`) — 232 tests passing.

Conclusion: Verified. The review is comprehensive, accurate, and zero edits are required on the target file.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[forms-converter]: ../../django_strawberry_framework/forms/converter.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-init]: ../../django_strawberry_framework/mutations/__init__.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[registry]: ../../django_strawberry_framework/registry.py
[rest-framework-init]: ../../django_strawberry_framework/rest_framework/__init__.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-forms-converter]: ../../tests/forms/test_converter.py
[test-forms-inputs]: ../../tests/forms/test_inputs.py
[test-forms-resolvers]: ../../tests/forms/test_resolvers.py
[test-forms-sets]: ../../tests/forms/test_sets.py
[test-mutations-sets]: ../../tests/mutations/test_sets.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
