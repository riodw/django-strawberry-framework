# DRY review: `django_strawberry_framework/mutations/__init__.py`

Status: verified

## System trace

`django_strawberry_framework/mutations/__init__.py` is the public export facade and package entry point for the framework's model-driven mutation write subsystem ([spec-036][spec-036]). It defines the subpackage's public API surface via `__all__`, re-exporting the four foundational symbols required for declarative GraphQL mutations:

1. **Subpackage Public Facade & Public Surface:**
   - [`DjangoMutation`][mutations-sets]: The declarative base class for model-driven create, update, and delete mutations ([spec-036][spec-036] Decision 2). Configured via an inner `class Meta` (`model`, `operation`, `fields`, `exclude`, `permission_classes`, `extra_kwargs`, etc.), it unifies schema generation, input type discovery, transaction management, validation, permission checking, and payload shaping.
   - [`DjangoMutationField`][mutations-fields]: The write-side field factory ([spec-036][spec-036] Decisions 5, 7, 8). Assigned to class attributes on an `@strawberry.type class Mutation`, it synthesizes root mutation fields with forward-referenced lazy return payloads, Relay GlobalID input argument typing, completion-spanning atomicity context markers, and runtime `in_async_context()` execution dispatch.
   - [`FieldError`][mutations-inputs]: The structured GraphQL error envelope ([spec-036][spec-036] Decision 6), standardizing validation and execution errors into `{ field: str, message: str, code: str }` payloads. Reused uniformly across all framework mutation flavors (model mutations, form mutations, serializer mutations, and session authentication).
   - [`DjangoModelPermission`][mutations-permissions]: The DRF-shaped write authorization class ([spec-036][spec-036] Decision 15). Maps mutation operations (`create -> add`, `update -> change`, `delete -> delete`) to Django model permissions, validating `info.context.request.user.has_perm` synchronously in the mutation pipeline and denying unauthenticated/anonymous callers by default.
   - Public export definition: [`__all__`][mutations-init] binds the explicit 4-tuple `("DjangoModelPermission", "DjangoMutation", "DjangoMutationField", "FieldError")`.

2. **Package-Root Export & Re-Export Wiring:**
   - All four symbols are re-exported at the package root [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] and included in the top-level `__all__` ([spec-036][spec-036] Decision 4, [`tests/base/test_init.py`][test-base-init]).
   - Consumers can import all four symbols directly from `django_strawberry_framework` or from `django_strawberry_framework.mutations`.

3. **Subsystem Architecture & Encapsulation Boundary:**
   The `django_strawberry_framework.mutations` subpackage follows a five-module layout ([spec-036][spec-036] Decision 4):
   - [`mutations/sets.py`][mutations-sets]: Defines [`DjangoMutation`][mutations-sets], metaclasses, `Meta` validation (`_validate_mutation_meta`), declaration registration (`_mutation_registry`), and the phase 2.5 finalizer bind seam (`bind_mutations()`).
   - [`mutations/inputs.py`][mutations-inputs]: Generates `<Model>Input` and `<Model>PartialInput` type classes from Django model fields, defines the [`FieldError`][mutations-inputs] envelope, and constructs the `<Name>Payload` return wrapper.
   - [`mutations/permissions.py`][mutations-permissions]: Implements [`DjangoModelPermission`][mutations-permissions], `_OPERATION_PERMISSION_ACTION` mapping, `DenyAll` (safe default for model-less plain forms), and `run_permission_classes` / `authorize_or_raise`.
   - [`mutations/resolvers.py`][mutations-resolvers]: Implements sync and async execution pipelines (`resolve_mutation_sync`, `resolve_mutation_async`, `run_write_pipeline_sync`, `run_write_pipeline_async`), GlobalID decoding and validation (`coerce_lookup_id`), model instance decoding, validation, permission enforcement, database save hooks, and optimizer re-fetching.
   - [`mutations/fields.py`][mutations-fields]: Defines the [`DjangoMutationField`][mutations-fields] field factory and target validation (`_validate_mutation_target`).
   - **Deliberate non-export of compiler internals:** Low-level functions (such as `build_mutation_input_class`, `bind_mutations`, `coerce_lookup_id`, `run_write_pipeline_sync`, `run_write_pipeline_async`, and metaclass helpers) are deliberately excluded from `mutations/__init__.py::__all__` per [spec-036][spec-036] Decision 4. Consumers interact solely with the declarative class bases, field factory, and error envelope; schema finalization and execution engines import internals directly from their respective modules.

