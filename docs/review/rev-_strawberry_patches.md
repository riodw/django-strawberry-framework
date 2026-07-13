# Review: `django_strawberry_framework/_strawberry_patches.py`

Status: verified

## Understanding

The module owns one defensive monkey-patch: it replaces `strawberry.http.base.BaseView.parse_json`
with a wrapper (`_patched_parse_json`, _strawberry_patches.py:201-236) that closes two upstream
gaps. Gap 1: the wrapper **delegates** to the import-time-captured upstream method
(`_original_parse_json`, _strawberry_patches.py:179) and translates the previously-uncaught
`UnicodeDecodeError` into the same `HTTPException(400, ...)` upstream already raises for malformed
JSON (upstream catches only `json.JSONDecodeError`, `.venv/.../strawberry/http/base.py:45-49` —
confirmed unfixed in installed strawberry-graphql 0.316.0). Gap 2: a successfully-parsed top-level
JSON scalar is rejected with a 400 (_strawberry_patches.py:230-235) because upstream
`parse_http_body` lets a scalar fall through to `data.get("query")` -> raw `AttributeError` -> 500
(`sync_base_view.py:196`, `async_base_view.py:653`; confirmed unfixed, exp2). A `list` passes
through so upstream's `_validate_batch_request` keeps batch ownership.

Lifecycle and joint ownership, fully traced:

- Applied second of the three patch modules from `apps.py::DjangoStrawberryFrameworkConfig.ready`
  (apps.py:38-44); gated by `conf.py::upstream_patches_enabled` (default on; malformed settings
  dict fails loud). Idempotent and self-healing via `_patch_is_installed`
  (_strawberry_patches.py:239-241); one install on `BaseView` covers both `SyncBaseHTTPView` and
  `AsyncBaseHTTPView` (and Strawberry's Django `GraphQLView`/`AsyncGraphQLView`, which pin their
  adapters in `strawberry/django/views.py:139,187` and convert `HTTPException` to a text/plain
  response in `dispatch`, views.py:150-160, 210-220).
- Delegate-vs-reimplement (the cycle question): for gap 1 this module sits on the **delegate**
  side — the original is called unchanged, so upstream body changes flow through, and
  `_validate_upstream_shape` (_strawberry_patches.py:182-198) correctly pins the delegation
  target (`callable(_original_parse_json)` + the `(self, data)` arity), matching item 1's hardened
  `_cross_web_patches.py` design. No body pin is needed for gap 1. Gap 2 is different in kind: the
  scalar guard is not a delegation but a **transplanted contract** — a rule owned by
  `parse_http_body` ("the parsed body must be an object or a batch array") grafted onto
  `parse_json`, which is a generic JSON helper with more callers than the body path. That
  transplant is where the High finding lives; it is a present-day behavior bug, not validator
  drift, so no additional pin on today's module would have caught it.
- Complete call-site inventory of `parse_json` in installed strawberry (grep, all 8 sites): sync
  POST body (`sync_base_view.py:173`), async POST body (`async_base_view.py:634`), async
  multipart-subscriptions body (`async_base_view.py:616`), sync multipart `operations`/`map`
  (`sync_base_view.py:149-150`), async multipart `operations`/`map`
  (`async_base_view.py:264-267`), and GET `variables` / GET `extensions` inside
  `parse_query_params` (`base.py:64,70`). The guard is correct at the six body/multipart sites
  (at the multipart sites it beneficially converts an upstream scalar-`operations` 500 into a
  400) and **wrong at the two `parse_query_params` sites**, where upstream has its own precise
  handling (`sync_base_view.py:203-215`, `async_base_view.py:660-672`: scalar `variables` /
  `extensions` -> per-param 400; `null` -> `None` -> request executes).
- The module docstring's gap-2 rationale (_strawberry_patches.py:54-71) claims "``parse_json`` is
  the *only* producer of a scalar ``data`` that reaches ``parse_http_body`` (the GET
  ``parse_query_params`` and ``parse_multipart`` paths always return a ``dict``)". True as far as
  it goes — but it analyzes only the flow *into* `parse_http_body` and never inventories the
  *other* callers of the method being patched. The nested GET parses were missed.
