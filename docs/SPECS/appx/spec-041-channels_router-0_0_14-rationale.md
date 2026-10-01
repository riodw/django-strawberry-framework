# Rationale: spec-041 — Channels ASGI router (rejected alternatives and derivations)

Deliberative companion to [`spec-041-channels_router-0_0_14.md`][spec-041]. The spec is the
contract and states what the code does; this file holds the alternatives each decision
rejected, with the reason each lost, and the derivations that do not change how a decision is
implemented. One entry per spec decision, named by the decision's own heading and linked to its
anchor. Where this file and the spec disagree, the spec is the contract.

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

- **Fold full auth-over-Channels verification into this card.** The *request-shape* half (the
  `request_from_info()` read contract) is in this card, as
  [Decision 11](#decision-11--the-channels-request-contract) — leaving it out would ship a router
  the package's own helpers reject. The session-*mutating* half (login / logout semantics over
  `channels.auth`) is real auth-subsystem work with its own failure modes, invisible in the
  card's S sizing; [`spec-040`][spec-040]'s `auth/sessions.py` owns it.
- **Add the fakeshop `asgi.py` for dogfooding.** It drags `channels` into the example's runtime
  and the live suite is WSGI `django.test.Client` — the new surface would be dead weight until a
  Channels-aware acceptance harness exists.

### Decision 3 — The symbol name

Spec: [Decision 3][d3].

**Alternatives rejected.**

- **`AuthGraphQLProtocolTypeRouter` verbatim.** Rejected by the card itself: the module would
  impersonate the upstream API — the [`GOAL.md`][goal] "thin wrapper" non-goal. Migration
  ergonomics live in the guide row instead
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
- **No submodule `__all__`.** Without it, `from ...routers import *` would leak the helper names
  into the consumer's namespace; with it, a submodule star import deliberately opts into the
  guard.

**Derivation of the name.** The card pre-pinned the architectural posture ("must use a
**distinctly-ours symbol name** (working name: `DjangoGraphQLProtocolRouter`) so the module is
unambiguously ours and does not impersonate the upstream API"). The name reads as the package's
own family (`Django*` prefix), drops upstream's `Auth` prefix (the auth stack is part of the
composition, not the headline) and upstream's `Type` infix (`ProtocolTypeRouter` is Channels'
internal naming; the package's consumer never thinks about "protocol types").

### Decision 4 — Module and test locations

Spec: [Decision 4][d4].

**Alternatives rejected.**

- **A `channels/` or `integrations/` subpackage.** One class does not justify a package;
  upstream keeps it flat. `strawberry_django`'s `integrations/` holds third-party *library*
  adapters (guardian), not transport.
- **Colocating the guard in `rest_framework/__init__.py` as a generic
  `require_soft_dependency(name, hint)`.** The single optional-import owner is
  [`utils/imports.py`][utils-imports], so `require_optional_module(module_name, *, install_hint)`
  lives there and `require_channels()` is a thin wrapper over it, never a fourth hand-rolled
  import pattern. A DRF-specific module is the wrong home for a primitive every soft
  dependency shares.

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
  thing to document without removing any code. The DRF precedent (no `[drf]` extra) set this.
- **A module-import-time guard** (`require_channels()` at `routers.py` top level, the literal
  `rest_framework/__init__.py` shape). It makes `import django_strawberry_framework.routers`
  itself raise, which (a) breaks innocent whole-package walkers — the [`docs/TREE.md`][tree]
  docstring renderer, coverage tooling, IDE indexers — on a channels-less machine, and (b)
  contradicts the card's own DoD wording ("top-level package import must not fail... raises
  `ImportError` with an install hint **when it is actually called**"). The `rest_framework/`
  package can afford import-time because its import is itself the opt-in; a top-level module
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
- **A declared floor lower than the dev-resolved one.** The install hint is public API in
  practice — it is the error message a deploying consumer follows — and the package advertises
  `Framework :: Django :: 6.0`, so a floor below the first 6.0-classifying Channels release would
  let a Django 6.0 user follow the package's own error message into an unsupported install. One
  floor serves the dev group, the hint and the test literal.
- **A bare `channels` dev-group pin plus a separate `daphne` row.** `channels/testing/__init__.py`
  unconditionally imports `.live`, whose module-level `from daphne.testing import DaphneProcess`
  makes every import path to the (themselves in-process, daphne-free) communicators fail without
  it. Channels' own `[daphne]` extra keeps the floor and the daphne compatibility in one
  dependency row instead of two independently-drifting ones.