4. **Permission Posture and Policy Symmetry:**
   - [`DjangoModelPermission`][mutations-permissions] is the canonical write-auth default for model-backed writes (`Meta.permission_classes` defaults to `[DjangoModelPermission]`). It enforces Django model `add` / `change` / `delete` permissions, keeping write authorization strictly separate from row visibility ([`apply_cascade_permissions`][permissions-cascade] / `get_queryset`).
   - `DenyAll` (defined in [`mutations/permissions.py`][mutations-permissions]) is the safe deny-by-default class for model-less plain forms ([`forms/sets.py`][forms-sets] passes `unset_default=(DenyAll,)`). It is deliberately not exported in `mutations/__init__.py::__all__` because model mutations use `DjangoModelPermission`.
   - `AllowAny` is the documented semantic posture of an explicit empty permission list `Meta.permission_classes = []` ([spec-040][spec-040] Decision 5). No separate `AllowAny` class exists in the framework, preventing redundant class hierarchies.
   - Custom permission checks (such as `IsAuthenticated`, `IsStaff`, `IsSuperuser`) follow DRF duck-typing conventions (sync hooks returning `bool`) and are defined by consumers or tests without polluting the core package facade.
   - Mutation field synthesis uses the unified [`DjangoMutationField`][mutations-fields] factory parameterized by declarative mutation classes rather than separate per-operation field factories (such as `CreateMutationField`, `UpdateMutationField`, `DeleteMutationField`), ensuring single-sited field typing and Relay argument handling.