- Joint ownership: gap 1 on the sync view requires the companion `_cross_web_patches.py` bytes
  fallback (verified in item 1); the fakeshop `/graphql/` mount is the sync `GraphQLView`
  (examples/fakeshop/config/urls.py:64-68, `allow_queries_via_get` defaults to `True`).
- Tests: `tests/test_strawberry_patches.py` (12 tests, 17 cases: idempotency, revert-reinstall,
  installed-at-collection, UnicodeDecodeError translation, valid-JSON pass-through, malformed-JSON
  400, six scalar rejections, list pass-through, missing-symbol/arity fail-loud, toggle off/on)
  plus live regressions in `examples/fakeshop/test_query/test_products_api.py:2118-2176`
  (invalid-UTF-8, raw binary, UTF-16 success, four non-object bodies). All bodies read; none —
  package or live — exercises a GET request or `parse_query_params`, which is exactly the blind
  spot the High finding sits in.

Prior-cycle context honored: item 1 used this module's `None`-sentinel + delegation-target
validation as the reference design (still sound for gap 1); item 2's artifact pre-forwarded this
module's stale "logging or" docstring clause to this item (Low below); the three-module `apply()`
scaffold DRY stays forwarded to the project pass per the 0.0.11 disposition.

## Verification

Scratch experiments under `docs/review/temp-tests/_strawberry_patches/test_scratch.py` (5 passed,
`uv run pytest docs/review/temp-tests/_strawberry_patches/ --no-cov -n0 -p no:randomly`):

