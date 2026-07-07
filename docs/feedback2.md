# Critical review — spec-042-debug_toolbar-0_0_14.md (pre-implementation)

Fourth review round (after the three rounds absorbed as Revisions 1–3). Every
load-bearing claim was re-verified against the actual sources before writing
this: the upstream `strawberry_django/middlewares/debug_toolbar.py` and its
template (read byte-for-byte from the local `strawberry-django-main` checkout),
the `django-debug-toolbar` **7.0.0** sources (`middleware.py`, `toolbar.py`,
`views.py`, `settings.py`, `apps.py`, `templates/debug_toolbar/base.html` —
fetched at the 7.0.0 tag), live PyPI metadata, the installed strawberry 0.316.0
views module, and the repo itself (fakeshop settings/urls, `pytest.ini`,
`schema_reload.py`, `tests/test_routers.py`, `utils/imports.py`,
`pyproject.toml`).

**Verdict: the spec is in strong shape — the borrowed mechanism, the
soft-dependency design, the floor argument, and the test architecture all
survive adversarial checking. But do not start production code until the two
P1 findings are fixed: the spec's stated failure mode for a missing
`debug_toolbar_urls()` is factually wrong at the pinned floor, and Test 6 as
specified can pass against the exact failure it exists to catch.** Both are
spec-text fixes, not design changes. Two P2 precision edits and one P3 nit
follow. Everything else I tried to break is listed as verified-correct at the
bottom so the implementer knows what was already grounded.

---

## P1.1 — The missing-URLconf failure mode is wrong: it is a hard `NoReverseMatch` on EVERY toolbar-processed request, not "handle renders, panel clicks fail"

**Where:** User-facing API ("All three pieces are load-bearing: without the
URLconf the injected toolbar renders its handle and the JSON payload carries a
`requestId`, but the toolbar's per-panel content fetches (`render_panel`) have
no route to resolve, so clicking a panel fails"), Test 6's rationale ("Without
it the JSON tests can pass while every panel click 404s because the URLconf
was omitted"), and the Slice-2 GLOSSARY item that will inherit this wording.

**Evidence (7.0.0, verified in the tagged sources):**

1. The stock `_postprocess` renders the toolbar **unconditionally**, for every
   response it processes — HTML and JSON alike:

   ```python
   # debug_toolbar/middleware.py::DebugToolbarMiddleware._postprocess
   # Always render the toolbar for the history panel, even if it is not
   # included in the response.
   rendered = toolbar.render_toolbar()
   ```

2. `render_toolbar()` renders `debug_toolbar/base.html`, and that template
   reverses the djdt namespace at render time:

   ```
   data-render-panel-url="{% url 'djdt:render_panel' %}"
   {% url 'djdt:history_sidebar' as history_url %}
   ```

3. `render_toolbar`'s `except` clause catches only `TemplateSyntaxError` (to
   raise the staticfiles `ImproperlyConfigured`). `NoReverseMatch` is **not**
   caught — it propagates out of the middleware.

So with the middleware listed but `debug_toolbar_urls()` absent, the `djdt`
namespace is unregistered and **the first toolbar-processed request — the
GraphiQL page GET or any tagged JSON POST — dies with `NoReverseMatch`**
(under `DEBUG=True`, the Django error page). Nothing renders a handle; no JSON
payload is produced; no panel click is ever reached. The toolbar itself treats
this as an error setup: `debug_toolbar/apps.py` ships a system check keyed on
exactly `show_toolbar_changed and not toolbar_urls_installed`.

