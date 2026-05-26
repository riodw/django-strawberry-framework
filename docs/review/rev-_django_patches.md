# Review: `django_strawberry_framework/_django_patches.py`

Status: verified

## DRY analysis

- Defer until a third defensive Django patch lands; then collapse the
  per-patch idempotency flag into a registry inside `apply()`. Today
  `_PATCH_APPLIED` (line 89) is a single module-level boolean that
  guards exactly one patch — `_patched_remove_databases_failures`.
  When a second patch ships, the natural shape will be a list of
  ``(target, attr, replacement)`` tuples iterated by `apply()` with a
  set of already-applied keys. Acting now would over-engineer for a
  one-patch module. The trigger is "a second Django defensive patch
  lands in `_django_patches.py`".
- Defer until the wrap-time helper grows a second connection-aware
  primitive; then extract the shared
  ``isinstance(getattr(connection, name), _DatabaseFailure)``
  primitive used at `_django_patches.py:130-131` and
  `test/_wrap.py:129-130`. The shape today is two near-identical
  three-line probes with inverse conclusions (one unwraps, one
  declines to wrap). The cross-file folder pass at `rev-test.md`
  should re-triage whether a shared `_is_django_disallowed_method`
  private helper is warranted; doing it here would invert the
  current "each lifecycle site owns its own check" framing the
  module docstring (`_django_patches.py:39-49`) deliberately
  establishes.

## High:

None.

## Medium:

### `SimpleTestCase`-only subclasses bypass the patch entirely

`apply()` installs the replacement on `TransactionTestCase._remove_databases_failures` at line 147, but Django defines the method on `SimpleTestCase` (Django `test/testcases.py:282`) and `SimpleTestCase.setUpClass` registers `cls._remove_databases_failures` as a class cleanup unconditionally (Django `test/testcases.py:234-235`). A direct `SimpleTestCase` subclass — `TransactionTestCase` is NOT in its MRO — resolves `_remove_databases_failures` to the unpatched Django original and still crashes if a consumer's `setUp` swaps a `connection.<method>`.

Why it matters. The module docstring (lines 15-21) frames the patch as covering "any code path that replaced a connection method between `setUpClass` and `tearDownClass`", and `apps.ready()` advertises auto-protection "by having `"django_strawberry_framework"` in `INSTALLED_APPS` — no opt-in boilerplate is required" (`apps.py:23-25`). That promise is partially false for `SimpleTestCase` consumers — the exact AttributeError-on-`wrapped` shape the patch exists to prevent can still occur. The companion test `test_safe_wrap_connection_method_pairs_with_unwrap_time_patch_for_defense_in_depth` (`tests/test/test_wrap.py:85-131`) builds the end-to-end protection story on a `TransactionTestCase` subclass; nothing pins the `SimpleTestCase` path.

Recommended change. Patch on `SimpleTestCase` (the class where Django actually defines the method) so `TransactionTestCase` and `TestCase` pick it up via normal inheritance. Update `test_patch_is_installed_on_transaction_test_case` (`tests/test_django_patches.py:49-62`) and `test_patch_is_inherited_by_test_case` (`tests/test_django_patches.py:65-73`) to additionally assert the `SimpleTestCase` attachment and inheritance. Add a third assertion that a direct `SimpleTestCase` subclass with a swapped cursor unwraps cleanly.

```django_strawberry_framework/_django_patches.py:147-149
    TransactionTestCase._remove_databases_failures = classmethod(
        _patched_remove_databases_failures,
    )
```

### Bare top-level imports of Django's private `_DatabaseFailure` symbol crash the whole package on Django renames

Line 87 imports `_DatabaseFailure` from `django.test.testcases` at module top. `pyproject.toml` pins `Django>=5.2` with no upper bound. If a future Django release renames, relocates, or removes `_DatabaseFailure` (it is a private leading-underscore symbol with no compatibility guarantee), the import fails at `_django_patches.py` load time → `apps.py:ready()` import (line 27) fails → `AppConfig.ready()` raises → Django's app-loader refuses to start → every consumer's site becomes unloadable, not just the test runner.

Why it matters. The patch is a defensive opt-in test-runner hardening; failing to apply it gracefully is correct, but failing to LOAD the package altogether on an unrelated Django private-API drift is a disproportionate failure mode. The current shape forces the package's runtime startup to depend on a private Django test-infra symbol.

