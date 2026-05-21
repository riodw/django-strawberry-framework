# Spec: `apps.py` and Django `AppConfig`

Target release: `0.0.7`.
Status: draft (revision 1, initial).
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`](GLOSSARY.md) (entries [`Django AppConfig`](GLOSSARY.md#django-appconfig), [`finalize_django_types`](GLOSSARY.md#finalize_django_types), [`DjangoType`](GLOSSARY.md#djangotype)), [`KANBAN.md`](../KANBAN.md) card `WIP-ALPHA-017-0.0.7`, predecessor spec [`docs/spec-016-list_field-0_0_7.md`](spec-016-list_field-0_0_7.md) (Decision 10 — joint `0.0.7` cut policy reused verbatim here).

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft. Pins module location (`django_strawberry_framework/apps.py`), AppConfig subclass shape (`DjangoStrawberryFrameworkConfig`, three attributes: `name`, `verbose_name`, no `label` override, no `default_auto_field`), the deliberate omission of `ready()` (no side effects until a shipped feature needs one — matches the `conf.py` posture in [`AGENTS.md`](../AGENTS.md) line 20), test placement at `tests/test_apps.py`, the four-test plan (importable / subclass / attribute pinning / registry pickup), the policy that consumers add the package to `INSTALLED_APPS` by its dotted package name (Django's implicit single-AppConfig discovery handles the rest), the live-fakeshop coverage path (the example project already lists `"django_strawberry_framework"` in `INSTALLED_APPS`; this card lands the explicit `AppConfig` underneath that entry without changing the entry text), the explicit deferral of the version bump to the last `0.0.7` card to ship (per [`spec-016`](spec-016-list_field-0_0_7.md) Decision 10), and the doc-updates list across `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, and `CHANGELOG.md` (no `README.md` / `GOAL.md` / `TODAY.md` updates — the AppConfig is not a consumer-visible surface change in those documents' framing).

## Key glossary references

Skim these [`docs/GLOSSARY.md`](GLOSSARY.md) entries first — they anchor the vocabulary used throughout the spec:

- [`Django AppConfig`](GLOSSARY.md#django-appconfig) — the entry this card flips from `planned for 0.0.7` to `shipped (0.0.7)` in [Slice 3](#slice-3--promotion--docs).
- [`finalize_django_types`](GLOSSARY.md#finalize_django_types) — the consumer-owned synchronization point that resolves pending relations; this card does NOT move that responsibility into `AppConfig.ready()` (see [Decision 4](#decision-4--no-readyhook-in-0_0_7)).
- [`DjangoType`](GLOSSARY.md#djangotype) — the package's primary public surface; consumer modules that declare `DjangoType`s are imported by the consumer's project, not by the `AppConfig` (see [Decision 4](#decision-4--no-readyhook-in-0_0_7)).
- [`ConfigurationError`](GLOSSARY.md#configurationerror) — not raised by anything in this card; mentioned here only so future-spec authors can see that `apps.py` is intentionally validation-free.

Project conventions to follow:

- [`AGENTS.md`](../AGENTS.md) — line 20 ("Add settings keys only when the feature that needs them lands; do not preemptively populate"); test placement at `tests/test_apps.py` per line 6's "tests/ (package tests, system-under-test is django_strawberry_framework itself)" rule paired with [`docs/TREE.md`](TREE.md) line 453's "`tests/test_<module>.py` (flat, at the root) — single-file Layer-3 module tests" mirror rule. **Note:** `AGENTS.md` line 21 prohibits `CHANGELOG.md` edits without explicit permission; [Slice 3](#slice-3--promotion--docs) grants that permission for this card's `[0.0.7]` `### Added` append.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — 100% coverage target.
- [`KANBAN.md`](../KANBAN.md) — card-ID format; column movement at Slice 3.
- [`docs/TREE.md`](TREE.md) — package layout; tests mirror source one-to-one; `apps.py` already appears in the target layout with the `[alpha]` tag (`docs/TREE.md:236`).

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan). Three slices total; this card is smaller than `spec-016` because there is no consumer-resolver dispatch matrix to test and no example-app boilerplate to remove.

- [ ] Slice 1: Module + `AppConfig` subclass
  - [ ] New flat module `django_strawberry_framework/apps.py` (placement decision: see [Decision 1](#decision-1--module-location--public-export)) housing `DjangoStrawberryFrameworkConfig`.
  - [ ] Implement `DjangoStrawberryFrameworkConfig(AppConfig)` with exactly three pieces of state:
    - `name = "django_strawberry_framework"` — Django app-label source; matches the package directory name so `django.apps.apps.get_app_config(...)` resolves through the same string consumers type into `INSTALLED_APPS`.
    - `verbose_name = "Django Strawberry Framework"` — display name in the Django admin's "Sites" / "Apps" listings; matches the `README.md` title.
    - module docstring (one line) naming the AppConfig's purpose ("Django AppConfig — registers the package with Django's app loader so consumers can list it in `INSTALLED_APPS` and Django's check / signal hooks resolve against it.").
  - [ ] Do NOT implement `ready()` (per [Decision 4](#decision-4--no-readyhook-in-0_0_7)); do NOT set `default_auto_field` (per [Decision 5](#decision-5--no-default_auto_field-and-no-models)); do NOT set `label` (per [Decision 2](#decision-2--name--label--verbose_name-pinning)).
  - [ ] Do NOT re-export `DjangoStrawberryFrameworkConfig` from `django_strawberry_framework/__init__.py` (per [Decision 3](#decision-3--no-public-export)). The class is accessible at `django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig` for consumers who want to name it explicitly in `INSTALLED_APPS`, but Django's implicit single-AppConfig discovery means consumers writing `"django_strawberry_framework"` in `INSTALLED_APPS` get the explicit config without naming it.
- [ ] Slice 2: Tests
  - [ ] New test module `tests/test_apps.py` covering the four contracts pinned in [Test plan](#test-plan): importable from `django_strawberry_framework.apps`, subclass of `django.apps.AppConfig`, `name` / `verbose_name` attribute values, and Django registry pickup (`django.apps.apps.get_app_config("django_strawberry_framework")` returns an instance of `DjangoStrawberryFrameworkConfig`).
  - [ ] One negative-shape test: assert `DjangoStrawberryFrameworkConfig` does NOT define `ready()` (pin the no-side-effects contract — see [Decision 4](#decision-4--no-readyhook-in-0_0_7)). The mechanism is `assert "ready" not in DjangoStrawberryFrameworkConfig.__dict__` — checks the class body explicitly, not the inherited `AppConfig.ready` which is always present. If a future card adds a `ready()`, that card's spec updates this test (or replaces it) in the same slice.
- [ ] Slice 3: Promotion + docs
  - [ ] Flip [`Django AppConfig`](GLOSSARY.md#django-appconfig) from `planned for 0.0.7` to `shipped (0.0.7)` in [`docs/GLOSSARY.md`](GLOSSARY.md); update the Index table's status column.
  - [ ] Update [`docs/README.md`](README.md) — move the `Django AppConfig` mention from the "Coming in `0.1.0`" bullet list (if present) and surface it in "Shipped today (`0.0.7`)" with a one-line note that consumers add the package to `INSTALLED_APPS` by its dotted package name.
  - [ ] Update [`docs/TREE.md`](TREE.md) — add `apps.py # AppConfig` to the **current on-disk layout** section under the `django_strawberry_framework/` tree (alphabetical position between `__init__.py` and `conf.py`). Remove the `[alpha]` tag from the existing `apps.py # [alpha] Django AppConfig` line in the **target package layout** section (line `docs/TREE.md:236`); the tag means "lands before `0.1.0`", and the bullet has now landed. Add `tests/test_apps.py` to the current test-tree section under the `tests/` listing.
  - [ ] Update [`KANBAN.md`](../KANBAN.md) — move `WIP-ALPHA-017-0.0.7` to the Done column with the next `DONE-NNN-0.0.7` id; rewrite the body in past tense per the existing Done-column convention.
  - [ ] Update [`CHANGELOG.md`](../CHANGELOG.md) — **append** to the existing `[0.0.7]` `### Added` subsection (do NOT create a second `[0.0.7]` heading per [`spec-016`](spec-016-list_field-0_0_7.md) Decision 10 — every `0.0.7` card under the joint cut appends to the same shared section): `Django AppConfig` — `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` so consumers can list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's check / signal hooks resolve through the package's AppConfig.
  - [ ] No edits to [`README.md`](../README.md), [`GOAL.md`](../GOAL.md), or [`TODAY.md`](../TODAY.md). Justification: the AppConfig is plumbing, not a consumer-visible API surface. `README.md`'s status section names features consumers write code against; `GOAL.md`'s six-file example does not exercise `INSTALLED_APPS`; `TODAY.md`'s capability snapshot is about what GraphQL queries work — none of those framings is touched by the AppConfig landing.
  - [ ] Version bump (deferred to **the last `0.0.7` card to ship**, NOT this card; per [Decision 6](#decision-6--joint-0_0_7-cut)): see [`spec-016`](spec-016-list_field-0_0_7.md) Decision 10. This card does NOT bump `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, or `tests/base/test_init.py`'s version assertion.
  - [ ] Final gates:
    - [ ] `uv run ruff format .` passes.
    - [ ] `uv run ruff check --fix .` passes.
    - [ ] `uv run pytest` passes with 100% package coverage (`fail_under = 100`).
    - [ ] Zero new public exports (the AppConfig is import-time plumbing, not a public symbol); `__all__` in `django_strawberry_framework/__init__.py` is unchanged.

## Problem statement

`django_strawberry_framework` does not ship an [`apps.py`](../django_strawberry_framework/) today. The example project's `examples/fakeshop/config/settings.py:48` already lists `"django_strawberry_framework"` in `INSTALLED_APPS`, and the example runs — but only because Django falls back to an implicit `AppConfig` synthesized from the package name when no explicit `apps.py` is found. That implicit `AppConfig`:

- carries the package's directory name as the `name` and `label`, with the same string as `verbose_name` — capitalized via Django's title-cased default ("Django Strawberry Framework"-ish but driven by Django's heuristic, not by the package),
- cannot be referenced by an explicit dotted path in `INSTALLED_APPS` (consumers who want the canonical Django pattern `"django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig"` cannot type it),
- gives the package no hook for future Django-integration work (a `ready()` site for a check, a signal handler, or — in a future card — schema-export bootstrap).

The asymmetry is small but real: `strawberry_django` ships an [`apps.py`](/Users/riordenweber/projects/strawberry-django-main/strawberry_django/apps.py) (verified to be a four-line `class StrawberryDjangoConfig(AppConfig)` with `name` and `verbose_name`); the upstream `graphene_django` does NOT ship one (verified via `find` against `~/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/` — no `apps.py`). The package's positioning argument in [`README.md`](../README.md) — "feels like `graphene-django` evolved onto a modern engine" — would currently match graphene-django's absence; the package's other half — "Strawberry stays as the engine" — would currently miss the parity with `strawberry-django`. This card ships the AppConfig so the parity is symmetric.

The shipping bar is intentionally low — the AppConfig is two attributes plus a docstring. The discipline the card needs to enforce is **what NOT to put in it**: no `ready()` body, no preemptive settings, no eager imports of `DjangoType` modules, no auto-call to [`finalize_django_types`](GLOSSARY.md#finalize_django_types). Each of those is a future-spec home (or, for `finalize_django_types`, an explicit anti-pattern — the consumer owns the synchronization point per [`docs/README.md`](README.md)'s "Schema setup boundary" section).

## Current state

- `django_strawberry_framework/` ships the modules listed in [`docs/TREE.md`](TREE.md) lines 188-224 (`__init__.py`, `conf.py`, `exceptions.py`, `list_field.py`, `registry.py`, `scalars.py`, the `optimizer/`, `types/`, and `utils/` subpackages) and `py.typed`. There is no `apps.py` on disk today; the target layout at `docs/TREE.md:236` lists `apps.py # [alpha] Django AppConfig` with the `[alpha]` tag meaning "lands before `0.1.0`".
- `django_strawberry_framework/conf.py` ships the `DJANGO_STRAWBERRY_FRAMEWORK` settings reader. It documents (in its module docstring lines 163-168) that `setting_changed` signal wiring is installed at **import time**, NOT in `AppConfig.ready()`, because "consumers may import `conf` before app loading during test bootstrap, so AppConfig.ready() is not a viable home for this wiring." Slice 1's `AppConfig` therefore has no settings-related wiring to subsume — the signal hook is intentionally outside `ready()` and stays there.
- `examples/fakeshop/config/settings.py:48` already declares `"django_strawberry_framework"` in `INSTALLED_APPS`. Django currently synthesizes an implicit `AppConfig` because no `apps.py` is found. Once Slice 1 lands, Django picks up the explicit `DjangoStrawberryFrameworkConfig` automatically (the implicit fallback applies only when no `AppConfig` subclass is defined in the package; Django 3.2+ resolves a single explicit AppConfig as the default without requiring `default = True`).
- `tests/base/test_init.py:35-44` pins the package's `__all__` tuple. The AppConfig is NOT a public export (see [Decision 3](#decision-3--no-public-export)); this assertion stays unchanged in `0.0.7`.
- `tests/test_list_field.py` is the existing model for a flat single-file Layer-3 module's test home. `tests/test_apps.py` follows the same convention per [`docs/TREE.md:453`](TREE.md).
- `examples/fakeshop/test_query/test_library_api.py` exercises the live `/graphql/` endpoint with the package installed via `INSTALLED_APPS`. The test suite already proves the implicit `AppConfig` works end-to-end; once Slice 1 lands, the same tests exercise the explicit `AppConfig` without code changes (the test file imports `from django.test import Client` and posts JSON to `/graphql/`, which has no AppConfig-specific assertions).
- `WIP-ALPHA-017-0.0.7`'s `KANBAN.md` card body (lines 78-88) is intentionally sparse — three Definition-of-done bullets and no "Why it matters" narrative. The narrative this spec carries (parity with `strawberry-django`, asymmetry with `graphene-django`, future-card seam) is fleshed out here so the spec can stand on its own.

## Goals

1. Ship `django_strawberry_framework/apps.py` containing `DjangoStrawberryFrameworkConfig(AppConfig)` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`. Two attributes plus a one-line module docstring; nothing else.
2. Ship `tests/test_apps.py` containing the four-test plan in [Test plan](#test-plan) — importability, subclass, attribute pinning, Django registry pickup — plus the one negative-shape test asserting `ready()` is NOT defined on the class.
3. Preserve [`AGENTS.md`](../AGENTS.md) line 20's "Add settings keys only when the feature that needs them lands; do not preemptively populate" by omitting `ready()`, `default_auto_field`, and any signal / check / management-command wiring. Future cards add what they need; this card adds the bare AppConfig.
4. Preserve the consumer's import order — the AppConfig must NOT eagerly import `DjangoType` modules or call [`finalize_django_types`](GLOSSARY.md#finalize_django_types). The synchronization-point contract documented in [`docs/README.md`](README.md)'s "Schema setup boundary" stays with the consumer.
5. Keep `__all__` unchanged. The AppConfig is import-time plumbing; consumers reach it via Django's app-loader machinery, not via `from django_strawberry_framework import ...`.

## Non-goals

- `ready()` body — checks, signals, management-command auto-registration, or `finalize_django_types` invocation. See [Decision 4](#decision-4--no-readyhook-in-0_0_7).
- A `default_auto_field` declaration. The package ships zero Django models; the attribute is meaningless here. See [Decision 5](#decision-5--no-default_auto_field-and-no-models).
- Auto-invocation of [`finalize_django_types`](GLOSSARY.md#finalize_django_types) from `AppConfig.ready()`. The consumer's `config/schema.py` (or equivalent) owns the call; `ready()` fires before the consumer's schema module is necessarily imported, so a `ready()`-side call would either finalize too early (relations from yet-to-import modules unresolved) or be silently ineffective.
- A re-export of `DjangoStrawberryFrameworkConfig` from `django_strawberry_framework/__init__.py`. Django's app-loader resolves the class through its dotted module path; consumers never write `from django_strawberry_framework import DjangoStrawberryFrameworkConfig`. See [Decision 3](#decision-3--no-public-export).
- A custom `label` shorter than `"django_strawberry_framework"`. The Django default (the last segment of `name`) is already unique. See [Decision 2](#decision-2--name--label--verbose_name-pinning).
- A bootstrap helper for `DJANGO_STRAWBERRY_FRAMEWORK` settings defaults. `conf.py` already handles missing-key and `None` cases; no `ready()`-side initialization is needed. AGENTS.md line 20 explicitly forbids preemptive settings.
- A Django management command surface. Tracked under `WIP-ALPHA-018-0.0.7` (the `export_schema` command), which has its own `management/commands/export_schema.py` module and does NOT need this card's AppConfig to do any wiring (Django discovers management commands by directory convention, not by AppConfig method).
- An update to `examples/fakeshop/config/settings.py:48`'s `INSTALLED_APPS` entry — current text is `"django_strawberry_framework"` (the dotted package name). Django's implicit single-AppConfig discovery means this entry continues to work unchanged; no need to tighten to `"django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig"`. See [Decision 7](#decision-7--no-fakeshop-installed_apps-entry-change).

## Borrowing posture

The two reference packages at the paths given in [`docs/TREE.md`](TREE.md) take opposite stances on shipping an `apps.py`. The slice borrows the shape from the one that ships it.

### From `strawberry_django` — borrow the AppConfig shape verbatim

Local source path: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/apps.py` (referenced from [`docs/TREE.md:78-158`](TREE.md)).

Verified contents (four lines plus blank):

```python
from django.apps import AppConfig


class StrawberryDjangoConfig(AppConfig):
    name = "strawberry_django"
    verbose_name = "Strawberry django"
```

- **AppConfig subclass with two attributes.** Same shape adopted here: `name` (the package directory) and `verbose_name` (a human-readable label). Justification: strawberry-django's shape is the minimal Django-correct surface for an installable package; the upstream has shipped this for years without needing more. Borrowing the shape verbatim avoids inventing complexity that the ecosystem has not asked for.
- **No `ready()`.** strawberry-django does not implement one; we do not either. Justification: `ready()` is the place where Django expects side effects (signal connections, model checks); strawberry-django has none that need `ready()`, and neither does this package at `0.0.7`. AGENTS.md line 20 makes this explicit on the settings side; the same posture applies to AppConfig hooks.
- **No `default_auto_field`.** strawberry-django does not declare one; neither do we. Justification: both packages ship zero Django models; the attribute is irrelevant.

### From `graphene_django` — explicitly do not borrow the absence

Local source path: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/` (referenced from [`docs/TREE.md:13-76`](TREE.md)).

- **graphene-django ships NO `apps.py`** (verified by `find … -name apps.py` over the installed package directory; no result). Consumers add `"graphene_django"` to `INSTALLED_APPS` and rely on Django's implicit AppConfig fallback.
- **We do not borrow this.** Justification: graphene-django's implicit-only stance is a historical artifact of the package predating Django 3.2's AppConfig-discovery improvements. Modern Django convention is to ship an explicit `AppConfig`; the parity story consumers expect coming from `strawberry-django` is on the explicit-AppConfig side; and the future-card seam (a `ready()` site reserved for later cards) only opens with an explicit class.

### Explicitly do not borrow

- strawberry-django's broader `apps/` / `extensions/` / `middleware/` structure that surrounds its `apps.py`. We ship just the AppConfig in `0.0.7`; the surrounding modules land card-by-card under their own specs ([`KANBAN.md`](../KANBAN.md) — `TODO-ALPHA-029` debug-toolbar, etc.).
- Any `verbose_name` translation infrastructure (`from django.utils.translation import gettext_lazy as _`). strawberry-django does not localize its string; we do not either. Translation is a separate concern; deferring it costs nothing.
- Django's `default = True` class attribute. Django 3.2+ resolves a single explicit AppConfig in a package as the default without the marker; declaring it would be redundant. See [Decision 8](#decision-8--no-default--true-marker).

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

Django's app loader scans `django_strawberry_framework/apps.py`, finds exactly one `AppConfig` subclass (`DjangoStrawberryFrameworkConfig`), and uses it as the package's `AppConfig` automatically. No change to consumer code is required compared to the implicit-AppConfig behavior they had under `0.0.6`; the explicit class is what changes.

### Explicit dotted path (optional, equivalent)

Consumers who prefer to be explicit can name the AppConfig directly:

```python path=null start=null
INSTALLED_APPS = [
    "django.contrib.admin",
    # ...
    "django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig",
]
```

Equivalent to the package-name form above. The package documentation recommends the package-name form in [`docs/README.md`](README.md) for brevity, but both work.

### `django.apps.apps.get_app_config("django_strawberry_framework")`

After Django finishes app-loading, the AppConfig is reachable through Django's registry under the `name` value `"django_strawberry_framework"`:

```python path=null start=null
from django.apps import apps

config = apps.get_app_config("django_strawberry_framework")
# -> <DjangoStrawberryFrameworkConfig: django_strawberry_framework>
config.verbose_name
# -> "Django Strawberry Framework"
```

This is the path future cards will use when they need to attach behavior to the package's AppConfig (e.g., the schema-export management command in `WIP-ALPHA-018-0.0.7` could resolve here, though Django's command discovery does not require it). Pinning the resolution path now means future cards do not have to re-litigate the lookup string.

## Architectural decisions

### Decision 1 — Module location & public export

**Module location.** `DjangoStrawberryFrameworkConfig` lives in **`django_strawberry_framework/apps.py`** (new flat single-file module at the package root, matching the [`docs/TREE.md`](TREE.md) target layout at line 236).

Justification:

- The card's KANBAN body (lines 78-88) names `django_strawberry_framework/apps.py` as the single new source file.
- [`docs/TREE.md:236`](TREE.md) already reserves this path with the `[alpha]` tag — Slice 3 removes the tag once the file lands.
- Django's app-loader expects `apps.py` at the package root by convention. Putting it anywhere else (`apps/config.py`, `_apps.py`, etc.) breaks the convention without benefit.

**Public-export surface.** `django_strawberry_framework/__init__.py` is NOT modified. See [Decision 3](#decision-3--no-public-export).

Alternatives considered (and rejected):

- **`django_strawberry_framework/django/apps.py` mimicking `strawberry/django/apps.py`'s nested shape.** Rejected: the `strawberry/django/` nesting reflects Strawberry's broader package layout where Django integration is one of many transport / adapter targets. This package's entire purpose is Django integration; an extra `django/` subdirectory would be redundant.
- **A `django_strawberry_framework/apps/__init__.py` subpackage.** Rejected: a single AppConfig class does not need a subpackage. [`docs/TREE.md:230`](TREE.md) reserves subpackages for Layer-3 subsystems with three-plus modules.

### Decision 2 — `name` / `label` / `verbose_name` pinning

The class declares exactly two attributes plus its inherited base behavior:

- `name = "django_strawberry_framework"` — matches the package directory; matches the `INSTALLED_APPS` entry consumers already type; matches the string `examples/fakeshop/config/settings.py:48` already declares.
- `verbose_name = "Django Strawberry Framework"` — Title Case with spaces; matches the `README.md` H1; matches the human-readable form a consumer would type if asked "what is this package called?".

Deliberately NOT declared:

- `label = "..."` — Django's default `label` is the last segment of `name` (here, `"django_strawberry_framework"`). The default is unique within any conceivable consumer project and matches the lookup string in `django.apps.apps.get_app_config(...)`. Declaring a custom `label` (e.g., `"dsf"`) would (a) introduce a second lookup string consumers have to learn, and (b) silently invalidate any future `manage.py` command that the package or a third party writes against the `django_strawberry_framework` label. Symmetric with strawberry-django's choice to omit `label`.
- `default_auto_field = "..."` — see [Decision 5](#decision-5--no-default_auto_field-and-no-models).

Justification:

- Three pieces of state is the entire surface strawberry-django ships; the borrowing posture is to match that surface.
- Every attribute the spec adds is one the test plan has to pin; every attribute that doesn't ship is one the spec doesn't have to defend.
- The `verbose_name` value diverges from strawberry-django's `"Strawberry django"` (lowercase second word) because the `README.md` and consumer-facing prose uses Title Case throughout. The string is cosmetic and would be the source of a future cosmetic fix if we got it wrong; the test plan pins it so the choice is durable.

Alternatives considered (and rejected):

- **`verbose_name = "django-strawberry-framework"` (kebab-case to match the PyPI distribution name).** Rejected: the Django admin's "Apps" listing renders the `verbose_name` directly; kebab-case is unergonomic for a UI string.
- **`verbose_name = _("Django Strawberry Framework")` with `gettext_lazy`.** Rejected: the package does not declare a translation surface; adding `gettext_lazy` here would pull `django.utils.translation` into the import graph for no benefit. If the package ever exposes localized strings, a follow-up card does this consistently across every site.
- **Add a `label = "dsf"` shortcut.** Rejected: aliasing is gratuitous when the default is already unique; consumers benefit from the longer label matching the package name 1:1 (no "wait, what's the label vs the name?" friction).

### Decision 3 — No public export

`django_strawberry_framework/__init__.py` is NOT modified. The class is reachable at the dotted path `django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig`; consumers never write `from django_strawberry_framework import DjangoStrawberryFrameworkConfig`.

Justification:

- Django's app-loader resolves AppConfigs through their dotted module path, not through any `__init__.py` re-export. The class never appears in consumer code that isn't `INSTALLED_APPS`.
- `tests/base/test_init.py:35-44` pins `__all__`; adding a name to `__all__` for something consumers never `import` would be a noise-only API widening.
- Symmetric with strawberry-django, which also does not re-export its `StrawberryDjangoConfig`.

Alternatives considered (and rejected):

- **Re-export anyway for consistency with other `0.0.7` cards.** Rejected: spec-016's [`DjangoListField`](GLOSSARY.md#djangolistfield) is re-exported because consumers `import` it directly into their schema code; the AppConfig is not in that category.
- **Re-export under a friendlier name like `Config`.** Rejected: a top-level `Config` symbol in a Django GraphQL framework would be ambiguous with a dozen other "Config" concepts (Django settings, Strawberry config, etc.).

### Decision 4 — No `ready()` hook in `0.0.7`

`DjangoStrawberryFrameworkConfig.__dict__` MUST NOT contain a `ready` key. The class inherits `AppConfig.ready` (a no-op on the base) and does not override it.

Justification:

- [`AGENTS.md`](../AGENTS.md) line 20 — "Add settings keys only when the feature that needs them lands; do not preemptively populate" — generalizes naturally to AppConfig hooks. There is no shipped feature in `0.0.7` that needs a `ready()` body.
- `finalize_django_types` is the only obvious candidate for a `ready()`-side call, and the consumer-owned synchronization-point contract documented in [`docs/README.md`](README.md)'s "Schema setup boundary" section makes that explicitly the wrong place for it. `ready()` fires after Django's app registry is populated but **before** the consumer's `config/schema.py` (or equivalent) is necessarily imported; calling `finalize_django_types` from `ready()` would either finalize too early (relations from not-yet-imported modules unresolved → `ConfigurationError`) or — if Django happened to import the schema module first via signal cascades — be silently redundant with the consumer's explicit call. Both shapes are footguns.
- The `conf.py` signal-receiver hookup is **already** outside `ready()` and the module docstring (lines 163-168) documents the rationale: "consumers may import `conf` before app loading during test bootstrap, so AppConfig.ready() is not a viable home for this wiring." The settings-side anti-pattern is pinned; the same logic applies here.
- Future cards that need `ready()` (e.g., a Django check that validates a `DjangoType` declaration constraint, a signal handler for model deletion that flushes a registry cache) add the hook in the same change as the feature that needs it. The Slice 2 negative test (`assert "ready" not in DjangoStrawberryFrameworkConfig.__dict__`) pins this so a `ready()` cannot creep in without a card-and-spec authorizing it.

The negative-shape test is the load-bearing part of this Decision; without it, a future drive-by edit could add `def ready(self): pass` (a "harmless" placeholder) and the package would silently develop a side-effect surface no card sanctioned.

Alternatives considered (and rejected):

- **Define `ready()` as an explicit `pass` body for "future flexibility."** Rejected: `pass`-body methods are the canonical anti-pattern AGENTS.md line 20 warns against. Future cards add the body when they need it; until then, the inherited no-op is fine.
- **Define `ready()` to call `finalize_django_types()`.** Rejected: contradicts the documented synchronization-point contract; would break consumers whose `config/schema.py` imports relation modules in a different order than Django's app loader does.
- **Define `ready()` to register a `django.core.checks` check that validates `DjangoType` declarations.** Rejected: even if a useful check existed, this card is not the home for it. The check has its own design surface (what does it warn about? what's the error message? does it gate `manage.py runserver`?) that needs its own spec.

### Decision 5 — No `default_auto_field` and no models

`DjangoStrawberryFrameworkConfig` does NOT declare `default_auto_field`. The package ships zero Django models; the attribute is meaningless.

Justification:

- `default_auto_field` controls the auto PK type for models declared *inside* the AppConfig's package. `django_strawberry_framework/` declares no `models.py`; no model anywhere in the package directory tree.
- Future cards that add models (none on the current roadmap; `BACKLOG.md` does not propose any either) would revisit this attribute alongside that decision.
- Symmetric with strawberry-django, which also does not declare it.

### Decision 6 — Joint `0.0.7` cut

`0.0.7` ships four WIP cards as a bundle per [`spec-016`](spec-016-list_field-0_0_7.md) Decision 10 (excluding the already-shipped `DONE-016-0.0.7`): `WIP-ALPHA-017-0.0.7` (this card), `WIP-ALPHA-018-0.0.7` (schema-export management command), `WIP-ALPHA-019-0.0.7` (multi-db cooperation contract), and `WIP-ALPHA-045-0.0.7` (warning-free scalar registration). The version bump in `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__` line, and `tests/base/test_init.py`'s pinned version assertion is owned by whichever card ships last in the bundle, NOT this card.

Justification:

- Restates [`spec-016`](spec-016-list_field-0_0_7.md) Decision 10 verbatim so this card's reader does not have to chase the cross-spec reference.
- Per [`KANBAN.md`](../KANBAN.md) line 50: "The last `0.0.7` card to ship owns the version bump from `0.0.6` per Decision 10 of `docs/spec-016-list_field-0_0_7.md`." The cross-card policy is already pinned in the KANBAN; this Decision pulls it into the spec so Slice 3's checklist can reference it.
- The CHANGELOG `[0.0.7]` `### Added` entries accumulate across the four remaining cards' Slice 3-equivalents; each card writes its own Added line under the same `[0.0.7]` heading.

The Slice 3 doc-updates list explicitly excludes the version bump.

Alternatives considered (and rejected):

- **This card bumps `0.0.7` because it ships earlier than 018/019/045.** Rejected: ship order is determined by which card a maintainer picks up next, not by card NNN; pinning the bump to a specific card creates a sequencing constraint that has no engineering justification.
- **Add a separate `TODO-ALPHA-XXX-0.0.7 — 0.0.7 release cut` card to KANBAN that owns the bump.** Rejected: out of scope for this spec (the spec's boundary forbids editing `KANBAN.md` outside the column move in Slice 3); the "last card to ship" policy is workable as-is.

### Decision 7 — No fakeshop `INSTALLED_APPS` entry change

`examples/fakeshop/config/settings.py:48` currently declares `"django_strawberry_framework"` (the dotted package name, not the AppConfig dotted path). Slice 1 does NOT change this entry.

Justification:

- Django's implicit single-AppConfig discovery (Django 3.2+) resolves the package-name form to the explicit `DjangoStrawberryFrameworkConfig` automatically once `apps.py` ships.
- Changing the fakeshop entry to `"django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig"` would (a) churn a settings file that has no other reason to change in this slice, and (b) advertise the explicit-dotted-path form as the recommended one — but the User-facing API section recommends the package-name form for brevity, and the example should match the recommendation.
- The existing live `/graphql/` HTTP tests in `examples/fakeshop/test_query/test_library_api.py` continue to exercise the package's `INSTALLED_APPS` path; once `apps.py` lands, those tests are the end-to-end evidence that the explicit AppConfig works through the same entry string the implicit one did.

Alternatives considered (and rejected):

- **Switch fakeshop to the dotted-path form to demonstrate the explicit pattern.** Rejected per the rationale above; the spec User-facing API already mentions the dotted-path form as an equivalent option, which is enough documentation. Cluttering the example settings is unnecessary.
- **Add a new test in `examples/fakeshop/tests/` that asserts the resolved AppConfig is `DjangoStrawberryFrameworkConfig`.** Rejected: the assertion belongs in `tests/test_apps.py` (package-internal, system-under-test is the package itself). An example-project test would be a coverage detour through fakeshop's Django machinery when the package's own test can pin the contract directly.

### Decision 8 — No `default = True` marker

`DjangoStrawberryFrameworkConfig` does NOT set `default = True`.

Justification:

- Django 3.2+ resolves a single explicit `AppConfig` subclass in a package's `apps.py` as the default automatically, without requiring the marker.
- The package will only ever declare one `AppConfig` (there is no use case for two within the same package directory), so the disambiguation that `default = True` provides is irrelevant.
- Symmetric with strawberry-django, which does not set the marker either.

Alternatives considered (and rejected):

- **Set `default = True` defensively in case a future Django version changes the implicit-default behavior.** Rejected: Django's `AppConfig` discovery rules have been stable since 3.2 (2021) and Django's deprecation policy would announce any change with multi-version warning. Defending against an unannounced change is over-engineering.

## Implementation plan

The slice ships as **three slices** aligned with the [Slice checklist](#slice-checklist). Each slice maps to one commit; squashing all three into a single PR is acceptable given the small surface.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — Module + `AppConfig` subclass | `django_strawberry_framework/apps.py` (new) | 0 (tests land in Slice 2) | `+10 / -0` |
| 2 — Tests | `tests/test_apps.py` (new) | 5 (4 positive + 1 negative-shape; see [Test plan](#test-plan)) | `+60 / -0` |
| 3 — Promotion + docs | `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md` | 0 | `+25 / -8` |

Total expected delta: ~95 lines across the three slices.

The three slices must be authored in order. Slice 2 depends on Slice 1 (the class must exist before tests can import it); Slice 3 depends on Slice 2 (the CHANGELOG `### Added` line and `KANBAN.md` Done body must describe a shipped, tested module, not a half-landed one).

## Edge cases and constraints

- **Django 3.2+ AppConfig discovery.** The package's `pyproject.toml` already pins `Django >= 4.2` (verified via the install path resolving to a `Django 4.2+` venv); Django's "explicit single AppConfig becomes the default" behavior has been in place since 3.2. The spec assumes this and does not include a fallback for older Django versions.
- **`INSTALLED_APPS` ordering.** Django processes `INSTALLED_APPS` top-to-bottom for `ready()` dispatch. Because this card adds no `ready()` body, ordering relative to other apps in the consumer's `INSTALLED_APPS` is irrelevant; any position works.
- **Multiple AppConfigs in `apps.py`.** Not a concern in `0.0.7` (only one class is declared) but worth noting for future cards: if a second AppConfig is ever added (for some reason), the explicit `default = True` marker becomes load-bearing. Future-card-author beware.
- **`django.apps.apps.get_app_config("dsf")` (or any other label shortcut).** Returns `LookupError` — the resolution string is `"django_strawberry_framework"` (the value of `name` / `label`), not an alias. Pinned in the test plan so a future drive-by `label = "dsf"` edit fails the test.
- **AppConfig instantiation under `pytest-django`.** `pytest-django` sets up Django's app registry once per session via `django.setup()`; the AppConfig is instantiated as part of that bootstrap. Tests in `tests/test_apps.py` can rely on the registry being populated and use `apps.get_app_config(...)` directly.
- **`AppConfig.ready` is called during `django.setup()`.** Because this card defines no `ready()`, Django's inherited no-op runs and the test session proceeds. No timing concerns.
- **Re-importing `django_strawberry_framework.apps` outside Django.** A pure-Python `import django_strawberry_framework.apps` is legal — the module just defines a class. `django.apps.AppConfig` is the only Django dependency (already present because the package's other modules import Django ORM types). No new dependency surface.
- **Coverage of the AppConfig under `fail_under = 100`.** The class body has two attribute assignments and a docstring; the test plan's importability + attribute pinning + registry pickup covers every line. The negative-shape test (`"ready" not in __dict__`) is a class-level assertion, not a body-line coverage assertion, so the class body's coverage is earned by the four positive tests.

## Test plan

Tests live in one tree, matching the rules in [`docs/TREE.md`](TREE.md) and [`AGENTS.md`](../AGENTS.md). Test-tree placement is mandatory.

### `tests/test_apps.py` (new)

Package tests; system-under-test is `django_strawberry_framework`. The file is the flat single-file module's mirror per [`docs/TREE.md:453`](TREE.md).

Positive tests (Slice 2):

- `test_djangostrawberryframeworkconfig_importable_from_apps_module` — `from django_strawberry_framework.apps import DjangoStrawberryFrameworkConfig` resolves without `ImportError`. Pins the module path so a future move to `django_strawberry_framework/django/apps.py` or similar fails this test (and is caught before merging).
- `test_djangostrawberryframeworkconfig_is_appconfig_subclass` — `issubclass(DjangoStrawberryFrameworkConfig, django.apps.AppConfig)` is `True`. Pins the inheritance so a refactor that accidentally inherits from a different base (e.g., `django.apps.config.AppConfig` via direct import, or a custom intermediate) is caught.
- `test_djangostrawberryframeworkconfig_pins_name_and_verbose_name` — asserts `DjangoStrawberryFrameworkConfig.name == "django_strawberry_framework"` and `DjangoStrawberryFrameworkConfig.verbose_name == "Django Strawberry Framework"`. Pins both attribute values; a cosmetic edit to either is caught at test time.
- `test_djangostrawberryframeworkconfig_resolves_through_django_app_registry` — calls `django.apps.apps.get_app_config("django_strawberry_framework")` and asserts the returned instance `isinstance(...)` of `DjangoStrawberryFrameworkConfig`. This is the load-bearing assertion that Django actually picked up the explicit class (not the implicit fallback). Without this test, the explicit AppConfig could silently fail to register and the implicit one could stand in.

Negative-shape test (Slice 2):

- `test_djangostrawberryframeworkconfig_does_not_define_ready` — `assert "ready" not in DjangoStrawberryFrameworkConfig.__dict__`. Pins the no-`ready()` contract from [Decision 4](#decision-4--no-readyhook-in-0_0_7). If a future drive-by edit adds `def ready(self): pass`, this test fails and the edit is caught before merge. The Decision 4 body documents the rationale; this test documents the enforcement mechanism.

No live `/graphql/` HTTP test is required. The `examples/fakeshop/test_query/test_library_api.py` suite already exercises the package through `INSTALLED_APPS` end-to-end; once `apps.py` lands, those tests continue to pass through the explicit AppConfig with zero modifications. Adding an HTTP test specifically for the AppConfig would be a coverage detour — the AppConfig's job is to register; the registry test above pins that contract directly.

No example-project test is required either. The system-under-test is the package's AppConfig; the package-internal test home is canonical.

## Doc updates

- [`docs/GLOSSARY.md`](GLOSSARY.md)
  - Flip [`Django AppConfig`](GLOSSARY.md#django-appconfig) from `planned for 0.0.7` to `shipped (0.0.7)`.
  - Update the entry body to describe the shipped contract: `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`; no `ready()` body in `0.0.7`; consumers list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's implicit single-AppConfig discovery resolves the explicit class.
  - Update the Index table's status column for the row at line 52.

- [`docs/README.md`](README.md)
  - Add a bullet to the "Shipped today (`0.0.7`)" list under "Today and coming next" (the list lives in lines 90-104 of the current state): "`Django AppConfig` — `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` so consumers can list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's check / signal hooks resolve through it (new in `0.0.7`)."
  - Remove "Channels ASGI router, debug-toolbar middleware, test client helper, response-extensions debug, schema export management command, Django `AppConfig`" from the "Coming in `0.1.0`" bullet IF the bullet currently includes "Django `AppConfig`" (verify against the current file at edit time; the current text at line 112 lumps the AppConfig in with the post-`0.0.7` plumbing). After this card and `WIP-ALPHA-018-0.0.7` ship, both the AppConfig and the schema-export command come out of that bullet; the bullet's remaining items stay.

- [`docs/TREE.md`](TREE.md)
  - Add `apps.py # AppConfig` to the **current on-disk layout** section under the `django_strawberry_framework/` tree (lines 192-224 of the current file). Alphabetical position: between `__init__.py` and `conf.py`.
  - Remove the `[alpha]` tag from the existing `apps.py # [alpha] Django AppConfig` line in the **target package layout** section (line 236) — the tag means "lands before `0.1.0`", and the bullet has now landed.
  - Add `tests/test_apps.py` to the current test-tree section (lines 329-360 of the current file). Position: between `test_list_field.py` and `test_registry.py` (alphabetical).

- [`KANBAN.md`](../KANBAN.md)
  - Move `WIP-ALPHA-017-0.0.7` to the Done column with the next available `DONE-NNN-0.0.7` id (the column-move pass renumbers as usual; the next available id is determined at merge time, not pinned in this spec). The past-tense Done body summarizes the shipped scope: "Shipped `django_strawberry_framework/apps.py` containing `DjangoStrawberryFrameworkConfig(AppConfig)` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`; no `ready()` body in `0.0.7` (deferred to the card that needs one); package-internal tests at `tests/test_apps.py`."
  - Update the `### In progress` summary paragraph (line 50) to remove `WIP-ALPHA-017-0.0.7` from the remaining-cards list once this card moves to Done.

- [`CHANGELOG.md`](../CHANGELOG.md)
  - **Append** to the existing `[0.0.7]` `### Added` subsection (do NOT create a second `[0.0.7]` heading — the repo's `CHANGELOG.md` already has a `[0.0.7]` section from `DONE-016-0.0.7` and other prior `0.0.7` commits; every `0.0.7` card under the joint cut appends to the same shared section per [Decision 6](#decision-6--joint-0_0_7-cut)): `Django AppConfig` — `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`. Consumers list `"django_strawberry_framework"` in `INSTALLED_APPS`; Django's check / signal hooks resolve through the package's AppConfig. No `ready()` body in `0.0.7`.
  - The version bump entry is owned by **the last `0.0.7` card to ship** per [Decision 6](#decision-6--joint-0_0_7-cut), NOT this slice.
  - [`AGENTS.md`](../AGENTS.md) line 21 ("Do not update CHANGELOG.md unless explicitly instructed") — this Slice 3 bullet is the explicit instruction.

- No edits to [`README.md`](../README.md). Justification: the README's status section is consumer-prose ("public names are stable; correctness and edge-case behavior are still hardening"); the AppConfig is plumbing, not a consumer-name surface change. The features the README does name (`DjangoListField`, the optimizer, `DjangoType`) are the user-facing primitives; the AppConfig is the registration plumbing underneath. If a future maintainer disagrees, the change is one-line and can be added later without revising this spec.

- No edits to [`GOAL.md`](../GOAL.md). Justification: `GOAL.md`'s `astronomy` showcase walks through model definitions, schema, filters, orders, aggregates, fieldsets — none of which exercises `INSTALLED_APPS` directly. The example project does declare `INSTALLED_APPS`, but `GOAL.md` is the framing document, not the example.

- No edits to [`TODAY.md`](../TODAY.md). Justification: `TODAY.md` is a query-shape-and-capability snapshot ("what GraphQL queries work in fakeshop today?"). The AppConfig is not a query-shape change; the fakeshop schema is unchanged by this card.

## Risks and open questions

Each item names a preferred answer for `0.0.7` and a fallback if implementation reveals the preferred answer is wrong.

- **Django's implicit single-AppConfig discovery edge cases.** Preferred answer: Django 3.2+'s "exactly one `AppConfig` subclass in `apps.py` becomes the default" behavior is stable; the consumer's `INSTALLED_APPS` entry `"django_strawberry_framework"` resolves to `DjangoStrawberryFrameworkConfig` without any further declaration. Fallback: if a real-world Django configuration is found where the discovery silently picks a different class (e.g., a consumer who installs both this package and a fork in the same project, with overlapping app names), document the explicit-dotted-path form (`"django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig"`) as the disambiguation recipe in `docs/README.md`. The User-facing API section already names this form as an equivalent option, so the fallback is already documented; the risk is purely whether the package-name form continues to work as the recommended shape.
- **`verbose_name` cosmetic drift.** Preferred answer: `"Django Strawberry Framework"` matches the `README.md` H1 and is pinned by `test_djangostrawberryframeworkconfig_pins_name_and_verbose_name`. Fallback: if a future rebrand changes the project's display name (unlikely on the road to `1.0.0`), the test and the AppConfig change in the same edit; nothing in the package's public surface depends on the verbose_name string.
- **Future-card `ready()` body adoption.** Preferred answer: no card needs `ready()` in the current roadmap; the no-`ready()` test stays. Fallback: when a future card needs `ready()` (e.g., a check that warns when `DjangoType`s are declared after `finalize_django_types()` and surfaces it through `manage.py check`), the negative-shape test in `tests/test_apps.py` is updated or replaced in that card's spec. The pattern: a card adding `ready()` removes the `"ready" not in __dict__` assertion AND adds a positive test for whatever the new `ready()` body does. Both edits are in the same change.
- **Last-card-to-ship version bump policy.** Preferred answer: the last of the four remaining `0.0.7` WIP cards (017, 018, 019, 045) to merge owns the bump, per [`spec-016`](spec-016-list_field-0_0_7.md) Decision 10. Fallback: identical to spec-016 — if real merge sequencing is unclear, a separate `KANBAN.md` edit (out of scope here per the spec boundary) adds an explicit release-cut card; this spec does not author that edit.

## Out of scope (explicitly tracked elsewhere)

- [Schema export management command](GLOSSARY.md#schema-export-management-command) (`manage.py export_schema`): `WIP-ALPHA-018-0.0.7` in [`KANBAN.md`](../KANBAN.md). The command's discovery happens through Django's `management/commands/` directory convention, not through this card's AppConfig; the two cards are independent.
- [Multi-database cooperation](GLOSSARY.md#multi-database-cooperation) contract: `WIP-ALPHA-019-0.0.7` in [`KANBAN.md`](../KANBAN.md). The cooperation is in `types/resolvers.py`, not in `apps.py`; the two cards are independent.
- Warning-free scalar registration via `StrawberryConfig.scalar_map`: `WIP-ALPHA-045-0.0.7` in [`KANBAN.md`](../KANBAN.md). The scalar map is consumer-facing schema-construction shape, not AppConfig surface.
- Django checks for `DjangoType` declaration invariants (e.g., warn when a relation target is unimported at finalization time). Not on the current roadmap; a future card would land its own AppConfig `ready()` body in tandem with the check's implementation.
- Channels ASGI router ([`DjangoGraphQLProtocolRouter`](GLOSSARY.md#djangographqlprotocolrouter)): `TODO-ALPHA-029` for `0.0.12`.
- [Debug-toolbar middleware](GLOSSARY.md#debug-toolbar-middleware): `TODO-ALPHA-031` for `0.0.12`.
- [Response-extensions debug middleware](GLOSSARY.md#response-extensions-debug-middleware): `TODO-ALPHA-032` for `0.0.12`.
- Test-client helpers ([`TestClient`](GLOSSARY.md#testclient), [`GraphQLTestCase`](GLOSSARY.md#graphqltestcase)): `TODO-ALPHA-033` for `0.0.12`.
- `default_auto_field` declaration: not on the roadmap; the package ships no Django models. See [Decision 5](#decision-5--no-default_auto_field-and-no-models).

## Definition of done

The card is complete when all of the following are true:

1. `django_strawberry_framework/apps.py` exists and defines `DjangoStrawberryFrameworkConfig(AppConfig)` per [Decision 1](#decision-1--module-location--public-export) and [Decision 2](#decision-2--name--label--verbose_name-pinning) — `name = "django_strawberry_framework"`, `verbose_name = "Django Strawberry Framework"`, no `label` override, no `default_auto_field`, no `ready()` body, no `default = True` marker.
2. `django_strawberry_framework/__init__.py` is NOT modified (per [Decision 3](#decision-3--no-public-export)). `__all__` is unchanged.
3. `tests/base/test_init.py`'s `__all__` assertion is unchanged (per [Decision 3](#decision-3--no-public-export)).
4. `tests/test_apps.py` exists and contains the 5 tests listed in the [Test plan](#test-plan) — 4 positive (importable, subclass, attribute pinning, registry pickup) + 1 negative-shape (no `ready()` in `__dict__`).
5. `examples/fakeshop/config/settings.py:48` is NOT modified (per [Decision 7](#decision-7--no-fakeshop-installed_apps-entry-change)). The existing `"django_strawberry_framework"` entry continues to work through Django's implicit single-AppConfig discovery, now resolving to the explicit class.
6. The class does not implement `ready()` (per [Decision 4](#decision-4--no-readyhook-in-0_0_7)); the `tests/test_apps.py` negative-shape test pins this.
7. The class does not declare `default_auto_field` (per [Decision 5](#decision-5--no-default_auto_field-and-no-models)).
8. The class does not declare `default = True` (per [Decision 8](#decision-8--no-default--true-marker)).
9. The fakeshop live `/graphql/` HTTP tests at `examples/fakeshop/test_query/test_library_api.py` continue to pass unmodified — the explicit AppConfig is exercised through the existing `INSTALLED_APPS` entry without code changes elsewhere.
10. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`).
11. `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, and `CHANGELOG.md` reflect the shipped state per the [Doc updates](#doc-updates) section. `README.md`, `GOAL.md`, and `TODAY.md` are NOT edited.
12. `KANBAN.md` moves `WIP-ALPHA-017-0.0.7` to Done with the next `DONE-NNN-0.0.7` id and a past-tense body summarizing the shipped scope.
13. The version bump is NOT in this card per [Decision 6](#decision-6--joint-0_0_7-cut); the last `0.0.7` card to ship owns `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s version assertion.
14. Zero new public exports — `__all__` is unchanged.
15. `uv run ruff format .` passes; `uv run ruff check --fix .` passes; `uv run pytest` passes with 100% package coverage.
