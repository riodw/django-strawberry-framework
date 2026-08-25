# DRY review: `django_strawberry_framework/middleware/__init__.py`

Status: verified

## System trace

`django_strawberry_framework/middleware/__init__.py` is the package marker and top-level namespace initializer for the framework's Django HTTP middleware subpackage ([spec-042][spec-042], [spec-046][spec-046]). It contains a module docstring defining its architectural purpose:

```python
"""Django HTTP middleware integrations for django-strawberry-framework.

Import-clean by design: this package marker imports nothing optional, so
``import django_strawberry_framework.middleware`` succeeds on machines without
django-debug-toolbar and whole-package walkers (the ``docs/TREE.md`` renderer,
coverage collection) traverse it safely. The consumer-facing surface is the
full leaf dotted path in a ``MIDDLEWARE`` settings string
(``django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware``);
there is deliberately NO re-export here - importing the leaf module is the
soft-dependency opt-in (spec-042 Decisions 3/4/5).
"""
```

It owns the following architectural responsibilities:

1. **Import-Clean Package Marker and Soft-Dependency Isolation:**
   - The framework provides two first-party Django middleware classes:
     - [`DebugToolbarMiddleware`][middleware-debug-toolbar] (in `django_strawberry_framework/middleware/debug_toolbar.py`): The `django-debug-toolbar` SQL panel integration for Strawberry Django GraphQL views ([spec-042][spec-042]). `django-debug-toolbar` is a [soft dependency][glossary] with an import-time `require_debug_toolbar()` guard and `apps.is_installed("debug_toolbar")` wiring check.
     - [`GraphQLRequestBodyBoundaryMiddleware`][middleware-request-body] (in `django_strawberry_framework/middleware/request_body.py`): The request-body size and header wire-encoding boundary middleware positioned before `CsrfViewMiddleware` ([spec-046][spec-046]).
   - `middleware/__init__.py` deliberately imports **nothing optional or leaf-scoped**. This guarantees that `import django_strawberry_framework.middleware` succeeds unconditionally in environments where `django-debug-toolbar` is not installed, allowing whole-package AST walkers, doc generators ([`scripts/build_tree_md.py`][scripts-build-tree]), test discovery, and coverage analysis to traverse the tree safely.

2. **Django Middleware Settings String Protocol & Surface Encapsulation:**
   - In Django architecture, middleware classes are configured via dotted module path strings in `settings.MIDDLEWARE` (e.g. `"django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware"` and `"django_strawberry_framework.middleware.request_body.GraphQLRequestBodyBoundaryMiddleware"`), resolved at runtime via `django.utils.module_loading.import_string`.
   - Consumers never import middleware classes directly in schema definitions or application code.
   - Per [spec-042][spec-042] (Decisions 3, 4, 5) and [spec-046][spec-046] (Decision 18), neither middleware is re-exported from `middleware/__init__.py` or the package root [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]. Importing the leaf module path is the explicit opt-in boundary.

