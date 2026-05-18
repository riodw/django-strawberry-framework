# Build: Cross-slice integration pass

Spec reference: `docs/spec-014-meta_primary-0_0_6.md` (the integration pass spans all six slices of build-014)
Status: final-accepted

## Pre-flight checklist

- **Required reading walked.** `AGENTS.md`, `START.md`, `BUILD.md`, `worker-1.md`, `GOAL.md`, `docs/FEATURES.md`, `CHANGELOG.md`, the active build plan (`docs/builder/build-014-meta_primary-0_0_6.md`), the active spec (`docs/spec-014-meta_primary-0_0_6.md`), and `docs/builder/worker-memory/worker-1.md` were re-read at the start of this pass. The `worker-1.md` memory file is now nine entries spanning Slices 1-6 closeout and stays under the 50-line consolidation threshold.
- **Every prior slice artifact read in order.** `bld-slice-1-registry_multitype.md` (final-accepted), `bld-slice-2-meta_primary_recognition.md` (final-accepted), `bld-slice-3-ambiguity_audit.md` (final-accepted), `bld-slice-4-consumer_site_updates.md` (final-accepted), `bld-slice-5-version_bump.md` (final-accepted), `bld-slice-6-docs_kanban_archive.md` (final-accepted). No "as needed" gap; the strict-reading rule from `BUILD.md` "Cross-slice integration pass" is honored.
- **Spec status-line re-verification (per `worker-1.md:42-48`).** Spec lines 1-7 re-read at the top of this pass: `Status: draft (revision 6, post-TODO-anchor review).` (line 4) describes revision history, not lifecycle; spec line 260 keeps the spec at its working location with no archival default. Slice 6's planning notes and final-verification both accepted the `draft` framing intentionally. **No spec edit during this integration pass.** Predecessor reference at spec line 6 (`KANBAN.md` card `WIP-ALPHA-014-0.0.6`) is historically accurate by design — the card has now been moved to `DONE-014-0.0.6` in `KANBAN.md`, but the spec records the predecessor identity at authoring time. **No spec edit.**
- **Static inspection helper coverage.** Six Python files were touched by the build:
  - `django_strawberry_framework/registry.py` (Slice 1) — shadow at `docs/builder/shadow/django_strawberry_framework__registry.overview.md`. Helper ran on Slice 1 Worker 3 pass.
  - `django_strawberry_framework/types/base.py` (Slices 2, 4) — shadow at `docs/builder/shadow/django_strawberry_framework__types__base.overview.md`. Helper ran on Slice 4 Worker 3 pass.
  - `django_strawberry_framework/types/definition.py` (Slice 2) — shadow at `docs/builder/shadow/django_strawberry_framework__types__definition.overview.md`. Worker 3 ran helper on Slice 2 (size below 30-line trigger but inside `types/`).
  - `django_strawberry_framework/types/finalizer.py` (Slice 3) — shadow at `docs/builder/shadow/django_strawberry_framework__types__finalizer.overview.md`. Helper ran on Slice 3 Worker 3 pass.
  - `django_strawberry_framework/optimizer/walker.py` (Slice 4) — shadow at `docs/builder/shadow/django_strawberry_framework__optimizer__walker.overview.md`. Helper ran on Slice 4 Worker 3 pass.
  - `django_strawberry_framework/optimizer/extension.py` (Slice 4) — shadow at `docs/builder/shadow/django_strawberry_framework__optimizer__extension.overview.md`. Helper ran on Slice 4 Worker 3 pass.

  All six shadow files exist under `docs/builder/shadow/`. No file is missing or skipped. No re-run required.

## Repeated string literals across slices

The per-file `Repeated string literals` sections from each shadow overview:

| File | Slices | Repeated literals (≥8 chars) |
|---|---|---|
| `registry.py` | 1 | None |
| `types/base.py` | 2, 4 | `optimizer_hints` (4x), `description` (2x), `interfaces` (2x) — all pre-Slice-1 |
| `types/definition.py` | 2 | None |
| `types/finalizer.py` | 3 | None |
| `optimizer/walker.py` | 4 | `prefetch` (3x), `selections` (3x), `related_model` (2x), `target_field` (2x) — all pre-Slice-4 |
| `optimizer/extension.py` | 4 | `_strawberry_schema` (2x) — pre-Slice-4 |

**Cross-file literal scan.** Compared each per-file literal set against every other file's set; no literal appears in two or more files. The build-014 error message strings each appear at exactly one site (confirmed via `grep`):

