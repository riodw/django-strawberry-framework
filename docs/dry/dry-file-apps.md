# DRY review: `django_strawberry_framework/apps.py`

Status: verified

## System trace

`DjangoStrawberryFrameworkConfig` owns two things: the package's Django app identity and the one
Phase-3 startup dispatcher for defensive upstream patches. Django 5.2's stable source and the
installed Django 6.0.5 both have `AppConfig.create()` discover the class from the bare
`"django_strawberry_framework"` entry because `apps.py` contains exactly one eligible `AppConfig`
subclass; both versions' `Apps.populate()` import every app and model before invoking `ready()`.
The fakeshop uses that bare entry, and the live registry resolves it to this class. The config is
intentionally not a package-root export.

`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` imports the patch
modules lazily, then calls the Django, Strawberry, and `cross_web` appliers in one explicit
sequence. No other production site dispatches them. Each patch module owns its
dependency-specific original capture, upstream-shape validation, installed-state check,
idempotent repair, failure message, and retirement axis. `conf.py::upstream_patches_enabled` is
already the single owner of the shared default-on `APPLY_UPSTREAM_PATCHES` policy; each public
module-level `apply()` self-gates so direct callers cannot bypass the consumer opt-out.

`tests/test_apps.py` owns discovery and aggregate dispatch coverage. The three patch-module suites
separately prove their applier's install, repair, opt-out, and upstream assumptions, while the live
products HTTP tests prove the complementary Strawberry/`cross_web` patches through real requests.
The example apps' ordinary metadata and `KanbanConfig.ready()` signal import are separate
application-domain lifecycles, not alternative owners of framework patch startup.

## Verification

- `git diff 87cab780975a094cc6d4486aa1ad9a5662169380` was empty for `apps.py`,
  all three patch modules, their four package test files, fakeshop settings, and `pyproject.toml`.
  Thus the reviewed item-scoped state is exactly the requested baseline despite unrelated checkout
  dirt relative to `HEAD`.
- An isolated fakeshop `django.setup()` on Django 6.0.5, Strawberry 0.316.0, and `cross-web` 0.7.0
  resolved the implicit config and found all three patches installed. The captured upstream Django
  body still contains its unguarded `.wrapped` unwrap, and the captured Strawberry and `cross_web`
  callables both still raise `UnicodeDecodeError` on the pinned invalid-body probes.
- An isolated aggregate lifecycle probe reverted all three patches, called `ready()` under
  `APPLY_UPSTREAM_PATCHES=False`, and observed `(False, False, False)`; after the override exited,
  another `ready()` produced `(True, True, True)`. This proves the shared option and repeated-ready
  behavior without inventing an app-level second gate.
- A package-wide search found the three production `apply()` imports only in `apps.py`.
  `strawberry_django/apps.py` has only app metadata, consistent with an upstream package that owns
  none of these local patches.
- Rejected a tuple/registry plus loop for patch appliers: it would replace three explicit calls with
  a second orchestration representation while the appliers have different state, validation,
  failure, and retirement contracts. Their zero-argument spelling is only superficial similarity.
- Rejected moving the setting check into `ready()`: direct applier calls are a tested contract, so
  central gating would either weaken the opt-out or retain both gates and add duplication.
- Rejected moving `conf.py`'s `setting_changed` receiver into `ready()`: settings references can be
  imported before app population and must update in place; that cache lifecycle has a different
  timing contract from Phase-3 patch installation.
- Rejected merging `tests/test_apps.py`'s aggregate dispatch test with per-module installation
  assertions. The former deliberately reverts all patches to prove every dispatcher edge; the
  latter prove each dependency owner's implementation and upstream premise.

The standing `docs/GLOSSARY.md` AppConfig entry and generated `docs/TREE.md` wording still describe
only the older Django-patch subset. That is documentation drift, not duplicated lifecycle
ownership, and it does not justify a code abstraction or an item-scoped source/test edit.

## Opportunities

None — startup orchestration is already single-sited in `apps.py`, shared settings interpretation
is already single-sited in `conf.py`, and the three superficially parallel appliers own
dependency-specific contracts that should not change or retire together.

## Judgment

No consolidation is warranted. Keeping the dispatcher explicit preserves import timing, visible
ordering, independent failure, direct-call safety, and per-dependency retirement without adding a
registry or mode-driven helper.

## Independent verification (Worker 3)

Verified. Django's stable 5.2 source and installed 6.0.5 source independently confirm that bare-app
discovery selects the sole eligible `AppConfig` subclass and that `Apps.populate()` completes all
app and model imports before Phase 3 calls `ready()` in installed-app order. A fresh-process probe
confirmed that package import and `AppConfig.create("django_strawberry_framework")` do not import
the patch modules, the config is not a package-root export, and the three lazy imports occur only
when `ready()` dispatches them.

The original baseline statement above became incomplete as concurrent work settled: `apps.py` and
`tests/test_apps.py` remain identical to `87cab780975a094cc6d4486aa1ad9a5662169380`, while the three
patch modules, `conf.py`, and their focused tests now carry connected prior-item changes. Re-tracing
that current state found no extra dispatcher or bypass. An isolated lifecycle probe observed
`(False, False, False)` under the global opt-out, `(False, True, True)` under
`{"django": False}`, and `(True, True, True)` after global re-enable; this confirms that each direct
applier remains safely self-gated and repeated `ready()` repairs only enabled patches.

The rejected consolidations remain rejected after challenging the current per-dependency setting.
The three dependency-name arguments are references to `conf.py`'s validated settings vocabulary,
not a second lifecycle registry; deriving one from the other would introduce a settings-to-startup
dependency or duplicate orchestration. A generic validate/check/install helper would hide three
different upstream shapes and state protocols for four lines of coincident control flow. Merging
the Strawberry and `cross_web` modules would conflate two dependency and retirement boundaries even
though they jointly harden the sync request path. Central gating in `ready()` would still weaken
safe direct calls, and moving `setting_changed` registration there would make pre-population
settings imports stale. The example apps' metadata and `KanbanConfig.ready()` signal registration
remain unrelated lifecycle owners.

Validation: 103 dispatcher/applier/settings tests passed with `--no-cov`; 10 live malformed-body,
UTF-16, and GET-query-parameter HTTP tests passed with `--no-cov`. The same 103 behavior tests also
passed under the normal coverage invocation; that intentionally focused run exited only because
repository-wide `fail_under = 100` cannot be met by a subset. The reported documentation drift is
confirmed: `docs/GLOSSARY.md` still names only `_django_patches`, and generated `docs/TREE.md` still
describes `apps.py` as applying only Django patches. Route that standing/generated documentation
update to its owning documentation pass; no production or permanent-test revision returns to
Worker 2.

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
