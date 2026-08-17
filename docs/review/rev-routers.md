# Review: `django_strawberry_framework/routers.py`

Status: verified

## Understanding

`routers.py` lazily materializes `DjangoGraphQLProtocolRouter` behind the soft `channels` dependency. The resulting `ProtocolTypeRouter` maps `http` directly to the required consumer-supplied Django ASGI application and maps `websocket` to `DjangoWebSocketHostValidator` > `AllowedHostsOriginValidator` > `AuthMiddlewareStack` > `URLRouter` > one `re_path` callback. The default route is exact (`r"^graphql/?$"`); HTTP path matching and the Django middleware lifecycle belong entirely to the supplied application and its URLconf.

The module does not implement GraphQL protocol handling. It builds the package revalidating consumer from Strawberry's `GraphQLWSConsumer`, or mounts an explicitly injected subclass/factory after validating the factory call and result. The consumer owns sync/async protocol dispatch, session actor revalidation, outbound gating, error masking, and connection-close settlement in `consumers.py`; the router only composes those wrappers and preserves the schema object.

`require_channels()` and the builder's split import catches keep module import channels-free while distinguishing absent `channels` from a degraded Channels or Strawberry Channels installation. `DjangoWebSocketHostValidator` delegates Host syntax and `ALLOWED_HOSTS` semantics to Django's `HttpRequest.get_host()`, while Channels owns Origin denial, malformed protocol-frame handling, and close/error wire shapes.

## Verification

- `git --no-pager diff 7caa1f83f5f02a8a3cb12cf74809806fffaa8b4b -- django_strawberry_framework/routers.py` is empty; the working `routers.py` is byte-identical to the scoped baseline.
- Read the full router, `consumers.py`, `utils/sessions.py`, `utils/permissions.py`, `auth/sessions.py`, `auth/mutations.py`, `views.py`, the fakeshop URL/view path, and the transport specifications/docs. The fakeshop is WSGI-only, so the Channels router is genuinely unreachable from its live GraphQL tier.
- `uv run pytest tests/test_routers.py --no-cov` passed 151 tests before the permanent additions. The existing suite exercises HTTP identity/delegation, exact default WebSocket paths, Host/Origin independence, AuthMiddlewareStack session behavior, schema pass-through, consumer injection, soft-dependency eviction and degraded imports, actor revalidation, sync/async operation paths, malformed no-route failures, error masking, and close/retry/teardown state.
- `docs/review/temp-tests/routers/test_edges.py` passed 6 focused probes. Real `WebsocketCommunicator` probes confirmed that malformed custom regexes are lazily rejected by Django as `ImproperlyConfigured` at first route match/handshake, non-text frames close with `4400` for `graphql-transport-ws` and `1002` for `graphql-ws`, and legacy malformed JSON is ignored while the connection continues to `connection_ack`.
- Installed Strawberry source inspection confirmed both protocol handlers receive through the shared adapter, transport-ws converts non-text/non-JSON input to a `4400` close, legacy graphql-ws converts non-text input to `1002` and intentionally uses `ignore_parsing_errors=True`, and both protocols retain their own operation close/error semantics. Channels source inspection confirmed `ProtocolTypeRouter`, `URLRouter`, `AllowedHostsOriginValidator`, and `AuthMiddlewareStack` behavior.

## Improvements

### High

None.

### Medium

- **Observation:** The router's permanent suite did not pin malformed protocol-frame behavior through the actual package composition, even though the router deliberately delegates this contract to Strawberry's two protocol handlers.
- **Evidence:** Upstream handler inspection and the scratch communicator probes established distinct, intentional behavior: a non-text frame closes with `4400` under `graphql-transport-ws` and `1002` under legacy `graphql-ws`; legacy malformed JSON is ignored and the connection remains usable. Before this change, `tests/test_routers.py` had no real communicator assertion for those paths.
- **Impact:** A future router/consumer-wrapper refactor could accidentally normalize, swallow, or gate malformed frames and alter the protocol's close/error lifecycle without a regression at the package boundary. This is especially risky because the two supported subprotocols intentionally differ.
- **Recommendation:** Keep protocol malformed-frame checks at the package tier, driving real `WebsocketCommunicator` connections through the router and asserting each protocol's upstream-owned result rather than reimplementing or mocking handler behavior.
- **Proof:** `tests/test_routers.py::test_router_delegates_non_text_frame_close_behavior_per_protocol` covers both close codes; `tests/test_routers.py::test_router_delegates_legacy_invalid_json_continuation` proves malformed JSON does not terminate the legacy connection and that a subsequent `connection_init` receives `connection_ack`.

