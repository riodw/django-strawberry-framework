# Review: `django_strawberry_framework/apps.py`

Status: verified

## DRY analysis

- None — the module is a 31-line Django `AppConfig` with a single `ready()` body whose only action is `from django_strawberry_framework._django_patches import apply` followed by `apply()` (`django_strawberry_framework/apps.py:28-30`); there is no second call site, no repeated literal, and the deferred import is load-bearing (must run after Django finishes app-load, so a module-level import would re-introduce the import-cycle the indirection exists to avoid). No helper to extract, no constant to name, no sibling to fold against.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The single first-party reference is the canonical `django_strawberry_framework._django_patches.apply()` entry point (`django_strawberry_framework/apps.py:28-30`); the module does not re-implement the patch-installation logic and does not duplicate the docstring's rationale — it forwards to `_django_patches` via the `:mod:` cross-ref (`django_strawberry_framework/apps.py:19-20`).
- **New helpers considered.** A `_apply_patches()` module-level wrapper around the two lines inside `ready()` was considered and rejected — `ready()` is itself the framework-supplied indirection layer that already exists for this exact purpose, and a wrapper would only push the deferred import one frame deeper without removing it. Promoting the import to module scope was considered and rejected for the same reason: AGENTS.md and `_django_patches` (per `rev-_django_patches.md`) hinge on the install happening at app-ready time, after Django has finished configuring; a module-level import would run at app-loader scan time and would also re-introduce the circular-import risk the deferred import is designed to avoid.
- **Duplication risk in the current file.** None. The class has exactly two class attributes (`name`, `verbose_name`), one method (`ready`), and a load-bearing docstring; nothing repeats inside the file.

### Other positives

- The `ready()` docstring (`django_strawberry_framework/apps.py:13-27`) explains *why* the patch-application sits in `ready()` (one-time setup that depends on Django being fully configured) and *how* consumers opt in (just listing `"django_strawberry_framework"` in `INSTALLED_APPS`), with a `:mod:` link to `_django_patches` for the per-patch rationale; this keeps the AppConfig surface free of patch-specific narrative that already lives in the patches module.
- The class-level docstring (`django_strawberry_framework/apps.py:7`) is one sentence and intentionally matches the module docstring (`django_strawberry_framework/apps.py:1`); Django's `AppConfig` discovery surfaces `verbose_name` separately and the docstring's job here is just to mark the class's role.
- Test discipline at `tests/test_apps.py` pins every load-bearing property of the module: the symbol is importable from `django_strawberry_framework.apps` (`tests/test_apps.py:8-11`), it is an `AppConfig` subclass (`tests/test_apps.py:14-15`), its `name` and `verbose_name` are pinned to their exact strings (`tests/test_apps.py:18-20`), Django's app registry resolves it under the canonical label (`tests/test_apps.py:23-25`), the spec-017 forbidden attributes `label`/`default_auto_field`/`default` are explicitly absent (`tests/test_apps.py:28-44`), and the `ready` slot is pinned both as present in `__dict__` and callable (`tests/test_apps.py:47-53`) so a future refactor that drops the body silently breaks the patch install.
- The "forbidden attributes" test annotates each forbidden attribute with the originating spec-017 decision and citation (`tests/test_apps.py:36-40`), and the test docstring at `tests/test_apps.py:28-35` records the deliberate supersession of the spec-017 "no `ready()` body in 0.0.7" stance by the Trac #37064 adoption — comment-as-decision-log shape that keeps the why-it-changed audit trail at the test site.
- GLOSSARY entry "Django `AppConfig`" (`docs/GLOSSARY.md:257-263`) is aligned with the shipped behavior: status `shipped (0.0.7)`, name and verbose_name strings pinned verbatim, `ready()` body's purpose stated, INSTALLED_APPS opt-in path documented, two-way cross-references to "Django Trac #37064 hardening" and "Schema export management command" present.

### Summary

