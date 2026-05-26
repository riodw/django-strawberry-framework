# Review: `django_strawberry_framework/` (project-level pass)

Status: verified

Project scope: the top-level `django_strawberry_framework/__init__.py` (covered here per `REVIEW.md` "Review scope") plus package-wide DRY / structure / responsibility / cross-cutting findings consolidated from the 31 verified per-file and folder-pass artifacts (`rev-_django_patches.md` through `rev-utils.md`). Shadow overview for the top-level `__init__.py`: `docs/shadow/django_strawberry_framework____init__.overview.md`.

## DRY analysis

- **Carry-forward (canonical resolution home: `rev-django_strawberry_framework.md`): rewrite `docs/GLOSSARY.md:462` to name BOTH FK-id elision introspection surfaces.** Three optimizer-internal artifacts (`rev-optimizer___context.md:21`, `rev-optimizer__extension.md:20-36`, `rev-optimizer__walker.md:138-144`) independently surfaced the same doc-vs-code drift on the FK-id elision introspection contract; the folder pass `rev-optimizer.md:28-38` promoted it to a single folder Low and forwarded to the project pass with the recommended replacement text verbatim. Recommended replacement text (Worker 1-authored, lifted verbatim from `rev-optimizer__extension.md:34` and re-pinned at `rev-optimizer.md:38`): `"FK-id elisions are stashed on info.context.dst_optimizer_plan.fk_id_elisions (tuple, as part of the plan) and info.context.dst_optimizer_fk_id_elisions (standalone set, for resolver-time membership checks)."` Act-now at the project-pass scope — this artifact IS the trigger condition all three per-file forwards quoted verbatim (`"when rev-django_strawberry_framework.md is written; consolidate the GLOSSARY:462 fix at the project pass alongside any other doc-surface drift the project pass surfaces"`). Treated as a Low finding below (see `## Low` → "GLOSSARY drift on the FK-id elision introspection contract").
- **Project-pass restatement of seven trigger-gated optimizer DRY carry-forwards.** Per `rev-optimizer.md:9-16`, the optimizer folder pass enumerated seven trigger-gated DRY bullets (`_resolve_origin_for_type_name`; `_walk_selection_tree`; `_walk_relation_target`; `has_custom_get_queryset` flag-threading across `plan_relation`; `RelationPlanCtx` dataclass; `FieldMeta._from_field_like` cross-folder hoist; the three `plans.py`-local centralizers). All seven carry verbatim grep-discoverable trigger conditions in `rev-optimizer.md:9-16` and again in Worker 2's bullet-by-bullet restatement at `rev-optimizer.md:119-125`. No project-pass-level consolidation candidate — every trigger is intra-folder or single-cross-folder (`FieldMeta._from_field_like`). Recording here so the next DRY cycle has one project-pass grep landing point for "every trigger-gated DRY bullet still live in 0.0.7."
- **Project-pass restatement of three `types/`-folder trigger-gated DRY carry-forwards.** Per `rev-types.md` (folder pass): (a) `_initial_queryset` cross-module promotion deferred-with-trigger (canonical home is a future `types/_queryset.py`); (b) `FieldMeta._from_field_like` hoist (cross-folder, canonical home `optimizer/field_meta.py`); (c) the `_format_*_error` finalize-time sibling-formatter convention recap (no act-now; sibling phrasing pinned). All three are routed to their canonical resolution homes; the project-pass restatement is inventory-only.
- **Project-pass restatement of three `utils/`-folder trigger-gated DRY carry-forwards.** Per `rev-utils.md`: (a) `unwrap_return_type` re-export ahead of its first in-package consumer (the upcoming schema-factory); (b) "single-trigger × three actions" record for the schema-factory consumer fanout in `utils/typing.py` (Optional/Union peel decision + `unwrap_return_type` first call site + third-unwrap-helper hoist); (c) `_check_n1` `kind: str | None` widening vs `is_many_side_relation_kind(RelationKind | None)` carrying the second-consumer trigger from `rev-utils__relations.md`. All three are intra-folder; no project-pass act-now candidate.
- **None — the four leaf surfaces (`registry.py`, `scalars.py`, `conf.py`, `utils/*`) are canonical-home modules.** The package's DRY backbone is the canonical-home framing across these four leaf surfaces: each is the single source of truth for its concern (registry indirection, BigInt scalar, settings reader, string/relation/typing helpers). The four-cycle utils chain (cycles 28-31, all consolidated single-spawn no-ops per `worker-memory/worker-1.md:53`) is the strongest argument that the package's leaf-canonical-home framing is intact. No new module ought to be a leaf-canonical-home but isn't.

## High:

None.

## Medium:

None.

## Low:

### GLOSSARY drift on the FK-id elision introspection contract — act-now at the project-pass scope

`docs/GLOSSARY.md:462` currently reads `"FK-id elisions are stashed on info.context.dst_optimizer_plan for introspection."` This under-describes the optimizer subsystem's actual introspection contract, which exposes the elision set on **two** independent context keys:

- `info.context.dst_optimizer_plan.fk_id_elisions` — `tuple[str, ...]`, attached to the plan instance (per `django_strawberry_framework/optimizer/plans.py:68-69,118`).
- `info.context.dst_optimizer_fk_id_elisions` — `set[str]`, populated from the same tuple but exposed for direct lookup at resolver time (consumed by `django_strawberry_framework/types/resolvers.py:36,63`; pinned by `tests/optimizer/test_extension.py:325-326,369-371,1430`).

