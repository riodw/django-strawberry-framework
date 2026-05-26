# Review: `django_strawberry_framework/optimizer/` (folder pass)

Status: verified

Folder scope: `_context.py`, `extension.py`, `field_meta.py`, `hints.py`, `plans.py`, `walker.py` (all already-verified per `review-0_0_7.md:106-111`), plus the folder's `__init__.py` (covered here per REVIEW.md "Review scope"). Shadow overview for `__init__.py`: `docs/shadow/django_strawberry_framework__optimizer____init__.overview.md`. Per-file artifacts read for cross-sibling synthesis: `rev-optimizer___context.md`, `rev-optimizer__extension.md`, `rev-optimizer__field_meta.md`, `rev-optimizer__hints.md`, `rev-optimizer__plans.md`, `rev-optimizer__walker.md`.

## DRY analysis

- **Carry-forward: `_resolve_origin_for_type_name(strawberry_schema, type_name) -> tuple[type, type] | None` extraction across `extension.py:342-358` and `extension.py:412-443`.** Surfaced verbatim by `rev-optimizer__extension.md:7` as the first of two trigger-gated DRY bullets; the canonical resolution home is this folder pass because both call sites live inside `extension.py`. Both branches re-implement the same five-step probe (`get_type_by_name` → check `None` → read `origin` → check `None` → reverse-lookup model). Defer-with-trigger verbatim: "act when a third site needs the same origin+model resolution from a graphql-core type name." The folder pass adds nothing the per-file artifact did not already capture; recording here so the next DRY cycle finds the bullet in either artifact.
- **Carry-forward: `_walk_selection_tree(node, fragments, visited, *, on_node)` generic AST visitor collapsing `_walk_directives` (`extension.py:92-128`) and `_walk_reachable_fragment_definitions` (`extension.py:199-227`).** Surfaced verbatim by `rev-optimizer__extension.md:8`; both walks already share `_child_selections` and `_unvisited_fragment_definition`, so the residual divergence is the per-node callback. Defer-with-trigger verbatim: "act when a third walker (e.g. one that emits `RequiredSelection` markers or computes a fingerprint other than the directive set or fragment set) lands in any optimizer module." The trigger is scoped to "any optimizer module," which is the folder-pass scope; recording here so the next walker-shaped helper in this folder (whether it lands in `extension.py`, `walker.py`, or a new sibling) trips the trigger.
- **Carry-forward: `_walk_relation_target(sel, related_model, plan, prefix, info, runtime_paths)` collapsing `walker.py:314-321` and `walker.py:381-388`.** Surfaced verbatim by `rev-optimizer__walker.md:7` as the first DRY bullet; both call sites share six of seven arguments and differ on `plan` identity + `prefix` shape. Defer-with-trigger verbatim: "a third nested-walk call site lands." Re-stated here because the trigger is folder-scoped — a third nested-walk call site could land in `walker.py` itself OR in a future `optimizer/` sibling (e.g. a hypothetical `optimizer/prefetch.py` if the prefetch-building logic ever migrates out of `walker.py`).
- **Carry-forward: thread the precomputed `has_custom_get_queryset` flag back across the `plan_relation` boundary.** Surfaced by `rev-optimizer__walker.md:8` and `rev-optimizer__walker.md:64-66`; the explicit-flag-threading idiom already exists downstream at `walker.py:351,377,394`. Defer-with-trigger verbatim: "until `plan_relation` gains its next signature change." Folder-scoped because the recommended cleanup touches both `walker.py:67` (`plan_relation` return shape) and `walker.py:337` (`_plan_prefetch_relation` re-call site), which is one folder-internal contract.
- **Carry-forward: `RelationPlanCtx` dataclass collapsing the four 9/10-arg positional dispatches at `walker.py:261-271,273-285,461-471,488-498`.** Surfaced verbatim by `rev-optimizer__walker.md:9`; the M1 `parent_type` removal from cycle 16 converged all four call sites onto the same 10-arg shape, so the dataclass conversion is incrementally cheaper now. Defer-with-trigger verbatim: "any relation planner gains an 11th positional argument." Folder-scoped because `_plan_select_relation` / `_plan_prefetch_relation` / `_apply_hint` are all in `walker.py`.
- **Carry-forward: `FieldMeta._from_field_like(field, *, is_relation: bool | None = None)` private classmethod collapsing `from_django_field` (`optimizer/field_meta.py:135-170`) and `_field_meta_for_resolver`'s fallback (`types/resolvers.py:182-210`).** Surfaced verbatim by `rev-optimizer__field_meta.md:23`; the fallback path reconstructs the 11-kwarg shape verbatim. Defer-with-trigger verbatim: "a third call site needs to assemble a `FieldMeta` from a non-Django shape (e.g. a future schema-driven `FieldMetaLike` for non-Django backends)." Cross-folder finding: the fix surface is in `optimizer/field_meta.py` (the new classmethod) but the second consumer lives in `types/resolvers.py`. Re-recorded here as the per-file artifact requested the folder pass be the re-triage venue.
- **Carry-forward (cross-folder, recording here so the folder pass does not double-count): explicit-loop replacement for `types/base.py:174`'s `snake_case` dict-comprehension that silently collapses key collisions.** Surfaced verbatim by `rev-optimizer__field_meta.md:51`; the fix surface is `types/base.py` (a sibling folder), not the optimizer folder. The optimizer folder pass forwards this carry-forward to the `types/` folder pass `rev-types.md` (planned per `review-0_0_7.md:124`) so the snake_case keying contract — spanning walker / finalizer / resolvers — is consolidated against the canonical `field_map` build site once. Defer-with-trigger verbatim: "either (a) Django relaxes its field-name uniqueness rule on `Meta.fields`, OR (b) a consumer files a bug where two columns collide on snake-cased names."
- **Carry-forward: three trigger-gated DRY bullets local to `plans.py`** — `_lookup_path` / `_consumer_prefetch_lookups` / `_consumer_only_fields` Django-private-attribute centralizers (deferred until fourth private attribute joins per `rev-optimizer__plans.md:7`); `_prefetch_lookup_paths` recursive flatten (deferred until second flatten site lands per `rev-optimizer__plans.md:8`); `_dedupe_append(values, value, *, key=...)` covering `append_unique` / `append_unique_many` / `append_prefetch_unique` (deferred until fourth dedupe mutator lands per `rev-optimizer__plans.md:9`). All three are folder-internal and `plans.py`-local; recording here so the next folder-scoped DRY sweep does not have to re-derive the trigger conditions.

