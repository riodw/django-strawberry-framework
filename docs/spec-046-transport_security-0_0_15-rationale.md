# Rationale: spec-046 — Transport security (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-046-transport_security-0_0_15.md`][spec-046]. The spec is the
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
- Three further `why not …` blocks were audited and **stay** in the spec under the same
  carve-out, so a later pass does not re-open them: "why not `len(request.body)`"
  ([Decision 7][s65-d7]) is the canonical statement of the probe order and the
  zero-is-a-measurement-failure rule; "why not `get_context`"
  ([Decision 11][s65-d11]) names the per-operation seams and the single-siting requirement;
  and "why not in `routers.py`" ([Decision 19][s65-d19]) decides which module the Host
  validator lives in, plus the `build_tree_md.py` consequence of the docstring it widens.
  A fourth, Decision 12's "why not enforce it", was pure deliberation and did move — see that
  entry.

## Program provenance

The review-round framing the spec carried while round 2 was in flight, moved here because the
spec is a contract rather than a changelog:

**Review rounds are evidence, not contract.** Round 1's findings are closed and
committed. Round 2 of the maintainer's transport review raised six items; four
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

### Change record for the spec's non-decision sections

Four corrections outside any numbered decision, kept here because they have no decision entry
to belong to:

- **The header `Status:` line and the card id.** The status line said Slices 1-4 were built and
  "Slice 5 remains"; all five are built now, so it states that, plus the fact a reader would
  otherwise infer wrongly — the version quintet still reads `0.0.14` on disk because the
  `0.0.15` release is the joint cut's ([Decision 15][s65-d15]). The opener's card id moved
  `WIP-ALPHA-046-0.0.15` -> `DONE-046-0.0.15` with the card flip. `Planned for 0.0.15` stays: the
  target release is still a target.
- **`## Doc updates`, the `docs/TREE.md` bullet.** It read as an exhaustive list of the rows the
  regenerate publishes and was three rows short of the render's actual output
  (`examples/fakeshop/test_query/test_transport_api.py`, `tests/test_prove_failability.py`, and
  corrected `routers.py` / `tests/test_routers.py` rows). Corrected, and the bullet now says the
  render is source-driven so the list is what it publishes rather than a ceiling on it — an
  enumeration of a generated artifact goes stale by construction, and saying so is what stops the
  next reader treating a missing name as a missing row.
- **`## Slice checklist`, the Slice-5 sub-bullet on the `test_transport_api.py` docstring.** Its
  premise ("still scopes the file to `(spec-046 Slices 1-2)`") was true when it was written and
  was falsified by Slice 3's own docstring edit, so the closing slice read a contract describing a
  state two slices earlier. The instruction was correct and is kept; only the premise is gone, now
  phrased as the standing requirement (name the file's actual slice scope, before the
  `docs/TREE.md` regenerate that publishes it). **Rejected alternative:** leaving it, on the
  precedent that a closed slice's checklist is the record of what was built against. Rejected
  because that precedent turns on the sentence being *incomplete*, not *false*: a reader cannot
  tell a false premise from a real regression, and the artifact that carries the sub-bullet
  verbatim is still the record of what was dispatched.
- **[`## Borrowing posture`][s65-borrowing-posture], the upstream views' import list.** It said
  the two subclassed Strawberry views' "imports are `django`, `cross_web`, and `strawberry`
  only, verified in the installed 0.316.0". `strawberry/django/views.py` also imports the
  standard library (`json`, `typing`) and, at module level,
  `from asgiref.sync import markcoroutinefunction`. The list now matches the one `views.py`'s
  own module docstring already stated correctly — the standard library, `asgiref`, `cross_web`,
  `django`, `strawberry.http`, and the sibling `strawberry.django.context` — which is another
  instance of the shipped code documenting the fact more accurately than the spec it was written
  from. **The conclusion is unaffected and is kept:** no optional-import guard applies, because
  `asgiref` is Django's own hard dependency and every other name is already a hard dependency of
  this package, so the `channels`-free property the bullet exists to establish still holds.
  **Direction of the drift:** an omission rather than an error, but the omitted name is the one a
  reader would have to check against `pyproject.toml` before trusting the bullet at all.

