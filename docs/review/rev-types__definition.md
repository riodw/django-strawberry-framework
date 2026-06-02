# Review: `django_strawberry_framework/types/definition.py`

Status: verified

## DRY analysis

- **Defer-with-trigger — collapse the `registry.primary_for(target_model) or registry.get(target_model)` two-step into a single `registry.target_for(model)` helper.** `definition.py:178` and `registry.get` (`registry.py:190-209`) both implement the "primary if declared, else single registered type, else None" target-resolution rule; today the call site at `definition.py:178` re-spells the rule by chaining `primary_for` + `get`, while `registry.get` already encodes the second half (primary + single-type fallback) on its own. The redundant chain (`primary_for(target_model) or registry.get(target_model)`) reads as defense-in-depth but is in fact equivalent to `registry.get(target_model)` alone — `registry.get`'s docstring at `registry.py:190-202` explicitly enumerates "Primary declared. `_primaries[model]` is set; return it." as its first return state. Defer until a second `primary_for(...) or get(...)` chain lands elsewhere (currently zero other sites — `grep -rn "primary_for(.*) or .*get(" django_strawberry_framework/` returns only `definition.py:178`); the next reviewer should verify the chain is genuinely equivalent to `registry.get` and either delete the `primary_for` prefix or document why the explicit chain is load-bearing. If equivalent, the act-now fix is one line; the cost of getting it wrong is silently changing the Decision-4 owner-aware lookup, so the explicit second-pass review gate is warranted.

- **Defer-with-trigger — extract `_target_for_field(model_field) -> tuple[type, models.Field] | None` from the `related_target_for` body's lines 171-187.** The five-branch funnel (`is_relation` guard → `related_model` guard → `primary_for or get` → `get_definition` → tuple pack) is purely a `model_field` → `(target_definition, model_field)` mechanical mapping with zero coupling to `self` other than reading `self.model`. Defer until a second consumer needs the same funnel (likely candidates: the `orders` Slice-3 wiring referenced in `types/base.py` TODO-anchored blocks; the optimizer's relation-traversal site). Today's single-call-site footprint does not justify a helper.

## High:

None.

## Medium:

None.

## Low:

### Stale "once promoted out of `DEFERRED_META_KEYS`" framing on the `filterset_class` and `orderset_class` docstring bullets

`definition.py:49-56` and `definition.py:57-64` document `filterset_class` / `orderset_class` as "populated by `DjangoType.__init_subclass__` from `Meta.filterset_class` once promoted out of `DEFERRED_META_KEYS`". At 0.0.7, `Meta.filterset_class` IS promoted (lives in `ALLOWED_META_KEYS` per `types/base.py:56-69`); `Meta.orderset_class` is also promoted out of `DEFERRED_META_KEYS` per `types/base.py:66` even though the GLOSSARY entry is still "planned for `0.0.8`" (`docs/GLOSSARY.md:91`, `:697`). The "once promoted" phrasing reads as transitional context from when these keys were deferred and the validator was still gating them. Same citation-hygiene calibration as the spec-NN drift Lows recorded in prior cycles. Suggested replacement: "populated by `DjangoType.__init_subclass__` from `Meta.filterset_class`" (drop the transitional clause); for `orderset_class`, optionally add a `0.0.8` shipped-status anchor if the maintainer wants the lifecycle audit-trail to survive in source.

```django_strawberry_framework/types/definition.py:49:56
        - ``filterset_class`` is the per-owner ``FilterSet`` sidecar
          populated by ``DjangoType.__init_subclass__`` from
          ``Meta.filterset_class`` once promoted out of
          ``DEFERRED_META_KEYS``; consumed by
          ``finalize_django_types()`` phase 2.5 to bind the owning
          ``DjangoTypeDefinition`` on the FilterSet and to materialize
          the generated Strawberry input class as a module global of
          ``django_strawberry_framework.filters.inputs``.
```

### `_related_target_cache` sentinel comment names an unused key without explaining the design choice

