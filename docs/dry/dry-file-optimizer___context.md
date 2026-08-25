# DRY review: `django_strawberry_framework/optimizer/_context.py`

Status: verified

## System trace

`django_strawberry_framework/optimizer/_context.py` is the execution-context hand-off and sentinel manager for the framework's GraphQL query optimization subsystem ([spec-002][spec-002], [spec-004][spec-004], [spec-033][spec-033], [spec-035][spec-035], [spec-047][spec-047], [spec-051][spec-051]). It defines the optimizer's request-context stash key vocabulary, provides start-of-execution context clearing, manages task-local `ContextVar` instances for relation planning scope and active strictness, and re-exports shape-agnostic context helpers. It owns the following architectural responsibilities:

1. **Optimizer Context Key Vocabulary & Constants:**
   - [`DST_OPTIMIZER_PLAN`][optimizer-context] (`"dst_optimizer_plan"`): Request-context stash key storing the root AST [`OptimizationPlan`][optimizer-plans] for introspection and testing ([spec-002][spec-002], [spec-004][spec-004]).
   - [`DST_OPTIMIZER_FK_ID_ELISIONS`][optimizer-context] (`"dst_optimizer_fk_id_elisions"`): Context stash key for the set of foreign-key ID scalar field names elided from relation loading when the foreign key column is already loaded on the parent row ([spec-035][spec-035]).
   - [`DST_OPTIMIZER_PLANNED`][optimizer-context] (`"dst_optimizer_planned"`): Context stash key storing the set of resolver keys for relations the optimizer planned for the execution under non-default strictness ([spec-004][spec-004], [spec-035][spec-035]).
   - [`DST_OPTIMIZER_LOOKUP_PATHS`][optimizer-context] (`"dst_optimizer_lookup_paths"`): Context stash key storing planned relation lookup paths for N+1 analysis ([spec-004][spec-004]).
   - [`DST_OPTIMIZER_STRICTNESS`][optimizer-context] (`"dst_optimizer_strictness"`): Context stash key recording the configured strictness level (`"off"`, `"warn"`, `"raise"`) on the request context ([spec-004][spec-004]).
   - [`DST_OPTIMIZER_KEYS`][optimizer-context]: Canonical tuple pinning all 5 context stash keys (`DST_OPTIMIZER_PLAN`, `DST_OPTIMIZER_FK_ID_ELISIONS`, `DST_OPTIMIZER_PLANNED`, `DST_OPTIMIZER_LOOKUP_PATHS`, `DST_OPTIMIZER_STRICTNESS`) used for start-of-execution reset ([spec-035][spec-035]).

2. **Start-of-Execution Context Lifecycle Reset:**
   - [`clear_optimizer_context`][optimizer-context]: Cleans all 5 [`DST_OPTIMIZER_KEYS`][optimizer-context] from a request context object before operation execution in [`DjangoOptimizerExtension.on_execute`][optimizer-extension]. This prevents sequential `execute` / `execute_sync` calls sharing a reused `context_value` from leaking FK-id elisions (which would cause subsequent full-object selections to return empty scalar stubs) or planned-relation sentinels (which would mask real N+1 query violations).
   - Delegates per-key removal to [`clear_context_key`][utils-context] from [`django_strawberry_framework.utils.context`][utils-context], preserving shape-agnostic handling across plain dicts, objects, `__slots__` mappings, and read-only/frozen contexts.

3. **Per-Execution Task-Local ContextVar State:**
   - Scoped Relations (`_scoped_relations: ContextVar[set[str] | None]`):
     - [`begin_scoped_relations`][optimizer-context]: Initializes a fresh `set()` for the current task/thread execution and returns a reset token.
     - [`end_scoped_relations`][optimizer-context]: Disarms the scoped relations set via the reset token upon execution exit.
     - [`publish_scoped_relations`][optimizer-context]: Idempotently unions planned relation resolver keys into the active execution's scoped set; safely no-ops if no execution is active or if passed falsy/empty collections.
     - [`relation_is_optimizer_scoped`][optimizer-context]: Determines whether a relation resolver key was planned by the optimizer for the current execution, allowing generated relation resolvers in [`django_strawberry_framework.types.resolvers`][types-resolvers] to distinguish optimizer-planned child caches from unhooked consumer prefetches. Fails closed (returns `False`) on unhashable or missing inputs.
   - Active Strictness (`_active_strictness: ContextVar[str | None]`):
     - [`begin_strictness`][optimizer-context]: Sets the active strictness (`"off"`, `"warn"`, `"raise"`) at `on_execute` entry and returns a reset token.
     - [`end_strictness`][optimizer-context]: Restores the previous strictness state via token.
     - [`active_strictness`][optimizer-context]: Returns the current execution's active strictness or `None` if no optimizer is running, ensuring N+1 guards in [`types/resolvers.py`][types-resolvers] remain armed even if an execution lacks a request `context_value` or if the root query returned an unplannable materialized list.

