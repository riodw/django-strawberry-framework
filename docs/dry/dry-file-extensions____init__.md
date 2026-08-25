# DRY review: `django_strawberry_framework/extensions/__init__.py`

Status: verified

## System trace

`django_strawberry_framework/extensions/__init__.py` is the public export facade for the framework's Strawberry schema extensions subpackage ([spec-044][spec-044], [spec-047][spec-047], [spec-048][spec-048]). It defines the subpackage export surface via `__all__`, re-exporting the three first-party `SchemaExtension` classes provided by `django-strawberry-framework`:

1. [`DjangoDebugExtension`][extensions-debug] (from `django_strawberry_framework.extensions.debug`): The development-only response-extensions debug surface capturing Django SQL queries (via connection-level `force_debug_cursor` bracketing) and execution exceptions into `response.extensions["debug"]` ([spec-044][spec-044]). It is **deliberately NOT re-exported from the package root** [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] ([spec-044][spec-044] Decision 11, [`tests/base/test_init.py`][test-base-init]). The package root exposes the always-on production schema-building recipe; isolating `DjangoDebugExtension` under `django_strawberry_framework.extensions` provides an explicit import-path signal that debug payload capture is an opt-in development tool that returns unmasked tracebacks and parameter-interpolated SQL.
2. [`DjangoErrorPolicyExtension`][extensions-error-policy] (from `django_strawberry_framework.extensions.error_policy`): The response-side enforcement extension for `ErrorPolicy` ([spec-048][spec-048]). It sanitizes and masks unexpected execution exceptions into stable, correlation-tagged `GraphQLError` instances while logging root exceptions server-side. It is installed automatically by [`DjangoSchema`][schema] at index 0 (front of extension list, unwinding last in LIFO order) and is also root-exported from [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] for consumers assembling plain `strawberry.Schema` instances.
3. [`DjangoResourcePolicyExtension`][extensions-resource-policy] (from `django_strawberry_framework.extensions.resource_policy`): The request-side enforcement extension for `ResourcePolicy` ([spec-047][spec-047]). It enforces pre-parse document token limits, AST complexity bounds, fragment spread cycle detection, and input cardinality budgets. It is installed automatically by [`DjangoSchema`][schema] (at the end of the extension list, executing first) and is also root-exported from [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] for consumers assembling plain `strawberry.Schema` instances.

Shape and Dependency Architecture:
- Eager re-export facade: imports explicit symbols and binds `__all__ = ["DjangoDebugExtension", "DjangoErrorPolicyExtension", "DjangoResourcePolicyExtension"]`.
- Hard core dependencies only: all underlying modules depend strictly on core framework libraries (`django`, `strawberry-graphql`, `graphql-core`). There are no optional or soft dependencies (e.g. `channels` or `rest_framework`) inside `extensions/`, so no dynamic PEP 562 `__getattr__` or lazy loader machinery is required.