## High:

None.

## Medium:

None.

## Low:

### Folder-level GLOSSARY drift on the FK-id elision introspection contract — forward to project pass

The `docs/GLOSSARY.md:462` line ("FK-id elisions are stashed on `info.context.dst_optimizer_plan` for introspection") names only the plan attribute and omits the standalone `dst_optimizer_fk_id_elisions` set that is the resolver-time fast-path introspection surface. Three per-file artifacts already flagged this drift independently:

- `rev-optimizer___context.md:21` — flagged that `DST_OPTIMIZER_PLAN` and `DST_OPTIMIZER_LOOKUP_PATHS` are write-only-from-the-helper constants whose read sites are external attribute access per the GLOSSARY:462,984 contract.
- `rev-optimizer__extension.md:20-36` — flagged that `_publish_plan_to_context` stashes the elision contract on two independent context keys (`DST_OPTIMIZER_PLAN` carrying `plan.fk_id_elisions: tuple[str, ...]` AND `DST_OPTIMIZER_FK_ID_ELISIONS` carrying a standalone `set[str]`), and the GLOSSARY names only one. Forwarded to `rev-django_strawberry_framework.md` (project pass) with the recommended replacement text verbatim.
- `rev-optimizer__walker.md:138-144` — restated the same forward so the walker artifact's project-pass forward is visible to this folder pass.

Promoted to the folder pass as a single Low because three optimizer-internal artifacts independently surfaced the same doc-vs-code drift, which means the GLOSSARY line under-describes the optimizer subsystem's introspection contract at a folder-wide scale rather than at any single file's scale. The canonical resolution home is `rev-django_strawberry_framework.md` (project pass) because `docs/GLOSSARY.md` is the fix surface, not any file in `optimizer/`. Trigger-condition verbatim from `rev-optimizer__walker.md:140`: "when `rev-django_strawberry_framework.md` is written; consolidate the GLOSSARY:462 fix at the project pass alongside any other doc-surface drift the project pass surfaces."

