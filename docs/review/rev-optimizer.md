# Folder review: `django_strawberry_framework/optimizer/`

Sibling artifacts read for this pass:

- `docs/review/rev-optimizer___context.md`
- `docs/review/rev-optimizer__extension.md`
- `docs/review/rev-optimizer__field_meta.md`
- `docs/review/rev-optimizer__hints.md`
- `docs/review/rev-optimizer__plans.md`
- `docs/review/rev-optimizer__walker.md`

## High:

None.

## Medium:

### Hand-rolled `logging.getLogger("django_strawberry_framework")` literal duplicated across `extension.py` and `walker.py`

Two files inside the subpackage originally created the framework-wide logger via the same string literal. The folder-level fix centralized `logger = logging.getLogger("django_strawberry_framework")` in `optimizer/__init__.py` and had `extension.py`, `walker.py`, and `types/resolvers.py` import the shared logger.

This was the right boundary fix to make in the folder pass because the deduplication only made sense once all call sites were recognized as duplicates.

## Low:

### `Any`-typed surfaces could share a forward-reference module

Several files (`hints.py`, `plans.py`, `field_meta.py`, `walker.py`) all import `Prefetch` or `models` under `TYPE_CHECKING` to tighten an `Any`-typed field. A shared `optimizer/_types.py` with the canonical `TYPE_CHECKING` imports would reduce the per-file boilerplate, but at a few files of two-line imports each, the current shape is acceptable. Note for monitoring; do not act yet.

### `logger.debug` log lines are inconsistently shaped

`extension.py` and `walker.py` both emit `logger.debug` lines but with slightly different message shapes. The shared `"Optimizer: "` prefix is consistent and the inconsistency is comment-polish tier only. Defer.

## What looks solid

- **Public surface is narrow and intentional.** `optimizer/__init__.py` re-exports only `DjangoOptimizerExtension` and `logger`; `OptimizationPlan` and `plan_optimizations` remain implementation details.
- **Module responsibilities are well-separated.** `_context.py` owns context hand-off helpers and sentinel constants, `field_meta.py` owns the cached value object, `hints.py` owns the consumer-facing directive type, `plans.py` owns the data model and reconciliation logic, `walker.py` owns selection-tree traversal, and `extension.py` owns the Strawberry hook and plan cache.
- **No circular-import risk.** `exceptions.py` remains the bottom of the import graph. The optimizer subpackage imports `registry` and `utils` but does not import from `types/`.
- **Cache invariants are consistent across files.** `OptimizationPlan.cacheable` is set/cleared by the walker and read by the extension; custom `get_queryset` paths poison cacheability and the cache only stores `cacheable=True` plans.
- **Resolver-key and lookup-path helpers are centralized.** `plans.py` owns `resolver_key`, runtime path helpers, and `_lookup_path`; `walker.py` now reuses `_lookup_path` when de-duplicating `Prefetch` entries.
- **Field-map resolution is centralized in the walker.** `_resolve_field_map` now owns the registered-type/cached-map lookup shared by `_walk_selections` and `_selected_scalar_names`.
- **Per-file Medium fixes are mutually consistent.** The cache-invariant pin in `OptimizationPlan` matches the walker's `replace`-not-mutate pattern, and the conflicting-flag rejection in `OptimizerHint.__post_init__` matches the priority order the walker consumes.

---

### Summary:

The optimizer subpackage is well-shaped: one job per module, narrow public surface, acyclic import graph, and consistent cache, resolver-key, lookup-path, field-map, and context-sentinel invariants across files. The earlier logger duplication was fixed during the review cycle. The remaining Low items are monitor-only typing-boilerplate and log-message polish.

---

### Worker 3 verification

- Medium fix: `optimizer/__init__.py` now defines the framework-wide `logger` once, and `extension.py`, `walker.py`, and `types/resolvers.py` import it.
- Closeout DRY fixes: `_context.py` centralizes context helpers and sentinel constants; `walker.py` centralizes field-map resolution in `_resolve_field_map`; `walker.py` reuses `plans._lookup_path` for `Prefetch` de-duplication.
- Low items: the forward-reference-module and `logger.debug` shape notes remain deferred per the artifact's monitor-only disposition.
- Validation: `uv run ruff format`, `uv run ruff check`, and `uv run pytest -q` passed; tests reported 360 passed, 4 skipped, 100% coverage.
- CHANGELOG: not updated. Internal refactors only; no consumer-visible behavior change.
- Checkbox in `docs/review/review-0_0_3.md`: marked `- [x]`.
