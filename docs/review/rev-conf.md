# Review: `django_strawberry_framework/conf.py`

Status: verified

## Understanding

`conf.py` owns the package-namespaced Django setting reader. `Settings(None)` is the module singleton's lazy, Django-backed cache; it live-resynchronizes when the top-level mapping is replaced or deleted without a `setting_changed` signal, while explicit `Settings(mapping)` instances keep a fixed normalized mapping. The signal receiver mutates the singleton in place so references imported with `from django_strawberry_framework.conf import settings` remain current.

The named readers provide defaults or deliberately defer domain validation to their invariant owners: upstream patch gates validate the strict bool/mapping shape; optimizer strategy resolution validates `NESTED_CONNECTION_STRATEGY`; the view validates `MAX_REQUEST_BODY_BYTES`; Relay finalization validates `RELAY_GLOBALID_STRATEGY`; filter input construction owns `HIDE_FLAT_FILTERS` truthiness; and schema construction validates `RESOURCE_POLICY` and `ERROR_POLICY`. Callers consume these at their documented lifecycle points: app-load patch installation, extension construction, fetch time, input/type finalization, view construction/request handling, test-client construction/query, and schema construction.

The pre-change baseline had no target diff relative to `be4a0a6fd8201bbafab403e5882f425b26d2ff27`; this review therefore evaluated the current contract and callers rather than only changed lines.

## Verification

- `uv run pytest tests/base/test_conf.py --no-cov` passed 46 tests before the fix and 47 after it.
- `uv run pytest tests/test_resource_policy.py tests/test_error_policy.py tests/testing/test_client.py --no-cov` passed 150 tests after the fix.
- A real fakeshop-settings experiment reproduced the defect: `s = Settings(); s.reload({"A": 1}); s.user_settings` returned the live Django mapping `{}` because `reload(mapping)` left `_django_backed` enabled.
- Existing signal and silent-change tests confirmed that the module singleton must remain Django-backed after `setting_changed`, including `del settings.DJANGO_STRAWBERRY_FRAMEWORK`.
- No focused experiment found a defect in the downstream validation split; each invalid domain is rejected by the caller that owns its vocabulary or precedence.

## Improvements

### High

None.

### Medium

- **Observation:** `Settings.reload(mapping)` documented replacement of the cached mapping, but on a Django-backed instance it stored the mapping while leaving `_django_backed=True`. The next `user_settings` read compared against the live Django setting, discarded the direct replacement, and returned the unrelated live mapping.
- **Evidence:** Before the fix, `Settings().reload({"A": 1})` followed by `user_settings` returned `{}` under the real fakeshop settings. The existing `Settings(mapping)` test passed only because that constructor starts non-backed; the signal receiver was the only path that relied on backed reload semantics.
- **Impact:** Direct reload callers could believe a new configuration was installed while every setting reader continued using stale or unrelated Django configuration. The failure was silent and depended on whether the instance had started Django-backed.
- **Recommendation:** Keep explicit `reload(mapping)` as a deterministic, non-Django-backed cache replacement. Give the `setting_changed` receiver a separate `_reload_from_django` path that normalizes the signal value, records its live source, and preserves singleton live synchronization. `reload(None)` continues to restore Django-backed lazy loading.
- **Proof:** `test_settings_reload_replaces_django_backed_mapping` pins direct replacement on `Settings()`, while the existing signal, override, deletion, malformed-live-value, and imported-reference tests continue to pass.

### Low

None.

## Summary

The setting lookup/default split and lifecycle consumers are coherent after one medium-severity cache-state fix. Explicit reloads now honor their replacement contract without weakening signal-driven live synchronization; no other accepted findings remain.

## Implementation (Worker 1)

- Changed `django_strawberry_framework/conf.py`: explicit non-`None` `Settings.reload` calls now switch to a fixed cache; `_reload_from_django` preserves the live-backed state for Django signal updates; `reload_settings` dispatches through that signal-only helper.
- Changed `tests/base/test_conf.py`: added a regression test proving a direct reload on a lazily constructed instance survives the subsequent `user_settings` read.
- Validation: `uv run pytest tests/base/test_conf.py --no-cov` (47 passed); connected policy/client tests (150 passed); `uv run ruff format .`; `uv run ruff check --fix .` (all checks passed).
- Rejected findings: no extra validation was added to the thin named readers because their connected callers already own the domain vocabulary and construction/fetch lifecycle, as verified by the focused policy, optimizer, view, Relay, and test-client tests.
- Changelog: no entry added; the correction is an internal `Settings.reload` cache contract and does not alter the externally documented setting keys or defaults.

## Independent verification (Worker 2)

- Re-read the complete `django_strawberry_framework/conf.py` and `tests/base/test_conf.py`, then traced every reader into its connected owner: patch gates (`_django_patches.py`, `_strawberry_patches.py`, `_cross_web_patches.py`), optimizer strategy construction and fetch-time fast-path gating, filter input construction, Relay finalization, request-body view resolution, test-client endpoint resolution, and schema-time resource/error policy resolution.
- Confirmed state semantics across explicit mappings, Django-backed lazy reads, `reload(None)`, signal-triggered `_reload_from_django`, missing/`None` values, silent deletion, malformed live values, mapping normalization, imported singleton references, and dispatch-UID registration. Explicit reloads remain fixed; signal updates restore/retain live backing.
- Scoped baseline inspection with `git --no-pager diff be4a0a6fd8201bbafab403e5882f425b26d2ff27 -- django_strawberry_framework/conf.py tests/base/test_conf.py docs/review/rev-conf.md` showed only the intended implementation, regression test, and artifact changes.
- `uv run pytest tests/base/test_conf.py --no-cov` — 47 passed.
- `uv run pytest tests/test_resource_policy.py tests/test_error_policy.py tests/testing/test_client.py --no-cov` — 150 passed.
- A configured Django probe emulating the baseline reload body left `_django_backed=True` and returned the live `{}` instead of `{"A": 1}`; invoking `test_settings_reload_replaces_django_backed_mapping` under that emulation failed, proving the permanent regression test detects the original bug. The current implementation passes the same test.
- No additional findings remain; rejected validation-split findings continue to be covered by the downstream owner tests and no unrelated paths were absorbed.