Severity Low because the source code is correct, the test pins are correct (`tests/optimizer/test_extension.py:325-326,369-371,1430` exercise `ctx.dst_optimizer_fk_id_elisions == {...}` directly; resolver consumers route through `types/resolvers.py:61-65`), and this is doc text not consumer-facing source. The recommended replacement text from `rev-optimizer__extension.md:34` is the canonical wording for the project pass to lift verbatim: `"FK-id elisions are stashed on info.context.dst_optimizer_plan.fk_id_elisions (tuple, as part of the plan) and info.context.dst_optimizer_fk_id_elisions (standalone set, for resolver-time membership checks)."`

### `optimizer/__init__.py` re-exports `logger` but the docstring framing under-describes the `from . import logger` re-publication contract two siblings depend on

`optimizer/__init__.py:21-22` re-exports `logger` (re-published from the top-level package `django_strawberry_framework/__init__.py`) and `DjangoOptimizerExtension`. Two siblings reach back through this re-export rather than importing `from .. import logger` directly:

- `extension.py:46` — `from . import logger`
- `walker.py:16` — `from . import logger`

The docstring at `optimizer/__init__.py:14-18` explains *why* `logger` is re-exported here ("the `"django_strawberry_framework"` literal lives in exactly one source location and future subpackages can pick it up the same way"), but it frames the re-export as a tests-only contract ("used by the optimizer pass-through tests") rather than as the canonical intra-subpackage logger handle that two production modules consume. A future maintainer reading the docstring could conclude the re-export is removable once the named pass-through tests retire — which would silently break the two production sibling imports at the `from . import logger` line.

Recommended change: extend the docstring to name the two production consumers explicitly, e.g.: "Re-exports the consumer-facing `DjangoOptimizerExtension` and the framework-wide `logger`. Both are consumed by sibling modules (`extension.py:46`, `walker.py:16`) via `from . import logger` and `from .extension import DjangoOptimizerExtension`, and by the optimizer pass-through tests via `from django_strawberry_framework.optimizer import logger`." This pins the production-consumer contract alongside the test-consumer contract so the docstring is honest about both load-bearing reasons the re-export exists.

Severity Low because the existing code is correct and the docstring is technically accurate (it just under-describes the second load-bearing reason). The risk surface is a future docstring-only edit that drops the re-export based on the now-narrow test-only framing.

```django_strawberry_framework/optimizer/__init__.py:1:24
"""Optimizer subsystem: ``DjangoOptimizerExtension`` (N+1 prevention).

Re-exports the consumer-facing ``DjangoOptimizerExtension`` and the
framework-wide ``logger`` so ``from django_strawberry_framework.optimizer
import logger`` (used by the optimizer pass-through tests) keeps
working after the flat ``optimizer.py`` module was promoted to a
subpackage.
...
"""

from .. import logger
from .extension import DjangoOptimizerExtension

__all__ = ("DjangoOptimizerExtension", "logger")
```

## What looks solid

### DRY recap