Connected behavior examined:
- [`django_strawberry_framework/middleware/debug_toolbar.py`][middleware-debug-toolbar]: `DebugToolbarMiddleware` subclass of `debug_toolbar.middleware.DebugToolbarMiddleware` overriding `process_view` and `_postprocess` ([spec-042][spec-042]).
- [`django_strawberry_framework/middleware/request_body.py`][middleware-request-body]: `GraphQLRequestBodyBoundaryMiddleware` enforcing request body byte caps and refusal wire formats before CSRF parsing ([spec-046][spec-046]).
- [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]: Framework package root, which deliberately excludes middleware classes from root `__all__`.
- [`django_strawberry_framework/views.py`][views]: HTTP GraphQL views cooperating with `GraphQLRequestBodyBoundaryMiddleware` through `_boundary_ordering.py` markers.
- [`django_strawberry_framework/utils/imports.py`][utils-imports]: `require_optional_module` primitive backing the soft-dependency guard in `debug_toolbar.py`.
- [`tests/middleware/__init__.py`][test-middleware-init]: Test subpackage marker for middleware tests.
- [`tests/middleware/test_debug_toolbar.py`][test-middleware-debug-toolbar]: Soft-dependency absence matrix and unit test suite for `DebugToolbarMiddleware`, explicitly verifying that `import django_strawberry_framework.middleware` succeeds without `django-debug-toolbar`.
- [`tests/test_views.py`][test-views]: Unit and integration tests for `GraphQLRequestBodyBoundaryMiddleware` ordering and cap enforcement.
- [`examples/fakeshop/config/settings.py`][example-settings]: Reference application configuring `GraphQLRequestBodyBoundaryMiddleware` and `DebugToolbarMiddleware` via full dotted paths in `MIDDLEWARE`.
- [`examples/fakeshop/test_query/test_transport_api.py`][example-test-transport-api]: Live transport API integration tests.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/middleware/__init__.py --include-constants`):
- Target file contains 12 lines, 0 class definitions, 0 function definitions, 0 constant definitions, 0 imports, and 0 mutable state.
- Verified packaging and soft-dependency isolation behavior across Django middleware loading infrastructure, test suites, and documentation.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `middleware/__init__.py` is an import-clean package marker. Unlike public feature subpackages ([`filters/__init__.py`][filters-init], [`forms/__init__.py`][forms-init], [`mutations/__init__.py`][mutations-init], [`orders/__init__.py`][orders-init], [`auth/__init__.py`][auth-init], [`extensions/__init__.py`][extensions-init], [`types/__init__.py`][types-init], [`optimizer/__init__.py`][optimizer-init]) that maintain eager re-exports and static `__all__` lists for direct consumer Python imports in schema definitions, `middleware/__init__.py` exports zero symbols because Django middleware is configured via dotted-string paths in `settings.MIDDLEWARE`. It mirrors the zero-export marker structure of Django infrastructure markers ([`management/__init__.py`][management-init] and [`management/commands/__init__.py`][management-commands-init]). There is zero duplicate logic across subpackage initializers.
2. **Sync and async twins:**
   Zero duplication. As a package marker containing solely a docstring, `middleware/__init__.py` contains no executable code, no branching, and no sync/async execution paths. Sync/async twin handling is managed at leaf owners (e.g. `request_body.py` dynamically adapts to sync and async `get_response` callables via `asgiref.sync.markcoroutinefunction`).
3. **Derived rather than repeated knowledge:**
   `middleware/__init__.py` contains only an architectural docstring explaining the import-clean opt-in model. It does not repeat middleware setting strings, class hierarchies, or configuration flags. Django dynamically resolves middleware classes from dotted paths in `settings.MIDDLEWARE` at startup.
4. **Inverse and round-trip pairs:**
   Inapplicable to this target. The module is a static package marker with no runtime state, serialization, decoding, or lifecycle transitions.
5. **Contracts restated in another medium:**
   The import-clean package marker contract, soft-dependency isolation, and dotted-path configuration requirement are codified across:
   - Code: [`django_strawberry_framework/middleware/__init__.py`][middleware-init], [`django_strawberry_framework/middleware/debug_toolbar.py`][middleware-debug-toolbar], [`django_strawberry_framework/middleware/request_body.py`][middleware-request-body], [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init];
   - Specifications: [`docs/SPECS/spec-042-debug_toolbar-0_0_14.md`][spec-042] (Decisions 3, 4, 5), [`docs/SPECS/spec-046-transport_security-0_0_14.md`][spec-046] (Decision 18);
   - Test suites: [`tests/middleware/test_debug_toolbar.py`][test-middleware-debug-toolbar] (`test_package_and_middleware_imports_stay_clean_without_toolbar`), [`tests/base/test_init.py`][test-base-init], [`tests/test_views.py`][test-views];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary] (Debug-toolbar middleware, GraphQLRequestBodyBoundaryMiddleware, Soft dependency), [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new Django middleware integration, e.g. `DjangoTelemetryMiddleware` in `middleware/telemetry.py`):**
  - Add `django_strawberry_framework/middleware/telemetry.py`.
  - Django middleware is wired via dotted-path strings in `settings.MIDDLEWARE` (`"django_strawberry_framework.middleware.telemetry.DjangoTelemetryMiddleware"`).
  - *Sites that must move in `django_strawberry_framework/middleware/__init__.py`:* Exactly 0 sites (the package marker remains completely decoupled from individual leaf modules).
  - *Site count in `middleware/__init__.py`:* 0.
- **Posited change 2 (Renaming or amending the subpackage namespace docstring / architectural policy):**
  - Update the module docstring in `django_strawberry_framework/middleware/__init__.py`.
  - *Sites that must move in `django_strawberry_framework/middleware/__init__.py`:* Exactly 1 site (the module docstring).
  - *Site count in `middleware/__init__.py`:* 1.

### Rejected candidates

1. **Re-exporting `DebugToolbarMiddleware` from `django_strawberry_framework/middleware/__init__.py`:**
   - Disproved and rejected per [spec-042][spec-042] Decisions 3, 4, and 5. `django-debug-toolbar` is an optional soft dependency. Importing `debug_toolbar.py` triggers `require_debug_toolbar()` and `apps.is_installed("debug_toolbar")`. Re-exporting `DebugToolbarMiddleware` in `middleware/__init__.py` would cause `import django_strawberry_framework.middleware` to fail on environments where `django-debug-toolbar` is not installed, breaking package inspection, tree doc rendering ([`scripts/build_tree_md.py`][scripts-build-tree]), and test suite discovery.
2. **Re-exporting `GraphQLRequestBodyBoundaryMiddleware` from `django_strawberry_framework/middleware/__init__.py`:**
   - Disproved. While `request_body.py` has no soft dependency, Django middleware is conventionally referenced by its full dotted string in `settings.MIDDLEWARE`. Re-exporting one middleware while deliberately omitting the other would create confusing asymmetry and redundant public API surface. Keeping `middleware/__init__.py` purely as an import-clean marker maintains a uniform and predictable rule: all middleware classes are referenced by their leaf dotted path (`django_strawberry_framework.middleware.<module>.<ClassName>`).
3. **Re-exporting middleware classes at package root (`django_strawberry_framework/__init__.py`):**
   - Disproved per [spec-042][spec-042] Decision 3 and [spec-046][spec-046] Decision 18, verified in [`tests/base/test_init.py`][test-base-init] and [`tests/middleware/test_debug_toolbar.py`][test-middleware-debug-toolbar]. Package root exports are reserved for schema construction primitives, fields, types, and default extensions. Middleware classes are configured in Django's settings list and are never used directly in schema definition code.
4. **Implementing PEP 562 lazy `__getattr__` exports in `middleware/__init__.py`:**
   - Disproved per [spec-042][spec-042] Decision 5. Dynamic lazy loading in `__init__.py` would obscure the explicit soft-dependency opt-in model. In Django, importing the leaf module via `settings.MIDDLEWARE` dotted path at startup is the exact point of opt-in, making lazy loading in `__init__.py` unnecessary and redundant.

## Opportunities

None — `django_strawberry_framework/middleware/__init__.py` is a clean, 12-line import-clean package marker module. It satisfies Django middleware conventions, protects soft-dependency boundaries, and introduces zero duplicate logic, zero unowned state, and zero excess surface.

## Judgment

Zero-edit review. `django_strawberry_framework/middleware/__init__.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 0/1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/middleware/__init__.py --review docs/dry/dry-file-middleware____init__.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

