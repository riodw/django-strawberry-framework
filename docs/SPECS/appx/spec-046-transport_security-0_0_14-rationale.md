# Rationale: spec-046 — Transport security (rejected alternatives)

Deliberative companion to [`spec-046-transport_security-0_0_14.md`][spec-046]. The spec is the
contract; this file holds the alternatives each decision rejected and why each lost, plus the
derivations that do not change how a decision is implemented. One entry per spec decision, under
the decision's own heading, so a citation such as "Decision 11's rejected alternatives" resolves
to exactly one place.

## Decision entries

### Decision 1 — Spec filename and canonical naming

Spec: [Decision 1][s65-d1].

**Rejected alternative — the `channels_router` slug.** The topic slug is `transport_security`
rather than `channels_router` (the `spec-041` slug) because the card's subject is the transport
boundary as a whole — HTTP ownership, body bounds, wire encoding, and socket actor freshness —
not the router module alone. Two of the four findings (S2's cap and S9's wire contract) land
outside `routers.py` entirely.

### Decision 2 — HTTP dispatches directly to a required, consumer-supplied Django ASGI application

Spec: [Decision 2][s65-d2].

**Why.** It is the only correction that gives the credential-accepting route the same
boundary as the rest of the application, and it deletes code rather than adding it.

**Alternatives rejected.**

- **Keep the Channels HTTP consumer and rebuild Django's boundary around it** (the
  audit's own conditional). Rejected: it means package-owned exact routing, Host
  validation, cookie-auth CSRF, cache variation, body limits, response security headers,
  and IDE/GET controls — a partial re-implementation of `MIDDLEWARE` that must track
  Django's security releases forever. [`AGENTS.md`][agents] #"Always give the root-cause fix even when slower" settles it.
- **Keep the Channels HTTP route but wrap it in Django's middleware chain manually.**
  Rejected: Django's middleware is written against `HttpRequest` / `HttpResponse`, not an
  ASGI scope; the adapter layer needed to make that true *is* `ASGIHandler`, which is
  what `get_asgi_application()` already returns.
- **Reorder the branch so `django_application` comes first.** Rejected: it makes
  the GraphQL consumer unreachable rather than safe, and leaves the whole apparatus in
  place as a trap.
- **Ship both modes with the safe one as the default.** Rejected explicitly by the
  maintainer's pinned direction, and correctly: an unsafe mode that exists is an unsafe
  mode that gets selected, and a security boundary with a documented opt-out is a
  boundary the audit would have to re-find next release.

### Decision 3 — `django_application` is required; omission fails at construction with no compatibility fallback

Spec: [Decision 3][s65-d3].

**Alternatives rejected.**

- **Keep it optional and warn.** Rejected: [`AGENTS.md`][agents] #"never offer defer-the-real-fix sequencing" — and the audit's own closing line, "Do
  not split these into 'ship the warning now, fix the architecture later' work."
- **Derive it internally with a lazy `get_asgi_application()` call.** Rejected on the
  initialization-order ambiguity in the spec's *Why deriving it internally is wrong*; a
  framework must not make Django's setup point implicit.
- **Accept a dotted path string and import it.** Rejected: it adds an import-time failure
  mode and a second way to spell the same thing, for no security gain.
- **Raise `ImproperlyConfigured` instead of `ConfigurationError`.** Rejected:
  [`ConfigurationError`][glossary-configurationerror] is the package's single typed
  configuration failure and is already the router module's available exception with no
  new import.

### Decision 4 — `url_pattern` becomes `websocket_url_pattern`, with exact matching as the secure default

Spec: [Decision 4][s65-d4].

**Why rename rather than keep one shared parameter.** A single parameter that no longer
affects HTTP would be a name that lies. The rename is the diff that tells a migrant the
semantics changed; silently narrowing `url_pattern`'s meaning would let a consumer keep
a custom HTTP-shaped regex that now does nothing to HTTP.

**Why exact rather than prefix.** A prefix default is a default that over-claims paths. On
WebSocket the blast radius is smaller than on HTTP — an over-claimed WS path denies a
handshake rather than exposing one — but the correct default is still the narrow one, and
a consumer wanting a prefix can pass one deliberately.

**Alternatives rejected.**

- **Keep `url_pattern` and accept both spellings.** Rejected: two names for one knob,
  and the compatibility alias would silently accept an HTTP-intended pattern.
- **Default to `r"^ws/graphql/?$"`** (a conventional WS-only path). Rejected: it breaks
  every WebSocket client already connecting on `graphql/` for a cosmetic gain, and the
  endpoint path is the consumer's choice.
- **Keep the prefix default and document the overmatch.** Rejected: documenting a
  routing surprise is not fixing it.

### Decision 5 — Compatibility policy: an intentional alpha breaking change to a security boundary

Spec: [Decision 5][s65-d5].

**Why the alpha break is the right trade.** The package is pre-`1.0` and its documented API
freeze begins at `1.0.0`; strict SemVer applies from `1.0.0` forward, not before. The broken
promise was itself a migration convenience — "a migrant changes exactly the import line" —
purchased by inheriting an upstream HTTP branch that bypasses Django's security middleware on a
route that accepts session credentials. Preserving byte compatibility with that contract means
preserving the defect for every consumer who adopts the router. Correcting a security-boundary
error during alpha costs a documented migration note; deferring it to `1.0.0` costs every
deployment in between.

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

Spec: [Decision 6][s65-d6].

**Why a package view rather than pointing consumers at Strawberry's.** Three reasons, in
order of weight. (a) It is the only home for the S2 cap that works identically on WSGI
and ASGI, sync and async — Django's own view layer. (b) It gives the migration note one
canonical line instead of a fork between "use upstream's view" and "except when you want
the cap". (c) Under the [live-first coverage mandate][glossary-live-first-coverage-mandate]
every S2 regression row is earnable over fakeshop's real `/graphql/` with
`django.test.Client`, rather than mocked at the package tier — decisive, because a body
limit asserted against a fake request proves nothing about the transport. It is also where
S9's wire contract lives, since a package-owned policy needs a package-owned boundary.

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
  precedent shows is easy to get wrong. (The optional ordering middleware of
  [Decision 18][s65-d18] holds no policy and applies no cap of its own; see that entry.)