- **Existing patterns reused.** The optimizer subpackage is a strong DRY citizen at the folder scale, beyond the per-file recaps:
  - **One-way dependency direction is clean.** The intra-folder import DAG (per the per-file shadow overviews and the cross-sibling import scan) has zero cycles: `_context.py` is a leaf (imports only `typing.Any`); `field_meta.py` depends on `..exceptions` and `..utils.relations`; `hints.py` depends on `..exceptions` and `django.db.models.Prefetch`; `plans.py` depends on `django.db.models.Prefetch` and `collections.abc`; `walker.py` depends on `..exceptions`, `..registry`, `..utils.relations`, `..utils.strings`, `. (logger)`, `.hints`, `.plans`; `extension.py` depends on `..registry`, `..utils.typing`, `. (logger)`, `._context`, `.hints`, `.plans`, `.walker`. The DAG is correctly shaped: `_context.py` and `plans.py` are the two innermost leaves that every active module reads through; `walker.py` and `extension.py` are the two outermost orchestrators; `field_meta.py` and `hints.py` are sibling-public-API dataclass modules consumed by the walker and the type layer.
  - **Sentinel keys consolidated at `_context.py`.** The five `DST_OPTIMIZER_*` constants at `_context.py:34-38` are imported by `extension.py:47` rather than re-declared; no `"dst_optimizer_*"` string literal appears as a bare literal anywhere in `extension.py` (verified at `rev-optimizer__extension.md:97` and re-confirmed in the shadow `Repeated string literals` table for this folder). The canonical "import-alias preserves API surface during shared-helper extraction" pattern at `extension.py:54-56` (`stash_on_context as _stash_on_context`) and `types/resolvers.py:40-42` (`get_context_value as _get_context_value`) is the folder-canonical shape for backwards-compat name preservation.
  - **Plan-shape helpers consolidated at `plans.py`.** `OptimizationPlan` (the mutable-during-construction-immutable-after-handoff dataclass), `resolver_key`, `runtime_path_from_info`, `runtime_path_from_path`, the three dedupe mutators (`append_unique` / `append_unique_many` / `append_prefetch_unique`), and the `diff_plan_for_queryset` reconciliation layer all live in one place. Both `walker.py:218,225,310,312,341,353,365,366,442,538,540,642` (twelve sites) and `extension.py:647,618,679,789` (four sites) route through the public surface; no re-declaration of the dataclass or the mutators in any sibling.
  - **Relation-classification helpers consolidated at `..utils/relations.py`.** `relation_kind` / `is_many_side_relation_kind` / `RelationKind` are imported by `field_meta.py:26` and `walker.py:14`; the `FieldMeta.relation_kind` and `FieldMeta.is_many_side` properties at `field_meta.py:103-111` delegate directly. No open-coded "is M2M or O2M?" check survives anywhere in the folder.
  - **Hint dispatch consolidated at `hints.py`.** `OptimizerHint`'s four flag-collision guards at `hints.py:83-102` plus the `hint_is_skip` dispatch helper at `hints.py:129-146` are the single source of truth for the SKIP/select/prefetch/prefetch_obj/no-op-empty five-shape contract. Two consumers (`walker.py:425` in planning; `extension.py:719` in the schema audit) reach the helper; no consumer open-codes a `hint is OptimizerHint.SKIP` identity check.
  - **`from . import logger`** at `extension.py:46` and `walker.py:16` re-publishes the package-level logger handle through the folder's `__init__.py:21` re-export. The literal `"django_strawberry_framework"` (the logger name) lives in exactly one source location — `django_strawberry_framework/__init__.py` — and is reached by both siblings via this two-hop import (per `optimizer/__init__.py:14-18`). The Low above flags the docstring under-description of this contract, not the contract itself.
- **New helpers considered.** Every act-now extraction was evaluated and deferred-with-trigger at the per-file scale; the folder pass adds no new helper candidate. The seven carry-forward DRY bullets above are all `Defer until <verbatim trigger>` shapes with grep-discoverable trigger conditions. The folder pass's only fresh consolidation candidate is the docstring extension at `optimizer/__init__.py:14-18` (the Low above), which is wording polish, not a helper extraction.
- **Duplication risk in the current folder.** Cross-sibling repeated-literal scan (per `docs/shadow/django_strawberry_framework__optimizer__*.overview.md` `## Repeated string literals` sections) returns zero literals appearing in two or more files — every intra-file repetition (`2x _strawberry_schema` in `extension.py`; `2x prefetch_to` in `plans.py`; `3x prefetch`, `3x selections`, `2x each of related_model / target_field / directives / arguments` in `walker.py`) is intentional sibling phrasing already justified in the per-file artifacts. The `"reverse_one_to_one"` literal at `field_meta.py:156` and `utils/relations.py:70` is a single-site live comparison plus a single-site classifier return, not a duplicate (per `rev-optimizer__field_meta.md:63`). The "centralize one brittle Django-private contract" docstring opener at `plans.py:248-255,258-266,269-297` is intentional triplicate phrasing with one trigger-gated bullet to fold them into a module-level block when a fourth centralizer joins (per `rev-optimizer__plans.md:7`). No literal-as-dispatch-key drift across siblings.

### Other positives

