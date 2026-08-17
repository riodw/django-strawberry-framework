# Review: `django_strawberry_framework/apps.py`

Status: verified

## Understanding

`DjangoStrawberryFrameworkConfig` is the package's Django app identity plus the
single startup dispatcher for the three dependency-specific upstream patch
modules. Django's `AppConfig.create("django_strawberry_framework")` discovers
the sole subclass in `apps.py`; the bare fakeshop `INSTALLED_APPS` entry and the
explicit dotted class path both resolve the same `name`, default `label`, and
`verbose_name`. The class is intentionally not re-exported from the package
root.

Django's app loader imports app configs and models before Phase 3 invokes
`ready()` in `INSTALLED_APPS` order. The method imports the patch modules lazily
only at that phase, then calls `apply_django()`, `apply_strawberry()`, and
`apply_cross_web()` explicitly. Each applier owns its own settings gate,
upstream-shape validation, process-global installed-state check, idempotent
repair, and failure message; `apps.py` owns no duplicate state or registry.
The ordering is safe because the appliers capture their upstream originals at
module import and install independent class/property replacements.

The package's settings `setting_changed` receiver remains owned by
`django_strawberry_framework.conf`; `apps.py` registers no signals or checks
and does not finalize consumer `DjangoType` declarations. The hard dependency
chain (`strawberry-graphql` brings `cross-web`) makes the three patch imports
part of normal startup, while the per-dependency opt-out is still enforced by
each direct `apply()` call. Patch state is process-local, so Django test
processes and xdist workers do not share mutations.

## Verification

- `git --no-pager diff 81f0e4fef9467be34e76ffff1eb2c57726f4da0e -- django_strawberry_framework/apps.py` was empty. The target and its permanent test were unchanged at dispatch and remain unchanged.
- `uv run python docs/review/temp-tests/apps/lifecycle_probe.py` in a fresh fakeshop process confirmed that patch modules are absent before setup, the bare app entry resolves `DjangoStrawberryFrameworkConfig`, all three patches are installed after setup, and repeated direct `ready()` calls remain installed.
- The same probe injected a failure in the Strawberry applier. Django reported `apps.loading=True`, `apps.ready=False`, left only the earlier Django patch installed, and rejected a retry with `RuntimeError: populate() isn't reentrant`. A failed `ready()` therefore aborts startup and cannot leave a usable partially initialized registry; adding rollback logic in this dispatcher would duplicate private applier ownership without helping a recoverable Django lifecycle.
- `AppConfig.create()` probes verified both `django_strawberry_framework` and `django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig` resolve the same explicit config, including the default label.
- `env -u DJANGO_SETTINGS_MODULE ... python -c 'import django_strawberry_framework.apps'` succeeded, confirming the module itself remains importable before Django settings/setup. The package root does not expose the AppConfig (`hasattr(...)` and `__all__` both false).
- `uv run pytest tests/test_apps.py --no-cov -n0`: 7 passed.
- `uv run pytest tests/test_apps.py tests/test_django_patches.py tests/test_strawberry_patches.py tests/test_cross_web_patches.py tests/base/test_conf.py --no-cov -n0`: 125 passed.
- `uv run pytest examples/fakeshop/test_query/test_transport_api.py -k cross_web --no-cov -n0`: 2 passed, 72 deselected. This exercises the installed cross-web patch through the real fakeshop HTTP mount.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The dispatcher is correctly scoped to Django's `ready()` lifecycle, keeps
dependency-specific policy in the appliers, preserves the consumer-owned schema
finalization boundary, and has adequate permanent coverage. No production or
test edit is warranted for this item.

## Implementation (Worker 1)

None — zero-edit cycle. The supplied baseline diff for `apps.py` was empty, and
the current implementation passed the lifecycle, focused, and real-example
verification above. No permanent test was added because the existing
`tests/test_apps.py` dispatch test plus the three applier suites already pin
discovery, ordering, opt-out, failure, idempotence, and repair behavior at the
strongest package tier.

