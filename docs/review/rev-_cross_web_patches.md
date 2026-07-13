# Review: `django_strawberry_framework/_cross_web_patches.py`

Status: verified

## Understanding

The module owns one defensive monkey-patch: it wraps the **sync**
`cross_web.DjangoHTTPRequestAdapter.body` property so that a request body that is not valid
UTF-8 falls back to the raw `request.body` bytes instead of letting the upstream bare
`self.request.body.decode()` raise `UnicodeDecodeError` (`.venv/.../cross_web/request/_django.py:33`,
confirmed unfixed in installed cross-web 0.7.0). The wrapper (`_patched_body`,
_cross_web_patches.py:162-175) delegates to the import-time-captured upstream getter
(`_original_body_fget`, captured at _cross_web_patches.py:126-129) so the success path is
byte-for-byte upstream and reinstalls never wrap a wrapper.

Callers and lifecycle, fully traced:

- Applied third from `apps.py::DjangoStrawberryFrameworkConfig.ready` (apps.py:38-44), so consumers
  get it via `INSTALLED_APPS`. Gated by `conf.py::upstream_patches_enabled` (conf.py:182-196,
  default on; malformed settings dict fails loud via `ConfigurationError`).
- The patched property is consumed by exactly one production site: Strawberry's sync view
  `parse_http_body` calls `self.parse_json(request.body)`
  (`.venv/.../strawberry/http/sync_base_view.py:173`); the GET (`:171`) and multipart (`:175-176`)
  branches never touch `.body`. `strawberry/django/views.py:139` pins
  `request_adapter_class = DjangoHTTPRequestAdapter`, so the sync `GraphQLView` is the sole
  transport affected. The async adapter already hands bytes to `parse_json`
  (`_django.py:100-101`), so no async patch is needed.
- The fix is **jointly owned** with `_strawberry_patches.py`: the bytes fallback alone still 500s,
  because `json.loads(b"\xff\xfe\xfa")` raises `UnicodeDecodeError`, not `JSONDecodeError`
  (verified, exp1 below), which upstream `BaseView.parse_json` does not catch
  (`.venv/.../strawberry/http/base.py:45-49`). Only the companion `parse_json` widening turns it
  into `HTTPException(400, ...)`. Both patches share the one toggle and the one `ready()` dispatch,
  so they cannot be enabled independently within this package; both module docstrings document the
  coupling and carry matching retirement instructions.
- Shape-drift protection: `_validate_upstream_shape` (_cross_web_patches.py:132-159) raises a
  targeted `RuntimeError` from `apply()` when the adapter symbol is missing, `body` is not a
  readable property, or the getter is not unary — dependency drift kills startup loudly instead of
  silently dropping the hardening.
- Tests: `tests/test_cross_web_patches.py` (8 package tests: idempotency, self-healing reinstall,
  installed-at-collection, both body paths, missing-symbol and signature fail-loud, toggle off/on)
  plus the live fakeshop regressions `test_post_invalid_utf8_json_body_returns_400_not_500` /
  `test_post_raw_binary_body_returns_400_not_500`
  (examples/fakeshop/test_query/test_products_api.py:2115-2130).

Prior-cycle context: the 0.0.11 artifact reviewed an earlier shape of this module (once-per-process
`logger.info` on missing symbol); the fail-loud `RuntimeError` redesign has since replaced it in all
three patch modules. The 0.0.11 DRY pass forwarded the three-module `apply()` scaffold to the
project pass; that forward is still live (see DRY analysis).

## Verification

Scratch experiments under `docs/review/temp-tests/_cross_web_patches/test_scratch.py`
(all pass, `uv run pytest docs/review/temp-tests/_cross_web_patches/ --no-cov`):

- **exp1 — coupling proof.** `json.loads` on invalid-UTF-8 bytes raises `UnicodeDecodeError`, not
  `JSONDecodeError`. Confirms this patch is inert for the 400 outcome without the
  `_strawberry_patches` widening; the two ship as one fix.
