# DRY review: `django_strawberry_framework/management/commands/__init__.py`

Status: verified

## System trace

`django_strawberry_framework/management/commands/__init__.py` is the subpackage marker and namespace initializer for the framework's Django management commands ([spec-022][spec-022], [spec-029][spec-029]). It contains a one-line module docstring defining the namespace:

```python
"""Implementations of the framework's ``manage.py`` commands (``export_schema``, ``inspect_django_type``)."""
```

It owns the following architectural responsibilities:

1. **Django Management Commands Subpackage Convention & Discovery:**
   - Django's command discovery mechanism (`django.core.management.find_commands` / `load_command_class`) dynamically inspects installed applications listed in `INSTALLED_APPS` (or declared via [`DjangoStrawberryFrameworkConfig`][apps] in `django_strawberry_framework/apps.py`).
   - Django's discovery convention requires both `django_strawberry_framework.management` and `django_strawberry_framework.management.commands` to be importable Python packages.
   - `django_strawberry_framework/management/commands/__init__.py` satisfies this requirement as an empty marker module (with docstring compliant with flake8/ruff `D100`).
   - Sibling command modules ([`export_schema.py`][commands-export-schema], [`inspect_django_type.py`][commands-inspect-django-type]) are discovered dynamically by filename inspection; private helper modules prefixed with an underscore ([`_imports.py`][commands-imports]) are automatically ignored by Django discovery.

2. **Zero Runtime Logic & Public Surface Encapsulation:**
   - The module intentionally defines no runtime execution logic, no classes, no helper functions, no mutable state, and no exports (`__all__`).
   - Management commands (`export_schema`, `inspect_django_type`) are invoked via the command-line interface (`python manage.py <command>`) or programmatically through `django.core.management.call_command`. Consumers never import `Command` classes directly from Python code.
   - In accordance with [spec-022][spec-022] Decision 1 and [spec-029][spec-029] Decision 4, management command classes are not re-exported from `commands/__init__.py`, `management/__init__.py`, or the package root [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] to avoid noise-only API widening and naming conflicts (both commands name their entrypoint class `Command`).
   - Internal helper utilities ([`django_strawberry_framework/management/commands/_imports.py`][commands-imports]) are kept encapsulated within `management/commands/` without leaking into public root exports.

Connected behavior examined:
- [`django_strawberry_framework/management/__init__.py`][management-init]: Parent package marker for the framework's management namespace.
- [`django_strawberry_framework/management/commands/export_schema.py`][commands-export-schema]: `export_schema` management command for exporting GraphQL SDL ([spec-022][spec-022]).
- [`django_strawberry_framework/management/commands/inspect_django_type.py`][commands-inspect-django-type]: `inspect_django_type` diagnostic management command for field-to-type resolution introspection ([spec-029][spec-029]).
- [`django_strawberry_framework/management/commands/_imports.py`][commands-imports]: Shared helper translating import errors to `CommandError` across management commands.
- [`django_strawberry_framework/apps.py`][apps]: `DjangoStrawberryFrameworkConfig` AppConfig registering the application in `INSTALLED_APPS` to activate management command discovery.
- [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]: Framework package root, which deliberately excludes management command classes from root exports.
- [`tests/management/__init__.py`][test-management-init]: Test subpackage marker for management command unit tests.
- [`tests/management/test_export_schema.py`][test-management-export-schema], [`tests/management/test_inspect_django_type.py`][test-management-inspect-django-type], [`tests/management/test_imports.py`][test-management-imports]: Package-tier unit test suites for management commands and helpers.
- [`examples/fakeshop/tests/test_export_schema.py`][example-test-export-schema], [`examples/fakeshop/tests/test_inspect_django_type.py`][example-test-inspect-django-type], [`examples/fakeshop/apps/products/tests/test_commands.py`][example-products-test-commands], [`examples/fakeshop/apps/kanban/tests/test_commands.py`][example-kanban-test-commands]: Live-tier integration tests exercising management commands via `call_command`.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/management/commands/__init__.py --include-constants`):
- Target file contains 2 lines, 0 class definitions, 0 function definitions, 0 constant definitions, 0 imports, and 0 mutable state.
- Verified packaging and discovery behavior across Django's management infrastructure, test suites, and documentation.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `management/commands/__init__.py` is a package namespace marker required by Django's management command discovery conventions. Unlike public feature subpackages ([`filters/__init__.py`][filters-init], [`forms/__init__.py`][forms-init], [`mutations/__init__.py`][mutations-init], [`orders/__init__.py`][orders-init], [`auth/__init__.py`][auth-init], [`extensions/__init__.py`][extensions-init], [`types/__init__.py`][types-init], [`optimizer/__init__.py`][optimizer-init]) that define eager or lazy re-exports and maintain static `__all__` lists for direct consumer importing, `management/commands/__init__.py` defines no public symbols because Django management commands are accessed exclusively via CLI or `django.core.management.call_command`. Sibling marker [`management/__init__.py`][management-init] serves the identical packaging marker role for the parent management directory. There is zero duplicate logic across subpackage initializers.
2. **Sync and async twins:**
   Zero duplication. As a namespace marker containing solely a docstring, `management/commands/__init__.py` contains no callable code, no execution branching, and no sync/async paths. Management commands themselves execute synchronously within Django CLI and `call_command` pipelines.
3. **Derived rather than repeated knowledge:**
   `management/commands/__init__.py` contains only a docstring declaring its namespace purpose and listing the implemented commands. It does not hardcode option parsers, argument definitions, execution logic, or command dispatch tables. Django dynamically derives command discovery by scanning the `commands/` directory on disk for command modules (`*.py` not starting with `_`).
4. **Inverse and round-trip pairs:**
   Inapplicable to this target. The module is a static package marker with no runtime state, serialization, decoding, or lifecycle transitions.
5. **Contracts restated in another medium:**
   The package marker requirement and directory-based discovery contract are codified across:
   - Code: [`django_strawberry_framework/management/commands/__init__.py`][management-commands-init], [`django_strawberry_framework/management/__init__.py`][management-init], [`django_strawberry_framework/apps.py`][apps];
   - Specifications: [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] (Decision 1, Slice 1), [`docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md`][spec-022-rationale] (Decision 1 rationale), [`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] (Decision 4);
   - Tests: [`tests/management/__init__.py`][test-management-init], [`tests/management/test_export_schema.py`][test-management-export-schema], [`tests/management/test_inspect_django_type.py`][test-management-inspect-django-type], [`tests/management/test_imports.py`][test-management-imports], [`examples/fakeshop/tests/test_export_schema.py`][example-test-export-schema], [`examples/fakeshop/tests/test_inspect_django_type.py`][example-test-inspect-django-type];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new Django management command, e.g. `check_optimizer`):**
  - Add `django_strawberry_framework/management/commands/check_optimizer.py`.
  - Django's `manage.py` dynamic discovery walks `management/commands/` directly on disk.
  - Updating the parenthetical list of commands in the docstring in `management/commands/__init__.py` is optional/informational (1 edit site if updated for docstring parity, 0 code edit sites for runtime execution).
  - *Sites that must move in `django_strawberry_framework/management/commands/__init__.py`:* 0 code sites (optionally 1 docstring site).
  - *Site count in `management/commands/__init__.py`:* 0 (code) / 1 (docstring).