Both surfaces are public introspection contracts. `_publish_plan_to_context` writes both at `django_strawberry_framework/optimizer/extension.py:671-672`:

```django_strawberry_framework/optimizer/extension.py:671:672
_stash_on_context(info.context, DST_OPTIMIZER_PLAN, plan)
_stash_on_context(info.context, DST_OPTIMIZER_FK_ID_ELISIONS, set(plan.fk_id_elisions))
```

Cross-folder cite-chain (so a future cycle can re-derive without re-reading every per-file artifact): `rev-optimizer___context.md:21` (the `DST_OPTIMIZER_*` write-only constants framing), `rev-optimizer__extension.md:20-36` (the original surface flagged by Worker 1), `rev-optimizer__walker.md:138-144` (walker-side restatement so the optimizer folder pass would see the drift), `rev-optimizer.md:28-38` (folder-pass promotion + forward to project pass).

Recommended change (doc-only, no source edit): replace `docs/GLOSSARY.md:462` with the verbatim wording lifted from `rev-optimizer__extension.md:34` / `rev-optimizer.md:38`:

> `"FK-id elisions are stashed on info.context.dst_optimizer_plan.fk_id_elisions (tuple, as part of the plan) and info.context.dst_optimizer_fk_id_elisions (standalone set, for resolver-time membership checks)."`

Severity Low because the source code is correct, the test pins are correct, and the fix surface is doc text not consumer-facing source. The drift's risk is a future consumer reading the GLOSSARY as the spec and never discovering the standalone set surface — they would read the plan attribute (slow tuple membership) instead of the set (fast `O(1)` lookup) and only notice via performance debugging.

### `docs/GLOSSARY.md:984` "Planned resolver keys and lookup paths are stashed on `info.context`" omits the standalone context-key names

`docs/GLOSSARY.md:984` reads `"Planned resolver keys and lookup paths are stashed on info.context for introspection during strictness incidents."` This describes the strictness-stash contract at the right granularity for the strictness narrative, but it does not name the two specific context attributes consumers grep against: `info.context.dst_optimizer_planned` (the planned-resolver-keys set, written at `extension.py:677-678`) and `info.context.dst_optimizer_lookup_paths` (the lookup-paths tuple, written at `extension.py:679-680`). The first is consumed at `types/resolvers.py:138`; the second is currently write-only (per the trigger-gated Low at `rev-optimizer___context.md:21`).