- **exp2 — bytes fallback widens behavior beyond "400 instead of 500".** A UTF-16-encoded JSON body
  (`'{"query": ...}'.encode("utf-16")`) raises `UnicodeDecodeError` from the upstream getter
  (the pre-patch 500), but with the patch the raw bytes reach `json.loads`, whose
  `detect_encoding` handles UTF-16/UTF-32 per RFC 8259 — the request now **succeeds**. This matches
  the async adapter's existing bytes contract (async already accepted UTF-16 bodies), so it is
  desirable parity, but it contradicts the module docstring's claim that "only the
  previously-500-ing case changes … so `parse_json` raises `UnicodeDecodeError` from `json.loads`"
  (_cross_web_patches.py:29-35) — see Low finding.
- **exp3 — validation checks the live descriptor, not the delegation target.** With the patch
  uninstalled and `_original_body_fget` swapped for a placeholder-shaped raising function,
  `apply()` passes validation (it inspects the live `descriptor.fget`), installs the wrapper, and
  every subsequent `adapter.body` read raises `NotImplementedError`; re-running
  `_validate_upstream_shape()` with the patch installed **also** passes, because the placeholder's
  `(adapter)` signature matches the expected unary shape by construction. See Medium finding.
- **exp4 — pass-through of other exceptions.** A non-`UnicodeDecodeError` raised by the upstream
  getter (e.g. Django's `RawPostDataException` shape) propagates unchanged; the wrapper narrows
  exactly one exception type.

Existing tests: read all of `tests/test_cross_web_patches.py` (bodies, not names) — they pin the
install lifecycle, both body paths, the toggle, and two fail-loud branches. Live regressions
re-run focused: `uv run pytest examples/fakeshop/test_query/test_products_api.py -k "utf8 or
binary or non_object" --no-cov` — 6 passed.

## Improvements

### High

None.

### Medium

- **Observation:** `_validate_upstream_shape`'s not-installed branch validates the wrong object —
  it inspects the live `descriptor.fget` (_cross_web_patches.py:143-144) while `apply()` installs a
  wrapper that delegates to the module-global `_original_body_fget` captured at import
  (_cross_web_patches.py:172-173). The import-time placeholder (_cross_web_patches.py:116-120) was
  written with the exact unary `(adapter)` signature the validator checks for, so a
  placeholder-backed install can never be detected by the shape check, before or after
  installation.
  **Evidence:** exp3 (scratch test): validation passes, the wrapper installs, every `body` read
  raises `NotImplementedError`, and post-install `_validate_upstream_shape()` still passes. The
  sibling `_strawberry_patches.py` validates the *captured original*
  (`not callable(_original_parse_json)`, _strawberry_patches.py:184) and uses a `None` sentinel
  (_strawberry_patches.py:179), so the two same-purpose modules disagree on what "the shape we
  wrap" means.
  **Impact:** the trigger window is narrow (symbol present at import with `body` missing/not a
  property, then a valid property at apply time — a third-party interleaving or an unsupported
  upstream shape), but the failure mode is the worst available: the fail-loud mechanism itself
  approves a wrapper that breaks every sync GraphQL request with `NotImplementedError` instead of
  refusing to install. A validator that inspects a different callable than the one it guards is the
  wrong abstraction regardless of trigger likelihood, and the divergence from the sibling makes the
  three-module scaffold harder to reason about as a family.
  **Recommendation:** own the fix in `_cross_web_patches.py`: drop the raising placeholder in favor
  of the sibling's `None` sentinel (`_original_body_fget: Callable | None = None`, rebound at
  import when the descriptor is a readable property), and make `_validate_upstream_shape` validate
  the delegation target — raise the "no longer a readable property" `RuntimeError` when
  `_original_body_fget` is `None`, and run the signature check against it, in every branch. The
  live-descriptor read then only serves `_patch_is_installed()`. This makes "validated" and
  "delegated-to" the same object by construction, matching `_strawberry_patches.py`.
  **Proof:** permanent package test in `tests/test_cross_web_patches.py` (unreachable from a live
  query, so package level per the test-placement ladder): with `body` reverted to the original
  property and `_original_body_fget` monkeypatched to `None`, `apply()` must raise `RuntimeError`
  and must not install; existing idempotency/reinstall/signature tests must stay green.