**Why it matters:** the paragraph is the consumer-facing contract, Slice 2
copies it into the GLOSSARY body, and a support question ("I added the
middleware and my whole GraphQL endpoint 500s") would be answered wrongly by
the package's own docs. It also misstates Test 6's value.

**Required edits:**

- Rewrite the User-facing API sentence: all three pieces are load-bearing
  because **omitting the URLconf breaks every toolbar-processed request with
  `NoReverseMatch`** (the stock postprocess renders the toolbar — which
  reverses `djdt:` routes — for every processed response, JSON included), not
  because panel clicks alone would fail.
- Fix Test 6's rationale: the JSON tests could not "pass while panel clicks
  404" — without the URLconf they crash loudly. Test 6's real, still-valid
  value is proving the injected `requestId` is **usable** (the id round-trips
  to stored panel content through the real route), which Tests 3/5 alone do
  not prove. Keep the test; fix the justification.
- Carry the corrected wording into the Slice-2 GLOSSARY checklist item.

---

## P1.2 — Test 6's "non-empty `content`" assertion is satisfied by the failure path

**Where:** Test plan, Test 6 ("assert … a JSON response … whose `content`
value is **non-empty** — stored SQL-panel content, not merely a 200 that
proves a URL exists") and the matching DoD bullet.

**Evidence (7.0.0, `debug_toolbar/views.py::render_panel`):** when
`DebugToolbar.fetch()` finds nothing for the given `request_id`, the view does
**not** 404 or return empty content — it returns **200 JSON with non-empty
`content`**:

> "Data for this panel isn't available anymore. Please reload the page and
> retry."

So a broken store round-trip (wrong id captured, per-test store isolation
eating the record, an id from a different toolbar instance) produces exactly
the response shape Test 6 accepts: 200, JSON, `content`/`scripts` keys,
non-empty `content`. The assertion is not stronger than the "merely a 200" it
claims to improve on.

**Required edit:** pin the success direction, not just the shape. Assert the
fallback message is **absent** and at least one SQL-panel-specific marker is
**present** (the rendered SQL panel content contains the operation's SELECT —
e.g. the products table name from the seeded query). That makes the test fail
when the id fails to resolve, which is its entire reason to exist.

---

## P2.3 — Decision 6 under-describes what `super()._postprocess(...)` does, and the precise description is load-bearing

**Where:** Decision 6 ("the stock method inserts the toolbar handle into HTML
responses and records history — the package must not re-implement or skip
it"), echoed in the targeted-units preamble.

**What the stock method actually does at 7.0.0, in order:** generates stats
and server timing for **every** enabled panel; **renders and stores the
toolbar for every processed response** (the "Always render the toolbar for
the history panel" line — JSON responses included); adds panel headers; and
only then, conditionally, inserts the handle into processable HTML.

**Why the precision matters:** (a) the unconditional render/store is the
mechanism that makes this whole card work — it is why a JSON operation gets a
history row and stored panel content that `render_panel` can later serve;
Test 6 depends on it. (b) It is why P1.1's `NoReverseMatch` fires for JSON
requests too, not just the IDE page. (c) It tells the implementer that every
tagged JSON operation pays a full server-side toolbar render in dev — expected
upstream-parity behavior, but the kind of surprise a spec this thorough should
state. One tightened paragraph in Decision 6 covers all three.

---

## P2.4 — The toolbar's staticfiles prerequisite goes unmentioned while adjacent prerequisites are documented

**Where:** Edge cases ("The consumer must list the package in
`INSTALLED_APPS`" — documents the package's template resolution requirement
and even the `APP_DIRS=False` variant, but not the analogous toolbar-side
requirement).

**Evidence:** `render_toolbar` converts a `TemplateSyntaxError` into
`ImproperlyConfigured` explicitly naming `django.contrib.staticfiles` and
`STATIC_URL`. Because this middleware routes GraphQL traffic through the stock
render on every processed response (P2.3), a consumer without staticfiles hits
that error on their **GraphQL** endpoint, and will plausibly file it against
this package. Fakeshop ships staticfiles + `STATIC_URL` (verified), so the
test plan is unaffected.

**Suggested edit (small):** one edge-case bullet — the toolbar requires
`django.contrib.staticfiles` + `STATIC_URL` (its own documented install
prerequisite); with this middleware the failure surfaces on `/graphql/`
traffic; the GLOSSARY body names the fix alongside the existing
`TemplateDoesNotExist` note.

---

## P3.5 — The template-port checklist hedges about `{% ... %}` tags that do not exist

**Where:** Borrowing posture ("Only the surrounding template comment and, if
needed, the app-namespace path in any `{% ... %}` tag change; the script body
is byte-for-byte upstream's").

**Evidence:** the upstream template was read in full — it is a single
`<script>` IIFE with **no Django template tags at all** (no `{% load %}`, no
`{% static %}`, no `{% url %}`; even the "surrounding template comment" is
absent — the file starts at `<script>`). The only rename in this card is the
`render_to_string(...)` path in the middleware, which is not in the asset.

**Suggested edit:** drop the hedge and say the port is a byte-identical copy
of the file (plus, if desired, one new header comment crediting upstream); all
five Test-16 invariants were verified present in the upstream asset verbatim
(`JSON.parse` wrapper, `Response.prototype.json` wrapper,
`delete data.debugToolbar`, `djDebug.setAttribute("data-request-id", ...)`,
per-panel title/subtitle DOM updates).

---

## Verified correct — checked and survived (do not re-litigate)

- **Upstream module borrowed accurately.** The local
  `strawberry-django-main/strawberry_django/middlewares/debug_toolbar.py` was
  read in full; the spec's description matches line-for-line: `_HTML_TYPES`
  set, `_get_payload` (request-id bail; `force_str` with response charset;
  `object_pairs_hook=OrderedDict`; `reversed(toolbar.enabled_panels)`;
  `TemplatesPanel` skip; `title` only when `has_content`; callable-called
  title/subtitle), `process_view` (`view_class` + `issubclass(view, BaseView)`,
  no `super()` call), `_postprocess` (`super()` first; streaming early-out;
  first-segment content-type sniff; HTML append + `Content-Length` refresh;
  exact `application/json` gate; broad-except `operationName`;
  `IntrospectionQuery` skip; `DjangoJSONEncoder` re-encode + refresh).
- **Stock middleware facts at 7.0.0.** No `process_view` on the stock class;
  `_postprocess(self, request, response, toolbar)` exists with that signature;
  `async_capable = True`; `show_toolbar` checks `settings.DEBUG` first, then
  `REMOTE_ADDR in INTERNAL_IPS`.
- **The cache-hygiene contract is right, and necessary.**
  `show_toolbar_func_or_path` is `@cache`-decorated and **no**
  `setting_changed` receiver clears it (the receiver in
  `debug_toolbar/settings.py` clears only `get_config` / `get_panels`);
  `DebugToolbar._panel_classes` / `_urlpatterns` are receiver-untouched class
  caches. The fixture's mandatory `cache_clear()` + save/clear/restore is
  exactly correct — a stale resolved callback would otherwise outlive the
  per-test `DEBUG_TOOLBAR_CONFIG` override.
- **`debug_toolbar_urls()` is `DEBUG`-gated** and returns `[]` when `DEBUG` is
  false — the fixture's import-ordering/eviction contract for the test URLconf
  is justified.
- **`render_panel` responds JSON with `content` / `scripts` keys** off
  `request_id` / `panel_id` query params (with the P1.2 fallback caveat).
- **The floor argument holds against live PyPI.** Latest is 7.0.0 (uploaded
  2026-06-19), `requires-python >=3.10`, `django>=5.2`, classifiers
  `Django :: 5.2` + `Django :: 6.0`; `6.0.0` is 2025-07-25 as the spec says.
  `>=7.0.0` as the single floor for the advertised range is correct, and
  upstream's `>=6.0.0` is correctly not copied.
- **`strawberry.django.views.BaseView` exists** in the installed 0.316.0 with
  `GraphQLView` / `AsyncGraphQLView` subclassing it; fakeshop wires
  `ensure_csrf_cookie(GraphQLView.as_view(..., graphql_ide="graphiql"))` at
  `graphql/` (so Test 3 exercises detection through the real decorator), and
  `/login/` is Django's `LoginView` (Test 7's class-based negative exists).
- **Test 5's mechanism is sound.** Strawberry renders the IDE only when the
  `Accept` header contains `text/html` or `*/*` (verified in
  `strawberry/http/base.py`); `HTTP_ACCEPT="application/json"` deterministically
  selects the JSON branch, and `json.loads(b"")` raising → inject matches the
  documented GET edge case.
- **Repo-state claims are all true post-spec-041.** `require_optional_module`
  is landed in `utils/imports.py` (routers.py rides it); `tests/test_routers.py`
  exists with the import-blocker scoped to absolute top-level names (the
  scoping this spec's absence fixture copies); `tests/__init__.py` exists, so
  the dotted `ROOT_URLCONF = "tests.middleware.debug_toolbar_urls"` is
  importable under pytest's rootdir insertion;
  `schema_reload.reload_all_project_schemas()` exists, reloads `config.urls`,
  and clears URL caches; `pytest.ini` matches every quoted property
  (`pythonpath = examples/fakeshop`, `--dist loadscope`, `-W error`-equivalent
  `filterwarnings = error`, no `django_debug_mode`); fakeshop's checked-in
  `DEBUG = True` + pytest-django's forced `False` is as described;
  `pyproject.toml`'s hatchling wheel packages the package directory wholesale
  (the template ships with no build-config change);
  `apps.products.services.seed_data` exists.
- **Decision 5's guard-shape reasoning is sound** (import-time guard in a
  dedicated opt-in leaf; the `middleware/__init__.py` stays clean for
  walkers), and the degraded-install posture (raw `ImportError` from a
  class-body submodule import, no second wrap) is consistent with the
  single-package boundary — unlike the router's two-package builder.
