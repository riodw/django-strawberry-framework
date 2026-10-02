# Rationale: spec-021 — `apps.py` and Django `AppConfig` (rejected alternatives)

Companion to [`spec-021-apps-0_0_7.md`][spec-021]. The spec is the contract; this file records, per Decision, the alternatives it rejected and why. A Decision's positive arguments live in the spec and are not repeated here.

## Entries keyed to the spec

### [Decision 1 — Module location & public export][spec-021-d1]

- **`django_strawberry_framework/django/apps.py`, mimicking `strawberry/django/apps.py`'s nested shape.** Rejected: Strawberry nests Django integration because Django is one of many adapter targets. This package's entire purpose is Django integration; a `django/` subdirectory would be redundant.
- **A `django_strawberry_framework/apps/__init__.py` subpackage.** Rejected: one AppConfig class does not need a subpackage, and Django looks for `apps.py` at the package root.

### [Decision 2 — `name` / `label` / `verbose_name` pinning][spec-021-d2]

- **`verbose_name = "django-strawberry-framework"`** (kebab-case, matching the PyPI distribution name). Rejected: the Django admin's app listing renders `verbose_name` directly, and kebab-case is unergonomic as a UI string.
- **`verbose_name = _("Django Strawberry Framework")` with `gettext_lazy`.** Rejected: the package declares no translation surface, and `gettext_lazy` here would pull `django.utils.translation` into the import graph for no benefit. If the package ever exposes localized strings, one card does it across every site.
- **A `label = "dsf"` shortcut.** Rejected: aliasing is gratuitous when the default is already unique, and a label matching the package name 1:1 spares consumers a "label vs name" distinction.

### [Decision 3 — No public export][spec-021-d3]

- **Re-export for consistency with other public symbols.** Rejected: [`DjangoListField`][glossary-djangolistfield] is re-exported because consumers `import` it into their schema code; the AppConfig is named only in `INSTALLED_APPS`.
- **Re-export under a friendlier name like `Config`.** Rejected: a top-level `Config` in a Django GraphQL framework is ambiguous with Django settings, Strawberry config and similar concepts.

### [Decision 4 — `ready()` applies the upstream patches][spec-021-d4]

- **No `ready()` at all.** Rejected: the upstream patches must be installed once Django is configured, and a consumer must not have to install them by hand. The rule that a hook lands with the shipped feature that needs it is satisfied: the patches are that feature.
- **Hoist the `APPLY_UPSTREAM_PATCHES` gate into `ready()`.** Rejected: the gate is per dependency (the mapping form disables one dependency's patches), and a dispatcher-level gate could only be all-or-nothing.
- **Enumerate in the spec which upstream bug each patch module fixes.** Rejected: each patch module's docstring is the single source of truth for its inventory, and `ready()`'s own docstring repeats none of it; a spec-side copy is a second thing to keep true.
- **Call the dispatch sequence a dependency order.** Rejected: the four appliers replace disjoint targets (`SimpleTestCase._remove_databases_failures`, Strawberry's `BaseView` / `SyncBaseHTTPView` / `AsyncBaseHTTPView` slots, `DjangoHTTPRequestAdapter.body`, `ExecutionContext.complete_list_value`), `apps.py` asserts no ordering constraint, and `tests/test_apps.py::test_ready_dispatches_all_four_patch_appliers_and_refires_safely` asserts that all four are installed, not the sequence. The spec states "in this order" as a fact, with no reason claimed.
- **Define `ready()` as an explicit `pass` body for "future flexibility".** Rejected: a `pass`-body method is the canonical preemptive-surface anti-pattern.
- **Have `ready()` call `finalize_django_types()`.** Rejected: it contradicts the consumer-owned synchronization point and would break consumers whose `config/schema.py` imports relation modules in an order different from Django's app loader.
- **Have `ready()` register a `django.core.checks` check validating `DjangoType` declarations.** Rejected: even a useful check has its own design surface — what it warns about, the message, whether it gates `manage.py runserver` — and needs its own spec.
- **Describe the `ready()` tests by their assertions alone.** Rejected: the dispatch test's assertion (all four patches installed) is satisfied by any earlier `apply()` on the worker; without the revert-first construction stated, the next author to "simplify" the test would delete the revert and keep an assertion that pins nothing.

### [Decision 5 — No `default_auto_field` and no models][spec-021-d5]

No alternative was weighed: the package declares no `models.py` anywhere in its tree, so the attribute has nothing to govern.

### [Decision 6 — Joint `0.0.7` cut][spec-021-d6]

- **This card bumps the version because it ships earlier than its siblings.** Rejected: ship order is whichever card a maintainer picks up next, not card number; pinning the bump to a specific card creates a sequencing constraint with no engineering justification.
- **A separate release-cut card on `KANBAN.md` that owns the bump.** Rejected: the "last card to ship" policy of [`spec-020`][spec-020] Decision 10 is workable as-is.

### [Decision 7 — No fakeshop `INSTALLED_APPS` entry change][spec-021-d7]

- **Switch fakeshop to the dotted-path form to demonstrate the explicit pattern.** Rejected: the spec's User-facing API already names the dotted path as an equivalent option, and the example should match the form the docs recommend.
- **A test in `examples/fakeshop/tests/` asserting the resolved AppConfig is `DjangoStrawberryFrameworkConfig`.** Rejected: the assertion belongs in `tests/test_apps.py`, where the system-under-test is the package; `tests/test_apps.py::test_djangostrawberryframeworkconfig_resolves_through_django_app_registry` pins it directly.

### [Decision 8 — No `default` attribute][spec-021-d8]

- **Set `default = True` defensively, in case a future Django changes the implicit-default behavior.** Rejected: Django's single-AppConfig discovery has been stable since 3.2, and Django's deprecation policy would announce a change with multi-version warnings.
- **Forbid only `default = True`.** Rejected: the negative-shape test asserts `"default" not in __dict__`, which catches any value, and `default = False` on the only AppConfig is self-defeating; forbidding the attribute outright matches Decisions 2 and 5.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-djangolistfield]: ../../GLOSSARY.md#djangolistfield

<!-- docs/SPECS/ -->
[spec-020]: ../spec-020-list_field-0_0_7.md
[spec-021]: ../spec-021-apps-0_0_7.md
[spec-021-d1]: ../spec-021-apps-0_0_7.md#decision-1--module-location--public-export
[spec-021-d2]: ../spec-021-apps-0_0_7.md#decision-2--name--label--verbose_name-pinning
[spec-021-d3]: ../spec-021-apps-0_0_7.md#decision-3--no-public-export
[spec-021-d4]: ../spec-021-apps-0_0_7.md#decision-4--ready-applies-the-upstream-patches
[spec-021-d5]: ../spec-021-apps-0_0_7.md#decision-5--no-default_auto_field-and-no-models
[spec-021-d6]: ../spec-021-apps-0_0_7.md#decision-6--joint-007-cut
[spec-021-d7]: ../spec-021-apps-0_0_7.md#decision-7--no-fakeshop-installed_apps-entry-change
[spec-021-d8]: ../spec-021-apps-0_0_7.md#decision-8--no-default-attribute

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