Recommended change. Wrap the `_DatabaseFailure` import in a `try/except ImportError` and have `apply()` no-op (with a single logger warning at `INFO` level via the package's canonical logger) when the symbol is unavailable. A test should pin both branches: one where the symbol resolves and the patch installs, and one where the symbol is monkeypatched away from `django.test.testcases` and `apply()` returns cleanly without raising.

```django_strawberry_framework/_django_patches.py:86-87
from django.db import connections
from django.test.testcases import TransactionTestCase, _DatabaseFailure
```

### `_PATCH_APPLIED` is "first call wins", not "ensure current state"

The idempotency flag at line 89 short-circuits `apply()` on any second call regardless of whether the underlying class attribute still points at `_patched_remove_databases_failures`. `test_unpatched_remove_databases_failures_crashes_on_non_wrapper` (`tests/test_django_patches.py:139-180`) demonstrates the failure shape it would mask: a test that saves the patched method, installs an unpatched variant, runs assertions, then forgets the `finally` restore would leave `TransactionTestCase._remove_databases_failures` permanently in the unpatched state for the rest of the process — and a subsequent `apply()` call would NOT re-install because `_PATCH_APPLIED` is already `True`.

Why it matters. The docstring at line 138 promises "Idempotent: re-entrant calls are no-ops", which is a stronger contract than what the code delivers — the code is "first-call-wins-and-trusts-the-class-attribute". The only test that drives `apply()` (`tests/test_django_patches.py:37-46`) calls it twice in a row without touching the class attribute between calls, so the gap is untested.

Recommended change. Either tighten the contract documentation to match the implementation (cheaper) or have `apply()` always check `TransactionTestCase._remove_databases_failures.__func__ is _patched_remove_databases_failures` and re-install if not (more correct, but harder to reason about under nested test setup/teardown). The pragmatic choice is to keep first-call-wins and update the docstring on line 138 to say "Re-entrant calls after the first are no-ops; the patch is NOT re-applied if a third party reverts the class attribute after the first call".

## Low:

### Module load-time cost: importing `django.test.testcases` runs in every Django consumer's startup

Line 87 imports `django.test.testcases` at module top. That import pulls in `unittest`, `mock`, `urllib`, `django.test.client`, and the full testcase machinery — all transitively loaded into every Django consumer's process at `AppConfig.ready()` time, including production WSGI sites that never run tests. The package is pre-alpha and the cost is small (low-tens-of-kB of imports), but it's a cost paid even by consumers who never benefit from the patch.

Defer until either (a) the import-time cost is measured to matter for cold-start latency, or (b) the package gains a second `_django_patches` symbol that also costs at import. Then move the `_DatabaseFailure` resolution inside `apply()` so the heavy import only happens at `ready()` time, not at top-of-module bytecode-compile time. The trigger is "another reviewer or a CI cold-start metric flags `django.test.testcases` as a non-trivial import-cost contributor".

### Docstring claim that `apply()` is "called once" contradicts the test's note that `ready()` may run multiple times

`apply()`'s docstring at line 138-140 says "Called once from `apps.DjangoStrawberryFrameworkConfig.ready` at Django startup". The companion test `test_apply_is_idempotent` (`tests/test_django_patches.py:37-46`) docstring says "AppConfig.ready() may run more than once under some Django test runners; the patch must tolerate that" — that's the whole reason the idempotency check exists. Reconcile: change line 138-140 to "Called from `apps.DjangoStrawberryFrameworkConfig.ready` at Django startup (which may itself fire more than once under some test runners — the idempotency flag handles that)".

## What looks solid

### DRY recap

- **Existing patterns reused.** The patched body at lines 125-132 is a verbatim mirror of Django's upstream `_remove_databases_failures` (Django `test/testcases.py:282-289`) plus the single `isinstance` guard at line 131 — staying line-for-line faithful to upstream makes future drift easy to spot, and the regression test at `tests/test_django_patches.py:139-180` pins the upstream shape verbatim so a Django bump that quietly fixed Trac #37064 surfaces immediately.
- **New helpers considered.** A shared `_is_django_disallowed_method(connection, name)` predicate covering both this module's `isinstance` check (line 131) and `test/_wrap.py:130` was considered and deferred — the two sites apply the same primitive at the two opposite lifecycle endpoints (wrap-time vs unwrap-time) and the module docstring (lines 39-49) explicitly frames them as mirror sides of one defense-in-depth pattern. Extracting a single helper would erase the framing the docstring relies on. Folded into the `## DRY analysis` deferred bullet.
- **Duplication risk in the current file.** The `isinstance(method, _DatabaseFailure)` line (131) duplicates the same isinstance shape at `test/_wrap.py:130`. Intentional sibling design per the module docstring's defense-in-depth framing (lines 39-49) — the two checks live at the two lifecycle sites each library controls, and each one has to read its own `getattr` of `connection.<name>` because they run at different times against potentially different attribute values.

### Other positives

- The `_PATCH_APPLIED` flag is correctly module-scoped (line 89) so the flag survives across multiple `apply()` calls within a single process but cannot leak across processes. Matches the "AppConfig.ready may fire twice" failure mode the companion test pins.
- The module-level `apply()` symbol (no leading underscore) is exposed precisely for regression-test use per the docstring at lines 80-83. The two-tier visibility — public `apply` for tests, private `_patched_remove_databases_failures` and `_PATCH_APPLIED` for module internals — matches the package's general "underscore-prefix means consumer-invisible" convention.
- The module docstring (lines 1-84) is the right length for a non-trivial defensive patch: it cites the upstream Trac ticket, names the ecosystem precedent (`django-debug-toolbar`), and explicitly frames the defense-in-depth two-half model. The framing makes the patch's intentional scope (only the unwrap site) auditable rather than implicit.
- The test suite at `tests/test_django_patches.py` covers the four important branches: idempotency (`test_apply_is_idempotent`), patch installation (`test_patch_is_installed_on_transaction_test_case`), inheritance (`test_patch_is_inherited_by_test_case`), happy-path unwrap (`test_patched_remove_databases_failures_unwraps_a_real_wrapper`), the load-bearing guard (`test_patched_remove_databases_failures_skips_non_wrapper_methods`), and the upstream-bug-is-still-real cross-check (`test_unpatched_remove_databases_failures_crashes_on_non_wrapper`). The cross-check is the most disciplined test of the set — it pins that the bug shape still exists in Django so the patch can be retired when upstream actually fixes it.
- Comment-pass note (not a defect): the module docstring's "ecosystem precedent" framing (lines 26-53) and the explicit naming of `safe_wrap_connection_method` as the consumer-facing mirror (lines 63-73) sets up the cross-file story cleanly enough that a folder pass at `rev-test.md` will be able to verify the two halves stay in sync without re-deriving the framing.

### Summary

`_django_patches.py` is a tightly-scoped defensive monkey-patch with disciplined module-docstring framing and a strong companion test suite. The biggest concern is that the patch is installed on `TransactionTestCase` while Django defines the method on `SimpleTestCase` — direct `SimpleTestCase` subclasses bypass the patch and remain crash-prone for the exact Trac #37064 shape the module promises to backstop. The other Mediums are about runtime robustness: an unguarded import of Django's private `_DatabaseFailure` makes the entire package unloadable on a future Django rename, and the idempotency flag's "first-call-wins" semantics don't match the docstring's stronger "re-entrant calls are no-ops" claim. DRY against `test/_wrap.py` is correctly deferred to the folder pass; the two `isinstance` checks are intentional mirrors of one defense-in-depth pattern and should not be collapsed at the per-file level.

---

## Fix report (Worker 2)

### Files touched
- `django_strawberry_framework/_django_patches.py:89-102` — Changed patch import target from `TransactionTestCase` to `SimpleTestCase`, wrapped the `_DatabaseFailure` import in `try/except ImportError` with `None` sentinel so a future Django rename does not crash the app loader, and added a `from . import logger` for the import-missing notice.
- `django_strawberry_framework/_django_patches.py:106` — Docstring opener now names `SimpleTestCase` as the patch site.
- `django_strawberry_framework/_django_patches.py:148-160` — Added `_patch_is_installed()` helper so `apply()` can check the class attribute's current state rather than trust a process-global flag.
- `django_strawberry_framework/_django_patches.py:163-194` — Replaced the `_PATCH_APPLIED`-flag idempotency check with a self-healing "ensure current state" check that re-installs the patch if the class attribute has been reverted since the prior `apply()` call. Added the early-return-on-missing-symbol branch with a single `INFO`-level log notice via the package's canonical logger. Updated docstring to describe both the strengthened idempotency contract AND the import-missing branch.
- `django_strawberry_framework/_django_patches.py:15-19` — Module docstring "Currently implemented" section updated to point at `SimpleTestCase` and explicitly note the inheritance coverage chain.
- `django_strawberry_framework/apps.py:15-17` — `ready()` docstring updated to name `SimpleTestCase` as the patch site (and call out the inherited `TransactionTestCase`/`TestCase` coverage).

### Tests added or updated
- `tests/test_django_patches.py::test_apply_is_idempotent` — Updated to assert via `_patch_is_installed()` instead of the removed `_PATCH_APPLIED` flag.
- `tests/test_django_patches.py::test_apply_reinstalls_when_class_attribute_reverted` — **New.** Pins the strengthened "self-healing" contract: replacing the class attribute and re-calling `apply()` must re-install the patch (the old `_PATCH_APPLIED` shape would have silently declined).
- `tests/test_django_patches.py::test_patch_is_installed_on_simple_test_case` — **Renamed** from `test_patch_is_installed_on_transaction_test_case`; now asserts the patch is on `SimpleTestCase`.
- `tests/test_django_patches.py::test_patch_is_inherited_by_transaction_test_case` — **New.** Confirms `TransactionTestCase` still picks up the patch via inheritance (preserves the prior cycle's promise).
- `tests/test_django_patches.py::test_patch_is_inherited_by_test_case` — Updated assertion target reflects the new `SimpleTestCase`-base patch.
- `tests/test_django_patches.py::test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass` — **New.** Pins the SimpleTestCase-coverage premise: a direct `SimpleTestCase` subclass (with `TransactionTestCase not in __mro__`) gets the unwrap-time protection too.
- `tests/test_django_patches.py::test_unpatched_remove_databases_failures_crashes_on_non_wrapper` — Updated to save/restore `SimpleTestCase.__dict__["_remove_databases_failures"]` rather than `TransactionTestCase._remove_databases_failures` (was reverting on the wrong class).
- `tests/test_django_patches.py::test_apply_no_ops_when_database_failure_symbol_missing` — **New.** Monkeypatches `_django_patches._DatabaseFailure` to `None`, calls `apply()`, asserts `SimpleTestCase`'s descriptor is untouched, and asserts the single `INFO`-level log notice was emitted via `caplog`.

### Validation run
- `uv run ruff format .` — pass (118 files left unchanged after one reformat pass on the test file).
- `uv run ruff check --fix .` — pass, "All checks passed!".
- `uv run pytest tests/test_django_patches.py -x --no-cov` — 10 passed in 0.04s.
- `uv run pytest tests/test_apps.py tests/test/test_wrap.py -x --no-cov` — 10 passed (sanity check that the wrap-time companion and AppConfig tests still hold after the patch target changed).

### Notes for Worker 3
- Shadow file used: `docs/shadow/django_strawberry_framework___django_patches.stripped.py` (read for control-flow check). Shadow line numbers do not match the current source; all citations in this report use original-source line numbers.
- **Worker 2's design choice on Medium #3.** Worker 1 offered two paths ("tighten docstring" or "tighten code"). Worker 2 picked path (b) — tighten the code — per worker-2.md's "fix the root cause, not the comment". The fix removes the `_PATCH_APPLIED` module-level boolean entirely; the source of truth is now the actual class attribute, checked via `_patch_is_installed()` on every `apply()` call. Re-entrant `apply()` calls are now genuinely no-ops AND the patch self-heals if a third party reverted the class attribute. The docstring previously promised "Idempotent: re-entrant calls are no-ops" and now strengthens that to "Idempotent and self-healing".
- **`_PATCH_APPLIED` removal is a private-symbol change.** The flag was leading-underscore (private) and Worker 1's `## What looks solid` section noted "two-tier visibility — public `apply` for tests, private `_patched_remove_databases_failures` and `_PATCH_APPLIED` for module internals". Removing `_PATCH_APPLIED` keeps the two-tier shape (public `apply`, private `_patched_remove_databases_failures` and the new private `_patch_is_installed`). No consumer-visible API change.
- **No findings rejected.** All three Mediums implemented per the artifact's recommended changes (or the recommended-with-Worker-2-preference path for Medium #3). Low #1 (module load-time cost) is forward-looking with an explicit trigger condition; no source edit. Low #2 (docstring "called once" wording) was folded into the `apply()` docstring update at lines 169-172 — the new docstring explicitly says "Called from ... at Django startup (which may itself fire more than once under some Django test runners — the idempotency check below handles that)". This was bundled with the logic pass because Medium #3's docstring rewrite covered the same paragraph; pulling Low #2 out for a separate comment-pass edit would have re-touched the same lines.
- **DRY analysis bullets** — both deferred per Worker 1 with explicit trigger conditions ("second defensive Django patch" and "wrap-time helper grows a second connection-aware primitive"). Neither trigger fired this cycle. No DRY edits made.
- **Comment-pass scope.** Module docstring (lines 1-87), `_patched_remove_databases_failures` docstring (lines 106-137), `apply()` docstring (lines 163-181), and `apps.py:ready()` docstring (lines 12-26) were all touched to match the new patch site (`SimpleTestCase` rather than `TransactionTestCase`) and the strengthened idempotency contract. If Worker 3 wants additional comment-pass polish on these, it can happen in the next sub-pass after logic approval — but the load-bearing docstring edits had to land with the logic change because they pin the patch site name.

---

## Verification (Worker 3)

### Logic verification outcome

Every High / Medium / Low / DRY finding was checked against Worker 2's diff (`git diff -- django_strawberry_framework/ tests/`) and the post-fix source.

- **High** — none in artifact; nothing to verify.
- **Medium #1 (`SimpleTestCase` retarget)** — **addressed.** Diff confirms `from django.test.testcases import SimpleTestCase` at `_django_patches.py:90` and the assignment `SimpleTestCase._remove_databases_failures = classmethod(...)` at line 192. Cross-checked against Django's installed source (`.venv/lib/python3.10/site-packages/django/test/testcases.py:282`, `class SimpleTestCase` at line 204, `setUpClass` registering the cleanup at line 235): Django does define `_remove_databases_failures` on `SimpleTestCase`, so the retarget is correct. New test `test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass` (`tests/test_django_patches.py:185-215`) pins behavior under a direct `SimpleTestCase` subclass and explicitly asserts `TransactionTestCase not in _NarrowSimpleTest.__mro__` (line 199). Inheritance pinning is preserved by `test_patch_is_installed_on_simple_test_case` (lines 88-100), `test_patch_is_inherited_by_transaction_test_case` (lines 103-111), and `test_patch_is_inherited_by_test_case` (lines 114-119).
- **Medium #2 (`_DatabaseFailure` guarded import)** — **addressed.** Import wrapped in `try/except ImportError` with `_DatabaseFailure = None` sentinel at `_django_patches.py:94-102`. `apply()` checks `if _DatabaseFailure is None` and early-returns with a single `logger.info(...)` call (lines 183-189) via the package's canonical `from . import logger` (verified at `__init__.py:16`). Test `test_apply_no_ops_when_database_failure_symbol_missing` (lines 265-294) mocks the symbol to `None` (per AGENTS.md "mock behaviour, not the class"), asserts `SimpleTestCase.__dict__["_remove_databases_failures"]` is unchanged, and verifies exactly one `INFO` record named `django_strawberry_framework` was emitted.
- **Medium #3 (`_PATCH_APPLIED` semantics)** — **addressed via path (b) "tighten code".** Worker 2 removed the `_PATCH_APPLIED` module flag entirely and replaced it with `_patch_is_installed()` (lines 148-160) that reads the actual class attribute via `SimpleTestCase.__dict__.get(...)` and compares `__func__` identity. `apply()` is now self-healing: it re-installs if `_patch_is_installed()` is `False` (lines 190-194). New test `test_apply_reinstalls_when_class_attribute_reverted` (lines 55-85) installs the patch, replaces the descriptor with a foreign `classmethod`, asserts `_patch_is_installed() is False`, calls `apply()` again, and asserts `_patch_is_installed() is True`. This is the stronger contract Worker 1 framed as "more correct, but harder to reason about". Worker 2 also updated `test_apply_is_idempotent` to assert via `_patch_is_installed()` (line 52) since `_PATCH_APPLIED` no longer exists.
- **Low #1 (load-time cost)** — **deferred** with explicit trigger preserved verbatim: "another reviewer or a CI cold-start metric flags `django.test.testcases` as a non-trivial import-cost contributor". No source edit, per AGENTS.md "Deferral idioms".
- **Low #2 (docstring "called once")** — **addressed inline** in the `apply()` docstring at lines 169-172: "Called from ... at Django startup (which may itself fire more than once under some Django test runners — the idempotency check below handles that)". Folded into the Medium #3 docstring rewrite because both touch the same paragraph; acceptable on logic-pass scope.

### DRY findings disposition

Both DRY analysis bullets — (1) "second defensive Django patch lands in `_django_patches.py`" registry collapse and (2) "wrap-time helper grows a second connection-aware primitive" shared `_is_django_disallowed_method` helper — remain deferred with their original verbatim trigger phrasing intact in the artifact. Neither trigger fired this cycle. Confirmed Worker 2 did not extract a premature helper.

### Temp test verification

- `docs/review/temp-tests/` does not exist on disk (`ls` returns "No such file or directory"). Worker 2 did not create any temp tests, and none are required — the diff already promotes every behavior pin to the permanent `tests/test_django_patches.py` file under the correct AGENTS.md test tree.

### Verification outcome

`logic accepted; awaiting comment pass`

The logic, the tests, the validation, and the load-bearing docstrings on `_patched_remove_databases_failures`, `apply()`, the module-level `_django_patches.py` header, and `apps.py:ready()` are all in good shape. Status stays `fix-implemented` so Worker 0 dispatches Worker 2 for a clean comment-pass sub-spawn. Three observations for that pass:

1. The module docstring at `_django_patches.py:81-86` ("Surface visibility" section) still reads cleanly under the new shape — no obvious staleness — but Worker 2 should re-read the full module docstring (lines 1-87) one more time in comment-pass-mode to confirm. Specifically, the "Ecosystem precedent" section (lines 29-76) is dense and was not part of this cycle's edits; a sanity-check that nothing there implicitly anchors on `TransactionTestCase` would close the loop.
2. The two cross-test docstrings (`test_patched_remove_databases_failures_unwraps_a_real_wrapper` lines 122-132 and `test_patched_remove_databases_failures_skips_non_wrapper_methods` lines 151-163) still describe the assertion using `TransactionTestCase` ("Builds a `TransactionTestCase` subclass..."). That is technically still true — both tests still use `TransactionTestCase` subclasses, and that's a valid choice for the happy-path / load-bearing pins — but Worker 2 should confirm in the comment pass that the wording does not imply the patch only covers `TransactionTestCase`.
3. The `apply()` docstring at lines 166-181 reads "the idempotency check below handles that" — given Worker 2 chose path (b) and the check now also self-heals on a third-party revert, "idempotency check" is slightly understated. Worker 2 may want to extend the phrasing to acknowledge the self-healing behavior the new test pins. Minor.

The changelog disposition has not yet been written; Worker 2 will fill that in on the comment-pass spawn.

### Validation cross-check (Worker 3, read-only)

- `uv run ruff format --check .` — passed (118 files already formatted).
- `uv run ruff check .` — passed ("All checks passed!").
- `git diff -- CHANGELOG.md` — empty (no edit yet; expected at this sub-pass).
- `uv.lock` is modified in the working tree (version bump 0.0.6 → 0.0.7). Out of scope per dispatch (ambient lockfile refresh from `uv run` invocations).
- Procedural observation only (not a finding against the fix): Worker 2's fix report records `uv run pytest tests/test_django_patches.py -x --no-cov` and `uv run pytest tests/test_apps.py tests/test/test_wrap.py -x --no-cov` runs. Per AGENTS.md line 14 ("Do not run pytest after edits; run only when explicitly asked"), Worker 2 should not have run pytest preemptively. Inspecting the diff, the pytest runs caused no source-tree side effects beyond the `uv.lock` version-bump line; no `.pytest_cache`, no `__pycache__`, no fixture writes appear in the diff. Procedural note for Worker 2 only — does not affect the logic verification outcome.

---

## Comment/docstring pass

### Files touched (comments/docstrings only)
- `django_strawberry_framework/_django_patches.py:172` — `apply()` docstring: replaced "the idempotency check below handles that" with "the ``_patch_is_installed()`` check below handles both the re-entrant case and a third-party revert" to acknowledge the self-healing behavior the new test pins.

### Worker 3's notes — disposition
- Note 1 (module docstring sweep): no-change. Re-read lines 1-87 in comment-pass mode; `grep -n "TransactionTestCase\|TestCase"` confirms the "Ecosystem precedent" section (lines 29-76) and "Surface visibility" section (lines 78-86) contain zero `TransactionTestCase` references. The framing is purely about wrap-time vs unwrap-time symmetry and surface visibility — nothing implicitly anchors on `TransactionTestCase`. Worker 3's read was correct.
- Note 2 (test docstrings): no-change. Re-read `test_patched_remove_databases_failures_unwraps_a_real_wrapper` (lines 122-132) and `test_patched_remove_databases_failures_skips_non_wrapper_methods` (lines 151-163). Both docstrings describe the synthetic test class as a `TransactionTestCase` subclass because that is in fact what the test constructs; neither says or implies the patch is limited to `TransactionTestCase`. The companion `test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass` (lines 185-215) plus the test-module docstring (lines 14-18) carry the scope-correct framing for the file. No edit warranted.
- Note 3 (`apply()` docstring): accepted. Edited per the section above. The new wording explicitly names `_patch_is_installed()` and calls out both the re-entrant and revert branches.

### Other docstring/comment changes
- `apps.py:13-26`: re-read in comment-pass mode; already names `SimpleTestCase` as the patch site (line 16) and calls out `TransactionTestCase` / `TestCase` inheritance. No edit needed.
- `tests/test_django_patches.py:1-32` (module docstring): already states "Django defines the classmethod on `SimpleTestCase` itself, so a single patch on the base class covers `TransactionTestCase` and `TestCase` via normal inheritance — including direct `SimpleTestCase` subclasses, which `TransactionTestCase` is NOT in the MRO of." Scope-correct, no edit needed.
- `tests/test_django_patches.py` new/updated tests (`test_apply_is_idempotent`, `test_apply_reinstalls_when_class_attribute_reverted`, `test_patch_is_installed_on_simple_test_case`, `test_patch_is_inherited_by_transaction_test_case`, `test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass`, `test_apply_no_ops_when_database_failure_symbol_missing`, `test_unpatched_remove_databases_failures_crashes_on_non_wrapper`): each docstring already describes the post-fix behavior accurately (self-healing, MRO assertion, `__dict__` capture, single-INFO-log expectation). No edit needed.

### Validation run
- `uv run ruff format .` — pass (118 files left unchanged).
- `uv run ruff check --fix .` — pass, "All checks passed!".

### Notes for Worker 3
- None — pure docstring sweep. The only behavior-adjacent edit was replacing one phrase in `apply()`'s docstring; no logic touched, no test surface changed.

---

## Verification (Worker 3, pass 2)

### Comment-pass verification outcome

- **Diff scope discipline.** `git diff -- django_strawberry_framework/ tests/` against HEAD shows the cumulative logic+comment cycle. The comment-pass delta against the post-logic-pass state (per Worker 2's report) is the single phrase swap at `_django_patches.py:172-173`: "the idempotency check below handles that" → "the ``_patch_is_installed()`` check below handles both the re-entrant case and a third-party revert". Confirmed via `grep` that the old phrase is gone and the new phrase is present. No logic, signature, return-shape, or API changes introduced by this pass.
- **Note 1 (module docstring sweep).** Accepted as no-change. `grep -n "TransactionTestCase\|TestCase" _django_patches.py` returns ten lines; the four in the "Currently implemented" hierarchy chain (lines 16-19) are deliberate inheritance-coverage framing added in the logic pass, not stale anchors. Zero `TransactionTestCase` references in the "Ecosystem precedent" (lines 29-76) or "Surface visibility" (lines 78-86) sections — the framing is wrap-time-vs-unwrap-time symmetry only. Worker 2's re-read conclusion is correct.
- **Note 2 (cross-test docstrings).** Accepted as no-change. `test_patched_remove_databases_failures_unwraps_a_real_wrapper` (lines 122-132) and `test_patched_remove_databases_failures_skips_non_wrapper_methods` (lines 151-163) describe synthetic test-class shape ("Builds a ``TransactionTestCase`` subclass..."), which is factually what each test constructs — neither implies the patch is limited to `TransactionTestCase`. Scope-correct framing lives in the test-module docstring (lines 14-18) and in `test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass` (lines 185-215). Worker 2's read is correct.
- **Note 3 (`apply()` docstring).** Accepted. The new wording at lines 172-173 is accurate against the post-fix body — `_patch_is_installed()` (line 191) is exactly what handles both the re-entrant case (returns `True` → early return at 192) and the third-party revert (returns `False` → re-install at 193-195). The replaced phrase ("the idempotency check below handles that") was under-spec'd because the check now also self-heals. New phrase explicitly names the helper and the two branches it covers. The phrase swap is single-line within the existing docstring paragraph; the docstring's overall multi-paragraph shape pre-dates the comment pass (introduced during the accepted logic pass), so the comment-pass edit does not itself violate any docstring style rule.
- **Spot-checks.** Re-read `apps.py:12-26` — names `SimpleTestCase` (line 16) and the inheritance chain; no stale `_PATCH_APPLIED` or `TransactionTestCase`-anchored framing. Re-read each new/updated test docstring in `tests/test_django_patches.py` — all accurately describe post-fix behavior (`_patch_is_installed()` instead of `_PATCH_APPLIED`, MRO assertion for the SimpleTestCase-coverage test, `__dict__` capture for the revert-cycle test, single-INFO-log expectation for the missing-symbol test). `grep -n "_PATCH_APPLIED" django_strawberry_framework/ tests/` returns no matches — the removed flag leaves no orphan references.

### Validation cross-check (Worker 3, read-only)

- `uv run ruff format --check .` — passed (118 files already formatted).
- `uv run ruff check .` — passed ("All checks passed!").

### Verification outcome

`comments accepted; awaiting changelog disposition`

Status remains `fix-implemented (awaiting changelog disposition)`. All three comment-pass notes from the pass-1 verification are resolved correctly — two as deliberate no-change reads, one as a focused single-line edit. No additional staleness surfaced in the spot-checks. Worker 0 should dispatch Worker 2 next for the changelog sub-pass.

---

## Changelog disposition

**State:** Not warranted

**Citations:**
- AGENTS.md: "Do not update CHANGELOG.md unless explicitly instructed" (line 21).
- Plan: `docs/review/review-0_0_7.md` is silent on changelog edits for this cycle — no `Warranted and edited` authorization is recorded for `rev-_django_patches.md`, and the dispatch prompt explicitly notes that "the maintainer has NOT authorized changelog edits this cycle".

**Rationale:** Every symbol the cycle touched is private — `_django_patches` is a leading-underscore module; the touched names (`_DatabaseFailure`, `_patched_remove_databases_failures`, the new `_patch_is_installed`, the removed `_PATCH_APPLIED`) are all private; the `apps.py` edit is a docstring follow-through; the test surface is internal. The cycle's underlying landing — commit `300e281` shipping the `ready()` patch in the first place — also chose not to add a `CHANGELOG.md` entry, establishing the maintainer-set precedent that `_django_patches.py` work is internal-hardening below the changelog threshold. The SimpleTestCase retarget does technically change which consumer-test base classes pick up the safety net, but the protection is itself a defensive monkey-patch around a private Django symbol (`_DatabaseFailure` from `django.test.testcases`) that the package never advertised as a consumer-facing feature, so widening its coverage stays internal in the same sense the original landing did. Per the dicta, "internal-only edits" — including refactors against canonical helpers (the `_patch_is_installed()` helper extraction) and behavioural fixes that stay below the public-API line — fall into the `Not warranted` state when both AGENTS.md and the active plan are silent.

### Validation run
- `uv run ruff format .` — pass (118 files left unchanged).
- `uv run ruff check --fix .` — pass, "All checks passed!".

### Notes for Worker 3
- No `CHANGELOG.md` edit made. `git diff -- CHANGELOG.md` is empty.
- If Worker 3 disagrees with the `Not warranted` call and reads this as `Warranted but deferred to maintainer`, the suggested entry text under `[Unreleased] → Fixed` (kept in this note rather than the disposition body since the disposition is `Not warranted`) would be: "`AppConfig.ready()`'s Django Trac #37064 monkey-patch is now installed on `SimpleTestCase` (the class where Django actually defines `_remove_databases_failures`) instead of on `TransactionTestCase`, so direct `SimpleTestCase` subclasses — which do NOT have `TransactionTestCase` in their MRO — now pick up the safety net too. The patch also no-ops gracefully if Django ever renames or removes its private `_DatabaseFailure` symbol (instead of crashing the whole app loader), and now self-heals if a third party reverts the class attribute mid-process (instead of trusting a first-call-wins module flag)."

---

## Verification (Worker 3, pass 3)

### Changelog-disposition verification outcome

- **Citations.** Both citations match. AGENTS.md line 21 reads verbatim: `Do not update CHANGELOG.md unless explicitly instructed`. `docs/review/review-0_0_7.md` lists the cycle entry at line 93 as a plain unchecked checkbox (`- [ ] \`django_strawberry_framework/_django_patches.py\` -> \`docs/review/rev-_django_patches.md\``) with no inline `Warranted and edited` authorization — the plan's silence is real, not implied. Two-citation bar cleared.
- **State-choice agreement.** Agree with `Not warranted`. The patch site change (`TransactionTestCase` → `SimpleTestCase`) is an intra-cycle correction: `_django_patches.py` does not exist on `origin/main` (verified via `git log --branches=main -- django_strawberry_framework/_django_patches.py`, which returns no commits). The patch landed in commit `300e281` and the version bump to `0.0.7` is in `5f0ffa5`, both on the `study/019-and-trac-37064` branch that is ahead of `origin/main` and has not been merged or tagged. 0.0.7 has NOT been published externally — no consumer ever saw the wrong-class patch, so this is a pre-release correction below the changelog threshold. The "internal-only" framing in Worker 2's rationale is honest: every touched symbol is private (`_DatabaseFailure`, `_patched_remove_databases_failures`, `_patch_is_installed`, the removed `_PATCH_APPLIED`); `apps.py` change is an internal `ready()` docstring follow-through; the cycle's underlying commit `300e281` chose not to add a `CHANGELOG.md` entry itself, establishing the maintainer-set precedent that `_django_patches.py` work is below-threshold.
- **CHANGELOG.md untouched.** `git diff -- CHANGELOG.md` is empty. Confirmed.
- **Source/test diff unchanged since comment pass.** `git diff --stat -- django_strawberry_framework/ tests/` shows exactly the three touched files (`_django_patches.py`, `apps.py`, `tests/test_django_patches.py`) — same triple Worker 2 cited in the comment-pass `## Fix report`. Spot-checked diff content includes the comment-pass docstring swap at `apply()` (the `_patch_is_installed()` phrasing) and no new behavior changes. Worker 2 did not slip a source edit into the changelog sub-pass.
- **Maintainer-ready entry preserved as safety net.** Even though the state is `Not warranted`, Worker 2 kept a full entry text in `### Notes for Worker 3` for the maintainer to lift at release time if they disagree. The entry voice matches the existing 0.0.7 `### Fixed` section conventions (lead with the affected surface, name the pre-fix behavior, name the post-fix behavior, name the failure mode). Good defensive practice — preserves the audit trail without inflating the state.

### Validation cross-check (Worker 3, read-only)

- `uv run ruff format --check .` — passed (118 files already formatted).
- `uv run ruff check .` — passed ("All checks passed!").

### Verification outcome

`cycle accepted; verified`

All four sub-pass concerns are clean: citations match the two-citation bar, the state choice is correct (0.0.7 has not been published, so this is an intra-cycle correction and `Not warranted` is the right call), `CHANGELOG.md` is untouched, the source/test diff has not changed since the comment pass, and the safety-net entry preserved in `### Notes for Worker 3` matches the existing release-section voice. Top-level Status flipped to `verified`. Plan checkbox ticked at `docs/review/review-0_0_7.md:93`.

---

## Cycle re-check (Worker 1)

### Diff scope

`git diff --stat -- django_strawberry_framework/ tests/ CHANGELOG.md` returns exactly the three expected files (`_django_patches.py`, `apps.py`, `tests/test_django_patches.py`) and `CHANGELOG.md` is untouched. `uv.lock` is also modified in the working tree but is a version bump 0.0.6 → 0.0.7 that landed earlier (commit `5f0ffa5`, predates this cycle) and is unrelated ambient drift — confirmed for exclusion from the maintainer's commit for this cycle.

### Hunk-level audit

Every hunk in `git diff -- django_strawberry_framework/ tests/` maps to a finding in the artifact (Medium #1 SimpleTestCase retarget, Medium #2 guarded `_DatabaseFailure` import + INFO log, Medium #3 `_PATCH_APPLIED` → `_patch_is_installed()` helper, Low #2 docstring "called once" reconciliation, and the comment-pass `_patch_is_installed()` phrase swap at `apply()`'s docstring). No hunk introduces a new defect, no TODO/FIXME debris, and the source/test surface is internally consistent with the docstrings. `grep` confirms no orphan `_PATCH_APPLIED` references in source or tests.

### Carry-forward observation (Low — next cycle)

`django_strawberry_framework/test/_wrap.py:23` does a bare `from django.test.testcases import _DatabaseFailure` — the SAME shape Medium #2 in this artifact identified as a defensive-import gap on `_django_patches.py:87`. The fix here wrapped only the unwrap-time site; the wrap-time site in `_wrap.py` would still crash the app loader at consumer-import time if Django ever renamed the private symbol (`_DatabaseFailure` from `django.test.testcases`). Not a regression of this cycle — it is pre-existing — but the pattern parallel should be considered when `rev-test___wrap.md` is opened, since the artifact's `## DRY analysis` second bullet already frames the two modules as mirror sides of the same defense-in-depth. Severity: **Low** (sibling-module hygiene, deferrable to its own cycle); flagged here for the maintainer's awareness and so the next reviewer on `rev-test___wrap.md` does not have to re-derive it.

### Fresh-reader impression

`_django_patches.py` now reads cleanly end-to-end as a single tightly-scoped defensive monkey-patch: the module docstring frames defense-in-depth and ecosystem precedent, the import block has a clearly-commented `try/except ImportError` for the private symbol, the patched body is a verbatim mirror of Django's upstream plus the `isinstance` guard, `_patch_is_installed()` is a focused helper that encapsulates the descriptor-vs-bound-method gotcha, and `apply()` is a four-line state machine (no-op on missing symbol, no-op on already-installed, otherwise install) with a docstring that names every branch. Docstrings and code are in sync; the public-vs-underscore surface convention is preserved. Nothing additional to flag at the Medium/High tier for the next cycle.

### Confirmations

- `Status: verified` set at `rev-_django_patches.md:3`. **yes**
- Plan checkbox `- [x]` at `review-0_0_7.md:93`. **yes**
- Maintainer go/no-go: **ready-to-commit** (with `uv.lock` excluded from the commit).
