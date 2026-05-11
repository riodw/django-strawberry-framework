# Review: `django_strawberry_framework/` (project-level pass)

Scope: package-wide patterns visible only after every per-file and folder pass is on disk. Sources read: all three folder artifacts (`rev-optimizer.md`, `rev-types.md`, `rev-utils.md`), `django_strawberry_framework/__init__.py`, the per-file artifacts they consolidate, and the cross-cutting greps for logger declarations, defensive-coerce sites, and `runtime_path_*` / `resolver_key` callers. Helper run on `django_strawberry_framework/__init__.py` per the project-pass rule for the top-level entry point; overview confirms four imports, zero symbols, zero hotspots, zero calls of interest, one TODO anchor, one repeated-literal-free re-export block.

The project pass does not duplicate per-file or folder findings; it consolidates the deferred items those artifacts explicitly routed forward, plus the genuinely package-wide concerns that only surface once every subpackage has been read.

## High:

None.

## Medium:

### Recovery / "documented contract, not enforced" theme needs a single package-wide owner

Every folder pass routes this question here. The pattern now spans seven sources:

- `registry.py` — `_finalized` flag documented as a guard, not enforced on mutators.
- `optimizer/plans.py` — `OptimizationPlan` documented as "treat as immutable after handoff", non-frozen `@dataclass` with mutable list fields, handed to the plan cache.
- `optimizer/walker.py` — hint-dispatch branches mutate the plan after the planner has handed it to the cache; `_append_*` helpers live next to `_lookup_path`'s consumer rather than next to the plan it mutates.
- `optimizer/extension.py` — `_publish_plan_to_context` defensively copies *two* plan fields into fresh sets, which is the only enforcement the invariant has today and is incomplete by design.
- `types/base.py` — non-atomic `registry.register` + `register_definition` pair; either call can raise and leave the other side stranded.
- `types/definition.py` — `DjangoTypeDefinition` is a non-frozen `@dataclass` with mutable `field_map` / `optimizer_hints` dicts and a `finalized: bool` slot that is the only recovery anchor.
- `types/finalizer.py` — Phase 2/3 are not failure-atomic; `definition.finalized = True` writes land before `registry.mark_finalized()`, so a Phase-3 raise on the Nth type leaves N-1 types flagged `finalized` and the registry as a whole not finalized.

Each per-file artifact proposed a local fix and the optimizer + types folder passes correctly collapsed those into "one owner needed". This project pass ratifies one of two shapes — they are exclusive and the choice is the deliverable:

1. **Registry-side state machine.** `TypeRegistry` owns the canonical state (`pending → attaching → finalized` per type plus a top-level `finalized` flag), and `registry.clear()` is the documented automatic recovery hook on any raise from `finalize_django_types`. `DjangoTypeDefinition` becomes `frozen=True` with `MappingProxyType` wrapping `field_map` / `optimizer_hints`, and `definition.finalized` is removed in favour of the registry-side state. `finalize_django_types` wraps Phases 1.5/2/3 in a single `try/except` that calls `registry.clear()` and re-raises.
2. **Plan-level finalize + per-call try/except.** `OptimizationPlan.finalize()` converts the four mutable list fields plus the two set-shaped fields to tuples / frozensets at walker exit; `extension._publish_plan_to_context`'s defensive copies become redundant. `types/base.DjangoType.__init_subclass__` wraps the `registry.register` + `register_definition` pair in a try/except that calls `registry.discard(meta.model)` (new) on failure. `types/finalizer` wraps Phases 1.5/2/3 in try/except calling `registry.clear()`.

Option 1 is the higher-leverage choice — it collapses five of the seven sources into one structural change (registry, definition, finalizer, base, plus the `discard_pending` consumer) — and leaves the optimizer-side `OptimizationPlan` mutation question as a separately-resolvable Medium under the optimizer folder pass. Test surface either way: a Phase-3 raise on the Nth type re-imports cleanly; a walker post-handoff mutation raises (tuple immutability) instead of silently poisoning the next request's cache hit.

