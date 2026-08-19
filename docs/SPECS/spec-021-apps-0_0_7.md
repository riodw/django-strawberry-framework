# Spec: `apps.py` and Django `AppConfig`

Target release: `0.0.7`.
Status: shipped (`0.0.7`, 2026-05-27); archived. Card `DONE-021-0.0.7`.
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [`Django AppConfig`][glossary-django-appconfig], [`finalize_django_types`][glossary-finalize-django-types], [`DjangoType`][glossary-djangotype]), [`KANBAN.md`][kanban] card `DONE-021-0.0.7`, predecessor spec [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] (Decision 10 — joint `0.0.7` cut policy reused verbatim here).

Deliberation — the six revisions of review feedback, the alternatives each Decision rejected, the risks-and-open-questions record, and every claim this spec once made and may no longer make — lives in [`spec-021-apps-0_0_7-rationale.md`][spec-021-rationale]. This file states only the contract that holds at `HEAD`.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`Django AppConfig`][glossary-django-appconfig] — the entry this card flips from `planned for 0.0.7` to `shipped (0.0.7)` in [Slice 3](#slice-checklist).
- [`finalize_django_types`][glossary-finalize-django-types] — the consumer-owned synchronization point that resolves pending relations; this card does NOT move that responsibility into `AppConfig.ready()` (see [Decision 4](#decision-4--ready-applies-the-upstream-patches)).
- [`DjangoType`][glossary-djangotype] — the package's primary public surface; consumer modules that declare `DjangoType`s are imported by the consumer's project, not by the `AppConfig` (see [Decision 4](#decision-4--ready-applies-the-upstream-patches)).
- [`ConfigurationError`][glossary-configurationerror] — not raised by anything in `apps.py`; mentioned here only so future-spec authors can see that the module is intentionally validation-free.

Project conventions to follow:

- [`AGENTS.md`][agents] — #"Add a settings key only when the feature that needs it lands" ("Add a settings key only when the feature that needs it lands; never preemptively"); test placement at `tests/test_apps.py` per #"Test placement: three test trees with no overlap"'s "tests/ (package tests, system-under-test is django_strawberry_framework itself)" rule paired with the flat `tests/test_<module>.py` mirror layout in [`docs/TREE.md #"## Test layout"`][tree]. **Note:** `AGENTS.md` #"No CHANGELOG.md updates unless told" prohibits `CHANGELOG.md` edits without explicit permission; [Slice 3](#slice-checklist) grants that permission for this card's `[0.0.7]` `### Added` append.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target.
- [`KANBAN.md`][kanban] — card-ID format; column movement at Slice 3.
- [`docs/TREE.md`][tree] — package layout; tests mirror source one-to-one. `apps.py` sits in both the current and target `django_strawberry_framework/` listings (`docs/TREE.md #"## django_strawberry_framework (current on-disk layout)"`).

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan). Three slices total; this card is smaller than [`spec-020`][spec-020] because there is no consumer-resolver dispatch matrix to test and no example-app boilerplate to remove.

- [ ] Slice 1: Module + `AppConfig` subclass
  - [ ] New flat module `django_strawberry_framework/apps.py` (placement decision: see [Decision 1](#decision-1--module-location--public-export)) housing `DjangoStrawberryFrameworkConfig`.
  - [ ] Implement `DjangoStrawberryFrameworkConfig(AppConfig)` with exactly **two class-level behavioral attributes** plus **two docstrings** (the docstrings are documentation, not class state, and are exempt from the negative-shape iteration accordingly):
    - `name = "django_strawberry_framework"` — Django app-label source; matches the package directory name so `django.apps.apps.get_app_config(...)` resolves through the same string consumers type into `INSTALLED_APPS`.
    - `verbose_name = "Django Strawberry Framework"` — display name in the Django admin's "Sites" / "Apps" listings; matches the `README.md` title.
    - module docstring (one line) naming the module's purpose — the shipped line is `"""Django ``AppConfig`` - registers the package and applies its upstream patches at app load."""` at the top of `apps.py`. **Required by ruff's `D100` rule** (`D100` "Missing docstring in public module" is in `pyproject.toml`'s `[tool.ruff.lint] select = [..., "D", ...]` and NOT in the `ignore` list; the per-file-ignores at `pyproject.toml #"[tool.ruff.lint.per-file-ignores]"` do not exempt `django_strawberry_framework/apps.py`). Do NOT suppress with `# noqa: D100` — the docstring IS the root-cause fix per [`AGENTS.md`][agents] #"Always give the root-cause fix even when slower".
    - class docstring (one line) naming the class's purpose — `"""Register django-strawberry-framework with Django's app loader."""` directly under the `class DjangoStrawberryFrameworkConfig(AppConfig):` line. **Required by ruff's `D101` rule** (symmetric with `D100`; `D101` "Missing docstring in public class" is also in `select` and not ignored). Do NOT suppress with `# noqa: D101` — same root-cause posture as `D100`.
  - [ ] Override `ready()` to dispatch the package's three upstream-patch appliers, and nothing else (per [Decision 4](#decision-4--ready-applies-the-upstream-patches)). The imports are function-local; the method body is three `apply()` calls in this order (`django`, `strawberry`, `cross_web`), each self-gated on `APPLY_UPSTREAM_PATCHES`.
  - [ ] Do NOT set `default_auto_field` (per [Decision 5](#decision-5--no-default_auto_field-and-no-models)); do NOT set `label` (per [Decision 2](#decision-2--name--label--verbose_name-pinning)); do NOT set `default` at any value — neither `default = True` nor `default = False` — per [Decision 8](#decision-8--no-default-attribute). The consolidated negative-shape test in Slice 2 catches `default` at any value, but this checklist sub-bullet — which Worker 0 copies verbatim into the build artifact per [`docs/builder/ARTIFACT.md`][artifact] #"The spec's nested sub-bullets for this slice from `## Slice checklist`, copied verbatim" — must name each forbiddance directly so Worker 2 sees it when reading top-down.
  - [ ] Do NOT re-export `DjangoStrawberryFrameworkConfig` from `django_strawberry_framework/__init__.py` (per [Decision 3](#decision-3--no-public-export)). The class is accessible at `django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig` for consumers who want to name it explicitly in `INSTALLED_APPS`, but Django's implicit single-AppConfig discovery means consumers writing `"django_strawberry_framework"` in `INSTALLED_APPS` get the explicit config without naming it.
- [ ] Slice 2: Tests
  - [ ] New test module `tests/test_apps.py` covering the four positive contracts pinned in [Test plan](#test-plan): importable from `django_strawberry_framework.apps`, subclass of `django.apps.AppConfig`, `name` / `verbose_name` attribute values, and Django registry pickup (`django.apps.apps.get_app_config("django_strawberry_framework")` returns an instance of `DjangoStrawberryFrameworkConfig`).
  - [ ] One **consolidated** negative-shape test: assert that `DjangoStrawberryFrameworkConfig.__dict__` contains none of the three **behavioral** keys this spec forbids — `"label"` (per [Decision 2](#decision-2--name--label--verbose_name-pinning)), `"default_auto_field"` (per [Decision 5](#decision-5--no-default_auto_field-and-no-models)), and `"default"` (per [Decision 8](#decision-8--no-default-attribute)). Mechanism: a single test function (one pytest item, NOT a `pytest.mark.parametrize` fan-out) that iterates a mapping of forbidden key to the Decision that forbids it and asserts `key not in DjangoStrawberryFrameworkConfig.__dict__` for each, with a fail message naming the offending key and that Decision. Checks the class body explicitly, not the inherited base attributes which are always present. **`"ready"` is NOT in the forbidden set** — `ready` is required, and its own tests are below. **The implicit `__doc__` key is NOT in the forbidden set either** — "no extra AppConfig attributes" means no extra **behavioral** class attributes, not "no class docstring"; `__doc__` is documentation, not behavior, and is mandated by ruff's `D101`. If a future card relaxes any of the three forbidden keys, that card's spec updates this test in the same slice.
  - [ ] Three `ready()` tests (per [Decision 4](#decision-4--ready-applies-the-upstream-patches)): that `ready` is present and callable in the class body; that driving `ready()` through the registered `AppConfig` installs all three patch sets and that a second `ready()` is safe; and that a `ready()` fired after a patch module reload retains the true upstream capture and reinstalls the reloaded replacement. Each restores every process-global slot it perturbs.
- [ ] Slice 3: Promotion + docs
  - [ ] Flip [`Django AppConfig`][glossary-django-appconfig] from `planned for 0.0.7` to `shipped (0.0.7)` in [`docs/GLOSSARY.md`][glossary]; update the Index table's status column.
  - [ ] Update [`docs/README.md`][readme]: add the `Django AppConfig` bullet to the shipped-features list with the wording in [Doc updates](#doc-updates), and remove the `Django AppConfig` mention from the forward-looking "coming" list, leaving every other entry in that list to the card that owns it.
  - [ ] Update [`docs/TREE.md`][tree] — `apps.py` appears in the `django_strawberry_framework/` **current on-disk layout** section (alphabetical position between `__init__.py` and `conf.py`) and in the **target package layout** section with no `[alpha]` tag, since the module has landed. `tests/test_apps.py` appears in the current test-tree section, **before** `test_list_field.py` (alphabetical).
  - [ ] Update [`KANBAN.md`][kanban] — move `DONE-021-0.0.7` to the Done column with the next `DONE-NNN-0.0.7` id; rewrite the body in past tense per the existing Done-column convention.
  - [ ] Update [`CHANGELOG.md`][changelog] — **append** to the existing `[0.0.7]` `### Added` subsection (do NOT create a second `[0.0.7]` heading per [`spec-020`][spec-020] Decision 10 — every `0.0.7` card under the joint cut appends to the same shared section) with the entry text in [Doc updates](#doc-updates).
  - [ ] No edits to [`README.md`][readme-root], [`GOAL.md`][goal], or [`TODAY.md`][today]. Justification: the AppConfig is plumbing, not a consumer-visible API surface. `README.md`'s status section names features consumers write code against; `GOAL.md`'s six-file example does not exercise `INSTALLED_APPS`; `TODAY.md`'s capability snapshot is about what GraphQL queries work — none of those framings is touched by the AppConfig landing.
  - [ ] Version bump (deferred to **the last `0.0.7` card to ship**, NOT this card; per [Decision 6](#decision-6--joint-007-cut)): see [`spec-020`][spec-020] Decision 10. This card does NOT bump `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, or `tests/base/test_init.py`'s version assertion.
  - [ ] Final gates:
    - [ ] `uv run ruff format .` passes (the per-pass gate, per [`AGENTS.md`][agents] #"`uv run ruff format .` and `uv run ruff check --fix .` after every edit").
    - [ ] `uv run ruff check --fix .` passes (the per-pass gate, per [`AGENTS.md`][agents] #"`uv run ruff format .` and `uv run ruff check --fix .` after every edit").
    - [ ] `uv run pytest --no-cov` (or scoped subset) passes; the explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov` and is the only permitted coverage-shaped flag per [`docs/builder/BUILD.md`][build] #"Coverage is the maintainer's gate, not a worker's tool". Coverage enforcement is CI's job (`pyproject.toml [tool.coverage.report] fail_under = 100`), not this slice's; workers verify the suite passes, not that coverage stays at 100%.
    - [ ] Zero new public exports (the AppConfig is import-time plumbing, not a public symbol); `__all__` in `django_strawberry_framework/__init__.py` is unchanged.

## Problem statement

`django_strawberry_framework` does not ship an [`apps.py`][pkg-dir] before this card. The example project's `examples/fakeshop/config/settings.py #"\"django_strawberry_framework\","` already lists `"django_strawberry_framework"` in `INSTALLED_APPS`, and the example runs — but only because Django falls back to an implicit `AppConfig` synthesized from the package name when no explicit `apps.py` is found. That implicit `AppConfig`:

- carries the package's directory name as the `name` and `label`, with the same string as `verbose_name` — capitalized via Django's title-cased default ("Django Strawberry Framework"-ish but driven by Django's heuristic, not by the package),
- cannot be referenced by an explicit dotted path in `INSTALLED_APPS` (consumers who want the canonical Django pattern `"django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig"` cannot type it),
- gives the package no hook for Django-integration work that must run once the app registry is populated.

The asymmetry is small but real: `strawberry_django` ships an [`apps.py`][apps] (verified to be a four-line `class StrawberryDjangoConfig(AppConfig)` with `name` and `verbose_name`); the upstream `graphene_django` does NOT ship one (verified via `find` against `~/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/` — no `apps.py`). The package's positioning argument in [`README.md`][readme-root] — "feels like `graphene-django` evolved onto a modern engine" — would currently match graphene-django's absence; the package's other half — "Strawberry stays as the engine" — would currently miss the parity with `strawberry-django`. This card ships the AppConfig so the parity is symmetric.

The shipping bar is intentionally low — the AppConfig is two behavioral attributes (`name`, `verbose_name`) plus a module docstring (required by `D100`) plus a class docstring (required by `D101`), and one `ready()` override whose entire body is the upstream-patch dispatch of [Decision 4](#decision-4--ready-applies-the-upstream-patches). The discipline the card enforces is **what NOT to put in it**: no preemptive settings, no eager imports of `DjangoType` modules, no auto-call to [`finalize_django_types`][glossary-finalize-django-types], no Django system checks. Each of those is a future-spec home (or, for `finalize_django_types`, an explicit anti-pattern — the consumer owns the synchronization point per [`docs/README.md`][readme]'s "Schema setup boundary" section).

## Current state

- `django_strawberry_framework/` ships the modules listed in [`docs/TREE.md`][tree] under the `## django_strawberry_framework (current on-disk layout)` section (`__init__.py`, `conf.py`, `exceptions.py`, `list_field.py`, `registry.py`, `scalars.py`, the `optimizer/`, `types/`, and `utils/` subpackages) and `py.typed`. There is no `apps.py` on disk before this card lands; the target layout at `docs/TREE.md #"## django_strawberry_framework (target package layout)"` already reserves the path.
- `django_strawberry_framework/conf.py` ships the `DJANGO_STRAWBERRY_FRAMEWORK` settings reader. It documents (in **inline comments** at `django_strawberry_framework/conf.py #"Import-time side effect: install the signal receiver"`, NOT in the module docstring — the module docstring at `django_strawberry_framework/conf.py #"Package settings, read from the host project's"` covers settings access, the defensive-`None` stance, and the `setting_changed` signal contract, but does not mention `AppConfig.ready()` as a non-viable home; the rationale lives as `#`-prefixed comments immediately above the `setting_changed.connect(...)` call) that `setting_changed` signal wiring is installed at **import time**, NOT in `AppConfig.ready()`, because "consumers may import `conf` before app loading during test bootstrap, so AppConfig.ready() is not a viable home for this wiring." Slice 1's `AppConfig` therefore has no settings-related wiring to subsume — the signal hook is intentionally outside `ready()` and stays there. That constraint is specific to the settings singleton and does not generalize: the upstream-patch dispatch of [Decision 4](#decision-4--ready-applies-the-upstream-patches) has the opposite requirement, since it must run once Django is fully configured.
- `examples/fakeshop/config/settings.py #"\"django_strawberry_framework\","` already declares `"django_strawberry_framework"` in `INSTALLED_APPS`. Django currently synthesizes an implicit `AppConfig` because no `apps.py` is found. Once Slice 1 lands, Django picks up the explicit `DjangoStrawberryFrameworkConfig` automatically (the implicit fallback applies only when no `AppConfig` subclass is defined in the package; Django 3.2+ resolves a single explicit AppConfig as the default without requiring `default = True`).
- `tests/base/test_init.py::test_public_api_surface_is_pinned` pins the package's `__all__` tuple. The AppConfig is NOT a public export (see [Decision 3](#decision-3--no-public-export)); this assertion stays unchanged in `0.0.7`.
- `tests/test_list_field.py` is the existing model for a flat single-file Layer-3 module's test home. `tests/test_apps.py` follows the same convention per [`docs/TREE.md #"## Test layout"`][tree].
- `examples/fakeshop/test_query/test_library_api.py` exercises the live `/graphql/` endpoint with the package installed via `INSTALLED_APPS`. The test suite already proves the implicit `AppConfig` works end-to-end; once Slice 1 lands, the same tests exercise the explicit `AppConfig` without code changes (the test file imports `from django.test import Client` and posts JSON to `/graphql/`, which has no AppConfig-specific assertions).
- `DONE-021-0.0.7`'s `KANBAN.md` card body (at [`KANBAN.md`][kanban] #"DONE-021-0.0.7 - `apps.py` and Django app config") is intentionally sparse — three Definition-of-done bullets and no "Why it matters" narrative. The narrative this spec carries (parity with `strawberry-django`, asymmetry with `graphene-django`, the app-load hook) is fleshed out here so the spec can stand on its own.

## Goals

1. Ship `django_strawberry_framework/apps.py` containing `DjangoStrawberryFrameworkConfig(AppConfig)` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`. Two class-level behavioral attributes plus a one-line module docstring (required by `D100`) and a one-line class docstring (required by `D101`); the docstrings are documentation, not behavior, and are exempt from the negative-shape iteration accordingly.
2. Ship `tests/test_apps.py` containing the four positive contracts in [Test plan](#test-plan) — importability, subclass, attribute pinning, Django registry pickup — the one consolidated negative-shape test asserting that none of `{"label", "default_auto_field", "default"}` are defined on the class, and the three tests pinning `ready()` and its dispatch.
3. Give the package the one app-load hook it needs and no more. `ready()` exists to dispatch the upstream patches of [Decision 4](#decision-4--ready-applies-the-upstream-patches); it registers no checks, connects no signals, adds no settings key, and imports no `DjangoType` module. [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands"'s "Add a settings key only when the feature that needs it lands; never preemptively" generalizes to AppConfig hooks: a hook lands with the shipped feature that needs it, never ahead of one.
4. Preserve the consumer's import order — the AppConfig must NOT eagerly import `DjangoType` modules or call [`finalize_django_types`][glossary-finalize-django-types]. The synchronization-point contract documented in [`docs/README.md`][readme]'s "Schema setup boundary" stays with the consumer.
5. Keep `__all__` unchanged. The AppConfig is import-time plumbing; consumers reach it via Django's app-loader machinery, not via `from django_strawberry_framework import ...`.

## Non-goals

- A `ready()` body beyond the upstream-patch dispatch — Django system checks, signal connections, management-command auto-registration, or `finalize_django_types` invocation. See [Decision 4](#decision-4--ready-applies-the-upstream-patches).
- A `default_auto_field` declaration. The package ships zero Django models; the attribute is meaningless here. See [Decision 5](#decision-5--no-default_auto_field-and-no-models).
- Auto-invocation of [`finalize_django_types`][glossary-finalize-django-types] from `AppConfig.ready()`. The consumer's `config/schema.py` (or equivalent) owns the call; `ready()` fires before the consumer's schema module is necessarily imported, so a `ready()`-side call would either finalize too early (relations from yet-to-import modules unresolved) or be silently ineffective.
- A re-export of `DjangoStrawberryFrameworkConfig` from `django_strawberry_framework/__init__.py`. Django's app-loader resolves the class through its dotted module path; consumers never write `from django_strawberry_framework import DjangoStrawberryFrameworkConfig`. See [Decision 3](#decision-3--no-public-export).
- A custom `label` shorter than `"django_strawberry_framework"`. The Django default (the last segment of `name`) is already unique. See [Decision 2](#decision-2--name--label--verbose_name-pinning).
- A bootstrap helper for `DJANGO_STRAWBERRY_FRAMEWORK` settings defaults. `conf.py` already handles missing-key and `None` cases; no `ready()`-side initialization is needed. [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands" explicitly forbids preemptive settings.
- The content of the upstream patches themselves. `ready()` dispatches them; what each one hardens, and why, belongs to the cards that shipped the patch modules — see [Out of scope](#out-of-scope-explicitly-tracked-elsewhere).
- A Django management command surface. Tracked under `DONE-022-0.0.7` (the `export_schema` command), which has its own `management/commands/export_schema.py` module and does NOT need this card's AppConfig to do any wiring (Django discovers management commands by directory convention, not by AppConfig method).
- An update to `examples/fakeshop/config/settings.py #"\"django_strawberry_framework\","`'s `INSTALLED_APPS` entry — current text is `"django_strawberry_framework"` (the dotted package name). Django's implicit single-AppConfig discovery means this entry continues to work unchanged; no need to tighten to `"django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig"`. See [Decision 7](#decision-7--no-fakeshop-installed_apps-entry-change).

## Borrowing posture

The two reference packages at the paths given in [`docs/TREE.md`][tree] take opposite stances on shipping an `apps.py`. The slice borrows the shape from the one that ships it.

### From `strawberry_django` — borrow the AppConfig shape

Local source path: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/apps.py` (referenced from [`docs/TREE.md #"## strawberry_django"`][tree]).

Verified contents (four lines plus blank):

```python
from django.apps import AppConfig


class StrawberryDjangoConfig(AppConfig):
    name = "strawberry_django"
    verbose_name = "Strawberry django"
```

- **AppConfig subclass with two attributes.** Same shape adopted here: `name` (the package directory) and `verbose_name` (a human-readable label). strawberry-django's shape is the minimal Django-correct surface for an installable package; the upstream has shipped this for years without needing more. **Two forced documentation divergences**: this repo's pydocstyle gate (`pyproject.toml [tool.ruff.lint] select = [..., "D", ...]`) enables both `D100` ("Missing docstring in public module") and `D101` ("Missing docstring in public class"); neither is in the ignore list. The upstream `strawberry_django/apps.py` has neither a module docstring nor a class docstring. We add one of each; see [Decision 2](#decision-2--name--label--verbose_name-pinning).
- **One deliberate behavioral divergence: `ready()`.** strawberry-django implements no `ready()`; this package does, because it ships defensive upstream patches that must be installed once Django is configured and that a consumer must not have to install by hand. The divergence is scoped to exactly that dispatch and nothing else — see [Decision 4](#decision-4--ready-applies-the-upstream-patches). The general posture is unchanged: an AppConfig hook lands with the shipped feature that needs it, never ahead of one.
- **No `default_auto_field`.** strawberry-django does not declare one; neither do we. Both packages ship zero Django models; the attribute is irrelevant.

### From `graphene_django` — explicitly do not borrow the absence

Local source path: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/` (referenced from [`docs/TREE.md #"## graphene_django"`][tree]).

- **graphene-django ships NO `apps.py`** (verified by `find … -name apps.py` over the installed package directory; no result). Consumers add `"graphene_django"` to `INSTALLED_APPS` and rely on Django's implicit AppConfig fallback.
- **We do not borrow this.** graphene-django's implicit-only stance is a historical artifact of the package predating Django 3.2's AppConfig-discovery improvements. Modern Django convention is to ship an explicit `AppConfig`; the parity story consumers expect coming from `strawberry-django` is on the explicit-AppConfig side; and the app-load hook the package needs for its upstream patches only opens with an explicit class.

### Explicitly do not borrow

- strawberry-django's broader `apps/` / `extensions/` / `middleware/` structure that surrounds its `apps.py`. We ship just the AppConfig in `0.0.7`; the surrounding modules land card-by-card under their own specs ([`KANBAN.md`][kanban] — `DONE-042-0.0.14` debug-toolbar middleware, etc.).
- Any `verbose_name` translation infrastructure (`from django.utils.translation import gettext_lazy as _`). strawberry-django does not localize its string; we do not either. Translation is a separate concern; deferring it costs nothing.
- Django's `default` class attribute (at any value — `True`, `False`, or other). Django 3.2+ resolves a single explicit AppConfig in a package as the default without the marker; declaring it at any value would be either redundant (`True`) or self-defeating (`False`). See [Decision 8](#decision-8--no-default-attribute).

## User-facing API

The shipped consumer surface in `0.0.7` adds exactly one new module (`django_strawberry_framework/apps.py`) containing one new class (`DjangoStrawberryFrameworkConfig`). The class is NOT added to `__all__`; consumers reach it through Django's app-loader, not through the package's import surface.

### Default usage — `INSTALLED_APPS` by package name

```python path=null start=null
# Consumer's Django settings module
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    # ... other Django apps ...
    "django_strawberry_framework",
    # Consumer's own apps:
    "apps.my_app",
]
```

Django's app loader scans `django_strawberry_framework/apps.py`, finds exactly one `AppConfig` subclass (`DjangoStrawberryFrameworkConfig`), and uses it as the package's `AppConfig` automatically. No change to consumer code is required compared to the implicit-AppConfig behavior they had under `0.0.6`; the explicit class is what changes. This entry is also the whole opt-in for the upstream patches of [Decision 4](#decision-4--ready-applies-the-upstream-patches) — there is no second thing to install.

### Explicit dotted path (optional, equivalent)

Consumers who prefer to be explicit can name the AppConfig directly:

```python path=null start=null
INSTALLED_APPS = [
    "django.contrib.admin",
    # ...
    "django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig",
]
```

Equivalent to the package-name form above. The package documentation recommends the package-name form in [`docs/README.md`][readme] for brevity, but both work.

### `django.apps.apps.get_app_config("django_strawberry_framework")`

After Django finishes app-loading, the AppConfig is reachable through Django's registry under the `name` value `"django_strawberry_framework"`:

```python path=null start=null
from django.apps import apps

config = apps.get_app_config("django_strawberry_framework")
# -> <DjangoStrawberryFrameworkConfig: django_strawberry_framework>
config.verbose_name
# -> "Django Strawberry Framework"
```

This is the path a card attaching behavior to the package's AppConfig uses, and the path `tests/test_apps.py` uses to drive `ready()` deterministically. Pinning the resolution path means later cards do not have to re-litigate the lookup string.

## Architectural decisions

### Decision 1 — Module location & public export

**Module location.** `DjangoStrawberryFrameworkConfig` lives in **`django_strawberry_framework/apps.py`** (new flat single-file module at the package root, matching the [`docs/TREE.md`][tree] target layout at `docs/TREE.md #"## django_strawberry_framework (target package layout)"`).

- The card's KANBAN body at [`KANBAN.md`][kanban] #"DONE-021-0.0.7 - `apps.py` and Django app config" names `django_strawberry_framework/apps.py` as the single new source file.
- Django's app-loader expects `apps.py` at the package root by convention. Putting it anywhere else (`apps/config.py`, `_apps.py`, etc.) breaks the convention without benefit.

**Public-export surface.** `django_strawberry_framework/__init__.py` is NOT modified. See [Decision 3](#decision-3--no-public-export).

### Decision 2 — `name` / `label` / `verbose_name` pinning

The class declares exactly **two class-level behavioral attributes** plus the `ready()` override of [Decision 4](#decision-4--ready-applies-the-upstream-patches) and its inherited base behavior; the module and class docstrings are documentation (not behavior) and are accordingly exempt from the negative-shape iteration set:

- `name = "django_strawberry_framework"` — matches the package directory; matches the `INSTALLED_APPS` entry consumers already type; matches the string `examples/fakeshop/config/settings.py #"\"django_strawberry_framework\","` already declares.
- `verbose_name = "Django Strawberry Framework"` — Title Case with spaces; matches the `README.md` H1; matches the human-readable form a consumer would type if asked "what is this package called?".

Documentation (gate-forced, not behavioral):

- Module docstring (one line) at the top of `apps.py` — required by ruff's `D100` rule (same `pyproject.toml [tool.ruff.lint] select = [..., "D", ...]` gate as `D101`; not in the ignore list).
- Class docstring `"""Register django-strawberry-framework with Django's app loader."""` (or equivalent one-liner) directly under the class statement — required by ruff's `D101` rule.

Both docstrings diverge from strawberry-django's `apps.py` (which has neither) because this repo's pydocstyle gate is stricter than the upstream's; both divergences are forced by the gate, not chosen for stylistic reasons.

Deliberately NOT declared:

- `label = "..."` — Django's default `label` is the last segment of `name` (here, `"django_strawberry_framework"`). The default is unique within any conceivable consumer project and matches the lookup string in `django.apps.apps.get_app_config(...)`. Declaring a custom `label` (e.g., `"dsf"`) would (a) introduce a second lookup string consumers have to learn, and (b) silently invalidate any future `manage.py` command that the package or a third party writes against the `django_strawberry_framework` label. Symmetric with strawberry-django's choice to omit `label`.
- `default_auto_field = "..."` — see [Decision 5](#decision-5--no-default_auto_field-and-no-models).

Every attribute the spec adds is one the test plan has to pin; every attribute that doesn't ship is one the spec doesn't have to defend. The `verbose_name` value diverges from strawberry-django's `"Strawberry django"` (lowercase second word) because the `README.md` and consumer-facing prose uses Title Case throughout. The string is cosmetic and would be the source of a future cosmetic fix if we got it wrong; the test plan pins it so the choice is durable.

### Decision 3 — No public export

`django_strawberry_framework/__init__.py` is NOT modified. The class is reachable at the dotted path `django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig`; consumers never write `from django_strawberry_framework import DjangoStrawberryFrameworkConfig`.

- Django's app-loader resolves AppConfigs through their dotted module path, not through any `__init__.py` re-export. The class never appears in consumer code that isn't `INSTALLED_APPS`.
- `tests/base/test_init.py::test_public_api_surface_is_pinned` pins `__all__`; adding a name to `__all__` for something consumers never `import` would be a noise-only API widening.
- Symmetric with strawberry-django, which also does not re-export its `StrawberryDjangoConfig`.
- The distinction against a sibling `0.0.7` card is the consumer's import: [`DjangoListField`][glossary-djangolistfield] IS re-exported by [`spec-020`][spec-020] because consumers write it into their schema modules by hand. The AppConfig is not in that category, so the two cards take opposite export decisions from the same rule.

### Decision 4 — `ready()` applies the upstream patches

`DjangoStrawberryFrameworkConfig` overrides `ready()`, and the override does exactly one thing: it dispatches the package's three defensive upstream-patch appliers, in this order — `django_strawberry_framework/_django_patches.py::apply`, then `django_strawberry_framework/_strawberry_patches.py::apply`, then `django_strawberry_framework/_cross_web_patches.py::apply` (`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`). The three imports are **function-local**, so importing `django_strawberry_framework.apps` outside Django pulls in no patch module.

One patch module per third-party dependency the package has to patch — the mechanism as a whole is [Upstream patches][glossary-upstream-patches]. **Each module's own docstring is the single source of truth for exactly which upstream bugs it hardens**, and `ready()` deliberately repeats none of that inventory — so does this Decision, for the same reason: a second copy of the inventory is a second thing to keep true.

Every applier self-gates on the `APPLY_UPSTREAM_PATCHES` setting (`django_strawberry_framework/conf.py::upstream_patches_enabled`, default on). A consumer who sets `DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": False}` gets none of them; the per-dependency mapping form `{"APPLY_UPSTREAM_PATCHES": {"django": False}}` disables one dependency's patches and leaves the others installed. **The gate lives inside each `apply()`, not in `ready()`** — the dispatcher is unconditional, so a consumer reading `ready()` sees three unguarded calls and must follow them to `conf.py` for the gate. That placement is deliberate: the gate is per dependency, and a `ready()`-level gate could only be all-or-nothing.

Each `apply()` is idempotent and self-healing, so a repeated `ready()` — some Django test runners fire it more than once — is safe, and a `ready()` fired after one of the patch modules has been reloaded retains the module's true upstream capture and installs the reloaded replacement rather than rejecting the prior replacement as an unsupported upstream change.

`ready()` is the canonical place for one-time setup that depends on Django being fully configured, and it is what makes the patches free for consumers: `"django_strawberry_framework"` in `INSTALLED_APPS` is the whole contract — no `conftest.py` workaround, no base test class to inherit, no settings key to add.

What `ready()` does NOT do:

- **It does not call [`finalize_django_types`][glossary-finalize-django-types].** `ready()` fires after Django's app registry is populated but **before** the consumer's `config/schema.py` (or equivalent) is necessarily imported, so a `ready()`-side call would either finalize too early (relations from not-yet-imported modules unresolved → `ConfigurationError`) or — if Django happened to import the schema module first via signal cascades — be silently redundant with the consumer's explicit call. Both shapes are footguns, and the consumer-owned synchronization-point contract in [`docs/README.md`][readme]'s "Schema setup boundary" section makes `ready()` explicitly the wrong home.
- **It does not import consumer `DjangoType` modules**, directly or transitively. The dispatch touches only the three private patch modules.
- **It does not install the `conf.py` `setting_changed` receiver.** That wiring is installed at import time because consumers may import `conf` before app loading during test bootstrap; see [Current state](#current-state).
- **It does not register Django system checks, connect signal handlers, or register management commands.** Django discovers management commands by directory convention, and a check that validates `DjangoType` declaration invariants has its own design surface (what does it warn about? what is the message? does it gate `manage.py runserver`?) that needs its own spec.

The negative-shape test of [Test plan](#test-plan) therefore forbids three keys, not four: `label`, `default_auto_field` and `default`. `ready` is required and is pinned positively — present and callable in the class body, dispatching all three appliers, safe on a re-fire, and correct across a patch-module reload.

### Decision 5 — No `default_auto_field` and no models

`DjangoStrawberryFrameworkConfig` does NOT declare `default_auto_field`. The package ships zero Django models; the attribute is meaningless.

- `default_auto_field` controls the auto PK type for models declared *inside* the AppConfig's package. `django_strawberry_framework/` declares no `models.py`; no model anywhere in the package directory tree.
- A future card that adds models (none on the current roadmap; `BACKLOG.md` does not propose any either) revisits this attribute alongside that decision.
- Symmetric with strawberry-django, which also does not declare it.

### Decision 6 — Joint `0.0.7` cut

`0.0.7` ships four WIP cards as a bundle per [`spec-020`][spec-020] Decision 10 (excluding the already-shipped `DONE-020-0.0.7`): `DONE-021-0.0.7` (this card), `DONE-022-0.0.7` (schema-export management command), `DONE-023-0.0.7` (multi-db cooperation contract), and `DONE-025-0.0.7` (warning-free scalar registration). The version bump in `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__` line, and `tests/base/test_init.py`'s pinned version assertion is owned by whichever card ships last in the bundle, NOT this card.

- The cross-card policy is [`spec-020`][spec-020]'s [Decision 10][spec-020-decision-10]: the last `0.0.7` card to ship owns the version bump from `0.0.6`. This Decision restates it verbatim so Slice 3's checklist can reference it without chasing the cross-spec pointer.
- The CHANGELOG `[0.0.7]` `### Added` entries accumulate across the bundle's cards; each card writes its own Added line under the same `[0.0.7]` heading.

The Slice 3 doc-updates list explicitly excludes the version bump.

### Decision 7 — No fakeshop `INSTALLED_APPS` entry change

`examples/fakeshop/config/settings.py #"\"django_strawberry_framework\","` currently declares `"django_strawberry_framework"` (the dotted package name, not the AppConfig dotted path). Slice 1 does NOT change this entry.

- Django's implicit single-AppConfig discovery (Django 3.2+) resolves the package-name form to the explicit `DjangoStrawberryFrameworkConfig` automatically once `apps.py` ships.
- Changing the fakeshop entry to `"django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig"` would (a) churn a settings file that has no other reason to change in this slice, and (b) advertise the explicit-dotted-path form as the recommended one — but the User-facing API section recommends the package-name form for brevity, and the example should match the recommendation.
- The existing live `/graphql/` HTTP tests in `examples/fakeshop/test_query/test_library_api.py` continue to exercise the package's `INSTALLED_APPS` path; once `apps.py` lands, those tests are the end-to-end evidence that the explicit AppConfig works through the same entry string the implicit one did.

### Decision 8 — No `default` attribute

`DjangoStrawberryFrameworkConfig` does NOT declare `default` at all (neither `default = True` nor `default = False`). The consolidated negative-shape test enforces this by asserting `"default" not in DjangoStrawberryFrameworkConfig.__dict__`; that scope matches `default = True`, `default = False`, and any other value, which is symmetric with [Decision 2](#decision-2--name--label--verbose_name-pinning) and [Decision 5](#decision-5--no-default_auto_field-and-no-models), each of which forbids its attribute outright rather than at a specific value.

- Django 3.2+ resolves a single explicit `AppConfig` subclass in a package's `apps.py` as the default automatically, without requiring the marker (the `True` case).
- `default = False` would be self-defeating in this context — declaring "this AppConfig is NOT the default" while shipping the only AppConfig in the package contradicts Django's implicit resolution. Forbidding both prevents the self-defeating shape from creeping in defensively.
- The package will only ever declare one `AppConfig` (there is no use case for two within the same package directory), so the disambiguation that an explicit `default` provides is irrelevant.
- Symmetric with strawberry-django, which does not declare `default` either (any value).

## Implementation plan

The slice ships as **three slices** aligned with the [Slice checklist](#slice-checklist). Each slice maps to one commit; squashing all three into a single PR is acceptable given the small surface.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — Module + `AppConfig` subclass | `django_strawberry_framework/apps.py` (new) | 0 (tests land in Slice 2) | `+43 / -0` |
| 2 — Tests | `tests/test_apps.py` (new) | 8 (4 positive shape + 1 consolidated negative-shape covering three forbidden keys + 3 pinning `ready()` and its dispatch; see [Test plan](#test-plan)) | `+184 / -0` |
| 3 — Promotion + docs | `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md` | 0 | `+25 / -8` |

The three slices must be authored in order. Slice 2 depends on Slice 1 (the class must exist before tests can import it); Slice 3 depends on Slice 2 (the CHANGELOG `### Added` line and `KANBAN.md` Done body must describe a shipped, tested module, not a half-landed one).

## Edge cases and constraints

- **Django 3.2+ AppConfig discovery.** The package's `pyproject.toml #"Django>=5.2"` pins `Django>=5.2.16`; Django's "explicit single AppConfig becomes the default" behavior has been in place since 3.2, well below the floor. The spec assumes this and does not include a fallback for older Django versions.
- **`INSTALLED_APPS` ordering.** Django processes `INSTALLED_APPS` top-to-bottom for `ready()` dispatch. This package's `ready()` installs process-global replacements on upstream classes and reads no other app's state, and every `apply()` is idempotent, so its position relative to other apps in the consumer's `INSTALLED_APPS` is irrelevant; any position works.
- **Multiple AppConfigs in `apps.py`.** Not a concern in `0.0.7` (only one class is declared) but worth noting for future cards: if a second AppConfig is ever added, the explicit `default = True` marker on one of the classes becomes load-bearing, AND the consolidated negative-shape test in `tests/test_apps.py` must be updated in the same change — the future card's spec removes `"default"` from the iterated forbidden-key set `{"label", "default_auto_field", "default"}` AND adds `default = True` to one of the AppConfig classes. A card that needs to declare a currently-forbidden attribute removes the key from the iterated set in the same change it adds the attribute; [Decision 8](#decision-8--no-default-attribute) pins the current single-AppConfig test scope, and a multi-AppConfig future explicitly relaxes that pin.
- **`django.apps.apps.get_app_config("dsf")` (or any other label shortcut).** Returns `LookupError` — the resolution string is `"django_strawberry_framework"` (the value of `name` / `label`), not an alias. Pinned in the test plan so a future drive-by `label = "dsf"` edit fails the test.
- **AppConfig instantiation under `pytest-django`.** `pytest-django` sets up Django's app registry once per session via `django.setup()`; the AppConfig is instantiated as part of that bootstrap. Tests in `tests/test_apps.py` can rely on the registry being populated and use `apps.get_app_config(...)` directly.
- **`AppConfig.ready` is called during `django.setup()`.** The three patch sets are therefore installed before any test row runs, which is why a test that wants to observe the dispatch must first revert the patched slots to the modules' captured upstream originals and then drive `ready()` itself — asserting "the patches are installed" without that revert asserts nothing about `ready()`, since an earlier direct `apply()` call anywhere in the session would satisfy it. Restore every perturbed slot in a `finally`: the slots are process-global and leak across the worker's remaining rows otherwise.
- **Re-importing `django_strawberry_framework.apps` outside Django.** A pure-Python `import django_strawberry_framework.apps` is legal — the module defines a class and imports `django.apps.AppConfig` and nothing else. The three patch-module imports live inside `ready()`, so they are not pulled in by the import alone. No new dependency surface.
- **Coverage of the AppConfig under `fail_under = 100`.** The class body has two attribute assignments, docstrings, and the `ready()` override. The positive tests cover importability, the attribute values and registry pickup; the three `ready()` tests cover the dispatch body, including a re-fire and a post-reload fire. The consolidated negative-shape test is a class-level assertion, not a body-line coverage assertion.

## Test plan

Tests live in one tree, matching the rules in [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Test-tree placement is mandatory.

### `tests/test_apps.py` (new)

Package tests; system-under-test is `django_strawberry_framework`. The file is the flat single-file module's mirror per [`docs/TREE.md #"## Test layout"`][tree]. Eight tests.

Positive shape tests (Slice 2):

- `test_djangostrawberryframeworkconfig_importable_from_apps_module` — `from django_strawberry_framework.apps import DjangoStrawberryFrameworkConfig` resolves without `ImportError`. Pins the module path so a future move to `django_strawberry_framework/django/apps.py` or similar fails this test (and is caught before merging).
- `test_djangostrawberryframeworkconfig_is_appconfig_subclass` — `issubclass(DjangoStrawberryFrameworkConfig, django.apps.AppConfig)` is `True`. Pins the inheritance so a refactor that accidentally inherits from a different base (e.g., `django.apps.config.AppConfig` via direct import, or a custom intermediate) is caught.
- `test_djangostrawberryframeworkconfig_pins_name_and_verbose_name` — asserts `DjangoStrawberryFrameworkConfig.name == "django_strawberry_framework"` and `DjangoStrawberryFrameworkConfig.verbose_name == "Django Strawberry Framework"`. Pins both attribute values; a cosmetic edit to either is caught at test time.
- `test_djangostrawberryframeworkconfig_resolves_through_django_app_registry` — calls `django.apps.apps.get_app_config("django_strawberry_framework")` and asserts the returned instance `isinstance(...)` of `DjangoStrawberryFrameworkConfig`. This is the load-bearing assertion that Django actually picked up the explicit class (not the implicit fallback). Without this test, the explicit AppConfig could silently fail to register and the implicit one could stand in.

Negative-shape test (Slice 2):

- `test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes` — iterates the three forbidden **behavioral** keys `{"label", "default_auto_field", "default"}` and asserts `key not in DjangoStrawberryFrameworkConfig.__dict__` for each, with a fail message naming the offending key and the Decision that forbids it. Pins the "exactly the two behavioral attributes of [Decision 2](#decision-2--name--label--verbose_name-pinning), the `ready()` override of [Decision 4](#decision-4--ready-applies-the-upstream-patches), and the docstrings required by `D100` / `D101`; nothing more" contract — covering `label` ([Decision 2](#decision-2--name--label--verbose_name-pinning)), `default_auto_field` ([Decision 5](#decision-5--no-default_auto_field-and-no-models)), and `default` ([Decision 8](#decision-8--no-default-attribute)) in a single class-body contract assertion. `"ready"` is deliberately absent from the set — the method is required, and the file carries an in-place comment saying so, since "no extra AppConfig attributes" is exactly the sentence a later reader would use to justify deleting it. The implicit `__doc__` key is not in the set either: documentation is not behavior. If a future drive-by edit adds `label = "dsf"`, `default_auto_field = "django.db.models.BigAutoField"`, `default = True` or `default = False` — each violating its corresponding Decision — this test fails and the edit is caught before merge.

`ready()` tests (Slice 2), per [Decision 4](#decision-4--ready-applies-the-upstream-patches):

- `test_djangostrawberryframeworkconfig_defines_ready_for_django_patches` — asserts `"ready" in DjangoStrawberryFrameworkConfig.__dict__` and that it is callable. The cheap structural pin: a refactor that removes the override outright fails loudly here, and the behavior is pinned by the next test.
- `test_ready_dispatches_all_three_patch_appliers_and_refires_safely` — reverts all three patches to the modules' captured upstream originals, asserts all three report not-installed, drives `ready()` through the registered `AppConfig`, and asserts every patch is installed. A second `ready()` pins dispatch-layer idempotence. The revert is what makes this test distinguishing: the patch modules' own suites each assert "installed at collection via `ready()`", but those assertions are masked by direct `apply()` calls made earlier in file order on the same worker, so a `ready()` that lost one dispatch line would still pass them.
- `test_ready_reinstalls_patches_after_their_modules_reload` — reloads each patch module **twice**, asserting after each reload that the module's captured upstream originals are unchanged, then fires `ready()` and asserts all three patches are installed. The second reload is the one that matters: it reloads a module whose installed replacement is itself the product of the first reload, so the capture contract is pinned for repeated reloads rather than only the first. Both process-global halves — the module namespaces and the patched class attributes — are saved and restored together, because restoring only the class attributes would leave them pointing at pre-reload objects while the modules hold post-reload ones, making every installed-check report a spurious `False` for the rest of the worker's run.

No live `/graphql/` HTTP test is required. The `examples/fakeshop/test_query/test_library_api.py` suite already exercises the package through `INSTALLED_APPS` end-to-end; once `apps.py` lands, those tests continue to pass through the explicit AppConfig with zero modifications. Adding an HTTP test specifically for the AppConfig would be a coverage detour — the AppConfig's job is to register and to dispatch; the registry test and the three `ready()` tests pin those contracts directly.

No example-project test is required either. The system-under-test is the package's AppConfig; the package-internal test home is canonical.

## Doc updates

- [`docs/GLOSSARY.md`][glossary]
  - Flip [`Django AppConfig`][glossary-django-appconfig] from `planned for 0.0.7` to `shipped (0.0.7)`.
  - Update the entry body to describe the shipped contract: `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`; `ready()` dispatches the package's three upstream-patch appliers, all gated by `APPLY_UPSTREAM_PATCHES`; consumers list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's implicit single-AppConfig discovery resolves the explicit class. The entry names the dispatch, not the patch inventory — each patch module's docstring owns that.
  - Update the Index table's status column for the [`Django AppConfig`][glossary-django-appconfig] row (at `docs/GLOSSARY.md #"[Django `AppConfig`](#django-appconfig)"`).

- [`docs/README.md`][readme]
  - Add a bullet to the shipped-features list: "`Django AppConfig` — `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` so consumers can list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's check / signal hooks resolve through it (new in `0.0.7`)."
  - Remove the `Django AppConfig` mention from the forward-looking "coming" list, and only that mention: every other entry in that list belongs to the card that ships it, and removing one early falsifies the docs while its feature is still planned.

- [`docs/TREE.md`][tree]
  - `apps.py` appears in the `django_strawberry_framework/` **current on-disk layout** section (`docs/TREE.md #"## django_strawberry_framework (current on-disk layout)"`), alphabetical position between `__init__.py` and `conf.py`.
  - `apps.py` appears in the **target package layout** section (`docs/TREE.md #"## django_strawberry_framework (target package layout)"`) with no `[alpha]` tag — the tag meant "lands before `0.1.0`", and the module has landed.
  - `tests/test_apps.py` appears in the current test-tree section (`docs/TREE.md #"## Test layout"`), positioned **before `test_list_field.py`** (alphabetical).

- [`KANBAN.md`][kanban]
  - Move `DONE-021-0.0.7` to the Done column with the next available `DONE-NNN-0.0.7` id (the column-move pass renumbers as usual; the next available id is determined at merge time, not pinned in this spec). The past-tense Done body summarizes the shipped scope: "Shipped `django_strawberry_framework/apps.py` containing `DjangoStrawberryFrameworkConfig(AppConfig)` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`, and no `ready()` override in this card's own diff; package-internal tests at `tests/test_apps.py`." The `ready()` body the `0.0.7` release carries arrives with sibling card `DONE-024-0.0.7` and dispatches the Django applier alone (see [Out of scope](#out-of-scope-explicitly-tracked-elsewhere)); a Done body attributing the full three-applier dispatch to this card would claim both a diff this card does not carry and appliers `0.0.7` does not ship.
  - Update the `### In progress` summary paragraph (at [`KANBAN.md`][kanban] #"### In progress") to remove `DONE-021-0.0.7` from the remaining-cards list once this card moves to Done.

- [`CHANGELOG.md`][changelog]
  - **Append** to the existing `[0.0.7]` `### Added` subsection (do NOT create a second `[0.0.7]` heading — the repo's `CHANGELOG.md` already has a `[0.0.7]` section from `DONE-020-0.0.7` and other prior `0.0.7` commits; every `0.0.7` card under the joint cut appends to the same shared section per [Decision 6](#decision-6--joint-007-cut)): `Django AppConfig` — `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`. Consumers list `"django_strawberry_framework"` in `INSTALLED_APPS`; Django's check / signal hooks resolve through the package's AppConfig. The `ready()` body imports `django_strawberry_framework._django_patches` and calls `apply()` to install the Django Trac #37064 hardening at app-load time — the one applier the `0.0.7` release carries; the Strawberry and `cross_web` appliers are not `0.0.7` content and this entry does not claim them.
  - The version bump entry is owned by **the last `0.0.7` card to ship** per [Decision 6](#decision-6--joint-007-cut), NOT this slice.
  - [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" ("No CHANGELOG.md updates unless told") — this Slice 3 bullet is the explicit instruction.

- No edits to [`README.md`][readme-root]. Justification: the README's status section is consumer-prose ("public names are stable; correctness and edge-case behavior are still hardening"); the AppConfig is plumbing, not a consumer-name surface change. The features the README does name (`DjangoListField`, the optimizer, `DjangoType`) are the user-facing primitives; the AppConfig is the registration plumbing underneath.

- No edits to [`GOAL.md`][goal]. Justification: `GOAL.md`'s `astronomy` showcase walks through model definitions, schema, filters, orders, aggregates, fieldsets — none of which exercises `INSTALLED_APPS` directly. The example project does declare `INSTALLED_APPS`, but `GOAL.md` is the framing document, not the example.

- No edits to [`TODAY.md`][today]. Justification: `TODAY.md` is a query-shape-and-capability snapshot ("what GraphQL queries work in fakeshop today?"). The AppConfig is not a query-shape change; the fakeshop schema is unchanged by this card.

## Out of scope (explicitly tracked elsewhere)

- The upstream patches `ready()` dispatches, and the modules that implement them. The Django half is `DONE-024-0.0.7` ([`docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md`][spec-024]); the Strawberry and `cross_web` halves are later cards. This card owns the dispatch site and the `AppConfig` shape around it, never the patch content — each patch module's docstring is the single source of truth for what it hardens.
- [Schema export management command][glossary-schema-export-management-command] (`manage.py export_schema`): `DONE-022-0.0.7` in [`KANBAN.md`][kanban]. The command's discovery happens through Django's `management/commands/` directory convention, not through this card's AppConfig; the two cards are independent.
- [Multi-database cooperation][glossary-multi-database-cooperation] contract: `DONE-023-0.0.7` in [`KANBAN.md`][kanban]. The cooperation is in `types/resolvers.py`, not in `apps.py`; the two cards are independent.
- Warning-free scalar registration via `StrawberryConfig.scalar_map`: `DONE-025-0.0.7` in [`KANBAN.md`][kanban]. The scalar map is consumer-facing schema-construction shape, not AppConfig surface.
- Django checks for `DjangoType` declaration invariants (e.g., warn when a relation target is unimported at finalization time). Not on the current roadmap; a future card would extend `ready()` in tandem with the check's implementation.
- Channels ASGI router ([`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]): `DONE-041-0.0.14`, shipped in `0.0.14`.
- [Debug-toolbar middleware][glossary-debug-toolbar-middleware]: `DONE-042-0.0.14`, shipped in `0.0.14`.
- Test-client helpers ([`TestClient`][glossary-testclient], [`GraphQLTestCase`][glossary-graphqltestcase]): `DONE-043-0.0.14`, shipped in `0.0.14`.
- [Response-extensions debug middleware][glossary-response-extensions-debug-middleware]: `DONE-044-0.0.14`, shipped in `0.0.14`.
- `default_auto_field` declaration: not on the roadmap; the package ships no Django models. See [Decision 5](#decision-5--no-default_auto_field-and-no-models).

## Definition of done

The card is complete when all of the following are true:

1. `django_strawberry_framework/apps.py` exists and defines `DjangoStrawberryFrameworkConfig(AppConfig)` per [Decision 1](#decision-1--module-location--public-export) and [Decision 2](#decision-2--name--label--verbose_name-pinning) — `name = "django_strawberry_framework"`, `verbose_name = "Django Strawberry Framework"`, a one-line **module docstring** (required by ruff's `D100`), a one-line **class docstring** (required by ruff's `D101`), no `label` override, no `default_auto_field`, no `default` attribute at any value.
2. `django_strawberry_framework/__init__.py` is NOT modified (per [Decision 3](#decision-3--no-public-export)). `__all__` is unchanged.
3. `tests/base/test_init.py`'s `__all__` assertion is unchanged (per [Decision 3](#decision-3--no-public-export)).
4. `tests/test_apps.py` exists and contains the 8 tests listed in the [Test plan](#test-plan) — 4 positive shape, 1 consolidated negative-shape (`test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`) asserting `{"label", "default_auto_field", "default"}` are all absent from `DjangoStrawberryFrameworkConfig.__dict__`, and 3 pinning `ready()`: its presence and callability, its three-applier dispatch plus safe re-fire, and its correctness across a patch-module reload.
5. `examples/fakeshop/config/settings.py #"\"django_strawberry_framework\","` is NOT modified (per [Decision 7](#decision-7--no-fakeshop-installed_apps-entry-change)). The existing `"django_strawberry_framework"` entry continues to work through Django's implicit single-AppConfig discovery, now resolving to the explicit class.
6. The class overrides `ready()` with the three-applier dispatch and nothing else (per [Decision 4](#decision-4--ready-applies-the-upstream-patches)), and does not declare `label`, `default_auto_field`, or `default` at any value (per [Decision 2](#decision-2--name--label--verbose_name-pinning), [Decision 5](#decision-5--no-default_auto_field-and-no-models), [Decision 8](#decision-8--no-default-attribute) respectively). The three absences are pinned by the consolidated `test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`; the `ready()` presence and behavior are pinned by the three `ready()` tests, all in `tests/test_apps.py`.
7. The fakeshop live `/graphql/` HTTP tests at `examples/fakeshop/test_query/test_library_api.py` continue to pass unmodified — the explicit AppConfig is exercised through the existing `INSTALLED_APPS` entry without code changes elsewhere.
8. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`).
9. `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, and `CHANGELOG.md` reflect the shipped state per the [Doc updates](#doc-updates) section, `ready()` included. `README.md`, `GOAL.md`, and `TODAY.md` are NOT edited.
10. `KANBAN.md` moves `DONE-021-0.0.7` to Done with the next `DONE-NNN-0.0.7` id and a past-tense body summarizing the shipped scope.
11. The version bump is NOT in this card per [Decision 6](#decision-6--joint-007-cut); the last `0.0.7` card to ship owns `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s version assertion.
12. Zero new public exports — `__all__` is unchanged.
13. `uv run ruff format .` passes; `uv run ruff check --fix .` passes; `uv run pytest --no-cov` passes (the explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov`; coverage enforcement is CI's job per `pyproject.toml [tool.coverage.report] fail_under = 100`, not this slice's — workers verify the suite passes, not that coverage stays at 100%).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[pkg-dir]: ../../django_strawberry_framework/
[readme-root]: ../../README.md
[today]: ../../TODAY.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-debug-toolbar-middleware]: ../GLOSSARY.md#debug-toolbar-middleware
[glossary-django-appconfig]: ../GLOSSARY.md#django-appconfig
[glossary-djangographqlprotocolrouter]: ../GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangolistfield]: ../GLOSSARY.md#djangolistfield
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-graphqltestcase]: ../GLOSSARY.md#graphqltestcase
[glossary-multi-database-cooperation]: ../GLOSSARY.md#multi-database-cooperation
[glossary-response-extensions-debug-middleware]: ../GLOSSARY.md#response-extensions-debug-middleware
[glossary-schema-export-management-command]: ../GLOSSARY.md#schema-export-management-command
[glossary-testclient]: ../GLOSSARY.md#testclient
[glossary-upstream-patches]: ../GLOSSARY.md#upstream-patches
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-020]: spec-020-list_field-0_0_7.md
[spec-020-decision-10]: spec-020-list_field-0_0_7.md#decision-10--joint-007-cut
[spec-021-rationale]: appx/spec-021-apps-0_0_7-rationale.md
[spec-024]: spec-024-django_trac_37064_hardening-0_0_7.md

<!-- docs/builder/ -->
[artifact]: ../builder/ARTIFACT.md
[build]: ../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[apps]: /Users/riordenweber/projects/strawberry-django-main/strawberry_django/apps.py
