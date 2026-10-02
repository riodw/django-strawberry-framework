# Spec: `apps.py` and Django `AppConfig`

Target release: `0.0.7`.
Status: shipped (`0.0.7`, 2026-05-27); archived. Card `DONE-021-0.0.7`.
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [`Django AppConfig`][glossary-django-appconfig], [`finalize_django_types`][glossary-finalize-django-types], [`DjangoType`][glossary-djangotype]), [`KANBAN.md`][kanban] card `DONE-021-0.0.7`, predecessor spec [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] (Decision 10 — joint `0.0.7` cut policy reused here).

The alternatives each Decision rejected, and why, live in [`spec-021-apps-0_0_7-rationale.md`][spec-021-rationale]. This file states the contract.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`Django AppConfig`][glossary-django-appconfig] — the entry describing the shipped `AppConfig` and its `ready()` dispatch.
- [`finalize_django_types`][glossary-finalize-django-types] — the consumer-owned synchronization point that resolves pending relations; `AppConfig.ready()` does NOT call it (see [Decision 4](#decision-4--ready-applies-the-upstream-patches)).
- [`DjangoType`][glossary-djangotype] — the package's primary public surface; consumer modules that declare `DjangoType`s are imported by the consumer's project, not by the `AppConfig` (see [Decision 4](#decision-4--ready-applies-the-upstream-patches)).
- [`ConfigurationError`][glossary-configurationerror] — not raised by anything in `apps.py`; the module is validation-free (setting validation lives in `django_strawberry_framework/conf.py::upstream_patches_enabled`, which each applier calls).

Project conventions to follow:

- [`AGENTS.md`][agents] — #"Add a settings key only when the feature that needs it lands"; test placement at `tests/test_apps.py` per #"Test placement: `tests/` = package tests", paired with the flat `tests/test_<module>.py` mirror layout in [`docs/TREE.md #"## Test layout"`][tree].
- [`CONTRIBUTING.md`][contributing] — 100% coverage target.
- [`docs/TREE.md`][tree] — package layout; tests mirror source one-to-one. `apps.py` sits in both `docs/TREE.md #"## django_strawberry_framework (current source layout)"` and `docs/TREE.md #"## django_strawberry_framework (target package layout)"`.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan). Boxes stay unticked by convention; the `Status:` line is the completion record.

- [ ] Slice 1: Module + `AppConfig` subclass
  - [ ] Flat module `django_strawberry_framework/apps.py` (placement: see [Decision 1](#decision-1--module-location--public-export)) housing `DjangoStrawberryFrameworkConfig`.
  - [ ] `DjangoStrawberryFrameworkConfig(AppConfig)` declares exactly **two class-level behavioral attributes** plus **two docstrings** (documentation, not class state, and exempt from the negative-shape set accordingly):
    - `name = "django_strawberry_framework"` — Django app-label source; matches the package directory name so `django.apps.apps.get_app_config(...)` resolves through the same string consumers type into `INSTALLED_APPS`.
    - `verbose_name: "StrOrPromise" = "Django Strawberry Framework"` — display name in the Django admin's app listing; matches the `README.md` title. The annotation is `AppConfig.verbose_name`'s own type (`django_stubs_ext.StrOrPromise`, imported under `TYPE_CHECKING` only), so the declaration does not narrow the mutable base attribute covariantly.
    - module docstring (one line) — `"""Django ``AppConfig`` - registers the package and applies its upstream patches at app load."""`. **Required by ruff's `D100` rule** (`"D"` is in `pyproject.toml`'s `[tool.ruff.lint] select`, `D100` is not ignored, and `pyproject.toml #"[tool.ruff.lint.per-file-ignores]"` does not exempt `django_strawberry_framework/apps.py`). Do NOT suppress with `# noqa: D100` — the docstring IS the root-cause fix per [`AGENTS.md`][agents] #"Always give the root-cause fix even when slower".
    - class docstring (one line) — `"""Register django-strawberry-framework with Django's app loader."""`. **Required by ruff's `D101` rule** (symmetric with `D100`). Do NOT suppress with `# noqa: D101`.
  - [ ] `ready()` (decorated `@override` from `typing_extensions`) dispatches the package's four upstream-patch appliers and nothing else (per [Decision 4](#decision-4--ready-applies-the-upstream-patches)). The imports are function-local; the body is four `apply()` calls in this order (`django`, `strawberry`, `cross_web`, `graphql_core`), each self-gated on `APPLY_UPSTREAM_PATCHES`.
  - [ ] Do NOT set `default_auto_field` (per [Decision 5](#decision-5--no-default_auto_field-and-no-models)); do NOT set `label` (per [Decision 2](#decision-2--name--label--verbose_name-pinning)); do NOT set `default` at any value — neither `default = True` nor `default = False` — per [Decision 8](#decision-8--no-default-attribute).
  - [ ] Do NOT re-export `DjangoStrawberryFrameworkConfig` from `django_strawberry_framework/__init__.py` (per [Decision 3](#decision-3--no-public-export)). The class is reachable at `django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig` for consumers who name it explicitly in `INSTALLED_APPS`; Django's single-AppConfig discovery means consumers writing `"django_strawberry_framework"` get the explicit config without naming it.
- [ ] Slice 2: Tests
  - [ ] Test module `tests/test_apps.py` covering the four positive contracts in [Test plan](#test-plan): importable from `django_strawberry_framework.apps`, subclass of `django.apps.AppConfig`, `name` / `verbose_name` values, and Django registry pickup (`django.apps.apps.get_app_config("django_strawberry_framework")` returns a `DjangoStrawberryFrameworkConfig`).
  - [ ] One negative-shape test function: `DjangoStrawberryFrameworkConfig.__dict__` contains none of the three **behavioral** keys this spec forbids — `"label"` ([Decision 2](#decision-2--name--label--verbose_name-pinning)), `"default_auto_field"` ([Decision 5](#decision-5--no-default_auto_field-and-no-models)) and `"default"` ([Decision 8](#decision-8--no-default-attribute)). It is parametrized over `(key, reason)` pairs, one collected item per key, and the fail message names the offending key and the Decision that forbids it. It checks the class body, not inherited base attributes. **`"ready"` is NOT in the forbidden set** — `ready` is required and pinned positively below. **`__doc__` is NOT in the set either** — documentation is not behavior, and `D101` mandates it. A card that relaxes a forbidden key updates this test in the same change.
  - [ ] Three `ready()` tests (per [Decision 4](#decision-4--ready-applies-the-upstream-patches)): `ready` is present and callable in the class body; driving `ready()` through the registered `AppConfig` installs all four patch sets and a second `ready()` is safe; a `ready()` fired after a patch module reload retains the true upstream capture and reinstalls the reloaded replacement. Each restores every process-global slot it perturbs.
- [ ] Slice 3: Docs
  - [ ] [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][readme], [`docs/TREE.md`][tree], [`KANBAN.md`][kanban] and [`CHANGELOG.md`][changelog] carry the shipped state per [Doc updates](#doc-updates).
  - [ ] No edits to [`README.md`][readme-root], [`GOAL.md`][goal], or [`TODAY.md`][today]: the AppConfig is plumbing, not a consumer-visible API surface.
  - [ ] The version bump is not this card's (per [Decision 6](#decision-6--joint-007-cut)).
  - [ ] Final gates: `uv run ruff check --fix .` then `uv run ruff format .` per [`AGENTS.md`][agents] #"Run `uv run ruff check --fix .` then `uv run ruff format .` after every edit"; `uv run pytest --no-cov` (or a scoped subset) passes, coverage enforcement being CI's job per [`docs/builder/BUILD.md`][build]'s coverage-gate section; `__all__` in `django_strawberry_framework/__init__.py` gains nothing.

## Problem statement

Without an `apps.py`, Django synthesizes an implicit `AppConfig` for `"django_strawberry_framework"` in `INSTALLED_APPS`. That implicit config:

- carries the package's directory name as `name` and `label`, with a `verbose_name` derived by Django's heuristic rather than chosen by the package,
- cannot be referenced by an explicit dotted path in `INSTALLED_APPS` (`"django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig"` names nothing),
- gives the package no hook for Django-integration work that must run once the app registry is populated.

`strawberry_django` ships an [`apps.py`][apps] (a `class StrawberryDjangoConfig(AppConfig)` with `name` and `verbose_name`); `graphene_django` ships none (no `apps.py` under `~/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/`). The package's "Strawberry stays as the engine" half of its positioning in [`README.md`][readme-root] calls for parity with `strawberry-django`, so the package ships an explicit `AppConfig`.

The AppConfig is two behavioral attributes (`name`, `verbose_name`), a module docstring (`D100`), a class docstring (`D101`), and one `ready()` override whose entire body is the upstream-patch dispatch of [Decision 4](#decision-4--ready-applies-the-upstream-patches). The discipline is **what NOT to put in it**: no preemptive settings, no eager imports of `DjangoType` modules, no call to [`finalize_django_types`][glossary-finalize-django-types], no Django system checks. The consumer owns the `finalize_django_types` synchronization point per [`docs/README.md`][readme]'s "Schema setup" section.

## Current state

- `django_strawberry_framework/apps.py` defines `DjangoStrawberryFrameworkConfig` as described in [Slice 1](#slice-checklist); `docs/TREE.md` lists it in both package layouts.
- `django_strawberry_framework/conf.py` installs its `setting_changed` receiver at **import time**, not in `AppConfig.ready()`; the reason is an inline comment block above the `setting_changed.connect(...)` call (`django_strawberry_framework/conf.py #"Import-time side effect: install the signal receiver"`): consumers may import `conf` before app loading during test bootstrap. That constraint is specific to the settings singleton. The upstream-patch dispatch has the opposite requirement — it must run once Django is configured — so it lives in `ready()`.
- `examples/fakeshop/config/settings.py::INSTALLED_APPS` lists `"django_strawberry_framework"`; Django resolves that entry to the explicit `DjangoStrawberryFrameworkConfig` (a package whose `apps.py` defines exactly one `AppConfig` subclass gets it as the default without `default = True`).
- `tests/base/test_init.py::test_public_api_surface_is_pinned` pins the package's `__all__`; the AppConfig is not in it (see [Decision 3](#decision-3--no-public-export)).
- The live `/graphql/` suite under `examples/fakeshop/test_query/` runs through the same `INSTALLED_APPS` entry, so every live test exercises the explicit `AppConfig` and the patches its `ready()` installs; none asserts anything AppConfig-specific.

## Goals

1. `django_strawberry_framework/apps.py` contains `DjangoStrawberryFrameworkConfig(AppConfig)` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`: two class-level behavioral attributes plus a one-line module docstring (`D100`) and a one-line class docstring (`D101`), the docstrings exempt from the negative-shape set.
2. `tests/test_apps.py` contains the four positive contracts in [Test plan](#test-plan) — importability, subclass, attribute pinning, Django registry pickup — the negative-shape test asserting none of `{"label", "default_auto_field", "default"}` is defined on the class, and the three tests pinning `ready()` and its dispatch.
3. The package has the one app-load hook it needs and no more. `ready()` dispatches the upstream patches of [Decision 4](#decision-4--ready-applies-the-upstream-patches); it registers no checks, connects no signals, adds no settings key, and imports no `DjangoType` module. [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands" generalizes to AppConfig hooks: a hook lands with the shipped feature that needs it, never ahead of one.
4. The consumer's import order is preserved — the AppConfig does not eagerly import `DjangoType` modules or call [`finalize_django_types`][glossary-finalize-django-types].
5. `__all__` does not include the AppConfig. Consumers reach it via Django's app loader, not via `from django_strawberry_framework import ...`.

## Non-goals

- A `ready()` body beyond the upstream-patch dispatch — Django system checks, signal connections, management-command auto-registration, or `finalize_django_types` invocation. See [Decision 4](#decision-4--ready-applies-the-upstream-patches).
- A `default_auto_field` declaration. The package ships zero Django models. See [Decision 5](#decision-5--no-default_auto_field-and-no-models).
- Calling [`finalize_django_types`][glossary-finalize-django-types] from `AppConfig.ready()`. The consumer's `config/schema.py` (or equivalent) owns the call; `ready()` fires before the consumer's schema module is necessarily imported, so a `ready()`-side call would either finalize too early or be silently redundant.
- A re-export of `DjangoStrawberryFrameworkConfig` from `django_strawberry_framework/__init__.py`. See [Decision 3](#decision-3--no-public-export).
- A custom `label`. The Django default (the last segment of `name`) is already unique. See [Decision 2](#decision-2--name--label--verbose_name-pinning).
- A `ready()`-side bootstrap for `DJANGO_STRAWBERRY_FRAMEWORK` defaults. `conf.py` handles missing keys and `None` itself.
- The content of the upstream patches. `ready()` dispatches them; what each hardens belongs to its own module and spec — see [Out of scope](#out-of-scope-explicitly-tracked-elsewhere).
- Management-command wiring. `django_strawberry_framework/management/commands/export_schema.py` is discovered by Django's directory convention, not by an AppConfig method.
- Changing the `"django_strawberry_framework"` entry in `examples/fakeshop/config/settings.py::INSTALLED_APPS` to the dotted AppConfig path. See [Decision 7](#decision-7--no-fakeshop-installed_apps-entry-change).

## Borrowing posture

The two reference packages at the paths given in [`docs/TREE.md`][tree] take opposite stances on shipping an `apps.py`. The package borrows the shape from the one that ships it.

### From `strawberry_django` — borrow the AppConfig shape

Local source path: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/apps.py` (referenced from [`docs/TREE.md #"## strawberry_django"`][tree]).

Contents:

```python
from django.apps import AppConfig


class StrawberryDjangoConfig(AppConfig):
    name = "strawberry_django"
    verbose_name = "Strawberry django"
```

- **AppConfig subclass with two attributes.** Same shape here: `name` (the package directory) and `verbose_name` (a human-readable label). **Two forced documentation divergences**: this repo's pydocstyle gate enables `D100` and `D101`, and upstream has neither a module nor a class docstring. See [Decision 2](#decision-2--name--label--verbose_name-pinning).
- **One deliberate behavioral divergence: `ready()`.** strawberry-django implements no `ready()`; this package does, because it ships defensive upstream patches that must be installed once Django is configured and that a consumer must not have to install by hand. The divergence is scoped to that dispatch — see [Decision 4](#decision-4--ready-applies-the-upstream-patches).
- **No `default_auto_field`.** Neither package declares one; both ship zero Django models.

### From `graphene_django` — explicitly do not borrow the absence

Local source path: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/` (referenced from [`docs/TREE.md #"## graphene_django"`][tree]).

- **graphene-django ships NO `apps.py`.** Consumers add `"graphene_django"` to `INSTALLED_APPS` and rely on Django's implicit AppConfig fallback.
- **Not borrowed.** Modern Django convention is an explicit `AppConfig`; the parity consumers expect from `strawberry-django` is on the explicit side; and the app-load hook the upstream patches need exists only with an explicit class.

### Explicitly do not borrow

- strawberry-django's surrounding `extensions/` / `middleware/` structure. Each of this package's comparable modules lands under its own spec (for example `DONE-042-0.0.14`, debug-toolbar middleware).
- `verbose_name` translation (`gettext_lazy`). strawberry-django does not localize its string; neither does this package.
- Django's `default` class attribute at any value. See [Decision 8](#decision-8--no-default-attribute).

## User-facing API

The consumer surface is one module (`django_strawberry_framework/apps.py`) containing one class (`DjangoStrawberryFrameworkConfig`), not in `__all__`.

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

Django's app loader finds exactly one `AppConfig` subclass in `django_strawberry_framework/apps.py` and uses it. This entry is also the whole opt-in for the upstream patches of [Decision 4](#decision-4--ready-applies-the-upstream-patches) — there is no second thing to install.

### Explicit dotted path (optional, equivalent)

```python path=null start=null
INSTALLED_APPS = [
    "django.contrib.admin",
    # ...
    "django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig",
]
```

Equivalent to the package-name form. [`docs/README.md`][readme] uses the package-name form.

### `django.apps.apps.get_app_config("django_strawberry_framework")`

After app loading, the AppConfig is reachable through Django's registry under its label `"django_strawberry_framework"`:

```python path=null start=null
from django.apps import apps

config = apps.get_app_config("django_strawberry_framework")
# -> <DjangoStrawberryFrameworkConfig: django_strawberry_framework>
config.verbose_name
# -> "Django Strawberry Framework"
```

This is the path `tests/test_apps.py` uses to drive `ready()` deterministically, and the path any card attaching behavior to the package's AppConfig uses.

## Architectural decisions

### Decision 1 — Module location & public export

**Module location.** `DjangoStrawberryFrameworkConfig` lives in **`django_strawberry_framework/apps.py`**, a flat single-file module at the package root. Django's app loader looks for `apps.py` at the package root by convention; anywhere else breaks the convention without benefit.

**Public-export surface.** Not re-exported. See [Decision 3](#decision-3--no-public-export).

### Decision 2 — `name` / `label` / `verbose_name` pinning

The class declares exactly **two class-level behavioral attributes**, plus the `ready()` override of [Decision 4](#decision-4--ready-applies-the-upstream-patches); the module and class docstrings are documentation and are exempt from the negative-shape set:

- `name = "django_strawberry_framework"` — matches the package directory, the `INSTALLED_APPS` entry consumers type, and the entry in `examples/fakeshop/config/settings.py::INSTALLED_APPS`.
- `verbose_name: "StrOrPromise" = "Django Strawberry Framework"` — Title Case with spaces; matches the `README.md` H1. Diverges from strawberry-django's `"Strawberry django"` because the package's consumer-facing prose uses Title Case; the test plan pins the value.

Documentation (gate-forced, not behavioral): the module docstring (`D100`) and the class docstring `"""Register django-strawberry-framework with Django's app loader."""` (`D101`). Both diverge from strawberry-django's `apps.py`, which has neither, because this repo's pydocstyle gate is stricter.

Deliberately NOT declared:

- `label = "..."` — Django's default `label` is the last segment of `name` (`"django_strawberry_framework"`), unique within any consumer project and identical to the `get_app_config(...)` lookup string. A custom label (e.g. `"dsf"`) would add a second lookup string consumers have to learn. strawberry-django omits it too.
- `default_auto_field = "..."` — see [Decision 5](#decision-5--no-default_auto_field-and-no-models).

### Decision 3 — No public export

`django_strawberry_framework/__init__.py` does not re-export the class; `__all__` does not include it. The class is reachable at `django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig`; consumers never write `from django_strawberry_framework import DjangoStrawberryFrameworkConfig`.

- Django's app loader resolves AppConfigs through their dotted module path, not an `__init__.py` re-export. The class never appears in consumer code other than `INSTALLED_APPS`.
- `tests/base/test_init.py::test_public_api_surface_is_pinned` pins `__all__`; adding a name consumers never `import` would be noise-only API widening.
- strawberry-django does not re-export its `StrawberryDjangoConfig` either.
- The discriminator is whether consumers write the symbol into their own code: [`DjangoListField`][glossary-djangolistfield] IS re-exported by [`spec-020`][spec-020] because consumers write it into their schema modules by hand. The AppConfig is not in that category.

### Decision 4 — `ready()` applies the upstream patches

`DjangoStrawberryFrameworkConfig` overrides `ready()`, and the override does exactly one thing: it dispatches the package's four defensive upstream-patch appliers, in this order — `django_strawberry_framework/_django_patches.py::apply`, `django_strawberry_framework/_strawberry_patches.py::apply`, `django_strawberry_framework/_cross_web_patches.py::apply`, then `django_strawberry_framework/_graphql_core_patches.py::apply` (`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`). The four imports are **function-local**, so importing `django_strawberry_framework.apps` outside Django pulls in no patch module.

One patch module per third-party dependency the package patches (Django, Strawberry, `cross_web`, `graphql-core`); the mechanism as a whole is [Upstream patches][glossary-upstream-patches]. **Each module's own docstring is the single source of truth for which upstream bugs it hardens**; `ready()` repeats none of that inventory, and neither does this Decision.

Every applier self-gates on the `APPLY_UPSTREAM_PATCHES` setting (`django_strawberry_framework/conf.py::upstream_patches_enabled`, default on). `DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": False}` disables all four; the mapping form, keyed by `django`, `strawberry`, `cross_web` and `graphql_core` (e.g. `{"APPLY_UPSTREAM_PATCHES": {"django": False}}`), disables one dependency's patches and leaves the others installed. **The gate lives inside each `apply()`, not in `ready()`** — the dispatcher is unconditional, so a reader of `ready()` sees four unguarded calls and must follow them to `conf.py` for the gate. The placement is deliberate: the gate is per dependency, and a `ready()`-level gate could only be all-or-nothing.

Each `apply()` is idempotent and self-healing, so a repeated `ready()` — some Django test runners fire it more than once — is safe, and a `ready()` fired after a patch module has been reloaded retains the module's true upstream capture and installs the reloaded replacement rather than rejecting the prior replacement as an unsupported upstream change.

`ready()` is the canonical place for one-time setup that depends on Django being fully configured, and it makes the patches free for consumers: `"django_strawberry_framework"` in `INSTALLED_APPS` is the whole contract — no `conftest.py` workaround, no base test class, no settings key.

What `ready()` does NOT do:

- **It does not call [`finalize_django_types`][glossary-finalize-django-types].** `ready()` fires after Django's app registry is populated but **before** the consumer's `config/schema.py` (or equivalent) is necessarily imported, so a `ready()`-side call would either finalize too early (relations from not-yet-imported modules unresolved) or be silently redundant with the consumer's explicit call. The consumer-owned synchronization point in [`docs/README.md`][readme]'s "Schema setup" section makes `ready()` the wrong home.
- **It does not import consumer `DjangoType` modules**, directly or transitively. The dispatch touches only the four private patch modules.
- **It does not install the `conf.py` `setting_changed` receiver.** That wiring is installed at import time; see [Current state](#current-state).
- **It does not register Django system checks, connect signal handlers, or register management commands.** Management commands are discovered by directory convention, and a check validating `DjangoType` declaration invariants needs its own spec.

The negative-shape test of [Test plan](#test-plan) therefore forbids three keys: `label`, `default_auto_field` and `default`. `ready` is required and pinned positively — present and callable in the class body, dispatching all four appliers, safe on a re-fire, and correct across a patch-module reload.

### Decision 5 — No `default_auto_field` and no models

`DjangoStrawberryFrameworkConfig` does NOT declare `default_auto_field`. `default_auto_field` controls the auto PK type for models declared inside the app's package, and `django_strawberry_framework/` declares no `models.py` and no model anywhere in its tree. A card that adds models revisits the attribute. strawberry-django does not declare it either.

### Decision 6 — Joint `0.0.7` cut

`0.0.7` shipped as a bundle per [`spec-020`][spec-020]'s [Decision 10][spec-020-decision-10]: the last `0.0.7` card to ship owns the version bump; this card does not. The release is single-sourced in `django_strawberry_framework/__init__.py`'s `__version__` (hatchling reads it via `pyproject.toml`'s `[tool.hatch.version]`), and `tests/base/test_init.py::test_version` pins it. Each bundled card writes its own line under the shared `[0.0.7]` `### Added` heading in `CHANGELOG.md`.

### Decision 7 — No fakeshop `INSTALLED_APPS` entry change

`examples/fakeshop/config/settings.py::INSTALLED_APPS` declares `"django_strawberry_framework"` (the package name, not the AppConfig dotted path).

- Django's single-AppConfig discovery resolves the package-name form to `DjangoStrawberryFrameworkConfig`.
- The example matches the form [`docs/README.md`][readme] recommends; switching it to the dotted path would advertise the other form.
- The live `/graphql/` tests under `examples/fakeshop/test_query/` run through this entry, so they are end-to-end evidence that the explicit AppConfig works through the package-name string.

### Decision 8 — No `default` attribute

`DjangoStrawberryFrameworkConfig` does NOT declare `default` at all (neither `default = True` nor `default = False`). The negative-shape test asserts `"default" not in DjangoStrawberryFrameworkConfig.__dict__`, which catches any value — symmetric with [Decision 2](#decision-2--name--label--verbose_name-pinning) and [Decision 5](#decision-5--no-default_auto_field-and-no-models), each of which forbids its attribute outright.

- Django resolves a single explicit `AppConfig` subclass in a package's `apps.py` as the default without the marker (the `True` case is redundant).
- `default = False` on the only AppConfig in the package contradicts Django's resolution; forbidding both values keeps the self-defeating shape out.
- The package declares one `AppConfig`, so the disambiguation `default` provides is irrelevant.
- strawberry-django does not declare `default` either.

## Implementation plan

Three slices aligned with the [Slice checklist](#slice-checklist); each maps to one commit.

| Slice | Files | Tests |
| --- | --- | --- |
| 1 — Module + `AppConfig` subclass | `django_strawberry_framework/apps.py` | 0 (tests land in Slice 2) |
| 2 — Tests | `tests/test_apps.py` | 8 test functions (4 positive shape + 1 negative-shape over three forbidden keys + 3 pinning `ready()`), 14 collected items once parametrized; see [Test plan](#test-plan) |
| 3 — Docs | `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md` | 0 |

Slice 2 depends on Slice 1 (the class must exist before tests import it); Slice 3 depends on Slice 2 (the docs describe a shipped, tested module).

## Edge cases and constraints

- **Single-AppConfig discovery.** `pyproject.toml #"Django>=5.2"` pins `Django>=5.2.16`; Django's "a single `AppConfig` subclass in `apps.py` becomes the default" behavior dates from 3.2, well below the floor. No fallback for older Django exists.
- **`INSTALLED_APPS` ordering.** Django calls `ready()` in `INSTALLED_APPS` order. This package's `ready()` installs process-global replacements on upstream classes, reads no other app's state, and every `apply()` is idempotent, so its position in the consumer's `INSTALLED_APPS` is irrelevant.
- **Multiple AppConfigs in `apps.py`.** Only one class is declared. If a second is ever added, an explicit `default = True` on one of them becomes load-bearing, and the same change removes `"default"` from the negative-shape test's forbidden set `{"label", "default_auto_field", "default"}`. Any card declaring a currently-forbidden attribute removes its key from the set in the same change.
- **`django.apps.apps.get_app_config("dsf")` (or any other label shortcut).** Raises `LookupError` — the label is `"django_strawberry_framework"`, with no alias. A drive-by `label = "dsf"` fails the negative-shape test's `label` row.
- **AppConfig instantiation under `pytest-django`.** `pytest-django` runs `django.setup()` once per session, instantiating the AppConfig; `tests/test_apps.py` uses `apps.get_app_config(...)` directly.
- **`AppConfig.ready` runs during `django.setup()`.** The four patch sets are installed before any test row runs, so a test that observes the dispatch must first revert the patched slots to the modules' captured upstream originals and then drive `ready()` itself — asserting "the patches are installed" without that revert asserts nothing about `ready()`, since any earlier direct `apply()` in the session satisfies it. Every perturbed slot is restored in a `finally`: the slots are process-global and leak across the worker's remaining rows otherwise.
- **Importing `django_strawberry_framework.apps` outside Django.** Legal: at runtime the module imports `typing.TYPE_CHECKING`, `django.apps.AppConfig` and `typing_extensions.override` (`django_stubs_ext.StrOrPromise` only under `TYPE_CHECKING`) and defines a class. The four patch-module imports live inside `ready()`.
- **Coverage under `fail_under = 100`.** The class body is two attribute assignments, docstrings and the `ready()` override. The positive tests cover importability, attribute values and registry pickup; the three `ready()` tests cover the dispatch body, including a re-fire and a post-reload fire. The negative-shape test is a class-level assertion, not a body-line one.

## Test plan

Tests live in one tree, matching [`docs/TREE.md`][tree] and [`AGENTS.md`][agents].

### `tests/test_apps.py`

Package tests; system-under-test is `django_strawberry_framework`. The file is the flat module's mirror per [`docs/TREE.md #"## Test layout"`][tree]. Eight test functions, 14 collected items.

Positive shape tests (Slice 2):

- `test_djangostrawberryframeworkconfig_importable_from_apps_module` — the module-level `from django_strawberry_framework.apps import DjangoStrawberryFrameworkConfig` is the load-bearing assertion; a move of the module fails collection.
- `test_djangostrawberryframeworkconfig_is_appconfig_subclass` — `issubclass(DjangoStrawberryFrameworkConfig, django.apps.AppConfig)`.
- `test_djangostrawberryframeworkconfig_pins_name_and_verbose_name` — parametrized over `name == "django_strawberry_framework"` and `verbose_name == "Django Strawberry Framework"` (two items); a cosmetic edit to either fails.
- `test_djangostrawberryframeworkconfig_resolves_through_django_app_registry` — `django.apps.apps.get_app_config("django_strawberry_framework")` returns an instance of `DjangoStrawberryFrameworkConfig`. The load-bearing assertion that Django picked up the explicit class rather than an implicit fallback.

Negative-shape test (Slice 2):

- `test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes` — parametrized over the three forbidden **behavioral** keys (`label`, `default-auto-field`, `default` ids), each asserting `key not in DjangoStrawberryFrameworkConfig.__dict__` with a fail message naming the key and the Decision that forbids it: `label` ([Decision 2](#decision-2--name--label--verbose_name-pinning)), `default_auto_field` ([Decision 5](#decision-5--no-default_auto_field-and-no-models)), `default` ([Decision 8](#decision-8--no-default-attribute)). `"ready"` is deliberately absent — the method is required, and the test's docstring says so, since "no extra AppConfig attributes" is exactly the sentence a later reader would use to justify deleting it. `__doc__` is absent too: documentation is not behavior.

`ready()` tests (Slice 2), per [Decision 4](#decision-4--ready-applies-the-upstream-patches):

- `test_djangostrawberryframeworkconfig_defines_ready_for_django_patches` — `"ready" in DjangoStrawberryFrameworkConfig.__dict__` and it is callable. The cheap structural pin; the behavior is pinned by the next test.
- `test_ready_dispatches_all_four_patch_appliers_and_refires_safely` — reverts enough patched slots to the captured upstream originals that every module's `_patch_is_installed()` reports `False` (`SimpleTestCase._remove_databases_failures`, `BaseView.parse_json` / `parse_query_params`, `DjangoHTTPRequestAdapter.body`, `ExecutionContext.complete_list_value`), asserts all four report not-installed, drives `ready()` through the registered `AppConfig`, and asserts all four are installed; a second `ready()` pins dispatch-layer idempotence. The revert makes it distinguishing: the patch modules' own suites (`tests/test_django_patches.py`, `tests/test_strawberry_patches.py`, `tests/test_cross_web_patches.py`, `tests/test_graphql_core_patches.py`) expect the patches in place via `ready()`, but direct `apply()` calls earlier on the same worker mask those assertions, so a `ready()` that lost a dispatch line would still pass them.
- `test_ready_reinstalls_patches_after_their_modules_reload` — parametrized per patch module (four items). Reloads the module, asserts its captured upstream originals are unchanged, fires `ready()` and asserts all four patches installed; then does it again. The second reload is the one that matters: it reloads a module whose installed replacement is itself the product of the first reload, pinning the capture contract for repeated reloads. Both process-global halves — the module namespace and every patched class slot — are saved and restored together, because restoring only the class attributes would leave them pointing at pre-reload objects while the module holds post-reload ones, making every `_patch_is_installed()` report a spurious `False` for the rest of the worker's run.

No live `/graphql/` test is AppConfig-specific: a live request can show a patched parse is in effect, not that `ready()` was the caller. Request-shaped outcomes of the patches live in `examples/fakeshop/test_query/test_products_api.py` and `examples/fakeshop/test_query/test_transport_api.py` (named in `tests/test_apps.py`'s module docstring). No example-project test either: the system-under-test is the package's AppConfig.

## Doc updates

What each doc carries for this card:

- [`docs/GLOSSARY.md`][glossary] — [`Django AppConfig`][glossary-django-appconfig] is `shipped (0.0.7)` in the entry and the Index table. The body names `name`, `verbose_name`, the four-applier dispatch in order, the function-local imports, the `APPLY_UPSTREAM_PATCHES` gate inside each `apply()`, idempotence, and what `ready()` does not do; it names the dispatch, not the patch inventory.
- [`docs/README.md`][readme] — `## Installation` tells consumers to add `"django_strawberry_framework"` to `INSTALLED_APPS`.
- [`docs/TREE.md`][tree] (rendered from module docstrings) — `apps.py` in `## django_strawberry_framework (current source layout)` and `## django_strawberry_framework (target package layout)`; `test_apps.py` in `## Test layout`.
- [`KANBAN.md`][kanban] — `DONE-021-0.0.7` sits in Done (`KANBAN.md #"DONE-021-0.0.7 - `apps.py` and Django app config"`), its package file `django_strawberry_framework/apps.py`.
- [`CHANGELOG.md`][changelog] — the `[0.0.7]` `### Added` entry for `Django AppConfig` (written under [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told", with this slice as the instruction). It describes the `0.0.7` release, whose `ready()` dispatched the Django applier alone, and stays that way.
- No edits to [`README.md`][readme-root] (its status prose names consumer-facing primitives; the AppConfig is plumbing), [`GOAL.md`][goal] (its showcase does not exercise `INSTALLED_APPS`), or [`TODAY.md`][today] (a query-capability snapshot the AppConfig does not change).

## Out of scope (explicitly tracked elsewhere)

- The upstream patch modules `ready()` dispatches and what each hardens — each module's docstring is the single source of truth; the mechanism is [Upstream patches][glossary-upstream-patches], and the Django half is [`docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md`][spec-024]. This card owns the dispatch site and the `AppConfig` shape around it.
- [Schema export management command][glossary-schema-export-management-command] (`manage.py export_schema`, `DONE-022-0.0.7`): discovered through Django's `management/commands/` directory convention, independent of this AppConfig.
- [Multi-database cooperation][glossary-multi-database-cooperation] (`DONE-023-0.0.7`): lives in `django_strawberry_framework/types/resolvers.py`, not `apps.py`.
- Warning-free scalar registration via `StrawberryConfig.scalar_map` (`DONE-025-0.0.7`): schema-construction shape, not AppConfig surface.
- Django checks for `DjangoType` declaration invariants. Not on the roadmap; a card adding one would extend `ready()` alongside the check.
- Channels ASGI router ([`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]), `DONE-041-0.0.14`.
- [Debug-toolbar middleware][glossary-debug-toolbar-middleware], `DONE-042-0.0.14`.
- Test-client helpers ([`TestClient`][glossary-testclient], [`GraphQLTestCase`][glossary-graphqltestcase]), `DONE-043-0.0.14`.
- [Response-extensions debug middleware][glossary-response-extensions-debug-middleware], `DONE-044-0.0.14`.
- `default_auto_field`: the package ships no Django models. See [Decision 5](#decision-5--no-default_auto_field-and-no-models).

## Definition of done

The card is complete when all of the following are true:

1. `django_strawberry_framework/apps.py` defines `DjangoStrawberryFrameworkConfig(AppConfig)` per [Decision 1](#decision-1--module-location--public-export) and [Decision 2](#decision-2--name--label--verbose_name-pinning) — `name = "django_strawberry_framework"`, `verbose_name = "Django Strawberry Framework"`, a one-line **module docstring** (`D100`), a one-line **class docstring** (`D101`), no `label`, no `default_auto_field`, no `default` at any value.
2. `django_strawberry_framework/__init__.py` does not re-export the class; `__all__` does not include it (per [Decision 3](#decision-3--no-public-export)).
3. `tests/base/test_init.py::test_public_api_surface_is_pinned` pins an `__all__` without the AppConfig (per [Decision 3](#decision-3--no-public-export)).
4. `tests/test_apps.py` contains the 8 test functions in the [Test plan](#test-plan) — 4 positive shape, 1 negative-shape (`test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`) asserting `label`, `default_auto_field` and `default` are absent from `DjangoStrawberryFrameworkConfig.__dict__`, and 3 pinning `ready()`: its presence and callability, its four-applier dispatch plus safe re-fire, and its correctness across a patch-module reload.
5. `examples/fakeshop/config/settings.py::INSTALLED_APPS` keeps the package-name entry (per [Decision 7](#decision-7--no-fakeshop-installed_apps-entry-change)), resolving to the explicit class.
6. The class overrides `ready()` with the four-applier dispatch and nothing else (per [Decision 4](#decision-4--ready-applies-the-upstream-patches)), and does not declare `label`, `default_auto_field`, or `default` (per [Decision 2](#decision-2--name--label--verbose_name-pinning), [Decision 5](#decision-5--no-default_auto_field-and-no-models), [Decision 8](#decision-8--no-default-attribute)). The absences are pinned by the negative-shape test; the `ready()` presence and behavior by the three `ready()` tests, all in `tests/test_apps.py`.
7. The fakeshop live `/graphql/` tests (e.g. `examples/fakeshop/test_query/test_library_api.py`) pass through the existing `INSTALLED_APPS` entry with no AppConfig-specific code.
8. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`).
9. `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, and `CHANGELOG.md` carry the state in [Doc updates](#doc-updates). `README.md`, `GOAL.md`, and `TODAY.md` are not edited.
10. `KANBAN.md` carries `DONE-021-0.0.7` in Done.
11. The version bump is not in this card per [Decision 6](#decision-6--joint-007-cut).
12. Zero new public exports.
13. `uv run ruff check --fix .` and `uv run ruff format .` pass; `uv run pytest --no-cov` passes (coverage enforcement is CI's job per `pyproject.toml [tool.coverage.report] fail_under = 100`).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
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
[build]: ../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[apps]: /Users/riordenweber/projects/strawberry-django-main/strawberry_django/apps.py
