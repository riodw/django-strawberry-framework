# Review: `django_strawberry_framework/optimizer/` (folder pass)

Scope: all sibling `.py` files in `django_strawberry_framework/optimizer/` plus the folder's `__init__.py`. Per-file artifacts already exist for `_context.py`, `extension.py`, `field_meta.py`, `hints.py`, `plans.py`, and `walker.py`; this pass surfaces cross-file concerns only.

## High:

None.

## Medium:

### Inconsistent `_optimizer_hints` shape guard between `extension.py` and `walker.py`

After the `walker.py` Medium-4 fix, the walker reads the legacy hints mirror as `getattr(type_cls, "_optimizer_hints", None) or {} if type_cls is not None else {}` (walker.py:141). The schema audit in `extension.py:483` still reads `getattr(type_cls, "_optimizer_hints", {})`. Both consume the same `ClassVar[dict[str, OptimizerHint]]` written at `types/base.py:148`, but the extension's read raises `AttributeError` if a future code path or test double sets the mirror to `None`, while the walker silently coerces. The hint-shape contract should be enforced once, the same way, on every reader. Folder-level recommendation: either route both readers through a single `_iter_type_hints(type_cls)` helper in `optimizer/hints.py` (next to `hint_is_skip`, matching the centralisation rationale already established for skip-dispatch), or — preferred per the existing TODO anchors at `walker.py:64-68` and `walker.py:138-140` — retire both reads behind `registry.get_definition(type_cls)` in the same slice that drops the `_optimizer_field_map`/`_optimizer_hints` mirrors.

```django_strawberry_framework/optimizer/extension.py:483:488
            hints = getattr(type_cls, "_optimizer_hints", {})
            for field_name, meta in field_map.items():
                if not meta.is_relation:
                    continue
                # Skip fields opted out via OptimizerHint.SKIP.
                if hint_is_skip(hints.get(field_name)):
```

```django_strawberry_framework/optimizer/walker.py:141:141
        hints_map = getattr(type_cls, "_optimizer_hints", None) or {} if type_cls is not None else {}
```

### `_optimizer_active` ContextVar has no reader inside the package

`extension.py:147-151` declares `_optimizer_active`, `extension.py:318` sets it on `on_execute`, `extension.py:324` resets it. Per-file review for `extension.py` flagged that no in-file reader exists and routed the check here. A package-wide grep across `django_strawberry_framework/` finds zero read sites — `types/resolvers.py` imports `DST_OPTIMIZER_*` keys from `_context.py` but does not import or call `_optimizer_active`. The toggle is therefore dead state with cost (one `set`/`reset` per execution plus the ContextVar object) and a misleading docstring inviting consumers to inspect it. Either delete the ContextVar (preferred — the comment block at `extension.py:155-160` says it exists to signal resolvers we are inside an optimised execution; resolvers do not read it today) or wire a `types/resolvers.py` consumer in the same slice that gives it a defined purpose. Test discipline: any retain decision should add an assertion that some resolver path reads the value, so future deletion is loud.

```django_strawberry_framework/optimizer/extension.py:147:151
_optimizer_active: ContextVar[bool] = ContextVar(
    "django_strawberry_framework_optimizer_active",
    default=False,
)
```

### Documented "do not mutate post-handoff" contract recurs across `plans.py`, `walker.py`, and `extension.py`

Three folder files lean on the same un-enforced invariant: `plans.OptimizationPlan` is documented as immutable-after-handoff but is a non-frozen dataclass with mutable list fields; `extension._publish_plan_to_context` defensively copies `plan.fk_id_elisions` and `plan.planned_resolver_keys` into fresh sets, which only covers the two fields it knows about; the walker's `_apply_hint` branches build the plan directly. The plan cache (extension.py:59 `_MAX_PLAN_CACHE_SIZE`) hands the same `OptimizationPlan` instance to every matching request, so any mutation by a caller (walker post-handoff or downstream resolver) silently poisons the cache for subsequent requests. This is the same calibration noted for `registry._finalized` in earlier cycles (registry.py): a documented contract enforced nowhere, with silent state corruption as the failure mode. Folder-level resolution path: extract a `OptimizationPlan.finalize()` that swaps `select_related`/`only_fields`/`prefetch_related`/`fk_id_elisions`/`planned_resolver_keys` to tuples; call it from the walker's exit (`plan_optimizations` return) and from `diff_plan_for_queryset`'s `replace` branch. The defensive copies in `_publish_plan_to_context` then become redundant and the symmetry — every caller observes an immutable plan — is enforced once. Test surface: a B1 cache-isolation test attempts to append to `cached_plan.prefetch_related` and asserts `TypeError` (tuple immutability).

```django_strawberry_framework/optimizer/plans.py:38:80
@dataclass
class OptimizationPlan:
    """Immutable-ish bag of optimizer directives for one root queryset.
    ...
    """
    select_related: list[str] = field(default_factory=list)
    ...
    prefetch_related: list[str | Prefetch] = field(default_factory=list)
    ...
    cacheable: bool = True
```