- **0.0.6 → 0.0.7 delta is scoped and well-pinned.** The folder-scoped diff against `f83bb71` (the 0.0.6 verified commit) lands cleanly: `_context.py` is unchanged (verified at `rev-optimizer___context.md`); `field_meta.py` is unchanged (`rev-optimizer__field_meta.md:67`); `hints.py` is unchanged (`rev-optimizer__hints.md:85`); `plans.py` is unchanged (carried forward at `rev-optimizer__plans.md:80`); `extension.py` shipped every 0.0.6 Medium with test pins (M1 type-name disambiguation at `extension.py:705-729` pinned by `tests/optimizer/test_extension.py:3219-3266`; M2 empty-plan strictness invariant pinned by `:1352-1394`; M3 cache-counter drift disclosed at `extension.py:503-513`; plus L1/L2/L4/L5 changes per `rev-optimizer__extension.md:101`); `walker.py` shipped error-attribution sharpening (the three `ConfigurationError` messages now include `{type_name}.{django_name}` per `rev-optimizer__walker.md:165`). Cycle 16 then shipped one new in-release Medium (M1 dead `parent_type` parameter removal at `walker.py:288-321`) verified at `rev-optimizer__walker.md:288-305`. No cycle-cycle drift; every behavioural change in the folder has a corresponding test pin in `tests/optimizer/`.
- **Subsystem boundaries are honoured.** The optimizer folder cleanly owns: N+1 prevention via plan construction (`walker.py`) and plan application (`plans.py:OptimizationPlan.apply` + `extension.py:_optimize`); request-context read/write helpers (`_context.py`); per-field metadata snapshots (`field_meta.py`); typed consumer-facing hint shapes (`hints.py`); the `SchemaExtension` entry point (`extension.py:DjangoOptimizerExtension`). Cross-folder consumers reach the optimizer exclusively through `..registry`, `..utils.relations`, `..utils.typing`, `..utils.strings`, `..exceptions`, and the public `_context.DST_OPTIMIZER_*` constants. No reverse-direction import (the optimizer never imports from `types/`); the `types/resolvers.py` resolver-side reads the optimizer's introspection-stash constants from `_context.py` but the optimizer subpackage does not depend on `types/`. The `Two Scoops of Django` module-responsibility shape is intact at the folder scale.
- **Comment/docstring consistency across siblings.** Every sibling carries a load-bearing module docstring that names the file's role within the subsystem: `_context.py:1-28` (28-line design record naming the four context shapes); `extension.py` (the `SchemaExtension` lifecycle plus the `_strawberry_schema_*` Strawberry-private contract); `field_meta.py` (the immutable per-field snapshot dataclass plus the cardinality-gated nullable rule); `hints.py:1-19` (the consumer-facing typed hint surface); `plans.py:1-13` (the mutable-during-construction-immutable-after-handoff dataclass contract); `walker.py` (the plan-construction recursive descent). No sibling carries a stale 0.0.5 or earlier framing; the docstring shape is internally consistent.
- **Error-handling shape is internally consistent.** `ConfigurationError` (from `..exceptions`) is raised at the four `__post_init__` flag-collision guards (`hints.py:83-102`) and at the `walker.py:455-458,513-516,524-527` hint-validation sites; `OptimizerError` (from `..exceptions`) is raised at the `FieldMeta.from_django_field` guard (`field_meta.py:130-134`). Every raise site names the specific consumer-visible mistake (the `Meta.optimizer_hints` key, the `OptimizerHint(...)` shape, or the `FieldMeta` input). No raw `RuntimeError` / `ValueError` survives in the folder.
- **Test discipline at the folder scale.** `tests/optimizer/test_*.py` (six test files: `test_context.py`, `test_extension.py`, `test_field_meta.py`, `test_hints.py`, `test_plans.py`, `test_walker.py`) carry dedicated `Test*` classes for every public surface plus targeted regression pins for every prior-cycle Medium and Low. Three live-HTTP test files in `examples/fakeshop/test_query/` (test_optimizer_*) pin the end-to-end optimizer behaviour through `/graphql/` HTTP per `AGENTS.md:9` (earn-it-via-real-query rule). The folder is one of the most heavily-tested subsystems in the package by sheer test-method count, and the test files are placed correctly per `AGENTS.md:6` (package tests in `tests/`, live HTTP in `examples/fakeshop/test_query/`).
- **Per-execution ContextVar lifecycle and cache discipline.** The `on_execute` pair-set/pair-reset at `extension.py:523-529` plus the FIFO plan-cache eviction at `extension.py:648-656` plus the `plan.cacheable=False` propagation discipline at `walker.py:337-339,434,391-392` are individually test-pinned (per `rev-optimizer__extension.md:111-112` and `rev-optimizer__walker.md:164`); the request-scope-uncacheability rule cooperates with the per-execution AST cache cleanly. No request-state mutation bug, no cache-key-collision risk, no async/sync hazard surfaced in any per-file artifact.

### Summary