- `"Meta.primary must be a bool"` — `django_strawberry_framework/types/base.py:401` (Slice 2, sole site).
- `"is already declared primary as"` — `django_strawberry_framework/registry.py:129` (Slice 1, sole site).
- `"primary flag cannot be flipped on re-register"` — `django_strawberry_framework/registry.py:121-122` (Slice 1, sole site; implicit-concatenation split across two adjacent string literals — counts as one literal at runtime).
- `"Models with multiple registered DjangoType subclasses and no primary:"` — `django_strawberry_framework/types/finalizer.py:59` (Slice 3, sole site).
- `"Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."` — `django_strawberry_framework/types/finalizer.py:61-62` (Slice 3, sole site; implicit-concatenation split across two adjacent string literals).

**No cross-file repeated literal candidate to centralize.** The pre-Slice literals (`optimizer_hints`, `prefetch`, `selections`, `related_model`, `target_field`, `_strawberry_schema`, `description`, `interfaces`) all live entirely within their owning file. No build-014 slice introduced a string that recurs across files.

## Imports / boundary analysis

The per-file `Imports` sections from each shadow overview, normalized to first-party / Django / Strawberry / standard categories:

- `registry.py` — locals: `.exceptions`, `.types.definition`, `.types.relations` (via `TYPE_CHECKING`). One-way: `registry` is a leaf module of the package's data-flow graph; it imports from `.types.*` only inside `if TYPE_CHECKING:` so the runtime dependency is `registry → exceptions`. **Clean.**
- `types/base.py` — locals: `..exceptions`, `..optimizer.field_meta`, `..optimizer.hints`, `..registry`, `..utils.strings`, `.converters`, `.definition`, `.relations`, `.relay`. Imports from `..optimizer.*` (one-way: types layer reads optimizer-side hint enums and field-meta dataclass) and from `..registry` (one-way). **Clean** — the imports are downward (from `types/` into `optimizer/` for shared dataclasses, from `types/` into `registry`).
- `types/definition.py` — locals: `..optimizer.field_meta`, `..optimizer.hints`. **Clean** — dataclass-only file with two upward imports of shared optimizer-side data shapes; no cycles.
- `types/finalizer.py` — locals: `..exceptions`, `..registry`, `.converters`, `.relations`, `.relay`, `.resolvers`. **Clean** — no new imports introduced by Slice 3 except `from django.db import models` (Django, not local). The existing local imports were unchanged.
- `optimizer/walker.py` — locals: `..exceptions`, `..registry`, `..utils.relations`, `..utils.strings`, `.hints`, `.plans`. **Clean** — Slice 4's H2 changes added a kwarg to existing helpers, no new imports.
- `optimizer/extension.py` — locals: `..registry`, `..utils.typing`, `._context`, `.hints`, `.plans`, `.walker`. **Clean** — Slice 4's H2/H3 changes added the `_OriginAndModel` NamedTuple (re-using the existing `from typing import NamedTuple` at line 32) and `from django.db import models` (already present). No new imports.

**One-way dependency direction verified end-to-end:**

- `registry.py` is the leaf module (only imports `exceptions`; `TYPE_CHECKING`-only imports of `types/`).
- `types/definition.py` imports from `optimizer/*` (shared `FieldMeta`, `OptimizerHint` dataclasses) — this is the **planned** cross-folder boundary the build inherited from pre-014 slices, not a Slice 1-6 regression.
- `types/base.py`, `types/finalizer.py`, `types/converters.py`, `types/relay.py` all import from `registry` (downward) and from `optimizer/*` for shared dataclasses.
- `optimizer/walker.py` imports from `registry` (upward — optimizer reads registry to resolve type → model). The walker does NOT import from `types/*`; type lookup goes through `registry`.
- `optimizer/extension.py` imports from `registry` (upward) and from `optimizer/walker` (sibling) and `optimizer/plans` (sibling). No `types/*` import — the optimizer reads model/type info via the registry, never directly from the `types/` layer.

