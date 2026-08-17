# Review: `django_strawberry_framework/_strawberry_patches.py`

Status: verified

## Understanding

The module owns two temporary Strawberry workarounds installed process-wide on
`strawberry.http.base.BaseView`: `_patched_parse_json` translates the upstream
`UnicodeDecodeError` gap and rejects scalar/non-object batch envelopes, while
`_patched_parse_query_params` preserves upstream GET `variables` /
`extensions` semantics by routing those two parses through the captured original.
The latter is a source-pinned reimplementation because calling the patched
`parse_json` there would apply a request-body guard to a bodyless GET.

`apply()` is called by
`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` after
the Django app registry is loaded. It gates first through
`django_strawberry_framework/conf.py::upstream_patches_enabled("strawberry")`, validates the captured
symbols, method signatures, and exact `parse_query_params` body, then installs
both methods as a pair. `_patch_is_installed()` compares both live
`BaseView.__dict__` entries by function identity, making repeated `ready()` /
`apply()` calls no-ops and repairing a partial third-party revert. There is no
runtime uninstaller: the gate is an app-load setting, matching the sibling
`_django_patches` and `_cross_web_patches` lifecycles.

The target is inherited by Strawberry's sync and async HTTP views. The sync
path also depends on
`django_strawberry_framework/_cross_web_patches.py::_patched_body` to deliver
raw bytes before this method can translate an undecodable body; package views
instead use `django_strawberry_framework/views.py::_RawBodyRequestAdapter` and
the package-owned strict UTF-8
boundary. The installed dependency set is Strawberry 0.323.2 and cross-web
0.7.0; the captured 0.323.2 `BaseView.parse_json` and
`BaseView.parse_query_params` shapes match the guards exactly.

## Verification

Scoped baseline evidence:

`git --no-pager diff a07198cf1b33293a491d1cb719f8ffe605814e85 -- django_strawberry_framework/_strawberry_patches.py tests/test_strawberry_patches.py tests/test_apps.py`

Result: empty. The target and its permanent tests were unchanged from the
assigned baseline.

Focused permanent tests:

- `uv run pytest --no-cov -n0 tests/test_strawberry_patches.py tests/test_apps.py`
  — 46 passed.
- `uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_products_api.py -k 'non_object_json_body or batch_with_non_object or get_query_with_'`
  — 10 passed. This covers live scalar/non-object body rejection and the GET
  `null` / scalar query-parameter shield.
- `uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_transport_api.py -k 'upstream_bug_workaround or cross_web_half or package_mount_answers_same_way'`
  — 3 passed. This covers the Strawberry-owned mount's `500` → `400`
  workaround, the opt-out, and the package mount's independent policy.

The disposable probe
`docs/review/temp-tests/_strawberry_patches/parse_json_override_probe.py`
showed that the shield intentionally bypasses a custom `parse_json` override
but still preserves the documented `decode_json` seam: `_original_parse_json`
calls `self.decode_json`. Calling a custom `parse_json` from the shield would
re-enter the package view's patched superclass and restore the already-fixed
GET scalar regression.

Source tracing confirmed all installed Strawberry `parse_json` readers:
sync/async POST bodies, sync/async multipart `operations` / `map`, and the two
GET query-parameter parses. The guard is intentionally broad for the body and
multipart sites, and the source-pinned shield is the only GET exception.

## Improvements

### High

None.

### Medium

None.

### Low

None.

### Rejected findings

- **Preserve arbitrary `BaseView.parse_json` overrides in the GET shield.**
  The direct probe demonstrates the dispatch difference, but Strawberry's
  parser customization seam is `decode_json`, which the captured upstream
  method preserves. Invoking `self.parse_json` would route package views back
  through `_patched_parse_json` and reintroduce the proven `variables=null`
  / `extensions=null` regression. No production edit is justified.
- **Add a runtime uninstaller when `APPLY_UPSTREAM_PATCHES` changes.** The
  setting is read at app load, and all three patch modules intentionally have
  install-only lifecycles. Removing a process-wide patch later could restore a
  foreign method/property and create a second race-prone lifecycle; tests
  simulate opt-out by restoring captured upstream identities before the
  request.