Connected behavior examined:
- [`django_strawberry_framework/mutations/fields.py`][mutations-fields]: Canonical implementation of `DjangoMutationField`.
- [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs]: Input type generation and `FieldError` envelope definition.
- [`django_strawberry_framework/mutations/permissions.py`][mutations-permissions]: `DjangoModelPermission` and `DenyAll` definitions.
- [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers]: Sync and async mutation execution pipelines.
- [`django_strawberry_framework/mutations/sets.py`][mutations-sets]: `DjangoMutation` class definition and registration.
- [`django_strawberry_framework/forms/__init__.py`][forms-init]: Sibling form mutation facade (`DjangoFormMutation`, `DjangoModelFormMutation`).
- [`django_strawberry_framework/rest_framework/__init__.py`][rest-framework-init]: Sibling DRF serializer mutation facade (`SerializerMutation`).
- [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]: Top-level framework facade re-exporting the four mutation symbols.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Phase 2.5 schema finalizer executing `bind_mutations()`.
- [`django_strawberry_framework/registry.py`][registry]: Global registry maintaining subsystem lifecycle clearing hooks for mutation registries and input namespaces.
- [`tests/base/test_init.py`][test-base-init]: Validates package-root and subpackage `__all__` lists and tests export identity.
- [`tests/mutations/test_fields.py`][test-mutations-fields], [`tests/mutations/test_inputs.py`][test-mutations-inputs], [`tests/mutations/test_permissions.py`][test-mutations-permissions], [`tests/mutations/test_resolvers.py`][test-mutations-resolvers], [`tests/mutations/test_sets.py`][test-mutations-sets], [`tests/mutations/test_write_transaction.py`][test-mutations-write-transaction]: Comprehensive test suite for model mutations.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/mutations/__init__.py --include-constants`):
- Parsed 1 target file, 35 lines, 1 constant/module variable ([`__all__`][mutations-init]), 4 imported symbols ([`DjangoModelPermission`][mutations-permissions], [`DjangoMutation`][mutations-sets], [`DjangoMutationField`][mutations-fields], [`FieldError`][mutations-inputs]).
- Confirmed zero execution logic, zero helper functions, zero side effects on import, and zero internal mutable state in `mutations/__init__.py`.
- Verified reverse references across the codebase, tests, and documentation.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   The framework provides three write mutation flavors: model mutations ([`mutations/__init__.py`][mutations-init]), form mutations ([`forms/__init__.py`][forms-init]), and DRF serializer mutations ([`rest_framework/__init__.py`][rest-framework-init]).
   - `mutations/__init__.py` and `forms/__init__.py` both use eager imports and static typed `__all__` tuples to expose their declarative mutation bases.
   - `rest_framework/__init__.py` gates imports behind `require_drf()`.
   - Query set-family facades ([`filters/__init__.py`][filters-init], [`orders/__init__.py`][orders-init]) define forward-reference helper functions (`filter_input_type`, `order_input_type`) for custom query resolvers. Mutations do not need forward-reference resolver helpers because mutation fields are synthesized during schema finalization via `bind_mutations()` and declarative metaclasses.
   - Shared write mechanics are single-sited: `FieldError` envelope in [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs], input materialization and deduplication in [`django_strawberry_framework/utils/inputs.py`][utils-inputs], declaration registries in [`django_strawberry_framework/mutations/sets.py`][mutations-sets], and subsystem clearing in [`django_strawberry_framework/registry.py`][registry].
2. **Sync and async twins:**
   Zero duplication. As a pure export facade, `mutations/__init__.py` contains no callable code or sync/async branching. Synchronous and asynchronous resolution twins (`resolve_mutation_sync` vs `resolve_mutation_async`, `run_write_pipeline_sync` vs `run_write_pipeline_async`) are implemented in [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers], sharing decoding, error extraction, permission checking, and payload formatting logic. [`DjangoMutationField`][mutations-fields] dispatches dynamically at runtime via `in_async_context()`.
3. **Derived rather than repeated knowledge:**
   `__all__` is derived directly from canonical class and factory definitions across the subpackage. The top-level package [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] re-exports `DjangoModelPermission`, `DjangoMutation`, `DjangoMutationField`, and `FieldError` directly from `.mutations`, preserving exact symbol identity without re-declaring types. The module docstring summarizes the five-module architecture without duplicating underlying class configurations.
4. **Inverse and round-trip pairs:**
   Declaration and schema binding pairing: `DjangoMutation` declarations register with `_mutation_registry` upon class definition; phase 2.5 finalization ([`django_strawberry_framework/types/finalizer.py`][types-finalizer]) calls `bind_mutations()` to bind input types, arguments, and return types into Strawberry schema fields.
   Test lifecycle pairing: `registry.clear()` flushes all mutation-related ledgers (`clear_mutation_registry`, `clear_mutation_input_namespace`, `clear_mutation_shape_build_cache`) to ensure clean isolation between test runs.
5. **Contracts restated in another medium:**
   The mutations subpackage public export contract is codified across:
   - Code: [`django_strawberry_framework/mutations/__init__.py`][mutations-init], [`django_strawberry_framework/mutations/fields.py`][mutations-fields], [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs], [`django_strawberry_framework/mutations/permissions.py`][mutations-permissions], [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers], [`django_strawberry_framework/mutations/sets.py`][mutations-sets], [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init], [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/registry.py`][registry];
   - Specifications: [`docs/SPECS/spec-036-mutations-0_0_11.md`][spec-036] (Decisions 2, 4, 5, 6, 7, 8, 14, 15), [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038], [`docs/SPECS/spec-039-serializer_mutations-0_0_13.md`][spec-039], [`docs/SPECS/spec-040-auth_mutations-0_0_13.md`][spec-040];
   - Test suites: [`tests/base/test_init.py`][test-base-init], [`tests/mutations/test_fields.py`][test-mutations-fields], [`tests/mutations/test_inputs.py`][test-mutations-inputs], [`tests/mutations/test_permissions.py`][test-mutations-permissions], [`tests/mutations/test_resolvers.py`][test-mutations-resolvers], [`tests/mutations/test_sets.py`][test-mutations-sets], [`tests/mutations/test_write_transaction.py`][test-mutations-write-transaction], [`examples/fakeshop/test_query/test_products_api.py`][test-products-api], [`examples/fakeshop/test_query/test_auth_api.py`][test-auth-api];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook], [`TODAY.md`][today], [`LIFECYCLE.html`][lifecycle].

### The single-edit-site test

- **Posited change 1 (Adding a new public mutation base, e.g. `DjangoBulkMutation`):** Introduce a new mutation base class in `mutations/sets.py` and expose it on the subpackage API.
  - *Sites that must move:* Exactly 1 site in this facade: [`django_strawberry_framework/mutations/__init__.py`][mutations-init] (import from `.sets` and append to `__all__`).
  - *Site count:* 1.
- **Posited change 2 (Renaming or deprecating an exported mutation symbol):** Rename an existing mutation export across the subpackage.
  - *Sites that must move:* Exactly 1 site in this facade: [`django_strawberry_framework/mutations/__init__.py`][mutations-init] (import statement and `__all__` tuple).
  - *Site count:* 1.