4. **Shape-Agnostic Re-exports:**
   - [`get_context_value`][optimizer-context] and [`stash_on_context`][optimizer-context]: Re-exported from [`django_strawberry_framework.utils.context`][utils-context] for backwards compatibility and convenient access within the optimizer subpackage and test suites.

Connected behavior examined:
- [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension]: SchemaExtension lifecycle hooks managing `begin_scoped_relations`, `begin_strictness`, `clear_optimizer_context`, `publish_scoped_relations`, and stashing `DST_OPTIMIZER_*` keys.
- [`django_strawberry_framework/types/resolvers.py`][types-resolvers]: Model relation resolvers querying `relation_is_optimizer_scoped` and `active_strictness` to enforce N+1 strictness and visibility scoping.
- [`django_strawberry_framework/utils/context.py`][utils-context]: Centralized shape-agnostic read, write, and delete dispatch for request context objects.
- [`django_strawberry_framework/resource_policy.py`][resource-policy]: Sibling subsystem consuming `utils/context.py` for request-context policy stashing.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Type finalizer verifying resolver sentinel contracts.
- [`django_strawberry_framework/connection/fields.py`][connection-fields]: Relay connection fields interacting with optimizer planning and context scoping.
- [`tests/optimizer/test_extension.py`][test-optimizer-extension]: Comprehensive test suites verifying context clearing, `ContextVar` isolation, re-entrant nested executions, and fail-closed error handling.
- [`tests/types/test_resolvers.py`][test-types-resolvers]: Unit tests asserting relation scoping and N+1 strictness behavior under `relation_is_optimizer_scoped` and `active_strictness`.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/optimizer/_context.py --include-constants`):
- Parsed 1 target file, 167 lines, 0 class definitions, 8 function definitions (`publish_scoped_relations`, `relation_is_optimizer_scoped`, `active_strictness`, `begin_strictness`, `end_strictness`, `begin_scoped_relations`, `end_scoped_relations`, `clear_optimizer_context`), 6 constants (`DST_OPTIMIZER_PLAN`, `DST_OPTIMIZER_FK_ID_ELISIONS`, `DST_OPTIMIZER_PLANNED`, `DST_OPTIMIZER_LOOKUP_PATHS`, `DST_OPTIMIZER_STRICTNESS`, `DST_OPTIMIZER_KEYS`), 1 re-exported import group (`clear_context_key`, `get_context_value`, `stash_on_context` from `..utils.context`), and 1 `__all__` tuple containing all 16 public symbols.
- Verified reverse references across `optimizer/extension.py`, `types/resolvers.py`, `tests/optimizer/test_extension.py`, and `tests/types/test_resolvers.py`.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `optimizer/_context.py` provides the underlying execution context and `ContextVar` communication seam for query optimization across all GraphQL operations (queries, mutations, Relay connections, and field resolvers). Sibling flavors (filters, forms, mutations, orders, auth, rest_framework) do not duplicate context stashing or execution-scoping mechanics; they rely uniformly on `DjangoOptimizerExtension` and `types/resolvers.py` which consume `_context.py`. Furthermore, shape-agnostic context dictionary/object access is centralized in [`django_strawberry_framework.utils.context`][utils-context] and shared with [`django_strawberry_framework.resource_policy`][resource-policy], eliminating cross-subsystem dispatch duplication.
2. **Sync and async twins:**
   Zero duplication. Python's `contextvars.ContextVar` handles task-local storage transparently across synchronous execution threads and asynchronous asyncio event loops. Functions in `_context.py` (`publish_scoped_relations`, `relation_is_optimizer_scoped`, `active_strictness`, `clear_optimizer_context`) are purely synchronous and invoked identically in sync and async resolvers (`_make_relation_resolver` sync and async paths in `types/resolvers.py`).
3. **Derived rather than repeated knowledge:**
   `DST_OPTIMIZER_KEYS` derives directly as a tuple of the 5 canonical key constants (`DST_OPTIMIZER_PLAN`, `DST_OPTIMIZER_FK_ID_ELISIONS`, `DST_OPTIMIZER_PLANNED`, `DST_OPTIMIZER_LOOKUP_PATHS`, `DST_OPTIMIZER_STRICTNESS`). `clear_optimizer_context` iterates over `DST_OPTIMIZER_KEYS` rather than repeating string literals. `__all__` statically mirrors every public constant and function. Context helpers `get_context_value` and `stash_on_context` are re-exported directly from `utils.context` rather than duplicated.
4. **Inverse and round-trip pairs:**
   Context lifecycle operations form symmetric pairs:
   - `begin_scoped_relations` sets an empty set and returns a token; `end_scoped_relations` resets the `ContextVar` to its previous state via that token.
   - `begin_strictness` sets the strictness string and returns a token; `end_strictness` restores the previous strictness via that token.
   - `stash_on_context` stashes keys on request context; `get_context_value` reads them; `clear_optimizer_context` deletes every key in `DST_OPTIMIZER_KEYS` via `clear_context_key`.
   - Re-entrant isolation is verified by [`tests/optimizer/test_extension.py`][test-optimizer-extension]::`test_strictness_and_scoped_relations_reentrant_isolation`.
5. **Contracts restated in another medium:**
   The context keys, lifecycle reset, and execution scoping contracts are codified across:
   - Code: [`django_strawberry_framework/optimizer/_context.py`][optimizer-context], [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension], [`django_strawberry_framework/types/resolvers.py`][types-resolvers], [`django_strawberry_framework/utils/context.py`][utils-context];
   - Specifications: [`docs/SPECS/spec-002-optimizer-0_0_2.md`][spec-002] (O3), [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004] (B5), [`docs/SPECS/spec-033-connection_optimizer-0_0_9.md`][spec-033], [`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`][spec-035], [`docs/SPECS/spec-047-resource_policy-0_0_14.md`][spec-047], [`docs/SPECS/spec-051-boundary_dry_squeeze-0_0_15.md`][spec-051];
   - Test suites: [`tests/optimizer/test_extension.py`][test-optimizer-extension] (`test_clear_optimizer_context_*`, `test_publish_scoped_relations_*`, `test_relation_is_optimizer_scoped_*`, `test_strictness_and_scoped_relations_reentrant_isolation`), [`tests/types/test_resolvers.py`][test-types-resolvers];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Adding a new optimizer context stash key):** Introduce a new optimizer sentinel key (e.g. `DST_OPTIMIZER_EXECUTION_TIMINGS = "dst_optimizer_execution_timings"`).
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/_context.py`][optimizer-context] (defining the constant, adding it to `DST_OPTIMIZER_KEYS`, and adding it to `__all__`).
  - *Site count:* 1.
