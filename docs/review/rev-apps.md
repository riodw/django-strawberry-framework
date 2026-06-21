# Review: `django_strawberry_framework/apps.py`

Status: verified

## DRY analysis

- **Shared `apply()`-scaffold consolidation across the three patch modules — forward to project pass, not a local finding.** `_cross_web_patches.py`, `_django_patches.py`, and `_strawberry_patches.py` each expose an `apply()` with an identical scaffold (toggle gate on `APPLY_UPSTREAM_PATCHES` + once-only missing-symbol notice + re-entrancy guard + import-time `ImportError` capture). `apps.py::DjangoStrawberryFrameworkConfig.ready` (`django_strawberry_framework/apps.py:38-44`) is the dispatch site that imports all three and calls them in sequence. The natural home of any shared-scaffold consolidation is the three modules themselves (or a shared helper they import), coordinated through the project pass. **Defer to `rev-django_strawberry_framework.md`**: all three per-file artifacts already carry this same forward, so the project pass collects them in one place. Do NOT duplicate it as a local `apps.py` finding.
- **`ready()` itself does not warrant a dispatch-table / iteration refactor.** The three `apply_*()` calls (`django_strawberry_framework/apps.py:42-44`) are three explicit named calls, not string-keyed dispatch over a collection. Folding them into a `for fn in (apply_django, apply_strawberry, apply_cross_web): fn()` loop would trade an explicit, greppable, order-visible call sequence for marginal line savings and obscure the deliberate ordering. Keep the explicit calls; no consolidation here.

## High:

None.

## Medium:

### GLOSSARY prose for `DjangoStrawberryFrameworkConfig.ready` is stale — describes a single-patch `ready()`

`docs/GLOSSARY.md:308` (the `## Django AppConfig` entry, a documented public-contract symbol) still describes `ready()` as it existed in `0.0.7`:

> The `ready()` body imports `django_strawberry_framework._django_patches` and calls `apply()` to install the [Django Trac #37064 hardening](#django-trac-37064-hardening) at Django app-load time.

The current `ready()` (`django_strawberry_framework/apps.py:38-44`) imports and calls **three** patch modules, not one: `_cross_web_patches`, `_django_patches`, and `_strawberry_patches`, all gated by the `APPLY_UPSTREAM_PATCHES` setting (default on). The prose understates the contract — a consumer reading the GLOSSARY would not learn that the non-UTF-8 request-body `500` fix (Strawberry + cross-web halves) is also installed at `ready()` time, nor that the `APPLY_UPSTREAM_PATCHES` toggle governs all of them.

This is a documented public-contract symbol, so per the GLOSSARY drift quick-check this is **Medium** (not Low). The source itself is correct and unchanged from HEAD; only the GLOSSARY prose is stale. This is a GLOSSARY-only edit and routes through the standard fix flow (shape #4 — Worker 2 makes the edit) — it does NOT qualify for the no-source-edit shape #5.

Verbatim replacement for the sentence at `docs/GLOSSARY.md:308` beginning "The `ready()` body imports" (replace exactly that one sentence; keep the preceding `name`/`verbose_name` clause and the following `INSTALLED_APPS` discovery sentence unchanged):

> The `ready()` body imports the package's three defensive patch modules — `django_strawberry_framework._cross_web_patches`, `django_strawberry_framework._django_patches`, and `django_strawberry_framework._strawberry_patches` — and calls each module's `apply()` at Django app-load time: `_django_patches` installs the [Django Trac #37064 hardening](#django-trac-37064-hardening) (test-only), while `_strawberry_patches` and `_cross_web_patches` install the non-UTF-8 request-body `500` fix for Strawberry's HTTP view (production request handling); all three are gated by the `APPLY_UPSTREAM_PATCHES` setting (default on), and each `apply()` self-gates, is idempotent, and is self-healing, so a consumer who sets `DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": False}` gets none of them.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `ready()` (`django_strawberry_framework/apps.py:38-44`) is a thin dispatcher: it lazily imports each patch module's `apply()` inside the method (correct — avoids import-time side effects and circular-import risk, and guarantees Django is fully configured before any patch runs) and calls all three. It carries no logic of its own to duplicate.
- **New helpers considered.** An iteration/dispatch-table refactor over the three `apply_*` callables was considered and rejected — three explicit named calls are clearer and preserve visible ordering; see DRY analysis.
- **Duplication risk in the current file.** None within the file. The cross-module `apply()`-scaffold duplication is real but lives in the three patch modules, not here; it is forwarded to the project pass. The one repeated literal `"django_strawberry_framework"` (`name`) is the framework-mandated app label, not an extractable constant.

### Other positives

- **Lazy imports inside `ready()`.** All three `apply` imports are method-local (`django_strawberry_framework/apps.py:38-40`), the correct AppConfig idiom — module import time stays side-effect-free.
- **Explicit, deterministic patch ordering.** `apply_django()` then `apply_strawberry()` then `apply_cross_web()` (`django_strawberry_framework/apps.py:42-44`) is a fixed, greppable sequence. Each `apply()` is independently idempotent/self-gating, so order is not load-bearing, but making it explicit aids reasoning.
- **Idempotency contract documented.** The `ready()` docstring (`django_strawberry_framework/apps.py:13-37`) states the repeated-`ready()` safety property some Django test runners rely on and ties the consumer-facing `APPLY_UPSTREAM_PATCHES` toggle to the behavior. Accurate against the source — and, notably, the docstring already correctly names all three patch modules, so only the GLOSSARY prose lags.
- **Static overview is clean.** Shadow overview reports 0 control-flow hotspots, 0 ORM markers, 0 calls of interest, 0 TODOs, 0 repeated literals — nothing requiring deeper logic attention.

### Summary

`apps.py` is a clean, minimal AppConfig dispatcher: a lazy-import `ready()` that applies the package's three defensive patch modules under the `APPLY_UPSTREAM_PATCHES` toggle. The source is unchanged from HEAD (`git diff HEAD -- django_strawberry_framework/apps.py` empty) and has zero source-level findings. The one finding is a **Medium GLOSSARY drift**: `docs/GLOSSARY.md:308` still describes the `0.0.7` single-patch `ready()` and must be updated to reflect all three patch modules and the `APPLY_UPSTREAM_PATCHES` gate (verbatim replacement supplied). Because that requires a real edit to a tracked file, this cycle routes through the standard fix flow (shape #4), not the no-source-edit shape #5. The shared `apply()`-scaffold DRY consolidation across the three patch modules is forwarded to `rev-django_strawberry_framework.md`.

---

## Fix report (Worker 2)

Consolidated single-spawn (shape #4): one GLOSSARY-only edit, no source change. Logic + comment + changelog disposition recorded together.

### Files touched
- `docs/GLOSSARY.md:308` — replaced the stale single-patch `ready()` sentence in the `## Django AppConfig` entry with the artifact's verbatim replacement. The new wording names all three patch modules (`_cross_web_patches`, `_django_patches`, `_strawberry_patches`), states the test-only vs. production-request split, and ties them to the `APPLY_UPSTREAM_PATCHES` toggle (default on, idempotent, self-healing). Preceding `name`/`verbose_name` clause and following `INSTALLED_APPS` discovery sentence left unchanged.

### Premise verification
- Artifact premise holds: `git diff HEAD -- django_strawberry_framework/apps.py` is empty (source unchanged from HEAD). `apps.py::DjangoStrawberryFrameworkConfig.ready` imports and calls all three `apply()`s gated by `APPLY_UPSTREAM_PATCHES`; the docstring already names all three modules. Only the GLOSSARY prose lagged at `0.0.7`. New wording verified accurate against current source.
- Link convention: the only link in the touched sentence is the in-page anchor `[Django Trac #37064 hardening](#django-trac-37064-hardening)`, which per START.md stays inline (in-page anchors are not reference-style). No cross-file links introduced, so no bottom link-definition block change is needed.

### Tests added or updated
- None. Documentation-only edit (no behavior change); no test surface applies. Source already at 100% coverage and unchanged.

### Validation run
- `uv run ruff format .` — pass (289 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed).
- `git diff HEAD -- docs/GLOSSARY.md` confirms exactly the one-sentence replacement; `git diff HEAD -- django_strawberry_framework/apps.py` empty.
- `uv.lock` untouched (no diff).

### Notes for Worker 3
- No shadow file used (no source edit; static overview already clean per artifact).
- No false-premise rejection — artifact premise confirmed correct.
- Other files appear modified in `git status` (e.g. `inspect_django_type.py`, `dicta.md`, other `rev-*.md`); these are concurrent maintainer/other-worker work outside this cycle's scope (AGENTS.md #33) — not touched by me. My edits are confined to `docs/GLOSSARY.md` and this artifact.

---

## Comment/docstring pass

Consolidated into this single spawn (shape #4).

### Files touched
- None. The reviewed source `django_strawberry_framework/apps.py` has zero defects and was not edited; its `ready()` docstring already correctly names all three patch modules and the `APPLY_UPSTREAM_PATCHES` gate (artifact "What looks solid" confirms this). No stale or obvious comments to remove, no non-obvious constraints undocumented. The GLOSSARY edit IS the documentation fix for this cycle.

### Per-finding dispositions
- Medium 1 (GLOSSARY prose stale): fixed via the `docs/GLOSSARY.md:308` verbatim replacement above.
- DRY analysis (shared `apply()`-scaffold; `ready()` dispatch-table refactor): both forward-looking / rejected by Worker 1 — no local edit. Scaffold consolidation forwarded to `rev-django_strawberry_framework.md`; the explicit three-call sequence is kept deliberately.

### Validation run
- `uv run ruff format .` — pass.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3
No comment/docstring changes were needed; the source docstring was already accurate.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
The cycle's only edit is internal documentation maintenance — a GLOSSARY freshness fix bringing stale `0.0.7` prose in line with the current (already-shipped, unchanged) `ready()` source. It is doc-sync, not a behavior change, public-symbol change, or consumer-visible contract change. Per AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed"), and the active review plan does not authorize a `CHANGELOG.md` edit for this per-file cycle (per-file/folder cycles are never the authorising scope; any CHANGELOG drift forwards to the project pass `rev-django_strawberry_framework.md`).

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass.
- `uv run ruff check --fix .` — pass.

---

## Verification (Worker 3)

Consolidated shape #4 GLOSSARY-only cycle; bare `fix-implemented` → terminal verification (logic + comment + changelog disposition together).

### Logic verification outcome
- **apps.py source unchanged vs HEAD** — `git diff HEAD -- django_strawberry_framework/apps.py` empty. The cycle's scope claim (source untouched, edits confined to `docs/GLOSSARY.md` + this artifact) holds.
- **Medium (GLOSSARY drift) — addressed.** `git diff HEAD -- docs/GLOSSARY.md` shows exactly the one-sentence replacement in the `## Django AppConfig` entry (`docs/GLOSSARY.md` #"The `ready()` body imports the package's three defensive patch modules"). Verified accurate against current `apps.py::DjangoStrawberryFrameworkConfig.ready`:
  - Names all three modules — `_cross_web_patches`, `_django_patches`, `_strawberry_patches` — matching the lazy imports at `apps.py` #"from django_strawberry_framework._cross_web_patches import apply" and the three calls `apply_django()`/`apply_strawberry()`/`apply_cross_web()`.
  - Test-only vs production split correct: `_django_patches` → Trac #37064 hardening (test-only); `_strawberry_patches` + `_cross_web_patches` → non-UTF-8 request-body `500` fix (production request handling). Matches the source docstring at `apps.py::DjangoStrawberryFrameworkConfig.ready` in substance.
  - `APPLY_UPSTREAM_PATCHES` (default on), self-gating/idempotent/self-healing, and the `{"APPLY_UPSTREAM_PATCHES": False}` opt-out — all match the docstring contract.
  - Preceding `name`/`verbose_name` clause and following `INSTALLED_APPS` discovery sentence left unchanged (confirmed in diff).
- **High / Low — both `None.`** in the artifact; confirmed genuine. Independent read of `ready()`: thin lazy-import dispatcher with no own logic to defect on; explicit three-call ordering retained.
- **Link convention respected.** The only link in the touched sentence is the in-page anchor `[Django Trac #37064 hardening](#django-trac-37064-hardening)`, which per AGENTS.md #28 stays inline (in-page anchors are not reference-style). No cross-file link introduced → no bottom `<!-- LINK DEFINITIONS -->` block change required. Correct.

### DRY findings disposition
Both DRY items are forward/reject, not local edits: the shared `apply()`-scaffold consolidation is correctly forwarded to the project pass (`rev-django_strawberry_framework.md`), consistent with the three sibling patch-module cycles' identical forward; the `ready()` dispatch-table refactor is correctly rejected (explicit named calls preserve visible ordering). No carry-forward owed by this cycle.

### Temp test verification
- None. Documentation-only edit, no behavior change, source at 100% coverage and unchanged — no test surface applies. No temp tests created.

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box at `docs/review/review-0_0_11.md` (the `apps.py` line).

Changelog disposition verified: `Not warranted` is correct — `git diff HEAD -- CHANGELOG.md` empty, and the disposition cites BOTH AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization for this per-file cycle. Internal-only framing is honest: a GLOSSARY freshness fix, no public-API surface changed.

Comment/docstring pass verified: no source comment/docstring change needed — `apps.py::DjangoStrawberryFrameworkConfig.ready` docstring already names all three modules and the toggle accurately; the GLOSSARY edit is the documentation fix.