- **Posited change 3 (Modifying mutation input shape generation or naming conventions):** Change how `<Model>Input` names or fields are synthesized from Django model fields.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs] or [`django_strawberry_framework/utils/inputs.py`][utils-inputs]. Zero edits in `mutations/__init__.py`.
  - *Site count:* 1.
- **Posited change 4 (Altering model permission mapping or write authorization hook execution):** Update the `_OPERATION_PERMISSION_ACTION` mapping or permission execution in `permissions.py`.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/permissions.py`][mutations-permissions]. Zero edits in `mutations/__init__.py`.
  - *Site count:* 1.

### Rejected candidates

1. **Re-exporting `DenyAll` from `django_strawberry_framework/mutations/__init__.py`:**
   - Disproved. `DenyAll` is a model-less deny-by-default permission class used internally as the default for `DjangoFormMutation` in [`django_strawberry_framework/forms/sets.py`][forms-sets]. Model mutations are model-backed and use [`DjangoModelPermission`][mutations-permissions] as their canonical default. Exposing `DenyAll` in `mutations/__init__.__all__` would create ambiguity on the model-mutation public surface.
2. **Minting and exporting explicit `AllowAny`, `IsAuthenticated`, `IsStaff`, or `IsSuperuser` classes in `mutations/__init__.py`:**
   - Disproved per [spec-040][spec-040] Decision 5. In django-strawberry-framework, "AllowAny" is the semantic behavior of setting `Meta.permission_classes = []` (the empty list). Minting a dedicated `AllowAny` class would create redundant mechanisms for public access. Role-based checks like `IsAuthenticated`, `IsStaff`, and `IsSuperuser` are simple sync hook implementations that consumers or auth layers implement per project conventions; leaving them un-minted preserves a lean, unopinionated framework core.
3. **Creating and exporting separate per-operation CUD mutation field factories (`CreateMutationField`, `UpdateMutationField`, `DeleteMutationField`):**
   - Disproved per [spec-036][spec-036] Decisions 4 and 5. In django-strawberry-framework, mutation operations are declared on `DjangoMutation` classes via `Meta.operation = "create"|"update"|"delete"`. The single [`DjangoMutationField`][mutations-fields] factory accepts any validated mutation class and wires its Relay GlobalID arguments, transactions, and runtime async dispatch uniformly. Creating separate field factories would duplicate factory logic and diverge from the DRF-first class-based design.
4. **Re-exporting compiler internals (`build_mutation_input_class`, `bind_mutations`, `coerce_lookup_id`, `run_write_pipeline_sync`):**
   - Disproved per [spec-036][spec-036] Decision 4. Keeping internal schema-building and resolver execution machinery private to their defining modules protects the public consumer API from unnecessary internal coupling.

## Opportunities

None — `django_strawberry_framework/mutations/__init__.py` is a clean, 35-line public export facade. It cleanly defines the four-symbol mutation public API surface, enforces encapsulation of subsystem compiler internals, and introduces zero duplicate logic or unowned invariants.

## Judgment

Zero-edit review. `django_strawberry_framework/mutations/__init__.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/mutations/__init__.py --review docs/dry/dry-file-mutations____init__.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent verification confirms that `django_strawberry_framework/mutations/__init__.py` is a clean, minimal public export facade conforming strictly to [spec-036][spec-036] (Decisions 2, 4, 5, 6, 7, 8, 14, 15).