- **Posited change 2 (Changing the ContextVar variable names or initial defaults for scoped relations):** Update the `ContextVar` descriptor name or initial value.
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/_context.py`][optimizer-context] (updating `_scoped_relations = ContextVar(...)`).
  - *Site count:* 1.
- **Posited change 3 (Extending shape-agnostic context dictionary/object read/write/clear mechanics for a new mapping type):** Add support for a new custom context container with idiosyncratic mutation behavior.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/context.py`][utils-context] (`get_context_value`, `stash_on_context`, `clear_context_key`). Exactly 0 sites in `_context.py`, which delegates shape dispatch directly to `utils/context.py`.
  - *Site count:* 1 (0 in target).

### Rejected candidates

1. **Re-implementing dictionary and attribute dispatch directly within `optimizer/_context.py` instead of delegating to `utils/context.py`:**
   - Disproved in [spec-047][spec-047]. The optimizer and resource policy subsystems both require safe, shape-agnostic read, write, and delete operations on GraphQL `info.context` objects (handling `None`, plain dicts, objects, `__slots__` mappings, and locked `QueryDict` instances). Centralizing this dispatch in `utils/context.py` ensures a single point of truth across the repository.
2. **Storing scoped relations and active strictness on `info.context` instead of `ContextVar` instances:**
   - Disproved in [spec-035][spec-035] and `_context.py` design rationale. Executions without a `context_value` or operations where the root query returns an unplannable materialized list would fail to stash or retrieve sentinels, silently disarming N+1 guards and scoping checks. `ContextVar` instances provide execution-lifetime tracking independent of context object presence.
3. **Merging `optimizer/_context.py` into `optimizer/extension.py`:**
   - Disproved. `optimizer/_context.py` is imported by downstream modules such as [`django_strawberry_framework.types.resolvers`][types-resolvers] to inspect `relation_is_optimizer_scoped` and `active_strictness` without importing the full `DjangoOptimizerExtension` class and its heavy AST walking dependencies, preventing cyclic imports and maintaining clean subsystem boundaries.

## Opportunities

None — `django_strawberry_framework/optimizer/_context.py` is a clean, 167-line, focused module. It cleanly defines the optimizer stash vocabulary, manages task-local execution state with fail-closed semantics, delegates generic context dispatch to `utils/context.py`, and exhibits zero duplicate logic or unowned state.

## Judgment