### Change record for `## Helper-reuse obligations (DRY)`

Spec: [`## Helper-reuse obligations (DRY)`][s65-dry]. Three corrections found by verifying each
obligation against the shipped code rather than reading it as an assertion — the cross-slice
integration pass's own duty, and the section had never been re-verified after the two review
rounds moved what shipped.

- **"Two overridden hooks" was four, and two of them are not on the mixin.** The obligation said
  `run` and `parse_json` were the overrides and that **both** sat on `_RequestBodyBoundaryMixin`.
  The shipped view overrides four upstream hooks — `as_view` and `parse_json` on the mixin,
  `run` and `parse_multipart` on each concrete view — and substitutes `request_adapter_class`
  besides. The `run` pair was per-view from Slice 2 onward (upstream splits `dispatch` by
  colour, and `csrf_protect` decides whether to await by inspecting the callable it wraps);
  `as_view` arrived with [Decision 18][s65-d18] and `parse_multipart` with
  [Decision 17][s65-d17], and neither round revisited this section. The obligation now states
  the property that is actually load-bearing and actually true — **every decision body is
  single-sited on the mixin, and each per-view override is a thin delegate onto it** — because
  the placement of an override is upstream's choice while the single-siting of the policy is
  the package's. **Rejected alternative:** naming only the two mixin-hosted hooks and dropping
  the other two, which would have made the sentence true by narrowing it and left a reader
  unable to find the cap's own override at all. **Direction of the drift:** the sentence
  *understated* what the view overrides, so nothing was mis-built from it — but this section is
  the only place the package states its own reuse contract, and a builder checking a fifth
  override against it would have read "two" as a ceiling.
- **The sibling bullet already contradicted it.** The multipart obligation says both
  `parse_multipart` overrides are delegates "in the same shape the two `run` overrides already
  take" — i.e. per-view — so the two adjacent bullets disagreed about where the hooks live.
  Fixed together, and the delegate count is now stated per colour (two statements sync, three
  async, the async request adapter's form data having to be awaited) instead of "two-line" for
  both.
- **"No local `getattr(settings, ...)`" needed its scope.** As written it reads as covering
  every settings read, and `views.py::_form_encoding_is_utf8` reads `settings.DEFAULT_CHARSET`
  directly — which [Decision 17][s65-d17] *requires*, because the check must reproduce the exact
  `encoding or settings.DEFAULT_CHARSET` pair `MultiPartParser.__init__` resolves. The rule is
  about the `DJANGO_STRAWBERRY_FRAMEWORK` keys and now says so, with the carve-out named at the
  one site that takes it. **Why it is worth the words:** the unscoped form would have been read
  as a violation by the next reviewer to sweep this section, and a false finding argued against
  correct code costs more than the clause does.
- **The three pieces of connection state are not "one set of state on the adapter instance".**
  The revalidation obligation said the connection-local lock, the revoked flag and the
  last-validated timestamp were **one** set of state on the adapter instance upstream creates
  per connection. None of the three is there. The lock and the flag are assigned in
  `consumers.py`'s `GraphQLWebSocketConsumer.__init__` (see [Decision 16][s65-d16]'s own
  correction), and the timestamp is written onto the ASGI `scope` under
  `consumers.py::_REVALIDATED_AT_SCOPE_KEY` — so the claim was wrong about the object *and*
  about there being one of them. What is load-bearing, and true, is that all three are
  **connection-scoped** rather than three parallel caches keyed by protocol, and the obligation
  now says exactly that, naming the two homes a connection already has. Both are reachable from
  the one argument the shared decision function is handed — the consumer, whose `scope` it reads
  — so "one connection, one set of state" survives the split. **Rejected alternative:** moving
  the timestamp onto the consumer instance so the obligation's original sentence would become
  true. Rejected on the spot: this is a custodian pass reconciling prose to shipped code, and
  rewriting working code to make a sentence true inverts which of the two is the contract.
  **Direction of the drift:** as with the lock's owner, the *scope* claim was right and the
  *location* claim was wrong, so nothing was mis-built — but a reuse obligation that names the
  wrong object cannot be verified against the tree, which is the only thing this section is for.

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