`apps.py` is a minimal, intentionally thin Django `AppConfig` shell that pushes all real behavior into `_django_patches.apply()`. The deferred import inside `ready()` is load-bearing and correctly placed. The test coverage pins every public-contract property (subclass, name, verbose_name, registry resolution, forbidden-attribute absence, `ready` callability). GLOSSARY prose is aligned. No DRY opportunities, no High/Medium/Low findings — the file is in its minimum-correct shape and any cleanup would be cosmetic at best, regressive at worst.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — `183 files left unchanged` (pass).
- `uv run ruff check --fix .` — `All checks passed!` (pass).

### Notes for Worker 3

- No High / Medium / Low findings to dispose of.
- DRY analysis: single bullet, declarative "None — …" with a stated reason (single call site, deferred-import is load-bearing). No deferred-with-trigger items.
- GLOSSARY drift quick-check: `DjangoStrawberryFrameworkConfig` and the "Django `AppConfig`" section at `docs/GLOSSARY.md:257-263` are aligned with the shipped module — name, verbose_name, `ready()` purpose, INSTALLED_APPS opt-in, status `shipped (0.0.7)` all match. No GLOSSARY-only fix in scope.
- Shadow overview at `docs/shadow/django_strawberry_framework__apps.overview.md` was consulted; quick-scan shows 0 control-flow hotspots, 0 Django/ORM markers, 0 calls of interest, 0 repeated literals — consistent with the manual read.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits required. The module-level docstring (`django_strawberry_framework/apps.py:1`), class docstring (`django_strawberry_framework/apps.py:7`), and `ready()` docstring (`django_strawberry_framework/apps.py:13-27`) are each at the correct altitude: the module docstring states the AppConfig's purpose, the class docstring restates the role for `AppConfig` discovery, and the `ready()` docstring explains the deferred-import rationale and the INSTALLED_APPS opt-in path while delegating per-patch detail to `_django_patches` via the `:mod:` cross-reference. No stale comments, no TODO anchors, no obsolete spec references.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. Per `AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed" and `docs/review/review-0_0_7.md` (the active plan lists `rev-apps.md` in the artifact list with no maintainer authorization for a CHANGELOG entry attached). No edits were made to any tracked file in this cycle, so there is nothing to record.

---

## Verification (Worker 3)

### Logic verification outcome

Shape #5 no-source-edit cycle. No High / Medium / Low findings to dispose of — the artifact's High / Medium / Low blocks are all `None`, and the DRY analysis is a single declarative `None — …` with a stated reason (single call site at `django_strawberry_framework/apps.py:28-30`, deferred-import is load-bearing to avoid app-load-time circular imports and to defer until Django is fully configured). Spot-verified the artifact's `What looks solid` claims against source:

- `django_strawberry_framework/apps.py` lines 28-30 hold the deferred `from … import apply` + `apply()` call exactly as cited.
- `ready()` docstring (`django_strawberry_framework/apps.py:13-27`) carries the `:mod:` cross-ref to `_django_patches` and the INSTALLED_APPS opt-in narrative as described.
- `tests/test_apps.py` pins every claimed property: subclass (lines 14-15), `name`/`verbose_name` (lines 18-20), registry resolution (lines 23-25), forbidden-attribute absence with spec-017 citations (lines 28-44), and `ready` present-and-callable (lines 47-53).
- `docs/GLOSSARY.md:257-263` shows status `shipped (0.0.7)`, both strings pinned verbatim, and the two-way cross-refs to "Django Trac #37064 hardening" and "Schema export management command" as claimed.

### DRY findings disposition

No DRY items to carry forward — the artifact's DRY analysis is `None` with a justified rationale (single call site, deferred-import is load-bearing). No GLOSSARY-only fix was in scope.

### Temp test verification

- No temp test files created; no behavior in question needed isolation.
- Disposition: n/a — shape #5 no-source-edit cycle has nothing to prove beyond the static reads above.

### Verification outcome

`cycle accepted; verified` — top-level `Status: verified` set; the `apps.py` checkbox in `docs/review/review-0_0_7.md` is marked.

---

## Iteration log

(none)
