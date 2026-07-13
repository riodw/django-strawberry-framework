# Review: `django_strawberry_framework/apps.py`

Status: verified

## Understanding

The module owns the package's Django registration and its only lifecycle hook. 45 lines: a
`DjangoStrawberryFrameworkConfig(AppConfig)` pinning `name` / `verbose_name` (apps.py:6-10) and a
`ready()` (apps.py:12-44) that imports the three patch modules and dispatches their `apply()`s in
the order django -> strawberry -> cross_web. That dispatch is the package's entire "no opt-in
boilerplate" delivery mechanism: consumers add `"django_strawberry_framework"` to
`INSTALLED_APPS` and `apps.populate()` auto-discovers the single `AppConfig` subclass and fires
`ready()` after all apps are loaded and settings are configured.

Registration is load-bearing beyond the patches: being an installed app is also what exposes the
`export_schema` / `inspect_django_type` management commands
(`django_strawberry_framework/management/commands/`) and the GraphiQL bridge template via the
app-dirs loader (`django_strawberry_framework/templates/`; consumed by fakeshop per the comment at
examples/fakeshop/config/settings.py:41-47). `ready()` triggers no registrations or finalizers —
type finalization is the consumer's explicit `finalize_django_types()` call, and `conf.py` wires
its `setting_changed` receiver at import time precisely because consumers may import `conf` before
app loading (conf.py:242-247), so nothing else in the package wants a `ready()` home.

Contracts traced into the three `apply()`s (all items 1-3 of this cycle, artifacts `verified`):

- Each `apply()` self-gates on `conf.upstream_patches_enabled()` (default on, read at `ready()`
  time when settings are guaranteed configured; malformed settings dict fails loud), validates
  upstream shape, no-ops when installed, and re-installs after a third-party revert. Idempotence
  across repeated `ready()` firings (some test runners fire it more than once) is pinned per
  module and re-verified at the dispatch layer here (exp1).
- Dispatch order is inconsequential today: the three appliers share no state and no install-time
  ordering dependency (the strawberry/cross_web joint fix is joint at *request* time, not
  install time), and if any `apply()` raises, startup dies anyway. The only order-visible effect
  is which drift error a consumer sees first, and that the later patches are skipped (exp2).
- Items 1-3 hardened all three `apply()`s with fail-loud validators that RAISE `RuntimeError` at
  `ready()` time on upstream drift. How that lands for consumers: the exception propagates out of
  `apps.populate()` and `django.setup()` fails — manage.py, WSGI/ASGI workers, anything (exp4c).
  For the two production request-hardening patches this is the right layer and the deliberate
  design: a startup abort with a targeted message beats silently shipping upstream 500s.
  For the *test-only* django patch the same blast radius is a severity mismatch — see Medium 2.
  `rev-_django_patches.md` (Worker 3) already recorded that Django `main` has moved the pinned
  body, so that abort is imminent on the next Django release, and accepted the fail-loud trade
  per-patch; the cross-patch coupling through the single toggle was not dispositioned there.

Tests and docs describing the target: `tests/test_apps.py` (import, `AppConfig` subclass,
name/verbose_name pins, registry resolution, forbidden-attribute set, and that a `ready` key
exists and is callable — tests/test_apps.py:47-53 asserts presence only, never behavior); the three
patch-module suites each carry an "installed at collection via `ready()`" test
(tests/test_django_patches.py:94, tests/test_strawberry_patches.py:67,
tests/test_cross_web_patches.py:53). No permanent test anywhere calls `ready()` (grep over
`tests/` and `examples/`: only docstring mentions).

## Verification

Scratch experiments under `docs/review/temp-tests/apps/test_scratch.py` (6 passed,
`uv run pytest docs/review/temp-tests/apps/ --no-cov -n0`):

- **exp1 — dispatch and re-fire.** With all three patches reverted to the captured originals,
  `get_app_config(...).ready()` installs all three; a second `ready()` is a no-op and the
  delegation targets remain the genuine upstream originals (no wrapper-wrapping).