The `optimizer/` folder is the most heavily-engineered subsystem in `django_strawberry_framework` and the per-file review pass produced a strong audit trail: zero High, zero new Medium beyond the cycle-16 `parent_type` dead-parameter removal (already shipped + verified), and a folder-scope-coherent set of trigger-gated DRY deferrals and forward-looking Lows. The folder pass adds two findings: (1) a single folder-level Low recording the `docs/GLOSSARY.md:462` FK-id elision introspection-key drift that three per-file artifacts independently surfaced — forwarded to `rev-django_strawberry_framework.md` (project pass) as the canonical resolution home, with the recommended replacement text from `rev-optimizer__extension.md:34` lifted verbatim; (2) a Low on `optimizer/__init__.py:1-19`'s docstring under-describing the two production consumers (`extension.py:46`, `walker.py:16`) that reach the re-exported `logger` via `from . import logger`, framing the re-export as tests-only when it is also the canonical intra-subpackage logger handle. The folder DAG is acyclic, the cross-sibling repeated-literal scan returns zero shared literals, every shared helper is sited at the correct level (sentinel keys at `_context.py`, plan-shape helpers at `plans.py`, hint dispatch at `hints.py`, relation classification at `..utils/relations.py`), and the test coverage at the folder scale spans `tests/optimizer/` (six test files) plus `examples/fakeshop/test_query/test_optimizer_*` (live-HTTP-pinned). Seven trigger-gated DRY carry-forwards are restated here so the next DRY cycle can grep them in this folder artifact rather than re-deriving them across six per-file artifacts.

---

## Fix report (Worker 2)

