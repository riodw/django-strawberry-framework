# Build: Slice 1 — S1: the protocol split (Django owns HTTP)

Spec reference: `docs/spec-046-transport_security-0_0_15.md` — Slice 1 checklist lines 112-133;
Decision 2 (lines 593-645), Decision 3 (647-689), Decision 4 (691-722), Decision 5 (724-762),
Decision 6 (764-815), Decision 13 (1078-1123); User-facing API lines 430-576; Helper-reuse
obligations lines 1211-1247; Edge cases lines 1249-1305; Test plan S1 rows 1-12 (lines 1311-1337).
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Utils inventory checked.** `docs/shadow/utils-inventory.md` was refreshed this pass (237
  lines, generated from `django_strawberry_framework/utils/` by the `worker-1.md` AST script).
  Relevant candidates: `utils/imports.py::require_optional_module` — the package's single
  optional-import owner, reached by `routers.py::require_channels`; it stays exactly as it is and
  is deliberately **not** used by the new `views.py` (see duplication risk 2). `utils/typing.py::is_async_callable`
  was reviewed and rejected: the constructor guard needs plain `callable()`, not
  coroutine-ness. No utility exists for "a configuration value must be callable" and none is
  justified — the package's established idiom is a local `callable()` test raising
  `ConfigurationError` (two precedents cited below). **No new `utils/` module or helper.**

- **Static inspection run (BUILD.md obligation).** `uv run python scripts/review_inspect.py
  django_strawberry_framework/routers.py --output-dir docs/shadow` →
  `docs/shadow/django_strawberry_framework__routers.stripped.py` +
  `docs/shadow/django_strawberry_framework__routers.overview.md`. Quick scan: 10 imports, 5
  symbols, **1 control-flow hotspot** (`_build_router_class`, 84 lines / 5 branch nodes), 0
  Django/ORM markers, 0 calls of interest, 0 TODOs, 1 repeated literal
  (`DjangoGraphQLProtocolRouter`, 2x — the two present-but-broken hint strings; not a DRY defect,
  they are two distinct actionable messages). Slice 1 *shrinks* that hotspot (one route list, one
  branch removed, one guard added). Shadow line numbers are not canonical; every citation below is
  symbol-qualified. `django_strawberry_framework/views.py` is new in this slice and is a
  pure-subclass module, so Worker 1 does not owe the helper on it; per BUILD.md "Worker 3 must
  run the helper when the slice adds a new `.py` file … unless it is a pure-class-definition
  module", Worker 3 records either the run or the skip-with-reason. No other existing package file
  gains logic in this slice, so no further inspection run is owed.

