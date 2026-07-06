# Spec-041 Critical Review

Verdict: **do not start production code until the spec is tightened.** The core
architecture is sound: a soft-`channels` top-level `routers.py`, optional-import
ownership in `utils/imports.py`, and a single request-shape extension in
`utils/permissions.py::request_from_info` are the right owners. The spec still has
several correctness and scope holes that will become flaky tests or misleading
consumer behavior if left as written.

One important scope note: the question about a setting read / validation anchor in
`django_strawberry_framework/types/relay.py::_resolve_globalid_strategy` does
**not** describe [spec-041][spec-041]. This Channels router spec explicitly says it
adds no settings key and leaves `django_strawberry_framework/conf.py` untouched.
That Relay setting path is existing Relay strategy behavior from earlier work, not
part of this router card. If another updated spec is trying to change Relay
settings, it should be reviewed separately.

## P1 Corrections

### 1. The Channels request adapter is too narrow

The spec says `request_from_info()` should return a small adapter exposing only
`.user` and `.session` from `consumer.scope`. That is enough for the built-in
`current_user` query and default model-permission path, but not enough for the
public permission-hook contract.

Existing surfaces pass the resolved request into user code:

- `django_strawberry_framework/filters/sets.py::FilterSet._request_from_info`
- `django_strawberry_framework/orders/sets.py::OrderSet._request_from_info`
- `django_strawberry_framework/mutations/permissions.py::DjangoModelPermission.has_permission`
- `django_strawberry_framework/rest_framework/resolvers.py::build_serializer_kwargs`

User-defined `check_<field>_permission(request)` hooks and serializer overrides may
read `request.headers`, `request.COOKIES`, `request.path`, `request.method`,
`request.consumer`, or other request-like attributes. Returning a two-property
adapter turns those legitimate hooks into `AttributeError`s only under Channels.

Required spec update:

- Keep the single-siting rule: support the Channels context only in
  `django_strawberry_framework/utils/permissions.py::request_from_info`.
- Make the adapter wrap the original Strawberry `ChannelsRequest`, not replace it
  with only scope fields.
- Expose `.user`, `.session`, and `.scope` explicitly from `consumer.scope`.
- Delegate unknown attributes to the wrapped request with `__getattr__`, so any
  request attributes Strawberry already exposes keep working.
- Add tests for both built-in behavior and user hook behavior: a fake permission
  method should read at least one delegated attribute and one scope-backed
  attribute.

This keeps the implementation DRY without silently narrowing the framework request
contract.

### 2. The degraded-install test is invalid unless it clears the lazy class cache

Test 17 says to block a builder-required import such as `channels.security.websocket`
and assert the incompatible-install `ImportError`. That only works if the real
router class has not already been built. The spec also requires repeated symbol
access to return a cached class, so any earlier construction test can make Test 17
miss the blocked import entirely.

Required spec update:

- In the Test 17 fixture, evict `django_strawberry_framework.routers` from
  `sys.modules`.
- Restore the parent package's `routers` attribute exactly as Decision 8 already
  requires for the channels-absent path.
- Assert `_ROUTER_CLASS` is unreachable because the module object was re-executed,
  not manually mutated in place.

This should be added to Decision 8, Helper-reuse D3, and Test 17. Otherwise the
test is order-dependent under both normal pytest order and `pytest-xdist`.

### 3. The incompatible-install error message is too channels-specific

The spec says a builder import failure should always raise an actionable
`ImportError` naming `channels>=4.3.2`. That is correct for missing or incompatible
Channels imports. It is misleading if the failing import is
`strawberry.channels.GraphQLHTTPConsumer` or `GraphQLWSConsumer`.

The spec already includes a Strawberry-floor gate, which proves the spec knows
Strawberry is part of the dependency boundary. The production error shape should
reflect that.

Required spec update:

- Keep `_CHANNELS_INSTALL_HINT` for true top-level `channels` absence.
- Add a separate builder-failure message that names both required halves:
  `channels>=4.3.2` and `strawberry-graphql>=0.262.0` with the
  `strawberry.channels` consumers available.
- Chain the original exception in all builder-failure cases.
- In Test 17, block one Channels import and one Strawberry consumer import in
  separate parametrized cases so both branches are pinned.

This avoids sending a user to reinstall Channels when their environment actually
has a broken or incompatible Strawberry install.

### 4. The authenticated-session claim is stronger than the planned test

The spec repeatedly says the router gives the package a session user on the scope.
Test 16 only proves anonymous resolution does not raise `ConfigurationError`.
That is useful, but it does not prove an authenticated session actor flows through
the router, and it does not prove the package's `current_user`-style path sees a
real authenticated user.

