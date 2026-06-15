# Review: `django_strawberry_framework/conf.py`

Status: verified

## DRY analysis

- None — `_normalize_user_settings` is already the single shared shape-contract chokepoint for all three cache-write sites (`Settings.__init__` eager construction, `Settings.user_settings` lazy read, `Settings.reload` signal/direct replacement); the `None`-passthrough wrapper (`None if value is None else _normalize_user_settings(value)`) appears at `conf.py:101` and `conf.py:131` but inlining a two-token ternary into a named helper would add indirection without removing a real near-copy, and the two sites differ in source (constructor arg vs. reload arg). Current factoring is correct.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_normalize_user_settings` (`conf.py:50-83`) is the one validator/normalizer reused by `Settings.__init__` (`conf.py:100-102`), `Settings.user_settings` (`conf.py:118-122`), and `Settings.reload` (`conf.py:131`); the module docstring (`conf.py:17-35`) explicitly cross-references the parallel `Meta.optimizer_hints = None` seam in `types/base.py` and warns against unifying the consumer-input `None`-coercion with the optimizer's reflective-shape `or {}` reads — the boundary is documented, not accidental.
- **New helpers considered.** A `_load_or_none(value)` wrapper around the `None if value is None else _normalize_user_settings(value)` ternary (sites `conf.py:101`, `conf.py:131`) — rejected; the ternary is two tokens, both call sites read clearly inline, and a helper would obscure that one path comes from a constructor argument and the other from `reload`.
- **Duplication risk in the current file.** The `DJANGO_SETTINGS_KEY` literal is referenced in `_normalize_user_settings` error text (`conf.py:79`), the lazy `getattr` (`conf.py:120`), and `reload_settings`' guard (`conf.py:173`) — all via the module constant `DJANGO_SETTINGS_KEY` (`conf.py:46`), never as a repeated string literal; the static overview confirms zero repeated string literals. Correct.

### Other positives

- **Single shape contract, fail-loud on non-mapping.** `_normalize_user_settings` raises `ConfigurationError` (verified present at `exceptions.py:20`) naming the received type for any non-`Mapping`, replacing the old `or {}` collapse that silently absorbed every falsy value; `None` and missing-key remain the documented "no settings configured" empty-mapping shape. The dict fast-path preserves identity (`conf.py:81-83`) so test fixtures capturing the dict by reference observe mutations.
- **`__getattr__` recursion safety.** The handler short-circuits `user_settings` / `_user_settings` and dunder names with a bare `AttributeError` (`conf.py:147-148`) before touching the `@property`, so a malformed-config `ConfigurationError` cannot recurse through the handler; only `KeyError` is converted to `AttributeError` (`conf.py:155-156`), letting `ConfigurationError` propagate through `hasattr` / `getattr(default=...)` probes by design. The inline comment (`conf.py:150-153`) explains why `user_settings` stays a `@property`.
- **In-place mutation over rebind.** `reload_settings` mutates the singleton via `settings.reload(value)` (`conf.py:173-174`) rather than rebinding the module global, so `from .conf import settings` bindings see fresh values; thread-safety caveat is honestly documented as test-only (`conf.py:112-116`).
- **Idempotent import-time signal wiring.** `setting_changed.connect(..., dispatch_uid=_DISPATCH_UID)` (`conf.py:182`) is idempotent on re-import; the comment (`conf.py:177-181`) justifies why AppConfig.ready() is not a viable home (consumers import `conf` before app loading during test bootstrap).
- **Completeness stance respected.** No settings keys are populated here; the only documented consumer key (`RELAY_GLOBALID_STRATEGY`) is read elsewhere through this thin reader, matching AGENTS.md "add settings keys only when the feature that needs them lands." GLOSSARY entries for `RELAY_GLOBALID_STRATEGY` (`GLOSSARY.md:1096-1106`) and `ConfigurationError` (`GLOSSARY.md:230`) are accurate and consistent with this file's role — no drift.

### Summary

`conf.py` is a thin, well-factored settings reader with a single shared normalization chokepoint, fail-loud validation on malformed (non-mapping) config, recursion-safe `__getattr__`, and honestly-documented test-only thread-safety and `None`-coercion contracts. The cycle diff against the baseline is empty, the static overview reports zero control-flow hotspots / ORM markers / repeated literals, GLOSSARY is in sync, and no High/Medium/Low issues exist. Qualifies as a no-findings (shape #1) + no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 267 files left unchanged.
- `uv run ruff check --fix .` — pass; all checks passed (only the pre-existing COM812/formatter advisory warning, unrelated to this file).

### Notes for Worker 3
- Shadow overview used: `docs/shadow/django_strawberry_framework__conf.overview.md` (read-only; not regenerated this cycle — source timestamp older than the plan-time `--all` sweep).
- Cycle diff `git diff 96f12c3dc9d81ef1bf8c43e114e795f413935679 -- django_strawberry_framework/conf.py` is empty.
- All severities `None.`; DRY analysis is the single justified `None` bullet.
- No GLOSSARY-only fix in scope — GLOSSARY entries for `RELAY_GLOBALID_STRATEGY` and `ConfigurationError` verified accurate, no edit needed.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source, test, GLOSSARY, or any tracked-file edits this cycle. AGENTS.md: "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_10.md` records no changelog directive for this item.