Defer-with-trigger: act when a second consumer of either constant lands inside the package (per `rev-optimizer___context.md:23`'s verbatim trigger), at which point the GLOSSARY line graduates to name both attributes alongside the elision-set update from the Low above. Until then the current wording is conservative-but-correct, the strictness-incident user-facing log message (per `tests/optimizer/test_extension.py:1430+`) names the right attributes by inspection of the actual context shape, and a docstring patch at this scale would force premature consolidation against an introspection surface whose second-consumer shape is still latent.

Severity Low — forward-looking; not act-now.

### Top-level `__init__.py:18` `# noqa: E402` comment is partially misleading

`django_strawberry_framework/__init__.py:18` carries `from strawberry import auto  # noqa: E402  # logger must exist before subpackage imports`. The trailing `# logger must exist before subpackage imports` comment is correct for the next five subpackage imports at lines 20-24 (each of which transitively imports the logger via `from .. import logger` and would crash if the logger weren't yet declared), but it is misleading on this specific line because `from strawberry import auto` does not depend on the package logger — it's the only non-local import in the block and only needs `E402` because of the docstring-and-module-logger preamble. The five subsequent `# noqa: E402` lines (20-24) carry no rationale comment despite being the actual reason the rationale exists.

Recommended change (cosmetic-only, comment polish): either (a) move the `# logger must exist before subpackage imports` rationale to a single comment block above the import group, OR (b) attach the rationale to the first local-import line (line 20, `from .list_field import DjangoListField`) where the dependency is genuine. The current placement attaches the rationale to the only import in the block that does not need it.

Severity Low because the actual code (`noqa: E402` on every import after the logger) is correct; the misleading comment is documentation-grade. Defer-with-trigger: act on the next touch to `__init__.py` that updates the import block (e.g. a 0.1.x slice landing a new top-level export); rewrite the rationale at the same time to avoid a comment-only churn cycle.

### `__all__` membership ordering and consistency

`django_strawberry_framework/__init__.py:28-37` declares `__all__` as an alphabetized tuple:

```django_strawberry_framework/__init__.py:28:37
__all__ = (
    "BigInt",
    "DjangoListField",
    "DjangoOptimizerExtension",
    "DjangoType",
    "OptimizerHint",
    "__version__",
    "auto",
    "finalize_django_types",
)
```

The alphabetization is mostly clean, with one nit: `__version__` sorts between `OptimizerHint` and `auto` only because Python's default string comparison places `_` (0x5F) between uppercase letters (0x41-0x5A) and lowercase letters (0x61-0x7A) — strictly correct lexicographic ordering, but reads oddly to a human scanner expecting `__version__` to live at the top or bottom of the tuple (the conventional placement for the dunder member). The current ordering does not violate any package rule; it is grep-discoverable; and `__version__` is already excluded from `logger` (which is NOT in `__all__` per the comment at `__init__.py:13-15` because consumers reach it via attribute access by name, not via star-import).

Severity Low — forward-looking style nit. Defer-with-trigger: act if a future cycle adds a second dunder (`__author__`, `__url__`, etc.) — at that point the dunder group convention becomes worth establishing.

### `logger` is in the public surface but not in `__all__` — the rationale is correct but trips static-analysis tooling

`django_strawberry_framework/__init__.py:13-15` documents that `logger` is "part of the public surface even though it is not in `__all__`" because consumers reach it via the logger-name string `"django_strawberry_framework"` in Django's `LOGGING` config dict, not via Python `from django_strawberry_framework import logger`. This is correct — Django logging configuration uses the dotted logger name, not the symbol — but the framing "part of the public surface even though it is not in `__all__`" trips two classes of static-analysis tool:

- Linters that flag "name referenced from outside the module but not in `__all__`" (e.g. some Pyright configurations).
- Documentation generators (Sphinx, pdoc) that filter top-level symbols by `__all__` membership and would silently omit `logger` from the consumer-facing docs.

Both are tooling-level concerns, not source defects. The comment at `__init__.py:10-15` carries the rationale clearly, so a future maintainer reading the source will not be misled. Defer-with-trigger: act if Sphinx / pdoc is wired into the package's doc build AND `logger` is missing from the rendered output — at that point the right fix is either to add `logger` to `__all__` (and update the comment) OR to add an explicit `:exclude-members:` / `:noindex:` directive in the doc-config. Both are valid; the comment-only state is correct today.

Severity Low — forward-looking; gated on a future doc-build slice landing.

### Cross-module `None`-stance assertion in `conf.py` module docstring — confirm-invariant disposition

`django_strawberry_framework/conf.py:17-35` carries a package-wide `None`-stance contract: `"Two top-level consumer-input seams coerce None ... DJANGO_STRAWBERRY_FRAMEWORK = None (this module ...) and Meta.optimizer_hints = None in types/base.py ..."`. The 0.0.6 cycle flagged this as a cross-module assertion the local file cannot enforce; the 0.0.7 cycle re-flagged it at `rev-conf.md:25` and forwarded to the project pass for re-confirmation.

Re-confirmed: both seams still coerce `None` to an empty mapping at 0.0.7:

- `django_strawberry_framework/conf.py:50+` (`_normalize_user_settings`) accepts `None` (via the `value is None` branch) and returns `{}` — Worker 3 verified this in the cycle-3 verification per `rev-conf.md:140`.
- `django_strawberry_framework/types/base.py:390-392` (`_meta_optimizer_hints`) reads `value = getattr(meta, "optimizer_hints", None)` and returns `{}` for `None`.

The cross-module invariant holds at 0.0.7. The project pass's per-`rev-conf.md:25` carry-forward instruction was: `"if the 0.0.7 project pass declines to relocate, restate as 'intentional duplication' so the next review cycle is not asked to re-litigate."`

Project-pass disposition: **intentional duplication**. The `conf.py` module docstring is the canonical narrative site for the cross-module `None`-stance because (a) `conf.py` is the file consumers read first when wiring `DJANGO_STRAWBERRY_FRAMEWORK` into Django settings, so the cross-seam reminder belongs adjacent to the first seam they encounter; (b) relocating the prose to `AGENTS.md` would split the load-bearing rationale from the source code; (c) relocating to `docs/GLOSSARY.md` would obscure the file-local-rationale shape the GLOSSARY is not designed to carry; (d) duplicating the bullet across `conf.py` and `types/base.py` would force two-site update on every drift — strictly worse than the current single-site narrative at `conf.py:17-35` referencing the `types/base.py` seam by name. The current factoring is the highest-quality shape. Next cycle (`rev-conf.md` under 0.0.8 if any) should not re-flag this as a finding; the disposition is closed as "intentional duplication, canonical narrative site is `conf.py`."

Severity Low — restatement-of-decision only; no source edit; no test edit; closing carry-forward.

## What looks solid

### DRY recap

- **Existing patterns reused at the package scale.** The package's DRY backbone is the canonical-home framing across four leaf surfaces: `registry.py` (the `Registry` singleton + the `model_for_type` / `get` / `get_definition` / `iter_types` indirection layer); `scalars.py` (the `BigInt` Strawberry scalar definition); `conf.py` (the `settings` singleton + `_normalize_user_settings`); and `utils/*` (the three leaf modules `relations`, `strings`, `typing`). Each is the single source of truth for its concern, with multi-consumer fan-in already mapped per-file (e.g. `utils/strings.snake_case` consumed at 5 call sites across `optimizer/walker.py` + `types/base.py` + `types/finalizer.py` per `rev-utils__strings.md`). The four-cycle utils chain (cycles 28-31, all consolidated single-spawn no-ops per `worker-memory/worker-1.md:53`) confirms the leaf surfaces are mature canonical homes that do not need further consolidation at 0.0.7.
- **Shared helper sites are correctly leveled across folders.** Optimizer subsystem internals (sentinel keys at `optimizer/_context.py`; plan-shape helpers at `optimizer/plans.py`; hint dispatch at `optimizer/hints.py`) live where they belong per `rev-optimizer.md:74-82`. Relation classification (`RelationKind` / `relation_kind` / `is_many_side_relation_kind` at `utils/relations.py`) is consumed by both `optimizer/` (walker + field_meta) and `types/` (relations + resolvers) without bidirectional cross-folder reach — utils is leaf, optimizer and types fan in. The two `__init__.py` re-export hubs (`optimizer/__init__.py` re-publishing `logger` + `DjangoOptimizerExtension`; `utils/__init__.py` re-publishing seven helper symbols) are consistent with their per-folder docstrings (per `rev-optimizer.md:40-49` and `rev-utils.md`).
- **New helpers considered at the project scale.** Every trigger-gated DRY bullet in this artifact was considered for act-now promotion and explicitly deferred — the seven optimizer carry-forwards, three types carry-forwards, three utils carry-forwards. The project-pass-scope grep landing point lives in `## DRY analysis` above so a future cycle has one file to grep instead of 13 separate per-file/folder artifacts. The only act-now project-pass edit candidate is the GLOSSARY:462 doc-text fix (recorded as a Low below, not as a DRY-analysis bullet, because the fix surface is doc text not source code).
- **Duplication risk at the package scale.** Cross-folder repeated-literal scan (per shadow overview Quick scans for every `.py` in `django_strawberry_framework/`) returns ZERO literals appearing in two or more files at the package scale beyond:
  - `"django_strawberry_framework"` — appears once at `__init__.py:16` (the logger name) and that's the only declaration; subpackages reach it via `from .. import logger` (per `optimizer/__init__.py:20`) — the literal is correctly NOT duplicated.
  - `"DJANGO_STRAWBERRY_FRAMEWORK"` — appears once at `conf.py:46` as `DJANGO_SETTINGS_KEY`; consumers reach it via the module constant, not the bare literal.
  - `"dst_optimizer_*"` sentinel keys — each appears exactly once in `optimizer/_context.py:34-38` as a module constant; every consumer imports the constant (per `rev-optimizer.md:76`).
  - Module docstring framings ("Re-exports …", "Shared … helpers", etc.) — intentional sibling phrasing across `__init__.py` files; per-folder pass verified the framings are coherent without duplicating logic.
  - The "DJANGO_STRAWBERRY_FRAMEWORK = None" / "Meta.optimizer_hints = None" cross-module assertion in `conf.py:17-35` (covered as "intentional duplication" in the Lows above).

### Other positives

- **Public API surface is minimal and intentional.** `django_strawberry_framework/__init__.py:28-37` exposes exactly eight names (`BigInt`, `DjangoListField`, `DjangoOptimizerExtension`, `DjangoType`, `OptimizerHint`, `__version__`, `auto`, `finalize_django_types`) plus `logger` (public-via-Django-LOGGING-name, intentionally not in `__all__` per `__init__.py:13-15`). Each top-level export has a documented consumer-facing role:
  - `DjangoType` — the consumer's Meta-class-driven model adapter (per `types/base.py:1-26`).
  - `finalize_django_types` — the consumer's deferred-relation resolution entry point (per `types/finalizer.py`).
  - `DjangoOptimizerExtension` — the consumer's N+1-prevention `SchemaExtension` (per `optimizer/extension.py`).
  - `OptimizerHint` — the consumer's typed hint shape (per `optimizer/hints.py`).
  - `DjangoListField` — the consumer's queryset-resolving list field factory (per `list_field.py`).
  - `BigInt` — the consumer's 64-bit-int scalar (per `scalars.py`).
  - `auto` — re-export of Strawberry's `auto` so consumers can `from django_strawberry_framework import auto` per `__init__.py:6-7`.
  - `__version__` — version string, mirrored against `pyproject.toml` per `AGENTS.md:29`.
  - `logger` — the canonical `"django_strawberry_framework"` logger name for Django's `LOGGING` dict, per `__init__.py:10-15`.
  No accidental exports; no internal symbols leaked; `__all__` is the source of truth for star-imports and `logger` is documented as the single exception with rationale.
- **Subpackage dependency direction is acyclic at the project scale.** The package-wide import DAG (synthesized from per-folder passes) has zero cycles:
  - **Leaves:** `exceptions.py` (used by everything), `scalars.py` (no internal consumers; pure scalar definition), `conf.py` (no internal consumers; consumer-facing settings reader), `utils/*` (leaf trio: relations, strings, typing).
  - **Mid-level:** `registry.py` (consumed by `optimizer/` and `types/`); `optimizer/_context.py` (consumed by `optimizer/extension.py` and `types/resolvers.py`); `optimizer/field_meta.py` and `optimizer/hints.py` (consumed by `optimizer/walker.py` + `types/base.py`).
  - **Top-of-DAG:** `optimizer/extension.py` (orchestrator); `optimizer/walker.py` (planner); `types/finalizer.py` (the only module that imports from every type sibling). `apps.py` and `_django_patches.py` import `apps.py`'s ready() hook into Django; `management/commands/export_schema.py` and `test/_wrap.py` are leaf-utility entry points.
  - **No back-edges:** `optimizer/` never imports from `types/`; `types/` never imports from `management/` or `test/`; `utils/` never imports from any other in-package subpackage. The `Two Scoops of Django` module-responsibility shape is intact at the project scale.
- **Logger naming consistency.** The single `"django_strawberry_framework"` logger name lives at `__init__.py:16` and is re-published by `optimizer/__init__.py:20` (per `rev-optimizer.md:80`). Every other module that needs the logger does `from .. import logger` (or `from . import logger` inside `optimizer/`). The `apps.py` ready-hook patch logs via `logger` directly (per `rev-apps.md`); the `_django_patches.py` defensive-import gap (consolidated 2026-05-25 carry-forward at `worker-memory/worker-1.md:6`) was swept in the cycle-1 re-check.
- **Error hierarchy consistency.** Two `exceptions.py`-rooted exception classes serve the package: `ConfigurationError` (consumer-misconfiguration errors raised by `conf.py`, `types/base.py`, `optimizer/walker.py`, `optimizer/hints.py`) and `OptimizerError` (optimizer-internal correctness errors raised by `optimizer/field_meta.py` and the strictness-on-relation-access path). Every raise site cites the specific consumer-visible mistake (per `rev-optimizer.md:89`); no raw `RuntimeError` / `ValueError` survives in the package. The error-message-substring contract (consumer + test pin) is enforced at the registry layer's four "already registered" phrasings (per `rev-registry.md:80,158,201` — closed as "the four phrasings stay" decision in the 0.0.6 cycle and re-confirmed at 0.0.7).
- **Test discipline at the project scale.** Three test trees per `AGENTS.md:6`: `tests/` (package tests, system-under-test is `django_strawberry_framework` itself), `examples/fakeshop/tests/` (example-project tests not hitting `/graphql` HTTP), `examples/fakeshop/test_query/` (live-HTTP-pinned GraphQL-API tests). Every public surface has both package-test coverage and (where applicable) live-HTTP coverage. The 100% `fail_under` coverage gate is enforced per `AGENTS.md:11`. Zero per-file artifact in 0.0.7 flagged a missing-branch-test as Medium; the only missing-test forwards are forward-looking trigger-gated Lows (per `rev-utils__typing.md` schema-factory consumer fanout; per `rev-optimizer__extension.md` graphql-core 4.x interface-API churn).
- **0.0.6 → 0.0.7 release delta is well-pinned.** Five new top-level files / subpackages landed in 0.0.7 (`_django_patches.py`, `apps.py`, `list_field.py`, `management/`, `test/` per `review-0_0_7.md:42-52`); each has a verified per-file artifact and a corresponding test pin in `tests/`. The new `__version__ = "0.0.7"` at `__init__.py:26` matches `pyproject.toml [project].version` per `AGENTS.md:29`. CHANGELOG / GLOSSARY / README / TREE updates landed via commit `5f0ffa5` (per the bump commit message) — no stale 0.0.6 framing survives in the source. The release-shape work is honest about the new surface area while preserving the prior contract.
- **Workflow discipline at the review scale.** Thirty-one cycles closed verified with zero High and zero Medium beyond cycle 16's `parent_type` dead-parameter removal (already shipped + verified). Every consolidated single-spawn no-op closed `Not warranted` for changelog disposition (per the 17-cycle precedent chain at `rev-optimizer.md:163` and the 31-cycle precedent at `worker-memory/worker-1.md:53`). The four-cycle utils chain (cycles 28-31) is the strongest single argument that the package's leaf-canonical-home framing is intact at 0.0.7. The DRY-cycle export script (`docs/dry/export_dry_review.py`) extracts every top-level bullet from `## DRY analysis` as a finding, so the project-pass bullets above are grep-discoverable for the next DRY sweep without re-deriving across 13 per-file/folder artifacts.

### Summary

`django_strawberry_framework/` enters 0.0.7's project pass with a clean audit chain: 31 verified per-file and folder-pass artifacts, zero High and zero Medium findings, a stable public API surface (eight `__all__` exports plus the documented-non-`__all__` `logger`), an acyclic subpackage DAG, internally-consistent error and logger naming, and three test trees pinning every consumer-visible contract. The project pass adds one act-now Low (the `docs/GLOSSARY.md:462` FK-id elision drift consolidated from three optimizer per-file artifacts and one folder pass — recommended replacement text lifted verbatim from `rev-optimizer.md:38`), plus five forward-looking / restatement Lows: the GLOSSARY:984 strictness-stash attribute-name omission (forward-gated on second consumer); the top-level `__init__.py:18` comment-placement nit (forward-gated on next import-block touch); the `__all__` dunder-ordering nit (forward-gated on second dunder); the `logger`-not-in-`__all__` static-analysis-tooling concern (forward-gated on Sphinx/pdoc wiring); and the cross-module `None`-stance restatement-of-decision (closed as "intentional duplication, canonical narrative site is `conf.py`" so 0.0.8 is not asked to re-litigate). Sixteen trigger-gated DRY carry-forwards are restated at the project-pass-scope grep landing point in `## DRY analysis` so the next DRY cycle has one file to grep instead of 13 separate artifacts. The package is in a strong shape for the 0.0.7 release-gate test run.

---

## Fix report (Worker 2)

Consolidated single-spawn pass (logic + comment + changelog) per `worker-2.md` "Consolidated single-spawn pass" criteria: the only in-cycle edit is a single doc-text replacement on one GLOSSARY line — no source change, no test change, no behavioural surface. All other Lows (L2-L6) are explicitly forward-looking per Worker 1's own prose with grep-discoverable trigger conditions, or closed-as-restatement.

### Files touched

- `docs/GLOSSARY.md:462` — replaced `"FK-id elisions are stashed on `info.context.dst_optimizer_plan` for introspection."` with the Worker 1-authored verbatim wording lifted from `rev-django_strawberry_framework.md:43` / `rev-optimizer.md:38` / `rev-optimizer__extension.md:34`: `"FK-id elisions are stashed on `info.context.dst_optimizer_plan.fk_id_elisions` (tuple, as part of the plan) and `info.context.dst_optimizer_fk_id_elisions` (standalone set, for resolver-time membership checks)."` Names both introspection surfaces (the tuple-on-plan path consumed by external readers via the plan instance, and the standalone set on `info.context.dst_optimizer_fk_id_elisions` consumed at `types/resolvers.py:36,63` and pinned by `tests/optimizer/test_extension.py:325-326,369-371,1430`).

### Tests added or updated

None. The fix surface is doc text in `docs/GLOSSARY.md`; no source change, no behavioural change. Both introspection surfaces are already pinned: `tests/optimizer/test_extension.py:325-326,369-371,1430` exercises `ctx.dst_optimizer_fk_id_elisions == {...}` directly, and the plan-attribute path is exercised via the same fixtures (the test stash assertions read the plan's `fk_id_elisions` tuple). No regression test is appropriate for a doc-text edit.

### Validation run

- `uv run ruff format .` — `118 files left unchanged` (the COM812 warning is pre-existing infrastructure, not raised by this cycle).
- `uv run ruff check --fix .` — `All checks passed!`
- No `pytest` run per `START.md` ("Do not run `pytest` after every change") and `worker-2.md` Validation dicta (no source change; no new test surface).

### Notes for Worker 3

- Shadow file used: `docs/shadow/django_strawberry_framework____init__.overview.md` (re-read per Worker 2 dicta; the top-level `__init__.py` overview's Quick-scan section is the same checklist that drove the project-pass review).
- Per-finding logic dispositions:
  - **Low 1 (GLOSSARY:462 FK-id elision drift — act-now at project pass):** Applied. Verbatim replacement text lifted from Worker 1's canonical citation chain (`rev-optimizer__extension.md:34` → `rev-optimizer.md:38` → `rev-django_strawberry_framework.md:43`). Three-citation precedent confirms the wording — no paraphrase. Grep-verified that the old wording `"FK-id elisions are stashed on `info.context.dst_optimizer_plan` for introspection."` no longer survives anywhere under `docs/` and that the new wording is grep-discoverable on `dst_optimizer_fk_id_elisions` (the standalone-set name) as the disambiguating token a future consumer will search.
  - **Low 2 (GLOSSARY:984 strictness-stash attribute-name omission):** No edit. Forward-gated per Worker 1's verbatim prose: `"Defer-with-trigger: act when a second consumer of either constant lands inside the package (per rev-optimizer___context.md:23's verbatim trigger), at which point the GLOSSARY line graduates to name both attributes alongside the elision-set update from the Low above. Until then the current wording is conservative-but-correct, the strictness-incident user-facing log message (per tests/optimizer/test_extension.py:1430+) names the right attributes by inspection of the actual context shape, and a docstring patch at this scale would force premature consolidation against an introspection surface whose second-consumer shape is still latent."` Trigger phrase: `"act when a second consumer of either constant lands inside the package"`. Grep landing: `rev-optimizer___context.md:23`.
  - **Low 3 (top-level `__init__.py:18` `# noqa: E402` comment placement):** No edit. Forward-gated per Worker 1's verbatim prose: `"Defer-with-trigger: act on the next touch to __init__.py that updates the import block (e.g. a 0.1.x slice landing a new top-level export); rewrite the rationale at the same time to avoid a comment-only churn cycle."` Trigger phrase: `"the next touch to __init__.py that updates the import block (e.g. a 0.1.x slice landing a new top-level export)"`. Avoiding a comment-only churn cycle is the explicit Worker 1-authored argument-against-act-now.
  - **Low 4 (`__all__` dunder-ordering nit):** No edit. Forward-gated per Worker 1's verbatim prose: `"Defer-with-trigger: act if a future cycle adds a second dunder (`__author__`, `__url__`, etc.) — at that point the dunder group convention becomes worth establishing."` Trigger phrase: `"a future cycle adds a second dunder"`. Worker 1's self-assessment: `"The current ordering does not violate any package rule; it is grep-discoverable"` — strictly-correct lexicographic ordering, no defect today.
  - **Low 5 (`logger` not in `__all__` static-analysis-tooling concern):** No edit. Forward-gated per Worker 1's verbatim prose: `"Defer-with-trigger: act if Sphinx / pdoc is wired into the package's doc build AND `logger` is missing from the rendered output — at that point the right fix is either to add `logger` to `__all__` (and update the comment) OR to add an explicit `:exclude-members:` / `:noindex:` directive in the doc-config. Both are valid; the comment-only state is correct today."` Trigger phrase: `"Sphinx / pdoc is wired into the package's doc build AND `logger` is missing from the rendered output"` (conjunctive trigger — both arms must fire).
  - **Low 6 (cross-module `None`-stance restatement at `conf.py:17-35`):** Closed-as-restatement. Per Worker 1's verbatim project-pass disposition: `"intentional duplication. The conf.py module docstring is the canonical narrative site for the cross-module None-stance ... The current factoring is the highest-quality shape. Next cycle (rev-conf.md under 0.0.8 if any) should not re-flag this as a finding; the disposition is closed as 'intentional duplication, canonical narrative site is conf.py.'"` This is a restatement-of-decision, not a defer-with-trigger; explicitly terminal (`"closing carry-forward"` per Worker 1's own Severity line at `rev-django_strawberry_framework.md:108`).
- DRY analysis: no act-now project-pass DRY edit. All sixteen trigger-gated DRY carry-forwards (7 optimizer + 3 types + 3 utils + 3 implied at `rev-django_strawberry_framework.md:10-12`) restated at the project-pass-scope grep landing point with their verbatim trigger conditions preserved. The four leaf canonical-home modules (`registry.py`, `scalars.py`, `conf.py`, `utils/*`) are confirmed canonical at 0.0.7 — zero new DRY consolidation candidate at project scope.
- Intentionally-rejected findings: none. Every Low has either an act-now disposition (L1, applied) or a verbatim-grep-discoverable Worker 1-authored deferral (L2-L5) or a Worker 1-authored closing-carry-forward disposition (L6).
- Memory pattern observations: the project pass IS the trigger condition for L1 (per Worker 1's prose: `"this artifact IS the trigger condition all three per-file forwards quoted verbatim"`); the verbatim wording is preserved across three citation sites (per-file artifact → folder artifact → project artifact), so the act-now edit is identical to lifting the line from any of the three — no paraphrase required.

---

## Comment/docstring pass

Consolidated into this single-spawn pass per the criteria above. The L1 edit is a doc-text replacement on `docs/GLOSSARY.md` — no source-code docstring or comment is touched. There is no post-logic comment-pass surface in this cycle.

### Files touched

None (no source-code comment or docstring touched this cycle). The L1 edit lands on `docs/GLOSSARY.md:462` and is described in the Fix report above; the GLOSSARY is the canonical narrative site for the elision introspection contract, and the source-code docstrings at `optimizer/extension.py:671-672` and `optimizer/plans.py:68-69,118` already name both surfaces correctly (per `rev-optimizer__extension.md:20-36` and `rev-optimizer__plans.md`).

### Per-finding dispositions

- **Low 1 (GLOSSARY:462 FK-id elision drift):** Comment pass is structurally a no-op — the edit IS the doc text; there is no separate docstring or comment to update. Worker 1's recommended-change paragraph at `rev-django_strawberry_framework.md:41-43` and the verbatim wording at line 43 are the contract.
- **Low 2 (GLOSSARY:984 strictness-stash attribute-name omission):** Comment pass no-op — no source edit, no docstring to update. Trigger phrase pinned in `## Notes for Worker 3`.
- **Low 3 (top-level `__init__.py:18` `# noqa: E402` comment placement):** Comment pass no-op — the rationale to fix this Low IS to rewrite the source-code comment, but Worker 1's deferral defers the comment rewrite until the next import-block touch. No source comment change this cycle.
- **Low 4 (`__all__` dunder-ordering nit):** Comment pass no-op — no source edit needed today; the ordering is strictly-correct lexicographic per Worker 1.
- **Low 5 (`logger` not in `__all__` static-analysis-tooling concern):** Comment pass no-op — the existing source comment at `__init__.py:13-15` is the canonical rationale and Worker 1 explicitly states `"the comment-only state is correct today"`.
- **Low 6 (cross-module `None`-stance restatement):** Comment pass no-op — Worker 1's explicit disposition is `"intentional duplication, canonical narrative site is conf.py"`. No source comment change; the `conf.py:17-35` docstring is the canonical narrative.

### Validation run

- `uv run ruff format .` — pass (no-changes; ruff was already run after the GLOSSARY edit and reported `118 files left unchanged`).
- `uv run ruff check --fix .` — pass (`All checks passed!`).

### Notes for Worker 3

Comment pass is structurally no-op because the only in-cycle edit lands on `docs/GLOSSARY.md` (a doc-text file), not on any source-code docstring or comment. Per pattern (15) in `worker-memory/worker-2.md:23` ("When the M1 fix lands the docstring in the same diff because the docstring IS the contract, the comment pass is structurally a no-op — document this explicitly rather than re-editing") — the same shape applies here, generalized from source docstrings to documentation files: when the L1 edit IS the doc-text contract, the comment pass is structurally a no-op.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

Per `AGENTS.md` line 21 (`"Do not update CHANGELOG.md unless explicitly instructed"`) AND the active plan's silence on changelog authorization for this cycle.

The active plan (per `docs/review/review-0_0_7.md`) does not name `CHANGELOG.md` authorization for the project-pass cycle 32, and the dispatch prompt does not authorize a changelog edit. The cycle's only edit is a single doc-text correction on `docs/GLOSSARY.md:462` to bring the GLOSSARY into alignment with the already-shipped optimizer-subsystem introspection contract (the `dst_optimizer_fk_id_elisions` standalone set was shipped in 0.0.6 per the cross-folder cite-chain at `rev-django_strawberry_framework.md:39`; the GLOSSARY drift accumulated against an already-correct source). Documentation-alignment edits that converge a doc surface onto already-shipped behaviour are precisely the `Not warranted` case per pattern from cycle 21 (`worker-memory/worker-2.md:34`): "Documentation-alignment edits (GLOSSARY matching already-shipped behaviour pinned by existing tests) reinforce the `Not warranted` argument because there is no behaviour change to note."

The 32-deep `Not warranted` precedent chain across the entire 0.0.7 review (cycles 1-31 all closed `Not warranted` per `worker-memory/worker-2.md` and `worker-memory/worker-1.md:53`) is the strongest single argument that the project-pass cycle should not break the chain on a doc-text-only correction. The maintainer owns CHANGELOG cadence at pre-alpha (per `START.md` and the 0.0.7 bump commit `5f0ffa5` precedent), and the elision introspection contract was already documented at the source-code level (`optimizer/extension.py:671-672` for the write site; `types/resolvers.py:36,63` for the read site; both pinned at `tests/optimizer/test_extension.py:325-326,369-371,1430`) — the GLOSSARY edit converges the doc to the already-canonical source-code narrative.

### What was done

No `CHANGELOG.md` edit. The cycle's only edit is a single doc-text correction on `docs/GLOSSARY.md:462` (described in the Fix report above) bringing the GLOSSARY line into alignment with the already-shipped optimizer introspection contract.

### Validation run

- `uv run ruff format .` — pass (no-changes; `118 files left unchanged`).
- `uv run ruff check --fix .` — pass (`All checks passed!`).

---

## Verification (Worker 3)

### Logic verification outcome

Project-pass cycle 32; consolidated single-spawn pass with exactly one act-now edit (L1 GLOSSARY:462 FK-id elision drift) and five forward-looking / closing-carry-forward Lows (L2-L6).

- **L1 (GLOSSARY:462 FK-id elision drift — act-now):** Applied verbatim. `git diff -- docs/GLOSSARY.md` shows the line-462 replacement matches Worker 1's recommended-replacement text at `rev-django_strawberry_framework.md:43` exactly: `"FK-id elisions are stashed on \`info.context.dst_optimizer_plan.fk_id_elisions\` (tuple, as part of the plan) and \`info.context.dst_optimizer_fk_id_elisions\` (standalone set, for resolver-time membership checks)."` — both surface names grep-discoverable; backtick-wrapping of attribute paths preserved; "(tuple, as part of the plan)" and "(standalone set, for resolver-time membership checks)" parenthetical disambiguators preserved verbatim. The three-citation precedent chain (`rev-optimizer__extension.md:34` → `rev-optimizer.md:38` → `rev-django_strawberry_framework.md:43`) is intact.
- **L2 (GLOSSARY:984 strictness-stash attribute-name omission):** Forward-gated. Worker 2's `### Notes for Worker 3` preserves Worker 1's verbatim deferral block including the conservative-but-correct framing and the trigger phrase `"act when a second consumer of either constant lands inside the package"`. Grep landing `rev-optimizer___context.md:23` cited verbatim.
- **L3 (`__init__.py:18` `# noqa: E402` comment placement):** Forward-gated. Trigger phrase `"the next touch to __init__.py that updates the import block (e.g. a 0.1.x slice landing a new top-level export)"` preserved verbatim. Worker 1's "avoid a comment-only churn cycle" argument-against-act-now preserved.
- **L4 (`__all__` dunder-ordering nit):** Forward-gated. Trigger `"a future cycle adds a second dunder (\`__author__\`, \`__url__\`, etc.)"` preserved verbatim. Worker 1's "current ordering does not violate any package rule; it is grep-discoverable" self-assessment preserved.
- **L5 (`logger` not in `__all__` static-analysis-tooling concern):** Forward-gated. Conjunctive multi-arm trigger `"Sphinx / pdoc is wired into the package's doc build AND \`logger\` is missing from the rendered output"` preserved verbatim — both arms must fire (the "AND" is the load-bearing connective). The "Both are valid; the comment-only state is correct today" closure also preserved.
- **L6 (cross-module `None`-stance restatement):** Closed-as-restatement. Worker 1's terminal disposition `"intentional duplication, canonical narrative site is conf.py"` is preserved verbatim, including the four-part justification (a-d) and the explicit closing-carry-forward instruction to 0.0.8: `"Next cycle (rev-conf.md under 0.0.8 if any) should not re-flag this as a finding."` This is structurally terminal, not deferral-with-trigger.

`__init__.py` diff empty per `git diff -- django_strawberry_framework/__init__.py` (the consolidated pass does not touch source — every Low concerning `__init__.py` (L3-L5) is forward-gated). Out-of-scope GLOSSARY hunks observed in `git diff -- docs/GLOSSARY.md`: line ~668 registry primary-collision wording (attributable to cycle 6 `rev-registry.md`); lines 899-904 scalar map prose with `DurationField` + `BinaryField` notes (attributable to cycle 21 `rev-types__converters.md` M1 verbatim replacement payload); line ~1000 `_django_patches` SimpleTestCase prose (attributable to cycle 1 `rev-_django_patches.md`). All three attributable per `worker-memory/worker-3.md:10` pattern (out-of-scope GLOSSARY hunks from prior verified cycles); grep-matching the surviving prose against prior cycle artifacts confirms attribution.

### DRY findings disposition

Sixteen trigger-gated DRY carry-forwards (7 optimizer + 3 types + 3 utils + 3 implied per artifact lines 10-12) restated at the project-pass-scope grep landing point — no act-now project-pass DRY edit. Four leaf canonical-home modules (`registry.py`, `scalars.py`, `conf.py`, `utils/*`) confirmed canonical at 0.0.7. Worker 2's restatement preserves every verbatim trigger condition without paraphrase.

### Temp test verification

None used; no behavioural change in the cycle.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box at `docs/review/review-0_0_7.md:130`.
