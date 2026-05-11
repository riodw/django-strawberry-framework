# Review: `django_strawberry_framework/conf.py`

## High:

None.

## Medium:

### `setting_changed` receiver is never disconnected and uses a strong reference

`setting_changed.connect(reload_settings)` runs at module import time with no `dispatch_uid` and no `weak=False`/teardown path. Django's signal framework holds a weak reference to module-level functions by default, but the `Settings` singleton bound in the closure is the module global `settings`, so the receiver remains live for the process lifetime — which is the intent. The risk is duplicate connection if `conf` is ever re-imported under a different module name (e.g. via test harness reloads or namespace gymnastics): each import would attach an additional receiver and each `override_settings` exit would mutate `settings._user_settings` N times. Adding `dispatch_uid="django_strawberry_framework.conf.reload_settings"` makes the connect idempotent against re-import without changing behavior under normal use. Worth a Medium because the bug only appears in pathological reload scenarios but the fix is one keyword arg.

```django_strawberry_framework/conf.py:69:73
# Import-time side effect: install the signal receiver so test overrides take
# effect without requiring an AppConfig.ready() hook.  Consumers may import
# ``conf`` before app loading during test bootstrap, so AppConfig.ready() is
# not a viable home for this wiring.
setting_changed.connect(reload_settings)
```

## Low:

### `or {}` swallows a misconfigured falsy `DJANGO_STRAWBERRY_FRAMEWORK`

`getattr(django_settings, DJANGO_SETTINGS_KEY, {}) or {}` treats any falsy value (most plausibly an empty dict, but also `None`, `0`, `""`) as "no settings". For an empty dict this is a no-op; for `None` it silently masks a likely consumer typo (e.g. `DJANGO_STRAWBERRY_FRAMEWORK = None`). Consider tightening to `getattr(..., {})` and letting downstream `KeyError`/`AttributeError` surface, or raising `ConfigurationError` when the key is present but not a mapping. Pre-alpha latitude makes this Low, not Medium.

```django_strawberry_framework/conf.py:41:43
if self._user_settings is None:
    self._user_settings = getattr(django_settings, DJANGO_SETTINGS_KEY, {}) or {}
return self._user_settings
```

### `__getattr__` accepts dunder lookups

`__getattr__` is only consulted for attributes Python could not otherwise resolve, but it will be called for arbitrary dunder names (`__wrapped__`, `__iter__`, etc.) by introspection tools and frameworks like `copy`/`deepcopy`. Each such probe raises `AttributeError("Invalid setting: '__wrapped__'")`, which is correct behavior but the error message is slightly misleading for dunders. Optional polish: short-circuit `name.startswith("__")` to raise a plain `AttributeError(name)` so introspection traces stay readable.

```django_strawberry_framework/conf.py:45:50
def __getattr__(self, name: str) -> Any:
    """Retrieve a setting's value using attribute-style access."""
    try:
        return self.user_settings[name]
    except KeyError:
        raise AttributeError(f"Invalid setting: `{name}`") from None
```

### Private-attribute write from module-level function

`reload_settings` mutates `settings._user_settings` directly. This is fine — it's the same module — but a small `Settings.reload(value)` method would keep the underscore attribute genuinely private and make the intent ("clear cached settings, optionally seeded with the new dict") readable at the call site.

```django_strawberry_framework/conf.py:56:66
def reload_settings(setting: str, value: Any, **kwargs: Any) -> None:
    ...
    if setting == DJANGO_SETTINGS_KEY:
        settings._user_settings = value
```

## What looks solid

- Lazy load via `user_settings` property defers Django settings access until first attribute read — safe under early imports during test bootstrap, as the docstring promises.
- Mutating the singleton in place (rather than rebinding the module global) correctly preserves `from .conf import settings` references across `override_settings` blocks; behavior matches the docstring at lines 10–15.
- `AttributeError` (not `KeyError`) from `__getattr__` matches Python's attribute-protocol contract and lets `getattr(settings, name, default)` work as expected.
- Module surface is minimal and matches the AGENTS.md "Settings surface today" rule: no preemptive future-feature keys.
- Static helper skipped: file is 73 lines, well under the 150-line threshold, not under `optimizer/` or `types/`, and has no ORM surface — per `REVIEW.md` "When to run the helper", running it is not required for this file.

---

### Summary:

`conf.py` is a tight, correct Settings shim. The only behavioral nit worth a Medium is the missing `dispatch_uid` on the import-time `setting_changed.connect`, which would harden the module against duplicate signal registration under reload scenarios. Lows are polish: tightening the `or {}` fallback, suppressing dunder lookups in `__getattr__`, and moving the private-attribute write into a small method on `Settings`. No High-severity issues; no test gaps relative to the current behavior (frozen `tests/base/test_conf.py` is the canonical coverage site if any of these are picked up).

## Verification

PASS.

- Medium (`dispatch_uid`): addressed — `_DISPATCH_UID` constant added and passed to `setting_changed.connect`; idempotency pinned by `test_setting_changed_receiver_uses_dispatch_uid`.
- Low (`or {}` swallows falsy): intentionally retained; the new `user_settings` docstring documents the collapse-to-empty-dict semantics so consumer falsy values uniformly raise `AttributeError` downstream. Acceptable rejection-with-reason given pre-alpha latitude.
- Low (dunder lookups in `__getattr__`): addressed with `name.startswith("__")` short-circuit; pinned by `test_settings_dunder_lookup_raises_plain_attributeerror`.
- Low (private-attribute write): addressed — new `Settings.reload(value)` method; `reload_settings` now calls it; pinned by `test_settings_reload_replaces_cached_mapping` and `test_settings_reload_with_none_restores_lazy_load`.
- Tests: `uv run pytest tests/base/test_conf.py -q` -> 12 passed. (Repository-wide `fail_under=100` correctly trips on a focused run because most modules are excluded from this slice; conf.py itself is at 100%.)
- Scope: changes are confined to `conf.py` and `tests/base/test_conf.py` aside from a stray cosmetic blank line in `examples/fakeshop/test_query/test_library_api.py` and a `REVIEW.md` reading-anchor; neither touches reviewed logic.
