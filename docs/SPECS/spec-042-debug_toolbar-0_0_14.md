# Spec: Debug-toolbar middleware — `DebugToolbarMiddleware` in a soft-`django-debug-toolbar` `middleware/debug_toolbar.py`, the SQL-panel window into `/graphql/` requests

Built for `0.0.14` (card [`DONE-042-0.0.14`][kanban]). This card is the
package's **`django-debug-toolbar` integration**: the
`django_strawberry_framework/middleware/debug_toolbar.py` module exposing
`DebugToolbarMiddleware` — a subclass of `debug_toolbar.middleware.DebugToolbarMiddleware`
that overrides `process_view` (to tag Strawberry-Django-view requests) and `_postprocess` (to
inject the toolbar payload into the two GraphQL response shapes) — plus its
template asset at
`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`.
It is a Required 🍓 `strawberry-graphql-django` parity item (the card's own tag):
[`strawberry_django/middlewares/debug_toolbar.py`][upstream-middleware] ships a
`DebugToolbarMiddleware` of the same shape, and without an equivalent,
`django-debug-toolbar`'s SQL panel never captures the queries a `/graphql/`
request triggers — developers cannot see the SQL their GraphQL selections
actually hit, which for a package whose headline is a cooperative N+1 optimizer
([`DjangoOptimizerExtension`][glossary-djangooptimizerextension]) is the single
most useful dev-time window into whether the plan did what the consumer expects.
`graphene-django` ships **no** equivalent (the card's own "Why it matters"), so
this is honest [single-upstream parity][glossary-single-upstream-parity] — the
same posture [`spec-041`][spec-041] took for the Channels router and
[`spec-040`][spec-040] took for the [auth module][glossary-auth-mutations].

The middleware is deliberately **thin and upstream-riding**: `django-debug-toolbar`
owns the panels, the request tracking, the handle rendering, and the stock
middleware lifecycle; the package contributes exactly the two overrides upstream
contributes — Strawberry-view tagging and payload injection — plus the
template that teaches the toolbar's frontend to consume the injected payload.
`django-debug-toolbar` is a **[soft dependency][glossary-soft-dependency]**
([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)) —
the package's third, after `djangorestframework` ([`spec-039`][spec-039]) and
`channels` ([`spec-041`][spec-041]): `import django_strawberry_framework` and
`import django_strawberry_framework.middleware` both succeed without it, and the
install-hint `ImportError` fires when the consumer actually imports the
middleware module — which for a Django middleware is exactly the `MIDDLEWARE`
dotted-path import at server startup, the earliest moment the integration is
reached for.

The card bumps no version: the `0.0.14` release is the [joint `0.0.14`
cut][glossary-joint-version-cut]
([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).

Status: **COMPLETE (card `DONE-042-0.0.14`).** The middleware, the template asset, the
soft-dependency gate, the example project's toolbar wiring and both test tiers are on `main`.
Two slices: Slice 1 (**the dependency gate + `middleware/debug_toolbar.py` + the template +
both test tiers** — the `django-debug-toolbar` dev-group row with the lockfile, the
soft-dependency guard, the middleware subclass, the template asset, the toolbar-present live
tests and the package-tier tests), and Slice 2 (**docs + card wrap** — the glossary entry, the
regenerated [`docs/TREE.md`][tree], and the kanban card).

Owner: package maintainer.

Predecessors: [`spec-041-channels_router-0_0_14.md`][spec-041] (the card that landed
[`require_optional_module`][glossary-require-optional-module] in
[`utils/imports.py`][utils-imports] — the raising optional-import primitive this
card's guard rides — and generalized the [soft-dependency][glossary-soft-dependency]
architecture to a second integration; `django-debug-toolbar` is the third);
[`spec-039-serializer_mutations-0_0_13.md`][spec-039] (the original
soft-dependency card — the single `require_*()` guard with one install-hint
string, the dev-group + lockfile dependency gate, and the
[eviction-simulated absence][glossary-eviction-simulated-absence] test
discipline); [`spec-040-auth_mutations-0_0_13.md`][spec-040] (the
single-upstream-parity posture precedent). [`docs/GLOSSARY.md`][glossary] carries
the [Debug-toolbar middleware][glossary-debug-toolbar-middleware] entry.

The alternatives each decision below rejected, and the derivations that do not change how it
is built, live in the companion [`spec-042-debug_toolbar-0_0_14-rationale.md`][rationale].
This spec is the contract.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary
used throughout the spec:

- [Debug-toolbar middleware][glossary-debug-toolbar-middleware] — the subject:
  `django-debug-toolbar` SQL-panel integration during `/graphql/` requests,
  mirroring `strawberry-django`'s `middlewares/debug_toolbar.py` shape, distinct
  from the in-response sibling.
- [Response-extensions debug middleware][glossary-response-extensions-debug-middleware]
  — the sibling card ([`DONE-044-0.0.14`][kanban]) this card is
  **deliberately distinct from**: this card is the server-side toolbar panel
  UI; that card surfaces SQL / exceptions **inside** the GraphQL response's
  `extensions` map. Both useful, not mutually exclusive — the card body says so
  and this spec preserves the boundary
  ([Decision 2](#decision-2--card-scope-boundary-the-server-side-toolbar-integration-ships-the-in-response-surface-and-async-verification-stay-out)).
- [Soft dependency][glossary-soft-dependency] — the pattern this card
  instantiates a third time: one `require_*()` guard over the
  `utils/imports.py` optional-import owner, one install-hint constant,
  [eviction-simulated absence][glossary-eviction-simulated-absence] tests, and
  the dev-group + lockfile dependency gate. The lazy-resolution *mechanism*
  differs from the router's — see the next two entries.
- [PEP 562 lazy export][glossary-pep-562-lazy-export] — the router's
  lazy-symbol mechanism, cited here as the **contrast**: this card deliberately
  does NOT use it. The middleware module is a dedicated leaf whose import is
  itself the opt-in (the `rest_framework/` shape), so the guard runs at module
  import time
  ([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).
- [Eviction-simulated absence][glossary-eviction-simulated-absence] — the test
  discipline for the toolbar-absent path: strict `sys.modules` eviction with the
  **two-sided** (parent-attribute) restore and an importlib-compatible
  `sys.modules["debug_toolbar"] = None` sentinel, through the shared
  `tests/_soft_dependency.py` helpers every soft-dependency suite uses (Decision 9).
- [`require_optional_module`][glossary-require-optional-module] — the raising
  optional-import primitive in [`utils/imports.py`][utils-imports];
  `require_debug_toolbar()` is a thin wrapper over it, never a hand-rolled
  import pattern of its own.
- [Joint version cut][glossary-joint-version-cut] — why no slice here bumps the
  version: the joint `0.0.14` cut owns the version and the release-status flips
  ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).
- [Live-first coverage mandate][glossary-live-first-coverage-mandate] — the
  test-placement rule
  [Decision 9](#decision-9--test-strategy-live-tier-tests-through-fakeshops-shipped-toolbar-package-tests-for-the-paths-no-live-request-reaches-eviction-simulated-absence)
  answers: the example's shipped settings wire the toolbar, so the toolbar-present
  tests drive **real fakeshop `/graphql/` requests** from the live tier, and only
  the paths no live request can reach — the soft-dependency absence matrix and the
  coverage-only branch units — stay in `tests/middleware/`.
- [Schema reload discipline][glossary-schema-reload-discipline] — the
  order-independence obligation the toolbar-present tests inherit from the live
  acceptance suites: a test executing real GraphQL through the aggregate fakeshop
  schema rebuilds that schema on setup via the single-sited
  `schema_reload.reload_all_project_schemas()` helper, so a package test's
  `registry.clear()` can never surface as an order-dependent `LazyType`
  `KeyError` / `DuplicatedTypeName`.
- [`seed_data`][glossary-seed-data] — the repo's seed-helper rule applied to
  the [Test plan](#test-plan): every product-query test's first executable
  line is `seed_data(1)` (or an explicit `seed_data(N)`) from
  `apps.products.services`, so the SQL-panel assertions ride real rows and
  real SQL.
- [Single-upstream parity][glossary-single-upstream-parity] — the card's
  Required 🍓 parity posture: `strawberry-graphql-django` ships the equivalent
  module, `graphene-django` ships none, and the card says so plainly instead
  of fabricating a second upstream — the same honesty
  [`spec-040`][spec-040] ([Auth mutations][glossary-auth-mutations]) and
  [`spec-041`][spec-041] recorded.
- [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] — the
  `0.0.14` predecessor whose soft-`channels` work built the guard primitive and
  the two-sided-restore test discipline this card reuses.
- [`SerializerMutation`][glossary-serializermutation] — the original
  soft-dependency precedent (`require_drf()`, the `_HINT_SUBSTRING` drift-check
  discipline, the import-time-guard-in-a-leaf-package shape this card's
  Decision 5 mirrors).
- [`TestClient`][glossary-testclient] / [`GraphQLTestCase`][glossary-graphqltestcase]
  — the `0.0.14` sibling card whose helpers own HTTP-level test ergonomics; the
  toolbar's live tier posts its GraphQL envelopes through `TestClient`, so the
  toolbar sees the same request path a consumer's own test would drive.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — untouched
  here, but the reason this card matters more for this package than for a
  generic GraphQL library: the SQL panel is how a developer *sees* the
  optimizer's `select_related` / `prefetch_related` / [`only()`
  projection][glossary-only-projection] plan as executed queries during a
  `/graphql/` request.
- [Django `AppConfig`][glossary-django-appconfig] — the shipped app config is
  what makes the template asset resolvable: consumers already list
  `"django_strawberry_framework"` in `INSTALLED_APPS`, so Django's app-dirs
  template loader finds the in-package
  `templates/django_strawberry_framework/debug_toolbar.html`
  ([Decision 4](#decision-4--module-template-and-test-locations-a-middleware-subpackage-an-in-package-template-asset-testsmiddleware)).
- [`ConfigurationError`][glossary-configurationerror] — NOT raised by
  `middleware/debug_toolbar.py`: a missing optional dependency is `ImportError`
  with an install hint per the soft-dependency contract, and a missing
  `"debug_toolbar"` app is Django's own `ImproperlyConfigured`
  ([Error shapes](#error-shapes)).

## Slice checklist

Each top-level item maps to one commit / PR. **Two slices: the dependency gate +
code + template + tests (Slice 1), and docs + card wrap (Slice 2).** The card is
an M — the middleware is two overrides and a module-level helper (~100 lines
upstream including imports), the template is a JS asset ported from upstream's,
and the weight is in the soft-dependency discipline and the live fakeshop
request tests.

- [ ] **Slice 1 — dependency gate + `middleware/debug_toolbar.py` + template +
  both test tiers**
  - [ ] **The dependency gate**: **`django-debug-toolbar>=7.0.0`** in
        `[dependency-groups].dev` in [`pyproject.toml`][pyproject], with
        `uv.lock` carrying it, so the declared and locked dev environments never
        diverge. The floor is **`7.0.0` everywhere — one floor, single-valued
        across every naming site**: [`pyproject.toml`][pyproject] advertises
        `Framework :: Django :: 5.2` / `6.0` / `6.1`, and `7.0.0` is the first
        `django-debug-toolbar` release carrying the Django 6.0 classifier, so the
        floor's Django coverage reaches 6.0 and stops short of the `6.1` the
        package also advertises (PyPI metadata: `6.0.0`, 2025-07-25, classifies
        Django 4.2–5.2 only; `7.0.0` classifies 5.2 + 6.0 with `django>=5.2` and
        `python>=3.10` — both compatible with the package's own floors), so
        upstream's `django-debug-toolbar>=6.0.0` declaration is deliberately
        **not** copied: a `6.0.0` floor would let a Django 6.0 user follow the
        package's own install hint into an unsupported toolbar
        ([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).
        The three-places-that-must-agree rule applies — the dev-group specifier,
        the `_DEBUG_TOOLBAR_INSTALL_HINT` string, and the re-typed test literal
        all name the same floor, and the package test compares all three (hint
        against literal, literal against the [`pyproject.toml`][pyproject] row)
        so none can move alone. Those three are the **gated** sites, not the
        whole population: documentation that restates the floor is gated by
        nothing, so a floor bump sweeps the tree instead of trusting any
        enumeration of where it is written — and sweeps for the package
        **name**, reading each hit, rather than for the `django-debug-toolbar>=`
        specifier, which a restatement separating the name from the constraint
        with a backtick or a space does not match.
  - [ ] **The Strawberry view-class gate**: `strawberry.django.views.BaseView`
        (the `issubclass` target of
        [Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned))
        is importable at the package's declared `strawberry-graphql` floor,
        checked in an isolated throwaway venv (never the shared `.venv`). **The
        floor version is read at gate time** from [`pyproject.toml`][pyproject]
        and [`docs/builder/BUILD.md`][build] `## Floor verification`, never from
        a number restated in this spec. At the installed strawberry,
        `strawberry/django/views.py` defines `BaseView` with `GraphQLView` /
        `AsyncGraphQLView` both subclassing it. If it is missing at the floor,
        bump the project's Strawberry floor instead.
  - [ ] `django_strawberry_framework/middleware/__init__.py` — the subpackage
        marker with its module docstring; imports nothing optional, so
        `import django_strawberry_framework.middleware` stays clean on a
        toolbar-less machine
        ([Decision 4](#decision-4--module-template-and-test-locations-a-middleware-subpackage-an-in-package-template-asset-testsmiddleware)).
  - [ ] `django_strawberry_framework/middleware/debug_toolbar.py` — the
        `require_debug_toolbar()` guard (a thin
        [`require_optional_module`][glossary-require-optional-module] wrapper;
        one `_DEBUG_TOOLBAR_INSTALL_HINT` string, no memoization) executed **at
        module import time**, then the `apps.is_installed("debug_toolbar")`
        wiring gate, both before the `debug_toolbar` imports the class body
        needs; the `_HTML_TYPES` constant; the module-level `_get_payload`
        helper; and `DebugToolbarMiddleware(debug_toolbar.middleware.DebugToolbarMiddleware)`
        overriding `process_view` (tag `request._is_graphiql` via
        `issubclass(view, strawberry.django.views.BaseView)`) and
        `_postprocess` (skip streaming and `Content-Encoding`-carrying
        responses; append the rendered template to GraphiQL HTML responses;
        inject the `debugToolbar` payload into Strawberry-view JSON operation
        responses; skip introspection queries; refresh `Content-Length` on both
        mutation paths)
        ([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)
        / [Decision 6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types)
        / [Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned)
        / [Decision 8](#decision-8--the-introspection-query-skip-is-preserved-verbatim)).
  - [ ] `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
        — the toolbar-frontend JS asset, ported from
        [upstream's template][upstream-template] carrying the documented guard
        divergences of the [template-port checklist](#borrowing-posture) (the
        `JSON.parse` / `Response.prototype.json` patch consuming the injected
        `debugToolbar` key and updating the panel titles / subtitles /
        `data-request-id`); rendered by the middleware via
        `render_to_string("django_strawberry_framework/debug_toolbar.html")`
        and resolved through Django's app-dirs template loader against the
        package's shipped [`AppConfig`][glossary-django-appconfig]
        ([Decision 4](#decision-4--module-template-and-test-locations-a-middleware-subpackage-an-in-package-template-asset-testsmiddleware)).
  - [ ] The example opts in: [`config/settings.py`][config-settings] lists
        `"debug_toolbar"` in `INSTALLED_APPS`, the package middleware near the
        front of `MIDDLEWARE` and `INTERNAL_IPS`; [`config/urls.py`][config-urls]
        appends `debug_toolbar_urls()`.
  - [ ] Both test tiers (the `tests/middleware/` package marker included),
        split per
        [Decision 9](#decision-9--test-strategy-live-tier-tests-through-fakeshops-shipped-toolbar-package-tests-for-the-paths-no-live-request-reaches-eviction-simulated-absence).
        **Toolbar-present — `examples/fakeshop/test_query/test_debug_toolbar_api.py`**
        (class-level `pytest.mark.django_db`): real fakeshop `/graphql/`
        requests through the example's shipped toolbar wiring, under a
        `DEBUG=True` override that reloads `config.urls` inside itself, a
        `DEBUG_TOOLBAR_CONFIG` with an always-true `SHOW_TOOLBAR_CALLBACK` and
        `RedirectsPanel` enabled, and the `show_toolbar_func_or_path` cache
        clear plus the `DebugToolbar._panel_classes`/`_urlpatterns`
        save/clear/restore — each product-query test starting with
        [`seed_data(1)`][glossary-seed-data]; covering the GraphiQL HTML path,
        the JSON operation path (a **named** operation when `operationName` is
        non-null), the introspection skip, the deterministic JSON-`Accept` GET
        branch, the **panel-content route fetch using the injected
        `requestId`** (asserting `render_panel`'s JSON `content`/`scripts`
        shape), the HTML passthroughs for both Django dispatch shapes, the
        unrelated-JSON-view leak guard, the `Content-Encoding` early-out at both
        mutation sites, the `Content-Length` match after each mutation, and the
        inert-under-shipped-settings baseline.
        **Package-tier — `tests/middleware/test_debug_toolbar.py`**: the paths no
        live request reaches — the coverage-only targeted units (streaming
        early-out, no-`request_id` bail / `has_content` false and callable
        title / subtitle / non-object and undecodable body bails, the non-class
        `view_class` guard), the template-port guard, and **toolbar-absent**:
        the shared `tests/_soft_dependency.py` eviction + two-sided
        parent-attribute restore with an importlib-compatible
        `sys.modules["debug_toolbar"] = None` sentinel —
        `import django_strawberry_framework` and `import
        django_strawberry_framework.middleware` both succeed; `import
        django_strawberry_framework.middleware.debug_toolbar` raises
        `ImportError` carrying the install hint (matched against a re-typed
        literal, the `_HINT_SUBSTRING` drift-catch discipline); plus the
        present-but-broken-install degraded test, the missing-`INSTALLED_APPS`
        wiring gate, and the floor's pyproject-row gate ([Test plan](#test-plan)).
  - [ ] Every symbol carries its docstring (the [`docs/TREE.md`][tree] render
        fails on missing module docstrings).
- [ ] **Slice 2 — docs + card wrap (no version bump)**
  - [ ] [`docs/GLOSSARY.md`][glossary]
        [Debug-toolbar middleware][glossary-debug-toolbar-middleware] entry body
        carries the contract (the dotted settings path, the
        replace-the-stock-entry wiring, the required `debug_toolbar_urls()`
        URLconf step with its true failure mode — omitting it is a
        `NoReverseMatch` on every toolbar-processed request, not a
        panel-click 404 — the `BaseView` detection, the view-scoped (not
        IDE-scoped) injection contract, the introspection skip, the
        soft-dependency behavior matrix, the show-toolbar gating note, the
        staticfiles + `STATIC_URL` prerequisite note, and the
        not-a-Channels-integration boundary).
  - [ ] [`docs/TREE.md`][tree] regenerated via
        [`scripts/build_tree_md.py`][build-tree-md] (never hand-edited): the
        `middleware/debug_toolbar.py` rows are docstring-derived, and
        `tests/middleware/test_debug_toolbar.py` appears in the test tree.
  - [ ] [`KANBAN.md`][kanban] card at Done with the `DONE-042-0.0.14` id and
        its `SpecDoc` pointing at this spec (kanban DB edit +
        [`scripts/build_kanban_md.py`][build-kanban-md] /
        `build_kanban_html.py` re-render, never a hand-edit).

## Problem statement

`django-debug-toolbar` is the standard dev-time window into a Django request:
which SQL ran, how long it took, what templates rendered, what signals fired. It
works by tracking a request through its middleware and rendering a per-request
panel UI into HTML responses. A GraphQL endpoint breaks both halves of that
contract: the interesting responses are JSON (an operation result has no HTML
body to inject a toolbar into), and the one HTML response the endpoint serves —
the GraphiQL IDE page — is loaded **once**, after which every query is a
`fetch()` the toolbar never sees. The result is the exact gap the card names:
`django-debug-toolbar`'s SQL panel captures nothing for `/graphql/` traffic, so
developers cannot see the queries their GraphQL selections trigger.

That gap matters more for this package than for a generic GraphQL library.
The package's headline claim — [`GOAL.md`][goal] success criterion 5, "rely
on automatic ORM optimization" — is that
[`DjangoOptimizerExtension`][glossary-djangooptimizerextension] turns nested
selections into one planned queryset — `select_related` joins, windowed
prefetches, [`only()` projections][glossary-only-projection], [FK-id
elision][glossary-fk-id-elision]. The SQL panel is how a developer *verifies*
that claim against their own schema during development: one look at the panel
after a `/graphql/` request shows whether the plan collapsed the N+1 or not.
Shipping the optimizer without the standard way to watch it work is an
observability hole in the package's own story.

`strawberry-graphql-django` closes the gap in
[`strawberry_django/middlewares/debug_toolbar.py`][upstream-middleware] (itself
based on the archived `django-graphiql-debug-toolbar` project, credited in its
header comment): a `DebugToolbarMiddleware` subclassing the stock toolbar
middleware, tagging Strawberry-Django-view requests in `process_view`, and
injecting a `debugToolbar` payload into the JSON responses those views return in
`_postprocess` — paired with a [template asset][upstream-template] that patches
the GraphiQL page's `JSON.parse` / `Response.json` so the toolbar's frontend
updates its panels from the injected payload after every query. The card
carries the Required 🍓 parity tag for exactly that module (the
[`KANBAN.md`][kanban] #"Decision: Alpha cards must claim upstream parity" rule;
`graphene-django` ships **no** equivalent — its debug story is the in-response
`DjangoDebug` subsystem tracked by the sibling card
[`DONE-044-0.0.14`][kanban] — so this is single-upstream parity, honest,
not fabricated).

The work is small — two overrides, one helper, one template — but it introduces
the package's **third soft dependency** (`django-debug-toolbar`, after
`djangorestframework` and `channels`), so the real design weight is in doing
that the way [`spec-039`][spec-039] and [`spec-041`][spec-041] already proved:
one guard, one install-hint string, a package import that never pays for the
integration it didn't ask for, and tests that simulate absence without
uninstalling anything.

## Current state

- **`django_strawberry_framework/middleware/` holds two leaves.** `debug_toolbar.py`
  is this card's; `request_body.py` (`GraphQLRequestBodyBoundaryMiddleware`) is
  [`spec-046`][spec-046]'s request-body boundary and imports nothing from the
  toolbar leaf. The package marker imports neither.
- **The package ships `templates/`.** [`pyproject.toml`][pyproject]'s hatchling
  wheel target packages the `django_strawberry_framework` directory wholesale, so
  the in-package template ships without a build-config entry of its own.
- **The package ships view classes.** [`views.py`][views]'s `DjangoGraphQLView` and
  `AsyncDjangoGraphQLView` subclass Strawberry's `GraphQLView` /
  `AsyncGraphQLView`, which subclass `strawberry.django.views.BaseView`; fakeshop's
  [`config/urls.py`][config-urls] mounts `DjangoGraphQLView` (wrapped in
  `ensure_csrf_cookie`, with `graphql_ide="graphiql"`). The engine base is what the
  detection targets
  ([Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned)).
- **`django-debug-toolbar` is a dev-group dependency only.** It is in
  `[dependency-groups].dev` and absent from `[project].dependencies` in
  [`pyproject.toml`][pyproject].
- **The soft-dependency architecture is shared.**
  [`utils/imports.py`][utils-imports]'s
  [`require_optional_module(module_name, *, install_hint)`][glossary-require-optional-module]
  backs `require_drf()`, `require_channels()` in [`routers.py`][routers], and
  `require_debug_toolbar()`; the absence suites share `tests/_soft_dependency.py`
  ([eviction-simulated absence][glossary-eviction-simulated-absence] with the
  two-sided parent-attribute restore and the `None` sentinel).
- **The whole test suite runs against fakeshop settings, which wire the toolbar.**
  [`pytest.ini`][pytest-ini] sets `DJANGO_SETTINGS_MODULE = config.settings` with
  `pythonpath = examples/fakeshop`; fakeshop's settings and URLconf carry all three
  toolbar pieces, which is what puts the toolbar-present tests in the live tier
  ([Decision 9](#decision-9--test-strategy-live-tier-tests-through-fakeshops-shipped-toolbar-package-tests-for-the-paths-no-live-request-reaches-eviction-simulated-absence)).

## Goals

1. **Make the SQL panel see `/graphql/` traffic.** With the middleware wired, a
   developer running the toolbar sees, for every GraphQL operation issued from
   GraphiQL, the toolbar panels update in place — the SQL panel carrying the
   queries that operation triggered, which for this package means the
   [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] plan as
   actually executed
   ([Decision 6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types)).
2. **Keep `django-debug-toolbar` soft.** `import django_strawberry_framework`
   (and `from django_strawberry_framework import *`) must succeed and stay
   toolbar-free; the install-hint `ImportError` fires only when the consumer
   actually imports the middleware module — which is what Django's `MIDDLEWARE`
   setting does at startup, so a consumer who lists the dotted path without the
   dependency gets one actionable error naming the floor
   ([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).
3. **One-line migration.** A `strawberry-graphql-django` migrant changes exactly
   one settings string —
   `"strawberry_django.middlewares.debug_toolbar.DebugToolbarMiddleware"` →
   `"django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware"` —
   with zero behavior change (same class name, same overrides, same template
   mechanism), and the rename is recorded for the migration guide's
   symbol-equivalents table
   ([Decision 3](#decision-3--the-symbol-is-debugtoolbarmiddleware--same-class-name-distinctly-ours-dotted-path)).
   This is [`GOAL.md`][goal] success criterion 7 — migrate "without bringing
   the source package along" — applied to a settings dotted path, the
   middleware's equivalent of an import line.
4. **Both dependency states tested, against real requests.** The
   toolbar-present tests drive the real fakeshop GraphiQL page and a real
   SQL-emitting products query over the example's shipped wiring, posting their
   GraphQL envelopes through the package's own
   [`TestClient`][glossary-testclient]; the toolbar-absent path pins the guarded
   `ImportError`. The package coverage gate
   (`fail_under = 100`) holds with `middleware/debug_toolbar.py` included
   ([Decision 9](#decision-9--test-strategy-live-tier-tests-through-fakeshops-shipped-toolbar-package-tests-for-the-paths-no-live-request-reaches-eviction-simulated-absence)).
5. **Own nothing the toolbar already owns.** No panel logic, no request
   tracking, no toolbar configuration surface — the package contributes the
   GraphQL-shaped injection points and nothing else, so toolbar upgrades keep
   working through the stock machinery
   ([Decision 6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types)).

## Non-goals

- **The in-response debug surface.** Surfacing SQL / exceptions inside the
  GraphQL response's `extensions` map is the sibling card
  [`DONE-044-0.0.14`][kanban]
  ([Response-extensions debug middleware][glossary-response-extensions-debug-middleware])
  — graphene-django parity, a Strawberry `SchemaExtension`, no toolbar
  involved. The two are complementary by design; nothing in this card reads or
  writes `extensions`.
- **A package view class shipped for detection's sake.** The Strawberry-view
  detection targets Strawberry's engine-owned `BaseView`
  ([Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned)),
  never a package-owned class — a view introduced so that a middleware can
  `issubclass` it would be surface for surface's sake. The package's own
  [`views.py`][views] views ship for transport reasons of their own and are
  covered by the engine-owned check for free, because they subclass Strawberry's
  views; this card contributes no view and no `issubclass` target.
- **Toolbar configuration passthrough.** `DEBUG_TOOLBAR_CONFIG`,
  `SHOW_TOOLBAR_CALLBACK`, panel selection, and `INTERNAL_IPS` are
  `django-debug-toolbar`'s own settings surface and remain the consumer's
  business; the middleware inherits whatever the stock middleware reads. No new
  package settings key — [`conf.py`][conf] is untouched (the [`START.md`][start]
  rule: add a settings key only when the feature that needs it lands; none does).
- **A hard `django-debug-toolbar` dependency, or an extras group.**
  `[project].dependencies` is untouched; no
  `django-strawberry-framework[debug-toolbar]` extra (upstream ships one, but
  the package's DRF and channels precedents both rejected extras — an extra
  changes how consumers install, not whether the import needs guarding; rejected
  again in
  [Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).
- **Async-path verification.** The stock toolbar middleware is async-capable
  and the subclass inherits that; but the package's own test vehicle (fakeshop)
  is WSGI/sync, and this card asserts nothing about the toolbar under
  `AsyncGraphQLView` or ASGI — recorded honestly in
  [Risks](#risks-and-open-questions), not implied.

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it?" test this card is
**single-upstream parity**: `strawberry-graphql-django` ships
[`middlewares/debug_toolbar.py`][upstream-middleware] + its
[template asset][upstream-template]; `graphene-django` ships no toolbar
integration (its debug story is the in-response `DjangoDebug` subsystem — the
sibling card's territory). The upstream module is 101 lines and every behavior
below is taken from it directly. Upstream's own header credits `django-graphiql-debug-toolbar` (the
archived origin project) — the lineage is toolbar-side, not GraphQL-side, which
is consistent with the module's shape: everything hard lives in
`django-debug-toolbar`; the integration is two overrides.

### From `strawberry-graphql-django` — borrow the mechanism, verbatim

[`middlewares/debug_toolbar.py`][upstream-middleware] is, in full:

- **`_HTML_TYPES = {"text/html", "application/xhtml+xml"}`** — the
  content-type sniff set for the HTML injection path.
- **`_get_payload(request, response, toolbar) -> dict | None`** — module-level
  helper: bail (`None`) when the toolbar assigned no `request_id`; otherwise
  decode the JSON response body (`force_str` with the response charset,
  `object_pairs_hook=OrderedDict`), **bail (`None`) again on any response-shape
  failure** — undecodable bytes, unparseable text, or a decoded body that is not
  a JSON object (see below), attach
  `payload["debugToolbar"] = {"panels": {...}, "requestId": toolbar.request_id}`,
  and fill `panels` from `reversed(toolbar.enabled_panels)` with each panel's
  `title` (only when `panel.has_content`, called if callable) and
  `nav_subtitle` (called if callable), **skipping `TemplatesPanel`** (its
  content churns per request and floods the payload). The response-shape bails
  are the module's second deliberate divergence from upstream, which decodes and
  subscript-assigns unconditionally: a valid single GraphQL response is always
  decodable JSON and always an object, but a malformed view, a mislabelled
  charset, or a future batch-response shape is none of those, and upstream's form
  then raises and turns this dev-only tool into a 500. Guarding the **answer**
  rather than one spelling of the bad input is why the bail covers the decode,
  the parse and the type together instead of only the non-object case.
- **`DebugToolbarMiddleware(debug_toolbar.middleware.DebugToolbarMiddleware)`**
  with exactly two methods:
  - `process_view` — `request._is_graphiql = isinstance(view, type) and
    issubclass(view, BaseView)` where `view = getattr(view_func, "view_class",
    None)` and `BaseView` is `strawberry.django.views.BaseView`. The
    `isinstance(view, type)` guard is a deliberate, narrow divergence from
    upstream's `bool(view and issubclass(...))` — see
    [Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned).
  - `_postprocess` (decorated `@override`) — call `super()._postprocess(...)`
    first (the stock toolbar does its own work: handle insertion into the
    GraphiQL HTML page, history tracking); return early for
    `response.streaming`; sniff `Content-Type` (first segment); **HTML path**:
    when HTML + Strawberry-view-tagged (`_is_graphiql`) + status 200, `render_to_string` the template
    asset, `response.write(template)`, refresh `Content-Length` if present;
    **JSON path**: when the request is Strawberry-view-tagged and the content type is
    `application/json`, read `operationName` from `json.loads(request.body)`
    (any exception → `None`), skip the payload entirely for
    `"IntrospectionQuery"`, else `_get_payload(...)` and re-encode the body
    with `json.dumps(payload, cls=DjangoJSONEncoder)` + `Content-Length`
    refresh.
- **The [template asset][upstream-template]** — a `<script>` appended to the
  GraphiQL HTML page that patches `JSON.parse` and `Response.prototype.json`:
  every JSON body the IDE decodes is passed through `update(data)`, which — when
  a `debugToolbar` key is present — writes the panel titles / subtitles into
  the already-rendered toolbar DOM, resets each updated panel's content area to
  a loader (the panel body is re-fetched lazily by the stock toolbar JS via the
  `data-request-id`), sets that `data-request-id` attribute on `djDebug` (via
  `setAttribute`), deletes the `debugToolbar` key, and returns the cleaned data
  so GraphiQL renders the response unpolluted.

The mechanism is borrowed as-is
([Decision 6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types));
the deltas are the module path, the template's render path
(`django_strawberry_framework/debug_toolbar.html`), the soft-dependency guard
upstream does not need, and the documented robustness divergences — **three**
Python-middleware ones plus the template-side guard family, all enumerated
below.

**Template-port checklist.** Because the asset is JavaScript and the package
test suite has no JS runtime, the port is a behavior-preserving copy verified
against upstream by diff, not by execution. The reviewable invariants a diff
against [upstream's template][upstream-template] must preserve — each also
pinned mechanically as a substring/pattern check by the [Test plan](#test-plan)'s
template-port guard (Test 16), so the list is not protected by visual review
alone:

- the `JSON.parse` wrapper is preserved (in the hardened form below, not
  upstream's verbatim `function (text)`);
- the `Response.prototype.json` wrapper is preserved;
- `delete data.debugToolbar` (the key is stripped before the IDE renders) is
  preserved;
- the `data-request-id` update on `#djDebug` (via `setAttribute`) is preserved;
- the per-panel title / subtitle DOM updates are preserved.

**Documented robustness divergences (the template-side family).** Upstream's
hook is a verbatim borrow that is unsafe as a *global* patch, in the same "a
dev-only tool that patches a global must neither corrupt nor crash unrelated page
code" class the middleware's three Python divergences address. Once `update` is
wired into the page-wide `JSON.parse` / `Response.prototype.json`, the guiding
rule is **payload scrubbing is mandatory and DOM updates are best-effort**. The
port diverges from the borrow in seven spots, every one of them serving that rule:

- **Reviver preservation.** Upstream's `JSON.parse = function (text) {
  return update(origParse(text)); }` drops the standard second `reviver`
  argument, so every page-wide `JSON.parse(text, reviver)` silently loses its
  reviver while GraphiQL is open — the port forwards every argument via
  `JSON.parse = function () { return update(origParse.apply(this, arguments)); }`.
- **Membership-guard safety.** Upstream's
  `!data.hasOwnProperty("debugToolbar")` guard throws for a null-prototype object
  (`Object.create(null)`) or one that shadows `hasOwnProperty` — the port's
  `update` bails unless the record predicate below accepts `data` **and**
  `Object.prototype.hasOwnProperty.call(data, "debugToolbar")` finds the key, so
  neither shape reaches a method lookup on the payload itself.
- **Mandatory scrub before the null-handle bail.** The port captures the
  `debugToolbar` payload and `delete`s the key *before* the
  `if (djDebug === null) return data;` guard, so a page whose toolbar DOM did not
  render still returns a scrubbed GraphQL payload instead of leaking the
  server-only key back to GraphiQL. The ordering is the contract, not an
  accident: the scrub is unconditional and the DOM work is what may be skipped.
- **Best-effort per-panel DOM.** The panel loop is a side-effect-only
  `forEach` that skips a panel whose content node is absent (`content === null`)
  and writes the nav subtitle only when the nav item exists, so a panel present
  in the payload but missing from the current toolbar DOM cannot throw inside the
  patched `JSON.parse` / `Response.prototype.json` and break the IDE response
  path. The same promise covers the panel **key**, which the loop interpolates
  into the `#…` selectors locating that panel's content and nav nodes: the key
  reaches `querySelector` only through a form the selector parser always
  accepts, and the one key that cannot be put into such a form is skipped
  before either lookup. So every key either names a node, resolves to nothing
  and skips that one panel exactly as an absent node does, or is skipped
  outright — and none raises a `DOMException` out of the patched globals. What
  the guard makes total is the **answer** the loop needs, not the lookup
  itself. A key that cannot be *resolved* and a node that cannot be *found* are
  the same promise, so they are guarded here rather than as a form of their own.
- **Shadow-DOM handle resolution.** `django-debug-toolbar` 7 defaults
  `USE_SHADOW_DOM=True`, so `#djDebug` lives inside `#djDebugRoot`'s shadow tree
  and upstream's bare `document.getElementById("djDebug")` resolves to `null` —
  under which the guard above is correct and every DOM update silently stops. The
  port mirrors the stock toolbar's own element lookup: read `#djDebugRoot`, and
  when it has a `shadowRoot` resolve `#djDebug` inside it, falling back to the
  light-DOM lookup so `USE_SHADOW_DOM=False` consumers keep working. Nav lookups
  go through the resolved handle for the same reason.
- **Per-node null guards on the panel render.** Every nested `querySelector`
  result inside a panel — the panel title, its heading, the scroll container, the
  loader's content parent, and the nav subtitle — is null-checked before it is
  written to. The chained upstream form throws a `TypeError` inside the patched
  `JSON.parse` the moment one node is absent, which blanks the toolbar and breaks
  the IDE response path; a missing node must skip one write, not the request.
- **Payload-shape guard.** Upstream reads `data.debugToolbar.panels` and every
  panel entry unconditionally, so a `debugToolbar` value that is `null`, a
  scalar, or an object without `panels` — or a panel entry that is not an
  object — throws a `TypeError` out of the patched `JSON.parse` /
  `Response.prototype.json` and breaks the caller's parse. The port asks the one
  question the DOM update depends on, "can keys be read from this value", with
  a single record predicate (`value !== null && typeof value === "object"`,
  defined once as `isRecord`) applied at every read site: `data` itself at the
  entry guard above, the captured `toolbar`, its `panels`, and each `panel`
  inside the loop. A payload the DOM
  update cannot read returns the already-scrubbed data; a panel entry it cannot
  read skips that one panel. The scrub stays unconditional and precedes this
  guard, so the server-only key is deleted from the response even when the
  payload is malformed. The guard is written against that answer, never against
  an enumeration of bad-input spellings, and never as a `try` / `catch` around
  the DOM work (a swallowed exception would hide a real toolbar-DOM bug behind a
  silent no-op). The `data-request-id` write stays upstream's: `setAttribute`
  coerces a non-string value and never throws for one, so a missing `requestId`
  degrades to the stock toolbar's own panel-miss fallback.

The DOM-update body is otherwise upstream's: the asset is a single `<script>`
IIFE with **no Django template tags at all** — no `{% load %}`, no `{% static %}`,
no `{% url %}`, and no pre-existing header comment to adapt. The only renamed
path in this card is the `render_to_string(...)` argument in the middleware,
which is not in the asset. Test 16 pins both the preserved invariants and the
diverged forms — the scrub-before-bail ordering, the shadow-DOM resolution, the
per-node guards and the payload-shape guard included — one test row per
predicate, so a dropped form fails its own rows and none can silently regress.

### Explicitly do not borrow

- **The hard `debug_toolbar` import.** Upstream imports `debug_toolbar.*` at
  module top level unguarded — it can afford to because its `debug-toolbar`
  extra and its docs gate who imports the module. This package's floor is
  "importable with zero optional dependencies"; the import stays
  at module top level (the class body needs it) but runs **behind the guard**
  ([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).
- **The `middlewares/` (plural) package name.** The package's own subpackage
  names are singular-noun subsystems (`optimizer/`, `auth/`, `testing/`). Documented divergence, zero
  consumer impact — consumers type the dotted path once
  ([Decision 4](#decision-4--module-template-and-test-locations-a-middleware-subpackage-an-in-package-template-asset-testsmiddleware)).
- **Upstream's dependency floor.** `django-debug-toolbar>=6.0.0` is upstream's
  declaration; `6.0.0` predates the Django 6.0 classifier this package
  advertises, so the package's floor is `>=7.0.0`
  ([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).

## User-facing API

The consumer's setup is the toolbar's own **three** standard pieces — app,
middleware, URLconf (the shape of the toolbar's own
[installation docs][debug-toolbar-install-docs]) — with one package-specific swap (the package middleware
**replaces** the stock `debug_toolbar.middleware.DebugToolbarMiddleware` entry,
exactly as upstream's does — it subclasses it, so listing both would run the
toolbar twice). All three pieces are load-bearing, and omitting the URLconf
fails **loudly, on every toolbar-processed request** — not quietly at
panel-click time: the stock `_postprocess` renders the toolbar
**unconditionally** for every response it processes, HTML and JSON alike
(7.0.0's "Always render the toolbar for the history panel" line), and that
render reverses `djdt:` routes inside `debug_toolbar/base.html`
(`{% url 'djdt:render_panel' %}`). `render_toolbar`'s `except` catches only
`TemplateSyntaxError`, so with the `djdt` namespace unregistered the very
first GraphiQL GET or tagged JSON POST dies with `NoReverseMatch` (under
`DEBUG=True`, the Django error page). The toolbar surfaces a missing URLconf
at **request time**, not via a startup system check: no general system check
fires for a `DEBUG=True` dev who omits `debug_toolbar_urls()` (the one check
keyed on `show_toolbar_changed and not toolbar_urls_installed`, `apps.py`'s
`E001`, is scoped to test runs — `not settings.DEBUG and IS_RUNNING_TESTS` —
and reports "The Django Debug Toolbar can't be used with tests", not a missing
URLconf). The dev-time signal is the `NoReverseMatch` above. The support-facing
consequence: "I added the middleware and my whole GraphQL endpoint 500s"
means the URLconf step was skipped.

Omitting the **app** fails even earlier and just as loudly: the package
middleware's module import defines a Django model (`debug_toolbar` ships
`HistoryEntry`), so with `"debug_toolbar"` absent from `INSTALLED_APPS` the leaf
raises `ImproperlyConfigured` naming the missing app at import (server boot /
`MIDDLEWARE` resolution) — the package's own wiring gate
(`apps.is_installed("debug_toolbar")`), in place of Django's cryptic
`HistoryEntry` app-label `RuntimeError` ([Error shapes](#error-shapes)). The
support-facing consequence: "the server won't start after I added the
middleware" means the `INSTALLED_APPS` step was skipped.

```python
# settings.py — dev only, the standard django-debug-toolbar setup
INSTALLED_APPS = [
    # ...
    "django_strawberry_framework",   # already present: the package's AppConfig
    "debug_toolbar",
]

MIDDLEWARE = [
    # The toolbar middleware goes as early as possible — after any
    # response-encoding middleware (e.g. GZipMiddleware) so it sees decoded
    # bodies, before everything else. Use the package class INSTEAD OF
    # "debug_toolbar.middleware.DebugToolbarMiddleware" — never both (it
    # subclasses the stock one; listing both runs the toolbar twice).
    "django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware",
    # ... your other middleware ...
]

INTERNAL_IPS = ["127.0.0.1"]
```

```python
# urls.py — the third standard piece: the toolbar's panel-content routes.
from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    # ... your GraphQL / admin / app routes ...
] + debug_toolbar_urls()   # DEBUG-gated: returns [] when DEBUG is False
```

Consumer-visible behavior:

- **The GraphiQL page carries the toolbar.** A GET of the GraphQL endpoint
  (the GraphiQL IDE HTML) renders with the stock toolbar handle — that part is
  the stock middleware's own work — plus the package's appended script asset.
- **Every GraphQL JSON response gets the panel payload — and the injection is
  view-scoped, not IDE-scoped.** This is the one contract subtlety worth stating
  plainly: the borrowed gate marks a request when its resolved view is a
  Strawberry Django view (`issubclass(view, BaseView)`), **not** when the
  request came from the GraphiQL IDE. So while the toolbar is enabled, *every*
  JSON response from that view — the IDE's own `fetch`, but equally a
  programmatic `POST /graphql/` from an API client, `curl`, a Django test, or
  frontend code — receives the extra top-level `debugToolbar` key (panel titles
  / subtitles + the toolbar `requestId`), unless skipped by the introspection
  rule below. The appended template strips the key **only in the GraphiQL page**
  where that script has run — updating the toolbar DOM and hiding the key from
  the IDE's response pane; a non-IDE client that does not load the template sees
  the raw extra key. This is verbatim upstream behavior (the
  `strawberry-graphql-django` port has the same side effect), accepted as the
  price of the one-settings-string migration
  ([Decision 6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types)).
  Clicking a panel in the IDE lazily fetches its full content from the toolbar's
  panel routes ([`debug_toolbar_urls()`](#user-facing-api)) via the request id —
  SQL, timing, everything the stock toolbar records.
- **Introspection is skipped.** GraphiQL and IDE tooling poll
  `IntrospectionQuery` constantly; a JSON response whose `operationName` is
  `"IntrospectionQuery"` is left untouched so the toolbar's request history is
  not flooded
  ([Decision 8](#decision-8--the-introspection-query-skip-is-preserved-verbatim)).
- **Non-GraphQL traffic is untouched.** The overrides tag only requests whose
  resolved view is a Strawberry Django view; everything else flows through the
  stock middleware behavior unchanged.
- **Production inertness is the toolbar's own.** The stock middleware disables
  itself unless the resolved show-toolbar callback allows the request; the
  default gate returns `False` when `settings.DEBUG` is false and otherwise
  only when `REMOTE_ADDR` is in `INTERNAL_IPS` (verified in
  `debug_toolbar.middleware.show_toolbar` at 7.0.0 — `DEBUG` is the first,
  decisive check). The subclass changes none of that gating.
- **Migration is the one settings string:**

  ```diff
  MIDDLEWARE = [
  -    "strawberry_django.middlewares.debug_toolbar.DebugToolbarMiddleware",
  +    "django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware",
  ]
  ```

- **Without `django-debug-toolbar` installed**, the settings entry (or any
  direct `import django_strawberry_framework.middleware.debug_toolbar`) raises
  `ImportError` at Django startup with the install hint naming the verified
  floor — at the first moment the integration is actually reached for, never at
  `import django_strawberry_framework`.

### Error shapes

- **`django-debug-toolbar` absent** — `ImportError` from the module import,
  message naming the package and floor (working text, single-sited in
  `_DEBUG_TOOLBAR_INSTALL_HINT`): `"DebugToolbarMiddleware requires
  django-debug-toolbar, which is not installed. Install it with `pip install
  'django-debug-toolbar>=7.0.0'` (the package's verified debug-toolbar
  floor)."` — the wording mirrors the DRF / channels hints so the soft
  dependencies fail identically. The hint is public API in practice — it
  is the error a deploying consumer follows — so it names the **one** floor
  the package verified, whose Django coverage reaches 6.0 and stops short of
  the `6.1` [`pyproject.toml`][pyproject] also advertises
  ([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).
  `require_debug_toolbar()` runs first and imports **only the top-level
  `debug_toolbar` package** (`require_optional_module("debug_toolbar", …)`), so
  it catches — and routes through the single hint, original `ImportError`
  chained (`__cause__`) — both a true absence **and** any `ImportError` raised
  while importing `debug_toolbar/__init__.py` itself, including a missing
  transitive dependency of the toolbar. That is acceptable here because the
  toolbar's `__init__` is lightweight (a version string and a couple of
  re-exports); if a future toolbar release grew a heavy `__init__` with its own
  optional imports, a genuine transitive failure would be mis-hinted as "not
  installed", and the guard would need widening — noted so the trade-off is
  explicit, not silent.
- **Present-but-broken installs** — `require_debug_toolbar()` passes (the
  top-level package imports) but a **class-body submodule import** then fails
  (`debug_toolbar.middleware` / `debug_toolbar.toolbar` / `strawberry.django.views`
  reshaped or half-installed). The guard does **not** cover these — it imported
  only the top-level package — so the raw `ImportError` propagates unwrapped,
  naming the real missing module, which is already actionable
  (`debug_toolbar.middleware` can only mean the toolbar install). Unlike the
  router's two-package boundary ([`spec-041`][spec-041] split messages), no
  second wrap message is added; the split there existed because the router's
  builder imported from two packages, whereas here the only wrapped import is
  the single top-level package. The [Test plan](#test-plan) still pins the
  degraded path so the propagation shape is contractual, not accidental.
- **`django-debug-toolbar` installed but `"debug_toolbar"` absent from
  `INSTALLED_APPS`** — a distinct, common misconfiguration (as likely as a
  forgotten `debug_toolbar_urls()`): `require_debug_toolbar()` passes (the
  top-level package imports), but the `debug_toolbar.middleware` import below
  reaches `debug_toolbar.models.HistoryEntry` (via `debug_toolbar.store`), and
  **defining a Django model whose app is not installed** raises Django's
  `RuntimeError` naming `HistoryEntry` — never the missing app, so it is *not*
  self-actionable (unlike the broken-install `ImportError` above, which names the
  real module). The leaf therefore adds a **second wiring gate** immediately
  after the package guard: `apps.is_installed("debug_toolbar")` (the app registry
  is ready by the time Django's `MIDDLEWARE` resolution imports the leaf), which
  raises the single `ImproperlyConfigured` carried in `_DEBUG_TOOLBAR_APP_HINT`
  and names the fix. This is the one place the card diverges from a pure
  `ImportError` error model — an `INSTALLED_APPS` omission is a settings error
  and `ImproperlyConfigured` is Django's idiom for it; the earlier "top-level
  package only" scope governs `require_debug_toolbar()`'s *import* guard, a
  separate concern from this *wiring* gate. The [Test plan](#test-plan) pins the
  shape (toolbar importable, app omitted, `ImproperlyConfigured` asserted).
- **Middleware listed but the view never matches** (a consumer whose GraphQL
  view is not a Strawberry Django view — a hand-rolled view, or an
  ASGI-consumer-only deployment) — not an error: `_is_graphiql` stays `False`,
  the overrides pass everything through, and the stock toolbar behavior is all
  that remains. The GLOSSARY body documents the detection contract so this
  reads as designed behavior, not silence.
- **A GraphQL JSON response whose media type is not `application/json`** — the
  JSON-injection path keys on `Content-Type == "application/json"` exactly as
  upstream does, so a response served as `application/graphql-response+json`
  (the GraphQL-over-HTTP "watershed" media type) is **not** injected. This is
  **in scope as a documented non-goal, not a defect**: Strawberry's
  Django view returns `application/json` today, so the card matches upstream and
  does not diverge for a media type the engine does not yet emit. Broadening the
  sniff to a `{"application/json", "application/graphql-response+json"}` set is a
  clean follow-up compatibility card if/when Strawberry emits the newer type;
  pinning the decision here keeps the gap explicit rather than a silent future
  regression. (Contrast the divergences the card *does* take — the `isinstance`
  guard, the response-shape and `Content-Encoding` bails, and the template
  hook's guard family — which prevent crashes rather than add a speculative
  feature.)
- **A strict Content Security Policy on the GraphiQL page** — the HTML path
  appends an inline `<script>` (the ported bridge asset) to the GraphiQL
  response, matching upstream and its `django-graphiql-debug-toolbar` lineage. A
  strict CSP without an `unsafe-inline` / matching hash for that script will
  **block it**: the server-side toolbar history still records, but the GraphiQL
  page will not consume or strip the `debugToolbar` key from JSON responses, so
  a non-IDE client watching that endpoint could observe the extra top-level
  `debugToolbar` key. Dev-only, but real: a CSP consumer has to allow the
  toolbar script or accept that the GraphiQL DOM updates will not run.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec stem is `spec-042-debug_toolbar-0_0_14`: card NNN `042`, topic slug
`debug_toolbar` (the card's subject), version segment `0_0_14` from the card's
trailing `-0.0.14`. Follows the [`docs/SPECS/NEXT.md`][next] convention. The file
is archived at `docs/SPECS/`, its `-terms.csv` and `-rationale.md` companions at
`docs/SPECS/appx/`.

Alternatives rejected: [rationale][rationale-d1].

### Decision 2 — Card-scope boundary: the server-side toolbar integration ships; the in-response surface and async verification stay out

This card ships exactly the card's DoD: the middleware module, the template
asset, the soft dependency, and the two test paths. Three adjacent-looking pieces
of work are explicitly out:

- **The in-response `extensions["debug"]` surface.** That is the sibling card
  [`DONE-044-0.0.14`][kanban]
  ([Response-extensions debug middleware][glossary-response-extensions-debug-middleware]),
  graphene-django parity with a completely different mechanism (a Strawberry
  `SchemaExtension`, no toolbar, no template). The card bodies of both cards
  name each other as "distinct from"; blending them here would entangle two
  parity stories with different upstreams. The one deliberate touch point:
  Slice 2's GLOSSARY body-edit keeps the two entries' "distinct from"
  cross-links accurate.
- **Not a Channels / ASGI toolbar integration.** Three precise statements, so
  "Django served under ASGI" is never conflated with "Channels consumer
  traffic": (1) the **tested contract** is sync Django test-client traffic
  through fakeshop's mounted GraphQL view — a Django **HTTP middleware**
  wrapping a Strawberry **Django view**; (2) a Django `ASGIHandler` deployment that
  runs the normal Django middleware chain **may be structurally compatible** —
  the stock toolbar middleware has been async-capable since its 4.x line and
  the subclass inherits `async_capable` — but this card does not verify it and
  claims nothing about it ([Risks](#risks-and-open-questions)); (3) **Channels
  consumers are out of scope entirely**: this is not an integration for the
  [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] Channels
  transport that landed in the same `0.0.14` line ([`spec-041`][spec-041]) —
  `django-debug-toolbar`'s own documentation calls out async limitations and
  states Channels is not supported, a Django HTTP middleware never runs in a
  Channels consumer's ASGI path, and the router is not expected to run this
  middleware.
- **No new `Meta` / settings key.** The middleware is configured where every
  Django middleware is configured — the `MIDDLEWARE` list — and the toolbar is
  configured where the toolbar documents (`DEBUG_TOOLBAR_CONFIG`). Nothing
  reads [`conf.py`][conf]; `DEFERRED_META_KEYS` is untouched. The
  [`START.md`][start] rule ("add a settings key only when the feature that
  needs it lands") — no feature here needs one.

Alternatives rejected: [rationale][rationale-d2].

### Decision 3 — The symbol is `DebugToolbarMiddleware` — same class name, distinctly-ours dotted path

The class is named `DebugToolbarMiddleware`, matching both upstream's subclass
**and** the stock `django-debug-toolbar` class it extends. A Django middleware is
referenced by dotted settings string —
`"django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware"` —
so the module path is the distinctly-ours identity and the class name is the
Django-ecosystem convention (`SessionMiddleware`, `AuthenticationMiddleware`,
`DebugToolbarMiddleware`) consumers pattern-match, never a namespace anyone
imports across packages.

No package-root re-export, and no `middleware/__init__.py` re-export either:
the consumer surface is the full dotted path in a settings string, mirroring
the structural-opt-in posture ([`spec-040`][spec-040] Decision 3 /
[`spec-041`][spec-041] Decision 3) — a consumer who never uses the toolbar
never types the path, and [`__init__.py`][init]'s `__all__` stays
toolbar-free by construction. The module needs no `__all__` gymnastics and no
`# noqa: F822`: unlike the router's [PEP 562 lazy
export][glossary-pep-562-lazy-export], `DebugToolbarMiddleware` is a real
module global once the module imports
([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).

Alternatives rejected: [rationale][rationale-d3].

### Decision 4 — Module, template, and test locations: a `middleware/` subpackage, an in-package template asset, `tests/middleware/`

The module is `django_strawberry_framework/middleware/debug_toolbar.py` — a
`middleware/` **subpackage** leaf, not a top-level `middleware.py` (the
subpackage also holds [`spec-046`][spec-046]'s `request_body.py`). Two reasons:
the leaf-module shape is what makes the import-time guard clean (the subpackage
`__init__.py` stays importable while the leaf is the opt-in — the
`rest_framework/` precedent,
[Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape));
and upstream uses the same package-with-leaf shape (`middlewares/debug_toolbar.py`).
The package name is **singular** `middleware/` where upstream is plural — the
package's subpackage names are singular-noun subsystems (`optimizer/`, `auth/`,
`testing/`); a one-character copy of upstream's plural would diverge from the
package's own convention to match a name consumers never see benefit from.

The template ships **inside the package** at
`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
(the doubled directory is Django's app-template namespacing convention) and is
rendered via `render_to_string("django_strawberry_framework/debug_toolbar.html")`.
Resolution rides Django's `APP_DIRS` template loader against the package's
shipped [`AppConfig`][glossary-django-appconfig] — consumers already list
`"django_strawberry_framework"` in `INSTALLED_APPS` (the package's documented
install step), so the template resolves with zero new setup.
Packaging needs no new build configuration: [`pyproject.toml`][pyproject]'s
hatchling wheel target packages the `django_strawberry_framework` directory
wholesale, non-Python files included.

The tests split across two trees. `tests/middleware/test_debug_toolbar.py` — a
`tests/` package mirroring the source subpackage, the same shape `tests/auth/` /
`tests/rest_framework/` use for their subpackages (the top-level
`tests/test_routers.py` shape applies to top-level modules, which this is not) —
owns the paths no live `/graphql/` request can reach. The toolbar-present tests
that drive a real request live in the live tier at
`examples/fakeshop/test_query/test_debug_toolbar_api.py`, because the example's
shipped settings wire the toolbar ([Decision 9](#decision-9--test-strategy-live-tier-tests-through-fakeshops-shipped-toolbar-package-tests-for-the-paths-no-live-request-reaches-eviction-simulated-absence)).

Alternatives rejected: [rationale][rationale-d4].

### Decision 5 — Soft `django-debug-toolbar` dependency: an import-time `require_debug_toolbar()` guard (the `rest_framework/` shape)

`django-debug-toolbar` joins `djangorestframework` and `channels` as the
package's third [soft dependency][glossary-soft-dependency], with the
established three-part architecture — but using the **import-time guard**
variant (the `rest_framework/` shape), not the router's [PEP 562
lazy-symbol][glossary-pep-562-lazy-export] variant:

1. **One guard, one hint — built on the shared optional-import owner.**
   `middleware/debug_toolbar.py` defines `require_debug_toolbar()` as a thin
   wrapper over
   [`require_optional_module`][glossary-require-optional-module]
   ([`utils/imports.py`][utils-imports] — no hand-rolled import pattern of its
   own), passing the single
   `_DEBUG_TOOLBAR_INSTALL_HINT` string naming the verified
   `django-debug-toolbar>=7.0.0` floor. No memoization: absence tests re-hit
   the guard after eviction, the [`require_drf()`][rf-init] /
   `require_channels()` contract.
2. **The guard runs at module import time, and the class is a plain module
   global.** The module body is: `require_debug_toolbar()`, then the
   `apps.is_installed("debug_toolbar")` wiring gate ([Error shapes](#error-shapes)),
   then the `debug_toolbar.middleware` / `debug_toolbar.toolbar` (and
   `strawberry.django.views`) imports, then `_HTML_TYPES`, `_get_payload`, and
   the `DebugToolbarMiddleware` class. This is the card's own DoD wording ("the
   middleware module raises `ImportError` with an install hint when actually
   imported") and the `rest_framework/` precedent. The rule the two shapes
   divide on: a top-level module innocent whole-package walkers must traverse
   lazies; a dedicated opt-in leaf guards at import. This is a leaf — nothing
   imports
   `django_strawberry_framework.middleware.debug_toolbar` except a consumer's
   `MIDDLEWARE` setting (via Django's `import_string` at startup) or an
   explicit import — both are the opt-in. The parent
   `middleware/__init__.py` imports nothing optional, so package walkers
   traverse cleanly; only the leaf pays.
3. **The dependency gate.** **`django-debug-toolbar>=7.0.0`** sits in
   `[dependency-groups].dev`, with `uv.lock` carrying it (the
   [`spec-039`][spec-039] lockfile discipline). **The floor is `7.0.0`,
   single-valued across the hint, the dev group, and the re-typed test
   literal** — deliberately above upstream's `>=6.0.0`, because `7.0.0` is the
   first release whose Django classifiers reach the `6.0` this package
   advertises. The [`spec-041`][spec-041] single-floor rule applies verbatim:
   the install hint is the error message a deploying consumer follows, so it
   must not guide a Django 6.0 user into an unsupported toolbar. The floor's
   Django coverage reaches 6.0 and stops short of the `6.1`
   [`pyproject.toml`][pyproject] also advertises — a gap recorded deliberately.
   The three-places-that-must-agree rule holds, and it names the **gated** trio:
   the package test compares the hint to the re-typed literal and the literal
   to the [`pyproject.toml`][pyproject] dev-group row, so none of the three can
   move alone. It is not a census of everywhere the floor is written — the
   consumer docs restate it ungated — so a bump sweeps the tree rather than
   trusting an enumeration, and sweeps for the package **name**, reading each
   hit: a needle carrying the `>=` misses a restatement that puts a backtick or
   a space between the name and the constraint, so the specifier is a narrower
   instrument than the population it is aimed at.

Alternatives rejected: [rationale][rationale-d5].

### Decision 6 — Subclass-and-override, borrowed as-is: `process_view` + `_postprocess`, `_get_payload`, `_HTML_TYPES`

The middleware **subclasses** `debug_toolbar.middleware.DebugToolbarMiddleware`
and overrides exactly two methods; the module carries the `_get_payload` helper
and `_HTML_TYPES` constant at module level. Every behavior is upstream's,
verbatim (the card's architectural posture: "Not a from-scratch middleware...
we do not re-implement the panel-rendering logic that `django-debug-toolbar`
already owns"):

- **`process_view(request, view_func, *args, **kwargs)`** — resolve
  `view = getattr(view_func, "view_class", None)` (the attribute Django's
  `View.as_view()` sets on the returned callable) and tag
  `request._is_graphiql = isinstance(view, type) and issubclass(view,
  BaseView)`. The override does not chain to `super()` — and does not need to:
  the stock `debug_toolbar.middleware.DebugToolbarMiddleware` defines no
  `process_view` of its own (it is a `__call__` / `__acall__`-style
  middleware), so there is no stock hook to
  preserve. This method's one deliberate divergence from upstream (the first of
  the module's three — the others are `_get_payload`'s response-shape bails and
  `_postprocess`'s `Content-Encoding` bail) is the
  `isinstance(view, type)` guard in front of `issubclass`: upstream writes
  `bool(view and issubclass(...))`, which raises `TypeError` if a `view_class`
  attribute is ever a non-class, and this middleware runs `process_view` for
  **all** global traffic (see
  [Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned)).
  Otherwise mirroring upstream. (Verified against the upstream source: its
  `process_view` body is the two lines above modulo that guard, no `super()`
  call — and against the toolbar sources: no stock `process_view` to chain to.)
- **`_postprocess(request, response, toolbar)`** — chain to
  `super()._postprocess(...)` **first**. What the stock method does at 7.0.0,
  in order: generates stats and server timing for **every** enabled panel;
  **renders and stores the toolbar for every processed response** — JSON
  included ("Always render the toolbar for the history panel"); adds panel
  headers; and only then, conditionally, inserts the handle into processable
  HTML. The unconditional render/store is the mechanism this whole card rides:
  it is why a JSON operation gets a history row and stored panel content that
  `render_panel` can later serve (Test 6), why a missing URLconf's
  `NoReverseMatch` fires on JSON requests too — the render reverses `djdt:`
  routes ([User-facing API](#user-facing-api)) — and why every tagged JSON
  operation pays a full server-side toolbar render in dev (expected
  upstream-parity behavior, stated so it isn't a surprise). The package must
  not re-implement or skip any of it. Then:
  - **streaming responses return immediately** (no body to inspect or mutate);
  - **an encoded body returns immediately** — a response carrying a
    `Content-Encoding` header is left untouched, the module's third deliberate
    divergence from upstream. The stock postprocess refuses encoded bodies for
    the same reason its own HTML handle insertion operates on decoded bytes:
    appending the bridge script to a gzipped body, or re-encoding one as JSON,
    corrupts the response. The middleware's documented ordering guidance —
    place it after any response-encoding middleware — is what keeps this an
    edge case rather than the normal path;
  - **HTML path** — `Content-Type`'s first segment in `_HTML_TYPES`, request
    tagged `_is_graphiql`, status 200: append
    `render_to_string("django_strawberry_framework/debug_toolbar.html")` via
    `response.write(...)` and refresh `Content-Length` when the header is
    present. This is what arms the GraphiQL page: the stock `_postprocess`
    injected the toolbar UI; the appended script teaches it to update from
    fetch responses.
  - **JSON path** — request tagged `_is_graphiql` and `Content-Type` is
    `application/json`: read `operationName` from `json.loads(request.body)`
    (**any** exception → `None` — malformed bodies, multipart bodies, GET
    queries with no body all degrade to "inject"); skip entirely when it is
    `"IntrospectionQuery"`
    ([Decision 8](#decision-8--the-introspection-query-skip-is-preserved-verbatim));
    otherwise `_get_payload(request, response, toolbar)` and — when it returns
    a payload — re-encode `response.content = json.dumps(payload,
    cls=DjangoJSONEncoder)` and refresh `Content-Length`.
- **`_get_payload`** — `None` when the toolbar assigned no `request_id`
  (nothing to reference); `None` again on any **response-shape** failure — the
  bytes cannot be decoded with the response's declared charset, the decoded text
  is not valid JSON, or the decoded body is not a JSON object. That family is the
  module's second deliberate divergence from upstream, which decodes and
  subscript-assigns unconditionally: a declared-JSON response the middleware
  cannot read is left alone rather than turned into a 500, because a dev-only
  diagnostic must never be the thing that breaks a request. Otherwise decode
  the response body with the
  response's own charset, attach `debugToolbar = {"panels": ..., "requestId":
  toolbar.request_id}` from `reversed(toolbar.enabled_panels)` — per panel,
  `title` only when `panel.has_content` (else `None`, which the frontend
  treats as "don't touch this panel's content area") and `nav_subtitle`, both
  called when callable — and **skip `TemplatesPanel`** (upstream's comment-free
  but deliberate exclusion: the panel's nav content churns per request and the
  lazy re-fetch handles it poorly).
- **`DjangoJSONEncoder`** for the re-encode — the payload embeds panel
  subtitle values that can be lazy translation proxies / datetimes; Django's
  encoder is the one that serializes them.

Alternatives rejected: [rationale][rationale-d6].

### Decision 7 — Strawberry-view detection: `issubclass` against `strawberry.django.views.BaseView` (engine-owned)

The detection target is the **engine-owned** `strawberry.django.views.BaseView`,
exactly as upstream's is — never a package-owned class. `BaseView` holds the
shared constructor and both `GraphQLView` and `AsyncGraphQLView` subclass it, so
the check is engine-shaped rather than package-shaped and covers every consumer
who wires a Strawberry Django view, subclassed or not. This is the "keeps Strawberry
as the engine" line ([`README.md`][readme]) applied to view identity, the
same way [`spec-041`][spec-041] Decision 7 applied it to the Channels consumers.

**The package's own views are covered by the same one line.**
[`views.py`][views]'s `DjangoGraphQLView` and `AsyncDjangoGraphQLView` mix the
package's request-body boundary into Strawberry's `GraphQLView` /
`AsyncGraphQLView`, which subclass `BaseView` — so
`issubclass(view, BaseView)` resolves for them, and fakeshop's `/graphql/` mount
(which is the package view, decorated with `ensure_csrf_cookie`) is detected
through the engine base with no package-specific branch. Keeping the target
engine-owned is what makes that true without this module knowing the package's
view exists.

Three mechanical notes the implementation carries:

- `strawberry.django.views` is **Strawberry core's** Django integration, not
  `strawberry-graphql-django`; the import adds no dependency. Its presence is
  confirmed by the view-class gate ([Slice checklist](#slice-checklist)) against the package's declared
  `strawberry-graphql` floor — read at gate time from
  [`pyproject.toml`][pyproject] and [`docs/builder/BUILD.md`][build]
  `## Floor verification`, never from a version restated here (a floor written
  into a spec rots the moment the floor moves). It is imported at module level
  *after* the guard — it needs Django configured but nothing optional.
- The `view_class` attribute survives decoration: `View.as_view()` sets it on
  the returned function, and Django's stacked decorators
  (`ensure_csrf_cookie`, which fakeshop's URLconf actually applies) copy
  function `__dict__` via `functools.wraps` — so the mounted view is detected
  through its decorator, and the test plan pins exactly that path (the tests
  drive fakeshop's real decorated URL).
- **The `issubclass` call is guarded with `isinstance(view, type)`** —
  `process_view`'s one deliberate divergence from upstream's verbatim `bool(view and
  issubclass(view, BaseView))`, added because this middleware is installed
  globally and `process_view` runs for **every** request, GraphQL or not.
  `view = getattr(view_func, "view_class", None)` is normally `None` (function
  views) or a class (`View.as_view()`), but nothing forbids an unrelated
  decorator or helper from attaching a **non-class** `view_class`; a bare
  `issubclass(non_class, BaseView)` raises `TypeError`, which — on the global
  middleware path — would 500 an unrelated view. `isinstance(view, type)`
  short-circuits to `False` first (reproduced: `issubclass("x", BaseView)`
  raises `TypeError: issubclass() arg 1 must be a class`). This is a strict
  robustness improvement, not a detection change: `None` and every real view
  class resolve identically to upstream, so no legitimate Strawberry view's
  detection differs. It joins the module's other documented divergences (the
  `middleware/` rename, the `>=7.0.0` floor, the
  `_get_payload` response-shape bails, the `Content-Encoding` bail, and the
  template hook's guard family) rather than silently breaking the "borrow
  verbatim" posture, and Test 14a pins the non-class case the real-request tests
  cannot reach.

Alternatives rejected: [rationale][rationale-d7].

### Decision 8 — The introspection-query skip is preserved, verbatim

When a Strawberry-view JSON request's `operationName` is
`"IntrospectionQuery"`, no payload is computed and the response passes through
untouched. The reason is upstream's, kept in the module as a comment: IDEs
(Apollo Sandbox, GraphiQL's own schema poller) issue introspection constantly
in the background; injecting per-introspection payloads floods the toolbar's
request history and evicts the developer's actual operations from it. The
detection reads the request body's `operationName` field — the standard GraphQL
POST envelope — with the broad-exception fallback to `None` (a body that
cannot be parsed is by definition not the IDE's introspection poll).

The skip is **name-based, not content-based**: a consumer who issues an
introspection query under a different `operationName` gets a payload, and a
consumer who names a data query `IntrospectionQuery` loses its payload. The
contract is identical to upstream's, which is what the one-settings-string
migration ([Goal 3](#goals)) rests on.

Alternatives rejected: [rationale][rationale-d8].

### Decision 9 — Test strategy: live-tier tests through fakeshop's shipped toolbar; package tests for the paths no live request reaches; eviction-simulated absence

Test placement follows the [live-first mandate][glossary-live-first-coverage-mandate]:
a package line covered by a real fakeshop GraphQL request **through the example's
shipped configuration** belongs in `examples/fakeshop/test_query/`, and everything
else stays package-internal. `middleware/debug_toolbar.py` falls on both sides of
that line, so the tests split across two trees:

- **`examples/fakeshop/test_query/test_debug_toolbar_api.py` — the toolbar-present
  group.** Fakeshop's shipped settings wire the toolbar's three pieces:
  `"debug_toolbar"` in `INSTALLED_APPS`, the package middleware's dotted path near
  the front of `MIDDLEWARE`, `INTERNAL_IPS`, and `debug_toolbar_urls()` appended in
  [`config/urls.py`][config-urls]. So the middleware is in the example's real
  request path and these tests drive it there — the real GraphiQL HTML render
  (through the real `ensure_csrf_cookie` decorator, proving the `view_class`
  detection survives decoration), and a real products query emitting real SQL
  through the real optimizer.
- **`tests/middleware/test_debug_toolbar.py` — the paths no live request can
  reach.** The soft-dependency absence matrix (a missing dependency is never a live
  path) and the coverage-only `_postprocess` / `_get_payload` branch units the real
  toolbar lifecycle does not naturally expose, driven directly against
  `RequestFactory` requests and fake toolbar objects.

**The one setting the live tier still overrides is `DEBUG`, and that is
load-bearing.** The checked-in fakeshop [`config/settings.py`][config-settings]
sets `DEBUG = True`, but [`pytest.ini`][pytest-ini] does not set
`django_debug_mode`, so pytest-django defaults it to `False` and forces
`settings.DEBUG = False` for the whole suite at
`setup_test_environment(debug=False)` time — pytest-django's documented
ini-option behavior, a property of the tool rather than of any locally installed
copy. Under `DEBUG=False` the toolbar is inert in **both** directions: the default
gate returns `False` (verified in
[`debug_toolbar.middleware.show_toolbar`][debug-toolbar-middleware-source] at
7.0.0: `if not settings.DEBUG: return False` is the first check), and
[`debug_toolbar_urls()`][debug-toolbar-toolbar-source] returns `[]`, so the `djdt`
routes do not exist. The toolbar-present fixture therefore:

- `override_settings(DEBUG=True)` — re-enables the toolbar's `DEBUG` gate and arms
  the `DEBUG`-gated `debug_toolbar_urls()`.
- **reloads `config.urls` inside that override** — the module-level `urlpatterns`
  are computed **once, at first import**, so a `config.urls` imported under the
  suite's forced `DEBUG=False` holds an empty `debug_toolbar_urls()` result
  permanently for that module object, and every panel-route reverse fails with
  `NoReverseMatch` even though the fixture set `DEBUG=True`. The reload must
  therefore happen while the override is active, and the restore must happen under
  ambient `DEBUG=False` so the `djdt` routes cannot leak into a neighbouring test.
- `override_settings(DEBUG_TOOLBAR_CONFIG={"SHOW_TOOLBAR_CALLBACK": <always-true>,
  "DISABLE_PANELS": {"debug_toolbar.panels.profiling.ProfilingPanel"}})` — pins the
  show-toolbar decision to true regardless of `REMOTE_ADDR` / `INTERNAL_IPS` (the
  default gate's second check), so the test is independent of client-address
  defaults; overriding the callback is `django-debug-toolbar`'s own documented test
  recipe. The narrowed `DISABLE_PANELS` enables `RedirectsPanel` (disabled by
  default), the live panel whose `has_content` is false.

Nothing else is overridden: `INSTALLED_APPS`, `MIDDLEWARE` and `ROOT_URLCONF` are
fakeshop's shipped values. The stock
`debug_toolbar.middleware.DebugToolbarMiddleware` must never appear in that list
beside the package class — the package class subclasses it, and listing both runs
the toolbar twice.

**Cache hygiene is part of the fixture contract, not an afterthought.**
`django-debug-toolbar` 7.0.0 memoizes the resolved show-toolbar callback with
`functools.cache`
([`debug_toolbar.middleware.show_toolbar_func_or_path`][debug-toolbar-middleware-source],
verified `@cache`-decorated), and caches its panel classes and URL patterns on the
toolbar class ([`DebugToolbar._panel_classes` /
`DebugToolbar._urlpatterns`][debug-toolbar-toolbar-source]). **None of them resets
with a settings override**, so a per-test `DEBUG_TOOLBAR_CONFIG` override that does
not clear them leaks a stale always-true callback (or a stale panel/url set) into a
later test on the same worker — especially under `--dist loadscope`, which keeps a
module's tests on one worker, so the local file passes while a neighbour inherits
the leak. The fixture treats these as **save / clear / restore** state, never
set-to-`None` state: on setup it calls
`debug_toolbar.middleware.show_toolbar_func_or_path.cache_clear()`, **saves** the
current `DebugToolbar._panel_classes` / `_urlpatterns` values, then sets both to
`None`; on teardown it calls `cache_clear()` again, discards whatever the test
populated, and **restores the saved values** — so a neighbour (or an earlier
same-worker test that had already initialized the toolbar's caches) gets back
exactly the state it had, rather than a fixture-imposed `None`. The callback
`cache_clear()` is mandatory because it is tied directly to the per-test
`DEBUG_TOOLBAR_CONFIG` override; the panel/url handling is belt-and-suspenders,
since all present-path tests share one toolbar configuration.

One more fixture obligation, from pytest-django rather than the toolbar: the
toolbar-present tests drive fakeshop's real `/graphql/` view and
[`seed_data(1)`][glossary-seed-data] — real ORM traffic — so **the toolbar-present
group carries `pytest.mark.django_db`** (a class-level mark over the group is
preferred, since every test in it can open the database through the fakeshop
schema or the SQL panel). Without the mark, pytest-django's database blocker trips
on the first SQL-emitting request before the middleware behavior is exercised. The
package-tier absence and guard tests are pure import machinery and stay
**unmarked**.

The live tier inherits the acceptance suites' order-independence discipline rather
than carrying its own: it drives the aggregate `config.schema` through the same
project-schema fixture every fakeshop live suite uses, which rebuilds the project
schema and reloads `config.schema` / `config.urls`, so a package test's
`registry.clear()` can never surface here as an order-dependent
`LazyType` `KeyError` / `DuplicatedTypeName` (the
[schema reload discipline][glossary-schema-reload-discipline]). The package-tier
tests never execute GraphQL and need none of it.

The toolbar-absent path uses the
[eviction-simulated absence][glossary-eviction-simulated-absence] discipline
through the shared `tests/_soft_dependency.py` helpers (`simulated_absence` /
`evicted_modules`, which the DRF and channels suites use too): strict
`sys.modules` eviction of `debug_toolbar*` and
`django_strawberry_framework.middleware`, with the **two-sided restore** (the
parent package's `middleware` attribute is saved/restored alongside the
`sys.modules` entries, putting the original module object back in both places,
which closes the `pytest-xdist` order-dependence hole), and the absence itself
simulated with an **importlib-compatible `sys.modules["debug_toolbar"] = None`
sentinel**. The sentinel is load-bearing: `require_debug_toolbar()` is a thin
[`require_optional_module`][glossary-require-optional-module] wrapper, i.e. an
`importlib.import_module("debug_toolbar")` call, and `importlib` routes through
`importlib._bootstrap._gcd_import` — it does **not** consult
`builtins.__import__`. A `__import__` block is therefore a no-op for this guard: it
re-imports the still-installed toolbar and the guard returns it, so the raise (if
any) would come from a later hintless statement-import rather than the wrapped
guard, and the absence tests would pass for the wrong reason. A `None` entry in
`sys.modules` is the documented importlib absence sentinel: `import_module` raises
`ModuleNotFoundError` (`"import of debug_toolbar halted; None in sys.modules"`),
which the guard catches and re-raises as the install hint.

One package-tier ordering obligation follows from the toolbar's own import chain:
`debug_toolbar.middleware` defines a Django model, so the **first** leaf import in
a process must happen with `"debug_toolbar"` in `INSTALLED_APPS`. The package-tier
fixture owns that explicitly rather than relying on an earlier same-worker test
having imported the leaf, which is what keeps the absence tests and the targeted
units order-independent under `pytest-xdist`.

The install hint is matched against a **re-typed literal** in the test file (the
`_HINT_SUBSTRING` drift-catch discipline — a test asserting the imported constant
against itself could never notice the hint drifting from the dev-group floor).

Alternatives rejected: [rationale][rationale-d9].

### Decision 10 — Version bumps are owned by the joint `0.0.14` cut

No slice in this card edits the package version: `__version__` in
[`__init__.py`][init] (the single source; hatchling derives the packaging version
from it) or [`tests/base/test_init.py::test_version`][test-base-init]. This card shares the
`0.0.14` patch line with [`DONE-041-0.0.14`][kanban], [`DONE-043-0.0.14`][kanban]
and [`DONE-044-0.0.14`][kanban], and the bump, the release-status flips and the
`CHANGELOG.md` bullets belong to the **[joint `0.0.14`
cut][glossary-joint-version-cut]**, not to any one card.

**`uv.lock` is not version state.** The dependency gate's
`django-debug-toolbar` dev-group row is locked in this card.

Alternatives rejected: [rationale][rationale-d10].

## Implementation plan

The file-level map (each row's contract is
specified in the decisions cited; **no slice bumps the version** — the joint
`0.0.14` cut owns it,
[Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)):

| File | Change | Slice |
| --- | --- | --- |
| [`pyproject.toml`][pyproject] + `uv.lock` | `django-debug-toolbar>=7.0.0` in `[dependency-groups].dev`, locked | 1 |
| `django_strawberry_framework/middleware/__init__.py` | Subpackage marker, docstring only; imports nothing optional ([Decision 4](#decision-4--module-template-and-test-locations-a-middleware-subpackage-an-in-package-template-asset-testsmiddleware)) | 1 |
| `django_strawberry_framework/middleware/debug_toolbar.py` | `_DEBUG_TOOLBAR_INSTALL_HINT` / `require_debug_toolbar()` (thin [`require_optional_module`][glossary-require-optional-module] wrapper) executed at import; `_HTML_TYPES`; `_get_payload`; `DebugToolbarMiddleware` with `process_view` + `_postprocess` overrides ([Decision 3](#decision-3--the-symbol-is-debugtoolbarmiddleware--same-class-name-distinctly-ours-dotted-path) / [5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape) / [6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types) / [7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned) / [8](#decision-8--the-introspection-query-skip-is-preserved-verbatim)) | 1 |
| `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | The GraphiQL-side JS asset, ported from [upstream][upstream-template] with the render path renamed ([Decision 4](#decision-4--module-template-and-test-locations-a-middleware-subpackage-an-in-package-template-asset-testsmiddleware)) | 1 |
| `tests/middleware/__init__.py` + `tests/middleware/test_debug_toolbar.py` | The package tier of the [Test plan](#test-plan): the soft-dependency absence matrix, the coverage-only targeted units, and the template-port guard — the paths no live `/graphql/` request reaches ([Decision 9](#decision-9--test-strategy-live-tier-tests-through-fakeshops-shipped-toolbar-package-tests-for-the-paths-no-live-request-reaches-eviction-simulated-absence)) | 1 |
| `examples/fakeshop/test_query/test_debug_toolbar_api.py` | The live tier of the [Test plan](#test-plan): real fakeshop `/graphql/` traffic through the example's shipped toolbar wiring, incl. the panel-route fetch, the unrelated-JSON leak guard, the `Content-Encoding` rows, and the fixture's `DEBUG=True` + `config.urls` reload + cache save/clear/restore contract ([Decision 9](#decision-9--test-strategy-live-tier-tests-through-fakeshops-shipped-toolbar-package-tests-for-the-paths-no-live-request-reaches-eviction-simulated-absence)) | 1 |
| [`examples/fakeshop/config/settings.py`][config-settings] + [`config/urls.py`][config-urls] | The example opts into the toolbar: `"debug_toolbar"` in `INSTALLED_APPS`, the package middleware near the front of `MIDDLEWARE`, `INTERNAL_IPS`, and `debug_toolbar_urls()` appended to `urlpatterns` — what puts the toolbar-present tests in the live tier | 1 |
| [`docs/GLOSSARY.md`][glossary] | [Debug-toolbar middleware][glossary-debug-toolbar-middleware] entry body carries the contract | 2 |
| [`docs/TREE.md`][tree] | Regenerated (script-rendered) | 2 |
| [`KANBAN.md`][kanban] / `KANBAN.html` | Card wrap via DB edit + re-render | 2 |

## Helper-reuse obligations (DRY)

The module is small; the ledger is short. Reuse is named per item, and
deliberate *non*-reuse carries its reason (the [`spec-040`][spec-040] /
[`spec-041`][spec-041] discipline).

- [ ] **D1** — the guard rides
  [`django_strawberry_framework/utils/imports.py::require_optional_module`][glossary-require-optional-module]:
  `require_debug_toolbar()` is a thin wrapper passing
  `_DEBUG_TOOLBAR_INSTALL_HINT` — never a hand-rolled import pattern
  ([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).
- [ ] **D2** — the install-hint string lives in exactly one module constant
  (`_DEBUG_TOOLBAR_INSTALL_HINT`), matched in tests by a **re-typed literal**
  (the `_HINT_SUBSTRING` drift-catch discipline the DRF
  ([`test_soft_dependency.py`][test-soft-dependency]) and channels suites
  share).
- [ ] **D3** — the toolbar-absent tests ride the shared
  `tests/_soft_dependency.py` helpers: `simulated_absence` (eviction + the
  **two-sided restore** — the parent package's attribute is saved/restored
  together with the `sys.modules` entries, so no test order leaves the
  attribute path and the import path holding different module objects — plus
  the importlib-compatible `sys.modules["debug_toolbar"] = None` sentinel) for
  pure absence, and `evicted_modules` directly for the broken-install row
  (composed with a submodule sentinel) and the missing-app row
  ([Decision 9](#decision-9--test-strategy-live-tier-tests-through-fakeshops-shipped-toolbar-package-tests-for-the-paths-no-live-request-reaches-eviction-simulated-absence)).
- [ ] **D4** — the guard has **no memoization**, and the module holds **no
  class cache to manage**: unlike the router's `_router_class`, the class is a
  plain module global, so `sys.modules` eviction alone fully resets the
  module's state — one less moving part in the absence fixture
  ([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).
- [ ] **D-N1** (non-reuse) — no re-implementation of anything
  `django-debug-toolbar` owns: no panel logic, no request-id assignment, no
  handle rendering, no history storage. The subclass calls
  `super()._postprocess(...)` before its own work and overrides nothing else
  ([Decision 6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types)).
- [ ] **D-N2** (non-reuse) — the middleware does **not** route through
  [`request_from_info`][glossary-request-from-info]: it is a Django HTTP
  middleware operating on the raw `HttpRequest` / `HttpResponse` pair before
  and after the view, not a resolver-context surface — the helper's
  single-siting rule governs resolver-reachable request decoding, which this
  module never does.
- [ ] **D-N3** (non-reuse) — the JSON body inspection (`json.loads(request.body)`
  for `operationName`) is deliberately local and upstream-shaped, not routed
  through any package parsing helper: it is a best-effort sniff with a
  swallow-everything fallback, semantics no shared helper should advertise.

## Edge cases and constraints

- **`import django_strawberry_framework.middleware.debug_toolbar` on a
  toolbar-less machine.** Raises `ImportError` carrying the install hint, with
  the original chained — this IS the designed behavior (the module import is
  the opt-in,
  [Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).
  The behavior matrix the tests pin: root package import → clean;
  `django_strawberry_framework.middleware` package import → clean; the leaf
  module import → `ImportError` with hint; `from django_strawberry_framework
  import *` → toolbar-free (no root export exists).
- **The consumer must list the package in `INSTALLED_APPS`.** The template
  resolves through the app-dirs loader against the package's
  [`AppConfig`][glossary-django-appconfig] — already the package's documented
  install step (and required for the [Trac #37064
  hardening][glossary-django-trac-37064-hardening] to apply). A consumer who
  skipped it gets `TemplateDoesNotExist` on the first GraphiQL page render
  with the toolbar enabled; the GLOSSARY body names the fix. A consumer with
  `APP_DIRS=False` and a bespoke loader configuration owns adding the
  equivalent (standard Django app-template mechanics, not package-specific).
- **The toolbar requires `django.contrib.staticfiles` + `STATIC_URL` — and
  with this middleware the failure surfaces on `/graphql/`.** The toolbar's
  own documented install prerequisite: `render_toolbar` converts a
  `TemplateSyntaxError` into `ImproperlyConfigured` explicitly naming
  `django.contrib.staticfiles` and `STATIC_URL`. Because the stock postprocess
  renders the toolbar for every processed response
  ([Decision 6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types)),
  a consumer without staticfiles hits that error on their **GraphQL**
  endpoint and will plausibly file it against this package — the GLOSSARY
  body names the fix alongside the `TemplateDoesNotExist` note. Fakeshop
  ships staticfiles + `STATIC_URL`, so the test plan is unaffected.
- **The package middleware REPLACES the stock toolbar entry.** It subclasses
  the stock middleware, so listing both would run the toolbar pipeline twice
  (double handles, double history rows). Same contract as upstream; documented
  in the GLOSSARY body and the User-facing API block. Ordering guidance is the
  toolbar's own ("as early as possible, after encoding-touching middleware");
  the package adds no ordering constraint of its own.
- **Show-toolbar gating is inherited, untouched.** The default
  `debug_toolbar.middleware.show_toolbar` returns `False` when `settings.DEBUG`
  is false (the first, decisive check at 7.0.0) and otherwise only when
  `REMOTE_ADDR` is in `INTERNAL_IPS` — so the toolbar (and every injected byte)
  is off in production, and the subclass flows through as a near-no-op
  (`process_view` tags one attribute; `_postprocess` is only reached when the
  stock middleware decided to process at all). This is also what makes the
  example's shipped toolbar wiring safe: under the suite's `DEBUG=False` the
  whole integration is inert, which the live tier pins directly. It is why the
  toolbar-present fixture must set **both** `DEBUG=True` (pytest-django forces
  the suite to `DEBUG=False`) **and** an always-true `SHOW_TOOLBAR_CALLBACK` (to
  be independent of `INTERNAL_IPS` / `REMOTE_ADDR`) — it satisfies the real gate
  rather than bypassing it
  ([Decision 9](#decision-9--test-strategy-live-tier-tests-through-fakeshops-shipped-toolbar-package-tests-for-the-paths-no-live-request-reaches-eviction-simulated-absence)).
- **Streaming responses are skipped.** `response.streaming` returns before any
  body inspection — a streaming body has no `.content` to decode or append to.
  Strawberry's Django views stream only for multipart-subscription responses;
  either way the guard is upstream's and stays.
- **Encoded response bodies are skipped.** A response carrying a
  `Content-Encoding` header returns untouched, before either mutation path: the
  bridge script cannot be appended to a gzipped body and a re-encoded JSON body
  would no longer match its declared encoding. This is why the documented
  ordering guidance places the toolbar middleware **after** any
  response-encoding middleware — in that position the middleware sees decoded
  bodies and the skip is the rare case rather than the normal one
  ([Decision 6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types)).
- **A declared-JSON response the middleware cannot read.** If the body's bytes
  do not decode under the response's own charset, or the decoded text is not
  valid JSON, or it parses to something other than an object, `_get_payload`
  returns `None` and the response is passed through unmodified. A GraphQL
  response is none of those things, so this is the guard against a mislabelled
  or hand-rolled response rather than an expected path — and passing it through
  is the contract: a development diagnostic must never be what turns an unusual
  response into a 500.
- **A `debugToolbar` value the bridge cannot read.** The bridge's `update` hook
  is a global patch, so a JSON body carrying a `debugToolbar` key whose value is
  not an object with an object `panels` — or whose panel entries are not
  objects — must not throw out of `JSON.parse` / `Response.prototype.json`. The
  key is scrubbed unconditionally; the DOM update then proceeds only for a value
  the record predicate accepts, skipping any single panel entry it cannot read
  ([Borrowing posture](#borrowing-posture), the payload-shape guard). The panel
  **keys** carry the same contract from the other direction: a key that cannot
  name a DOM node skips that one panel rather than raising a `DOMException` out
  of the patched globals, which is the best-effort per-panel rule applied to the
  selector the key is interpolated into. A real middleware payload keys its
  panels by the toolbar's own class-derived panel ids and is always readable, so
  both halves guard a foreign or hand-rolled `debugToolbar` key rather than an
  expected path.
- **`request.body` re-read in `_postprocess`.** Django caches the raw body
  bytes after first access (the view already read it), so the `operationName`
  sniff costs no I/O and raises no "body already read" — with one exception:
  a **multipart** upload request ([`Upload` scalar][glossary-upload-scalar]
  mutations) may have had its body consumed by the multipart parser;
  `json.loads` on it then raises inside the broad `except`, `operation_name`
  degrades to `None`, and the payload is injected normally. Degradation, not
  breakage — and identical to upstream.
- **A GraphiQL GET with `?query=` (queries via GET).** The response is JSON,
  the request is Strawberry-view-tagged, and `json.loads(request.body)` on the empty
  GET body raises → `operationName` is `None` → payload injected. Consistent
  with upstream; noted so the GET path in the tests is understood as covered
  by design rather than accident.
- **`_is_graphiql` is set on every request the middleware sees** (the
  attribute is written unconditionally in `process_view`), so `_postprocess`
  never needs a `hasattr` dance; requests that bypass `process_view`
  (short-circuited by an earlier middleware) fall back to
  `getattr(request, "_is_graphiql", False)` — upstream's exact read, kept.
- **Non-Strawberry GraphQL views are not tagged.** A consumer serving GraphQL
  through something that is not a `strawberry.django.views.BaseView` subclass
  gets stock toolbar behavior only (no injection). Documented as the
  detection contract
  ([Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned));
  the escape hatch is subclassing the package middleware and widening
  `process_view` — supported but undocumented-as-API.
- **Async posture.** The stock toolbar middleware is async-capable
  (`async_capable = True` in its recent releases) and the subclass inherits
  that capability flag; but this card's test vehicle is sync WSGI, so the
  async path ships **unverified** and unclaimed
  ([Risks](#risks-and-open-questions)). Nothing in the two overrides is
  coroutine-hostile (they run in the sync `_postprocess` hook the stock
  middleware calls from either mode), which is exactly as far as this card's
  claim goes.
- **Toolbar state leaking across tests on a `loadscope` worker.** The
  toolbar-present fixture's `DEBUG=True` / `DEBUG_TOOLBAR_CONFIG` overrides are
  scoped and restored by Django's own test utilities, but **the toolbar's module-
  and class-level caches do NOT reset with a settings override** —
  `show_toolbar_func_or_path` is `@cache`-memoized and
  `DebugToolbar._panel_classes` / `_urlpatterns` are class attributes. So the
  fixture clears the callback cache and saves / clears / restores the class
  caches on setup and teardown (Decision 9's cache-hygiene contract). Under
  `pytest.ini`'s `--dist loadscope`, which keeps a module's tests on one worker,
  a leaked always-true callback would otherwise let this module pass while a
  later same-worker test inherits it; the cache clears close that hole. The
  reloaded `config.urls` is the same class of state and is restored the same
  way, under ambient `DEBUG=False`, so the `djdt` routes cannot leak either.
- **Template `Content-Length` refresh.** Both mutation paths (`response.write`
  on HTML, `response.content = ...` on JSON) refresh `Content-Length` only
  when the header is already present — Django's `HttpResponse` normally
  computes it at serialization time, but a middleware or server layer that
  pre-set it would otherwise serve a truncated body. Upstream's guard, kept.

## Test plan

Split across two tiers per
[Decision 9](#decision-9--test-strategy-live-tier-tests-through-fakeshops-shipped-toolbar-package-tests-for-the-paths-no-live-request-reaches-eviction-simulated-absence).
**Tests 1–8a are the live tier**,
`examples/fakeshop/test_query/test_debug_toolbar_api.py` (class `TestToolbarPresent`),
driving fakeshop's real `/graphql/` URL through the example's shipped toolbar wiring —
GraphQL envelopes posted via the package's own [`TestClient`][glossary-testclient], the
raw `HttpResponse` inspected for the content-type, header and injected-payload
assertions. **Tests 9–16 are the package tier**,
`tests/middleware/test_debug_toolbar.py`, holding only what no live request can
reach.

The toolbar-present group shares the one fixture (`toolbar_client`) Decision 9
specifies — `DEBUG=True` with `config.urls` reloaded **inside** the override so its
`DEBUG`-gated `djdt` routes populate, a `DEBUG_TOOLBAR_CONFIG` carrying the always-true
`SHOW_TOOLBAR_CALLBACK` and a `DISABLE_PANELS` that leaves `RedirectsPanel` enabled,
and the mandatory `show_toolbar_func_or_path.cache_clear()` plus the save / clear /
restore of `DebugToolbar._panel_classes` / `_urlpatterns` on setup and teardown.
Everything else is fakeshop's shipped configuration. That group carries a class-level
`pytest.mark.django_db`; the package tier is unmarked. **Every product-query test's
first executable line is `seed_data(1)`** from `apps.products.services` — the repo's
seed-helper rule; the panel payload does not depend on row counts, but the query must
hit real rows to emit SQL. The absence / guard tests import **no** fakeshop catalog
helper.

`Content-Length` is checked on every mutating live row: fakeshop's `CommonMiddleware`
sets the header before the toolbar's response pass, so the package's header-present
refresh branches run on real traffic, and each of Tests 1, 3, 5 and 6 asserts the
header is present and equals `len(response.content)` after the mutation.

**Toolbar-present — the GraphiQL HTML path:**

1. GET `/graphql/` (the GraphiQL IDE page), parametrized over three HTML `Accept`
   spellings, returns 200 HTML carrying **both** injections: the stock toolbar handle
   (`id="djDebug"` — proving `super()._postprocess` ran and the stock pipeline is
   intact) and the package's appended template script (a distinctive substring of the
   asset — proving the HTML branch fired)
   (`test_graphiql_page_carries_stock_handle_and_bridge_script`).
2. The same GET **under fakeshop's shipped settings** — without the `DEBUG=True`
   override, so the suite's forced `DEBUG=False` applies — asserts **stable behavior,
   not byte-equality**: status 200, an HTML `Content-Type`, the GraphiQL marker
   present, the package script **absent**, and the stock toolbar handle **absent**
   (`test_no_toolbar_baseline_under_shipped_settings`). This is the production-safety
   baseline: the example ships the toolbar wired, and this pins that the whole
   integration is inert wherever `DEBUG` is off. Deliberately **no** "package
   middleware module not imported" assertion: under `--dist loadscope` any
   toolbar-present test that ran earlier on the same worker leaves
   `django_strawberry_framework.middleware.debug_toolbar` in `sys.modules`, so that
   assertion would pass or fail on local test order alone while the response is
   perfectly clean. Import-surface guarantees belong to the absence tests.

**Toolbar-present — the JSON operation path:**

3. `seed_data(1)`, then POST a **named** products operation — a non-null
   `operationName` in the JSON envelope requires a named operation document, so the
   query is `query ToolbarItems { allItems(first: 1) { edges { node { name category
   { name } } } } }` with `"operationName": "ToolbarItems"` (an anonymous `{ ... }`
   document plus a non-null `operationName` fails GraphQL validation before proving
   anything): the 200 JSON body carries `debugToolbar` with a non-empty `panels`
   mapping and a `requestId`; the `SQLPanel` entry carries a string `title` and a
   non-null `subtitle`; `RedirectsPanel`'s `title` is `null` (its `has_content` is
   false); `TemplatesPanel` is absent from the mapping (the skip); and the
   response's own `data` key is intact beside the injected one
   (`test_named_json_operation_gets_panel_payload`).
4. POST with `operationName: "IntrospectionQuery"` (a real introspection document):
   the response body carries **no** `debugToolbar` key and is otherwise a normal
   introspection result
   ([Decision 8](#decision-8--the-introspection-query-skip-is-preserved-verbatim))
   (`test_introspection_query_is_skipped`).
5. **GET `/graphql/?query=...` requesting JSON deterministically** — send
   `HTTP_ACCEPT="application/json"` so Strawberry's Django view returns the JSON
   result, not the GraphiQL HTML page. **Assert `Content-Type` is
   `application/json` before** inspecting the body, then assert the payload is
   injected: this exercises the broad-except `operationName` sniff branch (the GET
   body is empty, `json.loads` raises → `operationName` is `None` → inject)
   (`test_get_with_json_accept_hits_the_operation_name_except_branch`).

**Toolbar-present — the panel-content route (the actual user story):**

6. `seed_data(1)`, POST the named products operation of Test 3, and capture
   `debugToolbar.requestId` from the JSON body. Then GET the toolbar's
   `render_panel` view through the `djdt` routes fakeshop's own `config.urls`
   contributes, resolved via `reverse("djdt:render_panel")` so the test stays
   correct under a custom `debug_toolbar_urls(prefix=...)`, with `request_id` and
   `panel_id=SQLPanel` query parameters, and assert what debug-toolbar returns: a
   **JSON** response ([`render_panel`][debug-toolbar-views-source] responds with a
   JSON body carrying `content` and `scripts` keys) with no `debugToolbar` key,
   whose `content` is the **stored SQL-panel content for this id**. "Non-empty" is
   not enough to prove that: when `DebugToolbar.fetch()` finds nothing for the
   `request_id`, `render_panel` returns 200 JSON with a *non-empty* `content` too —
   the "isn't available anymore" fallback. So the test pins the success direction on
   both sides: the fallback message is **absent**, and SQL-panel markers from the
   seeded operation are **present** (`SELECT` and the `products_item` table name)
   (`test_injected_request_id_round_trips_to_stored_sql_panel_content`). Inspecting
   the `requestId` in the JSON (Test 3) proves the id exists; **this** test proves
   the id is *usable*. (It does not guard against a *missing* URLconf — omitting
   `debug_toolbar_urls()` crashes every toolbar-processed request with
   `NoReverseMatch` long before any panel fetch, per the
   [User-facing API](#user-facing-api).)

**Toolbar-present — detection mechanics:**

7. Detection's negative direction for HTML, parametrized over both Django dispatch
   shapes: a non-Strawberry **function-based** view (fakeshop's `/` index) and a
   non-Strawberry **class-based** view (Django's own `LoginView` at fakeshop's
   `/login/`) each return their normal HTML with **no** package-appended template
   script and **no** `debugToolbar` anywhere in the body
   (`test_non_strawberry_html_views_pass_through`). The negative assertion is
   deliberately **package-scoped, not toolbar-scoped**: the fixture's always-true
   show callback means the **stock** toolbar handle may legitimately appear in this
   ordinary HTML, because the package middleware subclasses and preserves stock
   behavior. The positive direction needs no separate test: the GraphiQL/JSON
   requests in Tests 1/3/5/6 already run through fakeshop's real
   `ensure_csrf_cookie(DjangoGraphQLView.as_view(...))` mount, so a passing Test 3
   IS the proof that `view_class` + `issubclass(..., BaseView)` resolves through
   `functools.wraps`-copied attributes — and, because that mount is the package's
   own [`views.py`][views] view, that the engine-owned check covers a package view
   with no branch of its own.
8. Detection's negative direction for JSON — the payload leak guard. The HTML
   negatives above cannot prove it: an implementation that injected `debugToolbar`
   into *every* JSON response would still pass Tests 1–7. With `ROOT_URLCONF` pointed
   at the test module's own URLconf (fakeshop's `config.urls` plus an
   `/unrelated.json` holder view returning a JSON body), the GET returns the body
   unmodified with **no** `debugToolbar` key
   (`test_unrelated_json_view_body_is_never_mutated`). Stock debug-toolbar *headers*
   are acceptable — the contract under test is "unrelated JSON bodies are never
   mutated", not "the stock toolbar ignores the request".
8a. **Encoded-body early-out** — an inner middleware appended after the toolbar in
    `MIDDLEWARE` stamps `Content-Encoding` on the response without compressing it,
    so the toolbar's response pass sees the header and the body stays readable.
    Parametrized over two encodings (`gzip`, `br`) **and** both mutation sites (the
    GraphiQL HTML append and the tagged-JSON re-encode), so the guard rests on the
    header's presence rather than one value and is measured at both sites it
    protects. Every row first posts the named operation of Test 3 without the
    stamp and asserts the injected payload — the positive control — then, under the
    stamping `MIDDLEWARE`, asserts the HTML row carries no bridge script and no
    `debugToolbar`, the JSON row carries its `data` and no `debugToolbar`, and the
    response still carries the stamped encoding
    (`test_encoded_response_gets_no_package_mutation`).

**Package tier — toolbar-absent** (the shared `tests/_soft_dependency.py` eviction +
two-sided restore with a `sys.modules["debug_toolbar"] = None` importlib sentinel; a
`builtins.__import__` block is a no-op for this `importlib`-based guard):

9. `import django_strawberry_framework` and
   `import django_strawberry_framework.middleware` both succeed;
   `from django_strawberry_framework import *` binds no toolbar name
   (`test_package_and_middleware_imports_stay_clean_without_toolbar`).
10. `import django_strawberry_framework.middleware.debug_toolbar` raises
    `ImportError` whose message contains `django-debug-toolbar>=7.0.0` — the
    **hint**, not the bare `ModuleNotFoundError` (proving `require_debug_toolbar()`
    wrapped it) — matched against the **re-typed literal** in the test file (the
    `_HINT_SUBSTRING` discipline), with the original `ImportError` chained
    (`__cause__`) (`test_leaf_import_raises_install_hint_when_toolbar_absent`).
11. After restore, the module imports again in the same process,
    `django_strawberry_framework.middleware.debug_toolbar is
    sys.modules["django_strawberry_framework.middleware.debug_toolbar"]`, and the
    parent package's `debug_toolbar` attribute is that same object — the
    two-sided-restore invariant (D3), making the present-path tests
    order-independent under `pytest-xdist` (`test_leaf_reimports_after_restore`).

**Test 11a — present-but-broken install (degraded path).** Leave the real top-level
`debug_toolbar` importable but make its `middleware` submodule unimportable
(`sys.modules["debug_toolbar.middleware"] = None`). `require_debug_toolbar()`
**passes** (it imports only the top-level package), then the leaf's own
`from debug_toolbar.middleware import ...` statement fails: assert
`import django_strawberry_framework.middleware.debug_toolbar` raises the **raw**
`ImportError` naming `debug_toolbar.middleware` — **without**
`_DEBUG_TOOLBAR_INSTALL_HINT` — and with no `__cause__` of its own, since the
statement-import error propagates unwrapped
(`test_broken_toolbar_install_propagates_raw_import_error`). This pins the
[Error shapes](#error-shapes) contract that the guard wraps only the top-level
package and never misreports a broken install as "not installed".

**Test 11b — installed but absent from `INSTALLED_APPS` (the wiring gate).** Leave
`debug_toolbar` importable but with `"debug_toolbar"` **removed** from
`INSTALLED_APPS` (`modify_settings`), and evict only the framework leaf so its body
re-runs. (The inverse obligation holds too: the **first** leaf import in a process
must happen with the app installed, because `debug_toolbar.middleware` defines a
Django model, which is what the package tier's `toolbar_leaf` fixture owns.)
`require_debug_toolbar()` **passes**, and — before the `debug_toolbar.middleware`
import that would otherwise surface Django's cryptic `HistoryEntry` app-label
`RuntimeError` — the `apps.is_installed("debug_toolbar")` gate raises
`ImproperlyConfigured` naming the fix (asserted against the `INSTALLED_APPS`
substring) (`test_leaf_import_requires_debug_toolbar_in_installed_apps`). This pins
the second [Error shapes](#error-shapes) contract: a missing app is reported as a
settings error, neither misfiled as "not installed" nor leaked as the raw
model-registration `RuntimeError`.

**Guard unit shape:**

12. `require_debug_toolbar()` returns the imported `debug_toolbar` module when
    present (identity with `sys.modules["debug_toolbar"]`), and under the `None`
    sentinel raises the hint-carrying `ImportError` with the original chained — the
    thin-wrapper contract over
    [`require_optional_module`][glossary-require-optional-module], whose own unit
    tests are not duplicated here (`test_require_debug_toolbar_guard_unit`). (Under
    a `builtins.__import__` block this assertion would fail: the guard's
    `importlib.import_module` call bypasses the block and returns the still
    installed toolbar.)

12a. **The floor's gated trio agrees.** Read [`pyproject.toml`][pyproject] and
    assert its `django-debug-toolbar>=` dev-group row is exactly the re-typed
    `_HINT_SUBSTRING` literal, and that the literal is a substring of
    `_DEBUG_TOOLBAR_INSTALL_HINT` — the same regex-over-`pyproject.toml` idiom the
    suite's governance rows use for the Channels and Strawberry floors
    (`test_install_hint_floor_matches_the_pyproject_dev_group_row`). Together with
    Test 10's hint match this is what makes the three-places rule a gate rather
    than a comment: none of the specifier, the hint, and the literal can move
    alone. It says nothing about documentation that restates the floor, and its
    docstring says so.

**Coverage-only targeted units** (branches the real toolbar lifecycle does not
naturally expose through the live tier; unmarked, no database, direct calls with
stub objects — mock only where the real path is impossible, per the
[coverage-priority rule][glossary-live-first-coverage-mandate]). One shared
constraint shapes the ones that enter `_postprocess`: the package override calls
`super()._postprocess(...)` **before** its own branches, so the stock toolbar
postprocess runs first — the fake toolbar therefore implements the small protocol
that method consumes (`enabled_panels` and `render_toolbar()`):

13. **Streaming early-out** — call `_postprocess` with a `StreamingHttpResponse` on a
    tagged request and a protocol-complete fake toolbar, and assert **no
    package-specific mutation after the stock postprocess returns**: the same
    response object back with unchanged streaming content
    (`test_streaming_response_gets_no_package_mutation`). Not "returns without
    touching the response" in the absolute sense — the stock postprocess runs first
    and may legitimately generate stats and headers. Fakeshop's GraphQL view never
    streams, so the branch is unreachable through the live tier.
14. **`_get_payload` bails and panel shape** — a stub toolbar whose `request_id` is
    `None` makes `_get_payload` return `None`
    (`test_get_payload_bails_without_request_id`); under the fixture's always-true
    show callback the real toolbar always assigns a `request_id`, so the bail never
    fires live. A sibling unit drives stub panels with `has_content` false (title
    `None`), callable `title` / `nav_subtitle` (called), and a `TemplatesPanel`
    (skipped) (`test_get_payload_panel_title_only_when_has_content`): stock panels
    expose properties, so the callable arm is package-only. A further sibling drives
    the **non-object-body bail**: a response whose decoded JSON is a list makes
    `_get_payload` return `None`
    (`test_get_payload_bails_on_non_object_json_body`). A valid single GraphQL
    response is always an object, so this branch is unreachable live.

14a. **`process_view` non-class `view_class` guard.** Call `process_view` with a
    `view_func` whose `view_class` attribute is the string `"not-a-class"` and assert
    `request._is_graphiql` is `False` with **no exception**
    (`test_process_view_tolerates_non_class_view_class`). The
    `isinstance(view, type)` guard short-circuits before `issubclass`, which would
    otherwise raise `TypeError`. No live request reaches it: a string `view_class`
    still 500s later inside stock `RequestPanel.generate_stats`, so the guard has no
    independent 200 on the wire.

14b. **Undecodable / unparseable declared-JSON body** — drive the full
    `_postprocess` on a tagged request with a pre-set `Content-Length`, parametrized
    over a body that is not JSON at all (`b"not json"`) and one whose bytes do not
    decode under the declared charset (`b"\xff"`); each returns the same response
    with its body and `Content-Length` unchanged
    (`test_malformed_json_body_gets_no_package_rewrite`). This is the rest of the
    response-shape family Test 14's non-object case starts, and it is parametrized
    because a guard written against one spelling of a bad input is a guess where a
    guard written against the answer is a boundary.

**Template-port guard** (mechanical, no JS runtime — reads the asset, executes
nothing):

16. Read `templates/django_strawberry_framework/debug_toolbar.html` and assert both
    halves of the
    [template-port checklist](#from-strawberry-graphql-django--borrow-the-mechanism-verbatim)
    as **one parametrized test row per predicate** — the module-level
    `_TEMPLATE_CONTRACT` table of (name, predicate over the asset text) with the
    names as the pytest ids, never a single test with a list of assertions, so that
    dropping one form fails that form's rows and only those
    (`test_template_port_invariants_and_robustness_divergence`). Substring presence,
    substring absence, single-definition, index-ordering, adjacency, own-line,
    nesting and return-count predicates are all rows of the same table. The rows pin
    the five preserved invariants (the `JSON.parse` wrapper, the
    `Response.prototype.json` wrapper, `delete data.debugToolbar`, the
    `data-request-id` update on the toolbar handle, and the per-panel title /
    subtitle DOM updates) **and** each of the seven diverged forms — the
    argument-forwarding `JSON.parse`, the safe membership guard, the mandatory scrub
    **ordering and unconditionality** (one row per early return and DOM write that
    follows the scrub — the null-handle bail, the payload-shape guard, the panel
    loop, the `data-request-id` write — plus the rows that pin the scrub
    unconditional, which an index comparison cannot see: that nothing returns
    between the entry guard and the scrub, counted from the function opener as well
    as from that guard's own return so that a bail hoisted *above* the guard is
    visible too, that nothing but whitespace separates the capture from it, that it
    stands alone on its own line, and that it is not nested inside a block of its
    own), the skip-on-absent-content-node panel loop with its selector-safe panel
    key, the shadow-root handle resolution with its light-DOM fallback, the per-node
    null checks, and the payload-shape guard (the guard's presence, its position
    after the scrub and before the panel loop, the per-panel record guard's presence
    as the loop body's first statement, the single `isRecord` definition, and the
    absence of any post-scrub `data.debugToolbar.*` read). Each kind of form is
    pinned by the kind of row that can falsify it. A form that diverges **by
    spelling** carries both halves of its divergence: a row pinning the port's
    spelling, and a row pinning that the upstream spelling it replaced is
    **absent** — the silent-revert detector a presence check cannot supply, since a
    paste of upstream's text can restore its shape alongside the port's. A form that
    diverges **by position** instead — the borrow carries the same statement,
    elsewhere — has no replaced spelling to assert absent and is pinned by rows
    comparing indices, adjacency, nesting, and the returns between two points. A
    **preserved** invariant carries the row pinning the upstream write the port
    keeps. What falsifies the claim: a spelling-diverged form whose rows are all
    presence checks, a post-scrub site no ordering row names, or an absence row that
    cannot fail on its own. The table's own comment states the three rules an
    absence needle obeys, because each violation reads exactly like a working row: it
    must occur in the borrow, contain no sibling absence needle, and be typed as a
    literal rather than derived from a shared constant. No test checks those rules;
    upstream's asset is not in the repository. The suite has no JS runtime, so this
    does not prove the script *works* — it turns the checklist's by-eye diff into a
    mechanical guard that fails, row by row, if a future edit drops one of the
    load-bearing behaviors.

Coverage: the package gate is `fail_under = 100`, and each branch has a named owner.
Reached by the **live tier (1–8a)**: the guard's success path, both `_postprocess`
main branches (HTML — Test 1; JSON — Tests 3/5), both header-present
`Content-Length` refreshes (Tests 1, 3, 5, 6), the `Content-Encoding` early-out
(Test 8a), the non-GraphiQL HTML and untagged-JSON early-outs (Tests 7, 8), the
introspection skip (Test 4), the `operationName` except-branch (Test 5), the
`TemplatesPanel` skip and both `has_content` outcomes (Test 3), and the panel-route
round trip (Test 6); Test 2 pins the inert-under-`DEBUG=False` direction. Reached by
the **absence / guard tests (9–12a)**: the guard's raise path, the import-surface
matrix, the raw-`ImportError` propagation for a present-but-broken install, and the
`apps.is_installed` wiring gate's `ImproperlyConfigured` raise. Reached **only by the
package-tier units (13–14b)**: the streaming early-out, the no-`request_id` bail, the
callable title / subtitle arm, the non-object / undecodable / unparseable branches of
`_get_payload`, and the `isinstance(view, type)` detection guard. The template-port
guard (16) earns no Python coverage — the asset is markup and JavaScript, not counted
lines; it exists to pin the port's invariants and diverged forms mechanically. A
branch unreachable through real requests gets its own targeted unit the same way —
the fallback is named per branch, never a blanket claim that the numbered
real-request tests reach everything.

## Doc updates

- [`docs/GLOSSARY.md`][glossary] — the
  [Debug-toolbar middleware][glossary-debug-toolbar-middleware] entry body
  carries the contract: the dotted settings path and the
  replace-the-stock-entry rule, the required `debug_toolbar_urls()` URLconf
  step **with its true failure mode** (omitting it fails every
  toolbar-processed request with `NoReverseMatch` — the stock postprocess
  renders the toolbar, which reverses `djdt:` routes, for every processed
  response — not "panel clicks 404"), the `BaseView` detection contract (and
  the non-Strawberry-view passthrough), the view-scoped (not IDE-scoped)
  injection contract, the introspection skip, the soft-dependency behavior
  matrix (package import clean / leaf import raises / hint text with the
  `7.0.0` floor), the `INSTALLED_APPS` template-resolution requirement and the
  toolbar's own `django.contrib.staticfiles` + `STATIC_URL` prerequisite
  (whose failure surfaces on `/graphql/` traffic under this middleware), the
  not-a-Channels-integration boundary, and the inherited show-toolbar
  gating. The "distinct from" edge
  to [Response-extensions debug middleware][glossary-response-extensions-debug-middleware]
  stays accurate in both entry bodies.
- [`docs/TREE.md`][tree] — rendered by
  [`scripts/build_tree_md.py`][build-tree-md] (missing module docstrings fail
  the render, so `middleware/__init__.py` and `middleware/debug_toolbar.py`
  carry docstrings written for their rows): the package tree's `middleware/`
  rows, and the test tree's `tests/middleware/` and the live tier's toolbar
  suite.
- [`KANBAN.md`][kanban] / `KANBAN.html` — the card via the DB + re-render
  (Slice 2 checklist).

## Risks and open questions

Each constraint below is live. The preferred-posture / fallback weighing behind
each is in the [rationale][rationale-risks].

- **`_postprocess` is a private-underscore method of `django-debug-toolbar`.**
  The subclass overrides (and chains to) a method the toolbar does not
  advertise as API; a toolbar major release could rename or reshape it, and
  the `>=7.0.0` floor is deliberately unbounded above (the package pins
  floors, not ceilings). The coupling is knowingly borrowed — upstream carries
  the identical override and the archived `django-graphiql-debug-toolbar`
  before it did too — and the containment is the behavior-level tests
  (Tests 1, 3), which fail loudly on any reshape.
- **The floor is single-valued across its three gated sites, and restated
  elsewhere ungated.** The dev-group specifier, the `_DEBUG_TOOLBAR_INSTALL_HINT`
  string, and the re-typed test literal must always name the same
  `django-debug-toolbar` floor; the package test compares all three, so moving
  one alone fails the suite. The install hint is the error message a deploying
  consumer follows, so a drift there misdirects a real install. The consumer
  docs restate the floor with no gate behind them, so a floor bump owes a sweep
  of the tree — never a count of the places it is written, which is a claim
  nothing checks. The sweep is for the package **name**, each hit read: a needle
  carrying the `>=` is bounded by one spelling and misses a restatement that
  separates the name from the constraint with a backtick or a space.
- **The Strawberry floor is read, never restated.** `BaseView`'s presence at the
  package's declared `strawberry-graphql` floor is confirmed by the view-class
  gate in a throwaway venv, with the floor version read at gate time from
  [`pyproject.toml`][pyproject] and [`docs/builder/BUILD.md`][build]
  `## Floor verification`. If it is ever missing at the floor, the recourse is
  to raise the project's Strawberry floor, not to weaken the check
  ([Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned)).
- **Toolbar process state outlives a settings override.** `show_toolbar`'s
  resolved callback is `@cache`-memoized and `DebugToolbar`'s panel/URL caches
  are class attributes, so any test that changes the toolbar's configuration
  owes the clear-and-restore contract in Decision 9. Under `--dist loadscope` a
  leak passes locally and fails a neighbour, so a surfaced flake in this class
  is fixed at source, never by weakening the suite's `-W error` posture.
- **Schema-registry order-dependence on a shared worker.** Package tests call
  `registry.clear()` for isolation, and the toolbar-present tests execute real
  GraphQL through the aggregate project schema — the documented `LazyType`
  `KeyError` class ([`test_query/README.md`][test-query-readme]). The answer is
  order-independence by reconstruction through the single-sited
  `schema_reload` helper, never a narrower private reload.
- **The async path ships unverified.** The stock middleware is async-capable
  and the overrides run in hooks it calls from either mode, but no test drives
  an async Strawberry view or an ASGI stack, and the glossary body claims only
  what is verified. [`spec-043`][spec-043] ships the async request vehicle
  (`AsyncTestClient`) and leaves the toolbar's async smoke to the toolbar's own
  test module, which carries none yet.
- **The bridge asset's guards are pinned by text, never by execution.** The
  suite has no JavaScript runtime, so Test 16's rows prove that each guard is
  present, single-sited and correctly ordered in the file on disk, and prove
  nothing about what any of them returns: that the record predicate accepts the
  values it should, that the escaped key is a selector `querySelector` parses,
  that a skipped panel is the only thing skipped. Those follow from the
  language and the CSSOM identifier-serialization rules, which is reasoning, not
  a measurement. The absence rows narrow the gap in one direction only — they
  detect a paste of upstream's text, and a rewrite of the same hole in different
  words passes every one of them. Whether this repository takes on a JS runtime
  is a maintainer decision and the named owner of this risk; until it is taken,
  a change to the asset's behavior is reviewed by reading and recorded in the
  build artifact, never demonstrated by a green suite.

## Out of scope (explicitly tracked elsewhere)

- **Response-extensions debug middleware** (`extensions["debug"]`, graphene
  parity) — [`DONE-044-0.0.14`][kanban]
  ([Response-extensions debug middleware][glossary-response-extensions-debug-middleware]);
  the two entries' "distinct from" cross-links are kept accurate by Slice 2.
- **The `TestClient` / `GraphQLTestCase` helpers themselves** —
  [`spec-043`][spec-043]
  ([`TestClient`][glossary-testclient] / [`GraphQLTestCase`][glossary-graphqltestcase]).
  This card does not build them; the live tier consumes `TestClient` to post its
  GraphQL envelopes, and an async smoke ([Risks](#risks-and-open-questions))
  would drive that card's `AsyncTestClient` from the toolbar's own test module.
- **The migration guide itself** — [`TODO-BETA-071-0.1.8`][kanban]; this card
  hands it the one-row settings-string mapping
  (`strawberry_django.middlewares.debug_toolbar.DebugToolbarMiddleware` →
  `django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware`,
  behavior unchanged) ([Goal 3](#goals)).

## Definition of done

- [ ] `django_strawberry_framework/middleware/debug_toolbar.py` exists, with
      module + symbol docstrings, exposing `DebugToolbarMiddleware`
      (subclassing `debug_toolbar.middleware.DebugToolbarMiddleware`,
      overriding `process_view` + `_postprocess` per
      [Decision 6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types))
      behind the import-time `require_debug_toolbar()` guard (a thin wrapper
      over `django_strawberry_framework/utils/imports.py::require_optional_module` — Helper-reuse D1).
- [ ] The template asset ships at
      `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
      and the middleware renders it via `render_to_string(...)` into GraphiQL
      HTML responses; the port preserves upstream's five invariants and carries
      the seven documented guard divergences
      ([template-port checklist](#borrowing-posture))
      ([Decision 4](#decision-4--module-template-and-test-locations-a-middleware-subpackage-an-in-package-template-asset-testsmiddleware)).
- [ ] The public wiring documents **all three** toolbar pieces — app,
      middleware (near the front of `MIDDLEWARE`, replacing the stock entry,
      after any response-encoding middleware), **and** `debug_toolbar_urls()`
      in the URLconf — and the example project wires all three in its own
      shipped settings and URLconf, so the toolbar-present tests need no
      wiring override of their own: only `DEBUG=True`, with `config.urls`
      reloaded inside that override so its `DEBUG`-gated `djdt` routes populate
      and restored outside it so they cannot leak
      ([User-facing API](#user-facing-api) / [Decision 9](#decision-9--test-strategy-live-tier-tests-through-fakeshops-shipped-toolbar-package-tests-for-the-paths-no-live-request-reaches-eviction-simulated-absence)).
- [ ] The injection contract is stated honestly: injection is view-scoped
      (every JSON response from a Strawberry Django view while the toolbar is
      enabled, minus `IntrospectionQuery`), **not** IDE-scoped — no wording
      promises "only the IDE's own fetches"
      ([Decision 6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types) / [User-facing API](#user-facing-api)).
- [ ] The spec states plainly this is a Django HTTP-middleware integration
      around Strawberry's Django views, **not** a Channels/ASGI toolbar for the
      [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter];
      ASGI/Channels behavior is neither claimed nor tested ([Non-goals](#non-goals)).
- [ ] `django-debug-toolbar` is a soft dependency: `import
      django_strawberry_framework` and `import
      django_strawberry_framework.middleware` succeed without it; importing the
      leaf module raises `ImportError` carrying the single install hint naming
      the verified floor (the card's DoD, sharpened by
      [Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).
- [ ] Strawberry-view detection targets `strawberry.django.views.BaseView`
      and is proven through fakeshop's real decorated URLconf
      ([Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned)).
- [ ] The introspection-query skip is preserved: no payload injection when
      `operationName == "IntrospectionQuery"`
      ([Decision 8](#decision-8--the-introspection-query-skip-is-preserved-verbatim)).
- [ ] **`django-debug-toolbar>=7.0.0`** is in `[dependency-groups].dev`, locked
      in `uv.lock`; the dev-group specifier, the
      hint string, and the re-typed test literal agree on the **single** floor
      and the package test compares all three (Test 12a), whose Django coverage
      reaches 6.0 and stops short of the `6.1` [`pyproject.toml`][pyproject]
      also advertises.
- [ ] The Strawberry view-class gate holds: `strawberry.django.views.BaseView`
      is importable at the package's declared `strawberry-graphql` floor
      — the version read at gate time from [`pyproject.toml`][pyproject] and
      [`docs/builder/BUILD.md`][build] `## Floor verification`, never from a
      number this spec restates — checked in an isolated throwaway venv (never
      the shared `.venv`).
- [ ] Both test tiers cover both dependency states per the
      [Test plan](#test-plan). **Live —
      `examples/fakeshop/test_query/test_debug_toolbar_api.py`:** the real
      GraphiQL HTML injection, the real SQL-emitting **named** JSON operation
      (each product-query test starting with `seed_data(1)`) with the `SQLPanel`
      entry present, `RedirectsPanel`'s `title` null and `TemplatesPanel`
      absent, the introspection skip, the
      deterministic JSON-`Accept` GET branch, the **panel-content fetch using
      the injected `requestId`** (asserting `render_panel`'s JSON
      `content`/`scripts` shape with the fallback "isn't available anymore"
      message **absent** and a SQL-panel marker from the seeded operation
      **present**), the HTML passthroughs for both dispatch shapes, the
      unrelated-JSON-view leak guard, the `Content-Encoding` early-out at both
      mutation sites, the `Content-Length` match after each mutation, and the
      inert-under-shipped-settings baseline — the group marked
      `pytest.mark.django_db`, with the fixture's mandatory
      `show_toolbar_func_or_path.cache_clear()` + `DebugToolbar` cache
      save/clear/restore on setup/teardown. **Package —
      `tests/middleware/test_debug_toolbar.py`:** the two-sided-restore absence
      matrix, the coverage-only targeted units (streaming early-out,
      no-`request_id` bail / callable title and subtitle / non-object and
      undecodable body bails, the non-class `view_class` guard),
      the pyproject-row gate over the floor's three sites, and the template-port
      guard over the copied-asset invariants **and** the diverged guard forms as
      one parametrized row per predicate, each form pinned by the kind of row
      that can falsify it — a form diverging by spelling carrying both the row
      for the port's spelling and the row asserting upstream's replaced spelling
      absent, a form diverging by position carrying the index, adjacency,
      nesting and return-count rows a substring copy satisfies. The package
      coverage gate
      (`fail_under = 100`) holds
      with `middleware/debug_toolbar.py` included, each branch mapped to a named
      test owner.
- [ ] The migration-guide handoff row content is recorded for
      [`TODO-BETA-071-0.1.8`][kanban] (the one settings-string swap, behavior
      unchanged) ([Goal 3](#goals)).
- [ ] Slice 2 doc updates land per [Doc updates](#doc-updates): the GLOSSARY
      entry body, the regenerated
      [`docs/TREE.md`][tree], and the kanban card wrap (DB edit + re-render).
- [ ] **No slice bumps the version** — the joint `0.0.14` cut owns the bump
      ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).
- [ ] `uv run ruff format .` / `ruff check --fix .` clean.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[pyproject]: ../../pyproject.toml
[pytest-ini]: ../../pytest.ini
[readme]: ../../README.md
[start]: ../../START.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[glossary-auth-mutations]: ../GLOSSARY.md#auth-mutations
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-debug-toolbar-middleware]: ../GLOSSARY.md#debug-toolbar-middleware
[glossary-django-appconfig]: ../GLOSSARY.md#django-appconfig
[glossary-django-trac-37064-hardening]: ../GLOSSARY.md#django-trac-37064-hardening
[glossary-djangographqlprotocolrouter]: ../GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-eviction-simulated-absence]: ../GLOSSARY.md#eviction-simulated-absence
[glossary-fk-id-elision]: ../GLOSSARY.md#fk-id-elision
[glossary-graphqltestcase]: ../GLOSSARY.md#graphqltestcase
[glossary-joint-version-cut]: ../GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: ../GLOSSARY.md#live-first-coverage-mandate
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-pep-562-lazy-export]: ../GLOSSARY.md#pep-562-lazy-export
[glossary-request-from-info]: ../GLOSSARY.md#request_from_info
[glossary-require-optional-module]: ../GLOSSARY.md#require_optional_module
[glossary-response-extensions-debug-middleware]: ../GLOSSARY.md#response-extensions-debug-middleware
[glossary-schema-reload-discipline]: ../GLOSSARY.md#schema-reload-discipline
[glossary-seed-data]: ../GLOSSARY.md#seed_data
[glossary-serializermutation]: ../GLOSSARY.md#serializermutation
[glossary-single-upstream-parity]: ../GLOSSARY.md#single-upstream-parity
[glossary-soft-dependency]: ../GLOSSARY.md#soft-dependency
[glossary-testclient]: ../GLOSSARY.md#testclient
[glossary-upload-scalar]: ../GLOSSARY.md#upload-scalar
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[next]: NEXT.md
[rationale]: appx/spec-042-debug_toolbar-0_0_14-rationale.md
[rationale-d1]: appx/spec-042-debug_toolbar-0_0_14-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-d10]: appx/spec-042-debug_toolbar-0_0_14-rationale.md#decision-10--version-bumps-are-owned-by-the-joint-0014-cut
[rationale-d2]: appx/spec-042-debug_toolbar-0_0_14-rationale.md#decision-2--card-scope-boundary
[rationale-d3]: appx/spec-042-debug_toolbar-0_0_14-rationale.md#decision-3--the-symbol-is-debugtoolbarmiddleware
[rationale-d4]: appx/spec-042-debug_toolbar-0_0_14-rationale.md#decision-4--module-template-and-test-locations
[rationale-d5]: appx/spec-042-debug_toolbar-0_0_14-rationale.md#decision-5--soft-django-debug-toolbar-dependency
[rationale-d6]: appx/spec-042-debug_toolbar-0_0_14-rationale.md#decision-6--subclass-and-override-borrowed-as-is
[rationale-d7]: appx/spec-042-debug_toolbar-0_0_14-rationale.md#decision-7--strawberry-view-detection-against-baseview
[rationale-d8]: appx/spec-042-debug_toolbar-0_0_14-rationale.md#decision-8--the-introspection-query-skip-is-preserved-verbatim
[rationale-d9]: appx/spec-042-debug_toolbar-0_0_14-rationale.md#decision-9--test-strategy
[rationale-risks]: appx/spec-042-debug_toolbar-0_0_14-rationale.md#risks-and-open-questions
[spec-039]: spec-039-serializer_mutations-0_0_13.md
[spec-040]: spec-040-auth_mutations-0_0_13.md
[spec-041]: spec-041-channels_router-0_0_14.md
[spec-043]: spec-043-test_client-0_0_14.md
[spec-046]: spec-046-transport_security-0_0_14.md

<!-- docs/builder/ -->
[build]: ../builder/BUILD.md

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[init]: ../../django_strawberry_framework/__init__.py
[rf-init]: ../../django_strawberry_framework/rest_framework/__init__.py
[routers]: ../../django_strawberry_framework/routers.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py
[views]: ../../django_strawberry_framework/views.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-soft-dependency]: ../../tests/rest_framework/test_soft_dependency.py

<!-- examples/ -->
[config-settings]: ../../examples/fakeshop/config/settings.py
[config-urls]: ../../examples/fakeshop/config/urls.py
[test-query-readme]: ../../examples/fakeshop/test_query/README.md

<!-- scripts/ -->
[build-kanban-md]: ../../scripts/build_kanban_md.py
[build-tree-md]: ../../scripts/build_tree_md.py

<!-- .venv/ -->

<!-- External -->
[debug-toolbar-install-docs]: https://django-debug-toolbar.readthedocs.io/en/latest/installation.html
[debug-toolbar-middleware-source]: https://raw.githubusercontent.com/django-commons/django-debug-toolbar/7.0.0/debug_toolbar/middleware.py
[debug-toolbar-toolbar-source]: https://raw.githubusercontent.com/django-commons/django-debug-toolbar/7.0.0/debug_toolbar/toolbar.py
[debug-toolbar-views-source]: https://raw.githubusercontent.com/django-commons/django-debug-toolbar/7.0.0/debug_toolbar/views.py
[upstream-middleware]: ../../../strawberry-django-main/strawberry_django/middlewares/debug_toolbar.py
[upstream-template]: ../../../strawberry-django-main/strawberry_django/templates/strawberry_django/debug_toolbar.html
