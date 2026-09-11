# Rationale: spec-041 — Channels ASGI router (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-041-channels_router-0_0_14.md`][spec-041]. The spec is the
contract and states only what is currently true; everything that explains **how it got there**
lives here: the alternatives each decision rejected and why each lost, the derivations that do
not change how a decision is implemented, every change a decision has undergone with the round
that caused it, and every claim a decision once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened long after the release, not before the build.** Card `DONE-041-0.0.14` shipped with no
companion at all, and later cards — chiefly [`spec-046`][spec-046] (transport security) and the
post-ship hardening of [`spec-040`][spec-040] (auth mutations) — corrected and extended what it
shipped while its own prose stayed at the pre-correction contract. This pass supplies the
companion and reconciles the spec in one custodian judgement, because what a decision now says
and what it used to say are decided together. Text marked *Moved* below was cut out of the
spec, not copied: it exists here and nowhere else.

## How to read this file

- **One entry per spec decision**, named by the decision's own heading and linked to its anchor,
  so a citation such as "Decision 11's rejected alternatives" resolves to exactly one place. An
  entry that named no decision could not be looked up and would be worthless however well
  argued.
- **Who reads it.** Worker 3 reads it during review; Worker 1 owns it; Worker 2 never reads it.
  A reader looking for what the package *does* wants the spec, not this file.
