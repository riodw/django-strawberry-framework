# Spec: Debug-toolbar middleware — `DebugToolbarMiddleware` in a soft-`django-debug-toolbar` `middleware/debug_toolbar.py`, the SQL-panel window into `/graphql/` requests

Planned for `0.0.14` (card [`WIP-ALPHA-042-0.0.14`][kanban]). This card adds the
package's **`django-debug-toolbar` integration**: a new
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
contributes — Strawberry-view tagging and payload injection — plus the ~45-line
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

**Version boundary** (see
[Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)): this
card **shares the `0.0.14` patch line** with two open siblings —
[`TODO-ALPHA-043-0.0.14`][kanban] ([`TestClient`][glossary-testclient] /
[`GraphQLTestCase`][glossary-graphqltestcase]) and
[`TODO-ALPHA-044-0.0.14`][kanban] ([Response-extensions debug
middleware][glossary-response-extensions-debug-middleware]) — and follows
[`DONE-041-0.0.14`][kanban] ([`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]),
which already deferred its own cut to the same [joint `0.0.14`
cut][glossary-joint-version-cut]. So the `pyproject.toml` / `__version__` /
[`tests/base/test_init.py::test_version`][test-base-init] bump from `0.0.13` to
`0.0.14` is owned by the **joint cut** (the last `0.0.14` card to land), not by
this card — the same shared-cut posture [`spec-041`][spec-041] Decision 10 and
[`spec-039`][spec-039] Decision 14 took. No slice below bumps the version.

Status: **PLANNED — no slice built yet.**
Two slices (the card is an M with one module, one template, and one test file):
Slice 1 (**the dependency gate + `middleware/debug_toolbar.py` + the template +
`tests/middleware/test_debug_toolbar.py`** — the `django-debug-toolbar` dev-group
add with the lockfile regenerated, the soft-dependency guard, the middleware
subclass, the template asset, and both the toolbar-present and toolbar-absent
test paths land in one commit), and Slice 2 (**docs + card wrap** — the
implemented-contract doc updates, the regenerated [`docs/TREE.md`][tree], and the
kanban card flip; the release-status wording and the version bump stay deferred
to the joint cut).

Owner: package maintainer.

Predecessors: [`spec-041-channels_router-0_0_14.md`][spec-041] (the
most-recently-shipped spec and the canonical voice / depth / section-layout
reference; also the card that landed
[`require_optional_module`][glossary-require-optional-module] in
[`utils/imports.py`][utils-imports] — the raising optional-import primitive this
card's guard rides — and generalized the [soft-dependency][glossary-soft-dependency]
architecture to a second integration; `django-debug-toolbar` becomes the third);
[`spec-039-serializer_mutations-0_0_13.md`][spec-039] (the original
soft-dependency card — the single `require_*()` guard with one install-hint
string, the dev-group + lockfile dependency gate, and the
[eviction-simulated absence][glossary-eviction-simulated-absence] test
discipline); [`spec-040-auth_mutations-0_0_13.md`][spec-040] (the
single-upstream-parity posture precedent). [`docs/GLOSSARY.md`][glossary] carries
[Debug-toolbar middleware][glossary-debug-toolbar-middleware] as `planned for
0.0.14`; Slice 2 updates the entry body to the implemented contract while the
`shipped (0.0.14)` status flip rides the joint cut.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft authored from the [`WIP-ALPHA-042-0.0.14`][kanban]
  card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-07-06). Pinned: the
  canonical structured filename
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)); the card-scope
  boundary — the server-side toolbar integration ships, the in-response
  `extensions` surface stays with the sibling card, fakeshop's shipped settings
  stay toolbar-free, no new `Meta` / settings key
  ([Decision 2](#decision-2--card-scope-boundary-the-server-side-toolbar-integration-ships-the-in-response-surface-fakeshop-settings-opt-in-and-async-verification-stay-out));
  the `DebugToolbarMiddleware` symbol name — deliberately the **same** class
  name as both upstream and stock `django-debug-toolbar`, distinguished by the
  module path, because a Django middleware's public identity IS its dotted
  settings string
  ([Decision 3](#decision-3--the-symbol-is-debugtoolbarmiddleware--same-class-name-distinctly-ours-dotted-path));
  the `middleware/` subpackage + template-asset + `tests/middleware/` locations
  ([Decision 4](#decision-4--module-template-and-test-locations-a-middleware-subpackage-an-in-package-template-asset-testsmiddleware));
  the soft-`django-debug-toolbar` guard as an **import-time**
  `require_debug_toolbar()` at module top (the `rest_framework/__init__.py`
  shape, NOT the `routers.py` PEP 562 lazy-symbol shape — the module import is
  itself the opt-in, per the card's own DoD wording), with the
  `django-debug-toolbar>=7.0.0` dev-group add + lockfile regeneration as the
  Slice-1 dependency gate — the floor deliberately **above** upstream's
  `>=6.0.0` because `7.0.0` is the first release with the Django 6.0 classifier
  the package advertises (PyPI metadata: `6.0.0` classifies 4.2–5.2 only)
  ([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape));
  the subclass-and-override shape borrowed as-is — `process_view` +
  `_postprocess`, the module-level `_get_payload` helper, the `_HTML_TYPES`
  constant, the `TemplatesPanel` skip, and the `DjangoJSONEncoder` re-encode
  ([Decision 6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types));
  the Strawberry-view detection pinned against engine-owned
  `strawberry.django.views.BaseView`, resolving the card's `DjangoGraphQLView`
  working-name hedge — the package ships no view class of its own; fakeshop and
  every documented consumer path wire Strawberry's Django views directly
  ([Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned--resolving-the-cards-djangographqlview-hedge));
  the introspection-query skip preserved verbatim
  ([Decision 8](#decision-8--the-introspection-query-skip-is-preserved-verbatim));
  the package-tests placement with real in-process fakeshop `/graphql/`
  requests under per-test settings overrides, justified against the
  [live-first mandate][glossary-live-first-coverage-mandate] — fakeshop's
  shipped configuration deliberately carries no soft-dependency middleware, so
  no live request through the example's own settings can reach these lines
  ([Decision 9](#decision-9--test-strategy-package-tests-driving-real-in-process-fakeshop-requests-under-settings-overrides-eviction-simulated-absence));
  and the joint-cut version deferral
  ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).
  One coupling tension is carried into [Risks](#risks-and-open-questions) rather
  than silently reconciled: `_postprocess` is a private-underscore method of
  `django-debug-toolbar` — upstream subclasses it anyway (with `@override`), and
  this card borrows that coupling knowingly, with the floor gate and the
  behavior-level tests as the containment.
- **Revision 2** — maintainer-review absorption (2026-07-06/07, two review
  rounds). First round: the injection contract restated honestly as
  view-scoped rather than IDE-scoped; `debug_toolbar_urls()` added as the
  third required setup piece (public docs, fixture, panel-fetch test); the
  fixture corrected to re-enable `DEBUG=True` (pytest-django's
  `django_debug_mode` default forces the suite to `DEBUG=False`) with an
  always-true `SHOW_TOOLBAR_CALLBACK` and debug-toolbar cache hygiene; the
  no-toolbar baseline moved off byte-equality; pytest restraint recorded.
  Second round: the test-URLconf import-ordering contract (named module
  `tests/middleware/debug_toolbar_urls.py`, dotted-path-only reference,
  `sys.modules` eviction on setup/teardown so `urlpatterns` compute under
  `DEBUG=True`); Test 3 changed to a **named** operation (a non-null
  `operationName` requires one); the order-dependent "module not imported"
  baseline assertion removed in favor of the absence tests; `django_db`
  marking pinned for the toolbar-present group; the coverage claims mapped
  branch-by-branch with new targeted units for the branches
  real requests cannot reach; the fixture's `MIDDLEWARE` built from the real
  stack and the `DebugToolbar` class caches handled save/clear/restore;
  `render_panel`'s JSON `content`/`scripts` response shape pinned; remaining
  "GraphiQL-tagged/-view" phrasing renamed to Strawberry-view terms (Decision
  7's heading and anchors updated); the ASGI boundary restated as three
  precise claims; and the debug-toolbar 7.0.0 source files added to the
  external link block.
- **Revision 3** — third-review absorption (2026-07-07). The JSON leak guard
  gained its own real-request negative (Test 8: a test-only JSON probe view in
  the test URLconf must come back with an unmodified body and no `debugToolbar`
  key — the HTML negatives alone could not catch an inject-into-every-JSON
  implementation); the HTML negative (Test 7) made explicitly package-scoped
  (the stock toolbar handle may legitimately appear under the fixture's
  always-true callback); the targeted `_postprocess` units reworded around
  `super()._postprocess(...)` running first (protocol-complete fake toolbar;
  "no package-specific mutation", not "no touch"); the absence import blocker
  pinned to absolute top-level `debug_toolbar` names only (the
  `tests/test_routers.py` scoping), so the leaf always reaches
  `require_debug_toolbar()` (**this last point superseded by Revision 5** — the
  `importlib`-based guard needs a `sys.modules` sentinel, not a `__import__`
  block); and the template-port checklist gained a mechanical guard (Test 16)
  asserting the five copied-asset invariants as substring checks.
- **Revision 4** — fourth-review absorption (2026-07-07, source-verified
  against the debug-toolbar 7.0.0 tag). Two factual corrections: the
  missing-URLconf failure mode rewritten everywhere it appears (User-facing
  API, Decision 9's fixture bullet, Test 6, both GLOSSARY checklist items) —
  the stock postprocess renders the toolbar unconditionally for every
  processed response and the render reverses `djdt:` routes, so omitting
  `debug_toolbar_urls()` is a hard `NoReverseMatch` on the first
  toolbar-processed request, not a quiet panel-click 404; and Test 6's
  assertion strengthened past the shape check — `render_panel` returns 200
  JSON with non-empty `content` even when the id resolves to nothing (the
  "isn't available anymore" fallback), so the test now asserts the fallback
  absent and a seeded-operation SQL marker present. Precision edits: Decision
  6 states what `super()._postprocess(...)` actually does in order (per-panel
  stats/timing, unconditional render/store — the mechanism Test 6 rides and
  the dev-cost of tagged JSON operations — headers, then conditional HTML
  handle); a staticfiles + `STATIC_URL` edge-case bullet (the toolbar's own
  prerequisite, surfacing on `/graphql/` under this middleware); and the
  template-port paragraph corrected to a byte-identical copy claim (the
  upstream asset contains no Django template tags to adapt).
- **Revision 5** — fifth-review absorption (2026-07-08), verified empirically
  before absorbing. **P1 — the absence-test mechanism.** The toolbar-absent
  fixture no longer copies the router/DRF `builtins.__import__` block:
  `require_debug_toolbar()` is a thin
  [`require_optional_module`][glossary-require-optional-module] wrapper, i.e. an
  `importlib.import_module("debug_toolbar")` call, and `importlib` routes
  through `importlib._bootstrap._gcd_import` — it does **not** consult
  `builtins.__import__`. So the block is a no-op for the guard: it re-imports
  the still-installed toolbar, and the raise (if any) comes from a later
  hintless statement-import, not the wrapped guard — Tests 10/12 would have
  failed for the wrong reason. Corrected to an importlib-compatible
  `sys.modules["debug_toolbar"] = None` sentinel everywhere the mechanism is
  prescribed (this glossary bullet, Decision 9, D3, the Slice checklist, the
  Test-plan header, Tests 10/12); the eviction + **two-sided restore**
  discipline is unchanged. This supersedes Revision 3's "the leaf always reaches
  `require_debug_toolbar()` under the block" reasoning. **P1 — the degraded
  path.** A present-but-broken-install test (Test 11a) was added so the numbered
  plan actually pins what the [Error shapes](#error-shapes) prose already
  claimed it pinned. **P2 — two narrow, documented robustness divergences** from
  the verbatim upstream borrow, each pinned by a targeted unit: `process_view`
  guards `issubclass` with `isinstance(view, type)` so a non-class `view_class`
  on unrelated global traffic cannot `TypeError`/500 (a `TypeError` was
  reproduced); `_get_payload` bails to `None` on a non-object JSON body.
  **Documentation:** `application/graphql-response+json` stated explicitly out
  of scope (a follow-up compatibility item); a strict-CSP caveat added for the
  inline GraphiQL bridge script; the dependency-floor prose reworded off
  "current release" to a verified-floor claim (`7.0.0` confirmed on PyPI as the
  first release carrying the `Framework :: Django :: 6.0` classifier). No change
  to the template-port guard (already substring-based, not a golden file) or the
  fixture-locality question (already file-local; inner-helper names now named).

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary
used throughout the spec:

- [Debug-toolbar middleware][glossary-debug-toolbar-middleware] — the subject.
  The glossary already pins the planned contract: `django-debug-toolbar`
  SQL-panel integration during `/graphql/` requests, mirroring
  `strawberry-django`'s `middlewares/debug_toolbar.py` shape, distinct from the
  in-response sibling. Slice 2 updates the entry body to the implemented
  contract (the status flip to `shipped (0.0.14)` rides the joint cut).
- [Response-extensions debug middleware][glossary-response-extensions-debug-middleware]
  — the sibling card ([`TODO-ALPHA-044-0.0.14`][kanban]) this card is
  **deliberately distinct from**: this card is the server-side toolbar panel
  UI; that card surfaces SQL / exceptions **inside** the GraphQL response's
  `extensions` map. Both useful, not mutually exclusive — the card body says so
  and this spec preserves the boundary
  ([Decision 2](#decision-2--card-scope-boundary-the-server-side-toolbar-integration-ships-the-in-response-surface-fakeshop-settings-opt-in-and-async-verification-stay-out)).
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
  **two-sided** (parent-attribute) restore, exactly the [`spec-041`][spec-041]
  refinement — but the absence itself is simulated with an importlib-compatible
  `sys.modules["debug_toolbar"] = None` sentinel, **not** the router/DRF
  `builtins.__import__` block, because the guard imports via `importlib`, which
  the block does not intercept (Decision 9, Revision 5).
- [`require_optional_module`][glossary-require-optional-module] — the raising
  optional-import primitive [`spec-041`][spec-041] Slice 1 landed in
  [`utils/imports.py`][utils-imports]; `require_debug_toolbar()` is a thin
  wrapper over it, never a fourth hand-rolled import pattern.
- [Joint version cut][glossary-joint-version-cut] — why no slice here bumps the
  version: the `0.0.14` line has two open siblings and one landed predecessor
  that already deferred; the last card to land owns the version quintet and the
  release-status flips
  ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).
- [Live-first coverage mandate][glossary-live-first-coverage-mandate] — the
  test-placement rule
  [Decision 9](#decision-9--test-strategy-package-tests-driving-real-in-process-fakeshop-requests-under-settings-overrides-eviction-simulated-absence)
  answers: the covering tests drive **real fakeshop `/graphql/` requests**, but
  they live in `tests/middleware/` because the middleware only exists in the
  request path under per-test settings overrides — fakeshop's shipped settings
  deliberately do not enable a soft-dependency middleware.
- [Schema reload discipline][glossary-schema-reload-discipline] — the fixture
  obligation Decision 9 inherits from the acceptance suites: package tests that
  execute real GraphQL through the aggregate fakeshop schema call the
  single-sited `schema_reload.reload_all_project_schemas()` on setup, before
  any URLconf step, so a prior package-test `registry.clear()` can never
  surface as an order-dependent `LazyType` `KeyError` / `DuplicatedTypeName`.
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
  — the `0.0.14` sibling card (`TODO-ALPHA-043-0.0.14`) whose helpers own
  HTTP-level test ergonomics; this card's tests use `django.test.Client`
  directly, as the whole suite does today.
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
- [`ConfigurationError`][glossary-configurationerror] — NOT used by this card
  (worth saying explicitly): the failure mode here is a missing optional
  dependency at import time, which is `ImportError` with an install hint per
  the soft-dependency contract, not a configuration validation error.

## Slice checklist

Each top-level item maps to one commit / PR. **Two slices: the dependency gate +
code + template + tests (Slice 1), and docs + card wrap (Slice 2).** The card is
an M — the middleware is two overrides and a module-level helper (~100 lines
upstream including imports), the template is a ~45-line JS asset ported with the
render path renamed, and the weight is in the soft-dependency discipline and the
in-process fakeshop request tests.

- [ ] **Slice 1 — dependency gate + `middleware/debug_toolbar.py` + template +
  `tests/middleware/test_debug_toolbar.py`**
  - [ ] **The dependency gate lands first, in the same commit** (the
        [`spec-039`][spec-039] Slice-0 discipline): **`django-debug-toolbar>=7.0.0`**
        added to `[dependency-groups].dev` in [`pyproject.toml`][pyproject] and
        `uv.lock` regenerated together (`uv lock`), so the declared and locked
        dev environments never diverge. The floor is **`7.0.0` everywhere — one
        floor for the whole advertised Django range**: [`pyproject.toml`][pyproject]
        advertises `Framework :: Django :: 6.0`, and `7.0.0` is the first
        `django-debug-toolbar` release carrying the Django 6.0 classifier
        (PyPI metadata: `6.0.0`, 2025-07-25, classifies Django 4.2–5.2 only;
        `7.0.0` classifies 5.2 + 6.0 with `django>=5.2` and `python>=3.10` —
        both compatible with the package's own floors), so upstream's
        `django-debug-toolbar>=6.0.0` declaration is deliberately **not**
        copied: a `6.0.0` floor would let a Django 6.0 user follow the
        package's own install hint into an unsupported toolbar
        ([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).
        The implementation worker **records the exact pytest command** (e.g.
        `uv run pytest tests/middleware/test_debug_toolbar.py`) for the
        maintainer to run, and does not run the suite itself unless the
        maintainer explicitly authorizes pytest for this slice — the
        [`AGENTS.md`][agents] #"Do not run pytest" workflow rule; this spec
        describes the verification but does not override that rule. When the
        floor is checked, the three-places-that-must-agree rule applies — the
        dev-group specifier, the `_DEBUG_TOOLBAR_INSTALL_HINT` string, and the
        re-typed test literal all name the same floor.
  - [ ] **The Strawberry view-class gate rides the same commit**: confirm
        `strawberry.django.views.BaseView` (the `issubclass` target of
        [Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned--resolving-the-cards-djangographqlview-hedge))
        is importable at the package's pinned `strawberry-graphql>=0.262.0`
        floor in an isolated throwaway venv (never the shared `.venv` — the
        [`spec-041`][spec-041] gate discipline); its presence at the installed
        strawberry 0.316.0 is verified now (`strawberry/django/views.py`
        defines `BaseView` with `GraphQLView` / `AsyncGraphQLView` both
        subclassing it), the floor-presence check is upstream history
        re-confirmed at the gate. If it is missing at the floor, bump the
        project's Strawberry floor instead. The command and outcome are
        recorded in the build artifact
        ([Definition of done](#definition-of-done)).
  - [ ] `django_strawberry_framework/middleware/__init__.py` (new) — the
        subpackage marker with its module docstring; imports nothing optional,
        so `import django_strawberry_framework.middleware` stays clean on a
        toolbar-less machine
        ([Decision 4](#decision-4--module-template-and-test-locations-a-middleware-subpackage-an-in-package-template-asset-testsmiddleware)).
  - [ ] `django_strawberry_framework/middleware/debug_toolbar.py` (new) — the
        `require_debug_toolbar()` guard (a thin
        [`require_optional_module`][glossary-require-optional-module] wrapper;
        one `_DEBUG_TOOLBAR_INSTALL_HINT` string, no memoization) executed **at
        module import time** before the `debug_toolbar` imports the class body
        needs; the `_HTML_TYPES` constant; the module-level `_get_payload`
        helper; and `DebugToolbarMiddleware(debug_toolbar.middleware.DebugToolbarMiddleware)`
        overriding `process_view` (tag `request._is_graphiql` via
        `issubclass(view, strawberry.django.views.BaseView)`) and
        `_postprocess` (append the rendered template to GraphiQL HTML
        responses; inject the `debugToolbar` payload into Strawberry-view JSON
        operation responses; skip streaming responses; skip introspection
        queries; refresh `Content-Length` on both mutation paths)
        ([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)
        / [Decision 6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types)
        / [Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned--resolving-the-cards-djangographqlview-hedge)
        / [Decision 8](#decision-8--the-introspection-query-skip-is-preserved-verbatim)).
  - [ ] `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
        (new) — the toolbar-frontend JS asset, ported from
        [upstream's template][upstream-template] with no behavioral change (the
        `JSON.parse` / `Response.prototype.json` patch consuming the injected
        `debugToolbar` key and updating the panel titles / subtitles /
        `data-request-id`); rendered by the middleware via
        `render_to_string("django_strawberry_framework/debug_toolbar.html")`
        and resolved through Django's app-dirs template loader against the
        package's shipped [`AppConfig`][glossary-django-appconfig]
        ([Decision 4](#decision-4--module-template-and-test-locations-a-middleware-subpackage-an-in-package-template-asset-testsmiddleware)).
  - [ ] `tests/middleware/test_debug_toolbar.py` (new, plus the
        `tests/middleware/` package marker and the named test-URLconf module
        `tests/middleware/debug_toolbar_urls.py` composing fakeshop's
        `urlpatterns` + `debug_toolbar_urls()` + the test-only JSON probe
        view — referenced by dotted path
        only, evicted from `sys.modules` around each fixture activation so its
        `urlpatterns` are computed under `DEBUG=True`, per Decision 9) —
        **toolbar-present** (module- or class-level `pytest.mark.django_db`):
        real in-process fakeshop `/graphql/` requests via
        `django.test.Client` under the Decision 9 fixture (`DEBUG=True` +
        `debug_toolbar` app + `MIDDLEWARE` built from the real stack + the
        `ROOT_URLCONF` test module +
        always-true `SHOW_TOOLBAR_CALLBACK`, with `show_toolbar_func_or_path`
        cache clears and the `DebugToolbar._panel_classes`/`_urlpatterns`
        save/clear/restore on setup/teardown), each product-query test
        starting with
        [`seed_data(1)`][glossary-seed-data] — covering the GraphiQL HTML path, the JSON operation
        path (a **named** operation when `operationName` is non-null), the
        introspection skip, the deterministic JSON-`Accept` GET
        branch, the **panel-content route fetch through `debug_toolbar_urls()`
        using the injected `requestId`** (asserting `render_panel`'s JSON
        `content`/`scripts` shape), the non-GraphiQL passthroughs (HTML views
        and the JSON-probe leak guard), the
        positive/negative view detection, plus the coverage-only targeted
        units (streaming early-out, no-`request_id` bail / `has_content`
        false, header-present `Content-Length` refreshes) and the
        template-port guard over the five copied-asset invariants.
        **toolbar-absent**: the eviction + two-sided parent-attribute restore
        pattern from
        [`tests/rest_framework/test_soft_dependency.py`][test-soft-dependency],
        but with an importlib-compatible `sys.modules["debug_toolbar"] = None`
        sentinel in place of the `builtins.__import__` block (the guard imports
        via `importlib`, which the block does not intercept — Revision 5) —
        `import django_strawberry_framework` and `import
        django_strawberry_framework.middleware` both succeed; `import
        django_strawberry_framework.middleware.debug_toolbar` raises
        `ImportError` carrying the install hint (matched against a re-typed
        literal, the `_HINT_SUBSTRING` drift-catch discipline); plus the
        present-but-broken-install degraded test (Test 11a)
        ([Decision 9](#decision-9--test-strategy-package-tests-driving-real-in-process-fakeshop-requests-under-settings-overrides-eviction-simulated-absence)
        / [Test plan](#test-plan)).
  - [ ] Every new symbol carries its docstring (the [`docs/TREE.md`][tree] render
        fails on missing module docstrings) and any staged-but-not-implemented
        seam carries a `TODO(spec-042 Slice N)` source anchor per
        [`AGENTS.md`][agents].
- [ ] **Slice 2 — docs + card wrap (no version bump)**
  - [ ] [`docs/GLOSSARY.md`][glossary]
        [Debug-toolbar middleware][glossary-debug-toolbar-middleware] entry body
        updated to the implemented contract (the dotted settings path, the
        replace-the-stock-entry wiring, the required `debug_toolbar_urls()`
        URLconf step with its true failure mode — omitting it is a
        `NoReverseMatch` on every toolbar-processed request, not a
        panel-click 404 — the `BaseView` detection, the view-scoped (not
        IDE-scoped) injection contract, the introspection skip, the
        soft-dependency behavior matrix, the show-toolbar gating note, the
        staticfiles + `STATIC_URL` prerequisite note, and the
        not-a-Channels-integration boundary); the **status stays `planned for
        0.0.14`** until the joint cut flips it
        ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).
  - [ ] [`docs/TREE.md`][tree] regenerated via
        [`scripts/build_tree_md.py`][build-tree-md] (never hand-edited): the
        `middleware/debug_toolbar.py` rows move from `planned by
        TODO-ALPHA-042-0.0.14` to the real docstring-derived rows, and
        `tests/middleware/test_debug_toolbar.py` appears in the test tree.
  - [ ] [`KANBAN.md`][kanban] card wrap: `WIP-ALPHA-042-0.0.14` → Done with the
        next `DONE-042-0.0.14` id and its `SpecDoc` pointing at this spec (kanban
        DB edit + [`scripts/build_kanban_md.py`][build-kanban-md] /
        `build_kanban_html.py` re-render, never a hand-edit).
  - [ ] **Deferred to the joint `0.0.14` cut** (not this slice): the version
        quintet (`pyproject.toml`, `__version__`,
        [`tests/base/test_init.py::test_version`][test-base-init], the GLOSSARY
        package-version line, the `django-strawberry-framework` `version` entry in
        `uv.lock`), the GLOSSARY status flip to `shipped (0.0.14)`, the
        [`README.md`][readme] / [`docs/README.md`][docs-readme] "Coming next" →
        "Shipped today" moves, and the `CHANGELOG.md` bullets. Per
        [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly
        instructed", the `CHANGELOG.md` edit additionally requires the joint-cut
        slice's maintainer prompt to grant it explicitly; this spec describes the
        edit but cannot grant the permission.

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
[`TODO-ALPHA-044-0.0.14`][kanban] — so this is single-upstream parity, honest,
not fabricated).

The work is small — two overrides, one helper, one template — but it introduces
the package's **third soft dependency** (`django-debug-toolbar`, after
`djangorestframework` and `channels`), so the real design weight is in doing
that the way [`spec-039`][spec-039] and [`spec-041`][spec-041] already proved:
one guard, one install-hint string, a package import that never pays for the
integration it didn't ask for, and tests that simulate absence without
uninstalling anything.

## Current state

A true description of the repo as this spec is authored:

- **No `middleware/` subpackage exists; [`docs/TREE.md`][tree] reserves it.** The
  target package layout carries `middleware/ # planned by TODO-ALPHA-042-0.0.14 -
  Debug-toolbar middleware` with `debug_toolbar.py` beneath it — this card's
  rows. The target test tree carries no `tests/middleware/` row yet (only the
  sibling card's `tests/extensions/`); the regenerated tree adds it in Slice 2.
- **The package ships no template directory.** `django_strawberry_framework/`
  has no `templates/`; this card creates it. The packaging side is already
  covered: [`pyproject.toml`][pyproject]'s hatchling wheel target packages the
  `django_strawberry_framework` directory wholesale, so an in-package template
  ships without a new build-config entry.
- **The package ships no view class.** There is no `DjangoGraphQLView` (the
  card's working name) anywhere in the package; the fakeshop example wires
  Strawberry's own `strawberry.django.views.GraphQLView` directly in
  [`examples/fakeshop/config/urls.py`][config-urls] (wrapped in
  `ensure_csrf_cookie`, with `graphql_ide="graphiql"`), and the installed
  strawberry 0.316.0 defines `BaseView` as the shared base of `GraphQLView`
  and `AsyncGraphQLView` ([`strawberry/django/views.py`][venv-strawberry-views]).
  This is the fact that resolves the card's view-detection hedge
  ([Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned--resolving-the-cards-djangographqlview-hedge)).
- **`django-debug-toolbar` is absent at spec-authoring time.** As this spec is
  authored it is in neither `[project].dependencies` nor
  `[dependency-groups].dev` in [`pyproject.toml`][pyproject], and `import
  debug_toolbar` fails in the local dev environment (verified). Slice 1 changes
  the dev group and lockfile — so this is a point-in-time snapshot of the repo,
  not an invariant the rest of the spec relies on.
- **The soft-dependency architecture exists, twice-proven, with the shared
  primitive landed.** [`utils/imports.py`][utils-imports] ships
  [`require_optional_module(module_name, *, install_hint)`][glossary-require-optional-module]
  ([`spec-041`][spec-041] Slice 1) — `require_channels()` in
  [`routers.py`][routers] already rides it, and
  [`tests/rest_framework/test_soft_dependency.py`][test-soft-dependency] +
  `tests/test_routers.py` pin the two existing absence matrices with the
  [eviction-simulated][glossary-eviction-simulated-absence] discipline
  (including the two-sided parent-attribute restore this card's absence
  fixture copies).
- **The whole test suite already runs against fakeshop settings.**
  [`pytest.ini`][pytest-ini] sets `DJANGO_SETTINGS_MODULE = config.settings`
  with `pythonpath = examples/fakeshop`, so a root-`tests/` test can drive the
  real fakeshop `/graphql/` URLconf (GraphiQL page and products schema,
  real SQL) through `django.test.Client` — the vehicle
  [Decision 9](#decision-9--test-strategy-package-tests-driving-real-in-process-fakeshop-requests-under-settings-overrides-eviction-simulated-absence)
  uses. Fakeshop's shipped settings carry no `debug_toolbar` app and no toolbar
  middleware — and this card deliberately keeps it that way
  ([Decision 2](#decision-2--card-scope-boundary-the-server-side-toolbar-integration-ships-the-in-response-surface-fakeshop-settings-opt-in-and-async-verification-stay-out)).
- **The version line reads `0.0.13`, and the `0.0.14` joint cut is already in
  motion.** [`DONE-041-0.0.14`][kanban] landed with its version bump deferred;
  `TODO-ALPHA-043` / `044` are non-Done at this card's patch version, so the
  [joint-cut rule][glossary-joint-version-cut] applies
  ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).

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
   the source package along … only the import line changes" — applied to a
   settings dotted path, the middleware's equivalent of an import line.
4. **Both dependency states tested, against real requests.** The
   toolbar-present tests drive the real fakeshop GraphiQL page and a real
   SQL-emitting products query through `django.test.Client`; the toolbar-absent
   path pins the guarded `ImportError`. The package coverage gate
   (`fail_under = 100`) holds with `middleware/debug_toolbar.py` included
   ([Decision 9](#decision-9--test-strategy-package-tests-driving-real-in-process-fakeshop-requests-under-settings-overrides-eviction-simulated-absence)).
5. **Own nothing the toolbar already owns.** No panel logic, no request
   tracking, no toolbar configuration surface — the package contributes the
   GraphQL-shaped injection points and nothing else, so toolbar upgrades keep
   working through the stock machinery
   ([Decision 6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types)).

## Non-goals

- **The in-response debug surface.** Surfacing SQL / exceptions inside the
  GraphQL response's `extensions` map is the sibling card
  [`TODO-ALPHA-044-0.0.14`][kanban]
  ([Response-extensions debug middleware][glossary-response-extensions-debug-middleware])
  — graphene-django parity, a Strawberry `SchemaExtension`, no toolbar
  involved. The two are complementary by design; nothing in this card reads or
  writes `extensions`.
- **Wiring the toolbar into fakeshop's shipped settings.** The example's
  runtime path stays free of soft dependencies (the [`spec-041`][spec-041]
  posture for `channels`, applied again): no `debug_toolbar` in fakeshop's
  `INSTALLED_APPS`, no middleware entry, no `INTERNAL_IPS`. The tests wire it
  per-test via settings overrides
  ([Decision 9](#decision-9--test-strategy-package-tests-driving-real-in-process-fakeshop-requests-under-settings-overrides-eviction-simulated-absence));
  a dev-ergonomics opt-in in the example (a `DEBUG`-gated conditional settings
  block) is a maintainer call for the fakeshop-activation card
  ([`TODO-BETA-053-0.1.5`][kanban]) if wanted at all.
- **A package view class.** The Strawberry-view detection targets Strawberry's
  engine-owned `BaseView`
  ([Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned--resolving-the-cards-djangographqlview-hedge));
  shipping a `DjangoGraphQLView` wrapper just to have a package-owned
  `issubclass` target would be surface for surface's sake. If the package ever
  ships its own view, that card updates the one `issubclass` line.
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
sibling card's territory). The card's `Verified in upstream` section names the
two upstream files and both were read in full for this spec; the upstream module
is 101 lines and every behavior below is taken from it directly, not from
memory. Upstream's own header credits `django-graphiql-debug-toolbar` (the
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
  `object_pairs_hook=OrderedDict`), **bail (`None`) again if the decoded body is
  not a mapping** (the P2.3 guard — see below), attach
  `payload["debugToolbar"] = {"panels": {...}, "requestId": toolbar.request_id}`,
  and fill `panels` from `reversed(toolbar.enabled_panels)` with each panel's
  `title` (only when `panel.has_content`, called if callable) and
  `nav_subtitle` (called if callable), **skipping `TemplatesPanel`** (its
  content churns per request and floods the payload). The non-mapping bail is
  the card's second deliberate divergence from upstream (which does
  `payload = json.loads(...)` then `payload["debugToolbar"] = ...` assuming a
  dict): a valid single GraphQL response is always a JSON object, but a
  malformed test view or a future batch-response shape could decode to a list or
  scalar, and without the guard the subscript-assign raises and this dev-only
  tool turns an unusual response into a 500. `if not isinstance(payload, dict):
  return None` keeps the toolbar silent on such responses instead. Test 14
  pins it.
- **`DebugToolbarMiddleware(debug_toolbar.middleware.DebugToolbarMiddleware)`**
  with exactly two methods:
  - `process_view` — `request._is_graphiql = isinstance(view, type) and
    issubclass(view, BaseView)` where `view = getattr(view_func, "view_class",
    None)` and `BaseView` is `strawberry.django.views.BaseView`. The
    `isinstance(view, type)` guard is a deliberate, narrow divergence from
    upstream's `bool(view and issubclass(...))` — see
    [Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned--resolving-the-cards-djangographqlview-hedge).
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

All of it is borrowed as-is
([Decision 6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types));
the deltas are the module path, the template's render path
(`django_strawberry_framework/debug_toolbar.html`), and the soft-dependency
guard upstream does not need.

**Template-port checklist.** Because the asset is JavaScript and the package
test suite has no JS runtime, the port is a behavior-preserving copy verified
against upstream by diff, not by execution. The reviewable invariants a diff
against [upstream's template][upstream-template] must preserve — each also
pinned mechanically as a substring/pattern check by the [Test plan](#test-plan)'s
template-port guard (Test 16), so the list is not protected by visual review
alone:

- the `JSON.parse` wrapper is preserved;
- the `Response.prototype.json` wrapper is preserved;
- `delete data.debugToolbar` (the key is stripped before the IDE renders) is
  preserved;
- the `data-request-id` update on `#djDebug` (via `setAttribute`) is preserved;
- the per-panel title / subtitle DOM updates are preserved.

The port is a **byte-identical copy** of the upstream file (plus, at most, one
new header comment crediting upstream): the asset is a single `<script>` IIFE
with **no Django template tags at all** — no `{% load %}`, no `{% static %}`,
no `{% url %}`, and no pre-existing header comment to adapt. The only renamed
path in this card is the `render_to_string(...)` argument in the middleware,
which is not in the asset. All five invariants above were verified present in
the upstream file verbatim.

### Explicitly do not borrow

- **The hard `debug_toolbar` import.** Upstream imports `debug_toolbar.*` at
  module top level unguarded — it can afford to because its `debug-toolbar`
  extra and its docs gate who imports the module. This package's floor is
  "importable with zero optional dependencies", proven twice; the import stays
  at module top level (the class body needs it) but runs **behind the guard**
  ([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).
- **The `middlewares/` (plural) package name.** [`docs/TREE.md`][tree]'s target
  layout reserved `middleware/` (singular) against this card before this spec
  was authored, and the package's own subpackage names are singular-noun
  subsystems (`optimizer/`, `auth/`, `testing/`). Documented divergence, zero
  consumer impact — consumers type the dotted path once
  ([Decision 4](#decision-4--module-template-and-test-locations-a-middleware-subpackage-an-in-package-template-asset-testsmiddleware)).
- **Upstream's dependency floor.** `django-debug-toolbar>=6.0.0` is upstream's
  declaration; `6.0.0` predates the Django 6.0 classifier this package
  advertises, so the package's floor is `>=7.0.0`
  ([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).
- **The `typing_extensions.override` decorator.** Upstream decorates
  `_postprocess` with `@override` from `typing_extensions`; the package does
  not depend on `typing_extensions` directly and its floor is Python 3.10
  (`typing.override` arrives in 3.12), so the override intent is carried by the
  docstring and the test suite instead of a decorator import the package would
  add a dependency for.

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
`DEBUG=True`, the Django error page). The toolbar itself treats this as a
setup error — `debug_toolbar/apps.py` ships a system check keyed on exactly
"show-toolbar configured but toolbar URLs not installed". The support-facing
consequence: "I added the middleware and my whole GraphQL endpoint 500s"
means the URLconf step was skipped.

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
  floor)."` — the exact wording mirrors the DRF / channels hints so the three
  soft dependencies fail identically. The hint is public API in practice — it
  is the error a deploying consumer follows — so it names the **one** floor
  that covers the package's whole advertised Django range (through 6.0)
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
  **in scope as a documented non-goal, not a defect** (P2.2): Strawberry's
  Django view returns `application/json` today, so the card matches upstream and
  does not diverge for a media type the engine does not yet emit. Broadening the
  sniff to a `{"application/json", "application/graphql-response+json"}` set is a
  clean follow-up compatibility card if/when Strawberry emits the newer type;
  pinning the decision here keeps the gap explicit rather than a silent future
  regression. (Contrast the two divergences the card *does* take — the
  `isinstance` and non-mapping guards — which prevent crashes rather than add a
  speculative feature.)
- **A strict Content Security Policy on the GraphiQL page** — the HTML path
  appends an inline `<script>` (the ported bridge asset) to the GraphiQL
  response, matching upstream and its `django-graphiql-debug-toolbar` lineage. A
  strict CSP without an `unsafe-inline` / matching hash for that script will
  **block it**: the server-side toolbar history still records, but the GraphiQL
  page will not consume or strip the `debugToolbar` key from JSON responses, so
  a non-IDE client watching that endpoint could observe the extra top-level
  `debugToolbar` key. Dev-only, but real; the Slice-2 GLOSSARY / user-facing
  note must say a CSP consumer has to allow the toolbar script path or accept
  that the GraphiQL DOM updates will not run (P2.4).

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

This spec lives at `docs/spec-042-debug_toolbar-0_0_14.md`: card NNN `042`, topic
slug `debug_toolbar` (the card's subject), version segment `0_0_14` from the
card's trailing `-0.0.14`. Follows the [`docs/SPECS/NEXT.md`][next] convention.

Alternatives considered (and rejected):

- **`spec-042-debug_toolbar_middleware-0_0_14.md`.** Rejected: the `_middleware`
  suffix adds length without disambiguation — no other card touches the debug
  toolbar, and the sibling debug card ([`TODO-ALPHA-044-0.0.14`][kanban]) is
  named by its own distinct subject (response extensions), so `debug_toolbar`
  alone is unambiguous. Precedent favors the shorter slug
  (`channels_router`, `auth_mutations`, not `channels_asgi_router_module`).
- **`spec-042-django_debug_toolbar-0_0_14.md`.** Rejected: the `django_` prefix
  restates the ecosystem every card lives in; the package's own module path
  (`middleware/debug_toolbar.py`) uses the short form.

### Decision 2 — Card-scope boundary: the server-side toolbar integration ships; the in-response surface, fakeshop settings opt-in, and async verification stay out

This card ships exactly the card's DoD: the middleware module, the template
asset, the soft dependency, and the two test paths. Four adjacent-looking pieces
of work are explicitly out:

- **The in-response `extensions["debug"]` surface.** That is the sibling card
  [`TODO-ALPHA-044-0.0.14`][kanban]
  ([Response-extensions debug middleware][glossary-response-extensions-debug-middleware]),
  graphene-django parity with a completely different mechanism (a Strawberry
  `SchemaExtension`, no toolbar, no template). The card bodies of both cards
  name each other as "distinct from"; blending them here would entangle two
  parity stories with different upstreams. The one deliberate touch point:
  Slice 2's GLOSSARY body-edit keeps the two entries' "distinct from"
  cross-links accurate.
- **Fakeshop settings opt-in.** The example's shipped runtime stays free of
  soft dependencies (the [`spec-041`][spec-041] `channels` posture): wiring
  `debug_toolbar` into fakeshop's `INSTALLED_APPS` / `MIDDLEWARE` — even
  `DEBUG`-gated — would make the example's `manage.py runserver` path require
  an optional package the moment a developer flips `DEBUG`. The tests wire the
  middleware per-test instead
  ([Decision 9](#decision-9--test-strategy-package-tests-driving-real-in-process-fakeshop-requests-under-settings-overrides-eviction-simulated-absence));
  a dogfooding opt-in belongs to the fakeshop-activation card
  ([`TODO-BETA-053-0.1.5`][kanban]) if the maintainer wants it.
- **Not a Channels / ASGI toolbar integration.** Three precise statements, so
  "Django served under ASGI" is never conflated with "Channels consumer
  traffic": (1) the **tested contract** is sync Django test-client traffic
  through fakeshop's `GraphQLView` — a Django **HTTP middleware** wrapping
  Strawberry's **Django views**; (2) a Django `ASGIHandler` deployment that
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

Justification: the card body pins the boundary itself ("Both mechanisms are
useful and not mutually exclusive" on the sibling; "developer experience" /
"Single module + tests" on scope), and the [`START.MD`][start] advice ("resist
scope creep... don't quietly mix in while-I'm-here extras") applies verbatim.

Alternatives considered (and rejected):

- **Fold both debug cards into one spec.** Rejected: different upstreams
  (🍓-only vs ⚛️-only), different mechanisms (Django HTTP middleware vs
  Strawberry `SchemaExtension`), different module homes (`middleware/` vs
  `extensions/`), and the board deliberately tracks them as two cards with
  "distinct from" edges. A joint spec would re-litigate the board.
- **Add the fakeshop `DEBUG`-gated toolbar block now for dogfooding.**
  Rejected: it drags a soft dependency into the example's runtime path and adds
  a settings branch the live acceptance suite never exercises (tests run
  `DEBUG=False`); dead weight until a deliberate dogfooding pass owns it.

### Decision 3 — The symbol is `DebugToolbarMiddleware` — same class name, distinctly-ours dotted path

The class is named `DebugToolbarMiddleware`, matching both upstream's subclass
**and** the stock `django-debug-toolbar` class it extends. This looks like it
contradicts the [`spec-041`][spec-041] Decision 3 "distinctly-ours symbol name"
posture; it does not, because the two surfaces have different identity
mechanics. A router class is *imported by name* in consumer code
(`from ... import DjangoGraphQLProtocolRouter`) — the name is the API. A Django
middleware is *referenced by dotted settings string* —
`"django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware"` —
so the module path IS the distinctly-ours identity, and the class name is a
Django-ecosystem convention (`SessionMiddleware`, `AuthenticationMiddleware`,
`DebugToolbarMiddleware`) that consumers pattern-match, not a namespace anyone
imports across packages. Upstream made the same call for the same reason: its
class is also named `DebugToolbarMiddleware`, distinguished from the stock one
purely by module path. The card's own DoD pre-pins the name ("exposing a
`DebugToolbarMiddleware`"); this decision preserves it and adds the reasoning.

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

Alternatives considered (and rejected):

- **A distinctly-ours class name (`DjangoStrawberryDebugToolbarMiddleware`,
  `GraphQLDebugToolbarMiddleware`).** Rejected: the settings string already
  carries full provenance; a novel class name buys nothing a consumer sees
  (nobody imports the class) while breaking the ecosystem naming convention
  and making the migration diff noisier than one path segment.
- **Re-exporting from `middleware/__init__.py`
  (`django_strawberry_framework.middleware.DebugToolbarMiddleware`).**
  Rejected: it would force the `__init__.py` to import the guarded module —
  making `import django_strawberry_framework.middleware` itself raise on a
  toolbar-less machine and breaking whole-package walkers (the
  [`docs/TREE.md`][tree] renderer, coverage collection) for zero consumer
  benefit; the settings string is typed once either way.

### Decision 4 — Module, template, and test locations: a `middleware/` subpackage, an in-package template asset, `tests/middleware/`

The module is `django_strawberry_framework/middleware/debug_toolbar.py` — a
`middleware/` **subpackage** with one leaf module, not a top-level
`middleware.py`. Three reasons: the card's predicted-files list and
[`docs/TREE.md`][tree]'s target layout both reserve exactly this path (a shipped
commitment in the docs); the leaf-module shape is what makes the import-time
guard clean (the subpackage `__init__.py` stays empty-and-importable while the
leaf is the opt-in — the `rest_framework/` precedent,
[Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape));
and upstream uses the same package-with-leaf shape (`middlewares/debug_toolbar.py`).
The package name is **singular** `middleware/` where upstream is plural —
[`docs/TREE.md`][tree] reserved the singular before this spec, and the package's
subpackage names are singular-noun subsystems (`optimizer/`, `auth/`,
`testing/`); a one-character copy of upstream's plural would diverge from the
package's own convention to match a name consumers never see benefit from.

The template ships **inside the package** at
`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
(the doubled directory is Django's app-template namespacing convention) and is
rendered via `render_to_string("django_strawberry_framework/debug_toolbar.html")`.
Resolution rides Django's `APP_DIRS` template loader against the package's
shipped [`AppConfig`][glossary-django-appconfig] — consumers already list
`"django_strawberry_framework"` in `INSTALLED_APPS` (the package's documented
install step since `0.0.7`), so the template resolves with zero new setup.
Packaging needs no new build configuration: [`pyproject.toml`][pyproject]'s
hatchling wheel target packages the `django_strawberry_framework` directory
wholesale, non-Python files included.

The tests are `tests/middleware/test_debug_toolbar.py` — a `tests/` package
mirroring the source subpackage, the same shape `tests/auth/` /
`tests/rest_framework/` use for their subpackages (the top-level
`tests/test_routers.py` shape applies to top-level modules, which this is not).

Alternatives considered (and rejected):

- **A top-level `middleware.py` module.** Rejected: [`docs/TREE.md`][tree]'s
  planned rows commit to the subpackage; the sibling card
  ([`TODO-ALPHA-044-0.0.14`][kanban]) similarly reserves `extensions/` — the
  two debug surfaces landing as sibling subpackages keeps the package tree
  legible; and a top-level module would need the router's lazier guard shape to
  stay walker-safe (see the rejected PEP 562 alternative in
  [Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).
- **Serving the script from `static/` instead of a template.** Rejected: the
  asset is injected server-side into an already-rendered HTML body by
  `response.write(...)` — a template rendered to a string is the mechanism
  upstream uses and the only one that needs no URL configuration, no
  `collectstatic` step, and no extra request; a static file would add all
  three.
- **Inlining the script as a Python string constant.** Rejected: a ~45-line JS
  asset inside a Python module is unreviewable and unlintable as JS; the
  template file matches upstream (easing future diff-syncs against upstream
  fixes) and the app-dirs resolution costs nothing given the shipped
  `AppConfig`.

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
   ([`utils/imports.py`][utils-imports], landed by [`spec-041`][spec-041]
   Slice 1 — no fourth hand-rolled import pattern), passing the single
   `_DEBUG_TOOLBAR_INSTALL_HINT` string naming the verified
   `django-debug-toolbar>=7.0.0` floor. No memoization: absence tests re-hit
   the guard after eviction, the [`require_drf()`][rf-init] /
   `require_channels()` contract.
2. **The guard runs at module import time, and the class is a plain module
   global.** The module body is: `require_debug_toolbar()`, then the
   `debug_toolbar.middleware` / `debug_toolbar.toolbar` (and
   `strawberry.django.views`) imports, then `_HTML_TYPES`, `_get_payload`, and
   the `DebugToolbarMiddleware` class. This is the card's own DoD wording ("the
   middleware module raises `ImportError` with an install hint when actually
   imported") and the `rest_framework/` precedent — [`spec-041`][spec-041]
   Decision 5 rejected import-time guarding *for the router* precisely because
   "a top-level module sitting in the package's own directory" gets imported by
   innocent whole-package walkers, and noted "the `rest_framework/` package
   could afford import-time because its import is itself the opt-in". The
   middleware leaf is the second case, not the first: nothing imports
   `django_strawberry_framework.middleware.debug_toolbar` except a consumer's
   `MIDDLEWARE` setting (via Django's `import_string` at startup) or an
   explicit import — both are the opt-in. The parent
   `middleware/__init__.py` imports nothing optional, so package walkers
   traverse cleanly; only the leaf pays.
3. **The dependency gate.** Slice 1 adds **`django-debug-toolbar>=7.0.0`** to
   `[dependency-groups].dev` and regenerates `uv.lock` in the same commit (the
   [`spec-039`][spec-039] lockfile discipline). **The floor is `7.0.0`,
   single-valued across the hint, the dev group, and the re-typed test
   literal** — and deliberately above upstream's `>=6.0.0`: per
   [PyPI metadata][debug-toolbar-pypi],
   `django-debug-toolbar` `6.0.0` (2025-07-25) classifies Django 4.2–5.2 only,
   while `7.0.0` is the **first checked release whose metadata covers the
   package's advertised Django 6.0 range** — it carries the
   `Framework :: Django :: 6.0` classifier, with `django>=5.2` and
   `python>=3.10` — exactly matching the package's own floors
   ([`pyproject.toml`][pyproject]: `Django>=5.2`, `requires-python >=3.10`,
   classifiers 5.2 + 6.0). The [`spec-041`][spec-041] single-floor rule applies
   verbatim: the install hint is the error message a deploying consumer
   follows, so it must not guide a Django 6.0 user into an unsupported toolbar.
   The worker records the pytest command for the maintainer rather than running
   the suite (the [`AGENTS.md`][agents] rule, [Slice checklist](#slice-checklist));
   the three-places-that-must-agree rule holds.

Alternatives considered (and rejected):

- **A hard dependency.** Rejected: the toolbar is a dev-only tool by its own
  design (it disables itself outside `DEBUG` + `INTERNAL_IPS`); taxing every
  production install with it inverts its purpose. Upstream itself ships it as
  an extra, not a core dependency.
- **A `django-strawberry-framework[debug-toolbar]` extra (upstream's shape).**
  Rejected: the DRF and channels precedents both rejected extras — an extra
  changes how consumers *install*, not whether the import needs guarding (an
  extra is advisory; nothing stops an extra-less install from listing the
  middleware), so it adds a second documented thing without removing any code.
  Three soft dependencies with one uniform no-extras contract beats two
  contracts.
- **The PEP 562 lazy-symbol shape (the `routers.py` pattern: clean module
  import, guard fires on attribute access).** Rejected for this surface, with
  the reasoning made explicit since the two shapes now coexist in the package:
  (a) the consumer's access path is Django's `import_string` on a settings
  string, which imports the module and immediately does `getattr` — the guard
  fires at the same startup moment either way, so laziness buys the consumer
  nothing; (b) the leaf module has no reason to be importable without its
  dependency — unlike `routers.py` (a top-level module walkers must traverse),
  nothing legitimate imports the leaf except the opt-in; (c) the lazy shape
  costs a builder function, a module-global cache, a `__getattr__`, and a
  `# noqa: F822` — real complexity the router needed and this module does not;
  and (d) the card's DoD pre-pins the import-time wording. The
  decision rule this leaves behind: **a top-level module lazies; a dedicated
  opt-in leaf guards at import.**
- **Guarding inside `DebugToolbarMiddleware.__init__` (a stub class).**
  Rejected: the class *body* needs the import (it subclasses the stock
  middleware), so a stub would lie about identity — the exact rejection
  [`spec-041`][spec-041] recorded for the router stub, and here the two-phase
  failure would be worse: Django imports middleware at startup, so the error
  would move from a clean startup `ImportError` to a first-request failure.

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
  `process_view` of its own (it is a `__call__` / `__acall__`-style middleware
  across the toolbar's whole `3.8`–`6.x` line), so there is no stock hook to
  preserve. This method's one deliberate divergence from upstream (the first of
  the module's two — the other is `_get_payload`'s non-mapping bail) is the
  `isinstance(view, type)` guard in front of `issubclass`: upstream writes
  `bool(view and issubclass(...))`, which raises `TypeError` if a `view_class`
  attribute is ever a non-class, and this middleware runs `process_view` for
  **all** global traffic (see
  [Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned--resolving-the-cards-djangographqlview-hedge)).
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
  (nothing to reference); `None` again when the decoded body is not a mapping
  (the P2.3 divergence: a non-object JSON body would otherwise make the
  `debugToolbar` subscript-assign raise and 500 the request); otherwise decode
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

Alternatives considered (and rejected):

- **A from-scratch Django middleware reading `connection.queries`.** Rejected
  by the card's own posture line — that mechanism (lower-fidelity,
  response-side) is the *sibling card's* design space, and re-implementing
  panel rendering would break every toolbar panel except SQL while doubling
  the maintenance surface.
- **Chaining `super().process_view(...)`.** Rejected: the stock
  `debug_toolbar.middleware.DebugToolbarMiddleware` defines **no**
  `process_view` — it is a `__call__` / `__acall__`-style middleware in every
  release across the toolbar's `3.8`–`6.x` line (verified against the on-disk
  toolbar sources), so there is no stock `process_view` behavior to preserve
  and nothing for `super().process_view(...)` to reach but the base-class
  no-op. Upstream's override therefore does not chain, and neither does this
  one; byte-borrowing that choice keeps the module diffable against its
  reference.
- **Injecting into every JSON response (dropping the `_is_graphiql` gate).**
  Rejected: the gate scopes injection to responses from a **Strawberry Django
  view**, so a JSON response from some *other* view (a DRF endpoint, an admin
  AJAX call) never grows a `debugToolbar` key. It does **not** narrow injection
  to the IDE — every JSON response from the GraphQL view gets the key while the
  toolbar is enabled, IDE-originated or not (the honest contract stated in the
  [User-facing API](#user-facing-api)); the gate's job is view-scoping, not
  IDE-detection. Dropping it entirely would leak the key onto unrelated JSON
  views, which is why it stays even though it is not an IDE filter.

### Decision 7 — Strawberry-view detection: `issubclass` against `strawberry.django.views.BaseView` (engine-owned) — resolving the card's `DjangoGraphQLView` hedge

The card hedges the detection target: "Our equivalent uses the same
`issubclass` check against whichever view class the package settles on (working
name `DjangoGraphQLView`; pinned during implementation)." This spec resolves
the hedge with a fact: **the package ships no view class, and should not grow
one for this card.** The package's documented consumer wiring — and fakeshop's
real URLconf ([`examples/fakeshop/config/urls.py`][config-urls]) — uses
Strawberry's own `strawberry.django.views.GraphQLView` (or `AsyncGraphQLView`);
both subclass the engine-owned `strawberry.django.views.BaseView` (verified at
the installed strawberry 0.316.0, [`strawberry/django/views.py`][venv-strawberry-views] —
`BaseView` holds the shared constructor; the two concrete views mix it with the
sync/async HTTP-view bases). So the detection target is **`BaseView`, exactly
as upstream's is** — the check is engine-shaped, not package-shaped, and it
covers every consumer who wires Strawberry's Django views, subclassed or not.
This is the "Strawberry stays as the engine" line ([`README.md`][readme])
applied to view identity, the same way [`spec-041`][spec-041] Decision 7
applied it to the Channels consumers.

Three mechanical notes the implementation carries:

- `strawberry.django.views` is **Strawberry core's** Django integration (inside
  the pinned `strawberry-graphql>=0.262.0` floor — presence re-confirmed at the
  Slice-1 gate), not `strawberry-graphql-django`; the import adds no
  dependency. It is imported at module level *after* the guard — it needs
  Django configured but nothing optional.
- The `view_class` attribute survives decoration: `View.as_view()` sets it on
  the returned function, and Django's stacked decorators
  (`ensure_csrf_cookie`, which fakeshop's URLconf actually applies) copy
  function `__dict__` via `functools.wraps` — so the fakeshop view is detected
  through its decorator, and the test plan pins exactly that path (the tests
  drive fakeshop's real decorated URL).
- **The `issubclass` call is guarded with `isinstance(view, type)`** — the one
  deliberate divergence from upstream's verbatim `bool(view and
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
  detection differs. It joins the card's other documented divergences (the
  `middleware/` rename, the `>=7.0.0` floor, the dropped `@override`) rather
  than silently breaking the "borrow verbatim" posture, and Test 14a pins the
  non-class case the real-request tests cannot reach.

Alternatives considered (and rejected):

- **Ship a package `DjangoGraphQLView` and detect that.** Rejected: a view
  class introduced *so that a middleware can `issubclass` it* is surface for
  surface's sake — it would narrow detection to consumers who adopt the new
  view (breaking every existing `GraphQLView` consumer, including fakeshop)
  and create a public API this card has no other reason to ship. If a future
  card ships a package view for its own reasons, it subclasses `BaseView` and
  detection keeps working unchanged.
- **Path-based detection (`request.path == settings.GRAPHQL_PATH`).**
  Rejected: it invents the settings key
  [Decision 2](#decision-2--card-scope-boundary-the-server-side-toolbar-integration-ships-the-in-response-surface-fakeshop-settings-opt-in-and-async-verification-stay-out)
  forbids, breaks multi-endpoint schemas, and diverges from upstream's proven
  mechanism for zero gain.
- **Duck-typed detection (`hasattr(view, "schema")`).** Rejected: looser than
  `issubclass` with no compensating benefit — any consumer view exposing a
  `schema` attribute would be silently tagged, and the upstream-parity claim
  ("the same `issubclass` check") would be false.

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

The skip is deliberately **name-based, not content-based**: a consumer who
issues an introspection query under a different `operationName` gets a payload
(harmless), and a consumer who names a data query `IntrospectionQuery` loses
its payload (their choice). Matching upstream exactly here matters more than
closing that cosmetic gap — the skip's contract must be identical for the
one-settings-string migration
([Goal 3](#goals)) to be behavior-preserving.

Alternatives considered (and rejected):

- **Parsing the query text for `__schema` selections.** Rejected: a GraphQL
  parse per response on the dev hot path, to improve a heuristic whose false
  positives are cosmetic. Upstream's name check is O(1) and proven.
- **Making the skip configurable.** Rejected: a knob on a dev tool's history
  hygiene is configuration surface nobody asked for; upstream ships none.

### Decision 9 — Test strategy: package tests driving real in-process fakeshop requests under settings overrides; eviction-simulated absence

All tests live in `tests/middleware/test_debug_toolbar.py`. The
[live-first mandate][glossary-live-first-coverage-mandate] sends a test to
`examples/fakeshop/test_query/` when "a package line can be covered by a real
fakeshop GraphQL request" **through the example's shipped configuration** — and
no `middleware/debug_toolbar.py` line can be: fakeshop's shipped settings
deliberately carry no `debug_toolbar` app, no toolbar middleware, and no
show-toolbar override
([Decision 2](#decision-2--card-scope-boundary-the-server-side-toolbar-integration-ships-the-in-response-surface-fakeshop-settings-opt-in-and-async-verification-stay-out)),
so the middleware exists in the request path only when a test's own settings
override puts it there. Per-test settings mutation is package-test machinery,
not the example's consumer-visible surface — the same
genuinely-unreachable-live reasoning [`spec-041`][spec-041] Decision 8 recorded
for the WSGI-only router, applied to a shipped-settings boundary instead of a
protocol boundary.

The tests are **not** structural for it — they drive the real thing. Because
[`pytest.ini`][pytest-ini] points the whole suite at fakeshop's
`config.settings`, a `tests/middleware/` test uses `django.test.Client` against
fakeshop's real `/graphql/` URL — the real GraphiQL HTML render (through the
real `ensure_csrf_cookie` decorator, proving the `view_class` detection
survives decoration), and a real products query emitting real SQL through the
real optimizer — with a test fixture layering the toolbar's **three** pieces on
top via `django.test.utils.override_settings` / `modify_settings`. The DEBUG
posture is the load-bearing detail: the checked-in fakeshop
[`config/settings.py`][config-settings] sets `DEBUG = True`, but
[`pytest.ini`][pytest-ini] does not set `django_debug_mode`, so pytest-django
defaults it to `False` and forces `settings.DEBUG = False` for the whole suite
at `setup_test_environment(debug=False)` time — pytest-django's documented
`django_debug_mode` ini-option behavior (its default is `False`), a property
of the tool, not of any locally installed copy (the local-source spot-check
belongs in the build notes, not here). So the fixture
must **re-enable `DEBUG=True` itself** — both because the toolbar's default
gate returns `False` when `DEBUG` is false (verified in
[`debug_toolbar.middleware.show_toolbar`][debug-toolbar-middleware-source] at
7.0.0: `if not settings.DEBUG: return False` is the first check) *and* because
[`debug_toolbar_urls()`][debug-toolbar-toolbar-source] returns
`[]` when `DEBUG` is false, so the panel routes would not exist. The fixture:

- `override_settings(DEBUG=True)` — re-enables the toolbar's `DEBUG` gate and
  arms the `DEBUG`-gated `debug_toolbar_urls()`; makes the test independent of
  pytest-django's suite default and of any future change to fakeshop's own
  `DEBUG`.
- `modify_settings(INSTALLED_APPS={"append": "debug_toolbar"})` — Django's
  test utilities fire `setting_changed`, whose `INSTALLED_APPS` receiver
  rebuilds the app registry and the `get_app_template_dirs` cache
  (`django/test/signals.py::update_installed_apps`), so the toolbar's panels
  and templates materialize per-test.
- `override_settings(MIDDLEWARE=[...])` — a list **built from the real
  `settings.MIDDLEWARE`** with the package's dotted path inserted near the
  front, preserving the rest of fakeshop's stack (sessions, CSRF, auth,
  messages) so the test path stays the real fakeshop request path — never an
  abbreviated replacement list. The insert replaces nothing (fakeshop ships no
  stock toolbar entry), and the list must never contain **both** the stock
  `debug_toolbar.middleware.DebugToolbarMiddleware` and the package middleware.
- `override_settings(ROOT_URLCONF="tests.middleware.debug_toolbar_urls")` — a
  tiny test URLconf module ([Implementation plan](#implementation-plan)) whose
  module body composes fakeshop's real `urlpatterns` **plus**
  `debug_toolbar_urls()`, so the `djdt` namespace and its panel-content routes
  (`render_panel`) actually resolve. Without this, **every** toolbar-processed
  request dies with `NoReverseMatch` — the stock postprocess unconditionally
  renders the toolbar, whose template reverses `djdt:` routes
  ([User-facing API](#user-facing-api)) — so the whole present-path group
  crashes on its first request; Test 6 additionally needs the routes to serve
  the stored panel content. **Import ordering is load-bearing and part of the
  fixture contract:** `debug_toolbar_urls()` returns `[]` when `settings.DEBUG`
  is false and the module-level `urlpatterns` are computed **once, at first
  import** — so if anything imports the test URLconf while pytest-django's
  forced `DEBUG=False` is still in effect, the `djdt` namespace is permanently
  missing for that module object and the present-path tests crash with
  `NoReverseMatch` even though the fixture later sets `DEBUG=True`. Therefore: the test file never imports the URLconf module
  at module level (it is referenced **only** by dotted path in the
  `ROOT_URLCONF` override); the fixture activates the override only after
  `override_settings(DEBUG=True)` is in effect; on setup the fixture **evicts
  `"tests.middleware.debug_toolbar_urls"` from `sys.modules`** before the first
  request so its `urlpatterns` are computed under `DEBUG=True`; and on teardown
  it evicts the module again, so no later test can inherit `urlpatterns`
  computed under the wrong `DEBUG` value.
- `override_settings(DEBUG_TOOLBAR_CONFIG={"SHOW_TOOLBAR_CALLBACK": <always-true>})`
  — pins the show-toolbar decision to true regardless of `REMOTE_ADDR` /
  `INTERNAL_IPS` (the default gate's second check), so the test is independent
  of client-address defaults. Overriding the callback is
  `django-debug-toolbar`'s own documented test recipe.

**Cache hygiene is part of the fixture contract, not an afterthought.**
`django-debug-toolbar` 7.0.0 memoizes the resolved show-toolbar callback with
`functools.cache`
([`debug_toolbar.middleware.show_toolbar_func_or_path`][debug-toolbar-middleware-source],
verified `@cache`-decorated), and caches its panel classes and URL patterns on
the toolbar class ([`DebugToolbar._panel_classes` /
`DebugToolbar._urlpatterns`][debug-toolbar-toolbar-source]).
A per-test `DEBUG_TOOLBAR_CONFIG` / app / URLconf override that does not clear
these can leak a stale always-true callback (or stale panel/url set) into a
later test on the same worker — especially under `--dist loadscope`, which keeps
a module's tests on one worker, so the local file passes while a neighbor
inherits the leaked callback. The fixture therefore treats these as
**save / clear / restore** state, not set-to-`None` state: on setup it calls
`debug_toolbar.middleware.show_toolbar_func_or_path.cache_clear()`, **saves**
the current `DebugToolbar._panel_classes` / `DebugToolbar._urlpatterns` values,
then sets both to `None`; on teardown it calls `cache_clear()` again, discards
whatever values the test populated, and **restores the saved values** — so a
neighboring test (or an earlier same-worker test that had already initialized
the toolbar's caches) gets back exactly the state it had, rather than a
fixture-imposed `None`. Because all present-path tests share one fixed toolbar
configuration, the panel/url handling is belt-and-suspenders; the callback
`cache_clear()` is mandatory because it is tied directly to the per-test
`DEBUG_TOOLBAR_CONFIG` override.

One more fixture obligation, from pytest-django rather than the toolbar: the
toolbar-present tests drive fakeshop's real `/graphql/` view and (in Tests 3
and 6) `seed_data(1)` — real ORM traffic — so **the toolbar-present group
carries `pytest.mark.django_db`** (a module- or class-level mark over the
group is preferred, since every test in it can open the database through the
fakeshop schema or the SQL panel). Without the mark, pytest-django's database
blocker trips on the first SQL-emitting request before the middleware behavior
is exercised. The absence / guard tests (Tests 9–12) are pure import-machinery
tests and stay **unmarked**.

A second suite-shape obligation comes from *where* these tests run: they
execute real GraphQL through the aggregate `config.schema` from inside the
package tree — the tree whose files call `registry.clear()` for isolation.
[`test_query/README.md`][test-query-readme] documents the failure class: after
a package test clears the global type registry, the combined schema is exposed
to a `LazyType` `KeyError` under collection orders that did not happen to
pre-materialize the referenced types — an order-dependent flake that
`--dist loadscope` localizes to whichever worker drew both files. Every
fakeshop acceptance suite answers it with the
[schema reload discipline][glossary-schema-reload-discipline]'s single-sited
`schema_reload.reload_all_project_schemas()` helper (importable from any test
via [`pytest.ini`][pytest-ini]'s `pythonpath = examples/fakeshop`), which
rebuilds every contributing app's schema in dependency-safe order, then
reloads `config.schema` / `config.urls` and clears URL caches. The
toolbar-present fixture calls the same helper **first, on setup, before the
URLconf steps** — so the test URLconf composes freshly rebuilt fakeshop
`urlpatterns` and every request executes a fully re-registered schema
regardless of what ran earlier on the worker. The absence / guard tests
(9–12), the targeted units (13–15), and the template-port guard (16) never
execute GraphQL and skip the reload.

The toolbar-absent path reuses the
[eviction-simulated absence][glossary-eviction-simulated-absence] discipline —
strict `sys.modules` eviction of `debug_toolbar*` and
`django_strawberry_framework.middleware.debug_toolbar`, with the **two-sided
restore** (the parent `middleware` package's `debug_toolbar` attribute is
saved/restored alongside the `sys.modules` entries, putting the original module
object back in both places — the [`spec-041`][spec-041] Revision-2 refinement
that closes the `pytest-xdist` order-dependence hole) — but simulates the
absence itself with an **importlib-compatible `sys.modules["debug_toolbar"] =
None` sentinel, not the `builtins.__import__` block the router/DRF fixtures
use** (Revision 5). The distinction is load-bearing here in a way it is not for
the router: `require_debug_toolbar()` is a thin
[`require_optional_module`][glossary-require-optional-module] wrapper, i.e. an
`importlib.import_module("debug_toolbar")` call, and `importlib` routes through
`importlib._bootstrap._gcd_import` — it does **not** consult
`builtins.__import__`. A `__import__` block is therefore a no-op for this guard:
it re-imports the still-installed toolbar and the guard returns it, so the raise
(if any) would come from a later hintless statement-import rather than the
wrapped guard — Tests 10/12 would fail for the wrong reason. A `None` entry in
`sys.modules` is the documented importlib absence sentinel: `import_module`
raises `ModuleNotFoundError` (`"import of debug_toolbar halted; None in
sys.modules"`), which the guard catches and re-raises as the install hint.
(Empirically verified against the installed `channels`: under a `__import__`
block `importlib.import_module` still returns the real module; under the `None`
sentinel it raises. The same sentinel shape is documented in
[`utils/imports.py`][utils-imports]'s `import_attr_if_importable`.) The block is
still fine for the DRF/router fixtures — DRF's guard is a direct `import`
statement, and the router's builder statement-imports `channels.*` submodules
that the block *does* see — but this guard's importlib shape needs the sentinel.
The install hint is matched against a **re-typed literal** in the test file (the
`_HINT_SUBSTRING` drift-catch discipline — a test asserting the imported
constant against itself could never notice the hint drifting from the dev-group
floor).

Alternatives considered (and rejected):

- **A live `examples/fakeshop/test_query/` placement with the same settings
  overrides.** Rejected: the live suite's charter is "consumer-visible GraphQL
  behavior" through the example as shipped, and its coverage rule reserves the
  fall-back for code "genuinely unreachable from a live `/graphql/` request"
  ([`test_query/README.md`][test-query-readme]) — which these lines are until
  settings opt in. A test that must rewrite `INSTALLED_APPS` / `MIDDLEWARE`
  before the surface exists is asserting package-internal wiring, not the
  example's shipped behavior; it would blur the boundary the
  [live-first mandate][glossary-live-first-coverage-mandate]'s placement rule
  protects. When a future card opts fakeshop's settings into the toolbar for
  real, the covering test moves live and the package stand-in is deleted (the
  documented promotion rule).
- **Wiring `debug_toolbar` permanently into fakeshop settings for the tests'
  benefit.** Rejected in
  [Decision 2](#decision-2--card-scope-boundary-the-server-side-toolbar-integration-ships-the-in-response-surface-fakeshop-settings-opt-in-and-async-verification-stay-out);
  additionally it would put the toolbar's middleware into every *other* suite
  request's path (inert but present), a blanket change to the whole suite's
  request pipeline for one test file's convenience.
- **Unit-testing the overrides against synthetic
  `HttpRequest` / `HttpResponse` objects only.** Rejected: the module exists
  to compose with the *real* toolbar lifecycle (`super()._postprocess`
  behavior, `toolbar.request_id` assignment, panel enablement) and the *real*
  Strawberry view (`view_class` through a decorator) — precisely the seams
  synthetic objects would fake. The [`START.md`][start] "coverage is a
  feature" posture: if the composition is wrong, only real traffic notices.
- **Uninstall-based absence testing (a separate no-toolbar CI job).**
  Rejected: the DRF and channels precedents both chose simulation (one env,
  one `uv run pytest` gate, no matrix).

### Decision 10 — Version bumps are owned by the joint `0.0.14` cut

No slice in this card edits the package-version state: `[project].version` in
[`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init], or
[`tests/base/test_init.py::test_version`][test-base-init]. This card **shares
the `0.0.14` patch line** with two open siblings —
[`TODO-ALPHA-043-0.0.14`][kanban] and [`TODO-ALPHA-044-0.0.14`][kanban] — and
one landed predecessor, [`DONE-041-0.0.14`][kanban], whose spec's Decision 10
already deferred the bump to the **[joint `0.0.14`
cut][glossary-joint-version-cut]** (the last `0.0.14` card to land). The
board's `## Done` column confirms `DONE-041` flipped Done with the version line
still reading `0.0.13` — the deferral this card continues. The release-status
wording splits the same way: Slice 2 updates **implemented-on-main** docs (the
GLOSSARY entry body, the regenerated [`docs/TREE.md`][tree]) but the public
`shipped (0.0.14)` status flip, the [`README.md`][readme] /
[`docs/README.md`][docs-readme] "Coming next" → "Shipped today" moves, and the
`CHANGELOG.md` bullets defer to the joint cut.

**`uv.lock` is NOT a version file — it is updated in this card, deliberately.**
The Slice-1 dependency gate adds `django-debug-toolbar` to
`[dependency-groups].dev` and regenerates the lockfile in the same commit; the
**toolbar dependency entries** in `uv.lock` change here, while the package's
own `version` entry inside it stays `0.0.13` until the joint cut — the exact
reconciliation [`spec-041`][spec-041] Decision 10 pinned for the channels
dev-group add.

Justification: per [`docs/SPECS/NEXT.md`][next] Step 3 / Step 6, when multiple
cards target one patch version the bump belongs to the joint cut, not any
individual card's spec. Three non-Done cards remain at `0.0.14` after this one
flips; this card is not the last.

Alternatives considered (and rejected):

- **Bump to `0.0.14` in Slice 2.** Rejected: two siblings still ship into
  `0.0.14`; a per-card bump races the joint cut and would be reconciled twice
  over.
- **Defer the lockfile regeneration to the joint cut too.** Rejected: Slice 1's
  tests import `debug_toolbar`; a dev-dependency without its lock entry breaks
  the reproducible-env contract the moment CI runs `uv sync`.

## Implementation plan

The file-level delta map for the Worker 0 build handoff (each row's contract is
specified in the decisions cited; **no slice bumps the version** — the joint
`0.0.14` cut owns it,
[Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)):

| File | Change | Slice |
| --- | --- | --- |
| [`pyproject.toml`][pyproject] + `uv.lock` | `django-debug-toolbar>=7.0.0` into `[dependency-groups].dev`; lock regenerated in the same commit | 1 |
| `django_strawberry_framework/middleware/__init__.py` (new) | Subpackage marker, docstring only; imports nothing optional ([Decision 4](#decision-4--module-template-and-test-locations-a-middleware-subpackage-an-in-package-template-asset-testsmiddleware)) | 1 |
| `django_strawberry_framework/middleware/debug_toolbar.py` (new) | `_DEBUG_TOOLBAR_INSTALL_HINT` / `require_debug_toolbar()` (thin [`require_optional_module`][glossary-require-optional-module] wrapper) executed at import; `_HTML_TYPES`; `_get_payload`; `DebugToolbarMiddleware` with `process_view` + `_postprocess` overrides ([Decision 3](#decision-3--the-symbol-is-debugtoolbarmiddleware--same-class-name-distinctly-ours-dotted-path) / [5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape) / [6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types) / [7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned--resolving-the-cards-djangographqlview-hedge) / [8](#decision-8--the-introspection-query-skip-is-preserved-verbatim)) | 1 |
| `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` (new) | The GraphiQL-side JS asset, ported from [upstream][upstream-template] with the render path renamed ([Decision 4](#decision-4--module-template-and-test-locations-a-middleware-subpackage-an-in-package-template-asset-testsmiddleware)) | 1 |
| `tests/middleware/__init__.py` + `tests/middleware/test_debug_toolbar.py` (new) | Tests 1–16 per the [Test plan](#test-plan), incl. the panel-route fetch, the fixture's schema-reload + cache save/clear/restore contract, the coverage-only targeted units, and the template-port guard | 1 |
| `tests/middleware/debug_toolbar_urls.py` (new) | The test URLconf: module body composes fakeshop's real `urlpatterns` + `debug_toolbar_urls()` + a tiny test-only JSON probe view (Test 8's non-Strawberry JSON negative). Referenced **only** by dotted path in the fixture's `ROOT_URLCONF` override (never imported at test-module import time) and evicted from `sys.modules` on fixture setup and teardown so `urlpatterns` are always computed under `DEBUG=True` (Decision 9) | 1 |
| [`docs/GLOSSARY.md`][glossary] | [Debug-toolbar middleware][glossary-debug-toolbar-middleware] entry body updated to the implemented contract; status flip deferred | 2 |
| [`docs/TREE.md`][tree] | Regenerated (script-rendered) after the card flips Done | 2 |
| [`KANBAN.md`][kanban] / `KANBAN.html` | Card wrap via DB edit + re-render | 2 |

## Helper-reuse obligations (DRY)

The module is small; the ledger is short. Reuse is named per item, and
deliberate *non*-reuse carries its reason (the [`spec-040`][spec-040] /
[`spec-041`][spec-041] discipline).

- [ ] **D1** — the guard rides
  [`utils/imports.py::require_optional_module`][glossary-require-optional-module]
  (landed by [`spec-041`][spec-041] Slice 1): `require_debug_toolbar()` is a
  thin wrapper passing `_DEBUG_TOOLBAR_INSTALL_HINT` — never a fourth
  hand-rolled import pattern
  ([Decision 5](#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape)).
- [ ] **D2** — the install-hint string lives in exactly one module constant
  (`_DEBUG_TOOLBAR_INSTALL_HINT`), matched in tests by a **re-typed literal**
  (the `_HINT_SUBSTRING` drift-catch discipline from
  [`test_soft_dependency.py`][test-soft-dependency], now three-for-three across
  the soft dependencies).
- [ ] **D3** — the toolbar-absent fixture reuses the eviction + **two-sided
  restore** pattern (the [`spec-041`][spec-041] refinement: the parent
  `middleware` package's attribute is saved/restored together with the
  `sys.modules` entries, so no test order leaves the attribute path and the
  import path holding different module objects), but simulates the absence with
  an importlib-compatible `sys.modules["debug_toolbar"] = None` sentinel rather
  than the `builtins.__import__` block the DRF/router fixtures use — because the
  guard imports via `importlib`, which the block does not intercept
  ([Decision 9](#decision-9--test-strategy-package-tests-driving-real-in-process-fakeshop-requests-under-settings-overrides-eviction-simulated-absence),
  Revision 5). The eviction + restore structure is copied and target names
  swapped; the absence *mechanism* is deliberately not. **This is the third copy
  of the absence fixture** (DRF, router, now toolbar) — but the three are **not**
  behavior-identical, and that is the point: DRF blocks a direct `import`
  statement, the router blocks `channels.*` submodule statement-imports its
  builder runs, and this guard needs the `None` sentinel because
  `importlib.import_module` bypasses the block. So **do not factor a shared
  absence helper in this card.** A premature extraction with a single "pluggable
  import-blocker predicate" would encode the wrong assumption that all guards
  share one absence mechanism; the correct extraction (deferred to a dedicated
  cleanup card) must support **both** the block shape (direct/statement-import
  guards) **and** the sentinel shape (importlib guards). Do not block this card
  on it, and do not let the toolbar copy drift from the two-sided-restore
  discipline.
- [ ] **D4** — the guard has **no memoization**, and the module holds **no
  class cache to manage**: unlike the router's `_ROUTER_CLASS`, the class is a
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
  stock middleware decided to process at all). Note this is why the test fixture
  must set **both** `DEBUG=True` (pytest-django forces the suite to `DEBUG=False`)
  **and** an always-true `SHOW_TOOLBAR_CALLBACK` (to be independent of
  `INTERNAL_IPS` / `REMOTE_ADDR`) — it satisfies the real gate rather than
  bypassing it
  ([Decision 9](#decision-9--test-strategy-package-tests-driving-real-in-process-fakeshop-requests-under-settings-overrides-eviction-simulated-absence)).
- **Streaming responses are skipped.** `response.streaming` returns before any
  body inspection — a streaming body has no `.content` to decode or append to.
  Strawberry's Django views stream only for multipart-subscription responses;
  either way the guard is upstream's and stays.
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
  ([Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned--resolving-the-cards-djangographqlview-hedge));
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
- **`override_settings(INSTALLED_APPS=...)` in a `loadscope` suite.** Django's
  test utilities re-populate the app registry on `INSTALLED_APPS` change and
  restore it on exit; the fixture scopes the override to each test (or the
  module's fixture) so no toolbar state leaks into neighboring files — and
  `pytest.ini`'s `--dist loadscope` keeps the whole module on one worker, the
  same isolation story every registry-touching test file in the suite already
  relies on. **The toolbar's own module- and class-level caches do NOT reset
  with the settings override**, though — `show_toolbar_func_or_path` is
  `@cache`-memoized and `DebugToolbar._panel_classes` / `_urlpatterns` are
  class attributes — so the fixture clears the callback cache and
  saves / clears / restores the class caches on setup and teardown
  (Decision 9's cache-hygiene contract). Under `--dist loadscope` a
  leaked always-true callback would otherwise let this module pass while a
  later same-worker test inherits it; the cache clears close that hole.
- **Template `Content-Length` refresh.** Both mutation paths (`response.write`
  on HTML, `response.content = ...` on JSON) refresh `Content-Length` only
  when the header is already present — Django's `HttpResponse` normally
  computes it at serialization time, but a middleware or server layer that
  pre-set it would otherwise serve a truncated body. Upstream's guard, kept.

## Test plan

All in `tests/middleware/test_debug_toolbar.py` (placement per
[Decision 9](#decision-9--test-strategy-package-tests-driving-real-in-process-fakeshop-requests-under-settings-overrides-eviction-simulated-absence)).
The toolbar-present tests share the one fixture specified in Decision 9's
fixture contract — a setup-time `schema_reload.reload_all_project_schemas()`
call first (the acceptance suites' order-independence-by-reconstruction
discipline, Decision 9), then `DEBUG=True`, `INSTALLED_APPS + "debug_toolbar"`,
`MIDDLEWARE` built from the real `settings.MIDDLEWARE` with the package dotted
path inserted near the front, `ROOT_URLCONF =
"tests.middleware.debug_toolbar_urls"` (referenced by dotted path only — never
imported at test-module import time — and evicted from `sys.modules` on both
setup and teardown so its `urlpatterns` are always computed under `DEBUG=True`),
and `DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": <always-true>}`, plus the
mandatory `show_toolbar_func_or_path.cache_clear()` and the save / clear /
restore of `DebugToolbar._panel_classes`/`_urlpatterns` on setup and teardown —
driving fakeshop's real `/graphql/` URL through `django.test.Client`. The
toolbar-present group carries a module- or class-level `pytest.mark.django_db`
(Decision 9); the absence / guard tests (9–12), the targeted coverage units
(13–15), and the template-port guard (16) stay unmarked. **Every
product-query test's first executable line is `seed_data(1)`** (or an explicit
`seed_data(N)`) from `apps.products.services` — the repo's seed-helper rule; the
panel payload does not depend on row counts, but the query must hit real rows to
emit SQL. The absence / guard tests (9–12) deliberately import **no** fakeshop
catalog helper.

**Toolbar-present — the GraphiQL HTML path:**

1. GET `/graphql/` (the GraphiQL IDE page) returns 200 HTML carrying **both**
   injections: the stock toolbar handle (`id="djDebug"` — proving
   `super()._postprocess` ran and the stock pipeline is intact) and the
   package's appended template script (a distinctive substring of the asset —
   proving the HTML branch fired). `Content-Length`, when present, matches
   `len(response.content)` after the append.
2. The same GET **without** the settings fixture (stock fakeshop settings, no
   toolbar) asserts **stable behavior, not byte-equality** (a Strawberry-rendered,
   `ensure_csrf_cookie`-wrapped page has no checked-in golden file): status 200,
   an HTML `Content-Type`, the GraphiQL marker present, the package
   debug-toolbar script **absent**, and the stock toolbar handle **absent**.
   This is the no-toolbar baseline proving the card changes nothing for
   consumers who don't opt in; pinning it here makes a future settings-bleed
   regression fail in this file, not an unrelated one. Deliberately **no**
   "package middleware module not imported" assertion: under `--dist loadscope`
   any toolbar-present test that ran earlier on the same worker leaves
   `django_strawberry_framework.middleware.debug_toolbar` in `sys.modules`, so
   that assertion would pass or fail on local test order alone while the
   response is perfectly clean. Import-surface guarantees belong to the absence
   tests (9–12), which evict and restore modules deliberately.

**Toolbar-present — the JSON operation path:**

3. `seed_data(1)`, then POST a **named** products operation — a non-null
   `operationName` in the JSON envelope requires a named operation document, so
   the query is e.g. `query ToolbarItems { allItems(first: 1) { edges { node {
   name category { name } } } } }` with `"operationName": "ToolbarItems"` (an
   anonymous `{ ... }` document plus a non-null `operationName` fails GraphQL
   validation before proving anything; a test that wants an anonymous operation
   must send `"operationName": null` or omit the key): the
   200 JSON response body carries `debugToolbar` with a non-empty `panels`
   mapping and a `requestId`; the `SQLPanel` entry is present with a non-null
   `subtitle` (the query count — the SQL the operation actually emitted);
   `TemplatesPanel` is absent from the mapping (the skip); the response's
   own `data` key is intact beside the injected one; and `Content-Length`, if
   present on the response after injection, equals `len(response.content)` (a
   behavior check only — the header-present refresh **branches** are owned by
   the targeted unit Test 15 below, since a real Strawberry `HttpResponse` may
   reach the middleware without the header set, Django normally computing it at
   serialization time).
4. POST with `operationName: "IntrospectionQuery"` (a real introspection
   document): the response body carries **no** `debugToolbar` key and is
   otherwise a normal introspection result
   ([Decision 8](#decision-8--the-introspection-query-skip-is-preserved-verbatim)).
5. **GET `/graphql/?query=...` requesting JSON deterministically** — send
   `HTTP_ACCEPT="application/json"` so Strawberry's Django view returns the JSON
   result, not the GraphiQL HTML page. **Assert `Content-Type` is
   `application/json` before** inspecting the body, then assert the payload is
   injected: this exercises the broad-except `operationName` sniff branch (the
   GET body is empty, `json.loads` raises → `operationName` is `None` → inject).
   The explicit `Accept` header is what keeps this test on the JSON branch
   instead of accidentally re-covering the HTML path of Test 1.

**Toolbar-present — the panel-content route (the actual user story):**

6. `seed_data(1)`, POST the named products operation of Test 3, and capture
   `debugToolbar.requestId` from the JSON body. Then GET the toolbar's
   `render_panel` view through the fixture's `debug_toolbar_urls()` routes —
   `GET /__debug__/render_panel/?request_id=<id>&panel_id=SQLPanel` under the
   default prefix (the test resolves the path via the route, staying correct if
   the fixture ever passes a custom `debug_toolbar_urls(prefix=...)`) — and
   assert what debug-toolbar 7.0.0 actually returns: a **JSON** response
   ([`render_panel`][debug-toolbar-views-source] responds with a JSON body
   carrying `content` and `scripts` keys, keyed off `request_id` / `panel_id`
   query parameters) whose `content` is the **stored SQL-panel content for
   this id**. "Non-empty" is not enough to prove that: when
   `DebugToolbar.fetch()` finds nothing for the `request_id`, `render_panel`
   returns 200 JSON with a *non-empty* `content` too — the fallback "Data for
   this panel isn't available anymore. Please reload the page and retry."
   So the test pins the success direction on both sides: the fallback message
   is **absent**, and at least one SQL-panel-specific marker from the seeded
   operation is **present** (the rendered panel content contains the
   operation's SELECT — e.g. the products table name). A broken store
   round-trip (wrong id captured, per-test isolation eating the record, an id
   from a different toolbar instance) then fails instead of passing on shape.
   Inspecting the `requestId` in the JSON (Test 3) proves the id exists;
   **this** test proves the id is *usable* — the id round-trips to the stored
   panel content through the real route, which Tests 3/5 alone do not prove.
   (It does not guard against a *missing* URLconf — omitting
   `debug_toolbar_urls()` crashes every toolbar-processed request with
   `NoReverseMatch` long before any panel fetch, per the
   [User-facing API](#user-facing-api).)

**Toolbar-present — detection mechanics:**

7. Detection's negative direction for HTML, parametrized over both Django
   dispatch shapes: a non-Strawberry **function-based** view (fakeshop's `/`
   index) and a non-Strawberry **class-based** view (Django's own `LoginView`
   at fakeshop's `/login/`) each return their normal HTML with **no
   package-appended template script** and **no** `debugToolbar` anywhere in the
   body — the `_is_graphiql=False` passthrough for both `view_func` and
   `view_class` dispatch. The negative assertion is deliberately
   **package-scoped, not toolbar-scoped**: the fixture's always-true show
   callback means the **stock** toolbar handle (`id="djDebug"`) may legitimately
   appear in this ordinary HTML, because the package middleware subclasses and
   preserves stock behavior — asserting "no stock toolbar" here would fail for
   the wrong reason. The positive direction needs no separate test: the
   GraphiQL/JSON requests in Tests 1/3/5/6 already run through the real
   `ensure_csrf_cookie(GraphQLView.as_view(...))` URLconf, so a passing Test 3
   IS the proof that `view_class` + `issubclass(..., BaseView)` resolves
   through `functools.wraps`-copied attributes.
8. Detection's negative direction for **JSON** — the payload leak guard. The
   HTML negatives above cannot prove it: an implementation that injected
   `debugToolbar` into *every* JSON response would still pass Tests 1–7. The
   test URLconf module gains a tiny test-only **JSON probe view** (a plain
   Django function view returning `JsonResponse({"probe": "ok"})`, defined in
   `tests/middleware/debug_toolbar_urls.py` beside the composed fakeshop
   `urlpatterns` + `debug_toolbar_urls()`); with the toolbar fixture active,
   GET it through `django.test.Client` and assert the response is JSON, the
   probe body round-trips unmodified, and there is **no** top-level
   `debugToolbar` key. Stock debug-toolbar *headers* on the response are
   acceptable — the contract under test is "unrelated JSON bodies are never
   mutated", not "the stock toolbar ignores the request".

**Toolbar-absent (simulated via eviction + a `sys.modules["debug_toolbar"] =
None` importlib sentinel — Revision 5; the `builtins.__import__` block the
router/DRF fixtures use is a no-op for this `importlib`-based guard):**

9. `import django_strawberry_framework` and
   `import django_strawberry_framework.middleware` both succeed;
   `from django_strawberry_framework import *` binds no toolbar name.
10. `import django_strawberry_framework.middleware.debug_toolbar` raises
    `ImportError` whose message contains `django-debug-toolbar>=7.0.0` — the
    **hint**, not the bare `ModuleNotFoundError` (proving `require_debug_toolbar()`
    wrapped it, which the sentinel makes possible and the block would not) —
    matched against the **re-typed literal** in the test file (the
    `_HINT_SUBSTRING` discipline), with the original `ImportError` chained
    (`__cause__`).
11. After restore, the module imports again in the same process and
    `django_strawberry_framework.middleware.debug_toolbar is
    sys.modules["django_strawberry_framework.middleware.debug_toolbar"]` —
    the two-sided-restore invariant (D3), making the present-path tests
    order-independent under `pytest-xdist`.

**Test 11a — present-but-broken install (degraded path).** Leave a
real/importable top-level `debug_toolbar` but make its `middleware` submodule
unimportable (`sys.modules["debug_toolbar.middleware"] = None`, or a narrow
`importlib.import_module` monkeypatch for that exact submodule).
`require_debug_toolbar()` **passes** (it imports only the top-level package),
then the leaf's own `import debug_toolbar.middleware` statement fails: assert
`import django_strawberry_framework.middleware.debug_toolbar` raises the **raw**
`ImportError` naming `debug_toolbar.middleware` — **without**
`_DEBUG_TOOLBAR_INSTALL_HINT` — and that `__cause__` is the original failing
import. This pins the [Error shapes](#error-shapes) contract that the guard
wraps only the top-level package and never misreports a broken install as "not
installed" (the numbered plan previously claimed to pin this but did not —
Revision 5).

**Guard unit shape:**

12. `require_debug_toolbar()` returns the imported `debug_toolbar` module when
    present (identity with `sys.modules["debug_toolbar"]`), and under the
    `None` sentinel raises the hint-carrying `ImportError` — the thin-wrapper
    contract over
    [`require_optional_module`][glossary-require-optional-module] (whose own
    unit tests, landed with [`spec-041`][spec-041], are not duplicated here).
    (Under a `builtins.__import__` block this assertion would fail: the guard's
    `importlib.import_module` call bypasses the block and returns the still
    installed toolbar — Revision 5.)

**Coverage-only targeted units** (branches the real toolbar lifecycle does not
naturally expose through Tests 1–8; unmarked, no database, direct calls with
stub objects — mock only where the real path is impossible, per the
[coverage-priority rule][glossary-live-first-coverage-mandate]). One shared
constraint shapes all three: the package override calls
`super()._postprocess(...)` **before** its own branches, so any unit that
enters `_postprocess` runs the stock toolbar postprocess first — the fake
toolbar must therefore implement the small stock-toolbar protocol
`debug_toolbar.middleware.DebugToolbarMiddleware._postprocess` consumes
(`enabled_panels`, `render_toolbar()`, and no-op panel record/generate hooks),
or use a real toolbar instance where that is simpler:

13. **Streaming early-out** — call `_postprocess` with a
    `StreamingHttpResponse` and a protocol-complete fake toolbar, and assert
    **no package-specific mutation after the stock postprocess returns**: no
    appended template script, no `debugToolbar` payload, unchanged streaming
    content. Not "returns without touching the response" in the absolute
    sense — the stock postprocess runs first and may legitimately generate
    stats and headers before `if response.streaming` sends the package branch
    home. No listed real-request test returns a streaming response, so the
    branch is unreachable through Tests 1–8.
14. **`_get_payload` no-`request_id` bail** — call `_get_payload` with a stub
    toolbar whose `request_id` is `None` and assert `None`: under the fixture's
    always-true show callback the real toolbar always assigns a `request_id`,
    so the bail never fires in the real-request tests. The same test (or a
    sibling case) drives a stub panel with `has_content` false, since real
    default panels do not reliably produce both `has_content` outcomes across
    toolbar versions. A further sibling case drives the **non-object-body bail**
    (the P2.3 guard): a response whose decoded JSON is a list (not a mapping)
    makes `_get_payload` return `None`, so the JSON path leaves the body
    unmodified. A valid single GraphQL response is always an object, so this
    branch is unreachable through the real-request tests.

**Test 14a — `process_view` non-class `view_class` guard.** Call `process_view`
with a `view_func` whose `view_class` attribute is a non-class value (e.g. the
string `"not-a-class"`) and assert `request._is_graphiql` is `False` with **no
exception**. The `isinstance(view, type)` guard (P2.1) short-circuits before
`issubclass`, which would otherwise raise `TypeError` and 500 the request.
Tests 7–8 only drive real class/function views, so this guard — which matters
precisely because the middleware runs for **all** global traffic, not just
GraphQL — is unreachable through them.

15. **`Content-Length` refresh branches, HTML and JSON** — build responses
    with `Content-Length` explicitly pre-set, run the mutation paths, and
    assert the header equals `len(response.content)` after. These units cover
    the package's refresh branches **after stock postprocessing has already
    run** (the pre-set header is the point: a real Strawberry `HttpResponse`
    may reach the middleware without the header, so the header-present
    branches need it planted).

**Template-port guard** (mechanical, no JS runtime — reads the asset, executes
nothing):

16. Render (or read) `templates/django_strawberry_framework/debug_toolbar.html`
    and assert the five [template-port checklist](#from-strawberry-graphql-django--borrow-the-mechanism-verbatim)
    invariants as substring/pattern checks: the `JSON.parse` wrapper, the
    `Response.prototype.json` wrapper, `delete data.debugToolbar`, the
    `data-request-id` update on `#djDebug`, and the per-panel title / subtitle
    DOM updates. The suite has no JS runtime, so this does not prove the script
    *works* — it turns the checklist's by-eye diff into a mechanical guard that
    fails if a future edit drops one of the load-bearing behaviors.

Coverage: the package gate is `fail_under = 100`, and each branch has a named
owner rather than an implicit hope. Reached by the **real-request tests
(1–8)**: the guard's success path, both `_postprocess` main branches (HTML —
Test 1; JSON — Tests 3/5), the non-GraphiQL early-out (HTML — Test 7; JSON —
Test 8), the introspection skip (Test 4), the `operationName` except-branch
(Test 5), the `TemplatesPanel` skip and the `has_content`-true panel path
(Test 3), and the panel-route round trip (Test 6). Reached by the
**absence / guard tests (9–12, incl. the degraded-install Test 11a)**: the
guard's raise path, the import-surface matrix, and the raw-`ImportError`
propagation for a present-but-broken install. Reached **only by the targeted
units (13–15, incl. 14a)**: the streaming early-out, the no-`request_id` bail /
`has_content`-false / non-object-body branches of `_get_payload`, the
`isinstance(view, type)` detection guard, and both header-present
`Content-Length` refreshes. The template-port guard (16) earns no Python
coverage — the asset is markup and JavaScript, not
counted lines; it exists to pin the port's five invariants mechanically. If
implementation finds another
branch unreachable through real requests, it gets its own targeted unit the
same way — the fallback is named per branch, never a blanket claim that the
numbered real-request tests reach everything.

## Doc updates

Slice 2, per the F8 split in
[Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut) —
implemented-on-main docs update here; release-status wording defers to the
joint `0.0.14` cut:

- [`docs/GLOSSARY.md`][glossary] — the
  [Debug-toolbar middleware][glossary-debug-toolbar-middleware] entry body
  grows the implemented contract: the dotted settings path and the
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
  stays accurate in both entry bodies. Status **stays `planned for 0.0.14`**
  until the joint cut.
- [`docs/TREE.md`][tree] — regenerated via
  [`scripts/build_tree_md.py`][build-tree-md] after the card flips Done (the
  file is script-rendered; missing module docstrings fail the render, so the
  `middleware/__init__.py` and `middleware/debug_toolbar.py` docstrings are
  written for their rows): the package tree's planned `middleware/` annotations
  resolve to real rows; the test tree gains `tests/middleware/`.
- [`KANBAN.md`][kanban] / `KANBAN.html` — card wrap via the DB + re-render
  (Slice 2 checklist).
- **Deferred to the joint cut:** [`README.md`][readme] /
  [`docs/README.md`][docs-readme] "Coming next — remaining alpha (`0.0.14`)" →
  "Shipped today" moves, the GLOSSARY status flip + package-version line,
  [`TODAY.md`][today]'s coming-next wording, and `CHANGELOG.md` (which
  additionally requires the explicit maintainer grant per [`AGENTS.md`][agents]).

## Risks and open questions

- **`_postprocess` is a private-underscore method of `django-debug-toolbar`.**
  The subclass overrides (and chains to) a method the toolbar does not
  advertise as API; a toolbar major release could rename or reshape it, and
  the `>=7.0.0` floor is deliberately unbounded above (the package pins
  floors, not ceilings). This is a knowingly borrowed coupling — upstream
  carries the identical override (decorated `@override`, so upstream CI
  notices a rename) and the archived `django-graphiql-debug-toolbar` before it
  did too; the mechanism has been stable across the toolbar's 4.x → 7.x line.
  **Preferred posture:** accept the coupling; the behavior-level tests
  (Tests 1, 3) fail loudly on any reshape, and the fix tracks upstream's fix.
  **Fallback:** if a toolbar release breaks the hook, the gate that catches it
  (the suite under a refreshed lockfile) also scopes the repair — worst case
  the floor gains a temporary ceiling with a follow-on card, the same
  containment any soft dependency carries.
- **The `7.0.0` floor is metadata-grounded, not yet suite-verified.** Per PyPI
  metadata, `7.0.0` is the first release with the Django 6.0 classifier
  (`6.0.0` stops at 5.2), and its `django>=5.2` / `python>=3.10` floors match
  the package's own. The Slice-1 dependency gate installs it and the worker
  records the pytest command for the maintainer to run (not run by the worker
  itself, per [`AGENTS.md`][agents]) before the hint string freezes.
  **Preferred answer:** `7.0.0` holds and all naming sites ship with it. **Fallback:** the gate moves all sites
  together — the dev-group specifier, the `_DEBUG_TOOLBAR_INSTALL_HINT`
  string, and the re-typed test literal — the three-places-that-must-agree
  rule, verbatim from [`spec-041`][spec-041].
- **The card's view-detection hedge, resolved against a package fact.** The
  card's architectural posture names a "working name `DjangoGraphQLView`...
  pinned during implementation"; this spec pins the target as engine-owned
  `strawberry.django.views.BaseView` instead, because the package ships no
  view class and fakeshop wires Strawberry's views directly
  ([Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned--resolving-the-cards-djangographqlview-hedge)).
  This is the card's own hedge resolving in the direction its "same
  `issubclass` check" sentence already pointed (upstream's check targets
  `BaseView` too), not a card conflict — recorded per the
  [`docs/SPECS/NEXT.md`][next] prefer-the-card rule: if a future card ships a
  package view class, the one `issubclass` line is that card's to update.
- **`BaseView` presence at the Strawberry floor is upstream history.** Verified
  at the installed strawberry 0.316.0; the Slice-1 gate re-confirms
  importability at the pinned `strawberry-graphql==0.262.0` floor in a
  throwaway venv. **Preferred answer:** present (the class predates the
  package's floor by a wide margin). **Fallback:** bump the project's
  Strawberry floor — the same recourse the [`spec-041`][spec-041] consumer
  gate named.
- **App-registry churn from per-test `INSTALLED_APPS` overrides.** Django's
  test utilities support it and the suite's `--dist loadscope` keeps the
  module on one worker, but registry re-population interacts with anything
  else module-scoped that caches app state. **Preferred answer:** the fixture
  is test-scoped, the suite's existing registry-sensitive files prove the
  pattern, and any surfaced flake is fixed at source (the
  [`tests/conftest.py`][tests-conftest] precedent — never by weakening the
  suite's `-W error` posture). **Fallback:** promote the overrides to a
  module-scoped fixture with an explicit teardown ordering, still inside
  `tests/middleware/`.
- **Schema-registry order-dependence on a shared worker.** Package tests
  `registry.clear()` for isolation; these tests execute real GraphQL from the
  same tree, the documented `LazyType` `KeyError` class
  ([`test_query/README.md`][test-query-readme]). **Preferred answer:** the
  fixture's setup-time `schema_reload.reload_all_project_schemas()` call
  (Decision 9) reconstructs the whole project schema per test — the same
  order-independence-by-reconstruction every live acceptance suite's autouse
  fixture already relies on, via the same single-sited helper (never a
  narrower private reload). **Fallback:** none anticipated; a surfaced flake
  in this class is fixed in the shared helper, at source.
- **The async path ships unverified.** The stock middleware is async-capable
  and the overrides run in hooks it calls from either mode, but no test
  drives `AsyncGraphQLView` or an ASGI stack. **Preferred answer for
  `0.0.14`:** ship sync-verified with the GLOSSARY body claiming exactly that;
  async verification rides whichever card first gives the suite an async
  request vehicle (the [`TestClient`][glossary-testclient] card's
  `AsyncTestClient` is the natural owner). **Fallback:** if the joint cut
  wants the claim earlier, a dedicated async smoke test is a small follow-on,
  not a redesign.

## Out of scope (explicitly tracked elsewhere)

- **Response-extensions debug middleware** (`extensions["debug"]`, graphene
  parity) — [`TODO-ALPHA-044-0.0.14`][kanban]
  ([Response-extensions debug middleware][glossary-response-extensions-debug-middleware]);
  the two entries' "distinct from" cross-links are kept accurate by Slice 2.
- **`TestClient` / `GraphQLTestCase` helpers** — [`TODO-ALPHA-043-0.0.14`][kanban]
  ([`TestClient`][glossary-testclient] / [`GraphQLTestCase`][glossary-graphqltestcase]);
  this card's tests use `django.test.Client` directly. The async verification
  handoff ([Risks](#risks-and-open-questions)) lands there if anywhere.
- **Fakeshop toolbar dogfooding** (a `DEBUG`-gated settings opt-in in the
  example) — the fakeshop-activation card [`TODO-BETA-053-0.1.5`][kanban] if
  the maintainer wants it; when it lands, the covering tests move live and the
  package stand-ins are deleted per the
  [live-first promotion rule][glossary-live-first-coverage-mandate].
- **The migration guide itself** — [`TODO-BETA-056-0.1.6`][kanban]; this card
  hands it the one-row settings-string mapping
  (`strawberry_django.middlewares.debug_toolbar.DebugToolbarMiddleware` →
  `django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware`,
  behavior unchanged) ([Goal 3](#goals)).
- **The `0.0.14` version bump and release-status flips** — the joint `0.0.14`
  cut ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).

## Definition of done

- [ ] `django_strawberry_framework/middleware/debug_toolbar.py` exists, with
      module + symbol docstrings, exposing `DebugToolbarMiddleware`
      (subclassing `debug_toolbar.middleware.DebugToolbarMiddleware`,
      overriding `process_view` + `_postprocess` per
      [Decision 6](#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types))
      behind the import-time `require_debug_toolbar()` guard (a thin wrapper
      over `utils/imports.py::require_optional_module` — Helper-reuse D1).
- [ ] The template asset ships at
      `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
      and the middleware renders it via `render_to_string(...)` into GraphiQL
      HTML responses; the port preserves upstream's five invariants
      ([template-port checklist](#borrowing-posture))
      ([Decision 4](#decision-4--module-template-and-test-locations-a-middleware-subpackage-an-in-package-template-asset-testsmiddleware)).
- [ ] The public wiring documents **all three** toolbar pieces — app,
      middleware (near the front of `MIDDLEWARE`, replacing the stock entry,
      after any response-encoding middleware), **and** `debug_toolbar_urls()`
      in the URLconf — and the toolbar-present tests wire `ROOT_URLCONF =
      "tests.middleware.debug_toolbar_urls"` (composing fakeshop's
      `urlpatterns` + `debug_toolbar_urls()`) **by dotted path only**, the
      module never imported at test-module import time and evicted from
      `sys.modules` on fixture setup and teardown so its `urlpatterns` are
      always computed under `DEBUG=True`
      ([User-facing API](#user-facing-api) / [Decision 9](#decision-9--test-strategy-package-tests-driving-real-in-process-fakeshop-requests-under-settings-overrides-eviction-simulated-absence)).
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
      ([Decision 7](#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned--resolving-the-cards-djangographqlview-hedge)).
- [ ] The introspection-query skip is preserved: no payload injection when
      `operationName == "IntrospectionQuery"`
      ([Decision 8](#decision-8--the-introspection-query-skip-is-preserved-verbatim)).
- [ ] **`django-debug-toolbar>=7.0.0`** (or the floor the Slice-1 gate proves,
      moving all naming sites together) is in `[dependency-groups].dev` with
      `uv.lock` regenerated in the same commit; the dev-group specifier, the
      hint string, and the re-typed test literal agree on the **single** floor
      covering the advertised Django range through 6.0.
- [ ] The Strawberry view-class gate ran: `strawberry.django.views.BaseView`
      confirmed importable at `strawberry-graphql==0.262.0` in an isolated
      throwaway venv (never the shared `.venv`), or the project's Strawberry
      floor was bumped instead; the command and outcome are recorded in the
      build artifact.
- [ ] `tests/middleware/test_debug_toolbar.py` covers both dependency states
      per the [Test plan](#test-plan) — including the real GraphiQL HTML
      injection, the real SQL-emitting **named** JSON operation (each
      product-query test starting with `seed_data(1)`) with the `SQLPanel`
      entry present and
      `TemplatesPanel` absent, the introspection skip, the deterministic
      JSON-`Accept` GET branch, the **panel-content fetch through
      `debug_toolbar_urls()` using the injected `requestId`** (asserting
      `render_panel`'s JSON `content`/`scripts` shape with the fallback
      "isn't available anymore" message **absent** and a SQL-panel marker from
      the seeded operation **present**), the non-GraphiQL passthroughs (HTML **and** the JSON-probe
      leak guard), the two-sided-restore absence
      matrix, the coverage-only targeted units (streaming early-out,
      no-`request_id` bail / `has_content`-false, header-present
      `Content-Length` refreshes), and the template-port guard over the five
      copied-asset invariants — the toolbar-present group marked
      `pytest.mark.django_db`, with the fixture's mandatory
      `show_toolbar_func_or_path.cache_clear()` + `DebugToolbar` cache
      save/clear/restore on setup/teardown — and the package coverage gate
      (`fail_under = 100`) holds with `middleware/debug_toolbar.py` included,
      each branch mapped to a named test owner.
- [ ] The migration-guide handoff row content is recorded for
      [`TODO-BETA-056-0.1.6`][kanban] (the one settings-string swap, behavior
      unchanged) ([Goal 3](#goals)).
- [ ] Slice 2 doc updates land per [Doc updates](#doc-updates): the GLOSSARY
      entry body (status flip deferred), the regenerated
      [`docs/TREE.md`][tree], and the kanban card wrap (DB edit + re-render).
- [ ] **No slice bumps the version** — `pyproject.toml` / `__version__` /
      [`tests/base/test_init.py`][test-base-init] still read `0.0.13` when this
      card flips Done; the joint `0.0.14` cut owns the bump
      ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).
- [ ] `uv run ruff format .` / `ruff check --fix .` clean; no `pytest` beyond
      the slices' own test additions unless the maintainer asks (the
      [`START.md`][start] workflow rule).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[pyproject]: ../pyproject.toml
[pytest-ini]: ../pytest.ini
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary]: GLOSSARY.md
[glossary-auth-mutations]: GLOSSARY.md#auth-mutations
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-debug-toolbar-middleware]: GLOSSARY.md#debug-toolbar-middleware
[glossary-django-appconfig]: GLOSSARY.md#django-appconfig
[glossary-django-trac-37064-hardening]: GLOSSARY.md#django-trac-37064-hardening
[glossary-djangographqlprotocolrouter]: GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-eviction-simulated-absence]: GLOSSARY.md#eviction-simulated-absence
[glossary-fk-id-elision]: GLOSSARY.md#fk-id-elision
[glossary-graphqltestcase]: GLOSSARY.md#graphqltestcase
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: GLOSSARY.md#live-first-coverage-mandate
[glossary-only-projection]: GLOSSARY.md#only-projection
[glossary-pep-562-lazy-export]: GLOSSARY.md#pep-562-lazy-export
[glossary-request-from-info]: GLOSSARY.md#request_from_info
[glossary-require-optional-module]: GLOSSARY.md#require_optional_module
[glossary-response-extensions-debug-middleware]: GLOSSARY.md#response-extensions-debug-middleware
[glossary-schema-reload-discipline]: GLOSSARY.md#schema-reload-discipline
[glossary-seed-data]: GLOSSARY.md#seed_data
[glossary-serializermutation]: GLOSSARY.md#serializermutation
[glossary-single-upstream-parity]: GLOSSARY.md#single-upstream-parity
[glossary-soft-dependency]: GLOSSARY.md#soft-dependency
[glossary-testclient]: GLOSSARY.md#testclient
[glossary-upload-scalar]: GLOSSARY.md#upload-scalar
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-039]: SPECS/spec-039-serializer_mutations-0_0_13.md
[spec-040]: SPECS/spec-040-auth_mutations-0_0_13.md
[spec-041]: SPECS/spec-041-channels_router-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../django_strawberry_framework/conf.py
[init]: ../django_strawberry_framework/__init__.py
[rf-init]: ../django_strawberry_framework/rest_framework/__init__.py
[routers]: ../django_strawberry_framework/routers.py
[utils-imports]: ../django_strawberry_framework/utils/imports.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-soft-dependency]: ../tests/rest_framework/test_soft_dependency.py
[tests-conftest]: ../tests/conftest.py
[test-routers]: ../tests/test_routers.py

<!-- examples/ -->
[config-settings]: ../examples/fakeshop/config/settings.py
[config-urls]: ../examples/fakeshop/config/urls.py
[test-query-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->
[build-kanban-md]: ../scripts/build_kanban_md.py
[build-tree-md]: ../scripts/build_tree_md.py

<!-- .venv/ -->
[venv-strawberry-views]: ../.venv/lib/python3.14/site-packages/strawberry/django/views.py

<!-- External -->
[upstream-middleware]: ../../strawberry-django-main/strawberry_django/middlewares/debug_toolbar.py
[upstream-template]: ../../strawberry-django-main/strawberry_django/templates/strawberry_django/debug_toolbar.html
[debug-toolbar-install-docs]: https://django-debug-toolbar.readthedocs.io/en/latest/installation.html
[debug-toolbar-middleware-source]: https://raw.githubusercontent.com/django-commons/django-debug-toolbar/7.0.0/debug_toolbar/middleware.py
[debug-toolbar-toolbar-source]: https://raw.githubusercontent.com/django-commons/django-debug-toolbar/7.0.0/debug_toolbar/toolbar.py
[debug-toolbar-views-source]: https://raw.githubusercontent.com/django-commons/django-debug-toolbar/7.0.0/debug_toolbar/views.py
[debug-toolbar-pypi]: https://pypi.org/pypi/django-debug-toolbar/json