### 1. Connected behavior, boundaries, and packaging contract re-trace
Independently traced `django_strawberry_framework/middleware/__init__.py` and re-evaluated the architectural decisions governing Django middleware subpackage initialization:
- **Soft-dependency isolation boundary:** `django-debug-toolbar` is a soft dependency with strict import-time guards in [`django_strawberry_framework/middleware/debug_toolbar.py`][middleware-debug-toolbar] (`require_debug_toolbar()`) and app registry checks (`apps.is_installed("debug_toolbar")`). Leaving `middleware/__init__.py` completely free of eager re-exports ensures `import django_strawberry_framework.middleware` remains clean and succeeds without `django-debug-toolbar` installed, preserving safe execution for whole-package tooling, AST scanners, and coverage collectors.
- **Django runtime loading protocol:** Middleware classes are loaded directly by Django's `import_string` from dotted-path strings in `settings.MIDDLEWARE` (e.g. `"django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware"` and `"django_strawberry_framework.middleware.request_body.GraphQLRequestBodyBoundaryMiddleware"`). There is no requirement or use case for schema code to import middleware from `middleware/__init__.py` or root [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init].
- **Zero re-export symmetry:** Keeping `middleware/__init__.py` purely as a marker module creates uniform, predictable behavior across all middleware components, preventing accidental coupling and ensuring that opting into leaf middleware occurs strictly at Django settings configuration time.

