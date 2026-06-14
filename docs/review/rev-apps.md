# Review: `django_strawberry_framework/apps.py`

Status: verified

## DRY analysis

- None — the module is a 31-line Django `AppConfig` whose only executable statement is the deferred local import `from django_strawberry_framework._django_patches import apply` followed by `apply()` (`django_strawberry_framework/apps.py:28-30`). There is no second call site, no repeated literal (`"django_strawberry_framework"` appears once as `name` at `apps.py:9`), and the deferred import is load-bearing: it must run after Django finishes app-load, so promoting it to module scope would re-introduce the import-cycle risk the indirection exists to avoid. No helper to extract, no constant to name, no sibling to fold against.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The single first-party reference is the canonical `django_strawberry_framework._django_patches.apply()` entry point (`apps.py:28-30`); the module does not re-implement patch-installation logic and forwards per-patch rationale to `_django_patches` via the `:mod:` cross-ref in the `ready()` docstring (`apps.py:19-20`). This is the same `ready()->apply()` wiring confirmed coherent across `_django_patches.py` and `testing/_wrap.py` in prior cycles (carried in worker-1 memory).
- **New helpers considered.** A `_apply_patches()` module-level wrapper around the `ready()` body was considered and rejected — `ready()` is itself the framework-supplied indirection for this exact purpose; a wrapper would push the deferred import one frame deeper without removing it. Promoting the import to module scope was likewise rejected: the install must happen at app-ready time after Django is configured, and a top-level import would run at loader-scan time and reintroduce circular-import risk.
- **Duplication risk in the current file.** None. The class has two class attributes (`name`, `verbose_name`), one method (`ready`), and docstrings; nothing repeats.

### Other positives

- The `apply` import is deliberately deferred inside `ready()` (`apps.py:28`) rather than at module top level — the correct Django idiom, avoiding import-time side effects and circular-import risk before the app registry is populated. Shadow overview confirms a clean read (0 control-flow hotspots, 0 ORM markers, 0 calls of interest, 0 repeated literals).
- `name` is the full dotted package path and `verbose_name` is the human-readable label (`apps.py:9-10`), so Django's implicit single-`AppConfig` discovery resolves this class with no `default_app_config` boilerplate.
- The `ready()` docstring (`apps.py:13-27`) explains *why* the patch-application sits in `ready()` (one-time setup that depends on Django being fully configured) and *how* consumers opt in (just listing `"django_strawberry_framework"` in `INSTALLED_APPS`), delegating per-patch detail to `_django_patches`. No stale comments, no TODO anchors, no obsolete spec references.
- Test discipline at `tests/test_apps.py` pins every load-bearing property: importable from the apps module (`tests/test_apps.py:8-11`), `AppConfig` subclass (`tests/test_apps.py:14-15`), `name`/`verbose_name` pinned verbatim (`tests/test_apps.py:18-20`), registry resolution under the canonical label (`tests/test_apps.py:23-25`), spec-017 forbidden attributes `label`/`default_auto_field`/`default` explicitly absent with per-attribute decision citations (`tests/test_apps.py:28-44`), and `ready` present-and-callable so a future refactor dropping the body fails loudly (`tests/test_apps.py:47-53`).
- GLOSSARY drift quick-check: `docs/GLOSSARY.md` "Django `AppConfig`" entry (line 281) and the Trac #37064 entries (lines 1113, 1293, 1295, 1299) describe `name`, `verbose_name`, the `ready()` -> `_django_patches.apply()` wiring, the `INSTALLED_APPS` opt-in, and status `shipped (0.0.7)` exactly as the source implements them. No drift; no replacement text needed. (Line numbers shifted from the prior cycle but content is aligned.)

### Summary