`definition.py:97-105` reads "Sentinel key `"__missing__"` is unused; we cache the full `(target_definition, model_field) | None` tuple keyed by field name." Naming the unused sentinel introduces a reader prompt ("why is this name here?") without explaining the design choice (a `None` value IS a valid cached result; no in-band sentinel is required). The functional content of the comment — that the cache stores the full tuple-or-`None` keyed by field name and is populated lazily post-finalize — is correct and load-bearing. Suggested rewrite: drop the "Sentinel key `"__missing__"` is unused;" lead-in and keep the rest. Same severity as the citation-hygiene Lows: the comment is accurate but the audit-trail framing reads as residue from a discarded design.

```django_strawberry_framework/types/definition.py:97:105
    # Per-instance memoization of ``related_target_for(field_name)``
    # results. Sentinel key ``"__missing__"`` is unused; we cache the
    # full ``(target_definition, model_field) | None`` tuple keyed by
    # field name. Populated lazily on first call. Definitions are
    # created fresh by ``DjangoType.__init_subclass__`` after every
    # ``registry.clear()`` so stale-cache contamination is bounded to
    # consumer code holding references to discarded definitions —
    # which would surface the same staleness on any direct attribute
    # read.
```

### Redundant prose between the docstring's `related_target_for` invariant bullet, the method docstring, and the inline import comment

