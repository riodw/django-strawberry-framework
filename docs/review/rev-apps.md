# Review: `django_strawberry_framework/apps.py`

Status: verified

## DRY analysis

- None — the file is a 30-line AppConfig wrapper with a single first-party import inside `ready()`; there is no repeated literal, no parallel call site, and no helper-extraction candidate, and the only string that could conceivably duplicate elsewhere (`"django_strawberry_framework"` as the dotted app label) is already the single source of truth that `INSTALLED_APPS` and the package logger key both point at (`__init__.py:16`, `examples/fakeshop/config/settings.py:48`). Forcing a "shared constant" here would create indirection without consolidating any duplication.

## High:

None.

## Medium:

None.

## Low:

### `ready()` docstring overstates the inheritance footprint of the patch

The docstring says the package "applies the Trac #37064 hardening for ``SimpleTestCase._remove_databases_failures`` (which ``TransactionTestCase`` and ``TestCase`` inherit)." That is correct for the two named subclasses but understates the actual coverage shape — the patch is installed on `SimpleTestCase` directly (see `_django_patches.py:193-195`), which means *every* `SimpleTestCase` subclass is covered, including direct `SimpleTestCase` subclasses that are NOT in `TransactionTestCase`'s MRO. That last branch is the exact reason `tests/test_django_patches.py::test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass` exists. The current wording reads as if only the two named subclasses inherit it. Recommend narrowing to "which every `SimpleTestCase` subclass (including ``TransactionTestCase`` and ``TestCase``) inherits" — single-sentence fix, no logic change. Comment-pass material; not a logic finding.

```django_strawberry_framework/apps.py:14:19
Currently applies the Trac #37064 hardening for
``SimpleTestCase._remove_databases_failures`` (which
``TransactionTestCase`` and ``TestCase`` inherit). See
:mod:`django_strawberry_framework._django_patches` for the
list of patches and the rationale for each.
```

## What looks solid

### DRY recap

- **Existing patterns reused.** The `ready()` body delegates entirely to `django_strawberry_framework._django_patches.apply()` (`apps.py:27-29`); the AppConfig adds zero patch logic of its own. The package logger key `"django_strawberry_framework"` lives in exactly one source location (`__init__.py:16`); `apps.py` does not duplicate it. The dotted app label `"django_strawberry_framework"` is set once on `name` (`apps.py:9`) and re-used implicitly by `INSTALLED_APPS` and by Django's app-registry lookups (`tests/test_apps.py:24` exercises that path).
- **New helpers considered.** A "patch-list-iterator" indirection (`for fn in PATCH_REGISTRY: fn()`) was considered and rejected — there is exactly one patch right now, `apply()` is already idempotent and self-healing, and adding a registry-of-one would push complexity into `_django_patches.py` for a future case that does not yet exist. If a second patch lands, the right consolidation is inside `_django_patches.py` (where the patch lives), not inside `apps.py`. AGENTS.md "add settings keys only when the feature that needs them lands" generalizes to this kind of premature plumbing.
- **Duplication risk in the current file.** None. The file is 30 lines, has exactly two imports, zero repeated literals, and zero control-flow hotspots per the shadow overview.

### Other positives