```django_strawberry_framework/types/finalizer.py:60:88
for pending, target_type in resolved:
    pending.source_type.__annotations__[pending.field_name] = resolved_relation_annotation(...)
    resolved_pending.append(pending)
registry.discard_pending(resolved_pending)
for type_cls, definition in registry.iter_definitions():
    if definition.finalized:
        continue
    _attach_relation_resolvers(...)
for type_cls, definition in registry.iter_definitions():
    if definition.finalized:
        continue
    strawberry.type(type_cls, name=definition.name, description=definition.description)
    definition.finalized = True
registry.mark_finalized()
```

### `FieldMeta` is the documented single source of truth for relation shape, but three callers re-derive it via raw `getattr`

`optimizer/field_meta.py` is documented (and worker-memory-confirmed) as the SSoT for `is_relation` / `attname` / `target_model` / cardinality shape derivation. The optimizer reads it via `definition.field_map` (correctly). Outside that path the same shape is re-derived three times:

- `types/resolvers.py:163-175` — `_make_relation_resolver` reads `field.name`, calls `relation_kind(field)`, walks `getattr(field, "attname", None)` directly on the raw Django field rather than reading `definition.field_map[field_name]`.
- `types/converters.py` — `resolved_relation_annotation` reads `getattr(field, "null", False)` rather than the `FieldMeta.nullable` shape `field_meta.from_django_field` already computes.
- `types/base.py` — `_record_pending_relation` inlines `nullable=kind == "reverse_one_to_one" or bool(getattr(field, "null", False))` against the raw field, even though the same call site already has the `FieldMeta` it just built.

The optimizer folder pass and types folder pass both routed this here as the cross-folder SSoT question. Each re-derivation is independently correct today, but the package has four reader sites for the same shape across three folders, and the shape-guard pattern is inconsistent at each (some use `getattr(..., False)`, some use `getattr(..., None)`, some compare a `kind` string-literal at the call site). Recommended resolution: every consumer of "relation cardinality + nullable + attname" reads `FieldMeta` (or a small `FieldMeta.from_field_name(model, name)` helper if the consumer does not already have the `definition`). Project-pass deliverable is to name `FieldMeta` as canonical in `optimizer/field_meta.py`'s module docstring and add a folder-cross-reference TODO at each of the three re-derivation sites until they are migrated.

```django_strawberry_framework/types/resolvers.py:163:175
def _make_relation_resolver(field: models.Field, parent_type: type) -> Callable[..., Any]:
    field_name = field.name
    kind = relation_kind(field)
    ...
    attname = getattr(field, "attname", None)
```

### `_optimizer_field_map` / `_optimizer_hints` class-attribute mirrors are written from `types/` and read from `optimizer/` with no retirement anchor at the writer

The single writer site is `types/base.py:147-148`. The two readers are `optimizer/walker.py:154` (`_optimizer_hints`) and the indirect mirror reader in `optimizer/extension.py:483` (the optimizer folder pass flagged the shape-guard asymmetry between these two readers — the walker coerces `None`, the extension does not). Both reader sites carry retirement TODO anchors; the writer carries none. A future grep on the retirement spec name will find the readers and miss the writer — exactly the calibration the optimizer folder pass already noted.

Two pieces are coupled here and only show up at project pass:

1. The shape-guard asymmetry across the two readers (folder-Medium 1 of `rev-optimizer.md`) is downstream of the mirror existing at all. Retiring the mirror in favour of `registry.get_definition(type_cls).field_map` / `.optimizer_hints` eliminates both readers and makes the asymmetry moot.
2. The retirement is also coupled to the recovery-contract Medium above — if `DjangoTypeDefinition` becomes `frozen=True` with `MappingProxyType` field-map slots, the optimizer's read path needs to land in the same change because the mirror is currently the *only* shape that supports `dict.get(field_name)`-style optional reads. The frozen-definition change must preserve that ergonomics.

Project-pass deliverable: either (a) drop the mirror writes at `types/base.py:147-148` in the same change that updates the two optimizer reader sites to read `definition.field_map` / `definition.optimizer_hints`, or (b) — at minimum, before that slice — add the matching `TODO(spec-fieldmeta-mirror-retirement)` anchor at the writer so the slice author finds it.

```django_strawberry_framework/types/base.py:140:150
        registry.register(meta.model, cls)
        registry.register_definition(cls, definition)
        for pending_relation in pending:
            registry.add_pending_relation(pending_relation)

        cls._optimizer_field_map = field_map
        cls._optimizer_hints = optimizer_hints_dict
```

