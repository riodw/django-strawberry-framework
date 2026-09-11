# Spec: Channels ASGI router — `DjangoGraphQLProtocolRouter` in a soft-`channels` `routers.py`, the package's GraphQL WebSocket transport

Shipped in `0.0.14` (card [`DONE-041-0.0.14`][kanban]). This card adds the
package's **Channels transport helper**: a `django_strawberry_framework/routers.py`
module exposing `DjangoGraphQLProtocolRouter` — a `channels.routing.ProtocolTypeRouter`
subclass that is the consumer's whole ASGI entrypoint. Its `"http"` value **is** the
project's own Django ASGI application, dispatched directly; its `"websocket"` value is
the package's GraphQL WebSocket composition, with Django's `AuthMiddlewareStack` (so
`scope["user"]` and the session machinery are present on the socket) and Channels'
`AllowedHostsOriginValidator` (the WebSocket origin check) composed in. It is a
Required 🍓 `strawberry-graphql-django` parity item (the card's own tag):
[`strawberry_django/routers.py`][upstream-routers] ships
`AuthGraphQLProtocolTypeRouter`, a module whose class is ~30 lines of composition and the **single import**
making ASGI / WebSocket migration painless — without an equivalent, a
`strawberry-graphql-django` migrant using Channels loses their one-line ASGI
entrypoint and must hand-compose `ProtocolTypeRouter` / `URLRouter` /
`AuthMiddlewareStack` / `AllowedHostsOriginValidator` over Strawberry's Channels
consumers themselves. This card exists **primarily to reduce migration friction, not
to expand the API surface** (the card's own "Why it matters"); `graphene-django`
ships no Channels router at all, so this is honest single-upstream parity, the same
posture [`spec-040`][spec-040] took for the auth module.

**The protocol split is [`spec-046`][spec-046]'s, and this spec states it rather than
owning it.** That card (transport security) took HTTP away from the router entirely —
GraphQL over HTTP is the package's own Django view,
[`views.py::DjangoGraphQLView`][views], declared in the consumer's URLconf — made
`django_application` required, renamed `url_pattern` to `websocket_url_pattern` with
exact matching, added the [WebSocket Host boundary][consumers] outside Channels' origin
check, and added the `websocket_consumer_class` injection seam with its revalidating
package default. Those five surfaces belong to `spec-046`; the shape they leave behind
is described here only as far as a `routers.py` reader needs it, and the contract is
`spec-046`'s to state.

The helper is deliberately **thin and engine-riding**: the GraphQL WebSocket consumer
comes from Strawberry core (`strawberry.channels`'s `GraphQLWSConsumer` — inside the
package's pinned `strawberry-graphql>=0.316.0` floor), the routing
and middleware layers (classes and factory functions) come from `channels`, and the package contributes exactly the
composition — under a **distinctly-ours symbol
name** ([Decision 3](#decision-3--the-symbol-is-djangographqlprotocolrouter--distinctly-ours-pinned-now)).
`channels` is a **[soft dependency][glossary-soft-dependency]**
([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)):
`import django_strawberry_framework` and `import django_strawberry_framework.routers`
both succeed without it, and the install-hint `ImportError` fires only when a
consumer actually reaches for the router symbol — the generalization of the
[`SerializerMutation`][glossary-serializermutation] soft-DRF pattern
([`spec-039`][spec-039] Decision 12) to a second optional integration. The HTTP half
of the transport needs none of it: [`views.py`][views] is channels-free, so a
WSGI-only project adopts the GraphQL view without the soft dependency.

**Version boundary** (see
[Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)): this
card **shares the `0.0.14` patch line** with three sibling cards —
[`DONE-042-0.0.14`][kanban] ([Debug-toolbar
middleware][glossary-debug-toolbar-middleware]), [`DONE-043-0.0.14`][kanban]
([`TestClient`][glossary-testclient] / [`GraphQLTestCase`][glossary-graphqltestcase]),
and [`DONE-044-0.0.14`][kanban] ([Response-extensions debug
middleware][glossary-response-extensions-debug-middleware]) — so the
`pyproject.toml` / `__version__` /
[`tests/base/test_init.py::test_version`][test-base-init] bump from `0.0.13` to
`0.0.14` is owned by the **[joint `0.0.14` cut][glossary-joint-version-cut]** (the
last `0.0.14` card to land), not
by this card — the same shared-cut posture [`spec-039`][spec-039] Decision 14 took
for the joint `0.0.13` cut. No slice below bumps the version.

Status: **COMPLETE** (card `DONE-041-0.0.14`) — both slices built, the card wrap landed,
and the `0.0.14` release rode the joint cut. Where later cards changed what this one
shipped, this spec states the current contract directly; what changed, when and why is
the [rationale companion][rationale]'s job.
Two slices (the card is a deliberate S): Slice 1 (**the dependency gate +
`routers.py` + `tests/test_routers.py`** — the `channels` dev-group add with the
lockfile regenerated, the soft-dependency guard, the router class, and both the
channels-present and channels-absent test paths land in one commit), and Slice 2
(**docs + card wrap** — the implemented-contract doc updates, the regenerated
[`docs/TREE.md`][tree], and the kanban card flip; the release-status wording and the
version bump stay deferred to the joint cut).

Owner: package maintainer.

Predecessors: [`spec-040-auth_mutations-0_0_13.md`][spec-040] (the
most-recently-shipped spec at authoring time and the canonical voice / depth /
section-layout reference; also the card whose [Auth mutations][glossary-auth-mutations]
surface explicitly deferred "Channels / websocket auth" to **this** router card — a
handoff this spec scopes honestly in
[Decision 2](#decision-2--card-scope-boundary-the-transport-router-ships-websocket-auth-semantics-and-fakeshop-asgi-stay-out));
[`spec-039-serializer_mutations-0_0_13.md`][spec-039] (the soft-dependency
architecture this card generalizes — the single `require_*()` guard with one
install-hint string, the dev-group + lockfile dependency gate, the
[absence-simulated-by-eviction][glossary-eviction-simulated-absence] test
discipline, and the joint-cut version Decision
this spec mirrors); [`spec-021-apps-0_0_7.md`][spec-021] (the package's
Django-integration surface conventions the new top-level module sits beside).
[`docs/GLOSSARY.md`][glossary] carries
[`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] as
`shipped (0.0.14)`, with the entry body Slice 2 wrote and later cards extended.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary
used throughout the spec:

- [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] — the
  subject, and the entry that carries the implemented contract end to end: the
  constructor, the direct-dispatch `"http"` value, the WebSocket wrapper chain, the
  soft-dependency behavior matrix, and a symbol name intentionally distinct from
  `strawberry-django`'s `AuthGraphQLProtocolTypeRouter`. Read it before this spec when
  what you want is the shape rather than the reasoning.
- [`SerializerMutation`][glossary-serializermutation] — the soft-dependency
  precedent. Its `require_drf()` guard, single install-hint string, lazy
  name-resolution through a PEP 562 `__getattr__`, and eviction-simulated absence
  tests are the architecture
  [Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)
  generalizes.
- [Soft dependency][glossary-soft-dependency] — the pattern itself, named: one
  `require_*()` guard over the `utils/imports.py` optional-import owner, one
  install-hint constant, PEP 562 lazy resolution, eviction-simulated absence
  tests, and the dev-group + lockfile dependency gate. `channels` becomes the
  package's second instance.
- [PEP 562 lazy export][glossary-pep-562-lazy-export] — the lazy-resolution
  mechanism itself: why a submodule star import fires the guard (`__all__`
  names the lazy symbol, and `import *` calls `getattr` per entry) while the
  root package stays channels-free, and why the `__all__` line carries a
  scoped `# noqa: F822` (the name is never a static module global).
- [Eviction-simulated absence][glossary-eviction-simulated-absence] — the test
  discipline for both dependency states: the `builtins.__import__` block +
  strict `sys.modules` eviction with the **two-sided** (parent-attribute)
  restore, reused by the degraded-install path so the re-executed module has
  no cached `_ROUTER_CLASS`.
- [`require_optional_module`][glossary-require-optional-module] — the Slice-1
  primitive added to [`utils/imports.py`][utils-imports] (module name +
  keyword-only `install_hint`, no `feature_label`); `require_channels()` is a
  thin wrapper over it, never a fourth hand-rolled import pattern.
- [`request_from_info`][glossary-request-from-info] — the shared
  request-resolution helper every framework surface routes through; the
  [Decision 11](#decision-11--the-package-request-contract-works-under-channels-request_from_info-learns-the-channels-context-shape-reads-auth-mutations-stay-deferred)
  subject. This card teaches it the Strawberry-Channels context shape (reads
  only) under the hard no-local-decoders rule (Helper-reuse D-P2).
- [Channels request adapter][glossary-channels-request-adapter] — what the
  helper returns for that shape: a wrapper exposing `.user` / `.session` /
  `.scope` from the ASGI scope — reached through `consumer.scope` or directly,
  depending on which consumer supplied the context — and delegating every other
  attribute to the wrapped request, so consumer hooks keep the full request
  contract under Channels.
- [Joint version cut][glossary-joint-version-cut] — why no slice here bumps the
  version: four cards share `0.0.14`, and the last to land owns the version
  quintet and the release-status flips
  ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).
- [Live-first coverage mandate][glossary-live-first-coverage-mandate] — the
  test-placement rule
  [Decision 8](#decision-8--test-strategy-package-tests-only-communicator-driven-execution-eviction-simulated-absence)
  answers: `routers.py` is the documented genuinely-unreachable-live case (the
  fakeshop example is WSGI-only), so the tests live in `tests/test_routers.py`.
- [Auth mutations][glossary-auth-mutations] — the shipped `0.0.13` session-auth
  surface whose GLOSSARY entry deferred "Channels / websocket auth" to this card. The
  router's `AuthMiddlewareStack` is what puts the session user on the Channels
  scope, and this card's [Decision 11](#decision-11--the-package-request-contract-works-under-channels-request_from_info-learns-the-channels-context-shape-reads-auth-mutations-stay-deferred)
  makes the package's **read** surfaces consume it. The session-*mutating* half is
  [`spec-040`][spec-040]'s: its own [`auth/sessions.py`][auth-sessions] classifies the
  transport and answers `login` / `logout` per transport.
- [`field_error`][glossary-fielderror-envelope] — the shared write-error envelope.
  Untouched by this card, but named because the request
  [`request_from_info()`][glossary-request-from-info] resolves is the same object
  [`build_serializer_kwargs`][rf-resolvers] hands DRF as `context["request"]`, and a
  serializer override that reads it under Channels produces entries in that envelope.
- [`TestClient`][glossary-testclient] / [`GraphQLTestCase`][glossary-graphqltestcase]
  — the `0.0.14` sibling card (`DONE-043-0.0.14`) whose helpers own
  HTTP-level test ergonomics; this card's tests use Channels' own communicators,
  not those helpers.
- [Debug-toolbar middleware][glossary-debug-toolbar-middleware] /
  [Response-extensions debug middleware][glossary-response-extensions-debug-middleware]
  — the other two `0.0.14` siblings sharing the joint cut
  ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — untouched here,
  but worth naming: the router carries a `strawberry.Schema` whose extensions ride
  along unchanged — a schema built with the optimizer keeps it under Channels; the
  router is transport only.

## Slice checklist

Each top-level item maps to one commit / PR. **Two slices: the dependency gate +
code + tests (Slice 1), and docs + card wrap (Slice 2).** The card is an S — the
module is ~30 lines of composition upstream and the composition itself stays that
size here; the weight is in the soft-dependency discipline and its tests. There is
**no live fakeshop slice**:
the fakeshop example is WSGI-only ([`config/wsgi.py`][config-wsgi] is its only
entrypoint; no `asgi.py` exists), so no `/graphql/` HTTP request can reach a Channels
router — the package-tests placement is the documented
genuinely-unreachable-live case, not a live-first weakening
([Decision 8](#decision-8--test-strategy-package-tests-only-communicator-driven-execution-eviction-simulated-absence)).

- [ ] **Slice 1 — dependency gate + `routers.py` + `tests/test_routers.py`**
  - [ ] **The dependency gate lands first, in the same commit** (the
        [`spec-039`][spec-039] Slice-0 discipline): **`channels[daphne]>=4.3.2`**
        added to `[dependency-groups].dev` in [`pyproject.toml`][pyproject] and
        `uv.lock` regenerated together (`uv lock`), so the declared and locked
        dev environments never diverge. The `[daphne]` extra is **test-only**
        in effect: `channels/testing/__init__.py` unconditionally imports
        `.live`, whose module-level `from daphne.testing import DaphneProcess`
        makes the (themselves daphne-free, in-process) communicators
        unimportable without daphne — the extra keeps the Channels floor and
        the daphne compatibility in **one dependency row** (Channels' own
        `daphne>=4.0.0` extra pin) instead of two independently-drifting rows;
        the shipped `routers.py` never touches daphne and the install hint
        stays channels-only. The floor is **`4.3.2` everywhere — one declared
        value across every naming site**: `4.3.2` is the first Channels release
        carrying the `Framework :: Django :: 6.0` classifier (PyPI metadata;
        `4.2.1` classifies only up to 5.2), so a lower public floor would let a
        Django 6.0 user follow the package's own install hint into an
        unsupported state. [`pyproject.toml`][pyproject] advertises
        `Framework :: Django :: 5.2`, `6.0` **and `6.1`**, and no Channels
        release at this floor carries a Django 6.1 classifier — the floor's
        guarantee reaches 6.0 and stops there.
        Re-verified at this gate by running the suite, and the naming sites move
        together: the dev-group specifier here, the
        [`utils/imports.py::CHANNELS_FLOOR`][utils-imports] constant every install
        hint interpolates, and the deliberately re-typed drift-catch literal in
        [`tests/test_routers.py`][test-routers]
        ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
  - [ ] **Strawberry-floor verification rides the same gate**: in an isolated
        throwaway venv (never the shared `.venv`), confirm the
        `strawberry.channels` consumer the builder actually imports — **not**
        `GraphQLProtocolTypeRouter`, which the package does not use; gating an
        unused upstream export is unnecessary coupling — imports at the package's
        pinned `strawberry-graphql` floor ([`pyproject.toml`][pyproject], with
        channels installed); if it is missing at the floor, bump the project's
        Strawberry floor instead. The floor itself is single-sited as
        [`utils/imports.py::STRAWBERRY_FLOOR`][utils-imports], with
        [`pyproject.toml`][pyproject] the one other written copy. The command and
        outcome are recorded in the build artifact
        ([Definition of done](#definition-of-done)).
  - [ ] `utils/imports.py` gains
        `require_optional_module(module_name, *, install_hint)`
        (with unit tests) — the shared optional-import owner already established
        in [`utils/imports.py`][utils-imports]; `require_channels()` rides it.
        No `feature_label` parameter: the feature-specific text lives in the
        caller's `install_hint`, so a second label parameter would be unused
        ceremony (the `require_drf()` shape passes its hint the same way)
        ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)
        / Helper-reuse D-P1).
  - [ ] `django_strawberry_framework/routers.py` (new) — the `require_channels()`
        guard (a thin `require_optional_module` wrapper; one
        `_CHANNELS_INSTALL_HINT` string, no
        memoization), the module-level PEP 562 `__getattr__` that materializes and
        caches the `DjangoGraphQLProtocolRouter` class (in the module global
        `_ROUTER_CLASS`, its first construction serialized behind a module-global
        lock) on first access (guard first, then the class body
        subclassing `channels.routing.ProtocolTypeRouter`), and the composition
        itself — `"http"`: the required `django_application`, assigned verbatim;
        `"websocket"`: the package's Host validator wrapping
        `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([graphql])))`
        over whatever consumer is mounted — by default the package's
        revalidating subclass of `strawberry.channels`'s `GraphQLWSConsumer`
        ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)
        / [Decision 6](#decision-6--constructor-and-composition)
        / [Decision 7](#decision-7--the-consumers-come-from-strawberrychannels-engine-owned-not-package-owned);
        the protocol split, the Host validator and the consumer seam are
        [`spec-046`][spec-046]'s).
        The module defines `__all__ = ("DjangoGraphQLProtocolRouter",)`
        (submodule star import is an opt-in to the router, so it may raise the
        install-hint `ImportError` when channels is absent); no package-root
        re-export; the consumer path is
        `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`
        ([Decision 3](#decision-3--the-symbol-is-djangographqlprotocolrouter--distinctly-ours-pinned-now)).
        The builder wraps present-but-incompatible import failures into an
        actionable `ImportError` — and names **which** half is broken
        (channels vs the `strawberry.channels` consumers), separate from the
        top-level channels-absent hint ([Error shapes](#error-shapes)).
  - [ ] [`django_strawberry_framework/utils/permissions.py`][utils-permissions]
        — `request_from_info()` learns the Strawberry-Channels context shape
        (a mapping context whose `"request"` value exposes an ASGI scope — through
        `consumer.scope` for the HTTP consumer's request object, directly through
        `scope` for the WebSocket consumer, which supplies itself; duck-typed, no
        `channels` import) and returns a request-like adapter
        that **wraps** the original context value rather than replacing it: it
        exposes `.user` / `.session` / `.scope` from the resolved scope explicitly
        (a read that blows up becoming a
        [`ConfigurationError`][glossary-configurationerror] rather than escaping
        raw) and **delegates every other attribute to the wrapped request via
        `__getattr__`**, so user-code hooks reading `request.headers`,
        `request.COOKIES`, `request.path`, `request.method`, `request.consumer`,
        etc. keep working under Channels instead of raising `AttributeError` — the
        adapter must not silently narrow the framework
        request contract; unit tests for the new branch land beside the
        helper's existing suite
        ([Decision 11](#decision-11--the-package-request-contract-works-under-channels-request_from_info-learns-the-channels-context-shape-reads-auth-mutations-stay-deferred)).
  - [ ] `tests/test_routers.py` (new) — **channels-present**: construction /
        composition assertions (a `ProtocolTypeRouter` instance; `http` +
        `websocket` mapping keys; the `"http"` value is the supplied application
        by identity; the WebSocket middleware wrapping order via the
        intent-named `unwrap_origin_validator()` / `unwrap_auth_stack()`
        helpers; a custom `websocket_url_pattern`), plus real execution through
        Channels' own communicators — an `HttpCommunicator` request proving every
        HTTP path reaches the supplied application, a `WebsocketCommunicator`
        connect on the `graphql-transport-ws` subprotocol passing the origin
        validator (with the mismatched- and **missing-`Origin`** denial
        directions), the **package-realistic request-contract round trip** (a
        resolver reading the actor through `request_from_info()`, both the
        anonymous read and a user-code hook reading a delegated attribute,
        Test 16), the **authenticated-session round trip** (a real user/session
        cookie rides the handshake and the resolver sees the authenticated
        actor, Test 18), plus the degraded partial-install error shapes
        (parametrized over a blocked channels import and a blocked
        `strawberry.channels` consumer, Test 17). **channels-absent**: the
        eviction + `builtins.__import__`-block pattern from
        [`tests/rest_framework/test_soft_dependency.py`][test-soft-dependency] —
        `import django_strawberry_framework` and
        `import django_strawberry_framework.routers` both succeed;
        `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`
        (and `from ... import *`, since `__all__` names the lazy symbol) raise
        `ImportError` carrying the install hint; the root package import
        stays channels-free — with the absence fixture saving/restoring the
        **parent package's `routers` attribute alongside** the `sys.modules`
        entries (the blocked-then-retried import re-executes `routers.py` and
        rebinds the parent attribute to a fresh module object; restoring only
        `sys.modules` would leave two live module objects with independent
        class caches, an order-dependent flake under `pytest-xdist`). The
        degraded-install path (Test 17) uses the **same** module-eviction +
        parent-attribute-restore fixture so the freshly re-executed module has
        no cached `_ROUTER_CLASS`, making the blocked builder import actually
        fire regardless of any earlier construction test
        ([Test plan](#test-plan)).
  - [ ] Every new symbol carries its docstring (the [`docs/TREE.md`][tree] render
        fails on missing module docstrings) and any staged-but-not-implemented
        seam carries a `TODO(spec-041 Slice N)` source anchor per
        [`AGENTS.md`][agents].
- [ ] **Slice 2 — docs + card wrap (no version bump)**
  - [ ] [`docs/GLOSSARY.md`][glossary]
        [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]
        entry body updated to the implemented contract (constructor signature, the
        composition, the soft-dependency behavior
        matrix, the WSGI-fakeshop non-demonstration note); the **status stays
        `planned for 0.0.14`** until the joint cut flips it
        ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).
  - [ ] [`docs/TREE.md`][tree] regenerated via
        [`scripts/build_tree_md.py`][build-tree-md] (never hand-edited): the
        `routers.py` row moves from `planned by WIP-ALPHA-041-0.0.14` to the real
        docstring-derived row, and `tests/test_routers.py` appears in the test
        tree.
  - [ ] [`KANBAN.md`][kanban] card wrap: the card moves to Done as
        `DONE-041-0.0.14`, its `SpecDoc` pointing at this spec (kanban
        DB edit + [`scripts/build_kanban_md.py`][build-kanban-md] /
        `build_kanban_html.py` re-render, never a hand-edit).
  - [ ] **Deferred to the joint `0.0.14` cut** (not this slice): the version
        quintet (`pyproject.toml`, `__version__`,
        [`tests/base/test_init.py::test_version`][test-base-init], the GLOSSARY
        package-version line, the `django-strawberry-framework` `version` entry in
        `uv.lock`), the GLOSSARY status flip to `shipped (0.0.14)`, the
        [`README.md`][readme] / [`docs/README.md`][docs-readme] "Coming next" →
        "Shipped today" moves, and the `CHANGELOG.md` bullets. Per
        [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told", the `CHANGELOG.md` edit additionally requires the joint-cut
        slice's maintainer prompt to grant it explicitly; this spec describes the
        edit but cannot grant the permission.

## Problem statement

A Django team running Channels (WebSockets, or simply an ASGI deployment that wants
one process for HTTP + WS) has to compose four pieces to serve GraphQL over a socket:
`channels.routing.ProtocolTypeRouter` splitting the two protocols, a WebSocket
`URLRouter`, Strawberry's Channels WebSocket consumer as its route target,
`channels.auth.AuthMiddlewareStack` so the
session user is on the scope, and `channels.security.websocket.AllowedHostsOriginValidator`
so cross-origin WebSocket connections are rejected. None of it is hard, all of it is
boilerplate, and every consumer who writes it by hand gets to re-discover the
non-obvious parts — that the origin validator belongs on the WebSocket branch only,
and that the wrapping order between it and the auth stack is load-bearing.

`strawberry-graphql-django` absorbs that boilerplate in
[`strawberry_django/routers.py`][upstream-routers]: `AuthGraphQLProtocolTypeRouter`,
a ~30-line `ProtocolTypeRouter` subclass with the exact composition above, consumed
as one import in the project's `asgi.py`. The card carries the Required 🍓 parity tag
for exactly that module (the [`KANBAN.md`][kanban] #"Decision: Alpha cards must claim upstream parity"
rule; `graphene-django` predates the Strawberry Channels story and
ships **no** router, so this is single-upstream parity — honest, not fabricated).
[`GOAL.md`][goal] confirms the same boundary from the north-star side: its working
reference — the `django-graphene-filters` cookbook
[`recipes/schema.py`][cookbook-recipes-schema] that the "Cookbook parity" target
example ports — is an HTTP-only Graphene schema (`Node.Field` +
`AdvancedDjangoFilterConnectionField`, no ASGI / Channels / subscription surface
anywhere in it), so the router sits on `GOAL.md`'s **migration axis** (success
criterion 7: migrate "without bringing the source package along"), not on the
sidecar-parity axis the cookbook port proves.
Without an equivalent, the package's migration story leaks at the ASGI entrypoint:
a migrating consumer keeps one `strawberry_django` import alive purely for transport
plumbing, exactly the "thin wrapper" dependency shape [`GOAL.md`][goal]'s non-goals
exist to prevent.

The work is small — the module is composition, not machinery — but it introduces the
package's **second soft dependency** (`channels`, after `djangorestframework`), so
the real design weight is in doing that the way [`spec-039`][spec-039] already
proved: one guard, one install-hint string, a package import that never pays for the
integration it didn't ask for, and tests that simulate absence without uninstalling
anything.

## Current state

A true description of the repo as this spec is authored:

- **No `routers.py` exists; [`docs/TREE.md`][tree] reserves it.** The target package
  layout carries `routers.py # planned by WIP-ALPHA-041-0.0.14 - Channels ASGI
  router (migration aid)` — this card's row, unlike the `auth/` gap `spec-040` had
  to record as a risk. The test-layout section carries no `tests/test_routers.py`
  row yet; the regenerated tree adds it in Slice 2.
- **The engine half is already installed.** `strawberry.channels` ships
  `GraphQLHTTPConsumer`, `GraphQLWSConsumer`, and — worth naming — Strawberry
  core's own `GraphQLProtocolTypeRouter` (`strawberry/channels/router.py`),
  verified at the installed strawberry 0.316.0 (its presence back at the pinned
  `strawberry-graphql>=0.262.0` floor is upstream history, spot-checked at the
  dependency gate — [Decision 7](#decision-7--the-consumers-come-from-strawberrychannels-engine-owned-not-package-owned)); core's router
  composes the same two consumers **without** `AuthMiddlewareStack` or the origin
  validator. The package's value-add over telling consumers "use Strawberry's
  router" is precisely the Django auth/session composition
  ([Borrowing posture](#borrowing-posture)).
- **`channels` is installed nowhere.** It is absent from `[project].dependencies`
  and `[dependency-groups].dev` in [`pyproject.toml`][pyproject], and
  `import channels` fails in the dev venv (verified). Importing
  `strawberry.channels` fails without it too (its handlers import `channels.db` /
  `channels.generic` at module level, verified in the venv source) — so the lazy
  import boundary must cover **both** the `channels.*` imports and the
  `strawberry.channels` imports
  ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
- **The soft-dependency architecture exists and is proven.**
  [`rest_framework/__init__.py`][rf-init] ships `require_drf()` — a function-local
  import wrapped into a single install-hint `ImportError`, no memoization so the
  absence tests can re-hit it — and the package root's PEP 562
  [`__getattr__`][init] resolves the DRF names lazily so
  `import django_strawberry_framework` never pays the DRF import.
  [`tests/rest_framework/test_soft_dependency.py`][test-soft-dependency] pins the
  whole matrix with absence **simulated** (a `builtins.__import__` block + strict
  `sys.modules` eviction/restore), the discipline this card's absent path reuses.
- **The fakeshop example is WSGI-only.** [`examples/fakeshop/config/`][config-wsgi]
  contains `wsgi.py` and no `asgi.py`; the live `/graphql/` acceptance suite
  ([`examples/fakeshop/test_query/`][test-query-readme]) drives `django.test.Client`
  over WSGI. There is no live surface a Channels router could be earned on today
  ([Decision 8](#decision-8--test-strategy-package-tests-only-communicator-driven-execution-eviction-simulated-absence)).
- **The auth surface points here.** The shipped `0.0.13`
  [Auth mutations][glossary-auth-mutations] GLOSSARY entry closes with "Channels /
  websocket auth is deliberately not covered until the `0.0.14`
  [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] card" — a
  handoff broader than this card's DoD, scoped in
  [Decision 2](#decision-2--card-scope-boundary-the-transport-router-ships-websocket-auth-semantics-and-fakeshop-asgi-stay-out).
- **The version line reads `0.0.13`, and three siblings share `0.0.14`.**
  Cards `042` / `043` / `044` were all non-Done at this card's patch version, so
  the joint-cut rule applies
  ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).

## Goals

1. **Ship the one-import ASGI entrypoint.** A consumer's `asgi.py` becomes:
   construct Django's ASGI app, import the schema, and instantiate
   `DjangoGraphQLProtocolRouter(schema, django_application=django_asgi)` — every
   HTTP request through the project's own Django stack, GraphQL over WebSocket with
   `AuthMiddlewareStack` sessions and `scope["user"]` populated, and the handshake
   validated on `Host` and `Origin`
   ([Decision 6](#decision-6--constructor-and-composition)).
   The package's **read-path request contract consumes that scope**: this card
   extends the shared request helper so
   [`request_from_info()`][glossary-request-from-info]-routed surfaces
   (the `current_user` query, permission gates) resolve the actor under
   Strawberry's Channels context
   ([Decision 11](#decision-11--the-package-request-contract-works-under-channels-request_from_info-learns-the-channels-context-shape-reads-auth-mutations-stay-deferred)).
   Session-*mutating* auth is not this card's, and the URLconf entry the GraphQL
   HTTP endpoint needs is [`spec-046`][spec-046]'s.
2. **Keep `channels` soft.** `import django_strawberry_framework` (and
   `from django_strawberry_framework import *`) must succeed and stay
   channels-free; the install-hint `ImportError` fires only when the consumer
   actually reaches for the router
   ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
3. **A documented migration, not a dangling dependency.** A
   `strawberry-graphql-django` migrant replaces
   `from strawberry_django.routers import AuthGraphQLProtocolTypeRouter` with
   `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`
   and keeps no upstream import alive for transport plumbing. The call site is
   **not** byte-compatible with upstream's — [`spec-046`][spec-046] Decision 5
   broke that deliberately, as an alpha breaking change to a security boundary — so
   the migration is a two-place recipe (the `asgi.py` argument and a URLconf entry
   for [`views.py::DjangoGraphQLView`][views]), carried by the migration guide's
   symbol-equivalents row and, until that card lands, by the
   [`docs/GLOSSARY.md`][glossary] entry and [`docs/README.md`][docs-readme]
   ([Decision 9](#decision-9--migration-ergonomics-live-in-the-migration-guide-row-not-the-symbol-name)).
   This is [`GOAL.md`][goal] success criterion 7 — migrate "without bringing the
   source package along" — applied to the ASGI entrypoint, the one migration site
   `GOAL.md`'s own coming-from-`strawberry-graphql-django` diff (a `Meta`-shape
   change) does not cover.
4. **Both dependency states tested.** `tests/test_routers.py` exercises the
   channels-present path (construction, composition, and real communicator-driven
   execution over the socket) and the channels-absent path (the guarded
   `ImportError`), keeping
   the package's 100% coverage gate honest for every `routers.py` line
   ([Decision 8](#decision-8--test-strategy-package-tests-only-communicator-driven-execution-eviction-simulated-absence)).
5. **Stay distinctly ours.** The symbol name does not impersonate the upstream API
   (the card's pre-pinned architectural posture, preserved as
   [Decision 3](#decision-3--the-symbol-is-djangographqlprotocolrouter--distinctly-ours-pinned-now)).

## Non-goals

- **WebSocket / Channels *auth mutation* semantics.** Upstream's
  `strawberry_django.auth` carries a `channels_auth` fallback that logs in/out
  against `request.consumer.scope`; the package's shipped
  [Auth mutations][glossary-auth-mutations] deliberately did not borrow it
  ([`spec-040`][spec-040] Decision 11), and this card does not either. The router
  puts the session user **on the scope** (transport) and
  [Decision 11](#decision-11--the-package-request-contract-works-under-channels-request_from_info-learns-the-channels-context-shape-reads-auth-mutations-stay-deferred)
  makes the package's *read* surfaces consume it. The session-**mutating** half is
  [`spec-040`][spec-040]'s own: [`auth/sessions.py`][auth-sessions] classifies a
  resolved request into one explicit transport and answers the capability question
  per transport — `login` is refused on any WebSocket, `logout` on a
  signed-cookie-engine WebSocket. Nothing about that boundary is stated here; read
  it there.
- **A fakeshop ASGI surface.** No `asgi.py`, no `channels` in the example's runtime
  path, no live `/graphql/` Channels tests. A future fakeshop ASGI dogfooding pass
  belongs with the fakeshop-activation card ([`TODO-BETA-062-0.1.5`][kanban]) if the
  maintainer wants it at all
  ([Decision 8](#decision-8--test-strategy-package-tests-only-communicator-driven-execution-eviction-simulated-absence)).
- **Subscriptions machinery.** `GraphQLWSConsumer` speaks the `graphql-transport-ws`
  / `graphql-ws` protocols already; whether a consumer's schema defines
  subscriptions is the consumer's business. The package ships no subscription
  surface and this card adds none — the router is transport only.
- **A hard `channels` dependency, or an extras group.** `[project].dependencies`
  is untouched; no `django-strawberry-framework[channels]` extra is introduced
  (rejected in
  [Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
- **A new [`DjangoType`][glossary-djangotype] `Meta` key or settings key.** The router is a plain class in
  a plain module; `DEFERRED_META_KEYS` and [`conf.py`][conf] are untouched — the
  same posture every integration-surface card has taken.
- **Sync-consumer variants.** `strawberry.channels` also ships
  `SyncGraphQLHTTPConsumer`; upstream's router does not expose it and neither does
  this card. A consumer with exotic consumer needs composes `ProtocolTypeRouter`
  by hand — the escape hatch is the underlying machinery. (A *supported* injection
  seam for the WebSocket consumer arrived later, under
  [`spec-046`][spec-046] Decision 11; it is not this card's, and it replaces the
  consumer rather than the composition wrapped around it.)

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it?" test this card is
**single-upstream parity**: `strawberry-graphql-django` ships
[`routers.py`][upstream-routers]; `graphene-django` ships no ASGI/Channels helper at
all. The card's `Verified in upstream` section names one file and it was read in
full for this spec, together with the Strawberry-core router it subclasses
alongside (`strawberry/channels/router.py`, from the checked-out venv) — the
comparison between the two is what isolates this card's actual value-add.

### From `strawberry-graphql-django` — borrow the WebSocket composition

[`AuthGraphQLProtocolTypeRouter`][upstream-routers] is `ProtocolTypeRouter` over an
HTTP branch, a WebSocket branch, and the signature
`(schema, django_application=None, url_pattern="^graphql")`.

**What this package borrows is the WebSocket branch** —
`AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([
re_path(pattern, GraphQLWSConsumer.as_asgi(schema=schema))])))`. The origin
validator is WS-branch-only (browsers enforce same-origin on fetch/XHR; the
WebSocket handshake needs the explicit server-side check) and the auth stack is what
puts the session user on the socket's scope. The delta against Strawberry core's
`GraphQLProtocolTypeRouter` (same consumers, same signature, **no**
`AuthMiddlewareStack`, **no** origin validator) is exactly that Django-auth
composition — which is why the package ships its own helper instead of pointing
consumers at the engine's: a Django-framework package whose auth mutations
([`spec-040`][spec-040]) assume the session user is resolvable should hand out the
transport that makes that true.

**What it does not borrow is upstream's HTTP branch.** Upstream serves GraphQL over
HTTP through a Channels consumer, wraps the whole HTTP `URLRouter` — GraphQL route
and optional Django fallback alike — in one `AuthMiddlewareStack`, and appends
`re_path(r"^", django_application)` behind the GraphQL route when provided. This
package's `"http"` value **is** `django_application`, dispatched directly with no
wrapper, so every HTTP request traverses the project's real `MIDDLEWARE`.
[`spec-046`][spec-046] Decisions 2 and 6 own that boundary and the reasoning for it;
what a `routers.py` reader needs here is only that there is no package-owned HTTP
branch to borrow into, and therefore no Strawberry HTTP consumer and no fallback
ordering to get right.

### Explicitly do not borrow

- **The hard `channels` import.** Upstream imports `channels.*` at module top
  level — `strawberry_django` can afford that because its consumers install it as
  the integration package. This package's floor is "importable with zero optional
  dependencies", proven by the DRF precedent; the imports move inside the guard
  ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
- **The symbol name.** `AuthGraphQLProtocolTypeRouter` is upstream's API; shipping
  it verbatim would make the module impersonate `strawberry_django` (the card's
  architectural posture; [`GOAL.md`][goal] non-goal "a thin wrapper around
  `strawberry-graphql-django`"). The rename is documented, not silently divergent
  ([Decision 3](#decision-3--the-symbol-is-djangographqlprotocolrouter--distinctly-ours-pinned-now)
  / [Decision 9](#decision-9--migration-ergonomics-live-in-the-migration-guide-row-not-the-symbol-name)).
- **`strawberry_django`'s consumers-and-auth coupling.** Upstream's `auth/`
  mutations reach into `request.consumer.scope` when the request is
  Channels-shaped; the package's auth surface stays request-shaped and this card
  does not extend it ([Non-goals](#non-goals)).

## User-facing API

The consumer's ASGI entrypoint, whole:

```python
# myproject/asgi.py
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

from django.core.asgi import get_asgi_application

django_asgi = get_asgi_application()   # Django is fully initialized here

from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter

from myproject.schema import schema

application = DjangoGraphQLProtocolRouter(
    schema,
    django_application=django_asgi,    # REQUIRED
)
```

```python
# myproject/urls.py
from django.urls import path

from django_strawberry_framework.views import DjangoGraphQLView

from myproject.schema import schema

urlpatterns = [
    path("graphql/", DjangoGraphQLView.as_view(schema=schema)),
]
```

That routes every WebSocket request matching `websocket_url_pattern` to Strawberry's
Channels WebSocket consumer over `schema` — with Django sessions and `scope["user"]`
populated (and readable by the package's own
`request_from_info()`-routed surfaces per
[Decision 11](#decision-11--the-package-request-contract-works-under-channels-request_from_info-learns-the-channels-context-shape-reads-auth-mutations-stay-deferred))
and the handshake refused unless both its `Host` and its `Origin` are allowed — while
every HTTP request, GraphQL included, goes to the project's own Django ASGI
application and therefore through the project's real `MIDDLEWARE`. **The two
declarations are independent by design**: the router knows nothing about the URLconf
path, so a project that moves its GraphQL URL changes both. The constructor:

```python
DjangoGraphQLProtocolRouter(
    schema,                                  # the strawberry.Schema (extensions ride along)
    django_application,                      # REQUIRED; becomes the "http" value verbatim
    *,
    websocket_url_pattern=r"^graphql/?$",    # re_path regex, WebSocket branch only
    websocket_consumer_class=None,           # consumer-injection seam (spec-046 Decision 11)
    websocket_revalidation_window=_DEFAULT_REVALIDATION_WINDOW,  # consumers.py's value, seconds
)
```

The three keyword parameters are [`spec-046`][spec-046]'s (Decisions 4 and 11); that
spec states their contract, and the [`docs/GLOSSARY.md`][glossary] entry carries the
consumer-facing summary. The revalidation default is named rather than spelled
because its one written value is
[`consumers.py::_DEFAULT_REVALIDATION_WINDOW`][consumers], which the signature reads
by name. What matters here is the shape: `schema` positional,
`django_application` required and positional-or-keyword, everything else keyword-only.

Consumer-visible behavior:

- **The schema is used as-is.** A schema built with
  [`strawberry_config()`][glossary-strawberry_config] and
  [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] keeps both — the
  router hands the schema object to the consumer untouched.
- **`django_application` is the whole HTTP branch.** It is the `"http"` value
  verbatim — no `URLRouter`, no `re_path`, no `AuthMiddlewareStack`, no GraphQL
  consumer — so HTTP runs Django's own request lifecycle, `ALLOWED_HOSTS` and CSRF
  included. Omitting it is Python's own `TypeError`; `None` or any non-callable is a
  [`ConfigurationError`][glossary-configurationerror] whose message names the
  migration. The router never calls `get_asgi_application()` itself: *when* that runs
  is load-bearing (it calls `django.setup()`), so it stays the consumer's explicit,
  visible decision.
- **Non-GraphQL WebSocket paths are never routed** — parity with upstream.
- **Migration is a recipe, not an import swap.** Upstream's byte-compatible
  constructor is deliberately gone
  ([`spec-046`][spec-046] Decision 5 — an intentional alpha breaking change to a
  security boundary), so a migrating project changes the import, passes its Django
  ASGI application, and adds the URLconf entry above
  ([Decision 9](#decision-9--migration-ergonomics-live-in-the-migration-guide-row-not-the-symbol-name)).
- **Without `channels` installed**, the `from django_strawberry_framework.routers
  import DjangoGraphQLProtocolRouter` line raises `ImportError` with the install
  hint naming the verified floor — at the consumer's `asgi.py` import, the first
  moment the symbol is actually reached for, never at
  `import django_strawberry_framework`. The URLconf half needs none of it:
  [`views.py`][views] is channels-free.

### Error shapes

- **`channels` absent** — `ImportError` from the symbol access, message naming the
  package and floor, single-sited in `_CHANNELS_INSTALL_HINT`:
  `"DjangoGraphQLProtocolRouter requires channels, which is not installed. Install
  it with `pip install 'channels>=<floor>'` (the package's verified Channels
  floor)."` — the exact wording mirrors the DRF hint's shape so the two soft
  dependencies fail identically. The floor is **interpolated** from
  [`utils/imports.py::CHANNELS_FLOOR`][utils-imports], never re-typed into the
  string (Helper-reuse D2). The hint is public API in practice — it is the
  error message a deploying consumer follows — so the floor it names is the first
  Channels release carrying the Django 6.0 classifier, never a lower one that would
  strand a Django 6.0 user. It carries no Django 6.1 guarantee:
  [`pyproject.toml`][pyproject] advertises that classifier and no Channels release at
  this floor does
  ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
- **`channels` present but a builder import fails** — `require_channels()`
  passes but the class body's imports then fail. The builder wraps that
  `ImportError` into an actionable one and chains the original
  (`raise … from exc`) so the real missing symbol stays visible — never a bare
  `AttributeError` or an unexplained transitive `ImportError` at ASGI startup.
  The wrap **names which half is broken**, because the builder imports from two
  packages and reinstalling the wrong one wastes the consumer's time:
  - a failing `channels.*` import (a Channels too old for a required symbol)
    names the Channels floor;
  - a failing `strawberry.channels` consumer import (`GraphQLWSConsumer` absent — a
    broken or too-old Strawberry, or a partial install) names **both** required
    halves: the Channels floor **and** the Strawberry floor, with the
    `strawberry.channels` consumer importable.

  Both messages interpolate their floors from
  [`utils/imports.py`][utils-imports] (`CHANNELS_FLOOR`, `STRAWBERRY_FLOOR`), so the
  only other written copy of either is its own [`pyproject.toml`][pyproject]
  dependency row.
  This is a **separate** message from `_CHANNELS_INSTALL_HINT` (which is for
  true top-level `channels` absence only); the Strawberry-floor gate exists
  precisely because Strawberry is part of the dependency boundary, so the
  runtime error shape reflects that
  ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
- **A `django_application` that is not usable** — `None` or any non-callable raises
  [`ConfigurationError`][glossary-configurationerror] at construction, with a message
  naming the two-place migration; omitting the argument is Python's own `TypeError`.
  The contract is [`spec-046`][spec-046] Decision 3's.
- **Cross-origin WebSocket** — the handshake is denied by
  `AllowedHostsOriginValidator` (connection closed before the GraphQL protocol
  starts); this is Channels' behavior, surfaced here because the router opts into
  it deliberately. A connection carrying **no `Origin` header at all** is
  likewise denied unless `ALLOWED_HOSTS` contains `"*"`
  ([Edge cases](#edge-cases-and-constraints)). A handshake whose **`Host`** Django's
  own boundary refuses is denied first, by the outermost wrapper, and is
  byte-identical on the wire — the two checks are separate questions and neither
  substitutes for the other ([`spec-046`][spec-046] Decision 19).
- **Unroutable scope types** (e.g. `lifespan` from uvicorn) — Channels'
  `ProtocolTypeRouter` raises its own `ValueError` for scope types with no mapping;
  parity with upstream, documented in [Edge cases](#edge-cases-and-constraints).

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec stem is `spec-041-channels_router-0_0_14`: card NNN `041`, topic
slug `channels_router` (the card's subject — the Channels ASGI router), version
segment `0_0_14` from the card's trailing `-0.0.14`. Follows the
[`docs/SPECS/NEXT.md`][next] convention. The file was authored at
`docs/` and archived to `docs/SPECS/` by a later spec author's Step 8, its
companions to `docs/SPECS/appx/`.

*Alternatives rejected, with the reason each lost: [rationale companion][rationale-decision-1--spec-filename-and-canonical-naming].*

### Decision 2 — Card-scope boundary: the transport router ships; WebSocket-auth semantics and fakeshop ASGI stay out

This card ships exactly the card's DoD: the `routers.py` module, the soft
dependency, the two test paths, and the migration-guide handoff row. Three
adjacent-looking pieces of work are explicitly out:

- **Auth *mutations* over Channels.** The [Auth mutations][glossary-auth-mutations]
  GLOSSARY entry deferred "Channels / websocket auth" to this card. The router
  delivers the transport half — `AuthMiddlewareStack` on the WebSocket branch, so
  `scope["user"]` is populated and the session machinery is present — **and**
  this card makes the package's *read-path* request contract consume it:
  `request_from_info()` learns the Channels context shape, so the
  `current_user` query and permission gates resolve the actor
  ([Decision 11](#decision-11--the-package-request-contract-works-under-channels-request_from_info-learns-the-channels-context-shape-reads-auth-mutations-stay-deferred)).
  The session-**mutating** half — whether `login` / `logout` / `register` function
  against a Channels scope, given that Channels ships its own async
  `channels.auth.login()` / `logout()` because the session semantics differ — is
  **not** this card's, and it is no longer open: [`spec-040`][spec-040]'s own
  [`auth/sessions.py`][auth-sessions] classifies the transport and answers the
  capability question per transport. That contract is stated there, not here.
- **Fakeshop ASGI activation.** Out per
  [Decision 8](#decision-8--test-strategy-package-tests-only-communicator-driven-execution-eviction-simulated-absence);
  still true today, the fakeshop example having no `asgi.py`.
- **No new `Meta` / settings key.** The router takes constructor arguments; nothing
  reads [`conf.py`][conf]. The `START.md` rule ("add a settings key only when the
  feature that needs it lands") — no feature here needs one.

Justification: the card body is explicit that this is a "pure migration-aid card"
and "small slice"; scope creep into auth semantics would entangle an S transport
card with the auth subsystem's request-shape contract, and the
[`START.md`][start] advice ("resist scope creep... don't quietly mix in
while-I'm-here extras") applies verbatim.

**The HTTP half of this boundary is [`spec-046`][spec-046]'s** (its Decisions 2 and
6): GraphQL over HTTP is not this router's concern at all. What survives here is the
WebSocket half — the transport ships, the auth *mutations* and the fakeshop ASGI
surface do not.

*Alternatives rejected, with the reason each lost: [rationale companion][rationale-decision-2--card-scope-boundary].*

### Decision 3 — The symbol is `DjangoGraphQLProtocolRouter` — distinctly ours, pinned now

The public symbol is `DjangoGraphQLProtocolRouter` — the package's own family
(`Django*` prefix like [`DjangoConnectionField`][glossary-djangoconnectionfield] /
[`DjangoMutationField`][glossary-djangomutationfield]), without upstream's `Auth`
prefix or its `Type` infix. It is deliberately **not** upstream's
`AuthGraphQLProtocolTypeRouter`: the module must not impersonate the upstream API
(the card's own architectural posture, and the [`GOAL.md`][goal] "thin wrapper"
non-goal). The card body, the [`docs/GLOSSARY.md`][glossary]
[entry][glossary-djangographqlprotocolrouter] with its own anchor other docs link,
and the migration-guide handoff row all carry this spelling.

No package-root re-export: the consumer path is
`from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`,
mirroring the [`spec-040`][spec-040] Decision 3 structural-opt-in posture (a
consumer who never deploys ASGI never types the import) and keeping
[`__init__.py`][init]'s `__all__` channels-free by construction.

**The submodule declares `__all__ = ("DjangoGraphQLProtocolRouter",)`.** Without
it, `from django_strawberry_framework.routers import *` would leak the helper
names (`require_channels`, whatever typing / `importlib` imports remain
module-global) into the consumer's namespace. Pinning `__all__` to the one public
symbol keeps the module's star surface clean — and, deliberately, makes
`from ...routers import *` **opt into the router**: `import *` calls
`getattr(module, "DjangoGraphQLProtocolRouter")`, which fires the PEP 562
`__getattr__`, which runs `require_channels()`, so a channels-absent star import
raises the same install-hint `ImportError` as the explicit `from ... import`
(pinned by the channels-absent test plan). Because the symbol is never a real
module global (it materializes through `__getattr__`), the `__all__` line
carries a scoped `# noqa: F822` — ruff's "undefined name in `__all__`" is a
false positive for a [PEP 562 lazy export][glossary-pep-562-lazy-export]. The
**root** package `__all__`
([`__init__.py`][init]) stays unchanged and channels-free — the router is never
re-exported there, so `from django_strawberry_framework import *` never touches
the guard.

*Alternatives rejected, with the reason each lost: [rationale companion][rationale-decision-3--the-symbol-name].*

### Decision 4 — Module and test locations: a top-level `routers.py` mirroring both upstreams; `tests/test_routers.py`

The module is `django_strawberry_framework/routers.py` — a top-level module, not a
package. Both upstream shapes agree (`strawberry_django/routers.py`;
`strawberry/channels/router.py`), the content is one lazily-built class, one guard
and the composition, and [`docs/TREE.md`][tree]'s target layout already reserves
exactly this path against this card. The tests are the card-named
`tests/test_routers.py` — a top-level test module beside
[`tests/test_list_field.py`][test-list-field] and its peers, matching the
one-source-module-one-test-module convention the root tree uses for top-level
modules (the `tests/auth/` package-per-subpackage shape applies to subpackages,
which this is not).

*Alternatives rejected, with the reason each lost: [rationale companion][rationale-decision-4--module-and-test-locations].*

### Decision 5 — Soft `channels` dependency: a lazy module `__getattr__` + one `require_channels()` guard

`channels` joins `djangorestframework` as the package's second soft dependency, with
the same three-part architecture ([`spec-039`][spec-039] Decision 12, generalized):

1. **One guard, one hint — built on the shared optional-import owner.**
   `routers.py` defines `require_channels()` as a thin wrapper over
   [`require_optional_module(module_name, *,
   install_hint)`][glossary-require-optional-module] —
   the primitive Slice 1 adds to the package's single optional-import owner
   ([`utils/imports.py`][utils-imports]), so `routers.py` does not hand-roll a
   fourth import-handling pattern beside the registry / generated-input helpers
   already migrated there. The primitive takes **no `feature_label`**: the
   feature-specific text is entirely inside the caller's `install_hint`, so a
   second label parameter would be dead ceremony (the `require_drf()` shape
   passes its hint the same way). The wrapper passes the single
   `_CHANNELS_INSTALL_HINT` string, which stays defined in `routers.py` (D2: one
   hint, one module constant) and **interpolates** the floor from
   [`utils/imports.py::CHANNELS_FLOOR`][utils-imports] rather than re-typing it, so
   the version has exactly one other written copy — its own
   [`pyproject.toml`][pyproject] dependency row. No memoization: each access
   re-fires the guard so the absence test can evict modules and re-hit it, exactly
   the [`require_drf()`][rf-init] contract.
2. **A lazy class, materialized on first access.** The class body subclasses
   `channels.routing.ProtocolTypeRouter`, so it **cannot** be defined at module
   import without paying the import. `routers.py` therefore defines the class
   inside a builder (`_build_router_class()`) and caches the built class in the
   module global **`_ROUTER_CLASS`**, exposing it via a [PEP 562
   **module-level `__getattr__`**][glossary-pep-562-lazy-export]: accessing
   `routers.DjangoGraphQLProtocolRouter` runs
   `require_channels()`, builds (or returns the cached) class, and hands it out.
   **First construction is serialized** behind a module-global lock, with the cache
   re-checked inside it, so two threads reaching for the symbol at once still get
   one class rather than two — a router class is an identity, and two of them would
   make `isinstance` lie. Because both the cache and its lock are module globals,
   evicting `routers` from `sys.modules` drops them with the module — the property
   the degraded-install and absence tests rely on (a re-executed module has no
   cached class, so a blocked builder import actually fires). `import
   django_strawberry_framework.routers` itself imports nothing optional — the
   module stays importable everywhere (introspection, `docs/TREE.md` rendering,
   coverage collection), and the install-hint fires at the earliest moment the
   consumer *actually reaches for the router* (their `from ... import` line in
   `asgi.py`). The builder's imports cover both halves of the boundary:
   `channels.routing` / `channels.auth` / `channels.security.websocket` **and**
   `strawberry.channels` (whose handlers import `channels.db` at module level —
   verified at the pinned `strawberry-graphql` floor, single-sited as
   [`utils/imports.py::STRAWBERRY_FLOOR`][utils-imports] — so it is equally unimportable
   without channels; `require_channels()` runs first so every *channels-absent*
   case routes through the one hint). **Degraded states are specified, not
   accidental, and name which half is broken**: if `require_channels()` passes
   but a builder import then fails, the builder catches that `ImportError` and
   re-raises an actionable one, chaining the original. A failing `channels.*`
   import (a Channels too old for a required symbol) names the Channels floor; a
   failing `strawberry.channels` consumer import names **both** floors with the
   consumer importable — so a broken Strawberry install does not send the consumer
   to reinstall Channels. Both messages interpolate their floors from
   [`utils/imports.py`][utils-imports]. This builder-failure message is **separate**
   from
   `_CHANNELS_INSTALL_HINT` (top-level channels absence only); deployment-time
   import paths deserve real error messages, because the failure happens when
   ASGI imports the application ([Error shapes](#error-shapes); both branches
   pinned in the [Test plan](#test-plan)).
3. **The dependency gate.** Slice 1 adds **`channels[daphne]>=4.3.2`** to
   `[dependency-groups].dev` and regenerates `uv.lock` in the same commit (the
   [`spec-039`][spec-039] Decision 14 lockfile discipline: a dev-dependency edit
   without the regenerated lock leaves declared and locked environments out of
   sync). The `[daphne]` extra exists because Channels' `testing/__init__.py`
   unconditionally imports `.live`, whose module-level
   `from daphne.testing import DaphneProcess` makes every import path to the
   communicators fail without daphne, even though the communicators themselves
   are in-process and daphne-free (verified against the Channels `4.2.1` and
   `4.3.2` sdists); expressing it as Channels' own extra (its `daphne>=4.0.0`
   pin) keeps the floor and the daphne compatibility in one dependency row
   instead of two independently-drifting ones. The shipped `routers.py` never
   imports daphne and the install hint stays channels-only. **The floor is
   single-valued** across the dev-group specifier, the install hint, and the test
   literal — `4.3.2` is the first Channels release carrying the
   `Framework :: Django :: 6.0` classifier (PyPI metadata), so any lower public
   floor would guide a Django 6.0 user into an unsupported install, and a split
   declared-vs-dev-resolved floor is exactly the misuse path a single floor
   removes. [`pyproject.toml`][pyproject]'s advertised Django range runs
   `5.2` / `6.0` / `6.1`, and no Channels release at this floor classifies 6.1,
   so the floor's guarantee reaches 6.0 and stops there. Re-verified at the gate by running the suite. Two written
   copies remain — [`utils/imports.py::CHANNELS_FLOOR`][utils-imports], which every
   hint interpolates, and the `channels[daphne]` row in
   [`pyproject.toml`][pyproject] — plus the deliberately independent re-typed
   literal in [`tests/test_routers.py`][test-routers], whose whole job is to notice
   the other two drifting apart.

The class-identity consequence is deliberate: because the real
`ProtocolTypeRouter` subclass is what the `__getattr__` returns, a
channels-present consumer gets a true subclass (subclassable, `isinstance`-able,
attribute-compatible with upstream's), never a stub pretending.

*Alternatives rejected, with the reason each lost: [rationale companion][rationale-decision-5--soft-channels-dependency].*

### Decision 6 — Constructor and composition

`schema` is positional and `django_application` is **required**; every other
parameter is keyword-only. The two branches are asymmetric on purpose:

- `http` → **`django_application` itself**, assigned verbatim. No `URLRouter`, no
  `re_path`, no `AuthMiddlewareStack`, no GraphQL consumer — every HTTP request
  traverses the project's real `MIDDLEWARE`, and the GraphQL HTTP endpoint is
  [`views.py::DjangoGraphQLView`][views] in the consumer's URLconf.
- `websocket` → the package's Host validator wrapping
  `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([
  re_path(websocket_url_pattern, <consumer>.as_asgi(schema=schema))])))`. All the
  wrappers are the **router's**, applied around whatever consumer is mounted, so a
  consumer injected through the seam cannot escape the Host check, the Origin check
  or authentication.

**Four of the five facts in that shape are [`spec-046`][spec-046]'s, not this
card's**, and are stated here only because a `routers.py` reader cannot understand
the composition without them: the required `django_application` and the
direct-dispatch `"http"` value (its Decisions 2, 3 and 6), the
`url_pattern` → `websocket_url_pattern` rename with exact-at-both-ends matching
(Decision 4), the outermost Host validator (Decision 19), and the
`websocket_consumer_class` / `websocket_revalidation_window` pair (Decision 11).
Read that spec for their contracts; duplicating them here would create a second copy
to rot. **What this card owns** is the WebSocket branch's auth-and-origin
composition — the layers upstream has and Strawberry core's router does not — and
the decision that the router composes Channels' primitives directly rather than
wrapping someone else's router class.

Typing: `django_application: ASGIHandler` under `TYPE_CHECKING` (Strawberry core's
own router annotates its equivalent `str | None`, which is simply wrong — the value
is an ASGI callable; the package does not copy the typo), and `schema: BaseSchema`
under `TYPE_CHECKING` (any Strawberry schema, not a package-specific one — the
router must accept the consumer's real schema object with whatever extensions it
carries).

*Alternatives rejected, with the reason each lost: [rationale companion][rationale-decision-6--constructor-and-composition].*

### Decision 7 — The consumers come from `strawberry.channels`, engine-owned, not package-owned

`GraphQLWSConsumer` is imported (inside the guard boundary) from
`strawberry.channels` — Strawberry core's Channels WebSocket handler, present
at the package's pinned `strawberry-graphql` floor, single-sited as
[`utils/imports.py::STRAWBERRY_FLOOR`][utils-imports] (verified at that floor:
`strawberry/channels/__init__.py` exports it — the export's presence back at the
`0.262.0` floor itself is upstream history, spot-checked at the dependency gate). The engine owns request parsing, multipart
handling, and the WS protocol state machines, exactly as it owns query execution
under the WSGI view; the package **never re-implements them**. This is the standing
"Strawberry stays as the engine" line from [`README.md`][readme] applied to
transport.

The one consumer class the package does define is a *subclass* of that engine
consumer, built by
[`consumers.py::build_revalidating_consumer_class`][consumers] to revalidate the
session actor at two security checkpoints. It is [`spec-046`][spec-046]
Decision 11's, it inherits the engine's protocol machinery rather than restating it,
and it is what `websocket_consumer_class=None` selects. Strawberry core's own
`GraphQLProtocolTypeRouter` is never imported: the package does not use it, and
gating an unused upstream export at the dependency floor would be unnecessary
coupling.

*Alternatives rejected, with the reason each lost: [rationale companion][rationale-decision-7--engine-owned-consumers].*

### Decision 8 — Test strategy: package tests only, communicator-driven execution, eviction-simulated absence

All tests live in `tests/test_routers.py`. The [live-first
mandate][glossary-live-first-coverage-mandate]
([`docs/TREE.md`][tree] #"Coverage priority." /
[`examples/fakeshop/test_query/README.md`][test-query-readme]) sends a test live
when "a package line can be covered by a real fakeshop GraphQL request" — no
`routers.py` line can be: the fakeshop project is WSGI-only (no `asgi.py`; the
acceptance suite drives `django.test.Client`), and a Channels router is
structurally unreachable from it. This is the documented
genuinely-unreachable-live placement (the same reasoning [`spec-040`][spec-040]
used for its permission-gate variants), not a weakening.

Within the package tests, the channels-present path does **not** stop at
structural assertions: Channels ships in-process test communicators
(`channels.testing.HttpCommunicator` / `WebsocketCommunicator`), so the suite
drives real protocol traffic through the router — a `WebsocketCommunicator`
handshake through the `websocket` branch, past the Host and Origin checks and the
auth stack, executing a real GraphQL query against a real `strawberry.Schema`, and
an `HttpCommunicator` request proving the `http` branch hands every path to the
supplied application. That earns the
composition lines with actual protocol traffic instead of `isinstance` checks
(the [`START.md`][start] "coverage is a feature" posture). One import-graph
caveat the dependency gate absorbs: the communicators themselves are in-process
and daphne-free, but `channels/testing/__init__.py` unconditionally imports
`.live` (whose module top level does `from daphne.testing import
DaphneProcess`), so **importing** them requires `daphne` — hence the
`channels[daphne]` extra on the dev-group row in
[Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard);
`routers.py` itself never touches daphne. The channels-absent path reuses the
[`test_soft_dependency.py`][test-soft-dependency] discipline —
[eviction-simulated absence][glossary-eviction-simulated-absence] — verbatim:
absence is **simulated** by a `builtins.__import__` block plus strict
`sys.modules` eviction (both `channels*` and
`django_strawberry_framework.routers`) with full
restore — **including the parent package's `routers` attribute**: the
blocked-then-retried import re-executes `routers.py` and rebinds
`django_strawberry_framework.routers` to a fresh module object, so restoring
only `sys.modules` would leave the attribute path and the import path pointing
at two live modules with independent class caches, an order-dependent identity
flake under `pytest-xdist` (the DRF fixture's defensive
`delattr(django_strawberry_framework, "SerializerMutation")` is the precedent;
here the restore must put the *original module object* back in both places).
With that, the test cannot poison channels-using neighbors under
`pytest-xdist`.

*Alternatives rejected, with the reason each lost: [rationale companion][rationale-decision-8--test-strategy].*

### Decision 9 — Migration ergonomics live in the migration-guide row, not the symbol name

The card's DoD hands [`TODO-BETA-068-0.1.8`][kanban] (Migration and adoption
guides) a one-row entry for its "symbol equivalents" table:
`strawberry_django.routers.AuthGraphQLProtocolTypeRouter` →
`django_strawberry_framework.routers.DjangoGraphQLProtocolRouter`, with the note
that **the constructor is not a drop-in** — `django_application` is required, the
URL parameter is `websocket_url_pattern`, and the project also declares
[`views.py::DjangoGraphQLView`][views] in its URLconf, so the migration is a
two-place recipe ([`spec-046`][spec-046] Decisions 3, 4, 5 and 6). That row is the
**single canonical location** for the migration story — this spec and the GLOSSARY
entry describe the mapping, but the guide owns the migrant-facing table. Because the
guide card is Beta-scheduled and this card shipped first, the handoff is recorded
here (and on the card's own reference edge, already in the kanban DB) rather than
edited into a guide that does not exist yet; the interim migrant-facing surfaces are
the [`docs/GLOSSARY.md`][glossary] entry and the migration note in
[`docs/README.md`][docs-readme].

*Alternatives rejected, with the reason each lost: [rationale companion][rationale-decision-9--migration-ergonomics].*

### Decision 10 — Version bumps are owned by the joint `0.0.14` cut

No slice in this card edits the package-version state: `[project].version` in
[`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init], or
[`tests/base/test_init.py::test_version`][test-base-init]. This card **shares the
`0.0.14` patch line** with three sibling cards — [`DONE-042-0.0.14`][kanban],
[`DONE-043-0.0.14`][kanban], and [`DONE-044-0.0.14`][kanban] — so the
bump from `0.0.13` to `0.0.14` is owned by the **joint `0.0.14` cut** (the last
`0.0.14` card to land), the same posture [`spec-039`][spec-039] Decision 14 took
for the joint `0.0.13` cut. The release-status wording splits the same way
([`spec-039`][spec-039]'s release-vs-implementation-docs split): Slice 2 updates
**implemented-on-main** docs (the
GLOSSARY entry body, the regenerated [`docs/TREE.md`][tree]) but the public
`shipped (0.0.14)` status flip, the [`README.md`][readme] /
[`docs/README.md`][docs-readme] "Coming next" → "Shipped today" moves, and the
`CHANGELOG.md` bullets defer to the joint cut — otherwise the repo would advertise
a released `0.0.14` feature while `__version__` still reports `0.0.13`.

**`uv.lock` is NOT a version file — it is updated in this card, deliberately.** The
Slice-1 dependency gate adds `channels` to `[dependency-groups].dev` and
regenerates the lockfile in the same commit
([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard));
the **channels dependency entries** in `uv.lock` change here, while the package's
own `version` entry inside it stays `0.0.13` until the joint cut — the exact
reconciliation [`spec-039`][spec-039] Decision 14 pinned for the DRF dev-group
add.

Justification: per [`docs/SPECS/NEXT.md`][next] Step 3 / Step 6, when multiple
cards target one patch version the bump belongs to the joint cut, not any
individual card's spec. Four cards targeted `0.0.14` and this was the first of
them, so its slices leave the version line untouched.

*Alternatives rejected, with the reason each lost: [rationale companion][rationale-decision-10--joint-cut-version-ownership].*

### Decision 11 — The package request contract works under Channels: `request_from_info()` learns the Channels context shape (reads); auth *mutations* stay deferred

The transport alone is not enough for this package's own surfaces. Strawberry's
Channels consumers hand resolvers a **dict** context whose `"request"` slot is not
an `HttpRequest` — it carries the authenticated actor on an ASGI scope instead. The
package's shared request helper, [`request_from_info()`][utils-permissions],
accepted only the attribute shape `info.context.request` or a bare `HttpRequest`, so
a Channels context raised
[`ConfigurationError`][glossary-configurationerror]. The blast
radius is **every** framework surface routed through the helper, and several of
them hand the resolved request straight into consumer-written code:
[`FilterSet`][glossary-filterset]`._request_from_info` ([`filters/sets.py`][filters-sets]) and
[`OrderSet`][glossary-orderset]`._request_from_info` ([`orders/sets.py`][orders-sets]) pass it to
their `check_<field>_permission(self, request)` input gates (the
`(self, request)`-shaped filter / order gates — distinct from the planned
`info`-shaped [per-field read hooks][glossary-per-field-permission-hooks] on
`FieldSet`);
[`DjangoModelPermission`][glossary-djangomodelpermission]`.has_permission`
([`mutations/permissions.py`][mutations-permissions]) reads it; and
[`build_serializer_kwargs`][rf-resolvers] sets it as DRF's
`context["request"]`. The auth `current_user` query and the default
model-permission path need only `.user`, but those user-written hooks and
serializer overrides may read `request.headers`, `request.COOKIES`,
`request.path`, `request.method`, `request.consumer`, or any other attribute the
context value Strawberry handed them exposes. A router that ships "the
session transport" while the package's own request contract rejects — or
silently narrows — the transport's context would be an incoherent integration.

So this card fixes the root cause for the **read** half:

1. **`request_from_info()` recognizes the Channels shape and returns a
   *wrapping* adapter.** A mapping-style context carrying a `"request"` key whose
   value exposes an ASGI scope resolves to the [Channels request
   adapter][glossary-channels-request-adapter]. **Two scope shapes are recognized,
   both duck-typed** — `utils/permissions.py` imports nothing from `channels`, so
   the helper stays soft-dependency-clean: the HTTP consumer supplies a
   `ChannelsRequest` whose scope is at `consumer.scope`, and the WebSocket consumer
   supplies *itself*, with the scope directly at `scope`. Since this router serves
   no GraphQL `http` scope, the second is the shape its own traffic produces.
   Crucially, the adapter **wraps the original context value, it does not replace
   it with a two-field object**: it exposes `.user`, `.session`, and `.scope`
   explicitly from the scope, and **delegates every other attribute to the wrapped
   request via `__getattr__`**, so the user-code hooks above keep working
   instead of raising `AttributeError` only under Channels. This keeps the fix
   DRY without narrowing the framework request contract. A scope read that blows up
   — a hostile or broken mapping — becomes a
   [`ConfigurationError`][glossary-configurationerror] rather than escaping raw out
   of a request-resolution helper. The
   adapter is defined beside the helper, not in `routers.py` — it is a context
   shape, not a router feature, and it must work for consumers who wire
   Strawberry's Channels consumers *without* this card's router. The
   `family_label` parameter (and its family-named `ConfigurationError`
   messages) is preserved unchanged. This is a **hard single-siting rule**: no
   local request decoders in `routers.py`, `auth/queries.py`,
   `auth/mutations.py`, `rest_framework/resolvers.py`, or any permission gate —
   every new request shape is supported in
   [`request_from_info()`][utils-permissions] only (Helper-reuse D-P2).
2. **Auth *mutations* are out of this card** ([Decision 2](#decision-2--card-scope-boundary-the-transport-router-ships-websocket-auth-semantics-and-fakeshop-asgi-stay-out)):
   `login` / `logout` / `register` mutate the session through
   `django.contrib.auth` against an `HttpRequest`, and Channels ships its own
   async `channels.auth.login()` / `logout()` precisely because those semantics
   differ (session cycling against the scope). Wiring that is real auth-subsystem
   work with its own failure modes, and this card's documentation obligation is
   correspondingly sharp: the GLOSSARY [Auth mutations][glossary-auth-mutations]
   wording says `AuthMiddlewareStack` makes `scope["user"]` available and the
   package's *read* surfaces consume it, never that this card's work makes the
   session-mutating surfaces function over Channels. **The owner turned out to be
   [`spec-040`][spec-040] itself**: its [`auth/sessions.py`][auth-sessions]
   classifies a resolved request into one explicit transport and answers the
   capability question per transport, so `login` over a WebSocket is refused and
   `logout` is supported only on a server-side session engine. The read contract
   below is what that classification consumes; the mutating contract is stated in
   that spec.
3. **Proven by package-realistic communicator tests**, not just plain-Strawberry
   transport: a schema whose resolver reads the actor through
   `request_from_info()` executes through the router over the WebSocket branch
   (Test 16, forcing the adapter to exist and the delegation boundary to be
   exact — the test's resolver reads both a scope-backed attribute and a
   delegated one), and an **authenticated-session** round trip proves a real
   session actor flows through `AuthMiddlewareStack` to the resolver (Test 18),
   so the repeated "session user on the scope" claim is earned, not asserted.

*Alternatives rejected, with the reason each lost: [rationale companion][rationale-decision-11--the-channels-request-contract].*

## Implementation plan

The file-level delta map for the Worker 0 build handoff (each row's contract is
specified in the decisions cited; **no slice bumps the version** — the joint
`0.0.14` cut owns it,
[Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)):

| File | Change | Slice |
| --- | --- | --- |
| [`pyproject.toml`][pyproject] + `uv.lock` | `channels[daphne]>=4.3.2` into `[dependency-groups].dev`; lock regenerated in the same commit | 1 |
| [`utils/imports.py`][utils-imports] | `require_optional_module(module_name, *, install_hint)` added to the shared optional-import owner (no `feature_label`), + unit tests (Helper-reuse D-P1) | 1 |
| `django_strawberry_framework/routers.py` (new) | `__all__ = ("DjangoGraphQLProtocolRouter",)`; `_CHANNELS_INSTALL_HINT` + a separate builder-failure message per broken half, both interpolating the [`utils/imports.py`][utils-imports] floors / `require_channels()` (thin `require_optional_module` wrapper) / `_build_router_class()` caching in `_ROUTER_CLASS` behind a module-global lock / PEP 562 `__getattr__` → `DjangoGraphQLProtocolRouter`; the composition of [Decision 6](#decision-6--constructor-and-composition) ([Decision 3](#decision-3--the-symbol-is-djangographqlprotocolrouter--distinctly-ours-pinned-now) / [5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard) / [7](#decision-7--the-consumers-come-from-strawberrychannels-engine-owned-not-package-owned)) | 1 |
| [`utils/permissions.py`][utils-permissions] | `request_from_info()` Channels-context branch + a wrapping adapter over both scope shapes (`.user` / `.session` / `.scope` explicit and contained, `__getattr__` delegation) ([Decision 11](#decision-11--the-package-request-contract-works-under-channels-request_from_info-learns-the-channels-context-shape-reads-auth-mutations-stay-deferred)) | 1 |
| `tests/test_routers.py` (new) + helper unit tests | Tests 1–18 per the [Test plan](#test-plan) | 1 |
| [`docs/GLOSSARY.md`][glossary] | Router entry body + [Auth mutations][glossary-auth-mutations] deferral rewrite; status flips deferred | 2 |
| [`docs/TREE.md`][tree] | Regenerated (script-rendered) after the card flips Done | 2 |
| [`KANBAN.md`][kanban] / `KANBAN.html` | Card wrap via DB edit + re-render | 2 |

## Helper-reuse obligations (DRY)

The module is small enough that the DRY ledger is short; the discipline is the
[`spec-040`][spec-040] one — reuse is named per item, and deliberate *non*-reuse
carries its reason.

- [ ] **D1** — the channels-absent test reuses the eviction / restore /
  `builtins.__import__`-block pattern from
  [`tests/rest_framework/test_soft_dependency.py`][test-soft-dependency]
  (structure copied, target names swapped; if the copy turns out mechanical
  enough, extracting a shared `tests/` helper is an in-slice call — either way the
  discipline, not necessarily the code, is the obligation)
  ([Decision 8](#decision-8--test-strategy-package-tests-only-communicator-driven-execution-eviction-simulated-absence)).
- [ ] **D2** — the install-hint string lives in exactly one module constant
  (`_CHANNELS_INSTALL_HINT`), matched by substring in tests — the
  [`rf-init`][rf-init] `_DRF_INSTALL_HINT` shape. The **floor inside it is
  interpolated, never re-typed**: `CHANNELS_FLOOR` / `STRAWBERRY_FLOOR` live in
  [`utils/imports.py`][utils-imports] and each has exactly one other written copy,
  its own [`pyproject.toml`][pyproject] dependency row. A hard literal in a hint
  string is compared against nothing, so it drifts silently away from the metadata
  it is telling the consumer to install
  ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
- [ ] **D3** — the guard has **no memoization** and the `__getattr__` caches only
  the *built class* (not a successful guard result), so eviction-based absence
  tests can re-hit the guard — the non-memoizing contract from
  [`__init__.py`][init]'s root `__getattr__`, adapted: the class cache is the
  module global `_ROUTER_CLASS` and the lock serializing its first construction is
  a module global too, so a `sys.modules` eviction of `routers`
  naturally drops both with the module — **and the eviction discipline is
  two-sided**: the absence fixture saves/restores the parent package's
  `routers` attribute together with the `sys.modules` entries, restoring the
  original module object to *both* places, so no test order can leave the
  attribute path and the import path holding different module objects (and
  therefore different `_ROUTER_CLASS` caches). **The degraded-install test
  (Test 17) uses the same eviction + parent-attribute restore** *before*
  blocking a builder import: without evicting `routers`, an earlier
  construction test's cached `_ROUTER_CLASS` would satisfy the symbol access
  and the blocked import would never fire — the test must observe
  `_ROUTER_CLASS` unreachable because the module was re-executed, not mutated
  in place, making it order-independent under normal pytest order and
  `pytest-xdist`
  ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)
  / [Decision 8](#decision-8--test-strategy-package-tests-only-communicator-driven-execution-eviction-simulated-absence)).
- [ ] **D-P1** — the generic optional-import owner is
  **[`utils/imports.py`][utils-imports]**, which already exists
  (`import_attr_if_importable` / `loaded_attr`, migrated from
  `registry.py`'s co-clear helpers and `utils/inputs.py::_safe_import`).
  Slice 1 adds `require_optional_module(module_name, *, install_hint)` there
  (with its own unit tests) and `require_channels()` is a thin wrapper over it
  — `routers.py` must NOT hand-roll a fourth import-handling pattern. There is
  **no `feature_label`** parameter (the feature text lives in the caller's
  `install_hint`; an unused label is ceremony). The hint string itself stays
  single-sited in `routers.py` as `_CHANNELS_INSTALL_HINT` (D2). Migrating
  `require_drf()` onto the same primitive is a deliberate non-goal here (its
  hint is byte-pinned by `_HINT_SUBSTRING` tests; a separate follow-on)
  ([Decision 4](#decision-4--module-and-test-locations-a-top-level-routerspy-mirroring-both-upstreams-teststest_routerspy)
  / [Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
- [ ] **D-P2** — no local request decoders anywhere in this card: not in
  `routers.py`, not in auth queries/mutations, not in serializer-mutation
  kwargs, not in permission gates. The Channels context shape is adapted
  **once**, in [`request_from_info()`][utils-permissions], keeping the
  `family_label` error-message contract and delegating unrecognized attributes
  to the wrapped context value
  ([Decision 11](#decision-11--the-package-request-contract-works-under-channels-request_from_info-learns-the-channels-context-shape-reads-auth-mutations-stay-deferred)).
- [ ] **D-N1** (non-reuse) — the router must NOT route through
  [`strawberry_config`][glossary-strawberry_config] or touch the consumer's
  schema config: the schema arrives fully built and is passed to the consumers
  untouched — reshaping it here would silently change scalar registration for
  Channels deployments only.
- [ ] **D-N2** (non-reuse) — no reuse of Strawberry core's
  `GraphQLProtocolTypeRouter` as a base: the auth/validator composition happens
  *inside* the `ProtocolTypeRouter.__init__` mapping, so subclassing core's router
  would mean overwriting its entire mapping — inheritance with nothing inherited
  ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard),
  alternatives).

## Edge cases and constraints

- **`import django_strawberry_framework.routers` on a channels-less machine.**
  Succeeds (module-level code is the hint constant, the guard function, the
  builder, and `__getattr__`); only symbol access raises. The behavior matrix the
  tests pin: root package import → clean; `routers` module import → clean;
  `from ...routers import DjangoGraphQLProtocolRouter` → `ImportError` with hint;
  `dir()` / unrelated attribute access on the module → normal `AttributeError`
  for misses, never the channels hint.
- **`strawberry.channels` is the second import inside the boundary.** Its handlers
  import `channels.db` / `channels.generic.http` at module level (verified in the
  venv), so on a channels-less machine importing it raises
  `ModuleNotFoundError: channels` — which is why `require_channels()` runs
  *before* any `strawberry.channels` import in the builder: every absence routes
  through the single hint, never a bare engine-internal traceback.
- **`websocket_url_pattern` is a regex (`re_path`), WebSocket-branch only, and
  exact at both ends by default.** With Channels' `URLRouter` matching against the
  path with the leading slash stripped, the default `r"^graphql/?$"` matches
  `/graphql` and `/graphql/` and rejects `/graphql-admin`, `/graphqlanything` and
  `/graphql/extra`. HTTP path matching is entirely the Django URLconf's, so the two
  declarations are independent: a project that moves its GraphQL URL changes both.
  The rename from upstream's shared-prefix `url_pattern`, and the exact default, are
  [`spec-046`][spec-046] Decision 4's.
- **Non-GraphQL WebSocket paths are unrouted.** The `websocket` branch's
  `URLRouter` has one route; a WS connect to any other path raises Channels'
  "No route found" error and the connection drops. Parity with upstream; a
  consumer multiplexing other WS consumers composes `ProtocolTypeRouter` by hand.
- **No Channels middleware runs on HTTP at all.** `django_application` is the
  `"http"` value verbatim, so an HTTP request enters Django's own ASGI stack
  directly: Channels' cookie / session / auth middleware never touches it, and
  `ALLOWED_HOSTS`, CSRF, security headers and cache policy are the project's real
  `MIDDLEWARE`'s job, exactly as under WSGI. Upstream wraps its whole HTTP
  `URLRouter` — GraphQL route and Django fallback alike — in one
  `AuthMiddlewareStack`; the package deliberately does not
  ([`spec-046`][spec-046] Decisions 2 and 6).
- **`lifespan` scope.** Channels' `ProtocolTypeRouter` raises `ValueError` for
  scope types absent from the mapping. Uvicorn sends `lifespan` on startup and
  logs the failure as benign ("ASGI 'lifespan' protocol appears unsupported");
  Daphne never sends it. Parity with upstream — the router adds no `lifespan`
  entry, and the GLOSSARY body notes the uvicorn log line so consumers don't
  misread it as breakage.
- **`AuthMiddlewareStack` requires the session machinery.** It resolves the user
  from the session in the scope's cookies — `django.contrib.sessions` /
  `django.contrib.auth` in `INSTALLED_APPS` and the session backend configured.
  A sessionless project gets Channels' own error; the same constraint the shipped
  [Auth mutations][glossary-auth-mutations] document for the WSGI path, arising
  here from the middleware rather than the resolver.
- **`AllowedHostsOriginValidator` reads `ALLOWED_HOSTS`.** Consumer-facing note:
  a dev setup with `ALLOWED_HOSTS = []` under `DEBUG` gets Channels' hardcoded
  localhost set (`["localhost", "127.0.0.1", "[::1]"]` in
  `channels/security/websocket.py`, mirroring Django's own `DEBUG` runserver
  behavior — Channels' code, not Django's). That fallback branch is
  **unreachable in this package's own suite**: pytest-django defaults
  `DEBUG=False` and Django's `setup_test_environment` appends `"testserver"` to
  `ALLOWED_HOSTS`, so the WS test's matching `Origin` is `http://testserver` —
  asserted positively (matching origin connects) and negatively (mismatched
  origin is denied) in the test plan.
- **A WebSocket handshake with no `Origin` header is denied.** The router opts
  into `AllowedHostsOriginValidator`, and `OriginValidator.valid_origin`
  returns `False` when the handshake carries no `Origin` header at all, unless
  `ALLOWED_HOSTS` contains `"*"` (verified in `channels/security/websocket.py`:
  `if parsed_origin is None and "*" not in self.allowed_origins: return False`).
  So a non-browser WS client that omits `Origin` is rejected exactly like a
  mismatched one. This is stable across the declared Channels floor, so the
  test plan asserts it as a third origin direction (missing → denied); the
  in-suite `ALLOWED_HOSTS` is `["testserver", ...]`, never `"*"`.
- **The WebSocket consumer is async; sync ORM resolvers are NOT threadpooled.**
  `GraphQLWSConsumer` executes on the ASGI event loop, and Channels'
  `database_sync_to_async` wrapper is not in that path. Consequence: a sync
  resolver that touches the ORM over this router's socket raises Django's
  `SynchronousOnlyOperation`; the supported ORM path is the package's **async
  twins** (every shipped surface has both paths), and the communicator execution
  tests keep their resolvers either ORM-free or on the async path. An `async def`
  [`get_queryset`][glossary-get-queryset-visibility-hook] misuse under a sync surface still raises
  [`SyncMisuseError`][glossary-syncmisuseerror] exactly as under WSGI — the router
  changes transport, not resolver dispatch. (GraphQL over HTTP has no such
  constraint from this card: it runs through [`views.py`][views] under Django's own
  request lifecycle.)
- **Multipart uploads never reach this router.** [`Upload`][glossary-upload-scalar]-typed
  mutations arrive over HTTP, so they are parsed by
  [`views.py::DjangoGraphQLView`][views] under Django's own `MultiPartParser`;
  [`spec-046`][spec-046] Decisions 17 and 18 own that parsing contract and its
  bounds. This card asserts nothing about uploads, and there is no WebSocket upload
  path to assert about.
- **One Channels floor, and what it does and does not classify.** Per PyPI
  metadata, `4.2.1` (2025-03-29) is the first Channels release with the
  Django 5.2 classifier and `4.3.2` (2025-11-20) the first with Django 6.0.
  The install hint is the error message deployers follow, so the declared floor is
  the 6.0-classifying one: a lower "Django 5.2-compatible" floor would satisfy the
  resolver while stranding a Django 6.0 user in an unsupported Channels version.
  [`pyproject.toml`][pyproject] advertises `Framework :: Django :: 5.2`, `6.0` and
  `6.1`, and no Channels release at this floor carries a 6.1 classifier, so the
  floor's coverage reaches 6.0 and stops there. The value is
  [`utils/imports.py::CHANNELS_FLOOR`][utils-imports], written once more in
  [`pyproject.toml`][pyproject]'s `channels[daphne]` row and re-typed once, on
  purpose, in [`tests/test_routers.py`][test-routers] as the drift-catch. The
  Slice-1 gate re-verifies by running the suite, and if it disagrees all the naming
  sites move together.
- **`pytest-asyncio` already covers the communicator tests; DB-connection
  residue is Channels' own job, not pre-solved by the conftest fixture.** The
  dev group pins `pytest-asyncio>=1.0.0` and communicator tests are `async def`
  under the repo's existing asyncio configuration. On connections: the DB work
  in the router path comes from Channels' own middleware (`AuthMiddleware`'s
  user resolution rides `database_sync_to_async` — the consumer itself
  threadpools nothing, per the async-consumer edge case above), and Channels'
  `DatabaseSyncToAsync` brackets every call with `close_old_connections()`
  (verified in `channels/db.py` at `4.2.1`), so it cleans up after itself — and
  the [`tests/conftest.py`][tests-conftest] cleanup fixture would **not** catch
  what it might miss anyway (the fixture deliberately tracks only connections
  opened *under a running event loop*; `database_sync_to_async` runs ORM code
  on an executor thread with no loop, the category the fixture's own comment
  says it leaves untouched). If a communicator test surfaces a sqlite
  `ResourceWarning` regardless, it is fixed at source per the conftest
  precedent — never by weakening the suite's `-W error` posture.

## Test plan

All in `tests/test_routers.py` (placement per
[Decision 8](#decision-8--test-strategy-package-tests-only-communicator-driven-execution-eviction-simulated-absence)).
The schema used by execution tests is a small module-local `strawberry.Schema`
(a plain `Query` with a deterministic field is sufficient — router behavior is
schema-agnostic, and avoiding `DjangoType` keeps these tests out of the [registry
lifecycle][glossary-finalize-django-types] and off the async consumer's sync-ORM
edge). One test proves the schema (with its extensions) passes through
**unchanged** using a custom recording Strawberry extension rather than the
optimizer (Test 10, kept ORM-free so it cannot trip `SynchronousOnlyOperation`
under the async consumer), and one exercises the package's shared request helper
over the socket (Test 16 — the package-realistic migration risk, per
[Decision 11](#decision-11--the-package-request-contract-works-under-channels-request_from_info-learns-the-channels-context-shape-reads-auth-mutations-stay-deferred)).
The structural walk of the WebSocket wrapper chain (Test 4) lives behind small
intent-named test helpers — `unwrap_origin_validator()` / `unwrap_auth_stack()` — so
a future Channels internal reshape changes one helper, not several tests; the
assertions read as contract, not as attribute spelunking.

**Channels-present — construction and composition:**

1. The router is an instance of `channels.routing.ProtocolTypeRouter` and its
   `application_mapping` carries exactly `http` and `websocket` — framed as a
   **current-shape parity assertion** (upstream maps exactly these two), not as the
   primary source of truth: the behavior tests (7–10, 16, 18) are what the mapping
   must actually deliver, and a deliberate future addition (an explicit `lifespan`
   handler, say) moves this assertion with a recorded decision rather than failing
   mysteriously.
2. The `http` value **is** the supplied Django ASGI application, asserted by
   object identity — no wrapper of any kind around it.
3. Construction rejects an unusable `django_application`: `None` and any
   non-callable raise [`ConfigurationError`][glossary-configurationerror], omitting
   the argument raises `TypeError`. Separately, the router module carries **no**
   Strawberry HTTP consumer at all — asserted positively, so the removal cannot
   regress silently.
4. The `websocket` branch is `AllowedHostsOriginValidator`-wrapped **outside** the
   `AuthMiddlewareStack`, with the package's Host validator outside that again
   (wrapping order asserted). Assertion mechanics:
   `AllowedHostsOriginValidator` is a factory *function*, not a class — the
   isinstance target is the `OriginValidator` instance it returns, and that
   layer stores its wrapped app as `.application`; the middleware
   layers beneath it (`CookieMiddleware` / `SessionMiddleware` /
   `AuthMiddleware` — only the last subclasses `BaseMiddleware`) each carry
   `.inner`.
5. A custom `websocket_url_pattern=` reaches the WebSocket `re_path`, and reaches
   nothing else — there is no second branch for it to leak into.
6. Repeated symbol access returns the identical cached class (the builder
   memoizes into `_ROUTER_CLASS`), and the class is subclassable (a consumer
   extension smoke check). Concurrent first access from several threads still
   yields **one** class, the module-global lock being what makes that true.
   `routers.__all__ == ("DjangoGraphQLProtocolRouter",)`
   (the star-surface pin, [Decision 3](#decision-3--the-symbol-is-djangographqlprotocolrouter--distinctly-ours-pinned-now)).

**Channels-present — execution through communicators:**

7. A `WebsocketCommunicator` GraphQL round trip on the `graphql-transport-ws`
   subprotocol resolves a query against the real schema and returns the expected
   `data` (the full consumer round trip, handshake to payload).
8. An `HttpCommunicator` request proves the `http` branch is pure delegation: both
   a well-formed GraphQL POST and an unrelated path reach the supplied application
   (a minimal recording ASGI callable that answers with its own status), so no
   package route intercepts either.
9. `WebsocketCommunicator` connect on the `graphql-transport-ws`
   subprotocol: with a matching `Origin` header (`http://testserver`) the
   handshake is accepted; with a **mismatched** `Origin` it is denied; and with
   **no `Origin` header at all** it is denied (the three origin directions —
   `AllowedHostsOriginValidator` treats a missing origin as invalid unless
   `ALLOWED_HOSTS` contains `"*"`, [Edge cases](#edge-cases-and-constraints)). The
   `Host` directions belong to [`spec-046`][spec-046] Decision 19's own test plan,
   not to this one.
10. **Schema pass-through, proven without forcing sync ORM.** The router must
    hand the consumer's schema object to the consumer unchanged, not rebuild
    it. Both halves are asserted: structurally, the mounted WebSocket route's
    consumer holds the exact schema object passed in; behaviorally, a schema
    carrying a **custom Strawberry extension that records it executed** (no ORM, no
    `DjangoType`) runs an operation over the WebSocket branch and the recorder
    fires — proving the exact schema object (extensions intact) reached the
    consumer.
    `DjangoOptimizerExtension` is deliberately **kept out of this execution
    test**: under the async WebSocket consumer a real `DjangoType` / ORM
    resolver would trip the same `SynchronousOnlyOperation` edge case the spec
    documents, and a trivial optimizer-installed schema proves nothing about
    the optimizer anyway. The "a `strawberry_config()` +
    [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] schema is
    accepted and passed through" claim is the structural half above (the schema
    object the consumer holds `is` the one passed in). Real optimizer behavior
    under Channels — if ever wanted — is a
    separate async-ORM test with its own async-safe setup, not a ride-along
    here.

**Channels-absent (simulated via the eviction + import-block pattern):**

11. `import django_strawberry_framework` succeeds and
    `from django_strawberry_framework import *` binds no router name (the root
    package stays channels-free). By contrast, the **submodule** star import
    `from django_strawberry_framework.routers import *` raises the install-hint
    `ImportError` — `__all__` names the lazy symbol, so `import *` reaches for
    it and fires the guard ([Decision 3](#decision-3--the-symbol-is-djangographqlprotocolrouter--distinctly-ours-pinned-now)).
12. `import django_strawberry_framework.routers` succeeds.
13. `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`
    raises `ImportError` whose message names the Channels floor — matched
    against a **re-typed literal in the test file** (the
    [`test_soft_dependency.py`][test-soft-dependency] `_HINT_SUBSTRING`
    discipline): the deliberately independent copy is the drift-catch — a test
    importing `_CHANNELS_INSTALL_HINT` (or `CHANNELS_FLOOR`) and asserting the
    constant against itself could never notice the floor drifting away from the
    dev-group row. The gate moves the test literal together with the other naming
    sites.
14. After restore, the present-path access works again in the same process (no
    stale negative caching — the D3 obligation), **and** the attribute path and
    the import path resolve to the *same* module object and the *same* cached
    class — i.e. `django_strawberry_framework.routers is
    sys.modules["django_strawberry_framework.routers"]` after teardown (the
    two-sided restore of Decision 8; this is the assertion that makes Test 6's
    identity claim order-independent under `pytest-xdist`).
15. An unrelated attribute miss on the module raises plain `AttributeError`, not
    the channels hint.

**Channels-present — the package request contract
([Decision 11](#decision-11--the-package-request-contract-works-under-channels-request_from_info-learns-the-channels-context-shape-reads-auth-mutations-stay-deferred)):**

16. A schema whose resolver reads the acting user through the package's shared
    `request_from_info()` helper executes through the router over the WebSocket
    branch: the `AuthMiddlewareStack`-populated `scope["user"]`
    resolves through the Channels-context adapter (an anonymous handshake yields
    `AnonymousUser` — no session fixture needed; the assertion is that the
    helper *resolves* rather than raising `ConfigurationError`). The **same
    resolver also reads a delegated attribute** to prove the adapter's
    `__getattr__` delegation to the wrapped context value works end-to-end, not
    just the scope-backed fields. This is the package-realistic migration test:
    it proves a framework-shaped schema, not just plain Strawberry transport,
    runs under the router. The adapter's **unit-level shape tests** (both scope
    shapes recognized — `consumer.scope` and a bare `scope`; `.user` / `.session` /
    `.scope` exposed from the scope and defaulting to `None` when the middleware
    did not run; a *delegated* attribute returns the wrapped request's value; a fake
    permission method reading **one delegated and one scope-backed** attribute
    succeeds; a hostile scope contained into `ConfigurationError`; non-Channels
    shapes still rejected with the family-labeled `ConfigurationError`) live beside
    the helper's existing suite in
    [`tests/utils/test_permissions.py`][test-utils-permissions].

**Channels-present — the session actor over the handshake:**

18. **Authenticated-session round trip.** A user and session are created
    async-safely (`database_sync_to_async` / the test session store), and the
    session cookie rides the WebSocket handshake headers to a resolver that reads
    the actor via `request_from_info()`; the resolver sees the **authenticated**
    user, not `AnonymousUser`. This is what actually earns the repeated
    "session user on the scope" claim — Test 16 only proves the
    contract does not raise; Test 18 proves a real session actor flows through
    `AuthMiddlewareStack`.

**Channels-present-but-degraded (simulated partial installs):**

17. **Parametrized over the two builder halves**, each in its own case, using
    the **same module-eviction + parent-attribute-restore fixture as the
    absent path** so the re-executed `routers` module has no cached
    `_ROUTER_CLASS` and the blocked import actually fires (without the evict, an
    earlier construction test's cache would satisfy the access and the block
    would be a no-op, and the test order-dependent):
    - **(a) a blocked `channels.*` builder import** (evict `routers` + block
      `channels.security.websocket`): symbol access raises the actionable
      incompatibility `ImportError` naming the Channels floor;
    - **(b) a blocked `strawberry.channels` consumer import** (evict `routers` +
      block the `strawberry.channels` consumer symbol): symbol access raises the
      **separate** builder-failure `ImportError` naming **both** floors with the
      consumer importable — proving a broken Strawberry install is not misreported
      as a Channels problem.
    Both chain the original `ImportError` (`__cause__`), never a bare transitive
    error at what would be ASGI-startup time ([Error shapes](#error-shapes)).

Coverage: the package gate is `fail_under = 100`; the builder body, both branches
of the guard, **both** incompatible-install wrap messages (channels-half and
strawberry-half), the `__getattr__` hit/miss paths, the constructor's accept and
reject branches, and the `request_from_info()`
Channels-shape branch (plus the wrapping adapter's explicit, delegated and
contained-read paths) are all reached by the list above.

## Doc updates

Slice 2 splits the doc work the way
[Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut) splits the
version: implemented-on-main docs update in this card; release-status wording
defers to the joint `0.0.14` cut:

- [`docs/GLOSSARY.md`][glossary] — the
  [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] entry body
  grows the implemented contract: the constructor signature, the
  composition, the soft-dependency behavior matrix
  (import clean / access raises / hint text), the WebSocket pattern's regex
  semantics, the `lifespan` note, and the see-also edges to
  [Auth mutations][glossary-auth-mutations] (session transport) and
  [`TestClient`][glossary-testclient] (the sibling card). Status **stays**
  `planned for 0.0.14` until the joint cut.
- [`docs/TREE.md`][tree] — regenerated via
  [`scripts/build_tree_md.py`][build-tree-md] after the card flips Done (the file
  is script-rendered; missing module docstrings fail the render, so `routers.py`'s
  docstring is written for its row): the package tree's `routers.py` planned
  annotation resolves to the real row; the test tree gains `tests/test_routers.py`.
- [`KANBAN.md`][kanban] / `KANBAN.html` — card wrap via the DB + re-render (Slice 2
  checklist).
- **Deferred to the joint cut:** [`README.md`][readme] / [`docs/README.md`][docs-readme]
  "Coming next — remaining alpha (`0.0.14`)" → "Shipped today" moves, the GLOSSARY
  status flip + package-version line, [`TODAY.md`][today]'s coming-next wording,
  and `CHANGELOG.md` (which additionally requires the explicit maintainer grant per
  [`AGENTS.md`][agents]).

## Risks and open questions

Every risk this card carried was a preferred-answer / fallback pair about a question
the build has since answered, so none of them is a live contract. They are recorded,
with what each one turned out to be, in the
[rationale companion][rationale-risks] — including the Channels-floor verification,
the auth-mutation half (whose eventual owner was not either candidate this card
named), the authenticated-session harness, and the standing posture on asserting
against Channels' composed middleware objects.

## Out of scope (explicitly tracked elsewhere)

- **`TestClient` / `GraphQLTestCase` helpers** — [`DONE-043-0.0.14`][kanban]
  ([`TestClient`][glossary-testclient] / [`GraphQLTestCase`][glossary-graphqltestcase]);
  this card's tests use Channels' own communicators, not those helpers.
- **Debug-toolbar middleware** — [`DONE-042-0.0.14`][kanban]
  ([Debug-toolbar middleware][glossary-debug-toolbar-middleware]).
- **Response-extensions debug middleware** — [`DONE-044-0.0.14`][kanban]
  ([Response-extensions debug middleware][glossary-response-extensions-debug-middleware]).
- **Auth-*mutation* execution over a Channels scope** (the session-mutating
  half; the read-path request contract ships in this card per
  [Decision 11](#decision-11--the-package-request-contract-works-under-channels-request_from_info-learns-the-channels-context-shape-reads-auth-mutations-stay-deferred))
  — owned by [`spec-040`][spec-040], whose [`auth/sessions.py`][auth-sessions]
  classifies the transport and answers `login` / `logout` per transport. This card
  adds no login-mutation test and states no part of that contract.
- **The GraphQL HTTP endpoint, the transport body and encoding bounds, the
  WebSocket Host boundary, the consumer-injection seam and the revalidation
  window** — all [`spec-046`][spec-046]'s
  ([`DONE-046-0.0.14`][kanban]). This spec states the shape they leave on
  `routers.py`; that spec states their contracts.
- **Fakeshop ASGI activation / Channels acceptance lane** — the
  fakeshop-activation card [`TODO-BETA-062-0.1.5`][kanban] if ever.
- **Subscriptions as a package surface** — no card; the router transports whatever
  the consumer's schema defines.
- **The migration guide itself** — [`TODO-BETA-068-0.1.8`][kanban]; this card only
  hands it the one-row symbol mapping
  ([Decision 9](#decision-9--migration-ergonomics-live-in-the-migration-guide-row-not-the-symbol-name)).
- **The `0.0.14` version bump and release-status flips** — the joint `0.0.14` cut
  ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).

## Definition of done

- [ ] `django_strawberry_framework/routers.py` exists, with module + symbol
      docstrings, exposing `DjangoGraphQLProtocolRouter` via the lazy
      `__getattr__` + `require_channels()` guard (a thin wrapper over
      `utils/imports.py::require_optional_module`, added there with unit
      tests — Helper-reuse D-P1)
      ([Decision 3](#decision-3--the-symbol-is-djangographqlprotocolrouter--distinctly-ours-pinned-now)
      / [Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
- [ ] `channels` is a soft dependency: `import django_strawberry_framework` and
      `import django_strawberry_framework.routers` succeed without it;
      symbol access raises `ImportError` carrying the single install hint naming
      the verified floor (the card's DoD, sharpened by
      [Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
- [ ] `routers.py` defines `__all__ = ("DjangoGraphQLProtocolRouter",)`, so
      `from ...routers import *` exposes only the router (and opts into the
      guard when channels is absent); `require_optional_module` takes no
      `feature_label`
      ([Decision 3](#decision-3--the-symbol-is-djangographqlprotocolrouter--distinctly-ours-pinned-now)
      / Helper-reuse D-P1).
- [ ] The constructor and the composition match
      [Decision 6](#decision-6--constructor-and-composition) exactly: `schema`
      positional, `django_application` required and the `"http"` value verbatim,
      every other parameter keyword-only; the `websocket` branch carrying the
      auth stack inside the origin validator inside the Host validator, over one
      `re_path` matched by `websocket_url_pattern`.
- [ ] **`channels[daphne]`** at the verified floor (or the floor the Slice-1 gate
      proves, moving all naming sites together) is in `[dependency-groups].dev`
      with `uv.lock` regenerated in the same commit; the dev-group specifier and
      [`utils/imports.py::CHANNELS_FLOOR`][utils-imports] — which every install
      hint interpolates — agree on the **single** floor, and that value is the
      first Channels release carrying the `Framework :: Django :: 6.0`
      classifier. [`pyproject.toml`][pyproject]'s advertised Django range also
      lists `6.1`, which no Channels release at this floor classifies.
- [ ] The Strawberry-floor gate ran: the `strawberry.channels` consumer the
      builder imports — not the unused `GraphQLProtocolTypeRouter` — confirmed
      importable at the pinned `strawberry-graphql` floor
      ([`pyproject.toml`][pyproject], single-sited for the package's own hints as
      [`utils/imports.py::STRAWBERRY_FLOOR`][utils-imports]) in an isolated
      throwaway venv (never the shared `.venv`), or the project's Strawberry floor
      was bumped instead; the command and outcome are recorded in the build
      artifact.
- [ ] `tests/test_routers.py` covers both dependency states per the
      [Test plan](#test-plan) — including at least one real `WebsocketCommunicator`
      GraphQL round trip, an `HttpCommunicator` row proving the `http` branch is
      pure delegation, **all three** origin-validator directions (match /
      mismatch / missing), the **package-realistic request-contract round
      trip** with a delegated-attribute read (Test 16), the
      **authenticated-session round trip** (Test 18), and **both** degraded
      partial-install error shapes (channels-half and strawberry-half, Test 17)
      — and the package coverage gate (`fail_under = 100`) holds with
      `routers.py` included.
- [ ] `request_from_info()` resolves Strawberry's Channels context: the
      mapping-shaped context, **both** ASGI scope shapes (`consumer.scope` and a
      bare `scope`), and a **wrapping** adapter that
      exposes `.user` / `.session` / `.scope` and **delegates other attributes
      to the wrapped request via `__getattr__`** (so user permission hooks and
      DRF serializer overrides keep reading `request.headers` / `.COOKIES` /
      etc. under Channels), with unit tests beside the helper's
      suite and no `channels` import added to `utils/`
      ([Decision 11](#decision-11--the-package-request-contract-works-under-channels-request_from_info-learns-the-channels-context-shape-reads-auth-mutations-stay-deferred)).
- [ ] The migration-guide handoff row content is recorded for
      [`TODO-BETA-068-0.1.8`][kanban]
      (`AuthGraphQLProtocolTypeRouter` → `DjangoGraphQLProtocolRouter`, **not** a
      drop-in: `django_application` required, `websocket_url_pattern`, plus the
      URLconf entry for [`views.py::DjangoGraphQLView`][views])
      ([Decision 9](#decision-9--migration-ergonomics-live-in-the-migration-guide-row-not-the-symbol-name)).
- [ ] Slice 2 doc updates land per [Doc updates](#doc-updates): the GLOSSARY entry
      body (status flip deferred), the regenerated [`docs/TREE.md`][tree], and the
      kanban card wrap (DB edit + re-render).
- [ ] The [Auth mutations][glossary-auth-mutations] GLOSSARY deferral sentence is
      re-worded to the honest post-router state: the router ships the session
      transport and the package's read-path request contract consumes it, without
      claiming this card verified session-mutating auth over Channels.
- [ ] **No slice bumps the version** — `pyproject.toml` / `__version__` /
      [`tests/base/test_init.py`][test-base-init] still read `0.0.13` when this
      card flips Done; the joint `0.0.14` cut owns the bump
      ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).
- [ ] `uv run ruff format .` / `ruff check --fix .` clean; no `pytest` beyond the
      slices' own test additions unless the maintainer asks (the
      [`START.md`][start] workflow rule).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[pyproject]: ../../pyproject.toml
[readme]: ../../README.md
[start]: ../../START.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[glossary-auth-mutations]: ../GLOSSARY.md#auth-mutations
[glossary-channels-request-adapter]: ../GLOSSARY.md#channels-request-adapter
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-debug-toolbar-middleware]: ../GLOSSARY.md#debug-toolbar-middleware
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangographqlprotocolrouter]: ../GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangomodelpermission]: ../GLOSSARY.md#djangomodelpermission
[glossary-djangomutationfield]: ../GLOSSARY.md#djangomutationfield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-eviction-simulated-absence]: ../GLOSSARY.md#eviction-simulated-absence
[glossary-fielderror-envelope]: ../GLOSSARY.md#fielderror-envelope
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-get-queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-graphqltestcase]: ../GLOSSARY.md#graphqltestcase
[glossary-joint-version-cut]: ../GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: ../GLOSSARY.md#live-first-coverage-mandate
[glossary-orderset]: ../GLOSSARY.md#orderset
[glossary-pep-562-lazy-export]: ../GLOSSARY.md#pep-562-lazy-export
[glossary-per-field-permission-hooks]: ../GLOSSARY.md#per-field-permission-hooks
[glossary-request-from-info]: ../GLOSSARY.md#request_from_info
[glossary-require-optional-module]: ../GLOSSARY.md#require_optional_module
[glossary-response-extensions-debug-middleware]: ../GLOSSARY.md#response-extensions-debug-middleware
[glossary-serializermutation]: ../GLOSSARY.md#serializermutation
[glossary-soft-dependency]: ../GLOSSARY.md#soft-dependency
[glossary-strawberry_config]: ../GLOSSARY.md#strawberry_config
[glossary-syncmisuseerror]: ../GLOSSARY.md#syncmisuseerror
[glossary-testclient]: ../GLOSSARY.md#testclient
[glossary-upload-scalar]: ../GLOSSARY.md#upload-scalar
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[next]: NEXT.md
[rationale]: appx/spec-041-channels_router-0_0_14-rationale.md
[rationale-decision-1--spec-filename-and-canonical-naming]: appx/spec-041-channels_router-0_0_14-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-decision-10--joint-cut-version-ownership]: appx/spec-041-channels_router-0_0_14-rationale.md#decision-10--joint-cut-version-ownership
[rationale-decision-11--the-channels-request-contract]: appx/spec-041-channels_router-0_0_14-rationale.md#decision-11--the-channels-request-contract
[rationale-decision-2--card-scope-boundary]: appx/spec-041-channels_router-0_0_14-rationale.md#decision-2--card-scope-boundary
[rationale-decision-3--the-symbol-name]: appx/spec-041-channels_router-0_0_14-rationale.md#decision-3--the-symbol-name
[rationale-decision-4--module-and-test-locations]: appx/spec-041-channels_router-0_0_14-rationale.md#decision-4--module-and-test-locations
[rationale-decision-5--soft-channels-dependency]: appx/spec-041-channels_router-0_0_14-rationale.md#decision-5--soft-channels-dependency
[rationale-decision-6--constructor-and-composition]: appx/spec-041-channels_router-0_0_14-rationale.md#decision-6--constructor-and-composition
[rationale-decision-7--engine-owned-consumers]: appx/spec-041-channels_router-0_0_14-rationale.md#decision-7--engine-owned-consumers
[rationale-decision-8--test-strategy]: appx/spec-041-channels_router-0_0_14-rationale.md#decision-8--test-strategy
[rationale-decision-9--migration-ergonomics]: appx/spec-041-channels_router-0_0_14-rationale.md#decision-9--migration-ergonomics
[rationale-risks]: appx/spec-041-channels_router-0_0_14-rationale.md#risks-and-open-questions
[spec-021]: spec-021-apps-0_0_7.md
[spec-039]: spec-039-serializer_mutations-0_0_13.md
[spec-040]: spec-040-auth_mutations-0_0_13.md
[spec-046]: spec-046-transport_security-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-sessions]: ../../django_strawberry_framework/auth/sessions.py
[conf]: ../../django_strawberry_framework/conf.py
[consumers]: ../../django_strawberry_framework/consumers.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[init]: ../../django_strawberry_framework/__init__.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[rf-init]: ../../django_strawberry_framework/rest_framework/__init__.py
[rf-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[views]: ../../django_strawberry_framework/views.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-list-field]: ../../tests/test_list_field.py
[test-routers]: ../../tests/test_routers.py
[test-soft-dependency]: ../../tests/rest_framework/test_soft_dependency.py
[test-utils-permissions]: ../../tests/utils/test_permissions.py
[tests-conftest]: ../../tests/conftest.py

<!-- examples/ -->
[config-wsgi]: ../../examples/fakeshop/config/wsgi.py
[test-query-readme]: ../../examples/fakeshop/test_query/README.md

<!-- scripts/ -->
[build-kanban-md]: ../../scripts/build_kanban_md.py
[build-tree-md]: ../../scripts/build_tree_md.py

<!-- .venv/ -->

<!-- External -->
[cookbook-recipes-schema]: ../../../django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py
[upstream-routers]: ../../../strawberry-django-main/strawberry_django/routers.py