- **exp1 — gap 1 still needed.** `_original_parse_json(BaseView(), bytes([0x7b, 0x80]))` raises
  `UnicodeDecodeError` at installed strawberry 0.316.0 (mirrors the docstring's retirement probe).
- **exp2 — gap 2 still needed, live.** POST body `b"null"` to fakeshop `/graphql/`: 400 with the
  patch; 500 with `BaseView.parse_json` reverted to the captured original (the raw
  `AttributeError` escapes `execute_operation`, which catches only `JSONDecodeError`/`KeyError`,
  `sync_base_view.py:77-83`).
- **exp3 — the High, live.** GET `?query={ __typename }&variables=null` (and `extensions=null`):
  **200 with data upstream (patch reverted), 400 under the patch** — a previously-succeeding valid
  request is broken by the patch, and the 400 body says "request body" on a GET that has no body.
- **exp4 — message shadowing, live.** GET `?variables=42`: 400 both ways, but upstream's precise
  "The GraphQL operation's `variables` must be an object or null, if provided." is replaced by the
  patch's generic request-body message, raised before upstream's own check can run.

Other verification: all 8 `parse_json` call sites enumerated by grep over the installed package
(inventory above); `replace_placeholders_with_files` read to confirm the multipart scalar outcome;
upstream `parse_http_body` (sync and async) re-read in full — the installed version already
carries per-param isinstance 400s for `query`/`variables`/`extensions` *values* but still no
`isinstance(data, dict)` guard before `data.get("query")`, so the docstring's upstream-status
section remains accurate for both gaps. Focused permanent runs: `uv run pytest
tests/test_strawberry_patches.py` + the three live malformed-body regressions `--no-cov -n0` — 23
passed. Scoped diff vs the item baseline `122eb74d` for `_strawberry_patches.py` /
`tests/test_strawberry_patches.py` is empty (target untouched this cycle).

## Improvements

### High

- **Observation:** the gap-2 scalar guard fires at every `parse_json` call site, not only the
  request-body sites it was designed for. Upstream's `parse_query_params` parses the GET
  `variables` and `extensions` query params through `self.parse_json` (`base.py:64,70`), so the
  guard intercepts them: a GET request with `variables=null` or `extensions=null` — valid per
  upstream's own contract ("`variables` must be an object or **null**", enforced at
  `sync_base_view.py:203-215`) — now 400s where upstream executes it, and a scalar
  `variables`/`extensions` gets the wrong error ("The GraphQL request **body** must be a JSON
  object …" on a GET with no body) instead of upstream's precise per-param 400.
  **Evidence:** exp3 (200 upstream -> 400 patched, live on fakeshop's sync `GraphQLView`, both
  params) and exp4 (message shadowing, live); the 8-site call-site inventory in Understanding. The
  module docstring's one-site rationale (_strawberry_patches.py:54-71, 217-224) analyzed only
  producers of `parse_http_body`'s `data` and never the other callers of the patched method.
  **Impact:** a production behavior regression shipped automatically to every consumer via
  `INSTALLED_APPS` — the patch module whose stated purpose is turning upstream 500s into clean
  400s instead turns a previously-succeeding valid request into a 400, on both the sync and async
  views, and degrades diagnostics for GET scalar params. No package or live test exercises a GET
  request, so nothing pins the correct behavior today.
  **Recommendation:** own the fix in `_strawberry_patches.py`. Keep `_patched_parse_json` as-is
  for the six body/multipart sites, and shield the two GET sites by also patching
  `BaseView.parse_query_params` with a reimplementation of upstream's 16-line body
  (`base.py:57-72`) whose two nested parses call `_original_parse_json` directly — restoring
  exact upstream GET semantics (`null` -> `None` -> executes; scalar -> upstream's own precise
  400; malformed -> upstream's `JSONDecodeError` 400). Because that is a **reimplementation**,
  pin the superseded body source in `_validate_upstream_shape` exactly as
  `_django_patches.py::_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` does (item-2 precedent:
  delegators pin the call shape, reimplementers pin the body), and install/validate it through
  the existing `apply()` lifecycle. Update the module and wrapper docstrings with the corrected
  call-site inventory, including the previously-undocumented multipart `operations`/`map`
  widening (scalar -> 400 instead of upstream's 500). Considered and rejected: passing `None`
  through the scalar guard (reopens POST `b"null"` -> 500, exp2); reimplementing both
  `parse_http_body` bodies with the eventual #3398 `isinstance(data, dict)` guard (the true
  contract owner, but two ~65-line frequently-evolving bodies to pin — disproportionate drift
  surface vs one stable 16-liner); a proxy-`self` delegation trick routing the original
  `parse_query_params` body's `self.parse_json` to the original (avoids the source pin but turns
  upstream body drift into a request-time crash instead of an apply-time `RuntimeError`).
  **Proof:** live fakeshop tests (strongest reachable tier, GET on `/graphql/`):
  `variables=null` and `extensions=null` -> 200 with data; `variables=42` -> 400 whose body is
  upstream's "`variables` must be an object or null" message, not the request-body message; the
  existing four non-object POST-body 400s and the batch pass-through stay green. Package tests
  for the new pin: a monkeypatched drifted `parse_query_params` source makes `apply()` raise the
  targeted `RuntimeError` without installing; install/reinstall idempotency extended to the
  second patched method. exp3/exp4 re-run against the fixed module must show upstream-identical
  GET behavior with the patch on.

### Medium

None.

### Low

- **Observation:** `apply()`'s docstring says the opt-out path "Returns before logging or
  touching anything" (_strawberry_patches.py:256), but the module has not logged since the
  once-per-process `logger.info` design was replaced by the fail-loud `RuntimeError` family
  redesign. Pre-forwarded to this item by the item-2 artifact (rev-_django_patches.md, Low 1).
  **Evidence:** no `logging` import or logger call anywhere in the module; the sibling's identical
  vestige was removed in item 2.
  **Impact:** stale phrase in the re-audit contract of a production monkey-patch; one clause, no
  behavior.
  **Recommendation:** drop "logging or" from the clause in `_strawberry_patches.py`, matching the
  item-2 fix; fold into the same edit as the High's docstring corrections.
  **Proof:** docs-only; reading the corrected docstring against the module body.

- **Observation:** the `apply()` scaffold — toggle gate, `_validate_upstream_shape()`,
  `_patch_is_installed()`, install — plus the import-time `ImportError`-nulling capture is
  structurally triplicated across `_strawberry_patches.py:244-268`, `_cross_web_patches.py`, and
  `_django_patches.py`.
  **Evidence:** the three bodies read line-for-line parallel; the family has changed together
  (fail-loud redesign, item-1 validator retarget).
  **Impact:** a fourth patch module or the next scaffold-policy change costs three edits and
  risks drift.
  **Recommendation:** unchanged disposition from 0.0.11 and items 1-2: cross-module, owned by the
  project pass — forward to `docs/review/rev-django_strawberry_framework.md`. No local edit. Note
  for that pass: if the High lands, this module becomes the first to carry *both* a delegating
  wrapper (arity pin) and a reimplementing one (body pin), so a shared scaffold must support
  per-patch validation depth.
  **Proof:** project-pass disposition; the three modules' existing suites are the regression net.

### DRY analysis

- The three-module `apply()` scaffold triplication (`_strawberry_patches.py` /
  `_cross_web_patches.py` / `_django_patches.py`) described in the second Low finding —
  cross-module, forwarded to the project pass (`docs/review/rev-django_strawberry_framework.md`),
  unchanged from the 0.0.11 and item-1/item-2 dispositions; not acted on locally.

## Summary

Gap 1 (the `UnicodeDecodeError` widening) is exactly right: pure delegation, validator pinned to
the delegation target, both upstream gaps confirmed still present at installed strawberry
0.316.0, and the POST-body lifecycle is well-pinned by 17 package test cases plus seven live
regressions. Gap 2's scalar guard, however, was grafted onto a method with eight call sites and
verified live to break the two it never accounted for: GET `variables=null` / `extensions=null`
regress from 200 to 400, and GET scalar params lose upstream's precise per-param 400 message —
a production public-contract regression shipped to every consumer, invisible to the test suites
because neither tier exercises a GET request. One High fix is tracked: shield
`parse_query_params` with a source-pinned reimplementation routing its nested parses through the
captured original (restoring exact upstream GET semantics while keeping both gap fixes on the
body paths), plus corrected docstrings carrying the full call-site inventory. One Low docstring
vestige ("logging or", pre-forwarded from item 2) folds into the same edit. The `apply()`
scaffold DRY stays forwarded to the project pass. Needs Worker 2.

## Implementation (Worker 2)

All of Worker 1's findings re-verified before editing: the five scratch experiments re-run green as
found (`uv run pytest docs/review/temp-tests/_strawberry_patches/ --no-cov -n0 -p no:randomly`,
5 passed pre-fix), the 8-site `parse_json` call-site inventory re-traced in the installed
strawberry 0.316.0, and the multipart widening confirmed by reading
`strawberry/file_uploads/utils.py::replace_placeholders_with_files` (a scalar `operations`
passes through untouched to `data.get("query")` -> 500; a scalar `map` crashes `.items()` -> 500;
the guard converts both to 400).

### Changed files

- `django_strawberry_framework/_strawberry_patches.py` — the High fix, as recommended: captured
  `_original_parse_query_params` at import time; added `_patched_parse_query_params`, a
  reimplementation of upstream's 16-line `parse_query_params` whose two nested parses call
  `_original_parse_json` directly (exact upstream GET semantics: `null` -> `None` -> executes,
  scalar passes through to upstream's per-param 400, malformed -> upstream's own 400, empty-string
  falsy skip preserved); pinned the superseded body as `_UPSTREAM_PARSE_QUERY_PARAMS_SOURCE`
  (verbatim at 0.316.0, the item-2 reimplementer precedent) with `_validate_upstream_shape` now
  running three tiers for it (presence, `(self, params)` arity, dedented-source match; unreadable
  source treated as drift); `_patch_is_installed` requires BOTH methods so a partial revert
  re-installs the pair (the guard never runs unshielded); `apply()` installs both. Docstrings
  corrected: the module docstring's false "only producer" one-site rationale replaced with the
  full 8-site inventory including the previously-undocumented multipart `operations`/`map`
  widening and the GET shield's rationale/retirement coupling to #3398; the wrapper docstring
  carries the same corrected inventory; the Low "logging or" vestige dropped from `apply()`'s
  docstring in the same edit.
- `tests/test_strawberry_patches.py` — 11 new tests (28 total): pair install at collection,
  pair re-install on a partial `parse_query_params` revert, shield parse semantics
  (`null` -> `None` for both params, scalar pass-through for upstream's per-param 400, object
  happy path, malformed -> upstream 400, empty-string falsy skip), and the fail-loud family for
  the new pin (missing symbol, `(self, params)` arity drift, body drift raising before install,
  sourceless original treated as drift).
- `examples/fakeshop/test_query/test_products_api.py` — 3 new live tests (strongest reachable
  tier, real GET against `/graphql/`): `variables=null` / `extensions=null` -> 200 with data
  (the exp3 regression, pinned fixed); `variables=42` -> 400 carrying upstream's precise
  "`variables` must be an object or null" message and NOT the request-body message (exp4);
  section comment extended to name the GET shield.
- `docs/review/temp-tests/_strawberry_patches/test_scratch.py` (untracked scratch) — exp3/exp4
  updated per the Proof clause to assert upstream parity against the fixed module, with the
  revert helper now restoring both methods for a true upstream comparison.

### Verification

- `uv run pytest tests/test_strawberry_patches.py --no-cov -n0 -p no:randomly` — 28 passed
  (every `apply()` call exercises the source pin against the installed 0.316.0, so the pin's
  accept-current-upstream premise is validated by the whole suite).
- `uv run pytest examples/fakeshop/test_query/test_products_api.py -k "utf8 or binary or utf16
  or non_object or get_query_with" --no-cov -n0 -p no:randomly` — 10 passed (3 new GET tests plus
  all 7 pre-existing live body regressions stay green: no POST-path regression from the pair
  install).
- Scratch re-run post-fix — 6 passed (exp1/exp2 unchanged: both gaps still need the patch;
  exp3/exp4 now prove upstream-identical GET behavior with the patch on, per the Proof clause).
- Formatter/linter: `uv run ruff format .` (352 files unchanged) and `uv run ruff check --fix .`
  (1 auto-fix: an unused `noqa` it removed from the new sourceless test; 0 remaining).
  `scripts/check_trailing_commas.py --check` clean on the three edited files.
- Scoped diff vs baseline `122eb74d`: `_strawberry_patches.py` +206/-32,
  `tests/test_strawberry_patches.py` +167/-1, plus the appended live tests. All other dirty files
  are the verified item-1/item-2 review diffs or the concurrent maintainer session's in-flight
  work — preserved untouched.

### Findings disposition

- High — implemented as recommended (shield + body pin + docstring inventory). Not rejected or
  altered.
- Low ("logging or" vestige) — implemented, folded into the same docstring edit.
- Low (three-module `apply()` scaffold DRY) — no local edit, stays forwarded to
  `docs/review/rev-django_strawberry_framework.md` per the standing disposition; note for that
  pass: this module now carries both a delegating wrapper (arity pin) and a reimplementing one
  (body pin), so a shared scaffold must support per-patch validation depth.

### Changelog

Not edited (no authorization). The change deserves a release note: it fixes a shipped production
regression where the upstream-patch module broke valid GET requests
(`?variables=null` / `?extensions=null` returned 400 instead of executing) and degraded GET
scalar-param diagnostics for every consumer with the patches enabled.

## Independent verification (Worker 3)

All behavior re-traced independently from the diff, the full module, the installed
strawberry-graphql 0.316.0 sources (`http/base.py`, `http/sync_base_view.py`,
`http/async_base_view.py`, `file_uploads/utils.py`), `apps.py`, `conf.py`, the fakeshop mount
(`examples/fakeshop/config/urls.py:63-72`, sync `GraphQLView` with
`multipart_uploads_enabled=True`), and all 28 package + 10 live tests read in full. Scratch
experiments in `docs/review/temp-tests/_strawberry_patches/test_scratch_w3.py` (5 passed,
`--no-cov -n0 -p no:randomly`), written without reading Worker 2's scratch.

Verified good:

- **Source pin exactness.** `textwrap.dedent(inspect.getsource(_original_parse_query_params))`
  compared `==` against `_UPSTREAM_PARSE_QUERY_PARAMS_SOURCE` in a live `django.setup()` process:
  exact match, both patches installed by `ready()`. No false-positive startup break; every
  `apply()` in the 28-test suite re-exercises the pin.
- **Patch surface re-traced.** Only `BaseView` defines `parse_json` / `parse_query_params` in the
  installed strawberry (no subclass shadows), so the pair install covers the sync and async views
  and Strawberry's Django views. The shield replaces upstream's method wholesale, so the two GET
  parses go through `_original_parse_json` (guard off); every other reachable call site sees the
  shielded wrapper. `_original_parse_json` still dispatches `self.decode_json`, preserving
  consumer `decode_json` overrides.
- **High regression gone, live, upstream-identical.** Scratch parity test: nine GET shapes
  (`variables`/`extensions` = `null`, scalar, `"boom"`, malformed, object, empty string,
  `[1, 2]`, absent) driven against pure upstream (both methods reverted) and against the patched
  pair - status codes and bodies identical; `variables=null`/`extensions=null` -> 200 with data,
  `variables=42` -> upstream's per-param 400 message.
- **New tests fail without the fix.** Scratch pre-fix simulation (guard installed, shield absent):
  GET `variables=null` -> 400 with the request-body message and `variables=42` -> 400 with the
  shadowed message - exactly the assertions the three new live tests invert. The 11 new package
  tests target symbols that do not exist pre-fix.
- **Break attempts.** `apply()` x5 stable; partial revert of `parse_json` alone (the direction the
  permanent tests don't cover) reports not-installed and re-installs the pair; multipart scalar
  `operations` and scalar `map` live on fakeshop -> 400 patched vs 500 with both methods reverted
  (confirming the docstring's widening claim and the `replace_placeholders_with_files` trace);
  POST body paths (`null`, `42`, `"a"`, malformed, invalid UTF-8) still 400 after the pair
  install. Async parity rests on the shared `BaseView` methods (no async mount exists in
  fakeshop); `async_base_view.py:632` calls `self.parse_query_params` directly - covered.
- **Focused permanent runs.** `tests/test_strawberry_patches.py` 28 passed;
  `-k "utf8 or binary or utf16 or non_object or get_query_with"` live run 10 passed. Scoped diff
  vs `122eb74d` touches only the three named files; concurrent maintainer work untouched.
- **Findings disposition.** High: implemented as recommended and verified live. Low ("logging
  or"): removed, docstring now matches the body. Low (scaffold DRY): correctly left forwarded to
  the project pass with the per-patch-validation-depth note.

Revision needed (one item, docstring-only - the behavior is correct):

- **The call-site arithmetic in the shipped docstrings is wrong.** Grep of the installed
  strawberry 0.316.0 finds **nine** `self.parse_json(` call expressions: `sync_base_view.py`
  149/150/173, `async_base_view.py` 264/267/616/634, `base.py` 64/70. The module docstring's
  bullets enumerate all nine, but the headline says "eight in total" and "the six body/multipart
  sites" (the bullets enumerate seven); the wrapper docstring repeats "(eight; ...)" and "six
  body/multipart sites". The counts reconcile only if the `async_base_view.py:616` site inside
  `AsyncBaseHTTPView.parse_multipart_subscriptions` is excluded - and that method is genuinely
  dead code at 0.316.0 (defined, never called anywhere in the installed package; grep finds only
  the definition) - but the docstring never says so, so a re-auditor repeating the artifact's own
  grep method finds nine sites against an "eight in total" claim in the exact inventory this fix
  shipped to be authoritative. Fix in `_strawberry_patches.py` (module docstring and
  `_patched_parse_json` docstring): either count the textual sites (nine total, seven
  body/multipart) or keep eight/six and state explicitly that the multipart-subscriptions site is
  defined-but-uncalled at 0.316.0, so eight are reachable. Reproduce with:
  `grep -rn "self.parse_json(" .venv/lib/python*/site-packages/strawberry` (9 hits) and
  `grep -rn "parse_multipart_subscriptions" .venv/lib/python*/site-packages/strawberry` (1 hit,
  the definition). The same slip originates in Worker 1's Understanding ("all 8 sites" over nine
  listed line numbers) and recurs in Worker 2's "full 8-call-site inventory" wording; only the
  shipped docstrings need the edit.

Everything else is verified; once the count is corrected (and `uv run ruff format .` /
`uv run ruff check --fix .` re-run), this item is ready to verify.

## Iterations

### Worker 2 revision pass (call-site arithmetic, docstring-only)

Counts re-verified before editing with Worker 3's reproduction greps:
`grep -rn "self.parse_json(" .venv/lib/python*/site-packages/strawberry` -> **nine** call
expressions (`sync_base_view.py` 149/150/173, `async_base_view.py` 264/267/616/634, `base.py`
64/70); `grep -rn "parse_multipart_subscriptions"` -> one source hit, the definition at
`async_base_view.py:610` (plus its `.pyc`), confirming
`AsyncBaseHTTPView.parse_multipart_subscriptions` is defined-but-uncalled dead code at 0.316.0.

Fix chosen: count the textual sites (Worker 3's first option). Both shipped docstrings in
`django_strawberry_framework/_strawberry_patches.py` now say **nine** total call sites and
**seven** body/multipart sites, with an explicit note that the multipart-subscriptions site is
defined but never called in the installed 0.316.0 package (so eight sites are reachable), and the
first inventory bullet names that site as the dead-code one:

- module docstring: the "eight in total" headline replaced with nine-total/one-unreachable
  wording ahead of the unchanged nine-bullet inventory; "the six body/multipart sites" -> "the
  seven body/multipart sites" in the GET-shield paragraph;
- `_patched_parse_json` docstring: "(eight; ...)" -> "(nine, one of them dead code at 0.316.0;
  ...)" and "six body/multipart sites" -> "seven body/multipart sites".

No source-behavior, test, or other-file changes; the diff is confined to the two docstrings.
Verification: `uv run ruff format .` (352 files unchanged), `uv run ruff check --fix .` (all
checks passed), `uv run pytest tests/test_strawberry_patches.py --no-cov -n0 -p no:randomly` —
28 passed. Concurrent dirty work outside the target untouched.

### Worker 3 re-review pass (verified)

The single revision item (call-site arithmetic in the shipped docstrings) is fixed and nothing
else drifted:

- **Counts re-reproduced against the installed strawberry-graphql 0.316.0** (version confirmed
  via `strawberry_graphql-0.316.0.dist-info`). `grep -rn "self.parse_json("` over the installed
  package -> exactly **nine** call expressions (`sync_base_view.py` 149/150/173,
  `async_base_view.py` 264/267/616/634, `base.py` 64/70);
  `grep -rn "parse_multipart_subscriptions"` -> one `.py` hit, the definition at
  `async_base_view.py:610`, confirming the site inside it is defined-but-uncalled dead code.
  Nine total / seven body-or-multipart / eight reachable is the correct arithmetic.
- **Shipped docstrings now carry it.** Module docstring: "nine in total, though one is
  unreachable (`AsyncBaseHTTPView.parse_multipart_subscriptions` is defined but never called ...
  eight sites are reachable)", the first inventory bullet names the dead-code site, and the
  GET-shield paragraph says "the seven body/multipart sites". `_patched_parse_json` docstring:
  "(nine, one of them dead code at 0.316.0; ...)" and "seven body/multipart sites". The
  arithmetic a re-auditor reproduces with the artifact's greps now matches the shipped inventory.
- **No behavior drift since the prior verification.** The full scoped diff of the target vs
  baseline `122eb74d` re-read hunk by hunk: every executable-code hunk (import-time pair capture,
  `_UPSTREAM_PARSE_QUERY_PARAMS_SOURCE` pin, three-tier validator, `_patched_parse_query_params`
  reimplementation routing both nested parses through `_original_parse_json`, both-methods
  `_patch_is_installed`, pair install in `apply()`) is identical to the design verified in the
  prior pass; the delta since that pass is confined to the module and `_patched_parse_json`
  docstrings plus the retirement note. Tests and live tests unchanged in substance (28 package
  tests collected as before; W2's originally recorded `+167/-1` vs today's numstat `+166/-1` for
  `tests/test_strawberry_patches.py` is recording imprecision, not a content change - the suite
  is the same 28 tests, all read in the prior pass).
- **Spot runs.** `uv run pytest tests/test_strawberry_patches.py
  docs/review/temp-tests/_strawberry_patches/test_scratch_w3.py --no-cov -n0 -p no:randomly` —
  33 passed (28 package + the 5 prior-pass scratch parity/break tests, so the live GET parity,
  pre-fix failure simulation, multipart widening, and POST shielding all still hold).

Status set to `verified`; plan checkbox marked in `docs/review/review-0_0_13.md`.