### Low

- **Observation:** the module docstring overstates the patch's outcome: "only the
  previously-``500``-ing case changes - the raw bytes are handed back instead, so ``parse_json``
  raises ``UnicodeDecodeError`` from ``json.loads``" (_cross_web_patches.py:29-35), and
  `_patched_body`'s docstring repeats it ("raises a controlled ``400``",
  _cross_web_patches.py:167-170).
  **Evidence:** exp2 — for a UTF-16/UTF-32-encoded JSON body, `json.loads` does not raise: RFC 8259
  `detect_encoding` decodes it and the request *succeeds* (200), where upstream 500s. Only
  undecodable-by-any-JSON-encoding bodies take the documented 400 path.
  **Impact:** the docs are the retirement/re-audit contract for a production monkey-patch; a future
  reviewer writing a regression from them would pin the wrong expectation (400) for a
  UTF-16 body, and the genuinely improved sync/async parity (async already accepted UTF-16 via the
  same bytes-into-`json.loads` route) goes unrecorded.
  **Recommendation:** correct both docstrings in `_cross_web_patches.py`: the fallback makes
  non-UTF-8 bodies behave exactly as on the async transport — JSON-decodable encodings (UTF-16/32)
  now succeed, and everything else 400s via the companion patch. One clause each; no behavior
  change.
  **Proof:** live fakeshop test in `examples/fakeshop/test_query/test_products_api.py` (strongest
  reachable level) POSTing a UTF-16-encoded `{"query": "{ __typename }"}` body and asserting 200
  with `__typename` data, pinning the sync/async parity the corrected docs describe.

- **Observation:** the `apply()` scaffold — `upstream_patches_enabled()` gate,
  `_validate_upstream_shape()` fail-loud, `_patch_is_installed()` re-entrancy check, install —
  is structurally triplicated across `_cross_web_patches.py:186-199`,
  `_strawberry_patches.py:244-268`, and `_django_patches.py:211-242`, including the import-time
  `ImportError`-nulling capture pattern.
  **Evidence:** the three bodies read line-for-line parallel; the family has already changed
  together once (the `logger.info` → `RuntimeError` fail-loud redesign landed in all three), which
  is the "same rule, should change together" test for genuine duplication.
  **Impact:** a fourth patch module or the next scaffold-policy change costs three edits and risks
  drift — the Medium finding above is exactly such a drift (one sibling validates the captured
  original, another the live descriptor).
  **Recommendation:** unchanged from the 0.0.11 cycle: this is cross-module and owned by the
  project-level pass — forward to `docs/review/rev-django_strawberry_framework.md`. Not a local
  edit for this cycle; note the Medium fix here *reduces* the drift the project pass would need to
  reconcile.
  **Proof:** project-pass disposition; if consolidated there, the three modules' existing test
  suites are the regression net.

### DRY analysis

- The three-module `apply()` scaffold triplication (`_cross_web_patches.py` /
  `_strawberry_patches.py` / `_django_patches.py`) described in the second Low finding —
  cross-module, forwarded to the project pass (`docs/review/rev-django_strawberry_framework.md`),
  not acted on locally.

## Summary

The patch is correctly targeted, minimal, and well-tested: the upstream bug is confirmed present in
installed cross-web 0.7.0, the single production consumer (`parse_http_body` →
`parse_json(request.body)` on the sync view) is fully traced, the joint 400 contract with
`_strawberry_patches` is verified live, and the wrap-don't-reimplement design keeps the success
path upstream's. Two tracked changes are warranted: a Medium fix making `_validate_upstream_shape`
validate the actual delegation target (today it inspects the live descriptor while installing a
wrapper bound to the captured original — a demonstrated path to approving a broken install), and a
Low docstring correction recording that the bytes fallback makes UTF-16/32 JSON bodies succeed
(async parity) rather than 400. The `apply()` scaffold DRY remains forwarded to the project pass.
Needs Worker 2.