### `runtime_path_*` / `resolver_key` placement now has a confirmed cross-folder caller

`optimizer/plans.py:135` defines `resolver_key`, `:147` defines `runtime_path_from_info`, `:160` defines `runtime_path_from_path`. The optimizer-folder Low flagged these as misfiled in `plans.py` and routed the project pass to confirm whether other folders consumed them. They do: `types/resolvers.py:39` imports both `resolver_key` and `runtime_path_from_info` from `optimizer.plans` and calls them at `:57` and `:128`. That cross-folder import is fine architecturally (resolvers depends on optimizer; optimizer does not depend on types), but it reinforces the placement question — these helpers are about `info.path` shape and resolver identity, not about the `OptimizationPlan` shape. Two viable homes:

- `optimizer/_context.py` — already the home for the `info.context` get/stash helpers, which are the closest sibling concept ("request-scope state plumbing").
- A new `optimizer/keys.py` — if `resolver_key` and the `runtime_path_*` pair grow more callers in the relay / connection-field slices.

Either way the resolution is "out of `plans.py`" so `plans.py` shrinks to plan shape + diff helpers (matching the folder-pass narrative of `plans.py` as the single owner of plan-shape invariants). Defer the move to the same slice that retires the legacy mirrors or to the relay slice, whichever lands first; do not split into a third change.

```django_strawberry_framework/types/resolvers.py:39:39
from ..optimizer.plans import resolver_key, runtime_path_from_info
```

## Low:

### `or {}` / `or ()` / `or []` / `or set()` defensive-coerce posture is now established across the package — ratify a single stance

Distribution from the project-wide grep is now concrete:

- `conf.py:48` — settings dict (consumer-supplied input)
- `types/base.py:255-259` — `_meta_optimizer_hints` legacy mirror read
- `types/converters.py:172` — Django `field.choices` coerce
- `optimizer/walker.py:154, 468, 496, 507, 522-524` — six sites, all reading reflective attributes off `SelectedField`-shaped objects
- `optimizer/plans.py:259` — queryset prefetch lookups read
- `optimizer/extension.py:86, 109, 115, 121, 550` — fragment / directive / argument / selection / `variable_values` reads

Two distinct concerns hide inside the same syntactic pattern:

1. **Consumer-supplied input** (`conf.py:48`, `types/base.py:259`) — coercing `None` to `{}` here silently swallows misconfiguration (`Meta.optimizer_hints = None` becomes "no hints" rather than "you passed the wrong thing"). The package-wide stance for consumer input should be explicit `None` check + raise (or at least log at warn level via the canonical logger).
2. **Strawberry / graphql-core / Django reflective shape reads** (the optimizer-folder sites) — coercing here is correct because the upstream contract genuinely allows the attribute to be absent or `None` on legitimate shapes (e.g., `SelectedField.directives`). The walker pattern (`getattr(obj, name, None) or {}`) is the right shape and should be applied consistently — the inconsistency the optimizer-folder pass flagged (`extension.py:483` does not coerce; `walker.py:154` does) is the bug, not the coerce itself.

Folder-level recommendation (deferred from optimizer folder pass): adopt the walker pattern across all reflective shape reads, and gate consumer input on explicit `None` so typos surface. The two cases were conflated in worker memory; the project-pass resolution is to split them. No source change this cycle; the deliverable is one comment block (likely in `conf.py` and `optimizer/_context.py` module docstrings) recording the stance.

### Subpackage `__init__.py` re-export contracts use three different shapes

The three subpackage entry points have drifted into three different conventions:

