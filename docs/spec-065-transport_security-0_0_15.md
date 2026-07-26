# Spec: Transport security — Django-owned HTTP, a bounded request body, one UTF-8 wire, and WebSocket actor revalidation

Planned for `0.0.15` (card [`WIP-ALPHA-065-0.0.15`][kanban]). This is **card 1 of a
four-card security-remediation program** derived from the hardening audit in
[`docs/feedback2.md`][feedback2]; it closes that audit's two Blockers (**S1**, **S2**),
two Mediums (**S9**, **S11**), and the **transport slice of S12**. Cards
[`TODO-ALPHA-066-0.0.16`][kanban] (request resource policy),
[`TODO-ALPHA-067-0.0.17`][kanban] (secure defaults), and
[`TODO-ALPHA-068-0.0.18`][kanban] (dependency / CI hygiene) each depend on this one:
the program is staged transport-first because every later bound is consumed by the
transports corrected here.

**`docs/feedback2.md` is review evidence this spec references, not a substitute for
it.** The audit established the facts; every decision, public-API shape,
compatibility promise, slice boundary, test row, and documentation obligation below is
this spec's own and, where the maintainer's pinned direction and the audit's
prescription differ, the maintainer's direction governs (most visibly in S2, where the
audit's "S1 removes the worst implementation" framing is deliberately **not** allowed
to soften the requirement for a package-owned cap).