- **Put the cap in an ASGI wrapper inside the router.** Rejected as the *primary* seam:
  it cannot serve a WSGI deployment, it cannot serve a consumer who adopts the view
  without the router (the common case, since the view needs no `channels`), and it would
  place a GraphQL-specific limit on every path the Django app serves. Its one genuine
  advantage — rejecting mid-stream before Django spools the body — is real, and is exactly
  what [Decision 8][s65-d8] assigns to the deployment layer, where it belongs and already
  exists.

### Decision 7 — The app-level body cap lives in the package Django view, counted not declared

Spec: [Decision 7][s65-d7].

**Alternatives rejected.**

- **Trust `Content-Length` alone.** Rejected by the maintainer's direction and correct on
  the merits: the header is client-supplied and, on ASGI with chunked transfer, may be
  absent entirely.
- **Documented `DATA_UPLOAD_MAX_MEMORY_SIZE` reliance plus a thin wrapper.** Rejected on
  the shared-knob argument in the spec's *Why its own key rather than
  `DATA_UPLOAD_MAX_MEMORY_SIZE`*, plus: it would make the package's most security-visible
  bound something the package neither owns nor tests.
- **An ASGI/middleware guard as the primary seam.** Rejected in [Decision 6][s65-d6];
  its mid-stream advantage is reassigned to the deployment layer.
- **Counting `len(request.body)`.** Its appeal is real — the property is the only *public*
  way to obtain a body, so counting it touches no private attribute. Rejected anyway,
  because it obtains the correct length only after Django has materialized the whole
  request, which makes it a detector rather than a bound; and on the Django 5.2.x series,
  against an absent or understated `Content-Length`, there is no earlier Django check to
  have shrunk that allocation. Measuring the stream Django keeps private, from one module
  pinned to both supported versions, is the smaller compatibility surface of the two — the
  alternative buys its purity with an unbounded allocation on the one path this card exists
  to bound.
- **Stashing the bounded read's bytes in `request._body`.** Rejected even though it mirrors
  what `HttpRequest.body` itself leaves behind: pre-filling Django's cache makes the
  property short-circuit, which silently disables **Django's own**
  `DATA_UPLOAD_MAX_MEMORY_SIZE` for every request that took the bounded branch, so a project
  whose Django knob sits below the package cap would lose it. A package cap adds a ceiling;
  it must not remove one. Handing the bytes back as a rewound stream leaves the property
  fully in charge and needs no ordering discipline to stay correct.
- **Copying Django 6.0's `body` implementation into the package.** Rejected: it
  reimplements a property whose behavior already differs across the supported range, and it
  would still have to make the same `_body`-vs-`_stream` decision. Probing the size and
  leaving the reading to Django's own property is less code and survives the next change to
  it.
- **Spreading `_stream` / `_body` / `_read_started` across the two view classes.** Rejected:
  the version-divergent knowledge *is* the risk, so it belongs in one module beside the
  contract it pins, with the views reading one boolean and owning policy only.
- **Rewriting `META["CONTENT_LENGTH"]` so an unparseable declaration parses.** Rejected: it
  edits the request to make Django's own later read succeed, concealing a malformed header
  the deployment should see, and bounds nothing that the counted check does not already
  bound.
- **Rejecting inside `_patched_parse_json`.** Rejected: the patch modules exist to fix
  *upstream defects*; a package size policy is not a defect fix, it would fire on GET
  query-param parses, and it would be unreachable for a multipart request.
- **Letting an unguarded capability call fall through as a `500`.** The probe's
  `seekable()`, `tell()` and `seek()` calls are made into a stream the package did not
  construct (an ASGI server's, or a consumer middleware's). Rejected: an unrelated `500` is
  the wrong answer at the one seam this design deliberately centralized, so every capability
  call is guarded and a restore the probe cannot verify fails closed with the package's own
  refusal.

### Decision 8 — The deployment-layer cap is a co-requirement, not an alternative

Spec: [Decision 8][s65-d8].

**Alternatives rejected.**

- **Treating the application cap as sufficient and mentioning the proxy in passing.**
  Rejected: it would restate the exact conflation the audit called out, and would make the
  package's own documentation the source of a false guarantee.
