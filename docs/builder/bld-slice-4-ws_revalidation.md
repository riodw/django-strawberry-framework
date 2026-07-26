# Build: Slice 4 — S11: WebSocket actor revalidation through an injection seam

Spec reference: `docs/spec-065-transport_security-0_0_15.md` — Slice 4 checklist lines 171-181;
Decision 11 (lines 1156-1235), Decision 12 (1237-1256), Decision 13 #"Placement" (1351-1361);
User-facing API #"The constructor" (565-576) + #"Consumer-visible behavior" (605-638) +
#"Error shapes" (640-673); Helper-reuse obligations (1449-1485, WS bullets 1464-1471); Edge
cases (1487-1567, WS bullets 1545-1559); Test plan S11 rows 25-30 (1625-1644); Risks
(1692-1744, the per-operation query cost and the no-fakeshop-`asgi.py` notes).
Status: planned

## Plan (Worker 1)

### DRY analysis

- **Utils inventory checked.** `docs/shadow/utils-inventory.md` refreshed this pass (237 lines,
  from `django_strawberry_framework/utils/` via the `worker-1.md` AST script). Relevant
  candidates:
  - `utils/permissions.py::ChannelsRequestAdapter` (+ `::_channels_scope`,
    `::_channels_request_adapter`) — the package's single Channels-scope decoder. **Reused
    indirectly and deliberately not extended**: Helper-reuse #"The actor is written back to
    `scope[\"user\"]` rather than plumbed to readers" forbids a second request-context decoder,
    and this slice adds none. The revalidation writes the key the adapter already reads.
  - `utils/querysets.py::run_in_one_sync_boundary(fn, *args, **kwargs)` — the package's ONE
    `sync_to_async(thread_sensitive=True)` primitive. **Reviewed and rejected for this slice**:
    the only blocking call the revalidation makes is `channels.auth.get_user`, which upstream
    already wraps in `channels.db.database_sync_to_async` (verified by reading
    `.venv/.../channels/auth.py` — the decorator is on the function). Re-wrapping it would be a
    second boundary AND would discard `database_sync_to_async`'s `close_old_connections`
    behaviour. The revalidation therefore crosses **exactly one** boundary, which is the
    discipline that helper exists to protect.
  - `utils/imports.py::require_optional_module` — the soft-dep owner behind
    `routers.py::require_channels`. Untouched; no second guard (see "channels boundary" below).
  - No utility exists for a monotonic clock, a session-store resolver, or a numeric-argument
    validator, and none is justified in `utils/` — each of the three has exactly one call site
    (see "New helpers justified").