- **A `feature_label` parameter on `require_optional_module`.** Dead ceremony: the
  feature-specific text lives entirely in the caller's hint, which is how `require_drf()` passes
  its own.
- **A literal floor inside the hint string, checked by a test that reads `pyproject.toml`.** A
  test that reads the metadata to check a string is a second place to maintain; interpolating
  `CHANNELS_FLOOR` / `STRAWBERRY_FLOOR` from [`utils/imports.py`][utils-imports] removes the drift
  entirely, leaving [`pyproject.toml`][pyproject] as the one other written copy.
- **An unsynchronized class cache.** Two threads reaching for the symbol at once could build two
  router classes, and two class identities make `isinstance` lie; the module-global lock with a
  re-check inside it costs nothing after the first build and, being a module global, is dropped
  with the module on eviction like the cache itself.

### Decision 6 — Constructor and composition

Spec: [Decision 6][d6].

**Alternatives rejected.**

- **A `path`-style (non-regex) `websocket_url_pattern`.** `re_path` semantics are Channels'
  routing idiom and upstream's contract, and one regex (`^graphql/?$`) matches both `/graphql`
  and `/graphql/`, which a literal `path("graphql")` would not.
- **An `allowed_hosts=` / `enable_auth=` knob set.** Upstream ships none; every knob is a
  divergence the migration-guide row would have to explain, and the Host and Origin policy is
  already Django's `ALLOWED_HOSTS`. The two WebSocket keywords the constructor does carry
  (`websocket_consumer_class`, `websocket_revalidation_window`) are [`spec-046`][spec-046]
  Decision 11's consumer-injection trust seam and its freshness price, not a re-spelling of the
  composition.

**Typing note.** `django_application: ASGIHandler` under `TYPE_CHECKING`, not Strawberry core's
`str | None`, which is simply wrong — the value is an ASGI callable, and the package does not
copy the annotation.

### Decision 7 — Engine-owned consumers

Spec: [Decision 7][d7].

**Alternatives rejected.**

