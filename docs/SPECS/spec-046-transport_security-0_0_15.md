# Spec: Transport security — Django-owned HTTP, a bounded request body, one UTF-8 wire, and WebSocket actor revalidation

Shipped in `0.0.15` (card [`DONE-046-0.0.15`][kanban]). This is **card 1 of a
four-card security-remediation program** derived from the hardening audit in
[`docs/feedback2.md`][feedback2]; it closes that audit's two Blockers (**S1**, **S2**),
two Mediums (**S9**, **S11**), and the **transport slice of S12**. Cards
[`DONE-047-0.0.16`][kanban] (request resource policy),
[`DONE-048-0.0.17`][kanban] (secure defaults), and
[`WIP-ALPHA-049-0.0.18`][kanban] (dependency / CI hygiene) each depend on this one:
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

Status: **SHIPPED — all five slices (S1, S2, S9, S11, and the S12 transport slice) are
built and released, with
[Decisions 16-19](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)'s
contracts landing inside them, and the joint `0.0.15` cut
([Decision 15](#decision-15--the-0015-version-bump-is-deferred-to-the-joint-cut)) has
since taken the version quintet past this card's patch line.** Two contracts here were
corrected after the release and the text below is the corrected form, not the shipped-then
form:
[Decision 18](#decision-18--the-body-gate-runs-before-djangos-multipart-parser)
now carries **two** CSRF-ordering arrangements — chain-supplied through
`GraphQLRequestBodyBoundaryMiddleware` and the original view-local fallback — plus the
declared-`charset` refusal under
[Decision 9](#decision-9--the-strict-utf-8-wire-contract-is-enforced-by-the-package-view-its-own-body-source-one-strict-decode);
and [Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)'s
cancelled-close ruling is now terminal rather than resting in `CLOSING`. Five slices:
Slice 1 (**S1** — the
protocol
split: HTTP to a required Django ASGI application, the package's Django GraphQL view,
WebSocket-only exact routing), Slice 2 (**S2** — the cumulative body cap plus the
documented proxy/server cap), Slice 3 (**S9** — the strict UTF-8 wire contract and the
inverted encoding tests), Slice 4 (**S11** — the WebSocket consumer-injection seam and
actor revalidation at both the admission and the outbound-frame checkpoint), Slice 5
(**S12 transport slice** — the migration note, transport deployment guidance, the
`spec-041` amendment, and the doc fold-in).

**Version boundary** (see
[Decision 15](#decision-15--the-0015-version-bump-is-deferred-to-the-joint-cut)): this
card **shares the `0.0.15` patch line** with [`TODO-ALPHA-050-0.0.19`][kanban], so the
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
- [Multi-database cooperation][glossary-multi-database-cooperation] — the rule the
  revalidation's session and user reads satisfy by delegating to Django's own database
  routers rather than pinning an alias of their own.
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
        **before** JSON parsing or schema execution, returning `413`, and they *measure*
        the body rather than materializing it — never `len(request.body)`
        ([Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)).
  - [ ] The declared multipart ceiling runs before `CsrfViewMiddleware.process_view` can touch
        `request.POST` and invoke `MultiPartParser`, under either arrangement: the chain runs
        the boundary from `GraphQLRequestBodyBoundaryMiddleware.process_view` where it is
        installed, and where it is not, the view is `csrf_exempt` on the outside and re-enters
        Django's public `csrf_protect` on the inside, **after** the body gate
        ([Decision 18](#decision-18--the-body-gate-runs-before-djangos-multipart-parser)).
  - [ ] New `django_strawberry_framework/_request_body.py`: the single compatibility helper
        that names `HttpRequest._stream` / `_body` / `_read_started`, handing the view one
        boolean and pinning the Django 5.2.0-vs-6.0 contract that measurement depends on
        ([Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)).
  - [ ] `_request_body.py::_measured_remaining` models the capability probe as **three**
        explicit outcomes — measurable; safely unmeasurable with the original position
        intact so the bounded read may run; or position potentially corrupted, so fail
        closed with the package's own controlled rejection — with every capability call
        (`seekable()`, both `seek()`s, and the subtraction) guarded rather than allowed to
        escape as an unrelated `500`
        ([Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)
        #"An unmeasurable stream has three outcomes, not two").
  - [ ] `_request_body.py::_bounded_read_exceeds_limit` is total in the same way and for the
        same reason: reading, sizing the returned chunks, closing the consumed stream and
        installing the replacement are all calls into a foreign object, so a failure in any
        of them is the module's fail-closed `True` plus one operator-side `WARNING` — never
        an `UnreadablePostError` escaping past upstream's `except HTTPException` as a `500`
        for a client that simply hung up mid-upload
        ([Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)
        #"The bounded read is guarded for the same reason the probe is").
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
  - [ ] `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin.parse_json` decodes
        `bytes` with **strict UTF-8** before delegating to upstream with `super()` — one
        method inherited by both package views, and independent of
        `APPLY_UPSTREAM_PATCHES`
        ([Decision 9](#decision-9--the-strict-utf-8-wire-contract-is-enforced-by-the-package-view-its-own-body-source-one-strict-decode)).
  - [ ] `django_strawberry_framework/views.py::_RawBodyRequestAdapter` — a one-property
        subclass of `cross_web.DjangoHTTPRequestAdapter` returning raw bytes, installed as
        `DjangoGraphQLView.request_adapter_class` through upstream's own per-view seam — so
        the sync transport's bytes reach that decode undecoded in **every** patch state.
        Without it the decode is never entered on sync and a BOM'd body is an unhandled
        `500`; the async view needs no counterpart and a row pins that asymmetry
        ([Decision 9](#decision-9--the-strict-utf-8-wire-contract-is-enforced-by-the-package-view-its-own-body-source-one-strict-decode)).
  - [ ] `_strawberry_patches.py::_patched_parse_json` decodes nothing and keeps its
        `UnicodeDecodeError` translation, which is a genuine upstream bug fix; both patch
        modules' `APPLY_UPSTREAM_PATCHES` docstring paragraphs state that the gate covers
        upstream *defects* only, scope the per-half consequence of disabling it **per
        mount** — the `cross_web` half reaches Strawberry's own view alone, the Strawberry
        half reaches a package mount too, through `super().parse_json` — and name the two
        view-owned halves that carry the wire
        contract whatever the setting says.
  - [ ] `_cross_web_patches.py::_patched_body` keeps returning raw bytes; its docstring
        is rewritten to state the new contract, the mount it now serves (a package view
        never reaches that getter), and why the patch survives S1.
  - [ ] The multipart control-document guard: each view overrides upstream's
        `parse_multipart` with a thin delegate over one shared mixin helper — two statements
        on the sync view, three on the async one, whose request adapter's form data must be
        awaited before it can be handed over — which
        accepts only an effective form encoding that canonicalizes to UTF-8 and refuses a
        `operations` / `map` value carrying Django's replacement marker `U+FFFD`, both with
        the same controlled `400`, **before** either value reaches `parse_json`
        ([Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard)).
  - [ ] A UTF-8 BOM is **rejected** with the same controlled `400`
        ([Decision 10](#decision-10--a-utf-8-bom-is-rejected)).
  - [ ] The three UTF-16/32/BOM **success** tests in
        `examples/fakeshop/test_query/test_products_api.py` are inverted to `400`, and the
        raw-bytes contract tests in `tests/test_cross_web_patches.py` are re-aimed: the
        adapter still returns raw bytes, and those bytes are followed into the package view
        that refuses them.
- [ ] **Slice 4 — S11: WebSocket actor revalidation through an injection seam**
  - [ ] `websocket_consumer_class=` injection on the router; an injected factory's calling
        convention **and** its returned application are validated before anything is
        mounted, and whatever is injected still sits inside all three router-applied
        wrappers — `DjangoWebSocketHostValidator`, `AllowedHostsOriginValidator`, and
        `AuthMiddlewareStack` — by construction
        ([Decision 11](#decision-11--a-websocket-consumer-classfactory-injection-seam-with-a-revalidating-package-default),
        [Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check)).
  - [ ] The package's default WebSocket consumer revalidates the session actor at **two**
        checkpoints — operation admission (`handle_subscribe` / `handle_start`) and every
        information-bearing outbound operation frame (`next` / `data` / operation `error`,
        through the derived `websocket_adapter_class`) — and writes the refreshed actor
        back onto `scope["user"]`. A failed validation at either checkpoint revokes and
        closes the whole connection
        ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)).
        The session store is resolved through
        `django_strawberry_framework/utils/sessions.py::session_store_class`, outside the
        structurally opt-in `auth` package ([`spec-040`][spec-040] Decision 3).
  - [ ] `consumers.py::_StopAwareSchema` / `::_stop_aware_results`, installed on both protocol
        handler subclasses by `consumers.py::_install_stop_aware_schema`: the package owns the
        generator upstream's `schema.subscribe` returns, so a revoked operation's result loop
        **ends** rather than being cancelled, and its inner source is closed in the wrapper's
        own `finally`
        ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
        #"How a revoked operation stops").
  - [ ] `consumers.py::_ConnectionRevocation` on `consumer._revocation`: the five-state
        revocation / close machine, its synchronous published decision, its connection-owned
        shielded close attempt bounded by `_MAX_REVOCATION_CLOSE_ATTEMPTS`, the outcome recorded
        by the attempt itself, the cancelled-attempt ruling, and the consumer's `disconnect`
        settling it
        ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
        #"The close is a state machine").
  - [ ] The derived adapter's delegated arm becomes conditional: once the revocation is
        **decided** it writes nothing further to the socket, delegated connection-control frames
        included, so the end-of-operation `complete` upstream emits when a revoked operation's
        result loop ends is dropped rather than committed after the `4403`. The read is a latch
        read outside the actor lease, because a suppression is not an authorization
        ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
        #"Delegation is not unconditional").
  - [ ] `websocket_revalidation_window=` — an explicit, bounded, opt-in revocation delay
        (default `0.0` = revalidate at every admission **and** every information-bearing
        outbound operation frame), with a typed construction-time
        domain: a finite number `>= 0.0` that converts to a `float`, or
        [`ConfigurationError`][glossary-configurationerror] — whose `got ...` tail renders
        through `exceptions.py::describe_value`, this slice's one shared value-describer,
        also used by both router injection seams and by the view's cap resolution.
  - [ ] Maximum connection lifetime, idle-socket lifetime, and aggregate connection limits
        documented as transport-resource policy the deployment owns, with the enforcement
        seam named
        ([Decision 12](#decision-12--maximum-connection-lifetime-is-documented-and-seamed-not-silently-enforced)).
  - [ ] `consumers.py::DjangoWebSocketHostValidator` — the private ASGI middleware that
        projects the handshake's Host metadata into a minimal Django `HttpRequest` and calls
        the public `request.get_host()`, composed **outside**
        `AllowedHostsOriginValidator` so Host and Origin stay two separate checks, denying
        through Channels' own `WebsocketDenier` so the two denials are indistinguishable on
        the wire
        ([Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check)).
  - [ ] `routers.py::_STRAWBERRY_CHANNELS_BROKEN_HINT` and the `tests/test_routers.py`
        assertion that pins it move from `strawberry-graphql>=0.262.0` to the `>=0.316.0`
        the hard dependency and the minimum CI matrix node already agree on — a user-facing
        recovery hint must not recommend a version the package metadata rejects.
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
        ([Decision 14](#decision-14--this-card-amends-spec-041-and-supersedes-three-of-its-decisions)),
        **and** its historical `strawberry-graphql>=0.262.0` floor prose reconciled to the
        live `>=0.316.0` requirement in the same pass. That spec is **shipped**, so the
        reconciliation corrects only factually-wrong prose — the sentences that describe the
        package's *current* dependency floor and the CI node that pins it — while checkbox
        state is left exactly as it is and the Status line remains the source of truth,
        which is this repo's shipped-card closeout convention. Sentences that are explicitly
        historical ("the export's presence at the 0.262.0 floor itself is upstream history,
        spot-checked at …") stay: they record what was true when that card shipped and are
        not claims about live code. There is no new Python 3.10 problem behind this: the
        dependency floor and the minimum CI matrix node already agree on `0.316.0`. The
        `routers.py::_STRAWBERRY_CHANNELS_BROKEN_HINT` string and the
        `tests/test_routers.py` assertion that pins it are corrected by Slice 4's own
        change, not here — this bullet owns the shipped spec's prose only.
  - [ ] [`docs/GLOSSARY.md`][glossary] via the glossary DB + re-render (never
        hand-edited); [`docs/TREE.md`][tree] regenerated for **all four** modules the
        earlier slices added — `views.py`, `_request_body.py`, `consumers.py`, and
        `utils/sessions.py` — in both the current and target package layouts, plus the new
        tests; [`README.md`][readme] / [`TODAY.md`][today] transport wording. The render
        reads each module docstring's first line, so a module whose docstring is missing
        fails the regenerate rather than silently omitting the row.
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
        fragmented-body rows. The exemption widens again for the
        real-`multipart/form-data` control-field rows
        ([Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard))
        and the `Client(enforce_csrf_checks=True)` ordering row with its parser sentinel
        ([Decision 18](#decision-18--the-body-gate-runs-before-djangos-multipart-parser))
        are both outside the shared harness, and the file must say so rather than leaving a
        reader to infer it from the absence of a row.
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
        clause, which the spec's corrected Edge-case sentence has made obsolete —
        the `400` explanation itself stays, since it is the reason the row asserts what it
        asserts.
  - [ ] The Slice-3 prose correction, in
        `examples/fakeshop/test_query/test_transport_api.py` and carried here for the same
        reason as the Slice-1 and Slice-2 prose above: the module docstring's **first line**
        must name the file's actual slice scope, which now also covers the S9 async rows and
        the wire contract's kill-switch rows — confirm it does and correct it if it does
        not, and do that **before** the [`docs/TREE.md`][tree] regenerate in
        this same slice, because that first line is the text `scripts/build_tree_md.py`
        renders (pinning a number at Slice 3 would have been a guess about a file Slice 4
        could still add rows to; pinning it here pins the truth). No assertion changes; the
        rows stay exactly as accepted.
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
- **The WebSocket branch's composition is sound as far as it goes, and this card preserves
  it** while adding one wrapper outside it:
  `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([...GraphQLWSConsumer...])))`,
  with the origin validator outside the auth stack so a cross-origin **or
  missing-`Origin`** handshake is denied against `ALLOWED_HOSTS`. What that composition does
  **not** do — measured, not assumed — is validate the handshake's `Host`.
  `channels.security.websocket.OriginValidator.__call__` reads the `Origin` header and
  nothing else, and `AllowedHostsOriginValidator` is a factory that configures it with
  `settings.ALLOWED_HOSTS` — or, under `DEBUG` with that setting empty, with its own
  hardcoded `["localhost", "127.0.0.1", "[::1]"]` — and reads no `Host` under either;
  a handshake carrying an allowed `Origin` and a
  hostile `Host` connects successfully. The class name is not evidence of behavior, and this
  card therefore adds the missing Host boundary rather than narrowing the claim
  ([Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check)).
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
  [Decision 9](#decision-9--the-strict-utf-8-wire-contract-is-enforced-by-the-package-view-its-own-body-source-one-strict-decode)
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
- **The `0.0.15` line has two non-Done cards.** [`TODO-ALPHA-050-0.0.19`][kanban] (the
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
   declared, with a `413` proving neither JSON parsing nor schema execution ran — and a
   refusal that is itself bounded, since a limit enforced after an unbounded allocation is a
   detector rather than a bound — plus a documented deployment-layer cap the package states
   it depends on.
4. **One wire encoding, on every JSON document the endpoint parses.** An
   `application/json` request body is UTF-8, strictly, with one documented BOM policy and
   byte-identical sync / async behavior. A multipart `operations` / `map` control document
   — which Django, not the package, decodes — must be decoded by Django in UTF-8, must not
   have declared any other encoding, and must survive that decode without a replacement marker
   ([Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard)).
   Both halves have a lifecycle of their own: permanent
   package policy, not a workaround riding a patch's kill switch.
5. **A WebSocket actor that cannot go stale silently.** Session revalidation on by default
   for the package's own consumer at **both** transport checkpoints — operation admission
   and every information-bearing outbound operation frame — so a revoked actor can neither
   start another operation nor emit another result from one already running, with any
   accepted revocation delay expressed as an explicit, bounded, opt-in number
   ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)).
6. **A transport that is configurable rather than frozen.** A consumer-class injection
   seam that cannot escape the package's Host, Origin, and authentication wrappers — three
   separate checks, each named by the wrapper that delivers it
   ([Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check))
   — so a deployment needing stronger revocation extends the transport instead of forking
   it.
7. **A migration a reader can execute.** Old `asgi.py`, new `asgi.py`, the required
   `urlpatterns` entry, and the transport deployment expectations, in one place.

## Non-goals

- **A central request resource-policy object.** Query depth / complexity / cost budgets,
  variable cardinality, collection bounds, and per-file upload limits are
  [`TODO-ALPHA-047-0.0.16`][kanban] (audit S3 / S4). This card ships exactly one
  transport bound — the cumulative body cap — and deliberately does not invent the policy
  object that later card owns.
- **Secure defaults for the IDE, GET, introspection, and error masking.** The card's
  regressions *prove* `graphql_ide=None` and `allow_queries_via_get=False` are supported
  on the new view; *changing the shipped defaults*, plus `DjangoSchema`-level production
  error policy and the [`DjangoDebugExtension`][glossary-djangodebugextension] disclosure
  gate (audit S8 / S10), belongs to [`TODO-ALPHA-048-0.0.17`][kanban].
- **The full deployment contract.** The `SECURITY.md` production-security profile and the
  mechanical `check --deploy`-style checklist (the rest of audit S12) belong to the later
  cards' doc slices; this card ships only the transport slice
  ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **A fakeshop `asgi.py` / live Channels tier.** Fakeshop stays WSGI-only. The
  [live-first coverage mandate][glossary-live-first-coverage-mandate] is satisfied for the
  HTTP half (fakeshop already serves a real Django GraphQL view over
  `django.test.Client`); the WebSocket half remains the documented
  genuinely-unreachable-live case that keeps `tests/test_routers.py` communicator-driven.
- **A second GraphQL protocol engine.** All three revalidation seams delegate to
  Strawberry's own classes with `super()` — the two admission pre-hooks on the protocol
  handlers and the outbound-frame gate on the WebSocket adapter
  ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam));
  the package implements no message loop, no subprotocol negotiation, and no frame
  serialization. It owns exactly **one** piece of an operation's lifecycle, and the boundary
  is stated rather than blurred: the stop-aware result source
  ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
  #"How a revoked operation stops") wraps the generator upstream's own `schema.subscribe`
  returns, so that a revoked operation can end and its generator can be closed. It produces
  no result of its own: every value, every error, and every non-subscription execution is
  still the real schema's, reached by identity.
- **A second Host-validation implementation, or a second `ALLOWED_HOSTS` matcher.**
  [Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check)'s
  WebSocket Host boundary adapts the ASGI handshake and then calls Django's public
  `HttpRequest.get_host()`; the package parses no hostnames, matches no wildcards, and adds
  no setting of its own.
- **A package-enforced connection lifetime, idle timeout, or connection-count limit.**
  Those are transport-resource policy owned by the ASGI server, the reverse proxy, or a
  deliberately injected consumer
  ([Decision 12](#decision-12--maximum-connection-lifetime-is-documented-and-seamed-not-silently-enforced),
  [Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
  #"The idle-socket consequence"). They are DoS-relevant and documented as such; they are
  not required to make the package's authorization boundary true.
- **A private copy, subclass, or monkeypatch of Django's `MultiPartParser`.** Django owns
  multipart framing, limits, and file streaming outright
  ([Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard)).
- **Reintroducing a Channels HTTP mode as an "advanced transport".** The audit offers
  that as a conditional; this spec declines it
  ([Decision 2](#decision-2--http-dispatches-directly-to-a-required-consumer-supplied-django-asgi-application);
  the rejected alternatives live in [the rationale companion][rationale-d2]).
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
  subclass shape. Upstream got the WebSocket branch right as far as it goes, and the audit's
  own "security strengths confirmed" list agrees. **Borrowed but not sufficient:** that
  composition validates `Origin` only, so this card wraps one more layer *outside* it
  ([Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check)).
  Channels' own validator is left untouched — the addition is a separate check for a
  separate question, never a replacement for or a re-implementation of theirs.
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
  Both are part of the existing hard `strawberry-graphql` dependency, and their imports are
  the standard library, `asgiref`, `cross_web`, `django`, `strawberry.http`, and their own
  `strawberry.django.context` sibling — verified in the installed 0.316.0, and the same list
  `views.py`'s own module docstring states. No optional-import guard applies: `asgiref` is
  Django's own hard dependency, and every other name is already a hard dependency of this
  package.
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
  migration note states the explicit policy and warns that an `APPEND_SLASH` redirect is a
  `301` most clients will not re-`POST` under `DEBUG=False`, and a `RuntimeError` rather than
  a redirect at all under `DEBUG=True` — post to the trailing-slash URL, or declare
  both patterns deliberately.
- **WebSocket path matching is the router's, and is exact.** `r"^graphql/?$"` matches
  `/graphql` and `/graphql/` and rejects every prefix extension.
- **A body over the cap gets `413`** with a `text/plain` reason, before `parse_json` and
  before schema execution — and, on a multipart request, before `request.POST`,
  `request.FILES`, `MultiPartParser`, or any upload handler, because the ordering is supplied
  either by the chain, where `GraphQLRequestBodyBoundaryMiddleware` is installed, or by the
  view itself, which is `csrf_exempt` on the outside and re-enters `csrf_protect` on the inside
  of the gate
  ([Decision 18](#decision-18--the-body-gate-runs-before-djangos-multipart-parser)).
  That exemption is an **ordering mechanism, not a CSRF bypass**: every request past the
  size boundary still undergoes Django's complete CSRF implementation.
- **Non-UTF-8 request JSON gets `400`** — the same controlled response malformed JSON
  already gets, on both package views, whatever `APPLY_UPSTREAM_PATCHES` says.
- **A multipart `operations` / `map` control document must be effectively UTF-8 and must
  survive Django's decode intact**, or it gets the same controlled `400`: an explicit
  non-UTF-8 `charset` on the form is refused, and so is a value carrying Django's
  replacement marker `U+FFFD`. Ordinary browser `JSON.stringify` output — including genuine
  multibyte UTF-8 — is unaffected, and a client that genuinely needs a replacement character
  in its document sends the ASCII escape `\ufffd`
  ([Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard)).
- **A revoked actor cannot admit another operation or emit another information-bearing
  operation frame over an open socket.** The connection is revoked and closed at whichever
  checkpoint notices first — the next operation's admission, or the next `next` / `data` /
  operation `error` frame an already-running subscription tries to send. Detection is
  event-boundary-driven: a socket sitting idle is not interrupted at the instant an external
  logout happens, and it has no authorization capability while idle. From the decision onward
  the package writes nothing more to that socket — not the suppressed payload, and not the
  `complete` the ended operation would otherwise produce — so the `4403` close is the last frame
  a client observes
  ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)).
- **A WebSocket handshake is validated on `Host` *and* `Origin`, as two separate checks.**
  A hostile `Host` is denied against Django's own `ALLOWED_HOSTS` boundary before
  authentication or consumer construction; a cross-origin or missing `Origin` is denied by
  Channels' validator. Passing one has never substituted for passing the other, and now
  both actually run
  ([Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check)).
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
  strict-decode failure, or upstream's own `400` for a decodable-but-not-JSON payload such
  as BOM-less UTF-16 or a UTF-8 BOM. The reason string is upstream's own `parse_json`
  literal, reproduced verbatim rather than invented, so the two mechanisms are
  indistinguishable on the wire and no caller can attribute a rejection by message.
- **Multipart control document the endpoint refuses to decode** — the same
  `HTTPException(400, "Unable to parse request body as JSON")` as every other refused
  request document, raised before `parse_json` sees either value. Identical status and
  reason for every refusal cause (a non-UTF-8 declared `charset`, a non-UTF-8 encoding
  Django would decode with, and a `U+FFFD`
  in a decoded control value) and identical to a plain malformed-JSON rejection, for the
  same reason the nine encoding shapes share one response: a caller must not be able to
  attribute a rejection by message
  ([Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard)).
- **Revoked actor on an open socket** — a **connection close**, code `4403`, reason
  `"Forbidden"`, on both protocols and at both checkpoints. No protocol-specific operation
  `error` frame precedes it: the actor is connection-scoped, so the close *is* the
  rejection, and the pending frame that triggered the gate is suppressed rather than sent.
  `4403` / `"Forbidden"` is upstream's own authentication-failure close on
  `graphql-transport-ws`, reproduced verbatim so a revoked-session close is
  indistinguishable on the wire from any other refusal to authorize this connection
  ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)).
  Exactly **one** such close is ever in flight, and the close is attempted a **bounded**
  number of times: if the transport refuses it the next security checkpoint retries once, and
  past that bound the connection is abandoned with the outbound gate still refusing every
  information-bearing frame — the refusal never depends on the close having reached the wire
  ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
  #"The close is a state machine"). And once the revocation is decided the client sees
  **nothing further from the package at all** — not the pending payload, and not the
  end-of-operation `complete` upstream produces when the revoked operation's result loop ends —
  so the `4403` close is the last thing on the wire.
- **Cross-origin or missing-`Origin` WebSocket handshake** — unchanged: denied by
  `AllowedHostsOriginValidator` before the GraphQL protocol starts.
- **Hostile-`Host` WebSocket handshake** — denied by the package's
  `DjangoWebSocketHostValidator` before `AllowedHostsOriginValidator`, before
  authentication, and before the consumer is constructed. The denial carries no detail
  about why; Django's `DisallowedHost` message is the *only* exception normalized into a
  denial, and any other exception from the projection propagates so a genuine bug stays
  visible instead of being reported as a rejected host
  ([Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check)).
- **`channels` absent** — unchanged: the install-hint `ImportError` at the consumer's
  `from django_strawberry_framework.routers import ...` line. Note the asymmetry this
  card introduces and must document: `django_strawberry_framework.views` needs **no**
  `channels`, so a WSGI-only project can adopt the whole HTTP half of this card without
  ever touching the soft dependency.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

This spec lives at `docs/SPECS/spec-046-transport_security-0_0_15.md`: card NNN `046`, topic
slug `transport_security`, target version `0.0.15` with dots as underscores, per the
[`docs/SPECS/NEXT.md`][next] Step 6 convention. The companion term ledger is
`docs/SPECS/appx/spec-046-transport_security-0_0_15-terms.csv`, and the companion **rationale** file —
[`spec-046-transport_security-0_0_15-rationale.md`][rationale], carrying the rejected
alternatives, the derivations, and the change record for every decision below, keyed to the
decision it belongs to — is where this spec's deliberative layer lives. This document is the
contract and states only what is currently true; it never narrates its own history.

*Rejected alternative and naming derivation: [rationale companion, Decision 1][rationale-d1].*

### Decision 2 — HTTP dispatches directly to a required, consumer-supplied Django ASGI application

**Decision.** The router's `"http"` key is the consumer's Django ASGI application,
**directly**. No `URLRouter`, no `re_path`, no `GraphQLHTTPConsumer`, and no
`AuthMiddlewareStack` on the HTTP branch:

```python
{
    "http": django_application,
    "websocket": DjangoWebSocketHostValidator(          # Decision 19
        AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter([re_path(websocket_url_pattern, consumer)])),
        ),
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

*Rejected alternatives and change record: [rationale companion, Decision 2][rationale-d2].*

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

*Rejected alternatives and change record: [rationale companion, Decision 3][rationale-d3].*

### Decision 4 — `url_pattern` becomes `websocket_url_pattern`, with exact matching as the secure default

**Decision.** The `url_pattern` parameter is **renamed and narrowed** to
`websocket_url_pattern`, keyword-only, defaulting to `r"^graphql/?$"`. It governs the
WebSocket branch **only**; HTTP path matching belongs entirely to the Django URLconf.
There is no aliased `url_pattern=` kwarg kept for compatibility.

`r"^graphql/?$"` is anchored at both ends, so — with Channels' leading-slash strip —
`/graphql` and `/graphql/` match and `/graphql-admin`, `/graphqlanything`,
`/graphql/extra` do not. That is the explicit policy the card's test plan demands, and it
preserves the URLs a `0.0.14` WebSocket client already uses while closing the overmatch.

*Rejected alternatives and change record: [rationale companion, Decision 4][rationale-d4].*

### Decision 5 — Compatibility policy: an intentional alpha breaking change to a security boundary

**Decision.** This card **intentionally breaks** the `0.0.14` byte-compatible upstream
constructor contract that [`spec-041`][spec-041] Decision 6 established. Three changes
are breaking: `django_application` becomes required, `url_pattern` is renamed to
`websocket_url_pattern`, and GraphQL HTTP now requires a `urlpatterns` entry that
`0.0.14` deployments do not have. The break is announced, migrated, and tested — not
mitigated by a flag.

**What is explicitly *not* broken.** The
[`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] symbol name and
import path, the [soft-`channels`][glossary-soft-dependency] guard and its install hints,
the [PEP 562 lazy export][glossary-pep-562-lazy-export] shape, the WebSocket composition
and its Origin semantics, the schema pass-through, and the package's
[Channels request adapter][glossary-channels-request-adapter] read path on WebSocket.

**One behavior change that is deliberately not in that list.** The WebSocket composition
carries an **outer** wrapper
([Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check)),
so a handshake whose `Host` is not in `ALLOWED_HOSTS` is denied where `0.0.14` accepted it.
That is a behavior change, and it is not a breaking change: it changes no signature, no
import, no setting and no documented promise — it makes an existing documented promise
("an injected consumer cannot escape Host validation") true. A deployment whose
`ALLOWED_HOSTS` is already correct for HTTP sees no difference; a deployment that sees a
difference was accepting handshakes addressed to a host it never allowed.

*Rejected alternatives and change record: [rationale companion, Decision 5][rationale-d5].*

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

The subclass adds exactly **one subject** — the raw request body — and inherits everything
else. That subject is two questions: how many of the body's bytes will be processed (the
cumulative cap,
[Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared))
and how those exact bytes become text (the strict UTF-8 wire contract,
[Decision 9](#decision-9--the-strict-utf-8-wire-contract-is-enforced-by-the-package-view-its-own-body-source-one-strict-decode)).
Answering them takes **four** overridden hooks, every decision body of which sits once on one
shared private mixin; the count, and which two of the four are hosted on the mixin itself
rather than declared per view, are stated once under *Helper-reuse obligations (DRY)*.
Every upstream kwarg (`graphql_ide`, `allow_queries_via_get`,
`multipart_uploads_enabled`) keeps working, unchanged, so the
S1 regression proving `graphql_ide=None` and `allow_queries_via_get=False` are supported
is a proof about the shipped surface rather than about a package reimplementation.

*Rejected alternatives and change record: [rationale companion, Decision 6][rationale-d6].*

### Decision 7 — The app-level body cap lives in the package Django view, counted not declared

**Decision.** `DjangoGraphQLView` / `AsyncDjangoGraphQLView` enforce a cumulative
request-body ceiling before `parse_json` and before schema execution:

1. **Declared over-limit rejects immediately.** If `CONTENT_LENGTH` is present and
   exceeds the limit, return `413` without reading the body.
2. **Actual bytes decide otherwise.** For a non-multipart request, measure the received
   body and reject at `413` if it exceeds the limit — a `Content-Length` that is absent or
   lying cannot buy a larger body. The measurement never materializes the body it may be
   about to refuse (see below). On WSGI Django's `LimitedStream` truncates reads at the
   declared length, so the declared value cannot understate what the application receives;
   on ASGI the spooled body file is measurable outright, so the refusal costs no allocation
   at all.
3. **Multipart is bounded by declaration plus Django's parser, not by materializing the
   body.** For a multipart request the view applies step 1 and then hands off to Django's
   `MultiPartParser` rather than reading `request.body` — reading it would force the whole
   payload into memory and defeat Django's streaming upload handlers, breaking the
   [`Upload` scalar][glossary-upload-scalar] path this package ships. Per-file count,
   per-file size, and aggregate size are [`TODO-ALPHA-047-0.0.16`][kanban] (audit S4);
   this card's contract for multipart is the declared-size gate plus an explicit
   statement of what it does and does not bound. **That gate really does run before
   Django's parser**, which is a property of the CSRF ordering rather than of this step
   alone: `CsrfViewMiddleware.process_view` reads `request.POST` for every cookie-bearing
   POST, so without one of the two arrangements of
   [Decision 18](#decision-18--the-body-gate-runs-before-djangos-multipart-parser)
   the declared gate would fire only *after* `MultiPartParser` and the upload handlers had
   already run.
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

**Method scoping, stated because steps 2 and 3 split on it.** The limit is resolved on every
request, so a misconfigured mount fails loud on `GET` too, but it bounds nothing on a `GET`:
this endpoint reads no body for one. Which of steps 2 and 3 a body-bearing request takes is
then decided by a single named discriminator, `views.py::_is_multipart_form_post`, true only
for a `multipart/form-data` **POST** — `HttpRequest._load_post_and_files` installs an empty
`QueryDict` without consulting the content type at all unless the method is `"POST"`. So a
stale `multipart/form-data` `Content-Type` on any other method describes a form Django will
never parse, and such a request takes step 2 and is **counted like any other body** — the
stricter direction — rather than being handed off under step 3. Naming the discriminator once
is also what stops this carve-out and
[Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard)'s
encoding guard drifting apart on a request shape.

**How the body is measured, and why not `len(request.body)`.** `HttpRequest.body` performs
an unbounded `self.read()` into one `bytes` value, so counting it would detect an
over-limit body only *after* the attacker-sized allocation the cap exists to prevent — and
on ASGI that read also copies back a `SpooledTemporaryFile` that
`ASGIHandler.read_body` may already have rolled to disk, synchronously, on the event loop
for `AsyncDjangoGraphQLView`. Django 6.0's own `body` narrows that window by size-checking
a seekable stream first; the **Django 5.2.0 floor carries no such check**, which is
precisely where the package's counted bound has to stand alone. So the cap asks a question
instead of reading a body, in descending order of cheapness. A body an earlier middleware
already cached is measured from that cache and still refused — the allocation cannot be
undone, but processing it can be. A measurable stream (the ASGI spool) is size-probed with
`seek` / `tell`, its original position restored, with **nothing read** — and it is the
probe's *answer* that is judged, not merely its arithmetic: a count of zero or less is a
measurement failure, never an empty body, so the request falls through to the bounded read
below. Zero is the one answer a size probe must not be believed on, because the cap reads
it as "within the limit" while nothing has been read, which hands the request straight to
`HttpRequest.body` with no package bound at all — and at the 5.2.0 floor that property's
only ceiling is the `CONTENT_LENGTH` this cap exists precisely not to trust. Verifying a
zero costs exactly one `read`, so the fail-safe direction is affordable, and a genuinely
empty body is still allowed — by measurement rather than by assumption. A stream the probe
cannot answer for (genuinely non-seekable, or refused as above) is read through
`request.read` — so Django keeps its own bookkeeping — in bounded chunks to at most
`limit + 1` bytes, one byte more than the largest legal body
and the least information that distinguishes "exactly at the limit" from "over it". Over
the limit the collected chunks are never joined and the remainder is left unread, so no
over-limit `bytes` value is allocated even transiently. Under it, the bytes are handed back
as a *stream* — the consumed stream closed, a rewound `BytesIO` over the same bytes
installed, `_read_started` reset to the `False` the request was constructed with — never by
pre-filling `request._body`, so `HttpRequest.body` still runs in full and Django's own
ceiling still fires exactly where it always did. Two states are unmeasurable, and the cap
defers rather than guessing: a synthetic `HttpRequest` that carries no `_stream` at all,
and a stream some other component already read from without caching `_body` — where
`HttpRequest.body` itself raises `RawPostDataException`, so nothing downstream can process
that request either and there is no bypass left to close. All three private attributes live
in **one** module, `_request_body.py`, which hands the view a single boolean: the
version-divergent knowledge is the risk, so it is single-sited beside the documented Django
contract it depends on rather than spread across the two view classes.

**An unmeasurable stream has three outcomes, not two.** The size probe reaches for four
capabilities of an object the package did not create — `seekable()`, a seek to the end, a
seek back to the original position, and the subtraction of the two answers — and a stream
supplied by consumer middleware or a custom ASGI server may raise from any of them.
Letting such a failure fall through as an unrelated `500` is the wrong answer at the one
seam this design deliberately centralizes, so the probe reports exactly three outcomes:

1. **Measurable** — a coherent position/end pair, the original position restored, nothing
   read. The count decides.
2. **Safely unmeasurable, original position intact** — the stream declared itself
   unseekable, or `tell()` refused, or the pair came out incoherent and the restore
   succeeded. No measurement is produced and the bounded read supplies the bound. A probed
   count of zero or less stays in this class, and that property is hard-won: zero taken at
   face value reads as "within the limit" while nothing has been read, which hands the
   request to `HttpRequest.body` with no package bound at all, and at the 5.2.0 floor that
   property's only ceiling is the `CONTENT_LENGTH` this cap exists precisely not to trust.
   Verifying a zero costs exactly one `read`, so the fail-safe direction is affordable, and
   a genuinely empty body is still allowed — by measurement rather than by assumption.
3. **Position potentially corrupted** — the seek to the end succeeded (or raised after
   moving) and the restore then failed to prove itself: the restoring seek raised, or the
   `tell()` that verifies it answered something other than the position the probe started
   from. Either way the stream's read position is no longer
   known to be where the request started, and the two are one outcome rather than two — an
   over-reported position takes the second route, because a `tell()` that lies about where
   the stream is lies about the restore too. The package **fails closed** with its own
   controlled rejection rather than reading from an unknown offset or guessing a rewind to
   zero: the bytes cannot be recovered, and a bounded read from an unknown position would
   measure a body nobody sent. This is the only new refusal, and it is a refusal rather
   than a `500`.

The split is deliberate about *which* failure fails closed. An outcome-2 failure has cost
nothing and lost nothing, so deferring to the read is strictly better than refusing a
possibly-legitimate request. An outcome-3 failure has already mutated state the request
depends on, and a package that quietly continued would be processing a request it can no
longer describe. Rewinding to zero instead was rejected explicitly: a stream legitimately
mid-position would then be misread from its start.

**The bounded read is guarded for the same reason the probe is.** Outcome 2 does not answer
the question, it *delegates* it — so the delegate has to be as total as the probe, or the
guarantee only holds on the branch that never runs in production. Everything the bounded read
touches is foreign too: `request.read` (a stream `OSError`, which Django re-raises as
`django.http.request.UnreadablePostError`), the chunk objects handed back, the consumed
stream's `close`, and the replacement stream installed in its place. Any of those failing means
the same thing — the package cannot prove this body is within the limit — so all of them
produce the same **fail-closed** answer and the same controlled rejection, with one
operator-side `WARNING` carrying the traceback because the wire deliberately cannot say why.
The shape this closes is not exotic: an ordinary client that hangs up mid-POST made
`UnreadablePostError` propagate through `views.py::_RequestBodyBoundaryMixin` and past
upstream's `except HTTPException`, turning the boundary whose whole job is to refuse politely
into a `500` and an error log. Nothing was executed and no cap was bypassed, which is why this
is the *response* and the *attribution* being wrong rather than a hole — and why the fix is
this module's documented `bool`, not a new exception type. A partially collected prefix is
dropped with the request rather than installed: `_read_started` stays `True` and `_body` is
never written, so anything that did reach for the body would get Django's own
`RawPostDataException`, never a fragment of a body nobody sent. `BaseException` stays uncaught
in both phases, so cancellation and process control still propagate.

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

*Rejected alternatives and change record: [rationale companion, Decision 7][rationale-d7].*

### Decision 8 — The deployment-layer cap is a co-requirement, not an alternative

**Decision.** The spec documents an explicit reverse-proxy / ASGI-server body cap as a
**required** part of the deployment contract, with concrete directions
(`client_max_body_size` on nginx, `LimitRequestBody` on Apache, and the statement that
**no mainstream ASGI server bounds the total body at all** — Uvicorn, Hypercorn, and
Daphne ship no total-request-body limit, the size knobs they do expose bound the request
line and headers rather than the body, and Daphne's request-buffer size controls fragment
delivery rather than total accepted body). Naming a header-shaped knob as if it capped the
body would hand the reader exactly the false comfort this decision exists to remove: the
proxy line is load-bearing **because** the layer below the application supplies nothing.
Slice 5's transport guidance states plainly that routing
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
  carve-out (on a multipart **POST** — the one request shape
  `views.py::_is_multipart_form_post` admits — the bound is the declaration plus Django's
  `MultiPartParser`, not a byte count; a multipart content type on any other method takes
  the counted path like any other body, per
  [Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)'s
  method scoping, and the carve-out must be stated with that scope so a reader cannot read
  the looser half as the whole rule) — and, alongside it, the statement that the
  declaration *is* nonetheless enforced before that parser and its upload handlers run,
  which is a property of the CSRF ordering — chain-supplied or view-local — rather than of
  the cap
  ([Decision 18](#decision-18--the-body-gate-runs-before-djangos-multipart-parser)).

**Why this is a decision and not a documentation footnote.** The most likely failure of
this card is not a code bug — it is a reader concluding "S1 fixed the transport, so S2 is
handled." Django's `ASGIHandler.read_body` refutes that in source: it buffers the full
request, rolling to disk past `FILE_UPLOAD_MAX_MEMORY_SIZE`, *before* `HttpRequest.body`
evaluates any limit. So an unbounded request still consumes bandwidth and disk on a
Django-routed deployment. Naming that boundary explicitly, in a numbered decision, is
what keeps the two layers from collapsing into one in the reader's head.

*Rejected alternatives and change record: [rationale companion, Decision 8][rationale-d8].*

### Decision 9 — The strict UTF-8 wire contract is enforced by the package view: its own body source, one strict decode

**Decision.** `views.py::_RequestBodyBoundaryMixin.parse_json` decodes `bytes` input with
**strict UTF-8** and then delegates with `super()` to upstream's `parse_json`, which stays
the only JSON parser in the path. A `UnicodeDecodeError` from that decode becomes
`HTTPException(400, "Unable to parse request body as JSON")` — upstream's own literal,
reproduced verbatim. A `str` input (the GET query-param path and the multipart
`operations` / `map` form fields, all of which Django has already decoded) passes through
**untouched, by identity**, and the existing `_patched_parse_query_params` shield keeps the
body-envelope guard off the two query-param sites regardless.

**Scope, stated so the decode is not read as more than it is.** This decision governs the
one document the package receives as *bytes*: the `application/json` request body. It is
**not** a wire-encoding contract for multipart, and cannot be, because Django decodes
multipart field data — with `force_str(..., errors="replace")` — before the package is
handed anything: `operations` and `map` arrive as `str` with every decode failure already
collapsed to `U+FFFD`, so a `str` pass-through here is the only correct behavior and a
strict decode here would have nothing left to be strict about. The multipart control
documents get their own boundary, one step earlier, in
[Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard).
The two together are what makes Goal 4's "one wire encoding" true of *every* JSON document
this endpoint parses; this decision alone governs the ordinary JSON body. The mixin sits first in both
views' bases, so it is the MRO owner of `parse_json` for the sync and async view alike:
one method, both transports, no duplication and no possible drift.

**The bytes have to arrive undecoded, and that half is the view's too.** A decode the
bytes never reach is not an enforcement, and on the sync transport they do not reach it by
default: upstream's `cross_web.DjangoHTTPRequestAdapter` UTF-8-decodes inside a
*property*, so `parse_json` is never entered with `bytes` at all and the
`UnicodeDecodeError` raised there escapes `dispatch`'s `except HTTPException` as an
unhandled `500` — the original upstream bug. The package view therefore supplies its own
body source: `views.py::_RawBodyRequestAdapter`, a one-property subclass of that same
adapter returning raw `self.request.body`, installed through `request_adapter_class` —
upstream's own per-view seam, the class attribute every integration sets, and the single
place `strawberry.http.sync_base_view` decides who answers `request_adapter.body`.
Subclassing keeps every other adapter member upstream's, and the property shadows the
(patched or unpatched) class attribute by identity, so neither the patch state nor the
install order can reach a package mount. The async view needs no counterpart —
`AsyncDjangoHTTPRequestAdapter.get_body` already hands over the raw bytes, which is exactly
the contract the sync subclass reproduces — and a test pins that asymmetry so it cannot
silently become a gap.

`_cross_web_patches.py::_patched_body` **keeps returning raw `self.request.body` bytes**,
and its docstring is rewritten — but the mount it serves is the *other* one. It replaces
the property on upstream's class process-wide, so a consumer who mounts **Strawberry's
own** view also gets the raise moved out of a property and into a scope that can answer it
with a controlled `400`; a package view never reaches that getter at all.
`_strawberry_patches.py::_patched_parse_json` decodes nothing and keeps its own
`UnicodeDecodeError` translation, which remains reachable on that same upstream-mounted
path (`json.loads(bytes)` raises it whenever the bytes are undecodable under the encoding
`detect_encoding` picks) and is a genuine upstream bug fix. The patch pair's joint
ownership of the malformed-body contract is unchanged, and so is its subject for the
`cross_web` half — Strawberry's own view. Its subject is *both* mounts for the Strawberry
half, whose body-envelope guard a package view still reaches through `super().parse_json`;
what narrows is the *success* set, and it narrows on the package view.

**The declared half: a `charset` this endpoint will not honour is refused at the boundary.**
The strict decode governs the bytes; `views.py::_RequestBodyBoundaryMixin
._enforce_body_charset_declaration` governs what the client *said* about them. One byte
sequence must not be `é` to this view and two Latin-1 characters to any hop that honours the
declaration, so a request declaring an encoding this endpoint will not decode with is refused
rather than having its bytes silently reinterpreted. The contract:

- **Absent is not a declaration**, and is the overwhelmingly common case. It passes, leaving
  the strict decode as the only encoding contract — which is the stronger one, because it
  inspects the bytes rather than a header.
- **Anything present must canonicalize to UTF-8.** Every alias Python's codec machinery
  resolves to UTF-8 is accepted. `utf-8-sig` is **not**: it is a different codec, and its BOM is
  what [Decision 10](#decision-10--a-utf-8-bom-is-rejected) refuses. An unknown codec name is
  not either.
- **A refusal is the shared `HTTPException(400, "Unable to parse request body as JSON")`**, the
  same wire shape the strict decode's failure produces, so a client cannot distinguish which of
  the two encoding boundaries refused it.
- **Multipart is excluded here** and belongs to the narrower owner in
  [Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard):
  Django consults the declaration itself on that path, and the package's business there is loss
  detection on the control documents.

**Method scope, with its one consequence stated rather than discovered.** The guard is skipped
for `GET` only — deliberately the same scope as
`::_enforce_request_body_limit`'s, so the two body boundaries do not disagree about which
requests they govern. The consequence is that a method carrying an unhonourable `charset` which
this endpoint does not serve is refused with `400` before method routing decides anything, where
upstream would have answered `405`. The direction is stricter and the reason string is shared,
which is why the scope agrees with the cap's rather than being widened to enumerate methods.

**Ownership follows lifecycle, so the gate does not carry the policy.** Both patches keep
installing where they install today — from `apps.py::DjangoStrawberryFrameworkConfig.ready`
at Django app load, the [Django `AppConfig`][glossary-django-appconfig] seam — and keep
their shared `APPLY_UPSTREAM_PATCHES` gate, which governs **upstream bug workarounds and
nothing else**. The wire contract is permanent package policy, so it does not ride a
temporary workaround's kill switch: a consumer who disables the patches (or a future
maintainer who deletes them once upstream fixes the bugs) keeps the strict wire contract on
every package view. That is a claim about **both** halves, which is why both are
view-owned: a policy is only as ungated as the least-owned step on the path to it, and the
path to the decode runs through the body source. Deletability is the other half of the same
property: because the patch module no longer holds a permanent policy, it can be removed
outright when both upstream bugs retire. A consumer who deliberately mounts
`strawberry.django.views.GraphQLView` instead keeps upstream's own RFC 8259 `bytes`
semantics — their choice to make, and no longer made for them by an unrelated setting; a
test pins that upstream behavior as a *requirement*, so the ownership split cannot silently
collapse back into one site.

**Which docs, by surface.** The same split
[Decision 8](#decision-8--the-deployment-layer-cap-is-a-co-requirement-not-an-alternative)
states for the body cap: the **code-documentation** surface belongs to the slice that
authors the code, so Slice 3 discharges it in four places, one per owner. `views.py`'s
`parse_json` docstring carries the decode itself, including why it lives there;
`_RawBodyRequestAdapter`'s docstring carries the other half — what upstream's
property-scoped decode costs, why `request_adapter_class` is the seam, and why this class
is not the `cross_web` patch under another name. The
`APPLY_UPSTREAM_PATCHES` paragraph of **both** patch module docstrings —
`_strawberry_patches.py` and `_cross_web_patches.py` — states that the gate covers upstream
*defects* only, and names the per-half consequence of disabling it **per mount**, because the
two halves do not reach the same mounts. The `cross_web` half reaches Strawberry's own view
alone — without it an undecodable body is an unhandled `500` there, while a package mount is
untouched, since `_RawBodyRequestAdapter` shadows the patched property by identity. The
Strawberry half reaches **both** mounts: the mixin's `parse_json` delegates with `super()`
into `BaseView.parse_json`, which is the very attribute that patch assigns, so with the gate
off a scalar or non-object-batch body (`b"42"`, `b"[1,2]"`) comes back out of a real
`DjangoGraphQLView` unguarded and reaches the same unhandled `500` it reaches on upstream's
view. What rides the gate on neither mount is the **wire contract**: the strict decode and
the body source are view-owned code, and both docstrings name those two halves as carrying it
whatever the setting says. Naming both is the point: a consumer who reads only the module they
disabled still learns exactly what they gave up, and what they did not. Any consumer-facing
restatement is Slice 5's transport deployment guidance, not a fifth code surface.

**What this means for `_patched_body` after S1.** The patch is unaffected by the protocol
split and remains necessary for the mount it serves. It patches
`cross_web.DjangoHTTPRequestAdapter`, the **Django view's** sync request adapter — the very
path S1 makes authoritative — not anything Channels-owned, and a consumer who mounts
Strawberry's own Django view is served by it. If anything, S1 raises the patch's importance
for that consumer: previously a Channels-routed deployment never reached that adapter at
all.

**Measured behavior** (verified, not assumed — the full shape set for an
`application/json` **request body**, so no reader has to infer a sibling's behavior from a
named one; the multipart control-document shapes are tabulated separately in
[Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard)):

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

Every non-UTF-8 form therefore reaches a `400` through **one** rejection branch, not nine:
the four undecodable shapes ride the single `except UnicodeDecodeError` the boundary owns,
and the other five are refused by upstream's own parser with no package branch at all. The
authoritative split across the nine rejected shapes is
**4 `UnicodeDecodeError` / 5 `json.JSONDecodeError`**: the BOM'd multi-byte
forms carry a leading byte that is not valid UTF-8, while the BOM-less multi-byte forms
decode into NUL-studded text that only the parser refuses. Status and message are
identical across all nine — deliberately, so one byte sequence has one interpretation at
every hop — which makes `__cause__` the only thing that records which mechanism fired, and
the only way a test can pin the five **inherited** rejections against a future `json`
that tolerated them.

*Rejected alternatives and change record: [rationale companion, Decision 9][rationale-d9].*

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

*Rejected alternatives and change record: [rationale companion, Decision 10][rationale-d10].*

### Decision 11 — A WebSocket consumer-class/factory injection seam, with a revalidating package default

**Decision.** The router gains `websocket_consumer_class=None`, accepting a
`GraphQLWSConsumer` subclass **or** a factory callable. A class must subclass
`GraphQLWSConsumer` and is mounted through its own `as_asgi(schema=schema)`; a factory is
called as `factory(schema=schema)` and must return the ASGI application to mount. Anything
else — a class that is not a `GraphQLWSConsumer` subclass, or a non-callable — is a
[`ConfigurationError`][glossary-configurationerror] at construction.

**A factory is validated on both halves of its contract, before anything is mounted.** The
*calling convention* is pre-bound with `inspect.signature(factory).bind(schema=schema)`
before the factory is invoked at all, with the binding `TypeError` preserved as
`__cause__`; a factory whose signature cannot be read is judged by the call instead. The
*returned object* must then be callable, and a coroutine object — what an `async def`
factory returns — is `close()`d on the way out, because dropping it makes CPython emit an
unraisable "never awaited" `RuntimeWarning` from the collector at an unrelated moment, in
the consumer's process. What "a valid ASGI application" means at this seam is stated rather
than implied: **callability is the floor, and the only false-positive-free check available
at construction**. ASGI conformance — accepting `(scope, receive, send)`, awaiting, emitting
the right events — is observable only by running a real connection through the object, which
router construction must not do, and an arity check on the result would falsely reject
legitimate `*args` middleware, `functools.partial` mounts, and callable instances whose
`__call__` is a C slot. So the validation converts every shape that *cannot* be an ASGI
application (`None`, a scalar, a mapping, a coroutine) into an actionable
`ConfigurationError` naming the contract, the factory, and the received value, and
deliberately leaves a callable that merely misbehaves to fail at the handshake, where its
own traceback is the useful signal. A `TypeError` raised from inside a correct factory's
body is never normalized — that is why the convention is pre-bound rather than caught
around the call.

`None` selects the package's own `GraphQLWebSocketConsumer`, a thin `GraphQLWSConsumer`
subclass that revalidates the session actor at both of
[Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)'s
checkpoints. Whatever is injected, the router applies
`DjangoWebSocketHostValidator(AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([...]))))`
around it — the
wrappers are the router's, not the consumer's, so an injected class **cannot** escape
**Host** validation (the package's own validator, delegating to Django's
`HttpRequest.get_host()`), **Origin** validation (Channels'
`AllowedHostsOriginValidator`), or **authentication** (`AuthMiddlewareStack`). Three
wrappers, three named checks — the Host half is
[Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check)'s
own boundary rather than a property of Channels' Origin validator. That structural
guarantee is the whole reason the seam is safe to offer — and it is a guarantee about the
*wrappers* only: the outbound-frame gate rides on the package's own consumer, so an injected
consumer opts out of it exactly as it opts out of the admission hooks.

**Where the revalidation hooks in, and why not `get_context`.** Strawberry's
`GraphQLWSConsumer.get_context` is called **once per connection**, inside
`AsyncBaseHTTPView.run`, before either protocol handler's message loop starts — so it is
not a per-operation seam. The per-operation **admission** entries are
`BaseGraphQLTransportWSHandler.handle_subscribe` and the `graphql_ws` sibling's
`handle_start`, reachable through the `graphql_transport_ws_handler_class` /
`graphql_ws_handler_class` class attributes on the view. The package's consumer points
those at two subclasses whose admission hook is three lines each: await one shared package
function, return without admitting the operation if it refused, otherwise delegate with
`super()`. The revalidation logic is single-sited in that function;
the per-protocol subclasses carry no logic of their own. Each also carries an `__init__` that
delegates with `super()` and then calls one shared installer for the stop-aware result source
([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
#"How a revoked operation stops") — the same single-siting rule, and the reason a mechanism
that has to serve both protocols is spelled once rather than twice.

Admission is only **half** the boundary. An admitted subscription iterates its result
source inside one task and never
returns through `handle_subscribe`, so an admission hook cannot stop an *already-running*
operation from emitting results after its actor is revoked. The second checkpoint — a gate
on the outbound frame, installed through the consumer's `websocket_adapter_class` — is
[Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam),
and it is what makes the S11 contract whole. Everything below in this
decision describes the admission checkpoint; read it together with Decision 16, which owns
the second checkpoint, the shared connection state, and the failure response both
checkpoints produce.

**What the revalidation does.** It reloads the session and resolves the actor for the
scope, writes the refreshed actor back onto `scope["user"]`, and — when the session is no
longer valid (revoked, flushed, the user disabled, the password rotated) — revokes and
closes the whole connection
([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)),
rather than failing one operation and leaving the socket authorized. The reload
goes through `channels.auth.get_user`, reused verbatim rather than reimplemented, over a
store the deployment's `SESSION_ENGINE` resolves — and that resolution is read from
`utils/sessions.py::session_store_class`, **outside** the `auth` package. `auth` is
structurally opt-in ([`spec-040`][spec-040] Decision 3) and its `__init__` eagerly imports
`.mutations` / `.queries`, so reaching the resolver through `auth.sessions` would make the
first authenticated operation on a socket import and register the whole GraphQL auth
subsystem, on the event loop, to read one settings string. Hosting the expression in
`utils/` — which the transport layer and the auth layer both already depend on — keeps one
expression for the engine and leaves `auth` opt-in. Writing
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
session read at all: only an authenticated socket pays the cost. And `scope["user"]` is
**never** downgraded to anonymous on a failed validation — the stale actor stays exactly
where it was. A revoked session must not quietly become an anonymous one that keeps
executing, and the invariant still matters after
[Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
closes the socket, because the close is not instantaneous: sibling operation tasks are still
ending while the connection's revocation is published, and any of them that reaches a
checkpoint in that window must take the same denial path rather than find an anonymous actor
that looks permissible for an unauthenticated read.

**The bounded window is explicit, and it means the same thing at both checkpoints.**
`websocket_revalidation_window` is **the maximum age of a successful actor validation that
may authorize a new operation or an information-bearing outbound operation frame**. `0.0`
(the default) revalidates at every admission and at every `next` / `data` / operation
`error` frame. A positive value permits reuse of the last successful validation only while
it is younger than that value. There is no artificial minimum interval, no second setting,
and no background task, and an idle authenticated socket performs **zero** database reads —
freshness is spent at event boundaries, not on a timer. The value is expressed as a number
in the constructor so the delay is a stated deployment decision rather than an emergent
cache behavior. The docs state the trade in one sentence: one session read per authorized
event, or a named number of seconds during which a revoked session may still be served.

The window's domain is typed and checked at construction: a **finite number `>= 0.0` that
converts to a `float`**. `bool` is refused explicitly (`isinstance(True, int)` is `True`), a
non-numeric value is refused, and the conversion runs in its own guarded step so an integer
with no `float` image raises the promised
[`ConfigurationError`][glossary-configurationerror] with the `OverflowError` chained as
`__cause__` rather than escaping as a raw arithmetic error; the sign and finiteness tests
then run on the converted `float`. `nan` and `inf` are refused as well, and the reason is
unusability rather than size: `nan` loses every comparison, so a window spelled that way
would silently never expire and never say why, and `inf` is the saturation sentinel a
failed computation produces rather than a number of seconds any deployment chose. A
negative value, `nan`, and `inf` all raise **one** message, because they differ in how they
detect an unusable value, not in what the deployment must change.
What is deliberately **not** refused, so the rationale is not read as more than it is, is a
finite but astronomical window: `10**300` and `1e308` are accepted, and a window that large
*is* "never revalidate again". The package sets no upper bound, for the same reason
[Decision 12](#decision-12--maximum-connection-lifetime-is-documented-and-seamed-not-silently-enforced)
sets no maximum connection lifetime — there is no correct default, any ceiling would be a
constant invented here rather than derived from anything, and the window is a deliberate
consumer trade-off (one session read per authenticated **checkpoint** against a named
revocation delay — never per operation, since the outbound frame is a checkpoint too) that the
deployment can price and the package has no standing to second-guess. The
guard is about values the package cannot *use*, not about values it disapproves of.

The message renders through the package's one safe value-describer, since the `got ...` tail
is built by an f-string at the *raise site* — before any exception object exists, so a value
whose `repr` cannot be produced would otherwise replace the typed error with an unrelated
one on exactly the hostile-configuration path where the typed error is the contract.

A **positive** window cannot be combined with `websocket_consumer_class`: the window
configures the package's own consumer, so pairing it with an injected class that owns its
own revalidation policy is a construction error rather than a silently ignored knob. An
explicit `0.0` alongside an injected class is accepted, because it configures nothing either
way and is already the public default — the rule is about the window's *effect*, not about
its presence in the call. Distinguishing "omitted" from "explicitly zero" would need a
private sentinel in a public signature, which is a worse API than a rule that keys on the
value that matters.

**One deliberate constraint, stated as a constraint.** The revalidation performs a
session read per authorized event — an admission or an information-bearing outbound frame —
or one per window, which is database work on the socket's
critical path. Where an *authenticated subscription* is concerned that is per emitted result
rather than per client message, which is the cost
[Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
prices explicitly and the window exists to let a deployment reduce.
The session and user reads honor their models' **normal Django
database-router decisions** — the store the deployment's `SESSION_ENGINE` resolves and
`channels.auth.get_user` both perform ordinary router selection, and the package captures no
alias of its own — which is what [Multi-database cooperation][glossary-multi-database-cooperation]
asks of a library: cooperate with the consumer's routing rather than pin around it.
Reimplementing `get_user` to force an alias would be strictly worse, and the window exists
precisely so a deployment can price the read. This is a cost the audit's finding makes
worth paying, not a cost the spec hides.

*Rejected alternatives and change record: [rationale companion, Decision 11][rationale-d11].*

### Decision 12 — Maximum connection lifetime is documented and seamed, not silently enforced

**Decision.** The package does **not** impose a maximum WebSocket connection lifetime, a
socket idle timeout, or an aggregate connection limit. Slice 5 documents (a) that an
established socket should have a deployment-enforced
maximum lifetime, (b) the ASGI-server and proxy settings that provide it, (c) the
upstream `connection_init_wait_timeout` and `keep_alive` knobs the injected consumer
class can set, and (d) that with revalidation on, the **authorization** bound is the
revalidation window and the checkpoints of
[Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
rather than the connection lifetime — while the **resource** bound remains the deployment's,
because a revoked socket producing no further events stays physically open until something
that owns connections closes it.

**Which bound lifetime is, and which it is not.** Lifetime is not the bound on *what a
revoked actor can do* — a revoked connection cannot admit an operation or emit an
information-bearing operation frame, and dies at the attempt — but it remains the bound on
*how long the socket, its subscription task, its session object, and its stale actor
reference occupy the server*. That residue is DoS-relevant and is named as such
([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
#"The idle-socket consequence"); it is not an authorization hole, because the idle socket has
no authorization capability while idle.

*Rejected alternatives and change record: [rationale companion, Decision 12][rationale-d12].*

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
   `OriginValidator`" assertion are preserved verbatim, beside the one assertion added for
   the outermost wrapper (below).

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
adapter still returns raw bytes (that contract is unchanged), and the new assertion follows
those bytes into the package view, which is what refuses them. For the BOM row that
distinction is load-bearing rather than cosmetic — `json.loads` on `bytes` detects
`utf-8-sig` and strips the BOM itself, so a patch-module-only assertion would have recorded
that body as *accepted*.

**Re-aimed to the connection-scoped revocation, ordering, Host and probe contracts.** Same
discipline as above: named explicitly so a reviewer can tell a deliberate inversion from a
regression.

- `tests/test_routers.py`'s revocation rows assert a **connection close** (`4403` /
  `"Forbidden"`) with no preceding operation error, at both checkpoints and on both
  protocols
  ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)).
  The revocation subject is preserved; the wire shape of the denial is what changes, and an
  operation-scoped `error` frame is unreachable through the outbound gate.
- `tests/test_routers.py` carries a controlled **multi-yield** subscription beside the
  single-yield `Subscription.tick`: a single-yield fixture cannot pin the active-operation
  gate at all, because operation 1 finishes before the revocation lands. The single-yield
  fixture serves the admission rows; the multi-yield one serves the outbound-frame rows.
- `tests/test_routers.py`'s `_STRAWBERRY_FLOOR_SUBSTRING` pins
  `routers.py::_STRAWBERRY_CHANNELS_BROKEN_HINT`, and both name
  `strawberry-graphql>=0.316.0` — the value the hard dependency and the minimum CI matrix
  node already agree on — because a user-facing recovery hint that recommends a version the
  package metadata rejects is a defect in the hint, not in the test that pins it.
- `examples/fakeshop/test_query/test_transport_api.py`'s declared-cap rows carry a
  `Client(enforce_csrf_checks=True)` sibling with a parser / upload-handler sentinel
  ([Decision 18](#decision-18--the-body-gate-runs-before-djangos-multipart-parser)),
  and the file carries the multipart control-field encoding matrix
  ([Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard)).
  Status `413` alone is not evidence of ordering, and a plain `Client()` — whose CSRF
  checks are off — cannot observe it; the rows say so.
- `tests/test_routers.py::test_websocket_branch_wraps_origin_validator_outside_the_auth_stack`
  asserts the wrapper nesting, and the nesting carries an outer layer
  ([Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check)):
  one assertion is **added** for the outermost wrapper, while the test's subject and its two
  existing assertions (the origin validator sits outside the auth stack; the `"http"` value
  is not an `OriginValidator`) are preserved verbatim. Nothing is weakened.
- `tests/test_views.py`'s stream-shape rows carry the third probe outcome — a stand-in whose
  restoring `seek` fails — which is the one shape that must produce the package's controlled
  rejection rather than a `500`
  ([Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)
  #"An unmeasurable stream has three outcomes, not two").

**Placement.** The S1 middleware / Host / CSRF / header / cache / routing regressions and
the entire S2 body-cap matrix live in `examples/fakeshop/test_query/` over the real
`/graphql/` — fakeshop already serves a Django GraphQL view, so the
[live-first coverage mandate][glossary-live-first-coverage-mandate] applies with no
exemption. The router's composition assertions and the WebSocket revalidation matrix stay
in `tests/test_routers.py` (communicator-driven), the documented
genuinely-unreachable-live case. `tests/test_views.py` is new and holds only what a live
request cannot reach — in Slice 1 the import-boundary and public-surface contracts (the
`channels`-free import proof, the `as_view()` kwarg-binding matrix, the async-twin
coroutine marking, and the exact `__all__` / stays-off-the-package-root assertion), in
Slice 2 the cap's argument validation, the settings-precedence matrix, and the stream-shape
rows whose whole point is a negative witness a real server cannot provide (a body file whose
`read` raises if the cap ever calls it, a stream that records every requested size, the
Python 3.10 spool shape reproduced from any interpreter), and in Slice 3 the nine-shape wire
matrix, because status and message are identical across all nine by design and `__cause__` —
the only discriminator — is exposed by no HTTP response, plus the two adapter-installation
rows, whose subject is a class attribute (`request_adapter_class` on each view) rather than
a response.

The same rule places the remaining rows, and it places them where the rule sends them, not
where they are convenient. The multipart control-field matrix and the CSRF-ordering row are
**live** — they are request-shaped, and a direct `parse_json(str)` call or a mocked request
proves nothing about either boundary
([Decisions 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard)
and [18](#decision-18--the-body-gate-runs-before-djangos-multipart-parser)).
The active-operation revocation matrix and the WebSocket Host rows stay in
`tests/test_routers.py`, communicator-driven, under the same documented
genuinely-unreachable-live exemption the rest of the WebSocket surface already carries —
fakeshop still has no `asgi.py`. The third probe outcome stays in `tests/test_views.py`,
because a stream whose restoring `seek` raises is exactly the negative witness a real server
cannot supply.

*Prior test contracts and the changes that replaced them: [rationale companion, Decision 13][rationale-d13].*

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

**One further reconciliation, deliberately *not* a
supersession.** `spec-041` repeatedly describes the package's Strawberry floor as
`strawberry-graphql>=0.262.0`. That floor has since moved to `>=0.316.0` in
`pyproject.toml`, and the minimum CI matrix node pins the same value — so those sentences are
now factually wrong *about live code*, which is the exact condition this decision's own
"why amend" argument is built on. The same pass therefore corrects them, under the repo's
shipped-card closeout convention: **factually-wrong prose only**, checkbox state left exactly
as it is, and the Status line treated as the source of truth. Sentences that are explicitly
historical — "the export's presence at the 0.262.0 floor itself is upstream history,
spot-checked at …" — are **kept**, because they record what was true when that card shipped
and make no claim about live code. This is a correction of the record, not a decision of
`spec-041`'s being superseded, and the amendment banner says so rather than listing it beside
the three superseded items. The corresponding live-code fix —
`routers.py::_STRAWBERRY_CHANNELS_BROKEN_HINT` and the `tests/test_routers.py` assertion that
pins it — is Slice 4's, because a user-facing recovery hint recommending a version the
package metadata rejects is a defect in the hint rather than in the spec that described it.
There is no Python 3.10 complication behind any of this: the dependency floor and the minimum
CI node already agree on `0.316.0`.

**Why amend rather than leave it as history.** `spec-041` is the standing design record
for a module that still exists and is still imported; a reader who finds it and follows
its constructor documentation would wire the insecure shape. This is the narrow case
where a shipped spec's prose becomes factually wrong about live code, and the repo's
practice is to correct the record in the same change rather than let two documents
disagree.

*Rejected alternatives and change record: [rationale companion, Decision 14][rationale-d14].*

### Decision 15 — The `0.0.15` version bump is deferred to the joint cut

**Decision.** No slice in this card edits any part of the version quintet:
`[project].version` in `pyproject.toml`, `__version__` in
`django_strawberry_framework/__init__.py`, `tests/base/test_init.py::test_version`, the
[`docs/GLOSSARY.md`][glossary] package-version line, or the root package `version` entry
in `uv.lock`. This card **shares the `0.0.15` patch line** with
[`TODO-ALPHA-050-0.0.19`][kanban] (both non-Done at authoring time), so the bump from
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

*Rejected alternatives and change record: [rationale companion, Decision 15][rationale-d15].*

### Decision 16 — Revocation is connection-scoped and gated at the WebSocket adapter's outbound frame seam

**Decision.** Revocation is **connection-scoped** and terminates the whole socket. The
package's consumer carries **two** security checkpoints, not one:

1. **Admission** — the existing shallow `handle_subscribe` / `handle_start` pre-hooks
   ([Decision 11](#decision-11--a-websocket-consumer-classfactory-injection-seam-with-a-revalidating-package-default)),
   which decide whether a *new* operation may start.
2. **Outbound frame** — a shared gate that validates the actor immediately before any
   **information-bearing operation frame** is sent, which is what stops an *already-running*
   subscription.

The gated frame types are deliberately `next` (`graphql-transport-ws`), `data` (legacy
`graphql-ws`), and operation-scoped `error` frames. Runtime resolver errors ride inside
`next` / `data`, but pre-execution and other operation errors travel as `error` frames and
may still expose schema names, validation detail, extension output, or
consumer-authored messages; gating them avoids drawing a disclosure distinction the package
would then have to defend. `complete`, `connection_ack`, `connection_error`, `ping` / `pong`,
`ka` and every other connection-control frame delegate to upstream unchanged — they carry no
operation payload, and gating them would price keep-alives as authorization events.

**Delegation is not unconditional, and the condition is the connection's state rather than the
frame's type: once revocation is DECIDED the adapter writes nothing further to this socket at
all**, delegated frames included. That arm is not tidiness. Ending a revoked operation's result
loop *normally* — which is what the stop-aware result source below does — means upstream
proceeds to its own end-of-operation frame (`run_operation`'s `complete` on
`graphql-transport-ws`, `handle_async_results`' on legacy `graphql-ws`), which is not
information-bearing and would otherwise be delegated straight through and committed **after**
the `4403`: a control frame arriving on a socket this package says it terminated, which is the
connection contract the revocation close exists to provide. It is also not merely untidy on a
real server — an ASGI send past the protocol's open state raises, and the raise surfaces inside
upstream's own operation task, which logs it and re-raises, so every revoked subscription would
report a worker-task error. The cut-off is keyed on the **decision**, deliberately, and not on
the committed close: between the two the socket is still physically open, so a frame written in
that window is a frame written to a connection the package has already refused — and the close
is not guaranteed to commit at all, since an attempt may raise and a connection whose attempt
bound is spent stays abandoned, so keying on the commit would leave exactly the connections
that *could not* be closed still emitting. The close itself is unaffected: the state machine
reaches the transport through the adapter's `close`, never through `send_json`.

**A suppression is not an authorization, so that arm takes no lease.** The revoked read on the
delegated path sits deliberately *outside* the connection's actor lease: taking it there would
put every `ping`, `pong` and keep-alive behind the protected-send serialization point, which is
a real head-of-line change on connection-control traffic for no authorization decision. It is
sound because the state is a latch that never returns to `PERMITTED`, so a stale read can only
be stale in one direction — one frame goes out that a concurrent checkpoint was about to forbid,
which is what already happens to any frame that races a checkpoint. The reverse error, a frame
written *after* the decision was published, cannot occur, because the decision is published
synchronously before any await.

**The seam is `GraphQLWSConsumer.websocket_adapter_class`, and it is a class attribute, not
a patch.** Upstream instantiates it **by name**, once per connection, at
`strawberry/http/async_base_view.py::AsyncBaseHTTPView.run`
#"self.websocket_adapter_class(self, request, websocket_response)", and both protocols funnel
every frame through that one object's `send_json`: `graphql-transport-ws` as
`Operation.send_next` -> `handler.send_message` -> adapter, and legacy `graphql-ws` as
`send_data_message` -> `handler.send_message` -> adapter. So
`consumers.py::build_revalidating_consumer_class` derives one private adapter subclass from
`base_consumer_cls.websocket_adapter_class` and installs it on the generated consumer —
*exactly* as it already derives and installs the two protocol handler classes from
`graphql_transport_ws_handler_class` / `graphql_ws_handler_class`. Same factory, same
mechanism, same "read the base off the class the factory was handed so an upstream re-point
is tracked for free" property. This is **not** per-instance patching of upstream internals,
and no upstream module is imported to do it.

**One failure response, at both checkpoints.** On failed validation the package publishes the
connection's revocation decision, suppresses the pending frame, closes the whole socket with
one documented connection-level code and a non-disclosing reason (`4403` / `"Forbidden"`, the
[Error shapes](#error-shapes) row), ends the revoked operation's own result loop through the
package-owned stop-aware result source below, and lets upstream's existing disconnect /
shutdown path cancel and await every remaining registered operation —
`BaseGraphQLTransportWSHandler.shutdown` and, on the legacy protocol,
`BaseGraphQLWSHandler.cleanup` / `::cleanup_operation` each already collect every registered
operation task, cancel it, and await it from the `finally` of their own `handle` loop, so the
package adds **no** teardown of its own beyond settling the one close attempt it owns
(`consumers.py::build_revalidating_consumer_class`'s `GraphQLWebSocketConsumer.disconnect`,
which runs *after* `super()`).
`scope["user"]` is **never** downgraded to anonymous.

**How a revoked operation stops: a package-owned result source, and deliberately not
cancellation.** A revoked operation must stop even when every value it would produce next is
*already available*, and that is the requirement that decides the mechanism. The package
substitutes one per-connection wrapper onto each protocol handler's own `self.schema`
(`consumers.py::_StopAwareSchema`, installed by
`consumers.py::_install_stop_aware_schema`); the wrapper's `subscribe` delegates to the real
schema and returns `consumers.py::_stop_aware_results`, a generator that consults the
connection's revocation state **before each pull** and simply **returns** once the connection
is revoked. Upstream's `async for result in result_source` loop (`run_operation` on
`graphql-transport-ws`, `handle_async_results` on legacy `graphql-ws`) therefore ends
**normally**, at its own next iteration, with no cancellation anywhere in the mechanism, and
the wrapper `aclose()`s the inner source in its own `finally` — so the subscription
generator's own `finally` runs deterministically *at the revocation* rather than whenever the
interpreter's asyncgen finalizer reaches it. That `finally` is load-bearing rather than
tidy-minded: `graphql-transport-ws` never closes its result source on **any** arm — no
`finally`, no `aclosing`, the local simply goes out of scope — while legacy
`cleanup_operation` closes whatever it registered, which is now this wrapper, so closing it
closes the real generator underneath. Reading the state before the pull rather than after it
is what makes the residue bounded and deterministic: **the suppressed frame's own value is
the last one the resolver is ever asked for.** The read takes no lease, because the state is
a latch and a stale `False` costs exactly one further value — which the outbound checkpoint
then refuses under the lease like any other frame — whereas taking the lease there would
serialize a connection's result *production* behind its own sends.

**Why cancellation cannot do this job**, stated because the mechanism it replaces was
plausible and wrong. `asyncio.Task.cancel()` on the *running* task only **requests**
cancellation; the request is consumed when the task is next rescheduled, which needs an await
that actually yields to the event loop. The suppressed-frame path has none: an uncontended
`asyncio.Lock.acquire()` returns without suspending, the revoked short-circuit takes no
session read, an already-decided close returns immediately, and an immediate-yield generator
hands over its next value without suspending either. A cancellation requested from there is
never delivered, so the operation keeps producing values the gate keeps suppressing, and it
monopolizes the loop at exactly the moment revocation should be unwinding it. Nothing is
disclosed — the frames stay suppressed — but the socket's teardown is starved, and on the
legacy protocol `cleanup_operation` *awaits* the operation task, so the teardown deadlocks
outright rather than merely lagging. Termination is therefore the mechanism, and the
outbound checkpoint adds **no suspension point of its own** on the way out.

**The substitution is narrow, and transparent by the only measure that matters.** Only the
two handler subclasses' `self.schema` is replaced, never the consumer's: upstream's
`AsyncBaseHTTPView.run` reads the *consumer's* `self.schema`, passes it to the handler as an
ordinary keyword, and never sees the wrapper. The two handler modules read exactly two
attributes off the schema they are handed — `subscribe` in both, and `execute` — and perform
no `isinstance` or `type` test on it; `subscribe` is the one the wrapper defines, and
`execute` and every other name resolve through `__getattr__` to the real schema **by
identity**. Non-subscription operations therefore need none of this and get none: `execute`
returns a single result and never loops, so that call is upstream's own, and the real schema
builds every execution context, which is why `info.schema` and every extension still see the
real object. One path arrives at the outbound gate with no operation of the package's to end
at all — the protocols' subscription-limit `error` frame, which both handlers emit from the
connection's own message-loop task — and it needs no carve-out, because nothing is cancelled:
the close alone is the whole rejection there.

**The close is a state machine, not a flag** (`consumers.py::_ConnectionRevocation`, one
instance per connection on `consumer._revocation`). Three facts have to stay separable — that
revocation was **decided**, that a close is **in flight**, and that a close **completed** —
because one boolean standing for all three records a close that raised, or one that was
abandoned, as a close that was committed, after which no later checkpoint ever tries again.
Information-bearing frames stay fail-closed either way, so this is not a disclosure hole; what
it costs is the *other* half of the promise, since the documented `4403` would silently never
reach the client — leaving it holding a socket this package has stopped writing to and will
never explain, while every checkpoint that could have retried the close reads a completed one.
The five states, and everything that follows from them:

- `PERMITTED` — the **only** state in which a checkpoint may authorize an operation or a
  frame. `decide()` moves it to `DECIDED`.
- `DECIDED` — revocation is published, no attempt is in flight, and one is still permitted.
  Reached from `PERMITTED` by `decide()`, and from `CLOSING` when an attempt **raised** with
  the attempt bound not yet spent.
- `CLOSING` — a connection-owned attempt is in flight; every checkpoint that arrives here
  awaits *that* attempt rather than starting its own.
- `CLOSED` — terminal: an attempt's own `await` on the adapter's `close` returned, so a
  `4403` was committed to the transport.
- `ABANDONED` — terminal, and reached two ways: the attempt bound is spent and no close ever
  completed, **or** the attempt was cancelled. A cancelled attempt records this state itself,
  before re-raising, which is what keeps it from resting in `CLOSING` — a state that claims an
  attempt is still in flight.

`decide()` is **synchronous and runs before any await**, which is what lets every checkpoint —
and the stop-aware result source — refuse on the published decision **read-free**, at no
session-read cost, however many frames a client pipelines behind the close. The close attempt
is a task the **connection** owns (`asyncio.create_task`), awaited through `asyncio.shield`,
and both halves of that are required: a plain `await` on a task installs it as the awaiter's
`_fut_waiter`, so cancelling the awaiter cancels the awaited task, and both protocols let a
client cancel the operation that first observed the revocation (`complete` / `stop`) — the
close must not die with it. The connection's `disconnect` reaches settlement through `finally`,
so a task the connection owns cannot outlive the connection even when upstream's teardown
raises or is cancelled, and settling never *starts* an attempt: teardown is not a security
checkpoint.

**The outcome is recorded by the task that awaited the close, after its own await returned** —
never before it, and never by a bystander. An ASGI `send` is asynchronous and unacknowledged,
so "a close was decided" and "a close reached the transport" are different facts, and a flag
set before the await records the first as the second. An attempt that **raised** is not a
success: the state returns to `DECIDED`, the failure is logged once naming the attempt and the
bound, and the next permitted checkpoint starts exactly one new attempt. The bound is
`consumers.py::_MAX_REVOCATION_CLOSE_ATTEMPTS` — the first attempt plus exactly **one** retry
— and it is bounded rather than open because checkpoints are client-driven, so an unbounded
retry hands a client one attempted close per frame it chooses to provoke, and because the
realistic raise set is not transient (a disconnected transport, a server state assertion, an
`OSError`), so a third attempt cannot succeed where the first two did not. Past the bound the
connection is `ABANDONED`: no further attempt, and the outbound gate stays fail-closed for
every information-bearing frame — the property that does not depend on the close reaching the
wire at all. Because exactly one attempt is ever in flight and only a *raise* reopens the
door, the ordinary path can never put two `4403` frames on the socket.

**A CANCELLED close attempt is TERMINAL, and settlement is what makes that true.** ASGI's
`send` returns `None` and offers no acknowledgement, so a cancellation delivered while the
close is suspended says nothing about whether the frame was committed: the outcome is
*unobservable*, and a retry would risk a second `4403` for a close that probably succeeded. So
no retry is attempted — but the attempt does not rest in `CLOSING` either, because a state
claiming an attempt is in flight must not outlive the attempt. The task records `ABANDONED`
itself, before re-raising, and it is the task that records it rather than its awaiter because
the task is the only party that knows whether the cancellation arrived before or after its own
`await` returned.

Only the connection's **final teardown** cancels this task. That premise is what the rest
rests on: the socket is already going away, so no later attempt could reach a client, which is
why terminal is the right answer rather than a retry. `settle` is the attempt's terminal owner
and is reached from `disconnect` through `finally`, so a cancelled or failing upstream teardown
cannot skip it and no task the connection owns outlives the connection. A cancellation
delivered to `settle` is answered rather than shielded away: shielding alone would let the
caller return while the task it was settling stayed suspended on a transport that is going
away, so `settle` cancels the attempt, awaits it to completion, and re-raises — the caller's
cancellation is honoured, and nothing retains the connection past it. Under *repeated*
cancellation the guarantee weakens by exactly one step, stated rather than left to be
discovered: the attempt is left cancel-requested and terminal rather than awaited to
completion.

The attempt's guard is `Exception` and not `BaseException` for the matching split: a
disconnected transport, a state assertion and an `OSError` are failures this connection can
still answer for, while an `asyncio.CancelledError` is the loop taking the connection away.
The failure is recorded and deliberately **not** re-raised out of the task — an awaiting
checkpoint's job is to know the attempt finished, not to inherit its exception, and an attempt
whose awaiter was cancelled must not leave an unretrieved exception behind either.

There is deliberately **no protocol-specific operation error before the close**. The actor is
connection-scoped, so the close *is* the rejection; error-then-close only adds protocol
asymmetry (two payload shapes for one event) and one more race between the error frame and
the close frame. This is also **forced rather than merely chosen**, and the derivation is
worth recording because it changes shipped behavior: an admission-checkpoint denial would
have to be delivered as an operation-scoped `error` frame, which is a gated type, so
checkpoint 2 would validate it against the same revoked actor, fail, suppress it, and close —
the client would never see it. A single unified response is therefore the only coherent
reading, and the consequence is explicit: the per-operation revoked-session `error` message
and its one per-protocol payload difference (a list for `graphql-transport-ws`, a bare object
for legacy `graphql-ws`) **leave the package** along with the `graphql.GraphQLError` import
that formatted them. That deletion belongs to the change that implements this decision, not
to Slice 5, because leaving an unreachable send path behind would be dead code under
`fail_under = 100`.

**One connection-local lease, held through the send, shared with the auth layer.** A single
`asyncio.Lock` spans the whole critical section: the window / cache decision, the session
read, the revoked-state transition, **and the actual send**. Holding it through the send is
intentional and is the reason the gate is sound. Releasing after validation would admit this
interleaving: sibling task A passes validation; sibling task B then detects revocation and
begins closing; task A, already authorized, emits its payload anyway.

It lives on the **ASGI scope** (`utils/sessions.py::actor_lease`, keyed into
`ConnectionActorState`) rather than on the consumer instance, and that placement is
load-bearing rather than incidental. A lock private to the consumer is still exactly one per
connection, but it is unreachable by the one revocation the package performs *itself*: a
same-connection `logout` (`auth/mutations.py::_channels_logout`) holds only
`auth/sessions.py::scope_session_lock`, so two private locks give **no ordering at all**
between the two state machines. Since an ASGI send is asynchronous, that left an interleaving
no after-the-fact check can repair — a checkpoint authorizes a frame, suspends inside `send`,
the whole logout completes through that suspension, and the frame is committed to a socket
whose identity no longer exists; a generation compared after `send` returns is checked against
bytes already on the wire. `utils/sessions.py::actor_transition` therefore takes the same
lease for the duration of the native teardown, which makes the two mutually exclusive in both
directions and puts the positive-window cache hit — an authorization decision that performs no
read, and therefore leaves no trace in the read budget below — under the same lease as an
uncached validation. **Lock order: `scope_session_lock` OUTER, the actor lease INNER**, with
`_channels_logout` the only site that holds both and nothing holding the lease ever entering
the auth layer.

The accepted cost is stated rather than discovered: a per-connection serialization point on
the outbound hot path, so concurrent operations on one socket wait behind a session-store read,
a same-connection `logout` waits behind an in-flight protected frame, and that frame's
successor waits behind the `logout`. *The lease* serializes **one connection** only — never a
`complete`, never a keep-alive, and never a frame on an unrelated connection — and an idle
socket never takes it at all (an anonymous socket takes it, then refuses or proceeds without a
read). What the lease scopes is not the whole blocking story, though, and the difference is
measured rather than reasoned about in the budget immediately below.

**The measured budget, and the one lever that moves it.** Measured on one machine against
local SQLite with `db` sessions, driving
`consumers.py::send_revalidated_operation_frame` directly. Treat the *shape* as the finding
and the absolute numbers as one deployment's price, not a portable guarantee:

- **A revalidated frame costs ~1-2 ms**, against ~0.55 us for a frame served inside a positive
  window and ~0.5 us for an anonymous socket. One connection sustains roughly **550-670
  protected frames/s**.
- **Both read-free paths are dominated by acquiring the lease**, which is why
  `utils/sessions.py::actor_lease` hands the lock back instead of wrapping it in an
  `asynccontextmanager`: the wrapper builds an async generator and an
  `_AsyncGeneratorContextManager` per acquisition and drives that generator once each way,
  measured at ~0.8 us per frame on the same harness - more than half of either figure above,
  on the two paths that have nothing else in them. The revalidated frame is unaffected,
  because a session read is three orders of magnitude larger.
- **Concurrency on one connection buys nothing**, as designed: eight tasks on a single socket
  measured at or below the serial rate. That is the lease, and it is the property that makes
  the gate sound.
- **Concurrency across *distinct* connections also buys almost nothing**, which is *not* the
  lease. Aggregate throughput plateaus at roughly **1.0-1.3k protected frames/s per process**
  no matter how many connections are open — sixteen concurrent authenticated sockets got
  ~60-80 frames/s each.
- **The cause is a single shared thread.** `channels.auth.get_user` is a
  `DatabaseSyncToAsync`, i.e. `thread_sensitive=True`, so every actor revalidation in the
  process — every connection's — runs on **one** asgiref executor thread. Probing thread
  identity across eight concurrent connections observed exactly one.
- **So a stalled store is a process-wide event, not a per-connection one.** Holding one
  connection's session read inside that thread blocked an *unrelated* connection's protected
  frame for the full duration of the stall. This is the one place where the per-connection
  framing of the lease does not describe the observable blast radius.
- **Changing the session backend is not the lever.** `cached_db` and a pure in-memory
  `cache` backend land in the same order of magnitude as `db` at the ceiling, because the
  revalidation still resolves the actor row across the same single thread.

**The lever that does move it is `websocket_revalidation_window`.** A positive window serves
the frame from the cached validation, which removes the sync boundary altogether — and with
it both the process-wide ceiling and the cross-connection stall coupling — for two to three
orders of magnitude. The `0.0` default is therefore a **correctness** default, not a
throughput one: a deployment whose authenticated subscription fan-out exceeds a few hundred
protected frames/s per process must price a positive window deliberately, and the docs say so
in those terms
([Doc updates](#doc-updates)). Lifting the ceiling *without* a window — by taking the actor
read off the thread-sensitive executor — is a change to a security boundary's concurrency
model and is **not** attempted by this card
([Risks and open questions](#risks-and-open-questions)).

**No package-level timeout on the read**, deliberately. The *behavior* on a failed or slow
read is already specified — `consumers.py::_actor_is_current` fails closed, so a driver-level
timeout surfaces as denial and revocation, never as a permitted frame — and only the *bound*
is deployment-owned, through the session database's own
`DATABASES[...]["OPTIONS"]` connect / statement timeouts. An `asyncio.wait_for` inside the
lock would not reclaim anything: the executor thread and its half-open connection would be
abandoned mid-read while the next frame queues behind the same thread, which makes a stalled
store strictly worse rather than bounded.

**The window keeps its meaning, expanded consistently across both checkpoints.**
`websocket_revalidation_window` is **the maximum age of a successful actor validation that
may authorize a new operation or an information-bearing outbound operation frame**. `0.0`
revalidates at every admission and at every `next` / `data` / operation `error` frame; a
positive value permits reuse only while the last successful validation is younger than that
value. No artificial minimum interval, no second setting, no background task, and an idle
authenticated socket performs **zero** database reads. One knob, one meaning, two
checkpoints.

**The idle-socket consequence**, stated explicitly rather than left implicit: a revoked
subscription that produces no further events may stay **physically open indefinitely**,
retaining its socket, its subscription task, its session object, and its stale actor
reference. That is accepted, because it has **no authorization capability while idle** — its
next operation or information-bearing frame must pass the gate, fail, and close the
connection. Idle timeout, maximum socket lifetime, and aggregate connection limits are
transport-resource policy owned by the ASGI server, the reverse proxy, or a deliberately
injected consumer
([Decision 12](#decision-12--maximum-connection-lifetime-is-documented-and-seamed-not-silently-enforced)):
DoS-relevant, documented as such, and **not** required to make the package's authorization
boundary true. Conflating the two is exactly the error Decision 12 names.

**The production claim, in the exact words the docs and docstrings must use.** *A revoked
actor cannot admit another operation or emit another information-bearing operation frame.
Detection is event-boundary-driven, not an asynchronous promise to interrupt an idle resolver
at the instant an external logout occurs.* `consumers.py`'s module docstring and
`GraphQLWebSocketConsumer`'s carry that claim in those words, in place of any "a revoked
session stops executing" / "without the socket having to end" wording: on this contract the
socket *does* end, and an already-running subscription is exactly the case such wording
gets wrong. Correcting those two docstrings belongs to the change that implements this
decision, not to Slice 5's prose sweep: they are load-bearing security claims in the file
being rewritten.

*Rejected alternatives and change record: [rationale companion, Decision 16][rationale-d16].*

### Decision 17 — Multipart control fields stay Django-parsed, behind a strict loss-detection guard

**Decision.** Django's `MultiPartParser`, `request.POST`, `request.FILES` and the upload
handlers remain the **sole owners** of multipart framing, limits and file streaming. The
package adds a guard at its own boundary, and nothing else: no copy or subclass of
`MultiPartParser._parse`, no double-read-and-rewind of the body, no monkeypatching of
`force_str`, and no second multipart parser anywhere in the package.

An accepted multipart control document must satisfy **three requirements** before Strawberry
parses `operations` / `map` as JSON. They are independent requirements and emphatically **not
rungs of a fallback chain**: Django applies no such order, so no requirement may be treated as
satisfied by another one falling through to it.

1. **The encoding Django will actually decode with must canonicalize to UTF-8.** That encoding
   is `request.encoding or settings.DEFAULT_CHARSET` — verbatim the value
   `HttpRequest.parse_file_upload` and `MultiPartParser.__init__` produce between them, and the
   only value Django decodes a non-file field with. It is checked whatever the client declared,
   which is the point: `request.encoding` is Django's documented per-request override, so one
   line of consumer middleware assigning it overwrites the promotion a declared `charset=utf-8`
   performed, and the declaration must never be allowed to mask that. Validating the
   declaration *instead* would let a client choose which value was checked while Django decoded
   with the other one — and because a Latin-1 decode never fails, requirement 3 could not see
   the substitution either.
2. **A declared top-level `charset`, when present, must canonicalize to UTF-8 as well.**
   Requirement 1 does not imply this and cannot. Django consults the declaration exactly
   **once**, at `HttpRequest._set_content_type_params`, which promotes a *usable* `charset` onto
   `request.encoding` and silently drops an unusable one; at parse time `content_params` is
   never read again. So for a codec name Django cannot load, `request.encoding` stays `None`,
   requirement 1 is satisfied by a UTF-8 `DEFAULT_CHARSET`, and the request would be accepted
   with its declaration honoured by nobody. The package refuses it instead — and refuses a
   *usable* non-UTF-8 declaration too, so a client asking for an encoding this endpoint will
   not honour always gets a controlled `400` rather than a decode in some other encoding, and
   the two requirements never have to be reasoned about jointly.
3. **A decoded control value must not carry Django's replacement marker.** After
   `request.POST` is populated, the guard inspects **only** the serialized `operations` and
   `map` values and refuses a literal `U+FFFD` before `json.loads` runs.

All three apply to precisely the requests whose non-file fields Django decodes, which is a
multipart **POST** and nothing else — the same `views.py::_is_multipart_form_post`
discriminator that scopes
[Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)'s
multipart carve-out. A stale `multipart/form-data` `Content-Type` on a `GET` therefore
describes a form nothing will parse, and refusing it would be the package inventing a
rejection for bytes nobody decodes.

Requirements 1 and 2 accept exactly the codec aliases `codecs.lookup` canonicalizes to UTF-8,
never a name comparison: every UTF-8 alias passes (`utf8`, `U8`, one the package never heard
of), the near-miss `utf-8-sig` is a *different* codec and is refused because it would swallow
the BOM [Decision 10](#decision-10--a-utf-8-bom-is-rejected) deliberately rejects, and a name
Python cannot resolve cannot be proven UTF-8 and is therefore a refusal.

A project that reconfigures `DEFAULT_CHARSET` away from UTF-8 is consequently refused when
nothing else supplies the encoding, and **accepted** when the client declares UTF-8 — because
that declaration is promoted onto `request.encoding` and is genuinely what Django decodes with.
The requirements track Django's real behavior rather than restating a rung order of the
package's own.

The guard is one shared helper on `_RequestBodyBoundaryMixin`; each view overrides upstream's
`parse_multipart` with a thin delegate that runs the helper and then calls `super()` — the
sync view synchronously in two statements, the async view as a coroutine in three, because its
request adapter's form data must be awaited before it can be handed over, which is the same
forced sync/async asymmetry the two `run` overrides already carry. No new module, and the mixin
keeps being the single home of the request-body boundary
([Decision 6](#decision-6--the-graphql-http-endpoint-is-a-package-owned-django-view-in-the-consumers-urlconf)).

**Why a loss *detector* rather than a strict decoder.** Django decodes multipart **field**
data with `force_str(..., errors="replace")` and honours a per-part `charset` only in the
**file** branch, so by the time the package sees `operations` and `map` they are `str` with
every decode failure already collapsed to `U+FFFD`. The original bytes are gone. Two live
probes confirmed the consequence: an `operations` field declared `charset=iso-8859-1` and
carrying a raw Latin-1 byte executed with `200`, and an `operations` field with no charset
and a malformed UTF-8 byte (`0x80`) was replacement-decoded and also executed with `200`. A
strict decode is therefore *unavailable* at this seam, and the honest options are to detect
the loss or to own the parser. This decision detects the loss.

**The contract, stated precisely.** An accepted multipart control document must be decoded by
Django in UTF-8, must not have *declared* any other encoding, **and** must survive that
decoding without a replacement marker. That is deliberately **slightly narrower** than "every
valid UTF-8 document": a document that
legitimately contains a literal `U+FFFD` character is refused, because the package cannot
distinguish it from a replacement Django generated. It is also deliberately **much wider**
than ASCII-only: genuine multibyte UTF-8 passes untouched, so ordinary browser
`JSON.stringify` output with non-ASCII variable values keeps working, and a client that
genuinely needs a replacement character in its document sends the ASCII escape
`\ufffd` — which is what a JSON serializer emitting `ensure_ascii` output produces anyway.
The contract is deterministic, fail-closed, and free of a private-parser maintenance fork
across Django 5.2 through current.

| multipart `operations` on the wire | Django's decode | package guard | outcome |
|---|---|---|---|
| UTF-8, ASCII only | clean | passes | **success** |
| UTF-8, genuine multibyte (`café`) | clean | passes | **success** |
| ASCII with a JSON escape (`\u00e9`, or `\ufffd`) | clean | passes | **success** |
| declared `charset=iso-8859-1` (or `utf-16`, or `utf-8-sig`) | clean, wrong codec — a usable declaration is promoted onto `request.encoding` | refused at requirement 2 | `400` |
| declared `charset=no-such-codec` | Django drops the unusable name and decodes with `DEFAULT_CHARSET` | refused at requirement 2 | `400` (a declaration nobody honoured) |
| no charset, `DEFAULT_CHARSET` reconfigured to `iso-8859-1` | clean, wrong codec | refused at requirement 1 | `400` |
| declared `charset=utf-8`, `DEFAULT_CHARSET` reconfigured to `iso-8859-1` | clean UTF-8 — the declaration is what `MultiPartParser` receives | passes | **success** |
| declared `charset=utf-8`, consumer middleware assigned a non-UTF-8 `request.encoding` | clean, wrong codec | refused at requirement 1 | `400` (the declaration cannot mask the override) |
| no charset, malformed UTF-8 byte | replaced with `U+FFFD` | refused at requirement 3 | `400` |
| UTF-8 containing a literal `U+FFFD` | clean | refused at requirement 3 | `400` (the accepted narrowing) |

*Rejected alternatives and change record: [rationale companion, Decision 17][rationale-d17].*

### Decision 18 — The body gate runs before Django's multipart parser

**Decision.** The body gate precedes Django's multipart parser under **two** arrangements, and
the package ships both: the ordering is supplied by the **middleware chain** where
`GraphQLRequestBodyBoundaryMiddleware` is installed, and by the **view itself** where it is
not. Neither reimplements token validation, and neither adds a required `MIDDLEWARE` entry.
Both enforce the cap and both enforce CSRF; they differ only in which class performs the check.

**The chain-supplied arrangement.** `GraphQLRequestBodyBoundaryMiddleware` runs the
whole boundary from `process_view`, which Django calls after URL resolution and before any
later middleware's `process_view` — hence before the CSRF middleware's. It holds no policy of
its own: it reaches the limit, the refusal statuses and the wire reasons by instantiating the
resolved view exactly as `View.as_view` does, so the limit that applies is the mount's own
`max_request_body_bytes`. An `HTTPException` becomes the same `text/plain` response upstream's
`dispatch` produces, so a client cannot tell from the response which side of the CSRF check
refused it.

Install it **immediately before the project's own CSRF entry**, by the full leaf dotted path
`django_strawberry_framework.middleware.request_body.GraphQLRequestBodyBoundaryMiddleware` —
`middleware/__init__.py` deliberately re-exports nothing, so importing the leaf module is the
opt-in, exactly as
[`spec-042`][spec-042] pinned for the toolbar middleware. A chain
that lists it *after* a CSRF entry is refused at startup with `ConfigurationError` rather than
allowed to fail open,
because that order would put the parse back in front of the cap. The audit compares entries by
**resolved class**, so a subclass of either side is recognized; where a chain carries more than
one CSRF entry it is judged against the **first**, since that is the entry whose `request.POST`
read would parse the body.

**The view-local fallback.** Where the chain does not supply the ordering, the package view is
`csrf_exempt` on the **outside** and re-enters Django's public `csrf_protect` on the
**inside**, after the body gate. The fixed order inside the view is:

1. the outer dispatch callback carries the exemption, so the global
   `CsrfViewMiddleware.process_view` returns before it touches `request.POST` (its earlier
   `process_request` may still run and reads no body — it only reads the cookie secret);
2. resolve and enforce the package body limit, returning the controlled `413` immediately if
   a declared multipart size exceeds it — **before** `request.POST`, `request.FILES`,
   `MultiPartParser`, or any upload handler;
3. otherwise enter a private continuation wrapped with Django's public `csrf_protect`, which
   delegates to Strawberry's inherited `run`.

The exemption is stamped by the package, once, on the callback `as_view()` returns — a single
override on the shared mixin, so both views get it and a URLconf author cannot forget it.
Django's `csrf_exempt` preserves the async view's coroutine marking by construction, so
`AsyncDjangoGraphQLView` keeps being dispatched on the event loop.

**The switch between them is per-request, not per-deployment.** The callback's `csrf_exempt`
value is a lazily-evaluated object rather than `True`, because whether the ordering is supplied
by the chain is not known when a URLconf is imported and a deployment must not have to state
the same fact twice. It reads **false for a request whose boundary a chain entry has actually
run** — the narrow fact, and the load-bearing one, since that is the request whose body is
proven measured — and **true for every other request**. So there are three states, not two:

- the chain ran the boundary, the exemption is false, and the deployment's own configured CSRF
  class runs in full, after the cap;
- no boundary middleware is installed, the exemption is true, and the view supplies the
  ordering itself exactly as it does with this middleware absent;
- the middleware is installed but **declined this callback** (below), the exemption is true,
  and the request keeps the view-local arrangement. The CSRF **class** degrades to Django's
  stock `CsrfViewMiddleware` for that request; the **ordering** does not degrade, and the cap
  still runs.

The guarantee is scoped to the chain that handles the request. A nested handler invoked inside
another handler's response cycle is a different chain, and the arrangement each request gets is
the one its own chain supplies.

**Which callbacks the middleware runs a boundary for.** It recognizes a package view by
attribute, never by importing the view classes, and the recognition **ends at the boundary**:
it runs a package view's boundary only for a callback whose `view_class` carries that boundary
**as something callable**, tested by attribute **on the class, before anything is
constructed**. It never calls anything that is not a class to try, it builds nothing it has not
established a boundary on, and **a read it cannot complete is a decline rather than an
exception out of the hook**. Every other callback is declined and keeps the view-local
arrangement.

Every outcome the **recognition** reaches is therefore a controlled one — a refusal, a stamp,
or a decline — including for a callback whose attribute reads raise instead of answering.
Running a boundary the recognition has *accepted* is a separate question and is deliberately
not guarded: a boundary that raises anything but `HTTPException` surfaces that mount's own
failure, package or forged, **exactly as it would with this middleware uninstalled**. A guard
there would sit across the body cap's own errors.

**The outer exemption is an ORDERING MECHANISM, NOT a CSRF bypass**, and this spec says so in
those words because it is the single sentence most likely to be misread. Every request that
gets past the size boundary still undergoes Django's **complete** CSRF implementation, from
Django's own code: cookie and header tokens, form tokens, `Origin` / `Referer` checks,
`CSRF_FAILURE_VIEW`, cookie rotation, and `Vary: Cookie`. The protected continuation is
package-owned and non-optional; there is **no consumer bypass switch**, no setting, and no
view kwarg that disables it.

**The invariant it buys.** Because the inner `csrf_protect` is entered unconditionally, the
GraphQL POST endpoint stays CSRF-protected **even if a consumer omits `CsrfViewMiddleware` from
`MIDDLEWARE` entirely**. The reordering therefore strengthens the boundary it reorders.
Django's own `csrf_protect` docstring settles the double-processing question — "Using both, or
using the decorator multiple times, is harmless and efficient" — so a project with the global
middleware installed pays a second cookie-secret read and nothing else. Where a CSRF check has
already run for this request, Django's own `csrf_processing_done` makes the continuation's
`process_view` a no-op, which is what makes **exactly one complete CSRF check** the guarantee in
all three states rather than one-or-two.

**Why the declared gate needs this at all.** `CsrfViewMiddleware._check_token` reads
`request.POST.get("csrfmiddlewaretoken", "")` for every cookie-bearing POST — even one that
will ultimately authenticate through the `X-CSRFToken` header — and `_check_token` runs from
`process_view`, before the view's `run` reaches
`_enforce_request_body_limit`. On a multipart request that single access invokes Django's
multipart parser and the upload handlers. Without one of the two arrangements above, the
declared gate would therefore run **after** the parser it claims to precede
([Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)
step 3). A plain `Client()` disables CSRF, so the global middleware exits before
`_check_token` and a row driven that way observes only the view-local branch: status `413`
alone is not evidence of ordering
([Decision 13](#decision-13--test-strategy-which-existing-tests-change-and-why)).

**What this does not change.** ASGI has already received and spooled the raw body in either
case; that half is unfixable in the application and is
[Decision 8](#decision-8--the-deployment-layer-cap-is-a-co-requirement-not-an-alternative)'s
deployment-layer co-requirement. What the reorder buys is that Django's **parser** and
**upload handlers** no longer run on a payload the package has already decided to refuse.

**Two consequences worth naming rather than discovering.** (a) On
`AsyncDjangoGraphQLView`, `csrf_protect`'s pre-processing is synchronous inside its async
wrapper, so the token check's `request.POST` read happens on the event loop — for a request
that has already passed the size gate, which is precisely why the gate comes first. (b) An
`HTTPException` raised inside the continuation (a `400` from the wire contract, say) unwinds
past `csrf_protect` without reaching its `process_response`, so those error responses do not
carry a rotated CSRF cookie; the `413` is raised outside the continuation entirely and never
did.

*Rejected alternatives and change record: [rationale companion, Decision 18][rationale-d18].*

### Decision 19 — A Django-backed WebSocket Host boundary, beside Channels' Origin check

**Decision.** The package adds a **WebSocket Host boundary**, and adds it by *calling Django*
rather than by implementing one. One small **private** ASGI middleware,
`DjangoWebSocketHostValidator`, projects the handshake's Host-related metadata into a minimal
Django `HttpRequest` and calls the public `request.get_host()`. The package parses and matches
no hostnames itself.

The composition becomes:

```python
DjangoWebSocketHostValidator(
    AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter([re_path(websocket_url_pattern, consumer)])),
    ),
)
```

**Host and Origin stay two separate checks.** Host answers *which server authority the client
addressed*; Origin answers *which browser origin initiated the socket*. Passing one must never
substitute for passing the other, and the router's claim now names the specific check that
delivers each. Channels' validator is left untouched.

**Where it lives, and why not in `routers.py`.** In `consumers.py`, beside the consumer
factory: that module is already the WebSocket-transport module, it is already `channels`-free
at import time with its `channels` imports made inside coroutines, and the denial reuses
`channels.security.websocket.WebsocketDenier` — imported the same way — so a denied `Host`
handshake looks byte-identical on the wire to a denied `Origin` handshake. `routers.py` stays
a composition module that *names* wrappers rather than defining them, which is the shape it
already has for `AllowedHostsOriginValidator` and `AuthMiddlewareStack`. The module's docstring
first line widens accordingly, and that matters mechanically: `scripts/build_tree_md.py`
renders that exact line, so Slice 5's regenerate picks up the wider scope.

**The projection preserves Django's semantics, deliberately and item by item.** Each of these
is a property of Django's own ASGI request adapter, reproduced so that WebSocket and HTTP
answer the same question the same way:

- collect the ASGI host header **without trusting its casing** (ASGI header names are
  lowercase bytes by spec, but the projection normalizes rather than assumes);
- **preserve duplicate values in the same comma-joined form** Django's ASGI request adapter
  uses (`django/core/handlers/asgi.py::ASGIRequest.__init__` #"join(value) for name"), so an
  ambiguous duplicate `Host`
  header fails validation exactly as it does on HTTP rather than being silently reduced to
  one value;
- include `X-Forwarded-Host`, so `USE_X_FORWARDED_HOST` behaves identically to HTTP;
- include `scope["server"]` as `SERVER_NAME` / `SERVER_PORT`, and when the scope carries no
  server at all, Django's own literals — `SERVER_NAME = "unknown"` and `SERVER_PORT = "0"`,
  the exact pair `django/core/handlers/asgi.py::ASGIRequest.__init__` installs — because that
  pair is what `HttpRequest._get_raw_host` reconstructs the host from when no host header is
  present. The literals are Django's, not the package's invention, and naming them is what
  makes the resulting **verdict** derivable rather than assumed: `"unknown"` with port `"0"`
  reconstructs to `"unknown:0"`, so a handshake carrying no host header, no
  `X-Forwarded-Host` and no `scope["server"]` is **denied** under any `ALLOWED_HOSTS` that
  does not contain `"unknown"` or `"*"`;
- decode header bytes with the **Latin-1** Django/ASGI transport convention, the same codec
  Django's adapter and Channels' `OriginValidator` both use.

`HttpRequest.get_host()` then **exclusively owns** syntax checking, port removal, IPv4 and
IPv6 handling, trailing-dot behavior, `ALLOWED_HOSTS` matching, wildcards, and the
`DEBUG`-and-empty-`ALLOWED_HOSTS` localhost defaults. The package contributes the projection
and nothing else.

**Only `DisallowedHost` becomes a denial.** The validator catches `DisallowedHost` and denies
the handshake **before authentication and before the consumer is constructed**. Any other
exception propagates: a bug in the projection must stay visible rather than being normalized
into "that host is not allowed", which would be indistinguishable from correct operation.

**Why call Django rather than narrow the claim.**
`channels.security.websocket.OriginValidator.__call__` reads the `Origin` header and nothing
else, and `AllowedHostsOriginValidator` is a factory that configures it with
`settings.ALLOWED_HOSTS`, or — under `DEBUG` with that setting empty — with its own hardcoded
`["localhost", "127.0.0.1", "[::1]"]`; the name is not evidence of behavior. That hardcoded
list is a second reason to delegate rather than to trust a name: in the same situation
`HttpRequest.get_host()` substitutes `[".localhost", "127.0.0.1", "[::1]"]`, so the leading
dot that makes Django accept every `*.localhost` subdomain is absent from Channels' list. Two
boundaries a reader would both call "allowed hosts" therefore already disagree about what the
`DEBUG` default means, which is exactly why the package's Host answer must be Django's own
`get_host()` and never a second expression of its own. Narrowing
the package's claim to Origin-only is the least surprising correction and is rejected,
because it leaves the handshake **accepting a hostile `Host`** with nothing else in the
stack to catch it: Django never sees the WebSocket handshake at all, so unlike HTTP there is
no other owner for the question. A boundary the package documents as absent is still absent.

**What this deliberately does not do.** It keeps Channels' validator untouched, invents no
second allowed-host matching algorithm, adds **no new setting** (WebSocket now follows the
same Django configuration as HTTP, `ALLOWED_HOSTS` included), and works across supported
WebSocket protocol versions because the ASGI specification requires an HTTP/2 or HTTP/3
`:authority` pseudo-header to be exposed as a `host` header in `scope["headers"]`. The
validator stays **private** and package-owned; its contract is "adapt the ASGI handshake and
invoke Django's Host boundary", never "reimplement Django Host validation". A consumer who
wants a different Host policy configures `ALLOWED_HOSTS`, exactly as they would for HTTP.

*Rejected alternatives and change record: [rationale companion, Decision 19][rationale-d19].*

## Implementation plan

| Slice | Finding | Where | Work | Risk profile |
|---|---|---|---|---|
| 1 | S1 | `routers.py`, new `views.py`, `tests/test_routers.py`, new `tests/test_views.py`, live tier | protocol split; required `django_application`; `websocket_url_pattern`; the package view; rewrite 5 router tests; live middleware / Host / CSRF / header / cache / routing proofs | **HIGH** — the breaking change; every downstream slice builds on the new shape |
| 2 | S2 | `views.py`, new `_request_body.py`, `conf.py`, live tier, `tests/test_views.py` | cumulative cap pre-parse, measured not materialized; the one private-attribute compatibility helper and its **three** probe outcomes ([Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)); `csrf_exempt` / `csrf_protect` re-entry so the gate really precedes `MultiPartParser` ([Decision 18](#decision-18--the-body-gate-runs-before-djangos-multipart-parser)); `MAX_REQUEST_BODY_BYTES` + view kwarg; the full regression matrix incl. the py3.10 / Django 5.2.0 floor | MED-HIGH — the measurement pins private Django internals whose seekability shape differs by interpreter, the CSRF re-entry reorders a security middleware, and multipart interaction with the [`Upload`][glossary-upload-scalar] path is the sharp edge |
| 3 | S9 | `views.py` (the mixin's `parse_json`, the multipart control-field guard, **and** `_RawBodyRequestAdapter`), both patch modules' docstrings, `_strawberry_patches.py`, `test_products_api.py`, `test_transport_api.py`, `tests/test_cross_web_patches.py`, `tests/test_views.py` | strict UTF-8 decode on the view's `parse_json`, fed by the view's own `request_adapter_class`; the multipart control-document encoding + loss guard behind two `parse_multipart` delegates ([Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard)); the patch gate narrowed to upstream defects; invert 3 live tests; re-aim 2 package tests; the kill-switch matrix in both opt-out spellings | LOW-MED — the JSON-body half is measured behavior with one rejection branch; the multipart half adds a second boundary on a path Django decodes first |
| 4 | S11 | `routers.py`, `consumers.py` (WS consumer + 2 handler pre-hooks + the derived outbound-frame adapter + the private Host validator), `utils/sessions.py`, `exceptions.py`, `auth/sessions.py`, `tests/test_routers.py` | injection seam with a validated factory contract; the shared revalidation decision function; the adapter-level outbound-frame gate, its connection-scoped actor lease and its one close code ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)); `DjangoWebSocketHostValidator` ([Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check)); window kwarg and its typed domain; the shared safe value-describer; the multi-yield revoke-mid-subscription matrix on both protocols; the `0.316.0` install-hint correction | **HIGH** — async, per-frame, communicator-driven, and the lease is held across a send |
| 5 | S12 | `docs/`, `spec-041`, glossary DB, kanban DB | migration note; transport guidance; `spec-041` amendment **plus** its stale `0.262.0` floor prose; GLOSSARY + TREE regen; card wrap | mechanical breadth; **no version quintet, no `CHANGELOG.md`** |

Sequencing inside the card is strict: **Slice 1 first and alone.** Slices 2 and 4 both
need Slice 1's seams (the view and the consumer-injection point respectively); Slice 3 is
independent of all of them and could land in parallel, but its inverted live tests share
`test_products_api.py` with Slice 2's new body-cap tests, so landing it after Slice 2
avoids a merge on that file. Slice 5 last, because it documents what the first four
actually did.

Staged-but-unbuilt slices carry `TODO(spec-046 Slice N)` source anchors at the sites they
will change, paired with `NotImplementedError` where a call path must fail loudly, and
removed in the change that ships the slice — the repo's standing staging discipline.

## Helper-reuse obligations (DRY)

- **The settings read goes through `conf.py`'s existing `Settings` reader.** No local
  `getattr(settings, ...)`; `MAX_REQUEST_BODY_BYTES` joins the existing key block with
  its own module-level key constant, exactly like `NESTED_CONNECTION_STRATEGY`. The rule is
  about **package** settings — the `DJANGO_STRAWBERRY_FRAMEWORK` keys. A **Django** setting a
  decision requires be read verbatim to mirror Django's own expression is not a package
  setting and is read where the mirroring happens: `views.py::_form_encoding_is_utf8` reads
  `settings.DEFAULT_CHARSET` directly because
  [Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard)
  requires the exact pair `MultiPartParser.__init__` resolves, and routing it through
  `conf.py` would put a layer between the check and the expression it must reproduce.
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
- **The WebSocket revalidation is one function, called from all three seams.**
  Each of the two protocol handler subclasses carries a single admission hook — one `await`
  and a `super()` call — and the derived outbound-frame adapter contains one type test, one
  `await` and a `super()` call; every decision (window expiry, session reload, actor
  write-back, revoke-or-continue) lives in the shared function, and the revoke-and-close
  response is a second shared coroutine both checkpoints reach
  ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)).
  The two handler subclasses carry one further hook each, an `__init__` that delegates with
  `super()` and then calls **one** shared installer
  (`consumers.py::_install_stop_aware_schema`) — so the stop-aware result source, like the
  revalidation, is single-sited and serves both protocols from one mechanism rather than
  being spelled once per protocol
  ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
  #"How a revoked operation stops").
  The actor lease, the revocation state machine and the last-validated timestamp are all
  **connection-scoped**, in the two homes a connection already has: the state machine on the
  one consumer instance Channels creates per connection, the timestamp and the lease on that
  connection's ASGI `scope` — never three parallel caches keyed by protocol. The lease is on
  the scope rather than the instance for the reason
  [Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
  gives: it is the one piece of this state the opt-in `auth` layer must also be able to
  acquire, and neither layer may import the other. The state machine is on the instance for
  the mirror reason: nothing outside this module transitions it, and the close attempt it owns
  is a connection-lifetime task rather than an operation-lifetime one.
- **The WebSocket Host boundary calls Django and matches nothing itself.**
  `DjangoWebSocketHostValidator` projects the handshake's Host metadata into a minimal
  `HttpRequest` and calls the public `HttpRequest.get_host()`; `ALLOWED_HOSTS` matching,
  wildcards, port and IPv6 handling, trailing dots, and the `DEBUG` localhost defaults are
  Django's alone, and no second allowed-host expression exists in the package
  ([Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check)).
- **The multipart control-field guard is one helper on the existing mixin.** Both views'
  `parse_multipart` overrides are thin delegates over it, in the same shape the two `run`
  overrides already take — the sync one two statements, the async one three, because the async
  request adapter's form data must be awaited before it can be handed over — and the `400`
  they raise reuses the one `_JSON_PARSE_REASON` constant rather than inventing a second
  reason string
  ([Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard)).
- **Neither CSRF arrangement reimplements any part of Django's check.** The fallback uses
  Django's two public decorators — `csrf_exempt` on the callback `as_view()` returns,
  `csrf_protect` around the private continuation, one `as_view` override on the shared mixin so
  the two views cannot diverge. The chain-supplied arrangement runs the deployment's own
  configured CSRF class untouched, in its own chain position. No package-authored token
  validation, cookie rotation, or `Vary` handling exists anywhere, and the ordering audit
  inspects `MIDDLEWARE` without importing or wrapping any CSRF class
  ([Decision 18](#decision-18--the-body-gate-runs-before-djangos-multipart-parser)).
- **The actor is written back to `scope["user"]` rather than plumbed to readers.** The
  existing [Channels request adapter][glossary-channels-request-adapter] and
  [`request_from_info`][glossary-request_from_info] single-siting is preserved; this card
  adds **no** new request-context decoder, per that helper's hard single-siting rule.
- **The view subclasses upstream rather than reimplementing it.** Four overridden hooks, and
  **every decision body sits once on the one private `_RequestBodyBoundaryMixin` the two views
  share** — that single-siting, not the placement of the override itself, is what stops the
  sync and async colours diverging. Two of the four are hosted on the mixin directly, because
  upstream spells them identically on both views: `as_view` for the CSRF ordering
  ([Decision 18](#decision-18--the-body-gate-runs-before-djangos-multipart-parser))
  and `parse_json` for the wire contract
  ([Decision 9](#decision-9--the-strict-utf-8-wire-contract-is-enforced-by-the-package-view-its-own-body-source-one-strict-decode)).
  The other two are declared on each concrete view, because upstream itself splits them by
  colour and a mixin cannot be both: `run` for the cap
  ([Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)) and
  `parse_multipart` for the control-field guard
  ([Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard)).
  Each of those four per-view overrides is a thin delegate onto a mixin-hosted method, so
  neither pair may carry policy of its own. The view also sets `request_adapter_class` to the
  package's own `_RawBodyRequestAdapter`, which is a class-attribute substitution rather than
  a method override. Every other behavior is inherited from
  `strawberry.django.views.GraphQLView` / `AsyncGraphQLView`.
- **The UTF-8 decode is one `parse_json` override that delegates with `super()`**, so
  upstream stays the only JSON parser in the path. `_patched_parse_json` keeps its own
  `UnicodeDecodeError` → `HTTPException(400, ...)` translation and its
  `_validate_upstream_shape` gate for the upstream-mounted path; no new patch module, no
  second patched method, and no reimplemented parser anywhere. The `400` reason string is
  deliberately named in **both** places rather than imported: an import would make
  `apps.py::ready` load `views.py` (and `strawberry.django.views`) at every consumer's
  startup, channels-only ones included, and would cost the patch module the import-time
  independence that lets it survive a missing dependency long enough to report the
  unsupported shape — and the property that actually matters is that both are byte-identical
  to *upstream's own* literal, which a test asserts against what upstream really raises.
- **The private-Django request-body interaction is single-sited in `_request_body.py`.** It
  is the only file in the package that names `HttpRequest._stream`, `_body`, or
  `_read_started`, it never raises `HTTPException` and never reads settings, and it hands the
  view one boolean; policy — which limit, what the `413` says — stays in `views.py`.
- **The `got {type} {value!r}` tail is rendered by `exceptions.py::describe_value`**, the one
  owner of that fragment, degrading to `an unprintable {type}` for a value that cannot be
  rendered. Every typed configuration rejection this card adds uses it — the revalidation
  window, both router injection seams, and the view's cap resolution — because the tail is
  built at the raise site, where the exception class's own rendering guards cannot help.
- **The session-store resolution is single-sited in `utils/sessions.py::session_store_class`**,
  imported by both `auth/sessions.py::uses_signed_cookie_sessions` and
  `consumers.py::_refreshed_actor`. One `SESSION_ENGINE` expression, hosted outside the
  opt-in `auth` package so neither caller drags the other in.
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
  `CommonMiddleware` answers `GET /graphql` with a `301`; under `DEBUG=False` a `POST` to
  `/graphql` also gets a `301`, which most HTTP clients will not re-`POST`. Under
  `DEBUG=True` it is not a redirect at all:
  `CommonMiddleware.get_full_path_with_slash` raises `RuntimeError` for `DELETE` / `POST` /
  `PUT` / `PATCH` rather than lose the body, so the same request is a `500` on the stack a
  reader is most likely to test it on. The migration note must say both and
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
- **A garbage `Content-Length` is Django's rejection, not the package's.** The package never
  *trusts* such a declaration — its declared-length reader returns `None` for both the absent
  and the unparseable shape, the fail-safe direction — so the counted check runs and can
  refuse an over-limit body with the package's own `413` on its own evidence. A body within
  the cap then reaches `HttpRequest.body`, which evaluates
  `int(self.META.get("CONTENT_LENGTH") or 0)` unguarded and raises `ValueError` from Django
  where the request adapter reads it — still before any JSON parse or schema execution, so
  the security property holds either way, and identically to a mount with the cap disabled.
  No test asserts a status code for this shape, deliberately: doing so would pin Django's
  exception as a package contract, and the two ways to avoid it — counting `request.body` or
  rewriting `META` so the declaration parses — are both rejected by name for
  [Decision 7 in the rationale companion][rationale-d7].
  A conforming server rejects such a header before Django sees it.
- **`request.body` is single-shot, and the cap must leave it usable.** Reading it caches
  `_body` and rebinds `_stream`; reading the *stream* first sets `_read_started` and makes a
  later `request.body` raise `RawPostDataException`. The cap therefore never reads through
  `request.body` and never writes `_body`: it size-probes where the stream allows it, and
  where it must read it reads through `request.read` in bounded chunks and then restores the
  request to an unread shape — old stream closed, a rewound `BytesIO` over the same bytes
  installed, `_read_started` back to `False` — which is a shape Django itself both produces
  and accepts, so Strawberry's later `request.body` returns the original bytes byte-for-byte
  with Django's own ceiling still applied. A request whose stream another component already
  consumed without caching `_body` cannot be measured at all; the cap defers there rather
  than translating that component's `RawPostDataException` into a misleading `413`
  ([Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)).
- **`SpooledTemporaryFile` does not declare `seekable()` at the Python 3.10 floor.** It
  became an `io.IOBase` subclass only in 3.11, so ASGI's body file is seekable *in fact* on
  every supported Python but advertises nothing at the floor this card protects; WSGI's
  `LimitedStream`, by contrast, does declare `seekable()` and returns `False`, with `tell()`
  raising `io.UnsupportedOperation`. The measurement therefore believes `seekable()` when the
  method exists — poking a stream that says no is undefined, and a misbehaving one would
  corrupt the read position — and lets `tell()` decide when it does not. Anything narrower
  drops the ASGI spool onto the read branch at exactly the interpreter the floor gate exists
  for: green on the dev stack, guarantee lost where it matters.
- **An incoherent size probe is a measurement failure, and the direction it fails in
  decides which refusal it gets.** Neither shape is hypothetical: a wrapper that answers
  `tell()` in the coordinates of the whole message over-reports the position, and a queue-
  or iterator-backed stream that can report a position but not take one returns the offset
  it was handed, under-reporting the end. The two are refused differently, because the
  restore is verified **before** the two answers are ever subtracted. An over-reported
  position cannot survive that verification — the restoring seek is issued in the same lying
  coordinates and the verifying `tell()` disagrees — so the probe reports a position it
  could not prove it put back and the request is refused with the package's own `413` on
  **zero bytes read**, plus the one server-side `WARNING` that records a distinction the
  wire deliberately cannot carry. An under-reported end restores cleanly, so its answer
  *is* judged, and it comes out at or below zero — where zero taken at face value would read
  as "within the limit" with no byte read anywhere, the one answer a size probe must never
  be believed on. A probe answering zero or less therefore yields no measurement at all and
  the bounded read supplies the bound. Recovering an over-reporting stream's true bytes is
  impossible, and rewinding to zero instead would corrupt a stream that was legitimately
  mid-position.
  Neither production stream lies (`ASGIRequest`'s spool and `WSGIRequest`'s `LimitedStream`
  both measure honestly on both supported interpreters); these shapes are consumer
  middleware and custom ASGI servers, which is exactly where a silent fail-open would be
  least visible. What no probe can catch is stated rather than implied away: a *plausible*
  lie — an end that is wrong but still ahead of the position — is indistinguishable from a
  measurement without reading the bytes it describes, which is the work the probe exists to
  avoid.
- **A capability call that *raises* is a third outcome, not a variant of the second.** Every
  call the probe makes into a stream it did not create — `seekable()`, the seek to the end,
  the restoring seek, and the subtraction of the two answers — is guarded, and the guard
  branches on *what has already been mutated*. A failure before anything moved leaves the
  original position intact, so the bounded read supplies the bound; a **restore the probe
  cannot prove** — the restoring seek raised, or the `tell()` that verifies it answered
  something other than the position the probe started from — leaves the position unknown, so
  the request is refused with the
  package's own controlled rejection rather than read from an unknown offset, guessed back to
  zero, or allowed to escape as an unrelated `500`
  ([Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)
  #"An unmeasurable stream has three outcomes, not two"). Production streams never take this
  path; consumer middleware and custom ASGI servers are exactly where it would otherwise be
  least visible.
- **Multipart must not be materialized.** Reading `request.body` on a multipart request
  forces the whole payload into memory and defeats Django's streaming upload handlers,
  breaking the [`Upload` scalar][glossary-upload-scalar] /
  [`DjangoMutation`][glossary-djangomutation] file path. The cap branches on
  `request.content_type` and applies the declared-size gate only.
- **The declared multipart gate is an ordering property, not just a cap property.** It runs
  before `MultiPartParser` only because something supplies the ordering — the boundary
  middleware from its chain position, or the view being `csrf_exempt` outside and
  `csrf_protect` inside
  ([Decision 18](#decision-18--the-body-gate-runs-before-djangos-multipart-parser)).
  A regression that proves the gate with a plain `Client()` proves nothing about ordering,
  because that client disables CSRF and the global middleware exits before it reads
  `request.POST`. `Client(enforce_csrf_checks=True)` with a real cookie and header, plus a
  parser or upload-handler sentinel, is the only shape that observes it.
- **A consumer middleware that reads `request.POST` before the view still defeats the
  ordering.** The package can only guarantee that *its own* CSRF re-entry no longer parses
  first; a project middleware that touches `request.POST` on the way in has already invoked
  Django's parser, and the cap then refuses a request whose parse already happened. That is
  stated rather than silently assumed away, and it is the same honesty the
  already-materialized-body case gets in
  [Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared).
- **The multipart control-field guard runs on the values, never on the wire bytes.** Django
  has already decoded them; the guard checks the *declared* encoding, the encoding Django
  actually decodes with, and the presence of `U+FFFD`, and it **refuses** a document that
  legitimately contains a literal `U+FFFD` — the one deliberate false positive of the contract
  ([Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard)).
  It must not be written as a `bytes` decode, because there are no bytes left to decode.
- **GET requests carry no body.** The cap is a no-op on GET; the `variables` /
  `extensions` query-param size is a `TODO-ALPHA-047-0.0.16` concern (S4), and the
  existing `_patched_parse_query_params` shield keeps the body contract off those parses.
- **`ALLOWED_HOSTS = []` with `DEBUG=True`** (fakeshop's shape) makes Django substitute
  `[".localhost", "127.0.0.1", "[::1]"]` — so every `*.localhost` subdomain is accepted, by
  virtue of the leading dot, and so is the IPv6 loopback. The hostile-`Host` live test must
  therefore assert a
  `400` from Django's own host validation, and must not depend on fakeshop's `DEBUG`
  value; it sets `ALLOWED_HOSTS` explicitly with `override_settings`. The **WebSocket**
  hostile-`Host` row inherits the same constraint for the same reason and through the same
  `HttpRequest.get_host()` code path
  ([Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check)),
  which is the point of delegating: one configuration, one matcher, two transports. The row
  that matters is an **allowed `Origin`** paired with a **hostile `Host`**, because either
  check passing alone is not the contract.
- **The router's `"http"` value is now an opaque callable.** The composition test asserts
  object identity with the supplied application rather than structural equality — there is
  nothing left to introspect, which is the point.
- **`lifespan` scope is unchanged.** Channels' `ProtocolTypeRouter` still raises
  `ValueError` for unmapped scope types; uvicorn's startup probe still logs its benign
  "ASGI 'lifespan' protocol appears unsupported".
- **A revalidation database error must fail closed.** A session-store or user-load failure
  during revalidation revokes and closes the connection and is logged; it never falls back to
  the stale cached actor, and it never lets the pending frame out. This mirrors the
  fail-closed posture the shipped
  [auth mutations][glossary-auth-mutations] already take after authentication. The guard
  catches `Exception`, not `BaseException`, so a cancellation raised while a task is being
  torn down propagates instead of being reported to the client as a revocation. Closing on a
  transient store failure is the accepted cost of fail-closed at a connection-scoped
  boundary: an actor the package cannot validate is an actor it cannot authorize a frame for,
  and a reconnect re-reads the session honestly
  ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)).
- **The outbound gate must not deadlock or re-enter.** The connection's actor lease is held
  across the protected send, so nothing reached from inside that critical section may send
  another protected frame: the revoke-and-close path writes no operation `error` frame (which
  is why there is none —
  [Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)),
  and `close` goes out through the adapter's own `close`, which does not pass through
  `send_json` at all. The frame this used to hand-wave about is `complete`, which both protocols
  emit when a result loop **ends normally** — which is exactly how a revoked operation ends now,
  so it is expected rather than incidental, and it is **not** delivered: the adapter writes
  nothing at all once the revocation is decided, so `complete` is dropped in the same arm as
  every other delegated frame rather than landing after the `4403`
  ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
  #"Delegation is not unconditional").
- **Once revocation is decided the package writes nothing further to the socket.** The
  suppression covers frames the adapter otherwise delegates untouched, because an end-of-operation
  `complete` committed after the `4403` would contradict the close, and because an ASGI send past
  the protocol's open state raises inside upstream's own operation task — which logs and re-raises
  it, so every revoked subscription would report a worker-task error. That read is a latch read
  outside the actor lease, deliberately: gating a keep-alive is not an authorization decision and
  must not inherit the protected send's head-of-line cost
  ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
  #"A suppression is not an authorization").
- **A revoked operation ends itself, and the ending is bounded.** The outbound checkpoint
  suppresses and revokes; it does not unwind the operation, and it adds no suspension point of
  its own. The operation's own result loop ends at its next iteration through the stop-aware
  result source, the package closes the inner generator so the subscription's `finally` runs
  at the revocation, and the resolver is asked for no value after the suppressed one
  ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
  #"How a revoked operation stops"). Cancellation is deliberately not the mechanism: a
  cancellation requested from a path that never yields to the event loop is never delivered,
  and on the legacy protocol `cleanup_operation` awaits the operation task, so an operation
  that never ends deadlocks the disconnect rather than merely lagging it.
- **A close that the transport refuses must not be recorded as a close that happened.** The
  revocation state machine keeps "decided", "in flight" and "completed" separate, and the
  outcome is written by the attempt itself after its own `await` returned. A raised attempt
  returns the connection to `DECIDED` and the next permitted checkpoint retries, once; past
  `consumers.py::_MAX_REVOCATION_CLOSE_ATTEMPTS` the connection is abandoned and no further
  attempt is made. Information-bearing frames stay refused in every one of those states, which
  is the property that does not depend on the close reaching the wire
  ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
  #"The close is a state machine").
- **A cancelled close attempt is never retried, and that is a ruling.** ASGI's `send` is
  unacknowledged, so a cancellation delivered mid-close leaves the outcome unobservable and a
  retry would risk a second `4403` for a close that probably succeeded. The attempt is the
  connection's own task, awaited through `asyncio.shield` so cancelling whichever
  client-cancellable operation started it cannot abandon it, and settled by the consumer's
  `disconnect` so it never outlives the connection
  ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)).
- **The Host projection must not swallow its own bugs.** Only `DisallowedHost` becomes a
  denial; every other exception propagates
  ([Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check)).
  A projection bug that silently denied every handshake would be indistinguishable from
  correct `ALLOWED_HOSTS` enforcement, which is the worst possible failure mode for a check
  whose whole value is that it rejects.
- **The revalidation read is router-decided, not alias-pinned.** Per
  [Multi-database cooperation][glossary-multi-database-cooperation] the session and user
  reads honor their models' normal **Django database-router** decisions — the session engine
  and `channels.auth.get_user` each select their connection the way any Django read does, and
  the package captures no alias to force on them. (The word *router* is overloaded in this
  card: here it means Django's `DATABASE_ROUTERS`, never the ASGI
  [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter].) A divergent-router
  deployment therefore gets exactly the routing it configured for those models, which is the
  cooperation the rule asks for; a stronger same-operation-alias guarantee is deliberately
  **not** claimed, because reaching it would mean reimplementing `get_user`.
- **An injected consumer class opts out of revalidation, not out of the wrappers.** All
  **three** wrappers — the package's `DjangoWebSocketHostValidator`, Channels'
  `AllowedHostsOriginValidator`, and `AuthMiddlewareStack` — are applied by the router around
  whatever is injected; a test asserts the full nesting order for an injected class as well
  as for the default. An injected class also opts out of the outbound-frame gate, because the
  gate is installed on the *package's* consumer through its `websocket_adapter_class`; that is
  the same explicit trade the admission hooks already carry, and the docs say so rather than
  implying the gate is structural like the wrappers are
  ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)).
- **A positive `websocket_revalidation_window` is meaningless when a custom class is
  injected.** The constructor rejects that combination rather than silently ignoring the
  window — a knob that does nothing is worse than an error. An explicit `0.0` is accepted
  alongside an injected class, because it configures nothing either way and is already the
  public default: the rule keys on the window's effect, not on its presence in the call, and
  the alternative would be a private omitted-value sentinel in a public signature.
- **ASCII-only in `.py`**; trailing-comma layout via `scripts/check_trailing_commas.py`
  with explicit paths (never the repo-wide auto-fix, which would touch untracked
  concurrent work); `ruff format` + `ruff check --fix` after every edit;
  `::QualifiedName` doc references swept when `routers.py`'s symbols change.
- **Coverage.** `fail_under = 100` must hold with all four new modules added — `views.py`,
  `_request_body.py`, `consumers.py`, `utils/sessions.py`, and no fifth: the
  outbound-frame adapter and the Host validator both live in `consumers.py`, and
  the multipart guard and the CSRF re-entry both live in `views.py`). The cap's
  settings-precedence and
  validation branches, the measurement's per-stream-shape branches, and the window's domain
  arms are package-tier; every request-shaped row is live-tier. No branch of the measurement
  needs a `pragma: no cover`: each stream shape it distinguishes is reachable from a real
  request or from a stand-in that subclasses the production stream class. Two
  consequences are coverage obligations rather than optional tidying: the per-operation
  revoked-session `error` message, its `errors_as_list` per-protocol split, and the
  `graphql.GraphQLError` import that formatted them become unreachable under
  [Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
  and must be **deleted** in the same change rather than left as dead code; and the adapter
  gate's delegated path needs a row per ungated frame type it must not touch **and** its
  post-decision twin, where the same types are dropped instead.
  The revocation state machine and the stop-aware result source add arms of their own that no
  happy-path row reaches: the raised-attempt arm in both of its outcomes (a retry permitted,
  and the bound spent), the second checkpoint that awaits an attempt already in flight rather
  than starting one, the connection teardown that settles an attempt whose starting checkpoint
  is gone, the wrapper's revoked exit and its `StopAsyncIteration` exit, and the wrapper's
  `__getattr__` forwarding for a name other than `subscribe`. Each is reachable from a real
  communicator-driven connection with a controlled adapter or a controlled subscription, so
  none of them wants a `pragma: no cover`.

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
    resolver / parse sentinel that must not fire — **and proof that the refusal itself is
    bounded**: a seekable ASGI body file far larger than the cap whose `read` raises if the
    cap ever calls it is still refused (in-memory and rolled-to-disk, absent and understated
    `Content-Length`); a non-seekable over-limit stream delivers at most `limit + 1` bytes
    and no single requested size exceeds it; a body an earlier middleware already cached is
    refused from that cache with the stream unreadable; and an under-limit control reaches
    Strawberry byte-for-byte, `_body` absent and `_read_started` `False`, through the
    rewound stream the cap installed. The two incoherent `tell()` / `seek` directions get
    separate rows, because the code refuses them differently. An **over-reported position**
    is refused outright, with no measurement and no read: `413`, nothing requested of the
    stream, nothing delivered, `_body` absent, and exactly one `WARNING` naming the probe
    outcome and the offending stream's class. An **under-reported end** — a full body whose
    probe answers zero — restores cleanly, so it is refused a *measurement* only and the
    bounded read supplies the bound: `413` after one bounded read, with bytes demonstrably
    left unread. Its control is a **genuinely empty** body on an honest stream, allowed after
    one bounded read of that same `limit + 1` size, so the probe's zero is never taken on
    trust in either direction. Each guarded capability call gets its own stand-in besides:
    one whose `seekable()` raises, one whose seek-to-end raises, one whose
    subtraction result cannot be produced, and one whose **restoring** seek raises — the
    first three bounded by the read with the original position intact, the last refused with
    the package's own controlled rejection and never a raw `500`, which is the same verdict
    the over-reported position reaches by the other route, since a restore that raises and a
    restore that cannot be verified are one outcome
    ([Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)
    #"An unmeasurable stream has three outcomes, not two"). The **bounded read's own** failure
    gets two rows on both views, backed by a non-seekable stream whose `read` raises after zero
    bytes and after a partial prefix: the package's own controlled rejection with its exact
    reason (never `UnreadablePostError` escaping as a `500`), a read count showing the loop
    stopped at the failure rather than retrying, `_body` absent, the consumed stream neither
    closed nor replaced, `request.body` raising Django's `RawPostDataException` so no partial
    body can reach Strawberry, and exactly one `WARNING` naming the stream's class and
    carrying the `UnreadablePostError` traceback
    ([Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)
    #"The bounded read is guarded for the same reason the probe is").
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
24. `_patched_body` still returns raw bytes, and the rejection is attributable to the strict
    decode on the package view's `parse_json` — reached through the view's own body source,
    which is pinned structurally as well as behaviorally:
    `DjangoGraphQLView.request_adapter_class` **is** `_RawBodyRequestAdapter`, that adapter
    hands over the identical bytes upstream's own adapter raises on, and
    `AsyncDjangoGraphQLView` stays on upstream's async adapter so a later "symmetrization"
    cannot take those bytes away again. `_patched_parse_json` is proven to leave
    upstream's own `bytes` semantics alone, so the ownership split cannot collapse back into
    one site. **And the contract survives the kill switch, in both of its spellings**: the
    same matrix on both package views with
    `APPLY_UPSTREAM_PATCHES = {"strawberry": False}` **and** with the broad `False` that
    opts the `cross_web` half out too, live as well as package-tier. In that same opted-out
    state the upstream bug workarounds the gate *does* own are proven to stop hardening (a
    JSON-scalar body reaches the unhandled `500` it would reach without the patch) — so the
    requirement cannot be satisfied by quietly moving everything somewhere ungated — while
    with the patches **on**, a mount of Strawberry's own view is proven to keep upstream's
    RFC 8259 auto-detection, answering `200` to the BOM'd UTF-16 body the package mount
    refuses. Four answers across two mounts and two patch states; only the package mount is
    constant.

**S11 — actor revalidation** (package, communicator-driven):

25. Establish a socket, then revoke / flush / disable the session through a **separate**
    request; the next operation is refused **without reconnecting**, as a connection close
    (`4403` / `"Forbidden"`) with **no** preceding operation `error` frame
    ([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)).
    Both tiers of "separate"
    are owed and neither subsumes the other: a **real second HTTP request** — an
    `AsyncClient` carrying the socket's own session cookie to a logout view on a
    [Probe URLconf][glossary-probe-urlconf], while the communicator stays open, asserting it
    resolved the same session key and actor *before* asserting the denial, so the real
    cookie / middleware / session-backend lifecycle is what invalidates the socket — plus the
    three direct mutators (session flush, user disabled, password rotated) as precise unit
    controls, one revocation shape each.
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
    window and is refused after it — asserted at **both** checkpoints, since the window's
    meaning is now "the maximum age of a successful validation that may authorize a new
    operation **or** an information-bearing outbound frame". Plus the property the window
    exists to buy: an **idle** authenticated socket performs zero session reads however long
    it sits.
28. An injected `websocket_consumer_class` is still wrapped by **all three** router-applied
    wrappers, in order: `DjangoWebSocketHostValidator`, `AllowedHostsOriginValidator`, and
    `AuthMiddlewareStack`.
29. Injecting a class **and** passing a **positive** window is a construction error; an
    explicit `0.0` alongside an injected class is accepted, since it configures nothing
    either way.
30. A revalidation store failure revokes and closes the connection (fail-closed) and never
    falls back to the cached actor — at both checkpoints, and with the pending frame proven
    not to have been sent.
31. The window's construction-time domain: `bool`, a non-numeric value, a negative number,
    `nan` / `inf`, and an integer with no `float` image are each a
    [`ConfigurationError`][glossary-configurationerror] — with the conversion's
    `OverflowError` chained as `__cause__` and the message rendering rather than raising on
    the value it is rejecting; accepted numbers arrive at the consumer coerced to `float`.
32. The injected-factory contract, at construction: a factory that cannot accept `schema=`
    (with the binding `TypeError` as `__cause__`), one returning a non-callable (`None`, a
    scalar, a mapping, a value whose `repr` cannot be rendered), and an `async def` factory
    (whose refused coroutine is closed, so no "never awaited" warning escapes into the
    consumer's process) are each a [`ConfigurationError`][glossary-configurationerror]; a
    sync factory returning an async ASGI callable is mounted **by identity** inside both
    wrappers; a `TypeError` raised from a correct factory's own body is not normalized; and a
    factory whose signature cannot be introspected is judged by the call.
33. The revalidation resolves its session store **without** the opt-in `auth` package: under
    strict eviction of the whole `django_strawberry_framework.auth` prefix, a real
    authenticated operation over the package's own mount still returns the actor, with
    `utils.sessions` in `sys.modules` and nothing under the `auth` prefix in it. Strict
    eviction is what makes the row a proof rather than a coincidence — a worker that already
    ran the auth suite has those modules cached, so a bare absence assertion would pass
    whatever production imports.

**Active-operation revocation**
([Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam);
package, communicator-driven, **once per protocol**):

34. The active-operation gate, in full: a controlled **multi-yield**
    async subscription; receive result 1; revoke through the existing **real second HTTP
    request** while the operation is still open; release result 2's event; prove result 2 is
    **never delivered**, that the operation has ended and its subscription generator has been
    finalized, and that the connection is closed with `4403` / `"Forbidden"` and no operation
    `error` frame; plus a
    **valid-session control** on the same fixture that receives both results. Both `next`
    (`graphql-transport-ws`) and `data` (legacy `graphql-ws`) are owed; neither protocol's row
    substitutes for the other's, because the two payload sends reach the adapter by different
    call chains.
35. Frame-type discrimination, positively and negatively: an operation-scoped `error` frame is
    gated (a revoked connection does not deliver it), while `complete`, `connection_ack`,
    `ping` / `pong` and `ka` delegate unchanged — a revoked-but-not-yet-closed connection is
    not the fixture for this row; the fixture is a **valid** connection with a session-read
    counter, proving the ungated types cost zero reads. Its counterpart is the *revoked*
    fixture, which proves the other half of the same arm: once revocation is decided **none**
    of those delegated types reaches the wire either — `complete` included, and specifically
    the `complete` upstream emits when the revoked operation's result loop ends normally — and
    the suppression still costs **zero** session reads, because it is a latch read outside the
    actor lease.
36. The seam is structural, not incidental: the generated consumer's
    `websocket_adapter_class` **is** the package's derived adapter, that adapter's base **is**
    the one read off `base_consumer_cls.websocket_adapter_class`, and an injected consumer
    class keeps its own adapter untouched.
37. Serialization: two concurrent operations on one socket cannot interleave a passed
    validation with a sibling's revocation — the losing task's payload is never emitted. And
    the lease's blast radius is bounded: a second connection is unaffected while the first is
    inside the critical section (two distinct scopes, asserted to hold two distinct leases by
    identity). The **same-connection `logout`** is the case a second HTTP request cannot
    reach, and it needs both directions of the exclusion, each driven deterministically with
    no wall-clock waits:
    - the subscription composition on **both** protocols — authenticate, admit a multi-yield
      subscription, receive result 1, run the package's own `logout` on this socket, release
      result 2, and prove the socket closes `4403` with result 2 suppressed and the generator
      finalized, at **no additional session read**: the refusal is the connection's
      authenticated provenance, which is what an implementation reading the live (now
      anonymous) scope actor would get wrong by taking the read-free carve-out and sending;
    - the frame-driven twin, on the protocol that can carry a mutation, proving the `logout`'s
      own `{ok: true}` reply is suppressed like any other post-revocation frame while the
      deleted session row proves the teardown completed durably;
    - the **anonymous control**, with the session-store resolver poisoned so zero reads is a
      positive proof: a socket that was never authenticated logs out, keeps the carve-out, and
      stays fully usable;
    - **logout cannot complete across an authorized send** — park the checkpoint's real send
      delegate (authorization granted, bytes uncommitted), start the `logout`, and prove it
      reaches the scope session lock and stops: session row intact, scope actor untouched, task
      not done. Releasing the park lets the pre-transition frame out, the `logout` linearizes
      behind it, and every later protected frame is refused;
    - **a transition in flight denies both checkpoints, inside a positive window** — park the
      `logout` inside `actor_transition` before Channels replaces the scope actor, with the
      three preconditions asserted (transition open, scope actor still authenticated, window
      timestamp still fresh), then drive a NEW operation into admission and a running
      subscription's next result into the outbound gate. Neither proceeds, asserted positively
      rather than as wire silence: the new operation's resolver never starts and the read count
      never moves — the shape a cache hit outside the lease would satisfy invisibly, since a
      cache hit performs no read to count.
38. The window at the frame checkpoint: with a positive window a revoked subscription keeps
    emitting until the window elapses and is then closed at the next frame, with exactly one
    session read per window rather than per frame.
39. **Termination, not cancellation**, and the residue it bounds — the row that fails if the
    mechanism regresses to a cancellation request. On a subscription whose **next value is
    already available** (an immediate-yield generator, so nothing on the suppressed-frame path
    suspends), a revocation must still stop it: the resolver is asked for **no** value after
    the suppressed one, the subscription's own `finally` runs *at the revocation* rather than
    at interpreter finalization, the operation's result loop ends **normally** — reaching
    upstream's own end-of-operation `complete`, which the adapter then drops rather than
    committing after the `4403`, and which no worker-task error accompanies — and the
    connection's disconnect completes rather than hanging, which is the assertion that catches
    the legacy protocol's `cleanup_operation` awaiting an operation task that never ends. Both
    protocols, and a valid-session control on the same fixture that runs to its natural end and
    *does* receive its `complete`.
40. The substitution is structural and narrow: each generated handler subclass's `schema`
    **is** the package's per-connection wrapper, the **consumer's** own `schema` is **not**,
    every attribute other than `subscribe` resolves to the real schema **by identity** (the
    same object, asserted rather than compared), a non-subscription operation's result comes
    back through upstream's own `execute` with no wrapper in the path, and `info.schema` inside
    a resolver is the real schema. An injected `websocket_consumer_class` keeps its own
    unwrapped schema, exactly as it keeps its own adapter.
41. The close is a state machine, not a boolean, proven on the failure arms a boolean hid: an
    adapter `close` that raises **once** leaves the connection revoked with the socket still up
    and information-bearing frames still refused, and the **next** checkpoint retries the close
    and completes it; a `close` that raises on **every** permitted attempt spends
    `_MAX_REVOCATION_CLOSE_ATTEMPTS`, attempts no third close however many frames the client
    pipelines, and still refuses every information-bearing frame — with one log record per
    failed attempt naming the attempt and the bound. The success control asserts the converse:
    exactly **one** `4403` reaches the wire no matter how many checkpoints observe the
    revocation.
42. The close attempt is the connection's and survives its starter: park the adapter's `close`,
    then cancel the operation that first observed the revocation (`complete` / `stop`) and
    prove the attempt is neither cancelled nor abandoned — it is still awaited and recorded,
    settled by the consumer's own `disconnect` if nothing else awaits it. And the cancelled-
    attempt ruling, asserted positively: an attempt cancelled mid-flight is terminal, recording
    `ABANDONED` itself rather than resting in `CLOSING`; no second close is attempted and no
    second `4403` reaches the wire; settlement is reached through `finally`, so a teardown that
    raises **and** a cancellation delivered inside that teardown both still settle the close;
    and a cancelled settlement cancels the attempt, awaits it, and re-raises.

**Multipart control fields**
([Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard);
live, real multipart requests, **both** package views):

43. The full matrix, as real `multipart/form-data` requests rather than a direct
    `parse_json(str)` call — which cannot prove a wire boundary at all: malformed UTF-8 with
    no charset → `400`; explicit `charset=iso-8859-1` → `400`; a JSON `\uXXXX` escape →
    success; genuine multibyte UTF-8 (the ordinary `JSON.stringify` shape) → success; a
    literal `U+FFFD` in an otherwise-clean document → `400`, the contract's one deliberate
    narrowing. The `map` field carries its own row, so the guard is proven not to inspect
    `operations` alone. **Each of the three requirements fails on its own row**, so removing
    any one of them costs the suite a distinct failure: alongside the usable non-UTF-8
    declarations (`iso-8859-1`, `utf-16`, and the near-miss `utf-8-sig`), a declared
    `charset` naming a codec Django **cannot load** → `400` even though the encoding Django
    would decode with is UTF-8; a `DEFAULT_CHARSET` reconfigured away from UTF-8 with no
    declaration → `400`; the same reconfiguration **with** a declared `charset=utf-8` →
    success, because Django genuinely decodes that form as UTF-8; and a consumer-middleware
    `request.encoding` assignment that a declared `charset=utf-8` must not mask → `400`.
    Each refusal is paired with the otherwise-identical request that executes normally, so no
    row can pass on a boundary that refuses everything. Both package views, since the guard's
    sync and async delegates are different code paths.
44. The upload path still works: an accepted multipart request with a real file reaches the
    [`Upload` scalar][glossary-upload-scalar] mutation unchanged, so the guard is shown to
    have added a boundary without taking Django's streaming upload handling away.

**Cap ordering against CSRF**
([Decision 18](#decision-18--the-body-gate-runs-before-djangos-multipart-parser);
live):

45. `Client(enforce_csrf_checks=True)`, a valid CSRF cookie **and** header, an
    over-package-limit multipart body, and an upload-handler or parser sentinel that must not
    fire: `413` with the sentinel silent. Status `413` alone is explicitly **not** evidence of
    ordering, which is why the sentinel is the assertion and the status is the control.
46. The exemption is not a bypass: with the global `CsrfViewMiddleware` installed, an
    under-limit POST with a missing token → rejected, a wrong token → rejected, a correct
    token → succeeds (the row 4 matrix, re-earned through the inner `csrf_protect`); and
    **with the global middleware removed entirely**, the same three outcomes still hold —
    which is the invariant the re-entry buys and the single most important row of this block.
    Both package views, since the sync and async `csrf_protect` wrappers are different code
    paths in Django.

**The WebSocket Host boundary**
([Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check);
package, communicator-driven):

47. An **allowed `Origin`** with a **hostile
    `Host`** is denied. Plus the converse control (allowed `Host`, hostile `Origin` → denied
    by Channels' validator) and the both-allowed control, so neither check is shown to be
    doing the other's work.
48. Django owns the matching, proven by delegation rather than by re-assertion: under
    `override_settings(ALLOWED_HOSTS=[...])` a wildcard entry, a leading-dot subdomain entry,
    a `Host` carrying an explicit port, an IPv6 literal, and a trailing-dot form each behave
    exactly as `HttpRequest.get_host()` behaves for the same value on HTTP.
49. Ambiguity fails closed: duplicate `Host` headers are comma-joined the way Django's ASGI
    request adapter joins them, so the resulting value fails validation instead of one of the
    two being silently chosen. Header-name casing does not change the outcome.
50. `X-Forwarded-Host` is honoured **only** under `USE_X_FORWARDED_HOST`, identically to HTTP;
    with no host header at all, `scope["server"]` supplies `SERVER_NAME` / `SERVER_PORT`. A
    handshake carrying **no** host header, **no** `X-Forwarded-Host` and **no**
    `scope["server"]` — which is what `channels.testing.WebsocketCommunicator` synthesizes by
    default and what a non-conformant ASGI server can produce — falls back to Django's
    `"unknown"` / `"0"` literals and is **denied**, because `"unknown:0"` is a host no
    `ALLOWED_HOSTS` in this project allows. That fallback arm gets its **own** row: every other
    WebSocket row supplies an allowed `Host` and so executes the arm without consulting it,
    which is statement coverage without behavioral coverage. The row asserts the denial against
    Django's own projection of the same scope rather than a typed-out expectation, with an
    allowed-`Host` control so it cannot pass on a router that denies everything.
51. Only `DisallowedHost` becomes a denial: an unexpected exception raised inside the
    projection propagates rather than being reported as a rejected host, and the row asserts
    the exception type rather than a denial.

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
  HTTP is Django-CSRF-protected now, and the sentence narrows to WebSocket. That guidance
  carries four further paragraphs, and each must name the specific
  mechanism rather than a family:
  - **Revocation.** The exact claim from
    [Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
    (*a revoked actor cannot admit another operation or emit another information-bearing
    operation frame; detection is event-boundary-driven*), the connection close a client
    should expect, the window's expanded meaning, and — stated, not implied — the
    idle-socket residue plus the deployment knobs that bound it. It also carries the
    window's **throughput** role, in the terms
    [Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)'s
    measured budget establishes and without restating its numbers: that `0.0` is a
    correctness default rather than a throughput one, that the revalidated-frame ceiling is
    **per process** rather than per connection, that reaching for a faster session backend
    does not lift it, and that the bound on a stalled session read is the session database's
    own `DATABASES[...]["OPTIONS"]` timeouts because the package deliberately adds none. A
    subscription-heavy deployment must be able to read that paragraph and correctly conclude
    that the window is the knob to reach for.
  - **WebSocket Host.** That the handshake is validated on `Host` **and** `Origin`, by two
    separate wrappers, that `Host` follows the project's existing `ALLOWED_HOSTS` and
    `USE_X_FORWARDED_HOST` exactly as HTTP does, and that no new setting exists
    ([Decision 19](#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check)).
  - **CSRF ordering.** That the ordering comes from one of two places, in one sentence that
    leads with *ordering mechanism, not bypass*, and that the endpoint stays CSRF-protected
    even without the global middleware
    ([Decision 18](#decision-18--the-body-gate-runs-before-djangos-multipart-parser)).
    A reader who skims this paragraph must not come away thinking CSRF was relaxed.
  - **Installing the boundary middleware.** That `GraphQLRequestBodyBoundaryMiddleware` exists,
    what installing it buys — the deployment's *own* configured CSRF class runs the check
    instead of Django's stock one — where it goes (immediately before the project's CSRF
    entry), that a chain listing it afterwards is refused at startup, and that a deployment
    which never edits `MIDDLEWARE` keeps the view-local arrangement with nothing to change. The
    withdrawal wording must be the narrow form the code implements: the exemption is false for
    a request whose boundary a chain entry **ran**, never for any request merely travelling an
    installed chain.
  - **Multipart control documents.** That `operations` / `map` must be effectively UTF-8 and
    must survive Django's decode without a replacement marker, with the `\uXXXX` escape named
    as the way to send a literal `U+FFFD`
    ([Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard)).
- **[`docs/GLOSSARY.md`][glossary]** via the glossary DB + `scripts/build_glossary_md.py`
  re-render — the [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]
  entry rewritten to the new composition and constructor; the
  [Channels request adapter][glossary-channels-request-adapter] entry narrowed to
  WebSocket; the [auth-mutation][glossary-auth-mutations] transport matrix's HTTP row
  corrected; and the new terms this card authors (the package Django view, the body cap,
  the UTF-8 wire contract, the consumer-injection seam, the revalidation window, the
  connection-scoped revocation contract, and the WebSocket Host
  boundary). New
  glossary entries require the maintainer-authorized DB update; they are **not**
  hand-written into the rendered file. Per [`AGENTS.md`][agents] the fold-in belongs to this
  shipping slice, so this spec's own companion term ledger is deliberately **not** enriched
  during authoring.
- **[`docs/TREE.md`][tree]** via `scripts/build_tree_md.py` — all four modules the earlier
  slices add, in both the current and target package layouts: `views.py`, `_request_body.py`,
  `consumers.py`, and `utils/sessions.py`; plus `tests/test_views.py`,
  `examples/fakeshop/test_query/test_transport_api.py` and `tests/test_prove_failability.py`
  in the test trees, and corrected `routers.py` / `tests/test_routers.py` rows. The render is
  source-driven, so that list is what the regenerate publishes rather than a ceiling on it:
  it reads each module docstring's first line, and a missing docstring fails the regenerate
  rather than silently dropping a row.
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

- **`spec-050` Decision 7 is now factually stale, and the joint cut needs one owner.**
  [`spec-050`][spec-050] Decision 7 asserts it is "the **only** card at `0.0.15`" and
  therefore owns the version cut. Card `046` has since joined that patch line, so the
  premise no longer holds and two specs would both claim the quintet. Preferred answer:
  `spec-050` Decision 7 is amended to the joint-cut deferral shape, and whichever of
  `050` / `046` lands **last** carries the quintet plus the `CHANGELOG.md` entry — the
  [joint version cut][glossary-joint-version-cut] rule as written. Fallback: the
  maintainer nominates the cut owner explicitly in the card body, and both specs cite that
  nomination. This spec is written for the deferral either way, so it needs no change
  under either resolution. **Flagged for the maintainer** because amending `spec-050`
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
- **The revalidation's per-authorized-event query cost — now measured, and the measurement
  moved the answer.** One session read per operation is real work on a socket's critical
  path;
  [Decision 16](#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam)
  extends it to every information-bearing outbound frame, so a high-rate authenticated
  subscription at the default window pays one session read **per emitted result**. That
  decision's budget now prices it, and two of this bullet's original premises did not
  survive contact with the numbers. First, the cost is **not** bounded by the
  connection-local lock: it is bounded by the single `thread_sensitive` executor thread that
  every connection's actor read shares, so the ceiling is **per process**, not per socket.
  Second, the fallback this bullet used to name — a session-store-level cache deferred to
  [`TODO-ALPHA-047-0.0.16`][kanban] — is **refuted**: an in-memory session backend measured
  in the same order of magnitude as `db`, because the store was never the bottleneck. Anyone
  reaching for a faster session store to fix this will buy nothing. Preferred answer,
  unchanged in substance and now evidence-backed: keep the default at `0.0`, because a
  stale-actor default is the finding being fixed, and document the window as the throughput
  lever it actually is. **Still flagged for the maintainer**, and now the sharper question:
  the only way to lift the per-process ceiling *without* a positive window is to take the
  actor read off the thread-sensitive executor, which trades a shared thread for
  per-revalidation database connections and changes the concurrency model of an
  authorization boundary. That is a deliberate design change, not a tuning knob, and it
  belongs to a card that can carry the connection-pool and transaction-context analysis with
  it — not to this one, and not to a silent amendment of Decision 16.
- **`csrf_protect` on the async view at the Django 5.2.0 floor.** Django's
  `make_middleware_decorator` branches on `iscoroutinefunction(view_func)` and produces an
  async wrapper, verified at the installed 6.0.5; the same branch is expected at the 5.2.0
  floor but has not been read there in this pass.
  [Decision 18](#decision-18--the-body-gate-runs-before-djangos-multipart-parser)
  is written as **decided**, and a builder is verifying the floor empirically in an isolated
  venv. Preferred answer: no change — the decorator is public API and its async support
  predates the floor. Fallback if the floor lacks it: the async view's continuation is wrapped
  by an explicit `sync_to_async`-free equivalent built from `CsrfViewMiddleware`'s own
  `process_view` / `process_response`, which is still Django's implementation and still not a
  reimplementation — **but that fallback is an amendment to Decision 18 and must be recorded
  as one, not applied silently.**
- **The multipart contract's one deliberate false positive.** A control document containing a
  literal `U+FFFD` is refused, because Django's replacement-decoding makes it
  indistinguishable from a decode failure
  ([Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard)).
  Preferred answer: accept the narrowing, document the `\uXXXX` escape, and record the
  upstream-hook escalation path. Fallback: none inside this package — the alternative is a
  Django parser fork, which the decision rejects by name.
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
  and bounded Relay many-side defaults: [`TODO-ALPHA-047-0.0.16`][kanban]. This card
  ships one transport bound and hands that card the view seam to hang the rest on.
- **Audit S5 — `DjangoFileType.path` in the safe generated output.**
  [`TODO-ALPHA-047-0.0.16`][kanban] / [`TODO-ALPHA-048-0.0.17`][kanban] per the program's
  staging; the [`DjangoFileType`][glossary-djangofiletype] /
  [`DjangoImageType`][glossary-djangoimagetype] output shape is untouched here.
- **Audit S8 / S10 — debug and unexpected-error disclosure failing closed under
  `DEBUG=False`.** [`TODO-ALPHA-048-0.0.17`][kanban]. The
  [developer-only debug posture][glossary-developer-only-debug-posture] and the
  [debug-toolbar middleware][glossary-debug-toolbar-middleware] gating are named in this
  card's transport guidance but not changed by it.
- **Audit S6 / S7 — stale Django resolutions and CI authority / supply-chain pins.**
  [`TODO-ALPHA-049-0.0.18`][kanban].
- **The rest of audit S12 — the full deployment contract.** The `SECURITY.md`
  production-security profile, the mechanical `check --deploy`-style checklist, the
  GlobalID-is-not-a-capability statement, upload-safety guidance beyond body size, and the
  "fakeshop must never be deployed" conspicuous notice: the later cards' doc slices. This
  card ships **only** the migration note plus transport deployment guidance.
- **Secure-default changes to `graphql_ide` / `allow_queries_via_get` / introspection.**
  [`TODO-ALPHA-048-0.0.17`][kanban]. This card proves the knobs work; it does not move
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
- [ ] The cap **measures** the body instead of materializing it: never `len(request.body)`,
      never more than `limit + 1` bytes allocated or read for an over-limit request, an
      allowed body handed back as a rewound stream so Django's own
      `DATA_UPLOAD_MAX_MEMORY_SIZE` still applies, and every `_stream` / `_body` /
      `_read_started` reference confined to `_request_body.py` and pinned on both the
      py3.10 / Django 5.2.0 floor and the current stack.
- [ ] The measurement's capability probe reports **three** outcomes and no capability call is
      unguarded: measurable; safely unmeasurable with the original position intact so the
      bounded read runs (a probed count of zero or less still counted as a measurement
      *failure*); or position potentially corrupted, refused with the package's own controlled
      rejection rather than a raw `500`.
- [ ] The declared multipart ceiling runs **before** `request.POST`, `request.FILES`,
      `MultiPartParser` and every upload handler, proven under
      `Client(enforce_csrf_checks=True)` with a parser / upload-handler sentinel that must not
      fire — and the ordering is shown to be an ordering mechanism and not a bypass, including
      with the global `CsrfViewMiddleware` removed. Proven in **both** arrangements: with
      `GraphQLRequestBodyBoundaryMiddleware` in the chain, and with the chain supplying nothing
      so the view-local re-entry is what holds.
- [ ] `GraphQLRequestBodyBoundaryMiddleware` runs a package view's boundary only for a callback
      whose `view_class` carries that boundary as something callable, tested on the class before
      anything is constructed; a callback it declines keeps the view-local arrangement with the
      cap still enforced; a read it cannot complete declines rather than raising out of
      `process_view`; and a chain that lists it after a CSRF entry is refused at startup.
- [ ] `MAX_REQUEST_BODY_BYTES` exists in `conf.py` with a per-mount view-kwarg override
      and the documented precedence; it is the only settings key this card adds.
- [ ] An `application/json` request body is UTF-8-only: UTF-16 / UTF-32 (BOM and BOM-less)
      and a UTF-8 BOM all return `400`; ordinary UTF-8 is unchanged; sync and async behave
      identically; the three live UTF-16/32/BOM success tests are inverted.
- [ ] A multipart `operations` / `map` control document must be decoded by Django in UTF-8,
      must not have declared any other encoding — including a codec name Django cannot load —
      and must survive that decoding without a `U+FFFD` replacement marker, enforced
      before either value is parsed as JSON, with genuine multibyte UTF-8 and ordinary
      `JSON.stringify` output still accepted — and with Django's `MultiPartParser`,
      `request.POST` / `request.FILES` and the upload handlers still the sole owners of
      multipart parsing (no copy, no subclass, no monkeypatch, no second parser).
- [ ] The wire contract is enforced by the package view itself — its own body source
      (`_RawBodyRequestAdapter`, installed as `request_adapter_class`) feeding one strict
      decode — and holds with `APPLY_UPSTREAM_PATCHES` disabled in either spelling, while
      the upstream bug workarounds that gate does own still respect their opt-out.
- [ ] `_cross_web_patches.py::_patched_body`'s contract and docstring are reconciled
      against the new HTTP path, the new wire contract, and the mount it now serves.
- [ ] A WebSocket consumer-class/factory injection seam exists; an injected factory's calling
      convention and returned application are validated at construction; the injected class
      still sits inside all three router-applied wrappers —
      `DjangoWebSocketHostValidator(AllowedHostsOriginValidator(AuthMiddlewareStack(...)))`;
      the package
      default revalidates the session actor at **both** checkpoints — resolving its session
      store outside the opt-in `auth` package — so a revoked actor can neither admit another
      operation nor emit another `next` / `data` / operation `error` frame, and the connection
      is closed (`4403` / `"Forbidden"`, no preceding operation error) at whichever checkpoint
      notices first, **without a reconnect**;
      `websocket_revalidation_window` makes any accepted delay explicit, means the same thing
      at both checkpoints, and rejects every unusable value as a
      [`ConfigurationError`][glossary-configurationerror].
- [ ] A multi-yield subscription revoked mid-flight delivers **no** further result, on both
      protocols, with a valid-session control that receives both results; the now-unreachable
      per-operation revoked-session error message, its per-protocol payload split, and the
      `graphql.GraphQLError` import are deleted rather than left as dead code.
- [ ] A revoked operation is stopped by **termination**, not cancellation: the package owns the
      generator upstream's `schema.subscribe` returns
      (`consumers.py::_StopAwareSchema` / `::_stop_aware_results`, installed on both protocol
      handlers by `consumers.py::_install_stop_aware_schema`), consults the revocation state
      before each pull, ends the result loop normally, and closes the inner source in its own
      `finally` — proven on a subscription whose next value is already available, where a
      cancellation request could never be delivered, and with the resolver asked for no value
      after the suppressed one. Non-subscription execution is untouched, the consumer's own
      `schema` is not wrapped, and every non-`subscribe` attribute resolves to the real schema
      by identity.
- [ ] The revocation close is a **state machine**, not a boolean
      (`consumers.py::_ConnectionRevocation`): "decided", "in flight" and "completed" stay
      separable; the decision is published synchronously so every checkpoint denies read-free;
      the attempt is a connection-owned task awaited through `asyncio.shield` and settled by
      the consumer's `disconnect` through `finally`, so a raising or cancelled upstream teardown
      cannot skip settlement; the outcome is recorded by the attempt after its own await
      returns; a raised attempt is retried within
      `consumers.py::_MAX_REVOCATION_CLOSE_ATTEMPTS` and then abandoned; a cancelled attempt is
      never retried and is terminal, recording `ABANDONED` itself rather than resting in
      `CLOSING`; a cancelled settlement cancels the attempt, awaits it and re-raises so the
      caller's cancellation is honoured; exactly one `4403` ever reaches the wire; and
      information-bearing frames
      stay refused in every state, so the refusal never depends on the close having been
      committed.
- [ ] Once revocation is **decided** the package puts no further frame on the socket, including
      the connection-control frames the adapter otherwise delegates untouched — proven on the
      end-of-operation `complete` upstream emits when a revoked operation's result loop ends,
      which must not be committed after the `4403` and must not surface as a worker-task error —
      with the cut-off keyed on the decision rather than on the committed close, and the read
      taken outside the actor lease so a keep-alive is never priced as an authorization event.
- [ ] A WebSocket handshake carrying an **allowed `Origin`** and a **hostile `Host`** is
      denied, before authentication and before the consumer is constructed, by a private
      package validator that delegates `ALLOWED_HOSTS` matching to Django's public
      `HttpRequest.get_host()`; Channels' validator is untouched, no second host matcher or
      settings key exists, and only `DisallowedHost` becomes a denial.
- [ ] `routers.py::_STRAWBERRY_CHANNELS_BROKEN_HINT` and its pinning test name
      `strawberry-graphql>=0.316.0`, matching the hard dependency and the minimum CI node, so
      the recovery hint no longer recommends a rejected version.
- [ ] Every preserved WebSocket Origin / auth test still passes unmodified; every rewritten
      HTTP-branch test asserts the new contract; every re-aimed test's inversion is
      named in
      [Decision 13](#decision-13--test-strategy-which-existing-tests-change-and-why).
- [ ] Migration note (old vs new `asgi.py` **plus** the `urlpatterns` entry) and transport
      deployment guidance authored, including the four mechanism paragraphs (revocation and its
      idle-socket residue, the WebSocket Host boundary, the CSRF ordering statement, the
      multipart control-document contract); [`spec-041`][spec-041] amended with the three
      superseded items **and** its stale `strawberry-graphql>=0.262.0` floor prose reconciled
      to `>=0.316.0` (factually-wrong prose only; checkbox state untouched; Status line the
      source of truth).
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
[agents]: ../../AGENTS.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[readme]: ../../README.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[feedback2]: ../feedback2.md
[glossary]: ../GLOSSARY.md
[glossary-auth-mutations]: ../GLOSSARY.md#auth-mutations
[glossary-channels-request-adapter]: ../GLOSSARY.md#channels-request-adapter
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-cookbook-parity]: ../GLOSSARY.md#cookbook-parity
[glossary-debug-toolbar-middleware]: ../GLOSSARY.md#debug-toolbar-middleware
[glossary-developer-only-debug-posture]: ../GLOSSARY.md#developer-only-debug-posture
[glossary-django-appconfig]: ../GLOSSARY.md#django-appconfig
[glossary-djangodebugextension]: ../GLOSSARY.md#djangodebugextension
[glossary-djangofiletype]: ../GLOSSARY.md#djangofiletype
[glossary-djangographqlprotocolrouter]: ../GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangoimagetype]: ../GLOSSARY.md#djangoimagetype
[glossary-djangomodelpermission]: ../GLOSSARY.md#djangomodelpermission
[glossary-djangomutation]: ../GLOSSARY.md#djangomutation
[glossary-djangonodesfield]: ../GLOSSARY.md#djangonodesfield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-eviction-simulated-absence]: ../GLOSSARY.md#eviction-simulated-absence
[glossary-fielderror-envelope]: ../GLOSSARY.md#fielderror-envelope
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-get_queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-graphqltestcase]: ../GLOSSARY.md#graphqltestcase
[glossary-hard-dependency]: ../GLOSSARY.md#hard-dependency
[glossary-joint-version-cut]: ../GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: ../GLOSSARY.md#live-first-coverage-mandate
[glossary-multi-database-cooperation]: ../GLOSSARY.md#multi-database-cooperation
[glossary-orderset]: ../GLOSSARY.md#orderset
[glossary-pep-562-lazy-export]: ../GLOSSARY.md#pep-562-lazy-export
[glossary-probe-urlconf]: ../GLOSSARY.md#probe-urlconf
[glossary-request_from_info]: ../GLOSSARY.md#request_from_info
[glossary-require_optional_module]: ../GLOSSARY.md#require_optional_module
[glossary-schema-reload-discipline]: ../GLOSSARY.md#schema-reload-discipline
[glossary-seed_data]: ../GLOSSARY.md#seed_data
[glossary-single-upstream-parity]: ../GLOSSARY.md#single-upstream-parity
[glossary-soft-dependency]: ../GLOSSARY.md#soft-dependency
[glossary-strawberry_config]: ../GLOSSARY.md#strawberry_config
[glossary-testclient]: ../GLOSSARY.md#testclient
[glossary-upload-scalar]: ../GLOSSARY.md#upload-scalar
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[next]: NEXT.md
[rationale]: appx/spec-046-transport_security-0_0_15-rationale.md
[rationale-d1]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-d10]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-10--a-utf-8-bom-is-rejected
[rationale-d11]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-11--a-websocket-consumer-classfactory-injection-seam-with-a-revalidating-package-default
[rationale-d12]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-12--maximum-connection-lifetime-is-documented-and-seamed-not-silently-enforced
[rationale-d13]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-13--test-strategy-which-existing-tests-change-and-why
[rationale-d14]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-14--this-card-amends-spec-041-and-supersedes-three-of-its-decisions
[rationale-d15]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-15--the-0015-version-bump-is-deferred-to-the-joint-cut
[rationale-d16]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam
[rationale-d17]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard
[rationale-d18]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-18--the-body-gate-runs-before-djangos-multipart-parser
[rationale-d19]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check
[rationale-d2]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-2--http-dispatches-directly-to-a-required-consumer-supplied-django-asgi-application
[rationale-d3]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-3--django_application-is-required-omission-fails-at-construction-with-no-compatibility-fallback
[rationale-d4]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-4--url_pattern-becomes-websocket_url_pattern-with-exact-matching-as-the-secure-default
[rationale-d5]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-5--compatibility-policy-an-intentional-alpha-breaking-change-to-a-security-boundary
[rationale-d6]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-6--the-graphql-http-endpoint-is-a-package-owned-django-view-in-the-consumers-urlconf
[rationale-d7]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared
[rationale-d8]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-8--the-deployment-layer-cap-is-a-co-requirement-not-an-alternative
[rationale-d9]: appx/spec-046-transport_security-0_0_15-rationale.md#decision-9--the-strict-utf-8-wire-contract-is-enforced-by-the-package-view-its-own-body-source-one-strict-decode
[spec-040]: spec-040-auth_mutations-0_0_13.md
[spec-041]: spec-041-channels_router-0_0_14.md
[spec-042]: spec-042-debug_toolbar-0_0_14.md
[spec-050]: spec-050-debug_extraction-0_0_19.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