Consolidated single-spawn pass per `worker-2.md:159-181`: L1 is explicitly forward-looking to the project pass (Worker 1's verbatim trigger-condition language), L2 is a single trivially-localised docstring edit with no logic change. Both conditions match the consolidated-shape qualifiers.

### Files touched
- `django_strawberry_framework/optimizer/__init__.py:1-23` — extended the module docstring to name the two production consumers (`extension.py:46`, `walker.py:16`) that reach the re-exported `logger` via `from . import logger`, alongside the existing tests-only framing. No logic change; the existing `from .. import logger`, `from .extension import DjangoOptimizerExtension`, and `__all__ = ("DjangoOptimizerExtension", "logger")` lines are untouched. This is the verbatim recommended-change application from `rev-optimizer.md:48-49`.

### Tests added or updated
None. The L2 fix is a docstring-only edit with no observable behaviour change. The contract being described (`from . import logger` resolving at both production sibling call sites) is structurally pinned by the existing import lines at `extension.py:46` and `walker.py:16` — if a future maintainer drops the re-export, both production imports break at module load time. No behavioural test surface to add.

### Validation run
- `uv run ruff format .` — pass, 118 files left unchanged
- `uv run ruff check --fix .` — pass, all checks passed
- Focused tests: not run per `worker-2.md:281` (formatting-only rule; docstring-only edit with no behaviour change does not require focused-test confirmation)

### Notes for Worker 3
- Shadow file used: `docs/shadow/django_strawberry_framework__optimizer____init__.overview.md` (per `rev-optimizer.md:5`); cited original source-file line numbers only.
- L1 disposition: no source edit. Worker 1 explicitly forwarded the GLOSSARY:462 fix to the project pass `rev-django_strawberry_framework.md` per `rev-optimizer.md:36` (verbatim trigger: "when `rev-django_strawberry_framework.md` is written; consolidate the GLOSSARY:462 fix at the project pass alongside any other doc-surface drift the project pass surfaces"). The recommended replacement text at `rev-optimizer.md:38` is preserved verbatim in the artifact for the project-pass cycle to lift without re-derivation.
- L2 disposition: docstring edit applied verbatim per the recommended-change line at `rev-optimizer.md:49`. The new wording names both production consumers (`extension.py:46`, `walker.py:16`) AND the test consumer pattern; preserves the existing "one source location" / "future subpackages" framing so the canonical-logger-handle rationale is still present.
- Seven trigger-gated DRY carry-forwards (the bullets at `rev-optimizer.md:9-16`) are kept in the artifact as forward-looking; each has a grep-discoverable verbatim trigger condition recorded so a future cycle can find it without re-deriving. Bullet-by-bullet trigger summary:
  - `_resolve_origin_for_type_name` (extension.py:342-358 + :412-443) → trigger: "act when a third site needs the same origin+model resolution from a graphql-core type name"
  - `_walk_selection_tree` (extension.py:92-128 + :199-227) → trigger: "act when a third walker (e.g. one that emits `RequiredSelection` markers or computes a fingerprint other than the directive set or fragment set) lands in any optimizer module"
  - `_walk_relation_target` (walker.py:314-321 + :381-388) → trigger: "a third nested-walk call site lands"
  - `has_custom_get_queryset` flag-threading across `plan_relation` boundary → trigger: "until `plan_relation` gains its next signature change"
  - `RelationPlanCtx` dataclass (walker.py:261-271, :273-285, :461-471, :488-498) → trigger: "any relation planner gains an 11th positional argument"
  - `FieldMeta._from_field_like` classmethod (cross-folder: field_meta.py + types/resolvers.py:182-210) → trigger: "a third call site needs to assemble a `FieldMeta` from a non-Django shape"
  - Three `plans.py`-local trigger-gated bullets → triggers: fourth Django-private centralizer / second prefetch-flatten site / fourth dedupe mutator

---

## Comment/docstring pass

Consolidated into the single-spawn shape. The only docstring edit in this cycle was applied in the logic pass (the L2 edit IS the docstring edit; no separate comment-pass surface). The fix and the comment are the same edit.

### Files touched
- `django_strawberry_framework/optimizer/__init__.py:1-23` — described under Fix report; no further edits in this sub-pass.

### Per-finding dispositions
- Low 1 (GLOSSARY:462 FK-id elision drift): no edit. Forwarded to project pass `rev-django_strawberry_framework.md` per Worker 1's explicit verbatim trigger condition at `rev-optimizer.md:36`. The recommended replacement text at `rev-optimizer.md:38` is preserved verbatim in this artifact so the project-pass cycle can lift it without re-derivation. Cross-folder cite-chain (`rev-optimizer___context.md:21`, `rev-optimizer__extension.md:20-36`, `rev-optimizer__walker.md:138-144`) is intact in `## Low` so the project pass can find every independently-flagging artifact.
- Low 2 (`optimizer/__init__.py:1-19` docstring under-describes production consumers): applied as a docstring edit. New wording at `optimizer/__init__.py:3-12` names both production consumers (`extension.py:46`, `walker.py:16` consuming via `from . import logger`) AND the test consumer pattern, with the explicit warning that "Removing the re-export would silently break both production siblings, not just the tests." Preserves the existing "one source location" / "future subpackages" framing further down so the canonical-logger-handle rationale stays present. Line numbers in the docstring (`extension.py:46`, `walker.py:16`) are grep-discoverable per `rev-optimizer.md:42-45`.

### Validation run
- `uv run ruff format .` — pass, 118 files left unchanged
- `uv run ruff check --fix .` — pass, all checks passed

### Notes for Worker 3
- The L2 docstring edit lands at lines 3-12 of the new docstring (the original "Re-exports … keeps working …" paragraph is replaced with a longer paragraph that names production consumers first, tests-second, plus the removal-warning). Lines 14-23 are unchanged from the original docstring.
- Forward-looking carry-forward block (the seven DRY triggers under `## Notes for Worker 3` in `## Fix report (Worker 2)`) is the canonical place a future folder-pass DRY cycle should grep for the trigger conditions. Each trigger condition is quoted verbatim from Worker 1's per-file artifact prose.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

Both citations from `worker-2.md:252-257` apply:

1. `AGENTS.md:21` — "Do not update `CHANGELOG.md` unless explicitly instructed." The dispatch prompt and the artifact do not authorise a `CHANGELOG.md` edit this cycle.
2. The active plan `docs/review/review-0_0_7.md` is silent on changelog authorisation for this cycle (the cycle-17 entry, like every prior 0.0.7 cycle, does not name a changelog edit).

The cycle's edits are entirely internal: one docstring extension on a subpackage `__init__.py` describing an already-shipped re-export contract. No consumer-visible behaviour change, no public-API surface touched (the `__all__ = ("DjangoOptimizerExtension", "logger")` line is unchanged), no error contract change. This continues the 0.0.7 precedent chain of `Not warranted` dispositions for internal-only docstring polish, now seventeen cycles deep.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass, 118 files left unchanged
- `uv run ruff check --fix .` — pass, all checks passed

---

## Verification (Worker 3)

### Logic verification outcome

Both Lows accepted as adjudicated.

- **L1 (GLOSSARY:462 FK-id elision drift):** no source edit; explicitly forwarded to project pass `rev-django_strawberry_framework.md`. Worker 1's verbatim trigger condition at `rev-optimizer.md:36` ("when `rev-django_strawberry_framework.md` is written; consolidate the GLOSSARY:462 fix at the project pass alongside any other doc-surface drift the project pass surfaces") preserved at Worker 2's restatement (artifact line 116). Recommended replacement text at `rev-optimizer.md:38` preserved verbatim — the full sentence "FK-id elisions are stashed on info.context.dst_optimizer_plan.fk_id_elisions (tuple, as part of the plan) and info.context.dst_optimizer_fk_id_elisions (standalone set, for resolver-time membership checks)." is intact for the project-pass lift. Cross-folder cite-chain (`rev-optimizer___context.md:21`, `rev-optimizer__extension.md:20-36`, `rev-optimizer__walker.md:138-144`) intact.
- **L2 (optimizer/__init__.py docstring under-describes production consumers):** docstring edit applied verbatim per Worker 1's recommendation at `rev-optimizer.md:49`. `git diff -- django_strawberry_framework/optimizer/__init__.py` is docstring-only — lines 3-12 replace the prior tests-only framing with the production-first wording naming both consumers (`extension.py:46`, `walker.py:16`) plus the removal-warning ("Removing the re-export would silently break both production siblings, not just the tests"); lines 14-23 unchanged. Imports (`from .. import logger`, `from .extension import DjangoOptimizerExtension`) and `__all__ = ("DjangoOptimizerExtension", "logger")` untouched. Cited consumer lines grep-confirmed: `extension.py:46:from . import logger` and `walker.py:16:from . import logger`.

### DRY findings disposition

Seven trigger-gated DRY carry-forwards (artifact lines 9-16) preserved verbatim with Worker 2's bullet-by-bullet restatement at lines 119-125. Spot-checked each trigger phrase against Worker 1's prose:

1. `_resolve_origin_for_type_name`: trigger "act when a third site needs the same origin+model resolution from a graphql-core type name" — verbatim at lines 9 and 119.
2. `_walk_selection_tree`: trigger including both arms ("emits `RequiredSelection` markers or computes a fingerprint other than the directive set or fragment set") preserved verbatim at lines 10 and 120.
3. `_walk_relation_target`: trigger "a third nested-walk call site lands" — verbatim at lines 11 and 121.
4. `has_custom_get_queryset` flag-threading: trigger "until `plan_relation` gains its next signature change" — verbatim at lines 12 and 122.
5. `RelationPlanCtx` dataclass: trigger "any relation planner gains an 11th positional argument" — verbatim at lines 13 and 123.
6. `FieldMeta._from_field_like`: trigger "a third call site needs to assemble a `FieldMeta` from a non-Django shape (e.g. a future schema-driven `FieldMetaLike` for non-Django backends)" — full verbatim at line 14; line 124 abbreviates after "non-Django shape" but the full clause is preserved at line 14 for grep.
7. Three `plans.py`-local bullets (fourth Django-private centralizer / second prefetch-flatten site / fourth dedupe mutator) — verbatim at lines 16 and 125.

Cross-folder `types/base.py:174` snake_case carry-forward (artifact line 15) — disjunctive trigger "either (a) Django relaxes its field-name uniqueness rule on `Meta.fields`, OR (b) a consumer files a bug where two columns collide on snake-cased names" — both arms preserved at line 15 and routed to `rev-types.md` via verbatim forward.

### Temp test verification

None created. The L2 fix is docstring-only with no observable behaviour change; the `from . import logger` contract at `extension.py:46` and `walker.py:16` is structurally pinned by the existing imports themselves (module-load-time failure if the re-export is dropped).

### Changelog disposition

`Not warranted`. `git diff -- CHANGELOG.md` empty. Both citations present and load-bearing: AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed" + active plan `docs/review/review-0_0_7.md` silence on changelog authorisation for this cycle. Internal-only framing honest — the only edit is a docstring extension on a subpackage `__init__.py` describing an already-shipped re-export contract; `__all__` is unchanged; no public-API surface touched. The seventeen-cycle 0.0.7 precedent chain buttresses the disposition.

### Validation run

- `uv run ruff format --check .` — pass, 118 files already formatted.
- `uv run ruff check .` — pass, all checks passed.
- Focused tests not run (docstring-only edit, no behavioural surface; consistent with `worker-2.md:281`).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` and marks `review-0_0_7.md:112`.