### 2. Challenge of candidate alternatives
- **Lazy `__getattr__` re-exports:** PEP 562 lazy exports (as used for DRF components at package root) were evaluated and rejected. DRF types are used directly in Python type definitions and mutation classes; middleware is only referenced as configuration strings. Lazy resolution in `middleware/__init__.py` would add unnecessary indirection without consumer benefit.
- **Root `__all__` inclusion:** Re-exporting middleware at package root was evaluated and confirmed invalid per [spec-042][spec-042] (Decision 3) and [spec-046][spec-046] (Decision 18), verified by [`tests/base/test_init.py`][test-base-init].

### 3. Duplication matrix and single-edit-site verification
- **5-axis probing matrix:** Confirmed that all 5 axes are fully and accurately discharged with sound architectural justifications.
- **Single-edit-site counts:** Verified that adding a new middleware integration requires 0 edits in `middleware/__init__.py`, and updating the subpackage docstring/policy requires exactly 1 edit.
- **Tooling check:** Ran `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/middleware/__init__.py --review docs/dry/dry-file-middleware____init__.md --include-constants` (0 definitions, 0 required topics missing).
- **Test validation:** Ran `uv run pytest tests/middleware/test_debug_toolbar.py --no-cov` (19 passing tests verifying import-clean invariants under simulated toolbar absence).

Status updated to `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-042]: ../SPECS/spec-042-debug_toolbar-0_0_14.md
[spec-046]: ../SPECS/spec-046-transport_security-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[apps]: ../../django_strawberry_framework/apps.py
[auth-init]: ../../django_strawberry_framework/auth/__init__.py
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[extensions-init]: ../../django_strawberry_framework/extensions/__init__.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[management-commands-init]: ../../django_strawberry_framework/management/commands/__init__.py
[management-init]: ../../django_strawberry_framework/management/__init__.py
[middleware-debug-toolbar]: ../../django_strawberry_framework/middleware/debug_toolbar.py
[middleware-init]: ../../django_strawberry_framework/middleware/__init__.py
[middleware-request-body]: ../../django_strawberry_framework/middleware/request_body.py
[mutations-init]: ../../django_strawberry_framework/mutations/__init__.py
[optimizer-init]: ../../django_strawberry_framework/optimizer/__init__.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[types-init]: ../../django_strawberry_framework/types/__init__.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py
[views]: ../../django_strawberry_framework/views.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-middleware-debug-toolbar]: ../../tests/middleware/test_debug_toolbar.py
[test-middleware-init]: ../../tests/middleware/__init__.py
[test-views]: ../../tests/test_views.py

<!-- examples/ -->
[example-settings]: ../../examples/fakeshop/config/settings.py
[example-test-transport-api]: ../../examples/fakeshop/test_query/test_transport_api.py

<!-- scripts/ -->
[scripts-build-tree]: ../../scripts/build_tree_md.py

<!-- .venv/ -->

<!-- External -->