### `_append_unique` / `_append_unique_many` / `_append_prefetch_unique` belong next to `_lookup_path` in `plans.py`

The three dedupe helpers live at `walker.py:453-465` but operate on `OptimizationPlan` fields, not on anything walker-internal. `_append_prefetch_unique` calls `_lookup_path` (imported from `plans.py:16`) for its dedupe key, so the helper already depends on `plans.py`. Conceptually the helpers are "plan list mutators" and belong in `plans.py` next to `_lookup_path` and the `_diff_*` helpers. Moving them collapses an asymmetry surfaced by the `walker.py` Medium-1 fix: the per-file reviewer noticed the `hint.prefetch_obj` branch was bypassing `_append_prefetch_unique` and called the fix at the walker; with the helpers in `plans.py` the dedupe discipline is a property of the plan shape rather than a walker convention. Folder-level recommendation: relocate in the same slice that ships the `OptimizationPlan.finalize()` work above; both changes converge `plans.py` into the single owner of plan-shape invariants.

```django_strawberry_framework/optimizer/walker.py:453:469
def _append_unique(values: list[Any], value: Any) -> None:
    ...
def _append_unique_many(values: list[Any], new_values: tuple[Any, ...]) -> None:
    ...
def _append_prefetch_unique(values: list[Any], prefetch: Prefetch) -> None:
    ...
```

## Low:

### `of_type` graphql-core type-peel duplicated twice in `extension.py`, absent elsewhere

