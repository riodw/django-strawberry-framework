# Review: `django_strawberry_framework/conf.py`

Status: verified

## DRY analysis

- Existing patterns reused: `DJANGO_SETTINGS_KEY` centralizes the consumer setting name for lazy reads and signal reload filtering at `django_strawberry_framework/conf.py:37-38`; `reload_settings` mutates the module-level singleton instead of rebinding it at `django_strawberry_framework/conf.py:91-101`; package tests already pin lazy `None` coercion, singleton mutation, and dispatch UID idempotence at `tests/base/test_conf.py:42-47`, `tests/base/test_conf.py:54-83`, and `tests/base/test_conf.py:111-120`.
- New helpers a fix might justify: a single user-settings normalizer for "read/replace the top-level settings mapping" would serve both the lazy-load path at `django_strawberry_framework/conf.py:61-63` and the signal/direct reload path at `django_strawberry_framework/conf.py:65-71`; it should preserve the current `None` -> `{}` contract while rejecting non-mapping values clearly.
- Duplication risk in the current file: the normalization contract is split between lazy loading and reload assignment at `django_strawberry_framework/conf.py:61-71`; because only the lazy path applies `or {}`, the two call sites can drift and already differ for truthy non-dict values. No repeated runtime string/key literals need consolidation beyond the existing `DJANGO_SETTINGS_KEY` constant.

## High:

None.

## Medium:

### Non-dict settings values bypass validation

`DJANGO_STRAWBERRY_FRAMEWORK` is documented as a top-level Django settings dict, but both entry points accept any truthy object. If a consumer configures a string, list, or other non-mapping value, `Settings.__getattr__` indexes that object with the requested setting name and can raise a raw `TypeError` instead of the package's expected configuration/access error shape. The same bug exists through `reload_settings` because the signal value is assigned directly. Recommended change: centralize normalization for lazy load and reload, keep `None` as "no settings configured", and raise a clear configuration exception for non-mapping values. Add coverage in `tests/base/test_conf.py` because this is the allowed package test file for `conf.py`.

```django_strawberry_framework/conf.py:61:85
        if self._user_settings is None:
            self._user_settings = getattr(django_settings, DJANGO_SETTINGS_KEY, {}) or {}
        return self._user_settings

    def reload(self, value: dict[str, Any] | None) -> None:
        """Replace the cached user-settings mapping in place.

        ``None`` restores lazy reload on next attribute access; any other
        value is used as-is.
        """
        self._user_settings = value

    def __getattr__(self, name: str) -> Any:
        """Retrieve a setting's value using attribute-style access.

        Dunder names short-circuit with a plain ``AttributeError`` so
        introspection tools (``copy``, ``deepcopy``, ``inspect``) get
        readable traces instead of the "Invalid setting" message.
        """
        if name.startswith("__"):
            raise AttributeError(name)
        try:
            return self.user_settings[name]
        except KeyError:
            raise AttributeError(f"Invalid setting: `{name}`") from None
```

## Low:

None.

## What looks solid

- Static helper skipped: `django_strawberry_framework/conf.py` is 109 lines, is not under `optimizer/` or `types/`, and this is not a folder pass, so it does not meet the mandatory helper triggers.
- The module keeps the settings surface narrow: it does not pre-populate future-feature keys and missing keys remain attribute-style lookups.
- `setting_changed.connect(..., dispatch_uid=...)` keeps pytest/Django settings overrides visible to existing imported references without duplicate receivers.

### Summary