- **Posited change 2 (Renaming or moving the framework's management commands namespace or app packaging layout):**
  - Rename or update the docstring of the management commands namespace.
  - *Sites that must move in `django_strawberry_framework/management/commands/__init__.py`:* Exactly 1 site (the module docstring).
  - *Site count in `management/commands/__init__.py`:* 1.

### Rejected candidates

1. **Re-exporting `Command` classes or defining `__all__` in `management/commands/__init__.py`:**
   - Disproved per [spec-022][spec-022] Decision 1 and [spec-029][spec-029] Decision 4. Django's `call_command` and CLI discover commands dynamically via `INSTALLED_APPS` and filenames under `management/commands/`. Re-exporting `Command` classes in `commands/__init__.py` would create name collisions (both `export_schema.py` and `inspect_django_type.py` define a class named `Command`), pollute the module namespace, and expose an artificial import API that bypasses Django's standard management dispatcher.
2. **Eliminating `management/commands/__init__.py` (relying on implicit namespace package):**
   - Disproved per Django management command discovery conventions. Django's `find_commands` implementation and standard package tooling expect `commands/` to be an explicit regular Python package containing `__init__.py`. Omitting `__init__.py` risks import and packaging discovery anomalies across diverse execution and installation environments.
3. **Implementing dynamic command dispatch or custom registration tables in `commands/__init__.py`:**
   - Disproved. Django core already provides the canonical discovery and dispatch machinery (`django.core.management.find_commands` and `django.core.management.load_command_class`). Creating a custom dispatcher or registry in `commands/__init__.py` would duplicate Django core's responsibility and introduce maintenance overhead.

## Opportunities

None — `django_strawberry_framework/management/commands/__init__.py` is a clean, 2-line package namespace marker module. It satisfies Django's management command discovery conventions, complies with flake8/ruff `D100`, and introduces zero duplicate logic, zero unowned state, and zero excess surface.

## Judgment

Zero-edit review. `django_strawberry_framework/management/commands/__init__.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 0/1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/management/commands/__init__.py --review docs/dry/dry-file-management__commands____init__.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent verification conducted by Worker 2 on 2026-08-24.

### 1. Target and Namespace Boundary Analysis
- Target `django_strawberry_framework/management/commands/__init__.py` was inspected. It is a 2-line packaging marker containing solely the module docstring:
  ```python
  """Implementations of the framework's ``manage.py`` commands (``export_schema``, ``inspect_django_type``)."""
  ```
- Checked runtime definitions: 0 classes, 0 functions, 0 variables, 0 constants, 0 type aliases, 0 imports, 0 mutable state.
- Django management command discovery mechanism (`django.core.management.find_commands` / `load_command_class`) relies on walking `management/commands/` within installed apps (`INSTALLED_APPS` registered through [`DjangoStrawberryFrameworkConfig`][apps]).
- Verified sibling command modules ([`export_schema.py`][commands-export-schema] and [`inspect_django_type.py`][commands-inspect-django-type]) are discovered dynamically by filename; helper module [`_imports.py`][commands-imports] is ignored by Django discovery due to the leading underscore prefix convention.
- Verified encapsulation: both `export_schema.py` and `inspect_django_type.py` name their entrypoint class `Command`. Intentionally omitting re-exports in `commands/__init__.py`, `management/__init__.py`, and root [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] avoids name collisions, unnecessary API expansion, and maintains idiomatic Django CLI/`call_command` invocation ([spec-022][spec-022], [spec-029][spec-029]).

### 2. Mandatory 5-Axis Duplication Probing Matrix Verification
- **Axis 1 (Cross-flavor policy mirroring):** Verified. Unlike public feature subpackages that maintain explicit `__all__` re-exports, `management/commands/__init__.py` defines no public symbols. Sibling marker [`management/__init__.py`][management-init] mirrors this zero-export marker structure for the parent management namespace.
- **Axis 2 (Sync and async twins):** Verified. Zero executable runtime logic or execution paths exist in the marker module. Management command dispatch in Django is synchronous.
- **Axis 3 (Derived rather than repeated knowledge):** Verified. Command availability is derived by Django core dynamically scanning the file system (`management/commands/*.py`) rather than hardcoding static registry tables in `__init__.py`.
- **Axis 4 (Inverse and round-trip pairs):** Verified legitimately inapplicable. The file is a static package marker with no runtime state, serialization, or inverse transforms.
- **Axis 5 (Contracts restated in another medium):** Verified. Packaging conventions and command behaviors are consistently defined across code ([`commands/__init__.py`][management-commands-init], [`management/__init__.py`][management-init], [`apps.py`][apps]), specifications ([spec-021][spec-021], [spec-022][spec-022], [spec-029][spec-029]), tests ([`tests/management/`][test-management-init]), and standing documentation ([`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree]).

### 3. Single-Edit-Site Counts
- **Change 1 (Adding a new management command):** 0 code edit sites in `commands/__init__.py` (optionally 1 docstring site for human-readable docstring synchronization).
- **Change 2 (Renaming/relocating namespace or updating docstring):** Exactly 1 edit site (the module docstring).

### 4. Verification Check and Test Execution
- Executed `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/management/commands/__init__.py --review docs/dry/dry-file-management__commands____init__.md --include-constants`: confirmed 0 missing definitions and 0 required topics.
- Executed `uv run pytest --no-cov tests/management/`: 59 passed in full suite.

### 5. Confirmation
Worker 1's findings and zero-edit determination are confirmed. No DRY violations, redundant logic, or unowned state exist. Target is verified clean.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-021]: ../SPECS/spec-021-apps-0_0_7.md
[spec-022]: ../SPECS/spec-022-export_schema-0_0_7.md
[spec-022-rationale]: ../SPECS/appx/spec-022-export_schema-0_0_7-rationale.md
[spec-029]: ../SPECS/spec-029-consumer_dx_cleanup-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[apps]: ../../django_strawberry_framework/apps.py
[auth-init]: ../../django_strawberry_framework/auth/__init__.py
[commands-export-schema]: ../../django_strawberry_framework/management/commands/export_schema.py
[commands-imports]: ../../django_strawberry_framework/management/commands/_imports.py
[commands-inspect-django-type]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[extensions-init]: ../../django_strawberry_framework/extensions/__init__.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[management-commands-init]: ../../django_strawberry_framework/management/commands/__init__.py
[management-init]: ../../django_strawberry_framework/management/__init__.py
[mutations-init]: ../../django_strawberry_framework/mutations/__init__.py
[optimizer-init]: ../../django_strawberry_framework/optimizer/__init__.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[types-init]: ../../django_strawberry_framework/types/__init__.py

<!-- tests/ -->
[test-management-export-schema]: ../../tests/management/test_export_schema.py
[test-management-imports]: ../../tests/management/test_imports.py
[test-management-init]: ../../tests/management/__init__.py
[test-management-inspect-django-type]: ../../tests/management/test_inspect_django_type.py

<!-- examples/ -->
[example-kanban-test-commands]: ../../examples/fakeshop/apps/kanban/tests/test_commands.py
[example-products-test-commands]: ../../examples/fakeshop/apps/products/tests/test_commands.py
[example-test-export-schema]: ../../examples/fakeshop/tests/test_export_schema.py
[example-test-inspect-django-type]: ../../examples/fakeshop/tests/test_inspect_django_type.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