- **Subclassing the consumers to inject package context** (e.g. a request-normalization shim for
  the auth mutations). That is the auth-over-Channels work
  [Decision 2](#decision-2--card-scope-boundary) scopes out; doing it inside the router would
  change auth behavior with no card, no tests, and no GLOSSARY story. The one consumer subclass
  the package defines, `consumers.py::build_revalidating_consumer_class`'s, revalidates the
  session actor under [`spec-046`][spec-046] Decision 11's own card, tests and glossary entries —
  exactly the condition this rejection names.
- **Vendoring upstream `strawberry_django`'s consumers.** Upstream's routers use Strawberry
  core's consumers too (its imports are `strawberry.channels.handlers.*`); there is nothing
  `strawberry_django`-specific to vendor.
- **Gating Strawberry core's `GraphQLProtocolTypeRouter` at the floor.** The builder never
  imports it, and gating an unused upstream export is unnecessary coupling; the floor gate covers
  the `strawberry.channels` consumer the builder actually imports.

### Decision 8 — Test strategy

Spec: [Decision 8][d8].

**Alternatives rejected.**

- **Adding a fakeshop `asgi.py` + a Channels acceptance lane.** Rejected in
  [Decision 2](#decision-2--card-scope-boundary); additionally, the live suite's fixtures
  (session cookies, `create_users`, `CaptureQueriesContext`) are all WSGI-client-shaped — a
  parallel ASGI harness is a card of its own, not a rider.
- **Structural assertions only (no communicators).** It would leave the consumer's `as_asgi`
  wiring and the middleware ordering unexercised — precisely the lines a composition module
  exists for. If the composition is wrong (origin validator on the wrong branch, auth stack
  outside the origin check), only traffic notices.
- **Uninstall-based absence testing (a separate no-channels CI job).** The DRF precedent chose
  simulation (one env, one run, no matrix), and the repo's test invocation is a single
  `uv run pytest` gate.
- **A one-sided restore (`sys.modules` only).** The blocked-then-retried import re-executes
  `routers.py` and rebinds the parent package's `routers` attribute to a fresh module object, so
  restoring only `sys.modules` would leave the attribute path and the import path holding two
  live modules with independent class caches — an order-dependent identity flake under
  `pytest-xdist`.
- **A degraded-install test without the eviction.** An earlier construction test's cached
  `_router_class` would satisfy the symbol access and the blocked builder import would never
  fire — a no-op test that passes.

### Decision 9 — Migration ergonomics

Spec: [Decision 9][d9].

**Alternatives rejected.**

- **Shipping a compatibility alias** (`AuthGraphQLProtocolTypeRouter = DjangoGraphQLProtocolRouter`).
  The alias *is* the impersonation the card forbids, just spelled as an assignment; it would
  also freeze upstream's name into the package's public surface.
- **Documenting the mapping only in this spec.** Specs are implementation contracts; the durable
  migrant-facing home is the guide and, until then, the GLOSSARY entry plus the migration note in
  [`docs/README.md`][docs-readme]. The card's own DoD names the guide row, so dropping it would
  fail the card.

### Decision 10 — Joint-cut version ownership

Spec: [Decision 10][d10].

**Alternatives rejected.**

- **Bump to `0.0.14` in Slice 2.** Three siblings also shipped into `0.0.14`; a per-card bump
  races the joint cut and would be reconciled three times over.
- **Defer the lockfile regeneration to the joint cut too.** Slice 1's tests import `channels`; a
  dev-dependency without its lock entry breaks the reproducible-env contract the moment CI runs
  `uv sync`.

### Decision 11 — The Channels request contract

Spec: [Decision 11][d11].

**Alternatives rejected.**

- **Transport-only, docs-softening instead of the adapter.** Every `request_from_info()` caller
  would fail under the Channels context, so "transport-only" ships a router whose advertised
  sessions the package itself cannot read; the root-cause helper extension is small,
  channels-import-free, and testable in this card.
- **A narrow `.user` / `.session`-only adapter.** The filter / order `check_<field>_permission`
  hooks and DRF serializer overrides receive the resolved request and legitimately read
  `request.headers` / `.COOKIES` / `.path` / `.method`, so a two-field adapter would turn working
  consumer hooks into `AttributeError`s under Channels only. Wrapping and delegating is the same
  single-siting with the full contract intact.
- **Full auth-mutations-over-Channels support in this card.** `channels.auth` login/logout
  semantics are async session mutations against the scope — auth subsystem work, invisible in
  this card's S sizing, and owned by [`spec-040`][spec-040].
- **Adapter in `routers.py`.** The context shape arrives with Strawberry's consumers, router or
  not; parking it in `routers.py` would make the fix reachable only through the soft-dependency
  module and couple the shared helper to it.

**Derivation of the HTTP-consumer shape.** Strawberry's Channels HTTP consumer hands resolvers a
**dict** context — `{"request": ChannelsRequest, "response": TemporalResponse}`
(`strawberry/channels/handlers/http_handler.py`, upstream) — where `ChannelsRequest` is a
dataclass wrapping `consumer` + `body`, so its scope is at `request.consumer.scope`. The
WebSocket consumer supplies *itself* as the context request, with the scope at `request.scope`.
Both are duck-typed shapes, which is why the helper recognizes them without importing
`channels`.

## Borrowing posture

The card's `Verified in upstream` section names one file, read in full for the spec together
with the Strawberry-core router it sits beside (`strawberry/channels/router.py`). **The
comparison between the two is what isolates this card's actual value-add**: core's
`GraphQLProtocolTypeRouter` composes the same consumers with the same signature and **no**
`AuthMiddlewareStack`, **no** origin validator. The delta is exactly the Django-auth
composition — which is why the package ships its own helper instead of pointing consumers at
the engine's: a Django-framework package whose auth mutations assume the session user is
resolvable should hand out the transport that makes that true.

**Declined borrowings, with the reasons.**

- **The hard `channels` import.** Upstream imports `channels.*` at module top level;
  `strawberry_django` can afford that because its consumers install it as the integration
  package. This package's floor is "importable with zero optional dependencies", proven by the
  DRF precedent.
- **The symbol name.** See [Decision 3](#decision-3--the-symbol-name).
- **`strawberry_django`'s consumers-and-auth coupling.** Upstream's `auth/` mutations reach into
  `request.consumer.scope` when the request is Channels-shaped; the package's auth surface
  classifies the resolved request by transport in [`spec-040`][spec-040]'s own module, never by
  a consumer reaching into a scope.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../../GOAL.md
[pyproject]: ../../../pyproject.toml

<!-- docs/ -->
[docs-readme]: ../../README.md
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
[spec-040]: ../spec-040-auth_mutations-0_0_13.md
[spec-041]: ../spec-041-channels_router-0_0_14.md
[spec-046]: ../spec-046-transport_security-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[utils-imports]: ../../../django_strawberry_framework/utils/imports.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