The graphql-core unwrap loop appears at `extension.py:203-204` (`_walk_gql_type`) and `extension.py:250-251` (`_resolve_model_from_return_type`). It is *not* duplicated in `walker.py` / `plans.py` (those operate on Strawberry's `SelectedField` shape, not raw graphql-core types), so the duplication is local to `extension.py`. Defer to per-file follow-up: a tiny module-private `_unwrap_gql_type(t)` helper in `extension.py` collapses the two call sites; do not lift to a package-level utility because there is no second consumer.

```django_strawberry_framework/optimizer/extension.py:250:251
    while hasattr(rt, "of_type"):
        rt = rt.of_type
```

### `runtime_path_from_path` / `runtime_path_from_info` are pure path helpers misfiled in `plans.py`

Flagged in the per-file `plans.py` review; surfaced here because the candidate destination is in this folder. The helpers operate on `info.path` linked lists and do not touch `OptimizationPlan`. `extension.py:56` imports `runtime_path_from_info` for its plan-cache key construction; `walker.py:16` imports it for resolver-key prefix work. Moving them to `_context.py` (which already holds the `info.context` get/stash helpers — same axis of "request-scope state plumbing") would let `plans.py` shrink to the plan shape + diff helpers, and `_context.py` would absorb the second responsibility it already adjoins. Not a per-file defect; raise at the project pass if other path-shaped helpers surface.

```django_strawberry_framework/optimizer/plans.py:123:150
def runtime_path_from_info(info: Any | None) -> tuple[str, ...]:
    ...
def runtime_path_from_path(path: Any) -> tuple[str, ...]:
    ...
```

### Two `TODO(post-foundation)` anchors plus one `TODO(spec-fieldmeta-mirror-retirement)` cite the same retirement decision

`walker.py:64-68`, `walker.py:138-140`, and `field_meta.py:11-13` all describe the eventual removal of the `_optimizer_field_map`/`_optimizer_hints` class-attribute mirrors in favour of reading through `registry.get_definition(type_cls)`. The walker uses the label `TODO(post-foundation)`; `field_meta.py` uses the label `TODO(spec-fieldmeta-mirror-retirement)`. A future grep on either label returns only some of the anchored sites. Folder-level fix: pick one label (the `spec-…` form is the AGENTS.md-prescribed shape) and rename the two walker anchors to match in the same change that retires the mirrors. The single writer site at `types/base.py:147-148` should also carry the retirement anchor — currently it carries none, even though it is the canonical removal point.

```django_strawberry_framework/optimizer/walker.py:64:68
    # TODO(post-foundation): once the one-minor compatibility mirror from
    # ``DjangoTypeDefinition.field_map`` to ``type_cls._optimizer_field_map``
    # is removed, read through ``registry.get_definition(type_cls)`` here
    # instead of the legacy class attribute.
```

### `or {}` / `or ()` / `or default` defensive-coerce pattern recurs across the folder

Calibrated in the worker-1 memory entry for `conf.py`; subsequent per-file reviews flagged it in `extension.py:87`, `plans.py:204`, `walker.py:141`, and indirectly in `field_meta.py` ("loose `field: object` annotation"). The optimizer folder posture is currently inconsistent: some sites coerce `None`-attribute reads to empty containers, some let `AttributeError` surface, some intermix the two. Recommended posture (folder-level): for legacy mirror reads on `DjangoType` subclasses where the documented contract is "dict or absent", use `getattr(type_cls, name, None) or {}` — the walker pattern. For settings/consumer-supplied input (`conf.py`), prefer explicit `None` checks so consumer typos surface. The optimizer's wire-key reads through `_context.get_context_value(..., default)` already implement the right shape and are the model. Adopt this stance package-wide at the project pass.

### `__init__.py` re-export surface is correct but inverts the documented dependency direction

`optimizer/__init__.py:22` defines `logger = logging.getLogger("django_strawberry_framework")`; `extension.py:44` and `walker.py:14` do `from . import logger`. The module docstring explicitly justifies the placement ("the 'django_strawberry_framework' string only appears once in the subpackage"). The re-export contract is small and correct (`DjangoOptimizerExtension`, `logger`), and `OptimizationPlan` / `plan_optimizations` are correctly *not* re-exported. The `# noqa: E402` comment for the post-logger import is appropriate. One small concern: the package's top-level `django_strawberry_framework/__init__.py` also (presumably) declares a logger and the project-pass should confirm there is one canonical `getLogger("django_strawberry_framework")` line in the package — the optimizer subpackage's logger should re-export the package logger, not declare a parallel one. Project-pass follow-up.

```django_strawberry_framework/optimizer/__init__.py:22:25
logger = logging.getLogger("django_strawberry_framework")

from .extension import DjangoOptimizerExtension  # noqa: E402  # logger must exist before this import
```

## What looks solid

- Import direction inside the folder is strictly one-way: `extension.py` → `walker.py` → `{plans.py, hints.py, _context.py, field_meta.py}`; `field_meta.py` is leaf; `hints.py` and `plans.py` are siblings with no cross-import. No circulars introduced by per-file fixes during the cycle.
- Wire-key contract is correctly centralised: the five `DST_OPTIMIZER_*` constants live only in `_context.py:24-28`; `extension.py:46-50` and `types/resolvers.py:31-33` import them by name. No string-literal duplication across the optimiser subpackage for these keys.
- `hint_is_skip` centralisation contract is honoured after the per-file fixes — both `walker.py:295` and `extension.py:488` dispatch through the helper; no open-coded `hint is OptimizerHint.SKIP or hint.skip` remains in the folder.
- `convert_selections` lazy import in `extension.py` is the only Strawberry-internal coupling and is well-justified; the folder otherwise has no import-time Strawberry-internals dependency.
- Helper (`scripts/review_inspect.py`) was run on `__init__.py` per the folder-pass mandate; output is minimal (logger + one import) and matches the documented re-export contract.
- Per-file artifacts are consistent in calibration: "documented contract not enforced" calls came up in registry, plans, and (transitively) walker, all calibrated Medium with the same reasoning — silent state corruption rather than loud failure.

---

### Summary:

## Verification

PASS — no-source-change folder pass. Zero High. All three Mediums and five Lows are explicitly framed in their own bodies as cross-cutting refactors deferred to a later slice or to the project pass: Medium 1 (`_optimizer_hints` reader unification) routes to the `spec-fieldmeta-mirror-retirement` slice that retires the legacy mirrors; Medium 2 (`_optimizer_active` dead state) names a future delete-or-wire slice; Medium 3 (`OptimizationPlan.finalize()`) and Medium 4 (`_append_*` helper relocation) are explicitly paired as a single future slice; Lows 1, 2, 3, 4 are flagged as per-file follow-ups, project-pass follow-ups, or calibration. `uv run pytest tests/optimizer -q` → 240 passed (focused-run coverage gate trips harmlessly per AGENTS.md). Folder checkbox marked complete.

Cross-file findings cluster around three themes. First, an enforcement asymmetry around the `OptimizationPlan` mutation invariant: it is documented in `plans.py`, partially defended by `extension._publish_plan_to_context`'s copies, and load-bearing for the plan cache, but no caller is forced to honour it. Recommend a `finalize()` that swaps lists for tuples at walker exit. Second, the legacy `_optimizer_field_map` / `_optimizer_hints` mirrors are read by both `walker.py` and `extension.py` with subtly different shape-guard patterns and three differently-labelled retirement TODOs across three files; consolidating the readers (or retiring the mirrors entirely behind `registry.get_definition`) lands several findings in one slice. Third, `_optimizer_active` is dead state with no in-package reader — either delete or wire a `types/resolvers.py` consumer. Low-tier folder issues are placement: the three `_append_*` helpers in `walker.py` belong in `plans.py`, the `runtime_path_*` helpers in `plans.py` belong in `_context.py`, and the duplicated `of_type` peel in `extension.py` deserves a local `_unwrap_gql_type`. The `__init__.py` re-export contract is small and correct; the only project-pass follow-up is to confirm the package-level logger is the single `getLogger` site. The folder is well-scoped overall; no High severity, no circular imports, no cross-file bugs.