- **Import-time vs ready-time split is correct.** The `apply()` import is local to `ready()` (`apps.py:27`), so app-registry import does not trigger Django ORM imports through `_django_patches` (which imports `django.db.connections` and `django.test.testcases`). Lifting that import to module top would risk circular-import / "Apps aren't loaded yet" surprises during Django's app-population phase. Local-inside-`ready()` is the canonical Django pattern; honoring it here.
- **Idempotency owned by the right layer.** `ready()` does NOT try to guard itself against a second invocation. The contract is delegated to `apply()` (`_django_patches.py:163-195` — `_patch_is_installed()` short-circuit AND self-healing re-install), which is already pinned by `tests/test_django_patches.py::test_apply_is_idempotent` and `test_apply_reinstalls_when_class_attribute_reverted`. Pushing idempotency into `apps.py` would duplicate the contract; keeping it in `apply()` means a regression test against `apply()` is sufficient. This is the right responsibility split.
- **No forbidden AppConfig attributes.** `tests/test_apps.py::test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes` pins that `label`, `default_auto_field`, and `default` are absent (rev4-decisions 2/5/8). The current `apps.py` honors all three.
- **`ready()` is pinned to exist.** `tests/test_apps.py::test_djangostrawberryframeworkconfig_defines_ready_for_django_patches` pins that the class defines a `ready` callable in its own `__dict__`, so a future refactor that silently drops the `ready()` body (and thereby disables the Trac #37064 backstop) fails loudly.
- **App-registry resolution is pinned end-to-end.** `tests/test_apps.py::test_djangostrawberryframeworkconfig_resolves_through_django_app_registry` exercises `django.apps.apps.get_app_config("django_strawberry_framework")` against the real test-runner app registry, confirming that no `default_app_config` shim is needed (Django ≥ 3.2 autodiscovers single-AppConfig modules) and that the dotted label resolves to *this* class — protecting against the "consumer installs the package under a different alias" failure mode in the only realistic shape (the package's own example project, `examples/fakeshop/config/settings.py:48`).
- **Cooperation with `_django_patches.apply()` is explicit.** Docstring (`apps.py:13-26`) names both the ticket and the rationale, and explicitly states that consumers do not have to opt in beyond `INSTALLED_APPS`. The companion docstring in `_django_patches.py:1-87` also names `apps.py` as the install site; the two halves stay coherent.
- **Multi-install / aliasing surface is benign.** If a consumer's `INSTALLED_APPS` were to list `"django_strawberry_framework"` twice, Django's own app-registry validation raises `ImproperlyConfigured` at startup — before `ready()` runs — so the AppConfig never has to defend against double-registration itself. If a consumer subclassed `DjangoStrawberryFrameworkConfig` and installed it under a different dotted path, `ready()` would fire on that subclass's instance, `apply()` would run, and the idempotency contract on `apply()` covers a re-run (whether by the subclass or by Django firing `ready()` more than once under a test runner). No defense needed here.

### Summary

`apps.py` is a textbook minimal Django AppConfig: 30 lines, no logic of its own, single-purpose `ready()` body that delegates to `_django_patches.apply()`. The shadow overview shows zero control-flow hotspots, zero ORM markers, zero calls of interest, and zero repeated literals. The import-time-vs-`ready()` split is correct, idempotency is owned by `apply()` (already pinned by the prior cycle's tests), the no-forbidden-attributes contract from rev4-decisions 2/5/8 is pinned by `tests/test_apps.py`, and the existence of `ready()` is itself pinned so a silent regression cannot disable the Trac #37064 backstop. The one Low is a docstring-narrowing in `ready()` so the wording matches the actual install footprint described by `_django_patches.py:193-195` and exercised by `test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass`. Comment-pass material, not a logic finding.

---

## Fix report (Worker 2)

### Files touched
- None — no logic change required. Consolidated single-spawn pass: the artifact's only in-cycle edit is the single docstring sentence handled below in `## Comment/docstring pass`.

### Tests added or updated
- None — comment-pass-only cycle.

### Validation run
- `uv run ruff format .` — pass / no-changes (118 files left unchanged)
- `uv run ruff check --fix .` — pass / no-changes (All checks passed!)

### Notes for Worker 3
- This is the consolidated single-spawn pattern per `worker-2.md` ("the artifact's only in-cycle edit is a single trivially-localised docstring sentence with no logic change"). Fix report is a no-op; the real edit lives under `## Comment/docstring pass`. Changelog disposition is `Not warranted` for the same reason.
- No shadow file consulted for this pass — the source is 30 lines and the edit site was cited directly in the artifact (`apps.py:14-19`).

---

## Comment/docstring pass

### Files touched (comments/docstrings only)
- `django_strawberry_framework/apps.py:15-19` — narrowed the `ready()` docstring sentence so the wording matches the actual install footprint. Old: "applies the Trac #37064 hardening for ``SimpleTestCase._remove_databases_failures`` (which ``TransactionTestCase`` and ``TestCase`` inherit)". New: "applies the Trac #37064 hardening for ``SimpleTestCase._remove_databases_failures``, which every ``SimpleTestCase`` subclass (including ``TransactionTestCase`` and ``TestCase``) inherits". The wording now matches the install site (`_django_patches.py:193-195`) and the coverage shape pinned by `tests/test_django_patches.py::test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass`.

### Worker 1's notes — disposition
- Low 1 (`ready()` docstring overstates the inheritance footprint of the patch) — accepted, edited per Worker 1's recommended wording (lightly rephrased to read more naturally as one short sentence while preserving the substantive claim).

### Other docstring/comment changes
- None. Module docstring (`apps.py:1`) and class docstring (`apps.py:7`) carry no `TransactionTestCase`-anchored wording and were left untouched. The rest of the `ready()` docstring (the canonical-place-for-one-time-setup paragraph) is unaffected and accurate.

### Validation run
- `uv run ruff format .` — pass / no-changes (118 files left unchanged)
- `uv run ruff check --fix .` — pass / no-changes (All checks passed!)

### Notes for Worker 3
- Consolidated single-spawn pattern applied: Fix report is no-op, the docstring edit is here, changelog is `Not warranted`. Worker 3's next pass is the single terminal verification — both logic (trivially, since none changed) and comment correctness on the same pass.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
- AGENTS.md: "Do not update CHANGELOG.md unless explicitly instructed."
- The active plan `docs/review/review-0_0_7.md:94` is silent on changelog authorization for this cycle.

### What was done
No `CHANGELOG.md` edit. The cycle's only change is an internal docstring sweep: the underlying behaviour (the Trac #37064 patch installing on `SimpleTestCase` directly, with the inheritance footprint Worker 1 named) is consumer-visible, but it was already verified and accepted in the just-closed `rev-_django_patches.md` cycle's own `Not warranted` disposition. This artifact tightens the *description* of that behaviour without changing the behaviour itself, so the precedent applies even more cleanly here.

### Validation run
- `uv run ruff format .` — pass / no-changes
- `uv run ruff check --fix .` — pass / no-changes

---

## Verification (Worker 3)

### Logic verification outcome
No logic changes in this cycle — Worker 1 recorded zero High and zero Medium findings, and the sole Low (docstring inheritance-footprint narrowing) is comment-pass material, not a logic finding. Confirmed via `git diff -- django_strawberry_framework/apps.py`: the diff is three lines of docstring text only (the `Currently applies the Trac #37064 hardening for ...` sentence), no logic surface touched. The pre-existing `_django_patches.py`, `tests/test_django_patches.py`, and `uv.lock` modifications in `git status` are out of scope (carried over from the prior cycle).

### DRY findings disposition
Worker 1's DRY analysis was a deliberate "no consolidation needed" verdict — the file is 30 lines with zero repeated literals and the dotted-app-label string `"django_strawberry_framework"` is already single-sourced. The recap also documents the rejected `for fn in PATCH_REGISTRY: fn()` indirection as appropriately premature for one patch. No carry-forward DRY action required from this cycle.

### Temp test verification
- No temp tests created. The docstring edit is non-behavioural and the prior cycle's `test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass` already pins the coverage shape the new wording describes.
- Disposition: N/A.

### Consolidated single-spawn qualification
Worker 2 invoked the consolidated single-spawn pattern: no-op fix report, single docstring-sentence edit in the comment pass, `Not warranted` changelog disposition. Per `worker-3.md` the pattern requires every Low to be forward-looking OR every edit to be a DRY delegation; this cycle's qualification is the borderline "single docstring sentence, no logic change" framing Worker 2 documents in its notes. I accept the consolidation here — the edit is trivially localised (one sentence, cited site `apps.py:14-19`), the diff is verifiably comment-only, the rewording is checkable against `_django_patches.py:193-195` in a single read, and re-running three sub-passes would generate no additional signal. The judgement is sound.

### Changelog disposition verification
`git diff -- CHANGELOG.md` is empty. Disposition cites both AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan's silence at `review-0_0_7.md:94`. Both citations present, two-citation bar met. The "internal-only" framing is honest — this cycle's edit is docstring-only and the underlying behaviour (the `SimpleTestCase` retarget) was already adjudicated `Not warranted` in the just-closed `rev-_django_patches.md` cycle. Accepted.

### Comment/docstring verification
The new wording at `apps.py:15-19` accurately describes the install footprint: `_django_patches.py:193-195` assigns `SimpleTestCase._remove_databases_failures = classmethod(...)`, so every `SimpleTestCase` subclass inherits the patched method, with `TransactionTestCase` and `TestCase` named as the two well-known subclasses. The substantive change versus the prior wording — "every ``SimpleTestCase`` subclass (including ...)" rather than "(which ``TransactionTestCase`` and ``TestCase`` inherit)" — corrects the implicit narrowing Worker 1 flagged. Module and class docstrings unchanged as appropriate.

### Validation run
- `uv run ruff format --check .` — pass (118 files already formatted; the `COM812` formatter-conflict warning is a long-standing config note, not a regression).
- `uv run ruff check .` — pass (All checks passed!).

### Verification outcome
`cycle accepted; verified`
