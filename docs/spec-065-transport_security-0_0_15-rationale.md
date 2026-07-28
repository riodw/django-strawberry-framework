# Rationale: spec-065 — Transport security (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-065-transport_security-0_0_15.md`][spec-065]. The spec is the
contract and states only what is currently true; everything that explains **how it got there**
lives here: the alternatives each decision rejected and why each lost, the derivations that do
not change how a decision is implemented, every change a decision has undergone with the review
round that caused it, and every claim a decision once made and may no longer make.

Created by the `docs/builder/BUILD.md` `## Spec rationale extraction` pass. The text below was
**moved** out of the spec, not copied: it exists here and nowhere else.

## How to read this file

- **One entry per spec decision**, with the decision's own heading and anchor, so a citation
  such as "Decision 11's rejected alternatives" resolves to exactly one place. An entry that
  named no decision could not be looked up and would be worthless however well argued.
- **Worker 3 reads this during review** — it is what stops a reviewer re-raising a settled
  alternative, and it is the reasoning the finished implementation is checked against.
  **Worker 1 owns it** as spec custodian and audits it at final verification. **Worker 2 never
  reads it**: that is the point of the move.
- **Append-only during the build.** A new review round's decisions land in the spec; their
  rejected alternatives, derivations and retractions append here in the same custodian pass.
- Round attribution: **Decisions 1-15** were authored from the `docs/feedback2.md` hardening
  audit (findings S1, S2, S9, S11, S12-transport). **Decisions 16-19** are review round 2's
  decided contracts. Round 1's findings were closed and committed before round 2 opened.
- Two things deliberately **stayed** in the spec even though they read like deliberation,
  because a builder who never reads them can rewrite a fail-open: the rejected
  rewind-to-zero direction and the "a probed count of zero is a measurement failure, never an
  empty body" reasoning, both inside [Decision 7][s65-d7]. Guard the answer, not one spelling
  of an incoherent input.

## Program provenance

The review-round framing the spec carried while round 2 was in flight, moved here because the
spec is a contract rather than a changelog:

**Review rounds are evidence, not contract.** Round 1's findings are closed and
committed. Round 2 (currently in [`docs/feedback.md`][feedback]) raised six items; four
became decisions of this spec's own —
[Decision 16][s65-d16]
(active-operation revocation),
[Decision 17][s65-d17]
(multipart control-field encoding),
[Decision 18][s65-d18]
(the body gate's ordering against CSRF), and
[Decision 19][s65-d19]
(the WebSocket Host boundary) — and two are straight fixes folded into the slices that own
the files (the stale Strawberry floor in `routers.py`'s broken-install hint, and the
unguarded stream-capability probe in `_request_body.py`). Where a round-2 decision
contradicts an earlier sentence of this spec, the earlier sentence has been rewritten in
place rather than left standing beside it: this document is the contract, and two
paragraphs of it must never disagree.

The two straight fixes named there are discharged by the slices that own the files, and the spec's
[`## Slice checklist`][s65-slice-checklist] carries both as normative bullets: the stale
Strawberry floor in `routers.py`'s broken-install hint (Slice 4) and the unguarded
stream-capability probe in `_request_body.py` (Slice 2).

## Decision entries

### Decision 1 — Spec filename and canonical naming

Spec: [Decision 1][s65-d1].

**Rejected alternative — the `channels_router` slug — and the naming derivation.**

The topic slug is `transport_security` rather than `channels_router` (the `spec-041`
slug) because the card's subject is the transport boundary as a whole — HTTP ownership,
body bounds, wire encoding, and socket actor freshness — not the router module alone.
Two of the four findings (S2's cap and S9's wire contract) land outside `routers.py`
entirely.

### Decision 2 — HTTP dispatches directly to a required, consumer-supplied Django ASGI application

Spec: [Decision 2][s65-d2]. Cited from
`django_strawberry_framework/routers.py` and from the spec's own
[`## Non-goals`][s65-non-goals] ("Reintroducing a Channels HTTP mode as an 'advanced
transport'" — the first alternative below is the one that declines it).

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

Spec: [Decision 3][s65-d3].

**Alternatives rejected.**

- **Keep it optional and warn.** Rejected: [`AGENTS.md`][agents] #"never propose
  ship-it-today-defer-the-real-fix sequencing" — and the audit's own closing line, "Do
  not split these into 'ship the warning now, fix the architecture later' work."
- **Derive it internally with a lazy `get_asgi_application()` call.** Rejected on the
  initialization-order ambiguity in the spec's *Why deriving it internally is wrong*; a
  framework must not make Django's setup point
  implicit.
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

Spec: [Decision 5][s65-d5].

**Derivation — why the alpha break is the right trade.**

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

**Change record — review round 2.** Round 2 added [Decision 19][s65-d19]'s WebSocket Host
boundary, which denies a handshake `0.0.14` accepted. This decision gained a paragraph placing
that behavior change deliberately *outside* the breaking-change list. That paragraph's first form
narrated the round rather than stating the position, and is recorded here:

One round-2 clarification belongs here rather than being discovered as a surprise: the
WebSocket composition gains an **outer** wrapper
([Decision 19][s65-d19]),
so a handshake whose `Host` is not in `ALLOWED_HOSTS` is now denied where `0.0.14` accepted
it. That is a behavior change and it is not in the breaking-change list above, deliberately:
it changes no signature, no import, no setting and no documented promise — it makes an
existing documented promise ("an injected consumer cannot escape Host validation") true for
the first time. A deployment whose `ALLOWED_HOSTS` is already correct for HTTP sees no
difference; a deployment that sees a difference was accepting handshakes addressed to a host
it never allowed.

The spec now makes the same compatibility statement directly, under "One behavior change that is
deliberately not in that list" — without the "One round-2 clarification belongs here rather than
being discovered as a surprise" opener, and without claiming the Host promise became true "for the
first time".

### Decision 6 — The GraphQL HTTP endpoint is a package-owned Django view in the consumer's URLconf

Spec: [Decision 6][s65-d6].

**Why a package view rather than pointing consumers at Strawberry's.** Four reasons, in
order of weight. (a) It is the only home for the S2 cap that works identically on WSGI
and ASGI, sync and async — Django's own view layer. (b) It gives the migration note one
canonical line instead of a fork between "use upstream's view" and "except when you want
the cap". (c) Under the [live-first coverage mandate][glossary-live-first-coverage-mandate]
every S2 regression row is then earnable over fakeshop's real `/graphql/` with
`django.test.Client`, rather than mocked at the package tier — decisive, because a body
limit asserted against a fake request proves nothing about the transport. (d) It is where
the later cards' transport-shaped bounds (S3's budget, S4's upload limits, S10's error
policy) will need to live, so the seam is created once rather than three times — and it is
where S9's wire contract lands for the same reason, since a package-owned policy needs a
package-owned boundary to live on.

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
  [Decision 8][s65-d8]
  assigns to the deployment layer, where it belongs and already exists.

### Decision 7 — The app-level body cap lives in the package Django view, counted not declared

Spec: [Decision 7][s65-d7]. Cited from the spec's
[`## Edge cases and constraints`][s65-edge-cases] for the two directions rejected by name below
(counting `request.body`; rewriting `META["CONTENT_LENGTH"]` so the declaration parses).

**Alternatives rejected.**

- **Trust `Content-Length` alone.** Rejected by the maintainer's direction and correct on
  the merits: the header is client-supplied and, on ASGI with chunked transfer, may be
  absent entirely.
- **Documented `DATA_UPLOAD_MAX_MEMORY_SIZE` reliance plus a thin wrapper.** Rejected on
  the shared-knob argument in the spec's *Why its own key rather than
  `DATA_UPLOAD_MAX_MEMORY_SIZE`*, plus: it would make the package's most security-visible
  bound something the package neither owns nor tests.
- **An ASGI/middleware guard as the primary seam.** Rejected in
  [Decision 6][s65-d6];
  its mid-stream advantage is reassigned to the deployment layer.
- **Counting `len(request.body)`.** Its appeal is real — the property is the only *public*
  way to obtain a body, so counting it touches no private attribute. Rejected anyway,
  because it obtains the correct length only after Django has materialized the whole
  request, which makes it a detector rather than a bound; and at the 5.2.0 floor, against an
  absent or understated `Content-Length`, there is no earlier Django check to have shrunk
  that allocation. Measuring the stream Django keeps private, from one module pinned to both
  supported versions, is the smaller compatibility surface of the two — the alternative
  buys its purity with an unbounded allocation on the one path this card exists to bound.
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

**Change record — review round 2: the probe's third outcome.** The shipped capability probe
modelled **two** outcomes — measurable, and safely unmeasurable so the bounded read supplies the
bound — and left `seekable()`, both `seek()`s and the subtraction unguarded, so a stream supplied
by consumer middleware or a custom ASGI server could take a capability failure out of the seam as
an unrelated `500`. Round 2 added the third outcome: a **restoring** seek that fails leaves the
read position unknown, and the package fails closed with its own controlled rejection. The
spec's first statement of that outcome recorded the change instead of the contract:

> Two outcomes were already modelled (measurable, and safely unmeasurable so the bounded read
> supplies the bound); the third was not, and letting it fall through as an unrelated `500` is
> the wrong answer at the one seam this design deliberately centralized.

The bolded phrase **"An unmeasurable stream has three outcomes, not two"** is load-bearing text
in the spec, not a heading of convenience: four other sites cite it as a `#"substring"`
reference. It must survive verbatim.

### Decision 8 — The deployment-layer cap is a co-requirement, not an alternative

Spec: [Decision 8][s65-d8].

**Alternative rejected.** Treating the application cap as sufficient and mentioning the
proxy in passing. Rejected: it would restate the exact conflation the audit called out,
and would make the package's own documentation the source of a false guarantee.

### Decision 9 — The strict UTF-8 wire contract is enforced by the package view: its own body source, one strict decode

Spec: [Decision 9][s65-d9].

**Derivation — why the decode belongs on the view rather than in the patch module.** The
operative half of this argument (a permanent policy must not ride a temporary patch's kill
switch, and the body source is on the path to the decode) stays in the spec under "Ownership
follows lifecycle, so the gate does not carry the policy"; the three-reason derivation is here.

**Why the decode belongs on the view rather than in the patch module.** Three reasons, and
the first is decisive. (a) A permanent security policy must not share a temporary patch's
lifecycle: an upstream shape change that forces a consumer to disable the patch would
otherwise reopen the parser differential S9 exists to close, silently. That argument
governs the body source identically, which is why the view owns that too — a switchable
body source is a switchable decode. (b) The mixin is one
seam covering both transports — `super()` delegates to upstream's `parse_json`, patched or
not, so nothing is reimplemented and the two views cannot diverge, which is the same
single-siting rule [`request_from_info`][glossary-request_from_info] establishes for
request decoding. (c) It is the same boundary as the body cap: the cap decides which bytes
reach the parse, and the parse decides how those exact bytes become text — one mixin, one
subject, the raw request body.

**Alternatives rejected.**

- **Decode inside `_patched_parse_json`.** The wire contract *is* a property of
  GraphQL-over-HTTP request parsing, and the patch module already owned that parse for both
  transports and both encodings-of-failure, so putting the decode there costs the fewest
  lines and covers upstream-mounted consumers too. Rejected on ownership: it makes a
  permanent package security policy share the lifecycle — and the `APPLY_UPSTREAM_PATCHES`
  kill switch — of temporary workarounds for upstream bugs. A consumer disabling those
  workarounds, or a maintainer deleting them once upstream fixes them, then silently
  restores multi-encoding request bodies. A security policy a consumer can switch off by
  accident is not a policy, and the extra reach over upstream-mounted views is not the
  package's to claim.
- **Decode inside `_patched_body`.** Rejected: it re-creates the unhandled-`500`
  path the patch module exists to close, and it would only fix the sync transport.
- **Let `_patched_body` be the package view's sync body source.** One patched property
  already hands raw bytes to both mounts, so the package view would need no adapter of its
  own and the decode would be reached for free. Rejected for the *same* reason the decode
  is not in the patch module, not a second one: the patch is gated, so the sync half of the
  wire contract would ride `APPLY_UPSTREAM_PATCHES` while the other half did not, and a
  policy that is half-switchable is worse than one that is honestly switchable, because the
  reader of either half is told something untrue. Measured rather than argued: with the
  gate off, a BOM'd UTF-16 or UTF-32 body on a mounted sync package view answers `500`
  instead of the contracted `400`, because upstream's property decodes first and
  `parse_json` is never entered with bytes. A decode the bytes never reach is not an
  enforcement.
- **Override `decode_json` instead of `parse_json`.** Rejected: a `UnicodeDecodeError`
  raised there lands in upstream's `except json.JSONDecodeError`, which does not catch it,
  so the `400` translation would depend on the Strawberry patch being installed — exactly
  the coupling this decision removes.
- **Reject non-UTF-8 by sniffing leading bytes** (a BOM / NUL-pattern check). Rejected: a
  bespoke encoding sniffer is a parser, and adding a second parser to close a parser
  differential is self-defeating. `bytes.decode("utf-8")` is the contract.
- **Set a strict codec on the adapter and let `json.loads` see a `str` everywhere.**
  Rejected — and worth distinguishing from the adapter subclass the view does install,
  which *removes* a decode rather than adding one. Putting the strict codec on the adapter
  instead re-introduces the property-scope raise, on the very transport the subclass exists
  to rescue: a `UnicodeDecodeError` with no `except` above it is a `500`, wherever the
  codec is strict. It also needs a matching change to the async adapter's contract to keep
  the two transports agreeing, losing the sync/async symmetry one inherited `parse_json`
  gives for free.
- **A `STRICT_UTF8_BODY` setting so a consumer can opt out of the policy too.** Rejected:
  a security policy a consumer can switch off is the finding this decision answers, not the
  fix — and [`AGENTS.md`][agents] forbids adding a settings key speculatively. The opt-out
  that does exist is deliberate and explicit: mount upstream's own view.

**Change record — review round 2: scope narrowed to the `application/json` body.** Round 2
established that Django decodes multipart field data with `force_str(..., errors="replace")`
before the package sees `operations` / `map`, so a strict decode is unavailable at that seam and
the control documents needed their own boundary — [Decision 17][s65-d17]. This decision's scope
paragraph was narrowed to the one document the package receives as *bytes*, and the sentence
that recorded the narrowing did so in the past tense ("this decision alone **was true only of**
the ordinary JSON body"); the spec now states the scope directly ("this decision alone
**governs** the ordinary JSON body").

### Decision 10 — A UTF-8 BOM is rejected

Spec: [Decision 10][s65-d10]. Cited from
`examples/fakeshop/test_query/test_products_api.py`, whose BOM rows say "Decision 10 chose
rejection over stripping" — the alternative below is what was not chosen.

**Alternative rejected.** Accept-and-strip via `utf-8-sig` or an explicit
`lstrip("﻿")`. It is friendlier to one misconfigured client and is what several JSON
parsers do — but it reintroduces the parser differential S9 exists to close,
adds a lenient pre-processing
step the contract must then document and test, and buys tolerance for a payload no
correct GraphQL client emits. Documented here as the considered-and-rejected direction so
a future reader knows the choice was deliberate rather than incidental.

### Decision 11 — A WebSocket consumer-class/factory injection seam, with a revalidating package default

Spec: [Decision 11][s65-d11]. Cited from
`django_strawberry_framework/consumers.py` as "Decision 11's rejected alternatives" for the
`get_context` / `receive()` seam choice — the `receive()` alternative below, together with the
spec's own "Where the revalidation hooks in, and why not `get_context`" paragraph, which stayed
there because it is implementation instruction.

**Why this and not the alternatives.**

- **Revalidate lazily in `ChannelsRequestAdapter.user`.** Rejected: it only fires when
  the package happens to read the actor, so an operation touching no permission gate
  would execute with no revalidation at all — failing the "reload the actor **before
  execution**" requirement — and it can only affect a read, never reject an operation.
- **Revalidate in the consumer's `receive()`.** Rejected: `receive` sees every *inbound*
  frame, including keep-alive pongs, `complete` messages, and `connection_init`, so it would
  fire a session read per frame regardless of whether anything was being authorized — the
  window would be pricing the wrong events. (The rationale originally continued "and at that
  layer the only available rejection is closing the socket, not failing one operation";
  [Decision 16][s65-d16]
  has since made closing the socket the *correct* rejection, so that half no longer counts
  against the alternative and is recorded here only so the reasoning is not read as
  unchanged. Inbound-frame cost is the surviving reason, and it is sufficient: it is also why
  the second checkpoint gates **outbound** frames, where the set of gated types is exactly
  the set that carries information.)
- **Ship a periodic background refresh task.** Rejected: it makes freshness a function of
  wall-clock luck rather than of the operation being authorized, and it adds a task
  lifecycle to a transport helper.
- **Implement the message loop ourselves to own the seam.** Rejected explicitly by the
  maintainer's direction and on the merits: a second GraphQL protocol engine is a
  permanent maintenance surface. Two `super()`-delegating pre-hooks are not an engine.
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
  about signed-cookie sessions already lives, so the expression looks at home there.
  Rejected: importing a submodule executes its package's `__init__`, and `auth` is
  structurally opt-in with an eager `__init__`, so a transport-layer read would drag the
  whole GraphQL auth subsystem into every process that never asked for it. Making
  `auth/__init__` lazy instead was also rejected — it changes the public opt-in surface
  [`spec-040`][spec-040] Decision 3 pins, to solve a transport problem — and duplicating the
  two-line `SESSION_ENGINE` expression was rejected outright: two sites would have to agree
  about how a consumer-authored engine subclass resolves.

The `receive()` bullet carries a retraction of its own, in its parenthetical: one of its two
original reasons ("at that layer the only available rejection is closing the socket") stopped
counting against the alternative once [Decision 16][s65-d16] made closing the socket the correct
rejection. Inbound-frame cost is the surviving reason, and it is sufficient.

**Claim this decision may no longer make (1) — "Host/Origin validation" as one wrapper.** It
described the router's wrappers as delivering "Host/Origin validation" as though one wrapper
delivered both. `channels.security.websocket.OriginValidator.__call__` reads the `Origin` header
and nothing else, so the Host half was never being performed; [Decision 19][s65-d19] exists
because of it. The removed sentence:

> Three wrappers, three named checks: this decision originally said "Host/Origin validation" as
> though one wrapper delivered both, and Decision 19 exists because the second half of that pair
> was never being performed.

The spec now names three wrappers and three checks, and attributes the Host half to Decision 19's
own boundary rather than to Channels' Origin validator.

**Claim this decision may no longer make (2) — admission as the whole boundary.** As originally
written it claimed the admission checkpoint was the whole of the S11 boundary. An admitted
subscription iterates its result source inside one task and never returns through
`handle_subscribe`, so an admission hook cannot stop an already-running operation from emitting
results after its actor is revoked. The removed framing:

> Admission is only **half** the boundary, and this decision as originally written claimed the
> whole of it. […] and it is what makes the S11 claim true rather than nearly true.

The spec now states the halves without the chronology: admission is half the boundary, the
outbound-frame gate is [Decision 16][s65-d16], and together they make the S11 contract whole.

### Decision 12 — Maximum connection lifetime is documented and seamed, not silently enforced

Spec: [Decision 12][s65-d12].

**Alternatives rejected.**

- **A `max_connection_lifetime=` kwarg with a default.** Rejected: either the default is
  long enough to be security-irrelevant, or it is short enough to break subscriptions. A
  consumer who wants it can enforce it in the injected class today.
- **A package-owned lifetime timer added as part of the round-2 revocation fix.** Rejected
  for the same reason as the kwarg, and for one more: it would answer a resource question
  with machinery justified by an authorization argument, which is how a transport helper
  grows a task lifecycle nobody asked for. The revocation fix is
  [Decision 16][s65-d16]'s
  two checkpoints and nothing else — no polling, no background task, no second setting, no
  maximum-lifetime timer.

**Claim this decision may no longer make.** It read:

> with revalidation on, lifetime stops being the security-relevant bound

which conflated the authorization bound with the resource bound. The retraction paragraph the spec
carried while that was being corrected, moved here in full:

**What this decision is not allowed to claim any more.** It previously read "with
revalidation on, lifetime stops being the security-relevant bound", which conflated the two
bounds. Correctly stated: lifetime stops being the bound on *what a revoked actor can do* —
a revoked connection cannot admit an operation or emit an information-bearing operation
frame, and dies at the attempt — but it remains the bound on *how long the socket, its
subscription task, its session object, and its stale actor reference occupy the server*. That
residue is DoS-relevant and is named as such
([Decision 16][s65-d16]
#"The idle-socket consequence"); it is not an authorization hole, because the idle socket has
no authorization capability while idle.

The spec now makes that same statement directly, under "Which bound lifetime is, and which it is
not", with no record of the claim it replaces.

### Decision 13 — Test strategy: which existing tests change, and why

Spec: [Decision 13][s65-d13]. The spec keeps the whole test strategy — which tests are rewritten,
preserved, re-aimed, inverted and deleted, and where each row lives. What moved here is the
chronology: which contract each round-2-amended row asserted *before* the round, and why the
change was deliberate rather than convenient.

**Change record — review round 2: prior test contracts and what replaced them.** The block as the
spec carried it, verbatim:

**Amended by review round 2 (they encode a contract the round-2 decisions replace).** Same
discipline as above: named explicitly so a reviewer can tell a deliberate inversion from a
regression.

- `tests/test_routers.py`'s revocation rows asserted an operation-scoped `error` frame on a
  revoked session with the socket left open. They now assert a **connection close** (`4403`
  / `"Forbidden"`) with no preceding operation error, at both checkpoints and on both
  protocols
  ([Decision 16][s65-d16]).
  The revocation subject is preserved; the wire shape of the denial is what changes, and it
  changes because the previous shape was unreachable through the new gate rather than because
  a test was inconvenient.
- `tests/test_routers.py`'s `Subscription.tick` yielded exactly once, which is precisely why
  the suite could not detect the active-operation gap: every revocation row let operation 1
  finish before revoking. A controlled **multi-yield** subscription is added beside it, and
  the single-yield fixture stays for the admission rows it was written for.
- `tests/test_routers.py`'s `_STRAWBERRY_FLOOR_SUBSTRING = "strawberry-graphql>=0.262.0"`
  deliberately pinned `routers.py::_STRAWBERRY_CHANNELS_BROKEN_HINT`'s stale floor. Both move
  to `0.316.0` — the value the hard dependency and the minimum CI matrix node already agree
  on — in one change, because a user-facing recovery hint that recommends a version the
  package metadata rejects is a defect in the hint, not in the test that pinned it.
- `examples/fakeshop/test_query/test_transport_api.py`'s multipart rows proved the declared
  cap through a plain `Client()`, whose CSRF checks are off — so they could not have observed
  the ordering defect. The cap rows gain a `Client(enforce_csrf_checks=True)` sibling with a
  parser / upload-handler sentinel
  ([Decision 18][s65-d18]),
  and the file gains the multipart control-field encoding matrix
  ([Decision 17][s65-d17]).
  Status `413` alone was never evidence of ordering, and the rows say so now.
- `tests/test_routers.py::test_websocket_branch_wraps_origin_validator_outside_the_auth_stack`
  asserts the wrapper nesting, and the nesting gains an outer layer
  ([Decision 19][s65-d19]).
  Its subject and its two existing assertions (the origin validator sits outside the auth
  stack; the `"http"` value is not an `OriginValidator`) are preserved verbatim; one assertion
  is **added** for the new outermost wrapper. Nothing is weakened, and this is the third time
  this test has had to track a default or a composition — which is exactly why the card names
  it each time rather than letting the diff speak.
- `tests/test_views.py`'s stream-shape rows gain the third probe outcome — a stand-in whose
  restoring `seek` fails — which is the one shape that must produce the package's controlled
  rejection rather than a `500`
  ([Decision 7][s65-d7]
  #"An unmeasurable stream has three outcomes, not two").

**Change record — placement.** The placement rule did not change; the paragraph that applied it
to the round's new rows opened by naming the round, and named the criticism that produced two of
them. Its original form:

The round-2 rows follow the same rule and land where the rule sends them, not where they are
convenient. The multipart control-field matrix and the CSRF-ordering row are **live** — they
are request-shaped, and a direct `parse_json(str)` call or a mocked request proves nothing
about either boundary, which is precisely the criticism that produced them
([Decisions 17][s65-d17]
and [18][s65-d18]).

One further reconciliation inside this decision: the "Preserved in subject and assertion
strength" item for
`::test_websocket_branch_wraps_origin_validator_outside_the_auth_stack` said its nesting
assertion and its "the HTTP value is not an `OriginValidator`" assertion "are unchanged", while
the round-2 block said the nesting gains an outer layer. Read in isolation the first was
misleading. The spec now says both assertions are **preserved verbatim, beside the one assertion
added for the outermost wrapper**, and the round-2 bullet no longer restates the pattern literal
the earlier item already owns. The meta-commentary that closed that bullet — "this is the third
time this test has had to track a default or a composition — which is exactly why the card names
it each time rather than letting the diff speak" — is history and lives only here.

### Decision 14 — This card amends `spec-041` and supersedes three of its decisions

Spec: [Decision 14][s65-d14].

**Alternative rejected.** Leaving `spec-041` untouched and relying on this spec to
supersede it implicitly. Rejected: implicit supersession between two specs at different
paths is exactly how a reader ends up following the wrong one.

**Change record — review round 2.** Round 2 added the `spec-041` floor reconciliation (its
`strawberry-graphql>=0.262.0` prose against the live `>=0.316.0` requirement) as a **correction of
the record**, deliberately not a fourth supersession. The obligation stays in the spec; only its
"added by review round 2" label moved here.

### Decision 15 — The `0.0.15` version bump is deferred to the joint cut

Spec: [Decision 15][s65-d15].

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

### Decision 16 — Revocation is connection-scoped and gated at the WebSocket adapter's outbound frame seam

Spec: [Decision 16][s65-d16]. **A review round 2 decision** (round 2's Blocker 1): the shipped
admission-only revalidation could not stop an already-running subscription from emitting results
after its actor was revoked.

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
  [Decision 11][s65-d11]
  already rejected for the same reason.
- **Per-operation cancellation without closing the socket.** Rejected: more machinery for a
  smaller guarantee. The actor is a property of the *connection*, so cancelling one operation
  leaves a socket whose remaining operations are authorized by an actor that no longer exists,
  and the package would then owe a per-operation revocation ledger to keep them straight.
- **Admission-only, with the S11 claim weakened to match.** Rejected: the stronger contract
  is achievable at this seam, with one derived class and one lock, so weakening the claim
  would be choosing a documented gap over a fix. [`AGENTS.md`][agents] #"always recommend the
  root-cause fix over the surface patch" settles it, and the review is right that maximum
  connection lifetime would otherwise become security-relevant again.
- **A package maximum-connection-lifetime timer as the answer to active-operation
  revocation.** Rejected in
  [Decision 12][s65-d12]:
  it answers an authorization question with a resource bound, and a bound that arrives
  minutes late is not a boundary.
- **A bespoke package close code** (e.g. `4499`) instead of upstream's `4403`. Rejected: a
  code unique to "your session was revoked" is a disclosure the reason string deliberately
  avoids, and reusing upstream's own `Forbidden` close keeps every refusal to authorize this
  connection indistinguishable on the wire — the same argument that makes the nine
  encoding-rejection shapes share one `400`
  ([Decision 9][s65-d9]).

**Claims this decision replaced.** `consumers.py`'s "a revoked session stops executing" and
`GraphQLWebSocketConsumer`'s "a revoked session stops executing without the socket having to end"
were false in both halves for an already-running subscription, and the second is false in the
opposite direction as well, because on this contract the socket *does* end. The tail of the
paragraph's first form, which narrated the replacement (the claim itself stayed in the spec and is
elided here):

[…] The claim this replaces — `consumers.py`'s "a
revoked session stops executing", and `GraphQLWebSocketConsumer`'s "a revoked session stops
executing without the socket having to end" — was false in both halves for an already-running
subscription, and the second half is now false in the opposite direction as well, since the
socket *does* end. Correcting those two docstrings belongs to the change that implements this
decision, not to Slice 5's prose sweep: they are load-bearing security claims in the file
being rewritten.

The spec now carries the exact words the docs and docstrings must use, states that they replace
that wording, and does not analyse why the old wording was false.

Two consequences are deletions rather than edits, and the spec states both as obligations: the
per-operation revoked-session `error` message with its per-protocol payload split, and the
`graphql.GraphQLError` import that formatted them, become unreachable under this decision and
leave the package in the change that implements it.

### Decision 17 — Multipart control fields stay Django-parsed, behind a strict loss-detection guard

Spec: [Decision 17][s65-d17]. **A review round 2 decision** (round 2's M1): a multipart
`operations` field declared `charset=iso-8859-1` and carrying a raw Latin-1 byte executed with
`200`, and so did one with no charset and a malformed UTF-8 byte — Django replacement-decodes
both before the package sees them.

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
  which is the parser differential
  [Decision 9][s65-d9]
  exists to close. The scope narrowing that *did* land is Decision 9's, and it is a statement
  about which decision owns which document — not a concession on the endpoint's behavior.

**Escalation path, recorded so a future reader does not re-litigate it.** If distinguishing a
genuine literal `U+FFFD` from a replacement-generated one ever becomes mandatory, the root
fix is **upstream**: a public Django hook for strict, non-file multipart-field decoding. Until
one exists at the package's supported floor, the package must not own or copy Django's parser
to get it.

### Decision 18 — The body gate runs before Django's multipart parser, via view-local CSRF re-entry

Spec: [Decision 18][s65-d18]. **A review round 2 decision** (round 2's M1 sibling on ordering).

**Alternatives rejected.**

- **A narrow package middleware placed before `CsrfViewMiddleware`, plus a system check that
  detects missing or wrong ordering** (the review's own first suggestion). Rejected: it adds
  a **required deployment entry** — a `MIDDLEWARE` line every consumer must add in the right
  position, policed by a check that exists only because the requirement exists — which cuts
  directly against this card's thesis that Django owns the HTTP stack and against
  [Decision 6][s65-d6]'s
  rejection of a `MIDDLEWARE`-shaped cap. It would also apply the GraphQL cap project-wide
  unless the middleware carried a path predicate, reintroducing the mount-matching problem the
  view seam removed.
- **Narrowing the claim without reordering** — "the view cap prevents Strawberry parsing and
  schema execution; proxy and Django upload settings own multipart resource consumption."
  Rejected: the reorder is achievable with two public Django decorators and no deployment
  surface at all, so narrowing would be choosing a documented gap over a fix that costs less
  than the documentation would.
- **Reimplementing the token check inside the view** to avoid the double middleware pass.
  Rejected on sight: the package would own CSRF validation, cookie rotation, `Vary`, and
  `CSRF_FAILURE_VIEW` — a partial re-implementation of a security middleware that must track
  Django's security releases forever, which is the same mistake S1 exists to undo.

**Claim this decision falsified.** The declared multipart ceiling was documented as running
before Django's `MultiPartParser`, and as shipped it did not:
`CsrfViewMiddleware._check_token` reads `request.POST` from `process_view`, before the view's
`run` reaches the body gate, and that single access invokes the parser and the upload handlers.
The live row that was supposed to prove the ordering used a plain `Client()`, whose CSRF checks
are disabled, so the middleware exited before `_check_token` and the row proved only the
view-local branch — status `413` alone was never evidence of ordering. The spec's own record of
that, before it was rewritten to state the mechanism rather than the history:

**Why the declared gate needed this at all.** `CsrfViewMiddleware._check_token` reads
`request.POST.get("csrfmiddlewaretoken", "")` for every cookie-bearing POST — even one that
will ultimately authenticate through the `X-CSRFToken` header — and `_check_token` runs from
`process_view`, before the view's `run` reaches
`_enforce_request_body_limit`. On a multipart request that single access invokes Django's
multipart parser and the upload handlers. So the declared gate, as shipped before this
decision, ran **after** the parser it claimed to precede
([Decision 7][s65-d7]
step 3). The live test that was supposed to prove the ordering used a plain `Client()`, whose
CSRF checks are disabled, so the middleware exited before `_check_token` and the row proved
only the view-local branch — status `413` alone was never evidence of ordering
([Decision 13][s65-d13]).

### Decision 19 — A Django-backed WebSocket Host boundary, beside Channels' Origin check

Spec: [Decision 19][s65-d19]. **A review round 2 decision** (round 2's M4).

**Alternatives rejected.**

- **Narrow every claim to Origin-only.** Rejected in the spec's *Why call Django rather
  than narrow the claim*: it converts a real gap into a
  documented gap, on a check that nothing else in the WebSocket stack owns.
- **Rely on the upstream class name as evidence.** Not an alternative so much as the mistake
  that produced the finding; recorded here so the next reader verifies behavior rather than
  nomenclature.
- **Fix it inside Channels' validator, or subclass `OriginValidator` to also read `Host`.**
  Rejected: it would overload one class with two independent questions and make the package's
  Host policy a fork of somebody else's Origin policy — and a consumer reading
  `AllowedHostsOriginValidator` in their own `asgi.py` would be reading a name that lies twice
  instead of once.
- **A package `ALLOWED_WEBSOCKET_HOSTS` setting.** Rejected: a second allowed-host list is a
  second thing to keep in sync with `ALLOWED_HOSTS`, and [`AGENTS.md`][agents] forbids adding
  a settings key that no feature needs. The whole point is that WebSocket now follows the
  project's existing Django configuration.
- **Build a full `ASGIRequest` for the handshake scope.** Rejected: `ASGIRequest.__init__`
  expects an HTTP scope (path, method, query string, a body file) and does work the Host
  question does not need. The projection supplies the minimum `META` `get_host()` reads, which
  is a smaller and more auditable compatibility surface than a request object built out of a
  scope it was not written for.

**Claim this decision falsified.** `routers.py` and this spec both claimed an injected consumer
"cannot escape Host/Origin validation". `channels.security.websocket.OriginValidator.__call__`
reads the `Origin` header and nothing else, and `AllowedHostsOriginValidator` is only a factory
for `OriginValidator(settings.ALLOWED_HOSTS)` — the class name was not evidence of behavior, and
a handshake carrying an allowed `Origin` and a hostile `Host` connected successfully. The spec's
own record of the falsified claim, before it was rewritten to argue the mechanism forward rather
than backward:

**Why this and not narrowing the claim.** The claim in `routers.py` and in this spec was that
an injected consumer "cannot escape Host/Origin validation".
`channels.security.websocket.OriginValidator.__call__` reads the `Origin` header and nothing
else, and `AllowedHostsOriginValidator` is only a factory for
`OriginValidator(settings.ALLOWED_HOSTS)` — the name is not evidence of behavior. Narrowing
every claim to Origin-only was the least surprising correction and is rejected, because it
leaves the handshake **accepting a hostile `Host`** with nothing else in the stack to catch
it: Django never sees the WebSocket handshake at all, so unlike HTTP there is no other owner
for the question. A boundary the package documents as absent is still absent.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md

<!-- docs/ -->
[feedback]: feedback.md
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-debug-toolbar-middleware]: GLOSSARY.md#debug-toolbar-middleware
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: GLOSSARY.md#live-first-coverage-mandate
[glossary-request_from_info]: GLOSSARY.md#request_from_info
[s65-d10]: spec-065-transport_security-0_0_15.md#decision-10--a-utf-8-bom-is-rejected
[s65-d11]: spec-065-transport_security-0_0_15.md#decision-11--a-websocket-consumer-classfactory-injection-seam-with-a-revalidating-package-default
[s65-d12]: spec-065-transport_security-0_0_15.md#decision-12--maximum-connection-lifetime-is-documented-and-seamed-not-silently-enforced
[s65-d13]: spec-065-transport_security-0_0_15.md#decision-13--test-strategy-which-existing-tests-change-and-why
[s65-d14]: spec-065-transport_security-0_0_15.md#decision-14--this-card-amends-spec-041-and-supersedes-three-of-its-decisions
[s65-d15]: spec-065-transport_security-0_0_15.md#decision-15--the-0015-version-bump-is-deferred-to-the-joint-cut
[s65-d16]: spec-065-transport_security-0_0_15.md#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam
[s65-d17]: spec-065-transport_security-0_0_15.md#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard
[s65-d18]: spec-065-transport_security-0_0_15.md#decision-18--the-body-gate-runs-before-djangos-multipart-parser-via-view-local-csrf-re-entry
[s65-d19]: spec-065-transport_security-0_0_15.md#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check
[s65-d1]: spec-065-transport_security-0_0_15.md#decision-1--spec-filename-and-canonical-naming
[s65-d2]: spec-065-transport_security-0_0_15.md#decision-2--http-dispatches-directly-to-a-required-consumer-supplied-django-asgi-application
[s65-d3]: spec-065-transport_security-0_0_15.md#decision-3--django_application-is-required-omission-fails-at-construction-with-no-compatibility-fallback
[s65-d4]: spec-065-transport_security-0_0_15.md#decision-4--url_pattern-becomes-websocket_url_pattern-with-exact-matching-as-the-secure-default
[s65-d5]: spec-065-transport_security-0_0_15.md#decision-5--compatibility-policy-an-intentional-alpha-breaking-change-to-a-security-boundary
[s65-d6]: spec-065-transport_security-0_0_15.md#decision-6--the-graphql-http-endpoint-is-a-package-owned-django-view-in-the-consumers-urlconf
[s65-d7]: spec-065-transport_security-0_0_15.md#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared
[s65-d8]: spec-065-transport_security-0_0_15.md#decision-8--the-deployment-layer-cap-is-a-co-requirement-not-an-alternative
[s65-d9]: spec-065-transport_security-0_0_15.md#decision-9--the-strict-utf-8-wire-contract-is-enforced-by-the-package-view-its-own-body-source-one-strict-decode
[s65-edge-cases]: spec-065-transport_security-0_0_15.md#edge-cases-and-constraints
[s65-non-goals]: spec-065-transport_security-0_0_15.md#non-goals
[s65-slice-checklist]: spec-065-transport_security-0_0_15.md#slice-checklist
[spec-065]: spec-065-transport_security-0_0_15.md

<!-- docs/SPECS/ -->
[spec-040]: SPECS/spec-040-auth_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
