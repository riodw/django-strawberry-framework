# DRY review: `django_strawberry_framework/_strawberry_patches.py`

Status: verified

## System trace

Reviewed the complete target and connected behavior at item baseline
`c846488289b2f3a29100571304c57634f68d759e`. The working target has no diff from that baseline;
concurrent changes elsewhere were not used as evidence.

The module owns one Strawberry monkey-patch pair and its complete lifecycle:

- `django_strawberry_framework/_strawberry_patches.py::_patched_parse_json` delegates to the
  import-time-captured upstream `BaseView.parse_json`, translates the otherwise uncaught
  `UnicodeDecodeError` to `HTTPException(400)`, and rejects parsed JSON scalars before Strawberry
  reaches `data.get(...)`. It preserves dictionaries, batch lists, other exceptions, and consumer
  `decode_json` overrides.
- `django_strawberry_framework/_strawberry_patches.py::_patched_parse_query_params` is the paired
  GET shield. It preserves upstream `variables` / `extensions` parsing through the captured
  original parser, so `null` remains valid and scalar parameters reach Strawberry's precise
  per-parameter validation rather than the request-body scalar guard.
- `django_strawberry_framework/_strawberry_patches.py::_validate_upstream_shape` validates both
  captured call shapes and source-pins the reimplemented query-parameter body. Unreadable or
  changed source fails loudly rather than silently replacing new upstream behavior.
- `django_strawberry_framework/_strawberry_patches.py::_patch_is_installed` treats the two methods
  as one atomic install. `django_strawberry_framework/_strawberry_patches.py::apply` self-gates,
  validates, no-ops only when the pair is intact, and repairs either partial revert.

`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` is the sole automatic
caller. It invokes the Django, Strawberry, and `cross_web` patch modules at app load; each module
independently reads
`django_strawberry_framework/conf.py::upstream_patches_enabled`. The shared
`DJANGO_STRAWBERRY_FRAMEWORK["APPLY_UPSTREAM_PATCHES"]` setting defaults on, and explicit `False`
also makes a direct test or consumer call to this module's `apply()` a no-op. The module remains
private and has no package-root export.

The request paths converge as intended:

- Sync JSON first crosses
  `django_strawberry_framework/_cross_web_patches.py::_patched_body`. Valid UTF-8 retains
  `cross_web`'s string result; invalid UTF-8 falls back to raw bytes, which then reach the patched
  Strawberry parser. UTF-16/32 JSON can consequently succeed through `json.loads`, while invalid
  binary becomes a controlled 400.
- Async JSON already arrives as raw bytes from `AsyncDjangoHTTPRequestAdapter.get_body`; inherited
  `BaseView.parse_json` supplies the same exception translation and scalar rejection without an
  async-specific framework implementation.
- Sync and async multipart upload parsing both call `self.parse_json` for `operations` and `map`,
  so malformed encodings and scalar form fields receive the same controlled 400 before
  `replace_placeholders_with_files`.
- GET calls the paired `parse_query_params` replacement instead. `variables=null` and
  `extensions=null` remain `None`; non-object values continue into Strawberry's own
  "`variables` / `extensions` must be an object or null" checks.
- Strawberry 0.317.2 also defines an async multipart-subscription parser that calls
  `self.parse_json`, but the installed package contains no caller for that method. Its behavior is
  covered if upstream activates the path, but it has no current public effect.

The consumer-visible effect is transport hardening, not a new API: malformed binary or JSON-scalar
bodies return HTTP 400 rather than an unhandled 500; sync UTF-16 JSON gains parity with async; valid
GET parameter semantics and custom JSON decoders remain intact.

Upstream was rechecked on 2026-07-12. Strawberry 0.317.2 remains the latest PyPI release, issue
https://github.com/strawberry-graphql/strawberry/issues/3398 remains open, and current `main` still
catches only `json.JSONDecodeError` in `BaseView.parse_json` and still calls `data.get(...)` without
a top-level mapping guard in both HTTP views. Current `main` has expanded streaming transport
machinery, but the two patched `BaseView` method signatures and the source-pinned
`parse_query_params` body remain compatible.

## Verification

Baseline searches followed every `apply`, patch setting, target method, multipart call, and live
request assertion while excluding prior review and DRY artifacts. Installed Strawberry source
contains exactly nine `parse_json` call sites relevant to this patch: three sync body/upload sites,
four async body/upload/subscription sites, and the two GET parameter sites shielded by the paired
replacement.

Permanent coverage is split by responsibility rather than duplicated:

- `tests/test_strawberry_patches.py` pins delegated success/error behavior, scalar/list handling,
  GET shielding, custom pair installation and repair, upstream signature/body drift, and opt-out.