This card **amends the contract of [`spec-041`][spec-041]**
([Decision 14](#decision-14--this-card-amends-spec-041-and-supersedes-three-of-its-decisions)):
it supersedes that spec's Decision 6 (constructor parity), the HTTP half of its
Decision 2 (card-scope boundary), and the HTTP-fallback half of its Borrowing posture.
The [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] symbol,
its [soft-`channels`][glossary-soft-dependency] guard, its
[PEP 562 lazy export][glossary-pep-562-lazy-export], and its WebSocket composition
all survive unchanged.

**This is an intentional, documented alpha breaking change**
([Decision 5](#decision-5--compatibility-policy-an-intentional-alpha-breaking-change-to-a-security-boundary)):
the `0.0.14` byte-compatible upstream constructor contract is broken on purpose. The
package's documented API freeze begins at `1.0.0`; correcting a newly confirmed
security-boundary error during alpha is strictly preferable to preserving an unsafe
migration convenience.

Status: **IN BUILD — Slices 1-3 (S1, S2, S9) are built and accepted; Slices 4-5 remain.** Five
slices: Slice 1 (**S1** — the protocol
split: HTTP to a required Django ASGI application, the package's Django GraphQL view,
WebSocket-only exact routing), Slice 2 (**S2** — the cumulative body cap plus the
documented proxy/server cap), Slice 3 (**S9** — the strict UTF-8 wire contract and the
inverted encoding tests), Slice 4 (**S11** — the WebSocket consumer-injection seam and
per-operation actor revalidation), Slice 5 (**S12 transport slice** — the migration
note, transport deployment guidance, the `spec-041` amendment, and the doc fold-in).

**Version boundary** (see
[Decision 15](#decision-15--the-0015-version-bump-is-deferred-to-the-joint-cut)): this
card **shares the `0.0.15` patch line** with [`TODO-ALPHA-045-0.0.15`][kanban], so the
version bump is owned by the [joint version cut][glossary-joint-version-cut] — the last
`0.0.15` card to land — and **no slice here moves any part of the version quintet**.

Permission caveat: [`AGENTS.md`][agents] prohibits `CHANGELOG.md` edits without
explicit permission. Because the `0.0.15` `CHANGELOG.md` entry is part of the joint cut
rather than this card, **no slice in this spec grants or exercises that permission** —
the grant travels with the cut, exactly as [`spec-041`][spec-041] Decision 10 pinned
for the joint `0.0.14` cut.

---

## Key glossary references

Terms this spec relies on (statuses per [`docs/GLOSSARY.md`][glossary]):

- [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] — the shipped
  transport helper this card redesigns; its HTTP branch is the S1 defect site.
- [Soft dependency][glossary-soft-dependency],
  [Hard dependency][glossary-hard-dependency],
  [PEP 562 lazy export][glossary-pep-562-lazy-export],
  [`require_optional_module`][glossary-require_optional_module],
  [Eviction-simulated absence][glossary-eviction-simulated-absence] — the optional-import
  discipline the router keeps, and the reason the new Django view is *not* subject to it.
- [Channels request adapter][glossary-channels-request-adapter],
  [`request_from_info`][glossary-request_from_info] — the package's own read path; the
  S11 revalidation writes the refreshed actor back where these already read it.
- [Auth mutations][glossary-auth-mutations] — the session surface whose transport matrix
  this card narrows on HTTP and extends on WebSocket.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook],
  [`DjangoModelPermission`][glossary-djangomodelpermission] — the authorization layers
  that consume the actor S11 keeps fresh.
- [`ConfigurationError`][glossary-configurationerror] — the typed construction-time
  failure for a missing or unusable `django_application`.
- [`Upload` scalar][glossary-upload-scalar], [`DjangoMutation`][glossary-djangomutation],
  [`FieldError` envelope][glossary-fielderror-envelope] — the multipart write path the
  body cap must not break.
- [`DjangoNodesField`][glossary-djangonodesfield] — ships the standing note that
  "request-size limiting belongs to the consumer's transport layer"; S2 makes that
  sentence true by giving the transport layer an actual limit.
- [`TestClient`][glossary-testclient], [`GraphQLTestCase`][glossary-graphqltestcase],
  [Probe URLconf][glossary-probe-urlconf],
  [Schema reload discipline][glossary-schema-reload-discipline],
  [`seed_data`][glossary-seed_data],
  [Live-first coverage mandate][glossary-live-first-coverage-mandate] — the test tiers
  and disciplines that decide where each S1/S2/S9 regression lives.
- [Single-upstream parity][glossary-single-upstream-parity] — the honest-parity rule; this
  card deliberately **diverges** from the single upstream it once matched.
- [Joint version cut][glossary-joint-version-cut] — the release rule deferring the bump.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension],
  [`strawberry_config`][glossary-strawberry_config] — the schema-construction surface the
  new view must pass through untouched.
- [Developer-only debug posture][glossary-developer-only-debug-posture],
  [Debug-toolbar middleware][glossary-debug-toolbar-middleware] — the development-only
  surfaces whose production exposure the transport guidance must address.
- [Multi-database cooperation][glossary-multi-database-cooperation] — the reason the
  revalidation read is alias-explicit rather than router-guessed.
- [Cookbook parity][glossary-cookbook-parity] — the rule that project-level engine
  configuration (here: the ASGI entrypoint and the URLconf) migrates by documented
  recipe rather than by import-only promise.

## Slice checklist

Each top-level item maps to one commit / PR.

- [ ] **Slice 1 — S1: the protocol split (Django owns HTTP)**
  - [ ] `django_strawberry_framework/routers.py`: the HTTP branch becomes the
        consumer-supplied Django ASGI application **directly** — no `URLRouter`, no
        `GraphQLHTTPConsumer`, no `AuthMiddlewareStack` on HTTP
        ([Decision 2](#decision-2--http-dispatches-directly-to-a-required-consumer-supplied-django-asgi-application)).
  - [ ] `django_application` becomes a **required** constructor parameter; `None` or a
        non-callable raises [`ConfigurationError`][glossary-configurationerror] naming the
        migration
        ([Decision 3](#decision-3--django_application-is-required-omission-fails-at-construction-with-no-compatibility-fallback)).
  - [ ] `url_pattern` is renamed and narrowed to `websocket_url_pattern`, default
        `r"^graphql/?$"` (exact, both-ends anchored)
        ([Decision 4](#decision-4--url_pattern-becomes-websocket_url_pattern-with-exact-matching-as-the-secure-default)).
  - [ ] New `django_strawberry_framework/views.py`: `DjangoGraphQLView` /
        `AsyncDjangoGraphQLView`, the package's Django GraphQL view, declared in the
        consumer's URLconf
        ([Decision 6](#decision-6--the-graphql-http-endpoint-is-a-package-owned-django-view-in-the-consumers-urlconf)).
  - [ ] `examples/fakeshop/config/urls.py`: the `/graphql/` mount swaps from
        `strawberry.django.views.GraphQLView` to the package's `DjangoGraphQLView`, so
        the live tier below proves the package's own view rather than upstream's and every
        S2 regression row is earnable over fakeshop's real `/graphql/`
        ([Decision 6](#decision-6--the-graphql-http-endpoint-is-a-package-owned-django-view-in-the-consumers-urlconf)
        reason c).
  - [ ] `tests/test_routers.py`: the five HTTP-branch tests are rewritten to the new
        contract (three rewritten, two merged into one); every WebSocket Origin / auth
        test is preserved in subject and assertion strength; and
        `tests/auth/test_mutations.py`'s borrowed router harness is repaired in place
        ([Decision 13](#decision-13--test-strategy-which-existing-tests-change-and-why)).
  - [ ] `tests/test_views.py` + a live `examples/fakeshop/test_query/` tier proving
        Django middleware, `ALLOWED_HOSTS`, CSRF, security headers, cache policy, and
        exact routing execute on the GraphQL HTTP route.
- [ ] **Slice 2 — S2: the cumulative request-body cap**
  - [ ] `DjangoGraphQLView` / `AsyncDjangoGraphQLView` enforce a cumulative byte cap
        **before** JSON parsing or schema execution, returning `413`
        ([Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)).
  - [ ] One new settings key, `MAX_REQUEST_BODY_BYTES`, in
        `django_strawberry_framework/conf.py`, with a per-mount view-kwarg override
        (constructor > setting > default) — the shipped
        `NESTED_CONNECTION_STRATEGY` precedence shape.
  - [ ] The reverse-proxy / ASGI-server hard cap is stated as a **co-requirement**, not an
        alternative, on the two **code-documentation** surfaces this slice ships:
        `conf.py`'s `MAX_REQUEST_BODY_BYTES` key comment and the cap-contract docstring in
        `views.py`. The consumer-facing deployment prose with the concrete directives is
        Slice 5's, per
        [Decision 8](#decision-8--the-deployment-layer-cap-is-a-co-requirement-not-an-alternative)'s
        own surface split.
  - [ ] The full S2 regression matrix earned live over fakeshop's real `/graphql/`.
- [ ] **Slice 3 — S9: one UTF-8 wire contract**
  - [ ] `django_strawberry_framework/_strawberry_patches.py::_patched_parse_json` decodes
        `bytes` with **strict UTF-8** before delegating
        ([Decision 9](#decision-9--the-strict-utf-8-wire-contract-is-enforced-once-in-_patched_parse_json)).
  - [ ] `_cross_web_patches.py::_patched_body` keeps returning raw bytes; its docstring
        is rewritten to state the new contract and why the patch survives S1.
  - [ ] A UTF-8 BOM is **rejected** with the same controlled `400`
        ([Decision 10](#decision-10--a-utf-8-bom-is-rejected)).
  - [ ] The three UTF-16/32/BOM **success** tests in
        `examples/fakeshop/test_query/test_products_api.py` are inverted to `400`, and the
        raw-bytes contract tests in `tests/test_cross_web_patches.py` are re-aimed at the
        new contract.
- [ ] **Slice 4 — S11: WebSocket actor revalidation through an injection seam**
  - [ ] `websocket_consumer_class=` injection on the router; the injected class still sits
        inside `AllowedHostsOriginValidator` + `AuthMiddlewareStack` by construction
        ([Decision 11](#decision-11--a-websocket-consumer-classfactory-injection-seam-with-a-revalidating-package-default)).
  - [ ] The package's default WebSocket consumer revalidates the session actor per
        operation and writes the refreshed actor back onto `scope["user"]`; an invalid
        session rejects the operation.
  - [ ] `websocket_revalidation_window=` — an explicit, bounded, opt-in revocation delay
        (default `0.0` = revalidate every operation).
  - [ ] Maximum connection lifetime documented, with the enforcement seam named
        ([Decision 12](#decision-12--maximum-connection-lifetime-is-documented-and-seamed-not-silently-enforced)).
- [ ] **Slice 5 — S12 transport slice: migration note, deployment guidance, doc fold-in**
  - [ ] The migration note: old vs new `asgi.py` **plus** the required Django
        `urlpatterns` entry, in [`docs/README.md`][docs-readme].
  - [ ] Transport deployment guidance: CSRF, cache / `Vary`, security headers, IDE and
        GET controls, and the body-limit deployment expectation — which is where the
        reverse-proxy / ASGI-server cap is stated as a **co-requirement** for the
        consumer, with its concrete directives (`client_max_body_size` on nginx, the
        ASGI-server equivalents, the Daphne request-buffer note) and with the multipart
        carve-out named, so a reader of the proxy-cap paragraph alone cannot conclude that
        multipart is byte-counted
        ([Decision 8](#decision-8--the-deployment-layer-cap-is-a-co-requirement-not-an-alternative)).
  - [ ] [`spec-041`][spec-041] amended in place with an amendment banner naming the three
        superseded decisions
        ([Decision 14](#decision-14--this-card-amends-spec-041-and-supersedes-three-of-its-decisions)).
  - [ ] [`docs/GLOSSARY.md`][glossary] via the glossary DB + re-render (never
        hand-edited); [`docs/TREE.md`][tree] regenerated for `views.py` and the new tests;
        [`README.md`][readme] / [`TODAY.md`][today] transport wording.
  - [ ] The three now-wrong transport strings in `django_strawberry_framework/auth/`,
        corrected in the same pass as the prose above: `sessions.py::classify_transport`'s
        unrecognized-scope-type `ConfigurationError` (it tells the reader to "route GraphQL
        through `DjangoGraphQLProtocolRouter`", which after Slice 1 produces no GraphQL
        `http` scope at all), and the `mutations.py::_login_resolve_body` /
        `::_logout_resolve_body` docstrings that describe "the package router's async
        consumer" (the package router no longer has an HTTP consumer of either colour).
        Prose only, no behavior change; none is load-bearing, and they are outside the
        named files of every earlier slice, which is why they route here.
  - [ ] `examples/fakeshop/test_query/README.md`: the **S1 and S2** acceptance rows (the
        file does not mention `test_transport_api.py` at all today) alongside S9's, **plus**
        a widened raw-envelope exemption — its current wording exempts only "malformed
        bodies, content-type negotiation" from the shared harness, which does not cover the
        hostile-`Host` / `secure=` / `enforce_csrf_checks=` / `AsyncClient` rows S1 added or
        the in-process `ASGIHandler` driver S2 added for the unmeasured / understated /
        fragmented-body rows.
  - [ ] The Slice-2 prose corrections, carried here for the same reason as the `auth/`
        strings above (prose only, none load-bearing, none in a Slice-2 named file's
        contract): `views.py`'s cap-contract docstring re-words its mixin-first rationale
        to the operative reason — the mixin's attribute and method must take precedence
        over any same-named attribute upstream may later add — rather than the
        non-operative claim that the ordering is what satisfies `View.as_view`'s keyword
        guard (that guard is a `hasattr` over the whole MRO, so a mixin-**last** subclass
        binds `max_request_body_bytes=` identically); `conf.py`'s `MAX_REQUEST_BODY_BYTES`
        comment gains the multipart carve-out so the surface a consumer configures does not
        claim counted bytes where the bound is the declaration alone; the trivially-true
        `mixin.__name__ not in __all__` assertion in `tests/test_views.py`'s mixin-privacy
        test is dropped, leaving the exact-`__all__` test as the single privacy proof; and
        `test_transport_api.py::test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce`'s
        docstring drops its "the spec's Edge-case sentence predicting a `413` is inaccurate"
        clause, which Slice 2's own final verification made obsolete by correcting the spec —
        the `400` explanation itself stays, since it is the reason the row asserts what it
        asserts.
  - [ ] The Slice-3 prose corrections, in
        `examples/fakeshop/test_query/test_transport_api.py` and carried here for the same
        reason as the Slice-1 and Slice-2 prose above: (a) the module docstring's **first
        line** still scopes the file to `(spec-065 Slices 1-2)` although it now carries an
        S9 async row — correct it to the file's actual slice scope, and do it **before**
        the [`docs/TREE.md`][tree] regenerate in this same slice, because that first line
        is the text `scripts/build_tree_md.py` renders (pinning a number at Slice 3 would
        have been a guess about a file Slice 4 could still add rows to; pinning it here
        pins the truth); and (b)
        `::test_the_async_package_view_enforces_the_same_utf8_wire_contract`'s attribution
        sentence claims a `400` there "can only come from the strict decode", which holds
        for its UTF-16 request but not for the UTF-8-BOM request in the same test, whose
        `__cause__` is upstream's `json.JSONDecodeError` — re-word to "the wrapper's strict
        decode having replaced the raw-bytes path", which is the but-for cause of both. No
        assertion changes in either; the rows stay exactly as accepted.
  - [ ] Card flip to Done + `KANBAN.md` / `KANBAN.html` regeneration from the DB.
  - [ ] **No version quintet movement, and no `CHANGELOG.md` edit**
        ([Decision 15](#decision-15--the-0015-version-bump-is-deferred-to-the-joint-cut)).

## Problem statement

The shipped router turns the session cookie into an authenticated actor on a transport
that never runs Django's request lifecycle. `routers.py::_build_router_class` composes
the HTTP branch as `AuthMiddlewareStack(URLRouter([re_path(url_pattern,
GraphQLHTTPConsumer.as_asgi(schema=schema))]))`, appending the optional
`django_application` **after** the GraphQL route as `re_path(r"^", django_application)`.
Three consequences follow from that single composition, and all three are structural
rather than contingent:

1. **The security-preserving branch is the optional one.** `AuthMiddlewareStack` supplies
   cookies, sessions, and `scope["user"]`; it is not Django's ASGI handler and it does
   not execute `MIDDLEWARE`. So `SecurityMiddleware`, `CsrfViewMiddleware`,
   `CommonMiddleware` and the `ALLOWED_HOSTS` request boundary, and every consumer
   tenant / rate-limit / audit / cache / security-header middleware are all skipped on
   the one route that accepts credentials. The audit's probe recorded
   `POST /graphql` with `Host: evil.example` returning `200` with `content-type` as its
   only response header. The package's own documentation already concedes half of this
   in [`docs/README.md`][docs-readme] #"the Channels GraphQL consumers do not enforce
   CSRF" — a documented gap is still a gap.
2. **The route overmatches.** `url_pattern="^graphql"` is a prefix regex with no
   right anchor, so `/graphql-admin` and `/graphqlanything` are claimed by the GraphQL
   consumer *before* the Django fallback can see them. A deployment can believe a Django
   URL and its middleware policy own a path the router silently intercepts.
3. **The body is unbounded.** The routed consumer inherits
   `channels.generic.http.AsyncHttpConsumer`, whose `http_request` appends every ASGI
   body fragment to `self.body` and then calls `await self.handle(b"".join(self.body))`.
   There is no application-level maximum anywhere in the package, and Django's
   `DATA_UPLOAD_MAX_MEMORY_SIZE` is never consulted because Django's ASGI handler is
   bypassed. That is an unauthenticated memory-amplification path that allocates before
   JSON parsing or schema execution, and it needs neither valid JSON nor an honest
   `Content-Length`.

Two narrower defects share the same transport surface. The request parser accepts
UTF-16 and UTF-32 network JSON — `_cross_web_patches.py::_patched_body` returns raw
bytes precisely so `json.loads` can auto-detect encodings, and three live tests
currently assert that as *success* — which creates a parser differential between the
application and every proxy, WAF, access log, and body scanner in front of it. And a
WebSocket scope's actor is captured at handshake and never refreshed, so a logout,
password reset, account disable, or session revocation performed anywhere else is
invisible to an established connection for its entire lifetime.

The unifying failure is one of ownership: the package built a **partial** Django
security stack around a bare Channels consumer instead of using Django's complete one.
Reproducing that stack faithfully — exact routing, Host validation, cookie-auth CSRF,
cache variation, body limits, response security headers, IDE and GET controls,
consumer-class injection — is materially more code and more drift risk than routing
through the boundary Django already ships and tests. That is the architecture this card
adopts.

## Current state

A true description of the repo as this spec is authored (`0.0.14`, HEAD on `main`):

- **The router's HTTP branch is as described above.** `routers.py::_build_router_class`
  builds `http_urls = [re_path(url_pattern, GraphQLHTTPConsumer.as_asgi(schema=schema))]`
  and appends `re_path(r"^", django_application)` only `if django_application is not
  None`. The constructor is
  `__init__(self, schema, django_application: ASGIHandler | None = None, url_pattern:
  str = "^graphql")`. `get_asgi_application()` appears **only** in the class docstring's
  example and is never called by the module.
- **The consumers are imported bare, so upstream defaults apply.**
  `from strawberry.channels import GraphQLHTTPConsumer, GraphQLWSConsumer`, instantiated
  with `schema=` alone. At the installed `strawberry-graphql` 0.316.0 that means
  `graphql_ide="graphiql"` (the IDE is **on**), `allow_queries_via_get=True` (GET queries
  are **on**), and `multipart_uploads_enabled=False`. The router exposes no constructor
  control over any of them, nor over either consumer class.
- **The WebSocket branch is already correct** and this card preserves it:
  `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([...GraphQLWSConsumer...])))`,
  with the origin validator outside the auth stack so a cross-origin **or
  missing-`Origin`** handshake is denied against `ALLOWED_HOSTS`.
- **The soft-dependency machinery is intact and stays.** `require_channels()` over
  [`require_optional_module`][glossary-require_optional_module], the split
  present-but-incompatible hints, the cached `_ROUTER_CLASS` module global that
  [eviction-simulated absence][glossary-eviction-simulated-absence] tests rely on, and
  the [PEP 562][glossary-pep-562-lazy-export] module `__getattr__`.
- **Django already enforces more than the audit credits it with — but not everything, and
  not identically across the supported range.** Both `cross_web` adapters
  (`DjangoHTTPRequestAdapter.body` and `AsyncDjangoHTTPRequestAdapter.get_body`) read
  Django's `HttpRequest.body`, and that property (a) rejects a declared-over-limit request
  from `CONTENT_LENGTH` **without reading the body**, on every supported release, and
  (b) **only from Django 6.0** additionally seeks a *seekable* stream — which is exactly
  ASGI's `SpooledTemporaryFile` — to the end and rejects on the **actual buffered size**,
  so an absent or lying `Content-Length` is caught by a real byte count. At the documented
  compatibility floor, **Django 5.2.0, check (b) does not exist**: `HttpRequest.body`
  carries the declared-`CONTENT_LENGTH` check alone (itself gated on
  `DATA_UPLOAD_MAX_MEMORY_SIZE is not None`) and no `_stream.seekable()` branch at all. So
  at the floor, against an absent or understated header, the package's own **counted** check
  is the only application-level bound in existence — which is the strongest available
  argument for [Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)'s
  "counted, not declared", and the reason the S2 test matrix must never combine a lowered
  `DATA_UPLOAD_MAX_MEMORY_SIZE` with the ASGI harness (see
  [Edge cases](#edge-cases-and-constraints)).

  Whichever check fires, the outcome is a **`400`, not a `413`**: `RequestDataTooBig` is
  raised **lazily** out of `HttpRequest.body`, i.e. inside the view, where
  `django/core/handlers/exception.py::response_for_exception` maps `SuspiciousOperation` to
  `400`. `ASGIHandler.create_request`'s `except RequestDataTooBig` → `413` branch guards
  only the `ASGIRequest(scope, body_file)` construction, and `ASGIRequest.__init__` never
  touches the body, so that `413` is unreachable for this flow on either transport or
  either supported release (measured on 5.2.0 and 6.0.x, and read at source).

  What Django does **not** do at all is stop the body from being received:
  `ASGIHandler.read_body` drains the entire request into a `SpooledTemporaryFile` (rolling
  to disk past `FILE_UPLOAD_MAX_MEMORY_SIZE`) *before* any cap is evaluated. This is why
  S2's deployment-layer cap is a co-requirement rather than a fallback
  ([Decision 8](#decision-8--the-deployment-layer-cap-is-a-co-requirement-not-an-alternative)).
- **`DATA_UPLOAD_MAX_MEMORY_SIZE` is a project-wide knob shared with file uploads.** A
  project that raises it for an upload endpoint silently raises the GraphQL body ceiling
  with it — the reason S2 gets its own key rather than inheriting Django's.
- **The two patch modules already own the malformed-body contract.**
  `_cross_web_patches.py::_patched_body` returns raw `self.request.body` so
  `json.loads` sees bytes; `_strawberry_patches.py::_patched_parse_json` wraps upstream's
  `parse_json` and translates `UnicodeDecodeError` into `HTTPException(400, ...)` plus a
  body-envelope guard, with `_patched_parse_query_params` shielding the two GET
  query-param parse sites. Both are gated by `APPLY_UPSTREAM_PATCHES` and validate the
  upstream shape before installing.
- **The encoding matrix was measured, not assumed.** Under today's raw-bytes contract,
  every one of UTF-8, UTF-8-with-BOM, UTF-16 (BOM and BOM-less, LE and BE), and UTF-32
  (BOM and BOM-less, LE and BE) parses successfully, because `json.loads` applies RFC 8259
  encoding auto-detection to `bytes`. Under a strict UTF-8 decode followed by `json.loads`
  on the resulting `str`, plain UTF-8 succeeds and every other shape reaches a `400` on an
  existing translation path with **no new rejection branch** — the finding that makes
  [Decision 10](#decision-10--a-utf-8-bom-is-rejected) nearly free. The complete
  ten-shape table, and which of the two mechanisms refuses each shape, is enumerated once
  in
  [Decision 9](#decision-9--the-strict-utf-8-wire-contract-is-enforced-once-in-_patched_parse_json)
  rather than restated here.
- **Three live tests assert the encodings this card rejects.**
  `test_products_api.py::test_post_utf16_json_body_succeeds_like_async_transport`,
  `::test_post_utf16_le_json_body_succeeds_like_async_transport`, and
  `::test_post_utf8_bom_json_body_succeeds_like_async_transport`, with companion
  raw-bytes contract tests in `tests/test_cross_web_patches.py`
  (`test_body_returns_raw_bytes_for_utf8_bom`,
  `test_body_returns_raw_bytes_for_utf16_le_without_bom`). Those three names are the
  state this card **found**; Slice 3 inverted all three, so a reader grepping them now
  finds
  `::test_post_utf16_json_body_is_rejected_as_400`,
  `::test_post_utf16_le_json_body_is_rejected_as_400`, and
  `::test_post_utf8_bom_json_body_is_rejected_as_400` instead — the raw-bytes contract
  tests keep their names and were re-aimed in place.
- **`tests/test_routers.py` is 582 lines and its HTTP assertions encode the old
  contract.** `test_http_branch_is_auth_wrapped_and_routes_only_graphql_without_fallback`,
  `test_django_application_fallback_is_appended_after_the_graphql_route`, and
  `test_custom_url_pattern_reaches_the_re_path_on_both_branches` all assert behavior this
  card deliberately removes. The Origin / auth tests
  (`test_websocket_handshake_origin_directions`,
  `test_websocket_branch_wraps_origin_validator_outside_the_auth_stack`,
  `test_authenticated_session_round_trip_reaches_the_resolver`,
  `test_request_contract_resolves_over_the_websocket_branch`) assert behavior it keeps.
- **The WebSocket actor is read once and never refreshed.**
  `utils/permissions.py::ChannelsRequestAdapter.user` returns `self._scope.get("user")`
  with no revalidation; only same-connection `auth/mutations.py` login / logout mutate
  `scope["user"]`. Strawberry's `GraphQLWSConsumer.get_context` is called **once per
  connection** inside `AsyncBaseHTTPView.run`, not per operation — so `get_context` is
  not a per-operation seam. The per-operation entry points are
  `BaseGraphQLTransportWSHandler.handle_subscribe` and the `graphql_ws` sibling's
  `handle_start`, reached through the `graphql_transport_ws_handler_class` /
  `graphql_ws_handler_class` class attributes on the view — both overridable.
- **Fakeshop already mounts Strawberry's Django view.** `examples/fakeshop/config/urls.py`
  serves `path("graphql/", ensure_csrf_cookie(GraphQLView.as_view(schema=schema,
  graphql_ide="graphiql", multipart_uploads_enabled=True)))`. That is the exact URLconf
  shape S1's migration note documents, and it means the live tier can earn the HTTP-side
  regressions today — without an `asgi.py`, which fakeshop still does not have.
- **No transport settings key exists.** `conf.py`'s `DJANGO_STRAWBERRY_FRAMEWORK` block
  carries `APPLY_UPSTREAM_PATCHES`, `NESTED_CONNECTION_STRATEGY`,
  `SINGLE_PARENT_FAST_PATH`, `TESTING_ENDPOINT`, `HIDE_FLAT_FILTERS`, and
  `RELAY_GLOBALID_STRATEGY`. Per [`AGENTS.md`][agents] #"Add settings keys only when the
  feature that needs them lands", this card adds exactly one.
- **The `0.0.15` line has two non-Done cards.** [`TODO-ALPHA-045-0.0.15`][kanban] (the
  debug extraction) and this one, so the
  [joint version cut][glossary-joint-version-cut] rule applies
  ([Decision 15](#decision-15--the-0015-version-bump-is-deferred-to-the-joint-cut)).

## Goals

1. **One authoritative HTTP boundary.** Every GraphQL HTTP request traverses the
   consumer's real Django ASGI application, URLconf, and complete `MIDDLEWARE` stack —
   the same boundary as the rest of the application, tested as such.
2. **No unsafe mode to fall into.** The insecure GraphQL-only HTTP mode is *removed*,
   not deprecated behind a flag; omitting the Django application fails loudly at
   construction with an actionable message.
3. **A bounded request body as a package contract.** An explicit cumulative-byte cap,
   enforced pre-parse and pre-execution on the GraphQL HTTP path, counted rather than
   declared, with a `413` proving neither JSON parsing nor schema execution ran — plus a
   documented deployment-layer cap the package states it depends on.
4. **One wire encoding.** Request JSON is UTF-8, strictly, with one documented BOM
   policy and byte-identical sync / async behavior.
5. **A WebSocket actor that cannot go stale silently.** Per-operation session
   revalidation on by default for the package's own consumer, with any accepted
   revocation delay expressed as an explicit, bounded, opt-in number.
6. **A transport that is configurable rather than frozen.** A consumer-class injection
   seam that cannot escape the package's Host/Origin and authentication wrappers, so a
   deployment needing stronger revocation extends the transport instead of forking it.
7. **A migration a reader can execute.** Old `asgi.py`, new `asgi.py`, the required
   `urlpatterns` entry, and the transport deployment expectations, in one place.

## Non-goals

- **A central request resource-policy object.** Query depth / complexity / cost budgets,
  variable cardinality, collection bounds, and per-file upload limits are
  [`TODO-ALPHA-066-0.0.16`][kanban] (audit S3 / S4). This card ships exactly one
  transport bound — the cumulative body cap — and deliberately does not invent the policy
  object that later card owns.
- **Secure defaults for the IDE, GET, introspection, and error masking.** The card's
  regressions *prove* `graphql_ide=None` and `allow_queries_via_get=False` are supported
  on the new view; *changing the shipped defaults*, plus `DjangoSchema`-level production
  error policy and the [`DjangoDebugExtension`][glossary-djangodebugextension] disclosure
  gate (audit S8 / S10), belongs to [`TODO-ALPHA-067-0.0.17`][kanban].
- **The full deployment contract.** The `SECURITY.md` production-security profile and the
  mechanical `check --deploy`-style checklist (the rest of audit S12) belong to the later
  cards' doc slices; this card ships only the transport slice
  ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **A fakeshop `asgi.py` / live Channels tier.** Fakeshop stays WSGI-only. The
  [live-first coverage mandate][glossary-live-first-coverage-mandate] is satisfied for the
  HTTP half (fakeshop already serves a real Django GraphQL view over
  `django.test.Client`); the WebSocket half remains the documented
  genuinely-unreachable-live case that keeps `tests/test_routers.py` communicator-driven.
- **A second GraphQL protocol engine.** The injection seam and the revalidation pre-hook
  delegate to Strawberry's handlers with `super()`; the package implements no message
  loop, no subprotocol negotiation, and no subscription machinery.
- **Reintroducing a Channels HTTP mode as an "advanced transport".** The audit offers
  that as a conditional; this spec declines it
  ([Decision 2](#decision-2--http-dispatches-directly-to-a-required-consumer-supplied-django-asgi-application),
  alternatives rejected).
- **A new [`DjangoType`][glossary-djangotype] `Meta` key.** Transport configuration is not
  type configuration; `DEFERRED_META_KEYS` is untouched.
- **A `channels` extras group or a hard dependency.** `channels` stays soft, exactly as
  [`spec-041`][spec-041] Decision 5 pinned. The new Django view is a
  [hard-dependency][glossary-hard-dependency] surface and needs no guard at all.

## Borrowing posture

This card **inverts** the borrowing posture of [`spec-041`][spec-041], and that inversion
is the point.

`spec-041` was [single-upstream parity][glossary-single-upstream-parity]: it borrowed
`strawberry_django.routers.AuthGraphQLProtocolTypeRouter`'s composition *verbatim*,
including the optional-Django-fallback HTTP branch, and held the constructor signature
byte-compatible so a migrant changed one import line. The audit establishes that the
borrowed HTTP branch is the defect. So this card **stops borrowing that half**:

- **Still borrowed, verbatim:** the WebSocket composition
  (`AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([...])))`), the
  engine-owned consumers from `strawberry.channels`, and the `ProtocolTypeRouter`
  subclass shape. Upstream got the WebSocket branch right, and the audit's own "security
  strengths confirmed" list agrees.
- **Deliberately not borrowed:** the HTTP branch, the optional `django_application`, the
  prefix `url_pattern` shared across both protocols, and the byte-compatible constructor
  signature. Keeping composition parity with an upstream whose HTTP branch bypasses
  Django's middleware would be parity with a defect — and [`GOAL.md`][goal]'s non-goal
  "a thin wrapper around `strawberry-graphql-django`" cuts against inheriting an unsafe
  boundary for migration convenience.
- **Borrowed from Django instead:** `get_asgi_application()`, the URLconf, `MIDDLEWARE`,
  and `HttpRequest.body`'s existing size checks — the declared-`CONTENT_LENGTH` one on
  every supported release, the buffered-size one from Django 6.0 — whose
  `RequestDataTooBig` surfaces as a `400` (see
  [Current state](#current-state)). The audit's recommended shape is Django's own documented
  ASGI arrangement; the package's contribution becomes the WebSocket composition plus the
  three package-owned bounds (body cap, UTF-8 wire, actor revalidation).
- **Borrowed from Strawberry:** `strawberry.django.views.GraphQLView` /
  `AsyncGraphQLView` are subclassed rather than reimplemented
  ([Decision 6](#decision-6--the-graphql-http-endpoint-is-a-package-owned-django-view-in-the-consumers-urlconf)).
  Both are part of the existing hard `strawberry-graphql` dependency (their imports are
  `django`, `cross_web`, and `strawberry` only, verified in the installed 0.316.0), so no
  optional-import guard applies.
- **`graphene-django` still ships no ASGI/Channels helper**, so the honest-parity claim
  from `spec-041` is unchanged in kind — but it is now parity *plus a documented
  divergence*, which per [Cookbook parity][glossary-cookbook-parity] is exactly the class
  of change that migrates by recipe (the migration note) rather than by the import-only
  promise. The migration-guide symbol-equivalents row gains a **call-site change**
  alongside the import change; it is no longer a one-line migration and the row must say
  so.

## User-facing API

### The consumer's `asgi.py` (new)

```python
# myproject/asgi.py
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

from django.core.asgi import get_asgi_application

django_asgi = get_asgi_application()          # Django is fully initialized here

from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter

from myproject.schema import schema

application = DjangoGraphQLProtocolRouter(
    schema,
    django_application=django_asgi,           # REQUIRED
)
```

### The consumer's URLconf (new, and required for HTTP GraphQL)

```python
# myproject/urls.py
from django.urls import path

from django_strawberry_framework.views import DjangoGraphQLView

from myproject.schema import schema

urlpatterns = [
    # ... the rest of the project
    path("graphql/", DjangoGraphQLView.as_view(schema=schema)),
]
```

### The constructor

```python
DjangoGraphQLProtocolRouter(
    schema,                                   # the strawberry.Schema (extensions ride along)
    django_application,                       # REQUIRED: get_asgi_application()
    *,
    websocket_url_pattern=r"^graphql/?$",     # WebSocket-only, exact by default
    websocket_consumer_class=None,            # class or factory; None -> the package default
    websocket_revalidation_window=0.0,        # seconds of accepted revocation delay
)
```

### The view

```python
DjangoGraphQLView.as_view(
    schema=schema,
    max_request_body_bytes=None,              # None -> the MAX_REQUEST_BODY_BYTES setting
    # every upstream strawberry.django.views.GraphQLView kwarg still applies:
    graphql_ide="graphiql",
    allow_queries_via_get=True,
    multipart_uploads_enabled=False,
)
```

`AsyncDjangoGraphQLView` is the async twin with an identical surface, for a project
whose GraphQL view must be async (the shape ASGI deployments generally want).

### The setting

```python
DJANGO_STRAWBERRY_FRAMEWORK = {
    # Cumulative request-body ceiling for the GraphQL HTTP path, in bytes.
    # None disables the package cap and leaves only Django's
    # DATA_UPLOAD_MAX_MEMORY_SIZE and the deployment-layer cap.
    "MAX_REQUEST_BODY_BYTES": 1_048_576,
}
```

### Consumer-visible behavior

- **The schema passes through untouched** on both protocols and in the view: a schema
  built with [`strawberry_config()`][glossary-strawberry_config] and
  [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] keeps both.
- **HTTP path matching is Django's.** `path("graphql/", ...)` matches `/graphql/` and
  nothing else; `/graphql` is handled by `CommonMiddleware`'s `APPEND_SLASH`, and
  `/graphql-admin` / `/graphqlanything` reach the rest of the URLconf or `404`. The
  migration note states the explicit policy and warns that an `APPEND_SLASH` redirect is
  a `301` most clients will not re-`POST` — post to the trailing-slash URL, or declare
  both patterns deliberately.
- **WebSocket path matching is the router's, and is exact.** `r"^graphql/?$"` matches
  `/graphql` and `/graphql/` and rejects every prefix extension.
- **A body over the cap gets `413`** with a `text/plain` reason, before `parse_json` and
  before schema execution.
- **Non-UTF-8 request JSON gets `400`** — the same controlled response malformed JSON
  already gets.
- **A revoked session cannot keep executing over an open socket**: the next operation is
  rejected without a reconnect.
- **Migration is no longer one line.** Both the `asgi.py` call site and the URLconf
  change:

  ```diff
  - application = DjangoGraphQLProtocolRouter(schema)
  + application = DjangoGraphQLProtocolRouter(schema, django_application=django_asgi)
  ```

  ```diff
  + from django_strawberry_framework.views import DjangoGraphQLView
  +
    urlpatterns = [
  +     path("graphql/", DjangoGraphQLView.as_view(schema=schema)),
    ]
  ```

### Error shapes

- **`django_application` omitted entirely** — `TypeError` from Python's own signature
  binding, naming the missing parameter. Deliberate: a required parameter should fail as
  a required parameter.
- **`django_application=None` or a non-callable** — [`ConfigurationError`][glossary-configurationerror]
  at construction, naming the security reason and the fix: that a `0.0.14` deployment
  which passed `None` (or omitted it) was serving GraphQL HTTP outside Django's
  middleware, that the mode is removed, and that the repair is
  `get_asgi_application()` plus the `urlpatterns` entry. The explicit-`None` branch
  exists precisely so a migrant who kept the old keyword gets prose instead of a
  `TypeError`.
- **Body over the cap** — `413` with reason `"Request body exceeded the configured
  GraphQL request-body limit."`, produced by the view before any parse. Distinct from
  Django's own rejection when the consumer's `DATA_UPLOAD_MAX_MEMORY_SIZE` is the lower
  ceiling and fires first, which is a **`400`** `SuspiciousOperation` on both transports
  rather than a `413` (see [Current state](#current-state) for why the `413` branch in
  `ASGIHandler.create_request` is unreachable here) — both are correct, and the tests
  assert which one fired. The `413` is therefore the package's own signature.
- **Non-UTF-8 body** — `HTTPException(400, "Unable to parse request body as JSON")` for a
  strict-decode failure (the existing message, unchanged), or upstream's own
  `400` for a decodable-but-not-JSON payload such as BOM-less UTF-16 or a UTF-8 BOM.
- **Revoked session, next operation** — a GraphQL error on that operation; the socket is
  closed when the protocol offers no per-operation error channel. The rejection is a
  transport-capability error in the same family as the shipped WebSocket
  [auth-mutation][glossary-auth-mutations] rejections, never the undifferentiated
  failed-login envelope.
- **Cross-origin or missing-`Origin` WebSocket handshake** — unchanged: denied by
  `AllowedHostsOriginValidator` before the GraphQL protocol starts.
- **`channels` absent** — unchanged: the install-hint `ImportError` at the consumer's
  `from django_strawberry_framework.routers import ...` line. Note the asymmetry this
  card introduces and must document: `django_strawberry_framework.views` needs **no**
  `channels`, so a WSGI-only project can adopt the whole HTTP half of this card without
  ever touching the soft dependency.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

This spec lives at `docs/spec-065-transport_security-0_0_15.md`: card NNN `065`, topic
slug `transport_security`, target version `0.0.15` with dots as underscores, per the
[`docs/SPECS/NEXT.md`][next] Step 6 convention. The companion term ledger is
`docs/spec-065-transport_security-0_0_15-terms.csv`.

The topic slug is `transport_security` rather than `channels_router` (the `spec-041`
slug) because the card's subject is the transport boundary as a whole — HTTP ownership,
body bounds, wire encoding, and socket actor freshness — not the router module alone.
Two of the four findings (S2's cap and S9's wire contract) land outside `routers.py`
entirely.

### Decision 2 — HTTP dispatches directly to a required, consumer-supplied Django ASGI application

**Decision.** The router's `"http"` key is the consumer's Django ASGI application,
**directly**. No `URLRouter`, no `re_path`, no `GraphQLHTTPConsumer`, and no
`AuthMiddlewareStack` on the HTTP branch:

```python
{
    "http": django_application,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter([re_path(websocket_url_pattern, consumer)])),
    ),
}
```

The router **must not instantiate or route to `GraphQLHTTPConsumer`** at all; the import
leaves `routers.py` in the same change. The GraphQL HTTP endpoint is declared in the
consumer's Django URLconf
([Decision 6](#decision-6--the-graphql-http-endpoint-is-a-package-owned-django-view-in-the-consumers-urlconf)),
so it inherits the full `MIDDLEWARE` stack, `ALLOWED_HOSTS`, CSRF, security headers,
cache policy, and every consumer-authored middleware, with exactly one home for the
endpoint's URL.

Dropping `AuthMiddlewareStack` from the HTTP branch is not a loss: Django's own
`SessionMiddleware` + `AuthenticationMiddleware` do that job inside the stack the request
now traverses, and doing it twice would layer a Channels-shaped scope actor underneath a
Django-shaped request actor on the same request. On the HTTP route this router serves the
actor is `request.user`: the
[Channels request adapter][glossary-channels-request-adapter] is a WebSocket-only shape
**in the package's own composition**, and
[`request_from_info`][glossary-request_from_info] resolves the plain `HttpRequest` on HTTP
exactly as it does for any WSGI deployment.

**What this does not remove.** The package stops *composing* a Channels HTTP GraphQL
route; it does not stop *supporting* one. `auth/sessions.py::Transport.CHANNELS_HTTP`,
`::classify_transport`'s `scope["type"] == "http"` arm, and both `auth/mutations.py`
resolve-body `CHANNELS_HTTP` branches all survive this card unchanged, so a consumer who
mounts `strawberry.channels.GraphQLHTTPConsumer` in their own `ProtocolTypeRouter` is
still classified and served exactly as in `0.0.14` — they simply no longer get that
composition from this package, and the [`ConfigurationError`][glossary-configurationerror]
of [Decision 3](#decision-3--django_application-is-required-omission-fails-at-construction-with-no-compatibility-fallback)
tells a `0.0.14` migrant so. That surviving support is why Slice 1 repairs
`tests/auth/test_mutations.py`'s borrowed transport harness in place rather than deleting
its eight `HttpCommunicator` round trips
([Decision 13](#decision-13--test-strategy-which-existing-tests-change-and-why)).

**Why.** It is the only correction that gives the credential-accepting route the same
boundary as the rest of the application, and it deletes code rather than adding it.

**Alternatives rejected.**

- **Keep the Channels HTTP consumer and rebuild Django's boundary around it** (the
  audit's own conditional). Rejected: it means package-owned exact routing, Host
  validation, cookie-auth CSRF, cache variation, body limits, response security headers,
  and IDE/GET controls — a partial re-implementation of `MIDDLEWARE` that must track
  Django's security releases forever. [`AGENTS.md`][agents] #"always recommend the
  root-cause fix over the surface patch" settles it.
- **Keep the Channels HTTP route but wrap it in Django's middleware chain manually.**
  Rejected: Django's middleware is written against `HttpRequest` / `HttpResponse`, not an
  ASGI scope; the adapter layer needed to make that true *is* `ASGIHandler`, which is
  what `get_asgi_application()` already returns.
- **Reorder the existing branch so `django_application` comes first.** Rejected: it makes
  the GraphQL consumer unreachable rather than safe, and leaves the whole apparatus in
  place as a trap.
- **Ship both modes with the safe one as the default.** Rejected explicitly by the
  maintainer's pinned direction, and correctly: an unsafe mode that exists is an unsafe
  mode that gets selected, and a security boundary with a documented opt-out is a
  boundary the audit would have to re-find next release.

### Decision 3 — `django_application` is required; omission fails at construction with no compatibility fallback

**Decision.** `django_application` becomes a **required** constructor parameter, and the
insecure GraphQL-only HTTP mode is **removed**. Passing `None` explicitly, or any
non-callable, raises [`ConfigurationError`][glossary-configurationerror] at construction
with the message shape in [Error shapes](#error-shapes). There is no
`allow_insecure_http=True`, no deprecation period, and no silent degradation.

The router does **not** call `get_asgi_application()` itself. The consumer calls it at
the normal point in `asgi.py` — after `DJANGO_SETTINGS_MODULE` is set and before the
schema import — and passes the result in.

**Why deriving it internally is wrong.** `get_asgi_application()` calls
`django.setup()`, so *when* it runs is load-bearing: calling it inside the router
constructor would place Django initialization after the consumer's schema import (which
itself imports models and calls `finalize_django_types()`), producing
`AppRegistryNotReady` for some consumers and working by accident for others depending on
import order in `asgi.py`. Requiring the parameter makes the ordering the consumer's
explicit, visible, documented decision — and Django's own ASGI documentation already
puts `get_asgi_application()` at exactly that point. Requiring it also makes the
security property *structural*: there is no code path in which HTTP is served without
Django.

**Why both a required parameter and an explicit-`None` check.** A required positional
parameter makes `DjangoGraphQLProtocolRouter(schema)` fail immediately, but Python's
`TypeError` cannot explain that the deployment was insecure. A migrant carrying
`django_application=None` from `0.0.14` binds the signature successfully and needs the
prose. Both paths therefore fail, with the second one explaining why.

**Alternatives rejected.**

- **Keep it optional and warn.** Rejected: [`AGENTS.md`][agents] #"never propose
  ship-it-today-defer-the-real-fix sequencing" — and the audit's own closing line, "Do
  not split these into 'ship the warning now, fix the architecture later' work."
- **Derive it internally with a lazy `get_asgi_application()` call.** Rejected on the
  initialization-order ambiguity above; a framework must not make Django's setup point
  implicit.
- **Accept a dotted path string and import it.** Rejected: it adds an import-time failure
  mode and a second way to spell the same thing, for no security gain.
- **Raise `ImproperlyConfigured` instead of `ConfigurationError`.** Rejected:
  [`ConfigurationError`][glossary-configurationerror] is the package's single typed
  configuration failure and is already the router module's available exception with no
  new import.

### Decision 4 — `url_pattern` becomes `websocket_url_pattern`, with exact matching as the secure default

**Decision.** The `url_pattern` parameter is **renamed and narrowed** to
`websocket_url_pattern`, keyword-only, defaulting to `r"^graphql/?$"`. It governs the
WebSocket branch **only**; HTTP path matching belongs entirely to the Django URLconf.
There is no aliased `url_pattern=` kwarg kept for compatibility.

`r"^graphql/?$"` is anchored at both ends, so — with Channels' leading-slash strip —
`/graphql` and `/graphql/` match and `/graphql-admin`, `/graphqlanything`,
`/graphql/extra` do not. That is the explicit policy the card's test plan demands, and it
preserves the URLs a `0.0.14` WebSocket client already uses while closing the overmatch.

**Why rename rather than keep one shared parameter.** A single parameter that no longer
affects HTTP would be a name that lies. The rename is the diff that tells a migrant the
semantics changed; silently narrowing `url_pattern`'s meaning would let a consumer keep
a custom HTTP-shaped regex that now does nothing to HTTP.

**Why exact rather than prefix.** A prefix default is a default that over-claims paths,
and the audit's probe demonstrates the consequence on the branch that mattered. On
WebSocket the blast radius is smaller than on HTTP — an over-claimed WS path denies a
handshake rather than exposing one — but the correct default is still the narrow one, and
a consumer wanting a prefix can pass one deliberately.

**Alternatives rejected.**

- **Keep `url_pattern` and accept both spellings.** Rejected: two names for one knob,
  and the compatibility alias would silently accept an HTTP-intended pattern.
- **Default to `r"^ws/graphql/?$"`** (a conventional WS-only path). Rejected: it breaks
  every `0.0.14` WebSocket client for a cosmetic gain, and the endpoint path is the
  consumer's choice.
- **Keep the prefix default and document the overmatch.** Rejected: documenting a
  routing surprise is not fixing it.

### Decision 5 — Compatibility policy: an intentional alpha breaking change to a security boundary

**Decision.** This card **intentionally breaks** the `0.0.14` byte-compatible upstream
constructor contract that [`spec-041`][spec-041] Decision 6 established. Three changes
are breaking: `django_application` becomes required, `url_pattern` is renamed to
`websocket_url_pattern`, and GraphQL HTTP now requires a `urlpatterns` entry that
`0.0.14` deployments do not have. The break is announced, migrated, and tested — not
mitigated by a flag.

**Why this is the right trade.** The package is at `0.0.14` and its documented API
freeze begins at `1.0.0`; strict SemVer applies from `1.0.0` forward, not before. The
broken promise was itself a migration convenience — "a migrant changes exactly the import
line" — purchased by inheriting an upstream HTTP branch now confirmed to bypass Django's
security middleware on a route that accepts session credentials. Preserving byte
compatibility with that contract means preserving the defect for every consumer who
adopts the router. Correcting a newly confirmed security-boundary error during alpha
costs a documented migration note; deferring it to `1.0.0` costs every deployment in
between. The package's status line already says "alpha-quality, not production" — this is
precisely the latitude that statement buys, and spending it here is what makes the
statement retractable later.

**What is explicitly *not* broken.** The
[`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] symbol name and
import path, the [soft-`channels`][glossary-soft-dependency] guard and its install hints,
the [PEP 562 lazy export][glossary-pep-562-lazy-export] shape, the WebSocket composition
and its Origin semantics, the schema pass-through, and the package's
[Channels request adapter][glossary-channels-request-adapter] read path on WebSocket.

**Alternatives rejected.**

- **A `0.1.0`-gated break.** Rejected: it leaves the blocker live across the whole
  remaining alpha line, and `0.1.0` is the beta cut-over — the worst moment to land a
  transport rewrite.
- **A compatibility shim accepting the old signature with a `DeprecationWarning`.**
  Rejected: the shim's only behavior would be to construct the insecure router, which is
  the thing being removed. A warning that precedes an exploitable default is decoration.
- **A new symbol beside the old one** (`DjangoGraphQLProtocolRouter2`, or a
  `SecureDjangoGraphQLProtocolRouter`). Rejected: it keeps the unsafe symbol importable
  and installs a naming wart permanently, to spare a documented one-time migration.

### Decision 6 — The GraphQL HTTP endpoint is a package-owned Django view in the consumer's URLconf

**Decision.** The package ships `django_strawberry_framework/views.py` with
`DjangoGraphQLView` (subclassing `strawberry.django.views.GraphQLView`) and
`AsyncDjangoGraphQLView` (subclassing `AsyncGraphQLView`). The migration note and the
`urlpatterns` entry name the package view, and it is the seam that carries S2's body cap.
It is a leaf-module import — `from django_strawberry_framework.views import
DjangoGraphQLView` — never a package-root export, matching the established posture for
every integration surface (`routers.py`, `middleware/debug_toolbar.py`,
`extensions/`). It resolves both of the card's open API questions at once: the package
does ship a view, and the exact `urlpatterns` entry is the one above.

The subclass adds **one** behavior — the cumulative body cap — and inherits everything
else. Every upstream kwarg (`graphql_ide`, `allow_queries_via_get`,
`multipart_uploads_enabled`, `subscriptions_enabled`) keeps working, unchanged, so the
S1 regression proving `graphql_ide=None` and `allow_queries_via_get=False` are supported
is a proof about the shipped surface rather than about a package reimplementation.

**Why a package view rather than pointing consumers at Strawberry's.** Four reasons, in
order of weight. (a) It is the only home for the S2 cap that works identically on WSGI
and ASGI, sync and async — Django's own view layer. (b) It gives the migration note one
canonical line instead of a fork between "use upstream's view" and "except when you want
the cap". (c) Under the [live-first coverage mandate][glossary-live-first-coverage-mandate]
every S2 regression row is then earnable over fakeshop's real `/graphql/` with
`django.test.Client`, rather than mocked at the package tier — decisive, because a body
limit asserted against a fake request proves nothing about the transport. (d) It is where
the later cards' transport-shaped bounds (S3's budget, S4's upload limits, S10's error
policy) will need to live, so the seam is created once rather than three times.

**Why a subclass rather than a wrapper decorator.** A decorator around
`GraphQLView.as_view()` cannot reach the request before Django's view dispatch in a way
that composes with `as_view(...)` kwargs, and it would leave the cap invisible to anyone
reading the URLconf. The subclass keeps one symbol in the URLconf and one place to look.

**Alternatives rejected.**

- **Point consumers directly at `strawberry.django.views.GraphQLView`.** Rejected: it
  leaves S2 with no seam on the HTTP path at all, which is precisely the gap the
  maintainer's direction forbids representing as closed.
- **Put the cap in Django `MIDDLEWARE`** (a package-shipped `BodyLimitMiddleware`).
  Rejected: it applies project-wide rather than to the GraphQL endpoint, needs a path
  predicate to avoid capping unrelated upload views, and burdens every consumer with a
  `MIDDLEWARE` edit the [Debug-toolbar middleware][glossary-debug-toolbar-middleware]
  precedent shows is easy to get wrong.
- **Put the cap in an ASGI wrapper inside the router.** Rejected as the *primary* seam:
  it cannot serve a WSGI deployment, it cannot serve a consumer who adopts the view
  without the router (which this card makes the common case, since the view needs no
  `channels`), and it would place a GraphQL-specific limit on every path the Django app
  serves. Its one genuine advantage — rejecting mid-stream before Django spools the body
  — is real, and is exactly what
  [Decision 8](#decision-8--the-deployment-layer-cap-is-a-co-requirement-not-an-alternative)
  assigns to the deployment layer, where it belongs and already exists.

### Decision 7 — The app-level body cap lives in the package Django view, counted not declared

**Decision.** `DjangoGraphQLView` / `AsyncDjangoGraphQLView` enforce a cumulative
request-body ceiling before `parse_json` and before schema execution:

1. **Declared over-limit rejects immediately.** If `CONTENT_LENGTH` is present and
   exceeds the limit, return `413` without reading the body.
2. **Actual bytes decide otherwise.** For a non-multipart request, measure the real body
   length and reject at `413` if it exceeds the limit — a `Content-Length` that is absent
   or lying cannot buy a larger body. On ASGI this composes with Django's own
   seekable-stream check on the spooled size; on WSGI Django's `LimitedStream` truncates
   reads at the declared length, so the declared value cannot understate what the
   application receives.
3. **Multipart is bounded by declaration plus Django's parser, not by materializing the
   body.** For a multipart request the view applies step 1 and then hands off to Django's
   `MultiPartParser` rather than reading `request.body` — reading it would force the whole
   payload into memory and defeat Django's streaming upload handlers, breaking the
   [`Upload` scalar][glossary-upload-scalar] path this package ships. Per-file count,
   per-file size, and aggregate size are [`TODO-ALPHA-066-0.0.16`][kanban] (audit S4);
   this card's contract for multipart is the declared-size gate plus an explicit
   statement of what it does and does not bound.
4. **The limit is configured once, overridable per mount.** `MAX_REQUEST_BODY_BYTES` in
   `DJANGO_STRAWBERRY_FRAMEWORK`, overridden by a `max_request_body_bytes=` view kwarg —
   the constructor > setting > default precedence the shipped
   `NESTED_CONNECTION_STRATEGY` knob established. **The package default is `1_048_576`
   (1 MiB)** — the "default" rung of that ladder, and the value the settings example above
   shows: a GraphQL request body is a query document, so its legitimate size sits orders of
   magnitude below Django's upload-shaped 2.5 MB `DATA_UPLOAD_MAX_MEMORY_SIZE`. It is stated
   once in the package, in `conf.py`'s reader, and the view never restates it. `None`
   disables the package cap explicitly; a `None` *kwarg*, by contrast, means "this mount did
   not override anything" and defers to the setting, so a single mount cannot disable a cap
   the project has set.

**Why its own key rather than `DATA_UPLOAD_MAX_MEMORY_SIZE`.** Django's knob is
project-wide and shared with file uploads: a project that raises it to accommodate an
upload endpoint silently raises the GraphQL body ceiling to match. A GraphQL request body
is a *query document*, whose legitimate size is orders of magnitude smaller than a file
upload, so the two want different numbers. Django's knob is also not a package contract
— the package cannot test "our limit holds" against a value the consumer owns for
unrelated reasons. Both still apply, and whichever is lower wins; the tests assert which
one fired.

**Why the view rather than earlier.** No application-level cap can prevent the ASGI
server or Django's `read_body` from *receiving* the bytes — `read_body` drains the whole
request into a spooled temporary file before any cap is evaluated. That is not a defect
this card can fix in the application, and pretending otherwise is exactly the
misrepresentation the maintainer's direction forbids. What the view *can* guarantee, and
does, is that the application never parses, allocates a document from, or executes a
schema against an over-limit body, and that the rejection is a tested package contract
with a controlled `413`. The un-fixable half is [Decision 8](#decision-8--the-deployment-layer-cap-is-a-co-requirement-not-an-alternative).

**Alternatives rejected.**

- **Trust `Content-Length` alone.** Rejected by the maintainer's direction and correct on
  the merits: the header is client-supplied and, on ASGI with chunked transfer, may be
  absent entirely.
- **Documented `DATA_UPLOAD_MAX_MEMORY_SIZE` reliance plus a thin wrapper.** Rejected on
  the shared-knob argument above, plus: it would make the package's most security-visible
  bound something the package neither owns nor tests.
- **An ASGI/middleware guard as the primary seam.** Rejected in
  [Decision 6](#decision-6--the-graphql-http-endpoint-is-a-package-owned-django-view-in-the-consumers-urlconf);
  its mid-stream advantage is reassigned to the deployment layer.
- **Pre-reading the stream in chunks and stashing `request._body`.** Rejected: it
  duplicates what Django's `body` property already does, mutates a private attribute, and
  would make `request.body` raise `RawPostDataException` if the ordering ever drifted.
- **Rejecting inside `_patched_parse_json`.** Rejected: the patch modules exist to fix
  *upstream defects*; a package size policy is not a defect fix, it would fire on GET
  query-param parses, and it would be unreachable for a multipart request.

### Decision 8 — The deployment-layer cap is a co-requirement, not an alternative

**Decision.** The spec documents an explicit reverse-proxy / ASGI-server body cap as a
**required** part of the deployment contract, with concrete directions
(`client_max_body_size` on nginx, `--limit-request-field-size` / equivalents on the ASGI
server, and the note that Daphne's request-buffer size controls fragment delivery rather
than total accepted body). Slice 5's transport guidance states plainly that routing
through Django restores the authoritative middleware lifecycle but **does not**
automatically provide every transport resource bound, and that the package's view cap
bounds what the application *processes*, not what the server *accepts*.

**Two surfaces, one per slice.** This decision is documentation, and it is documentation on
two distinct surfaces that two different slices own — stated here so neither slice can read
the other's obligation as its own:

- **Slice 2 owns the code-documentation surface**, because it is the slice that authors the
  code being documented and no later slice edits those files: `conf.py`'s
  `MAX_REQUEST_BODY_BYTES` key comment (the surface a consumer reads while configuring the
  key) and `views.py`'s cap-contract docstring (the surface a consumer reads while mounting
  the view) each state that the deployment-layer cap is required *alongside* the package
  cap, never an alternative to it, and each state the `read_body`-already-spooled boundary
  that makes it so. A settings key whose own comment omits the co-requirement for a whole
  release is the exact misreading this decision exists to prevent, so the statement ships
  with the key rather than after it.
- **Slice 5 owns the consumer-facing prose surface**: the [`docs/README.md`][docs-readme]
  transport guidance, where the concrete directives above live, together with the multipart
  carve-out (for a multipart request the bound is the declaration plus Django's
  `MultiPartParser`, not a byte count).

**Why this is a decision and not a documentation footnote.** The most likely failure of
this card is not a code bug — it is a reader concluding "S1 fixed the transport, so S2 is
handled." Django's `ASGIHandler.read_body` refutes that in source: it buffers the full
request, rolling to disk past `FILE_UPLOAD_MAX_MEMORY_SIZE`, *before* `HttpRequest.body`
evaluates any limit. So an unbounded request still consumes bandwidth and disk on a
Django-routed deployment. Naming that boundary explicitly, in a numbered decision, is
what keeps the two layers from collapsing into one in the reader's head.

**Alternative rejected.** Treating the application cap as sufficient and mentioning the
proxy in passing. Rejected: it would restate the exact conflation the audit called out,
and would make the package's own documentation the source of a false guarantee.

### Decision 9 — The strict UTF-8 wire contract is enforced once, in `_patched_parse_json`

**Decision.** `_strawberry_patches.py::_patched_parse_json` decodes `bytes` input with
**strict UTF-8** before delegating to the captured upstream `parse_json`. A
`UnicodeDecodeError` from that decode reaches the existing translation and becomes the
same `HTTPException(400, "Unable to parse request body as JSON")` the patch already
raises. A `str` input (the GET query-param path, which Django has already decoded) is
passed through untouched, and the existing `_patched_parse_query_params` shield keeps the
body-envelope guard off those two sites regardless.

`_cross_web_patches.py::_patched_body` **keeps returning raw
`self.request.body` bytes**, and its docstring is rewritten. This is the load-bearing
half of the decision and needs stating precisely: the patch's job is to stop the sync
adapter from UTF-8-decoding *inside a property*, because a `UnicodeDecodeError` raised
there escapes `parse_json`'s `except` and surfaces as an unhandled `500` — the original
upstream bug. Moving the strict decode into `_patched_parse_json` keeps the raise inside
the one scope that can translate it, and — because both the sync and async views inherit
the single `BaseView.parse_json` — fixes both transports from one site. The patch pair's
existing joint ownership of the malformed-body contract is unchanged; only the *success*
set narrows.

Both patches keep installing where they install today — from
`apps.py::DjangoStrawberryFrameworkConfig.ready` at Django app load, the
[Django `AppConfig`][glossary-django-appconfig] seam — and keep their shared
`APPLY_UPSTREAM_PATCHES` gate. A consumer who disables the Strawberry patch therefore
opts out of the strict wire contract along with the malformed-body hardening the pair
already jointly owns; the docs state that consequence rather than splitting the gate.

**Which docs, by surface.** The same split
[Decision 8](#decision-8--the-deployment-layer-cap-is-a-co-requirement-not-an-alternative)
states for the body cap: the **code-documentation** surface belongs to the slice that
authors the code, so Slice 3 discharges it on the `APPLY_UPSTREAM_PATCHES` paragraph of
**both** patch module docstrings — `_strawberry_patches.py` and `_cross_web_patches.py` —
each of which already documents the pair's joint ownership of the malformed-body contract
and must now name the wire contract travelling with the same gate. Naming both is the
point: the consequence differs per half (without the `cross_web` half an undecodable body
is an unhandled `500`; without the Strawberry half the wire contract is absent and a
UTF-16 / UTF-32 body silently succeeds), so a consumer who reads only the module they
disabled still learns what they gave up. Any consumer-facing restatement is Slice 5's
transport deployment guidance, not a third code surface.

**What this means for `_patched_body` after S1.** The patch is unaffected by the protocol
split and remains necessary. It patches `cross_web.DjangoHTTPRequestAdapter`, the **Django
view's** sync request adapter — the very path S1 makes authoritative — not anything
Channels-owned. If anything, S1 raises the patch's importance: previously a
Channels-routed deployment never reached that adapter at all.

**Why the decode belongs in the patch module rather than in the new view.** The UTF-8
wire contract is a property of GraphQL-over-HTTP request parsing, which the patch module
already owns end-to-end for both transports and both encodings-of-failure. Enforcing it
in `views.py` would cover only consumers who adopt the package view, would miss the async
view's own parse path unless duplicated, and would split one contract across two modules
— the single-siting rule [`request_from_info`][glossary-request_from_info] already
establishes for request decoding.

**Measured behavior** (verified, not assumed — the full shape set, so no reader has to
infer a sibling's behavior from a named one):

| request body | strict `decode("utf-8")` | `json.loads(str)` | outcome |
|---|---|---|---|
| plain UTF-8 (ASCII or multi-byte) | ok | ok | **success** |
| UTF-16 with BOM | `UnicodeDecodeError` | — | `400` at the decode |
| UTF-32 with BOM | `UnicodeDecodeError` | — | `400` at the decode |
| an invalid UTF-8 byte inside otherwise-JSON | `UnicodeDecodeError` | — | `400` at the decode |
| raw binary | `UnicodeDecodeError` | — | `400` at the decode |
| UTF-16-LE without BOM | ok | `JSONDecodeError` | `400` at `json.loads` |
| UTF-16-BE without BOM | ok | `JSONDecodeError` | `400` at `json.loads` |
| UTF-32-LE without BOM | ok | `JSONDecodeError` | `400` at `json.loads` |
| UTF-32-BE without BOM | ok | `JSONDecodeError` | `400` at `json.loads` |
| UTF-8 with BOM | ok | `JSONDecodeError` | `400` at `json.loads` |

Every non-UTF-8 form therefore reaches a `400` through an existing path, with **no new
rejection branch** to write or cover. The authoritative split across the nine rejected
shapes is **4 `UnicodeDecodeError` / 5 `json.JSONDecodeError`**: the BOM'd multi-byte
forms carry a leading byte that is not valid UTF-8, while the BOM-less multi-byte forms
decode into NUL-studded text that only the parser refuses. Status and message are
identical across all nine — deliberately, so one byte sequence has one interpretation at
every hop — which makes `__cause__` the only thing that records which mechanism fired, and
the only way a test can pin the five **inherited** rejections against a future `json`
that tolerated them.

**Alternatives rejected.**

- **Decode inside `_patched_body`.** Rejected: it re-creates the unhandled-`500`
  path the patch module exists to close, and it would only fix the sync transport.
- **Reject non-UTF-8 by sniffing leading bytes** (a BOM / NUL-pattern check). Rejected: a
  bespoke encoding sniffer is a parser, and adding a second parser to close a parser
  differential is self-defeating. `bytes.decode("utf-8")` is the contract.
- **Set a strict codec on the adapter and let `json.loads` see a `str` everywhere.**
  Rejected: it changes the async adapter's contract too and re-introduces the property-
  scope raise; the sync/async symmetry the current patch pair achieves would be lost.

### Decision 10 — A UTF-8 BOM is rejected

**Decision.** A leading UTF-8 BOM (`EF BB BF`) makes the request a `400`. The package
does **not** strip it, and does not decode with `utf-8-sig`.

**Why reject.** RFC 8259 §8.1 says implementations MUST NOT add a BOM and **MAY** ignore
one — permission, not obligation — so both directions are conformant and the choice is
ours to justify. Three reasons decide it. (a) It is the direct consequence of the strict
decode: a BOM'd body decodes to a `str` beginning `﻿`, which `json.loads` rejects,
so rejection needs zero extra code and no lenient branch whose behavior could drift from
the declared contract. (b) Accepting-and-stripping re-creates precisely the parser
differential S9 exists to close: a proxy, WAF, access log, or body scanner that does not
strip the BOM sees a different document than the application does. Rejecting means one
byte sequence has one interpretation at every hop. (c) A GraphQL-over-HTTP request body
is machine-generated by a client library, not a hand-saved text file; a BOM signals a
misconfigured client, and a `400` is the fastest way for that client's author to find
out.

**Alternative rejected.** Accept-and-strip via `utf-8-sig` or an explicit
`lstrip("﻿")`. It is friendlier to one misconfigured client and is what several JSON
parsers do — but it reintroduces the differential above, adds a lenient pre-processing
step the contract must then document and test, and buys tolerance for a payload no
correct GraphQL client emits. Documented here as the considered-and-rejected direction so
a future reader knows the choice was deliberate rather than incidental.

### Decision 11 — A WebSocket consumer-class/factory injection seam, with a revalidating package default

**Decision.** The router gains `websocket_consumer_class=None`, accepting a
`GraphQLWSConsumer` subclass **or** a factory callable. A class must subclass
`GraphQLWSConsumer` and is mounted through its own `as_asgi(schema=schema)`; a factory is
called as `factory(schema=schema)` and must return the ASGI application to mount. Anything
else — a class that is not a `GraphQLWSConsumer` subclass, or a non-callable — is a
[`ConfigurationError`][glossary-configurationerror] at construction. `None` selects the
package's own `GraphQLWebSocketConsumer`, a thin `GraphQLWSConsumer` subclass that revalidates the
session actor per operation. Whatever is injected, the router applies
`AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([...])))` around it — the
wrappers are the router's, not the consumer's, so an injected class **cannot** escape
Host/Origin validation or authentication. That structural guarantee is the whole reason
the seam is safe to offer.

**Where the revalidation hooks in, and why not `get_context`.** Strawberry's
`GraphQLWSConsumer.get_context` is called **once per connection**, inside
`AsyncBaseHTTPView.run`, before either protocol handler's message loop starts — so it is
not a per-operation seam. The per-operation entries are
`BaseGraphQLTransportWSHandler.handle_subscribe` and the `graphql_ws` sibling's
`handle_start`, reachable through the `graphql_transport_ws_handler_class` /
`graphql_ws_handler_class` class attributes on the view. The package's consumer points
those at two two-line subclasses, each of which awaits one shared package function and
then delegates with `super()`. The revalidation logic is single-sited in that function;
the per-protocol subclasses carry no logic of their own.

**What the revalidation does.** It reloads the session and resolves the actor for the
scope, writes the refreshed actor back onto `scope["user"]`, and rejects the operation
when the session is no longer valid (revoked, flushed, or the user disabled). Writing
back is what makes the rest of the package compose for free: the
[Channels request adapter][glossary-channels-request-adapter] reads
`scope["user"]`, so every surface reached through
[`request_from_info`][glossary-request_from_info] — the
[`get_queryset` visibility hook][glossary-get_queryset-visibility-hook]'s user reads,
[`DjangoModelPermission`][glossary-djangomodelpermission], the
[`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset]
`check_<field>_permission` input gates, and the
[auth-mutation][glossary-auth-mutations] `current_user` path — observes the fresh actor
with **no change to `utils/permissions.py`**.

Two boundary cases the contract states rather than leaves emergent. A connection whose
scope actor is anonymous has no session actor to revalidate, so it passes through with no
session read at all: only an authenticated socket pays the cost. And once an operation is
denied, the scope keeps the stale actor instead of being downgraded to anonymous, so every
later operation on that socket is denied identically — a revoked session must not quietly
become an anonymous one that keeps executing.

**The bounded window is explicit.** `websocket_revalidation_window=0.0` (the default)
revalidates every operation. A positive value is an accepted revocation delay in seconds,
expressed as a number in the constructor so the delay is a stated deployment decision
rather than an emergent cache behavior. The docs state the trade in one sentence: one
session read per operation, or a named number of seconds during which a revoked session
still executes.

**Why this and not the alternatives.**

- **Revalidate lazily in `ChannelsRequestAdapter.user`.** Rejected: it only fires when
  the package happens to read the actor, so an operation touching no permission gate
  would execute with no revalidation at all — failing the "reload the actor **before
  execution**" requirement — and it can only affect a read, never reject an operation.
- **Revalidate in the consumer's `receive()`.** Rejected: `receive` sees every frame,
  including keep-alive pongs and `complete` messages, so it would fire a session read per
  frame; and at that layer the only available rejection is closing the socket, not
  failing one operation.
- **Ship a periodic background refresh task.** Rejected: it makes freshness a function of
  wall-clock luck rather than of the operation being authorized, and it adds a task
  lifecycle to a transport helper.
- **Implement the message loop ourselves to own the seam.** Rejected explicitly by the
  maintainer's direction and on the merits: a second GraphQL protocol engine is a
  permanent maintenance surface. Two `super()`-delegating pre-hooks are not an engine.
- **Make revalidation opt-in.** Rejected: the audit's finding is that the default is
  stale; an opt-in fix leaves the default stale. Injecting a custom consumer class is the
  opt-out, and it is an opt-out that requires the consumer to own the concern explicitly.

**One deliberate constraint, stated as a constraint.** The revalidation performs a
session read per authenticated operation (or per window), which is database work on the socket's
critical path. It is pinned to the operation's own resolved alias rather than guessed, per
[Multi-database cooperation][glossary-multi-database-cooperation], and the window exists
precisely so a deployment can price it. This is a cost the audit's finding makes
worth paying, not a cost the spec hides.

### Decision 12 — Maximum connection lifetime is documented and seamed, not silently enforced

**Decision.** The package does **not** impose a maximum WebSocket connection lifetime.
Slice 5 documents (a) that an established socket should have a deployment-enforced
maximum lifetime, (b) the ASGI-server and proxy settings that provide it, (c) the
upstream `connection_init_wait_timeout` and `keep_alive` knobs the injected consumer
class can set, and (d) that with per-operation revalidation on, the freshness bound is
the revalidation window rather than the connection lifetime.

**Why not enforce it.** A framework-imposed disconnect is a visible behavior change for
every subscription consumer, with no correct default: the right lifetime for a dashboard
subscription and for a short-lived request-response socket differ by orders of magnitude.
The audit asks for "at minimum, document a maximum connection lifetime and a
consumer-class injection seam"; the seam ships in
[Decision 11](#decision-11--a-websocket-consumer-classfactory-injection-seam-with-a-revalidating-package-default),
and with revalidation on, lifetime stops being the security-relevant bound.

**Alternative rejected.** A `max_connection_lifetime=` kwarg with a default. Rejected:
either the default is long enough to be security-irrelevant, or it is short enough to
break subscriptions. A consumer who wants it can enforce it in the injected class today.

### Decision 13 — Test strategy: which existing tests change, and why

**Decision.** The card changes existing tests only where they assert the removed
contract, and it says which, explicitly, so a reviewer can distinguish a deliberate
inversion from a regression.

**Rewritten (they encode the old HTTP contract).**

- `tests/test_routers.py::test_http_branch_is_auth_wrapped_and_routes_only_graphql_without_fallback`
  — the HTTP branch is no longer auth-wrapped and no longer routes GraphQL at all.
  Becomes: the `"http"` value **is** the supplied Django application object, identically.
- `::test_django_application_fallback_is_appended_after_the_graphql_route` — there is no
  fallback and no GraphQL route to append after. Becomes: omission is a `TypeError` and
  explicit `None` is a [`ConfigurationError`][glossary-configurationerror].
- `::test_custom_url_pattern_reaches_the_re_path_on_both_branches` — the pattern reaches
  one branch now. Becomes: `websocket_url_pattern` reaches the WebSocket `re_path` only,
  plus an exact-match matrix (`/graphql`, `/graphql/` connect; `/graphql-admin`,
  `/graphqlanything`, `/graphql/extra` do not).
- `::test_http_communicator_graphql_round_trip` and
  `::test_non_graphql_path_reaches_the_fallback_only_when_provided` — both drive the
  removed consumer. Become one test that the HTTP branch delegates to the supplied
  application unchanged.

**Preserved verbatim (they construct no router, so nothing in them moves).** The whole
[eviction-simulated absence][glossary-eviction-simulated-absence] block and the cached-class
test. These are the only literally byte-identical survivors, and the card says so rather
than over-claiming: every other preserved test must at minimum supply the constructor
argument [Decision 3](#decision-3--django_application-is-required-omission-fails-at-construction-with-no-compatibility-fallback)
makes required, so `DjangoGraphQLProtocolRouter(schema)` is a `TypeError` in all of them.

**Preserved in subject and assertion strength (they assert what the card keeps).** Every
WebSocket Origin / auth test survives with its assertions intact and nothing weakened.
Three mechanical facts make "verbatim" unachievable for them, and each is a deliberate,
reviewable change rather than a regression:

1. **The construction line moves; no assertion does.** All of them route through one
   test-module-local builder that supplies `django_application=` in exactly one place, so
   each test changes on one executable line and every assertion stays byte-identical.
   `::test_websocket_handshake_origin_directions` (matching / mismatched / missing Origin)
   changes in that way and no other;
   `::test_request_contract_resolves_over_the_websocket_branch` additionally refreshes its
   docstring, because deleting the HTTP colour of the same contract (below) renumbers it
   and its prose described the HTTP sibling it is now the sole survivor of.
2. **Re-aimed to the WebSocket branch, subject preserved.**
   `::test_schema_object_passes_through_unchanged_with_extensions_intact` and
   `::test_authenticated_session_round_trip_reaches_the_resolver` were HTTP-branch tests —
   the first interrogated the HTTP consumer's `consumer_initkwargs` and executed a POST
   through `HttpCommunicator`, the second sent its session cookie through the HTTP
   branch's `AuthMiddlewareStack`. This card removes the transport underneath them, not
   the property they pin, so both are re-aimed at the WebSocket branch with their subjects
   intact: the schema object passes through untouched with extensions intact, and a real
   session cookie flows through `AuthMiddlewareStack` to the actor. The structural half
   drops only the assertion whose subject no longer exists, and the extension firing count
   holds unchanged on the WebSocket single-result flow.
3. **One assertion literal necessarily tracks
   [Decision 4](#decision-4--url_pattern-becomes-websocket_url_pattern-with-exact-matching-as-the-secure-default).**
   `::test_websocket_branch_wraps_origin_validator_outside_the_auth_stack` is a genuine
   WebSocket Origin test, but its pattern assertion reads the default, so `["^graphql"]`
   becomes `[r"^graphql/?$"]`. The nesting assertion and the "the HTTP value is not an
   `OriginValidator`" assertion are unchanged.

**Repaired harness, call sites and assertions untouched.**
`tests/auth/test_mutations.py::_channels_router` borrowed the `0.0.14` router as this
suite's Channels transport harness, so all eight of its `HttpCommunicator` call sites break
at construction. Its **body** becomes a local `ProtocolTypeRouter` composition of exactly
the shape the `0.0.14` router composed; every call site and every assertion is untouched.
Repair rather than deletion is the correct call because the surface those tests exercise is
not removed by this card — see
[Decision 2](#decision-2--http-dispatches-directly-to-a-required-consumer-supplied-django-asgi-application)
#"What this does not remove" — and because those eight round trips are the only end-to-end
`HttpCommunicator` coverage of the Channels-HTTP auth session lifecycle (cookie mint, key
cycling, durable teardown, reconnect). No coverage claim rests on the harness beyond that:
the `Transport.CHANNELS_HTTP` member itself and both `auth/mutations.py` arms are covered
independently by `tests/auth/test_sessions.py` and by the two non-harness sync-bridge
tests.

**Deleted (its transport is gone; its surviving colour is preserved).**
`::test_request_contract_resolves_through_the_router_for_anonymous_reads` is the HTTP
colour of the [Channels request adapter][glossary-channels-request-adapter] contract, which
the package no longer composes. Its WebSocket colour
(`::test_request_contract_resolves_over_the_websocket_branch`) is preserved, and the two
production lines it uniquely touched — `utils/permissions.py::ChannelsRequestAdapter.__getattr__`
and `::_channels_scope`'s `consumer.scope` branch — are covered independently by
`tests/utils/test_permissions.py`, which must be read and confirmed before the deletion
lands rather than assumed.

**Inverted (they assert encodings the card rejects).** The three
`test_products_api.py` UTF-16/32/BOM success tests become `400` assertions, keeping their
docstrings' explanation of *why* each byte sequence used to succeed — the history is the
point. `tests/test_cross_web_patches.py`'s raw-bytes contract tests are re-aimed: the
adapter still returns raw bytes (that contract is unchanged), and the new assertion is
that the strict decode in `_patched_parse_json` is what rejects them.

**Placement.** The S1 middleware / Host / CSRF / header / cache / routing regressions and
the entire S2 body-cap matrix live in `examples/fakeshop/test_query/` over the real
`/graphql/` — fakeshop already serves a Django GraphQL view, so the
[live-first coverage mandate][glossary-live-first-coverage-mandate] applies with no
exemption. The router's composition assertions and the WebSocket revalidation matrix stay
in `tests/test_routers.py` (communicator-driven), the documented
genuinely-unreachable-live case. `tests/test_views.py` is new and holds only what a live
request cannot reach — in Slice 1 the import-boundary and public-surface contracts (the
`channels`-free import proof, the `as_view()` kwarg-binding matrix, the async-twin
coroutine marking, and the exact `__all__` / stays-off-the-package-root assertion), and in
Slice 2 the cap's argument validation and the settings-precedence matrix.

### Decision 14 — This card amends `spec-041` and supersedes three of its decisions

**Decision.** Slice 5 edits [`spec-041`][spec-041] in place, adding an amendment banner
immediately under its title that names this spec and lists exactly what is superseded:

- **Decision 6 (constructor parity)** — superseded in full. The signature is no longer
  byte-compatible with upstream.
- **Decision 2 (card-scope boundary)**, HTTP half — superseded. Its scoping of "the
  transport router ships" assumed a package-owned HTTP branch.
- **Borrowing posture**, the HTTP-branch and Django-fallback paragraphs — superseded by
  this spec's [Borrowing posture](#borrowing-posture).

Everything else in `spec-041` stands: Decision 3 (the symbol name), Decision 5 (the soft
dependency), Decision 7 (engine-owned consumers — now with the injection seam layered
over it), Decision 8 (the test strategy), Decision 10 (joint-cut version ownership), and
Decision 11 (the Channels request contract).

**Why amend rather than leave it as history.** `spec-041` is the standing design record
for a module that still exists and is still imported; a reader who finds it and follows
its constructor documentation would wire the insecure shape. This is the narrow case
where a shipped spec's prose becomes factually wrong about live code, and the repo's
practice is to correct the record in the same change rather than let two documents
disagree.

**Alternative rejected.** Leaving `spec-041` untouched and relying on this spec to
supersede it implicitly. Rejected: implicit supersession between two specs at different
paths is exactly how a reader ends up following the wrong one.

### Decision 15 — The `0.0.15` version bump is deferred to the joint cut

**Decision.** No slice in this card edits any part of the version quintet:
`[project].version` in `pyproject.toml`, `__version__` in
`django_strawberry_framework/__init__.py`, `tests/base/test_init.py::test_version`, the
[`docs/GLOSSARY.md`][glossary] package-version line, or the root package `version` entry
in `uv.lock`. This card **shares the `0.0.15` patch line** with
[`TODO-ALPHA-045-0.0.15`][kanban] (both non-Done at authoring time), so the bump from
`0.0.14` to `0.0.15` is owned by the [joint version cut][glossary-joint-version-cut] —
the last `0.0.15` card to land — exactly as [`spec-041`][spec-041] Decision 10 pinned for
the joint `0.0.14` cut.

The release-status wording splits the same way. Slice 5 updates
**implemented-on-main** docs — the GLOSSARY entry bodies, the regenerated
[`docs/TREE.md`][tree], the migration note and transport guidance in
[`docs/README.md`][docs-readme] — but the public `shipped (0.0.15)` status flips, the
[`README.md`][readme] / [`docs/README.md`][docs-readme] "Coming next" → "Shipped today"
moves, and the `CHANGELOG.md` bullets all defer to the cut. Otherwise the repo would
advertise a released `0.0.15` transport contract while `__version__` still reports
`0.0.14`.

**`uv.lock` is not touched at all by this card.** Unlike `spec-041`, this card adds no
dependency: `channels` is already in the dev group, and the new view rides the existing
hard `strawberry-graphql` requirement.

**Alternatives rejected.**

- **Bump to `0.0.15` in Slice 5.** Rejected: card `045` also ships into `0.0.15`; a
  per-card bump races the joint cut and gets reconciled twice.
- **Claim the cut for this card because it is the higher-numbered / more urgent one.**
  Rejected: the rule keys on *last to land*, not on card number or priority, and the
  landing order is the maintainer's to decide.
- **Ship the `CHANGELOG.md` entry here and let the cut add the version.** Rejected: the
  [joint version cut][glossary-joint-version-cut] contract puts the `CHANGELOG.md`
  bullets in the cut, and [`AGENTS.md`][agents] requires an explicit grant this card does
  not hold.

## Implementation plan

| Slice | Finding | Where | Work | Risk profile |
|---|---|---|---|---|
| 1 | S1 | `routers.py`, new `views.py`, `tests/test_routers.py`, new `tests/test_views.py`, live tier | protocol split; required `django_application`; `websocket_url_pattern`; the package view; rewrite 5 router tests; live middleware / Host / CSRF / header / cache / routing proofs | **HIGH** — the breaking change; every downstream slice builds on the new shape |
| 2 | S2 | `views.py`, `conf.py`, live tier, `tests/test_views.py` | cumulative cap pre-parse; `MAX_REQUEST_BODY_BYTES` + view kwarg; the full regression matrix incl. the py3.10 / Django 5.2.0 floor | MED — multipart interaction with the [`Upload`][glossary-upload-scalar] path is the sharp edge |
| 3 | S9 | `_strawberry_patches.py`, `_cross_web_patches.py` docstring, `test_products_api.py`, `tests/test_cross_web_patches.py` | strict UTF-8 decode in the wrapper; invert 3 live tests; re-aim 2 package tests | LOW — measured behavior, no new branch |
| 4 | S11 | `routers.py`, new package WS consumer + 2 handler pre-hooks, `tests/test_routers.py` | injection seam; revalidation function; window kwarg; revoke-then-operate matrix | MED-HIGH — async, per-operation, communicator-driven |
| 5 | S12 | `docs/`, `spec-041`, glossary DB, kanban DB | migration note; transport guidance; `spec-041` amendment; GLOSSARY + TREE regen; card wrap | mechanical breadth; **no version quintet, no `CHANGELOG.md`** |

Sequencing inside the card is strict: **Slice 1 first and alone.** Slices 2 and 4 both
need Slice 1's seams (the view and the consumer-injection point respectively); Slice 3 is
independent of all of them and could land in parallel, but its inverted live tests share
`test_products_api.py` with Slice 2's new body-cap tests, so landing it after Slice 2
avoids a merge on that file. Slice 5 last, because it documents what the first four
actually did.

Staged-but-unbuilt slices carry `TODO(spec-065 Slice N)` source anchors at the sites they
will change, paired with `NotImplementedError` where a call path must fail loudly, and
removed in the change that ships the slice — the repo's standing staging discipline.

## Helper-reuse obligations (DRY)

- **The settings read goes through `conf.py`'s existing `Settings` reader.** No local
  `getattr(settings, ...)`; `MAX_REQUEST_BODY_BYTES` joins the existing key block with
  its own module-level key constant, exactly like `NESTED_CONNECTION_STRATEGY`.
- **The construction-time failure is [`ConfigurationError`][glossary-configurationerror]**,
  the package's single typed configuration error — not a new exception class, not
  `ImproperlyConfigured`, not `ValueError`.
- **The soft-`channels` guard is unchanged.** `require_channels()` over
  [`require_optional_module`][glossary-require_optional_module] stays exactly as
  [`spec-041`][spec-041] Decision 5 shaped it, with the same
  `_CHANNELS_INSTALL_HINT` / `_CHANNELS_BROKEN_HINT` /
  `_STRAWBERRY_CHANNELS_BROKEN_HINT` triple and the same `_ROUTER_CLASS` cache the
  [eviction-simulated absence][glossary-eviction-simulated-absence] tests depend on. No
  new guard, no new hint string, no second lazy-export mechanism.
- **The WebSocket revalidation is one function, called from both protocol pre-hooks.**
  The `graphql_transport_ws` and `graphql_ws` subclasses contain a single `await` and a
  `super()` call each; every decision (window expiry, session reload, actor write-back,
  reject-or-continue) lives in the shared function.
- **The actor is written back to `scope["user"]` rather than plumbed to readers.** The
  existing [Channels request adapter][glossary-channels-request-adapter] and
  [`request_from_info`][glossary-request_from_info] single-siting is preserved; this card
  adds **no** new request-context decoder, per that helper's hard single-siting rule.
- **The view subclasses upstream rather than reimplementing it.** One overridden hook for
  the cap; every other behavior inherited from
  `strawberry.django.views.GraphQLView` / `AsyncGraphQLView`.
- **The UTF-8 decode is added to the existing `_patched_parse_json` wrapper**, reusing its
  existing `UnicodeDecodeError` → `HTTPException(400, ...)` translation and its existing
  `_validate_upstream_shape` gate. No new patch module, no second patched method.
- **Live tests start with [`seed_data`][glossary-seed_data]** and route the schema through
  [`Schema reload discipline`][glossary-schema-reload-discipline]'s
  `reload_all_project_schemas()`; the body-cap and header tests use
  [`TestClient`][glossary-testclient] or a raw `django.test.Client` where CSRF
  enforcement (`Client(enforce_csrf_checks=True)`) or a custom `Host` header is required.
  A view configured differently from fakeshop's mounted one (e.g. `graphql_ide=None`)
  uses the existing [Probe URLconf][glossary-probe-urlconf] pattern rather than a new
  harness.

## Edge cases and constraints

- **`APPEND_SLASH` and `POST /graphql`.** With `path("graphql/", ...)`,
  `CommonMiddleware` answers `GET /graphql` with a `301`; a `POST` to `/graphql` also gets
  a `301`, which most HTTP clients will not re-`POST`. The migration note must say so and
  offer the two deliberate resolutions (post to the trailing slash, or declare both
  patterns). This is the "explicit policy" the card's test plan asks for.
- **Django's cap may fire before the package's, and it answers `400` on both transports.**
  If `DATA_UPLOAD_MAX_MEMORY_SIZE` < `MAX_REQUEST_BODY_BYTES`, Django raises
  `RequestDataTooBig` first — but lazily, out of `HttpRequest.body` inside the view, so
  `response_for_exception` maps the `SuspiciousOperation` to a **`400`** on ASGI exactly as
  on WSGI. `ASGIHandler.create_request`'s `413` branch guards only request *construction*,
  which never reads the body, so it never fires for this flow (see
  [Current state](#current-state)). The package's own ceiling is the `413`. Both are correct
  outcomes; the tests assert which fired so the two ceilings are never confused.
- **Never lower `DATA_UPLOAD_MAX_MEMORY_SIZE` in a test row that drives the ASGI handler.**
  That single combination is the one cell where the supported Django range diverges: on 6.0
  the seekable actual-size check rejects the spooled body, at the 5.2.0 floor no such check
  exists and the request succeeds. Django's ceiling is therefore exercised **only** through
  the declared-`CONTENT_LENGTH` path, which is identical on both releases, and every
  ASGI-driven row leaves Django's knob at its default — which is what makes the floor-parity
  row (Test plan row 18) bit-identical rather than merely green.
- **A garbage `Content-Length` is Django's rejection, not the package's.**
  `HttpRequest.body` evaluates `int(self.META.get("CONTENT_LENGTH") or 0)` unguarded, so a
  non-numeric declaration raises `ValueError` from Django before the package's counted check
  can complete. The package never *trusts* such a declaration — its declared-length reader
  returns `None` for both the absent and the unparseable shape, the fail-safe direction — and
  the failure still precedes any JSON parse or schema execution, so the security property
  holds. It is not a regression the cap introduces: a mount with the cap disabled raises
  identically, because the raise happens later, where the request adapter reads the body.
  No test asserts a status code for this shape, deliberately: doing so would pin Django's
  exception as a package contract, and the alternatives — pre-reading the stream or
  rewriting `META` — are both rejected by name in
  [Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared).
  A conforming server rejects such a header before Django sees it.
- **`request.body` is single-shot.** Reading it caches `_body` and rebinds `_stream`;
  reading the *stream* first sets `_read_started` and makes a later `request.body` raise
  `RawPostDataException`. The view must not pre-read the stream, which is why
  [Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)
  measures `request.body` rather than chunk-counting.
- **Multipart must not be materialized.** Reading `request.body` on a multipart request
  forces the whole payload into memory and defeats Django's streaming upload handlers,
  breaking the [`Upload` scalar][glossary-upload-scalar] /
  [`DjangoMutation`][glossary-djangomutation] file path. The cap branches on
  `request.content_type` and applies the declared-size gate only.
- **GET requests carry no body.** The cap is a no-op on GET; the `variables` /
  `extensions` query-param size is a `TODO-ALPHA-066-0.0.16` concern (S4), and the
  existing `_patched_parse_query_params` shield keeps the body contract off those parses.
- **`ALLOWED_HOSTS = []` with `DEBUG=True`** (fakeshop's shape) makes Django accept
  `localhost` / `127.0.0.1` only. The hostile-`Host` live test must therefore assert a
  `400` from Django's own host validation, and must not depend on fakeshop's `DEBUG`
  value; it sets `ALLOWED_HOSTS` explicitly with `override_settings`.
- **The router's `"http"` value is now an opaque callable.** The composition test asserts
  object identity with the supplied application rather than structural equality — there is
  nothing left to introspect, which is the point.
- **`lifespan` scope is unchanged.** Channels' `ProtocolTypeRouter` still raises
  `ValueError` for unmapped scope types; uvicorn's startup probe still logs its benign
  "ASGI 'lifespan' protocol appears unsupported".
- **A revalidation database error must fail closed.** A session-store or auth-alias
  failure during revalidation rejects the operation; it never falls back to the stale
  cached actor. This mirrors the fail-closed posture the shipped
  [auth mutations][glossary-auth-mutations] already take after authentication.
- **The revalidation read is alias-explicit.** Per
  [Multi-database cooperation][glossary-multi-database-cooperation] the session and user
  reads use the router's resolved alias rather than an implicit default, so a
  divergent-router deployment does not silently read auth off the wrong connection.
- **An injected consumer class opts out of revalidation, not out of the wrappers.** The
  Host/Origin and authentication wrappers are applied by the router around whatever is
  injected; a test asserts the wrapper nesting for an injected class as well as for the
  default.
- **`websocket_revalidation_window` is meaningless when a custom class is injected.** The
  constructor rejects the combination rather than silently ignoring the window — a knob
  that does nothing is worse than an error.
- **ASCII-only in `.py`**; trailing-comma layout via `scripts/check_trailing_commas.py`
  with explicit paths (never the repo-wide auto-fix, which would touch untracked
  concurrent work); `ruff format` + `ruff check --fix` after every edit;
  `::QualifiedName` doc references swept when `routers.py`'s symbols change.
- **Coverage.** `fail_under = 100` must hold with `views.py` added. The cap's
  settings-precedence and validation branches are package-tier; every request-shaped row
  is live-tier.

## Test plan

Maintainer-invoked gates only, per [`AGENTS.md`][agents].

**S1 — the HTTP boundary** (live, `examples/fakeshop/test_query/`):

1. A project middleware sentinel executes on the GraphQL HTTP route.
2. `SecurityMiddleware`'s configured headers appear on a GraphQL HTTP response
   (`X-Content-Type-Options`, referrer policy, and the HSTS header under
   `SECURE_HSTS_SECONDS`).
3. A hostile `Host` is rejected on GraphQL **HTTP** (`400`), under explicit
   `override_settings(ALLOWED_HOSTS=[...])`.
4. Cookie-authenticated mutations under `Client(enforce_csrf_checks=True)`: missing token
   → rejected, wrong token → rejected, correct token → succeeds.
5. An authenticated GET response is non-cacheable or varies on `Cookie`.
6. Routing policy: `/graphql/` matches; `/graphql` follows the documented `APPEND_SLASH`
   policy; `/graphql-admin` and `/graphqlanything` reach the rest of the URLconf or `404`.
7. `graphql_ide=None` and `allow_queries_via_get=False` are supported and proven on the
   package view (via a [Probe URLconf][glossary-probe-urlconf]).

**S1 — the router composition** (package, `tests/test_routers.py`):

8. `"http"` is the supplied Django application object, by identity.
9. `GraphQLHTTPConsumer` is not imported or referenced anywhere in `routers.py`.
10. Omitting `django_application` → `TypeError`; explicit `None` and a non-callable →
    [`ConfigurationError`][glossary-configurationerror] whose message names the migration.
11. `websocket_url_pattern` exact-match matrix: `/graphql`, `/graphql/` connect;
    `/graphql-admin`, `/graphqlanything`, `/graphql/extra` do not.
12. Every preserved WebSocket Origin / auth / schema-passthrough /
    [eviction-simulated absence][glossary-eviction-simulated-absence] test still passes
    unmodified.

**S2 — the body cap** (live, plus package-tier for the knob):

13. No `Content-Length`; declared below, at, and above the limit; a declared-small body
    whose streamed content exceeds it; a body arriving in multiple ASGI fragments that
    crosses the boundary.
14. JSON, malformed JSON, and multipart bodies each hit the documented outcome.
15. An early `413` with **proof that neither JSON parsing nor schema execution ran** — a
    resolver / parse sentinel that must not fire.
16. Which ceiling fired: package cap vs. Django's `DATA_UPLOAD_MAX_MEMORY_SIZE`, both
    directions.
17. `max_request_body_bytes=` view kwarg beats `MAX_REQUEST_BODY_BYTES`; the setting beats
    the default; `None` disables the package cap.
18. Parity across the supported **py3.10 / Django 5.2.0 floor** and the current stack
    (isolated venvs; never the shared `.venv`).

**S9 — the wire contract** (live, inverted; plus package-tier):

19. UTF-16 and UTF-32, BOM and BOM-less → `400`.
20. Ordinary UTF-8 → unchanged success.
21. Malformed UTF-8 → `400` (the existing assertion, still green).
22. UTF-8 BOM → `400` (the chosen direction).
23. Sync and async transports behave identically.
24. `_patched_body` still returns raw bytes; the rejection is attributable to the strict
    decode in `_patched_parse_json`.

**S11 — actor revalidation** (package, communicator-driven):

25. Establish a socket, then revoke / flush / disable the session through a **separate**
    request; the next operation is denied **without reconnecting**.
26. A valid session keeps executing, and the refreshed actor — not the connect-time one —
    is what the next operation observes at
    [`request_from_info`][glossary-request_from_info], the single read the
    [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] and
    [`DjangoModelPermission`][glossary-djangomodelpermission] both resolve their actor
    through, so proving freshness there proves both layers. Driving those two layers over
    a socket would need the async live tier fakeshop does not have (see Risks) and would
    put sync ORM on the event loop inside a deliberately ORM-free test module; the proof is
    an out-of-band change to the user row that the next operation reads back.
27. `websocket_revalidation_window` > 0: a revoked session still executes inside the
    window and is denied after it.
28. An injected `websocket_consumer_class` is still wrapped by
    `AllowedHostsOriginValidator` and `AuthMiddlewareStack`.
29. Injecting a class **and** passing a window is a construction error.
30. A revalidation store failure denies the operation (fail-closed), never falls back to
    the cached actor.

**Gates.** Full suite green under `fail_under = 100`; `ruff format` / `ruff check` clean;
`scripts/check_trailing_commas.py --check` clean on the touched paths; `manage.py check`
and `makemigrations --check` clean; pre-commit run before any commit.

## Doc updates

Slice 5's set. Every generated doc is regenerated from its source, never hand-edited.

- **[`docs/README.md`][docs-readme]** — the migration note (old `asgi.py`, new `asgi.py`,
  the required `urlpatterns` entry, the `APPEND_SLASH` policy) and the transport
  deployment guidance (CSRF on the Django view, cache / `Vary` for authenticated
  responses, security headers, IDE and GET controls, the reverse-proxy / ASGI-server body
  cap as a co-requirement, and the WebSocket revalidation window and connection-lifetime
  expectations). The existing "Channels GraphQL consumers do not enforce CSRF" sentence
  in the [session-auth deployment boundary][glossary-auth-mutations] section is corrected:
  HTTP is Django-CSRF-protected now, and the sentence narrows to WebSocket.
- **[`docs/GLOSSARY.md`][glossary]** via the glossary DB + `scripts/build_glossary_md.py`
  re-render — the [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]
  entry rewritten to the new composition and constructor; the
  [Channels request adapter][glossary-channels-request-adapter] entry narrowed to
  WebSocket; the [auth-mutation][glossary-auth-mutations] transport matrix's HTTP row
  corrected; and the new terms this card authors (the package Django view, the body cap,
  the UTF-8 wire contract, the consumer-injection seam, the revalidation window). New
  glossary entries require the maintainer-authorized DB update; they are **not**
  hand-written into the rendered file.
- **[`docs/TREE.md`][tree]** via `scripts/build_tree_md.py` — `views.py` in both the
  current and target package layouts, `tests/test_views.py` in the test trees.
- **[`README.md`][readme]** and **[`TODAY.md`][today]** — the `0.0.14`
  [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] paragraphs, which
  currently advertise "serving GraphQL on both HTTP and WebSocket in one import" and
  "constructor-compatible with upstream", both now false. The public `shipped (0.0.15)`
  status flip and the "Coming next" → "Shipped today" move stay with the joint cut
  ([Decision 15](#decision-15--the-0015-version-bump-is-deferred-to-the-joint-cut)).
- **[`spec-041`][spec-041]** — the amendment banner and the three superseded items
  ([Decision 14](#decision-14--this-card-amends-spec-041-and-supersedes-three-of-its-decisions)).
- **`examples/fakeshop/test_query/README.md`** — the new S1/S2/S9 acceptance rows (the file
  does not mention `test_transport_api.py` at all today, so S1's rows are owed as well as
  S2's), plus the widened raw-envelope exemption: its current "malformed bodies,
  content-type negotiation" wording does not cover S1's hostile-`Host` / `secure=` /
  `enforce_csrf_checks=` / `AsyncClient` rows or S2's in-process `ASGIHandler` driver.
- **`KANBAN.md` / `KANBAN.html`** via the kanban DB + the two render scripts.
- **Untouched:** `CHANGELOG.md` (joint cut, plus an explicit grant this card lacks),
  `GOAL.md` (no north-star change — the transport correction serves the existing migration
  axis), `SECURITY.md` (the production-security profile belongs to the later cards' doc
  slices), and `uv.lock` (no dependency change).

## Risks and open questions

- **`spec-045` Decision 7 is now factually stale, and the joint cut needs one owner.**
  [`spec-045`][spec-045] Decision 7 asserts it is "the **only** card at `0.0.15`" and
  therefore owns the version cut. Card `065` has since joined that patch line, so the
  premise no longer holds and two specs would both claim the quintet. Preferred answer:
  `spec-045` Decision 7 is amended to the joint-cut deferral shape, and whichever of
  `045` / `065` lands **last** carries the quintet plus the `CHANGELOG.md` entry — the
  [joint version cut][glossary-joint-version-cut] rule as written. Fallback: the
  maintainer nominates the cut owner explicitly in the card body, and both specs cite that
  nomination. This spec is written for the deferral either way, so it needs no change
  under either resolution. **Flagged for the maintainer** because amending `spec-045`
  is outside this card's boundary and that spec anchors in-flight work.
- **Whether the required `urlpatterns` entry should be a package-provided
  `include()`.** A `path("graphql/", include("django_strawberry_framework.urls"))` would
  shorten the migration but would have to source the schema from a settings key — a new
  global the package does not want, and a second way to wire a schema. Preferred answer:
  keep the explicit `DjangoGraphQLView.as_view(schema=schema)` line; the schema stays a
  Python object the consumer passes, matching every other package surface. Fallback: an
  `include()` helper as an additive convenience in a later card, never as the documented
  primary.
- **Async view adoption.** An ASGI deployment arguably *wants*
  `AsyncDjangoGraphQLView`, but the package's live tier is WSGI and its mutation pipeline
  is sync-first. Preferred answer: ship both, document the async twin, and make the
  migration note's default the sync view (matching what fakeshop proves); a consumer on
  ASGI chooses the async one deliberately. Fallback: ship the sync view only and add the
  async twin when a live async tier exists — rejected for now because an ASGI-shaped card
  that omits the async view would be an odd omission.
- **The revalidation's per-operation query cost.** One session read per operation is real
  work on a socket's critical path, and the bounded window is the only mitigation this
  card ships. Preferred answer: default to `0.0` (always revalidate), document the window
  with the trade stated in one sentence, and let a measured deployment price it. Fallback:
  if a later benchmark shows the read dominating a subscription-heavy workload, a
  session-store-level cache belongs to [`TODO-ALPHA-066-0.0.16`][kanban]'s resource
  policy, not to a second knob here.
- **`websocket_url_pattern`'s default keeps a WS path that HTTP no longer serves.** After
  this card, `^graphql/?$` on WebSocket and `graphql/` in the URLconf are two independent
  declarations that a consumer must keep in sync by hand. Preferred answer: document that
  they are independent and why (Django owns HTTP matching, Channels owns WS matching) —
  the coupling is the thing being removed, so re-coupling them would undo the fix.
  Fallback: none; a shared-pattern convenience would reintroduce exactly the conflation
  S1 exists to break.
- **Fakeshop still has no `asgi.py`, so the router half stays package-tier-only.** The
  HTTP half of this card is now fully live-testable (fakeshop serves a Django GraphQL
  view), but the WebSocket revalidation matrix is not. Preferred answer: keep the
  documented genuinely-unreachable-live exemption for the router, as
  [`spec-041`][spec-041] Decision 8 established, and revisit at the fakeshop-activation
  card. Fallback: a `tests/`-local ASGI harness — rejected as a second harness for the
  same thing.
- **A consumer who adopts the view without the router gets no WebSocket at all.** That is
  correct and intended, but it is a new shape the docs must name explicitly: the HTTP half
  of this card is `channels`-free, and a WSGI project can take the body cap and the UTF-8
  contract without ever installing the soft dependency.

## Out of scope (explicitly tracked elsewhere)

- **Audit S3 / S4 — the request resource policy.** Query depth / complexity / cost
  budgets, variable cardinality, collection bounds, per-file and aggregate upload limits,
  and bounded Relay many-side defaults: [`TODO-ALPHA-066-0.0.16`][kanban]. This card
  ships one transport bound and hands that card the view seam to hang the rest on.
- **Audit S5 — `DjangoFileType.path` in the safe generated output.**
  [`TODO-ALPHA-066-0.0.16`][kanban] / [`TODO-ALPHA-067-0.0.17`][kanban] per the program's
  staging; the [`DjangoFileType`][glossary-djangofiletype] /
  [`DjangoImageType`][glossary-djangoimagetype] output shape is untouched here.
- **Audit S8 / S10 — debug and unexpected-error disclosure failing closed under
  `DEBUG=False`.** [`TODO-ALPHA-067-0.0.17`][kanban]. The
  [developer-only debug posture][glossary-developer-only-debug-posture] and the
  [debug-toolbar middleware][glossary-debug-toolbar-middleware] gating are named in this
  card's transport guidance but not changed by it.
- **Audit S6 / S7 — stale Django resolutions and CI authority / supply-chain pins.**
  [`TODO-ALPHA-068-0.0.18`][kanban].
- **The rest of audit S12 — the full deployment contract.** The `SECURITY.md`
  production-security profile, the mechanical `check --deploy`-style checklist, the
  GlobalID-is-not-a-capability statement, upload-safety guidance beyond body size, and the
  "fakeshop must never be deployed" conspicuous notice: the later cards' doc slices. This
  card ships **only** the migration note plus transport deployment guidance.
- **Secure-default changes to `graphql_ide` / `allow_queries_via_get` / introspection.**
  [`TODO-ALPHA-067-0.0.17`][kanban]. This card proves the knobs work; it does not move
  their defaults.
- **A fakeshop ASGI surface and live Channels acceptance tier.** The
  fakeshop-activation card, if the maintainer wants it at all.
- **The `0.0.15` version quintet and `CHANGELOG.md` entry.** The joint cut
  ([Decision 15](#decision-15--the-0015-version-bump-is-deferred-to-the-joint-cut)).

## Definition of done

- [ ] `routers.py`'s HTTP branch is the supplied Django ASGI application directly;
      `GraphQLHTTPConsumer` is neither imported nor referenced anywhere in the module.
- [ ] `django_application` is required; omission is a `TypeError` and explicit `None` /
      a non-callable is a [`ConfigurationError`][glossary-configurationerror] naming the
      migration. No compatibility flag exists.
- [ ] `websocket_url_pattern` replaces `url_pattern`, is WebSocket-only, and exact-matches
      by default; `/graphql-admin` and `/graphqlanything` no longer match on either
      protocol.
- [ ] `django_strawberry_framework/views.py` ships `DjangoGraphQLView` /
      `AsyncDjangoGraphQLView`; the documented `urlpatterns` entry uses it.
- [ ] A cumulative request-body cap is enforced pre-parse and pre-execution on the
      GraphQL HTTP path, counting received bytes rather than trusting `Content-Length`,
      with an early `413` proving neither JSON parsing nor schema execution ran; the
      reverse-proxy / ASGI-server cap is documented as a co-requirement.
- [ ] `MAX_REQUEST_BODY_BYTES` exists in `conf.py` with a per-mount view-kwarg override
      and the documented precedence; it is the only settings key this card adds.
- [ ] Request JSON is UTF-8-only: UTF-16 / UTF-32 (BOM and BOM-less) and a UTF-8 BOM all
      return `400`; ordinary UTF-8 is unchanged; sync and async behave identically; the
      three live UTF-16/32/BOM success tests are inverted.
- [ ] `_cross_web_patches.py::_patched_body`'s contract and docstring are reconciled
      against the new HTTP path and the new wire contract.
- [ ] A WebSocket consumer-class/factory injection seam exists; the injected class still
      sits inside `AllowedHostsOriginValidator` + `AuthMiddlewareStack`; the package
      default revalidates the session actor per operation and denies an operation on a
      revoked session without a reconnect; `websocket_revalidation_window` makes any
      accepted delay explicit.
- [ ] Every preserved WebSocket Origin / auth test still passes unmodified; every rewritten
      HTTP-branch test asserts the new contract.
- [ ] Migration note (old vs new `asgi.py` **plus** the `urlpatterns` entry) and transport
      deployment guidance authored; [`spec-041`][spec-041] amended with the three
      superseded items.
- [ ] [`docs/GLOSSARY.md`][glossary] updated via the glossary DB + re-render (never
      hand-edited); [`docs/TREE.md`][tree] regenerated; [`README.md`][readme] /
      [`TODAY.md`][today] transport wording corrected.
- [ ] Full suite green at 100% coverage; `ruff` + trailing-comma clean; `manage.py check`
      and `makemigrations --check` clean.
- [ ] Card flipped Done and `KANBAN.md` / `KANBAN.html` regenerated from the DB.
- [ ] **No version quintet movement and no `CHANGELOG.md` edit** — both belong to the
      joint `0.0.15` cut.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[readme]: ../README.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[feedback2]: feedback2.md
[glossary]: GLOSSARY.md
[glossary-auth-mutations]: GLOSSARY.md#auth-mutations
[glossary-channels-request-adapter]: GLOSSARY.md#channels-request-adapter
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-cookbook-parity]: GLOSSARY.md#cookbook-parity
[glossary-debug-toolbar-middleware]: GLOSSARY.md#debug-toolbar-middleware
[glossary-developer-only-debug-posture]: GLOSSARY.md#developer-only-debug-posture
[glossary-django-appconfig]: GLOSSARY.md#django-appconfig
[glossary-djangodebugextension]: GLOSSARY.md#djangodebugextension
[glossary-djangofiletype]: GLOSSARY.md#djangofiletype
[glossary-djangographqlprotocolrouter]: GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangoimagetype]: GLOSSARY.md#djangoimagetype
[glossary-djangomodelpermission]: GLOSSARY.md#djangomodelpermission
[glossary-djangomutation]: GLOSSARY.md#djangomutation
[glossary-djangonodesfield]: GLOSSARY.md#djangonodesfield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-eviction-simulated-absence]: GLOSSARY.md#eviction-simulated-absence
[glossary-fielderror-envelope]: GLOSSARY.md#fielderror-envelope
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-get_queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-graphqltestcase]: GLOSSARY.md#graphqltestcase
[glossary-hard-dependency]: GLOSSARY.md#hard-dependency
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: GLOSSARY.md#live-first-coverage-mandate
[glossary-multi-database-cooperation]: GLOSSARY.md#multi-database-cooperation
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-pep-562-lazy-export]: GLOSSARY.md#pep-562-lazy-export
[glossary-probe-urlconf]: GLOSSARY.md#probe-urlconf
[glossary-request_from_info]: GLOSSARY.md#request_from_info
[glossary-require_optional_module]: GLOSSARY.md#require_optional_module
[glossary-schema-reload-discipline]: GLOSSARY.md#schema-reload-discipline
[glossary-seed_data]: GLOSSARY.md#seed_data
[glossary-single-upstream-parity]: GLOSSARY.md#single-upstream-parity
[glossary-soft-dependency]: GLOSSARY.md#soft-dependency
[glossary-strawberry_config]: GLOSSARY.md#strawberry_config
[glossary-testclient]: GLOSSARY.md#testclient
[glossary-upload-scalar]: GLOSSARY.md#upload-scalar
[spec-045]: spec-045-debug_extraction-0_0_15.md
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-041]: SPECS/spec-041-channels_router-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