- **No timeline.** The spec carried a nine-entry `Revision history` block and a three-item
  amendment banner; both moved here and were **restructured into per-decision `Change record`
  blocks**. A reader asking "what did Decision 6 used to say?" finds the answer under
  [Decision 6](#decision-6--constructor-and-composition), not by reading a chronology and
  applying it. `## Round vocabulary` below names the rounds once so each block can cite one
  without restating it.
- **Three kinds of change are recorded, and they are not the same kind.** A *pre-implementation
  revision* changed a decision before any code existed. A *supersession* is a later card taking
  a decision's subject away from this one. A *post-ship correction* is the shipped code having
  moved while the spec's prose did not. `## Post-ship corrections` carries the third kind for
  the whole spec, keyed by the finding numbers `docs/builder/build-041-channels_router-0_0_14.md`
  assigned them, and each decision entry cross-links the ones that touch it.
- **Where a change record and the spec disagree, the spec is the contract** and the change
  record is why it moved. A claim the decision may no longer make is named in the record rather
  than deleted silently.
- **What deliberately stayed in the spec even though it reads like deliberation.** Decision 5's
  "`require_channels()` runs *before* any `strawberry.channels` import" ordering and Decision
  11's "wrap, do not narrow" reasoning are both instructions to a builder, not records of
  thinking: a builder who never reads them re-writes the bare-traceback path or the two-field
  adapter. Likewise the `## Edge cases and constraints` reasoning about why a missing `Origin`
  is denied, and the `## Test plan`'s note that a structural walk is isolated behind one helper.
  When it was unclear whether a sentence was deliberation or instruction, it stayed.

## Round vocabulary

The spec's `Revision history` block named nine revisions. They were not nine of the same thing,
and the distinction is what makes the per-decision records readable:

- **Revision 1** — the initial draft, authored from the `WIP-ALPHA-041-0.0.14` card body via the
  [`docs/SPECS/NEXT.md`][next] flow (2026-07-03). It pinned Decisions 1-10.
- **Revisions 2, 3 and 4** — three successive **adversarial claim-verification passes**. Each
  re-verified every factual claim against a source before editing: Revision 2 against the
  Channels `4.2.1` source and changelog, the installed strawberry `0.316.0`, and the package's
  own conftest / DRF-guard sources; Revision 3 independently against the Channels `4.2.1` *and*
  `4.3.2` sdists plus PyPI release metadata; Revision 4 against the `channels/auth.py` /
  `channels/sessions.py` sources at the `4.2.1` tag, plus a [`GOAL.md`][goal] cross-reference
  pass the maintainer asked for.
- **Revision 5** — a maintainer review, foundational items first. The largest single change: it
  added Decision 11.
- **Revision 6** — alignment with a maintainer `utils/` DRY review whose prescribed refactors
  landed in the repo in the same pass.
- **Revisions 7 and 9** — two full glossary-anchoring passes, before and after the Revision-8
  edits. They added vocabulary entries to the glossary DB, re-rendered
  [`docs/GLOSSARY.md`][glossary], and grew the companion terms CSV from 16 rows to 22 and then
  to 30.
- **Revision 8** — a second critical review, surfaced while adding the `TODO(spec-041 Slice N)`
  source anchors; ten required pre-implementation edits.

Every one of the nine happened **before implementation**. Nothing in that block recorded what
the build discovered, which is why moving it costs the spec nothing a builder needed.

## Supersession: what `spec-046` took over

*Moved from the spec's amendment banner, which sat immediately under the title.*

[`spec-046`][spec-046] (card `DONE-046-0.0.14`, transport security) supersedes exactly three
items of this spec, and its own [Decision 14][s46-d14] is where that supersession is decided:

1. **[Decision 6](#decision-6--constructor-and-composition)** (constructor parity with
   upstream's `AuthGraphQLProtocolTypeRouter`) — superseded **in full**: `django_application` is
   now required, `url_pattern` is now `websocket_url_pattern` and exact rather than a shared
   prefix, and the byte-compatible upstream constructor is deliberately broken as an intentional
   alpha breaking change.
2. The **HTTP half** of [Decision 2](#decision-2--card-scope-boundary) (the card-scope boundary)
   — GraphQL over HTTP is no longer this router's concern at all; it is the package's own Django
   view (`views.py::DjangoGraphQLView`) declared in the consumer's
   URLconf. The WebSocket half of that decision stands.
3. The HTTP-branch and Django-fallback paragraphs of the spec's `## Borrowing posture` — the
   router serves no `http` GraphQL scope, so there is no Strawberry HTTP consumer to borrow and
   no `^` fallback appended behind one. The `"http"` value **is** the consumer's Django ASGI
   application, dispatched directly.

Everything else this card shipped survives: the `DjangoGraphQLProtocolRouter` symbol
([Decision 3](#decision-3--the-symbol-name)), its soft-`channels` guard and PEP 562 lazy export
([Decision 5](#decision-5--soft-channels-dependency)), the engine-owned consumer
([Decision 7](#decision-7--engine-owned-consumers)), the test strategy
([Decision 8](#decision-8--test-strategy)), joint-cut version ownership
([Decision 10](#decision-10--joint-cut-version-ownership)), and the Channels request contract
([Decision 11](#decision-11--the-channels-request-contract)).

**Separately, and explicitly not a supersession.** The spec repeatedly described the package's
*current* pinned `strawberry-graphql` floor as `>=0.262.0`. That floor moved to `>=0.316.0` in
[`pyproject.toml`][pyproject] and the minimum CI matrix node pins the same value, so those
sentences were factually wrong *about live code* rather than decisions this card made and
`spec-046` reversed. `spec-046`'s Slice 5 corrected the prose it could see and **missed the
Definition-of-done line**, which is why that line survived as F5 below. Sentences that are
explicitly historical — "the export's presence at the `0.262.0` floor itself is upstream
history, spot-checked at the dependency gate" — are **kept in the spec**, because they record
what was true when this card shipped and make no claim about live code. Checkbox state
throughout the spec is likewise untouched: the `Status:` line is the source of truth, which is
this repo's shipped-card closeout convention.

**Rejected alternatives for the reconciliation itself** — whether an archived spec should be
rewritten to the current contract at all, as against keeping the amendment banner it carried.
This is a contract choice rather than a worker's call, and the maintainer decided it: the spec
must match what exists, and the explanation of what changed goes here.

- **Keep the amendment banner, edit nothing.** Lost because [`docs/builder/BUILD.md`][build]
  `## Spec rationale extraction` makes a spec a contract that never narrates its own history,
  and because a reader had to apply a three-item chronology to the document to learn what was
  true.
- **Delete the superseded decisions outright.** Lost because it would strand every inbound
  citation and erase the reasoning this file exists to preserve.

## Post-ship corrections

Twelve findings, each read against source at HEAD before being written down, and each recorded
as *what the spec used to claim* / *what HEAD does* / *which card caused it*. All twelve are
spec-only: the code-conformance sweep found **every** `spec-041` deliverable landed, and no code
change was owed. The one class of absence it found is correct rather than a gap — four Test-plan
rows have no live counterpart because each asserted the HTTP GraphQL branch `spec-046`
deliberately removed: the `AuthMiddlewareStack`-wraps-HTTP row, the HTTP fallback-route
**ordering** row, the `HttpCommunicator` GraphQL POST round trip, and the non-GraphQL-path
fallback row. `tests/test_routers.py::test_graphql_http_consumer_left_the_router_module_entirely`
now pins that removal positively. Those four rows are named by content on purpose: the
rewritten `## Test plan` reuses every one of their ordinals for different content.

### F1 — the constructor signature

*Claimed:* `(schema, django_application=None, url_pattern="^graphql")`, held byte-compatible
with upstream, in [Decision 6](#decision-6--constructor-and-composition), `## User-facing API`,
`## Implementation plan` and `## Definition of done`.
*HEAD:* `routers.py::_build_router_class_uncached`'s inner
`DjangoGraphQLProtocolRouter.__init__` is
`(schema, django_application, *, websocket_url_pattern=r"^graphql/?$",
websocket_consumer_class=None, websocket_revalidation_window=...)`.
*Cause:* [`spec-046`][spec-046] Decisions 3, 4, 5 and 11.
*Also falsified, and reconciled with it:* [Decision 9](#decision-9--migration-ergonomics)'s
migration-guide row, whose "the constructor signature is unchanged" note was the whole point of
the row, and `## Goals` Goal 3, whose "zero call-site changes" promise rested on the same
byte-compatibility. A third sentence rotted from the other end: Goal 3 quoted
[`GOAL.md`][goal] success criterion 7 as "only the import line changes", and criterion 7 no
longer carries that phrase — it now reads "The import-only promise covers `Meta`-driven domain
declarations; project-level engine configuration … migrates by documented recipe." Both halves
of the sentence had moved, in opposite directions.

### F2 — the `http` branch

*Claimed:* `AuthMiddlewareStack(URLRouter([graphql, *django_fallback]))`.
*HEAD:* the consumer's Django ASGI application, assigned verbatim —
`routers.py` #'"http": django_application'. No `URLRouter`, no
`re_path`, no `AuthMiddlewareStack`, no GraphQL consumer.
*Cause:* [`spec-046`][spec-046] Decisions 2 and 6.

### F3 — the `websocket` branch

*Claimed:* `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([graphql])))`.
*HEAD:* a fourth layer wraps that composition outermost —
`consumers.py::DjangoWebSocketHostValidator`, which denies a
handshake whose `Host` Django's own `HttpRequest.get_host()` refuses, before the Origin check,
before the session middleware, and before any consumer is constructed.
*Cause:* [`spec-046`][spec-046] Decision 19.

### F4 — which consumers are imported

*Claimed:* `GraphQLHTTPConsumer` **and** `GraphQLWSConsumer`, in
[Decision 7](#decision-7--engine-owned-consumers), `## Error shapes`, the Strawberry-floor gate,
and the DoD.
*HEAD:* `_build_router_class_uncached` imports only `GraphQLWSConsumer`, and hands it to
`consumers.py::build_revalidating_consumer_class`.
*Cause:* [`spec-046`][spec-046] Decisions 2, 6 and 11.

### F5 — the Strawberry floor in the Definition of done

*Claimed:* the gate confirms the consumers importable at `strawberry-graphql==0.262.0`.
*HEAD:* [`pyproject.toml`][pyproject] #"strawberry-graphql>=0.316.0",
`utils/imports.py::STRAWBERRY_FLOOR`, and the re-typed test literal
`tests/test_routers.py` #"_STRAWBERRY_FLOOR_SUBSTRING" all read `0.316.0`.
*Cause:* the floor bump, and `spec-046` Decision 14's reconciliation pass, which corrected the
prose sentences and missed this one. The DoD line therefore contradicted the spec's own
preamble — a live requirement naming a version the package metadata rejects. Unlike the
historical sentences that stay, a DoD item is a completion claim and gets no vintage licence.

### F6 — the floors are no longer written inside the hint strings

*Claimed:* Helper-reuse **D2** described an install-hint constant carrying the floor as text.
*HEAD:* `utils/imports.py::CHANNELS_FLOOR` and
`utils/imports.py::STRAWBERRY_FLOOR` are interpolated into every
hint that names them, leaving [`pyproject.toml`][pyproject] as the one other written copy of
each.
*Cause:* a later DRY consolidation the spec never absorbed. The obligation's *intent* — one
written floor, compared against something — is strengthened by the change, not weakened: the
version was previously re-typed as a bare literal that nothing compared against the
`channels[daphne]` row.

### F7 — first construction is serialized

*Claimed:* only the unsynchronized `_ROUTER_CLASS` module-global cache.
*HEAD:* `routers.py` #"_ROUTER_CLASS_LOCK" plus a double-checked
`routers.py::_build_router_class` /
`routers.py::_build_router_class_uncached` pair, pinned by
`tests/test_routers.py::test_concurrent_first_class_access_returns_one_cached_class`.
*Cause:* post-ship hardening. The eviction property Decision 5 and Helper-reuse **D3** depend on
is unaffected — both the cache and its lock are module globals, so a `sys.modules` eviction
still drops them with the module.

### F8 — the Channels adapter grew a second shape and a fail-closed read

*Claimed:* [Decision 11](#decision-11--the-channels-request-contract) described the HTTP
consumer's `ChannelsRequest`, whose scope lives at `consumer.scope`.
*HEAD:* `utils/permissions.py::_channels_scope` resolves **both**
shapes — `consumer.scope` for the HTTP consumer's request object, and `request.scope` for the
WebSocket consumer, which supplies *itself* as the context request — and
`utils/permissions.py::ChannelsRequestAdapter._scope_value` converts
a hostile scope mapping into a [`ConfigurationError`][glossary-configurationerror] rather than
letting it escape raw.
*Cause:* [`spec-046`][spec-046]'s WebSocket-only router made the second shape the *primary* one,
and the hardening pass added the contained read. The decision's own rule — wrap, never narrow —
is what both extensions obey.

### F9 — auth over Channels is no longer wholly deferred

*Claimed:* [Decision 11](#decision-11--the-channels-request-contract) point 2 and
[Decision 2](#decision-2--card-scope-boundary) defer session-*mutating* auth to a follow-on
card, and `## Non-goals` / `## Out of scope` name that card as the `TestClient` sibling or a
dedicated follow-on.
*HEAD:* the transport-owned boundary ships in
`auth/sessions.py`, which classifies a request into one explicit
transport (`Transport.DJANGO_HTTP`, `Transport.CHANNELS_HTTP`, `Transport.CHANNELS_WEBSOCKET`)
by `isinstance` against the adapter and then `scope["type"]`, and answers the capability
question per transport: `auth/sessions.py::login_supported` is
`False` on any WebSocket (an established socket cannot send the replacement session cookie
login's key rotation produces), and
`auth/sessions.py::logout_supported` is `False` only on a
signed-cookie-engine WebSocket.
*Cause:* [`spec-040`][spec-040]'s own post-ship hardening of the session lifecycle, not
`spec-046`. The deferral was discharged by the card that owned the auth surface, which is why
the spec now attributes it there rather than re-absorbing the contract.

### F10 — the test plan

*Claimed:* four rows over the HTTP GraphQL branch — `AuthMiddlewareStack` wrapping HTTP, the
HTTP fallback-route ordering assertion, the `HttpCommunicator` GraphQL POST round trip, and the
non-GraphQL-path fallback — plus the package-request-contract row and the authenticated-session
round trip, both specified over `HttpCommunicator`.
*HEAD:* those four HTTP-branch rows are correctly gone, with their removal pinned positively by
`tests/test_routers.py::test_graphql_http_consumer_left_the_router_module_entirely`; the
rewritten `## Test plan` reuses their ordinals for different content, so they are named here by
content rather than by number. The request-contract and authenticated-session rows
are proven over the WebSocket branch instead —
`tests/test_routers.py::test_request_contract_resolves_over_the_websocket_branch` and
`tests/test_routers.py::test_authenticated_session_round_trip_reaches_the_resolver`. The
`HttpCommunicator` survives in the suite, but proving *delegation*
(`tests/test_routers.py::test_http_branch_delegates_every_path_to_the_supplied_application`)
rather than GraphQL execution.
*Cause:* [`spec-046`][spec-046] Decision 13, which decided which existing tests change and why.
*The subject was preserved, only the transport moved*: the authenticated-session round trip
still mints a real user and session and still asserts the resolver sees the authenticated actor.

### F11 — the edge cases

*Claimed:* four paragraphs describing a branch that no longer exists — the `^graphql` prefix
semantics, "the HTTP fallback runs *inside* `AuthMiddlewareStack`", the async-HTTP-consumer
sync-ORM paragraph, and multipart uploads over the Channels HTTP consumer.
*HEAD:* the pattern is `websocket_url_pattern`, WebSocket-only and exact at both ends; there is
no fallback branch to sit inside anything; the async/sync-ORM constraint is real but belongs to
the WebSocket consumer, which is equally async; and multipart arrives at
`views.py::DjangoGraphQLView`, whose parsing contract
[`spec-046`][spec-046] Decisions 17 and 18 own.
*Cause:* [`spec-046`][spec-046] Decisions 4, 6, 17 and 18.
*Two of the four were rewritten rather than deleted*, because the constraint survived its
branch: sync ORM under the router's GraphQL transport still raises `SynchronousOnlyOperation`,
and an `async def` `get_queryset` under a sync surface still raises `SyncMisuseError`.

### F12 — the slice checklist and implementation plan

*Claimed:* rows restating F1-F4 — the constructor signature, the two-branch composition, and
both consumers.
*HEAD:* as F1-F4.
*Cause:* inherited. Recorded separately because a slice-checklist box and an implementation-plan
row are completion claims rather than dated observations, so they get no vintage licence and
had to be corrected in the same pass as the decisions they restate.

## Decision entries

### Decision 1 — Spec filename and canonical naming

Spec: [Decision 1][d1].

**Alternatives rejected.**

- **`spec-041-routers-0_0_14.md`.** The module name alone under-describes the card (a future
  card could touch routing again); the slug names the feature.
- **`spec-041-asgi_router-0_0_14.md`.** "Channels" is the load-bearing noun — the card, the
  GLOSSARY entry, and the upstream module are all Channels-specific; a hypothetical
  non-Channels ASGI story would be a different card.

### Decision 2 — Card-scope boundary

Spec: [Decision 2][d2].

**Alternatives rejected.**

- **Fold full auth-over-Channels verification into this card.** Partially superseded by the
  Revision-5 maintainer review: the *request-shape* half (the `request_from_info()` read
  contract) **was** folded in as [Decision 11](#decision-11--the-channels-request-contract) —
  leaving it out would have shipped a router the package's own helpers reject. The
  session-*mutating* half (login / logout semantics over `channels.auth`) stayed rejected here:
  real auth-subsystem work with its own failure modes, invisible in the card's S sizing. The
  honest move was the scoped risk entry.
- **Add the fakeshop `asgi.py` now for dogfooding.** It drags `channels` into the example's
  runtime and the live suite is WSGI `django.test.Client` — the new surface would be dead weight
  until a Channels-aware acceptance harness exists.

**Change record — Revision 5.** The bullet on auth mutations was rewritten from "the router
delivers the transport half and the rest is out" to "the transport half **and** the read-path
request contract ship; the session-mutating half stays out", when Decision 11 was added.

**Change record — superseded in half by `spec-046`.** See `## Supersession` item 2. The decision
as drafted scoped "the transport router ships" over a package-owned HTTP branch; there is none.
The WebSocket half stands unchanged.

**Change record — the auth-mutation deferral was discharged elsewhere (F9).** The decision's
deferral named no owner beyond "a follow-on card". The owner turned out to be
[`spec-040`][spec-040] itself, whose post-ship session-lifecycle hardening built the
transport-classification and capability layer. **The claim this decision may no longer make:**
that session-mutating auth over Channels is unverified anywhere in the package.

### Decision 3 — The symbol name

Spec: [Decision 3][d3].

**Alternatives rejected.**

- **`AuthGraphQLProtocolTypeRouter` verbatim.** Rejected by the card itself: the module would
  impersonate the upstream API — the [`GOAL.md`][goal] "thin wrapper" non-goal. Migration
  ergonomics are preserved by the guide row instead
  ([Decision 9](#decision-9--migration-ergonomics)).
- **A shorter `DjangoGraphQLRouter`.** It erases the one term (`Protocol`) that signals "this
  routes multiple ASGI protocols" — the class's entire reason to exist over a plain URL router —
  and diverges from both upstream names at once, making the migration-guide row harder to
  eyeball.
- **A lazy package-root export (the `SerializerMutation` shape).** `SerializerMutation` is a
  *write base* consumers subclass in schema modules, where a root import is idiomatic; the
  router is deployment plumbing typed in exactly one file (`asgi.py`). The submodule path is
  self-documenting there, and keeping the root namespace free of transport symbols keeps the
  root `__getattr__` map single-purpose (DRF names only).

**Derivation of the name, moved because it does not change how the class is built.** The card
pre-pinned the architectural posture ("must use a **distinctly-ours symbol name** (working name:
`DjangoGraphQLProtocolRouter`) so the module is unambiguously ours and does not impersonate the
upstream API") and hedged the final name to implementation time. Revision 1 resolved the hedge
in favour of the working name, because three surfaces already carried it — the card body, the
[`docs/GLOSSARY.md`][glossary] entry with its own anchor other docs link, and the
migration-guide handoff row's mapping text — so any other choice would ripple through shipped
docs for zero consumer benefit. The name reads as the package's own family (`Django*` prefix),
drops upstream's `Auth` prefix (the auth stack is part of the composition, not the headline) and
upstream's `Type` infix (`ProtocolTypeRouter` is Channels' internal naming; the package's
consumer never thinks about "protocol types").

**Change record — Revision 8.** `__all__ = ("DjangoGraphQLProtocolRouter",)` and its scoped
`# noqa: F822` were added here, together with the deliberate consequence that a submodule star
import opts into the guard. Before that edit the module declared no `__all__` at all, and
`from ...routers import *` would have leaked the helper names.

**The card's own name hedge, recorded as a risk and now closed.** The card said "final name
pinned during implementation" while this spec pinned `DjangoGraphQLProtocolRouter` up front. Not
a conflict strictly — pinning early is the spec doing the implementation's design work — but it
was recorded per the [`docs/SPECS/NEXT.md`][next] prefer-the-card rule, with the escape route
named: if implementation surfaced a genuine problem with the name, the change would be a spec
revision rather than a silent drift, and the GLOSSARY anchor plus the card's reference edges
would move with it. Implementation surfaced none; the name shipped as pinned.

### Decision 4 — Module and test locations

Spec: [Decision 4][d4].

**Alternatives rejected.**

- **A `channels/` or `integrations/` subpackage.** One class does not justify a package;
  upstream keeps it flat; and [`docs/TREE.md`][tree]'s planned row (a shipped commitment in the
  docs) named the flat path. `strawberry_django`'s `integrations/` holds third-party *library*
  adapters (guardian), not transport.
- **Colocating the guard in `rest_framework/__init__.py` as a generic
  `require_soft_dependency(name, hint)`.** The single optional-import owner is
  [`utils/imports.py`][utils-imports], which already carried `import_attr_if_importable` /
  `loaded_attr` migrated from the registry and generated-input clear paths. Slice 1 added
  `require_optional_module(module_name, *, install_hint)` there instead, and
  `require_channels()` is a thin wrapper over it, never a fourth hand-rolled import pattern.

**Change record — Revision 6.** This alternative's text was rewritten by the maintainer `utils/`
DRY review, whose prescribed refactors landed in the repo in the same pass: `utils/imports.py`
became the single optional-import owner, the neutral write-error owners moved out of
`mutations/resolvers.py` into `utils/errors.py` (`field_error`, `relation_field_error`,
`validation_error_to_field_errors`, `join_error_path`) and `utils/write_values.py`, and
`graphql_camel_name` moved to `utils/strings.py`. Before that revision, this alternative was
rejected on the narrower ground that a DRF-specific module was the wrong home; afterwards it is
rejected because a *correct* home already existed.

**Change record — the size estimate.** The decision described "one class plus one guard (~60
lines with docstrings)". `routers.py` is several times that today —
the injection seam, the window validation and five hint constants arrived with
[`spec-046`][spec-046] Decision 11 — so the spec now names the shape (one lazily-built class,
one guard, the composition) without a line figure. **Why no figure replaces it:** a
present-tense line count of a file later slices edit is false by construction.

### Decision 5 — Soft `channels` dependency

Spec: [Decision 5][d5].

**Alternatives rejected.**

- **A hard dependency.** The overwhelming majority of Django GraphQL deployments are
  WSGI-or-plain-ASGI without Channels; taxing every consumer with `channels` (which drags
  `asgiref` pins and an app-config) for a migration aid inverts the card's purpose. Upstream can
  hard-import; an integration package whose pitch includes "the package imports with zero
  optional dependencies" cannot.
- **A `django-strawberry-framework[channels]` extra.** An extra changes how consumers *install*,
  not whether the import is guarded — the guard is needed regardless (an extra is advisory;
  nothing stops an extra-less install from importing the module), so the extra adds a second
  thing to document without removing any code. The DRF precedent (no `[drf]` extra) already set
  this.
- **A module-import-time guard** (`require_channels()` at `routers.py` top level, the literal
  `rest_framework/__init__.py` shape). It makes `import django_strawberry_framework.routers`
  itself raise, which (a) breaks innocent whole-package walkers — the [`docs/TREE.md`][tree]
  docstring renderer, coverage tooling, IDE indexers — on a channels-less machine, and (b)
  contradicts the card's own DoD wording ("top-level package import must not fail... raises
  `ImportError` with an install hint **when it is actually called**"). The `rest_framework/`
  package could afford import-time because its import is itself the opt-in; a top-level module
  sitting in the package's own directory cannot.
- **A stub class whose `__init__` raises when channels is absent.** It reads the DoD's "when
  actually called" most literally, but the stub lies about identity — it is not a
  `ProtocolTypeRouter`, cannot be subclassed meaningfully, and produces a confusing two-phase
  failure (import succeeds, deploy fails). The `__getattr__` shape fails at the consumer's
  import-from line — earlier, with the same hint, and the returned object is never a lie.
- **Depending on Strawberry core's router and re-exporting it wrapped.** Core's
  `GraphQLProtocolTypeRouter` lacks the auth stack and origin validator — the entire value-add —
  and wrapping-then-mutating someone else's router class is exactly the "thin wrapper" smell;
  composing Channels' primitives directly is the same line count and honest.

**Change record — the Channels floor moved twice, and the reason changed with it.**

- *Revision 1* declared `channels>=4.2.0`.
- *Revision 2* corrected it to **`4.2.1`** on changelog evidence: `4.2.0` (2024-11-15) predates
  Django 5.2 entirely, and `4.2.1` (2025-03-29) is the first release with official Django 5.2
  support. That revision also introduced a **split**: declared floor `4.2.1`, dev-resolved
  `>=4.3.2` for the CI matrix's Django 6.0 leg.
- *Revision 5* collapsed the split to a **single** `4.3.2` everywhere. The install hint is public
  API in practice — it is the error message a deploying consumer follows — and the package
  advertises `Framework :: Django :: 6.0`, so a lower public floor would let a Django 6.0 user
  follow the package's own error message into an unsupported install. **The claim this decision
  may no longer make:** that a declared floor and a dev-resolved floor may differ.

**Change record — Revision 2: the `[daphne]` extra.** The dev-group row became
`channels[daphne]>=4.3.2` rather than a bare `channels` pin, because
`channels/testing/__init__.py` unconditionally imports `.live`, whose module-level
`from daphne.testing import DaphneProcess` makes every import path to the (themselves
in-process, daphne-free) communicators fail without it. Expressing it as Channels' own extra
keeps the floor and the daphne compatibility in **one** dependency row instead of two
independently-drifting ones. The shipped `routers.py` never imports daphne and the install hint
stays channels-only.

**Change record — Revision 8: `require_optional_module` lost its `feature_label`.** The
primitive was drafted with a `feature_label` parameter alongside `install_hint`. It was dropped
as dead ceremony: the feature-specific text lives entirely in the caller's hint, which is how
`require_drf()` already passed its own.

**Change record — the floors left the hint strings (F6).** Helper-reuse **D2** described the
floor as text inside the hint constant. At HEAD the hint interpolates `CHANNELS_FLOOR` /
`STRAWBERRY_FLOOR` from [`utils/imports.py`][utils-imports]. **Rejected alternative, decided at
the time of that consolidation:** keeping the literal and adding a test that compares it against
`pyproject.toml`. Lost because a test that reads the metadata to check a string is a second
place to maintain, where one interpolation removes the drift entirely. **Direction of the
drift:** D2's *intent* is strengthened, not weakened — but the obligation as written pointed a
reader at the wrong file.

**Change record — first construction is serialized (F7).** The decision described only the
`_ROUTER_CLASS` module global. HEAD adds `_ROUTER_CLASS_LOCK` and the double-checked
`_build_router_class` / `_build_router_class_uncached` pair. **Why it does not weaken the
eviction contract** (Helper-reuse **D3**, and the absence tests that depend on it): both the
cache and the lock are module globals, so evicting `routers` from `sys.modules` still drops both
with the module, and the guard itself is still un-memoized.

### Decision 6 — Constructor and composition

Spec: [Decision 6][d6]. **This decision's heading changed in the reconciliation pass**, because
the old one literally stated the superseded signature:

> Decision 6 — Constructor parity: `(schema, django_application=None, url_pattern="^graphql")`;
> composition borrowed as-is

The old anchor was
`#decision-6--constructor-parity-schema-django_applicationnone-url_patterngraphql-composition-borrowed-as-is`;
the new one is `#decision-6--constructor-and-composition`. No document outside the spec cited
the old anchor (verified by sweeping `spec-041-channels_router-0_0_14.md#` across `docs/`,
`KANBAN.md` and `BACKLOG.md`), and every in-spec citation moved with it in the same pass. The
new heading deliberately names no signature, so a future parameter change cannot strand it
again.

**What this decision used to say, in full (F1).** The signature was held **byte-compatible**
with [`AuthGraphQLProtocolTypeRouter`][upstream-routers] — positional `schema`, keyword
`django_application=None`, keyword `url_pattern="^graphql"` — so that a migrating call site
changed zero characters after the import line. The composition was upstream's, verbatim:

- `http` → `AuthMiddlewareStack(URLRouter(http_urls))` where `http_urls` is the GraphQL
  `re_path(url_pattern, GraphQLHTTPConsumer.as_asgi(schema=schema))` followed by
  `re_path(r"^", django_application)` when provided.
- `websocket` → `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([
  re_path(url_pattern, GraphQLWSConsumer.as_asgi(schema=schema))])))`.

**Alternatives rejected at the time — every one of which the supersession later reversed or
mooted.** They are kept because they record *why the insecure shape was chosen deliberately*,
which is the context [`spec-046`][spec-046] Decision 5 reversed:

- **Making `django_application` required.** Rejected then: upstream's optional default supports
  the GraphQL-only ASGI process (a dedicated GraphQL service behind a router that sends
  everything else elsewhere); requiring it breaks that deployment and the byte-compatibility
  goal. **Reversed in full** by `spec-046` Decision 3 — the GraphQL-only ASGI process was
  precisely the deployment serving credential-accepting HTTP outside Django's middleware.
- **A `path`-style (non-regex) `url_pattern`.** Rejected then: `re_path` semantics are
  upstream's contract and the byte-compat goal pins them; a `graphql` regex also matches
  `/graphql/`, which a literal `path("graphql")` would not. **Partly reversed:** the parameter
  is still a regex, but its default is exact at both ends rather than a shared prefix
  (`spec-046` Decision 4), so the argument's premise — prefix matching is a feature — is gone.
- **Adding an `allowed_hosts=` / `enable_auth=` knob set.** Rejected then: upstream ships none;
  every knob is a divergence the migration-guide row would have to explain. **Still rejected,
  and for the same reason** — but the constructor did grow two knobs (`websocket_consumer_class`
  and `websocket_revalidation_window`, `spec-046` Decision 11), which are a consumer-injection
  trust seam and its freshness price rather than a re-spelling of the composition.

**The typing note, kept in the spec.** `django_application: ASGIHandler | None` under
`TYPE_CHECKING` rather than Strawberry core's `str | None`, which is simply wrong — the value is
an ASGI callable, and the package does not copy the typo. The `| None` half went with the
supersession; the reason not to copy the annotation did not.

### Decision 7 — Engine-owned consumers

Spec: [Decision 7][d7].

**Alternatives rejected.**

- **Subclassing the consumers to inject package context** (e.g. a request-normalization shim for
  the auth mutations). That is the auth-over-Channels work
  [Decision 2](#decision-2--card-scope-boundary) scoped out; doing it silently inside the router
  would change auth behavior with no card, no tests, and no GLOSSARY story. **Note how narrowly
  this was reversed:** [`spec-046`][spec-046] Decision 11 does subclass `GraphQLWSConsumer`, but
  to revalidate the session actor at two security checkpoints — under its own card, its own
  tests and its own glossary entries, which is exactly the condition this rejection named.
- **Vendoring upstream `strawberry_django`'s consumers.** Upstream's routers use Strawberry
  core's consumers too (verified — its imports are `strawberry.channels.handlers.*`); there is
  nothing `strawberry_django`-specific to vendor.

**Change record — Revision 8.** The Strawberry-floor gate was narrowed to the two symbols the
builder actually imports, explicitly **not** `GraphQLProtocolTypeRouter`: gating an unused
upstream export is unnecessary coupling.

**Change record — only one consumer is imported now (F4).** The decision named
`GraphQLHTTPConsumer` and `GraphQLWSConsumer`. HEAD imports `GraphQLWSConsumer` alone. **The
claim this decision may no longer make:** that the package defines *no* consumer subclass at
all. It defines exactly one, built by
`consumers.py::build_revalidating_consumer_class`, and the surviving
contract is the narrower and more useful one — the engine still owns request parsing and the WS
protocol state machines, and the package never re-implements them.

### Decision 8 — Test strategy

Spec: [Decision 8][d8].

**Alternatives rejected.**

- **Adding a fakeshop `asgi.py` + a Channels acceptance lane.** Rejected in
  [Decision 2](#decision-2--card-scope-boundary); additionally, the live suite's fixtures
  (session cookies, `create_users`, `CaptureQueriesContext`) are all WSGI-client-shaped — a
  parallel ASGI harness is a card of its own, not a rider.
- **Structural assertions only (no communicators).** It would leave the consumers' `as_asgi`
  wiring and the middleware ordering unexercised — precisely the lines a composition module
  exists for. If the composition is wrong (origin validator on the wrong branch, fallback before
  the GraphQL route), only traffic notices.
- **Uninstall-based absence testing (a separate no-channels CI job).** The DRF precedent already
  chose simulation (one env, one run, no matrix), and the repo's test invocation is a single
  `uv run pytest` gate.

**Change record — Revision 2: the restore became two-sided.** The absence fixture originally
saved and restored only the `sys.modules` entries. The blocked-then-retried import re-executes
`routers.py` and rebinds the parent package's `routers` attribute to a fresh module object, so
restoring only `sys.modules` would leave the attribute path and the import path holding two live
modules with independent class caches — an order-dependent identity flake under `pytest-xdist`.
The fixture now saves and restores the parent attribute alongside, putting the *original* module
object back in both places (the DRF fixture's defensive
`delattr(django_strawberry_framework, "SerializerMutation")` is the precedent), and Test 14
asserts the post-teardown same-object invariant.

**Change record — Revision 8: the degraded-install test reuses the same eviction.** Without
evicting `routers` first, an earlier construction test's cached `_ROUTER_CLASS` would satisfy
the symbol access and the blocked builder import would never fire — a no-op test that passes.

**Change record — the execution rows moved transport (F10).** The decision said the suite
executes "a POST through the `http` branch resolving against a real `strawberry.Schema`, and a
WebSocket handshake through the `websocket` branch". There is no `http` GraphQL branch to POST
through. The placement ruling itself — package tests only, because the fakeshop example is
WSGI-only and a Channels router is structurally unreachable from it — is unchanged and still
true.

### Decision 9 — Migration ergonomics

Spec: [Decision 9][d9].

**Alternatives rejected.**

- **Shipping a compatibility alias** (`AuthGraphQLProtocolTypeRouter = DjangoGraphQLProtocolRouter`).
  The alias *is* the impersonation the card forbids, just spelled as an assignment; it would
  also freeze upstream's name into the package's public surface one release before the
  API-freeze discipline starts caring.
- **Documenting the mapping only in this spec.** Specs are implementation contracts and may
  later archive; the durable migrant-facing home is the guide and, until then, the GLOSSARY. The
  card's own DoD names the guide row, so dropping it would fail the card.

**Change record — the handoff row's content is no longer a rename (F1).** The row was drafted as
`strawberry_django.routers.AuthGraphQLProtocolTypeRouter` →
`django_strawberry_framework.routers.DjangoGraphQLProtocolRouter`, "with the note that the
constructor signature is unchanged". The signature is not unchanged, and migration is no longer
an import swap: it is a recipe touching both the `asgi.py` call site and the URLconf
([`spec-046`][spec-046] Decisions 3, 4 and 6). **The claim this decision may no longer make:**
that a migrating call site changes zero characters. **What survives, and is why the decision is
not retired:** the migration story's single canonical home is still the guide row, not the
symbol name — the rename is documented rather than silently divergent, and the interim
migrant-facing surface is the [`docs/GLOSSARY.md`][glossary] entry plus the migration note in
[`docs/README.md`][docs-readme].

### Decision 10 — Joint-cut version ownership

Spec: [Decision 10][d10].

**Alternatives rejected.**

- **Bump to `0.0.14` in Slice 2.** Three siblings also shipped into `0.0.14`; a per-card bump
  races the joint cut and would be reconciled three times over.
- **Defer the lockfile regeneration to the joint cut too.** Slice 1's tests import `channels`; a
  dev-dependency without its lock entry breaks the reproducible-env contract the moment CI runs
  `uv sync`.

**Derivation, moved.** Per [`docs/SPECS/NEXT.md`][next] Step 3 / Step 6, when multiple cards
target one patch version the bump belongs to the joint cut rather than any individual card's
spec. Four cards targeted `0.0.14` and this was the first of them, so its slices left the
version line untouched. The joint cut landed; `0.0.14` released on 2026-08-29.

### Decision 11 — The Channels request contract

Spec: [Decision 11][d11].

**Alternatives rejected.**

- **Transport-only, docs-softening instead of the adapter.** Every `request_from_info()` caller
  fails under the Channels context, so "transport-only" quietly ships a router whose advertised
  sessions the package itself cannot read; the root-cause helper extension is small,
  channels-import-free, and testable in this card.
- **A narrow `.user` / `.session`-only adapter.** The filter / order `check_<field>_permission`
  hooks and DRF serializer overrides receive the resolved request and legitimately read
  `request.headers` / `.COOKIES` / `.path` / `.method`, so a two-field adapter would turn working
  consumer hooks into `AttributeError`s under Channels only. Wrapping and delegating is the same
  single-siting with the full contract intact.
- **Full auth-mutations-over-Channels support now.** `channels.auth` login/logout semantics are
  async session mutations against the scope — auth subsystem work, invisible in this card's S
  sizing.
- **Adapter in `routers.py`.** The context shape arrives with Strawberry's consumers, router or
  not; parking it in `routers.py` would make the fix reachable only through the soft-dependency
  module and couple the shared helper to it.
- **Switch the HTTP branch to `SyncGraphQLHTTPConsumer` so sync ORM resolvers are threadpooled.**
  Upstream's router used the async `GraphQLHTTPConsumer`, and the byte-compatible parity contract
  was this card's whole migration promise; the package's async twins are the supported ORM path
  under an async consumer. **Mooted rather than reversed:** there is no HTTP branch to switch,
  and the constraint now belongs to the equally-async WebSocket consumer.

**Derivation of the blast radius, moved.** Strawberry's Channels consumers hand resolvers a
**dict** context — `{"request": ChannelsRequest, "response": TemporalResponse}`, read in the
checked-out upstream (not first-party) at
`strawberry/channels/handlers/http_handler.py::GraphQLHTTPConsumer.get_context` and identical on
`::SyncGraphQLHTTPConsumer.get_context` — where `ChannelsRequest` is a dataclass wrapping
`consumer` + `body`. The package's
shared helper accepted only `info.context.request` or a bare `HttpRequest`, so a dict context
failed `getattr(context, "request", None)` and raised
[`ConfigurationError`][glossary-configurationerror]. That is not an auth-mutations problem: the
blast radius is every framework surface routed through the helper, and several of them hand the
resolved request straight into consumer-written code. A router that ships "the session
transport" while the package's own request contract rejects the transport's context would be an
incoherent integration.

**Change record — Revision 5 created this decision.** It did not exist in Revisions 1-4. The
maintainer review found that the transport alone was not enough for the package's own surfaces,
and the decision was added with the read path closed and the session-mutating path explicitly
deferred.

**Change record — Revision 8: the adapter wraps rather than replaces.** As drafted in Revision 5
the adapter was a narrow scope-backed object exposing `.user` and `.session`. Revision 8 made it
**wrap** the original `ChannelsRequest` and delegate every other attribute through `__getattr__`
— the second rejected alternative above is the retracted first draft. **The claim this decision
made and may no longer make:** that exposing the scope's `user` and `session` is a sufficient
request contract.

**Change record — a second scope shape and a contained read (F8).** The decision described the
HTTP consumer's `consumer.scope` shape only.
`utils/permissions.py::_channels_scope` now resolves the WebSocket
consumer's `request.scope` shape too — and since [`spec-046`][spec-046] removed the HTTP GraphQL
branch, that second shape is the one the package's own router produces. `_scope_value` also
contains a hostile scope mapping into a `ConfigurationError` instead of letting it escape raw.
Both extensions obey the decision's own rule rather than amending it.

**Change record — the deferral was discharged by `spec-040` (F9).** Point 2 deferred
session-mutating auth with the sharpened wording "the docs say `AuthMiddlewareStack` makes
`scope["user"]` available and the package's *read* surfaces consume it — never that the
package's session-mutating auth surfaces work over Channels". That wording was correct when it
shipped and is now under-stated: `auth/sessions.py` classifies the
transport and answers the capability question per transport. **The claim this decision may no
longer make:** that the package says nothing about `login` / `logout` over a Channels scope. It
says something precise — `login` is refused on any WebSocket, `logout` only on a
signed-cookie-engine WebSocket — and [`spec-040`][spec-040] owns it.

## Change record for the spec's non-decision sections

### `## Borrowing posture`

*Moved:* the comparison reasoning and the declined-borrowings list's derivations.

The card's `Verified in upstream` section names one file, read in full for the spec together
with the Strawberry-core router it sits beside (`strawberry/channels/router.py`, from the
checked-out venv). **The comparison between the two is what isolated this card's actual
value-add**: core's `GraphQLProtocolTypeRouter` composes the same consumers with the same
signature and **no** `AuthMiddlewareStack`, **no** origin validator. The delta is exactly the
Django-auth composition — which is why the package ships its own helper instead of pointing
consumers at the engine's: a Django-framework package whose auth mutations assume the session
user is resolvable should hand out the transport that makes that true.

**Declined borrowings, with the reasons.**

- **The hard `channels` import.** Upstream imports `channels.*` at module top level;
  `strawberry_django` can afford that because its consumers install it as the integration
  package. This package's floor is "importable with zero optional dependencies", proven by the
  DRF precedent.
- **The symbol name.** See [Decision 3](#decision-3--the-symbol-name).
- **`strawberry_django`'s consumers-and-auth coupling.** Upstream's `auth/` mutations reach into
  `request.consumer.scope` when the request is Channels-shaped; this card kept the package's
  auth surface request-shaped. (That boundary later moved — see F9 — but by classification in
  [`spec-040`][spec-040]'s own module, never by a consumer reaching into a scope.)

**Change record — the HTTP-branch and Django-fallback paragraphs are superseded.** See
`## Supersession` item 3. The borrowed HTTP composition and the appended `^` fallback describe a
branch the router no longer has.

### `## Problem statement` and `## Goals`

**Change record — Revision 4: the `GOAL.md` anchoring pass.** The parity paragraph gained the
observation that [`GOAL.md`][goal]'s own working reference — the cookbook `recipes/schema.py`
its "Cookbook parity" target example ports — is an HTTP-only Graphene schema with no ASGI /
Channels / subscription surface anywhere in it (read directly), independently corroborating the
single-upstream-parity claim. Goal 3 gained a citation of `GOAL.md` success criterion 7.

**Change record — that citation rotted from both ends (F1).** Goal 3 quoted criterion 7 as
migrate "without bringing the source package along — … only the import line changes". Criterion
7 today reads "The import-only promise covers `Meta`-driven domain declarations; project-level
engine configuration (`extensions=`, the `GRAPHENE` settings block) migrates by documented
recipe" — the quoted clause is gone from `GOAL.md`, and the one-line migration it promised is
gone from the router. The spec now states the migration axis without the quotation.

### `## Current state`

Its vintage framing licenses dated **observations** of the pre-build repo, so falsified
observations stay — the section header dates them. Three are falsified and kept deliberately:
"No `routers.py` exists", "`channels` is installed nowhere", and "The version line reads
`0.0.13`". One sentence is kept for a sharper reason: "its presence back at the pinned
`strawberry-graphql>=0.262.0` floor is upstream history, spot-checked at the dependency gate"
records what was true on its date and makes no claim about live code, which is exactly the
carve-out [`spec-046`][spec-046] Decision 14 named.

**Change record — Revision 3.** Two `docs/TREE.md` row quotations were updated
`TODO-ALPHA-041` → `WIP-ALPHA-041` (the Slice-2 board re-render moved the annotation with the
card id; the substance — the row is reserved — was already correct), and the intro's "~30-line
module" was tightened to "~30 lines of composition", the upstream file being 73 lines with a
~30-line class body.

### `## Edge cases and constraints`

**Change record — Revision 2: the conftest attribution was withdrawn.** The communicator-test
DB-connection edge case originally credited the [`tests/conftest.py`][tests-conftest] cleanup
fixture. That fixture deliberately tracks only connections opened under a running event loop,
while Channels' `database_sync_to_async` runs ORM code on a no-loop executor thread — the
category the fixture's own comment leaves untouched. The actual mechanism is Channels'
`DatabaseSyncToAsync` bracketing every call with `close_old_connections()` (verified in
`channels/db.py`). **The claim the edge case may no longer make:** that the repo's own conftest
fixture covers this.

**Change record — Revision 2: the localhost fallback is Channels' list, not Django's.** The
empty-`ALLOWED_HOSTS`-under-`DEBUG` localhost set is hardcoded in
`channels/security/websocket.py`, mirroring Django's runserver behavior rather than coming from
Django itself.

**Change record — Revision 3: that fallback is unreachable in this suite.** pytest-django
defaults `DEBUG=False` and Django's `setup_test_environment` appends `"testserver"` to
`ALLOWED_HOSTS`, so the WebSocket test's matching `Origin` is `http://testserver`, never the
localhost set.

**Change record — Revision 5: the threadpooling claim was false and was removed.** The spec had
said sync resolvers ride `database_sync_to_async` under `GraphQLHTTPConsumer`. The wrapper
exists only on `SyncGraphQLHTTPConsumer.run` (verified at the installed strawberry `0.316.0`).
**A claim the spec made and may not make again**, in either the HTTP or the WebSocket form.

**Change record — Revision 8: the HTTP fallback inside `AuthMiddlewareStack` was documented as
accepted parity**, and the missing-`Origin` denial was documented and added as a third
origin-validator test direction (verified against `channels/security/websocket.py`:
`if parsed_origin is None and "*" not in self.allowed_origins: return False`).

**Change record — four paragraphs described a removed branch (F11).** The `^graphql`
prefix-semantics paragraph, the HTTP-fallback-inside-`AuthMiddlewareStack` paragraph (the very
one Revision 8 had just documented as accepted parity), the async-HTTP-consumer paragraph and
the multipart paragraph all described the `http` GraphQL branch. Two were rewritten onto the
WebSocket branch because the constraint survived its transport; two were retired to the owners
[`spec-046`][spec-046] Decisions 4, 17 and 18 gave them. **Rejected alternative:** deleting all
four, on the ground that spec-046 owns the subject now. Lost because two of them state
constraints a `spec-041` reader still hits — sync ORM under the router's transport, and where
uploads actually go — and a spec that answers neither sends the reader to guess.

### `## Test plan`

**Change record — Revision 2: Test 13 pins a re-typed literal.** The corrected floor is matched
against a literal typed independently in the test file (the `test_soft_dependency.py`
`_HINT_SUBSTRING` discipline). A test importing `_CHANNELS_INSTALL_HINT` and asserting the
constant against itself could never notice the hint drifting away from the dev-group floor.

**Change record — Revision 3: Test 4's isinstance target.** `AllowedHostsOriginValidator` (and
`AuthMiddlewareStack`) are factory *functions*, not classes. The isinstance target is the
returned `OriginValidator` instance, whose outermost hop is `.application`.

**Change record — Revision 4: which layers carry `.inner`.** "The `BaseMiddleware` layers beneath
carry `.inner`" was a wrong classification. `AuthMiddlewareStack` composes
`CookieMiddleware(SessionMiddleware(AuthMiddleware(inner)))` and only `AuthMiddleware` subclasses
`BaseMiddleware` (verified in `channels/auth.py` / `channels/sessions.py` at the `4.2.1` tag);
the outer two are plain classes that also carry `.inner`, so an isinstance-on-`BaseMiddleware`
walk would fail on them.

**Change record — Revision 5: Test 1 was demoted, and structural walks were isolated.** The
exact `application_mapping` assertion was reframed as a **current-shape parity assertion**
subordinate to the behavior tests, so a deliberate future addition moves it with a recorded
decision rather than failing mysteriously. The structural walks moved behind the intent-named
`unwrap_origin_validator()` / `unwrap_auth_stack()` helpers, so a Channels internal reshape
changes one helper rather than several tests.

**Change record — Revision 8: Test 10 uses a recording extension.** Schema pass-through is
proven with a custom Strawberry extension that records it executed, kept ORM-free and
`DjangoType`-free so it cannot trip `SynchronousOnlyOperation` under the async consumer.
`DjangoOptimizerExtension` is deliberately out of that execution test: a trivial
optimizer-installed schema proves nothing about the optimizer anyway.

**Change record — Revision 8: Test 18 was added to earn a claim.** The repeated "session user on
the scope" claim rested on nothing until an authenticated-session round trip existed. Test 16
only proves the contract does not raise.

**Change record — four rows retired, two moved transport (F10).** See the finding. **Why the
retired rows are not a coverage gap:** each asserted the HTTP GraphQL branch, and its removal is
now pinned positively by a test that asserts the consumer left the module entirely.

### Risks and open questions

*Moved in full.* Every entry was a preferred-answer / fallback pair about a question the build
has since answered, and three of the four preferred answers landed.

- **The channels floor was metadata-grounded, not yet suite-verified.** `4.3.2` was chosen from
  PyPI metadata (first release with the Django 6.0 classifier) with the Slice-1 gate to install
  it and run the suite before the hint string froze. **Preferred answer:** `4.3.2` holds and all
  naming sites ship with it. **Fallback:** the gate moves all sites together to whatever the
  suite proves — the three-places-that-must-agree rule existing precisely so that is one edit
  rather than a drift. *Outcome:* the preferred answer held.
- **Auth *mutations* over Channels remained the open half.** With Decision 11 the read path was
  closed in this card. The mutating path was left open with a named owner: the `TestClient` card
  if it absorbed it, otherwise a dedicated follow-on card. The evidence that it needed real
  adaptation rather than just the adapter was strong — Channels ships its own async
  `channels.auth.login()` / `logout()` because the session semantics differ, and upstream carries
  a `channels_auth` fallback for the same reason. *Outcome:* neither named owner took it.
  [`spec-040`][spec-040]'s own post-ship hardening did, and it confirmed the risk's reading —
  the mutating path needed a transport classification and per-transport capability answers, not
  an adapter (F9).
- **The authenticated-session test might need a careful async-safe harness.** **Preferred
  answer:** the test lands and the "session user on the scope" wording stays, now earned.
  **Fallback:** keep Test 16 and weaken the user-facing wording to "the card composes
  `AuthMiddlewareStack` and proves the package can read the Channels request shape; full
  authenticated session-cookie behavior is delegated to Channels and not asserted by this card",
  with the gap tracked. The wording and the test were to move together; the docs never claim
  more than the suite proves. *Outcome:* the preferred answer held, and the row survived
  [`spec-046`][spec-046]'s protocol split by moving onto the WebSocket handshake.
- **The card's name hedge.** Recorded under [Decision 3](#decision-3--the-symbol-name).
- **`ProtocolTypeRouter` internals as an assertion target.** Channels' middleware factories and
  classes are stable public API but the attribute names are not contractual; if a Channels
  release reshapes them the structural tests get noisy while the communicator tests keep the
  truth. **Preferred posture:** keep both layers — the structural tests name the intent, the
  communicator tests hold the behavior — with the walk isolated behind the intent-named helpers
  so a reshape is absorbed by updating one helper, gate-visible either way. *Outcome:* the
  posture held and the suite still carries both layers.

### `## Doc updates` and the Slice-2 wrap

**Change record — the slice's own predictions are discharged.** The GLOSSARY entry body was
rewritten to the implemented contract and its status has since flipped to `shipped (0.0.14)`;
[`docs/TREE.md`][tree] was regenerated; the kanban card wrapped to `DONE-041-0.0.14`; and the
joint cut took the version quintet, the README "Coming next" moves and the `CHANGELOG.md`
bullets. The spec states the obligations without the prediction tense.

**Deferred, and recorded here rather than edited.** The spec carries stale kanban card
*numerals* for two Beta cards — the fakeshop-activation card (`TODO-BETA-062-0.1.5`, **two**
occurrences in the spec; the live card is `TODO-BETA-066-0.1.5`) and the migration-guides card
(`TODO-BETA-068-0.1.8`, **three** occurrences; the live card is `TODO-BETA-071-0.1.8`). Both
belong to the board's own archived-spec card-id sweep, which explicitly requires one pass over
the whole population rather than a per-spec share of it; renumbering `spec-041`'s share alone
would be the partial fix that item warns against.

Those are the sweepable spec-side figures, and they are lower than the spec once held — three
and four — because the extraction moved two enclosing passages out of the spec and condensed
both without their numeral: the `062` mention inside Decision 2's rejected alternative, and the
`068` mention inside a revision-log entry. Neither numeral survives in this file's own body
except in the paragraph above, which quotes each one inside a sentence declaring it stale — the
same class the board excludes from its own sweepable total. A later custodian sweeping this
population should therefore expect five renumberable sites in the pair, not seven.

The three `0.0.14` sibling cards named in this spec were a different case — a lifecycle prefix
rather than a renumber, and not part of that population — so they read `DONE-` here.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../../GOAL.md
[pyproject]: ../../../pyproject.toml

<!-- docs/ -->
[docs-readme]: ../../README.md
[glossary]: ../../GLOSSARY.md
[glossary-configurationerror]: ../../GLOSSARY.md#configurationerror
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[d1]: ../spec-041-channels_router-0_0_14.md#decision-1--spec-filename-and-canonical-naming
[d10]: ../spec-041-channels_router-0_0_14.md#decision-10--version-bumps-are-owned-by-the-joint-0014-cut
[d11]: ../spec-041-channels_router-0_0_14.md#decision-11--the-package-request-contract-works-under-channels-request_from_info-learns-the-channels-context-shape-reads-auth-mutations-stay-deferred
[d2]: ../spec-041-channels_router-0_0_14.md#decision-2--card-scope-boundary-the-transport-router-ships-websocket-auth-semantics-and-fakeshop-asgi-stay-out
[d3]: ../spec-041-channels_router-0_0_14.md#decision-3--the-symbol-is-djangographqlprotocolrouter--distinctly-ours-pinned-now
[d4]: ../spec-041-channels_router-0_0_14.md#decision-4--module-and-test-locations-a-top-level-routerspy-mirroring-both-upstreams-teststest_routerspy
[d5]: ../spec-041-channels_router-0_0_14.md#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard
[d6]: ../spec-041-channels_router-0_0_14.md#decision-6--constructor-and-composition
[d7]: ../spec-041-channels_router-0_0_14.md#decision-7--the-consumers-come-from-strawberrychannels-engine-owned-not-package-owned
[d8]: ../spec-041-channels_router-0_0_14.md#decision-8--test-strategy-package-tests-only-communicator-driven-execution-eviction-simulated-absence
[d9]: ../spec-041-channels_router-0_0_14.md#decision-9--migration-ergonomics-live-in-the-migration-guide-row-not-the-symbol-name
[next]: ../NEXT.md
[s46-d14]: ../spec-046-transport_security-0_0_14.md#decision-14--this-card-amends-spec-041-and-supersedes-three-of-its-decisions
[spec-040]: ../spec-040-auth_mutations-0_0_13.md
[spec-041]: ../spec-041-channels_router-0_0_14.md
[spec-046]: ../spec-046-transport_security-0_0_14.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->
[utils-imports]: ../../../django_strawberry_framework/utils/imports.py

<!-- tests/ -->
[tests-conftest]: ../../../tests/conftest.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-routers]: ../../../../strawberry-django-main/strawberry_django/routers.py