## Implementation (Worker 2)

Both accepted findings were independently reproduced before editing: the four scratch experiments
under `docs/review/temp-tests/_cross_web_patches/` were re-run against the pre-fix module
(`uv run pytest docs/review/temp-tests/_cross_web_patches/ --no-cov -p no:randomly` — 4 passed),
confirming exp2 (UTF-16 body parses via the bytes fallback) and exp3 (placeholder-backed install
passes the live-descriptor shape check).

Changed files:

- `django_strawberry_framework/_cross_web_patches.py` — the root-cause fix per the Medium
  recommendation: the raising `(adapter)` placeholder is deleted and `_original_body_fget` now
  starts as the `None` sentinel (rebound at import only when `body` is a readable property),
  matching the `_strawberry_patches.py` design. `_validate_upstream_shape` now validates the
  delegation target in every branch: `None` raises the "no longer a readable property"
  `RuntimeError`, and the `(self)` signature check runs against `_original_body_fget` itself. The
  live descriptor is now read only by `_patch_is_installed()`. "Validated" and "delegated-to" are
  the same object by construction, so no placeholder-shaped callable exists for the validator to
  mis-approve — the module's only states are the genuine captured getter or a refused install.
  For the Low finding, the module docstring (lines 31-38), `_patched_body`'s docstring, and
  `apply()`'s docstring were corrected: the previously-500-ing cases now behave exactly as on the
  async transport — JSON-decodable encodings (UTF-16/UTF-32 via `json.loads`' RFC 8259
  `detect_encoding`) succeed, everything else 400s via the companion patch.
- `tests/test_cross_web_patches.py` — permanent package test (Medium proof; the sentinel state is
  unreachable from a live query, so package tier per the test-placement ladder):
  `test_apply_fails_loudly_when_original_getter_was_never_captured` reverts `body` to a
  valid-looking original property, monkeypatches `_original_body_fget` to `None`, and pins that
  `apply()` raises `RuntimeError` ("no longer a readable property") and does **not** install.
- `examples/fakeshop/test_query/test_products_api.py` — live regression (Low proof, strongest
  reachable tier): `test_post_utf16_json_body_succeeds_like_async_transport` POSTs a
  UTF-16-encoded `{"query": "{ __typename }"}` body via `_post_graphql_raw` and asserts 200 with
  `{"__typename": "Query"}`, pinning the sync/async parity the corrected docs describe. The
  malformed-body section comment was updated to state the widened outcome. No seed helper: the
  test exercises the request envelope, not catalog data, matching its sibling malformed-body
  tests.

Finding 3 (three-module `apply()` scaffold DRY): no local edit, per the accepted disposition —
remains forwarded to `docs/review/rev-django_strawberry_framework.md`.

Verification:

- `uv run pytest tests/test_cross_web_patches.py examples/fakeshop/test_query/test_products_api.py
  -k "cross_web or apply or body or utf8 or utf16 or binary or non_object or installed" --no-cov`
  — 17 passed (all 9 pre-existing package tests plus the new sentinel test, both 400 live
  regressions, the 4 non-object 400 cases, and the new UTF-16 200 test).
- `uv run ruff format .` — 351 files left unchanged; `uv run ruff check --fix .` — all checks
  passed.

Changelog-worthiness: the placeholder removal and validator retarget are internal hardening of a
private module with no consumer-visible behavior change (no entry warranted on their own). The
UTF-16/32-bodies-now-succeed parity was already shipped behavior since the patch landed — this
cycle only documents and pins it — so no new entry is warranted; if the original patch's release
note is ever revised, it should say "non-UTF-8 bodies behave as on the async transport" rather
than "400 instead of 500". `CHANGELOG.md` untouched.

## Independent verification (Worker 3)

Scope confirmed: the working-tree diff vs `ff6215ef` for this cycle touches exactly
`django_strawberry_framework/_cross_web_patches.py`, `tests/test_cross_web_patches.py`, and
`examples/fakeshop/test_query/test_products_api.py`; the other dirty/untracked files are named
concurrent work and were left untouched.

