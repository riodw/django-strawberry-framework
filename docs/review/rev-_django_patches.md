# Review: `django_strawberry_framework/_django_patches.py`

Status: verified

## DRY analysis

- None — the file is intentionally a near-verbatim mirror of Django's upstream `SimpleTestCase._remove_databases_failures` (with one added guard) plus a small `apply()` install/idempotency wrapper; the only repeated literal `"_remove_databases_failures"` is the upstream class-attribute name, which only appears twice (`_django_patches.py:186` and `_django_patches.py:227`) and is the load-bearing identity of the patch site, so a local constant would obscure rather than help.

## High:

None.

## Medium:

None.

## Low:

### `apply()` mutates `_missing_symbol_logged` via `global` instead of a small helper

`_django_patches.py:215-224` reaches for `global _missing_symbol_logged` to gate the once-per-process INFO log. The current shape works and the test suite pins it (`tests/test_django_patches.py::test_apply_logs_missing_symbol_notice_only_once`), but `global` mutation inside `apply()` is the only function-level state mutation in the module, which makes the otherwise pure-function file harder to scan. A `_log_missing_symbol_once()` helper that owns the sentinel and the `logger.info(...)` call would localise the mutation and keep `apply()` itself a flat install/guard sequence.

Defer until a second once-per-process notice lands (e.g. for a future second defensive patch in this module). At that point the helper signature collapses both call sites; today it would be a one-call refactor with no DRY win.

```django_strawberry_framework/_django_patches.py:215:224
    global _missing_symbol_logged
    if _DatabaseFailure is None:
        if not _missing_symbol_logged:
            logger.info(
                "django-strawberry-framework: skipping _remove_databases_failures patch — "
                "Django's private _DatabaseFailure symbol is unavailable at this Django "
                "version. The Trac #37064 backstop will not be installed.",
            )
            _missing_symbol_logged = True
        return
```

### `_patch_is_installed()` and `apply()`'s install call share knowledge of the `classmethod` descriptor shape

`_django_patches.py:186-189` encapsulates the `__dict__.get → __func__` unwrap; `_django_patches.py:227-229` builds the matching `classmethod(_patched_remove_databases_failures)` install side. The pair is symmetric by design and the docstrings on both functions explain the asymmetry (one inspects the descriptor, one builds it), so the duplication is intentional, but a future third site that needs the same install or inspect step would tilt this toward a shared `_INSTALLED_ATTR = "_remove_databases_failures"` named constant.

Defer until a third site touches `SimpleTestCase._remove_databases_failures`; today the two-site symmetry reads more clearly inline than through a constant.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_is_database_failure()` (`_django_patches.py:129-131`) is consumed by both the loop body inside `_patched_remove_databases_failures` (`_django_patches.py:173`) and is the documented mirror of debug-toolbar's wrap-time check; the module docstring (`_django_patches.py:36-91`) explicitly frames the wrap-time/unwrap-time symmetry and references `safe_wrap_connection_method` as the wrap-time twin so consumers see one helper at each lifecycle site.
- **New helpers considered.** Considered factoring the `if _is_database_failure(method): setattr(...)` line into a `_safe_unwrap(connection, name)` helper, but rejected — the file's "verbatim copy of Django's upstream method, with one added guard" property is load-bearing for the docstring's correctness argument (`_django_patches.py:135-156`) and the regression test `tests/test_django_patches.py::test_unpatched_remove_databases_failures_crashes_on_non_wrapper` reads the upstream body inline at `tests/test_django_patches.py:263-271`; both would have to be rewritten to chase a one-line helper.
- **Duplication risk in the current file.** The class-attribute name `"_remove_databases_failures"` appears at `_django_patches.py:186` and again at `_django_patches.py:227` (read vs install sides of the same descriptor). This is intentional sibling design — extracting a module-level constant would force every reader to follow an indirection to confirm the patch targets the exact attribute Django's class defines, which is the load-bearing identity of the file.

### Other positives

- The docstring (`_django_patches.py:1-102`) lays out the upstream Trac ticket, the wrap-time/unwrap-time defense-in-depth framing with debug-toolbar's precedent, and the explicit reason this module cannot adopt debug-toolbar's cache-panel sentinel strategy. It is the single longest non-source-code unit in the file and it earns its length — every later reviewer can answer "why does this patch exist and why this shape" without leaving the module.
- The `try: from django.test.testcases import _DatabaseFailure / except ImportError` block (`_django_patches.py:109-117`) plus the `_DatabaseFailure is None` early-return in `apply()` (`_django_patches.py:216-224`) make the patch self-disabling on a future Django version that renames or removes the private symbol. The `_missing_symbol_logged` sentinel (`_django_patches.py:126`) caps the noise at exactly one INFO record per process even when `AppConfig.ready()` fires repeatedly, and `tests/test_django_patches.py::test_apply_logs_missing_symbol_notice_only_once` pins the behavior with three back-to-back `apply()` calls.
- `apply()` is idempotent and self-healing — re-entrant calls when the patch is already installed are no-ops (`_django_patches.py:225-226`), and the `_patch_is_installed()` check re-installs the patch if a third party reverted the class attribute since the prior call. Pinned by `tests/test_django_patches.py::test_apply_is_idempotent` and `tests/test_django_patches.py::test_apply_reinstalls_when_class_attribute_reverted`.
- The patch site is `SimpleTestCase` (where Django defines the method) rather than `TransactionTestCase`, so a single install covers `TransactionTestCase` and `TestCase` plus direct `SimpleTestCase` subclasses (which `TransactionTestCase` is NOT in the MRO of). Pinned by `tests/test_django_patches.py::test_patch_is_inherited_by_transaction_test_case`, `tests/test_django_patches.py::test_patch_is_inherited_by_test_case`, and the dedicated `tests/test_django_patches.py::test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass`.
- The crash-without-the-patch behavior is pinned by `tests/test_django_patches.py::test_unpatched_remove_databases_failures_crashes_on_non_wrapper`, which inlines a verbatim copy of Django 5.2.13's upstream method body and asserts `AttributeError: ... wrapped`. A future Django release that silently fixes the bug will flip this test from passing to failing with a different error, which is the planned retirement trigger for the patch.
- The module is gated behind a leading-underscore name (`_django_patches.py`) and the only consumer-visible entry point (`apply()`) is invoked from `apps.py::DjangoStrawberryFrameworkConfig.ready` — consumers do not import from the module, which keeps the patch a side-effect of `INSTALLED_APPS` membership exactly as the module docstring promises.
- GLOSSARY drift quick-check: the documented public-contract symbols `safe_wrap_connection_method` (`docs/GLOSSARY.md:907-920`) and the `Django Trac #37064 hardening` entry (`docs/GLOSSARY.md:1075-1083`) are consistent with the module — both correctly identify `SimpleTestCase._remove_databases_failures` as the patch site, the `isinstance(method, _DatabaseFailure)` guard as the change, and the wrap-time/unwrap-time pairing with `safe_wrap_connection_method`. No drift; nothing to forward to Worker 2.