Zero-edit review. `optimizer/_context.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/_context.py --review docs/dry/dry-file-optimizer___context.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independently traced and verified `django_strawberry_framework/optimizer/_context.py` against all callers, sibling modules, test suites, and specifications.

1. **Behavioral Trace & Boundary Analysis:**
   - **Context Stash Keys & Start-of-Execution Reset:** Re-verified all 5 key constants ([`DST_OPTIMIZER_PLAN`][optimizer-context], [`DST_OPTIMIZER_FK_ID_ELISIONS`][optimizer-context], [`DST_OPTIMIZER_PLANNED`][optimizer-context], [`DST_OPTIMIZER_LOOKUP_PATHS`][optimizer-context], [`DST_OPTIMIZER_STRICTNESS`][optimizer-context]) and the canonical reset tuple [`DST_OPTIMIZER_KEYS`][optimizer-context]. Verified that [`clear_optimizer_context`][optimizer-context] delegates per-key clearing to [`clear_context_key`][utils-context] in [`django_strawberry_framework.utils.context`][utils-context], ensuring shape-agnostic handling across dictionaries, custom context objects, and read-only structures without leaking state across sequential operations reusing a `context_value`.
   - **Task-Local ContextVar Lifecycle:** Re-verified `_scoped_relations` and `_active_strictness` lifecycle management. `begin_scoped_relations` and `begin_strictness` open per-execution scope returning tokens that `end_scoped_relations` and `end_strictness` restore in `DjangoOptimizerExtension.on_execute`'s `finally` block. Confirmed that [`publish_scoped_relations`][optimizer-context] and [`relation_is_optimizer_scoped`][optimizer-context] fail closed on empty, `None`, or unhashable objects.
   - **Shape-Agnostic Re-exports:** Re-verified that [`get_context_value`][optimizer-context] and [`stash_on_context`][optimizer-context] are clean re-exports from [`django_strawberry_framework.utils.context`][utils-context], preserving backwards-compatible imports across the optimizer subpackage and test suites without duplicating dictionary/attribute dispatch.

2. **Mandatory 5-Axis Matrix Discharge:**
   - *Cross-flavor policy mirroring:* Verified. Optimizer context management is singular to `optimizer/_context.py`; generic request-context access is consolidated in `utils/context.py` and shared with `resource_policy.py`.
   - *Sync and async twins:* Verified. `contextvars.ContextVar` transparently handles task-local state across synchronous threads and asyncio event loops. `publish_scoped_relations`, `relation_is_optimizer_scoped`, and `active_strictness` operate synchronously and are consumed identically by sync and async relation resolvers.
   - *Derived rather than repeated knowledge:* Verified. `DST_OPTIMIZER_KEYS` aggregates the 5 canonical key constants; `clear_optimizer_context` iterates over the tuple; `__all__` statically mirrors the public export surface.
   - *Inverse and round-trip pairs:* Verified. `begin_scoped_relations` / `end_scoped_relations` and `begin_strictness` / `end_strictness` form symmetric bracketed lifecycle pairs.
   - *Contracts restated in another medium:* Verified. Contracts align across code, specifications ([spec-002][spec-002], [spec-004][spec-004], [spec-033][spec-033], [spec-035][spec-035], [spec-047][spec-047], [spec-051][spec-051]), tests ([`tests/optimizer/test_extension.py`][test-optimizer-extension], [`tests/types/test_resolvers.py`][test-types-resolvers]), and documentation ([`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook]).

3. **Single-Edit-Site Counts:**
   - Posited changes 1–3 confirmed with single-edit-site counts of 1 at their authoritative owners.

4. **Tooling & Test Gate:**
   - Executed `export_dry_review.py check --target django_strawberry_framework/optimizer/_context.py --review docs/dry/dry-file-optimizer___context.md --include-constants` (14 target definitions covered).
   - Test suites in `tests/optimizer/` and `tests/types/` pass cleanly (1341 tests passing).

Status verified.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-002]: ../SPECS/spec-002-optimizer-0_0_2.md
[spec-004]: ../SPECS/spec-004-optimizer_beyond-0_0_3.md
[spec-033]: ../SPECS/spec-033-connection_optimizer-0_0_9.md
[spec-035]: ../SPECS/spec-035-optimizer_hardening-0_0_10.md
[spec-047]: ../SPECS/spec-047-resource_policy-0_0_14.md
[spec-051]: ../SPECS/spec-051-boundary_dry_squeeze-0_0_15.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection-fields]: ../../django_strawberry_framework/connection/fields.py
[optimizer-context]: ../../django_strawberry_framework/optimizer/_context.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[optimizer-plans]: ../../django_strawberry_framework/optimizer/plans.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py
[utils-context]: ../../django_strawberry_framework/utils/context.py

<!-- tests/ -->
[test-optimizer-extension]: ../../tests/optimizer/test_extension.py
[test-types-resolvers]: ../../tests/types/test_resolvers.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
