# Project review: `django_strawberry_framework/`

Sibling artifacts read for this pass:

- Per-file: `rev-conf.md`, `rev-exceptions.md`, `rev-registry.md`
- Optimizer: `rev-optimizer___context.md`, `rev-optimizer__extension.md`, `rev-optimizer__field_meta.md`, `rev-optimizer__hints.md`, `rev-optimizer__plans.md`, `rev-optimizer__walker.md`, `rev-optimizer.md`
- Types: `rev-types__base.md`, `rev-types__converters.md`, `rev-types__resolvers.md`, `rev-types.md`
- Utils: `rev-utils__relations.md`, `rev-utils__strings.md`, `rev-utils__typing.md`, `rev-utils.md`

## High:

None.

## Medium:

### Silent-data-loss patterns recurred across multiple files; harden similar surfaces proactively

Three independent files in this cycle had the same shape of bug: a defensive operation accepted inputs that downstream code silently dropped or mis-mapped, with no signal to the consumer.

- `OptimizerHint.__post_init__` now rejects conflicting flag combinations that walker priority order previously would have resolved silently.
- `_validate_optimizer_hints_against_selected_fields` now rejects hint keys for excluded fields.
- `convert_choices_to_enum` now rejects raw choice values that sanitize to the same enum member.
- The registry now rejects same-class-against-two-models and mismatched enum re-registration.

The class of remaining surfaces worth a future audit:

- `_select_fields` could reject a typo or filter combination that produces an empty field selection.
- `convert_relation` still trusts the registered target type and lets some consumer cardinality misunderstandings surface only later at query time.
- `DjangoOptimizerExtension.cache_info()` exposes cache counters but does not identify hot-plan eviction.

Recommended: track these as a coherent validation-hardening thread for the next cycle. Each guard is small and should have a single test pinning the new error path.

## Low:

### Caches are independent today; a shared cache lifecycle note would centralize lifetimes

Four caches live in the package: registry maps, `DjangoOptimizerExtension._plan_cache`, per-`DjangoType` `_optimizer_field_map`, and per-`DjangoType` `_optimizer_hints`. Each lifetime is correct for its consumer, but the package has no single document or comment that enumerates them. Note for AGENTS.md or future internals docs; no source-code change required.

### Public API is consistent and DRF-shaped

The public surface is exactly: `DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, `auto`, `__version__`. All five are DRF-shaped and no Strawberry decorator surface leaks onto consumer classes. No action needed.

### Test placement honored across the cycle

Tests added during the cycle landed in package-parallel locations such as `tests/optimizer/`, `tests/types/`, and `tests/utils/`. No tests were added under frozen paths; no tests landed in `examples/fakeshop/`.

## What looks solid

- **Public API surface is small and DRF-shaped.** Five exports total: `DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, `auto`, `__version__`.
- **Import graph is acyclic and one-directional.** `exceptions.py` is the bottom of the graph; `utils/` imports nothing from the package; `registry.py` imports only `exceptions`; `optimizer/` imports `exceptions`, `registry`, and `utils`; `types/` consumes optimizer primitives but the optimizer does not import back from `types/`.
- **Framework-wide logger is centralized.** `optimizer/__init__.py` defines `logger = logging.getLogger("django_strawberry_framework")`; optimizer modules and relation resolvers import it.
- **Context hand-off is centralized.** `optimizer/_context.py` owns `get_context_value`, `stash_on_context`, and all `dst_optimizer_*` sentinel constants used by the optimizer write side and resolver read side.
- **Relation cardinality classification is centralized.** `utils/relations.py` owns the shared many/reverse-one-to-one/forward-single classification used by converters, resolvers, and optimizer planning.
- **Optimizer lookup-path and field-map invariants are centralized.** `plans._lookup_path` is reused by `walker._append_prefetch_unique`, and `walker._resolve_field_map` owns registered-type field-map lookup inside the walker.
- **Cache invariants are pinned and consistent.** `OptimizationPlan` remains mutable-with-discipline, cacheability propagates from child to parent, and registry idempotency guards match converter cache behavior.
- **Validation is layered and load-bearing.** `Meta` validation, optimizer-hint validation, choice enum collision checks, and registry guards all fail loudly with model/field context.
- **Selection-tree walking honors GraphQL semantics.** `@skip` / `@include` directives are evaluated, aliased selections are merged, and resolver keys preserve all aliases via response keys.
- **Two Scoops of Django shape is honored.** Modules are small and focused, queryset boundaries are explicit, settings are isolated, and reusable utilities are introduced only for genuinely shared behavior.
- **CHANGELOG was not touched.** Per AGENTS.md, `CHANGELOG.md` is not updated except on explicit instruction.

---

### Summary:

The package is small, well-shaped, and gets the most consumer-visible behavior right: Meta-driven `DjangoType` validation, optimizer N+1 prevention, and cardinality-aware relation resolvers. The review cycle fixed the confirmed Medium items and the closeout pass resolved the stale DRY findings: context helpers and sentinel keys are centralized, relation-cardinality classification is shared, field-map resolution is centralized, and prefetch lookup-path handling is reused. One project-level Medium remains as forward-looking work: a coherent validation-hardening pass over surfaces that can still silently drop or mis-map inputs. No High issues remain.