1. **Connected Behavior & Encapsulation Boundary Verification:**
   - **Public Export Surface:** [`__all__`][mutations-init] explicitly re-exports the canonical 4-symbol write surface: [`DjangoModelPermission`][mutations-permissions], [`DjangoMutation`][mutations-sets], [`DjangoMutationField`][mutations-fields], and [`FieldError`][mutations-inputs].
   - **Root Re-Export Parity:** Top-level [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] re-exports all four symbols by direct import, verified by identity assertion in [`tests/base/test_init.py`][test-base-init] (`test_reexported_types_resolve_to_canonical_subpackage_definitions`).
   - **Encapsulation of Subsystem Internals:** Internal compiler functions (`build_mutation_input_class`, `bind_mutations`, `coerce_lookup_id`, `run_write_pipeline_sync`, `run_write_pipeline_async`, metaclass validation helpers) are strictly non-exported from the facade, preventing leaky abstraction boundaries.
   - **Write Authorization Posture:** [`DjangoModelPermission`][mutations-permissions] is the canonical model write-auth default class. `DenyAll` is preserved for model-less plain forms ([`forms/sets.py`][forms-sets]) and intentionally excluded from `mutations/__init__.__all__`. `AllowAny` is cleanly modeled by an empty permission list `Meta.permission_classes = []` ([spec-040][spec-040] Decision 5) rather than a redundant class definition.
   - **Flavor Symmetry:** The write subsystem facade structure mirrors sibling packages ([`forms/__init__.py`][forms-init], [`rest_framework/__init__.py`][rest-framework-init]), while query-side resolver helper functions (`filter_input_type`, `order_input_type`) in [`filters/__init__.py`][filters-init] / [`orders/__init__.py`][orders-init] are omitted here because mutations synthesize schema fields through phase 2.5 finalization (`bind_mutations()`).

2. **5-Axis Probing Matrix Evaluation:**
   - **Axis 1 (Cross-flavor policy mirroring):** Verified single-sited. The [`FieldError`][mutations-inputs] envelope, input generation deduplication ([`utils/inputs.py`][utils-inputs]), and mutation registration ledgers ([`mutations/sets.py`][mutations-sets]) are shared uniformly across all write flavors.
   - **Axis 2 (Sync and async twins):** Verified clean. As an export facade, `mutations/__init__.py` contains zero execution logic. Sync and async execution twins are consolidated in [`mutations/resolvers.py`][mutations-resolvers], with dynamic runtime dispatch handled in [`mutations/fields.py`][mutations-fields].
   - **Axis 3 (Derived rather than repeated knowledge):** Verified. `__all__` is derived from canonical submodule exports; the module docstring describes subpackage architecture without duplicating configuration schemas.
   - **Axis 4 (Inverse and round-trip pairs):** Verified. Declaration registration in `mutations/sets.py` pairs with phase 2.5 finalization schema binding ([`types/finalizer.py`][types-finalizer]), and test suite isolation is guaranteed via clearing hooks in [`registry.py`][registry].
   - **Axis 5 (Contracts restated in another medium):** Verified exact alignment between code, specifications ([spec-036][spec-036], [spec-038][spec-038], [spec-039][spec-039], [spec-040][spec-040]), test suites ([`tests/base/test_init.py`][test-base-init], [`tests/mutations/`][test-mutations-sets]), and documentation ([`README.md`][readme], [`COOKBOOK.md`][cookbook], [`GLOSSARY.md`][glossary], [`TREE.md`][tree], [`LIFECYCLE.html`][lifecycle], [`TODAY.md`][today]).

3. **Single-Edit-Site & Boundary Checks:**
   - Single-edit-site counts for all 4 posited changes hold at exactly 1 site.
   - Rejection rationale for candidates (`DenyAll` re-export, separate `AllowAny` class, per-operation mutation field factories, and compiler internals export) is verified sound.

4. **Tooling & Validation:**
   - Automated check passed: `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/mutations/__init__.py --review docs/dry/dry-file-mutations____init__.md --include-constants` returned 0 errors.
   - Full test suite passed: 6,450 passed tests with 100.0% coverage.

Status updated to `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[lifecycle]: ../../LIFECYCLE.html
[today]: ../../TODAY.md

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-036]: ../SPECS/spec-036-mutations-0_0_11.md
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: ../SPECS/spec-039-serializer_mutations-0_0_13.md
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-init]: ../../django_strawberry_framework/mutations/__init__.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[permissions-cascade]: ../../django_strawberry_framework/permissions.py
[registry]: ../../django_strawberry_framework/registry.py
[rest-framework-init]: ../../django_strawberry_framework/rest_framework/__init__.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-mutations-fields]: ../../tests/mutations/test_fields.py
[test-mutations-inputs]: ../../tests/mutations/test_inputs.py
[test-mutations-permissions]: ../../tests/mutations/test_permissions.py
[test-mutations-resolvers]: ../../tests/mutations/test_resolvers.py
[test-mutations-sets]: ../../tests/mutations/test_sets.py
[test-mutations-write-transaction]: ../../tests/mutations/test_write_transaction.py

<!-- examples/ -->
[test-auth-api]: ../../examples/fakeshop/test_query/test_auth_api.py
[test-products-api]: ../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