### Summary

`_django_patches.py` is a tight defensive-patch module with a long, load-bearing docstring, one verbatim-with-guard copy of Django's upstream classmethod, and a small idempotent installer. Tests at `tests/test_django_patches.py` cover every branch (idempotency, reinstall-after-revert, both arms of the unwrap loop, direct `SimpleTestCase` subclass coverage, missing-symbol no-op, once-per-process log gating, and the un-patched crash shape). No High or Medium findings. The two Lows are both forward-looking deferrals that only become actionable if a second once-per-process notice or a third reference to the patched attribute name lands, so this cycle qualifies as a no-source-edit pass.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — `183 files left unchanged` (no edits made this cycle).
- `uv run ruff check --fix .` — `All checks passed!` (no edits made this cycle).

### Notes for Worker 3
- Both Lows are forward-looking deferrals with explicit triggers (second once-per-process notice landing; third reference to `"_remove_databases_failures"`). Neither is actionable today.
- GLOSSARY drift quick-check returned clean — no GLOSSARY-only fix in scope.
- Shadow overview is current (timestamp newer than source); helper not re-run this cycle.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits required — the module docstring, the two function docstrings on `_patched_remove_databases_failures` and `apply()`, and the inline comments on the `try/except ImportError` block and the `_missing_symbol_logged` sentinel all match current behavior and current test coverage.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. **Not warranted** — no source, test, GLOSSARY, or behavior edits this cycle, so there is nothing for `CHANGELOG.md` to record. Citations: `AGENTS.md` #"Do not update CHANGELOG.md unless explicitly instructed" and `docs/review/review-0_0_7.md` (active plan is silent on changelog action for this cycle item).

---

## Verification (Worker 3)

### Logic verification outcome
Shape #5 (no-source-edit) cycle. All five terminal checks pass:
1. `git diff --stat HEAD -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` is empty (only `docs/feedback.md` is dirty plus the two untracked review artifacts, all out of scope).
2. Each of the three Worker 2 sections (`## Fix report (Worker 2)`, `## Comment/docstring pass`, `## Changelog disposition`) opens with `Filled by Worker 1 per no-source-edit cycle pattern.`
3. Both Lows carry verbatim trigger phrasing: L1 "Defer until a second once-per-process notice lands" and L2 "Defer until a third site touches `SimpleTestCase._remove_databases_failures`". No GLOSSARY-only fixes are present.
4. Changelog disposition is `Not warranted` with both required citations: `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") AND `docs/review/review-0_0_7.md` (active plan silence on changelog action for this item).
5. Ruff format-check (`183 files already formatted`) and `ruff check` (`All checks passed!`) both pass on spot-verification, matching the artifact's recorded outcomes.

Spot-checked the "What looks solid" claims against source: the `global _missing_symbol_logged` mutation at `_django_patches.py:215`, the `_patch_is_installed()` descriptor unwrap at `_django_patches.py:186-189`, and the `classmethod(_patched_remove_databases_failures)` install at `_django_patches.py:227-229` all match the artifact's references. All seven cited tests (`test_apply_is_idempotent`, `test_apply_reinstalls_when_class_attribute_reverted`, `test_patch_is_inherited_by_transaction_test_case`, `test_patch_is_inherited_by_test_case`, `test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass`, `test_unpatched_remove_databases_failures_crashes_on_non_wrapper`, `test_apply_logs_missing_symbol_notice_only_once`) exist in `tests/test_django_patches.py` at the expected names.

### DRY findings disposition
Worker 1's DRY analysis declares None — the file is a near-verbatim mirror of Django's upstream method plus a small idempotent installer. The duplicated `"_remove_databases_failures"` literal (`_django_patches.py:186` and `_django_patches.py:227`) is intentional sibling design at the read/install descriptor sites and is load-bearing for the patch's identity argument. Carried forward as-is; no DRY action.

### Temp test verification
- Temp test files used: none.
- Disposition: not applicable; no source or test edits this cycle.

### Verification outcome
`cycle accepted; verified` — top-level `Status: verified`; checklist box marked in `docs/review/review-0_0_7.md`.