### Low

None.

## Summary

The router composition, required HTTP ownership, exact WebSocket routing, Host/Origin/Auth ordering, optional dependency errors, custom consumer seam, and sync/async lifecycle are coherent and already strongly exercised. No production router change was warranted. Permanent real-protocol tests now pin the previously implicit malformed-frame delegation without duplicating Strawberry or Channels policy.

## Implementation (Worker 1)

- Changed `tests/test_routers.py`: added protocol-tier regression coverage for non-text frames on both supported subprotocols (`4400` transport-ws, `1002` legacy graphql-ws) and for legacy malformed JSON continuing to a valid `connection_ack`.
- Created `docs/review/temp-tests/routers/test_edges.py` as untracked scratch evidence for malformed custom regex handling, custom consumer callback identity, and malformed protocol frames. The scratch suite passed 6 tests.
- Focused validation: `uv run pytest tests/test_routers.py --no-cov -k 'router_delegates_non_text_frame_close_behavior_per_protocol or router_delegates_legacy_invalid_json_continuation'` — 3 passed.
- Pre-edit focused baseline: `uv run pytest tests/test_routers.py --no-cov` — 151 passed.
- Formatter/linter: `uv run ruff format tests/test_routers.py` and `uv run ruff check --fix tests/test_routers.py` — passed; targeted scratch formatting/lint also passed.
- Rejected finding: malformed custom `websocket_url_pattern` is consumer-supplied `re_path` configuration. Django intentionally compiles it lazily and raises its own `ImproperlyConfigured` on first match; the router should not add a second regex compiler or normalize a delegated framework error without a package contract requiring eager validation. Scratch coverage records both direct pattern access and a real handshake propagation.
- Changelog: no entry added; this is a bounded regression-coverage improvement with no production behavior change.

## Independent verification (Worker 2)

- `git --no-pager diff 7caa1f83f5f02a8a3cb12cf74809806fffaa8b4b -- django_strawberry_framework/routers.py` is empty; the item has no production edit. The scoped test diff contains only the two parametrized protocol assertions plus the legacy continuation assertion shown in the implementation section.
- Re-traced `routers.py::_build_router_class` and the built class: `ProtocolTypeRouter` maps exactly `http` to the supplied `django_application` by identity and `websocket` to `DjangoWebSocketHostValidator` > `AllowedHostsOriginValidator` > `AuthMiddlewareStack` > `URLRouter` > one `re_path`. Channels source confirms protocol dispatch and leading-slash stripping; the package tests cover HTTP delegation, exact `/graphql` and `/graphql/` matching, rejected suffix/prefix paths, Host-before-auth ordering, independent Host/Origin denial, soft absence, and split degraded-install errors.
- Installed Strawberry source confirms the delegated protocol differences: `graphql-transport-ws` catches `NonTextMessageReceived` and closes `4400`, while legacy `graphql-ws` catches it and closes `1002`; legacy iterates with `ignore_parsing_errors=True`, so malformed JSON is discarded and a later `connection_init` can still produce `connection_ack`.
- `uv run pytest tests/test_routers.py --no-cov` — **154 passed**. The focused new selection — **3 passed** — independently pinned `4400` vs `1002` and legacy malformed-JSON continuation. `uv run pytest docs/review/temp-tests/routers/test_edges.py --no-cov` — **6 passed**, including custom-consumer callback delegation and both direct/real-handshake malformed-regex probes.
- The rejected startup-validation candidate remains correctly rejected: constructing `_router(websocket_url_pattern="[")` succeeds; accessing the route regex or matching a real handshake raises Django's own `ImproperlyConfigured` (`not a valid regular expression`). Eager package validation would duplicate delegated Django behavior and add no package contract, so no revision is required.
- No overclaim: these permanent tests pin malformed-frame delegation at the package router boundary; they do not reimplement Strawberry/Channels parsing or claim to cover every protocol error shape.