Required spec update, choose one:

- Add an authenticated-session communicator test that creates a user/session,
  sends the session cookie through `HttpCommunicator`, and asserts a resolver using
  `request_from_info()` sees the authenticated user.
- Or explicitly weaken the user-facing wording: the card composes
  `AuthMiddlewareStack` and proves the package can read the Channels request
  shape; full authenticated session-cookie behavior is delegated to Channels and
  not asserted by this card.

The first option is higher quality if it can be implemented without a fragile test
harness. The second is acceptable only if the docs are honest and the risk is
tracked.

## P2 Corrections

### 5. `require_optional_module(..., feature_label=...)` is needless API surface

The planned helper accepts `feature_label`, but the spec says the feature-specific
message lives in the caller's `install_hint`. That makes `feature_label` an unused
parameter, which adds ceremony without behavior.

Required spec update:

- Prefer `require_optional_module(module_name, *, install_hint)`.
- If the spec keeps `feature_label`, require the utility to use it in a generated
  fallback message. Do not keep a parameter "for future diagnostics" in a new
  utility.

The first option is simpler and closer to the existing `require_drf()` shape.

### 6. `routers.py` needs an explicit `__all__` decision

The spec says the root package star import stays channels-free, but it does not
define submodule star-import behavior. Without `__all__`,
`from django_strawberry_framework.routers import *` will expose helper names such
as `require_channels` and whatever typing imports remain module-global. With
`__all__ = ("DjangoGraphQLProtocolRouter",)`, submodule star import will trigger
the lazy symbol and therefore the channels guard.

Required spec update:

- State that `routers.py` defines `__all__ = ("DjangoGraphQLProtocolRouter",)`.
- State that submodule star import is an opt-in to the router and may raise the
  same install-hint `ImportError` when Channels is absent.
- Keep the root package `__all__` unchanged and channels-free.

This keeps the public module clean and avoids accidental public helper exports.

### 7. Test 10 over-specifies `DjangoOptimizerExtension`

The spec wants a schema using `strawberry_config()` and `DjangoOptimizerExtension`
to execute through the Channels router unchanged. The intent is good: the router
must pass the schema object through, not rebuild it. The current test wording risks
two bad outcomes:

- A trivial schema with the optimizer installed may not prove anything about the
  optimizer.
- A real `DjangoType` / ORM query under `GraphQLHTTPConsumer` may trip the same
  `SynchronousOnlyOperation` edge case the spec already documents.

Required spec update:

- Prove "schema object passes through unchanged" structurally in the composition
  tests, or with a custom Strawberry extension that records execution without ORM.
- Keep `DjangoOptimizerExtension` out of the Channels execution test unless the
  resolver path is explicitly async-safe.
- If the spec wants real optimizer behavior under Channels, make that a separate
  async ORM test with its own setup, not a ride-along assertion.

### 8. The Strawberry-floor gate checks an unused symbol

The implementation uses `GraphQLHTTPConsumer` and `GraphQLWSConsumer`. It does not
use Strawberry core's `GraphQLProtocolTypeRouter`. The spec currently requires the
floor gate to verify all three.

Required spec update:

- Gate only the symbols this implementation imports.
- If `GraphQLProtocolTypeRouter` remains in the gate, explain why an unused
  upstream parity symbol is allowed to block this package's router.

Blocking on unused upstream exports is unnecessary coupling.

### 9. HTTP fallback double-middleware behavior should be documented

The borrowed upstream composition wraps the entire HTTP `URLRouter` in
`AuthMiddlewareStack`, including the optional Django ASGI fallback. That means a
non-GraphQL HTTP request can pass through Channels' cookie/session/auth stack before
entering Django's normal ASGI middleware stack.

This is probably acceptable because it is upstream parity and scope-level mutation
is harmless for Django's ASGI app, but it is still a real behavior and small
performance cost on fallback requests.

Required spec update:

- Add an edge-case note that the HTTP fallback is also inside
  `AuthMiddlewareStack`.
- State that this is upstream parity and accepted for one-import migration.
- Do not introduce a separate fallback branch unless the spec deliberately breaks
  upstream parity.

### 10. `docs/feedback.md` should not be cited as durable spec authority

The spec revision text cites `docs/feedback.md P1.5` and similar review anchors.
This file is mutable scratch feedback and is often overwritten by later reviews.
Using it as standing-doc authority makes the spec's reasoning non-reproducible.

Required spec update:

- Fold the DRY decision text directly into the spec, which it mostly already does.
- Replace durable citations to `docs/feedback.md` with citations to the actual
  owner symbols, such as `django_strawberry_framework/utils/imports.py` and
  `django_strawberry_framework/utils/permissions.py::request_from_info`.

## P3 Clarifications

### 11. The auth-mutation fallback language is too loose

The Risks section says that if a login-mutation smoke test is "nearly free" it can
be added. That is not a crisp implementation contract. Either auth mutations over
Channels are out of scope, or the spec should require a test and define the
expected behavior.

Recommended spec update:

- Remove the "if nearly free" fallback.
- Keep auth mutations out of scope for this card.
- Create or reference a follow-on card for Channels auth mutation semantics.

### 12. Missing-Origin WebSocket behavior is unspecified

The spec tests matching and mismatched `Origin` headers. It does not say what
happens when a non-browser WebSocket client sends no `Origin` header. Channels owns
that behavior, but this router opts into the validator, so the package docs should
not leave the case implicit.

Recommended spec update:

- Add an edge-case sentence documenting Channels' missing-origin behavior.
- Add a test only if the behavior is stable enough across the declared Channels
  floor.

## Configuration And Performance Finding

The `types/relay.py` setting-read concern is not a blocker for spec-041.

Current Relay behavior:

- `django_strawberry_framework/conf.py` is intentionally a generic settings reader
  and shape validator for `DJANGO_STRAWBERRY_FRAMEWORK`.
- Domain validation for `RELAY_GLOBALID_STRATEGY` lives in
  `django_strawberry_framework/types/relay.py::_resolve_globalid_strategy`.
- That function is called during type finalization, not during each GraphQL query.

So the lazy read does **not** introduce per-query overhead for the router, does not
add a new thread-safety issue beyond the already-documented `Settings` cache
behavior, and does not require moving strategy validation into `conf.py`.

There is one possible Relay cleanup, but it belongs outside spec-041: if many Relay
types are finalized, the schema-wide setting can be validated repeatedly during one
finalization pass. That is finalization-time overhead, not request-time overhead.
If it ever matters, add a finalization-scoped helper in `types/relay.py` that
resolves and validates the setting once per pass. Do not move domain-specific
validation into `conf.py`; that would make the settings reader know about every
feature's value grammar.

## Test Setup Risks

The existing test suite can validate this spec without a major rewrite, but only if
the spec is adjusted as above.

Manageable with local helpers:

- Simulated absence can reuse the DRF soft-dependency fixture pattern.
- Communicator tests can live in `tests/test_routers.py`.
- `request_from_info()` unit coverage belongs in `tests/utils/test_permissions.py`.
- `require_optional_module()` unit coverage belongs in `tests/utils/test_imports.py`.

Risky unless clarified:

- Authenticated session-cookie communicator tests may require careful async-safe
  user/session setup.
- Optimizer execution through `GraphQLHTTPConsumer` can collide with the async
  consumer's sync-ORM limitation.
- Degraded-install tests will be flaky unless they evict the router module and its
  parent attribute before blocking imports.

## Required Spec Edits Before Implementation

1. Expand Decision 11's adapter contract to wrap and delegate to the original
   Channels request, not expose only `.user` / `.session`.
2. Update Test 17 and Helper-reuse D3 so degraded-install tests evict the router
   module and class cache.
3. Split incompatible-install error wording for Channels failures and Strawberry
   consumer failures.
4. Either add an authenticated-session communicator test or weaken the session-user
   claim.
5. Remove or justify `feature_label` on `require_optional_module`.
6. Add an explicit `routers.py::__all__` decision.
7. Rewrite Test 10 so schema pass-through is proven without forcing sync ORM under
   the async consumer.
8. Remove the unused `GraphQLProtocolTypeRouter` floor gate or justify it.
9. Document HTTP fallback double-middleware behavior.
10. Remove durable references to `docs/feedback.md` from the spec.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[pyproject]: ../pyproject.toml

<!-- docs/ -->
[spec-041]: spec-041-channels_router-0_0_14.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../django_strawberry_framework/conf.py
[routers]: ../django_strawberry_framework/routers.py
[types-relay]: ../django_strawberry_framework/types/relay.py
[utils-imports]: ../django_strawberry_framework/utils/imports.py
[utils-permissions]: ../django_strawberry_framework/utils/permissions.py

<!-- tests/ -->
[test-routers]: ../tests/test_routers.py
[test-soft-dependency]: ../tests/rest_framework/test_soft_dependency.py
[test-utils-imports]: ../tests/utils/test_imports.py
[test-utils-permissions]: ../tests/utils/test_permissions.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
