# Spec: Channels ASGI router — `DjangoGraphQLProtocolRouter` in a soft-`channels` `routers.py`, the one-import ASGI / WebSocket migration aid

Planned for `0.0.14` (card [`WIP-ALPHA-041-0.0.14`][kanban]). This card adds the
package's **Channels transport helper**: a new `django_strawberry_framework/routers.py`
module exposing `DjangoGraphQLProtocolRouter` — a `channels.routing.ProtocolTypeRouter`
subclass that wires GraphQL onto **both** HTTP and WebSocket in one import, with
Django's `AuthMiddlewareStack` (so `scope["user"]` / the session machinery is present
on both protocols) and Channels' `AllowedHostsOriginValidator` (the WebSocket
origin check) composed in. It is a Required 🍓 `strawberry-graphql-django` parity item
(the card's own tag): [`strawberry_django/routers.py`][upstream-routers] ships
`AuthGraphQLProtocolTypeRouter`, a module whose class is ~30 lines of composition and the **single import**
making ASGI / WebSocket migration painless — without an equivalent, a
`strawberry-graphql-django` migrant using Channels loses their one-line ASGI
entrypoint and must hand-compose `ProtocolTypeRouter` / `URLRouter` /
`AuthMiddlewareStack` / `AllowedHostsOriginValidator` over Strawberry's Channels
consumers themselves. This card exists **primarily to reduce migration friction, not
to expand the API surface** (the card's own "Why it matters"); `graphene-django`
ships no Channels router at all, so this is honest single-upstream parity, the same
posture [`spec-040`][spec-040] took for the auth module.

The helper is deliberately **thin and engine-riding**: the GraphQL consumers come
from Strawberry core (`strawberry.channels`'s `GraphQLHTTPConsumer` /
`GraphQLWSConsumer` — already inside the package's pinned
`strawberry-graphql>=0.262.0` floor — export presence verified at the installed
`strawberry-graphql` 0.316.0; the floor-version presence is upstream history,
re-confirmed at the Slice-1 dependency gate), the routing
and middleware layers (classes and factory functions) come from `channels`, and the package contributes exactly the
composition — the same composition upstream ships — under a **distinctly-ours symbol
name** ([Decision 3](#decision-3--the-symbol-is-djangographqlprotocolrouter--distinctly-ours-pinned-now)).
`channels` is a **soft dependency**
([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)):
`import django_strawberry_framework` and `import django_strawberry_framework.routers`
both succeed without it, and the install-hint `ImportError` fires only when a
consumer actually reaches for the router symbol — the generalization of the
[`SerializerMutation`][glossary-serializermutation] soft-DRF pattern
([`spec-039`][spec-039] Decision 12) to a second optional integration.

**Version boundary** (see
[Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)): this
card **shares the `0.0.14` patch line** with three open siblings —
[`TODO-ALPHA-042-0.0.14`][kanban] ([Debug-toolbar
middleware][glossary-debug-toolbar-middleware]), [`TODO-ALPHA-043-0.0.14`][kanban]
([`TestClient`][glossary-testclient] / [`GraphQLTestCase`][glossary-graphqltestcase]),
and [`TODO-ALPHA-044-0.0.14`][kanban] ([Response-extensions debug
middleware][glossary-response-extensions-debug-middleware]) — verified against the
re-rendered board, where all four sit in `## In progress` with `041` the sole WIP. So
the `pyproject.toml` / `__version__` /
[`tests/base/test_init.py::test_version`][test-base-init] bump from `0.0.13` to
`0.0.14` is owned by the **joint `0.0.14` cut** (the last `0.0.14` card to land), not
by this card — the same shared-cut posture [`spec-039`][spec-039] Decision 14 took
for the joint `0.0.13` cut. No slice below bumps the version.

Status: **PLANNED — no slice built yet.**
Two slices (the card is a deliberate S): Slice 1 (**the dependency gate +
`routers.py` + `tests/test_routers.py`** — the `channels` dev-group add with the
lockfile regenerated, the soft-dependency guard, the router class, and both the
channels-present and channels-absent test paths land in one commit), and Slice 2
(**docs + card wrap** — the implemented-contract doc updates, the regenerated
[`docs/TREE.md`][tree], and the kanban card flip; the release-status wording and the
version bump stay deferred to the joint cut).

Owner: package maintainer.

Predecessors: [`spec-040-auth_mutations-0_0_13.md`][spec-040] (the
most-recently-shipped spec and the canonical voice / depth / section-layout
reference; also the card whose [Auth mutations][glossary-auth-mutations] surface
explicitly deferred "Channels / websocket auth" to **this** router card — a handoff
this spec scopes honestly in
[Decision 2](#decision-2--card-scope-boundary-the-transport-router-ships-websocket-auth-semantics-and-fakeshop-asgi-stay-out)
and [Risks](#risks-and-open-questions));
[`spec-039-serializer_mutations-0_0_13.md`][spec-039] (the soft-dependency
architecture this card generalizes — the single `require_*()` guard with one
install-hint string, the dev-group + lockfile dependency gate, the
absence-simulated-by-eviction test discipline, and the joint-cut version Decision
this spec mirrors); [`spec-021-apps-0_0_7.md`][spec-021] (the package's
Django-integration surface conventions the new top-level module sits beside).
[`docs/GLOSSARY.md`][glossary] carries
[`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] as `planned for
0.0.14`; Slice 2 updates the entry body to the implemented contract while the
`shipped (0.0.14)` status flip rides the joint cut.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft authored from the [`WIP-ALPHA-041-0.0.14`][kanban]
  card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-07-03). Pinned: the
  canonical structured filename
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)); the card-scope
  boundary — the transport router ships, WebSocket-auth mutation semantics and a
  fakeshop ASGI surface stay out, no new `Meta` / settings key
  ([Decision 2](#decision-2--card-scope-boundary-the-transport-router-ships-websocket-auth-semantics-and-fakeshop-asgi-stay-out));
  the `DjangoGraphQLProtocolRouter` symbol name pinned now, resolving the card's
  "final name pinned during implementation" hedge in favor of the name the card,
  the [`docs/GLOSSARY.md`][glossary] entry, and the migration-guide handoff row all
  already carry
  ([Decision 3](#decision-3--the-symbol-is-djangographqlprotocolrouter--distinctly-ours-pinned-now));
  the top-level `routers.py` module + `tests/test_routers.py` mirror
  ([Decision 4](#decision-4--module-and-test-locations-a-top-level-routerspy-mirroring-both-upstreams-teststest_routerspy));
  the soft-`channels` guard as a lazy module `__getattr__` materializing the class
  behind one `require_channels()` guard, with the `channels>=4.2.0` dev-group add
  (floor corrected to `4.2.1` in Revision 2) + lockfile regeneration as the
  Slice-1 dependency gate
  ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard));
  the constructor signature held byte-compatible with upstream
  (`(schema, django_application=None, url_pattern="^graphql")`) and the middleware
  composition borrowed as-is
  ([Decision 6](#decision-6--constructor-parity-schema-django_applicationnone-url_patterngraphql-composition-borrowed-as-is));
  the GraphQL consumers reused from `strawberry.channels`, never subclassed or
  re-implemented
  ([Decision 7](#decision-7--the-consumers-come-from-strawberrychannels-engine-owned-not-package-owned));
  the package-tests-only placement justified as genuinely-unreachable-live, with
  communicator-driven real execution
  ([Decision 8](#decision-8--test-strategy-package-tests-only-communicator-driven-execution-eviction-simulated-absence));
  the migration-guide one-row handoff to [`TODO-BETA-056-0.1.6`][kanban]
  ([Decision 9](#decision-9--migration-ergonomics-live-in-the-migration-guide-row-not-the-symbol-name));
  and the joint-cut version deferral
  ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).
  One handoff tension is carried into [Risks](#risks-and-open-questions) rather than
  silently reconciled: the shipped [Auth mutations][glossary-auth-mutations] GLOSSARY
  wording promises "Channels / websocket auth" coverage to this card, but the card's
  own DoD is transport-only — the preferred reading (transport now, auth-over-Channels
  compatibility verified separately) is named there.
- **Revision 2** — applied an adversarial claim-verification review pass (every
  finding re-verified against the Channels `4.2.1` source / changelog, the
  installed strawberry 0.316.0, and the package's own conftest / DRF-guard
  sources before editing). **Build-critical fixes:** **(P1, daphne)** the
  Slice-1 dependency gate gains a **test-only `daphne`** dev-group entry —
  `channels/testing/__init__.py` unconditionally imports `.live`, whose
  module-level `from daphne.testing import DaphneProcess` makes every import
  path to the (themselves in-process, daphne-free) communicators fail without
  it; the shipped `routers.py` never imports daphne and the install hint stays
  channels-only
  ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)
  / [Decision 8](#decision-8--test-strategy-package-tests-only-communicator-driven-execution-eviction-simulated-absence)).
  **(P1, floor)** the channels floor moves `4.2.0` → **`4.2.1`** across every
  naming site — per the Channels changelog, `4.2.0` (2024-11-15) predates
  Django 5.2 entirely; `4.2.1` (2025-03-29) is the first release with official
  Django 5.2 support and `4.3.2` (2025-11-20) the first confirming Django 6.0,
  so the declared floor is `4.2.1` and the dev-resolved version must be
  `>=4.3.2` for the CI matrix's Django 6.0 leg; Test 13 pins the corrected
  floor as a **re-typed literal in the test file** (the
  `test_soft_dependency.py` `_HINT_SUBSTRING` drift-catch discipline — a test
  asserting the imported constant against itself could never notice the hint
  drifting from the dev-group floor), closing the Test-13-vs-DoD placeholder
  inconsistency
  ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)
  / [Risks](#risks-and-open-questions) / [Test plan](#test-plan)
  / [Definition of done](#definition-of-done)). **Implementation-trap fixes:**
  **(P2, two-sided restore)** the channels-absent fixture's eviction discipline
  is made two-sided — the blocked-then-retried import re-executes `routers.py`
  and rebinds the parent package's `routers` attribute to a fresh module
  object, so restoring only `sys.modules` would leave the attribute path and
  the import path holding two live modules with independent class caches (an
  order-dependent Test-6 identity flake under `pytest-xdist`); the fixture now
  saves/restores the parent attribute alongside the `sys.modules` entries
  (restoring the original module object to both places, the DRF fixture's
  `delattr` precedent extended), and Test 14 asserts the post-teardown
  same-object invariant
  ([Decision 8](#decision-8--test-strategy-package-tests-only-communicator-driven-execution-eviction-simulated-absence)
  / [Helper-reuse D3](#helper-reuse-obligations-dry) / [Test plan](#test-plan)).
  **(P2, conftest attribution)** the communicator-test DB-connection edge case
  no longer credits the [`tests/conftest.py`][tests-conftest] cleanup fixture —
  that fixture deliberately tracks only connections opened under a running
  event loop, while Channels' `database_sync_to_async` runs ORM code on a
  no-loop executor thread (the category the fixture's own comment leaves
  untouched); the actual mechanism is Channels' `DatabaseSyncToAsync`
  bracketing every call with `close_old_connections()` (verified in
  `channels/db.py`), and any residue a communicator test surfaces is fixed at
  source, never by weakening `-W error`
  ([Edge cases](#edge-cases-and-constraints)). **Wording fixes:** **(P3)**
  "verified in the checked-out venv" claims now name the installed strawberry
  **0.316.0** explicitly (the 0.262.0-floor presence is upstream history,
  re-confirmed at the dependency gate), and the `AllowedHostsOriginValidator`
  edge case attributes the empty-`ALLOWED_HOSTS`-under-`DEBUG` localhost set to
  **Channels' hardcoded list** in `channels/security/websocket.py` (mirroring
  Django's runserver behavior), not to Django itself
  ([Edge cases](#edge-cases-and-constraints)). The review also **confirmed
  correct** (no change needed): the upstream composition/signature reading, the
  graphene-django no-router sweep (single-upstream parity holds), the
  `require_drf()` / root-`__getattr__` mirror claims, the PEP 562
  `from ... import` → `__getattr__` → propagated-`ImportError` behavior matrix,
  the `URLRouter` leading-slash-strip claim, Channels' `ProtocolTypeRouter`
  `ValueError`-on-unmapped-scope (`lifespan`) behavior, and the
  auth-over-Channels risk framing (upstream's `auth/utils.py` reads
  `request.consumer.scope["user"]` — the request-shape divergence is real).
- **Revision 3** — a second, independent adversarial review pass (reviewer
  verified the Channels claims against the `4.2.1` **and** `4.3.2` sdists plus
  PyPI release metadata; every finding re-verified against the sources before
  editing; no blockers, four precision fixes). **(P3, factory-not-class)**
  `AllowedHostsOriginValidator` (and `AuthMiddlewareStack`) are factory
  *functions*, not classes — Test 4's isinstance target is the returned
  `OriginValidator` instance, whose outermost hop is `.application` (only the
  `BaseMiddleware` layers beneath carry `.inner`); Test 4 and the Risks
  structural-assertion note now say so
  ([Test plan](#test-plan) / [Risks](#risks-and-open-questions)). **(P3,
  suite-vs-consumer DEBUG note)** the localhost-fallback edge case is split
  into its consumer-facing half and an explicit "unreachable in this suite"
  note — pytest-django defaults `DEBUG=False` and `setup_test_environment`
  appends `"testserver"` to `ALLOWED_HOSTS` (both verified in the installed
  packages), so Test 9's matching `Origin` is `http://testserver`, never the
  localhost set ([Edge cases](#edge-cases-and-constraints)). **(P3, stale
  quotes)** the two `docs/TREE.md` row quotes updated `TODO-ALPHA-041` →
  `WIP-ALPHA-041` (the Slice-2 board re-render moved the annotation with the
  card id; the substance — the row is reserved — was already correct), and the
  intro's "~30-line module" tightened to "~30 lines of composition" (the
  upstream file is 73 lines; the class body is the ~30). The pass also
  re-confirmed Revision 2's floor facts independently (4.2.1 first with the
  Django 5.2 classifier, 4.3.2 first with Django 6.0, via PyPI metadata — the
  sdists ship no changelog) and the full verified-correct set (upstream parity
  line-by-line, the daphne import chain, `close_old_connections` bracketing,
  the PEP 562 behavior matrix, the graphene-django zero-channels sweep, link
  targets on disk).

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary
used throughout the spec:

- [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] — the
  subject. The glossary already pins the planned contract: a Channels
  `ProtocolTypeRouter`-wrapping helper with a soft `channels` dependency and a
  symbol name intentionally distinct from `strawberry-django`'s
  `AuthGraphQLProtocolTypeRouter`. Slice 2 updates the entry body to the
  implemented contract (the status flip to `shipped (0.0.14)` rides the joint cut).
- [`SerializerMutation`][glossary-serializermutation] — the soft-dependency
  precedent. Its `require_drf()` guard, single install-hint string, lazy
  name-resolution through a PEP 562 `__getattr__`, and eviction-simulated absence
  tests are the architecture
  [Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)
  generalizes.
- [Auth mutations][glossary-auth-mutations] — the shipped `0.0.13` session-auth
  surface whose GLOSSARY entry defers "Channels / websocket auth" to this card. The
  router's `AuthMiddlewareStack` is what puts the session user on the Channels
  scope; whether the auth *mutations* run through the Channels HTTP consumer is a
  scoped open question ([Risks](#risks-and-open-questions)).
- [`TestClient`][glossary-testclient] / [`GraphQLTestCase`][glossary-graphqltestcase]
  — the `0.0.14` sibling card (`TODO-ALPHA-043-0.0.14`) whose helpers own
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
module is ~30 lines of composition upstream and stays that size here; the weight is
in the soft-dependency discipline and its tests. There is **no live fakeshop slice**:
the fakeshop example is WSGI-only ([`config/wsgi.py`][config-wsgi] is its only
entrypoint; no `asgi.py` exists), so no `/graphql/` HTTP request can reach a Channels
router — the package-tests placement is the documented
genuinely-unreachable-live case, not a live-first weakening
([Decision 8](#decision-8--test-strategy-package-tests-only-communicator-driven-execution-eviction-simulated-absence)).

- [ ] **Slice 1 — dependency gate + `routers.py` + `tests/test_routers.py`**
  - [ ] **The dependency gate lands first, in the same commit** (the
        [`spec-039`][spec-039] Slice-0 discipline): `channels>=4.2.1` **and
        `daphne`** added to `[dependency-groups].dev` in
        [`pyproject.toml`][pyproject] and `uv.lock` regenerated together
        (`uv lock`), so the declared and locked dev environments never diverge.
        `daphne` is **test-only**: `channels/testing/__init__.py`
        unconditionally imports `.live`, whose module-level
        `from daphne.testing import DaphneProcess` makes the (themselves
        daphne-free, in-process) communicators unimportable without it — the
        shipped `routers.py` never touches daphne and the install hint stays
        channels-only. The floor is re-verified at this gate by running the
        suite (`4.2.1` is the first Channels release with official Django 5.2
        support per the Channels changelog; the dev-resolved version must be
        `>=4.3.2`, the first release confirming Django 6.0, to clear the CI
        matrix's Django 6.0 leg) and the three-places-that-must-agree rule
        applies: the dev-group specifier, the install-hint string, and this
        spec's [Risks](#risks-and-open-questions) note all name the same floor
        ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
  - [ ] `django_strawberry_framework/routers.py` (new) — the `require_channels()`
        guard (function-local imports, one `_CHANNELS_INSTALL_HINT` string, no
        memoization), the module-level PEP 562 `__getattr__` that materializes and
        caches the `DjangoGraphQLProtocolRouter` class on first access (guard
        first, then the class body subclassing
        `channels.routing.ProtocolTypeRouter`), and the composition itself —
        HTTP: `AuthMiddlewareStack(URLRouter([graphql, *django_fallback]))`;
        WebSocket:
        `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([graphql])))` —
        over `strawberry.channels`'s `GraphQLHTTPConsumer` / `GraphQLWSConsumer`
        ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)
        / [Decision 6](#decision-6--constructor-parity-schema-django_applicationnone-url_patterngraphql-composition-borrowed-as-is)
        / [Decision 7](#decision-7--the-consumers-come-from-strawberrychannels-engine-owned-not-package-owned)).
        No package-root re-export; the consumer path is
        `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`
        ([Decision 3](#decision-3--the-symbol-is-djangographqlprotocolrouter--distinctly-ours-pinned-now)).
  - [ ] `tests/test_routers.py` (new) — **channels-present**: construction /
        composition assertions (a `ProtocolTypeRouter` instance; `http` +
        `websocket` mapping keys; the middleware wrapping order; the
        `django_application` fallback present / absent; a custom `url_pattern`),
        plus real execution through Channels' own communicators — an
        `HttpCommunicator` GraphQL POST through the router resolving a query, and
        a `WebsocketCommunicator` connect on the `graphql-transport-ws`
        subprotocol passing the origin validator. **channels-absent**: the
        eviction + `builtins.__import__`-block pattern from
        [`tests/rest_framework/test_soft_dependency.py`][test-soft-dependency] —
        `import django_strawberry_framework` and
        `import django_strawberry_framework.routers` both succeed;
        `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`
        raises `ImportError` carrying the install hint; the root package import
        stays channels-free — with the absence fixture saving/restoring the
        **parent package's `routers` attribute alongside** the `sys.modules`
        entries (the blocked-then-retried import re-executes `routers.py` and
        rebinds the parent attribute to a fresh module object; restoring only
        `sys.modules` would leave two live module objects with independent
        class caches, an order-dependent flake under `pytest-xdist`)
        ([Test plan](#test-plan)).
  - [ ] Every new symbol carries its docstring (the [`docs/TREE.md`][tree] render
        fails on missing module docstrings) and any staged-but-not-implemented
        seam carries a `TODO(spec-041 Slice N)` source anchor per
        [`AGENTS.md`][agents].
- [ ] **Slice 2 — docs + card wrap (no version bump)**
  - [ ] [`docs/GLOSSARY.md`][glossary]
        [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]
        entry body updated to the implemented contract (constructor signature, the
        auth-stack / origin-validator composition, the soft-dependency behavior
        matrix, the WSGI-fakeshop non-demonstration note); the **status stays
        `planned for 0.0.14`** until the joint cut flips it
        ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).
  - [ ] [`docs/TREE.md`][tree] regenerated via
        [`scripts/build_tree_md.py`][build-tree-md] (never hand-edited): the
        `routers.py` row moves from `planned by WIP-ALPHA-041-0.0.14` to the real
        docstring-derived row, and `tests/test_routers.py` appears in the test
        tree.
  - [ ] [`KANBAN.md`][kanban] card wrap: `WIP-ALPHA-041-0.0.14` → Done with the
        next `DONE-041-0.0.14` id and its `SpecDoc` pointing at this spec (kanban
        DB edit + [`scripts/build_kanban_md.py`][build-kanban-md] /
        `build_kanban_html.py` re-render, never a hand-edit).
  - [ ] **Deferred to the joint `0.0.14` cut** (not this slice): the version
        quintet (`pyproject.toml`, `__version__`,
        [`tests/base/test_init.py::test_version`][test-base-init], the GLOSSARY
        package-version line, the `django-strawberry-framework` `version` entry in
        `uv.lock`), the GLOSSARY status flip to `shipped (0.0.14)`, the
        [`README.md`][readme] / [`docs/README.md`][docs-readme] "Coming next" →
        "Shipped today" moves, and the `CHANGELOG.md` bullets. Per
        [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly
        instructed", the `CHANGELOG.md` edit additionally requires the joint-cut
        slice's maintainer prompt to grant it explicitly; this spec describes the
        edit but cannot grant the permission.

## Problem statement

A Django team running Channels (WebSockets, or simply an ASGI deployment that wants
one process for HTTP + WS) has to compose four pieces to serve GraphQL:
`channels.routing.ProtocolTypeRouter` over an HTTP `URLRouter` and a WebSocket
`URLRouter`, Strawberry's Channels consumers (`GraphQLHTTPConsumer` /
`GraphQLWSConsumer`) as the route targets, `channels.auth.AuthMiddlewareStack` so the
session user is on the scope, and `channels.security.websocket.AllowedHostsOriginValidator`
so cross-origin WebSocket connections are rejected. None of it is hard, all of it is
boilerplate, and every consumer who writes it by hand gets to re-discover the two
non-obvious parts (the origin validator belongs on the WebSocket branch only; the
Django ASGI fallback belongs on the HTTP branch only).

`strawberry-graphql-django` absorbs that boilerplate in
[`strawberry_django/routers.py`][upstream-routers]: `AuthGraphQLProtocolTypeRouter`,
a ~30-line `ProtocolTypeRouter` subclass with the exact composition above, consumed
as one import in the project's `asgi.py`. The card carries the Required 🍓 parity tag
for exactly that module (the [`KANBAN.md`][kanban] #"Decision: Alpha cards must claim
upstream parity" rule; `graphene-django` predates the Strawberry Channels story and
ships **no** router, so this is single-upstream parity — honest, not fabricated).
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
  [Decision 2](#decision-2--card-scope-boundary-the-transport-router-ships-websocket-auth-semantics-and-fakeshop-asgi-stay-out)
  and carried in [Risks](#risks-and-open-questions).
- **The version line reads `0.0.13`, and three siblings share `0.0.14`.**
  `TODO-ALPHA-042` / `043` / `044` are all non-Done at this card's patch version, so
  the joint-cut rule applies
  ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).

## Goals

1. **Ship the one-import ASGI entrypoint.** A consumer's `asgi.py` becomes:
   construct Django's ASGI app, import the schema, and instantiate
   `DjangoGraphQLProtocolRouter(schema, django_application=django_asgi)` — HTTP
   GraphQL, WebSocket GraphQL, session auth on both, origin validation on WS, and
   the Django fallback for every other HTTP path
   ([Decision 6](#decision-6--constructor-parity-schema-django_applicationnone-url_patterngraphql-composition-borrowed-as-is)).
2. **Keep `channels` soft.** `import django_strawberry_framework` (and
   `from django_strawberry_framework import *`) must succeed and stay
   channels-free; the install-hint `ImportError` fires only when the consumer
   actually reaches for the router
   ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
3. **One-line migration.** A `strawberry-graphql-django` migrant changes exactly
   one import — `from strawberry_django.routers import AuthGraphQLProtocolTypeRouter`
   → `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter` —
   with zero call-site changes (the constructor signature is held byte-compatible),
   and the rename is documented in the migration guide's symbol-equivalents table
   ([Decision 9](#decision-9--migration-ergonomics-live-in-the-migration-guide-row-not-the-symbol-name)).
4. **Both dependency states tested.** `tests/test_routers.py` exercises the
   channels-present path (construction, composition, and real communicator-driven
   execution) and the channels-absent path (the guarded `ImportError`), keeping
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
  puts the session user **on the scope** (transport); making the `0.0.13` auth
  *mutations* function through a Channels consumer's request object is a separate
  question this card only scopes ([Risks](#risks-and-open-questions)).
- **A fakeshop ASGI surface.** No `asgi.py`, no `channels` in the example's runtime
  path, no live `/graphql/` Channels tests. A future fakeshop ASGI dogfooding pass
  belongs with the fakeshop-activation card ([`TODO-BETA-053-0.1.5`][kanban]) if the
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
- **Sync-consumer or per-consumer knobs.** `strawberry.channels` also ships
  `SyncGraphQLHTTPConsumer`; upstream's router does not expose it and neither does
  this card. A consumer with exotic consumer needs composes `ProtocolTypeRouter`
  by hand — the escape hatch is the underlying machinery, not more constructor
  parameters.

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it?" test this card is
**single-upstream parity**: `strawberry-graphql-django` ships
[`routers.py`][upstream-routers]; `graphene-django` ships no ASGI/Channels helper at
all. The card's `Verified in upstream` section names one file and it was read in
full for this spec, together with the Strawberry-core router it subclasses
alongside (`strawberry/channels/router.py`, from the checked-out venv) — the
comparison between the two is what isolates this card's actual value-add.

### From `strawberry-graphql-django` — borrow the composition, verbatim

[`AuthGraphQLProtocolTypeRouter`][upstream-routers] is `ProtocolTypeRouter` over:

- **HTTP** — `AuthMiddlewareStack(URLRouter([re_path(url_pattern,
  GraphQLHTTPConsumer.as_asgi(schema=schema)), re_path(r"^", django_application)
  if provided]))`. The Django fallback is HTTP-branch-only, appended after the
  GraphQL route so the regex ordering resolves correctly.
- **WebSocket** — `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([
  re_path(url_pattern, GraphQLWSConsumer.as_asgi(schema=schema))])))`. The origin
  validator is WS-branch-only (browsers enforce same-origin on fetch/XHR; the
  WebSocket handshake needs the explicit server-side check).
- **Signature** — `(schema, django_application=None, url_pattern="^graphql")`.

All three are borrowed as-is
([Decision 6](#decision-6--constructor-parity-schema-django_applicationnone-url_patterngraphql-composition-borrowed-as-is)).
The delta against Strawberry core's `GraphQLProtocolTypeRouter` (same consumers,
same signature, **no** `AuthMiddlewareStack`, **no** origin validator) is exactly
the Django-auth composition — which is why the package ships its own helper instead
of pointing consumers at the engine's: a Django-framework package whose auth
mutations ([`spec-040`][spec-040]) assume the session user is resolvable should hand
out the transport that makes that true on both protocols.

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

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django_asgi = get_asgi_application()

from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter

from myproject.schema import schema

application = DjangoGraphQLProtocolRouter(
    schema,
    django_application=django_asgi,
)
```

That routes every HTTP and WebSocket request matching `^graphql` to Strawberry's
Channels consumers over `schema` — with Django sessions and `scope["user"]`
available on both protocols and cross-origin WebSocket handshakes rejected against
`ALLOWED_HOSTS` — and every other HTTP request to the normal Django ASGI
application. The constructor:

```python
DjangoGraphQLProtocolRouter(
    schema,                      # the strawberry.Schema (extensions ride along)
    django_application=None,     # optional ASGI fallback for non-GraphQL HTTP paths
    url_pattern="^graphql",      # re_path regex for the GraphQL endpoint
)
```

Consumer-visible behavior:

- **The schema is used as-is.** A schema built with
  [`strawberry_config()`][glossary-strawberry_config] and
  [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] keeps both — the
  router hands the schema object to the consumers untouched.
- **`django_application` is the HTTP fallback only.** Omitted, non-GraphQL HTTP
  paths have no route (Channels raises its no-route error); provided, they resolve
  through Django's stack (admin, static in dev, the WSGI-era views). Non-GraphQL
  **WebSocket** paths are never routed — parity with upstream.
- **Migration is the one import line.** Same positional schema, same
  `django_application=`, same `url_pattern=` default:

  ```diff
  - from strawberry_django.routers import AuthGraphQLProtocolTypeRouter
  + from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter

  - application = AuthGraphQLProtocolTypeRouter(schema, django_application=django_asgi)
  + application = DjangoGraphQLProtocolRouter(schema, django_application=django_asgi)
  ```

- **Without `channels` installed**, the `from django_strawberry_framework.routers
  import DjangoGraphQLProtocolRouter` line raises `ImportError` with the install
  hint naming the verified floor — at the consumer's `asgi.py` import, the first
  moment the symbol is actually reached for, never at
  `import django_strawberry_framework`.

### Error shapes

- **`channels` absent** — `ImportError` from the symbol access, message naming the
  package and floor (working text, single-sited in `_CHANNELS_INSTALL_HINT`):
  `"DjangoGraphQLProtocolRouter requires channels, which is not installed. Install
  it with `pip install 'channels>=4.2.1'` (the package's verified Channels
  floor)."` — the exact wording mirrors the DRF hint's shape so the two soft
  dependencies fail identically.
- **Cross-origin WebSocket** — the handshake is denied by
  `AllowedHostsOriginValidator` (connection closed before the GraphQL protocol
  starts); this is Channels' behavior, surfaced here because the router opts into
  it deliberately.
- **Unroutable scope types** (e.g. `lifespan` from uvicorn) — Channels'
  `ProtocolTypeRouter` raises its own `ValueError` for scope types with no mapping;
  parity with upstream, documented in [Edge cases](#edge-cases-and-constraints).

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

This spec lives at `docs/spec-041-channels_router-0_0_14.md`: card NNN `041`, topic
slug `channels_router` (the card's subject — the Channels ASGI router), version
segment `0_0_14` from the card's trailing `-0.0.14`. Follows the
[`docs/SPECS/NEXT.md`][next] convention.

Alternatives considered (and rejected):

- **`spec-041-routers-0_0_14.md`.** Rejected: the module name alone under-describes
  the card (a future card could touch routing again); the slug names the feature.
- **`spec-041-asgi_router-0_0_14.md`.** Rejected: "Channels" is the load-bearing
  noun — the card, the GLOSSARY entry, and the upstream module are all
  Channels-specific; a hypothetical non-Channels ASGI story would be a different
  card.

### Decision 2 — Card-scope boundary: the transport router ships; WebSocket-auth semantics and fakeshop ASGI stay out

This card ships exactly the card's DoD: the `routers.py` module, the soft
dependency, the two test paths, and the migration-guide handoff row. Three
adjacent-looking pieces of work are explicitly out:

- **Auth-mutations-over-Channels.** The [Auth mutations][glossary-auth-mutations]
  GLOSSARY entry defers "Channels / websocket auth" to this card, but the card's
  DoD is transport-only. The router **does** deliver the transport half — with
  `AuthMiddlewareStack` on both branches, `scope["user"]` is populated and the
  session machinery is present. Whether the shipped `login` / `logout` / `register`
  / `me` resolvers **function** through `GraphQLHTTPConsumer`'s request object
  (upstream carries a `channels_auth` fallback precisely because the Channels
  request differs from a Django `HttpRequest`) is a verification question, not a
  transport question — carried in [Risks](#risks-and-open-questions) with a
  preferred answer rather than silently absorbed into this card's scope.
- **Fakeshop ASGI activation.** Out per
  [Decision 8](#decision-8--test-strategy-package-tests-only-communicator-driven-execution-eviction-simulated-absence).
- **No new `Meta` / settings key.** The router takes constructor arguments; nothing
  reads [`conf.py`][conf]. The `START.md` rule ("add a settings key only when the
  feature that needs it lands") — no feature here needs one.

Justification: the card body is explicit that this is a "pure migration-aid card"
and "small slice"; scope creep into auth semantics would entangle an S transport
card with the auth subsystem's request-shape contract, and the
[`START.md`][start] advice ("resist scope creep... don't quietly mix in
while-I'm-here extras") applies verbatim.

Alternatives considered (and rejected):

- **Fold auth-over-Channels verification into this card.** Rejected: it requires
  the full `graphql-transport-ws` / Channels-HTTP request-shape analysis of the
  auth resolvers' `request_from_info` path — real work with its own failure modes,
  invisible in the card's S sizing. The honest move is the scoped risk entry.
- **Add the fakeshop `asgi.py` now for dogfooding.** Rejected: it drags `channels`
  into the example's runtime and the live suite is WSGI `django.test.Client` —
  the new surface would be dead weight until a Channels-aware acceptance harness
  exists ([`TODO-BETA-053-0.1.5`][kanban] territory).

### Decision 3 — The symbol is `DjangoGraphQLProtocolRouter` — distinctly ours, pinned now

The card pre-pins the architectural posture ("must use a **distinctly-ours symbol
name** (working name: `DjangoGraphQLProtocolRouter`) so the module is unambiguously
ours and does not impersonate the upstream API") and hedges the final name to
implementation time. This spec resolves the hedge: the name is
`DjangoGraphQLProtocolRouter`, now. Three surfaces already carry it — the card
body, the [`docs/GLOSSARY.md`][glossary]
[`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] entry (with
its own anchor other docs link), and the migration-guide handoff row's mapping
text — so any other choice would ripple through shipped docs for zero consumer
benefit. The name reads as the package's own family (`Django*` prefix like
[`DjangoConnectionField`][glossary-djangoconnectionfield] / [`DjangoMutationField`][glossary-djangomutationfield]), drops upstream's `Auth` prefix
(the auth stack is part of the composition, not the headline — the headline is
"the GraphQL protocol router for Django"), and drops upstream's `Type` infix
(`ProtocolTypeRouter` is Channels' internal naming; the package's consumer never
thinks about "protocol types").

No package-root re-export: the consumer path is
`from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`,
mirroring the [`spec-040`][spec-040] Decision 3 structural-opt-in posture (a
consumer who never deploys ASGI never types the import) and keeping
[`__init__.py`][init]'s `__all__` channels-free by construction.

Alternatives considered (and rejected):

- **`AuthGraphQLProtocolTypeRouter` verbatim.** Rejected by the card itself: the
  module would impersonate the upstream API — the [`GOAL.md`][goal] "thin wrapper"
  non-goal. Migration ergonomics are preserved by the guide row instead
  ([Decision 9](#decision-9--migration-ergonomics-live-in-the-migration-guide-row-not-the-symbol-name)).
- **A shorter `DjangoGraphQLRouter`.** Rejected: it erases the one term
  (`Protocol`) that signals "this routes multiple ASGI protocols" — the class's
  entire reason to exist over a plain URL router — and diverges from both
  upstream names at once, making the migration-guide row harder to eyeball.
- **A lazy package-root export (the `SerializerMutation` shape).** Rejected:
  `SerializerMutation` is a *write base* consumers subclass in schema modules,
  where a root import is idiomatic; the router is deployment plumbing typed in
  exactly one file (`asgi.py`). The submodule path is self-documenting there, and
  keeping the root namespace free of transport symbols keeps the `__getattr__`
  map single-purpose (DRF names only).

### Decision 4 — Module and test locations: a top-level `routers.py` mirroring both upstreams; `tests/test_routers.py`

The module is `django_strawberry_framework/routers.py` — a top-level module, not a
package. Both upstream shapes agree (`strawberry_django/routers.py`;
`strawberry/channels/router.py`), the content is one class plus one guard (~60
lines with docstrings), and [`docs/TREE.md`][tree]'s target layout already reserves
exactly this path against this card. The tests are the card-named
`tests/test_routers.py` — a top-level test module beside
[`tests/test_list_field.py`][test-list-field] and its peers, matching the
one-source-module-one-test-module convention the root tree uses for top-level
modules (the `tests/auth/` package-per-subpackage shape applies to subpackages,
which this is not).

Alternatives considered (and rejected):

- **A `channels/` or `integrations/` subpackage.** Rejected: one class does not
  justify a package; upstream keeps it flat; and [`docs/TREE.md`][tree]'s planned
  row (a shipped commitment in the docs) names the flat path. `strawberry_django`'s
  `integrations/` holds third-party *library* adapters (guardian), not transport.
- **Colocating the guard in `rest_framework/__init__.py` as a generic
  `require_soft_dependency(name, hint)`.** Rejected for now: two call sites with
  different hint strings and different import targets don't yet earn an
  abstraction, and the DRF guard's docstring contract is deliberately
  DRF-specific. If the `0.0.14` siblings add a third soft dependency, promotion to
  `utils/` is the follow-on — noted in
  [Helper-reuse obligations](#helper-reuse-obligations-dry) as D-P1, not built
  speculatively.

### Decision 5 — Soft `channels` dependency: a lazy module `__getattr__` + one `require_channels()` guard

`channels` joins `djangorestframework` as the package's second soft dependency, with
the same three-part architecture ([`spec-039`][spec-039] Decision 12, generalized):

1. **One guard, one hint.** `routers.py` defines `require_channels()` — a
   function-local `import channels` wrapped, on `ImportError`, into a new
   `ImportError` carrying the single `_CHANNELS_INSTALL_HINT` string (naming
   `channels>=4.2.1`, the verified floor). No memoization: each access re-fires
   the guard so the absence test can evict modules and re-hit it, exactly the
   [`require_drf()`][rf-init] contract.
2. **A lazy class, materialized on first access.** The class body subclasses
   `channels.routing.ProtocolTypeRouter`, so it **cannot** be defined at module
   import without paying the import. `routers.py` therefore defines the class
   inside a builder (`_build_router_class()`, module-cached) and exposes it via a
   PEP 562 **module-level `__getattr__`**: accessing
   `routers.DjangoGraphQLProtocolRouter` runs `require_channels()`, builds (or
   returns the cached) class, and hands it out. `import
   django_strawberry_framework.routers` itself imports nothing optional — the
   module stays importable everywhere (introspection, `docs/TREE.md` rendering,
   coverage collection), and the install-hint fires at the earliest moment the
   consumer *actually reaches for the router* (their `from ... import` line in
   `asgi.py`). The builder's imports cover both halves of the boundary:
   `channels.routing` / `channels.auth` / `channels.security.websocket` **and**
   `strawberry.channels` (whose handlers import `channels.db` at module level —
   verified at the installed strawberry 0.316.0 — so it is equally unimportable
   without channels; `require_channels()` runs first so every absence routes
   through the one hint).
3. **The dependency gate.** Slice 1 adds `channels>=4.2.1` **and `daphne`** to
   `[dependency-groups].dev` and regenerates `uv.lock` in the same commit (the
   [`spec-039`][spec-039] Decision 14 lockfile discipline: a dev-dependency edit
   without the regenerated lock leaves declared and locked environments out of
   sync). `daphne` is test-only — Channels' `testing/__init__.py`
   unconditionally imports `.live`, whose module-level
   `from daphne.testing import DaphneProcess` makes every import path to the
   communicators fail without it, even though the communicators themselves are
   in-process and daphne-free (verified against the Channels `4.2.1` source);
   the shipped `routers.py` never imports daphne and the install hint stays
   channels-only. The floor is changelog-grounded (`4.2.1` is the first release
   with official Django 5.2 support; `4.3.2` the first confirming Django 6.0,
   so the dev-resolved version must be `>=4.3.2` for the CI matrix's Django 6.0
   leg) and re-verified at the gate by running the suite; three places must
   agree on it — the dev-group specifier, the `_CHANNELS_INSTALL_HINT` string,
   and this spec's [Risks](#risks-and-open-questions) note.

The class-identity consequence is deliberate: because the real
`ProtocolTypeRouter` subclass is what the `__getattr__` returns, a
channels-present consumer gets a true subclass (subclassable, `isinstance`-able,
attribute-compatible with upstream's), never a stub pretending.

Alternatives considered (and rejected):

- **A hard dependency.** Rejected: the overwhelming majority of Django GraphQL
  deployments are WSGI-or-plain-ASGI without Channels; taxing every consumer with
  `channels` (which drags `asgiref` pins and an app-config) for a migration aid
  inverts the card's purpose. Upstream can hard-import; an integration package
  whose pitch includes "the package imports with zero optional dependencies"
  cannot.
- **A `django-strawberry-framework[channels]` extra.** Rejected: an extra changes
  how consumers *install*, not whether the import is guarded — the guard is needed
  regardless (an extra is advisory; nothing stops an extra-less install from
  importing the module), so the extra adds a second thing to document without
  removing any code. The DRF precedent (no `[drf]` extra) already set this.
- **A module-import-time guard (`require_channels()` at `routers.py` top level, the
  literal `rest_framework/__init__.py` shape).** Rejected: it makes
  `import django_strawberry_framework.routers` itself raise, which (a) breaks
  innocent whole-package walkers (the [`docs/TREE.md`][tree] docstring renderer,
  coverage tooling, IDE indexers) on a channels-less machine, and (b) contradicts
  the card's own DoD wording — "top-level package import must not fail... raises
  `ImportError` with an install hint **when it is actually called**". The
  `rest_framework/` package could afford import-time because its import is itself
  the opt-in; a top-level module sitting in the package's own directory cannot.
- **A stub class whose `__init__` raises when channels is absent.** Rejected: it
  reads the DoD's "when actually called" most literally, but the stub lies about
  identity — it is not a `ProtocolTypeRouter`, cannot be subclassed meaningfully,
  and produces a confusing two-phase failure (import succeeds, deploy fails). The
  `__getattr__` shape fails at the consumer's import-from line — earlier, with the
  same hint, and the returned object is never a lie.
- **Depending on Strawberry core's router and re-exporting it wrapped.** Rejected:
  core's `GraphQLProtocolTypeRouter` lacks the auth stack and origin validator —
  the entire value-add — and wrapping-then-mutating someone else's router class is
  exactly the "thin wrapper" smell; composing Channels' primitives directly is the
  same line count and honest.

### Decision 6 — Constructor parity: `(schema, django_application=None, url_pattern="^graphql")`; composition borrowed as-is

The constructor signature is held **byte-compatible** with
[`AuthGraphQLProtocolTypeRouter`][upstream-routers] (and, coincidentally but
usefully, with Strawberry core's router): positional `schema`, keyword
`django_application=None`, keyword `url_pattern="^graphql"`. A migrating call site
changes zero characters after the import line — that is the whole card
([Goal 3](#goals)). The composition is upstream's, verbatim:

- `http` → `AuthMiddlewareStack(URLRouter(http_urls))` where `http_urls` is the
  GraphQL `re_path(url_pattern, GraphQLHTTPConsumer.as_asgi(schema=schema))`
  followed by `re_path(r"^", django_application)` when provided.
- `websocket` → `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([
  re_path(url_pattern, GraphQLWSConsumer.as_asgi(schema=schema))])))`.

Typing follows upstream's honest version: `django_application: ASGIHandler | None`
under `TYPE_CHECKING` (Strawberry core's own router annotates it `str | None`,
which is simply wrong — the value is an ASGI callable; the package does not copy
the typo), and `schema: BaseSchema` under `TYPE_CHECKING` (any Strawberry schema,
not a package-specific one — the router must accept the consumer's real schema
object with whatever extensions it carries).

Alternatives considered (and rejected):

- **Making `django_application` required.** Rejected: upstream's optional default
  supports the GraphQL-only ASGI process (a dedicated GraphQL service behind a
  router that sends everything else elsewhere); requiring it breaks that
  deployment and the byte-compatibility goal.
- **A `path`-style (non-regex) `url_pattern`.** Rejected: `re_path` semantics are
  upstream's contract and the byte-compat goal pins them; a `graphql` regex also
  matches `/graphql/` (the trailing-slash form the fakeshop example uses), which a
  literal `path("graphql")` would not.
- **Adding an `allowed_hosts=` / `enable_auth=` knob set.** Rejected: upstream
  ships none; every knob is a divergence the migration-guide row would have to
  explain; and the escape hatch (compose `ProtocolTypeRouter` by hand) already
  exists for consumers who need a different stack.

### Decision 7 — The consumers come from `strawberry.channels`, engine-owned, not package-owned

`GraphQLHTTPConsumer` and `GraphQLWSConsumer` are imported (inside the guard
boundary) from `strawberry.channels` — Strawberry core's Channels handlers, present
at the package's pinned `strawberry-graphql>=0.262.0` floor (verified in the
installed strawberry 0.316.0: `strawberry/channels/__init__.py` exports both —
the export's presence at the 0.262.0 floor itself is upstream history, spot-checked
at the dependency gate). The package
defines **no** consumer subclass: the engine owns request parsing, multipart
handling, and the WS protocol state machines, exactly as it owns query execution
under the WSGI view. This is the standing "Strawberry stays as the engine" line
from [`README.md`][readme] applied to transport.

Alternatives considered (and rejected):

- **Subclassing the consumers to inject package context (e.g. a
  request-normalization shim for the auth mutations).** Rejected: that is the
  auth-over-Channels work [Decision 2](#decision-2--card-scope-boundary-the-transport-router-ships-websocket-auth-semantics-and-fakeshop-asgi-stay-out)
  scoped out; doing it silently inside the router would change auth behavior with
  no card, no tests, and no GLOSSARY story.
- **Vendoring upstream `strawberry_django`'s consumers.** Rejected: upstream's
  routers use Strawberry core's consumers too (verified — its imports are
  `strawberry.channels.handlers.*`); there is nothing `strawberry_django`-specific
  to vendor.

### Decision 8 — Test strategy: package tests only, communicator-driven execution, eviction-simulated absence

All tests live in `tests/test_routers.py`. The live-first mandate
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
executes a real GraphQL query through the router — a POST through the `http`
branch resolving against a real `strawberry.Schema`, and a WebSocket handshake
through the `websocket` branch passing the origin validator. That earns the
composition lines with actual protocol traffic instead of `isinstance` checks
(the [`START.md`][start] "coverage is a feature" posture). One import-graph
caveat the dependency gate absorbs: the communicators themselves are in-process
and daphne-free, but `channels/testing/__init__.py` unconditionally imports
`.live` (whose module top level does `from daphne.testing import
DaphneProcess`), so **importing** them requires `daphne` — hence the test-only
`daphne` dev-group entry in
[Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard);
`routers.py` itself never touches daphne. The channels-absent path reuses the
[`test_soft_dependency.py`][test-soft-dependency] discipline verbatim: absence
is **simulated** by a `builtins.__import__` block plus strict `sys.modules`
eviction (both `channels*` and `django_strawberry_framework.routers`) with full
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

Alternatives considered (and rejected):

- **Adding a fakeshop `asgi.py` + a Channels acceptance lane.** Rejected in
  [Decision 2](#decision-2--card-scope-boundary-the-transport-router-ships-websocket-auth-semantics-and-fakeshop-asgi-stay-out);
  additionally, the live suite's fixtures (session cookies, `create_users`,
  `CaptureQueriesContext`) are all WSGI-client-shaped — a parallel ASGI harness is
  a card of its own, not a rider.
- **Structural assertions only (no communicators).** Rejected: it would leave the
  consumers' `as_asgi` wiring and the middleware ordering unexercised — precisely
  the lines a composition module exists for. If the composition is wrong (origin
  validator on the wrong branch, fallback before the GraphQL route), only traffic
  notices.
- **Uninstall-based absence testing (a separate no-channels CI job).** Rejected:
  the DRF precedent already chose simulation (one env, one run, no matrix), and
  the repo's test invocation is a single `uv run pytest` gate.

### Decision 9 — Migration ergonomics live in the migration-guide row, not the symbol name

The card's DoD hands [`TODO-BETA-056-0.1.6`][kanban] (Migration and adoption
guides) a one-row entry for its "symbol equivalents" table:
`strawberry_django.routers.AuthGraphQLProtocolTypeRouter` →
`django_strawberry_framework.routers.DjangoGraphQLProtocolRouter`, with the note
that the constructor signature is unchanged. That row is the **single canonical
location** for the rename story — this spec and the GLOSSARY entry describe the
mapping, but the guide owns the migrant-facing table. Because the guide card is
Beta-scheduled and this card ships first, the handoff is recorded here (and on the
card's own reference edge, already in the kanban DB) rather than edited into a
guide that does not exist yet; the interim migrant-facing surface is the GLOSSARY
entry's "intentionally distinct from" sentence, which already ships.

Alternatives considered (and rejected):

- **Shipping a compatibility alias (`AuthGraphQLProtocolTypeRouter = DjangoGraphQLProtocolRouter`).**
  Rejected: the alias *is* the impersonation the card forbids, just spelled as an
  assignment; it would also freeze upstream's name into the package's public
  surface one release before the API-freeze discipline starts caring.
- **Documenting the mapping only in this spec.** Rejected: specs archive; the
  guide (and until then the GLOSSARY) is where a migrant actually looks. The
  card's own DoD names the guide row, so dropping it would fail the card.

### Decision 10 — Version bumps are owned by the joint `0.0.14` cut

No slice in this card edits the package-version state: `[project].version` in
[`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init], or
[`tests/base/test_init.py::test_version`][test-base-init]. This card **shares the
`0.0.14` patch line** with three open siblings — [`TODO-ALPHA-042-0.0.14`][kanban],
[`TODO-ALPHA-043-0.0.14`][kanban], and [`TODO-ALPHA-044-0.0.14`][kanban] — so the
bump from `0.0.13` to `0.0.14` is owned by the **joint `0.0.14` cut** (the last
`0.0.14` card to land), the same posture [`spec-039`][spec-039] Decision 14 took
for the joint `0.0.13` cut. The release-status wording splits the same way
(`spec-039`'s F8 discipline): Slice 2 updates **implemented-on-main** docs (the
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
individual card's spec. Four cards target `0.0.14`; this is the first of them, so
its slices must leave the version line untouched.

Alternatives considered (and rejected):

- **Bump to `0.0.14` in Slice 2.** Rejected: three siblings also ship into
  `0.0.14`; a per-card bump races the joint cut and would be reconciled three
  times over.
- **Defer the lockfile regeneration to the joint cut too.** Rejected: Slice 1's
  tests import `channels`; a dev-dependency without its lock entry breaks the
  reproducible-env contract the moment CI runs `uv sync`.

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
  [`rf-init`][rf-init] `_DRF_INSTALL_HINT` shape, including the
  floor-naming-in-hint rule
  ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
- [ ] **D3** — the guard has **no memoization** and the `__getattr__` caches only
  the *built class* (not a successful guard result), so eviction-based absence
  tests can re-hit the guard — the non-memoizing contract from
  [`__init__.py`][init]'s root `__getattr__`, adapted: the class cache must be
  keyed so a `sys.modules` eviction of `routers` naturally drops it (a module
  global, cleared with the module) — **and the eviction discipline is
  two-sided**: the absence fixture saves/restores the parent package's
  `routers` attribute together with the `sys.modules` entries, restoring the
  original module object to *both* places, so no test order can leave the
  attribute path and the import path holding different module objects (and
  therefore different class caches)
  ([Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)
  / [Decision 8](#decision-8--test-strategy-package-tests-only-communicator-driven-execution-eviction-simulated-absence)).
- [ ] **D-P1** (deliberate deferral, not built now) — a generic
  `utils/` `require_soft_dependency(module, hint)` promotion waits for a third
  soft dependency; two sites with two hints do not earn it
  ([Decision 4](#decision-4--module-and-test-locations-a-top-level-routerspy-mirroring-both-upstreams-teststest_routerspy)).
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
- **`url_pattern` is a regex (`re_path`), matching `^graphql`.** It matches
  `/graphql`, `/graphql/`, and `/graphql-anything`; Channels' `URLRouter` matches
  against the path with the leading slash stripped. Consumers wanting an exact
  path pass `url_pattern=r"^graphql/$"` — documented behavior, upstream parity,
  not a bug to fix here.
- **Non-GraphQL WebSocket paths are unrouted.** The `websocket` branch's
  `URLRouter` has one route; a WS connect to any other path raises Channels'
  "No route found" error and the connection drops. Parity with upstream; a
  consumer multiplexing other WS consumers composes `ProtocolTypeRouter` by hand.
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
- **The consumers execute the schema on the ASGI event loop.** Sync resolvers ride
  Channels' `database_sync_to_async` machinery inside the HTTP consumer; the
  package's sync/async twin discipline (every shipped surface has both paths) is
  what makes the schema Channels-safe without new work here. An `async def`
  [`get_queryset`][glossary-get-queryset-visibility-hook] misuse under a sync surface still raises
  [`SyncMisuseError`][glossary-syncmisuseerror] exactly as under WSGI — the router
  changes transport, not resolver dispatch.
- **Multipart uploads over the Channels HTTP consumer.** Strawberry's
  `GraphQLHTTPConsumer` parses multipart via Django's `MultiPartParser` (verified
  in the venv source), so [`Upload`][glossary-upload-scalar]-typed mutations are
  transport-compatible in principle — but upload ergonomics and their tests are
  the [`TestClient`][glossary-testclient] card's territory
  (`TODO-ALPHA-043-0.0.14`); this card asserts nothing about them.
- **`channels>=4.2.1` and the `Django>=5.2` floor.** Per the Channels changelog,
  `4.2.1` (2025-03-29) is the first release with official Django 5.2 support —
  `4.2.0` predates Django 5.2 — and `4.3.2` (2025-11-20) the first confirming
  Django 6.0. So the *declared* floor is `4.2.1` (matching the package's own
  `Django>=5.2` floor) while the dev-*resolved* version must be `>=4.3.2` for
  the CI matrix's Django 6.0 leg; the Slice-1 gate re-verifies by running the
  suite, and if it disagrees all three naming sites move together
  ([Risks](#risks-and-open-questions)).
- **`pytest-asyncio` already covers the communicator tests; DB-connection
  residue is Channels' own job, not pre-solved by the conftest fixture.** The
  dev group pins `pytest-asyncio>=1.0.0` and communicator tests are `async def`
  under the repo's existing asyncio configuration. On connections: Channels'
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
schema-agnostic, and avoiding `DjangoType` keeps these tests out of the registry
lifecycle); one test uses a `DjangoType`-bearing schema to prove the
extensions-ride-along claim.

**Channels-present — construction and composition:**

1. `DjangoGraphQLProtocolRouter(schema)` is an instance of
   `channels.routing.ProtocolTypeRouter`; its `application_mapping` carries exactly
   `http` and `websocket`.
2. The `http` branch is `AuthMiddlewareStack`-wrapped and, without
   `django_application`, routes only the GraphQL pattern.
3. With `django_application=` provided, the `http` branch carries the fallback
   route **after** the GraphQL route (ordering asserted — the regression a
   composition module exists to prevent).
4. The `websocket` branch is `AllowedHostsOriginValidator`-wrapped **outside** the
   `AuthMiddlewareStack` (wrapping order asserted). Assertion mechanics:
   `AllowedHostsOriginValidator` is a factory *function*, not a class — the
   isinstance target is the `OriginValidator` instance it returns, and that
   outermost layer stores its wrapped app as `.application` (only the
   `BaseMiddleware` layers beneath it carry `.inner`).
5. A custom `url_pattern=` reaches the `re_path` on both branches.
6. Repeated symbol access returns the identical cached class (the builder
   memoizes), and the class is subclassable (a consumer extension smoke check).

**Channels-present — execution through communicators:**

7. `HttpCommunicator` POST of a GraphQL query to `/graphql` through the router
   returns 200 with the expected `data` (the full consumer round trip).
8. The same POST to a non-GraphQL path with `django_application=` provided reaches
   the fallback app (a minimal recording ASGI callable), and without it does not
   resolve.
9. `WebsocketCommunicator` connect to `/graphql` on the `graphql-transport-ws`
   subprotocol with a matching `Origin` header is accepted; with a mismatched
   `Origin` the handshake is denied (the validator, both directions).
10. A schema constructed with [`strawberry_config()`][glossary-strawberry_config]
    and [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] executes
    through the router unchanged (extensions-ride-along; a scalar from the
    package's map round-trips).

**Channels-absent (simulated via the eviction + import-block pattern):**

11. `import django_strawberry_framework` succeeds and
    `from django_strawberry_framework import *` binds no router name.
12. `import django_strawberry_framework.routers` succeeds.
13. `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`
    raises `ImportError` whose message contains `channels>=4.2.1` — matched
    against a **re-typed literal in the test file** (the
    [`test_soft_dependency.py`][test-soft-dependency] `_HINT_SUBSTRING`
    discipline): the deliberately independent copy is the drift-catch — a test
    importing `_CHANNELS_INSTALL_HINT` and asserting the constant against
    itself could never notice the hint drifting away from the dev-group floor.
    The gate moves the test literal together with the other naming sites.
14. After restore, the present-path access works again in the same process (no
    stale negative caching — the D3 obligation), **and** the attribute path and
    the import path resolve to the *same* module object and the *same* cached
    class — i.e. `django_strawberry_framework.routers is
    sys.modules["django_strawberry_framework.routers"]` after teardown (the
    two-sided restore of Decision 8; this is the assertion that makes Test 6's
    identity claim order-independent under `pytest-xdist`).
15. An unrelated attribute miss on the module raises plain `AttributeError`, not
    the channels hint.

Coverage: the package gate is `fail_under = 100`; the builder body, both branches
of the guard, the `__getattr__` hit/miss paths, and the fallback-present /
fallback-absent constructor branches are all reached by the list above.

## Doc updates

Slice 2, per the F8 split in
[Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut) —
implemented-on-main docs update here; release-status wording defers to the joint
`0.0.14` cut:

- [`docs/GLOSSARY.md`][glossary] — the
  [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] entry body
  grows the implemented contract: the constructor signature, the
  auth-stack / origin-validator composition, the soft-dependency behavior matrix
  (import clean / access raises / hint text), the `url_pattern` regex semantics,
  the `lifespan` note, and the see-also edges to
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

- **The channels floor is changelog-grounded, not yet suite-verified.**
  `channels>=4.2.1` (the first release with official Django 5.2 support, per the
  Channels changelog; the earlier `4.2.0` draft floor predated Django 5.2 and was
  corrected in review) is the declared floor, with the dev-resolved version
  required at `>=4.3.2` (the first release confirming Django 6.0) so the CI
  matrix's Django 6.0 leg passes. The Slice-1 dependency gate installs it and
  runs the suite before the hint string freezes. **Preferred answer:** `4.2.1`
  holds and all three naming sites ship with it. **Fallback:** the gate moves
  all three sites together to whatever the suite proves — the
  three-places-that-must-agree rule exists precisely so this is one edit, not a
  drift. A fourth site rides along either way: `daphne` in the dev group
  (test-only, required to *import* `channels.testing` at all —
  [Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
- **The auth-mutations handoff is wider than this card.** The shipped
  [Auth mutations][glossary-auth-mutations] GLOSSARY entry says Channels /
  websocket auth "waits for the `0.0.14` router card"; this card's DoD ships
  transport only
  ([Decision 2](#decision-2--card-scope-boundary-the-transport-router-ships-websocket-auth-semantics-and-fakeshop-asgi-stay-out)).
  The open question: do the `0.0.13` auth resolvers (whose request handling
  targets a Django `HttpRequest` — session attribute, `auth.login`'s expectations)
  function through `GraphQLHTTPConsumer`'s Channels-shaped request? Upstream ships
  a `channels_auth` fallback because the shapes differ, which is evidence they may
  not. **Preferred answer for `0.0.14`:** this card ships the transport; Slice 2's
  GLOSSARY body-edit re-words the auth entry's deferral honestly ("the `0.0.14`
  router ships the session transport; auth-mutation execution over Channels
  consumers remains unverified") so the shipped docs stop over-promising, and the
  verification itself lands with the [`TestClient`][glossary-testclient] card
  (`TODO-ALPHA-043-0.0.14`, whose helpers make protocol-level assertions cheap)
  or a dedicated follow-on if it proves broken. **Fallback:** if the Slice-1
  communicator tests happen to make the check nearly free, a single smoke test
  (login mutation through `HttpCommunicator`) is added — as evidence for the
  re-worded GLOSSARY sentence, not as a shipped compatibility claim.
- **The card's name hedge.** "final name pinned during implementation" vs. this
  spec pinning `DjangoGraphQLProtocolRouter` now
  ([Decision 3](#decision-3--the-symbol-is-djangographqlprotocolrouter--distinctly-ours-pinned-now)).
  Not a conflict, strictly — pinning early is the spec doing the implementation's
  design work — but recorded per the [`docs/SPECS/NEXT.md`][next] prefer-the-card
  rule: if implementation surfaces a genuine problem with the name, the change is
  a spec revision, not a silent drift, and the GLOSSARY anchor
  (`#djangographqlprotocolrouter`) plus the card's reference edges move with it.
- **`ProtocolTypeRouter` internals as an assertion target.** Tests 2–4 assert
  middleware wrapping order by inspecting Channels' composed application objects
  (the outermost WS layer is an `OriginValidator` instance holding `.application`
  — `AllowedHostsOriginValidator` is a factory function — and the
  `BaseMiddleware` layers beneath carry `.inner`). Channels' middleware
  factories and classes are stable public API, but the
  attribute names are not contractual; if a Channels release reshapes them, the
  structural tests get noisy while the communicator tests (7–10) keep the truth.
  **Preferred posture:** keep both layers — the structural tests name the intent,
  the communicator tests hold the behavior; a Channels reshape is absorbed by
  updating the structural helpers, gate-visible either way.

## Out of scope (explicitly tracked elsewhere)

- **`TestClient` / `GraphQLTestCase` helpers** — [`TODO-ALPHA-043-0.0.14`][kanban]
  ([`TestClient`][glossary-testclient] / [`GraphQLTestCase`][glossary-graphqltestcase]);
  this card's tests use Channels' own communicators, not those helpers.
- **Debug-toolbar middleware** — [`TODO-ALPHA-042-0.0.14`][kanban]
  ([Debug-toolbar middleware][glossary-debug-toolbar-middleware]).
- **Response-extensions debug middleware** — [`TODO-ALPHA-044-0.0.14`][kanban]
  ([Response-extensions debug middleware][glossary-response-extensions-debug-middleware]).
- **Auth-mutation execution over Channels consumers** — scoped to the
  [`TestClient`][glossary-testclient] card or a follow-on per
  [Risks](#risks-and-open-questions); the [Auth mutations][glossary-auth-mutations]
  GLOSSARY wording is corrected in Slice 2 either way.
- **Fakeshop ASGI activation / Channels acceptance lane** — the
  fakeshop-activation card [`TODO-BETA-053-0.1.5`][kanban] if ever.
- **Subscriptions as a package surface** — no card; the router transports whatever
  the consumer's schema defines.
- **The migration guide itself** — [`TODO-BETA-056-0.1.6`][kanban]; this card only
  hands it the one-row symbol mapping
  ([Decision 9](#decision-9--migration-ergonomics-live-in-the-migration-guide-row-not-the-symbol-name)).
- **The `0.0.14` version bump and release-status flips** — the joint `0.0.14` cut
  ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).

## Definition of done

- [ ] `django_strawberry_framework/routers.py` exists, with module + symbol
      docstrings, exposing `DjangoGraphQLProtocolRouter` via the lazy
      `__getattr__` +`require_channels()` guard
      ([Decision 3](#decision-3--the-symbol-is-djangographqlprotocolrouter--distinctly-ours-pinned-now)
      / [Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
- [ ] `channels` is a soft dependency: `import django_strawberry_framework` and
      `import django_strawberry_framework.routers` succeed without it;
      symbol access raises `ImportError` carrying the single install hint naming
      the verified floor (the card's DoD, sharpened by
      [Decision 5](#decision-5--soft-channels-dependency-a-lazy-module-__getattr__--one-require_channels-guard)).
- [ ] The constructor is byte-compatible with upstream
      (`(schema, django_application=None, url_pattern="^graphql")`) and the
      composition matches [Decision 6](#decision-6--constructor-parity-schema-django_applicationnone-url_patterngraphql-composition-borrowed-as-is)
      exactly (auth stack both branches; origin validator WS-only; Django fallback
      HTTP-only, after the GraphQL route).
- [ ] `channels>=4.2.1` (or the floor the Slice-1 gate proves, moving all naming
      sites together) **and the test-only `daphne`** are in
      `[dependency-groups].dev` with `uv.lock` regenerated in the same commit;
      the dev-group specifier, the hint string, and this spec's Risks note agree
      on the floor, and the resolved dev version is `>=4.3.2` (the Django 6.0 CI
      leg).
- [ ] `tests/test_routers.py` covers both dependency states per the
      [Test plan](#test-plan) — including at least one real `HttpCommunicator`
      GraphQL round trip and both origin-validator directions — and the package
      coverage gate (`fail_under = 100`) holds with `routers.py` included.
- [ ] The migration-guide handoff row content is recorded for
      [`TODO-BETA-056-0.1.6`][kanban]
      (`AuthGraphQLProtocolTypeRouter` → `DjangoGraphQLProtocolRouter`, signature
      unchanged) ([Decision 9](#decision-9--migration-ergonomics-live-in-the-migration-guide-row-not-the-symbol-name)).
- [ ] Slice 2 doc updates land per [Doc updates](#doc-updates): the GLOSSARY entry
      body (status flip deferred), the regenerated [`docs/TREE.md`][tree], and the
      kanban card wrap (DB edit + re-render).
- [ ] The [Auth mutations][glossary-auth-mutations] GLOSSARY deferral sentence is
      re-worded to the honest post-router state
      ([Risks](#risks-and-open-questions)).
- [ ] **No slice bumps the version** — `pyproject.toml` / `__version__` /
      [`tests/base/test_init.py`][test-base-init] still read `0.0.13` when this
      card flips Done; the joint `0.0.14` cut owns the bump
      ([Decision 10](#decision-10--version-bumps-are-owned-by-the-joint-0014-cut)).
- [ ] `uv run ruff format .` / `ruff check --fix .` clean; no `pytest` beyond the
      slices' own test additions unless the maintainer asks (the
      [`START.md`][start] workflow rule).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[kanban]: ../KANBAN.md
[goal]: ../GOAL.md
[pyproject]: ../pyproject.toml
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary-auth-mutations]: GLOSSARY.md#auth-mutations
[glossary-debug-toolbar-middleware]: GLOSSARY.md#debug-toolbar-middleware
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangographqlprotocolrouter]: GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangomutationfield]: GLOSSARY.md#djangomutationfield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-get-queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-graphqltestcase]: GLOSSARY.md#graphqltestcase
[glossary-response-extensions-debug-middleware]: GLOSSARY.md#response-extensions-debug-middleware
[glossary-serializermutation]: GLOSSARY.md#serializermutation
[glossary-strawberry_config]: GLOSSARY.md#strawberry_config
[glossary-syncmisuseerror]: GLOSSARY.md#syncmisuseerror
[glossary-testclient]: GLOSSARY.md#testclient
[glossary-upload-scalar]: GLOSSARY.md#upload-scalar
[glossary]: GLOSSARY.md
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-021]: SPECS/spec-021-apps-0_0_7.md
[spec-039]: SPECS/spec-039-serializer_mutations-0_0_13.md
[spec-040]: SPECS/spec-040-auth_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../django_strawberry_framework/conf.py
[init]: ../django_strawberry_framework/__init__.py
[rf-init]: ../django_strawberry_framework/rest_framework/__init__.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-list-field]: ../tests/test_list_field.py
[test-soft-dependency]: ../tests/rest_framework/test_soft_dependency.py
[tests-conftest]: ../tests/conftest.py

<!-- examples/ -->
[config-wsgi]: ../examples/fakeshop/config/wsgi.py
[test-query-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->
[build-kanban-md]: ../scripts/build_kanban_md.py
[build-tree-md]: ../scripts/build_tree_md.py

<!-- .venv/ -->

<!-- External -->
[upstream-routers]: ../../strawberry-django-main/strawberry_django/routers.py