- **Static inspection run (BUILD.md obligation).** `uv run python scripts/review_inspect.py
  django_strawberry_framework/routers.py --output-dir docs/shadow` →
  `docs/shadow/django_strawberry_framework__routers.overview.md` +
  `…__routers.stripped.py`. Quick scan on the current (Slice-1/2/3) source: 11 imports, 5
  symbols, **1 control-flow hotspot** (`_build_router_class`, lines 107-225 / 5 branch nodes), 0
  Django/ORM markers, 0 calls of interest, 0 TODOs, 1 repeated literal
  (`DjangoGraphQLProtocolRouter`, 2x — the two present-but-broken hint strings; two distinct
  actionable messages, not a DRY defect). This slice adds ~4 statements to that hotspot (one
  factory call, one consumer-selection call, two validated kwargs) and puts every new *decision*
  in the new module instead, so the hotspot does not grow into a second builder.
  `django_strawberry_framework/consumers.py` does not exist yet, so Worker 1 cannot inspect it;
  it is a new `.py` file with real logic, so **Worker 3 must run the helper on it** (BUILD.md
  "Worker 3 must run the helper when the slice adds a new `.py` file … unless it is a
  pure-class-definition module" — this one is not). `tests/test_routers.py` gains >50 lines but
  is outside `django_strawberry_framework/`; Worker 3 owes the helper there too under the
  50-line rule. Shadow line numbers are not canonical; every citation below is symbol-qualified.
- **Existing patterns reused.**
  - `strawberry.channels.GraphQLWSConsumer` and its two protocol handlers are **subclassed, not
    reimplemented** (Decision 11 #"Two `super()`-delegating pre-hooks are not an engine").
    Verified by reading the installed sources in full — see "Upstream verification" below.
  - `channels.auth.get_user(scope)` is reused verbatim as the actor resolver. It owns the
    backend allow-list check (`backend_path in settings.AUTHENTICATION_BACKENDS`), the
    `backend.get_user(user_id)` load (which is where `ModelBackend.user_can_authenticate`
    rejects a disabled user), and the constant-time `get_session_auth_hash()` verification.
    Reimplementing any of that in the package would be a security-critical near-copy.
  - `routers.py::_build_router_class`'s guard-then-import ordering, the `_ROUTER_CLASS` global
    cache, the `_CHANNELS_INSTALL_HINT` / `_CHANNELS_BROKEN_HINT` /
    `_STRAWBERRY_CHANNELS_BROKEN_HINT` triple, and the PEP 562 `routers.py::__getattr__` are
    **unchanged in mechanism and in count** (Helper-reuse #"No new guard, no new hint string, no
    second lazy-export mechanism"). The new consumer class is built *inside* the existing
    builder, behind the existing guard, cached by the existing `_ROUTER_CLASS` — see step 2.
  - `views.py::_resolved_max_request_body_bytes` — the shape for the window's validation: reject
    `bool` explicitly (`isinstance(True, int)` is `True`), reject the out-of-domain value, and
    raise `ConfigurationError` with the
    `f"… ; got {type(value).__name__} {value!r}."` tail. Same author, same slice family, same
    error type; the window's validator is a sibling, not a new idiom.
  - `exceptions.py::ConfigurationError` — the package's single typed configuration failure
    (Helper-reuse #"The construction-time failure is `ConfigurationError`"). No new exception.
  - `auth/mutations.py::_channels_http_login_establish` #"from channels.auth import login as
    channels_login" — the precedent for reaching `channels.auth` through a **function-body**
    import rather than a module-level one, which is what keeps the new module channels-free at
    import time.
  - `auth/sessions.py::_SCOPE_LOCK_KEY` — the precedent for a private, distribution-namespaced
    scope key (`"__django_strawberry_framework_…__"`) that cannot collide with an ASGI key set
    by Channels, Django, or consumer middleware. The window's last-revalidated timestamp uses
    the same shape.
  - `auth/sessions.py::uses_signed_cookie_sessions` #"import_string(f\"{settings.SESSION_ENGINE}.SessionStore\")"
    — the package's existing way to resolve the configured session store class. Step 4 extracts
    that one line into `auth/sessions.py::session_store_class()` and re-points this existing
    function at it, so the revalidation's fresh-store construction and the signed-cookie
    capability answer read the engine through ONE expression.
  - `django_strawberry_framework/__init__.py` #"logger = logging.getLogger" via `from . import
    logger` — the canonical package logger, used exactly as
    `extensions/debug.py::_collect_debug_payload` uses it (`logger.exception(...)` on a
    fail-closed degrade). No new logger name.
  - `tests/test_routers.py`'s existing helpers: `_router(...)`, `_router_class()`,
    `unwrap_origin_validator`, `unwrap_auth_stack`, `_route_patterns`, `_ws_graphql_data`, the
    `_HINT_SUBSTRING` **re-typed-literal** discipline (never import the message constant you are
    asserting), and Test 18's `database_sync_to_async` session-minting shape.
- **New helpers justified.**
  - `django_strawberry_framework/consumers.py` — **one** new module. Single responsibility: *the
    package's WebSocket GraphQL consumer and the per-operation actor revalidation it performs*.
    It holds one module-level coroutine (`revalidate_operation_actor`), one pure class factory
    (`build_revalidating_consumer_class`), and three module constants. Why a module and not more
    lines inside `routers.py::_build_router_class`: that builder is already the file's only
    control-flow hotspot, `routers.py`'s single responsibility is *composing transports*, and the
    revalidation is the one piece of this slice with real branch logic and its own docstring
    contract (the Decision 12 lifetime statement lands there). It pairs with `views.py` the way
    Channels/Django projects pair `consumers.py` with `views.py`.
  - `auth/sessions.py::session_store_class()` — a 2-line helper with **two** call sites
    (`uses_signed_cookie_sessions`, and the revalidation's fresh store). Single responsibility:
    resolve the configured `SESSION_ENGINE`'s `SessionStore` class. Justified precisely because
    the second call site exists; without it the `import_string(f"{…}.SessionStore")` expression
    would be spelled twice in two modules.
  - `consumers.py::_monotonic()` — a one-line wrapper over `time.monotonic()`. Justified as the
    **documented test seam**: the window test must age the clock deterministically rather than
    sleeping through a real interval (this suite is `-W error`, `-n auto`, and has a documented
    history of order-dependent async flakes). Named in the docstring as such.
  - **Two** test-module-local helpers in `tests/test_routers.py` (`_open_ws`, `_ws_operation`) and
    **two** `database_sync_to_async` fixtures-as-functions (`_make_user_and_session`,
    plus the three tiny out-of-band mutators). See "Test additions".
  - **Nothing else.** No new settings key (the spec's DoD pins `MAX_REQUEST_BODY_BYTES` as *the
    only* key this card adds — the window is a constructor argument, deliberately), no new
    exception type, no new soft-dep guard, no second lazy export, no new request decoder, no new
    logger, no `conf.py` edit, no `CHANGELOG.md` edit, no version-quintet movement.
- **Duplication risk avoided.**
  1. **A second GraphQL protocol engine.** Rejected by name in Decision 11. Avoided
     structurally: each protocol subclass is one `await` + one `super()` call, and the two
     subclasses are generated by one factory from the base consumer's own handler attributes.
  2. **Two copies of the revalidation decision tree (one per protocol).** Avoided: ONE
     `revalidate_operation_actor(handler, operation_id, *, errors_as_list)` owns window expiry,
     the anonymous carve-out, the acknowledged carve-out, the session reload, the actor
     write-back, the rejection, and the fail-closed branch. The per-protocol subclasses hold no
     decision at all; the single irreducible difference between the protocols (the `error`
     message's `payload` is a **list** of formatted errors on `graphql-transport-ws` and a
     **single** formatted error on legacy `graphql-ws` — measured, see "Upstream verification")
     is expressed as one keyword literal at each of the two call sites.
  3. **Re-implementing `channels.auth.get_user`'s verification** (backend allow-list, session
     auth-hash constant-time compare, disabled-user rejection). Avoided by delegating; the
     package supplies only the *fresh* session store the function reads.
  4. **A second soft-`channels` guard / hint / lazy export for `consumers.py`.** Avoided: the
     module is channels-free at import (its only `channels` import is inside a coroutine body),
     and the router builds the consumer class inside the try-block whose failure already raises
     `_STRAWBERRY_CHANNELS_BROKEN_HINT`. See "The `channels` import boundary".
  5. **A second class cache with its own eviction semantics.** Avoided: `consumers.py` caches
     nothing. `_build_router_class` calls the factory once and the resulting class lives inside
     the existing `_ROUTER_CLASS` closure, so its lifetime is exactly the router class's and the
     eviction-simulated-absence discipline in `tests/test_routers.py` needs no new machinery. (A
     module-level cache in `consumers.py` would *survive* the eviction of
     `django_strawberry_framework.routers` + `strawberry.channels` and hand a fresh router a
     consumer subclass derived from the dead `GraphQLWSConsumer` — a hazard this shape cannot
     have.)
  6. **A second session-minting block in the tests.** Test 18
     (`::test_authenticated_session_round_trip_reaches_the_resolver`) already contains one; the
     new rows need four more. Consolidated into one module-level
     `_make_user_and_session(username)` — Test 18's **assertions stay byte-identical**, only its
     local helper is lifted (Worker 3 and Worker 1's final verification must diff the assertion
     lines against `git show HEAD:tests/test_routers.py`).
  7. **A second WebSocket handshake/`connection_init`/`connection_ack` block.** The new
     multi-operation rows need the socket to stay open, which `_ws_graphql_data` (open → one
     operation → close) cannot express. Consolidated: `_open_ws` owns handshake + init + ack,
     `_ws_operation` owns one operation round trip, and `_ws_graphql_data` is **rewritten to
     call both** so there is exactly one handshake site. Its three existing callers keep their
     assertions untouched.
  8. **Duplicating the anonymity predicate.** `auth/mutations.py::_authenticated_actor_or_none`
     is the package's stated "ONE anonymity definition the session-auth surfaces share". The
     revalidation needs the same predicate but deliberately does **not** import it: it is
     private to the auth-mutation surface, and importing a 1200-line module that pulls
     `mutations.resolvers` and the Strawberry type stack into a transport-layer coroutine would
     invert the dependency direction (`auth/` already depends on `utils/permissions.py`, not the
     reverse). `consumers.py` instead spells the two-condition test once, with a comment naming
     `auth/mutations.py::_authenticated_actor_or_none` as the same predicate. **Extraction
     trigger, named:** if a third site needs it, promote it to `utils/permissions.py` beside
     `ChannelsRequestAdapter` (the cycle-safe substrate both callers already import) rather than
     letting a third copy appear.

### Upstream verification (read, not remembered)

Read in full: `.venv/lib/python3.14/site-packages/strawberry/channels/handlers/ws_handler.py`
(194 lines), `.venv/…/strawberry/subscriptions/protocols/graphql_ws/handlers.py` (266 lines),
`.venv/…/channels/auth.py` (the `get_user` / `login` / `logout` trio),
`.venv/…/channels/sessions.py` (grep-level: `InstanceSessionWrapper`). Read in part:
`.venv/…/strawberry/http/async_base_view.py` (the class-attribute block and `run`),
`.venv/…/strawberry/subscriptions/protocols/graphql_transport_ws/handlers.py`
(`__init__`, `handle`, `handle_message`, `handle_subscribe`). Runtime probe (`uv run python`)
confirmed the attribute shapes quoted below. Installed: `strawberry-graphql 0.316.0`,
`channels 4.3.2` (the package's verified floor).

1. **`get_context` is once per connection — confirmed, and the spec is right to reject it.**
   `AsyncBaseHTTPView.run` #"context = (" awaits `self.get_context(request, response=…)`
   **before** dispatching to either handler's `handle()`, i.e. once per socket.
   `GraphQLWSConsumer.get_context` returns `{"request": request, "ws": request}` where `request`
   **is the consumer itself**, so the context holds no user snapshot — which is exactly why
   writing `scope["user"]` is observable to later operations without touching the context.
2. **The per-operation seams and their exact signatures.**
   - `graphql-transport-ws`: `BaseGraphQLTransportWSHandler.handle_subscribe(self, message: SubscribeMessage) -> None`.
     Upstream's own comment inside it — #"NOTE: this applies to all in-flight operations
     (queries and mutations executed over WebSocket included), not only subscriptions" — is the
     proof that this single method is *the* per-operation entry for queries and mutations too,
     not just subscriptions.
   - legacy `graphql-ws`: `BaseGraphQLWSHandler.handle_start(self, message: StartMessage) -> None`.
   - Both are reached through **class attributes on the view (= the consumer)**:
     `AsyncBaseHTTPView.graphql_transport_ws_handler_class` and
     `AsyncBaseHTTPView.graphql_ws_handler_class`, read by `run` at dispatch time
     (#"await self.graphql_transport_ws_handler_class(" / #"await self.graphql_ws_handler_class(").
     Overriding them on a `GraphQLWSConsumer` subclass is the whole seam.
3. **Those two attributes are subscripted generic aliases, not plain classes.** Probed:
   `type(GraphQLWSConsumer.graphql_transport_ws_handler_class)` is `typing._GenericAlias`
   (`BaseGraphQLTransportWSHandler[~Context, ~RootValue]`), because the class body assigns
   `= BaseGraphQLTransportWSHandler[Context, RootValue]`. Deriving from the attribute
   nevertheless works — `__mro_entries__` resolves it — and was probed end-to-end: the subclass
   MRO comes out `['T', 'BaseGraphQLTransportWSHandler', 'Generic', 'object']` with
   `__orig_bases__` preserved. **So the factory must derive from the attribute, never from a
   fresh import**, which also means it needs no import of either handler module and
   automatically tracks an upstream re-point.
4. **Both handlers already carry `self.connection_acknowledged`** (set in each `__init__`, flipped
   in each `handle_connection_init`) and both `handle_subscribe` / `handle_start` open with
   `if not self.connection_acknowledged: await self.websocket.close(code=4401, reason="Unauthorized"); return`.
   One attribute name across both protocols is what lets the shared function make the
   "not acknowledged yet → let upstream close it" decision without a per-protocol branch.
5. **Both protocols have a per-operation error channel** — so per spec #"Error shapes" the
   rejection is a GraphQL error on the operation and the socket is **not** closed. The two wire
   shapes, measured from upstream's own pre-execution refusals:
   - transport-ws `handle_subscribe` #"Subscription limit reached" sends
     `{"id": …, "type": "error", "payload": [error.formatted]}` — payload is a **list**.
   - legacy `handle_start` #"Subscription limit reached" sends
     `{"type": "error", "id": …, "payload": {…}}` — payload is a **single** dict, and
     `handle_async_results` proves a bare `GraphQLError.formatted` is an accepted payload there.
   Both refuse *before* creating the operation task, which is precisely the shape our pre-hook
   needs, and is the precedent it mirrors.
6. **`as_asgi` passes initkwargs to `__init__` per scope.** `channels.consumer`'s
   `as_asgi(cls, **initkwargs)` builds `app(scope, receive, send)` that does
   `consumer = cls(**initkwargs)`, and sets `app.consumer_class` / `app.consumer_initkwargs`
   (which `tests/test_routers.py::test_schema_object_passes_through_unchanged_with_extensions_intact`
   already reads). So the window must ride as an **initkwarg**, not as a class attribute: one
   cached consumer class serves every router instance, and two routers may carry two windows.
   `GraphQLWSConsumer.__init__(self, schema, keep_alive=False, keep_alive_interval=1,
   subscription_protocols=("graphql-transport-ws", "graphql-ws"),
   connection_init_wait_timeout=None, max_subscriptions_per_connection=100)` — the default
   protocol tuple is why **both** protocols are live on the package's mount and why both must be
   covered.
7. **`channels.auth.get_user(scope)` reads only `scope["session"]`** (it raises
   `ValueError("Cannot find session in scope…")` when absent and touches nothing else), is
   decorated `@database_sync_to_async`, and returns `AnonymousUser()` for every invalid shape:
   missing `_auth_user_id` (flushed / deleted session), a backend outside
   `AUTHENTICATION_BACKENDS`, `backend.get_user()` returning `None` (which is where
   `ModelBackend.user_can_authenticate` rejects `is_active=False`), and a failed
   `get_session_auth_hash` compare (password change / `logout` elsewhere). One call therefore
   covers all three revocation shapes the spec names — revoked, flushed, disabled — plus the
   password-rotation shape.
8. **`channels.auth.login` / `logout` set `scope["user"] = …` directly** (as does
   `auth/mutations.py::_channels_http_login_establish` #"request.scope[\"user\"] = AnonymousUser()"),
   so *replacing* the value — rather than poking `UserLazyObject._wrapped` — is the
   upstream-sanctioned write. `channels.auth.AuthMiddleware` resolves the user **eagerly** at
   connect (`await get_user(scope)` in `resolve_scope`), so reading `scope["user"].is_authenticated`
   in the pre-hook does no database work.
9. **`scope["session"]` must not be swapped for the fresh store.**
   `channels.sessions.InstanceSessionWrapper.send` / `::save_session` re-read
   `self.scope["session"]` at send time and may `asave()` it, so replacing the object could
   persist a store the connection never mutated. The fresh store therefore stays private to the
   revalidation, and `scope["session"].session_key` (an attribute read, no IO) is the only thing
   taken from the scope's own session.

### Where the revalidating consumer lives, and how the `channels` import boundary stays clean

New module **`django_strawberry_framework/consumers.py`**. The boundary rules it must satisfy,
and how:

- **A view-only adopter must never import `channels`.** `views.py` does not import
  `consumers.py`, `routers.py`, or `channels` — and must not start (Slice 1's `views.py`
  docstring and `tests/test_views.py`'s channels-free import proof both pin this). Slice 4 adds
  no import to `views.py` at all, so that proof holds untouched.
- **`import django_strawberry_framework` stays channels-free.** `consumers.py` is a leaf
  integration module and is **not** imported by `django_strawberry_framework/__init__.py` (same
  posture as `routers.py`, `views.py`, `middleware/debug_toolbar.py`, `extensions/`).
- **`import django_strawberry_framework.consumers` is itself channels-free.** Module-level
  imports are limited to `__future__`, `time`, `typing`, `from . import logger`, and
  `from .exceptions import ConfigurationError`. `channels.auth.get_user` is imported **inside**
  `revalidate_operation_actor`'s body (the `auth/mutations.py` precedent), and the two handler
  base classes are never imported at all — they are read off the base consumer class the factory
  is *handed* (Upstream verification #3).
- **No second guard, hint, or lazy export** (Helper-reuse). `routers.py::_build_router_class`
  imports `consumers.py` at module level (channels-free, so the absence tests are unaffected)
  and calls `build_revalidating_consumer_class(GraphQLWSConsumer)` **inside** the existing
  `try: from strawberry.channels import GraphQLWSConsumer` block's success path, so a degraded
  Strawberry install still raises exactly `_STRAWBERRY_CHANNELS_BROKEN_HINT`.
- **The class is not exported.** `consumers.py` declares no `__all__` and is not re-exported by
  `routers.py::__all__` (which `tests/test_routers.py::test_repeated_access_returns_the_cached_class_which_is_subclassable`
  pins to the one symbol) nor by the package root. This matches `auth/sessions.py`'s stated
  "deliberately NOT re-exported" posture, and it is coherent with the spec's own seam design:
  the supported choices are *the package default* or *your own consumer* (a class + a window is
  a construction error, Edge cases), not "subclass ours". Recorded as a follow-up candidate: if
  a consumer needs to extend the package default, a later card exports it by adding one name to
  the existing PEP 562 `__getattr__` — no new mechanism required.

### Implementation steps

Line numbers below are pin-at-write-time navigational hints; verify against the current source
before editing (another pass may have shifted the file).

1. **New file `django_strawberry_framework/consumers.py`.** Module docstring first: its **first
   line must be one complete sentence ending in a period** — `scripts/build_tree_md.py`
   #"first docstring line must be a sentence." raises `TreeRenderError` otherwise, and that line
   is what `docs/TREE.md` renders in Slice 5. No staging language ("planned", "Slice N",
   `TODO(`). The docstring states, in this order: what the module owns; that the class is built
   by `routers.py` behind the soft-`channels` guard and is deliberately not exported; the
   channels-free import boundary (above); and the **Decision 12 lifetime statement** (see step 6).
   Module constants, in this order:
   - `_DEFAULT_REVALIDATION_WINDOW = 0.0` — the ONE spelling of the default, imported by
     `routers.py` for its keyword default so the number is not typed twice.
   - `_REVOKED_SESSION_MESSAGE` — the single rejection message, used by both protocols and by
     the fail-closed branch. Wording must be a transport-capability statement, must not
     distinguish "revoked" from "store failure" (no information disclosure), and must not be the
     failed-login envelope (spec #"Error shapes"). Proposed:
     `"The session for this WebSocket connection is no longer valid. Reconnect with a current session to continue."`
   - `_REVALIDATED_AT_SCOPE_KEY = "__django_strawberry_framework_ws_revalidated_at__"` — the
     private namespaced scope key, shaped after `auth/sessions.py::_SCOPE_LOCK_KEY`.
2. **`consumers.py::_monotonic() -> float`** — `return time.monotonic()`. Docstring: monotonic
   (never wall clock, so a clock step cannot widen or collapse the window) and named as the
   deterministic test seam the window rows monkeypatch.
3. **`consumers.py::resolved_revalidation_window(value) -> float`** — the validator, shaped after
   `views.py::_resolved_max_request_body_bytes`: reject `bool` explicitly, reject a non-`(int,
   float)`, reject a negative, reject a non-finite (`math.isfinite`) — each with
   `ConfigurationError` naming the parameter, the domain ("a number of seconds `>= 0.0`"), and
   the `got {type(value).__name__} {value!r}` tail. Return `float(value)`. Called by the router
   (step 7), so the failure is a **construction-time** failure, never a per-operation one.
4. **`auth/sessions.py::session_store_class() -> type`** — lift
   `import_string(f"{settings.SESSION_ENGINE}.SessionStore")` out of
   `auth/sessions.py::uses_signed_cookie_sessions` into a documented 2-line helper and re-point
   that function at it (its `issubclass(store_cls, SignedCookieSessionStore)` answer must stay
   byte-identical — this is a pure extraction, and `tests/auth/` coverage of
   `uses_signed_cookie_sessions` must stay green untouched).
5. **`consumers.py::revalidate_operation_actor(handler, operation_id, *, errors_as_list) -> bool`**
   — the ONE decision function. Returns `True` to let the operation proceed, `False` after it has
   already sent the per-operation `error` message. Ordered body, one branch per bullet:
   1. `if not handler.connection_acknowledged: return True` — the handshake is incomplete, so
      upstream's own `4401 Unauthorized` close must be what the client sees; no session read.
   2. `scope = handler.view.scope` (Upstream verification #1: `handler.view` **is** the
      consumer, and `ChannelsWSConsumer` carries the ASGI scope).
   3. `actor = scope.get("user")`;
      `if actor is None or not actor.is_authenticated: return True` — the anonymous carve-out
      (spec Decision 11 #"has no session actor to revalidate"). Comment names
      `auth/mutations.py::_authenticated_actor_or_none` as the same predicate and why it is not
      imported (DRY item 8).
   4. Window: `window = getattr(handler.view, "revalidation_window", …)`; if `window > 0.0` and
      `_monotonic() - scope.get(_REVALIDATED_AT_SCOPE_KEY, -inf) < window`, `return True`.
      Prefer the explicit `scope.get(key)`-is-`None` form over an `-inf` sentinel if it reads
      more plainly; either way there is exactly one comparison.
   5. `try:` resolve the fresh actor —
      `store = session_store_class()(scope["session"].session_key)` (no IO: the store's `load()`
      is deferred to first item access) then
      `refreshed = await get_user({"session": store})` (the ONE `database_sync_to_async`
      boundary; the synthetic one-key mapping is deliberate — Upstream verification #7 proves
      `get_user` reads nothing else, and passing the real scope would risk upstream's
      `session.flush()` landing on the connection's own session object).
      `except Exception:` → `logger.exception(…)` naming the fail-closed degrade, then fall
      through to the rejection (Edge cases #"A revalidation database error must fail closed").
      Catch `Exception`, **not** `BaseException`: an `asyncio.CancelledError` from task teardown
      must propagate, not be converted into a denial.
   6. `if not refreshed.is_authenticated:` → reject. Do **not** write `AnonymousUser()` back:
      leaving the stale actor in place is what makes every later operation on the socket take the
      same path and be denied identically (spec Decision 11 #"the scope keeps the stale actor").
      Rejection = `await handler.send_message({...})` with
      `payload=[formatted] if errors_as_list else formatted` where
      `formatted = GraphQLError(_REVOKED_SESSION_MESSAGE).formatted`, then `return False`.
   7. Success: `scope["user"] = refreshed` (the write-back — Upstream verification #8), and, only
      when `window > 0.0`, `scope[_REVALIDATED_AT_SCOPE_KEY] = _monotonic()`. `return True`.
   The docstring must state: why this is not `get_context` / `receive()` (cite Decision 11's
   rejected alternatives in one sentence each, no more); that the read is alias-explicit **by
   delegation** — both the session load and the user load resolve their alias through Django's
   own `router.db_for_read`, never a hardcoded `"default"`, which is the same authority
   `utils/permissions.py::resolve_auth_aliases` reads (Edge cases #"The revalidation read is
   alias-explicit"); that it takes **no** lock (`auth/sessions.py::scope_session_lock` guards
   *session mutations*; this is a read of a private store, both interleavings with a concurrent
   `logout` are safe, and taking a mutation lock on the socket's critical path would add
   contention for nothing); and the signed-cookie caveat (with
   `SESSION_ENGINE=…signed_cookies`, a flush is not observable server-side — which is why
   `auth/sessions.py::logout_supported` already refuses logout there — while the disabled-user
   and password-rotation shapes still are).
6. **`consumers.py::build_revalidating_consumer_class(base_consumer_cls) -> type`** — a pure
   factory (no cache, no guard, no import of `channels` or `strawberry`). Body:
   - `class _RevalidatingGraphQLTransportWSHandler(base_consumer_cls.graphql_transport_ws_handler_class)`
     with exactly:
     `async def handle_subscribe(self, message): if not await revalidate_operation_actor(self, message["id"], errors_as_list=True): return` then
     `await super().handle_subscribe(message)`.
   - `class _RevalidatingGraphQLWSHandler(base_consumer_cls.graphql_ws_handler_class)` with the
     same two lines against `handle_start` / `message["id"]` / `errors_as_list=False`.
   - `class GraphQLWebSocketConsumer(base_consumer_cls)` setting both handler class attributes
     and `def __init__(self, *args, revalidation_window=_DEFAULT_REVALIDATION_WINDOW, **kwargs)`
     that stores `self.revalidation_window` **before** `super().__init__(*args, **kwargs)`.
   - The class docstring carries the **Decision 12 code-documentation half**: the package imposes
     no maximum connection lifetime; the enforcement seam is `websocket_consumer_class=`, and an
     injected class can both set upstream's `connection_init_wait_timeout` / `keep_alive`
     constructor knobs and close the socket on its own schedule; a hard lifetime belongs to the
     ASGI server / reverse proxy; and with revalidation on, the freshness bound is the
     revalidation window rather than the connection lifetime. Consumer-facing prose with the
     concrete directives is Slice 5's (spec Decision 12 assigns it there, and Slice 5's
     `docs/README.md` bullet already names "the WebSocket revalidation window and
     connection-lifetime expectations" — **no new Slice 5 obligation is created**).
   - Annotate the two `message` parameters as `Any` with a comment naming the upstream TypedDicts
     (`SubscribeMessage` / `StartMessage`). Deliberate: a `TYPE_CHECKING` import of
     `strawberry.subscriptions.protocols.*.types` would be a deep-path dependency no gate
     verifies, and the factory otherwise imports nothing from upstream at all.
7. **`routers.py` — module-level.** Add
   `from .consumers import _DEFAULT_REVALIDATION_WINDOW, build_revalidating_consumer_class,
   resolved_revalidation_window` (adjust names/underscores to whatever step 1-3 settles on; a
   cross-module import of an underscored constant should instead be a plain name — Worker 2 picks
   one spelling and uses it consistently). Add two module-level `ConfigurationError` message
   constants beside `_MISSING_DJANGO_APPLICATION_HINT`:
   - `_UNUSABLE_WEBSOCKET_CONSUMER_HINT` — names both accepted shapes (a `GraphQLWSConsumer`
     subclass, or a callable invoked as `factory(schema=schema)` returning the ASGI application)
     and what was received.
   - `_WINDOW_WITH_INJECTED_CONSUMER_HINT` — "a knob that does nothing is worse than an error"
     (Edge cases #"`websocket_revalidation_window` is meaningless when a custom class is
     injected"): state that the window configures the *package's* consumer only, and that the
     injected class owns its own revalidation policy.
8. **`routers.py::_build_router_class`** — after the existing
   `from strawberry.channels import GraphQLWSConsumer` try-block succeeds, add
   `package_consumer_class = build_revalidating_consumer_class(GraphQLWSConsumer)` (one
   statement, inside the same builder, so it is cached with `_ROUTER_CLASS` and dies with it).
9. **`routers.py::DjangoGraphQLProtocolRouter.__init__`** — the reopened signature:
   ```
   def __init__(
       self,
       schema: BaseSchema,
       django_application: ASGIHandler,
       *,
       websocket_url_pattern: str = r"^graphql/?$",
       websocket_consumer_class: Any = None,
       websocket_revalidation_window: float = _DEFAULT_REVALIDATION_WINDOW,
   ) -> None:
   ```
   Both new parameters go **after the existing `*`**, so
   `tests/test_routers.py::test_the_websocket_pattern_is_keyword_only_with_no_legacy_url_pattern_alias`
   stays green unmodified (its `TypeError, match="positional"` probe passes a third positional,
   which still binds nothing) and Slice 1's Decision-4 contract is preserved. The signature now
   has 6 parameters, so `scripts/check_trailing_commas.py` (threshold 4) requires the
   one-per-line + trailing-comma layout above — run it with **explicit paths only**, never the
   repo-wide auto-fix (it would touch the maintainer's untracked `drys.md` / `vulns.md`).
   Body order, before `super().__init__`:
   1. the existing `if not callable(django_application): raise ConfigurationError(...)` guard,
      unchanged and still first;
   2. `window = resolved_revalidation_window(websocket_revalidation_window)` — validate the value
      on its own terms first, so a bad value is a bad value regardless of what else was passed;
   3. `if websocket_consumer_class is not None and window > 0.0: raise
      ConfigurationError(_WINDOW_WITH_INJECTED_CONSUMER_HINT)` — an explicit `0.0` alongside an
      injected class is harmless and stays legal (it configures nothing either way);
   4. resolve the WS ASGI application for the `re_path`, in exactly three cases:
      `websocket_consumer_class is None` → `package_consumer_class.as_asgi(schema=schema,
      revalidation_window=window)`; a `type` → require
      `issubclass(candidate, GraphQLWSConsumer)` (else `_UNUSABLE_WEBSOCKET_CONSUMER_HINT`) then
      `candidate.as_asgi(schema=schema)`; otherwise `callable(candidate)` →
      `candidate(schema=schema)`, and a non-callable raises
      `_UNUSABLE_WEBSOCKET_CONSUMER_HINT`. Order matters: a class is callable, so the `type`
      test must come first. Keep this as one small private module-level helper in `routers.py`
      (proposed `_websocket_application(...)`) rather than four branches inline in `__init__`, so
      the builder's hotspot does not grow;
   5. the existing `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([re_path(...)])))`
      composition, **byte-identical except for the callback expression**. The wrappers stay the
      router's, applied around whatever was selected — that structural guarantee is Decision 11's
      whole safety argument and Edge cases #"An injected consumer class opts out of
      revalidation, not out of the wrappers".
10. **`routers.py::DjangoGraphQLProtocolRouter`'s class docstring** — add one short paragraph for
    the seam (both accepted shapes, the wrapper guarantee, the window's meaning and its `0.0`
    default, and the "class + window is an error" rule) and one sentence pointing at
    `consumers.py::GraphQLWebSocketConsumer` for the lifetime statement. Keep the existing
    `asgi.py` / `urls.py` example block unchanged.
11. **Hygiene, in this order:** `uv run ruff format .`, `uv run ruff check --fix .`,
    `uv run python scripts/check_trailing_commas.py django_strawberry_framework/consumers.py
    django_strawberry_framework/routers.py django_strawberry_framework/auth/sessions.py
    tests/test_routers.py` (explicit paths). ASCII-only in `.py`. No `pytest --cov*` ever.

### Test additions / updates

All package-tier in **`tests/test_routers.py`** — Decision 13 #"Placement" pins the revalidation
matrix there (communicator-driven), and the spec's Risks note keeps the documented
genuinely-unreachable-live exemption for the router because fakeshop has no `asgi.py`. No live
tier, no new test module, no fakeshop change.

**Harness work first (DRY items 6 and 7).**

- `_open_ws(application, *, cookie=None, subprotocol="graphql-transport-ws")` — an
  `@contextlib.asynccontextmanager` that builds the `WebsocketCommunicator` (origin header +
  optional cookie header, exactly as `_ws_graphql_data` does today), connects, asserts the
  negotiated subprotocol, sends `{"type": "connection_init"}`, asserts `connection_ack`, yields
  the communicator, and `disconnect()`s in `finally`.
- `_ws_operation(communicator, query, *, op_id="1", subprotocol="graphql-transport-ws")` — sends
  the protocol's operation frame and returns the raw received message. One module constant maps
  protocol → `(operation_frame_type, success_message_type)`:
  `{"graphql-transport-ws": ("subscribe", "next"), "graphql-ws": ("start", "data")}`.
- `_ws_graphql_data(...)` — **rewritten** to `async with _open_ws(...)` + `_ws_operation(...)`,
  keeping its current contract (assert `next`, assert no `errors`, return `payload["data"]`) so
  its three existing callers (Tests 10, 16, 18) are untouched.
- `_make_user_and_session(username, password=…)` — module-level `@database_sync_to_async`, lifted
  from Test 18's local `make_user_and_session_cookie` with the same three session keys
  (`SESSION_KEY` / `BACKEND_SESSION_KEY` / `HASH_SESSION_KEY`) and `session.save()`; returns the
  user plus the `f"{settings.SESSION_COOKIE_NAME}={session.session_key}"` cookie (and the session
  key, which the revocation rows need). Test 18 calls it; **its assertions do not change**.
- Three tiny `@database_sync_to_async` out-of-band mutators — flush the session row, set
  `is_active=False`, and `set_password(...) + save()` — standing in for the spec's "**separate**
  request". Deliberate deviation, stated in the docstring: the property under test is "denied
  **without reconnecting**", not "an HTTP round trip happened", and this module's schema is
  ORM-free on purpose (sync ORM in a resolver on the event loop is `SynchronousOnlyOperation`);
  Test 18 already establishes the `database_sync_to_async` ORM-write idiom for exactly this file.
- `_REVOKED_SUBSTRING` — a **re-typed** fragment of `_REVOKED_SESSION_MESSAGE` (never imported),
  matching this module's `_HINT_SUBSTRING` discipline so a message drift is caught.

**Construction / composition rows (sync, no DB).**

| Row | Test | Pins |
|---|---|---|
| 19 | `test_the_default_websocket_consumer_is_the_packages_revalidating_subclass` | the default mount's `routes[0].callback.consumer_class` is a `GraphQLWSConsumer` subclass that is **not** `GraphQLWSConsumer` itself, and its `consumer_initkwargs` carry the exact schema object plus `revalidation_window == 0.0` (spec checklist box 2 + box 3's default) |
| 20 | `test_an_injected_consumer_class_still_sits_inside_both_wrappers` | **spec row 28**: with `websocket_consumer_class=Injected`, `unwrap_auth_stack(unwrap_origin_validator(...))` still walks, `_route_patterns` is unchanged, and `routes[0].callback.consumer_class is Injected`; plus `application_mapping["http"]` is still the supplied object by identity |
| 21 | `test_an_injected_consumer_factory_is_called_with_the_schema_and_mounted` | the factory branch: the factory records the `schema=` keyword it received (identity with the passed schema) and the route's callback **is** the object it returned |
| 22 | `test_an_unusable_websocket_consumer_class_is_a_construction_error` | `ConfigurationError` for a `type` that is not a `GraphQLWSConsumer` subclass and for a non-callable non-class; re-typed message substrings |
| 23 | `test_the_revalidation_window_rejects_unusable_values` | `ConfigurationError` matrix: `-1.0`, `True`, `"1.0"`, `float("nan")`, `float("inf")`; and `0`/`0.0`/`2.5` are accepted (the accepted half also proves an `int` is coerced) |
| 24 | `test_injecting_a_consumer_class_with_a_window_is_a_construction_error` | **spec row 29**, plus the legal corner: `websocket_consumer_class=Injected, websocket_revalidation_window=0.0` constructs fine |
| 25 | `test_the_two_new_websocket_keywords_are_keyword_only` | `inspect.signature(...)` — `websocket_url_pattern`, `websocket_consumer_class`, `websocket_revalidation_window` are all `KEYWORD_ONLY`. A *new* row: Slice 1's `::test_the_websocket_pattern_is_keyword_only_with_no_legacy_url_pattern_alias` must stay green **unmodified**, and this one extends its subject to the two parameters Slice 4 adds |

**Execution rows (async; `@pytest.mark.django_db(transaction=True)` — Test 18's marker, required
so the executor-thread session/user reads see committed rows; the module's existing comment block
above the communicator tests already explains why every communicator row carries `django_db`).**

| Row | Test | Pins |
|---|---|---|
| 26 | `test_a_revoked_session_is_denied_on_the_next_operation_without_reconnecting` | **spec row 25**, parametrized `flushed` / `disabled` / `password-rotated`: one socket, operation 1 succeeds (`next` with data), the out-of-band mutation runs, operation 2 on the **same** communicator returns `{"type": "error", "id": "2", "payload": [{"message": …}]}` carrying `_REVOKED_SUBSTRING`. Assert the payload is a **list** (the transport-ws wire shape) and that no reconnect happened (same communicator object, no second `connect()`). Add a third operation asserting the denial is **stable** (spec Decision 11 #"denied identically") rather than degrading to an executing anonymous operation |
| 27 | `test_a_valid_session_keeps_executing_and_the_next_operation_sees_the_refreshed_actor` | **spec row 26** as amended: operation 1 succeeds; an out-of-band `username` change (plus an `is_staff` flip if a second field helps) is committed; operation 2's resolver reads `request_from_info(info).user` and returns the **new** value. That is a genuine re-read (the connect-time actor cannot produce it) and it is the single read `get_queryset` / `DjangoModelPermission` resolve their actor through. Needs one new field on the module-local `Query` (e.g. `actor_identity` returning `f"{request.user.username}|{request.user.is_staff}"`) — attribute reads only, no ORM, so the ORM-free rule holds |
| 28 | `test_the_revalidation_window_defers_the_denial_until_it_expires` | **spec row 27**: `websocket_revalidation_window=3600.0`; operation 1 succeeds, session is flushed, operation 2 **still succeeds** (inside the window); then `monkeypatch.setattr(consumers, "_monotonic", …)` advances the clock past the window and operation 3 is denied. Deterministic — no `asyncio.sleep`, no wall-clock dependence |
| 29 | `test_the_legacy_graphql_ws_protocol_is_revalidated_at_handle_start` | the **second protocol**: `subprotocol="graphql-ws"`, `start` → `data` for operation 1, revoke, `start` again → `{"type": "error", "id": …, "payload": {"message": …}}`. Assert the payload is a **dict** (the legacy wire shape), which is what distinguishes the two `errors_as_list` call sites |
| 30 | `test_a_revalidation_store_failure_denies_the_operation_and_is_logged` | **spec row 30**: `monkeypatch` the fresh-store resolver (or `channels.auth.get_user`) to raise; operation 2 is denied with the same message, and `caplog` shows the `django_strawberry_framework` logger's `ERROR` record — proving fail-closed *and* not silently swallowed. Also assert the stale actor was **not** replaced by a working actor (no fallback) |
| 31 | `test_an_anonymous_socket_is_not_revalidated` | the anonymous carve-out: no cookie, operation succeeds, and the store resolver is monkeypatched to raise `AssertionError` — so the row proves the early return really skipped the session read rather than merely tolerating it |
| 32 | `test_a_subscribe_before_connection_init_is_closed_by_upstream_without_revalidating` | the acknowledged carve-out: with the same poisoned store resolver, sending `subscribe` before `connection_init` yields upstream's `4401 Unauthorized` close and no revalidation. Use the `send_input` + explicit receive shape the module already uses for reject directions rather than `connect()`-then-timeout |

**Branch-coverage ledger** (the `fail_under = 100` gate is the maintainer's, but every branch must
have an owner): acknowledged-carve-out → 32; anonymous-carve-out → 31; window-not-expired → 28;
window-expired → 28; refreshed-authenticated (write-back) → 27; refreshed-not-authenticated
(reject) → 26, 29; `except Exception` → 30; `errors_as_list=True` / `False` → 26 / 29;
consumer-selection default / class / factory / bad-class / bad-value → 19, 20, 21, 22;
window validator arms → 23; window-plus-class → 24; `session_store_class()` → every DB row plus
the existing `uses_signed_cookie_sessions` tests.

**Temp/scratch tests for Worker 3.** A scratch communicator script under
`docs/builder/temp-tests/slice-4/` is a reasonable way to confirm the two wire shapes
independently (assert the raw `error` frame for each protocol) before trusting the rows above.
Note it in `Notes for Worker 3` and delete or promote it per BUILD.md.

**Sweeps Worker 2 owes.** `grep -rn "url_pattern\|websocket_consumer_class\|websocket_revalidation_window" tests/ examples/ docs/`
to catch any other construction site of the router (Slice 1 repaired
`tests/auth/test_mutations.py::_channels_router` into a local `ProtocolTypeRouter`, so it should
**not** appear — confirm, do not assume), and `grep -rn "GraphQLWSConsumer" django_strawberry_framework/ tests/`
to confirm the import stays single-sited in `routers.py`.

### Implementation discretion items

Assessed and decided — these are Worker 2's to spell:

1. **Exact identifier spellings** in `consumers.py` (`revalidate_operation_actor` vs
   `revalidate_scope_actor`, `resolved_revalidation_window` vs `_resolved_revalidation_window`,
   `_RevalidatingGraphQLTransportWSHandler`'s length). One constraint: a name imported by
   `routers.py` should not be underscore-prefixed, and the two generated handler classes should
   be.
2. **The window-expiry comparison's sentinel** — `scope.get(key, float("-inf"))` vs an explicit
   `is None` test. Equivalent; pick the one that reads plainly with no extra branch.
3. **Whether the `formatted` payload is built by one local expression or two** inside the
   rejection (`payload=[formatted] if errors_as_list else formatted` vs an `if/else` block).
4. **The exact wording** of `_REVOKED_SESSION_MESSAGE`, `_UNUSABLE_WEBSOCKET_CONSUMER_HINT`, and
   `_WINDOW_WITH_INJECTED_CONSUMER_HINT`, within the constraints named in steps 1 and 7.
5. **Whether row 27 adds one new `Query` field or extends the existing `actor` field.** A new
   field is cleaner (the existing `actor` string is asserted verbatim by Test 16); extending it
   would force a Test 16 assertion change, which is why the plan leans new — but the shape is
   Worker 2's.
6. **Where `_open_ws` / `_ws_operation` sit in the file** relative to `_ws_graphql_data`, and
   whether the protocol→frames mapping is a dict or a tuple of pairs.

Everything architectural is fixed above. Nothing in this list changes a contract.

### Planning-pass spec-reconciliation notes (Worker 1)

1. **Every symbol the spec names for this slice exists or is created here.** Verified present:
   `strawberry.channels.GraphQLWSConsumer`, `BaseGraphQLTransportWSHandler.handle_subscribe`,
   `BaseGraphQLWSHandler.handle_start`, `graphql_transport_ws_handler_class` /
   `graphql_ws_handler_class`, `channels.auth.get_user`, `AllowedHostsOriginValidator`,
   `AuthMiddlewareStack`, `exceptions.py::ConfigurationError`,
   `utils/permissions.py::ChannelsRequestAdapter.user` (the `scope["user"]` reader the write-back
   feeds), `utils/permissions.py::request_from_info`, `auth/sessions.py::logout_supported` /
   `::uses_signed_cookie_sessions`. Created here: `consumers.py` and
   `GraphQLWebSocketConsumer` (the spec names the class but not a module — the module choice is
   this plan's, justified above).
2. **`ConfigurationError` is in `exceptions.py`, not `conf.py`** — confirmed; `routers.py`
   already imports it from there.
3. **Four spec edits made this pass** — see the next section. Two are contract-completing (the
   factory calling convention; the anonymous / stale-actor boundary cases), one is a precision
   fix, one narrows an unexecutable test row to the strongest executable proof.
4. **No contradiction found between Decision 11 and the codebase.** The one thing that *looked*
   like a contradiction — Edge cases #"The revalidation read is alias-explicit … use the router's
   resolved alias rather than an implicit default" — resolves cleanly: the session load and the
   user load both route through Django's own `router.db_for_read`, which is a deployment's
   explicit routing decision and never a hardcoded `"default"`. The alternative reading (the
   package computes an alias and forces it) is not achievable without reimplementing
   `channels.auth.get_user` and the session backend — which Helper-reuse forbids — and would
   contradict Decision 11's "subclass upstream, do not reimplement" posture. No spec edit
   needed; the plan records the reading and the docstring will state it.
5. **Decision 12's ownership splits by surface, as this build has done twice before.** The
   checklist box lives in Slice 4 while Decision 12's own text assigns the documentation to
   Slice 5. Split: the **code-documentation** half (the four facts, in
   `consumers.py::GraphQLWebSocketConsumer`'s docstring and one sentence in the router docstring)
   lands here; the **consumer-facing prose** with concrete server/proxy directives stays in
   Slice 5, which already names it. Worker 2 may therefore tick box 4 when the docstrings land.
6. **New Slice 5 obligation created by this slice — exactly one, stated explicitly.**
   `docs/TREE.md`'s Slice 5 regenerate currently names only `views.py` and the new tests; it must
   also cover **`django_strawberry_framework/consumers.py`**. No DB row is required (
   `scripts/build_tree_md.py` renders current trees from the filesystem + module docstrings and
   skips `TrackedPath` predictions for paths already on disk), but the module docstring's first
   line must be a period-terminated sentence or the render raises `TreeRenderError`. Slice 5's
   glossary bullet already names "the consumer-injection seam, the revalidation window" as new
   terms, so no glossary obligation is added. Slice 5's eight standing prose obligations gain
   nothing else from this slice, and `examples/fakeshop/test_query/README.md` is untouched (no
   live rows here).
7. **Two BINDING cross-slice DRY items inherited by `bld-integration.md`** (from the Slice 1-3
   artifacts, restated so this slice does not accidentally discharge or duplicate them): extract
   `_user_who_can_add_categories()` in `examples/fakeshop/test_query/test_transport_api.py`, and
   rewire that file's six inline `await ….post(...)` blocks onto the existing `_post_bytes`.
   Slice 4 touches neither file and adds no async row there.
8. **`test_transport_api.py`'s module-docstring first line** is Slice 5's to correct (Slice 3
   deliberately deferred pinning the file's slice scope "because Slice 4 could still add rows").
   Slice 4 adds **no** row to that file, so the number Slice 5 pins is now knowable — recorded
   for the Slice 5 planner.
9. **No version quintet movement, no `CHANGELOG.md`, no `conf.py` key, no public export.**
   `django_strawberry_framework/__init__.py` is untouched; `routers.py::__all__` stays
   `("DjangoGraphQLProtocolRouter",)` (a test pins it); `views.py` is untouched.
10. **Spec status line re-verified** (`docs/spec-065-transport_security-0_0_15.md` lines 37-44):
    "Status: **IN BUILD — Slices 1-3 (S1, S2, S9) are built and accepted; Slices 4-5 remain.**"
    is accurate at the start of this planning pass; it needs Worker 1's edit once Slice 4 is
    `final-accepted`.

### Spec changes made (Worker 1 only)

1. **`docs/spec-065-transport_security-0_0_15.md` Decision 11, lines 1158-1163** (the
   `**Decision.**` paragraph) — added the calling convention for both injected shapes: a class
   must subclass `GraphQLWSConsumer` and is mounted through its own `as_asgi(schema=schema)`; a
   factory is called as `factory(schema=schema)` and must return the ASGI application; anything
   else is a `ConfigurationError` at construction. *Reason:* the spec offered "a subclass **or** a
   factory callable" with no factory contract, so the public API's calling convention was
   unspecified — an implementation gap that would otherwise have been resolved silently by
   Worker 2 or left to a review round. Triggered by Slice 4.
2. **Decision 11, after the `**What the revalidation does.**` paragraph (new paragraph at lines
   1192-1199)** — stated two boundary cases as contract: an anonymous scope actor is passed
   through with no session read, and a denied operation leaves the stale actor in place so later
   operations are denied identically rather than downgrading to an executing anonymous session.
   *Reason:* both are consumer-visible behaviors that the "revalidates the session actor per
   operation" wording leaves emergent; the second is a genuine fail-closed-vs-fail-open choice
   that must not be made by implementation accident. Triggered by Slice 4.
3. **Decision 11 `**One deliberate constraint…**`, line 1226** — "a session read per operation"
   → "per **authenticated** operation", for consistency with edit 2. *Reason:* precision. The
   bounded-window trade sentence (line ~1204) and the Risks note on per-operation query cost
   (line ~1720) were both re-read and left unchanged: each describes the cost model of the
   authenticated case they are about, and both remain accurate under edit 2.
4. **Test plan row 26, lines 1629-1637** — rewritten from "the refreshed actor reaches a
   `get_queryset` hook and a `DjangoModelPermission` gate" to "the refreshed actor is what the
   next operation observes at `request_from_info` — the single read both layers resolve their
   actor through", with the reason recorded inline. *Reason:* as written the row is not
   executable in the tier the same spec pins for it. Decision 13 #"Placement" puts the
   revalidation matrix in `tests/test_routers.py`, whose module docstring records that the
   execution schema is deliberately ORM-free because sync ORM in a resolver on the event loop
   raises `SynchronousOnlyOperation`; and the spec's own Risks note keeps the async live tier out
   of this card because fakeshop has no `asgi.py`. The replacement is not a weakening: an
   out-of-band change to the user row that the next operation reads back proves a genuine
   re-read, which asserting "a permission gate returned True" would not. Triggered by Slice 4.

`uv run python scripts/check_spec_glossary.py --spec docs/spec-065-transport_security-0_0_15.md`
→ `OK: 37 terms` after all four edits (unchanged count; every term added by the edits reuses an
existing linked form and no `-terms.csv` row is owed).

### Spec slice checklist (verbatim)

Copied byte-for-byte from `docs/spec-065-transport_security-0_0_15.md` lines 172-181 (the four
sub-bullets of the Slice 4 block), preserving text, nesting, em-dashes, and inline citations;
verified with `diff` against the spec extract. The in-page `(#decision-11--…)` / `(#decision-12--…)`
anchors are verbatim from the spec and resolve there, not in this scratchpad artifact.

  - [ ] `websocket_consumer_class=` injection on the router; the injected class still sits
        inside `AllowedHostsOriginValidator` + `AuthMiddlewareStack` by construction
        ([Decision 11](#decision-11--a-websocket-consumer-classfactory-injection-seam-with-a-revalidating-package-default)).
  - [ ] The package's default WebSocket consumer revalidates the session actor per
        operation and writes the refreshed actor back onto `scope["user"]`; an invalid
        session rejects the operation.
  - [ ] `websocket_revalidation_window=` — an explicit, bounded, opt-in revocation delay
        (default `0.0` = revalidate every operation).
  - [ ] Maximum connection lifetime documented, with the enforcement seam named
        ([Decision 12](#decision-12--maximum-connection-lifetime-is-documented-and-seamed-not-silently-enforced)).