- `optimizer/__init__.py:22` — declares a package-level logger (`logging.getLogger("django_strawberry_framework")`) and re-exports `DjangoOptimizerExtension`. The grep confirms this is the *only* `getLogger` site in the entire package; `types/` and `utils/` and the top-level `__init__.py` do not declare loggers. Worker-memory carry-forward asked whether the top-level package should own the logger declaration so the subpackage merely re-exports; the answer is yes — the canonical `getLogger("django_strawberry_framework")` line should live at `django_strawberry_framework/__init__.py` and `optimizer/__init__.py` should `from .. import logger`. This is a small move but it makes the logger declaration line up with the package name, eliminates the comment block at `optimizer/__init__.py` justifying the placement, and lets future subpackages (filters, orders, aggregates) get the logger without redeclaring it.
- `types/__init__.py` — re-exports `DjangoType` and `finalize_django_types`, `__all__` is tight, docstring is sparse. No internal helpers (`PendingRelationAnnotation`, `PendingRelation`, `DjangoTypeDefinition`, `FieldMeta`, `OptimizerHint`) are re-exported. This is the right shape.
- `utils/__init__.py` — re-exports `pascal_case`, `snake_case`, `unwrap_return_type`, and (after the utils folder fix) `relation_kind`, `RelationKind`. Docstring lists every submodule. This is now the right shape post-fix.

Project-pass deliverable: standardise on the `utils/__init__.py` post-fix shape (docstring lists submodules + `__all__` matches the public surface), confirm the top-level `__init__.py` owns the canonical logger declaration, and the `optimizer/__init__.py` becomes a thin re-export shim.

```django_strawberry_framework/optimizer/__init__.py:22:25
logger = logging.getLogger("django_strawberry_framework")

from .extension import DjangoOptimizerExtension  # noqa: E402  # logger must exist before this import
```

### `__init__.py` top-level surface is tight; the relay TODO needs to enumerate the no-change promise more concretely

`django_strawberry_framework/__init__.py:14-25` is the package's full public-API surface: `DjangoOptimizerExtension`, `DjangoType`, `OptimizerHint`, `auto`, `finalize_django_types`, `__version__`. The `auto` re-export is correctly justified inline. The relay TODO anchor at line 15-16 says "ship Relay interfaces without adding public exports; only the version changes." — that promise is correct, but the project-pass observation is that the relay slice will also add `__version__ = "0.0.5"` and bump `pyproject.toml`'s version per AGENTS.md "Versioning" rule. The TODO already names the spec; consider adding to the TODO line that the version bump is the only line that changes in this file, so a future maintainer running `git diff` on `__init__.py` after the relay slice can confirm no exports leaked. Trivial polish; project-pass surface-area note.

### Logger name string `"django_strawberry_framework"` is declared once in the package — good, but no test pins it

The string `"django_strawberry_framework"` as a logger name appears only at `optimizer/__init__.py:22`. The package has no test that asserts the logger name is what consumers expect to configure in their Django `LOGGING` dict. If the string drifts (e.g., to `"django-strawberry-framework"` or `"djsf"`), no test catches it. Low-tier project-pass test gap: a single test in `tests/base/test_init.py` (frozen scope per AGENTS.md is fine — `test_init.py` is one of the two allowed files there and can grow) asserting `logger.name == "django_strawberry_framework"` would pin the consumer-visible string. Defer to the same change that lands the logger relocation to the top-level `__init__.py`.

### Recurring bug class to record for the retrospective: "shape-guard asymmetry across reader sites"

Worker memory now records the same calibration in six files (`optimizer/field_meta.py`, `optimizer/walker.py`, `optimizer/extension.py`, `types/converters.py`, `types/resolvers.py`, `utils/relations.py`). The pattern: two or more reader sites consume the same reflective attribute through `getattr(obj, name, default)` with different defaults or different shape guards. Symptom is silent divergence — same input produces different downstream behaviour depending on which reader was hit first. The `utils/relations.py` fix (`_RelationFieldLike` Protocol + `@runtime_checkable`) is the reference shape and lands the right pattern: when the package has more than one reader of a reflective attribute, declare the shape via Protocol and let the Protocol be the contract. The recurring-bug-class entry for the closeout retrospective should name this explicitly so the next release's review run scans for it from the start rather than discovering it incrementally.

## Test gaps surfaced at project scope