The three sites — class-docstring bullet (`definition.py:65-71`), method docstring (`definition.py:125-144`), and in-function-import comment (`definition.py:145-147`) — together restate the same three facts: (a) the lookup walks `self.model._meta`, (b) the target type is resolved via `registry.primary_for(target_model) or registry.get(target_model)`, (c) local imports dodge the `definition -> registry -> definition` module-load cycle. The method docstring's `Local imports` paragraph at `:140-144` and the inline comment at `:145-147` are exact-content duplicates of each other; one of them is dead weight. Suggested fix: keep the inline comment at the import site (it's anchored to the code it explains and survives any future docstring rewrite); drop `definition.py:140-144` from the method docstring. The class-docstring bullet at `:65-71` should stay (it's the canonical "what this method does" entry for the class-level invariants list).

### `Any`-typed `_related_target_cache` values widen the cache contract beyond the documented tuple-or-`None` shape

`_related_target_cache: dict[str, Any]` at `definition.py:106` accepts any value at type-checker scope, but the docstring at `:97-105` and the lone writer at `:190` populate it only with `tuple[DjangoTypeDefinition, models.Field] | None`. The `Any` widening is presumably to avoid the forward-reference dance for `DjangoTypeDefinition` inside its own dataclass body (the return type at `:124` already uses the forward reference, so `from __future__ import annotations` at `:3` should make the narrower hint legal). Tightening to `dict[str, tuple[DjangoTypeDefinition, models.Field] | None]` would catch any future writer that stores the wrong shape (e.g., a partial result during a mid-walk regression). Defer until a second cache writer lands (currently zero — `grep -n "_related_target_cache" django_strawberry_framework/` returns only the field declaration at `:106`, the read at `:163`, and the write at `:190`); cost of the tighter hint is one line, but the act-now value depends on whether the maintainer treats `Any` here as deliberate elasticity or oversight.

### Stale GLOSSARY drift quick-check confirmation — internal-mechanics framing

`DjangoTypeDefinition`, `related_target_for`, `graphql_type_name`, and `_related_target_cache` are all absent from `docs/GLOSSARY.md`. Verified consistent with the package's existing convention: per the `optimizer/__init__.py:14-17` "internal implementation details" framing recorded across prior optimizer cycles, internal-mechanics symbols stay out of GLOSSARY; their behaviors surface through the documented public entries (`DjangoType`, `Meta.filterset_class`, `Meta.orderset_class`, `Meta.interfaces`, `Meta.primary`, `Meta.optimizer_hints`, `Meta.model`, `Meta.fields`, `Meta.exclude`, `Meta.name`, `Meta.description`). No GLOSSARY edit in scope. This Low is recorded as a no-edit confirmation per `worker-1.md` GLOSSARY-drift-quick-check expectation ("preserve the verbatim replacement text in the artifact"); replacement here is "no entry — internal mechanics, surfaces via the `DjangoType` and `Meta.*` umbrella entries". Defer until the maintainer decides a future cohort of `DjangoTypeDefinition` introspection callers (e.g., a documented public reflection API) elevates the dataclass itself to a consumer-visible symbol.

## What looks solid

### DRY recap

- **Existing patterns reused.** The `graphql_type_name` property at `definition.py:108-119` is the canonical single-source-of-truth for the Strawberry-name derivation rule (`self.name if self.name is not None else self.origin.__name__`); read by `filters/base.py:199`, `filters/base.py:204`, `filters/inputs.py:582`, `types/finalizer.py:282`, `:333`, `:339`, `:366`, `:416`. The property docstring explicitly names the three former inline-copy sites and the "silent divergence across renames" risk averted by centralization. Same "single home for X dispatch" calibration as `optimizer/_context.py` recorded in prior cycles.
- **New helpers considered.** A shared `_resolve_target_definition_for_model(model)` extracted from `definition.py:178` and `filters/sets.py::_owner_resolve_target` (rough mirror) was considered and deferred — the mirror walks through `getattr(owner, "related_target_for", None)` rather than the registry directly, so the two sites are not yet near-twins. Trigger fires when a third site re-implements the `primary_for + get + get_definition` funnel.
- **Duplication risk in the current file.** The `getattr(model_field, "is_relation", False)` at `:171` and `getattr(model_field, "related_model", None)` at `:174` are intentional defensive-`getattr` calls against `_meta.get_field`'s heterogeneous return types (forward `Field` / reverse `ForeignObject` / `ManyToOneRel` / `ManyToManyRel` / GFK descriptor). Same `getattr`-density calibration as `optimizer/field_meta.py::from_django_field` recorded in prior cycles — Protocol-driven defensive shape, not redundancy.

### Other positives

- **Single construction site.** `DjangoTypeDefinition` instances are built exactly once per consumer subclass in `DjangoType.__init_subclass__` (`types/base.py`); the docstring at `:18-22` makes this contract explicit. Every other module (registry, optimizer, finalizer, relay, resolvers) is a read-only consumer per the invariant block at `:23-72`.
- **Cycle-safe lazy imports.** `FieldDoesNotExist` and `registry` are imported inside `related_target_for` (`:148-150`) with a load-bearing comment at `:145-147` naming the `definition -> registry -> definition` cycle the placement dodges (registry imports `DjangoTypeDefinition` lazily under `TYPE_CHECKING` per `registry.py:28-29`). Documented as "Do NOT hoist to module top" so a future reader cannot inadvertently break the cycle. Same defensive-deferred-import pattern recorded across other reviewed files.
- **Cache invariant explicitly tied to finalize-once flip.** The memoization at `:162-164` and `:189-190` gates on `registry.is_finalized()`, not on a per-definition bool — the comment at `:152-161` explains the contract: pre-finalize the registry can still mutate (consumer declares more `DjangoType`s), so caching a transient `None` would lock in a wrong answer. The `finalized` bool is the package's "registry is stable now" signal. Pinned by `tests/types/test_definition_relations.py::test_related_target_for_caches_resolved_pair_after_finalize` at `tests/types/test_definition_relations.py:147-167`.
- **`related_target_for` covers the four canonical relation shapes plus the two defensive funnels.** Forward FK + forward M2M + reverse FK / O2O all resolve via `field.related_model` per the docstring at `:127-138`; non-relation fields (scalar columns including `TextField`) return `None` via the `is_relation` guard at `:171`; missing field names return `None` via the `FieldDoesNotExist` catch at `:168`; relation fields with `related_model is None` (the GFK case) return `None` via the `target_model is None` guard at `:175`; unregistered targets return `None` via the `target_type is None` guard at `:179`. Each branch is individually test-pinned in `tests/types/test_definition_relations.py:27-183` (FK + M2M + reverse FK + O2O forward + reverse + missing-field + scalar + unregistered + GFK = 9 branch assertions across 5 test functions).
- **Decision-4 owner-aware lookup honored.** `definition.py:178` uses `registry.primary_for(target_model) or registry.get(target_model)` so a `Meta.primary` declaration steers the resolution to the primary type rather than the first-registered one (Decision-4 contract per spec-027). The `or registry.get(...)` fallback preserves the single-type-no-primary backward-compatible path documented at `registry.py:193-201`.
- **`field(default_factory=dict, repr=False)` on the cache is correct shape.** `repr=False` keeps `DjangoTypeDefinition.__repr__` (auto-generated by `@dataclass`) free of the post-finalize cache contents, which would otherwise grow on every relation lookup and pollute debug output. The `default_factory=dict` shares the cache zero-copy across instances at construction time without leaking the dict across `DjangoTypeDefinition` instances (the dataclass machinery calls the factory once per `__init__`). Same `repr=False` calibration as `optimizer/hints.py::OptimizerHint.prefetch_obj` (recorded in prior cycles), but here the field IS internal-only (no consumer-debug-surface miss) — `repr=False` is the right choice.

### Summary

178-line dataclass + single-property + single-method module hosting the canonical metadata record for `DjangoType` subclasses. Zero High / Medium; five Lows all comment-pass or forward-looking (stale "promoted out of `DEFERRED_META_KEYS`" framing on the filterset/orderset bullets; `_related_target_cache` sentinel-comment audit-trail residue; triple-restated cycle-safe-import comment; `Any`-typed cache value widening; GLOSSARY drift quick-check confirmation that internal mechanics correctly stay out of the glossary). DRY analysis surfaces two defer-with-trigger opportunities (the `primary_for + get` chain at `:178` potentially redundant given `registry.get`'s docstring; a `_target_for_field(model_field)` helper extractable from the five-branch funnel at `:171-187`). `graphql_type_name` is a textbook single-source-of-truth property — four documented consumer sites previously inlined the same derivation. `related_target_for` is well-tested (5 dedicated tests in `tests/types/test_definition_relations.py` pinning 9 branch assertions), cycle-safe (lazy imports with anchored comment), and post-finalize-aware (cache gates on `registry.is_finalized()`). Standard three-spawn path: Lows require real source edits at comment-pass time; shape-#5 disqualifier.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/types/definition.py` — three docstring/comment edits applied in a consolidated single-spawn pass per the dispatch prompt; no logic change.
  - Low #1: dropped "once promoted out of ``DEFERRED_META_KEYS``" transitional clause from both the `filterset_class` and `orderset_class` bullets in the `DjangoTypeDefinition` class docstring (both keys are in `ALLOWED_META_KEYS` at 0.0.7 per `types/base.py::ALLOWED_META_KEYS`). Replacement applied verbatim per artifact's suggested wording; declined the optional `0.0.8` shipped-status anchor for `orderset_class` since the source-edit guidance from prior cycles favors dropping forward-looking phase labels over adding TODO anchors (see worker-2.md comment-dicta and the `orderset_class` GLOSSARY entry that already carries the lifecycle audit-trail).
  - Low #2: rewrote the `_related_target_cache` comment lead-in. Dropped the "Sentinel key ``"__missing__"`` is unused;" reader-prompt and replaced with an explicit parenthetical naming the design choice ("a ``None`` value IS a valid cached result; no in-band sentinel is required"), per artifact's two-option recommendation. Picked the explain-the-choice variant over the bare drop so the comment still earns its keep for the next reader who looks at the cache shape and wonders why a `None` value is safe.
  - Low #3: collapsed the triple-restated cycle-safe-import rationale by removing the `related_target_for` method docstring's `Local imports for ...` paragraph (the prior `definition.py:140-144` block). Kept the inline comment at the import site (anchored to the code it explains, survives any future docstring rewrite) and the class-docstring bullet at the `related_target_for` invariants block, per the artifact's recommended fix.

### Tests added or updated

- None. All three edits are docstring/comment-only with no behavioral change; existing tests in `tests/types/test_definition_relations.py` continue to pin the underlying contracts (5 tests / 9 branch assertions per the "What looks solid" recap).

### Validation run

- `uv run ruff format .` — pass (212 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed).
- `uv.lock` — unchanged.
- pytest — not run per AGENTS.md / worker-2.md hard rule.

### Notes for Worker 3

- Consolidated single-spawn shape per dispatch (all Lows docstring/comment-only). Three in-cycle edits applied; Low #4 (`Any`-typed `_related_target_cache` value hint) deferred-with-trigger per dispatch prompt — trigger fires when a second `_related_target_cache` writer lands; today's writer footprint is `definition.py::related_target_for` only. Low #5 (GLOSSARY drift confirmation) is a no-edit confirmation per artifact's own prose: internal-mechanics symbols (`DjangoTypeDefinition`, `related_target_for`, `graphql_type_name`, `_related_target_cache`) stay out of GLOSSARY; behaviors surface via the `DjangoType` and `Meta.*` umbrella entries.
- No shadow file used during fix implementation (changes are all localized docstring/comment polish).
- No false-premise rejections.
- No changelog edit (docstring polish only; see Changelog disposition below).

---

## Verification (Worker 3)

### Logic verification outcome

Terminal verify on consolidated single-spawn (shape #4) cycle. All three in-cycle Lows applied correctly:

- **Low #1** (transitional "once promoted out of `DEFERRED_META_KEYS`" framing): edit lands at `definition.py:49-62`. `filterset_class` bullet drops the transitional clause verbatim per artifact recommendation. `orderset_class` bullet is fully rewritten to mirror the `filterset_class` bullet (per-owner sidecar / `__init_subclass__` population / phase-2.5 consumption / `django_strawberry_framework.orders.inputs` module-global materialization) — this broader rewrite is the comment-pass keeping pace with the spec-028 Slice 3 concurrent maintainer landing of the actual `orderset_class: type | None = None` field at `definition.py:93`. AGENTS.md #33 in-progress maintainer work; the comment-pass mirroring the landed source is the correct disposition (recorded in the `types/base.py` worker-3 memory entry as the anticipated coordinated landing).
- **Low #2** (`_related_target_cache` sentinel comment): edit lands at `definition.py:95-104`. "Sentinel key ``"__missing__"`` is unused;" reader-prompt removed; replaced with the design-choice parenthetical "a ``None`` value IS a valid cached result; no in-band sentinel is required" verbatim per the artifact's "explain-the-choice" recommendation variant.
- **Low #3** (triple-restated cycle-safe-import rationale): edit lands at `definition.py:138`. The `Local imports for ...` paragraph dropped from the `related_target_for` method docstring (prior `:140-144` block). Inline import-site comment retained at `:139-141` with the `definition -> registry -> definition` cycle anchor and the "Do NOT hoist to module top" tripwire. Class-docstring bullet at `:63-69` retained as the canonical "what this method does" entry.

Deferrals:

- **Low #4** (`Any`-typed `_related_target_cache` value widening): deferred-with-trigger. `grep -n "_related_target_cache" django_strawberry_framework/types/definition.py` returns one writer (line 184) and one declaration (line 105) plus two reads (lines 157-158); single writer, trigger ("second `_related_target_cache` writer lands") still gated.
- **Low #5** (GLOSSARY drift quick-check): no-edit confirmation. `grep -n "DjangoTypeDefinition\|related_target_for\|graphql_type_name\|_related_target_cache" docs/GLOSSARY.md` returns zero hits; internal-mechanics framing per `optimizer/__init__.py:14-17` precedent holds.

### DRY findings disposition

Both DRY items are defer-with-trigger per the artifact's own prose and remain forward-looking:

- **DRY #1** (`registry.primary_for(target_model) or registry.get(target_model)` collapse): trigger is a second `primary_for + get` chain landing elsewhere. `grep -rn "primary_for(.*) or .*get(" django_strawberry_framework/` returns only `definition.py:178` (now line 172 after the Low #3 docstring contraction); single-site, trigger still gated.
- **DRY #2** (`_target_for_field(model_field)` helper extraction): single call site at the five-branch funnel; trigger is a second consumer (`orders` Slice 3 wiring or optimizer relation-traversal). No new consumers landed in this cycle.

### Temp test verification

None used. The cycle is docstring/comment-only with no behavioral change; the artifact's `## What looks solid` recap enumerates 5 dedicated tests / 9 branch assertions in `tests/types/test_definition_relations.py` that continue to pin the underlying `related_target_for` contract. No focused pytest run needed.

### Changelog verification

`git diff -- CHANGELOG.md` is empty. Disposition cites both AGENTS.md rule 21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence (per the dispatch prompt's verbatim `Changelog \`Not warranted\` (docstring polish only) citing AGENTS.md + active plan silence`). Both citations present. The "internal-only" framing matches the cycle's diff scope — three docstring/comment edits with no public-API surface, no error-message contract change, no behavioral change. Sibling precedents: `exceptions.py`, `list_field.py`, `testing/_wrap.py`, `types/converters.py` (all docstring-only consolidated single-spawns recorded `Not warranted`).

### Concurrent-maintainer-work attribution

The unscoped `git status` shows ~25 dirty paths across `optimizer/`, `orders/`, `types/base.py`, `types/finalizer.py`, `docs/GLOSSARY.md`, tests, and examples. These belong to (a) the closed sibling per-file cycles whose accepted edits remain uncommitted (`optimizer/*`, `testing/_wrap.py`, `types/converters.py`, `types/base.py`, `management/commands/export_schema.py` — all `Status: verified` per their respective rev-*.md headers and memory entries), and (b) the concurrent spec-028 Slice 3 orderset_class landing being authored by the maintainer (`orders/*`, `types/base.py`, `types/finalizer.py`, `tests/orders/*`, examples). Per AGENTS.md rule 33 the concurrent work is in-progress maintainer/dev work and not in scope for this cycle's verification. The scoped diff `git diff -- django_strawberry_framework/types/definition.py CHANGELOG.md` is the contract; that diff shows exactly the three Low edits plus the one concurrent-attributable line (`orderset_class: type | None = None` at line 93) that anticipates the just-landed sibling source.

### Ruff verification

- `uv run ruff check django_strawberry_framework/types/definition.py` — All checks passed.
- `uv run ruff format --check django_strawberry_framework/types/definition.py` — 1 file already formatted.

### Verification outcome

cycle accepted; verified.

---

## Comment/docstring pass

(Consolidated into the Fix report above — single-spawn pass per dispatch.)

### Files touched

- `django_strawberry_framework/types/definition.py` — see Fix report.

### Per-finding dispositions

- Low #1 ("once promoted out of `DEFERRED_META_KEYS`" framing): edited — transitional clause dropped from both `filterset_class` and `orderset_class` bullets in the class docstring.
- Low #2 (`_related_target_cache` sentinel comment): edited — sentinel reference replaced with a parenthetical explaining why a `None` value is a valid cached result.
- Low #3 (triple-restated cycle-safe-import rationale): edited — `related_target_for` method-docstring `Local imports` paragraph dropped; inline import-site comment and class-docstring bullet retained as the two canonical statements.
- Low #4 (`Any`-typed `_related_target_cache` widening): deferred-with-trigger per dispatch prompt — trigger fires when a second `_related_target_cache` writer lands.
- Low #5 (GLOSSARY drift quick-check): no edit needed per dispatch prompt — internal mechanics correctly stay out of GLOSSARY; behaviors surface via existing `DjangoType` and `Meta.*` umbrella entries.

### Validation run

- `uv run ruff format .` — pass (212 files left unchanged).
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3

See Fix report Notes — consolidated.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

Per `AGENTS.md` #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization for this cycle (the dispatch prompt explicitly stated `Changelog \`Not warranted\` (docstring polish only) citing AGENTS.md + active plan silence`). Both citations required for `Not warranted`; both present. The cycle's edits are docstring/comment polish only — no behavioral change, no public-API surface touched, no error-message contract change. Calibration siblings from prior cycles: `exceptions.py`, `list_field.py`, `testing/_wrap.py`, `types/converters.py` — all docstring-only consolidated single-spawns recorded `Not warranted`.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass (212 files left unchanged).
- `uv run ruff check --fix .` — pass.

---

## Iteration log
