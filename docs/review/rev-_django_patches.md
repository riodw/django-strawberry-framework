# Review: `django_strawberry_framework/_django_patches.py`

Status: verified

## Understanding

The module owns one defensive monkey-patch: it replaces
`django.test.testcases.SimpleTestCase._remove_databases_failures` with a guarded copy
(`_patched_remove_databases_failures`, _django_patches.py:153-193) that adds an
`isinstance(method, _DatabaseFailure)` check before the `setattr(..., method.wrapped)` unwrap, so a
connection method replaced by a third party between `setUpClass` and `tearDownClass` no longer
crashes the cleanup loop (Django Trac #37064, closed `wontfix`). Django defines the classmethod on
`SimpleTestCase`, so one install covers the whole test-case hierarchy; confirmed at installed
Django 6.0.5 (`.venv/.../django/test/testcases.py:273-280`, sole caller the `addClassCleanup` at
`:226`; `TransactionTestCase`/`TestCase` add no override). The upstream body at 6.0.5 is identical
to the 5.2.13 copy the patch mirrors.

Lifecycle and joint ownership, fully traced:

- Applied first of the three patch modules from `apps.py::DjangoStrawberryFrameworkConfig.ready`
  (apps.py:38-44); gated by `conf.py::upstream_patches_enabled` (default on, malformed settings
  dict fails loud). Idempotent and self-healing via `_patch_is_installed` (live
  `SimpleTestCase.__dict__` read, _django_patches.py:196-208), re-entrancy and third-party-revert
  reinstall pinned by tests.
- Unlike both siblings (`_cross_web_patches.py`, `_strawberry_patches.py`), this patch
  **reimplements** the upstream body instead of wrapping and delegating — the guard sits inside
  the loop, so delegation is not possible. The import-time capture
  `_original_remove_databases_failures` (_django_patches.py:123-125) is therefore never delegated
  to; it serves only as the drift probe for `_validate_upstream_shape`
  (_django_patches.py:128-145: symbol import, classmethod-ness, `(cls)` arity). This is the key
  structural difference from the item-1 reference design, and it is where the Medium finding
  lives: a delegating patch only needs its call shape validated because upstream body changes flow
  through; a reimplementing patch *supersedes* the body, so shape-only validation under-protects.
- Wrap-time companion: `testing/_wrap.py::safe_wrap_connection_method` (consumer-facing half of the
  defense-in-depth) imports `_is_database_failure` from this module; the `None`-tolerant predicate
  (_django_patches.py:148-150) lets the public `testing` import degrade rather than crash if the
  private symbol ever moves. Verified by reading `_wrap.py` and `tests/testing/test_wrap.py`.
- Dependency exposure: `pyproject.toml` pins `Django>=5.2` with **no upper bound**, so consumers
  can run a Django the package never tested against; `_validate_upstream_shape`'s `RuntimeError`
  (naming the `APPLY_UPSTREAM_PATCHES` opt-out) is their only guard.
- Tests: `tests/test_django_patches.py` (11 tests: idempotency, revert-reinstall, installed on
  `SimpleTestCase`/inherited by `TransactionTestCase`/`TestCase`, absent-attr branch, unwrap happy
  path, guard path, direct-`SimpleTestCase`-subclass path, upstream-crash pin, missing-symbol and
  signature fail-loud, toggle off/on) plus `tests/testing/test_wrap.py` for the wrap-time half.
  All bodies read; all 19 pass focused (`--no-cov`).

Prior-cycle context: 0.0.11 reviewed this module and forwarded the three-module `apply()` scaffold
DRY to the project pass; item 1 of this cycle (rev-_cross_web_patches.md, verified) hardened the
sibling's validation to target the delegation object and kept the DRY forward. Both dispositions
are respected here.

## Verification

Scratch experiments under `docs/review/temp-tests/_django_patches/test_scratch.py` (4 passed,
`uv run pytest docs/review/temp-tests/_django_patches/ --no-cov -p no:randomly`):

- **exp1 — validation approves body-contract drift.** Simulated a future Django that renames
  `_disallowed_connection_methods` while keeping `_remove_databases_failures` a `(cls)` classmethod
  and keeping `_DatabaseFailure`: the renamed upstream unwraps all four disallowed methods
  correctly on its own, `_validate_upstream_shape()` passes, `apply()` installs the package patch
  on top of the working upstream, and the installed patch then crashes every teardown with
  `AttributeError: ... _disallowed_connection_methods` — the exact crash class the Trac #37064
  hardening exists to prevent, now *introduced* by the patch on an un-drifted-looking install.
- **exp2 — the captured original is genuinely upstream's and crashes today.** 
  `_original_remove_databases_failures.__func__` is Django's (`__module__ ==
  "django.test.testcases"`, not the patched function); installed live, it raises
  `AttributeError: ... 'wrapped'` on a plain-callable replacement at Django 6.0.5. So a permanent
  test can drive the *live* upstream body instead of a frozen copy.
- **exp3 — the existing retirement test is Django-insensitive by construction.** With a simulated
  "fixed Django" (guarded live method) in place, the hardcoded 5.2.13 copy used by
  `test_unpatched_remove_databases_failures_crashes_on_non_wrapper` still crashes and the test
  still "passes", reporting the bug as present. The copy tests itself, not the installed Django.
- **exp4 — `.wrapped` is a real but unvalidated dependency.** The unwrap line's
  `_DatabaseFailure.wrapped` contract holds at 6.0.5; a drifted `__init__` that stores nothing
  still passes `_validate_upstream_shape()` (it never touches `_DatabaseFailure` beyond `is None`).

Other verification: upstream `_remove_databases_failures` body read directly at
`.venv/.../django/test/testcases.py:272-280` and confirmed byte-identical to the patched body minus
the guard (and to the test's 5.2.13 copy); `_add_databases_failures` (`:249-266`) confirmed as the
symmetric wrap site whose `_DatabaseFailure(method, message)` instances the guard recognizes;
`ensure_connection_patch_method` teardown confirmed independent (mock.patch class context, not this
method). Focused permanent runs: `uv run pytest tests/test_django_patches.py
tests/testing/test_wrap.py --no-cov` — 19 passed. Scoped diff vs cycle baseline `ada14039` for
`_django_patches.py` / `tests/test_django_patches.py` / `testing/_wrap.py` is empty.

## Improvements

### High

None.

### Medium

- **Observation:** `_validate_upstream_shape` validates the wrong shape for a *reimplementing*
  patch: it checks only the captured descriptor's classmethod-ness and `(cls)` arity
  (_django_patches.py:128-145), while the installed replacement supersedes upstream's entire body
  and depends on body-level contracts the validator never examines —
  `cls._disallowed_connection_methods`, `_DatabaseFailure.wrapped`, and the loop semantics
  themselves.
  **Evidence:** exp1 — a body-drifted Django (renamed method list, working upstream remove) passes
  validation, `apply()` clobbers the working upstream, and every teardown then crashes with the
  very `AttributeError` class the patch exists to prevent. exp4 — a drifted `_DatabaseFailure`
  ctor also passes. Both siblings are safe from this by design (they delegate, so upstream body
  changes flow through; their validators now check the delegation target per item 1); this module
  cannot delegate, so its validator must pin what it supersedes. `pyproject.toml` sets
  `Django>=5.2` with no ceiling, so consumers upgrade Django ahead of the package and validation
  is their only guard — exactly the scenario the fail-loud redesign was built for
  (`apply()` docstring: "Dependency drift raises a targeted RuntimeError instead of silently
  dropping the protection" — currently true only for signature drift).
  **Impact:** the failure mode inverts the module's purpose: on a shape-passing but body-drifted
  Django, the patch either crashes every `SimpleTestCase` teardown in consumer suites
  (attribute/protocol rename) or silently supersedes new upstream teardown behavior (semantic
  drift), and an upstream fix of #37064 itself would be silently masked instead of triggering
  deliberate retirement.
  **Recommendation:** own the fix in `_django_patches.py::_validate_upstream_shape`: pin the
  superseded body by comparing the captured original's source
  (`inspect.getsource(function)`, dedented/normalized, against a module-level constant holding the
  known upstream body) and raise the existing targeted `RuntimeError` on any mismatch, keeping the
  current symbol/classmethod/arity checks as the first tier. Source-pinning is the reimplementer's
  equivalent of the siblings' delegation: any upstream body change — rename, restructure, or the
  bug being fixed — becomes a loud, deliberate re-audit instead of a latent behavior change. (A
  formatting-only Django change also trips it; that is the documented fail-loud trade the family
  already accepts, and the error names the `APPLY_UPSTREAM_PATCHES` opt-out.)
  **Proof:** permanent package test in `tests/test_django_patches.py` (state unreachable from a
  live query, so package tier per the placement ladder): monkeypatch
  `_original_remove_databases_failures` to a `(cls)`-shaped classmethod with a different body and
  assert `apply()` raises `RuntimeError` without installing; existing idempotency/reinstall/
  signature tests stay green; scratch exp1 re-run against the fixed module must fail to install.

- **Observation:** `test_unpatched_remove_databases_failures_crashes_on_non_wrapper`
  (tests/test_django_patches.py:248-292) claims to pin "that Trac #37064's bug shape IS still in
  Django at our pin" and that "a Django upgrade that quietly fixed the bug upstream would make
  this test fail" — but it installs a *hardcoded copy* of the 5.2.13 body, so it never exercises
  the installed Django at all. Both claims are false as implemented.
  **Evidence:** exp3 — with a simulated fixed-Django live method in place, the hardcoded copy
  still crashes and the test still passes, reporting the bug as present. exp2 — the drop-in
  replacement exists and is green today: the module's own import-time capture
  `_original_remove_databases_failures` is genuinely upstream's method and crashes identically at
  6.0.5.
  **Impact:** the test is the package's designated retirement signal for a production-shipped
  monkey-patch and it cannot fire; a Django release that fixes #37064 would leave the patch
  installed indefinitely with the docs claiming otherwise. (The Medium fix above adds apply-time
  detection; this test remains the regression-level pin and its docstring promise should become
  true rather than deleted.)
  **Recommendation:** own the fix in `tests/test_django_patches.py`: install
  `_django_patches._original_remove_databases_failures` (the captured upstream classmethod
  descriptor) instead of the hardcoded `_unpatched` copy, and drop the copy. The test then
  genuinely exercises the installed Django's body and fails — signalling retirement — on any
  Django that guards the unwrap.
  **Proof:** the rewritten test itself: passes at Django 6.0.5 (exp2), and exp3's fixed-Django
  simulation run against the rewritten assertion shows it failing (no `AttributeError` raised),
  i.e. the retirement signal now fires.

### Low

- **Observation:** `apply()`'s docstring says the toggle-off path "returns immediately, before
  logging or touching ``SimpleTestCase``" (_django_patches.py:214-216), but the module has not
  logged since the once-per-process `logger.info` design was replaced by the fail-loud
  `RuntimeError` (per the 0.0.11→0.0.13 redesign recorded in rev-_cross_web_patches.md).
  **Evidence:** no `logging` import or logger call anywhere in the module.
  **Impact:** stale phrase sends a reader hunting for a logger that no longer exists in a module
  whose docstrings are the re-audit contract; one clause, no behavior.
  **Recommendation:** drop "logging or" from the clause in `_django_patches.py` (the sibling
  `_strawberry_patches.py:256` carries the same vestige — that belongs to its own plan item, next
  in the cycle).
  **Proof:** docs-only; reading the corrected docstring against the module body.

- **Observation:** the `apply()` scaffold — toggle gate, `_validate_upstream_shape()`,
  `_patch_is_installed()`, install — plus the import-time `ImportError`-nulling capture is
  structurally triplicated across `_django_patches.py:211-242`, `_cross_web_patches.py:188-202`,
  and `_strawberry_patches.py:244-268`.
  **Evidence:** the three bodies read line-for-line parallel; the family has changed together once
  already (the fail-loud redesign), and item 1's Medium fix was itself a drift repair within this
  family.
  **Impact:** a fourth patch module or the next scaffold-policy change costs three edits and risks
  drift; this module's Medium finding is again family drift (validation depth differing by module
  kind).
  **Recommendation:** unchanged disposition from 0.0.11 and item 1: cross-module, owned by the
  project pass — forward to `docs/review/rev-django_strawberry_framework.md`. No local edit. If
  consolidated there, note that a shared scaffold must still let this module keep its
  reimplementation-specific body pin (the validation *depth* legitimately differs; only the
  scaffold is common).
  **Proof:** project-pass disposition; the three modules' existing suites are the regression net.

### DRY analysis

- The three-module `apply()` scaffold triplication (`_django_patches.py` / `_cross_web_patches.py`
  / `_strawberry_patches.py`) described in the second Low finding — cross-module, forwarded to the
  project pass (`docs/review/rev-django_strawberry_framework.md`), unchanged from the 0.0.11 and
  item-1 dispositions; not acted on locally.

## Summary

The patch is correctly targeted and its runtime behavior at the installed Django 6.0.5 is sound:
single upstream caller traced, the guard is a strict superset of the upstream body, the
install/reinstall/toggle lifecycle is well-pinned by 11 package tests, and the wrap-time companion
(`testing/_wrap.py`) shares the `None`-tolerant predicate cleanly. The genuine weaknesses are both
about drift, not today's behavior: `_validate_upstream_shape` pins only the call shape while the
patch supersedes a whole body (demonstrated: a shape-passing body-drifted Django gets its working
teardown clobbered and re-broken by the patch), and the designated retirement test exercises a
frozen copy of Django 5.2.13 rather than the installed Django, so it can never signal an upstream
fix. Two Medium fixes (body pin in the validator; retirement test driven through the captured
original) plus one Low docstring vestige are tracked changes. The `apply()` scaffold DRY stays
forwarded to the project pass. Needs Worker 2.

## Implementation (Worker 2)

All accepted findings verified independently before editing: re-ran Worker 1's scratch suite
(`docs/review/temp-tests/_django_patches/test_scratch.py`, 4 passed at Django 6.0.5) and probed
`textwrap.dedent(inspect.getsource(...))` on the import-time capture to fix the exact pin shape
(includes the `@classmethod` line and a trailing newline).

Changed files:

- `django_strawberry_framework/_django_patches.py` — Medium 1 root-cause fix: added module
  constant `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` (verbatim dedented upstream body, with a
  comment explaining why a reimplementing patch must pin the body it supersedes) and a third
  validation tier in `_validate_upstream_shape` comparing the captured original's dedented
  `inspect.getsource` against the constant, raising the family's targeted `RuntimeError` (names
  the `APPLY_UPSTREAM_PATCHES` opt-out) on mismatch. Unreadable source (`OSError`/`TypeError`
  from `getsource`, e.g. a bytecode-only distribution) is treated as drift — an unverifiable body
  must not be silently superseded. Tier order preserved (symbols, classmethod, arity, then body)
  so existing fail-loud tests keep their messages. Also Low 1: dropped the stale "logging or"
  clause from `apply()`'s docstring and updated its validation paragraph plus
  `_validate_upstream_shape`'s docstring to describe the three tiers and the
  reimplementer-vs-delegator rationale.
- `tests/test_django_patches.py` — Medium 2:
  `test_unpatched_remove_databases_failures_crashes_on_non_wrapper` now installs the module's own
  import-time capture `_original_remove_databases_failures` (with a premise assertion that
  `__func__.__module__ == "django.test.testcases"`) instead of the hardcoded 5.2.13 copy, which
  is deleted; its docstring's retirement-signal claim is now true (exp2/exp3). Medium 1 permanent
  tests added: `test_apply_fails_loudly_when_upstream_body_drifts` (a `(cls)`-shaped classmethod
  with a renamed-`_disallowed_connection_methods` body monkeypatched into the capture; `apply()`
  raises `RuntimeError` matching "upstream body" and `_patch_is_installed()` stays `False`) and
  `test_apply_fails_loudly_when_upstream_source_is_unavailable` (an `exec`-built sourceless
  function; `getsource` raises `OSError`; same targeted `RuntimeError`). Package tier per the
  placement ladder: drifted-Django module state is unreachable from a live query.

Permanent tests and the behavior they pin: the two new tests pin apply-time body-drift and
unverifiable-source rejection; the rewritten retirement test pins that Trac #37064's crash exists
in the *installed* Django and fires (fails) on any Django that fixes it. Existing 11 tests
(idempotency, reinstall, hierarchy coverage, guard/unwrap paths, symbol/signature fail-loud,
toggle) unchanged and green — the body pin passes against the real capture at 6.0.5, so the
happy-path lifecycle is untouched.

Verification: exp1 as written mutates only the class attribute, not the import-time capture, so
re-running it verbatim against the fixed module would still install (correctly — on a genuinely
drifted Django the capture itself is the drifted method). The faithful re-run is
`docs/review/temp-tests/_django_patches/test_scratch_worker2.py::test_exp1_rerun_fixed_module_refuses_to_install_over_drifted_django`:
exp1's renamed-list Django with the capture drifted too — `apply()` now raises, nothing installs,
and the working renamed upstream teardown runs un-clobbered. Focused runs:
`uv run pytest tests/test_django_patches.py tests/testing/test_wrap.py
docs/review/temp-tests/_django_patches/ --no-cov` — 26 passed (13 permanent patch tests, 8 wrap
tests, 5 scratch), re-confirmed after the ruff pass. No full suite run (final gate owns it).

Formatter/linter: `uv run ruff format .` — 351 files unchanged; `uv run ruff check --fix .` — 1
fixed (removed an unnecessary `noqa` I had added to the `exec` line), 0 remaining.

Rejected/deferred: nothing rejected. Low 2 (three-module `apply()` scaffold DRY) deliberately not
acted on locally per the 0.0.11/item-1 disposition — stays forwarded to
`docs/review/rev-django_strawberry_framework.md`; note for that pass: a shared scaffold must let
this module keep its reimplementation-specific body pin.

Working-tree classification at completion: slice-intended — `_django_patches.py`,
`tests/test_django_patches.py`, this artifact, and the untracked worker-2 scratch file. Untouched
concurrent work preserved — `_cross_web_patches.py` + `tests/test_cross_web_patches.py` (verified
item-1 diff), `mutations/resolvers.py`, `tests/mutations/test_resolvers.py`,
`mutations/review.md`, `docs/GLOSSARY.md`, `docs/README.md`, `examples/fakeshop/db.sqlite3`, both
`test_query` files, the untracked `<folder>/review.md` notes, and
`docs/review/rev-optimizer__walker.md`.

Changelog-worthiness (not edited, per policy): yes-worthy if authorized — the validator now
fail-louds on upstream body drift instead of clobbering a working teardown on future Djangos; a
consumer-visible hardening of a shipped patch's upgrade behavior.

## Independent verification (Worker 3)

Scope confirmed: `git --no-pager diff ada14039` for `_django_patches.py` /
`tests/test_django_patches.py` contains only the described changes (source-pin constant, third
validation tier, docstring updates; retirement-test rewrite plus two new fail-loud tests); all
concurrent work (item-1 files, `mutations/`, `test_query`, docs, `<folder>/review.md` notes,
`rev-optimizer__walker.md`) untouched.

Behavior re-traced independently: import-time capture (`_django_patches.py::_original_remove_databases_failures`)
precedes any `apply()`; `apply()` gates on the toggle, validates on every call (including the
re-entrant and reinstall paths), and installs only after all three tiers pass; the patched body
(`_django_patches.py::_patched_remove_databases_failures`) re-read against installed Django 6.0.5's
`_remove_databases_failures` (`.venv/.../django/test/testcases.py:272-280`) — strict superset,
guard only; sole upstream caller remains the `addClassCleanup` in `SimpleTestCase.setUpClass`;
`testing/_wrap.py`'s `_is_database_failure` import unaffected.

Source-pin false-positive check (the consumer-breaking risk) done explicitly: in a fresh
interpreter, `textwrap.dedent(inspect.getsource(...))` of the genuine upstream classmethod at
installed Django 6.0.5 is byte-identical to `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE`
(including the `@classmethod` line and trailing newline); the Django 5.2 branch body (GitHub,
`django/test/testcases.py:281-289`) is identical too, so the pin holds across the package's
`Django>=5.2` floor. Notably, Django `main` has ALREADY drifted (the method list moved to
`connection.features.disallowed_simple_test_case_connection_methods`), so the Medium finding was
imminent, not hypothetical: on the next Django release the baseline module would have installed
the stale reimplementation (exp1's clobber), while the fixed validator raises the targeted
`RuntimeError` — the deliberate re-audit the design intends. Residual (accepted, documented
fail-loud trade): consumers upgrading past 6.0 will hit that `RuntimeError` until the patch is
re-audited or `APPLY_UPSTREAM_PATCHES` is disabled; likewise bytecode-only distributions.

Experiments (`docs/review/temp-tests/_django_patches/test_scratch_worker3.py`, 4 passed; full
focused run `uv run pytest docs/review/temp-tests/_django_patches/ tests/test_django_patches.py
tests/testing/test_wrap.py --no-cov -p no:randomly` — 30 passed):

- **w3exp1 — new tests fail without the fix.** The baseline module (loaded from
  `git show ada14039`) approves both the body-drifted capture and the sourceless (`exec`-built)
  capture that the fixed validator rejects with the "upstream body" `RuntimeError`; both new
  permanent tests are genuinely fix-sensitive.
- **w3exp2 — the rewritten retirement test fires on a fixed Django.** With a guarded (#37064-fixed)
  body installed as the capture would be on such a Django, the retirement scenario raises no
  `AttributeError` and the test's `pytest.raises` fails — the signal now works; the premise assert
  (`__func__.__module__ == "django.test.testcases"`) pins that the capture is genuinely upstream's.
- **w3exp3 — pin stability and sensitivity.** Re-validation against the real capture is idempotent
  (3 consecutive passes); plausible reformattings (extra blank line, tab indentation, dropped
  decorator, stripped trailing newline) all differ from the pin even after dedent — each trips the
  fail-loud path, per the documented trade.
- **w3exp4 — end-to-end teardown.** Real `setUpClass` -> third-party cursor clobber ->
  `doClassCleanups`: no teardown exceptions, the foreign cursor is left untouched, every other
  disallowed method is unwrapped to its original.

Findings disposed: Medium 1 (body pin) implemented and proven fix-sensitive (w3exp1; Worker 2's
exp1 rerun re-confirmed in the 30-test run); Medium 2 (retirement test drives the live capture)
implemented and proven Django-sensitive (w3exp2); Low 1 (stale "logging or") removed in the diff;
Low 2 (three-module `apply()` scaffold DRY) correctly left forwarded to the project pass with the
body-pin caveat noted. Worker 1's exp1/exp4 scenarios re-ran green; exp1-as-written still installs
against the genuine capture, which is correct (the capture, not the class attribute, is what a
real drifted import presents — Worker 2's rerun covers the faithful scenario). Existing 11 tests
plus the toggle/idempotence/reinstall contracts re-verified in the same run. `uv run ruff format
--check` and `uv run ruff check` clean on both changed files. No revision needed.