- **Logger name pinning** — see Low #4 above.
- **Plan-cache mutation guard** — once `OptimizationPlan.finalize()` lands, a test asserting `plan.prefetch_related.append(...)` raises `TypeError` (tuple immutability) is the right shape for proving the contract is now enforced.
- **Recovery contract** — once the registry-side state machine (or wrapped try/except in finalizer) lands, a test that injects a Phase-3 raise on the Nth type and asserts a subsequent `finalize_django_types()` call rebuilds cleanly is the right shape.
- **`__init__.py` re-export surface** — `tests/base/test_init.py` already pins the package version. A companion test pinning `set(django_strawberry_framework.__all__) == {...}` would catch silent surface widening (e.g., an accidental `OptimizerHint` rename). Worker memory routes through `tests/base/` frozen-scope rule; both `test_init.py` and `test_conf.py` may grow, so this is in-scope.

## Deferred items consolidated from folder passes

These are the explicit "route to project pass" items from the three folder artifacts. None require source changes in this cycle; they are recorded here so the closeout retrospective and the next release's review run have one place to read them from.

1. **From `rev-optimizer.md`:**
   - `_optimizer_active` ContextVar has no in-package reader — delete or wire a consumer (folder Medium 2).
   - `OptimizationPlan.finalize()` and `_append_*` helper relocation paired as one slice (folder Mediums 3 + 4).
   - `_unwrap_gql_type` local helper for the two `of_type` peels in `extension.py` (folder Low 1).
   - `runtime_path_*` placement question — confirmed via the cross-folder caller above (folder Low 2).
   - Three differently-labelled mirror-retirement TODOs to converge on `TODO(spec-fieldmeta-mirror-retirement)` and add to the writer site (folder Low 3).
   - Top-level logger placement question — answered above under Low #2 (folder Low 5).

2. **From `rev-types.md`:**
   - Recovery contract single-owner — answered above under Medium #1 (folder Medium 1).
   - Mirror writer TODO anchor — answered above under Medium #3 (folder Medium 2).
   - Consumer-surface `Meta.*` error string split across `base.py` / `finalizer.py` — either move both to a shared `_errors.py` or add a sibling-pointer comment (folder Medium 3). Project-pass position: defer to the relay slice, where Phase 2.5 lands and the loop consolidation happens; the same change can host the error-string move.
   - `FieldMeta` SSoT across resolvers/converters/base — answered above under Medium #2 (folder Medium 4).
   - `or {}` posture — answered above under Low #1 (folder Low 1).
   - 14 relay TODO anchors across 6 files — one slice-author checklist, no project-pass action (folder Low 2).
   - Triple `iter_definitions` loop in `finalizer.py` — coupled to recovery-contract decision (folder Low 3).
   - Reverse-O2O nullable rule belongs in `utils/relations.py` — defer to next utils-folder slice (folder Low 4).

3. **From `rev-utils.md`:**
   - Shape-guard-asymmetry stance — answered above under Low #5 as a recurring-bug-class (folder Low 1).
   - `unwrap_return_type` naming question — defer to the slice that lands the second named consumer (folder Low 2).
   - Soft `queryset` future-submodule prose — confirm uniform across all `__init__.py` files; the project-pass position is "soft prose without anchor is acceptable when no design doc exists" (folder Low 3).
   - Standing `tests/utils/test_<submodule>.py` per-branch convention — adopted (folder Low 4).

## What looks solid

- **Public-API surface is tight.** The top-level `__init__.py` re-exports six names; helper run confirms zero symbols, zero hotspots, zero calls of interest, one TODO anchor that correctly anchors a future slice and names the spec. No surface bleed from internals — `PendingRelation`, `DjangoTypeDefinition`, `FieldMeta`, `OptimizationPlan`, internal converters, internal resolvers are all reachable only via dotted submodule paths.
- **Dependency direction across the package is one-way and clean.** `utils/` is leaf; `optimizer/` depends on `utils/`; `types/` depends on `optimizer/` and `utils/`; the top-level `__init__.py` depends on `optimizer/` and `types/`. No back-edges observed in any folder pass. The `types/` folder docstring's promise that "optimizer must not import back from `types/`" is honoured (verified across both folder passes).
- **Wire-key contract is centralised.** The five `DST_OPTIMIZER_*` keys live only in `optimizer/_context.py:24-28`; every consumer imports by name. No string-literal duplication across the optimizer or its cross-folder caller in `types/resolvers.py`.
- **`hint_is_skip` centralisation contract is honoured** after the per-file fixes — both walker and extension dispatch through the helper; no open-coded skip checks remain.
- **Logger name is single-sourced** at `optimizer/__init__.py:22` (one `getLogger` site in the whole package). The placement is the right principle; only the location (subpackage vs top-level) is the Low note above.
- **`__version__` versioning rule is honoured.** `__init__.py:14` and `pyproject.toml`'s `[project].version` both read `0.0.4`; the relay-slice TODO at line 15 explicitly notes the next version bump.
- **Per-branch named test conventions are now consistent** across `tests/utils/test_<submodule>.py` (relations, strings, typing) and the type folder is moving toward the same shape (per the resolvers folder-pass carry-forward).
- **`auto` re-export from Strawberry is correctly justified inline** at `__init__.py:6-8` — the DRF-shaped public-surface rationale matches the AGENTS.md "DRF first, strawberry second" guidance and prevents consumers from importing `strawberry` directly.
- **No circular-import risk anywhere in the package** after every per-file and folder fix landed in the cycle. Folder-pass import sweeps for `optimizer/` and `types/` both confirm one-way edges; the project-pass sweep against `utils/` and the top-level `__init__.py` finds the same.