- **exp2 — drift failure ordering.** With the django body pin drifted (the state Django `main`
  is already in), `ready()` raises the targeted `RuntimeError` from `apply_django()` and neither
  production patch installs.
- **exp3 — the Medium-1 masking mechanic, executable.** With the patches reverted (equivalent to
  `ready()` dispatch lines deleted), calling each module's `apply()` directly — exactly what
  `test_apply_is_idempotent` does *earlier in file order* in each patch-module test file — makes
  all three "installed at collection" assertions pass. No randomization plugin is installed and
  `--dist loadscope` keeps a module's tests on one worker in file order, so those tests cannot
  deterministically detect a dropped dispatch line.
- **exp4a/b — production import weight.** Subprocess `django.setup()`: with
  `INSTALLED_APPS=[]`, `django.test.testcases` is not imported; adding
  `"django_strawberry_framework"` imports Django's test machinery into every process type,
  solely via `ready()` -> `_django_patches`.
- **exp4c — consumer landing of a drifted pin.** Subprocess consumer with the drifted django pin:
  `django.setup()` itself fails with the `RuntimeError` naming the `APPLY_UPSTREAM_PATCHES`
  opt-out.

Other verification: scoped diff vs the cycle baseline for this item is empty
(`git --no-pager diff 11fc7c16 -- django_strawberry_framework/apps.py tests/test_apps.py` — no
output; the target is untouched by items 1-3). Existing test bodies read in full
(`tests/test_apps.py` and the three patch-module suites). Live `test_query` malformed-body
regressions pin the strawberry/cross_web *effects* but only on workers that have not already run
the patch suites (and under `-n0` the `testpaths` order runs `tests/` first), so they are a
scheduling-dependent net, not a deterministic dispatch pin; the test-only django patch has no
live-tier pin at all.

## Improvements

### High

None.

### Medium