**Change record — the `APPEND_SLASH` policy is `DEBUG`-dependent and now says so.** Two sites
stated the consequence of `POST /graphql` against a `path("graphql/", …)` mount without a
qualifier: the [`## Edge cases and constraints`][s65-edge-cases] bullet ("a `POST` to `/graphql`
also gets a `301`, which most HTTP clients will not re-`POST`") and the
[`### Consumer-visible behavior`][s65-consumer-visible] bullet that the migration note is written
from. That holds under `DEBUG=False` only. `CommonMiddleware.get_full_path_with_slash` raises
`RuntimeError` for `DELETE`, `POST`, `PUT` and `PATCH` when `settings.DEBUG` is true — rather than
redirect and lose the body — so the same request is a `500` on a development stack. Both sites now
carry the split. **Why it earns the words:** the reader most likely to *test* the claim is running
`DEBUG=True`, would observe a `500`, and would conclude the documented policy is wrong. The
consumer-facing transport guidance in `docs/README.md` already stated both halves, so this is once
more the shipped doc being more accurate than the spec it was written from — the direction that
says the spec is what has to move. **Direction of the drift:** it named the milder of two
outcomes, and the omitted one is the noisier and more confusing of the pair.

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

**Change record — the method scoping round 2's L1 introduced.** Step 3's carve-out was stated
for "a multipart request", while `views.py::_is_multipart_form_post` narrowed it in the same
round to a multipart **POST**; the decision also never said that a `GET` is outside the cap
altogether. So the spec answered "hand off to Django's parser" for a request shape the code
counts like any other body. The scoping is now stated in the decision, keyed to the one named
discriminator [Decision 17][s65-d17] shares. Nothing was rejected: the only alternative was
leaving the spec silent about a shape the round had just changed, which is how the divergence
arose in the first place.

**Change record — the over-reporting direction was described as read, and it is refused.** The
spec's [`## Edge cases and constraints`][s65-edge-cases] bullet on the incoherent probe said
that both incoherent shapes "make the probed difference zero or negative", and then disclosed a
cost the code does not pay: "the restored position lands past the end, so the request reaches
Strawberry with an **empty** body and is a `400` at the parse". Read against
`django_strawberry_framework/_request_body.py`, that is the behavior of the *two*-state probe
this decision's own third outcome replaced. `_measured_remaining` verifies the restore through
`_position_restored` **before** the subtraction is ever reached, and a `tell()` that
over-reports the position over-reports it again when the restore is verified, so the verdict is
`_Probe.CORRUPTED`: `body_exceeds_limit` logs the corrupted-probe `WARNING` and returns `True`,
which is the package's own `413` with **zero** bytes read.
`tests/test_views.py::test_a_stream_reporting_a_position_past_its_end_is_refused_rather_than_read`
pins exactly that (`413`, `requested == []`, `delivered == 0`, one log record), and its own
docstring calls the empty-body outcome "what the two-state version did". Only the
under-reported end and an honest zero ever reach the subtraction. The bullet and test-plan row
15 now state the two directions separately; the neighbouring capability-call bullet and outcome
3 of *An unmeasurable stream has three outcomes, not two* now also say that a restore fails when
the verifying `tell()` disagrees as well as when the seek raises, because `_position_restored`
returns `False` for both and the caller refuses them identically. **Direction of the drift:** it
understated how strict the boundary is, so nothing was exposed by it — but it attributed the
refusal to Strawberry's parser and a `400` where the package answers `413` itself, which is the
class of drift that sends an operator debugging a real refusal to the wrong layer. **Rejected
alternative:** deleting the disclosure sentence instead of rewriting it. Rejected because the
honesty it was reaching for is real — recovering an over-reporting stream's true bytes *is*
impossible, and rewinding to zero *would* corrupt a legitimately mid-position stream — so both
facts are kept, attached to the outcome they actually explain.

### Decision 8 — The deployment-layer cap is a co-requirement, not an alternative

Spec: [Decision 8][s65-d8].

**Alternative rejected.** Treating the application cap as sufficient and mentioning the
proxy in passing. Rejected: it would restate the exact conflation the audit called out,
and would make the package's own documentation the source of a false guarantee.

**Change record — the "concrete directions" no longer name a header knob as a body cap.**
The decision listed `--limit-request-field-size` "/ equivalents on the ASGI server" beside
nginx's `client_max_body_size`. That knob bounds a **header field**, not the body, and no
mainstream ASGI server bounds the total body at all — so the list implied a layer of
protection that does not exist, in a decision whose entire purpose is to stop the two layers
collapsing in the reader's head. It now names `LimitRequestBody` on Apache as the second real
directive and states the ASGI-server absence outright, which is what makes the proxy line
load-bearing rather than belt-and-braces. **Rejected alternative:** keeping the knob with a
qualifier ("bounds headers, not the body"). Rejected because a reader scanning a list of
"concrete directions" takes the list, not the qualifier — and this class of drift was found
by the shipped guidance being *more* accurate than the decision it was written from, which is
the direction that says the decision, not the doc, is what has to move.

**Change record — the multipart carve-out is stated POST-scoped, matching Decision 7.**
[Decision 7][s65-d7]'s own method-scoping paragraph names `views.py::_is_multipart_form_post`
as the single discriminator and states that a multipart content type on any other method is
counted like any other body. Decision 8's parenthetical still said "for a multipart request",
which is the looser half of that rule stated as the whole of it. The scope is now inside the
parenthetical, and the obligation to state it is now part of the Slice-5 prose contract rather
than left to the writer. Direction of the drift: it **understated** enforcement, so nothing
was exposed by it, and the same unscoped wording had already propagated from here into
`conf.py`'s key comment, `views.py`'s `**Multipart.**` docstring paragraph, the consumer-facing
transport guidance and the rendered `Request-body cap` glossary entry — the four surfaces the
routed follow-up now names one by one. **Rejected alternative:** leaving the sentence
unscoped because the divergence is in the safe direction. Rejected: an understated boundary
still teaches a consumer the wrong rule, and this decision is the source every other telling
was copied from.

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

**Change record — the gate reaches a package mount too, for one of its two halves.** *Which
docs, by surface* scoped the per-half consequence of disabling `APPLY_UPSTREAM_PATCHES` to
"**on Strawberry's own view**, the only mount the gate can still reach", and the
[`## Slice checklist`][s65-slice-checklist] sub-bullet for `_patched_parse_json` said the same.
That is true of the `cross_web` half and false of the Strawberry half.
`_strawberry_patches.py::apply` assigns `BaseView.parse_json`, and the mixin's own `parse_json`
override delegates with `super().parse_json(data)` — which resolves to exactly that patched
attribute — so the **body-envelope** guard rides the gate on a package mount as well. Measured:
with the patch installed, `DjangoGraphQLView().parse_json(b"42")` and `…(b"[1,2]")` both raise
the envelope guard's `HTTPException(400, …)`; with `BaseView.parse_json` restored to the captured
original they return `42` and `[1, 2]`, and upstream's unguarded `data.get("query")` turns each
into an unhandled `500` — pinned on the wire against the package mount by
`examples/fakeshop/test_query/test_transport_api.py::test_the_upstream_bug_workaround_still_respects_its_own_opt_out`.
What genuinely does **not** ride the gate on either mount is the **wire contract**: the strict
UTF-8 decode and the body source are view-owned code, which is this decision's whole ownership
argument and is unchanged. Both patch-module docstrings already carried the corrected scoping,
`_strawberry_patches.py`'s in the words "What the gate does NOT scope is the **mount**"; the spec
is what had to move. **Direction of the drift:** this one is in the **unsafe** direction — the
false scoping told a consumer that disabling the Strawberry patch could not affect a package
mount, when it turns a controlled `400` into an unhandled `500` there. It is the only one of this
pass's corrections that overstated a guarantee rather than understating it. **Rejected
alternative:** rewiring the mixin to call the captured original rather than `super()`, which would
have made the old sentence true and given the envelope guard the same ungated ownership the wire
contract has. Rejected as out of scope for a custodian pass and wrong on the merits: the guard is
a workaround for a specific upstream defect (#3398), so it *should* stay opt-out-able, which is
[Decision 9][s65-d9]'s own lifecycle rule applied in the other direction.

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

**Change record — the window's cost, priced per checkpoint rather than per operation.** The
decision's own opening states the window "means the same thing at both checkpoints" and prices
the trade as "one session read per authorized *event*"; twenty lines later the astronomical-window
paragraph still priced it as "one session read per authenticated **operation**". That is the
pre-[Decision 16][s65-d16] single-checkpoint framing surviving inside the decision that replaced
it, so the decision contradicted itself about its own cost model, and the sentence understated
the read count by the number of information-bearing frames an operation emits. Now "per
authenticated **checkpoint**", matching `consumers.py::resolved_revalidation_window`'s own
wording and both of the decision's other two tellings. **The code was already right** — only
this sentence and `routers.py`'s public constructor docstring carried the old framing, and the
docstring is source rather than spec. **Rejected alternative:** deleting the price from this
paragraph and pointing at the opening instead. Rejected because the paragraph's argument *is*
the price — it is why the package refuses to invent an upper bound — so a reader who has to
navigate away to find it loses the reason the astronomical window is accepted at all.

**Change record — the admission subclasses' size.** *Where the revalidation hooks in* called the
two per-protocol admission subclasses "two two-line subclasses"; each carries a three-line body
(the awaited revalidation, a bare `return` on refusal, the `super()` delegation). Corrected as
one site of the three-site "two-line delegate" sweep recorded under [Decision 17][s65-d17]; the
single-siting claim the sentence exists to make — the logic lives in the shared function and the
subclasses carry none of it — was verified against `consumers.py` and is unchanged.

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
- **Enforce a maximum lifetime in the package at all** — the alternative the decision's title
  names. Rejected for the reason the spec argued at length and no longer needs to, moved here
  in full because every normative half of it is stated elsewhere in the decision (the "does
  not impose" sentence, the Slice 5 documentation items (a)-(d), and the
  authorization-versus-resource bound paragraph):

  > **Why not enforce it.** A framework-imposed disconnect is a visible behavior change for
  > every subscription consumer, with no correct default: the right lifetime for a dashboard
  > subscription and for a short-lived request-response socket differ by orders of magnitude.
  > The audit asks for "at minimum, document a maximum connection lifetime and a
  > consumer-class injection seam"; the seam ships in
  > [Decision 11][s65-d11],
  > and with revalidation on at both checkpoints, lifetime stops being the bound the
  > *authorization* boundary depends on.

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

- **Bump to `0.0.15` in Slice 5.** Rejected: card `050` also ships into `0.0.15`; a
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

**Change record — the lock's owner is the consumer, not the adapter.** *One connection-local
lock, held through the send* said the single `asyncio.Lock` was "owned by the connection's
adapter instance (upstream constructs exactly one per connection …)". Nothing of the sort lives
on the adapter: `consumers.py::build_revalidating_consumer_class`'s
`GraphQLWebSocketConsumer.__init__` assigns `self._revocation_lock` and
`self._revocation_observed`, and the generated class's own docstring gives the reason in the
same words the decision uses — "per-INSTANCE … one consumer instance is exactly one
connection". The adapter reaches both through `websocket.ws_consumer` in
`consumers.py::send_revalidated_operation_frame`. Because Channels builds exactly one consumer
per connection, the parenthetical's *reasoning* was sound and is kept word for word; only the
named owner and the layer that constructs it changed (`upstream` -> `Channels`). Everything
after it — holding the lock through the send, and the sibling-task interleaving that closes —
was re-verified against that coroutine and is unchanged. **Direction of the drift:** it named
the wrong object for state whose *scope* it stated correctly, so the soundness argument was
never at risk; what was at risk is a reader looking for the lock on the derived adapter
subclass, finding none, and concluding the outbound gate is unsynchronized.

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

**Rejected — a fallback chain over the encoding sources.** "Resolve the effective encoding the
way Django does: the declared top-level `charset`, else `request.encoding`, else
`settings.DEFAULT_CHARSET`, and require whatever wins to canonicalize to UTF-8." It is the
reading the decision first shipped with, in both code and spec, and it is **wrong about
Django**, which applies no such rung order: the declaration is consulted exactly once, at
`HttpRequest._set_content_type_params`, and at parse time only `request.encoding or
settings.DEFAULT_CHARSET` is ever read. The chain fails in both directions —

- it lets the **declaration** be the value validated while Django decodes with something else,
  so one line of consumer middleware assigning `request.encoding` is masked by a client
  sending `charset=utf-8`; and because a Latin-1 decode never fails, the `U+FFFD` check cannot
  see the substitution either;
- it **accepts** a declared codec name Django cannot load: the promotion never happens,
  `request.encoding` stays `None`, and the chain falls through to a UTF-8 `DEFAULT_CHARSET`
  while the client's declaration was honoured by nobody.

The shipped contract is therefore two **independent** encoding requirements joined with `and`
(plus the loss check), and the rung-ordered phrasing must not be reintroduced.

**Change record — the round-2 adversarial review (M1).** The chain landed in the round-2
implementation and in this decision's own condition 1. `bld-review-2-w3_review.md` M1 caught it
in code — an `or` where the contract needed an `and` — and its `## Notes for Worker 1` item 1
said the chain described the shipped bug rather than the contract and must not land as spec
prose. The code was corrected first (`views.py::_form_encoding_is_utf8`, two conditions), and
the spec caught up in a later custodian pass: condition 1 and condition 2 became three
requirements, the outcome table gained the unusable-declared-codec, reconfigured-`DEFAULT_CHARSET`
and middleware-`request.encoding` rows, and the sentence quoted below left the spec.

**Claim this decision may no longer make.** It read:

> **The effective multipart form encoding must canonicalize to UTF-8.** The package resolves
> it the way Django does — the declared top-level `charset` (which Django has already
> promoted onto `request.encoding` from `content_params`), else `settings.DEFAULT_CHARSET` —
> and accepts only codec aliases that canonicalize to UTF-8.

Two things in it are false: that the resolution is a fallback chain at all, and that a declared
`charset` is *always* promoted onto `request.encoding` (an unusable one never is). One further
sentence went with it — an edge-case bullet claiming the guard "accepts a document that
legitimately contains a literal `U+FFFD` as the one deliberate false positive", which inverted
the decision's own narrowing: such a document is **refused**.

**Change record — which requests the three requirements apply to.** They were stated without a
scope. They apply to a multipart **POST** and nothing else, through the same
`views.py::_is_multipart_form_post` discriminator that scopes [Decision 7][s65-d7]'s cap
carve-out — the guard's original content-type-only scoping answered `400` to a `GET` carrying a
stale `multipart/form-data` header, i.e. to a form Django never parses (round 2's L1). Stated in
the decision at final verification; the code and its tests already had it.

**Change record — "two-line delegate", corrected at all three sites that still said it.** Three
places priced a delegate by a line count the shipped code does not have, and the count had
already been corrected in a fourth. `views.py`'s sync `parse_multipart` override is two
statements; the async one is **three**, because `await request.get_form_data()` has to run
before the guard can be handed a form. This decision's *The guard is one shared helper* sentence
said "a two-line delegate" for both colours, and so did the
[`## Slice checklist`][s65-slice-checklist] sub-bullet for the multipart guard. Separately,
[Decision 11][s65-d11]'s *Where the revalidation hooks in* called the two admission subclasses
"two two-line subclasses": `consumers.py`'s `_RevalidatingTransportWSHandler.handle_subscribe`
and `_RevalidatingGraphQLWSHandler.handle_start` each carry a **three**-line body — the awaited
revalidation, a bare `return` when it refuses, and the `super()` delegation. The telling to match
was already in [`## Helper-reuse obligations (DRY)`][s65-dry], whose multipart obligation states
the split per colour ("the sync one two statements, the async one three, because the async
request adapter's form data must be awaited"); all three sites now agree with it. **Why one
correction and not three:** the same claim survived an earlier correction pass precisely because
that pass landed on the DRY bullet and not on its three siblings, so the sweep is the unit of
work rather than the site. **Direction of the drift:** the count was too small in every case, so
no builder wrote too little code from it — but "two-line" is the kind of detail a reviewer checks
literally, and a delegate that reads three lines against a spec that says two is a finding
argued against correct code.

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
reads the `Origin` header and nothing else, and `AllowedHostsOriginValidator` is a factory that
configures it with `settings.ALLOWED_HOSTS` (or, under `DEBUG` with that setting empty, with its
own hardcoded `["localhost", "127.0.0.1", "[::1]"]`) — the class name was not evidence of
behavior, and a handshake carrying an allowed `Origin` and a hostile `Host` connected
successfully. The spec's
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

**Change record — the round-2 adversarial review (M3).** The projection was specified "item by
item", and one item — the verdict when the handshake carries no `Host`, no `X-Forwarded-Host`
and no `scope["server"]` — was pinned by nothing: every other WebSocket row supplies an allowed
`Host` and so executes that arm without consulting it, which is statement coverage without
behavioral coverage and the shape a fail-open expression hides in.
`bld-review-2-w3_review.md` M3 raised it, and its `## Notes for Worker 1` item 3 added the half
no builder could supply: the arm's values are **Django's ASGI adapter's literals** and are
therefore not derivable from a spec that does not name them. The remediation pass added the
behavioral row; the custodian pass then named `SERVER_NAME = "unknown"` / `SERVER_PORT = "0"`
in the projection bullet and the resulting denial in test-plan row 46, so a reader can derive
the verdict instead of taking it on trust. Naming the literals is deliberate rather than
incidental precision: the reason the handshake is denied is arithmetic on those two values
(`"unknown:0"` is a host no `ALLOWED_HOSTS` allows), and a spec that says only "Django's normal
fallback" leaves a reader unable to tell a denial from an accept.

**Change record — `AllowedHostsOriginValidator` is not "only a factory", and the divergence it
hides is evidence for this decision.** Two spec sites — [`## Current state`][s65-current-state]
and this decision's *Why call Django rather than narrow the claim* — said
`AllowedHostsOriginValidator` "is only a factory for `OriginValidator(settings.ALLOWED_HOSTS)`".
Read at the installed channels 4.3.2 (`channels/security/websocket.py`), it does one thing more:
when `settings.DEBUG` is true and `ALLOWED_HOSTS` is empty it substitutes its own hardcoded
`["localhost", "127.0.0.1", "[::1]"]`. That substituted list is **not** the one Django's own
`HttpRequest.get_host()` substitutes in the identical situation —
`[".localhost", "127.0.0.1", "[::1]"]`, whose leading dot matches every `*.localhost`
subdomain — so two boundaries a reader would both call "allowed hosts" already disagree about
what the `DEBUG` default means. Both sites now state the substitution, and the decision carries
the divergence, because it is *additional* evidence for the decision rather than a footnote: it
is the second reason the package's Host answer has to be a call into `get_host()` and never an
expression of its own. **The operative claim was verified and stands unchanged:**
`OriginValidator.__call__` reads `Origin` and nothing else and never validates `Host`, so a
handshake carrying an allowed `Origin` and a hostile `Host` still connects. **Direction of the
drift:** the claim was too small rather than too large, and in the safe direction for this
decision's conclusion — but "only a factory" is exactly the kind of dismissal that stops the
next reader from opening the file, and what is in the file is a `DEBUG` default that does not
match Django's.

**Change record — the `DEBUG` + empty `ALLOWED_HOSTS` default, stated as Django states it.** The
[`## Edge cases and constraints`][s65-edge-cases] bullet on fakeshop's shape said that
combination "makes Django accept `localhost` / `127.0.0.1` only". `django/http/request.py`'s
`HttpRequest.get_host()` substitutes `[".localhost", "127.0.0.1", "[::1]"]`, identically on 5.2
and 6.0: the leading dot admits every `*.localhost` subdomain, and the IPv6 loopback is accepted
too, so the real default is wider than the bullet's in both directions it was wrong about. The
bullet's remediation is untouched and was correct all along — the hostile-`Host` rows must not
depend on fakeshop's `DEBUG` value and set `ALLOWED_HOSTS` explicitly with `override_settings`,
which is what makes the correction cost one clause rather than a test change. **Direction of the
drift:** it understated what a `DEBUG` deployment accepts, which is the unsafe direction for a
reader who takes the bullet as a statement about their own development stack.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md

<!-- docs/ -->
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-debug-toolbar-middleware]: GLOSSARY.md#debug-toolbar-middleware
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: GLOSSARY.md#live-first-coverage-mandate
[glossary-request_from_info]: GLOSSARY.md#request_from_info
[s65-borrowing-posture]: spec-046-transport_security-0_0_15.md#borrowing-posture
[s65-consumer-visible]: spec-046-transport_security-0_0_15.md#consumer-visible-behavior
[s65-current-state]: spec-046-transport_security-0_0_15.md#current-state
[s65-d10]: spec-046-transport_security-0_0_15.md#decision-10--a-utf-8-bom-is-rejected
[s65-d11]: spec-046-transport_security-0_0_15.md#decision-11--a-websocket-consumer-classfactory-injection-seam-with-a-revalidating-package-default
[s65-d12]: spec-046-transport_security-0_0_15.md#decision-12--maximum-connection-lifetime-is-documented-and-seamed-not-silently-enforced
[s65-d13]: spec-046-transport_security-0_0_15.md#decision-13--test-strategy-which-existing-tests-change-and-why
[s65-d14]: spec-046-transport_security-0_0_15.md#decision-14--this-card-amends-spec-041-and-supersedes-three-of-its-decisions
[s65-d15]: spec-046-transport_security-0_0_15.md#decision-15--the-0015-version-bump-is-deferred-to-the-joint-cut
[s65-d16]: spec-046-transport_security-0_0_15.md#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam
[s65-d17]: spec-046-transport_security-0_0_15.md#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard
[s65-d18]: spec-046-transport_security-0_0_15.md#decision-18--the-body-gate-runs-before-djangos-multipart-parser-via-view-local-csrf-re-entry
[s65-d19]: spec-046-transport_security-0_0_15.md#decision-19--a-django-backed-websocket-host-boundary-beside-channels-origin-check
[s65-d1]: spec-046-transport_security-0_0_15.md#decision-1--spec-filename-and-canonical-naming
[s65-d2]: spec-046-transport_security-0_0_15.md#decision-2--http-dispatches-directly-to-a-required-consumer-supplied-django-asgi-application
[s65-d3]: spec-046-transport_security-0_0_15.md#decision-3--django_application-is-required-omission-fails-at-construction-with-no-compatibility-fallback
[s65-d4]: spec-046-transport_security-0_0_15.md#decision-4--url_pattern-becomes-websocket_url_pattern-with-exact-matching-as-the-secure-default
[s65-d5]: spec-046-transport_security-0_0_15.md#decision-5--compatibility-policy-an-intentional-alpha-breaking-change-to-a-security-boundary
[s65-d6]: spec-046-transport_security-0_0_15.md#decision-6--the-graphql-http-endpoint-is-a-package-owned-django-view-in-the-consumers-urlconf
[s65-d7]: spec-046-transport_security-0_0_15.md#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared
[s65-d8]: spec-046-transport_security-0_0_15.md#decision-8--the-deployment-layer-cap-is-a-co-requirement-not-an-alternative
[s65-d9]: spec-046-transport_security-0_0_15.md#decision-9--the-strict-utf-8-wire-contract-is-enforced-by-the-package-view-its-own-body-source-one-strict-decode
[s65-dry]: spec-046-transport_security-0_0_15.md#helper-reuse-obligations-dry
[s65-edge-cases]: spec-046-transport_security-0_0_15.md#edge-cases-and-constraints
[s65-non-goals]: spec-046-transport_security-0_0_15.md#non-goals
[s65-slice-checklist]: spec-046-transport_security-0_0_15.md#slice-checklist
[spec-046]: spec-046-transport_security-0_0_15.md

<!-- docs/SPECS/ -->
[spec-040]: SPECS/spec-040-auth_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