---

### Summary:

Four Mediums and five Lows at project scope. The Mediums are all consolidation issues whose folder-pass artifacts explicitly routed forward: (1) the package-wide "documented contract, not enforced" recovery-semantics question spans seven sources and needs a single owner — recommend the registry-side state machine + frozen-definition shape, with `registry.clear()` as the automatic recovery hook called from a wrapping try/except in `finalize_django_types`; (2) `FieldMeta` is documented as the relation-shape SSoT but three callers (`types/resolvers.py`, `types/converters.py`, `types/base.py`) re-derive the same shape via raw `getattr` — name `FieldMeta` as canonical in the module docstring and add cross-folder TODO anchors at the re-derivation sites; (3) the `_optimizer_field_map` / `_optimizer_hints` mirror writer in `types/base.py` lacks the retirement TODO anchor that the two optimizer readers cite — drop the mirror entirely and have the optimizer read `DjangoTypeDefinition` directly, paired with the recovery-contract change; (4) `runtime_path_*` / `resolver_key` placement in `optimizer/plans.py` is now confirmed misfiled because `types/resolvers.py` is a cross-folder caller — move to `optimizer/_context.py` (preferred) or a new `optimizer/keys.py`.

Lows: ratify the `or {}` defensive-coerce stance by splitting "consumer-supplied input" (raise on misconfig) from "reflective shape read" (coerce per walker pattern); relocate the canonical logger declaration to the top-level `__init__.py` and have `optimizer/__init__.py` re-export it; refine the relay TODO at the top-level `__init__.py` to enumerate the no-export promise concretely; pin the logger name in `tests/base/test_init.py`; record "shape-guard asymmetry across reader sites" as the recurring bug class for the closeout retrospective.

The top-level `__init__.py` re-export contract is tight and correct; the package's public-API surface is six names with no internal bleed. Dependency direction is one-way across the four subpackage layers; no circular-import risk; wire-key and `hint_is_skip` contracts are centralised. The deferred-items consolidation above is the project pass's single-source-of-truth handoff to the closeout retrospective and to the next release's review run.

## Verification

PASS — 2026-05-11 — project-level pass.

Worker 2 implemented the small project-pass deliverables that ship in this cycle (logger relocation to top-level `__init__.py` with `optimizer/__init__.py` re-export, refined relay TODO at the top-level, and the matching pin in `tests/base/test_init.py`) and explicitly deferred the larger Mediums (recovery-contract single owner, `FieldMeta` SSoT migration across three callers, `_optimizer_field_map` / `_optimizer_hints` mirror retirement, `runtime_path_*` / `resolver_key` relocation) to future slices, matching every "route forward" framing in the artifact body. The diff scope stays within the project-pass remit: top-level `__init__.py`, `optimizer/__init__.py`, and the test pin.

`uv run pytest tests/ -q --no-cov` → 387 passed, 1 skipped (2 unrelated Django model-reload warnings on `test_convert_scalar_*` already covered by the `types/converters.py` cycle).

Outstanding checklist items (`optimizer/field_meta.py`, `optimizer/` folder pass) are pre-existing unticked boxes from earlier cycles, out of scope for the project-pass verification.