`apps.py` is a minimal, intentionally thin Django `AppConfig` shell that pushes all real behavior into `_django_patches.apply()`. The deferred import inside `ready()` is load-bearing and correctly placed. Test coverage pins every public-contract property (subclass, `name`, `verbose_name`, registry resolution, forbidden-attribute absence, `ready` callability), and GLOSSARY prose is aligned. Source and tests are unchanged in substance since the prior cycle. No DRY opportunities and no High/Medium/Low findings — the file is in its minimum-correct shape; any cleanup would be cosmetic at best, regressive at worst. This is a no-findings, no-source-edit cycle (collapsible shape #5 / skip-shape #2).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 265 files left unchanged.
- `uv run ruff check --fix .` — pass; all checks passed.

### Notes for Worker 3
- No High / Medium / Low findings to dispose of.
- DRY analysis: single declarative `None — …` bullet with stated reason (single call site at `apps.py:28-30`, deferred import is load-bearing). No defer-with-trigger items.
- GLOSSARY drift quick-check: "Django `AppConfig`" (`docs/GLOSSARY.md:281`) and Trac #37064 entries (lines 1113, 1293, 1295, 1299) align with the shipped module. No GLOSSARY-only fix in scope.
- Shadow overview `docs/shadow/django_strawberry_framework__apps.overview.md` matches current source (import line 28, `ready` lines 12-30); not re-run.
- Note: the prior committed artifact was the 0.0.7-cycle review; this file is the fresh 0.0.9-cycle artifact for the active plan (`docs/review/review-0_0_9.md`). Source/tests unchanged in substance since.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits required. The module docstring (`apps.py:1`), class docstring (`apps.py:7`), and `ready()` docstring (`apps.py:13-27`) are each at the correct altitude: module docstring states the AppConfig's purpose, class docstring marks the role for `AppConfig` discovery, and `ready()` explains the deferred-import rationale and INSTALLED_APPS opt-in while delegating per-patch detail to `_django_patches` via the `:mod:` cross-reference. No stale comments, no TODO anchors, no obsolete spec references.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. Per `AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed" and the active plan `docs/review/review-0_0_9.md` (lists `rev-apps.md` with no maintainer authorization for a CHANGELOG entry). No edits were made to any tracked file in this cycle, so there is nothing to record.

---

## Verification (Worker 3)

Shape #5 no-source-edit cycle. Verified independently against baseline `0872a20fcbecf870b3669742f108364202709e26`.

### Logic verification outcome

No High / Medium / Low findings to dispose of — the artifact is a no-findings cycle, and I confirm that conclusion is correct after independent inspection of `apps.py`:

- **Deferred local import is load-bearing (confirmed, not just asserted).** `_django_patches.apply` exists (`_django_patches.py:192`), and `_django_patches.py` imports `from django.test.testcases import SimpleTestCase` at module top level (`_django_patches.py:105`). Promoting `apps.py`'s `from ..._django_patches import apply` to module scope would force `django.test.testcases` to load during the app-registry scan, before Django is fully configured — exactly the import-time side effect / cycle risk the deferred import inside `ready()` (`apps.py:28-30`) avoids. The placement is the correct Django idiom, and Worker 1's "load-bearing" claim is substantiated.
- **AppConfig contract holds.** `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"` (`apps.py:9-10`); `ready(self) -> None` (`apps.py:12`) correctly overrides the framework one-time-setup hook with the right signature; no forbidden attributes (`label`/`default_auto_field`/`default`). Implicit single-AppConfig discovery resolves the explicit class with no `default_app_config` boilerplate.
- **Test discipline pins the contract.** `tests/test_apps.py` pins importability (8-11), subclass (14-15), `name`/`verbose_name` verbatim (18-20), registry resolution (23-25), forbidden-attribute absence with per-attr citations (28-44), and `ready` present-and-callable so a future refactor dropping the body fails loudly (47-53). No edge case a clean pass missed.

### DRY findings disposition

Single `None — …` bullet accepted. Independently confirmed: one call site (`apps.py:28-30`), the literal `"django_strawberry_framework"` appears once as `name`, and the `ready()->apply()` indirection is itself the framework-supplied seam — a `_apply_patches()` wrapper would only push the deferred import one frame deeper. Nothing to extract. No defer-with-trigger items to forward.

### Temp test verification

- None used — verification was satisfiable by static inspection (no behavioral suspicion to prove); did not run pytest (no test introduced; AGENTS.md bars preemptive runs).

### Shape #5 bookkeeping

- `git diff 0872a20fcbecf870b3669742f108364202709e26 -- django_strawberry_framework/apps.py` — empty.
- `git diff --stat <baseline> -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` — empty. The only dirty tracked files are `docs/review/rev-*.md` bookkeeping artifacts; no source/test/GLOSSARY/CHANGELOG edit by this cycle. "Files touched: None" holds.
- Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` — confirmed.
- Changelog: `git diff -- CHANGELOG.md` empty; disposition cites BOTH AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization. Internal-only framing matches the (empty) diff scope.
- GLOSSARY drift: citations at `docs/GLOSSARY.md:281` ("Django `AppConfig`") and Trac #37064 entries (1113, 1293, 1295, 1299) read and confirmed aligned with the shipped `name`/`verbose_name`, the `ready()->_django_patches.apply()` wiring, and the `INSTALLED_APPS` opt-in. No drift; no GLOSSARY-only fix present (would have been disqualifying).
- Ruff outcomes recorded: `ruff format .` clean (265 files unchanged), `ruff check --fix .` clean.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `apps.py` checklist box in `docs/review/review-0_0_9.md`.