Lifecycle re-traced independently from source, not the artifact: the upstream bug is present in
installed cross-web 0.7.0 (`cross_web/request/_django.py::DjangoHTTPRequestAdapter.body` bare
`.decode()`); the sole production consumer is the sync `parse_http_body` →
`self.parse_json(request.body)` (`strawberry/http/sync_base_view.py::SyncBaseHTTPView.parse_http_body`,
with `strawberry/django/views.py` pinning `request_adapter_class`); the async adapter already
returns raw bytes (`_django.py::AsyncDjangoHTTPRequestAdapter.get_body`); upstream `parse_json`
catches only `JSONDecodeError` (`strawberry/http/base.py::BaseView.parse_json`), confirming the
joint 400 ownership with `_strawberry_patches.py`. All three sibling patch modules now validate
the captured original rather than the live attribute (`_strawberry_patches.py::_validate_upstream_shape`,
`_django_patches.py::_validate_upstream_shape`), so the Medium fix restores family consistency.

Medium fix verified genuine: the raising placeholder is gone; the module's only states are the
genuine captured getter or the `None` sentinel, and `None` now refuses install with the targeted
`RuntimeError` in **every** branch (validation runs before the installed short-circuit). No
placeholder-shaped callable remains for the validator to mis-approve.

Experiments (all under `docs/review/temp-tests/_cross_web_patches/`; Worker 1's four scratch
tests re-run and still pass; my additions in `test_w3_verify.py` against a HEAD snapshot of the
pre-fix module, 8/8 passing via `uv run pytest docs/review/temp-tests/_cross_web_patches/
--no-cov -p no:randomly`):

- **w3-exp1 — new package test fails without the fix.** The exact scenario of
  `test_apply_fails_loudly_when_original_getter_was_never_captured` run against the pre-fix
  module (loaded from `git show HEAD:…`): `apply()` raises nothing, installs a broken wrapper,
  and every `body` read then raises `TypeError` — so the permanent test's
  `pytest.raises(RuntimeError)` would fail pre-fix. Confirmed at package tier correctly (the
  sentinel state is unreachable from a live query).
- **w3-exp2 — installed branch also guarded.** With the patch installed and
  `_original_body_fget` mocked to `None`, both `apply()` and `_validate_upstream_shape()` raise
  the "no longer a readable property" `RuntimeError`.
- **w3-exp3 — deliberate behavior delta, disposed as acceptable.** Pre-fix, a third party
  clobbering the live `body` with a non-property made `apply()` raise; post-fix `apply()`
  self-heals by reinstalling the wrapper. This is the sibling `_strawberry_patches.py` contract
  (it never validated the live attribute either) and matches the documented self-healing design;
  recorded here so the delta is deliberate, not accidental.
- **w3-exp4 — no wrapper-wrapping, delegation target genuine.** After repeated `apply()` calls
  the descriptor fget is `_patched_body` and `_original_body_fget` is the genuine upstream
  `DjangoHTTPRequestAdapter.body` getter, which still bare-decodes (patch still needed).

Permanent tests: all 10 package tests in `tests/test_cross_web_patches.py` plus the three live
malformed-body regressions and the new UTF-16 200 test pass (13 focused, `--no-cov`), and the
four non-object 400 live cases pass — the widened-encoding parity did not loosen any 400 path.
Docstrings (module, `_patched_body`, `apply()`) and the live-test section comment now describe
the final behavior (UTF-16/32 parse success, everything else 400 via the companion patch),
verified against w3-exp4 and the live UTF-16 test. Ruff format/check clean on all three scoped
files. Both Low dispositions (docstring fix here; `apply()` scaffold DRY forwarded to the
project pass) confirmed appropriate. No unrelated work absorbed; `CHANGELOG.md` untouched.

Residual notes (non-blocking): `_original_body_fget = None` carries no `Callable | None`
annotation (matches the sibling's unannotated sentinel; no typing gate in CI), and Worker 1's
scratch exp3 still "passes" post-fix only because it injects a foreign unary callable — a state
the module can no longer reach on its own.

Status: verified.