---

## Verification (Worker 3)

Terminal verification of a no-findings (shape #1) + no-source-edit (shape #5) cycle. Re-read source `django_strawberry_framework/conf.py` and shadow overview `docs/shadow/django_strawberry_framework__conf.overview.md` (shadow line numbers treated as non-canonical per the shadow-file dictum; used only for control-flow corroboration).

### Logic verification outcome
No High/Medium/Low to disposition — all three severities are `None.` and I confirm no missed finding warrants reopening:
- Fail-loud non-mapping validation in `_normalize_user_settings` (`conf.py:75-83`) raises `ConfigurationError` (def confirmed at `exceptions.py:20`) naming the received type; `None`/missing-key coerce to `{}` per the documented package-wide `None` stance (module docstring `conf.py:17-35`). Not a defect.
- Missing settings keys raising `AttributeError` via `__getattr__` (`conf.py:155-156`) is intended per AGENTS.md ("missing keys raise AttributeError"; "add settings keys only when the feature that needs them lands") — absence is NOT flagged as a defect.
- `__getattr__` recursion safety (dunder + `user_settings`/`_user_settings` short-circuit at `conf.py:147-148`, only `KeyError`→`AttributeError`) is sound; `ConfigurationError` propagating through `hasattr`/`getattr(default=...)` is by-design fail-loud.
- Idempotent import-time `setting_changed.connect(..., dispatch_uid=_DISPATCH_UID)` (`conf.py:182`) and in-place `settings.reload(value)` (`conf.py:173-174`) over rebind — both correct, honestly documented.

### DRY findings disposition
DRY=`None` (single justified bullet). Confirmed sound: `_normalize_user_settings` is the lone shape-contract chokepoint shared by all three cache-write sites (`__init__` `conf.py:100-102`, `user_settings` `conf.py:118-122`, `reload` `conf.py:131`). The `None if value is None else _normalize_user_settings(...)` ternary at `conf.py:101`/`conf.py:131` is correctly left inline — two tokens, distinct sources (constructor arg vs reload arg); a `_load_or_none` wrapper would add indirection without removing a real near-copy. `DJANGO_SETTINGS_KEY` referenced via the module constant, never as a repeated literal (shadow confirms zero repeated string literals). Carried forward: nothing.

### Temp test verification
- No temp tests created — no source edit, no behavior to pin beyond what the existing suite covers.
- Disposition: n/a.

### Shape #5 checklist
1. `git diff 96f12c3... -- django_strawberry_framework/conf.py` empty; `git diff --stat 96f12c3... -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty for cycle-owned paths. Working-tree dirty files (`__init__.py`, `pyproject.toml`, `uv.lock`, `docs/bug_hunt/dicta.md`) all diff-empty vs the baseline SHA — pre-baseline orchestrator/version-bump work per AGENTS.md #33, not this item's edits.
2. Both Worker 2 sections (`## Fix report`, `## Changelog disposition`) start with `Filled by Worker 1 per no-source-edit cycle pattern.` — confirmed.
3. No Low findings to forward; no GLOSSARY-only fix in scope. GLOSSARY entries for `RELAY_GLOBALID_STRATEGY` and `ConfigurationError` confirmed present and accurate (anchors `#relay_globalid_strategy`, `#configurationerror`); the artifact's raw line cites are slightly stale but per AGENTS.md #27 line numbers are non-authoritative in standing-doc references — anchor/entry existence is what matters. In sync.
4. Changelog `Not warranted` cites BOTH AGENTS.md and the active plan's silence; `git diff -- CHANGELOG.md` empty. Internal-only framing honest — cycle touched no public-API surface.
5. `uv run ruff format --check` (1 file already formatted) + `uv run ruff check` (all checks passed) — pass; only the pre-existing COM812/formatter advisory, unrelated.

### Verification outcome
cycle accepted; verified — sets top-level `Status: verified` AND marks the `conf.py` checklist box in `docs/review/review-0_0_10.md`.