- `tests/test_cross_web_patches.py` pins the separate sync-adapter bytes fallback.
- `tests/test_apps.py` pins all three app-load dispatches and repeated `ready()` behavior.
- `examples/fakeshop/test_query/test_products_api.py` proves the sync public HTTP effects for
  invalid UTF-8, raw binary, UTF-16 success, scalar bodies, valid GET `null`, and Strawberry's
  original scalar-parameter error.
- `tests/base/test_conf.py` pins the patch toggle's absent/true/false matrix.

An isolated in-process matrix using the project virtualenv additionally exercised the inherited
sync and async `parse_http_body` paths, sync and async multipart `operations` parsing, the
`cross_web` handoff, both GET outcomes, and a `BaseView.decode_json` override. It passed with:

`verified: sync+cross_web, async, GET shield, sync/async multipart, custom decode_json`

Strongest rejected candidates:

1. **Move scalar validation to `parse_http_body`.** This would not consolidate ownership.
   Strawberry implements that method separately for sync and async, and multipart `operations` /
   `map` parsing sits outside the post-body validation point. Correct coverage would require
   parallel transport patches or a new upstream abstraction. The current `BaseView.parse_json`
   owner is the one existing shared parse seam; the GET shield is the narrowly pinned cost of using
   it for a body-only invariant.
2. **Delegate the GET shield instead of source-pinning its body.** Calling the original normally
   dispatches its nested calls back through `self.parse_json`, reintroducing the invalid body guard.
   Temporarily mutating the class method would be request-unsafe, and a proxy `self` would alter
   subclass identity/state semantics. The small, exact reimplementation plus fail-loud source pin
   is safer and gives upstream continued ownership at the explicit drift gate.
3. **Generalize patch lifecycle across the three dependency modules.** The shared four-step
   sequence is superficial. Installation units differ (one property, one classmethod, or an atomic
   method pair), as do descriptor handling, delegation targets, source pins, drift messages, and
   repair conditions. A callback/mode-driven helper would hide dependency ownership without
   eliminating any invariant. Per-module self-gating is also required because each `apply()` is a
   valid direct entry point.
4. **Merge the unit and live regressions.** The package tests prove private installation and
   fail-loud drift paths that no HTTP request can reach; the live tests prove status codes and
   `cross_web` cooperation. The separate `cross_web` suite likewise protects a different upstream
   owner and retirement condition. Combining them would reduce diagnostics, not duplicated policy.

## Opportunities

None — the body rule, GET exception, install pair, shared setting, and `cross_web` handoff each have
one repository owner. The closest structural repetitions either represent distinct upstream
contracts or would split the current single sync/async/multipart behavior into more patch sites.

## Judgment

The baseline implementation is already consolidated at Strawberry's shared `BaseView` parse seam
and explicitly contains the only exception that seam requires. Its paired lifecycle prevents an
unsafe half-install, its companion dependency patch owns the sync-only adapter defect, and the
test tiers prove different contracts. No tracked source or permanent-test change is warranted;
Worker 3 should independently verify this zero-edit judgment.

## Independent verification (Worker 3)

Verified independently against item baseline `c846488289b2f3a29100571304c57634f68d759e`.
The target, AppConfig/settings owner, `cross_web` companion, and connected unit/live regression
files are all unchanged from that baseline, so this remains a zero-edit production item.

The trace confirmed that inherited `BaseView.parse_json` is the one shared seam for sync and async
JSON bodies plus both multipart implementations. The paired `parse_query_params` replacement is
the necessary narrow exception: it preserves valid GET `null`, leaves scalar parameters for
Strawberry's parameter-specific validation, and still dispatches through consumer `decode_json`
overrides. AppConfig is the sole automatic dispatcher; each direct `apply()` independently honors
the shared setting; and `cross_web` owns only the sync adapter's pre-parser bytes fallback.

An isolated matrix passed for the sync/async JSON paths, sync/async multipart operations, GET
shield, custom decoder success/error behavior, and `cross_web` UTF-16/invalid-byte handoff. Focused
permanent tests also passed: 65 patch/AppConfig/settings tests and 10 live HTTP regressions.

The supported floor installed locally is Strawberry 0.316.0. PyPI 0.317.2 remains latest, and
current upstream `main` at `ef20f650c96a05259bf8b3298f182c8074014a74` retains both patched
signatures, the pinned query-parameter body, the uncaught `UnicodeDecodeError`, and the unguarded
sync/async `data.get("query")`; issue #3398 remains open. The retirement claim is therefore sound:
the scalar guard and its GET shield retire together when upstream owns the mapping check, while the
Unicode wrapper remains until that separate gap is fixed.

The rejected alternatives remain rejected. Moving validation into sync/async body methods would
multiply the rule and miss multipart parsing; delegating the GET method would redispatch into the
guard, while class mutation or a proxy would introduce request-safety or subclass-semantics risks;
and a common patch-lifecycle helper would parameterize genuinely different descriptors, validation,
and repair units. The debug-toolbar JSON handling is response diagnostics, not another request
parser owner. No consolidation or permanent-test change is warranted.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