Connected behavior examined:
- [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]: Re-exports `DjangoErrorPolicyExtension` and `DjangoResourcePolicyExtension` in root `__all__`, while deliberately omitting `DjangoDebugExtension`.
- [`django_strawberry_framework/schema.py`][schema]: Automatically instantiates and orders `DjangoErrorPolicyExtension` and `DjangoResourcePolicyExtension` during `DjangoSchema` construction.
- [`django_strawberry_framework/optimizer/__init__.py`][optimizer-init]: Sibling subsystem facade exporting `DjangoOptimizerExtension`, kept distinct because optimizer planning constitutes a dedicated subsystem.
- [`tests/base/test_init.py`][test-base-init]: Pins package root `__all__` and tests that `DjangoDebugExtension` is excluded from root exports.
- [`tests/extensions/test_debug.py`][test-extensions-debug]: Imports `DjangoDebugExtension` via `from django_strawberry_framework.extensions import DjangoDebugExtension`.
- [`tests/test_error_policy.py`][test-error-policy], [`tests/test_resource_policy.py`][test-resource-policy]: Validate error and resource policy extension execution.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/extensions/__init__.py --include-constants`):
- Parsed 1 target file, 36 lines, 1 constant definition (`__all__`), 3 imports (`DjangoDebugExtension`, `DjangoErrorPolicyExtension`, `DjangoResourcePolicyExtension`).
- Confirmed zero runtime logic, zero class definitions, zero helper functions, and zero internal state inside `extensions/__init__.py`.
- Verified reverse imports and subpackage boundary contracts across the entire test suite and codebase.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `extensions/__init__.py` is the subpackage facade for `SchemaExtension` implementations. Other subpackages (`filters/__init__.py`, `forms/__init__.py`, `auth/__init__.py`, `optimizer/__init__.py`, `utils/__init__.py`, `testing/__init__.py`) expose their respective subsystem entry points following uniform repository conventions: eager re-exports with static `__all__` for hard-dependency modules, or lazy `__getattr__` guards for optional soft dependencies. `extensions/__init__.py` strictly encapsulates schema extensions without duplicating resolver construction, type mapping, or mutation logic.
2. **Sync and async twins:**
   Zero duplication. As an export facade, `extensions/__init__.py` defines no callable code or execution paths. The underlying extension classes manage their own execution hooks (`DjangoDebugExtension` bridges via thread/task local context; `DjangoErrorPolicyExtension` uses a synchronous generator teardown valid for both sync and async operations; `DjangoResourcePolicyExtension` performs synchronous pre-parse text scan and AST validation before execution begins).
3. **Derived rather than repeated knowledge:**
   `extensions/__init__.py` derives its public surface directly from the canonical member modules (`extensions/debug.py`, `extensions/error_policy.py`, `extensions/resource_policy.py`) by importing the classes and listing their exact names in `__all__`. It does not redefine docstring summaries or duplicate class configurations. Its module docstring provides architectural context explaining the purposeful asymmetry between root-exported default extensions and subpackage-only debug extensions.
4. **Inverse and round-trip pairs:**
   Inapplicable to this target. The module is a static export facade and owns no serialization, encoding, or lifecycle state transitions.
5. **Contracts restated in another medium:**
   The export contract of `django_strawberry_framework.extensions` (including the isolation of `DjangoDebugExtension` and the root-re-export of `DjangoErrorPolicyExtension` and `DjangoResourcePolicyExtension`) is codified across:
   - Code: [`django_strawberry_framework/extensions/__init__.py`][extensions-init], [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] (comments lines 55-56), [`django_strawberry_framework/schema.py`][schema];
   - Specifications: [`docs/SPECS/spec-044-debug_extension-0_0_14.md`][spec-044] (Decisions 1, 11), [`docs/SPECS/spec-047-resource_policy-0_0_14.md`][spec-047], [`docs/SPECS/spec-048-secure_output_defaults-0_0_14.md`][spec-048];
   - Test suites: [`tests/base/test_init.py`][test-base-init], [`tests/extensions/test_debug.py`][test-extensions-debug], [`tests/test_error_policy.py`][test-error-policy], [`tests/test_resource_policy.py`][test-resource-policy];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new first-party Strawberry SchemaExtension):** Introduce a new schema extension (e.g. `DjangoTracingExtension` in `extensions/tracing.py`).
  - *Sites that must move:* Exactly 1 site within the subpackage facade: [`django_strawberry_framework/extensions/__init__.py`][extensions-init] (adding the import and appending the class name to `__all__`).
  - *Site count:* 1.
- **Posited change 2 (Renaming or deprecating an extension export):** Rename an existing schema extension class across the subpackage.
  - *Sites that must move:* Exactly 1 site in this facade: [`django_strawberry_framework/extensions/__init__.py`][extensions-init] (import statement and `__all__` list).
  - *Site count:* 1.

### Rejected candidates

1. **Re-exporting `DjangoOptimizerExtension` from `django_strawberry_framework/extensions/__init__.py`:**
   - Disproved. While `DjangoOptimizerExtension` inherits from `SchemaExtension`, it is the entry point of the dedicated query-planning optimizer subsystem (`django_strawberry_framework/optimizer/`). It is canonically exported from `django_strawberry_framework.optimizer` and root `django_strawberry_framework`. Creating an additional alias in `extensions/` would produce redundant import paths and obscure optimizer subsystem ownership.
2. **Re-exporting `DjangoDebugExtension` from root `django_strawberry_framework/__init__.py`:**
   - Disproved. Explicitly rejected by [spec-044][spec-044] Decision 11 and pinned by [`tests/base/test_init.py`][test-base-init]. `DjangoDebugExtension` returns parameter-interpolated SQL and unmasked exception tracebacks intended solely for development environments. Excluding it from package-root exports prevents accidental leakage into production schema configurations.
3. **Introducing lazy import machinery (PEP 562 `__getattr__`) to `extensions/__init__.py`:**
   - Disproved. All three extension modules depend only on required core libraries (`django`, `strawberry-graphql`, `graphql-core`). There are no optional soft dependencies in `extensions/`, making eager re-exports with `__all__` the cleanest, most idiomatic implementation.

## Opportunities

None — `django_strawberry_framework/extensions/__init__.py` is a clean, 36-line eager export facade. It correctly exposes the subpackage public API (`DjangoDebugExtension`, `DjangoErrorPolicyExtension`, `DjangoResourcePolicyExtension`) with zero duplicate logic, zero unowned state, and total fidelity to architectural and security boundaries.

## Judgment

Zero-edit review. `extensions/__init__.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/extensions/__init__.py --review docs/dry/dry-file-extensions____init__.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Worker 2 independently inspected `django_strawberry_framework/extensions/__init__.py` and reviewed the findings recorded by Worker 1:

1. **Subpackage Export Facade & Canonical Owners:**
   - The file acts strictly as an eager re-export facade with `__all__ = ["DjangoDebugExtension", "DjangoErrorPolicyExtension", "DjangoResourcePolicyExtension"]`.
   - Each symbol maps 1:1 to its canonical implementation module (`.debug`, `.error_policy`, `.resource_policy`).
   - Re-export identity verified across `tests/base/test_init.py` and dedicated extension suites.

2. **Security & Packaging Boundary Verification:**
   - Verified that `DjangoDebugExtension` is deliberately NOT exported from package root `django_strawberry_framework/__init__.py` ([spec-044][spec-044] Decision 11). This separation maintains an explicit import-path distinction for development-only introspection tools that expose unmasked tracebacks and interpolated SQL.
   - Verified that `DjangoErrorPolicyExtension` and `DjangoResourcePolicyExtension` are re-exported at package root because they are installed by default by `DjangoSchema` ([spec-047][spec-047], [spec-048][spec-048]).
   - Verified that `DjangoOptimizerExtension` is properly isolated in `django_strawberry_framework.optimizer` as the entry point of the query-planning subsystem, rather than aliased in `extensions/`.

3. **Mandatory 5-Axis Duplication Probing Matrix:**
   - All 5 axes verified and discharged with valid technical justifications:
     - Cross-flavor policy mirroring: Standard eager facade matching repository conventions.
     - Sync and async twins: No executable code in facade.
     - Derived rather than repeated knowledge: `__all__` directly derives from imported symbols.
     - Inverse and round-trip pairs: Inapplicable to static export facade.
     - Contracts restated in another medium: Verified parity between code, specs, tests, and documentation.

4. **Single-Edit-Site Invariant:**
   - Confirmed that modifying, adding, or deprecating an extension entry in the facade touches exactly 1 site in `extensions/__init__.py`.

5. **Tooling & Coverage Validation:**
   - Ran `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/extensions/__init__.py --review docs/dry/dry-file-extensions____init__.md --include-constants` (exited 0, all targets and topics covered).

Target is confirmed clean, sound, and adhering to all DRY principles. Status updated to `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-044]: ../SPECS/spec-044-debug_extension-0_0_14.md
[spec-047]: ../SPECS/spec-047-resource_policy-0_0_14.md
[spec-048]: ../SPECS/spec-048-secure_output_defaults-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[extensions-debug]: ../../django_strawberry_framework/extensions/debug.py
[extensions-error-policy]: ../../django_strawberry_framework/extensions/error_policy.py
[extensions-init]: ../../django_strawberry_framework/extensions/__init__.py
[extensions-resource-policy]: ../../django_strawberry_framework/extensions/resource_policy.py
[optimizer-init]: ../../django_strawberry_framework/optimizer/__init__.py
[schema]: ../../django_strawberry_framework/schema.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-error-policy]: ../../tests/test_error_policy.py
[test-extensions-debug]: ../../tests/extensions/test_debug.py
[test-extensions-init]: ../../tests/extensions/__init__.py
[test-resource-policy]: ../../tests/test_resource_policy.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