- **Observation:** `ready()`'s dispatch — the package's sole automatic delivery mechanism for all
  three shipped patches — is not deterministically pinned by any test.
  `tests/test_apps.py:47-53` asserts only that a callable `ready` key exists, and each
  patch-module "installed at collection via `ready()`" test is preceded in file order by
  `test_apply_is_idempotent`, which installs the patch directly
  (tests/test_cross_web_patches.py:30 vs :53, tests/test_strawberry_patches.py:44 vs :67,
  tests/test_django_patches.py:49 vs :94).
  **Evidence:** exp3 — with zero `ready()` dispatch, the direct `apply()` calls make every
  installed-at-collection assertion pass; no permanent test calls `ready()` (grep); no test
  reordering plugin is installed and `--dist loadscope` keeps each module's tests on one worker
  in file order, so the masking is systematic, not incidental. The live malformed-body
  regressions catch a dropped strawberry/cross_web dispatch only when xdist happens to schedule
  them on a worker that never ran the patch suites; a dropped `apply_django()` is caught by
  nothing.
  **Impact:** a refactor that drops or reorders a dispatch line out of `ready()` can pass the
  full gate while consumers silently stop receiving the patches — including the production
  request hardening — with the docstrings and test names still claiming delivery. The
  `tests/test_apps.py:28-35` comment records that a "no `ready()` body" stance existed as recently as
  0.0.7 and was reversed, so the deletion scenario is not hypothetical churn.
  **Recommendation:** own the fix in `tests/test_apps.py` (the dispatch is `apps.py`'s own
  contract, distinct from each patch's mechanics): a package-tier test that reverts all three
  patches to their captured originals, calls
  `django.apps.apps.get_app_config("django_strawberry_framework").ready()`, and asserts all
  three `_patch_is_installed()` — plus a second `ready()` call pinning dispatch-layer
  idempotence. Package tier per the placement ladder: the reverted state is unreachable from a
  live query. exp1 is the template (save/restore via `__dict__` descriptors, as the existing
  patch suites do).
  **Proof:** the new test itself — it fails when any of the three dispatch lines is removed
  (exp3 demonstrates the existing tests do not), and stays green today (exp1 passed).

- **Observation:** the fail-loud validators land at the right layer for the production patches,
  but `apply_django()` — guarding a *test-only* behavior (`SimpleTestCase` teardown) — shares
  the same blast radius: its drift `RuntimeError` aborts every process type, including
  production servers where the patched code can never execute, and the only escape,
  `APPLY_UPSTREAM_PATCHES = False`, is all-or-nothing, so silencing the test-only failure also
  removes the strawberry/cross_web production request hardening (non-UTF-8 and scalar-body
  requests revert to upstream 500s).
  **Evidence:** exp4c (consumer `django.setup()` fails outright on a drifted django pin); exp2
  (django is dispatched first, so the production patches are never reached); exp4a/b (the
  test-only patch also drags `django.test.testcases` into every production process);
  conf.py:49-53 and conf.py:182-196 (one boolean governs "every defensive patch");
  `rev-_django_patches.md` Worker 3: Django `main` has already moved the pinned body, so the
  trigger is the next Django release, not a hypothetical; `pyproject.toml` pins `Django>=5.2`
  with no ceiling, so consumers routinely upgrade Django ahead of the package.
  **Impact:** consumers upgrading Django will have production deployments refuse to boot over a
  test-teardown patch, and the escape hatch they will reach for silently degrades production
  request handling — the exact silent-drop failure mode the fail-loud redesign exists to
  prevent, reintroduced through toggle coarseness. The per-patch fail-loud trade was accepted in
  items 1-3; this cross-risk-class coupling was never dispositioned.
  **Recommendation:** the root cause is toggle granularity, owned by
  `conf.py::upstream_patches_enabled` and the three patch modules — not by `ready()`, which
  correctly dispatches and correctly does not catch (catching would defeat fail-loud at the
  wrong layer). Keep `True`/`False` semantics and additionally accept a per-dependency shape
  (e.g. a mapping or collection of dependency names) so a consumer can disable exactly the
  drifted dependency's patch while keeping the rest; document that strawberry+cross_web jointly
  own one fix (disabling one alone is safe but leaves the sync transport unfixed). The
  settings-key rule is satisfied: the key's new shape lands with the feature that needs it.
  Considered and rejected: catching/downgrading in `ready()` (silent drop, wrong layer); gating
  `apply_django()` on under-test detection (no reliable signal; the package's stance is zero
  consumer test boilerplate); a Django upper bound in `pyproject.toml` (complementary packaging
  policy, does not help in-range point-release drift and is overridable at install time).
  **Forwarded:** to `docs/review/rev-conf.md` (the toggle's owner is the next plan item), with
  the project pass (`docs/review/rev-django_strawberry_framework.md`) as the integration
  fallback — it already owns the three-module `apply()` scaffold DRY, and a shared scaffold
  should carry the per-dependency gate. No `apps.py` edit is part of this fix.
  **Proof:** package tests in the owner's cycle: with the per-dependency opt-out set for
  `django`, a drifted django pin no longer aborts `ready()` while strawberry/cross_web still
  install; existing all-or-nothing toggle tests stay green.

### Low

- **Observation:** `ready()`'s docstring summarizes the strawberry/cross_web modules as "the
  non-UTF-8 request-body ``500`` fix" (apps.py:20-23), but since item 3 `_strawberry_patches`
  also closes the scalar-body gap and ships the `parse_query_params` GET shield — the summary
  has already drifted once within this cycle.
  **Evidence:** apps.py:17-24 vs the `_strawberry_patches` module docstring (two gaps, nine
  call sites, GET shield, #3398 retirement coupling).
  **Impact:** `ready()`'s docstring is the first description a consumer or re-auditor reads of
  what the package does at startup; a stale per-module inventory misdirects exactly the drift
  re-audits the patch family is built around.
  **Recommendation:** own in `apps.py`: stop duplicating per-module bug inventories in the
  dispatcher's docstring — name one module per dependency (its already-stated organizing rule)
  and defer specifics to the module docstrings, which are the family's single source of truth.
  Root cause is the duplicated inventory, not this particular staleness.
  **Proof:** docs-only; reading the corrected docstring against the three module docstrings.

## Summary

`apps.py` itself is sound: registration is minimal and correctly pinned, `ready()` is the right
home for the patch dispatch, ordering is inconsequential, repeat firings are safe at the dispatch
layer (verified executably), and settings access happens strictly after configuration. The
genuine weaknesses sit at the seams: nothing deterministically tests that `ready()` actually
dispatches the three appliers (Medium 1, owned here — the masking mechanic is systematic under
the suite's fixed intra-module order), and the ready-time fail-loud design, correct for the
production patches, couples a test-only patch's imminent drift failure to production startup with
only an all-or-nothing escape (Medium 2, assessed here as toggle-granularity root cause and
forwarded to `rev-conf.md`/the project pass). One Low docstring de-duplication rounds it out.
Needs Worker 2 for Medium 1 and the Low.

## Implementation (Worker 2)

Both accepted findings re-verified before editing: Worker 1's six scratch experiments re-run
green (`uv run pytest docs/review/temp-tests/apps/ --no-cov -n0 -q` -> 6 passed), and a fresh
grep confirmed every `ready()` mention under `tests/` is docstring/comment-only - no permanent
test called it. Medium 2 (toggle granularity) implemented nowhere here per the forward to
`rev-conf.md`; no `apps.py` or `conf.py` change was made for it.

Changed files:

- `tests/test_apps.py` (Medium 1) - added
  `test_ready_dispatches_all_three_patch_appliers_and_refires_safely` plus the
  `_all_patches_installed()` helper: reverts all three patches to the import-time-captured
  upstream originals (save/restore via `__dict__` descriptors in `try`/`finally`, the existing
  patch-suite idiom), drives `ready()` through
  `django.apps.apps.get_app_config("django_strawberry_framework")`, asserts all three
  `_patch_is_installed()`, then re-fires `ready()` to pin dispatch-layer idempotence. Package
  tier per the placement ladder: the reverted state is unreachable from a live query. Also
  refreshed the module docstring, the spec-017 comment in the forbidden-attributes test, and the
  presence test's docstring, which all still described `ready()` as applying only the Django
  Trac #37064 patch (same inventory-drift root cause as the Low).
- `django_strawberry_framework/apps.py` (Low) - `ready()`'s docstring no longer restates
  per-module bug inventories (the drifted "non-UTF-8 ... fix" summary); it now names one module
  per dependency and defers specifics to the module docstrings as the single source of truth.
  Module docstring line 1 corrected from "applies its Django patches" to "applies its upstream
  patches" (same drift). No behavior change: the baseline diff for `apps.py` is docstring-only
  (`git --no-pager diff 11fc7c16 -- django_strawberry_framework/apps.py`).

Permanent tests and the behavior they pin:

- `tests/test_apps.py::test_ready_dispatches_all_three_patch_appliers_and_refires_safely` pins
  that `ready()` itself dispatches all three `apply()`s (deterministically, independent of the
  patch suites' earlier direct `apply()` calls) and that a repeated `ready()` stays installed.

Verification:

- `uv run pytest tests/test_apps.py --no-cov -n0 -q` -> 7 passed.
- Mutation probe (the finding's Proof): temporarily replaced the `apply_django()` dispatch line
  with `pass`, re-ran the new test -> FAILED at the `(True, True, True)` assertion with actual
  `(False, True, True)`; restored the line and confirmed the baseline diff is docstring-only
  again. exp3's masking claim is thereby closed: the dropped dispatch line is now caught.
- Combined single-worker run mirroring the loadscope grouping
  (`uv run pytest tests/test_apps.py tests/test_django_patches.py tests/test_strawberry_patches.py
  tests/test_cross_web_patches.py --no-cov -n0 -q`) -> 60 passed; the new test's save/restore
  leaks no state into the patch suites.

Formatter/linter: `uv run ruff format .` -> 352 files left unchanged; `uv run ruff check --fix .`
-> all checks passed.

Working-tree classification at completion: slice-intended = `django_strawberry_framework/apps.py`,
`tests/test_apps.py`, this artifact. Everything else `git status` shows is preserved concurrent
work, untouched: the verified item 1-3 diffs (three `_*_patches.py` modules + their test files +
`examples/fakeshop/test_query/test_products_api.py`), a concurrent DRY-cycle session
(`docs/dry/*`, `tests/test_export_dry_review.py`), the maintainer's untracked
`<folder>/review.md` notes (including the deleted `optimizer/review.md`), and the untracked
review artifacts.

Changelog-worthiness: not changelog-worthy - a test-gap closure plus docstring de-duplication;
no consumer-visible behavior changed. (Not recorded in `CHANGELOG.md` per standing rule.)

## Independent verification (Worker 3)

Scope re-established independently: `git --no-pager diff 11fc7c16 --stat` shows exactly
`django_strawberry_framework/apps.py` and `tests/test_apps.py` - no unrelated work absorbed; the
`apps.py` hunks are docstring-only (module line 1 plus the `ready()` inventory de-duplication),
no dispatch, import, or class-attribute line changed. Both files pass `ruff format --check` /
`ruff check` and the trailing-comma checker in check mode.

Behavior re-traced through the full target and all three patch modules: `ready()` dispatches
django -> strawberry -> cross_web; each `apply()` gates on
`conf.upstream_patches_enabled()` (conf.py:196), validates upstream shape fail-loud, no-ops when
installed, and re-installs after a revert. The new test's save/restore idiom is sound: all four
saved descriptors are read from `__dict__` and restored in `finally`, and the module-level
`_original_*` captures it installs are exactly the states `_patch_is_installed()` reports `False`
for.

Scratch experiments (`docs/review/temp-tests/apps/test_w3_scratch.py`, 5 passed, plus Worker 1's
6 re-run green - 11 passed combined):

- **w3exp1 - three-way mutation test of the finding's Proof.** Worker 2's probe mutated only
  `apply_django()`; I mutated each dispatch target separately (no-oping `<module>.apply`, which
  is call-time-equivalent to deleting the dispatch line because `ready()` resolves each `apply`
  via `from <module> import apply` at call time - the experiment self-validates that equivalence).
  The permanent test FAILS for each of the three dropped lines and passes unmutated. Medium 1's
  masking gap (exp3) is closed for all three patches, not just one.
- **w3exp2 - restore-on-failure.** After each mutated (failing) run, installed state is back to
  `(True, True, True)`: the `finally` restore holds on the failure path Worker 2's green runs
  never exercised, so a real regression would not cascade into the patch suites.
- **w3exp3 - dispatch-layer self-healing.** A third-party revert of one method between `ready()`
  firings is repaired by the next `ready()` with no wrapper-wrapping.

Break attempts beyond the mutations: combined runs of `tests/test_apps.py` with all three
patch-module suites in both orders (`test_apps` first and last), single-worker `-n0` -> 60 passed
twice; parallel `-n2 --dist loadscope` -> 60 passed; re-run under the pytest.ini
`config.test_settings` (shell env had `DJANGO_SETTINGS_MODULE=config.settings`) -> 12 passed. No
leakage or order sensitivity found.

Findings disposed: Medium 1 - implemented and mutation-proven (above); the placement (package
tier, `tests/test_apps.py`) is correct since the reverted-patch state is unreachable from a live
query. Medium 2 - correctly NOT implemented here; the forward is recorded in this artifact with
an explicit destination (`docs/review/rev-conf.md`, project pass as fallback), matching the
established cross-cycle forward mechanism (cf. the 0.0.11 scaffold forward picked up by the item
1-3 artifacts); evidence independently confirmed against conf.py:49-53 and conf.py:196 (one
boolean gates all three patches) and exp2/exp4c re-run green. The conf.py cycle's Worker 1 must
ingest it from here. Low - confirmed in the diff: the dispatcher docstring now names one module
per dependency and repeats no inventory; the refreshed `tests/test_apps.py` docstrings/comments
match final behavior.

Residual notes (no action this item): the Medium 2 forward must not be dropped when `rev-conf.md`
is created; `check_trailing_commas.py --check` on the two files produced no violations.

Verdict: implementation matches the artifact, the new test genuinely closes the masking gap, and
no regression or leakage was found. Status set to `verified`; plan checkbox marked.