- **Listing a header-size knob (`--limit-request-field-size`) beside the body directives.**
  Rejected: it bounds a **header field**, not the body, and no mainstream ASGI server bounds
  the total body at all. A reader scanning a list of concrete directions takes the list, not
  a qualifier, so the list names only real body directives (nginx's `client_max_body_size`,
  Apache's `LimitRequestBody`) and states the ASGI-server absence outright.

### Decision 9 — The strict UTF-8 wire contract is enforced by the package view: its own body source, one strict decode

Spec: [Decision 9][s65-d9].

**Why the decode belongs on the view rather than in the patch module.** Three reasons, and
the first is decisive. (a) A permanent security policy must not share a temporary patch's
lifecycle: an upstream shape change that forces a consumer to disable the patch would
otherwise reopen the parser differential S9 exists to close, silently. That argument
governs the body source identically, which is why the view owns that too — a switchable
body source is a switchable decode. (b) The mixin is one seam covering both transports —
`super()` delegates to upstream's `parse_json`, patched or not, so nothing is reimplemented
and the two views cannot diverge, which is the same single-siting rule
[`request_from_info`][glossary-request_from_info] establishes for request decoding. (c) It
is the same boundary as the body cap: the cap decides which bytes reach the parse, and the
parse decides how those exact bytes become text — one mixin, one subject, the raw request
body.

**Alternatives rejected.**

- **Decode inside `_patched_parse_json`.** The wire contract *is* a property of
  GraphQL-over-HTTP request parsing, and the patch module owns that parse for both
  transports, so putting the decode there costs the fewest lines and covers
  upstream-mounted consumers too. Rejected on ownership: it makes a permanent package
  security policy share the lifecycle — and the `APPLY_UPSTREAM_PATCHES` kill switch — of
  temporary workarounds for upstream bugs. A consumer disabling those workarounds, or a
  maintainer deleting them once upstream fixes them, would then silently restore
  multi-encoding request bodies. A security policy a consumer can switch off by accident is
  not a policy, and the extra reach over upstream-mounted views is not the package's to
  claim.
- **Decode inside `_patched_body`.** Rejected: it re-creates the unhandled-`500`
  path the patch module exists to close, and it would only fix the sync transport.
- **Let `_patched_body` be the package view's sync body source.** One patched property
  already hands raw bytes to both mounts, so the package view would need no adapter of its
  own and the decode would be reached for free. Rejected for the *same* reason the decode
  is not in the patch module: the patch is gated, so the sync half of the wire contract
  would ride `APPLY_UPSTREAM_PATCHES` while the other half did not. With the gate off,
  upstream's sync property decodes first and `parse_json` is never entered with bytes, so a
  BOM'd UTF-16 or UTF-32 body on a mounted sync package view would answer `500` instead of
  the contracted `400`. A decode the bytes never reach is not an enforcement.
- **Override `decode_json` instead of `parse_json`.** Rejected: a `UnicodeDecodeError`
  raised there lands in upstream's `except json.JSONDecodeError`, which does not catch it,
  so the `400` translation would depend on the Strawberry patch being installed — exactly
  the coupling this decision removes.
- **Reject non-UTF-8 by sniffing leading bytes** (a BOM / NUL-pattern check). Rejected: a
  bespoke encoding sniffer is a parser, and adding a second parser to close a parser
  differential is self-defeating. `bytes.decode("utf-8")` is the contract.
- **Set a strict codec on the adapter and let `json.loads` see a `str` everywhere.**
  Rejected — and distinct from the adapter subclass the view does install, which
  *removes* a decode rather than adding one. Putting the strict codec on the adapter
  re-introduces the property-scope raise, on the very transport the subclass exists to
  rescue: a `UnicodeDecodeError` with no `except` above it is a `500`, wherever the codec
  is strict. It also needs a matching change to the async adapter's contract to keep the
  two transports agreeing, losing the sync/async symmetry one inherited `parse_json` gives
  for free.
- **A `STRICT_UTF8_BODY` setting so a consumer can opt out of the policy too.** Rejected:
  a security policy a consumer can switch off is the finding this decision answers, not the
  fix — and [`AGENTS.md`][agents] forbids adding a settings key speculatively. The opt-out
  that does exist is deliberate and explicit: mount upstream's own view.
- **Calling the captured upstream `parse_json` rather than `super()` from the mixin.** The
  mixin's `super().parse_json(data)` resolves to the attribute
  `_strawberry_patches.py::apply` assigns, so the body-envelope guard rides
  `APPLY_UPSTREAM_PATCHES` on a package mount too. Bypassing the patch would give the guard
  the same ungated ownership the wire contract has. Rejected: the guard is a workaround for
  a specific upstream defect (#3398), so it *should* stay opt-out-able — this decision's own
  lifecycle rule applied in the other direction. What does not ride the gate on either mount
  is the strict decode and the body source, which are view-owned code.

**The declared `charset`.** The strict decode governs the bytes; the declared `charset` is
refused separately (`views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration`),
because without it one byte sequence can be `é` to this endpoint and two Latin-1 characters to
any hop that honours the declaration.

- **Refusing an absent declaration.** Rejected: absent is the overwhelmingly common case and
  leaves the strict decode as the only encoding contract — the stronger one, because it
  inspects bytes rather than a header.
- **Comparing the declared name to a literal set.** Rejected: Python's codec machinery already
  resolves every legitimate alias, and a hand-kept alias list is a blacklist by another name.
  `utf-8-sig` is refused despite canonicalizing *near* UTF-8 because it is a different codec
  whose BOM [Decision 10][s65-d10] independently refuses.
- **Two copies of the "is the declaration honourable" test.** Rejected: the JSON gate and the
  multipart gate both ask it, so the answer is one function
  (`views.py::_declared_charset_is_unhonourable`) rather than two copies that can drift on
  what "declared" means — the same reason `views.py::_is_multipart_form_post` is named once.
- **Enumerating methods to preserve upstream's `405`.** The guard is skipped for `GET` only,
  matching `views.py::_RequestBodyBoundaryMixin._enforce_request_body_limit`'s scope so the two
  body boundaries cannot disagree about which requests they govern. A method this endpoint does
  not serve which nonetheless declares an unhonourable `charset` is therefore refused `400`
  before routing would have answered `405`. Accepted: the direction is stricter, the reason
  string is shared with the strict decode's, and agreement between the two body boundaries is
  worth more than the status code on a request that was going to be refused either way.

### Decision 10 — A UTF-8 BOM is rejected

Spec: [Decision 10][s65-d10].

**Alternative rejected.** Accept-and-strip via `utf-8-sig` or an explicit
`lstrip("﻿")`. It is friendlier to one misconfigured client and is what several JSON
parsers do — but it reintroduces the parser differential S9 exists to close, adds a lenient
pre-processing step the contract must then document and test, and buys tolerance for a
payload no correct GraphQL client emits.

### Decision 11 — A WebSocket consumer-class/factory injection seam, with a revalidating package default

Spec: [Decision 11][s65-d11].

**Alternatives rejected.**

- **Revalidate lazily in `ChannelsRequestAdapter.user`.** Rejected: it only fires when
  the package happens to read the actor, so an operation touching no permission gate
  would execute with no revalidation at all — failing the "reload the actor **before
  execution**" requirement — and it can only affect a read, never reject an operation.
- **Revalidate in the consumer's `receive()`.** Rejected: `receive` sees every *inbound*
  frame, including keep-alive pongs, `complete` messages, and `connection_init`, so it would
  fire a session read per frame regardless of whether anything was being authorized — the
  window would be pricing the wrong events. The same cost argument is why the second
  checkpoint gates **outbound** frames, where the set of gated types is exactly the set that
  carries information.
- **Ship a periodic background refresh task.** Rejected: it makes freshness a function of
  wall-clock luck rather than of the operation being authorized, and it adds a task
  lifecycle to a transport helper.
- **Implement the message loop ourselves to own the seam.** Rejected explicitly by the
  maintainer's direction and on the merits: a second GraphQL protocol engine is a
  permanent maintenance surface. `super()`-delegating hooks on upstream's handlers and
  adapter are not an engine.
- **Make revalidation opt-in.** Rejected: the audit's finding is that the default is
  stale; an opt-in fix leaves the default stale. Injecting a custom consumer class is the
  opt-out, and it is an opt-out that requires the consumer to own the concern explicitly.
- **Mount whatever the factory returns and let a bad value fail at the first handshake.**
  Rejected: an injection seam that accepts an object it can already prove is not an
  application converts a configuration mistake into a runtime routing failure, far from the
  line that caused it. Construction is where the seam's contract is knowable, so it is where
  the contract is enforced.
- **Catch `TypeError` around `factory(schema=schema)` instead of pre-binding.** Rejected: a
  `TypeError` raised by the call cannot be told apart from one raised *inside* a correct
  factory's body, so a consumer's own bug would be reported as "your factory has the wrong
  signature" — the wrong diagnosis, with the real traceback buried under `__cause__`.
- **Validate the class branch's `as_asgi(schema=schema)` result too.** Rejected: that return
  value is upstream's contract, not the consumer's, so checking it would assert against
  Strawberry rather than against the injection seam.
- **Resolve the session store from `auth/sessions.py`.** It is where the capability question
  about signed-cookie sessions lives, so the expression looks at home there. Rejected:
  importing a submodule executes its package's `__init__`, and `auth` is structurally opt-in
  with an eager `__init__`, so a transport-layer read would drag the whole GraphQL auth
  subsystem into every process that never asked for it. Making `auth/__init__` lazy instead
  was also rejected — it changes the public opt-in surface [`spec-040`][spec-040] Decision 3
  pins, to solve a transport problem — and duplicating the `SESSION_ENGINE` expression was
  rejected outright: two sites would have to agree about how a consumer-authored engine
  subclass resolves. Both layers read `utils/sessions.py::session_store_class`.

### Decision 12 — Maximum connection lifetime is documented and seamed, not silently enforced

Spec: [Decision 12][s65-d12].

**Alternatives rejected.**

- **Enforce a maximum lifetime in the package at all.** Rejected: a framework-imposed
  disconnect is a visible behavior change for every subscription consumer, with no correct
  default — the right lifetime for a dashboard subscription and for a short-lived
  request-response socket differ by orders of magnitude. The audit asks for "at minimum,
  document a maximum connection lifetime and a consumer-class injection seam"; the seam ships
  in [Decision 11][s65-d11], and with revalidation at both checkpoints, lifetime stops being
  the bound the *authorization* boundary depends on.
- **A `max_connection_lifetime=` kwarg with a default.** Rejected: either the default is
  long enough to be security-irrelevant, or it is short enough to break subscriptions. A
  consumer who wants it can enforce it in the injected class.
- **A package-owned lifetime timer as part of the revocation fix.** Rejected for the same
  reason as the kwarg, and for one more: it would answer a resource question with machinery
  justified by an authorization argument, which is how a transport helper grows a task
  lifecycle nobody asked for. The revocation fix is [Decision 16][s65-d16]'s two checkpoints
  and nothing else — no polling, no background task, no second setting, no maximum-lifetime
  timer.

### Decision 13 — Test strategy: which existing tests change, and why

Spec: [Decision 13][s65-d13].

**Why the active-operation revocation properties are separate rows.** The immediate-yield
subscription a cancellation request could never stop, the structural narrowness of the
stop-aware schema substitution, the close-attempt failure arms (a raised close retried once and
then abandoned while information-bearing frames stay refused), and the close surviving the
cancellation of whichever operation started it each get their own row rather than being folded
into one "revocation works" row. Each fails on its own, so removing any one mechanism costs the
suite a distinct failure — the same discipline the multipart matrix applies to its three
requirements. Rejected: a single combined row, which a boolean flag or an undelivered
cancellation request can satisfy vacuously.

### Decision 14 — This card amends `spec-041` and supersedes three of its decisions

Spec: [Decision 14][s65-d14].

**Alternative rejected.** Leaving `spec-041` untouched and relying on this spec to
supersede it implicitly. Rejected: implicit supersession between two specs at different
paths is exactly how a reader ends up following the wrong one.

### Decision 15 — The version bump is deferred to the joint cut

Spec: [Decision 15][s65-d15].

**Alternatives rejected.**

- **Bump the version in Slice 5.** Rejected: this card shares its patch line with others; a
  per-card bump races the joint cut and gets reconciled twice.
- **Claim the cut for this card because it is the higher-numbered / more urgent one.**
  Rejected: the rule keys on *last to land*, not on card number or priority, and the
  landing order is the maintainer's to decide.
- **Ship the `CHANGELOG.md` entry here and let the cut add the version.** Rejected: the
  [joint version cut][glossary-joint-version-cut] contract puts the `CHANGELOG.md`
  bullets in the cut, and [`AGENTS.md`][agents] requires an explicit grant this card does
  not hold.

### Decision 16 — Revocation is connection-scoped and gated at the WebSocket adapter's outbound frame seam

Spec: [Decision 16][s65-d16]. Admission-only revalidation cannot stop an already-running
subscription from emitting results after its actor is revoked: an admitted subscription iterates
its result source inside one task and never returns through `handle_subscribe`.

**Alternatives rejected.**

- **A send-time guard on `handler.send_message` only.** The obvious smaller seam, and it
  fails on two counts. That funnel also carries connection-control frames
  (`connection_ack`, `complete`, `ka`, `pong`), so a guard there would either price
  keep-alives as authorization events or need a type allow-list anyway — and the type
  allow-list is the part worth having, which the adapter can hold just as well. More
  decisively, a *symmetric payload-only* seam does not exist at the handler level:
  `graphql-transport-ws`'s payload send is `Operation.send_next`, and `Operation(...)` is
  constructed **by name inside `handle_subscribe`**, so reaching it would mean patching an
  upstream internal per instance. The adapter is the one object both protocols already share
  by class attribute.
- **A periodic polling monitor**, in any cadence variant — a fixed interval, a second
  interval setting, or reusing `websocket_revalidation_window` as a poll interval with a
  floor. Rejected: polling is not immediate, it merely creates a detection interval where
  there was none, and it multiplies database reads by the count of **idle authenticated
  connections** — a cost that scales with connections rather than with authorized events,
  which is backwards. It also reintroduces the background-task lifecycle
  [Decision 11][s65-d11] rejects for the same reason.
- **Per-operation revocation without closing the socket.** Rejected: more machinery for a
  smaller guarantee. The actor is a property of the *connection*, so ending one operation
  leaves a socket whose remaining operations are authorized by an actor that no longer exists,
  and the package would then owe a per-operation revocation ledger to keep them straight. This
  is a rejection of the *scope*, not the mechanism: the revoked operation does end — through
  the stop-aware result source, which reads one **connection**-scoped latch and needs no
  ledger — and the socket closes as well.
- **Admission-only, with the S11 claim weakened to match.** Rejected: the stronger contract
  is achievable at this seam, with one derived adapter class and the connection's actor
  lease, so weakening the claim would be choosing a documented gap over a fix.
  [`AGENTS.md`][agents] #"Always give the root-cause fix even when slower" settles it, and
  maximum connection lifetime would otherwise become security-relevant again.
- **A package maximum-connection-lifetime timer as the answer to active-operation
  revocation.** Rejected in [Decision 12][s65-d12]: it answers an authorization question with
  a resource bound, and a bound that arrives minutes late is not a boundary.
- **A bespoke package close code** (e.g. `4499`) instead of upstream's `4403`. Rejected: a
  code unique to "your session was revoked" is a disclosure the reason string deliberately
  avoids, and reusing upstream's own `Forbidden` close keeps every refusal to authorize this
  connection indistinguishable on the wire — the same argument that makes the nine
  encoding-rejection shapes share one `400` ([Decision 9][s65-d9]).

**Why the revoked operation ends by termination rather than cancellation.** Rejected:
cancelling the running operation task. `Task.cancel()` on the *running* task sets a
pending-cancellation request that is consumed only when the task is next rescheduled, which
requires an await that actually yields to the loop — and the suppressed-frame path has none: an
uncontended lock acquire returns without suspending, the revoked short-circuit takes no session
read, an already-decided close returns immediately, and an async generator whose next value is
already available hands it over without yielding. For an immediate-yield subscription the
request is never delivered, so the operation keeps producing values the gate keeps suppressing:
nothing disclosed, but the loop monopolized and the teardown starved — and on the legacy
protocol `cleanup_operation` *awaits* the operation task, so the disconnect deadlocks. With
termination, both protocols' result loops end normally and each sends its own `complete`.

- **`await asyncio.sleep(0)` after `task.cancel()`,** to force the request to be delivered.
  Rejected because it delivers the error in the wrong place: the suspension it creates is in
  the `async for` **body**, so the `CancelledError` unwinds the body and leaves the generator
  *suspended* — the opposite of closing it. It also converts the outbound checkpoint into a
  coroutine that yields to the loop while holding the connection's actor lease, on the hot
  path, to buy nothing.
- **Repeating `task.cancel()`** — once more, or in a loop. Rejected on mechanics: a repeated
  request cannot make a task yield. `cancel()` is a request, not a preemption.
- **Closing the inner source from the checkpoint instead of from the wrapper.** Rejected: the
  checkpoint does not have the source, and reaching it would mean reading a per-operation
  registry off the handler — a second bookkeeping surface for a fact the generator already
  knows. The wrapper's own `finally` is the one place that runs on every exit arm, including
  the revoked one, upstream's normal end, and legacy's `cleanup_operation`.
- **Relying on the interpreter's asyncgen finalizer.** Rejected: it runs at an unrelated
  moment, so a subscription's `finally` — where a consumer releases a broker subscription, a
  cursor, or a lock — would run after the socket had already gone. Closing it *at the
  revocation* is the property worth owning.

**Why the revocation state is a five-state machine rather than a boolean.** One flag set
before the close was awaited conflates three separable facts: that revocation was *decided*,
that a close is *in flight*, and that a close *completed*. A close that raised, or one
abandoned mid-flight, would be recorded permanently as committed, so no later checkpoint
would try again and the documented `4403` could silently never reach the client.
`consumers.py::_ConnectionRevocation` therefore has five named states, a bounded attempt count,
a connection-owned shielded attempt, and an outcome written by the attempt after its own
`await` returns.

- **Moving the boolean's assignment to *after* the `await`.** The minimal edit, and rejected
  because it does not address the failure it appears to fix. An ASGI `send` is unacknowledged:
  a close that commits its frame and is then cancelled — or one whose await never returns
  because the transport is gone — leaves the flag unset, so the *next* checkpoint sends a
  second `4403` for a close that already happened. Two facts cannot be encoded in one bit
  however the assignment is ordered; "in flight" is the third.
- **`asyncio.shield` alone, without a state machine.** Rejected because shielding buys
  *survival*, never *observability*. It stops a cancelled awaiter from taking the close down
  with it — which is why the attempt is shielded — but it says nothing about whether the frame
  reached the transport, because ASGI's `send` returns `None`. Learning the outcome requires
  somebody to record what their own `await` returned, which is what the attempt task does.
- **An unbounded retry.** Rejected: checkpoints are client-driven, so "retry on every
  checkpoint" hands a client one attempted close per frame it chooses to provoke, and the
  realistic raise set — a disconnected transport, a server state assertion, an `OSError` — is
  not transient. Hence `_MAX_REVOCATION_CLOSE_ATTEMPTS`: the first attempt
  plus exactly one retry, and then `ABANDONED`.
- **Retrying a cancelled attempt.** Rejected: the outcome of a cancelled `send` is
  unobservable, so a retry would risk a second `4403` for a close that probably succeeded. Only
  the connection's final teardown cancels the attempt, at which point no retry could reach a
  client anyway, so a cancelled attempt records `ABANDONED`.
- **Re-raising the attempt's exception out of the task, so an awaiting checkpoint learns why.**
  Rejected: an awaiting checkpoint's job is to know the attempt finished, not to inherit its
  exception, and an attempt whose awaiter was cancelled would then leave an unretrieved
  exception behind. The failure is logged once, at the attempt, naming the attempt number and
  the bound.
- **Making the close a per-operation task.** Rejected: both protocols let a client cancel the
  operation that first observed the revocation (`complete` / `stop`), so an operation-owned
  close dies with the operation it happened to be started from. Ownership by the connection is
  what makes the attempt's lifetime match the thing being closed, and the consumer's
  `disconnect` settles it so a task the connection owns cannot outlive the connection.

**Why settlement is terminal.** Shielding keeps the attempt alive through a waiter's
cancellation but does not keep the waiter awaiting it, so a settlement that merely shielded
would let `disconnect` return while the attempt stayed pending, holding the adapter, consumer,
scope, session and a stale actor after the ASGI application had returned.

- **Having the awaiter record a cancelled attempt's state.** Rejected: only the task knows
  whether the cancellation arrived before or after its own `await` returned, so
  `_ConnectionRevocation._attempt_close` sets `ABANDONED` itself before re-raising.
- **Shielding the cancellation away in `settle`.** Rejected: it lets the caller return while
  the task it was settling stays suspended on a transport that is going away. `settle` instead
  cancels the attempt, awaits it to completion, and re-raises, so the caller's cancellation is
  honoured and no task retains the connection past it. The mid-connection shield in `close()`
  stays: a revocation close racing another caller must still survive that caller's
  cancellation. Only final teardown ends the task.
- **A sequential `await super().disconnect(code)` followed by settlement.** Rejected: a
  `CancelledError` arriving while upstream's teardown is still awaiting would leave
  `super().disconnect` and never reach a sequential settlement, orphaning a close the transport
  still has parked. `disconnect` reaches settlement through `finally`.
- **The residual, accepted.** Under *repeated* cancellation the attempt is left
  cancel-requested and terminal rather than awaited to completion: the second cancellation is
  the loop taking the connection away while it is already being taken away, and the state is
  terminal either way.

`settle`'s correctness rests on one premise: only the connection's final teardown cancels the
attempt task. A third-party cancellation would propagate a `CancelledError` in place of a
caller's exception; it is unreachable through any supported seam, because `attempt.cancel()`
occurs once in the package, inside `settle`.

**Why nothing is written once revocation is decided.** A revoked operation's result loop ends
*normally*, so upstream proceeds to its own end-of-operation `complete` — a frame the revocation
itself produces. Delegating it would commit a control frame **after** the `4403`, and an ASGI
send past the protocol's open state raises inside upstream's own operation task, which logs it
and re-raises, so every revoked subscription would report a worker-task error.

- **Exempting `complete` specifically, as an end-of-stream courtesy.** Rejected: a per-type
  carve-out on the one path whose whole value is that it has none, and it does not even buy the
  courtesy, because the frame either races the close or arrives after it. The close *is* the
  end-of-stream signal.
- **Keying the cut-off on the committed close rather than on the decision.** Rejected in both
  directions. Between the decision and the commit the socket is still physically open, so a
  frame written in that window goes to a connection the package has already refused; and the
  close is not guaranteed to commit at all, so keying on the commit would leave exactly the
  connections that *could not* be closed still emitting. The `revoked` latch covers all four
  post-decision states.
- **A lease-free revoked read on the delegated path.** Rejected: without the lease, a control
  frame can pass the read, suspend in upstream's asynchronous send, and commit after another
  task has published the revocation decision. The delegated arm therefore reads the state and
  sends under the connection's actor lease, accepting that a ping or keep-alive can wait behind
  one session read or protected send — the head-of-line cost of the "nothing after revocation"
  invariant. (The stop-aware result source's read is lease-free: a stale `False` there costs one
  more value, which the outbound checkpoint then refuses under the lease.)
- **Routing the close itself through the same gate.** Rejected as a category error: the close
  reaches the transport through the adapter's `close`, not through `send_json`, so it is
  outside the gate by construction — which is also why a gate that refuses everything cannot
  deadlock the revocation it exists to serve.

### Decision 17 — Multipart control fields stay Django-parsed, behind a strict loss-detection guard

Spec: [Decision 17][s65-d17]. Django decodes multipart field data with
`force_str(..., errors="replace")` before the package sees `operations` / `map`, so
[Decision 9][s65-d9]'s strict decode is unavailable at that seam and the control documents need
their own boundary.

**Alternatives rejected.**

- **ASCII-only control fields after Django's decode.** The strongest contract enforceable
  without touching Django's parser, and rejected on breakage: JSON escapes can express any
  Unicode, but a browser's `JSON.stringify` does **not** escape non-ASCII, so every client
  sending a non-ASCII variable through a file upload would break. Refusing a literal `U+FFFD`
  costs one unusable character; refusing all non-ASCII costs a normal client's normal output.
- **A raw-preserving streaming pre-decode seam.** The only way to get "full raw UTF-8", and
  rejected because Django exposes no narrow strict-field decoding hook: reaching one means
  copying `MultiPartParser._parse`, i.e. owning a maintenance fork of Django's multipart
  parser across every supported release, to gain one character of coverage.
- **`FileUploadHandler.receive_data_chunk`.** Rejected: it is called only for **file**
  payloads, never for the non-file fields `operations` and `map` are.
- **`handle_raw_input`.** Rejected: its documented contract is to take over the **entire**
  multipart parse, which is the private-parser fork under a different name.
- **Monkeypatching `force_str`, or the parser's use of it.** Rejected outright: a
  process-wide change to a Django utility, to affect two field values on one endpoint, in a
  package whose whole thesis in this card is that Django owns the HTTP stack.
- **Narrowing the claim instead — "strict UTF-8 applies to `application/json` only; multipart
  inherits Django's replacement semantics."** Accurate, and rejected: it leaves one body
  shape on the endpoint accepting a byte sequence the package's own contract calls invalid,
  which is the parser differential [Decision 9][s65-d9] exists to close. Decision 9's scope
  is a statement about which decision owns which document, not a concession on the endpoint's
  behavior.
- **A fallback chain over the encoding sources** — the declared top-level `charset`, else
  `request.encoding`, else `settings.DEFAULT_CHARSET`, requiring whatever wins to canonicalize
  to UTF-8. Rejected: it is **wrong about Django**, which applies no such rung order. The
  declaration is consulted exactly once, at `HttpRequest._set_content_type_params`, and at
  parse time only `request.encoding or settings.DEFAULT_CHARSET` is ever read. The chain fails
  in both directions: it lets the **declaration** be the value validated while Django decodes
  with something else, so one line of consumer middleware assigning `request.encoding` is
  masked by a client sending `charset=utf-8` (and because a Latin-1 decode never fails, the
  `U+FFFD` check cannot see the substitution either); and it **accepts** a declared codec name
  Django cannot load, because the promotion never happens, `request.encoding` stays `None`, and
  the chain falls through to a UTF-8 `DEFAULT_CHARSET` while the client's declaration was
  honoured by nobody. `views.py::_form_encoding_is_utf8` therefore checks two **independent**
  conditions joined with `and`, and the loss check runs beside them.

**Escalation path.** If distinguishing a genuine literal `U+FFFD` from a replacement-generated
one ever becomes mandatory, the root fix is **upstream**: a public Django hook for strict,
non-file multipart-field decoding. Until one exists at the package's supported floor, the
package must not own or copy Django's parser to get it.

### Decision 18 — The body gate runs before Django's multipart parser

Spec: [Decision 18][s65-d18].

**Why the ordering needs a decision at all.** `CsrfViewMiddleware._check_token` reads
`request.POST` for every cookie-bearing POST — even one that will authenticate through the
`X-CSRFToken` header — and runs from `process_view`, before the view's `run` reaches the body
gate. On a multipart request that single access invokes Django's multipart parser and the
upload handlers. A row driven through a plain `Client()`, whose CSRF checks are disabled, cannot
observe that ordering; status `413` alone is never evidence of it.

**Alternatives rejected.**

- **Narrowing the claim without reordering** — "the view cap prevents Strawberry parsing and
  schema execution; proxy and Django upload settings own multipart resource consumption."
  Rejected: the reorder is achievable with two public Django decorators and no deployment
  surface at all, so narrowing would be choosing a documented gap over a fix that costs less
  than the documentation would.
- **Reimplementing the token check inside the view** to avoid the double middleware pass.
  Rejected: the package would own CSRF validation, cookie rotation, `Vary`, and
  `CSRF_FAILURE_VIEW` — a partial re-implementation of a security middleware that must track
  Django's security releases forever, which is the same mistake S1 exists to undo.
- **A package middleware with a required `MIDDLEWARE` entry, policed by a system check.**
  Rejected: a required deployment line every consumer must add in the right position cuts
  against this card's thesis that Django owns the HTTP stack, and a project-wide cap would need
  a path predicate. What ships,
  `middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware`, has none of those costs:
  the entry is optional (the callback's `csrf_exempt` is a withdrawable object rather than
  `True`, so a deployment that never edits `MIDDLEWARE` keeps the view-local arrangement);
  misordering is a startup `ConfigurationError` from the middleware's own `__init__` rather than
  a check a consumer may never run; and the middleware holds no policy — it runs a boundary only
  for callbacks it recognizes as package views, at the resolved mount's own
  `max_request_body_bytes`, reached by building the view as `View.as_view` does.
- **Relying on the view-local `csrf_protect` re-entry alone.** It is built from Django's
  *stock* `CsrfViewMiddleware`, so on a project whose `MIDDLEWARE` names a subclass —
  strengthened token binding, tenant checks, a different rejection policy — the continuation
  runs the base implementation in that subclass's place. The configured class is a property of
  the chain and cannot be recovered from inside the view, which is why the ordering also has to
  be available *from* the chain.
- **Removing the exemption and the stock re-entry outright,** so the middleware is the only
  arrangement. Rejected: it changes behaviour for every deployment that has not edited
  `MIDDLEWARE`, which is precisely the population the fallback exists for.
- **Withdrawing the exemption chain-wide** ("this middleware is handling a request").
  Rejected: that is a property of the *chain*, not of the request, so any callback the
  middleware did not recognize would travel with the exemption withdrawn and no boundary run,
  and the configured CSRF middleware would parse the form ahead of the cap. The withdrawal is
  keyed off the per-request `_BOUNDARY_ENFORCED` stamp, so "the exemption is withdrawn" and
  "the boundary ran" are one fact about one request. A declined callback keeps the exemption:
  the CSRF **class** degrades, while ordering and cap stay intact.

**Where recognition probes, and how widely it guards.** Recognition ends at the boundary: a
callback carrying the package's private marker over a buildable class that is no package view
must not reach `process_view`'s boundary call and raise there.

- **Probing the built instance.** Rejected: it closes the same hole, but only after running a
  foreign class's `__init__`. The probe reads the **class**, before construction, and requires
  a **callable** boundary attribute — one that cannot be called is not a boundary the
  middleware can run either.
- **Declaring the forged marker out of contract, or refusing it with a `ConfigurationError`.**
  Rejected: the first is more text than the fix and an exception to the no-unrelated-`500`
  doctrine [Decision 7][s65-d7] establishes; the second contradicts the contract in which every
  unforeseen state answers "no" and falls back to the view-local arrangement.
- **One broad `except Exception` around recognition and construction together.** Rejected: it
  would convert a package mount's own non-`TypeError` construction failure into a silent
  decline. The recognition **reads** are guarded broadly, because a read that raises is no
  answer at all; the construction keeps a narrow `except TypeError`, because a class that
  cannot be built from the kwargs it names is a determined answer.

**The probe's limit.** An attribute read on a class consults that class's own attribute
machinery — a metaclass `__getattr__` or a class-level descriptor under the probed name — so
recognition can still run consumer code, which is why every recognition read is guarded.
**Forging the package's private marker is outside the threat model** (the [spec-045][spec-045]
stance that no in-interpreter walk is a trust boundary against a party already executing code
in the process); the probe and the read guard exist so that every outcome the recognition
reaches is controlled, not to defend against a forger. Running a boundary the recognition has
*accepted* is deliberately unguarded: a boundary that raises anything but `HTTPException` leaves
`process_view` uncaught, identically for a package mount and a forged class, because a guard
there would sit across the body cap's own errors and across a package mount's genuinely broken
boundary.

### Decision 19 — A Django-backed WebSocket Host boundary, beside Channels' Origin check

Spec: [Decision 19][s65-d19].

**Why.** `channels.security.websocket.OriginValidator.__call__` reads the `Origin` header and
nothing else, so a handshake carrying an allowed `Origin` and a hostile `Host` connects through
Channels' validators. Django never sees the WebSocket handshake, so unlike HTTP there is no
other owner for the Host question.

**Alternatives rejected.**

- **Narrow every claim to Origin-only.** Rejected in the spec's *Why call Django rather
  than narrow the claim*: it converts a real gap into a documented gap, on a check that
  nothing else in the WebSocket stack owns.
- **Rely on the upstream class name as evidence.** Not an alternative so much as a
  mistake: `AllowedHostsOriginValidator` is a factory that configures `OriginValidator`, and
  the next reader should verify behavior rather than nomenclature.
- **Fix it inside Channels' validator, or subclass `OriginValidator` to also read `Host`.**
  Rejected: it would overload one class with two independent questions and make the package's
  Host policy a fork of somebody else's Origin policy — and a consumer reading
  `AllowedHostsOriginValidator` in their own `asgi.py` would be reading a name that lies twice
  instead of once. The `DEBUG` default is a second reason: when `settings.DEBUG` is true and
  `ALLOWED_HOSTS` is empty, `AllowedHostsOriginValidator` substitutes
  `["localhost", "127.0.0.1", "[::1]"]`, while Django's `HttpRequest.get_host()` substitutes
  `[".localhost", "127.0.0.1", "[::1]"]`, whose leading dot matches every `*.localhost`
  subdomain. Two boundaries both called "allowed hosts" already disagree, so the package's Host
  answer has to be a call into `get_host()`, never an expression of its own.
- **A package `ALLOWED_WEBSOCKET_HOSTS` setting.** Rejected: a second allowed-host list is a
  second thing to keep in sync with `ALLOWED_HOSTS`, and [`AGENTS.md`][agents] forbids adding
  a settings key that no feature needs. WebSocket follows the project's existing Django
  configuration.
- **Build a full `ASGIRequest` for the handshake scope.** Rejected: `ASGIRequest.__init__`
  expects an HTTP scope (path, method, query string, a body file) and does work the Host
  question does not need. The projection supplies the minimum `META` `get_host()` reads, which
  is a smaller and more auditable compatibility surface than a request object built out of a
  scope it was not written for.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md

<!-- docs/ -->
[glossary-configurationerror]: ../../GLOSSARY.md#configurationerror
[glossary-debug-toolbar-middleware]: ../../GLOSSARY.md#debug-toolbar-middleware
[glossary-joint-version-cut]: ../../GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: ../../GLOSSARY.md#live-first-coverage-mandate
[glossary-request_from_info]: ../../GLOSSARY.md#request_from_info

<!-- docs/SPECS/ -->
[s65-d1]: ../spec-046-transport_security-0_0_14.md#decision-1--spec-filename-and-canonical-naming
[s65-d10]: ../spec-046-transport_security-0_0_14.md#decision-10--a-utf-8-bom-is-rejected
[s65-d11]: ../spec-046-transport_security-0_0_14.md#decision-11--a-websocket-consumer-classfactory-injection-seam-with-a-revalidating-package-default
[s65-d12]: ../spec-046-transport_security-0_0_14.md#decision-12--maximum-connection-lifetime-is-documented-and-seamed-not-silently-enforced
[s65-d13]: ../spec-046-transport_security-0_0_14.md#decision-13--test-strategy-which-existing-tests-change-and-why
[s65-d14]: ../spec-046-transport_security-0_0_14.md#decision-14--this-card-amends-spec-041-and-supersedes-three-of-its-decisions
[s65-d15]: ../spec-046-transport_security-0_0_14.md#decision-15--the-version-bump-is-deferred-to-the-joint-cut
[s65-d16]: ../spec-046-transport_security-0_0_14.md#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam
[s65-d17]: ../spec-046-transport_security-0_0_14.md#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard
[s65-d18]: ../spec-046-transport_security-0_0_14.md#decision-18--the-body-gate-runs-before-djangos-multipart-parser
[s65-d19]: ../spec-046-transport_security-0_0_14.md#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check
[s65-d2]: ../spec-046-transport_security-0_0_14.md#decision-2--http-dispatches-directly-to-a-required-consumer-supplied-django-asgi-application
[s65-d3]: ../spec-046-transport_security-0_0_14.md#decision-3--django_application-is-required-omission-fails-at-construction-with-no-compatibility-fallback
[s65-d4]: ../spec-046-transport_security-0_0_14.md#decision-4--url_pattern-becomes-websocket_url_pattern-with-exact-matching-as-the-secure-default
[s65-d5]: ../spec-046-transport_security-0_0_14.md#decision-5--compatibility-policy-an-intentional-alpha-breaking-change-to-a-security-boundary
[s65-d6]: ../spec-046-transport_security-0_0_14.md#decision-6--the-graphql-http-endpoint-is-a-package-owned-django-view-in-the-consumers-urlconf
[s65-d7]: ../spec-046-transport_security-0_0_14.md#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared
[s65-d8]: ../spec-046-transport_security-0_0_14.md#decision-8--the-deployment-layer-cap-is-a-co-requirement-not-an-alternative
[s65-d9]: ../spec-046-transport_security-0_0_14.md#decision-9--the-strict-utf-8-wire-contract-is-enforced-by-the-package-view-its-own-body-source-one-strict-decode
[spec-040]: ../spec-040-auth_mutations-0_0_13.md
[spec-045]: ../spec-045-visibility_boundary-0_0_14.md
[spec-046]: ../spec-046-transport_security-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