- **Replace exact source pinning with signature-only validation.** The shield
  reimplements upstream behavior, so a same-signature body change could add
  new query parameters or alter falsy handling and would otherwise be silently
  overwritten. The current fail-loud source guard is the correct owner.
- **Narrow the envelope guard to one call site.** The guard closes the same
  scalar/non-object `.get()` failure across both transports and multipart
  paths; narrowing it would leave reachable upstream callers with the original
  unhandled exception. GET is the only path proven to require the shield.

## Summary

The target has a single app-load owner for Strawberry's two upstream defects,
validated source/signature boundaries, a dependency-specific kill switch,
sync/async coverage through shared `BaseView` methods, and pairwise
self-healing installation. Live fakeshop requests confirm malformed bodies are
controlled `400` responses, GET query parameters retain upstream semantics,
and the package mount remains protected independently of the upstream
workaround switch. No root-cause production change was proven necessary.

## Implementation (Worker 1)

None — zero-edit cycle.

The scoped diff against `a07198cf1b33293a491d1cb719f8ffe605814e85` is empty for
the target and connected permanent-test paths. Existing tests already pin
application loading, repeated application, partial-revert repair, missing
symbols, method signatures, source drift, global/per-dependency opt-outs,
Unicode and envelope behavior, GET shielding, and sync/async live behavior.
The scratch override probe remains disposable review evidence.

No formatter or linter run was needed because no tracked source or permanent
test changed. No changelog entry is warranted.

## Independent verification (Worker 2)

The scoped target and permanent-test diff against
`a07198cf1b33293a491d1cb719f8ffe605814e85` is empty:
`django_strawberry_framework/_strawberry_patches.py`,
`tests/test_strawberry_patches.py`, and `tests/test_apps.py` are unchanged.
The only scoped working-tree change is this review artifact.

Independent source tracing used the installed Strawberry 0.323.2,
cross-web 0.7.0, and Django 6.1. The captured
`BaseView.parse_query_params` body matches
`_UPSTREAM_PARSE_QUERY_PARAMS_SOURCE` exactly. The installed HTTP source has
three sync `parse_json` callers, four async callers (including multipart
subscriptions), and two GET query-parameter callers; the pair therefore
covers the shared body/multipart seam and shields only the two GET parses.
The sync and async downstream handlers still call `.get(...)` on the parsed
single envelope and batch elements without object checks, so the scalar and
non-object-element guard remains required.

Focused evidence:

- `uv run pytest --no-cov -n0 tests/test_strawberry_patches.py tests/test_apps.py`
  — 46 passed.
- `uv run pytest --no-cov -n0 tests/base/test_conf.py` — 46 passed, including
  the global and per-dependency gate matrix.
- `uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_products_api.py -k 'non_object_json_body or batch_with_non_object or get_query_with_'`
  — 10 live requests passed.
- `uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_transport_api.py -k 'upstream_bug_workaround or cross_web_half or package_mount_answers_same_way'`
  — 3 live upstream/package mount requests passed.
- Async JSON and multipart wire rows covering the opt-out, lossy controls, and
  declared form encodings — 11 passed.

An isolated lifecycle probe passed: app-load installation, repeated
application, global opt-out no-op, partial-pair repair, and final restoration
all held by function identity. There is no runtime uninstaller, consistent with
the app-load-only contract shared by the patch modules.

The custom override probe intentionally subclassed `BaseView` with both
`parse_json` and `decode_json` overrides. The GET shield bypassed the former
but invoked the latter, and `_patched_parse_json` likewise delegated through
`decode_json`. This confirms the rejected override hypothesis rather than
silently assuming it: Strawberry's customization seam used by the captured
parser is `decode_json`; invoking `self.parse_json` in the shield would
re-enter the body-only envelope guard and regress valid GET `null` values.
Signature-only validation, a runtime uninstaller, and narrowing the guard to a
single body caller remain rejected for the same independently reproduced
reasons recorded above.

No source, permanent test, or unrelated dirty file was edited. Item 5 is
complete.