**Boundary leaks scan.** No new cross-folder imports introduced by the build. No sibling has started importing from outside the documented boundary. The build did not introduce any `types/` → `optimizer/` upward import (definition's pre-existing one stays); did not introduce any `optimizer/` → `types/` import (the optimizer reads through `registry` as designed).

## Cross-slice DRY observations

Walked the eight cross-slice DRY axes from `BUILD.md` "The integration pass itself should check" plus the four maintainer-flagged carry-forward items from the task prompt. Each observation cites file:line, severity per the Worker 3 ladder, and a recommended action.

### Observation 1 — Sibling formatter envelope at `types/finalizer.py:21-63` (Slice 3 deferral)

**Sites.** `django_strawberry_framework/types/finalizer.py:21-42` (`_format_unresolved_targets_error`) and `:45-63` (`_format_ambiguity_error`).

**Shape.** Both formatters use the same three-piece envelope: `<header>\n + body + \n\n + <footer>` where `body = "\n".join(<per-item>)`. The header strings, footer strings, and per-item builders differ materially:

- `_format_unresolved_targets_error` iterates `list[PendingRelation]`; per-item is `f"  - {source_model}.{field_name} -> {related_model} (no registered DjangoType)"`; for-loop with `append`.
- `_format_ambiguity_error` iterates `list[tuple[Model, tuple[type, ...]]]`; per-item is `f"  {model.__name__}: {', '.join(...)}"`; list comprehension.

**Severity.** Low. Slice 3 Worker 3 already recorded this as Low with disposition "keep as-is; if a third formatter joins, the envelope helper starts paying off." Slice 3 Worker 1 final verification confirmed "consolidation is deferred to the cross-slice integration pass — `docs/builder/bld-integration.md` will re-check whether any Slice 4-6 follow-up introduces a third formatter at this site; if so, the integration pass spawns the consolidation cycle then." Slice 4 added zero formatters to `types/finalizer.py`. Slices 5 and 6 added zero `.py` lines.

**Recommended action.** **Leave as is.** N=2 sibling formatters with differing per-item builders; a factored `_format_finalize_error(header, lines, footer) -> str` would save ~3-4 lines per caller but require each caller to still build its own per-line list and pass three string arguments — net wash. The plan's DRY analysis and Slice 3 Worker 3 review both reached the same conclusion. **Trigger condition for revisiting: a third formatter joins `types/finalizer.py`.** Not the case in build-014. Status: deferred (the deferral is recorded in `### Deferred follow-up catalog` below).

### Observation 2 — `_OriginAndModel` NamedTuple sibling of `CacheInfo` (Slice 4 prompt carry-forward)

**Sites.** `django_strawberry_framework/optimizer/extension.py:274-279` (`CacheInfo` NamedTuple) and `:371-386` (`_OriginAndModel` NamedTuple). Both are module-private (one is leading-capital, the other is leading-underscore; both are file-internal).

**Package-wide NamedTuple scan.** `grep -rn "^class.*NamedTuple" django_strawberry_framework/` returns **only these two**. No other NamedTuple class exists anywhere in the package. The `_OriginAndModel` NamedTuple does NOT duplicate any other NamedTuple pattern.

**DRY check.** Both NamedTuples reuse the single `from typing import NamedTuple` import at `extension.py:32` (one shared import, two module-local helpers). The two-NamedTuple cluster pattern is intentional and DRY: `CacheInfo` is the public-shape return of `DjangoOptimizerExtension.cache_info()`; `_OriginAndModel` is the private-shape return of `_resolve_model_from_return_type()`. Distinct domains (cache observability vs. resolver return-type resolution), distinct call sites (one public, one private), zero overlap.

**Severity.** None. The sibling-NamedTuple shape is exactly the kind of DRY-by-reuse the build intends.

**Recommended action.** **Leave as is.** No consolidation candidate; no boundary leak.

### Observation 3 — H3 dedupe rationale comment length (Slice 4 Worker 3 Low L2, prompt carry-forward)

**Site.** `django_strawberry_framework/optimizer/extension.py:645-652` — the dedupe rationale comment above the `seen` / `warnings` accumulator pair in `check_schema`.

**Shape.** Seven lines (eight if counting the line with the dedupe guard itself). Spec line 150 asked for a "one-line comment"; the plan's Implementation discretion items at `bld-slice-4-consumer_site_updates.md:292` flagged comment wording as a discretion item; Worker 2 chose the multi-line form because the rationale needed to reference both the spec contract and the `iter_types()` semantic change to encode the "this is a multi-type artifact, not generic defensiveness" framing.

**Severity.** Low. Worker 3 recorded this as Low ("Content is correct and clear; the multi-type-artifact framing is preserved per the spec contract. The seven-line form is a minor stylistic departure from the plan's wording"). Worker 1 final verification accepted as-is ("the rationale references both the spec contract and the `iter_types()` semantic change. The expansion is a code-comment clarity matter, not a correctness issue. Accepted as-is per Worker 2's discretion").

**Cross-slice impact.** Zero. The comment is local to `optimizer/extension.py:check_schema`; no other slice touches the dedupe path or the comment shape.

**Recommended action.** **Leave as is.** The carry-forward verdict from Slice 4 holds at the integration pass: the comment encodes load-bearing content (the multi-type-artifact framing per spec line 150's intent) that a one-line form could not capture without losing fidelity. No consolidation; no spec edit.

### Observation 4 — Error message conventions (prompt carry-forward)

**Sites.** Five distinct error messages introduced by build-014:

| Message substring | Site | Slice | Caller's contract |
|---|---|---|---|
| `"<name> is already registered <label> <existing>"` | `registry.py:73` (existing `_already_registered` helper) | pre-014 | Reverse-collision (same type, two models) — survived the rewrite |
| `"<type_cls> is already registered for <model>; primary flag cannot be flipped on re-register"` | `registry.py:121-122` inline | 1 | Same-type re-register with disagreeing `primary` flag |
| `"<type_cls> is already declared primary as <existing_primary>"` | `registry.py:129` inline | 1 | Two distinct types both declaring primary on same model (at registration time) |
| `"Meta.primary must be a bool"` | `types/base.py:401` inline | 2 | Per-`Meta.*` bool guard |
| `"Models with multiple registered DjangoType subclasses and no primary:\n... Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."` | `types/finalizer.py:59-62` via `_format_ambiguity_error` | 3 | Multi-type-no-primary detected at finalize time (the audit) |

**Shape analysis.**

- Three single-call-site messages (`registry.py:121-122`, `:129`, `types/base.py:401`) are inlined as bare `ConfigurationError(...)` raises. The plan rejected helper extraction for each (one call site apiece; helper would force label expansion or method-jump for a single consumer).
- One multi-call-site helper (`registry.py:73` `_already_registered("against", ...)`) survives from the pre-014 surface and continues to handle the reverse-collision branch.
- One finalize-time message is built by the dedicated `_format_ambiguity_error` formatter at `types/finalizer.py:45-63` to keep the per-formatter "build a list of lines, concat with envelope" shape parallel to its sibling `_format_unresolved_targets_error`. The choice of formatter-over-inline is explicit in the plan (Slice 3 DRY analysis) because the audit's message has structured offender data that benefits from the formatter abstraction.

**Consistency check.** Every build-014 `ConfigurationError(...)` raise:

1. Starts with the offending subject's identifier (the type class name or the model name or `Meta.primary`).
2. States what's wrong in active voice (`"is already declared primary as"`, `"primary flag cannot be flipped"`, `"must be a bool"`).
3. For the multi-offender case (audit), follows with an actionable fix sentence (`"Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."`).

The five new messages match the pre-014 `ConfigurationError` shape convention (which `registry.py:73` exemplifies: `f"{name} is already registered {label} {existing_name}"`) — subject + verb + qualifier. No outlier message; no message uses passive voice.

**Severity.** None. The error-message convention is consistent across all build-014 sites.

**Recommended action.** **Leave as is.** No drift to consolidate. The duplicate-primary message (`registry.py:129`) and the audit error message (`types/finalizer.py:59-62`) describe complementary contracts (at-registration vs. at-finalize) and use distinct framings ("already declared primary as X" vs. "multiple DjangoType subclasses and no primary"); folding them into a shared helper would require parametrizing the framing and would not reduce the surface meaningfully.

### Observation 5 — Plan cache key tuple shape (Slice 4 Worker 3 L1 carry-forward)

**Site.** `django_strawberry_framework/optimizer/extension.py:732-735` — the five-element cache key tuple returned by `_build_cache_key`. Annotation declared at `:461-464`.

**Shape.** `tuple[str, frozenset[tuple[str, Any]], type, tuple[str, ...], type | None]` — `(doc_key, relevant_vars, target_model, runtime_path_from_info(info), origin)`.

**Single-source check.** The tuple is constructed at exactly one site (`_build_cache_key`'s `return`). The annotation on `self._plan_cache` (line 461-464) was extended in the same edit. The five-slot tuple is not duplicated as a constant elsewhere; no parallel tuple-builder exists.

**Slice 4 Worker 3 L1 deferral.** `test_plan_cache_keys_distinguish_primary_and_secondary_returns_for_same_model` at `tests/optimizer/test_extension.py` relies on `response_path` (`("allItems",)` vs `("allAdminItems",)`) to distinguish the two queries — the new `origin` slot is not the unique differentiator in that single test. Three sibling tests (`test_optimizer_walker_plans_root_from_resolver_return_type_when_secondary`, `test_scalar_only_secondary_resolver_uses_secondary_field_map`, `test_resolve_model_from_return_type_unwraps_nested_wrappers`) verify the origin-threading at the upstream layer, so the H2 contract is verifiable across the cluster.

**Severity.** Low (Slice 4 Worker 3 disposition: "Worker 1 may add a complementary test (or accept the cluster-level coverage) during integration pass review"). Slice 4 Worker 1 final verification accepted as-is on the cluster-level coverage rationale.

**Recommended action.** **Leave as is for build-014.** The H2 contract is pinned by three independent tests at the walker and resolver-helper layers. Adding a stricter cache-key isolation test (e.g., holding response_path constant and varying origin only via per-field return-type annotations) is a future-card hardening candidate but not a build-014 defect.

### Observation 6 — Module-level `_OriginAndModel` placement (Slice 4 prompt carry-forward)

**Site.** `django_strawberry_framework/optimizer/extension.py:371-386`. The NamedTuple lives immediately above `_resolve_model_from_return_type` (its only producer).

**DRY check.** This is the **only** call/unpack site pair in the file. Plan offered a discretion choice between (a) place above the producer (`_resolve_model_from_return_type`) or (b) place next to the sibling `CacheInfo` cluster. Worker 2 picked (a) so reading the producer top-down explains the return shape.

**Severity.** None. The choice is a stylistic-discretion item that lands without DRY consequence.

**Recommended action.** **Leave as is.** No consolidation; no boundary leak.

### Observation 7 — Two reads of `Meta.primary` (Slice 2 shape, prompt-implicit carry-forward)

**Sites.** `django_strawberry_framework/types/base.py:399` (`primary = getattr(meta, "primary", False)` inside `_validate_meta`) and `:93` (`primary = getattr(meta, "primary", False)` inside `__init_subclass__`).

**Shape.** Two `getattr` reads of the same key with the same default. Slice 2 Worker 1 plan explicitly addressed this in the DRY analysis ("Two reads of `Meta.primary` are intentional, not duplication"); spec line 327 confirms; Slice 2 Worker 3 review accepted. The first read is the guard inside the validator; the second is the plumb to `DjangoTypeDefinition(...)` and `registry.register_with_definition(...)`.

**Cross-slice impact.** Slice 4 did not touch either site. The plumb still flows `types/base.py:93 → :133 → :135` and is consumed by `registry.register_with_definition(model, type_cls, definition, *, primary=primary)`.

**Severity.** None. The two-read shape is the spec contract.

**Recommended action.** **Leave as is.** No consolidation; the two reads encode distinct contracts (guard / plumb) and consolidating into a tuple return on `_validate_meta` would balloon every Meta-key consumer.

### Observation 8 — Three-helper vocabulary across docs surfaces (Slice 6, prompt-implicit carry-forward)

**Sites.** Six doc surfaces post-Slice-6 mention the `primary_for(model)` / `types_for(model)` / `models_with_multiple_types()` trio:

- `docs/FEATURES.md:664` (Registry-surface paragraph in `## Meta.primary` entry).
- `CHANGELOG.md:25` (`Added` line) and `:31` (`Changed`'s `iter_types` bullet).
- `KANBAN.md:1622-1623` (DONE-014 body's "New registry surface" bullet).
- `docs/spec-014-meta_primary-0_0_6.md:255` and `:257` (verbatim source).
- `docs/README.md:101` (single-line nod — intentionally compact).
- `TODAY.md` (deep-links to FEATURES — intentionally no restate).

**Consistency check.** The three helper names appear identically wherever the registry surface is described. Slice 6 Worker 3 verified during the documentation/release-sanity pass; Slice 6 Worker 1 final verification re-verified ("Three-helper vocabulary (`primary_for` / `types_for` / `models_with_multiple_types`) confirmed consistent across `docs/FEATURES.md:664`, `CHANGELOG.md:25` / `:31`, `KANBAN.md:1622-1623`, and the spec source — no drift").

**Severity.** None.

**Recommended action.** **Leave as is.** Vocabulary discipline confirmed; no consolidation needed.

### Observation 9 — Ambiguity-rule four-row statement across docs (Slice 6, prompt-implicit carry-forward)

**Sites.** Two doc surfaces post-Slice-6 enumerate the four ambiguity rules:

- `docs/FEATURES.md:659-662` (the `## Meta.primary` entry's Ambiguity rules block).
- `KANBAN.md:1627-1631` (DONE-014 body's ambiguity-rules sub-bullets).

**Plus three test contracts** that pin each rule:

- `tests/test_registry.py::test_register_two_primaries_for_same_model_raises_configuration_error` (multiple-two-primary-at-registration rejected).
- `tests/test_registry.py::test_register_two_types_same_model_without_primary_allows_both_in_types_for` (multiple-no-primary allowed at registration; rejected later by audit).
- `tests/test_registry.py::test_finalize_raises_when_model_has_multiple_types_no_primary` (audit at finalize-time).

**Severity.** None. The wording is identical across the doc surfaces; the test contracts pin every rule.

**Recommended action.** **Leave as is.** No drift.

### Observation 10 — Public-surface (`__all__`) check

**Check.** `git diff -- django_strawberry_framework/__init__.py` against the pre-build baseline returns empty across every slice. None of Slices 1-6 added or removed entries from `__all__`. The three new registry helpers (`primary_for`, `types_for`, `models_with_multiple_types`) and the new `Meta.primary` flag stay reachable via `from django_strawberry_framework.registry import registry`; `audit_primary_ambiguity()` and `_OriginAndModel` and `_format_ambiguity_error` are private to their modules. Slice 3 explicitly excluded `audit_primary_ambiguity` from `types/__init__.py`'s `__all__`.

**Severity.** None. The Definition of Done's "no new public exports" item is satisfied.

**Recommended action.** **Leave as is.** The public surface is unchanged.

### Observation 11 — Comments tell one coherent story across the new code

Walked every comment block touching build-014 code:

- `types/base.py:55-67` — `ALLOWED_META_KEYS` frozenset: no per-entry comment; the canonical reference is the `## Meta.primary` entry in `docs/FEATURES.md`. Pre-014 convention; no inconsistency.
- `types/base.py:88-141` — `__init_subclass__` body: the inline `primary = getattr(meta, "primary", False)` (line 93) is contextless because the surrounding lines (`fields = ...`, `optimizer_hints = ...`) all use the same `getattr(meta, "<key>", default)` pattern. Local readability is high.
- `types/base.py:397-402` — `_validate_meta` bool guard for `Meta.primary`: three lines matching the `Meta.model` guard's shape at `:388-392`. No new comment needed; the pattern is established.
- `types/definition.py` — `primary: bool = False` dataclass field: no per-field comment, matching the surrounding `consumer_*` and deferred placeholder fields. Convention preserved.
- `types/finalizer.py:21-63` — sibling formatters: both docstrings carry "Sibling convention" paragraphs that mutually reference each other. Self-referential and grep-stable. Slice 3 Worker 2 explicitly updated `_format_unresolved_targets_error`'s docstring to name `_format_ambiguity_error`.
- `types/finalizer.py:66-86` — `audit_primary_ambiguity()` docstring: cites the spec line, the Slice 1 helper at `registry.py:200-206`, the M1 placement contract, and the routing helpers used. Stands alone for a future reader.
- `optimizer/walker.py:509-516` — the rev6 M1 audit invariant comment for `_selected_scalar_names`: encodes the "do NOT thread `source_type` here; nested-only by design" rationale plus a call-graph note. Worker 3 confirmed the TODO prefix was correctly dropped during Slice 4 implementation; the content is permanent code-comment material.
- `optimizer/extension.py:645-652` — H3 dedupe rationale (the seven-line block in Observation 3): encodes the multi-type-artifact framing per the spec contract.
- `optimizer/extension.py:371-386` — `_OriginAndModel` NamedTuple with docstring: explains the pair-or-None failure contract.
- `optimizer/extension.py:389+` — `_resolve_model_from_return_type` updated docstring: reflects the new return shape.

**Story coherence check.** Every comment block describes the final accepted behavior. No stale TODO references to spec-014 anchors remain in the source (verified by `grep -rn "TODO(spec-014" django_strawberry_framework/` — returns no matches; all anchors were removed in the same edits that landed each contract). No comment talks about a behavior that did not ship.

**Severity.** None.

**Recommended action.** **Leave as is.** Comments tell one coherent story across the build.

### Observation 12 — Duplicated helpers across slices

**Scan.** Compared the new module-level functions / methods introduced by each slice:

- Slice 1: `TypeRegistry.primary_for`, `TypeRegistry.types_for`, `TypeRegistry.models_with_multiple_types`. Three single-purpose accessors on the registry class; one body line each; no duplication.
- Slice 2: zero new functions (only signature additions and field additions).
- Slice 3: `audit_primary_ambiguity()` and `_format_ambiguity_error(offenders)`. One audit + one formatter; both module-level in `types/finalizer.py`.
- Slice 4: `_OriginAndModel` NamedTuple. No new functions; the four signature changes added `source_type` / `origin` parameters in place.
- Slices 5, 6: zero new functions.

**Duplication check.** No helper duplicates another helper's body. No two helpers share a near-identical shape. No "while I'm here" extraction candidate.

**Severity.** None.

**Recommended action.** **Leave as is.** Zero duplicated helpers across slices.

## Recommendations

For each observation above:

| # | Observation | Disposition | Why |
|---|---|---|---|
| 1 | Sibling formatter envelope at `types/finalizer.py` | **Leave as is** (deferred to future card) | N=2 formatters with differing per-item builders; consolidation pays off only at N≥3. Slice 3 / Slice 4 explicit deferral. |
| 2 | `_OriginAndModel` NamedTuple shape | **Leave as is** | Sibling of `CacheInfo`; the two-NamedTuple cluster pattern is intentional DRY-by-reuse. Not duplication. |
| 3 | H3 dedupe comment is seven lines | **Leave as is** | Content is load-bearing (multi-type-artifact framing); one-line form would lose fidelity. Worker 2 discretion item; Worker 3 / Worker 1 accepted. |
| 4 | Error message conventions | **Leave as is** | Conventions consistent across all five new sites; no outlier. |
| 5 | Plan cache key tuple shape | **Leave as is** (future-card hardening candidate) | Single-source construction; H2 contract pinned by sibling tests at the walker/resolver-helper layers. Stricter cache-only test is a future-card task. |
| 6 | `_OriginAndModel` placement above its producer | **Leave as is** | Stylistic discretion; no DRY consequence. |
| 7 | Two reads of `Meta.primary` | **Leave as is** | Spec contract (Decision 1; `spec:327`). Distinct guard / plumb roles. |
| 8 | Three-helper vocabulary across docs | **Leave as is** | Verified consistent at Slice 6 Worker 3 + Worker 1 verification. No drift. |
| 9 | Ambiguity-rule four-row statement across docs | **Leave as is** | Identical wording across FEATURES + KANBAN; tests pin each rule. |
| 10 | Public-surface (`__all__`) check | **Leave as is** | `__init__.py` unchanged across all six slices. DoD satisfied. |
| 11 | Comments tell one coherent story | **Leave as is** | Every comment describes shipped behavior; no stale TODO anchors remain. |
| 12 | Duplicated helpers across slices | **Leave as is** | Zero duplication. |

**No consolidation loop required.** Every observation in this pass is `leave-as-is` or `future-card escalation` (Observations 1 and 5 only). No High or Medium DRY findings; the two Low items both have prior-slice acceptances on record. The integration pass is clean.

**No spec edits made in this pass.** Slice 2, Slice 4 each made one spec edit during their respective final-verification passes (recorded under their `### Spec changes made (Worker 1 only)` sections). The integration pass surfaced no additional spec gap.

**Sanity test run.** Ran `uv run pytest tests/ --no-cov` during this pass — **610 passed, 3 skipped** in 9.98s. The build's full Slice 1-6 working tree is green at integration-pass time.

## Deferred follow-up catalog

Walked every per-slice `Notes for Worker 1 (spec reconciliation)`, `What looks solid`, and `DRY findings` section for explicit deferrals. These are the items the next spec author should pick up; the final test-run gate (`bld-final.md`'s `### Deferred work catalog`) will reproduce this catalog.

| # | Source | Description | Spec line | Severity / class |
|---|---|---|---|---|
| 1 | `bld-slice-3-ambiguity_audit.md:316-346` (Slice 3 Worker 3 Low) + `:399` (Slice 3 Worker 1 deferral) | Sibling-formatter envelope at `django_strawberry_framework/types/finalizer.py:21-63` — `_format_unresolved_targets_error` and `_format_ambiguity_error` share a three-piece envelope shape. Consolidation deferred to a future slice if a third formatter joins the site. Re-verified at integration; N=2 still. | n/a (DRY discretion) | Low (deferred) |
| 2 | `bld-slice-4-consumer_site_updates.md:415-431` (Slice 4 Worker 3 Low L1) + `:517-518` (Slice 4 Worker 1 deferral) | Plan-cache key test `test_plan_cache_keys_distinguish_primary_and_secondary_returns_for_same_model` does not strictly pin "origin slot is what distinguishes the keys" — the `response_path` slot is sufficient to distinguish the two queries in that single test. Cluster-level coverage from three sibling tests compensates. A stricter pin (e.g., holding `response_path` constant and varying origin only via per-field return-type annotations) is a future-card hardening candidate. | n/a (DRY discretion) | Low (deferred) |
| 3 | `bld-slice-1-registry_multitype.md:255-257` + `:402-409` (Slice 1 ruff drift carry; resolved at slice close but the drift in `scripts/check_spec_glossary.py` predates the build and is intentionally out of scope) | Two pre-existing ruff `D301`/`D103` errors in `scripts/check_spec_glossary.py` are pre-Slice-1 surface drift, not introduced by build-014. The cosmetic ruff-format whitespace/COM812 fixes in the same file are byproducts of `uv run ruff format .` invocations during Slice 1 build. Recorded as out-of-scope at Slice 1; not re-touched in Slices 2-6. The maintainer may fold them into a separate "ruff-format byproduct" commit or accept them with the build commit. | n/a (out-of-scope) | n/a (documentation) |
| 4 | `bld-slice-6-docs_kanban_archive.md:432-433` (Slice 6 Worker 2 notes) + `:516` (Slice 6 Worker 3 notes) + `:553` (Slice 6 Worker 1 final verification) | Forward `WIP-ALPHA-014-0.0.6` cross-references at `KANBAN.md:406` and `KANBAN.md:574` sit inside unrelated TODO cards (`TODO-ALPHA-020-0.0.8` filters; `TODO-ALPHA-026-0.0.11` mutations) and reference this card by its pre-rename identity for design-context dependency. The spec/plan only authorize moving this card's own body; rewriting cross-references is a separate docs-hygiene pass. Worker 1 accepted as historically accurate. | spec line 185-186 (cross-references not authorized) | n/a (docs-hygiene) |
| 5 | `bld-slice-6-docs_kanban_archive.md:518` (Slice 6 Worker 3 notes) | `docs/FEATURES.md:101` and `:887` Index row + body for `Scalar field override semantics` remain `planned for 0.0.6` — that entry is `WIP-ALPHA-015-0.0.6` territory, not this card's. Surfaced only as a flag for the maintainer to confirm `0.0.6` is still the right target version for that card before the patch closes. | n/a (different card) | n/a (different card) |
| 6 | `bld-slice-6-docs_kanban_archive.md:52` (Slice 6 Worker 1 closeout memory) | Snapshot section's parallel stale sub-bullet about deferred scalar conversions is also already-shipped (`DONE-013-0.0.6`) but is out of Slice 6 scope. Flagged for a future docs-hygiene pass. | n/a (out-of-scope) | n/a (docs-hygiene) |

**Catalog summary.** Six deferrals total, all explicitly flagged in prior slice artifacts. Two are Low-severity DRY discretion items where prior-slice review accepted the current shape (#1, #2). Three are docs-hygiene items not authorized by this card's spec checklist (#3, #4, #6). One is a separate-card concern flagged for maintainer awareness (#5). **No deferral blocks build-014 closeout.**

## Final status

`final-accepted`.

### Summary

Cross-slice integration pass for build-014 (`meta_primary / 0.0.6`) read every prior `bld-slice-*.md` artifact (six total, all `final-accepted`), every shadow overview under `docs/builder/shadow/` (six total — registry, types/base, types/definition, types/finalizer, optimizer/walker, optimizer/extension), and the active spec and build plan. Twelve DRY observations were walked:

- **Cross-file string literals.** No build-014 string appears in two or more files; every error message is single-site. Pre-014 repeated literals (`optimizer_hints`, `prefetch`, `selections`, etc.) stay local to their owning files. No centralization candidate.
- **Imports / boundaries.** One-way dependency direction holds end-to-end. No sibling has started importing from outside the documented boundary. `registry.py` is the leaf module; `types/*` reads from `registry` and from `optimizer/*` for shared dataclasses; `optimizer/*` reads from `registry` (upward) and from `optimizer/*` siblings. No new cross-folder import introduced by the build.
- **Maintainer-flagged carry-forwards.** Slice 3's sibling formatters (Observation 1) remain N=2 — consolidation deferred per Slice 3 / Slice 4 Worker 1 acceptance. Slice 4's H3 dedupe seven-line comment (Observation 3) accepted as load-bearing per Slice 4 Worker 1. `_OriginAndModel` NamedTuple (Observation 2) does not duplicate any other NamedTuple in the package — `CacheInfo` and `_OriginAndModel` are the only two, in the same file, sharing the `from typing import NamedTuple` import deliberately. Error message conventions (Observation 4) are consistent across all five new sites.
- **Other DRY axes.** Plan cache key tuple (Observation 5) constructed at a single site with cluster-level test coverage. Two-reads of `Meta.primary` (Observation 7) are the spec-pinned shape. Three-helper vocabulary (Observation 8) and ambiguity-rule four-row statement (Observation 9) consistent across docs surfaces. Public surface (Observation 10) unchanged. Comments tell one coherent story (Observation 11). Zero duplicated helpers across slices (Observation 12).

The pass is clean: no High / Medium findings; the two Low items both have prior-slice acceptances on record (Slice 3 envelope deferral, Slice 4 cache-test deferral). **No consolidation loop required**, no Worker 2 dispatch needed. Six deferrals are catalogued for the final test-run gate's `### Deferred work catalog` and the next spec author's reading list. Full `uv run pytest tests/ --no-cov` run during this pass confirmed 610 passed / 3 skipped — the build's Slice 1-6 working tree is green at integration time.

### Spec changes made (Worker 1 only)

None.
