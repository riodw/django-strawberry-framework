# DRY review: `django_strawberry_framework/optimizer/__init__.py`

Status: verified

## System trace

`django_strawberry_framework/optimizer/__init__.py` is the public export facade and package initializer for the framework's GraphQL query optimization subsystem ([spec-002][spec-002], [spec-003][spec-003], [spec-004][spec-004], [spec-006][spec-006], [spec-033][spec-033], [spec-035][spec-035]). It defines the subpackage's public API surface via `__all__`, exposing the consumer-facing `DjangoOptimizerExtension` and re-exporting the canonical framework logger. It owns the following architectural responsibilities:

1. **Subpackage Public Export Facade & Canonical Re-export Surface:**
   - [`DjangoOptimizerExtension`][optimizer-extension] (from `django_strawberry_framework.optimizer.extension`): The primary consumer-facing Strawberry `SchemaExtension` that automatically drives selection-tree AST walking, Django ORM query planning, and N+1 query prevention for GraphQL query execution over Django models ([spec-002][spec-002], [spec-006][spec-006]).
   - [`logger`][django-strawberry-framework-init] (re-exported from `django_strawberry_framework` package root): The framework-wide canonical logger instance (`logging.getLogger("django_strawberry_framework")`). Re-exporting `logger` here serves a load-bearing dual role:
     - Sibling production modules within the optimizer subsystem ([`optimizer/extension.py`][optimizer-extension], [`optimizer/walker.py`][optimizer-walker], [`optimizer/nested_planner.py`][optimizer-nested-planner], and [`optimizer/single_parent_fetch.py`][optimizer-single-parent-fetch]) consume `logger` via `from . import logger` through this subpackage facade as their canonical intra-subpackage logger handle.
     - Downstream types modules ([`types/finalizer.py`][types-finalizer], [`types/resolvers.py`][types-resolvers]) and optimizer tests ([`tests/base/test_init.py`][test-base-init], [`tests/optimizer/test_extension.py`][test-optimizer-extension], [`tests/optimizer/test_nested_index_advisory.py`][test-optimizer-nested-index-advisory]) import `logger` from `django_strawberry_framework.optimizer` to pin the re-export contract established when the flat `optimizer.py` module was promoted to a subpackage.
     - It guarantees that the string literal `"django_strawberry_framework"` is defined in exactly **one** source location ([`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]), avoiding duplicated `logging.getLogger(...)` literals across subpackages.
   - Bound public surface: [`__all__ = ("DjangoOptimizerExtension", "logger")`][optimizer-init] explicitly pins the exported symbols.

2. **Subsystem Encapsulation & Deliberate Non-Exports:**
   - [`OptimizerHint`][optimizer-hints] (from `django_strawberry_framework.optimizer.hints`): The declarative per-field / per-relation optimization override wrapper ([spec-002][spec-002], [spec-006][spec-006]). It is re-exported at package root [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] and reachable via submodule path `django_strawberry_framework.optimizer.hints::OptimizerHint`. It is intentionally omitted from `optimizer/__init__.py::__all__` to keep the subpackage entry point uncluttered and focused on `DjangoOptimizerExtension`.
   - Internal planning mechanics: Query planning data structures and algorithms ([`OptimizationPlan`][optimizer-plans] from `optimizer.plans`, [`plan_optimizations`][optimizer-walker] and `plan_relation` from `optimizer.walker`, [`classify_relation_join`][optimizer-join-taxonomy] from `optimizer.join_taxonomy`, [`NestedConnectionRequest`][optimizer-nested-fetch] from `optimizer.nested_fetch`, [`stash_on_context`][optimizer-context] / [`get_context_value`][optimizer-context] from `optimizer._context`) reside at their dedicated dotted module paths. They are internal implementation details consumed by `DjangoOptimizerExtension`, [`DjangoConnectionField`][connection-fields], and test suites, and are deliberately not re-exported in `optimizer/__init__.py`.
   - Absence of manual query-wrapping decorators or wrappers: The framework's architecture operates via declarative schema extensions (`DjangoOptimizerExtension`) intercepting root resolvers and Relay connections automatically. Manual wrapper constructs (e.g. standalone `optimize()` helper functions, `optimizer_hints` decorators, or `PrefetchType` wrappers common in legacy or alternate GraphQL libraries) are deliberately absent: query planning, `select_related`, `prefetch_related`, and column projection (`only()`) are handled transparently by AST inspection in `DjangoOptimizerExtension` and `walker.py`.

3. **Interaction with Package Root & Sibling Subpackages:**
   - [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]: Re-exports `DjangoOptimizerExtension` (from `.optimizer`) and `OptimizerHint` (from `.optimizer.hints`) in root `__all__`, allowing consumers to import directly from the top-level package or from `django_strawberry_framework.optimizer`.
   - [`django_strawberry_framework/connection/fields.py`][connection-fields]: `DjangoConnectionField` directly delegates to `DjangoOptimizerExtension.apply_to` to execute query planning before connection slicing hides the pre-slice queryset ([spec-033][spec-033]).
   - [`django_strawberry_framework/extensions/debug.py`][extensions-debug]: `DjangoDebugExtension` captures SQL query metrics without duplicating optimizer planning state.

Connected behavior examined:
- [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension]: SchemaExtension lifecycle hooks, cache keys, directive traversal, and root resolve execution.
- [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker]: Selection AST walker producing `OptimizationPlan` instances with `select_related`, `prefetch_related`, and `only()` projection.
- [`django_strawberry_framework/optimizer/hints.py`][optimizer-hints]: `OptimizerHint` dataclass and relation override metadata.
- [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans]: `OptimizationPlan`, `PrefetchPlan`, and plan execution logic.
- [`django_strawberry_framework/optimizer/_context.py`][optimizer-context]: Per-request context storage for plans and sentinels.
- [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]: Canonical logger declaration and root re-export of `DjangoOptimizerExtension` and `OptimizerHint`.
- [`tests/base/test_init.py`][test-base-init]: Pins package root `__all__`, verifies logger identity (`optimizer_logger is logger`), and tests subpackage re-exports.
- [`tests/optimizer/test_extension.py`][test-optimizer-extension]: Comprehensive unit and integration test suite for `DjangoOptimizerExtension`.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/optimizer/__init__.py --include-constants`):
- Parsed 1 target file, 30 lines, 0 class/function definitions, 2 imports (`from .. import logger`, `from .extension import DjangoOptimizerExtension`), 1 constant/assignment (`__all__ = ("DjangoOptimizerExtension", "logger")`).
- Zero runtime logic, zero class definitions, zero helper functions, and zero internal mutable state inside `optimizer/__init__.py`.
- Verified reverse imports across sibling optimizer modules, package root, type finalizers, and test suites.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `optimizer/__init__.py` is the subpackage facade for the query optimization subsystem. Other subpackages (`extensions/__init__.py`, `filters/__init__.py`, `forms/__init__.py`, `mutations/__init__.py`, `orders/__init__.py`, `auth/__init__.py`, `types/__init__.py`, `testing/__init__.py`) follow uniform repository conventions: eager re-exports with static `__all__` for hard-dependency modules, or lazy `__getattr__` guards for soft dependencies (`rest_framework`). Subpackages needing logging re-export `logger` from `..` rather than duplicating `logging.getLogger("django_strawberry_framework")`. `optimizer/__init__.py` strictly encapsulates schema extensions without duplicating resolver construction, type mapping, or mutation logic.
2. **Sync and async twins:**
   Zero duplication. As an export facade, `optimizer/__init__.py` defines no callable code or execution paths. The underlying `DjangoOptimizerExtension` manages sync and async execution hooks uniformly (the selection-tree AST walk is purely synchronous and produces an `OptimizationPlan` applied to Django querysets before execution).
3. **Derived rather than repeated knowledge:**
   `optimizer/__init__.py` derives its public surface directly from canonical source locations (`DjangoOptimizerExtension` from `.extension` and `logger` from `..`). The logger name literal `"django_strawberry_framework"` lives in exactly one place ([`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]), and `optimizer/__init__.py` derives its logger by re-exporting that instance. `__all__` statically mirrors the 2 imported symbols.
4. **Inverse and round-trip pairs:**
   Inapplicable to this target. The module is a static export facade and owns no serialization, encoding, or lifecycle state transitions.
5. **Contracts restated in another medium:**
   The export contracts of `django_strawberry_framework.optimizer` and `DjangoOptimizerExtension` are codified across:
   - Code: [`django_strawberry_framework/optimizer/__init__.py`][optimizer-init], [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] (line 32), [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension];
   - Specifications: [`docs/SPECS/spec-002-optimizer-0_0_2.md`][spec-002] (O1–O6), [`docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md`][spec-003], [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004], [`docs/SPECS/spec-006-public_surface-0_0_3.md`][spec-006] (Lines 51–65), [`docs/SPECS/spec-033-connection_optimizer-0_0_9.md`][spec-033], [`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`][spec-035];
   - Test suites: [`tests/base/test_init.py`][test-base-init] (`test_optimizer_subpackage_reexports_top_level_logger`, `test_public_api_surface_is_pinned`), [`tests/optimizer/test_extension.py`][test-optimizer-extension];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Adding a new consumer-facing export to the optimizer subpackage):** Introduce a new public symbol (e.g. re-exporting `OptimizerHint` directly in `optimizer/__init__.py`).
  - *Sites that must move:* Exactly 1 site within the subpackage facade: [`django_strawberry_framework/optimizer/__init__.py`][optimizer-init] (adding the import from `.hints` and appending the name to `__all__`).
  - *Site count:* 1.
- **Posited change 2 (Renaming or deprecating an export in the subpackage facade):** Rename `DjangoOptimizerExtension` across the optimizer facade.
  - *Sites that must move:* Exactly 1 site in this facade: [`django_strawberry_framework/optimizer/__init__.py`][optimizer-init] (import statement and `__all__` list).
  - *Site count:* 1.
- **Posited change 3 (Changing the canonical framework logger domain name):** Update the logger name literal from `"django_strawberry_framework"` to a new identifier.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] (`logger = logging.getLogger(...)`). Exactly 0 sites in `optimizer/__init__.py` or sibling optimizer modules, because they re-export and consume the single logger instance.
  - *Site count:* 1 (0 in target).

### Rejected candidates

1. **Re-exporting internal planning symbols (`OptimizationPlan`, `plan_optimizations`, `classify_relation_join`) from `optimizer/__init__.py`:**
   - Disproved per [spec-002][spec-002] and [spec-006][spec-006]. These symbols are internal query planning mechanics consumed by `extension.py`, `DjangoConnectionField`, and tests at their canonical dotted submodule paths (`django_strawberry_framework.optimizer.plans`, `django_strawberry_framework.optimizer.walker`, etc.). Re-exporting them in `optimizer/__init__.py` would clutter the public consumer facade.
2. **Re-declaring `logger = logging.getLogger("django_strawberry_framework")` locally inside `optimizer/__init__.py` or individual optimizer modules:**
   - Disproved and pinned by [`tests/base/test_init.py`][test-base-init]::`test_optimizer_subpackage_reexports_top_level_logger`. Declaring local `getLogger` instances would duplicate the string literal `"django_strawberry_framework"` across modules. Re-exporting the root `logger` instance guarantees that the logger name literal lives in exactly one single source location.
3. **Re-exporting `DjangoOptimizerExtension` from `django_strawberry_framework.extensions`:**
   - Disproved per [spec-006][spec-006] and DRY reviews [`dry-file-extensions____init__.md`][dry-file-extensions-init] and [`dry-folder-extensions.md`][dry-folder-extensions]. `DjangoOptimizerExtension` is the entry point of the dedicated query-planning optimizer subsystem and is canonically located at `django_strawberry_framework.optimizer` and root `django_strawberry_framework`. Aliasing it under `extensions/` would produce redundant import paths and obscure optimizer subsystem ownership.
4. **Implementing manual query-wrapping decorators (`@optimize`, `optimizer_hints`, `PrefetchType`) in `optimizer/__init__.py`:**
   - Disproved. `django-strawberry-framework` relies on declarative schema extensions (`DjangoOptimizerExtension`) intercepting root resolvers and Relay connections automatically. Manual field decorators or wrapper objects would duplicate AST walking responsibilities and violate the framework's DRF-first declarative architecture.

## Opportunities

None — `django_strawberry_framework/optimizer/__init__.py` is a clean, 30-line eager export facade. It correctly exposes the subpackage public API (`DjangoOptimizerExtension`, `logger`) with zero duplicate logic, zero unowned state, and total fidelity to architectural and packaging boundaries.

## Judgment

Zero-edit review. `optimizer/__init__.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/__init__.py --review docs/dry/dry-file-optimizer____init__.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Worker 2 independently inspected `django_strawberry_framework/optimizer/__init__.py` and reviewed the findings recorded by Worker 1:

1. **Subpackage Export Facade & Canonical Re-Export Surface:**
   - The file acts strictly as an eager public re-export facade with bound surface [`__all__ = ("DjangoOptimizerExtension", "logger")`][optimizer-init].
   - [`DjangoOptimizerExtension`][optimizer-extension] is derived directly from `.extension` and exposed as the primary consumer-facing Strawberry `SchemaExtension` for selection-tree query planning and N+1 prevention ([spec-002][spec-002], [spec-006][spec-006]).
   - [`logger`][django-strawberry-framework-init] is derived directly from `..` (`logging.getLogger("django_strawberry_framework")`). Re-exporting it here is load-bearing:
     - Intra-subpackage sibling modules ([`optimizer/extension.py`][optimizer-extension], [`optimizer/nested_planner.py`][optimizer-nested-planner], [`optimizer/single_parent_fetch.py`][optimizer-single-parent-fetch], [`optimizer/walker.py`][optimizer-walker]) consume `logger` via `from . import logger`.
     - Downstream modules ([`types/finalizer.py`][types-finalizer], [`types/resolvers.py`][types-resolvers]) and optimizer tests ([`tests/base/test_init.py`][test-base-init], [`tests/optimizer/test_extension.py`][test-optimizer-extension], [`tests/optimizer/test_nested_index_advisory.py`][test-optimizer-nested-index-advisory]) import `logger` from `django_strawberry_framework.optimizer`.
     - Identity assertion `assert optimizer_logger is logger` in [`tests/base/test_init.py`][test-base-init] confirms that `"django_strawberry_framework"` is defined in exactly one single source location.

2. **Subsystem Encapsulation & Packaging Boundaries:**
   - Verified that internal query planning machinery ([`OptimizationPlan`][optimizer-plans], [`plan_optimizations`][optimizer-walker], `plan_relation`, [`classify_relation_join`][optimizer-join-taxonomy], [`NestedConnectionRequest`][optimizer-nested-fetch], [`stash_on_context`][optimizer-context] / [`get_context_value`][optimizer-context]) resides at dedicated dotted submodule paths and is intentionally excluded from `optimizer/__init__.__all__`.
   - Verified that [`OptimizerHint`][optimizer-hints] is re-exported at package root [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] and reachable via `django_strawberry_framework.optimizer.hints::OptimizerHint`, while deliberately excluded from `optimizer/__init__.__all__` per [spec-006][spec-006] to keep the optimizer subpackage facade focused on `DjangoOptimizerExtension`.
   - Verified that manual query-wrapping decorators (`@optimize`, `optimizer_hints`, `PrefetchType` wrappers) are absent in favor of declarative schema extensions and transparent AST traversal.

3. **Mandatory 5-Axis Duplication Probing Matrix:**
   - All 5 axes verified and discharged with valid technical justifications:
     - Cross-flavor policy mirroring: Standard eager facade matching repository conventions.
     - Sync and async twins: Zero execution logic in facade; sync and async execution hooks managed uniformly in `DjangoOptimizerExtension`.
     - Derived rather than repeated knowledge: `__all__` directly mirrors imported symbols; single logger literal maintained at root.
     - Inverse and round-trip pairs: Inapplicable to static export facade.
     - Contracts restated in another medium: Verified exact parity between code, specifications ([spec-002][spec-002], [spec-003][spec-003], [spec-004][spec-004], [spec-006][spec-006], [spec-033][spec-033], [spec-035][spec-035]), test suites ([`tests/base/test_init.py`][test-base-init], [`tests/optimizer/`][test-optimizer-extension]), and standing documentation ([`README.md`][readme], [`GLOSSARY.md`][glossary], [`TREE.md`][tree], [`COOKBOOK.md`][cookbook]).

4. **Single-Edit-Site Invariant:**
   - Single-edit-site counts for all 3 posited changes hold at exactly 1 site (or 0 for root logger changes).
   - Rejection rationale for candidates is verified sound.

5. **Tooling & Coverage Validation:**
   - Ran `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/__init__.py --review docs/dry/dry-file-optimizer____init__.md --include-constants` (exited 0, all targets and topics covered).
   - Full test suite verified passing with 100.0% coverage across 6,450 tests.

Target is confirmed clean, sound, and adhering to all DRY principles. Status updated to `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[dry-file-extensions-init]: dry-file-extensions____init__.md
[dry-folder-extensions]: dry-folder-extensions.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-002]: ../SPECS/spec-002-optimizer-0_0_2.md
[spec-003]: ../SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md
[spec-004]: ../SPECS/spec-004-optimizer_beyond-0_0_3.md
[spec-006]: ../SPECS/spec-006-public_surface-0_0_3.md
[spec-033]: ../SPECS/spec-033-connection_optimizer-0_0_9.md
[spec-035]: ../SPECS/spec-035-optimizer_hardening-0_0_10.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection-fields]: ../../django_strawberry_framework/connection/fields.py
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[extensions-debug]: ../../django_strawberry_framework/extensions/debug.py
[optimizer-context]: ../../django_strawberry_framework/optimizer/_context.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[optimizer-hints]: ../../django_strawberry_framework/optimizer/hints.py
[optimizer-init]: ../../django_strawberry_framework/optimizer/__init__.py
[optimizer-join-taxonomy]: ../../django_strawberry_framework/optimizer/join_taxonomy.py
[optimizer-nested-fetch]: ../../django_strawberry_framework/optimizer/nested_fetch.py
[optimizer-nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[optimizer-plans]: ../../django_strawberry_framework/optimizer/plans.py
[optimizer-single-parent-fetch]: ../../django_strawberry_framework/optimizer/single_parent_fetch.py
[optimizer-walker]: ../../django_strawberry_framework/optimizer/walker.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-optimizer-extension]: ../../tests/optimizer/test_extension.py
[test-optimizer-nested-index-advisory]: ../../tests/optimizer/test_nested_index_advisory.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