`conf.py` is small and generally aligned with the documented settings boundary, but the settings mapping normalization is not shared between lazy reads and reloads. That leaves an edge-case crash path for invalid non-dict configuration values and is the only confirmed finding for this file.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/conf.py` — added `_normalize_user_settings` and routed lazy loading plus
  `reload()` through it so materialized `DJANGO_STRAWBERRY_FRAMEWORK` values accept mappings/`None` and
  reject non-mapping values with `ConfigurationError`.
- `tests/base/test_conf.py` — added focused coverage for non-dict mappings, invalid lazy settings values,
  and invalid reload values preserving the previous cached mapping.

### Tests added or updated

- `tests/base/test_conf.py::test_settings_user_settings_accepts_mapping_values` — pins the accepted
  mapping path in the shared normalizer.
- `tests/base/test_conf.py::test_settings_user_settings_rejects_non_mapping_django_setting` — pins the
  lazy-load invalid top-level setting path.
- `tests/base/test_conf.py::test_settings_reload_rejects_non_mapping_value` — pins the reload invalid
  setting path and verifies a failed reload leaves the cached mapping intact.

### Validation run

- `uv run ruff format .` — pass.
- `uv run ruff check --fix .` — pass.
- `uv run pytest tests/base/test_conf.py` — test assertions passed, command failed only because repo-wide
  coverage gating applies to the single-file run.
- `uv run pytest tests/base/test_conf.py --no-cov` — pass, 15 passed.

### Notes for Worker 3

- No shadow helper used; the artifact explicitly said the static helper was not mandatory for this file.
- No findings were intentionally rejected.
- Comments/docstrings were not intentionally revised in this logic pass; if Worker 3 accepts the logic,
  the remaining comment pass should update any stale wording around reload normalization.

---

## Verification (Worker 3)

### Logic verification outcome

- High: none to verify.
- Medium: `Non-dict settings values bypass validation` is addressed. Worker 2 added a shared
  `_normalize_user_settings()` helper, routed constructor eager settings, lazy Django settings reads, and
  `reload()` through it, and rejects non-mapping values with `ConfigurationError`.
- Low: none to verify.
- Scope check: source/test edits stayed within `django_strawberry_framework/conf.py` and
  `tests/base/test_conf.py`, matching the artifact.
- Validation check: Worker 2's reported focused no-coverage test pass is reproducible:
  `uv run pytest tests/base/test_conf.py --no-cov` passed with 15 tests. The reported single-file
  coverage-gate failure is acceptable because full package coverage is enforced only on full-suite runs.

### DRY findings disposition

- Accepted. The duplicated lazy-load/reload normalization path is consolidated into
  `_normalize_user_settings()`, and the existing `DJANGO_SETTINGS_KEY` constant remains the single runtime
  setting-name literal. No additional DRY issue is introduced by the fix.

### Temp test verification

- No temp tests used.

### Verification outcome

- logic accepted; awaiting comment pass.

Comment/docstring lifecycle is not complete. The logic pass leaves stale wording that should be handled in
Worker 2's comment pass, including the `Settings.__init__()` docstring saying a dict is used "as-is",
`Settings.user_settings` describing all falsy values as collapsing via the old fallback behavior, and
`Settings.reload()` saying any non-`None` value is used as-is. Changelog disposition has not been reached.

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/conf.py` — updated `Settings.__init__()`, `Settings.user_settings`, and
  `Settings.reload()` docstrings so they describe the final normalization behavior: `None` defers or
  becomes an empty mapping, mappings are accepted, non-`dict` mappings are copied, and non-mappings raise
  `ConfigurationError`.
- `tests/base/test_conf.py` — updated stale test section/docstring wording that still referred to the
  old broad falsy/`or {}` fallback.

### Validation run

- `uv run ruff format .` — pass, 92 files left unchanged.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3

- Comment/docstring-only pass. No accepted logic was changed.
- Changelog disposition has not been reached; no `CHANGELOG.md` edit was made.

---

## Verification (Worker 3, pass 2)

### Comment/docstring verification outcome

- Accepted. `Settings.__init__()` now describes the mapping normalization contract instead of the old
  dict-only/as-is behavior.
- Accepted. `Settings.user_settings` now describes missing/`None` configuration as the empty-mapping
  contract and non-mapping configuration as a `ConfigurationError`, not the old broad falsy fallback.
- Accepted. `Settings.reload()` now describes mapping replacement, dict retention, copied non-dict
  mappings, and `None` restoring lazy reload instead of saying every non-`None` value is used as-is.
- Accepted. The touched `tests/base/test_conf.py` comment/docstring wording now describes normalization
  and `None` behaving like no configured settings.

### Changelog disposition

- Missing. Worker 2 recorded that changelog disposition has not been reached and no `CHANGELOG.md` edit
  was made, but the review workflow requires an explicit changelog disposition before the cycle can be
  verified.

### Verification outcome

- comments accepted; awaiting changelog disposition.

---

## Changelog disposition

- Changelog edit: not warranted for this review-cycle fix.
- Reason: the accepted change hardens invalid `DJANGO_STRAWBERRY_FRAMEWORK` top-level settings handling by
  normalizing mappings and raising `ConfigurationError` for non-mapping values. That is an internal
  edge-case correctness fix around an invalid configuration shape, not a new public feature, public API
  addition, or documented behavior change that needs a release-note entry.
- Action taken: no `CHANGELOG.md` edit was made because `AGENTS.md` prohibits changelog updates unless
  explicitly instructed, and this review plan/pass only required recording the disposition.

---

## Verification (Worker 3, pass 3)

### Logic verification outcome

- Accepted. The prior logic acceptance still holds: lazy reads, eager constructor mappings, and reloads all
  use the shared normalizer; non-mapping values fail with `ConfigurationError`; and the failed reload path
  preserves the previous cached mapping.

### DRY findings disposition

- Accepted. The duplicated normalization behavior called out in the artifact remains consolidated in
  `_normalize_user_settings()`, with no new parallel settings path introduced by the comment or changelog
  passes.

### Comment/docstring verification outcome

- Accepted. `django_strawberry_framework/conf.py` and `tests/base/test_conf.py` describe the final mapping
  normalization behavior and no longer describe broad falsy fallback or non-`None` reload values as used
  as-is.

### Validation verification

- Accepted. Re-ran `uv run pytest tests/base/test_conf.py --no-cov`; 15 tests passed.

### Changelog disposition

- Accepted. No `CHANGELOG.md` edit was made, and the artifact records the reason: this is invalid-config
  hardening, not a public feature or explicitly authorized changelog item.

### Temp test verification

- No temp tests used.

### Verification outcome

- cycle accepted; verified.