The disposable probe remains under
`docs/review/temp-tests/apps/lifecycle_probe.py` as review evidence. No
formatter or linter run was needed because no tracked source or test file was
edited. No changelog entry is warranted for a zero-edit review.

## Independent verification (Worker 2)

The assigned zero-edit claim holds byte-for-byte. `django_strawberry_framework/apps.py` and
`tests/test_apps.py` have the same Git object IDs as baseline
`81f0e4fef9467be34e76ffff1eb2c57726f4da0e`; `git --no-pager diff 81f0e4fef9467be34e76ffff1eb2c57726f4da0e -- django_strawberry_framework/apps.py tests/test_apps.py`
and the corresponding `--name-only` query are empty. No source or permanent test was edited during
this verification; only this artifact changed.

Installed Django 6.1 source confirms `AppConfig.create()`'s bare-entry path imports
`django_strawberry_framework.apps`, selects its sole `AppConfig` subclass, and otherwise falls back
to the implicit base config; the explicit dotted class path takes the same `name`, default label, and
`verbose_name`. `Apps.populate()` is thread-safe/idempotent but not reentrant: it imports app
configs, then models, then invokes `ready()` in `INSTALLED_APPS` order. The fresh discovery probe
resolved both forms to `DjangoStrawberryFrameworkConfig`, and the pre-settings import probe showed
no patch module in `sys.modules`.

The disposable lifecycle probe
`uv run python docs/review/temp-tests/apps/lifecycle_probe.py` passed: before setup the three patch
modules were absent; normal setup installed all three; repeated direct `ready()` calls remained
installed; a synthetic Strawberry failure stopped the later cross-web call; and a fresh failed setup
left `apps.loading=True`, `apps.ready=False`, with retry raising `RuntimeError: populate() isn't
reentrant`. This is the fatal startup behavior Django owns, so `apps.py` correctly does not add
rollback or retry logic around dependency appliers.

Focused evidence re-ran successfully:

- `uv run pytest tests/test_apps.py tests/test_django_patches.py tests/test_strawberry_patches.py tests/test_cross_web_patches.py tests/base/test_conf.py --no-cov -n0` — **125 passed**.
- `uv run pytest examples/fakeshop/test_query/test_transport_api.py -k cross_web --no-cov -n0` — **2 passed, 72 deselected**.

The direct gate matrix in fresh configured Django processes matched the three appliers' ownership:
global `{"APPLY_UPSTREAM_PATCHES": False}` produced `(False, False, False)`, while
`{"APPLY_UPSTREAM_PATCHES": {"django": False}}` produced `(False, True, True)`. A simulated missing
cross-web symbol returned safely under its explicit dependency opt-out and raised the expected
targeted `RuntimeError` when enabled. Existing module tests additionally pin each gate before shape
validation, idempotent re-entry, foreign/partial-revert repair, and dependency-shape failure.

### Rejected findings and scope checks

- A dispatch table or generic patch registry remains unwarranted: `ready()` has three explicit,
  grep-visible calls whose order is part of startup behavior, while each applier has different
  captured state, descriptor shape, validation depth, failure message, and retirement boundary.
- Moving the gate into `ready()` would weaken direct `apply()` callers; the focused gate matrix and
  per-module tests prove the current self-gating contract. Moving `conf.py`'s `setting_changed`
  receiver into `ready()` would break pre-population settings imports and live cache refresh; the
  settings suite covers that separate lifecycle.
- Combining the aggregate dispatch test with module-local tests would lose diagnostic ownership:
  `tests/test_apps.py` deliberately restores all three upstream originals to prove every dispatcher
  edge, while each patch suite owns its private dependency behavior.
- The generated `docs/GLOSSARY.md` AppConfig entry still describes only the older Django patch,
  although the current dispatcher installs Django, Strawberry, and cross-web patches. This is
  confirmed documentation drift in a generated standing surface; the prior DRY review routes it to
  the owning docs/project pass, and it does not justify changing this zero-edit target or its
  permanent tests.

No correctness, discovery, lazy-import, setup-ordering, gate, idempotence, optional-dependency,
fatal-startup, reentrancy, caller, or test-tier finding remains for item 6.

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