- **Existing patterns reused.**
  - `strawberry.django.views.GraphQLView` / `AsyncGraphQLView` are **subclassed, not
    reimplemented** (Decision 6 / Helper-reuse #"The view subclasses upstream"). Verified by
    reading the installed source in full:
    `.venv/lib/python3.14/site-packages/strawberry/django/views.py` (242 lines). See "Upstream
    verification" below for the exact base classes, kwargs, and override points.
  - `django_strawberry_framework/exceptions.py::ConfigurationError` — the package's single typed
    configuration failure (Helper-reuse #"The construction-time failure is `ConfigurationError`").
    `routers.py` does **not** import it today; step 3 adds the import.
  - The callable-validation-plus-`ConfigurationError` idiom, copied in shape from
    `django_strawberry_framework/list_field.py` #"resolver must be callable." and
    `django_strawberry_framework/rest_framework/serializer_converter.py::register_serializer_field_converter`
    #"must be a callable(field) -> SerializerFieldConversion".
  - `routers.py::require_channels`, `routers.py::_build_router_class`'s guard-then-import
    ordering, the `_ROUTER_CLASS` module-global cache, the `_CHANNELS_INSTALL_HINT` /
    `_CHANNELS_BROKEN_HINT` / `_STRAWBERRY_CHANNELS_BROKEN_HINT` triple, and the PEP 562
    `routers.py::__getattr__` — all untouched in mechanism (Helper-reuse #"The soft-`channels`
    guard is unchanged").
  - `tests/test_routers.py`'s existing helpers: `unwrap_origin_validator`, `unwrap_auth_stack`,
    `_route_patterns`, `_graphql_post`, `_ws_graphql_data`, `_router_class`, `_CHANNELS_PREFIXES`,
    and the `tests/_soft_dependency.py::simulated_absence` / `::evicted_modules` two-sided
    eviction discipline. No new eviction machinery.
  - Live tier: `examples/fakeshop/graphql_client.py::post_graphql` / `::graphql_payload` /
    `::assert_graphql_data`, `apps.products.services::seed_data` / `::create_users` (AGENTS.md
    rule 7 — first line of every catalog/auth test), the autouse reload fixtures in
    `examples/fakeshop/test_query/conftest.py`, and the **Probe URLconf** pattern from
    `examples/fakeshop/test_query/test_client_api.py` (a module-level `urlpatterns` plus
    `@override_settings(ROOT_URLCONF=__name__)`, with the probe view resolving its target at
    *request* time so it tracks the per-test schema rebuild). No new live harness or fixture
    module (Helper-reuse #"uses the existing Probe URLconf pattern rather than a new harness").

- **New helpers justified.**
  - `django_strawberry_framework/views.py` — **one** new module. Single responsibility: *the
    package's Django GraphQL HTTP endpoint classes*. In this slice it holds exactly two thin
    subclasses with no overridden behavior. It exists now, empty of logic, because (a) the
    migration note and the documented `urlpatterns` entry need one canonical symbol (Decision 6
    reason b), (b) it is the seam Slice 2's body cap attaches to and the seam the later cards'
    transport bounds (audit S3 / S4 / S10) reuse (Decision 6 reason d), and (c) mounting it in
    fakeshop makes every S2 row live-earnable (Decision 6 reason c). Authorized by Decision 6.
  - **One** test-module-local construction seam in `tests/test_routers.py`: a stub ASGI
    application plus a `_router(...)` builder that supplies the now-required `django_application=`.
    Single responsibility: satisfy the new required parameter in exactly one place so every
    preserved test's *assertions* stay byte-identical. Without it, eight call sites each grow the
    same keyword — the single largest duplication this slice risks.
  - **Nothing else.** No new constant beyond the one `ConfigurationError` message, no new
    exception type, no new settings key (`MAX_REQUEST_BODY_BYTES` is Slice 2), no new soft-dep
    guard, no second lazy-export mechanism.

- **Duplication risk avoided.**
  1. **Re-implementing Django's HTTP boundary inside the router** (the audit's own rejected
     conditional). Avoided structurally: the `"http"` value *is* the supplied application object,
     so there is nothing to keep in sync with Django's security releases (Decision 2).
  2. **A second soft-dependency guard for `views.py`.** `views.py` imports only
     `strawberry.django.views`, whose own imports are `json`, `asgiref.sync`, `cross_web`,
     `django.*`, and `strawberry.*` — verified by reading the installed module top-to-bottom;
     **no `channels` anywhere**. So `views.py` needs no `require_*` guard, no PEP 562 lazy export,
     and must **never** import `routers.py` or `channels`. This is the asymmetry the spec's Error
     shapes require the package to hold and the docs to name.
  3. **Pre-building the Slice 2 body cap.** Slice 1 adds **no** cap logic, **no**
     `max_request_body_bytes` class attribute, **no** `conf.py` key, and **no** `dispatch`
     override. The seam is named by a `TODO(spec-046 Slice 2)` anchor on each view class (exact
     content in step 1) and removed by Slice 2.
  4. **Eight copies of `django_application=`** across `tests/test_routers.py` → the single
     `_router(...)` helper.
  5. **A parallel live-tier harness.** Reuse `graphql_client.py` and the existing Probe URLconf
     shape; add no fixture module and no second reload discipline.
  6. **A blanket swap of the three existing live probe views** that build upstream's view directly
     — `examples/fakeshop/test_query/test_optimizer_auto_api.py` #"GraphQLView.as_view(schema=schema)(request)",
     `test_multi_db.py` #"GraphQLView.as_view(schema=schema)(request)", and
     `test_debug_extension_api.py` #"GraphQLView.as_view(schema=schema)(request)". These are
     **deliberately left on upstream's view**: their subject is the optimizer / multi-DB routing /
     debug extension, upstream's view remains a fully supported mount, and swapping them would be
     scope creep that muddies this slice's diff. Recorded here so Worker 3 reads the asymmetry as
     intentional rather than as drift.
  7. **Duplicating the transport-boundary proofs across tiers.** Each S1 row lands in exactly one
     tier: request-shaped proofs live (fakeshop), composition/absence proofs package-tier
     (`tests/`). Nothing is asserted twice.

### Upstream verification (read, not remembered)

Read in full: `.venv/lib/python3.14/site-packages/strawberry/django/views.py`. Supporting reads:
`.venv/lib/python3.14/site-packages/strawberry/http/base.py` (whole file),
`.venv/lib/python3.14/site-packages/strawberry/http/sync_base_view.py` +
`async_base_view.py` (seam grep), `.venv/lib/python3.14/site-packages/django/views/generic/base.py`
(`View.as_view`). Findings the plan depends on:

- **Exact base classes.** `strawberry.django.views.GraphQLView(BaseView, SyncBaseHTTPView[...], django.views.generic.View)`
  and `strawberry.django.views.AsyncGraphQLView(BaseView, AsyncBaseHTTPView[...], View)`. Both are
  exported by that module's `__all__ = ["AsyncGraphQLView", "GraphQLView"]`. **This matches spec
  Decision 6 exactly** — no contradiction found.
- **Exact `as_view` kwargs.** `View.as_view(**initkwargs)` raises `TypeError("… received an
  invalid keyword … as_view only accepts arguments that are already attributes of the class")`
  for any key that is not already a class attribute, then instantiates `cls(**initkwargs)`.
  The bindable keys are therefore: `schema` (class attr on both views),
  `graphql_ide` (class attr, default `"graphiql"`), `allow_queries_via_get` (class attr, default
  `True`), and `multipart_uploads_enabled` (class attr on `strawberry.http.base.BaseView`, default
  `False`). `strawberry.django.views.BaseView.__init__(schema, graphql_ide, allow_queries_via_get,
  multipart_uploads_enabled, **kwargs)` consumes the four and forwards the rest to Django's
  `View.__init__`, which `setattr`s them. **Consequence Slice 2 must respect:**
  `max_request_body_bytes` will only bind through `as_view(...)` if `DjangoGraphQLView` declares
  it as a **class attribute**. Named in the Slice-2 anchor; not built here.
- **Exact override points available for the Slice-2 cap.** `GraphQLView.dispatch(self, request,
  *args, **kwargs)` wraps `self.run(request=request)` in `try/except HTTPException` and turns the
  exception into `HttpResponse(content=e.reason, status=e.status_code, content_type="text/plain")`.
  `AsyncGraphQLView.dispatch` is the `async def` twin with identical translation. So raising
  `cross_web.HTTPException(413, reason)` from a pre-`run` check inside `dispatch` yields exactly
  the spec's "`413` with a `text/plain` reason, before `parse_json` and before schema execution"
  with **zero** new response machinery. That is the seam; Slice 2 owns it.
- **The parse seam Slice 3 patches is elsewhere and unaffected:**
  `strawberry.http.base.BaseView.parse_json` — inherited by *both* views, which is why Decision 9's
  single-siting claim holds.
- **The async twin needs no `as_view` work from us.** `AsyncGraphQLView.as_view` is a
  `classonlymethod` that calls `super().as_view(**initkwargs)` then `markcoroutinefunction(view)`;
  a subclass inherits that unchanged (Django's `View.view_is_async` would otherwise report `False`
  because neither view defines `get`/`post` handlers).

### Implementation steps

Line numbers below are pin-at-write-time navigational hints; verify against current source before
editing.

1. **`django_strawberry_framework/views.py` (NEW).**
   - Module docstring is **mandatory** — `scripts/build_tree_md.py` fails its render on a missing
     module docstring, and Slice 5 regenerates `docs/TREE.md`. It must state: the package's Django
     GraphQL HTTP endpoint, declared in the consumer's URLconf; that it is `channels`-free so a
     WSGI-only project can adopt it without the soft dependency; and cite `spec-046` Decision 6.
     Do **not** use staging language ("planned", "Slice N") in the docstring prose — that would
     render into `TREE.md` as unbuilt (BUILD.md documentation-sanity rule). The Slice-2 anchor
     below is a `#` comment, not docstring prose.
   - `from __future__ import annotations`, then
     `from strawberry.django.views import AsyncGraphQLView, GraphQLView`. No other import. In
     particular: no `channels`, no `.routers`, no `require_*` guard.
   - `class DjangoGraphQLView(GraphQLView):` — docstring naming the inherited surface (every
     upstream `as_view()` kwarg still applies: `schema`, `graphql_ide`, `allow_queries_via_get`,
     `multipart_uploads_enabled`) and stating that the class overrides nothing today. Body is the
     docstring plus the anchor comment.
   - `class AsyncDjangoGraphQLView(AsyncGraphQLView):` — the async twin, identical surface;
     docstring notes it is the shape an ASGI deployment generally wants and that the migration
     note's default stays the sync view (spec Risks #"Async view adoption").
   - `__all__ = ("AsyncDjangoGraphQLView", "DjangoGraphQLView")` — module-level, alphabetical,
     tuple form matching `routers.py::__all__`.
   - The staging anchor, one per class, verbatim intent (wording is Worker 2's):
     `# TODO(spec-046 Slice 2): the cumulative request-body cap overrides ``dispatch`` here
     (Decision 7). It needs a ``max_request_body_bytes`` CLASS attribute -- Django's
     ``View.as_view`` rejects any kwarg that is not already a class attribute.`
     **No `NotImplementedError`**: no call path must fail loudly, because the view is fully
     functional without the cap. (Spec Implementation plan #"paired with `NotImplementedError`
     where a call path must fail loudly" — this is not such a path.)
   - **No edit to `django_strawberry_framework/__init__.py`.** Authorized verbatim by Decision 6:
     "It is a leaf-module import — `from django_strawberry_framework.views import
     DjangoGraphQLView` — never a package-root export, matching the established posture for every
     integration surface (`routers.py`, `middleware/debug_toolbar.py`, `extensions/`)." Confirmed
     against the current root surface: `django_strawberry_framework/__init__.py::__all__` holds 32
     names and contains neither `routers` nor `DjangoGraphQLProtocolRouter`. Worker 3's
     public-surface check should therefore show `git diff -- django_strawberry_framework/__init__.py`
     empty for this slice.

2. **`django_strawberry_framework/routers.py` — drop the HTTP consumer.**
   - `routers.py::_build_router_class` #"from strawberry.channels import GraphQLHTTPConsumer, GraphQLWSConsumer"
     → `from strawberry.channels import GraphQLWSConsumer`. Decision 2 requires the import to
     leave the module in the same change; Test plan row 9 asserts it.
   - `routers.py` #"_STRAWBERRY_CHANNELS_BROKEN_HINT" — the parenthetical
     `(GraphQLHTTPConsumer / GraphQLWSConsumer)` becomes `(GraphQLWSConsumer)`. This is a
     truthfulness edit to an existing string, **not** a new hint string: the triple and its owners
     are unchanged (Helper-reuse #"No new guard, no new hint string"). Assertion-safe —
     `tests/test_routers.py::test_degraded_partial_install_raises_the_split_actionable_errors`
     asserts only the re-typed floor substrings `channels>=4.3.2` and
     `strawberry-graphql>=0.262.0`.
   - `URLRouter`, `AuthMiddlewareStack`, `AllowedHostsOriginValidator`, `ProtocolTypeRouter`, and
     `django.urls.re_path` imports all **stay** — the WebSocket branch still needs every one.

3. **`routers.py::DjangoGraphQLProtocolRouter.__init__` — the new signature and body.**
   - Signature (matching the spec's `## The constructor` block exactly):
     `def __init__(self, schema: BaseSchema, django_application: ASGIHandler, *, websocket_url_pattern: str = r"^graphql/?$") -> None:`
     - `django_application` is positional-or-keyword and **required** — omission raises Python's
       own `TypeError` naming the parameter (Decision 3 / Error shapes; Test plan row 10). The
       `| None` leaves the annotation.
     - `websocket_url_pattern` is **keyword-only** (after `*`) with default `r"^graphql/?$"`
       (Decision 4). There is no `url_pattern=` alias.
     - Do **not** add `websocket_consumer_class=` or `websocket_revalidation_window=` — Slice 4
       (Decision 11). No anchor is owed at this site either: the spec's staging rule anchors
       *staged-but-unbuilt* work, and Slice 4's own checklist already names `routers.py`; adding a
       parameter-shaped TODO here would have to be removed two slices later for no gain. Worker 2
       may add one only if it records the reason.
   - Body, in order:
     ```
     if django_application is None or not callable(django_application):
         raise ConfigurationError(_MISSING_DJANGO_APPLICATION_HINT)
     super().__init__(
         {
             "http": django_application,
             "websocket": AllowedHostsOriginValidator(
                 AuthMiddlewareStack(
                     URLRouter(
                         [re_path(websocket_url_pattern, GraphQLWSConsumer.as_asgi(schema=schema))],
                     ),
                 ),
             ),
         },
     )
     ```
     One guard covers explicit-`None` and non-callable because Error shapes gives them one
     message. The `"http"` value is the raw object — no wrapper, no `URLRouter`, no `re_path`, no
     `AuthMiddlewareStack` (Decision 2; Edge case #"The router's `\"http\"` value is now an opaque
     callable").
   - Add the message as a module-level constant beside the existing hint constants (proposed name
     `_MISSING_DJANGO_APPLICATION_HINT`). Per Error shapes it must name, in prose: (a) that a
     `0.0.14` deployment which passed `None` or omitted the argument was serving GraphQL HTTP
     outside Django's middleware — no `ALLOWED_HOSTS` check, no CSRF, no security headers; (b) that
     the mode is **removed**, not flagged; (c) the repair — `django.core.asgi.get_asgi_application()`
     passed as `django_application`, **plus** the `urlpatterns` entry
     `django_strawberry_framework.views.DjangoGraphQLView.as_view(schema=schema)`. ASCII only; each
     physical line <= 100 columns.
   - Add `from .exceptions import ConfigurationError` at module top (a real runtime import;
     `routers.py` has none today). It is `channels`-free, so
     `tests/test_routers.py::test_routers_module_import_succeeds_without_channels` stays green.

4. **`routers.py` docstrings — reconcile both to the shipped truth.**
   - Module docstring: the current text ("GraphQL on HTTP + WebSocket in one import", "exactly the
     upstream `strawberry_django.routers.AuthGraphQLProtocolTypeRouter` composition", "`AuthMiddlewareStack`
     (sessions + `scope[\"user\"]` on both)") is now false. Rewrite: the WebSocket branch is the
     package's Channels composition; HTTP is the consumer's Django ASGI application, dispatched
     directly, so it traverses the project's real `MIDDLEWARE`; the GraphQL HTTP endpoint is
     `views.py::DjangoGraphQLView` in the consumer's URLconf. Cite `spec-046` Decisions 2 / 3 / 4
     alongside the surviving `spec-041` Decisions 3 and 5.
   - Class docstring: replace the example block with the spec's own two-file shape (`## The
     consumer's asgi.py` and `## The consumer's URLconf`, lines 432-468) — required
     `django_application=`, plus the `path("graphql/", DjangoGraphQLView.as_view(schema=schema))`
     line. State that `websocket_url_pattern` governs the WebSocket branch **only**, is exact at
     both ends by default (so `/graphql` and `/graphql/` match and `/graphql-admin`,
     `/graphqlanything`, `/graphql/extra` do not), and that HTTP path matching belongs entirely to
     Django's URLconf — the two declarations are independent by design (spec Risks
     #"`websocket_url_pattern`'s default keeps a WS path that HTTP no longer serves"). Delete every
     "byte-compatible with upstream" and "non-GraphQL HTTP paths fall through to
     `django_application`" sentence.
   - **AGENTS.md rule 27 sweep:** no symbol is renamed in this slice (`DjangoGraphQLProtocolRouter`,
     `_build_router_class`, `require_channels`, `__getattr__` all keep their names), so no
     `::OldName` grep sweep is owed. `url_pattern` is a *parameter*, not a symbol; its stale prose
     in `docs/GLOSSARY.md`, `README.md`, `TODAY.md`, and `docs/SPECS/spec-041-*.md` is **Slice 5's**
     work (spec `## Doc updates`, lines 1383-1419). **Worker 2 must not touch any `.md` in this
     slice.**

5. **`examples/fakeshop/config/urls.py` — mount the package view.**
   - `from strawberry.django.views import GraphQLView` → `from django_strawberry_framework.views
     import DjangoGraphQLView`; `GraphQLView.as_view(...)` → `DjangoGraphQLView.as_view(...)`.
     Keep `ensure_csrf_cookie`, `graphql_ide="graphiql"`, `multipart_uploads_enabled=True`, and the
     entire existing explanatory comment block **verbatim**; append one sentence naming `spec-046`
     Decision 6 as the reason the mount is the package view.
   - **Why this belongs to Slice 1** (the spec's Slice-1 checklist does not name this file, so the
     reasoning is recorded rather than assumed): the slice's own live-tier bullet requires the S1
     proofs to execute "on the GraphQL HTTP route"; Decision 6 reason (c) pins every S2 regression
     row as earnable "over fakeshop's real `/graphql/`"; `AGENTS.md` rule 9 plus the live-first
     coverage mandate make the example project the proof of the documented shape; and without the
     swap the live tier would prove *upstream's* view while `views.py` carried no live coverage at
     all. See the planning-pass reconciliation note below.
   - Blast radius checked: `examples/fakeshop/tests/test_urls.py` asserts only index-page content
     (no view identity), and `examples/fakeshop/schema_reload.py` #"_reload_or_import(\"config.urls\")"
     already reloads `config.urls`, so the per-test shell rebuild picks the new mount up with no
     fixture change. `examples/fakeshop/config/wsgi.py` is untouched.
   - **No `examples/fakeshop/config/asgi.py` is added.** Decided explicitly: spec Non-goals
     #"A fakeshop `asgi.py` / live Channels tier. Fakeshop stays WSGI-only.", spec Risks
     #"Fakeshop still has no `asgi.py`, so the router half stays package-tier-only … keep the
     documented genuinely-unreachable-live exemption for the router, as `spec-041` Decision 8
     established", and Out of scope #"A fakeshop ASGI surface and live Channels acceptance tier."
     `docs/SPECS/spec-041-channels_router-0_0_14.md` Decision 8 is the standing exemption and is
     re-verified as still accurate: no `routers.py` line is reachable from a WSGI-only fakeshop.
     Worker 2 must not create one.

6. **`tests/test_routers.py` — the construction seam, the rewrites, and the transport moves.**
   - **Construction seam** (add next to `_router_class`): a module-level recording stub ASGI
     application (appends `scope["path"]`, sends `http.response.start` `418` + a body) and a
     `_router(schema=SCHEMA, **kwargs)` builder that supplies `django_application=` from the stub
     unless the caller overrides it. Contract is fixed (one place supplies the required argument);
     spelling is Worker 2's.
   - **Preserved tests — construction line only, assertions byte-identical.** Switch
     `_router_class()(SCHEMA)` → `_router()` in: `test_router_is_a_protocol_type_router_mapping_exactly_http_and_websocket`,
     `test_websocket_branch_wraps_origin_validator_outside_the_auth_stack` (its trailing
     `not isinstance(..., OriginValidator)` assertion on the HTTP value still holds — a bare
     callable is not an `OriginValidator`), `test_websocket_handshake_origin_directions`, and
     `test_request_contract_resolves_over_the_websocket_branch`.
     `test_repeated_access_returns_the_cached_class_which_is_subclassable` and the whole
     eviction / degraded-install block (`test_root_package_and_star_import_stay_channels_free`
     through `test_degraded_partial_install_raises_the_split_actionable_errors`) construct no
     router and stay **byte-identical**.
   - **Rewrite A** — `test_http_branch_is_auth_wrapped_and_routes_only_graphql_without_fallback`
     → rename to the new contract (e.g. `test_http_branch_is_the_supplied_django_application_by_identity`):
     `router.application_mapping["http"] is <the stub>`, and it is **not** a `CookieMiddleware`,
     `URLRouter`, or `OriginValidator`. Identity, not structural equality (Test plan row 8; Edge
     case #"asserts object identity with the supplied application").
   - **Rewrite B** — `test_django_application_fallback_is_appended_after_the_graphql_route`
     → the construction-failure matrix (Test plan row 10): `_router_class()(SCHEMA)` raises
     `TypeError` matching `django_application`; `django_application=None` and a non-callable (e.g.
     `object()`) each raise `ConfigurationError`. The message assertions **re-type** substrings
     (never import `_MISSING_DJANGO_APPLICATION_HINT` — the existing `_HINT_SUBSTRING` discipline
     in this file's own comment: "importing the router constants and asserting them against
     themselves could never catch the hint drifting"). Assert the message names
     `get_asgi_application` and `DjangoGraphQLView`.
   - **Rewrite C** — `test_custom_url_pattern_reaches_the_re_path_on_both_branches` → WebSocket-only
     (Test plan row 11): a custom `websocket_url_pattern=` appears on the WS `URLRouter` via the
     existing `_route_patterns` helper **and** the `"http"` value is still the identical stub
     object; plus a parametrized exact-match matrix over the **default** pattern driving
     `WebsocketCommunicator` — `/graphql` and `/graphql/` connect; `/graphql-admin`,
     `/graphqlanything`, `/graphql/extra` do not. Reuse Test 9's
     `headers=[(b"origin", b"http://testserver")]` + `subprotocols=["graphql-transport-ws"]` shape
     and its `django_db` marker rationale. **Implementation note for Worker 2:** a non-matching WS
     path raises `ValueError("No route found")` out of `URLRouter`; follow the existing
     `send_input` + `communicator.wait(timeout=10)` + `pytest.raises(ValueError, match="No route
     found")` idiom already in this file rather than sitting out `connect()`'s timeout.
   - **Merge D** — `test_http_communicator_graphql_round_trip` **and**
     `test_non_graphql_path_reaches_the_fallback_only_when_provided` → **one** test (e.g.
     `test_http_branch_delegates_every_path_to_the_supplied_application`): drive `HttpCommunicator`
     at `/graphql` **and** at `/admin/login/`, assert the stub recorded both paths and returned its
     own `418` both times — proving no package route intercepts either, which is the whole point of
     Decision 2 (Decision 13 #"Become one test that the HTTP branch delegates to the supplied
     application unchanged"). Reuse `_graphql_post` for the `/graphql` leg.
   - **Transport move E** — `test_schema_object_passes_through_unchanged_with_extensions_intact`
     must be **re-aimed at the WebSocket branch**, both halves: the structural half keeps only
     `ws_router.routes[0].callback.consumer_initkwargs["schema"] is recording_schema` (the HTTP
     consumer no longer exists to interrogate), and the execution half runs
     `_ws_graphql_data(router, "{ ping }")` instead of `_graphql_data(...)`, then asserts
     `fired == ["operation"]`. Its *subject* — the schema object passes through untouched with
     extensions intact (Test plan row 12) — is fully preserved; only the transport it is proven on
     changes. If the WS single-result flow records a different number of `on_operation` firings,
     Worker 2 adjusts the expectation and records the reason in `### Implementation notes`; it must
     not weaken the assertion to a membership test without that note.
   - **Transport move F** — `test_authenticated_session_round_trip_reaches_the_resolver` must move
     to the WebSocket branch for the same reason (its cookie previously traversed the HTTP
     branch's `AuthMiddlewareStack`, which no longer exists). Keep the
     `database_sync_to_async` user + session-cookie construction and the `{ username }` resolver
     **unchanged**; drive it through `_ws_graphql_data`, extended with an optional `cookie=`
     parameter that appends `(b"cookie", cookie.encode())` to the existing header list. That is a
     one-parameter extension of an existing helper, not a new helper. The contract the spec's DoD
     names — "a real session cookie flows through `AuthMiddlewareStack` to the actor" — is
     preserved.
   - **Deletion G** — `test_request_contract_resolves_through_the_router_for_anonymous_reads`
     (the HTTP colour of the request-adapter contract) is **deleted**, together with the now-orphan
     `whoami` field on the module-local `Query`. Authorized by Decision 2: "the
     [Channels request adapter] is now a WebSocket-only shape". Its surviving colour is
     `test_request_contract_resolves_over_the_websocket_branch` (kept, preserved).
     - **Coverage check Worker 2 must perform, not assume:** the lines that test uniquely touched
       live in `django_strawberry_framework/utils/permissions.py` —
       `::ChannelsRequestAdapter.__getattr__` (the delegated read) and `::_channels_scope`'s first
       branch (the `consumer.scope` HTTP duck shape). Both are **already** covered independently by
       `tests/utils/test_permissions.py` (its `ChannelsRequest` duck-shape fake, the
       `adapter.consumer is wrapped.consumer` delegation assertion, and the non-mapping
       `consumer.scope` fall-through). Confirm that by reading those tests before deleting, and if
       any line would drop, keep the coverage at the package tier rather than reinstating a
       transport that no longer exists.
   - **Orphan sweep** (AGENTS.md rule 13): after E / F / G, `_graphql_data` has no remaining
     callers — delete it. `_graphql_post` survives as the `HttpCommunicator` builder for Merge D
     (simplify its `cookie=` parameter away if unused). Re-grep the file for any other unreferenced
     helper.
   - **Module docstring** of `tests/test_routers.py` must be reconciled: it currently advertises
     "real execution through Channels' in-process communicators", "the package-realistic request
     contract … (Test 16)", and "the authenticated-session round trip (Test 18)" as HTTP-branch
     facts. Restate: `HttpCommunicator` now proves *delegation* to the supplied Django application;
     the request contract and the authenticated round trip are proven over the WebSocket branch.

7. **`tests/test_views.py` (NEW) — only what a live request cannot reach.**
   Decision 13's Placement reserves this file for "what a live request cannot reach"; the cap's
   argument validation and settings-precedence matrix are Slice 2's rows. Slice 1's rows are the
   import-boundary and public-surface contracts, which no live request can express:
   - A module-local ORM-free `strawberry.Schema` (mirror `tests/test_routers.py`'s `Query.ping`
     shape). No `DjangoType`, no registry mutation, no `django_db`.
   - `test_views_module_imports_with_channels_absent` — the Decision 6 / Error-shapes asymmetry.
     Use `tests/_soft_dependency.py::simulated_absence("channels", "strawberry.channels", "daphne",
     "django_strawberry_framework.views", parent=django_strawberry_framework, attr="views")` (the
     sentinel name heads the prefix list inside the helper, so do not repeat `"channels"` in
     `prefixes`), then `importlib.import_module("django_strawberry_framework.views")` succeeds and
     both symbols resolve. Assertion shape: no `ImportError`, both classes are classes, and
     `sys.modules["channels"] is None` inside the block (so the test proves absence rather than
     coincidence).
   - `test_every_upstream_as_view_kwarg_still_binds_on_the_package_views` — parametrized over both
     classes: `as_view(schema=SCHEMA, graphql_ide=None, allow_queries_via_get=False,
     multipart_uploads_enabled=True)` returns a callable whose `view_class` is the package class
     and whose `view_initkwargs` round-trips all four. Pins Decision 6 #"Every upstream kwarg …
     keeps working, unchanged".
   - `test_an_unknown_as_view_kwarg_is_rejected_by_djangos_class_attribute_guard` — a deliberately
     bogus kwarg (e.g. `not_a_view_kwarg=1`) raises `TypeError` matching `invalid keyword`.
     Chosen bogus so **Slice 2 never has to edit this test**; the docstring records the
     consequence Slice 2 depends on (a cap kwarg needs a class attribute).
   - `test_async_view_as_view_is_marked_as_a_coroutine_function` — `asgiref.sync.iscoroutinefunction`
     is `True` for `AsyncDjangoGraphQLView.as_view(schema=SCHEMA)` and `False` for
     `DjangoGraphQLView.as_view(schema=SCHEMA)`. The async-twin contract, pinned package-tier so it
     does not depend on the live async probe surviving.
   - `test_module_exports_exactly_the_two_view_classes_and_stays_off_the_package_root` —
     `views.__all__ == ("AsyncDjangoGraphQLView", "DjangoGraphQLView")`; neither name nor `"views"`
     appears in `django_strawberry_framework.__all__`. This is the assertion Worker 3's
     public-surface check reads against Decision 6.

8. **`examples/fakeshop/test_query/test_transport_api.py` (NEW) — the live S1 tier.**
   New file (proposed name; see discretion item 4) rather than an addition to
   `test_products_api.py`, so Slice 3's inverted encoding tests and this slice's transport proofs
   never collide on one file. Module docstring: the S1 HTTP-boundary acceptance tier — every proof
   that Django's real request lifecycle executes on the package's GraphQL HTTP route now that
   `routers.py` no longer serves HTTP; cite `spec-046` Slice 1 / Decision 2 / Decision 6 and Test
   plan rows 1-7. First line of every DB-touching test is `seed_data(N)` or `create_users(N)`
   (AGENTS.md rule 7).
   Module-level scaffolding:
   - A recording project middleware (`__init__(self, get_response)` + `__call__`) that appends the
     request path to a module list and stamps a sentinel response header. Referenced from
     `MIDDLEWARE` by its dotted path `"<module __name__>._SentinelMiddleware"` — importable
     because pytest has already put the module in `sys.modules` under that name, the same
     mechanism `test_client_api.py` relies on for `ROOT_URLCONF=__name__`.
   - A Probe URLconf: `urlpatterns = [path("", include("config.urls")), path("ide-off/",
     _ide_off_view), path("async-graphql/", _async_graphql_view)]`, inert unless a test sets
     `@override_settings(ROOT_URLCONF=__name__)`. Both probe views import `config.schema` and build
     `as_view(...)` **at request time**, mirroring `test_client_api.py::_alt_graphql_view`'s
     resolve-at-request-time rationale so the probe tracks the per-test schema rebuild.
     `_async_graphql_view` is an `async def` that awaits
     `AsyncDjangoGraphQLView.as_view(schema=schema)(request, ...)`.
   Rows (numbers are the spec's Test plan S1 rows):
   - **Row 1 — project middleware executes.** Inside
     `override_settings(MIDDLEWARE=[*settings.MIDDLEWARE, "<module>._SentinelMiddleware"])`,
     construct a **new** `Client()` *inside* the override block (Django caches the middleware chain
     on the handler at its first request), POST a real query → `200`, the recorded path list
     contains `/graphql/`, and the sentinel response header is present. Asserting the *path* is
     what makes this a proof about the GraphQL route rather than about any route.
   - **Row 2 — security headers.** A plain POST carries `X-Content-Type-Options: nosniff` and a
     `Referrer-Policy` header (both are `SecurityMiddleware` defaults under fakeshop's settings);
     then under `override_settings(SECURE_HSTS_SECONDS=3600)` a `secure=True` POST carries
     `Strict-Transport-Security` with `max-age=3600`. The `secure=True` is load-bearing —
     `SecurityMiddleware` emits HSTS only when `request.is_secure()`.
   - **Row 3 — hostile `Host` rejected.** Under `override_settings(ALLOWED_HOSTS=["testserver"])`
     (explicit, so the test never depends on fakeshop's `DEBUG` — spec Edge case
     #"`ALLOWED_HOSTS = []` with `DEBUG=True`"), POST with `HTTP_HOST="evil.example"` → `400`, and
     the response body is **not** a GraphQL envelope (no `"data"` key) — the load-bearing half,
     proving Django's host boundary ran before schema execution.
   - **Row 4 — CSRF on cookie-authenticated mutations.** `create_users(1)`, then
     `Client(enforce_csrf_checks=True)` + `force_login`. Three directions (parametrized or three
     tests — discretion): missing `X-CSRFToken` → rejected (`403`); a wrong token → rejected
     (`403`); the correct token, read from `client.cookies["csrftoken"]` after a prior
     `client.get("/graphql/")` (fakeshop's `ensure_csrf_cookie` sets it) → `200` with a real
     payload. Drive a real write mutation already exercised by a sibling live suite.
   - **Row 5 — authenticated GET varies on `Cookie`.** `create_users(1)` + `force_login`, then
     `client.get("/graphql/", {"query": "{ me { username } }"})` → `200`, the payload names the
     logged-in user, and `"Cookie" in response.headers.get("Vary", "")`. Deterministic:
     `ensure_csrf_cookie` forces `CsrfViewMiddleware._set_csrf_cookie`, which calls
     `patch_vary_headers(response, ("Cookie",))`; `SessionMiddleware` patches it as well on session
     access. `{ me { username } }` is the shipped auth-surface field
     (`examples/fakeshop/apps/accounts/schema.py::Query.me`, already driven live by
     `test_auth_api.py`).
   - **Row 6 — routing policy is Django's.** `/graphql/` POST → `200`; `/graphql` POST → `301`
     whose `Location` is `/graphql/` (`CommonMiddleware`'s `APPEND_SLASH`, the documented policy
     Slice 5 must warn about because most clients will not re-`POST` a `301`); `/graphql-admin` and
     `/graphqlanything` → `404` **and** no GraphQL envelope in the body, proving those paths reach
     the rest of the URLconf rather than the GraphQL view. **Worker 2 caution:** under `DEBUG=True`
     `CommonMiddleware` raises `RuntimeError` for a POST `APPEND_SLASH` redirect instead of
     returning `301`; pytest-django runs the suite at `DEBUG=False`, so `301` is the ambient
     expectation — do not add a `DEBUG=True` override to this row.
   - **Row 7 — `graphql_ide=None` and `allow_queries_via_get=False` are supported on the package
     view.** Under `@override_settings(ROOT_URLCONF=__name__)`: `GET /ide-off/` with
     `Accept: text/html` does **not** return the GraphiQL page (no `text/html` GraphiQL body), and
     `GET /ide-off/?query={...}` is rejected rather than executed; contrast with
     `GET /graphql/` + `Accept: text/html` on the default mount, which **does** return the IDE page
     (`200`, `text/html`). Pin status codes, `Content-Type`, and the absence of an HTML body — do
     **not** pin upstream's exact reason strings, which are upstream's to change.
   - **Async twin probe.** `django.test.AsyncClient` POST `{ __typename }` to `/async-graphql/`
     under the same Probe URLconf → `200`, `data == {"__typename": "Query"}`, and a
     `SecurityMiddleware` header present (Django's middleware chain ran on the async path). The
     query is deliberately **DB-free** so the async view never touches the ORM from the event loop
     (`SynchronousOnlyOperation`). **Fallback, if and only if the async probe proves
     environment-hostile:** do not delete the coverage — the package-tier
     `iscoroutinefunction` assertion in step 7 remains, and Worker 2 records the reason under
     `### Notes for Worker 1 (spec reconciliation)`.

9. **Hygiene, in this order.** `uv run ruff format .`; `uv run ruff check --fix .`;
   `uv run python scripts/check_trailing_commas.py <explicit paths only>` — **never** repo-wide,
   which defaults to auto-fix and would rewrite the maintainer's untracked `drys.md` / `vulns.md`
   (spec Edge cases; build-plan baseline-dirty list). ASCII-only in every `.py`. Then
   `git status --short` and classify every modified file per BUILD.md's Validation-run rule.
   The baseline-dirty files (`django_strawberry_framework/filters/sets.py`,
   `tests/filters/test_sets.py`, `docs/feedback.md`, `docs/feedback2.md`, `drys.md`, `vulns.md`,
   `docs/row-preserving-predicates-part1-plan.md`, `docs/GLOSSARY.md`, `KANBAN.md`,
   `KANBAN.html`, `examples/fakeshop/db.sqlite3`) are out of scope: do not edit, do not revert.

### Test additions / updates

Package tier — `tests/test_views.py` (NEW; no `django_db`):

- `::test_views_module_imports_with_channels_absent` — under
  `simulated_absence("channels", "strawberry.channels", "daphne",
  "django_strawberry_framework.views", parent=django_strawberry_framework, attr="views")`:
  `importlib.import_module(...)` raises nothing, both classes resolve, and
  `sys.modules["channels"] is None` inside the block.
- `::test_every_upstream_as_view_kwarg_still_binds_on_the_package_views` — parametrized over both
  classes; `view.view_class is <class>` and `view.view_initkwargs` round-trips
  `schema` / `graphql_ide=None` / `allow_queries_via_get=False` / `multipart_uploads_enabled=True`.
- `::test_an_unknown_as_view_kwarg_is_rejected_by_djangos_class_attribute_guard` —
  `pytest.raises(TypeError, match="invalid keyword")`.
- `::test_async_view_as_view_is_marked_as_a_coroutine_function` — `iscoroutinefunction` True for the
  async view's `as_view()` result, False for the sync one.
- `::test_module_exports_exactly_the_two_view_classes_and_stays_off_the_package_root` — the exact
  `__all__` tuple; neither symbol nor `"views"` in `django_strawberry_framework.__all__`.

Package tier — `tests/test_routers.py` (rewrites and moves; Test plan rows 8-12):

- Rewritten: HTTP-value identity (row 8); the `TypeError` / `ConfigurationError` construction
  matrix with re-typed message substrings naming `get_asgi_application` and `DjangoGraphQLView`
  (row 10); `websocket_url_pattern` reaching only the WS `re_path` plus the parametrized
  exact-match connect/reject matrix over `/graphql`, `/graphql/`, `/graphql-admin`,
  `/graphqlanything`, `/graphql/extra` (row 11).
- New (merged from two): the HTTP branch delegates **every** path — `/graphql` and
  `/admin/login/` — to the supplied application, which records both and answers `418`.
- Row 9 (`GraphQLHTTPConsumer` is neither imported nor referenced anywhere in `routers.py`) is
  proven by a source-text assertion over `Path(routers_module.__file__).read_text()`: the file
  contains no `GraphQLHTTPConsumer` occurrence. Reading the file (rather than probing
  `dir(routers_module)`) is what makes it a real absence proof — an unimported name would not
  appear in `dir()` either way. `docs/shadow/` must **not** be the read target.
- Re-aimed to WebSocket, subject preserved: the schema-passthrough / extensions-intact test
  (row 12) and the authenticated-session round trip.
- Deleted: the HTTP colour of the request-adapter contract, plus the orphan `whoami` field and the
  orphan `_graphql_data` helper.
- Untouched, byte-identical: the origin-direction matrix, the origin-validator nesting test, the WS
  request-contract test, the cached-class test, and the entire eviction-simulated absence /
  degraded-install block.

Live tier — `examples/fakeshop/test_query/test_transport_api.py` (NEW; Test plan rows 1-7 plus the
async probe): the eight rows enumerated in step 8, with the assertion shapes given there. Every
DB-touching row opens with `seed_data(N)` / `create_users(N)`; posts go through
`examples/fakeshop/graphql_client.py` except where the subject *is* the raw envelope or a custom
client (`Client(enforce_csrf_checks=True)`, a `Host` header, `secure=True`, `AsyncClient`), which
is the documented raw-`django.test.Client` exemption in
`examples/fakeshop/test_query/README.md` #"Only tests whose subject is the raw request envelope".

Temp/scratch tests: none planned. Worker 3 may put throwaway probes under
`docs/builder/temp-tests/slice-1/` if it wants to re-derive the `APPEND_SLASH` `301` or the
`Vary: Cookie` header independently; both are cheap to confirm and worth confirming rather than
trusting this plan's reading of Django.

Do **not** run `pytest` with any `--cov*` flag. Worker 2's focused scope should be
`uv run pytest tests/test_routers.py tests/test_views.py examples/fakeshop/test_query/test_transport_api.py --no-cov`,
plus `uv run pytest examples/fakeshop/tests/ --no-cov` because step 5 edits `config/urls.py`.
The full sweep is Worker 1's final gate.

### Implementation discretion items

Assessed and delegated — each is a spelling or arrangement choice between equally correct shapes:

1. The exact name of the module-level `ConfigurationError` message constant in `routers.py`
   (`_MISSING_DJANGO_APPLICATION_HINT` proposed) and its precise wording, provided it names all
   three facts Error shapes requires.
2. The exact names and shapes of the `tests/test_routers.py` construction seam (the stub
   application and the `_router(...)` builder) — module-level function vs. small factory, and
   whether the stub records into a module list or a per-test list. Contract fixed: one place
   supplies `django_application=`.
3. Which existing live write mutation the Row-4 CSRF matrix drives, and whether the three CSRF
   directions are one parametrized test or three named ones.
4. The new live file's name (`test_transport_api.py` proposed) and the order of its rows within the
   file.
5. Whether the WebSocket exact-match matrix is one parametrized test or two (connect-set /
   reject-set), and whether Rewrite C's custom-pattern assertion rides in the same test.
6. The renamed test-function names for Rewrites A / B / C and Merge D (the proposals above are
   suggestions), and all docstring wording — which must be accurate but is otherwise free.
7. Whether `views.py`'s two Slice-2 anchors are one shared comment above both classes or one per
   class.

**Not discretion — fixed by the spec, do not vary:** the constructor's parameter order and the
keyword-only boundary; `django_application` being required (omission = `TypeError`) with explicit
`None`/non-callable = `ConfigurationError`; the `"http"` value being the raw supplied object with no
wrapper; `websocket_url_pattern`'s default `r"^graphql/?$"`; `GraphQLHTTPConsumer` leaving the
module entirely; `views.py` carrying **no** cap, **no** `max_request_body_bytes` attribute, and
**no** `dispatch` override in this slice; no `django_strawberry_framework/__init__.py` edit; no
`conf.py` key; no `examples/fakeshop/config/asgi.py`; no `.md` edits; no version-quintet or
`CHANGELOG.md` movement.

### Planning-pass spec-reconciliation notes (Worker 1)

Recorded, not acted on — the spec is **not** edited during a planning pass. Worker 1's
final-verification pass decides whether any of these warrants a spec edit.

1. **Decision 13's "Preserved verbatim" list is not literally achievable, for two separable
   reasons.** (a) *Mechanically:* eight preserved tests construct the router as
   `_router_class()(SCHEMA)`, which Decision 3 makes a `TypeError`. Their construction line must
   gain the now-required argument; the plan routes all eight through one `_router()` helper so every
   **assertion** stays byte-identical, which is the reading that preserves the decision's intent.
   (b) *Substantively:* two of the named "preserved" tests are **HTTP-branch** tests that the split
   removes the transport for — `::test_schema_object_passes_through_unchanged_with_extensions_intact`
   interrogates `http_router.routes[0].callback.consumer_initkwargs` and executes a GraphQL POST
   through `HttpCommunicator`, and `::test_authenticated_session_round_trip_reaches_the_resolver`
   sends its session cookie through the HTTP branch's `AuthMiddlewareStack`. Neither survives
   unmodified. The plan re-aims both at the WebSocket branch, preserving their subjects (schema
   passthrough with extensions intact; a real session cookie reaching the actor) on the transport
   that still has the machinery. **Candidate spec edit** at final verification: Decision 13 should
   move these two from "Preserved verbatim" to a third category ("re-aimed to the WebSocket
   branch, subject preserved").
2. **A sixth existing test is unlisted by Decision 13 and must be deleted.**
   `tests/test_routers.py::test_request_contract_resolves_through_the_router_for_anonymous_reads`
   is the HTTP colour of the Channels request-adapter contract. It appears in neither the
   "Rewritten" nor the "Preserved" list. Decision 2 authorizes the deletion outright — "the
   Channels request adapter is now a WebSocket-only shape" — and its WebSocket colour
   (`::test_request_contract_resolves_over_the_websocket_branch`) is preserved. The plan deletes it
   plus the orphan `whoami` resolver, with a required coverage check against
   `tests/utils/test_permissions.py`.
3. **The Slice-1 checklist says "the three HTTP-branch tests"; Decision 13 names five** (three
   rewritten plus two merged into one). The checklist bullet cites Decision 13, so Decision 13
   governs; the plan implements five. Cosmetic count mismatch only.
4. **`examples/fakeshop/config/urls.py` is not named in the Slice-1 checklist** but the slice cannot
   deliver its own live-tier bullet without it (see step 5's justification). Recorded as an
   inference from Decision 6 reason (c), the live-first coverage mandate, and AGENTS.md rule 9,
   not as an invented requirement.
5. **The spec's Implementation-plan sequencing sentence assumes Slice 2's body-cap tests land in
   `test_products_api.py`** ("its inverted live tests share `test_products_api.py` with Slice 2's
   new body-cap tests"). This plan puts the S1 transport proofs in a new
   `test_transport_api.py` instead, and recommends Slice 2's cap matrix join it. The sequencing
   *conclusion* — land Slice 3 after Slice 2 — is unaffected either way, since Slice 3's inverted
   encoding tests genuinely live in `test_products_api.py` today.
6. **Spec status line re-verified** (`docs/spec-046-transport_security-0_0_15.md` lines 37-43):
   "Status: **PLANNED — no slice built yet.**" is accurate at the start of this planning pass. It
   will need Worker 1's edit once Slice 1 is `final-accepted`.

### Spec slice checklist (verbatim)

Copied byte-for-byte from `docs/spec-046-transport_security-0_0_15.md` lines 113-133 (the six
sub-bullets of the Slice 1 block), preserving text, nesting, em-dashes, and inline citations. The
reference-style `[glossary-configurationerror]` link is verbatim from the spec and intentionally
has no definition in this scratchpad artifact.

  - [x] `django_strawberry_framework/routers.py`: the HTTP branch becomes the
        consumer-supplied Django ASGI application **directly** — no `URLRouter`, no
        `GraphQLHTTPConsumer`, no `AuthMiddlewareStack` on HTTP
        ([Decision 2](#decision-2--http-dispatches-directly-to-a-required-consumer-supplied-django-asgi-application)).
  - [x] `django_application` becomes a **required** constructor parameter; `None` or a
        non-callable raises [`ConfigurationError`][glossary-configurationerror] naming the
        migration
        ([Decision 3](#decision-3--django_application-is-required-omission-fails-at-construction-with-no-compatibility-fallback)).
  - [x] `url_pattern` is renamed and narrowed to `websocket_url_pattern`, default
        `r"^graphql/?$"` (exact, both-ends anchored)
        ([Decision 4](#decision-4--url_pattern-becomes-websocket_url_pattern-with-exact-matching-as-the-secure-default)).
  - [x] New `django_strawberry_framework/views.py`: `DjangoGraphQLView` /
        `AsyncDjangoGraphQLView`, the package's Django GraphQL view, declared in the
        consumer's URLconf
        ([Decision 6](#decision-6--the-graphql-http-endpoint-is-a-package-owned-django-view-in-the-consumers-urlconf)).
  - [x] `tests/test_routers.py`: the three HTTP-branch tests are rewritten to the new
        contract; every WebSocket Origin / auth test is preserved verbatim
        ([Decision 13](#decision-13--test-strategy-which-existing-tests-change-and-why)).
  - [x] `tests/test_views.py` + a live `examples/fakeshop/test_query/` tier proving
        Django middleware, `ALLOWED_HOSTS`, CSRF, security headers, cache policy, and
        exact routing execute on the GraphQL HTTP route.

---

## Build report (Worker 2)

### Files touched

Slice-intended, from `git status --short` (not memory):

- `django_strawberry_framework/views.py` (**NEW**) — the package's Django GraphQL HTTP
  endpoint. Module docstring (mandatory for `build_tree_md.py`; no staging language),
  `from __future__ import annotations`, one import (`strawberry.django.views`), module-level
  `__all__ = ("AsyncDjangoGraphQLView", "DjangoGraphQLView")`, one shared
  `TODO(spec-046 Slice 2)` anchor comment, and two thin subclasses that override nothing.
  No `channels`, no `.routers`, no `require_*` guard, no cap, no `max_request_body_bytes`,
  no `dispatch` override.
- `django_strawberry_framework/routers.py` — Decision 2/3/4 landed: `GraphQLHTTPConsumer`
  dropped from the `strawberry.channels` import; `from .exceptions import ConfigurationError`
  added (a real runtime import, still channels-free); new module-level
  `_MISSING_DJANGO_APPLICATION_HINT`; `_STRAWBERRY_CHANNELS_BROKEN_HINT`'s parenthetical
  narrowed to `(GraphQLWSConsumer)`; new constructor signature
  `(self, schema, django_application, *, websocket_url_pattern=r"^graphql/?$")` with the
  callable guard and the `{"http": django_application, "websocket": ...}` mapping; module and
  class docstrings rewritten to the shipped truth (both previously asserted upstream
  byte-compatibility, `AuthMiddlewareStack` on both branches, and an HTTP fallthrough that no
  longer exist).
- `examples/fakeshop/config/urls.py` — the `/graphql/` mount swapped from
  `strawberry.django.views.GraphQLView` to `django_strawberry_framework.views.DjangoGraphQLView`.
  `ensure_csrf_cookie`, `graphql_ide="graphiql"`, `multipart_uploads_enabled=True`, and the whole
  existing comment block kept verbatim; one paragraph appended naming Decision 6 as the reason.
  (`ruff check --fix` also re-sorted the import block, folding `django_strawberry_framework`
  and `config` into one first-party group — tool-authoritative, kept.)
- `tests/test_routers.py` — the construction seam, the three rewrites, the merge, the two
  transport moves, the deletion, and the orphan sweep (details below).
- `tests/test_views.py` (**NEW**) — the five package-tier rows.
- `examples/fakeshop/test_query/test_transport_api.py` (**NEW**) — the live S1 tier.
- `tests/auth/test_mutations.py` — **not named by the plan**; required by the slice's own
  breaking change. See `### Notes for Worker 1` item 6 and `### Implementation notes`.

Baseline-dirty, untouched and not reverted (build plan's out-of-scope list):
`django_strawberry_framework/filters/sets.py`, `tests/filters/test_sets.py`, `docs/feedback.md`,
`docs/row-preserving-predicates-part1-plan.md`, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`,
`examples/fakeshop/db.sqlite3`, `drys.md`, `vulns.md`, the spec + terms CSV, the build plan.
No `.md` outside this artifact was edited; no version quintet, no `CHANGELOG.md`, no
`django_strawberry_framework/__init__.py`, no `conf.py`, no `examples/fakeshop/config/asgi.py`.

### Tests added or updated

`tests/test_views.py` (NEW, no `django_db`):

- `::test_views_module_imports_with_channels_absent` — pins the Decision 6 / Error-shapes
  asymmetry: under `simulated_absence("channels", "strawberry.channels", "daphne",
  "django_strawberry_framework.views", parent=..., attr="views")` the module imports and both
  classes resolve, with `sys.modules["channels"] is None` asserted INSIDE the block so it is a
  proof about absence rather than a coincidence.
- `::test_every_upstream_as_view_kwarg_still_binds_on_the_package_views[sync|async]` — pins
  "every upstream kwarg keeps working, unchanged": `view.view_class` identity plus a
  `view_initkwargs` round trip of all four keywords.
- `::test_an_unknown_as_view_kwarg_is_rejected_by_djangos_class_attribute_guard[sync|async]` —
  pins that Django's class-attribute guard is the gate (`TypeError` / `invalid keyword`), which
  is the constraint the Slice-2 cap keyword must satisfy.
- `::test_async_view_as_view_is_marked_as_a_coroutine_function` — `iscoroutinefunction` True for
  the async view's `as_view()` result, False for the sync one.
- `::test_module_exports_exactly_the_two_view_classes_and_stays_off_the_package_root` — the exact
  `__all__` tuple; neither class nor `"views"` on `django_strawberry_framework.__all__` (the
  assertion Worker 3's public-surface check reads).

`tests/test_routers.py` (rewrites / moves / deletion; Test-plan rows 8-12):

- Added `_RecordingDjangoApplication` + `_router(schema=SCHEMA, **kwargs)` — the ONE place that
  supplies `django_application=`. Every preserved test's construction line became `_router()`
  and its assertions stayed byte-identical.
- `::test_http_branch_is_the_supplied_django_application_by_identity` (row 8; rewrite of
  `::test_http_branch_is_auth_wrapped_and_routes_only_graphql_without_fallback`) — object
  identity on `application_mapping["http"]`, plus `not isinstance(..., (CookieMiddleware,
  URLRouter, OriginValidator))`.
- `::test_construction_rejects_an_omitted_or_unusable_django_application` (row 10; rewrite of
  `::test_django_application_fallback_is_appended_after_the_graphql_route`) — omission raises
  `TypeError` matching `django_application`; `None` and `object()` each raise
  `ConfigurationError` whose message names `ALLOWED_HOSTS`, `get_asgi_application`, and
  `DjangoGraphQLView`. Substrings are RE-TYPED, never imported.
- `::test_graphql_http_consumer_left_the_router_module_entirely` (row 9, NEW) — reads
  `Path(routers_module.__file__).read_text()` and asserts no `GraphQLHTTPConsumer` occurrence.
  Source text, not `dir()`, is what makes it an absence proof.
- `::test_custom_websocket_url_pattern_reaches_only_the_websocket_re_path` (row 11 structural;
  rewrite of `::test_custom_url_pattern_reaches_the_re_path_on_both_branches`) — the custom
  pattern is on the WS `URLRouter` only, and the HTTP value is still the identical stub.
- `::test_default_websocket_url_pattern_matches_exactly[bare|trailing-slash|suffix-extension|prefix-extension|path-extension]`
  (row 11 behavioral, NEW) — `/graphql` and `/graphql/` connect; `/graphql-admin`,
  `/graphqlanything`, `/graphql/extra` raise `ValueError("No route found")` via the existing
  `send_input` + `wait(timeout=10)` idiom.
- `::test_http_branch_delegates_every_path_to_the_supplied_application` (merge of
  `::test_http_communicator_graphql_round_trip` + `::test_non_graphql_path_reaches_the_fallback_only_when_provided`)
  — a GraphQL POST at `/graphql` AND a GET at `/admin/login/` both reach the stub, which records
  both paths and answers `418` both times.
- `::test_schema_object_passes_through_unchanged_with_extensions_intact` (row 12) — subject
  preserved, transport moved to WebSocket: structural half reads the WS consumer's
  `consumer_initkwargs["schema"]`, execution half runs `_ws_graphql_data`. `fired ==
  ["operation"]` held unchanged on the WS single-result flow (no expectation weakened).
- `::test_authenticated_session_round_trip_reaches_the_resolver` — subject preserved, transport
  moved to WebSocket; the `database_sync_to_async` user + session-cookie construction and the
  `{ username }` resolver are unchanged, and the cookie now rides `_ws_graphql_data(..., cookie=)`.
- DELETED `::test_request_contract_resolves_through_the_router_for_anonymous_reads` plus the
  now-orphan `Query.whoami` field and the orphan `_graphql_data` helper; `_graphql_post` lost its
  unused `path=` / `cookie=` parameters. `::test_request_contract_resolves_over_the_websocket_branch`
  is the surviving colour (renumbered Test 16b -> Test 16).
- Byte-identical apart from the construction line: the origin-direction matrix, the
  origin-validator nesting test, the WS request-contract test, the cached-class test, and the
  entire eviction / degraded-install block (Tests 11-15, 17 keep their numbers).
- Module docstring reconciled: `HttpCommunicator` now proves delegation; the request contract,
  the schema pass-through, and the authenticated round trip are WebSocket facts.

`examples/fakeshop/test_query/test_transport_api.py` (NEW, live):

- `::test_project_middleware_executes_on_the_graphql_http_route` (row 1) — a dotted-path
  `_SentinelMiddleware` records `/graphql/` (the recorded PATH is the load-bearing half) and
  stamps a response header; the `Client` is built inside the override block.
- `::test_security_middleware_headers_ride_the_graphql_response` (row 2) —
  `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`, and under
  `SECURE_HSTS_SECONDS=3600` a `secure=True` POST carries `max-age=3600`.
- `::test_a_hostile_host_header_is_rejected_before_the_schema_runs` (row 3) — under explicit
  `ALLOWED_HOSTS=["testserver"]`, `HTTP_HOST="evil.example"` yields `400` with no `"data"` in
  the body.
- `::test_csrf_is_enforced_on_a_cookie_authenticated_graphql_mutation[missing-token|wrong-token|correct-token]`
  (row 4) — `Client(enforce_csrf_checks=True)` + `force_login`; missing/wrong -> `403` with no
  envelope and no row written, correct (token read off the `ensure_csrf_cookie` GET) -> `200`
  with the row present.
- `::test_an_authenticated_get_varies_on_cookie` (row 5) — authenticated `GET
  ?query={ me { username } }` -> `200`, payload names the logged-in user, `Vary` contains
  `Cookie`.
- `::test_routing_policy_is_djangos_urlconf_not_the_routers` (row 6) — `/graphql/` `200`;
  `/graphql` `301` to `/graphql/`; `/graphql-admin` and `/graphqlanything` `404` with no
  envelope. No `DEBUG` override (see the environment trap below).
- `::test_graphql_ide_and_get_queries_can_be_turned_off_on_the_package_view` (row 7) — Probe
  URLconf: `/ide-off/` HTML GET -> `404` `text/plain` with no HTML body; `/ide-off/?query=` ->
  `400` with no envelope; a POST to `/ide-off/` still `200`; the default `/graphql/` HTML GET
  still serves the IDE (`200`, `text/html`).
- `::test_the_async_package_view_runs_inside_djangos_middleware_chain` — `AsyncClient` POST of a
  DB-free `{ __typename }` to the async probe -> `200`, correct data, and `nosniff` present.
- `::test_the_package_view_serves_an_ordinary_graphql_response` — the shared
  `graphql_client.py` helpers against the swapped mount, so the `config/urls.py` change itself
  has a transport-named guard.

### Validation run

1. `uv run ruff format .` — **pass** (`400 files left unchanged` on the final run).
2. `uv run ruff check --fix .` — **pass** (`All checks passed!`; one earlier auto-fix, the
   `config/urls.py` import re-sort, is kept and recorded above).
3. `uv run python scripts/check_trailing_commas.py <explicit paths>` — **pass**. Explicit paths
   only, never repo-wide: `django_strawberry_framework/views.py`,
   `django_strawberry_framework/routers.py`, `examples/fakeshop/config/urls.py`,
   `examples/fakeshop/test_query/test_transport_api.py`, `tests/test_routers.py`,
   `tests/test_views.py`, `tests/auth/test_mutations.py`. First run reformatted 2 files
   (`tests/test_routers.py`, `tests/test_views.py` — sub-threshold collapses); the follow-up
   `--check` over the same paths exits 0.
4. `git status --short` after both ruff invocations — every entry classified. Slice-intended:
   `django_strawberry_framework/routers.py`, `examples/fakeshop/config/urls.py`,
   `tests/auth/test_mutations.py`, `tests/test_routers.py`, and the three new untracked files
   (`django_strawberry_framework/views.py`, `tests/test_views.py`,
   `examples/fakeshop/test_query/test_transport_api.py`) plus this artifact. Everything else
   (`KANBAN.html`, `KANBAN.md`, `django_strawberry_framework/filters/sets.py`,
   `docs/GLOSSARY.md`, `docs/feedback.md`, `docs/row-preserving-predicates-part1-plan.md`,
   `examples/fakeshop/db.sqlite3`, `tests/filters/test_sets.py`, `drys.md`, `vulns.md`, the
   spec + terms CSV, the build plan) is on the baseline-dirty list: left exactly as found,
   never `git checkout --`ed. **No unrelated tool churn was produced, so nothing was reverted.**
   ASCII-only verified on every touched `.py`; no new line exceeds 100 columns.
5. Focused tests (no `--cov*`; `--no-cov` only):
   - `uv run pytest tests/test_routers.py tests/test_views.py examples/fakeshop/test_query/test_transport_api.py --no-cov -q` — **44 passed**.
   - `uv run pytest tests/test_routers.py --no-cov -q -n0` — **26 passed**.
   - `uv run pytest tests/test_views.py --no-cov -q -n0` — **7 passed**.
   - `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov -q -n0` — **11 passed**.
   - `uv run pytest tests/auth/ --no-cov -q` — **125 passed** (the sibling suite the constructor
     break reached; see Notes for Worker 1 item 6).
   - `uv run pytest tests/ --no-cov -q` — **4033 passed, 38 skipped**.
   - `uv run pytest examples/fakeshop/tests/ --no-cov -q` — **17 passed** (the tier that owns
     `config/urls.py`).
   - `uv run pytest examples/fakeshop/test_query/ --no-cov -q` — **510 passed, 1 skipped,
     1 FAILED** (`test_kanban_api.py::test_select_board_docs_and_lookup_roots_for_static_dashboard`).
   - `uv run pytest tests/ examples/fakeshop/tests/ --no-cov -q` — **4045 passed, 38 skipped,
     5 FAILED** (four `examples/fakeshop/tests/test_export_schema.py` rows and
     `test_urls.py::test_index_view_renders_dev_links`).
   - **`uv run pytest --no-cov -q` (the canonical full sweep, all four `testpaths`) — 4800
     passed, 40 skipped, ZERO failures.** Both failure sets above are **subset-invocation
     artifacts**, not regressions — see the verification immediately below. Nothing was hidden,
     weakened, or skipped to reach that number.

#### Pre-existing / invocation-shape claim verification

Not a `git stash` (concurrent writers are active in this tree — `START.md` "Concurrent
sessions"); verified by swapping in HEAD's copy of the only file of mine on those request paths.

```shell
# 1. The canonical invocation is green, so neither failure set blocks the final gate:
uv run pytest --no-cov -q
#   -> 4800 passed, 40 skipped in 61.51s

# 2. Both failure sets reproduce IDENTICALLY with HEAD's config/urls.py (the upstream
#    GraphQLView mount, so neither views.py nor routers.py is on the request path at all):
git show HEAD:examples/fakeshop/config/urls.py > <scratchpad>/urls_head.py
cp examples/fakeshop/config/urls.py <scratchpad>/urls_mine.py
cp <scratchpad>/urls_head.py examples/fakeshop/config/urls.py
uv run pytest "examples/fakeshop/test_query/test_kanban_api.py::test_select_board_docs_and_lookup_roots_for_static_dashboard" --no-cov -q -n0
#   -> 1 failed          (same as with my copy)
uv run pytest tests/ examples/fakeshop/tests/ --no-cov -q
#   -> 5 failed, 4045 passed, 38 skipped   (the same five, same names)
cp <scratchpad>/urls_mine.py examples/fakeshop/config/urls.py   # restored; git diff --stat confirms 7/2

# 3. Mechanism of the kanban one, via a throwaway probe under docs/builder/temp-tests/slice-1/
#    (deleted after): allKanbanSections returns 5 rows -- scope, test_plan, decision,
#    open_question, note -- where the test expects only the one `scope` row _seed_board() makes.
grep -rn "open_question" examples/fakeshop/apps/kanban/migrations/*.py
#   -> 0015_seed_reclassification_sections.py seeds the four extra Section lookups
git log --oneline -3 -- examples/fakeshop/apps/kanban/migrations/
#   -> c6a6ecfe / 4f68d3f2 / 0c08204f  (all COMMITTED)
git status --short examples/fakeshop/apps/kanban examples/fakeshop/test_query/test_kanban_api.py
#   -> empty: both the migration and the test are unmodified at HEAD
```

Reading: a committed kanban data migration seeds four extra `Section` lookup rows, and the
committed live test expects only its own. It nonetheless PASSES under the canonical
`-n auto --dist loadscope` full sweep and FAILS under `-n0` or a single-directory run, so the
test's greenness depends on the worker/DB distribution the full invocation happens to produce
(a `transaction=True` neighbour flushing the migration-seeded lookup table on that worker). The
same shape explains the five `examples/fakeshop/tests/` failures, which appear only when
`examples/fakeshop/test_query/` and `examples/fakeshop/apps/` are excluded from the run.

None of it is in this build's diff, none of the involved files is dirty, and all of it reproduces
with this slice's production code entirely out of the request path. It is a **pre-existing
order/distribution fragility** in committed example-project tests, flagged (not fixed) in
`### Notes for Worker 1` item 7 — fixing it would mean editing committed tests outside this
slice's contract, and it does not block the gate.

**Consequence for Worker 3:** verify with the canonical `uv run pytest --no-cov`, per BUILD.md
"Example-project schema changes must sync every schema-module list" — a narrowed invocation
surfaces these pre-existing artifacts and will read as a false regression.

### Implementation notes

- **The `None` arm of the constructor guard is folded into `callable()`.** The plan's body sketch
  read `if django_application is None or not callable(django_application):`; `callable(None)` is
  already `False`, so the first operand can never change the outcome. Implemented as
  `if not callable(django_application):` with a comment recording that this is the arm the
  explicit-`None` migrant lands on. Both Error-shapes cases still get the one prose message, and
  both are asserted. Recorded as drift in `### Notes for Worker 1` item 1.
- **One shared Slice-2 anchor, not one per class** (discretion item 7). Two byte-identical
  comments would be a repeated literal in a 75-line module; the single anchor sits immediately
  above both classes and says "on BOTH classes below", naming the `max_request_body_bytes`
  class-attribute constraint once. No `NotImplementedError` — the view is fully functional
  without the cap, so no call path must fail loudly.
- **The router stub is a callable class instance, not a function** (discretion item 2).
  `_RecordingDjangoApplication` lets one object serve both the identity assertion (`"http" is
  <it>`) and the per-instance path recording, with no module-level list to clear between tests.
  `_router()` supplies a fresh instance via `kwargs.setdefault`, so a caller that cares passes
  its own and a caller testing the failure matrix passes the unusable value explicitly.
- **`_ws_graphql_data` moved up beside `_graphql_post`** into the "Communicator plumbing"
  section, because it now has three callers spread across the file rather than one below its old
  definition site. Its new `cookie=` parameter appends to the existing header list — a
  one-parameter extension, not a second helper.
- **Test numbers were re-flowed only inside the present-state block** (1, 2, 3, 3b, 4, 5, 6, 7,
  8, 9, 10) so the eviction / degraded block keeps its committed numbers (11-15, 17) untouched.
  The surviving WebSocket request-contract test moved from "Test 16b" to "Test 16" now that the
  HTTP colour is deleted. `3b` follows the file's own existing `16b` precedent.
- **`fired == ["operation"]` was NOT weakened** for the re-aimed schema-passthrough test: the
  graphql-transport-ws single-result flow fires `on_operation` exactly once, verified by running
  it. No adjustment or membership-test downgrade was needed.
- **Row 4 grants `add_category` explicitly** rather than relying on a superuser. First attempt
  used `staff_1`; it failed with `Not authorized to create CategoryType` because
  `create_users` makes `staff_1` `is_staff=True` but NOT a superuser. Switched to the sibling
  suite's own idiom (`view_category_1` + an explicit `Permission` grant + a re-fetch to drop the
  stale perm cache), so the row fails on CSRF alone and never on authorization.
- **Row 7's GET-with-query direction is `400`, not `405`.** Derived from a real run and from
  reading `strawberry/http/sync_base_view.py`: `allow_queries_via_get=False` subtracts
  `OperationType.QUERY` from `allowed_operation_types`, and the resulting
  `InvalidOperationTypeError` is translated to `HTTPException(400, ...)`. The plan's prose said
  only "rejected rather than executed", which this satisfies; recorded because the number is
  now pinned.
- **Row 7 pins `404` + `text/plain` for `graphql_ide=None`.** Upstream raises
  `HTTPException(404, "Not Found")` when an IDE-eligible GET arrives with no IDE configured, and
  `dispatch` renders it `text/plain`. Status + content type + absence of an HTML body are
  asserted; the reason string is not.
- **The IDE rows send an explicit `Accept: text/html`.** `should_render_graphql_ide` requires
  `text/html` or `*/*` in the accept header, and Django's test client sends no `Accept` by
  default — a bare GET would silently take the query path and prove nothing about the IDE.
- **The async probe needed no `django_db` marker.** `{ __typename }` touches neither the ORM nor
  the session store, so pytest-django's blocker stays satisfied; `override_settings` is used as a
  context manager inside the async body rather than as a decorator, avoiding any question about
  decorator/coroutine interaction.
- **`tests/auth/test_mutations.py::_channels_router` became a local composition.** Body only —
  all eight call sites and every assertion are untouched. It now composes
  `ProtocolTypeRouter({"http": AuthMiddlewareStack(URLRouter([re_path(r"^graphql/?$",
  GraphQLHTTPConsumer.as_asgi(schema=schema))])), "websocket": AllowedHostsOriginValidator(...)})`
  — exactly the shape the `0.0.14` router composed, which those tests were borrowing as a
  harness. Keeping the tests is not optional: they are the only coverage of
  `auth/sessions.py`'s `Transport.CHANNELS_HTTP` arm, which this card does not remove, and
  deleting them would drop the package below `fail_under = 100`.
- **The three live probe views that build upstream's `GraphQLView` directly were left alone**
  (`test_optimizer_auto_api.py`, `test_multi_db.py`, `test_debug_extension_api.py`), per the
  plan's duplication-risk 6 — upstream's view remains a supported mount and their subjects are
  the optimizer / multi-DB routing / debug extension.

### Notes for Worker 3

- No shadow file was used for implementation; `views.py` is a pure-class-definition module
  (docstrings + two empty subclass bodies + one comment), which is BUILD.md's stated skip case
  for the static helper — record either the run or the skip-with-reason.
- Row 9's absence proof reads `Path(routers_module.__file__).read_text()`, i.e. the real
  `django_strawberry_framework/routers.py`, never anything under `docs/shadow/`.
- `django_strawberry_framework/__init__.py` is NOT in the diff, so the public-surface check
  should show `git diff -- django_strawberry_framework/__init__.py` empty. The three breaking
  constructor changes are authorized by spec Decision 5 (measure against it, not against "no API
  breakage").
- Two throwaway artifacts existed during the pass and were removed: a probe under
  `docs/builder/temp-tests/slice-1/` (used only to dump the kanban payload) and two scratchpad
  copies of `config/urls.py` used for the pre-existing-failure verification. `git diff --stat`
  on `config/urls.py` after the restore shows only the slice's own 7/2 change.
- One non-obvious control flow worth knowing before reading the WS matrix: a non-matching
  WebSocket path raises `ValueError("No route found")` out of `URLRouter`, and
  `WebsocketCommunicator.connect()` would sit out its full 10 s timeout before re-raising it, so
  the reject direction uses the file's existing `send_input` + `wait()` idiom instead.
- **Verify with the canonical `uv run pytest --no-cov`** (all four `testpaths`), which is green at
  4800 passed / 40 skipped. Narrower invocations (`examples/fakeshop/test_query/` alone, or
  `tests/` + `examples/fakeshop/tests/`) surface pre-existing order/distribution-dependent
  failures in committed example tests; all of them reproduce with HEAD's `config/urls.py`, i.e.
  with this slice's production code off the request path. Commands and outputs are under
  `#### Pre-existing / invocation-shape claim verification`. Please do not attribute them to this
  diff.

### Notes for Worker 1 (spec reconciliation)

Resolution of the five discrepancies the plan handed me, then two new ones.

1. **Plan item 1(a) — "Preserved verbatim" is mechanically unachievable.** Resolved exactly as
   planned: all eight preserved constructions route through one `_router()` helper and every
   preserved test's *assertions* are byte-identical. **Small drift to note inside this item:**
   the plan's literal guard body was `if django_application is None or not callable(...)`; I
   implemented `if not callable(...)` because `callable(None)` is already `False` and the first
   operand is unreachable-as-a-decision. Both Error-shapes inputs are still tested and still get
   the one message. If you prefer the two-operand form as documentation, say so and I will
   restore it; the comment above the guard currently carries that documentation instead.
2. **Plan item 1(b) — two "preserved" tests are HTTP-branch tests.** Resolved as planned: both
   re-aimed at WebSocket with subjects intact
   (`::test_schema_object_passes_through_unchanged_with_extensions_intact`,
   `::test_authenticated_session_round_trip_reaches_the_resolver`). Your candidate spec edit
   still stands: Decision 13 should carry a third category, "re-aimed to the WebSocket branch,
   subject preserved". Confirmed detail for that edit: the WS single-result flow fires
   `on_operation` exactly once, so row 12's assertion needed no adjustment.
3. **Plan item 2 — the unlisted sixth test.** Resolved as planned:
   `::test_request_contract_resolves_through_the_router_for_anonymous_reads` deleted with the
   orphan `whoami` field. The required coverage check was performed, not assumed: I read
   `tests/utils/test_permissions.py` before deleting and confirmed both uniquely-touched lines
   are covered there independently — `ChannelsRequestAdapter.__getattr__` by its delegation
   assertions (`adapter.method`, `adapter.headers`, `adapter.consumer`, `adapter.body`, plus the
   `AttributeError` direction) and `_channels_scope`'s first branch by the `_FakeChannelsRequest`
   / `_FakeConsumer` `consumer.scope` mapping duck shape, with the non-mapping fall-through
   covered too. Nothing was reinstated at a transport that no longer exists.
4. **Plan item 3 — "three HTTP-branch tests" vs Decision 13's five.** Implemented Decision 13:
   five rewritten/merged. Cosmetic count mismatch in the Slice-1 checklist bullet only.
5. **Plan item 4 — `examples/fakeshop/config/urls.py` unnamed by the checklist.** Swapped, with
   the rationale recorded in the file itself (a comment naming Decision 6) as well as in the
   plan. The live tier now proves the package view rather than upstream's; sixth live row
   (`::test_the_package_view_serves_an_ordinary_graphql_response`) guards the swap directly.
   Plan item 5 (Slice 2's cap matrix should join `test_transport_api.py` rather than
   `test_products_api.py`) is unaffected by anything I did and I agree with the recommendation.
6. **NEW — Decision 13's test inventory misses `tests/auth/test_mutations.py`, which the
   constructor break reaches.** `::_channels_router` called `DjangoGraphQLProtocolRouter(schema)`
   and eight tests drove `HttpCommunicator` against the result to exercise the Channels-HTTP auth
   session lifecycle (`test_channels_http_login_round_trip_...`,
   `..._anon_to_auth_cycles_key_...`, `..._as_different_user_flushes_old_data`,
   `..._relogin_same_user_matching_hash_retains_key`,
   `..._relogin_same_user_mismatched_hash_flushes_and_replaces`,
   `test_channels_http_logout_invalidates_cookie_and_durable_session`,
   `test_channels_http_anonymous_logout_is_false_but_flushes_residue`, and
   `test_websocket_server_side_logout_invalidates_and_survives_reconnect`, whose login leg is an
   HTTP post). Every one broke at construction. I repaired the harness in place (helper body
   only; all call sites and assertions untouched) because worker-2.md makes an in-build failure
   the build's to fix in the active loop, AGENTS.md rule 13 requires the sweep in the same
   change, and those tests are the only coverage of `auth/sessions.py`'s
   `Transport.CHANNELS_HTTP` arm — deleting them would break `fail_under = 100` on a surface this
   card does not remove. **Two things for you to weigh:** (a) whether Decision 13 should name
   this file explicitly, since a reviewer reading only the spec would see an unlisted test
   change; and (b) whether the spec wants a sentence stating that Channels-HTTP GraphQL remains
   a *consumer-composable* transport (the package simply stops composing it), because that is
   the premise the repaired harness rests on and it sits right next to Decision 2's "the Channels
   request adapter is now a WebSocket-only shape".
   - Adjacent, smaller: `django_strawberry_framework/auth/sessions.py`
     #"Route GraphQL through DjangoGraphQLProtocolRouter so the scope carries a" is a production
     error message that now over-promises — the router no longer produces an `http` scope for
     GraphQL. It fires only for an unrecognized `scope["type"]`, so it is not load-bearing, and
     it is outside this slice's named files, so I left it. Candidate for Slice 5's transport
     wording pass or a one-line Worker-1 call.
7. **NEW — pre-existing order/distribution fragility in committed example tests. Does NOT block
   the gate; the canonical full sweep is green (4800 passed / 40 skipped).** Two sets surface
   only under narrowed invocations, and both reproduce with HEAD's `config/urls.py`:
   - `examples/fakeshop/test_query/test_kanban_api.py::test_select_board_docs_and_lookup_roots_for_static_dashboard`
     expects `allKanbanSections == [{"key": "scope"}]`, but the committed data migration
     `examples/fakeshop/apps/kanban/migrations/0015_seed_reclassification_sections.py` seeds four
     more `Section` rows (`test_plan`, `decision`, `open_question`, `note`). It passes under
     `-n auto --dist loadscope` with all four `testpaths` and fails under `-n0` or a
     single-directory run — so its greenness rests on a `transaction=True` neighbour flushing the
     migration-seeded lookup table on the same worker, not on the assertion being true.
   - four `examples/fakeshop/tests/test_export_schema.py` rows plus
     `test_urls.py::test_index_view_renders_dev_links` fail when `examples/fakeshop/test_query/`
     and `examples/fakeshop/apps/` are excluded from the invocation.

   Both are committed-and-clean files outside this slice's contract, so I flagged rather than
   fixed them. Worth a maintainer-facing follow-up in the deferred-work catalog: a live test that
   only passes because a neighbour truncated a migration-seeded lookup table is a latent
   order-dependence of exactly the class BUILD.md's "invisible below the full parallel test run"
   note warns about, and the honest fix (expect the migration-seeded rows) is a one-liner.

---

## Review (Worker 3)

Reviewed against the working-tree diff obtained independently (`git status --short`,
`git diff`, `git diff --stat`) rather than against the build report's inventory. The
report's inventory matched the diff exactly: `django_strawberry_framework/views.py` (new),
`django_strawberry_framework/routers.py`, `examples/fakeshop/config/urls.py`,
`tests/test_routers.py`, `tests/test_views.py` (new),
`examples/fakeshop/test_query/test_transport_api.py` (new), and
`tests/auth/test_mutations.py`. Nothing else in the diff; every other dirty path is on the
build plan's baseline-dirty list and was neither reviewed nor touched.

**Static inspection helper.** Ran
`uv run python scripts/review_inspect.py django_strawberry_framework/routers.py --output-dir docs/shadow`
-> `docs/shadow/django_strawberry_framework__routers.{stripped.py,overview.md}`. Post-slice
overview: 11 imports, 5 symbols, **1 control-flow hotspot** (`_build_router_class`, 119
lines / 5 branch nodes), 0 Django/ORM markers, 0 calls of interest, **0 TODO comments**
(the slice left no anchor in `routers.py`, as planned), 1 repeated literal
(`DjangoGraphQLProtocolRouter` 2x - the two present-but-broken hint strings, two distinct
actionable messages; not a DRY defect). The hotspot survives but its *content* shrank: the
`http_urls` list and the `if django_application is not None` append are gone, one
`callable()` guard arrived. Shadow line numbers are not canonical; every citation below is
symbol-qualified.

**`views.py`: helper SKIPPED, reason recorded.** It is a pure-class-definition module in
BUILD.md's exact sense - module docstring, `from __future__ import annotations`, one
import, `__all__`, one `#` comment, and two classes whose entire bodies are docstrings.
Zero statements of logic, zero branches, zero calls. Nothing the AST overview would
surface.

**Canonical full sweep, run by me:** `uv run pytest --no-cov` ->
**4800 passed, 40 skipped in 59.82s, zero failures.** Byte-for-byte the count Worker 2
reported. Focused confirmation:
`uv run pytest tests/test_routers.py tests/test_views.py examples/fakeshop/test_query/test_transport_api.py tests/auth/test_mutations.py tests/utils/test_permissions.py --no-cov`
-> 165 passed.

**Hygiene re-verified independently** (not taken on the report's word), explicit paths
only: `ruff format --check` -> `7 files already formatted`; `ruff check` -> `All checks
passed!`; `scripts/check_trailing_commas.py --check <7 explicit paths>` -> silent/0;
`git diff --check` -> clean; ASCII-only scan of all seven touched `.py` -> clean; no
physical line over 100 columns in any new or touched file.

### High:

None. No correctness bug, no spec-contract violation, no unauthorized API break, no
security or data-isolation regression, and no crashed consumer path was found. The five
spec Decisions this slice owns (2, 3, 4, 6, 13) each land as written - evidence under
`### What looks solid`.

### Medium:

#### M1 - the `channels`-free import boundary is asserted but not proven: the eviction prefixes miss `strawberry.django`

`tests/test_views.py::test_views_module_imports_with_channels_absent` is the only test
pinning Decision 6 / Error shapes' asymmetry ("`django_strawberry_framework.views` needs
**no** `channels`, so a WSGI-only project can adopt the whole HTTP half of this card
without ever touching the soft dependency"), and its own docstring plus
`django_strawberry_framework/views.py`'s module docstring
#"This module is ``channels``-free: it imports only ``strawberry.django.views``, which
itself reaches for ``django``, ``cross_web``, and ``strawberry``" claim the *graph*, not
just the leaf. The test cannot make that proof.

```tests/test_views.py:37
_ABSENCE_PREFIXES = ("strawberry.channels", "daphne", "django_strawberry_framework.views")
```

`tests/_soft_dependency.py::_matches` evicts only names equal to, or dotted children of, a
listed prefix. `strawberry.django` / `strawberry.django.views` match none of them, and both
are already in `sys.modules` from this test module's own line-31 top-level import. So
inside the `simulated_absence` block the re-executed `views.py` body resolves
`from strawberry.django.views import AsyncGraphQLView, GraphQLView` **straight out of the
module cache**, and the `sys.modules["channels"] = None` sentinel is never on that import's
path. The test would stay green if `strawberry.django.views` grew a `channels` import
tomorrow - i.e. it cannot fail for the reason it claims to test. This is BUILD.md's
"a test that asserts only observability is not proof" in the import-boundary flavor.

**The underlying property IS true** - verified, not assumed, with a throwaway
fresh-interpreter probe (see `### Temp test verification`): with
`sys.modules["channels"] = None` and `sys.modules["daphne"] = None` installed *before any
strawberry import at all*, `import django_strawberry_framework.views` succeeds, both
classes resolve, `"strawberry.channels"` never enters `sys.modules`, and `routers.py` still
refuses with its install hint. So this is a test-strength defect, not a behavior defect -
which is exactly why it is worth fixing now rather than discovering later.

**Recommended change.** Add `"strawberry.django"` to `_ABSENCE_PREFIXES` so
`strawberry.django.views`' own module body re-executes under the sentinel. I confirmed the
fix is viable and does not poison neighbouring state: a temp mirror test with the stronger
prefix tuple passed alongside the whole of `tests/test_views.py`, and a broader
single-worker run
(`docs/builder/temp-tests/slice-1/test_stronger_absence.py tests/test_views.py tests/test_routers.py tests/utils/ tests/testing/ -n0`)
came back **527 passed**. Because re-executing a third-party package body is precisely the
order-dependent class BUILD.md's "invisible below the full parallel test run" note warns
about, Worker 2 must re-confirm with the canonical `uv run pytest --no-cov` after the
change. If that sweep does surface pollution, the acceptable fallback is a subprocess
probe (the shape of my temp file), NOT reverting to the current non-distinguishing
assertion.

**Test expectation.** Inside the block: `sys.modules["channels"] is None`,
`"strawberry.django.views" not in sys.modules` (the new load-bearing precondition - it is
what proves the chain re-executes), the import succeeds, both classes are classes, and
`"strawberry.channels" not in sys.modules` after the import.

#### M2 - the build report's justification for the `tests/auth/test_mutations.py` repair is factually wrong, and Worker 1 would inherit the false premise

`### Implementation notes` #"they are the only coverage of ``auth/sessions.py``'s
``Transport.CHANNELS_HTTP`` arm, which this card does not remove, and deleting them would
drop the package below ``fail_under = 100``" and `### Notes for Worker 1` item 6 repeat the
same claim. Per `worker-3.md` #"Pre-existing claim verification" I checked it rather than
accepting it, and it does not hold:

- `tests/auth/test_sessions.py:69` asserts
  `classify_transport(_adapter({"type": "http"})) is Transport.CHANNELS_HTTP`; `:167`
  covers `require_session(adapter, Transport.CHANNELS_HTTP)`; `:302`, `:308`, `:317` cover
  `login_supported` / `logout_supported` for that member. That is the
  `auth/sessions.py::Transport.CHANNELS_HTTP` surface, covered without the router harness.
- `tests/auth/test_mutations.py::test_sync_channels_http_bridge_establishes_and_persists_the_session`
  and `::test_sync_channels_http_logout_bridge_tears_down_the_session` are self-documented
  as "The ``transport is CHANNELS_HTTP`` arm of the SYNC body" and drive
  `auth/mutations.py::_login_resolve_body` #"if transport is sessions.Transport.CHANNELS_HTTP"
  and its logout twin **without** `_channels_router`. The async colours
  (`::test_channels_http_login_signal_failure_compensates_scope_and_durable`,
  `::..._cleanup_failure_retains_primary_and_chains_cleanup`,
  `::..._cancelled_between_key_write_and_asave_compensates`,
  `::test_async_channels_http_wrong_password_...`,
  `::test_channels_logout_flush_failure_...`, `::test_channels_logout_signal_failure_...`)
  likewise do not use the harness.

The eight `_channels_router` call sites are the only **end-to-end HttpCommunicator** proof
of the Channels-HTTP session round trip (cookie mint, key cycling, durable teardown,
reconnect) - a real and worth-keeping subject, and a defensible reason to repair rather than
delete. But that is a different, narrower claim than the one recorded, and the recorded one
is the premise Worker 1 is being asked to weigh a spec edit against.

**Recommended change.** Correct the two statements in the build report to the verified
scope: the harness is the only end-to-end HTTP-transport coverage of the Channels-HTTP auth
session lifecycle; the `Transport.CHANNELS_HTTP` enum member and both `mutations.py` arms
are independently covered in `tests/auth/test_sessions.py` and by the two `_sync_..._bridge`
tests. No code change. (My verdict on the repair itself is under
`### Notes for Worker 1` - it is legitimate consumer-side composition, not a contract
contradiction.)

#### M3 - Decision 4's two negative contracts are stated by the spec and pinned by nothing

Decision 4 asserts, in its own words, "There is no aliased `url_pattern=` kwarg kept for
compatibility" and makes `websocket_url_pattern` keyword-only; the constructor implements
both (`routers.py::DjangoGraphQLProtocolRouter.__init__` - `*` before the parameter, no
alias). Neither is pinned by a test. The spec's Test plan has no row for them, so this is
not a silently-unaddressed checklist sub-check - but they are the two contracts most likely
to be quietly re-added by a later slice's convenience edit (Slice 4 reopens this exact
signature to add `websocket_consumer_class=` and `websocket_revalidation_window=`), and the
whole point of the rename per Decision 4 is that "a single parameter that no longer affects
HTTP would be a name that lies".

**Recommended change.** Two rows in the existing
`::test_construction_rejects_an_omitted_or_unusable_django_application` (or one sibling
test): `pytest.raises(TypeError, match="url_pattern")` for
`_router(url_pattern="^graphql")`, and `pytest.raises(TypeError)` for
`_router_class()(SCHEMA, _RecordingDjangoApplication(), "^graphql")` (the positional
third argument the keyword-only boundary must refuse). Cheap, and they make Slice 4's
signature edit fail loudly if it relaxes either.

### Low:

#### L1 - the hint's "REMOVED, not flagged" half can drift out unnoticed

`routers.py` #"_MISSING_DJANGO_APPLICATION_HINT" carries the three facts spec Error shapes
requires, including "That mode is REMOVED, not flagged." The re-typed assertions in
`tests/test_routers.py::test_construction_rejects_an_omitted_or_unusable_django_application`
pin `"ALLOWED_HOSTS"` (fact a) and `"get_asgi_application"` + `"DjangoGraphQLView"`
(fact c), but nothing pins fact (b). Add `assert "REMOVED" in message`. The re-typing
discipline (never import the constant) is correct and should be kept.

#### L2 - three production strings in `auth/` are now factually wrong because of this slice

Not load-bearing, outside the slice's named files, and correctly left alone by Worker 2 -
recorded so they are discharged rather than forgotten:

- `django_strawberry_framework/auth/sessions.py::classify_transport`
  #"Route GraphQL through DjangoGraphQLProtocolRouter so the scope carries a" - a
  `ConfigurationError` message that now over-promises: the router produces no GraphQL
  `http` scope at all. Reachable only for an unrecognized `scope["type"]`.
- `django_strawberry_framework/auth/mutations.py::_login_resolve_body` and
  `::_logout_resolve_body`, both #"the package router's async consumer instead awaits the
  native async body" - the package router has no async HTTP consumer any more.

Route to Slice 5's transport-wording pass (spec `## Doc updates`), or a one-line Worker 1
call. Flagged for the deferred-work catalog either way.

#### L3 - `test_transport_api.py` naming reads backwards from what it does

`examples/fakeshop/test_query/test_transport_api.py::test_graphql_ide_and_get_queries_can_be_turned_off_on_the_package_view`
#"default_post = _post(client, _TYPENAME, path=\"/ide-off/\")" - the variable named
`default_post` posts to the *probe* mount, not the default one, and sits three lines above
`default_ide`, which genuinely does hit the default mount. Rename to `ide_off_post` (or
similar). Cosmetic; the assertion is correct.

#### L4 - row 2's exact-value referrer assertion (recorded, no change required)

`::test_security_middleware_headers_ride_the_graphql_response`
#"assert response.headers[\"Referrer-Policy\"] == \"same-origin\"" pins Django's default
by value, so a future fakeshop `SECURE_REFERRER_POLICY` change would fail this row for a
reason unrelated to its subject. **Intentionally rejected as a finding:** the header's
configured *value* riding a GraphQL response is part of what spec Test plan row 2 asks to
prove, fakeshop's settings are the example project's own pinned contract, and the docstring
names the source. Leaving it exact is the more honest assertion. No change.

### DRY findings

- **D1 (change requested).** The "no GraphQL envelope" intent is spelled implicitly four
  times as a bare byte-literal search in
  `examples/fakeshop/test_query/test_transport_api.py`: rows 3, 4, 6 and 7
  (#"assert b'\"data\"' not in response.content" and its three siblings). It is the
  load-bearing half of three of those rows - the thing that proves Django answered *before*
  schema execution - and it currently reads as an incidental substring check. One
  module-level `def _assert_no_graphql_envelope(response):` names it once and makes the
  four call sites say what they mean. BUILD.md Medium-tier "repeated literal that should be
  a named constant" applies; recorded at DRY rather than Medium because the fix is
  mechanical and the assertions are individually correct.
- **D2 (verified live, then rejected).** `tests/auth/test_mutations.py::_channels_router`
  re-types the WebSocket composition and the `r"^graphql/?$"` literal that
  `routers.py::_build_router_class` owns. The DRY-er shape would be to source the WS half
  from `DjangoGraphQLProtocolRouter(...).application_mapping["websocket"]`. **Rejected:**
  that would re-couple the auth harness to the very transport this card decoupled, and it
  would make an auth-suite failure depend on a router change - the opposite of what the
  repair is for. This file's own established discipline
  (`tests/test_routers.py` #"importing the router constants and asserting them against
  themselves could never catch the hint drifting") is to re-type rather than import. Only
  one of the eight harness consumers needs the WS half
  (`::test_websocket_server_side_logout_invalidates_and_survives_reconnect`), so the
  composition is live, not dead. Leave as-is.
- **D3 (verified live, then rejected).** `test_transport_api.py::_post` vs
  `examples/fakeshop/graphql_client.py::post_graphql`. Read both: `post_graphql`'s
  signature is `(query, *, client=None, variables=None)` and it routes through
  `django_strawberry_framework.testing.TestClient` against the fixed endpoint - it has no
  seam for a path, `HTTP_HOST`, `secure=True`, or arbitrary `**extra`, which four of these
  rows require by subject. That is the documented raw-envelope exemption in
  `examples/fakeshop/test_query/README.md` #"Only tests whose subject is the raw request
  envelope". The two rows whose subject *is* an ordinary response
  (`::test_the_package_view_serves_an_ordinary_graphql_response`) correctly do go through
  the shared helpers. Not a near-copy to consolidate.
- **D4 (no finding).** No second live harness was introduced. The Probe URLconf follows
  `examples/fakeshop/test_query/test_client_api.py` #"urlpatterns = [path(\"\",
  include(\"config.urls\")), path(\"alt/\", _alt_graphql_view)]" exactly, including the
  resolve-the-view-at-request-time rationale, and four sibling live modules already carry
  their own module-level `urlpatterns`. No new fixture module, no second reload discipline.
- **D5 (no finding).** The single `_router(...)` construction seam in
  `tests/test_routers.py` is the right call and demonstrably paid for itself: eight
  preserved tests each needed the new required argument, and every one of them kept its
  assertions byte-identical instead of growing the same keyword. `_RecordingDjangoApplication`
  as one instance serving both the identity assertion and the path recording removes the
  module-level list the old `test_non_graphql_path_reaches_the_fallback_only_when_provided`
  needed.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty**. The root `__all__` (32
names) is unchanged and contains neither `views` nor either view class, and
`tests/test_views.py::test_module_exports_exactly_the_two_view_classes_and_stays_off_the_package_root`
pins that as a standing assertion rather than a review-time observation.
`routers.py::__all__` is unchanged at `("DjangoGraphQLProtocolRouter",)` with its PEP 562
`noqa: F822` lazy-export comment intact.

**Measured against spec Decision 5, not against "no API breakage"** (per the build plan's
context flag). Decision 5 names exactly three permitted breaks; the diff contains exactly
those three and no fourth:

1. **`django_application` becomes required** - `routers.py::DjangoGraphQLProtocolRouter.__init__`
   now takes it positional-or-keyword with no default. Authorized (Decision 3, Decision 5
   break 1).
2. **`url_pattern` -> `websocket_url_pattern`** - renamed, narrowed to WebSocket, and
   keyword-only. Authorized (Decision 4, Decision 5 break 2). The keyword-only narrowing is
   a sub-aspect of the same break and is stated verbatim by Decision 4 ("keyword-only"), so
   it needs no separate authorization.
3. **GraphQL HTTP now requires a `urlpatterns` entry** - `views.py` ships the class the
   entry names. Authorized (Decision 5 break 3, Decision 6).

Everything else checked and found non-breaking: the `"http"` mapping value becoming the raw
supplied application is Decision 2's *behavior*, not a signature change;
`_STRAWBERRY_CHANNELS_BROKEN_HINT`'s parenthetical narrowed from
`(GraphQLHTTPConsumer / GraphQLWSConsumer)` to `(GraphQLWSConsumer)` but it is a private
module constant and
`::test_degraded_partial_install_raises_the_split_actionable_errors` asserts only the two
re-typed floor substrings, which are untouched; the soft-`channels` guard,
`require_channels`, the `_ROUTER_CLASS` cache, the three-hint triple, and the module
`__getattr__` are unchanged in mechanism. The two new public symbols
(`DjangoGraphQLView`, `AsyncDjangoGraphQLView`) are purely additive leaf-module exports,
authorized verbatim by Decision 6 #"It is a leaf-module import ... never a package-root
export".

**Verdict: clean. No break present that Decision 5 does not name.**

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`. Confirmed by
`git diff --name-only -- CHANGELOG.md` -> empty.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Verified
directly rather than inferred - `git diff --name-only -- docs/README.md README.md TODAY.md
docs/TREE.md CHANGELOG.md pyproject.toml uv.lock tests/base/test_init.py` returns **empty**,
so the version quintet is entirely unmoved (spec Decision 15, build-plan joint-cut flag).
`docs/GLOSSARY.md` reports one changed line, which is the baseline-dirty concurrent
row-preserving FilterSet edit already recorded in the build plan's out-of-scope list, not
this slice's; `KANBAN.md` / `KANBAN.html` / `examples/fakeshop/db.sqlite3` likewise. No
`.md` outside this artifact is in the diff. `docs/TREE.md` not carrying `views.py` yet is
correct: spec `## Doc updates` assigns the regeneration to Slice 5, and no test or gate
command in this build asserts TREE currency.

One forward note, not a finding: between this slice and Slice 5 the tree contains
`docs/README.md` / `README.md` / `TODAY.md` prose describing a router that no longer
exists. That is the spec's own chosen sequencing and the maintainer's first touch point is
after `bld-final.md`, so the wrong prose never reaches a commit boundary alone.

### What looks solid

- **Decision 2 lands structurally, and is proven three independent ways.** The mapping is
  `{"http": django_application, "websocket": AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([...])))}`
  with no wrapper on HTTP. `::test_http_branch_is_the_supplied_django_application_by_identity`
  pins object identity (correct - Channels' `ProtocolTypeRouter.__init__` stores the mapping
  verbatim with no coercion, which I read in `channels/routing.py` to confirm the identity
  assertion is meaningful rather than accidental);
  `::test_http_branch_delegates_every_path_to_the_supplied_application` proves it
  *behaviorally* by driving a real GraphQL-shaped POST at `/graphql` **and** an unrelated
  `/admin/login/` GET through `HttpCommunicator` and asserting the stub recorded
  `["/graphql", "/admin/login/"]` and answered its own deliberately un-Django-like `418`
  both times - so no package route intercepts the GraphQL path, which is the actual
  content of the decision; and
  `::test_graphql_http_consumer_left_the_router_module_entirely` reads the real
  `Path(routers_module.__file__).read_text()` (verified: not a `docs/shadow/` target) for
  the absence of the symbol. I independently confirmed `grep GraphQLHTTPConsumer
  django_strawberry_framework/routers.py` is empty, and that the only surviving package
  mentions are three prose references to `SyncGraphQLHTTPConsumer` in `auth/` (see L2).
- **Decision 3 is genuinely required, both arms tested.** No default on the parameter, so
  `_router_class()(SCHEMA)` is Python's own `TypeError` naming it - asserted. The
  `callable()`-only guard drift Worker 2 recorded is **correct and verified**:
  `callable(None)` is `False`, so the plan's `django_application is None or not
  callable(...)` first operand can never change the outcome, and the comment above the
  guard carries the documentation the deleted operand would have. Both Error-shapes inputs
  are exercised (`for unusable in (None, object())`), both get the one prose message, and
  the message substrings are re-typed rather than imported - which is the discipline that
  makes the assertion able to catch drift at all.
- **Decision 4's default is exactly `r"^graphql/?$"` and genuinely both-ends anchored**,
  and the exact-match matrix is behavioral rather than structural:
  `::test_default_websocket_url_pattern_matches_exactly` drives five real
  `WebsocketCommunicator` cases - `/graphql` and `/graphql/` connect and negotiate
  `graphql-transport-ws`; `/graphql-admin`, `/graphqlanything`, `/graphql/extra` each raise
  `ValueError("No route found")` out of the `URLRouter`, via the file's existing
  `send_input` + `wait(timeout=10)` idiom rather than sitting out `connect()`'s timeout.
  The structural half (`::test_custom_websocket_url_pattern_reaches_only_the_websocket_re_path`)
  additionally asserts the HTTP value is still the identical stub, which is the half that
  proves the parameter stopped governing HTTP.
- **The live tier genuinely hits real HTTP and pins load-bearing properties, not
  observability.** Every row drives `django.test.Client` / `AsyncClient` against a real
  URLconf (AGENTS.md rule 9). Specifically: row 1 does **not** merely assert a header
  exists - it asserts the recorded *path* (`_MIDDLEWARE_PATHS == ["/graphql/"]`) from a
  middleware installed via its dotted path and appended last (innermost, so every earlier
  middleware demonstrably ran first), with the `Client` built inside the override block
  because a handler caches its chain at first request; row 3 pairs the `400` with
  `b'"data"' not in response.content`, which is what proves Django's host boundary answered
  *before* the schema; row 4's matrix is real (`enforce_csrf_checks=True` + `force_login`,
  the correct token read off the `ensure_csrf_cookie` GET like a browser, the wrong token a
  well-formed 64-char alnum string rather than a malformed one so the rejection is a
  mismatch and not a format error) and it asserts the **database side effect** in both
  directions - no `Category` row on either rejection, the row present on success; row 6
  pins `/graphql/` 200, `/graphql` -> `301` with `Location: /graphql/`, and both prefix
  extensions 404-with-no-envelope; row 7 contrasts the probe mount against the default
  mount inside one test so the difference is attributable to the keywords, and sends an
  explicit `Accept: text/html` (without which a bare GET silently takes the query path and
  proves nothing about the IDE). Row 5's `Vary: Cookie` is the weakest of the set - the
  `ensure_csrf_cookie` mount would set it for an anonymous request too - but spec Test plan
  row 5's bar is "non-cacheable **or** varies on `Cookie`", the payload assertion pins that
  the response really is the logged-in actor's, and the docstring is honest about both
  sources. Acceptable as written.
- **Decision 13's preserved WebSocket Origin / auth subjects survive with nothing
  weakened.** I diffed each one rather than trusting the report.
  `::test_websocket_handshake_origin_directions` (matching / mismatched / missing Origin) -
  construction line only, assertions byte-identical.
  `::test_websocket_branch_wraps_origin_validator_outside_the_auth_stack` - the nesting
  assertion and the `not isinstance(http, OriginValidator)` assertion both survive; only
  the pattern literal changed, forced by Decision 4 (see M4-adjacent escalation below).
  `::test_request_contract_resolves_over_the_websocket_branch` - assertion
  `{"actor": "ChannelsRequestAdapter|True"}` unchanged.
  `::test_authenticated_session_round_trip_reaches_the_resolver` - `database_sync_to_async`
  user + session construction unchanged, `{"username": "channels_probe"}` unchanged, the
  cookie now rides the WS handshake headers via a one-parameter extension of the existing
  `_ws_graphql_data` rather than a second helper.
  `::test_schema_object_passes_through_unchanged_with_extensions_intact` - `fired ==
  ["operation"]` **not** weakened to a membership test, and the structural half lost only
  the assertion whose subject (the HTTP consumer's `initkwargs`) no longer exists. The whole
  eviction-simulated-absence / degraded-install block is untouched.
- **The deleted sixth test's coverage genuinely survives, verified by reading, not by
  claim.** `::test_request_contract_resolves_through_the_router_for_anonymous_reads`
  uniquely touched `utils/permissions.py::ChannelsRequestAdapter.__getattr__` and
  `::_channels_scope`'s first branch. `tests/utils/test_permissions.py` covers both
  independently: its `_FakeChannelsRequest` carries a `_FakeConsumer` whose `.scope` is a
  mapping (the `consumer.scope` HTTP duck shape, `_channels_scope` line 142-145), and its
  delegation test asserts `adapter.method == "POST"`, `adapter.headers is wrapped.headers`,
  `adapter.consumer is wrapped.consumer`, `adapter.body == wrapped.body` plus the
  `AttributeError` direction; the non-mapping `consumer.scope` fall-through is covered too.
  The orphan sweep is clean: no `_graphql_data`, `whoami`, or `url_pattern=` reference
  survives anywhere in `tests/`, and the `_graphql_data` hits in `examples/` are unrelated
  local aliases of `graphql_client.assert_graphql_success`. Every remaining helper in
  `tests/test_routers.py` has live callers.
- **The soft-dependency asymmetry is real** (independent of M1's test weakness): traced in
  a fresh interpreter, `views.py`'s entire transitive import graph is `channels`-free and
  `strawberry.channels` never even enters `sys.modules`. `views.py` imports no `channels`,
  no `.routers`, and no `require_*` guard, so a view-without-router adopter needs nothing
  from the soft dependency.
- **The `examples/fakeshop/config/urls.py` swap is the right call even though the Slice-1
  checklist does not name it.** Without it the live tier would prove *upstream's* view
  while `views.py` carried no live coverage at all, and Decision 6 reason (c) pins the
  live-earnability of the later cap rows to this mount.
  `::test_the_package_view_serves_an_ordinary_graphql_response` guards the swap under a
  transport-shaped name. Blast radius is large (500+ live tests now traverse the package
  view) but genuinely inert: the subclass overrides nothing, and the full sweep is green.
- **Pre-existing-vs-regression: Worker 2's claim holds, and I proved it a way the report
  did not.** The report's reproduction restored HEAD's `config/urls.py` but still collected
  the new `test_transport_api.py`, so it did not isolate the new file - and the new file
  adds a `django_db(transaction=True)` row to `test_query/`, which under
  `--dist loadscope` is exactly the mechanism the report blames. I closed that hole:
  `uv run pytest examples/fakeshop/test_query/ --ignore=examples/fakeshop/test_query/test_transport_api.py --no-cov`
  -> **1 failed, 499 passed, 1 skipped**, the same
  `test_kanban_api.py::test_select_board_docs_and_lookup_roots_for_static_dashboard`. The
  failure therefore predates and is independent of this slice's new file, its
  `transaction=True` row, and its production code. Combined with the canonical sweep being
  green at 4800/40, the conclusion stands: **pre-existing invocation-shape fragility in
  committed example tests, not a regression from this diff.** Worth carrying to the
  deferred-work catalog - a live test whose greenness depends on a neighbour truncating a
  migration-seeded lookup table is latent order-dependence, and the honest fix (expect the
  `0015_seed_reclassification_sections` rows) is a one-liner outside this slice.
- Plan-vs-implementation drift was disclosed rather than buried in all three places it
  occurred (the folded `callable()` guard, row 7's `400`/`404` numbers derived from a real
  run plus a read of `strawberry/http/sync_base_view.py`, and the `tests/auth/` repair),
  which is what made this review checkable.

### Spec slice checklist walk

All six boxes are ticked. Walked each against the diff:

- Box 1 (HTTP branch is the Django application directly, no `URLRouter` /
  `GraphQLHTTPConsumer` / `AuthMiddlewareStack`) - **landed**, three-way proof above.
- Box 2 (`django_application` required; `None` or non-callable -> `ConfigurationError`
  naming the migration) - **landed**, both arms tested, message names the migration.
- Box 3 (`url_pattern` -> `websocket_url_pattern`, default `r"^graphql/?$"`, exact,
  both-ends anchored) - **landed**, plus a five-case behavioral matrix.
- Box 4 (new `views.py` with both classes, declared in the consumer's URLconf) - **landed**,
  and actually mounted in fakeshop.
- Box 5 (three HTTP-branch tests rewritten; every WebSocket Origin / auth test preserved
  verbatim) - **first half landed** (five rewritten/merged, per Decision 13 which governs
  over the checklist's "three"). **Second half is not literally true** and cannot be - see
  the escalation below. Left ticked because the contract the box exists to deliver did
  land; the un-truth is in the spec's wording, which only Worker 1 may fix.
- Box 6 (`tests/test_views.py` + a live tier proving middleware, `ALLOWED_HOSTS`, CSRF,
  security headers, cache policy, and exact routing on the GraphQL HTTP route) -
  **landed**, all six named surfaces present as live rows.

No box is over-ticked in the "ticked without matching implementation" sense, and no
sub-check is silently unaddressed.

### Temp test verification

Both files created under `docs/builder/temp-tests/slice-1/` and **deleted after the runs**
(directory left empty; `git status --short` re-confirmed no new dirt):

- `probe_import_graph.py` - fresh-interpreter probe installing
  `sys.modules["channels"] = None` / `["daphne"] = None` *before any strawberry import*,
  then importing `django_strawberry_framework.views`. Output: both classes resolved,
  `"strawberry.channels" in sys.modules` -> `False`, and `routers.py` still raised its
  install hint. **Disposition: became finding M1** - it proves the property the shipped
  test claims but cannot prove. Deleted; Worker 2 should strengthen the permanent test
  rather than adopt this probe (the in-process prefix fix keeps the coverage in the tier
  that owns it).
- `test_stronger_absence.py` - a mirror of the shipped absence test with
  `"strawberry.django"` added to the eviction prefixes, used to prove M1's recommended fix
  is viable and non-polluting rather than speculative. Passed alongside all of
  `tests/test_views.py` (9 passed), and in a broader single-worker scope with
  `tests/test_routers.py tests/utils/ tests/testing/` (**527 passed**).
  **Disposition: folded into M1's recommended change.** Deleted.

No temp test caught a behavior bug, so nothing needs promotion beyond M1's fix to the
existing permanent test.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Medium) - Decision 13's "Preserved verbatim" list needs a third category,
  and it covers THREE tests, not two.** Worker 1's planning note and Worker 2's report both
  identified two named-as-preserved tests that had to be re-aimed
  (`::test_schema_object_passes_through_unchanged_with_extensions_intact`,
  `::test_authenticated_session_round_trip_reaches_the_resolver`). I found a third that
  neither pass names: `::test_websocket_branch_wraps_origin_validator_outside_the_auth_stack`
  is a genuine WebSocket Origin test on Decision 13's "Preserved verbatim" list, and its
  assertion changed - `_route_patterns(ws_router) == ["^graphql"]` became
  `== [r"^graphql/?$"]`, plus a rewritten trailing comment. The change is *compelled* by
  Decision 4's new default and weakens nothing, but it means the Slice-1 checklist's
  "every WebSocket Origin / auth test is preserved verbatim" and Decision 13's list are
  both literally unachievable for three tests. **Resolution paths:** (a) add the third
  category Worker 1 already proposed ("re-aimed / mechanically updated, subject preserved")
  and move all three into it, noting for this one that only the pattern literal moved and
  why; or (b) keep two categories and add a one-line carve-out to Decision 13 stating that
  a preserved test's `websocket_url_pattern` literal necessarily tracks Decision 4's
  default. (a) is the honest record. Either way the Slice-1 checklist bullet's "verbatim"
  should read "preserved in subject and assertion strength". No code change either way.
- **Escalated (Medium) - Decision 2's "the Channels request adapter is now a
  WebSocket-only shape" is broader than the code, and Decision 13's inventory omits
  `tests/auth/test_mutations.py`.** My verdict on the repair, asked for explicitly:
  **legitimate consumer-side composition, not a contract contradiction.** The reasoning,
  checked in the source rather than inferred: `auth/sessions.py::Transport.CHANNELS_HTTP`
  still exists, `::classify_transport` still returns it for a Channels scope with
  `type == "http"`, and `auth/mutations.py` still branches on it in both the sync login and
  sync logout bodies. The package therefore still *supports* a consumer who mounts
  `strawberry.channels.GraphQLHTTPConsumer` themselves; what Slice 1 removed is the package
  *composing* it, and that removal is independently proven by the source-text absence test
  over `routers.py`. The repaired `::_channels_router` composes the transport in a test
  file, exercising a shipped-and-unremoved arm - the correct alternative (deleting eight
  tests of a surviving surface) would have been the actual defect. **But the spec now says
  two things that read as contradicting each other**, and a reviewer reading only the spec
  would see an unlisted test change. **Resolution paths:** (a) narrow Decision 2's sentence
  to "the Channels request adapter is a WebSocket-only shape *in the package's own
  composition*; a consumer-mounted `GraphQLHTTPConsumer` is still classified and served by
  `Transport.CHANNELS_HTTP`", and add `tests/auth/test_mutations.py` to Decision 13's
  inventory as a harness-only repair; or (b) leave Decision 2 and add the clarifying
  sentence to Decision 13 alone. (a) is stronger - Decision 2 is the sentence a future
  reader will cite. Note also that this is the premise the Slice-1 deletion of
  `::test_request_contract_resolves_through_the_router_for_anonymous_reads` rests on, so
  the two decisions should say the same thing.
  - Correction Worker 1 should carry into that weighing: the build report's stated
    justification for the repair is **factually wrong** (finding M2). The eight tests are
    the only *end-to-end HttpCommunicator* coverage of the Channels-HTTP auth session
    lifecycle; they are **not** the only coverage of `Transport.CHANNELS_HTTP`, which
    `tests/auth/test_sessions.py` and two non-harness `_sync_..._bridge` tests cover
    independently. The repair is still right; the premise as written is not.
- **Escalated (Low) - three `auth/` production strings are now factually wrong** (finding
  L2). All outside this slice's named files, none load-bearing. Either fold them into Slice
  5's transport-wording pass (spec `## Doc updates`) or make a one-line Worker 1 call now.
  They belong in `bld-final.md`'s deferred-work catalog if not fixed.
- **For the deferred-work catalog:** the pre-existing kanban / export-schema
  order-dependence, now verified independent of this slice's new file (see
  `### What looks solid`). Committed-and-clean files, outside this build's contract.
- **Agreed, no action needed:** Worker 1's planning notes 3 (three-vs-five count), 4
  (`config/urls.py` unnamed by the checklist - I judge the swap in-scope and necessary), 5
  (Slice 2's cap matrix should join `test_transport_api.py`, not `test_products_api.py` - I
  concur), and 6 (spec status line needs Worker 1's edit at `final-accepted`).

### Review outcome

`revision-needed`.

The diff is strong - the spec contract lands in full, the live tier pins load-bearing
properties rather than observability, the preserved WebSocket assertions are intact, the
public surface breaks exactly the three things Decision 5 authorizes and nothing else, and
the canonical sweep is green at 4800 passed / 40 skipped. It is one Medium away from
acceptance, and that Medium is Worker-2-fixable without any spec context, which is what
rules out `review-accepted`-with-escalation:

- **M1** (strengthen the `channels`-absence eviction prefixes so the test can fail for the
  reason it claims) - one-line change, fix verified viable; re-confirm with the canonical
  full sweep.
- **M2** (correct the overstated `Transport.CHANNELS_HTTP` coverage claim in the build
  report) - prose only, but Worker 1 is being asked to weigh a spec edit against it.
- **M3** (two `pytest.raises` rows for Decision 4's no-alias and keyword-only contracts).
- **L1** (`assert "REMOVED" in message`), **L3** (rename `default_post`), **D1** (one
  `_assert_no_graphql_envelope` helper for the four sites).
- **L4 intentionally rejected**, reason recorded above. **L2 escalated** to Worker 1 /
  Slice 5. **D2, D3, D4, D5** verified live and closed with reasons; no action.

---

## Build report (Worker 2, pass 2)

Apply-changes pass against `## Review (Worker 3)`. Scope: M1, M3, D1 in code/tests; M2
corrected here in prose; L1 and L3 closed. **L4 left exactly as Worker 3 rejected it** (row 2's
exact `Referrer-Policy` value is unchanged). **L2 not touched** — the three now-wrong `auth/`
production strings are escalated to Slice 5, and this pass edits no `auth/` production file.

### Findings resolved

#### M1 (Medium) — the channels-absence test can now fail for the reason it claims

Two changes in `tests/test_views.py::test_views_module_imports_with_channels_absent`, plus a
docstring correction in `django_strawberry_framework/views.py`.

1. **`strawberry.django` is now evicted** — so the single upstream module `views.py` imports
   re-executes its body under the `sys.modules["channels"] = None` sentinel instead of
   answering from the cache. It is evicted through its **own** `evicted_modules(...)` guard
   rather than as a fourth entry in `_ABSENCE_PREFIXES`, because re-executing a third-party
   package body rebinds `django` on the `strawberry` package object and only the
   `(parent, attr)` two-sided restore puts the attribute path and the import path back on one
   module object. **Measured, not assumed** (scratchpad probe, both variants in one process):

   ```text
   BARE prefix   -> vars(strawberry)["django"] is sys.modules["strawberry.django"]  : False
   BARE prefix   -> ...["django"].views      is sys.modules["strawberry.django.views"]: False
   COMPOSED      -> both                                                            : True
   ```

   That divergence is precisely what `evicted_modules`' `(parent, attr)` contract exists to
   prevent (spec-041 D3), so composing the existing helper twice — no new eviction machinery —
   is the shape that keeps the discipline whole. Deviation from Worker 3's literal one-line
   recommendation is recorded here deliberately; the eviction Worker 3 asked for happens, with
   the restore its own helper documents.

2. **Two identity assertions replace the non-distinguishing shape.** Preconditions
   (`"django_strawberry_framework.views" not in sys.modules`,
   `"strawberry.django.views" not in sys.modules`) prove both bodies are out of the cache;
   `"strawberry.channels" not in sys.modules` after the import proves nothing pulled it in;
   and the load-bearing pair is

   ```python
   assert module.DjangoGraphQLView is not DjangoGraphQLView
   assert module.DjangoGraphQLView.__base__ is not DjangoGraphQLView.__base__
   ```

   A re-executed module body produces NEW class objects, so `is not` against the module-scope
   imports is direct evidence that **both** bodies ran under the sentinel. The second line is
   the one the added eviction buys.

**Proof that it can now fail, in both directions** (throwaway scratchpad probes, no repo files
left behind):

```text
# Direction 1 - revert to pass-1's prefix tuple (no strawberry.django):
pass-1 prefixes: views.py body re-ran            -> True
pass-1 prefixes: upstream body re-ran            -> False   <- the new assertion FAILS
pass-1 prefixes: strawberry.django.views cached  -> True

# Direction 2 - inject `import channels` at the top of views.py, restore after (sha256 verified):
uv run pytest tests/test_views.py::test_views_module_imports_with_channels_absent --no-cov -q -n0
  E   ModuleNotFoundError: import of channels halted; None in sys.modules
  django_strawberry_framework/views.py:41: ModuleNotFoundError
  1 failed
```

Direction 2 also holds for the other channels-reaching shapes `views.py` could grow:
`from strawberry.channels import ...` (evicted prefix, and `strawberry.channels` imports
`channels.db` at module level) and `from .routers import DjangoGraphQLProtocolRouter` (the PEP
562 lazy export runs `require_channels()`, which hits the sentinel).

**Docstrings now claim exactly what is proven.**
`django_strawberry_framework/views.py`'s module docstring said `strawberry.django.views`
"reaches for `django`, `cross_web`, and `strawberry`"; it now names the verified set — "the
standard library, `asgiref`, `cross_web`, `django`, `strawberry.http`, and its own
`strawberry.django.context` sibling" — and states that both bodies re-execute under a
simulated absence, which is the scope of the assertion. The test docstring states the boundary
explicitly: modules already imported **below** that boundary (`strawberry.http`, `cross_web`,
`django`) stay cached and are upstream's own contract, not this assertion's. Neither docstring
now claims a whole-graph proof.

A fresh-subprocess probe was **not** promoted: Worker 3's own disposition
(`### Temp test verification`) is that the in-process fix keeps the coverage in the tier that
owns it, and the canonical sweep came back clean, so the documented fallback was not needed.

#### M2 (Medium) — the pass-1 justification was factually wrong; corrected here

Pass 1's `### Implementation notes` and `### Notes for Worker 1` item 6 both claimed the eight
`tests/auth/test_mutations.py::_channels_router` tests "are the only coverage of
`auth/sessions.py`'s `Transport.CHANNELS_HTTP` arm". **That claim is wrong.** Prior sections are
not edited (BUILD.md forbids it); the correction stands here.

**The true, narrower claim:** the eight harness tests are the only **end-to-end
`HttpCommunicator`** coverage of the Channels-HTTP auth session lifecycle (cookie mint, key
cycling, durable teardown, reconnect). They are **not** the only coverage of
`Transport.CHANNELS_HTTP`, and deleting them would not by itself drop the package below
`fail_under = 100`.

Re-verified independently this pass, not taken from the review:

```shell
grep -n "CHANNELS_HTTP" tests/auth/test_sessions.py
#  69: classify_transport(_adapter({"type": "http"})) is Transport.CHANNELS_HTTP
# 167: require_session(adapter, Transport.CHANNELS_HTTP) is session
# 302/308/317: login_supported / logout_supported for that member
grep -c "_channels_router(_auth_router_schema())" tests/auth/test_mutations.py   # -> 8
uv run pytest tests/auth/test_sessions.py \
  "tests/auth/test_mutations.py::test_sync_channels_http_bridge_establishes_and_persists_the_session" \
  "tests/auth/test_mutations.py::test_sync_channels_http_logout_bridge_tears_down_the_session" \
  --no-cov -q
#  -> 28 passed
```

I also read both bridge tests' bodies rather than trusting their names: each builds its
transport with `_channels_adapter(...)` and calls `auth_mutations._login_resolve_body` /
`::_logout_resolve_body` directly, so both `mutations.py` `CHANNELS_HTTP` arms are exercised
with the router harness nowhere on the path. The `_channels_router` call sites (8, confirmed by
count) are all `HttpCommunicator` round trips.

**The repair itself is unchanged and still right** — the subject it protects is real and the
alternative was deleting eight tests of a surviving surface. Only the recorded premise was
false. Worker 1: weigh the Decision 2 / Decision 13 edits against the corrected claim.

#### M3 (Medium) — Decision 4's two negative contracts are now pinned

New `tests/test_routers.py::test_the_websocket_pattern_is_keyword_only_with_no_legacy_url_pattern_alias`
(Test 5b, placed beside the two pattern tests so Decision 4's positive and negative halves read
together; `3b` is the file's own precedent for a lettered insert, and Test 6+ keep their
numbers). Two assertions, both message-matched rather than bare `TypeError`, with the real
messages read off a live construction:

```text
_router(url_pattern="^graphql")
  -> TypeError: ...DjangoGraphQLProtocolRouter.__init__() got an unexpected keyword
     argument 'url_pattern'                                   [match="url_pattern"]
_router_class()(SCHEMA, _RecordingDjangoApplication(), "^graphql")
  -> TypeError: ...DjangoGraphQLProtocolRouter.__init__() takes 3 positional arguments
     but 4 were given                                         [match="positional"]
```

Each fails loudly under exactly the edit it guards: adding a `url_pattern=` alias makes the
first raise nothing; dropping the `*` boundary makes the second raise nothing. That is the
Slice-4 tripwire Worker 3 asked for.

#### D1 (DRY, change requested) — one named helper for the four envelope-absence sites

`examples/fakeshop/test_query/test_transport_api.py::_assert_no_graphql_envelope(response)`
replaces the four bare `b'"data"' not in response.content` searches (rows 3, 4, 6, 7). Its
docstring names why the assertion is load-bearing — a `400` **with** a payload and a `400`
**without** one are different failures, and only the absent `data` key distinguishes "Django
answered first" from "the view executed and reported an error". The assertion message carries
`response.request["PATH_INFO"]`, which strictly improves on row 6's hand-written `, unmatched`
label (now automatic, and present at all four sites instead of one).

#### L1 (Low) — addressed, both halves

- The unpinned fact (b) is now pinned: `assert "REMOVED" in message` joins `"ALLOWED_HOSTS"`,
  `"get_asgi_application"`, and `"DjangoGraphQLView"` in
  `::test_construction_rejects_an_omitted_or_unusable_django_application`, and that test's
  docstring now enumerates all three Error-shapes facts instead of two. The re-typing
  discipline is kept — the constant is still never imported.
- The second half of the task's L1 framing ("pin that the package no longer composes a Channels
  HTTP GraphQL route") **is already covered, three ways**, so no assertion was added:
  `::test_graphql_http_consumer_left_the_router_module_entirely` (source-text absence of
  `GraphQLHTTPConsumer` in the real `routers.py`),
  `::test_http_branch_is_the_supplied_django_application_by_identity` (the `"http"` value IS the
  supplied object, and is none of the three former wrappers), and
  `::test_http_branch_delegates_every_path_to_the_supplied_application` (a GraphQL-shaped POST
  at `/graphql` reaches the stub and gets its `418`, so no package route intercepts it).

#### L3 (Low) — the backwards variable name

`default_post` -> `ide_off_post` in
`::test_graphql_ide_and_get_queries_can_be_turned_off_on_the_package_view` (three occurrences).
It posts to the probe mount; only `default_ide` hits the default one.

#### Not touched, deliberately

- **L4** — intentionally rejected by Worker 3 with a recorded reason. Row 2's
  `Referrer-Policy == "same-origin"` is unchanged.
- **L2** — three factually-wrong `auth/` production strings, escalated to Slice 5. No `auth/`
  production file is in this pass's diff.
- **D2 / D3 / D4 / D5** — verified live and closed by Worker 3 with reasons; unchanged.

### Files touched

Slice-intended, from `git status --short` (not memory) — four files, all already in pass 1's
inventory, so pass 2 adds no new path to the diff:

- `tests/test_views.py` — M1: the composed `evicted_modules` + `simulated_absence` block, the
  two preconditions, the `strawberry.channels` post-condition, the two identity assertions, the
  rewritten test docstring, and the `_ABSENCE_PREFIXES` comment now explaining why
  `strawberry.django` rides its own guard.
- `django_strawberry_framework/views.py` — M1: module-docstring paragraph corrected to the
  verified upstream import set and scoped to what the test proves. **No code change** — the
  import line, `__all__`, the Slice-2 anchor, and both class bodies are byte-identical.
- `tests/test_routers.py` — M3 (new Test 5b) and L1 (`"REMOVED"` assertion + the enumerated
  three-facts docstring).
- `examples/fakeshop/test_query/test_transport_api.py` — D1 (`_assert_no_graphql_envelope` and
  its four call sites) and L3 (`ide_off_post`).

Unchanged from pass 1 and NOT re-touched: `django_strawberry_framework/routers.py`,
`examples/fakeshop/config/urls.py`, `tests/auth/test_mutations.py`.

Baseline-dirty, untouched and not reverted: `django_strawberry_framework/filters/sets.py`,
`tests/filters/test_sets.py`, `docs/feedback.md`,
`docs/row-preserving-predicates-part1-plan.md`, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`,
`examples/fakeshop/db.sqlite3`, `drys.md`, `vulns.md`, the spec + terms CSV, the build plan.

No `.md` outside this artifact was edited. No version quintet, no `CHANGELOG.md`, no
`django_strawberry_framework/__init__.py`, no `conf.py`, no `docs/README.md` / `README.md` /
`TODAY.md` / `docs/TREE.md`.

### Tests added or updated

- **NEW** `tests/test_routers.py::test_the_websocket_pattern_is_keyword_only_with_no_legacy_url_pattern_alias`
  (Test 5b) — Decision 4's two negative contracts, message-matched.
- **STRENGTHENED** `tests/test_views.py::test_views_module_imports_with_channels_absent` — see
  M1. Now able to fail in both directions; verified by injection.
- **STRENGTHENED** `tests/test_routers.py::test_construction_rejects_an_omitted_or_unusable_django_application`
  — fourth substring `"REMOVED"`.
- **REFACTORED, assertions unchanged in strength**
  `examples/fakeshop/test_query/test_transport_api.py` rows 3, 4, 6, 7 — the same
  `b'"data"'` check, now behind one named helper with a path in its failure message.

No test was deleted, weakened, skipped, or `xfail`ed in this pass.

### Validation run

In the required order:

1. `uv run ruff format .` — **pass** (`400 files left unchanged`; the only output is the
   standing `COM812`-vs-formatter advisory warning, which is pre-existing config, not this
   diff).
2. `uv run ruff check --fix .` — **pass** (`All checks passed!`; no auto-fix applied this pass).
3. `uv run python scripts/check_trailing_commas.py <explicit paths>` — **pass**
   (`Fixed 0 file(s).`), then the same four paths with `--check` — **exit 0**. Explicit paths
   only, never repo-wide: `tests/test_views.py`, `tests/test_routers.py`,
   `examples/fakeshop/test_query/test_transport_api.py`,
   `django_strawberry_framework/views.py`. The maintainer's untracked `drys.md` / `vulns.md`
   were never on the command line and are unmodified.
4. `git status --short` — every entry classified. **Slice-intended:**
   `django_strawberry_framework/routers.py`, `examples/fakeshop/config/urls.py`,
   `tests/auth/test_mutations.py`, `tests/test_routers.py` and the three untracked new files
   (`django_strawberry_framework/views.py`, `tests/test_views.py`,
   `examples/fakeshop/test_query/test_transport_api.py`) plus this artifact. **Baseline-dirty,
   left exactly as found:** `KANBAN.html`, `KANBAN.md`,
   `django_strawberry_framework/filters/sets.py`, `docs/GLOSSARY.md`, `docs/feedback.md`,
   `docs/row-preserving-predicates-part1-plan.md`, `examples/fakeshop/db.sqlite3`,
   `tests/filters/test_sets.py`, `drys.md`, `vulns.md`, the spec + terms CSV, the build plan.
   **No unrelated tool churn was produced, so nothing was reverted** and nothing on the
   baseline-dirty list was `git checkout --`ed. Additionally verified: `git diff --check` clean;
   ASCII-only on all four touched `.py`; no physical line over 100 columns in any of them.
5. Tests (no `--cov*`; `--no-cov` only):
   - `uv run pytest tests/test_views.py tests/test_routers.py --no-cov -q` — **34 passed**
     (27 routers + 7 views; +1 vs pass 1 = the new Test 5b).
   - `uv run pytest tests/test_views.py --no-cov -q -n0` — **7 passed**.
   - `uv run pytest tests/test_routers.py --no-cov -q -n0` — **27 passed**.
   - Live tier + the sibling suites the changed surfaces reach:
     `uv run pytest examples/fakeshop/test_query/test_transport_api.py tests/auth/test_mutations.py tests/utils/test_permissions.py --no-cov -q`
     — **132 passed**.
   - `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov -q -n0` —
     **11 passed**.
   - `uv run pytest tests/auth/test_sessions.py <the two bridge tests> --no-cov -q` —
     **28 passed** (the M2 re-verification).
   - **`uv run pytest --no-cov` (the canonical full sweep, all four `testpaths`) — 4801
     passed, 40 skipped in 60.24s, ZERO failures.** Exactly pass 1's 4800 plus the one new
     test. **The M1 change produced no cross-test pollution under the full parallel run**,
     which is the re-confirmation Worker 3 required before accepting an eviction that
     re-executes a third-party package body.

Nothing failed. No pre-existing-failure claim is made in this pass: under the canonical
invocation there are no failures to attribute. The pass-1 invocation-shape artifacts
(`test_kanban_api.py::test_select_board_docs_and_lookup_roots_for_static_dashboard` and the
`examples/fakeshop/tests/` rows) were not re-chased, per the task's instruction and Worker 3's
independent confirmation that they are pre-existing and slice-independent.

### Spec slice checklist (verbatim) — boxes changed this pass

**None.** All six boxes were already `- [x]` after pass 1, and Worker 3 walked each against the
diff and found no over-tick. Re-checked after this pass's changes: every box still accurately
reflects what landed, and this pass only **strengthens** the proofs behind boxes 3
(`websocket_url_pattern`, now with the two negative contracts pinned) and 6 (`tests/test_views.py`,
now able to fail for the reason it claims). No box was newly ticked and none was un-ticked.

Box 5's second half ("every WebSocket Origin / auth test is preserved verbatim") is still not
literally true for three tests, exactly as Worker 3 escalated; that is spec wording, which only
Worker 1 may fix, and it is unchanged by this pass.

### Implementation notes

- **`evicted_modules` composed rather than a fourth prefix** (the one judgement call in this
  pass). Rationale and the measurement that forced it are under M1. It is a test-file-local
  arrangement using an existing helper twice — no change to `tests/_soft_dependency.py`, no new
  eviction machinery, and no other suite is affected.
- **Identity divergence chosen as the load-bearing assertion**, over "`strawberry.channels` not
  in `sys.modules`" alone. The absence assertion is necessary but not distinguishing (it would
  also hold if nothing re-executed); `__base__ is not __base__` is positive evidence that
  upstream's body actually ran under the sentinel, which is the property the added eviction
  buys. Both are kept.
- **Test 5b placed with the pattern tests, not folded into Test 3.** Worker 3 offered either.
  Decision 4's positive half (default pattern, custom pattern, exact-match matrix) already lives
  there, and Test 3's name and docstring are about `django_application`; a `url_pattern` row
  inside it would have made the name lie. The lettered insert keeps Test 6 onward numbered as
  committed.
- **Both M3 assertions are `match=`-qualified.** A bare `pytest.raises(TypeError)` would also
  pass if the constructor started raising `TypeError` for an unrelated reason (e.g. a future
  annotation-validation guard), which would silently stop pinning the contract.
- **`_assert_no_graphql_envelope` takes the response, not the bytes**, so it can read
  `response.request["PATH_INFO"]` for the failure message. Every one of the four call sites is a
  `django.test.Client` response, where the test client always sets `.request`.
- **No new module-level constant for the `b'"data"'` literal.** The literal now appears exactly
  once, inside the helper that names it; a separate constant would add a second name for the
  same idea.

### Notes for Worker 3

- The M1 verification probes lived in the scratchpad (not `docs/builder/temp-tests/`) and are
  gone; `git status --short` above shows no new dirt. The `import channels` injection into
  `django_strawberry_framework/views.py` was restored and confirmed with
  `shasum -a 256 -c` (**OK**) before anything else ran.
- **Please re-verify with the canonical `uv run pytest --no-cov`.** The M1 change re-executes a
  third-party package body (`strawberry.django`, its `__init__`, `views`, and `context`), so
  order-dependent pollution is the failure class to look for and it is invisible below the full
  parallel run. It is green at 4801 passed / 40 skipped here. Two facts that make the pollution
  risk small: `strawberry_django` is not installed in this venv, so `strawberry/django/__init__.py`
  re-execution just takes its `except ModuleNotFoundError` branch (no heavy re-import), and the
  composed guard restores both the `sys.modules` entry and the `strawberry.django` attribute.
- `django_strawberry_framework/views.py` is in the diff again, but the change is
  **docstring-only** — `git diff -- django_strawberry_framework/views.py` should show one prose
  hunk and no statement. The public surface is untouched, so the pass-1 public-surface verdict
  stands unchanged (`git diff -- django_strawberry_framework/__init__.py` still empty).
- No static-helper run is owed for this pass: no new `.py` file, and no production logic
  changed.

### Notes for Worker 1 (spec reconciliation)

Pass 1's items 1-7 stand as written except item 6's premise, corrected above. New or updated:

1. **Corrected premise for your Decision 2 / Decision 13 weighing (was pass-1 item 6).** The
   `tests/auth/test_mutations.py` harness repair is the only **end-to-end `HttpCommunicator`**
   coverage of the Channels-HTTP auth session lifecycle — not the only coverage of
   `Transport.CHANNELS_HTTP`, which `tests/auth/test_sessions.py` (5 sites) and the two
   non-harness `_sync_..._bridge` tests cover independently. Verification commands under M2. The
   repair is still the right call and Worker 3's verdict on it ("legitimate consumer-side
   composition") is unaffected; only the justification changes, and it no longer rests on a
   `fail_under = 100` claim.
2. **`django_strawberry_framework/views.py`'s module docstring changed prose this pass** (the
   upstream import set is now named precisely, and the `channels`-free claim is scoped to what
   the test proves). Slice 5 regenerates `docs/TREE.md` from module docstrings, so this is the
   text that will render. It carries no staging language.
3. **No spec edit is created or needed by this pass.** M1, M3, D1, L1, and L3 are all
   test/docstring strength; no Decision changed meaning, and no new contract was introduced
   that the spec does not already state (Decision 4's no-alias and keyword-only sentences are
   now pinned by a test that did not exist before, which is the spec catching up to itself, not
   the reverse).
4. **Still open from Worker 3, unchanged by this pass:** the three-test "Preserved verbatim"
   carve-out (Decision 13), the Decision 2 narrowing plus `tests/auth/test_mutations.py` in
   Decision 13's inventory, L2's three `auth/` strings (Slice 5), and the pre-existing kanban /
   export-schema order-dependence for `bld-final.md`'s deferred-work catalog.

---

## Review (Worker 3, pass 2)

Re-review of `## Build report (Worker 2, pass 2)` against the working-tree diff obtained
independently (`git status --short`, `git diff`, `git diff --stat`). Pass 2's four claimed
paths are the only paths in the diff beyond pass 1's inventory, and pass 2 added **no new
path**: `tests/test_views.py`, `tests/test_routers.py`,
`examples/fakeshop/test_query/test_transport_api.py`, and
`django_strawberry_framework/views.py`. `git status --short` is byte-for-byte the list pass 1
recorded (same slice-intended set, same baseline-dirty set, nothing new, nothing reverted);
`docs/GLOSSARY.md` still reports exactly the one concurrent row-preserving line.

**Static inspection helper: not owed this pass, skip recorded.** No new `.py` file, and no
production logic changed. I verified the "docstring-only" claim mechanically rather than on
prose: an AST dump of `django_strawberry_framework/views.py` yields exactly `Expr` (module
docstring), `ImportFrom __future__`, `ImportFrom strawberry.django.views [AsyncGraphQLView,
GraphQLView]`, `Assign __all__ = ("AsyncDjangoGraphQLView", "DjangoGraphQLView")`, and two
`ClassDef`s (`DjangoGraphQLView(GraphQLView)`, `AsyncDjangoGraphQLView(AsyncGraphQLView)`)
whose entire bodies are a single docstring `Expr` each. Zero statements of logic, zero
branches, zero calls - identical to the inventory pass 1 recorded for the same file, and the
`TODO(spec-046 Slice 2)` `#` anchor is still present and still a comment. **Caveat stated
plainly:** `views.py` is untracked, so there is no git baseline for a pass-1-vs-pass-2 byte
diff; "byte-identical apart from the docstring" is verified at AST/statement-inventory level
plus the pass-1 review's own recorded inventory and its pinned `__all__` tuple, not by a byte
diff. Same limitation applies to the tracked files' pass-1-vs-pass-2 delta, which is why the
per-file collection counts below carry the weight instead.

**Canonical full sweep, run by me:** `uv run pytest --no-cov` -> **4801 passed, 40 skipped in
58.25s, zero failures.** Byte-for-byte Worker 2's number, and exactly pass 1's 4800 + 1.

**The +1 delta is exactly the new test, measured not assumed.** Per-file `--collect-only`:
`tests/test_routers.py` **27** (pass 1: 26), `tests/test_views.py` **7** (pass 1: 7),
`examples/fakeshop/test_query/test_transport_api.py` **11** (pass 1: 11) - 45 vs pass 1's 44,
with the single increment isolated to `tests/test_routers.py`. Its 20 test functions were
enumerated and every one is accounted for in pass 1's inventory plus the one new Test 5b, so
the +1 is an addition and not a delete-plus-two-adds netting to +1. No test was deleted,
skipped, or `xfail`ed.

**Hygiene re-verified independently, explicit paths only** (never repo-wide - the maintainer's
untracked `drys.md` / `vulns.md` were never on a command line): `ruff format --check` -> `4
files already formatted`; `ruff check` -> `All checks passed!`;
`scripts/check_trailing_commas.py --check <4 explicit paths>` -> exit 0; `git diff --check` ->
clean; ASCII-only and no line over 100 columns in all four touched files (scanned
programmatically, not by eye).

### Per-finding verdicts

**M1 - CLOSED, and the fix is proven to earn its keep.** Three independent verifications.

1. *The `parent`/`attr` claim is real.* Read `tests/_soft_dependency.py::evicted_modules`: the
   two-sided restore is `saved_attr = vars(parent).get(attr, missing)` on entry and
   `vars(parent).pop` / `setattr(parent, attr, saved_attr)` on exit, with every read and write
   through `__dict__` so a package `__getattr__` never fires - citing spec-041 D3 for exactly
   the "attribute path and import path point at one module object" property Worker 2 invoked.
   Then measured it rather than inferring it (temp probe, both variants in one process):
   after a **bare** fourth prefix under the framework-aimed guard,
   `vars(strawberry)["django"] is sys.modules["strawberry.django"]` -> **False**; under the
   shipped **composed** shape -> **True**. (Worker 2's table also reported the `.views` line
   as False under BARE where I measure True; that is the same divergence read from a
   different starting object - Worker 2 walked the *rebound* attribute's `.views`, I walked
   the *restored* `sys.modules` entry's. No substantive discrepancy.) So the deviation from
   my literal one-line pass-1 recommendation is justified, not a dodge.
2. *The test genuinely fails if `views.py` grows a channels-reaching import - reproduced by
   me.* Injected `import channels` after the `strawberry.django.views` import line in
   `django_strawberry_framework/views.py`, ran
   `tests/test_views.py::test_views_module_imports_with_channels_absent --no-cov -q -n0` ->
   **1 failed**, `ModuleNotFoundError: import of channels halted; None in sys.modules` at
   `django_strawberry_framework/views.py:43`. Restored from a pre-injection copy and verified:
   `shasum -a 256 -c` -> `django_strawberry_framework/views.py: OK`
   (`c2b128874863e36b27ea420176a8eb2deafe620d3819a0d839e1b797e93f6d40`), `grep -c PROBE` -> 0,
   size back to 3523 bytes.
3. *The added eviction closes the exact hole pass 1 named, proven by the case pass 1 said the
   old test could not see.* My pass-1 M1 was "the test would stay green if
   `strawberry.django.views` grew a `channels` import tomorrow". So I injected
   `import channels` into
   `.venv/lib/python3.14/site-packages/strawberry/django/views.py` and ran both shapes under
   that one injection: the **shipped** test **FAILED**
   (`ModuleNotFoundError ... strawberry/django/views.py:5`), while a temp mirror carrying
   **pass 1's** prefix tuple **PASSED**. That is the finding, closed, demonstrated rather than
   asserted. Upstream restored and verified: `shasum -a 256 -c` ->
   `.venv/.../strawberry/django/views.py: OK`
   (`399d70ab4e6c223c8ff937113537a4d43fb86fc0355e2bbc7207b70315b6b736`), `grep -c PROBE` -> 0,
   and `tests/test_views.py` re-run clean at **7 passed**.

   The two identity assertions are the right load-bearing shape: `module.DjangoGraphQLView is
   not DjangoGraphQLView` fails if the package body did not re-execute, and
   `.__base__ is not .__base__` fails if upstream's did not - which is precisely the assertion
   the added eviction buys, and precisely what the mirror could not carry.

   **Docstrings now claim only what the assertions earn** - checked clause by clause.
   `views.py`'s "``strawberry.django.views`` reaches only for the standard library,
   ``asgiref``, ``cross_web``, ``django``, ``strawberry.http``, and its own
   ``strawberry.django.context`` sibling" is exactly that module's AST import set (`json`,
   `typing`, `collections.abc`, `asgiref.sync`, `cross_web`, five `django.*`, three
   `strawberry.http.*`, `.context`) - I enumerated it rather than trusting the prose. The
   test docstring names the re-executing set (`views.py`, upstream `views`, plus that
   package's `__init__` and `context`) and explicitly scopes out what stays cached
   *below* the boundary (`strawberry.http`, `cross_web`, `django`) as upstream's own
   contract. Neither now claims a whole-graph proof. See L5 for the one residual clause.

**M2 - CLOSED; the corrected claim is accurate.** The operative sentence is now "the 8 harness
tests are the only end-to-end `HttpCommunicator` coverage of the Channels-HTTP auth session
lifecycle". Verified as a repo-wide negative, not spot-checked: `grep -rn HttpCommunicator`
across `tests/` and `examples/` returns hits in exactly two files - `tests/test_routers.py`
(whose subject after this slice is router *delegation*, not an auth session) and
`tests/auth/test_mutations.py`. Inside the latter, `_channels_router(_auth_router_schema())`
appears at exactly **8** call sites, which I mapped to their enclosing test names: five
`::test_channels_http_login_*` / `::test_channels_http_relogin_*`, two
`::test_channels_http_*logout*`, and `::test_websocket_server_side_logout_invalidates_and_survives_reconnect`
- the eighth mints its cookie through the same `HttpCommunicator` helper (`_ch_post`, line
1503) before opening the socket, so "all 8 are `HttpCommunicator` round trips" holds, with the
nuance that the eighth's *subject* is the WebSocket half. The withdrawn half is genuinely
withdrawn: no `fail_under = 100` justification survives, and pass 1's independently-covered
surfaces re-check out (`tests/auth/test_sessions.py` carries `Transport.CHANNELS_HTTP` at 5
sites; the two `_sync_..._bridge` tests drive both `mutations.py` arms with no harness).
One scope note under `### Notes for Worker 1`.

**M3 - CLOSED, and both assertions pin real behavior; I mutated the constructor to prove it.**
Read `_router` first, because a `match=`-qualified raise can be satisfied by the harness rather
than the contract: `_router(**kwargs)` only `setdefault`s `django_application` and forwards, so
`url_pattern=` reaches the real `__init__`. Then two mutations of
`django_strawberry_framework/routers.py`, each run against the new test alone:

- reintroduced a `url_pattern: str | None = None` alias that assigns through to
  `websocket_url_pattern` -> `Failed: DID NOT RAISE <class 'TypeError'>` at the
  `match="url_pattern"` row. So the assertion pins the absence of the alias, not an incidental
  `TypeError`.
- deleted the `*` keyword-only boundary -> `Failed: DID NOT RAISE <class 'TypeError'>` at the
  `match="positional"` row.

Restored from a pre-mutation copy and verified: `shasum -a 256 -c` ->
`django_strawberry_framework/routers.py: OK`
(`61251f8c994b914f3978c429034b1cf86cb98a6ad59ec11fb24661a4503deb4e`), and
`grep -c "url_pattern: str | None"` -> 0. Test 5b is a real Slice-4 tripwire. Placement beside
the pattern tests (rather than folded into Test 3) is the better call for the reason Worker 2
gives: Test 3's name is about `django_application`.

**D1 - CLOSED, all four converted, none missed.** `_assert_no_graphql_envelope` is called at
rows 3 (host rejection), 4 (both CSRF rejection colours, inside the `else` arm), 6 (inside the
loop, so **both** prefix-extension paths), and 7 (the GET-query refusal). `b'"data"'` now
appears **exactly once** in the file, inside the helper. Row 6's hand-written `, unmatched`
label survives on its status assertion and the path is now automatic at all four sites.
One thing worth checking that a green suite cannot: the assertion *message*
`response.request["PATH_INFO"]` only evaluates on failure, so a bad expression there would
mask a real regression as a `KeyError`. Probed it against all four response shapes (400 host
rejection, 404 URL miss, 403 CSRF rejection, GET-query refusal) - `.request` is present and
subscriptable on every one, so a regression surfaces as an `AssertionError` naming the path.

**L1 - CLOSED.** `assert "REMOVED" in message` sits alongside `"ALLOWED_HOSTS"`,
`"get_asgi_application"`, and `"DjangoGraphQLView"` in
`::test_construction_rejects_an_omitted_or_unusable_django_application`, the docstring now
enumerates all three Error-shapes facts, `_MISSING_DJANGO_APPLICATION_HINT` really does carry
"That mode is REMOVED, not flagged.", and the re-typing discipline is intact (the constant is
still never imported).

**L3 - CLOSED.** `default_post` -> `ide_off_post`: 0 occurrences of the old name, 3 of the new.

**L4 - correctly NOT "fixed".**
`::test_security_middleware_headers_ride_the_graphql_response` still asserts
`response.headers["Referrer-Policy"] == "same-origin"` by exact value, as I rejected it.

**L2 - correctly untouched and still escalated.** No `django_strawberry_framework/auth/`
production file is in the diff (`git diff --name-only | grep django_strawberry_framework/auth`
-> empty; the only `auth`-shaped path is the *test* file `tests/auth/test_mutations.py`, which
pass 2 did not re-touch).

### High:

None. No correctness bug, no spec-contract violation, no unauthorized API break, no security
or data-isolation regression, and no crashed consumer path. Pass 2 changed no production
statement at all - only one module-docstring paragraph and three test files.

### Medium:

None. Every pass-1 Medium (M1, M2, M3) is closed and independently verified above, M1 by
mutation in both the package file and the upstream file, M3 by mutation of the constructor in
both directions.

### Low:

#### L5 - the eviction's blast radius now includes upstream's OPTIONAL `strawberry_django` re-export, which no docstring names (recorded, no change required)

Adding `strawberry.django` to the eviction means the re-executing set includes
`.venv/.../strawberry/django/__init__.py`, whose body is
`try: from strawberry_django import *  / except ModuleNotFoundError: <lazy __getattr__>`. That
conditional third-party reach is not named by either docstring, and it makes the assertion's
meaning environment-dependent in a way pass 1's shape was not.

**Intentionally rejected as a change request**, because I traced it to benign in every
configuration that exists rather than assuming either way:

- `strawberry-graphql-django` is not in `pyproject.toml` and not in `uv.lock`; it is not
  installed in this venv, so `__init__` takes its `except ModuleNotFoundError` arm and the
  re-execution is exactly the set the docstrings name.
- Even *with* it installed, the reach stays graceful: in the maintainer's sibling checkout
  (`~/projects/strawberry-django-main`), `strawberry_django/__init__.py` reaches `channels`
  only through `auth/mutations.py`, whose import is itself
  `try: from channels import auth / except ModuleNotFoundError`. The `sys.modules[name] = None`
  sentinel raises `ModuleNotFoundError` on this interpreter (observed in both of my injection
  runs), so that guard absorbs it. The one module-level `from channels...` in
  `strawberry_django/routers.py` is not reached by `__init__`.

So the test would not start failing spuriously, and `views.py`'s scoped claim about
`strawberry.django.views`' own import set is accurate as written. Recording it so the next
person who sees a mystery `channels` failure in a venv with `strawberry-graphql-django`
installed has the trail. If Worker 1 wants the belt-and-braces version, one clause in the test
docstring ("plus, when installed, the optional `strawberry_django` namespace re-export
`strawberry.django.__init__` attempts") is the whole fix. No code change.

### DRY findings

- **D1 closed** (verified above): four implicit byte-literal searches -> one named helper, the
  literal now stated once, the failure message strictly better at all four sites and proven
  safe to evaluate. No new constant was added for `b'"data"'`, correctly - a second name for
  the same idea would be the DRY defect.
- **No new duplication introduced by pass 2.** The composed guard reuses
  `tests/_soft_dependency.py` twice with no edit to that module and no new eviction machinery;
  Test 5b adds no helper and reuses `_router` / `_router_class` / `_RecordingDjangoApplication`;
  `ide_off_post` is a rename. The two channels-asymmetry explanations (production module
  docstring vs test docstring) are not a near-copy - one states the contract, the other states
  the proof's boundary, and they carry different content.
- **D2 / D3 / D4 / D5** unchanged from pass 1 (verified live there, closed with reasons).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **0 lines**, empty. `routers.py`
`__all__` is unchanged at `("DjangoGraphQLProtocolRouter",)` with its PEP 562 `noqa: F822`
comment intact; `views.py` `__all__` is unchanged at
`("AsyncDjangoGraphQLView", "DjangoGraphQLView")` (AST-verified, and
`::test_module_exports_exactly_the_two_view_classes_and_stays_off_the_package_root` pins it as
a standing assertion). Pass 2 introduced **no** new public symbol and **no** signature change -
its only production edit is prose inside a docstring - so the pass-1 verdict measured against
**spec Decision 5** (exactly the three authorized breaks: required `django_application`,
`url_pattern` -> keyword-only `websocket_url_pattern`, GraphQL HTTP now needs a `urlpatterns`
entry) stands unchanged. **Verdict: clean.**

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`. Re-confirmed for pass 2:
`git diff --name-only -- CHANGELOG.md` -> empty.

### Documentation / release sanity

Not applicable; pass 2 modified no docs / release / KANBAN / archive surface. Verified rather
than inferred: no `.md` outside this artifact is in the diff, and
`git diff --name-only -- docs/README.md README.md TODAY.md docs/TREE.md CHANGELOG.md
pyproject.toml uv.lock tests/base/test_init.py` -> empty, so the version quintet stays unmoved
(spec Decision 15, build-plan joint-cut flag).

One forward-facing check, since Slice 5 regenerates `docs/TREE.md` from module docstrings and
pass 2 rewrote one: `views.py`'s module docstring carries **no staging language** - programmatic
scan for `planned`, `Slice`, `TODO(`, `coming soon`, `will be`, `future` returns all False. Its
`spec-046 Decision 6` mention is a provenance citation (keep, per `AGENTS.md`), and the
`TODO(spec-046 Slice 2)` anchor is a `#` comment outside the docstring, so it will not render.

### What looks solid

- **The M1 repair is stronger than what I asked for, and the deviation is disclosed rather
  than buried.** I recommended a fourth bare prefix; Worker 2 measured that shape leaving the
  attribute path diverged from `sys.modules`, chose the composed two-sided guard instead, and
  recorded the measurement and the deviation in its own report. I reproduced the measurement
  and it holds. That is the right way to decline a reviewer's literal instruction.
- **The failability proof is real in both directions, and I did not have to take it on trust** -
  the injection reproduces at `views.py` *and*, more tellingly, at the upstream module that was
  the actual content of the finding, where the pass-1 shape stays green under the same
  injection.
- **Both M3 assertions are `match=`-qualified for the stated reason**, and the reason is
  correct: a bare `pytest.raises(TypeError)` would keep passing if the constructor started
  raising `TypeError` for an unrelated future guard, silently retiring the contract.
- **The pass-2 edits are the smallest ones that close the findings.** Zero production
  statements changed; the diff is one docstring paragraph, one new test, one added substring
  assertion, one extracted assertion helper, and one variable rename. Nothing was refactored
  in passing, and no finding was closed by weakening an assertion.
- **Every pass-1 rejection and escalation was respected exactly** - L4 untouched, L2 left for
  Slice 5 with no `auth/` production file in the diff, D2-D5 unchanged.
- **The full-parallel re-confirmation I required was actually run and is green**, which is the
  order-dependence check that matters for an eviction that re-executes a third-party package
  body. I re-ran it myself: 4801 / 40, zero failures. Worker 2's two mitigating facts check
  out (`strawberry_django` absent, so `strawberry/django/__init__.py` re-execution takes the
  cheap `except` arm; the composed guard restores both sides).
- **Checklist boxes: none changed state, none over-ticked.** All six remain `- [x]` exactly as
  pass 1 walked them; no box was newly ticked and none un-ticked. Pass 2 only strengthens the
  proofs behind boxes 3 (`websocket_url_pattern`, now with both negative contracts pinned) and
  6 (`tests/test_views.py`, now able to fail for the reason it claims). Box 5's second half
  remains literally untrue for three tests - spec wording, still escalated, unchanged.
- **Prior-entry integrity: intact.** `## Build report (Worker 2, pass 2)` is appended at the
  same top level after a `---` separator; Worker 1's plan (including the verbatim spec
  checklist) and my `## Review (Worker 3)` are unedited - the pass-1 section still carries all
  six findings in their original severities, my `revision-needed` outcome, and my rejection of
  L4. The top-level `Status:` was correctly moved to `built` by Worker 2 and nothing else in
  the header changed.

### Temp test verification

Three files created under `docs/builder/temp-tests/slice-1/` and **all deleted after the runs**
(directory left empty, `__pycache__` removed; `git status --short` re-confirmed byte-identical
to the pre-review state - no new dirt):

- `test_pass1_shape_mirror.py` - pass 1's prefix tuple replayed verbatim, run against an
  upstream `import channels` injection to show it stays green where the shipped test fails.
  **Disposition: deleted.** Its value was proving M1's fix earns its keep; the permanent test
  now carries that coverage and a mirror of a superseded shape must not be kept.
- `test_parent_attr_claim.py` - measured the BARE-vs-COMPOSED `vars(strawberry)["django"]`
  divergence in one process. **Disposition: deleted.** It verifies a property of
  `tests/_soft_dependency.py` that spec-041 D3 already owns and
  `tests/test_routers.py::test_restore_is_two_sided_and_the_present_path_works_again` already
  pins for the guard's own suite; nothing to promote.
- `test_failure_message_path.py` - confirmed `response.request["PATH_INFO"]` is readable on all
  four boundary response shapes, so D1's assertion message cannot mask a real failure.
  **Disposition: deleted, no promotion.** It found no bug, and a test whose only subject is
  another test's failure-message expression would be noise in the permanent suite.

No temp test caught a behavior bug, so nothing needs promotion.

### Notes for Worker 1 (spec reconciliation)

- **Pass 1's escalations all stand, unchanged by pass 2** and still needing Worker 1's decision:
  (a) Decision 13's "Preserved verbatim" list needs the third category and covers **three**
  tests, not two (the third being
  `::test_websocket_branch_wraps_origin_validator_outside_the_auth_stack`, whose pattern
  literal necessarily tracks Decision 4's new default); (b) Decision 2's "the Channels request
  adapter is now a WebSocket-only shape" should be narrowed to the package's own composition,
  and `tests/auth/test_mutations.py` added to Decision 13's inventory; (c) L2's three
  factually-wrong `auth/` production strings -> Slice 5's transport-wording pass; (d) the
  pre-existing kanban / export-schema order-dependence -> `bld-final.md`'s deferred-work
  catalog.
- **You may now rely on the corrected M2 premise; I verified it independently.** The
  `tests/auth/test_mutations.py` harness repair protects the only end-to-end
  `HttpCommunicator` coverage of the Channels-HTTP auth session lifecycle
  (`grep -rn HttpCommunicator` over both test trees hits only `tests/test_routers.py` and that
  file; 8 `_channels_router` call sites, mapped to names). It is **not** the only coverage of
  `Transport.CHANNELS_HTTP`. My pass-1 verdict on the repair ("legitimate consumer-side
  composition, not a contract contradiction") is unaffected.
  - *One scope note, not a finding.* The correction's trailing clause - "deleting them would
    not by itself drop the package below `fail_under = 100`" - is an unverifiable negative for
    a worker, since no worker may run `--cov`. It **weakens** the prior justification rather
    than strengthening it, no decision hangs on it, and nobody is deleting the tests, so it is
    harmless as recorded. Do not build a spec edit on that clause specifically; the
    grep-verified only-`HttpCommunicator`-coverage claim is the durable one.
- **L5 (Low, rejected with reason) if you want it closed by wording rather than left as a
  trail:** one clause in `tests/test_views.py::test_views_module_imports_with_channels_absent`'s
  docstring naming upstream's optional `strawberry_django` re-export. Proven benign in every
  configuration that exists today; details under `### Low:`.
- **`views.py`'s module docstring is the text Slice 5 renders into `docs/TREE.md`.** It is
  staging-language-free (scanned) and now names the verified upstream import set, so Slice 5
  needs no docstring scrub for this file.

### Review outcome

`review-accepted`.

Every pass-1 finding is now closed or intentionally rejected with a recorded reason: **M1**
closed and proven failable by injection in both the package file and the upstream module (with
the pass-1 shape shown green under the same injection), **M2** closed and the corrected claim
independently verified as a repo-wide negative, **M3** closed and both assertions proven to
fail under the exact mutations they guard, **D1 / L1 / L3** closed and verified,
**L4** correctly left alone, **L2** correctly still escalated with no `auth/` production file in
the diff. One new **L5** is recorded and intentionally rejected with the trace that shows it
benign. No High or Medium remains, nothing is escalated to Worker 1 above Low severity beyond
pass 1's existing spec-wording items, the canonical sweep is green at **4801 passed / 40
skipped** with the delta measured to be exactly the one new test, hygiene is clean on explicit
paths, the checklist boxes are unchanged and un-over-ticked, and prior artifact entries are
unedited.

What convinced me, specifically: pass 2 closed a test-strength finding by making the test fail
in the exact scenario the finding named, and I could reproduce that failure - and the
complementary pass of the superseded shape - myself, with both injected files restored and
checksum-verified. Everything else in the pass was the smallest edit that closed its finding,
with zero production statements changed.

---

## Final verification (Worker 1)

Read end-to-end before acting: the plan, both Worker 2 build reports, both Worker 3
reviews, `docs/spec-046-transport_security-0_0_15.md`, the build plan, `CHANGELOG.md`
(read-only, unedited), and `docs/builder/worker-memory/worker-1.md`. The working-tree diff
was obtained independently (`git status --short`, `git diff`, `git diff --stat`) and is
exactly the seven paths the reports claim -- `django_strawberry_framework/views.py` (new),
`django_strawberry_framework/routers.py`, `examples/fakeshop/config/urls.py`,
`tests/test_routers.py`, `tests/test_views.py` (new),
`examples/fakeshop/test_query/test_transport_api.py` (new), `tests/auth/test_mutations.py`
-- plus this artifact and the spec I edit below. Every other dirty path is on the build
plan's baseline-dirty list and was neither edited nor reverted.

### Spec slice checklist audit (box by box, against the diff)

I am the auditor here, not the ticker. All six boxes were `- [x]`; each is confirmed
against the diff, and **no box was un-ticked or newly ticked**.

- **Box 1** (HTTP branch is the consumer-supplied Django ASGI application directly -- no
  `URLRouter`, no `GraphQLHTTPConsumer`, no `AuthMiddlewareStack` on HTTP) -- **LANDED.**
  `routers.py::DjangoGraphQLProtocolRouter.__init__` maps `"http": django_application`
  with no wrapper; the `http_urls` list and the `re_path(r"^", ...)` append are gone.
  Verified myself: `grep -c GraphQLHTTPConsumer django_strawberry_framework/routers.py` ->
  **0**, and the `strawberry.channels` import is now `GraphQLWSConsumer` alone.
- **Box 2** (`django_application` required; `None` / non-callable -> `ConfigurationError`
  naming the migration) -- **LANDED.** No default on the parameter, so omission is
  Python's own `TypeError`; `if not callable(django_application)` raises
  `ConfigurationError(_MISSING_DJANGO_APPLICATION_HINT)`, and the hint carries all three
  Error-shapes facts (`ALLOWED_HOSTS` / CSRF / headers, "REMOVED, not flagged",
  `get_asgi_application` + `DjangoGraphQLView`) -- all four re-typed in the test.
- **Box 3** (`url_pattern` -> `websocket_url_pattern`, default `r"^graphql/?$"`, exact,
  both-ends anchored) -- **LANDED**, keyword-only, with a five-case behavioral
  connect/reject matrix plus Test 5b pinning the two negative contracts (no alias,
  keyword-only).
- **Box 4** (new `views.py`: `DjangoGraphQLView` / `AsyncDjangoGraphQLView`, declared in
  the consumer's URLconf) -- **LANDED.** I read the file: module docstring, one import,
  `__all__`, one `#` anchor, two docstring-only subclasses. Actually mounted in
  `examples/fakeshop/config/urls.py`.
- **Box 5** (the HTTP-branch tests rewritten; every WebSocket Origin / auth test
  preserved) -- **LANDED**, and I proved the preservation half **mechanically** rather than
  on prose (`worker-1.md` #"Verifying relocated / promoted / unchanged claims"). An
  `ast.unparse` per-function diff of `tests/test_routers.py` against
  `git show HEAD:tests/test_routers.py`:

  | preserved test | changed AST lines |
  |---|---|
  | `::test_repeated_access_returns_the_cached_class_which_is_subclassable` | **0** |
  | the whole eviction / degraded-install block (6 tests) | **0** each |
  | `::test_websocket_handshake_origin_directions` | 2 -- construction line only |
  | `::test_websocket_branch_wraps_origin_validator_outside_the_auth_stack` | 4 -- construction line + the pattern literal |
  | `::test_request_contract_resolves_over_the_websocket_branch` | 10 -- construction line + docstring |

  No assertion changed in any of them except the pattern literal Decision 4 compels. The
  docstring delta on the third is a **fourth** deviation from "verbatim" that no prior pass
  named; I found it in this audit and folded it into the spec edit rather than leaving the
  spec over-claiming (see spec change 3).
- **Box 6** (`tests/test_views.py` + a live tier proving Django middleware,
  `ALLOWED_HOSTS`, CSRF, security headers, cache policy, and exact routing on the GraphQL
  HTTP route) -- **LANDED.** All six named surfaces have a live row
  (`::test_project_middleware_executes_on_the_graphql_http_route`,
  `::test_a_hostile_host_header_is_rejected_before_the_schema_runs`,
  `::test_csrf_is_enforced_on_a_cookie_authenticated_graphql_mutation`,
  `::test_security_middleware_headers_ride_the_graphql_response`,
  `::test_an_authenticated_get_varies_on_cookie`,
  `::test_routing_policy_is_djangos_urlconf_not_the_routers`), and `tests/test_views.py`
  holds exactly the five package-tier contracts a live request cannot express.

**No `- [ ]` remains, so no deferral reason is owed.** Two spec-side reconciliations that
touch the checklist's own text are recorded under `### Spec changes made (Worker 1 only)`.

### DRY check

No prior accepted slices exist, so this is a within-slice check. **Verdict: clean, no new
duplication.** Independently re-derived rather than inherited from the review:

- `scripts/review_inspect.py` on `routers.py` post-slice: one repeated literal
  (`DjangoGraphQLProtocolRouter`, 2x -- two distinct actionable hint messages). Not a
  defect.
- `tests/test_views.py`: repeated literals are all module *names* used both in an eviction
  prefix tuple and in a `sys.modules` assertion. Collapsing them into one constant would
  make the assertion compare a constant with itself -- the exact anti-pattern
  `tests/test_routers.py` #"importing the router constants and asserting them against
  themselves could never catch the hint drifting" warns about. No finding.
- `test_transport_api.py`: `/graphql/` 6x and `text/html` 4x. Inspected every site -- they
  split between *request* inputs (`_post`'s default, `HTTP_ACCEPT=`) and *response*
  assertions (`_MIDDLEWARE_PATHS == ["/graphql/"]`, `Location`, `Content-Type`). A shared
  constant would couple the request to its own assertion. No finding. `b'"data"'` now
  appears once, inside `_assert_no_graphql_envelope` (D1, closed).
- The `r"^graphql/?$"` literal lives at exactly three sites:
  `routers.py::DjangoGraphQLProtocolRouter.__init__` (the default),
  `tests/test_routers.py` (a re-typed assertion, deliberately), and
  `tests/auth/test_mutations.py::_channels_router` (D2, rejected with reason -- sourcing it
  from the router would re-couple the auth harness to the transport this card decoupled).
  I agree with the rejection.
- The `tests/auth/test_mutations.py` repair is **body-only**, verified in the diff: a
  single hunk entirely inside `_channels_router`; all eight call sites and every assertion
  are untouched.

### Existing tests still pass

`uv run pytest tests/test_routers.py tests/test_views.py tests/auth/test_mutations.py tests/utils/test_permissions.py examples/fakeshop/test_query/test_transport_api.py examples/fakeshop/tests/ --no-cov -q`
-> **183 passed**, zero failures (8 workers, 19.06s). No `--cov*` flag was used anywhere in
this pass.

The canonical full sweep was measured independently by Worker 2 (pass 2) and Worker 3
(pass 2) at **4801 passed, 40 skipped, zero failures** -- pass 1's 4800 plus the one new
Test 5b, with the +1 delta isolated by per-file `--collect-only`. I cite theirs rather than
re-running it; the build's own final test-run gate (`bld-final.md`) re-runs it as the
backstop.

### Staged-anchor check

`django_strawberry_framework/views.py` carries one `TODO(spec-046 Slice 2)` anchor. That is
a **correctly staged** anchor for a not-yet-shipped slice and must survive until Slice 2
ships the body cap; it is not an undischarged obligation for this slice. No anchor naming
Slice 1 exists anywhere in the tree.

### `views.py` docstring staging-language verdict

**Clean.** Scanned the module docstring and both class docstrings via `ast.get_docstring`
for `planned`, `Slice`, `TODO(`, `coming soon`, `not yet`, `will be`, `future`, `unbuilt`
-> **zero hits in all three**. The `spec-046 Decision 6` mention is a provenance citation
(`AGENTS.md` keeps those). The `TODO(spec-046 Slice 2)` anchor is a `#` comment *outside*
every docstring, confirmed by regex, so `scripts/build_tree_md.py` will not render it.
**Slice 5 needs no docstring scrub for this file, and must not delete the anchor.**

### L2 routing (three now-wrong `auth/` production strings)

**Routed to Slice 5, contractually** -- not merely noted. I added a Slice-5 checklist
sub-bullet naming all three sites, so Slice 5's planning pass inherits them as a contract
item instead of discovering them in `bld-final.md`'s catalog (spec change 5). Verified each
string in the source rather than trusting the escalation:

- `auth/sessions.py::classify_transport` #"Route GraphQL through
  DjangoGraphQLProtocolRouter so the scope carries a" -- reachable only for an
  unrecognized `scope["type"]`; the router now produces no GraphQL `http` scope at all.
- `auth/mutations.py::_login_resolve_body` and `::_logout_resolve_body`, both #"the package
  router's async consumer instead awaits the native async body" -- the package router has
  no HTTP consumer of either colour.

All three are prose, none load-bearing, none in this slice's named files. **They also
belong in `bld-final.md`'s `### Deferred work catalog`** if Slice 5 has not closed them by
then.

### Also carried to `bld-final.md`'s deferred-work catalog

- The **pre-existing kanban / export-schema order-dependence** in committed example tests
  (`test_kanban_api.py::test_select_board_docs_and_lookup_roots_for_static_dashboard` plus
  four `test_export_schema.py` rows and `test_urls.py::test_index_view_renders_dev_links`).
  Independently confirmed by Worker 3 to reproduce with this slice's new file excluded, and
  by Worker 2 to reproduce with HEAD's `config/urls.py`. Committed-and-clean files outside
  this build's contract; the canonical sweep is green. Not this slice's to fix.
- **L5** (Worker 3, Low, rejected with reason): the eviction's blast radius includes
  upstream's optional `strawberry_django` re-export. I reviewed the trace and **agree with
  the rejection** -- the package is absent from `pyproject.toml` and `uv.lock`, and even
  installed its `channels` reach is itself `try`/`except ModuleNotFoundError`. No spec edit
  and no docstring clause; the trail is recorded in the artifact, which is what a Low of
  this shape warrants.

### Summary

Slice 1 delivers the S1 protocol split end-to-end. `routers.py`'s `"http"` key is now the
consumer's Django ASGI application verbatim -- no `URLRouter`, no `AuthMiddlewareStack`, no
`GraphQLHTTPConsumer` anywhere in the module -- so GraphQL HTTP traverses the project's
real `MIDDLEWARE`; `django_application` is a required parameter whose omission is a
`TypeError` and whose `None` / non-callable value is a `ConfigurationError` naming the
two-place migration; `url_pattern` is renamed, narrowed, and made keyword-only as
`websocket_url_pattern` with the exact both-ends-anchored default `r"^graphql/?$"`; and a
new `channels`-free `django_strawberry_framework/views.py` ships `DjangoGraphQLView` /
`AsyncDjangoGraphQLView` as leaf-module imports, mounted in fakeshop so every S1 proof --
project middleware, `ALLOWED_HOSTS`, CSRF, security headers, `Vary: Cookie`, and exact
routing -- is earned over a real `/graphql/` request. The public surface breaks exactly the
three things spec Decision 5 authorizes and nothing else; `django_strawberry_framework/__init__.py`
is not in the diff. Two review passes closed three Mediums, three Lows, and one DRY finding
without weakening a single assertion, and the M1 fix was proven failable by injection at
both the package module and the upstream module. No version quintet movement, no
`CHANGELOG.md` edit, no `.md` outside this artifact and the spec.

The one thing this slice does that its checklist did not name -- swapping fakeshop's
`/graphql/` mount to the package view -- was the right call and is now named by the spec.
Without it the live tier would have proved *upstream's* view while `views.py` carried no
live coverage at all.

**Final status: `final-accepted`.**

### Spec changes made (Worker 1 only)

Six edits to `docs/spec-046-transport_security-0_0_15.md`, all triggered by Slice 1. The
glossary checker passes after every one:
`uv run python scripts/check_spec_glossary.py --spec docs/spec-046-transport_security-0_0_15.md`
-> **`OK: 37 terms - all have glossary entries and at least one spec link.` (exit 0)**. No
new glossary term was introduced, so `-terms.csv` is unchanged (still untracked-as-authored,
not in the diff). All 17 in-page anchors were re-verified to resolve to real headings, and
`git diff --check` is clean. **Decision 15 and the version-boundary preamble were not
touched.**

1. **Status line (line 37).** `Status: **PLANNED — no slice built yet.**` ->
   `Status: **IN BUILD — Slice 1 (S1) is built and accepted; Slices 2-5 remain.**` --
   required by `worker-1.md` #"Spec status-line re-verification"; the header would
   otherwise describe a built slice as unbuilt for the rest of the cycle.

2. **Slice-1 checklist, new sub-bullet (lines 129-134):** `examples/fakeshop/config/urls.py`
   swapping its `/graphql/` mount to `DjangoGraphQLView`, citing Decision 6 reason (c). --
   **Reconciliation item 4, decided: the checklist should name it.** The slice cannot
   deliver its own live-tier bullet without the swap (otherwise the live tier proves
   upstream's view and `views.py` has zero live coverage), 500+ live tests now traverse the
   package view, and a reviewer reading only the spec would have seen an unlisted
   production-adjacent file change. **Consequence recorded explicitly:** the spec's Slice-1
   block now has **seven** sub-bullets while this artifact's `### Spec slice checklist
   (verbatim)` block carries the **six** copied at planning time. That block is left
   untouched on purpose -- it is the audited historical record of what Worker 2 ticked and
   what I just verified. The seventh box's contract **did land and is verified** (the
   `config/urls.py` diff plus
   `::test_the_package_view_serves_an_ordinary_graphql_response` guarding it), so it would
   read `- [x]`; nothing is deferred and nothing is silently un-ticked.

3. **Slice-1 checklist, fifth sub-bullet reworded (lines 135-139)** and **Decision 13's
   "Preserved verbatim" section restructured (lines 1134-1195).** -- **Reconciliation items
   1 and 3, decided: amend.** The checklist's "the three HTTP-branch tests" is now "the
   five ... (three rewritten, two merged into one)", matching Decision 13, which governs
   (item 3, cosmetic miscount, resolved in the checklist's favour of the Decision). Its
   "preserved verbatim" is now "preserved in subject and assertion strength". Decision 13
   gains the third category the planning pass proposed, and it covers **four** mechanical
   deviations rather than the two the plan named or the three Worker 3 found -- the fourth
   being the docstring refresh on
   `::test_request_contract_resolves_over_the_websocket_branch`, which I found in this
   pass's AST diff. The new shape is: *Preserved verbatim* (the eviction block and the
   cached-class test -- measured at 0 changed AST lines, the only literal survivors);
   *Preserved in subject and assertion strength* with the three numbered reasons
   (construction line, re-aimed transport, the Decision-4-compelled pattern literal);
   *Repaired harness*; and *Deleted*. Reason: the old text was not achievable, and a spec
   that claims a preservation the diff cannot deliver trains reviewers to discount it.

4. **Decision 2 narrowed, with a new "What this does not remove" paragraph (lines 637-657).**
   -- **Reconciliation item 2, decided: narrow it.** "the Channels request adapter is now a
   WebSocket-only shape" now reads "is a WebSocket-only shape **in the package's own
   composition**", and the new paragraph states that
   `auth/sessions.py::Transport.CHANNELS_HTTP`, `::classify_transport`'s
   `scope["type"] == "http"` arm, and both `auth/mutations.py` resolve-body branches all
   survive, so a consumer-mounted `GraphQLHTTPConsumer` is still classified and served.
   **Verified in the source, not inherited:** `sessions.py:78` / `:111` and
   `mutations.py:611` / `:639`. This is also the premise the Slice-1 deletion of the HTTP
   request-adapter test rests on, so both Decisions now say the same thing.
   `tests/auth/test_mutations.py` is named in Decision 13's inventory (edit 3's *Repaired
   harness* paragraph) on exactly that basis. **The corrected premise is what I relied on:**
   those eight tests are the only end-to-end `HttpCommunicator` coverage of the
   Channels-HTTP auth session lifecycle -- **not** the only coverage of the enum member,
   which `tests/auth/test_sessions.py` and the two non-harness sync-bridge tests carry.
   Worker 2's original `fail_under = 100` justification is withdrawn and is deliberately
   **not** load-bearing for any sentence I wrote (Worker 3's scope note about unverifiable
   coverage negatives is respected).

5. **Slice-5 checklist, new sub-bullet (lines 189-198):** the three now-wrong transport
   strings in `django_strawberry_framework/auth/`. -- Worker 3's escalated **L2**, routed as
   a contract item so Slice 5 owns it rather than rediscovering it. Prose only.

6. **Decision 13's "Placement" sentence corrected (lines 1210-1215).** It described
   `tests/test_views.py` as holding only "the cap's argument validation and the
   settings-precedence matrix" -- Slice 2's rows. Slice 1 legitimately put the
   import-boundary and public-surface contracts there (they are equally unreachable from a
   live request). The sentence now enumerates both slices' halves, so Slice 1's five rows
   are not readable as out-of-contract.

