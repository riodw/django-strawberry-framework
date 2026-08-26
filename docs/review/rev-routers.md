# Review: `django_strawberry_framework/routers.py`

Status: verified

## Understanding

`django_strawberry_framework/routers.py` provides the Channels ASGI integration entry point `DjangoGraphQLProtocolRouter` (spec-041, spec-046). It implements the transport protocol split: delegating HTTP traffic directly to Django's native ASGI handler while composing the package's hardened WebSocket middleware and consumer stack.

It owns:
1. **Lazy export and soft-dependency boundary (`__getattr__`, `require_channels`, `_build_router_class`)**:
   - Manages `channels` as a soft dependency behind a PEP 562 lazy module `__getattr__` export.
   - Guarded by `require_channels` via `utils.imports.require_optional_module`, raising actionable `ImportError` (`_CHANNELS_INSTALL_HINT`) only upon symbol access (`from ...routers import DjangoGraphQLProtocolRouter` or `*`), keeping `import django_strawberry_framework` and `import django_strawberry_framework.routers` free of soft-dependency import requirements.
   - Distinguishes missing channels from degraded/partial installs with split actionable messages (`_CHANNELS_BROKEN_HINT`, `_STRAWBERRY_CHANNELS_BROKEN_HINT`).
   - Caches the synthesized router class behind `_ROUTER_CLASS_LOCK` using double-checked locking for thread safety across concurrent initializations.
2. **Construction parameter validation**:
   - `django_application`: enforces callable ASGI application requirement at construction; provides detailed migration guidance in `_MISSING_DJANGO_APPLICATION_HINT` when `None` or non-callable values are passed (omission raises Python `TypeError`).
   - `websocket_url_pattern`: requires exact `str` type and compiles regular expressions upfront to prevent malformed or non-string patterns from failing late during handshake (`_INVALID_WEBSOCKET_URL_PATTERN_HINT`).
   - `websocket_revalidation_window`: validates window parameter via `consumers.resolved_revalidation_window` and rejects positive window values when paired with a custom `websocket_consumer_class` (`_WINDOW_WITH_INJECTED_CONSUMER_HINT`).
3. **Consumer injection seam (`_websocket_application`, `_factory_application`, `_require_factory_calling_convention`)**:
   - Accepts `None` (resolving package default `GraphQLWebSocketConsumer` with configured revalidation window).
   - Accepts `strawberry.channels.GraphQLWSConsumer` subclasses mounted via `candidate.as_asgi(schema=schema)`.
   - Accepts factory callables invoked as `factory(schema=schema)`: pre-validates call signatures via `inspect.signature(...).bind` (allowing unintrospectable callables), enforces that the returned object is callable, and detects/closes unawaited coroutine returns (`_ASYNC_FACTORY_HINT`) to prevent event-loop warnings/crashes.
   - Enforces construction-time failure (`_UNUSABLE_WEBSOCKET_CONSUMER_HINT`) on non-consumer classes, non-callable types, or non-matching factory signatures.
4. **Protocol composition & security middleware ordering (`ProtocolTypeRouter`)**:
   - Maps `"http"` verbatim to `django_application` without middleware wrappers, ensuring HTTP requests traverse Django's standard middleware stack (`ALLOWED_HOSTS`, CSRF, security headers, auth) and route to `views.DjangoGraphQLView` in URLconf.
   - Maps `"websocket"` to the complete security stack composed in strict outermost-to-innermost order:
     1. `consumers.DjangoWebSocketHostValidator` (handshake Host header validation against Django's `HttpRequest.get_host()`).
     2. `channels.security.websocket.AllowedHostsOriginValidator` (Origin header validation against `settings.ALLOWED_HOSTS`).
     3. `channels.auth.AuthMiddlewareStack` (session middleware and `scope["user"]` population).
     4. `channels.routing.URLRouter` with `re_path(websocket_url_pattern, websocket_application)`.

## Verification

1. Traced module connections across dependencies and callers:
   - `consumers.py`: factory integration (`build_revalidating_consumer_class`), Host validator (`DjangoWebSocketHostValidator`), and revalidation window validator (`resolved_revalidation_window`).
   - `utils/imports.py`: soft-dependency import helper (`require_optional_module`).
   - `exceptions.py`: `ConfigurationError` and `describe_value` error formatting.
   - `views.py`: independent HTTP URLconf endpoint declaration (`DjangoGraphQLView`).
2. Examined test suites:
   - `tests/test_routers.py` (166 tests): thoroughly verifies lazy module loading, missing/degraded dependency handling, router parameter validation, consumer injection seam (subclasses, factories, async rejections), Host/Origin handshake validation, and HTTP delegation.
3. Focused test executions:
   - `uv run pytest tests/test_routers.py --no-cov` (166 passed).
   - `uv run pytest tests/test_routers.py --cov=django_strawberry_framework.routers --cov-report=term-missing` (100% line coverage for `routers.py`).
4. Scratch tests:
   - `docs/review/temp-tests/routers/test_routers_scratch.py`: verified PEP 562 lazy loading, `AttributeError` on unknown names, `django_application` validation, `websocket_url_pattern` regex validation, consumer injection seam (subclasses, window conflict, factory signature pre-binding, async factory closure, non-callable returns), and exact WebSocket middleware wrapping hierarchy (6 passed).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/routers.py` is exceptionally well-designed, robust, and clean. It cleanly isolates soft dependencies behind PEP 562 lazy exports, enforces rigorous construction-time validation with actionable diagnostics, provides a safe consumer injection seam, and correctly composes the WebSocket security middleware hierarchy while preserving Django's native ownership of HTTP traffic. Code coverage is 100% with no defects or design improvements identified.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files:** None (zero-edit cycle). Scoped diff against cycle baseline (`HEAD` = `12779c99`) for `django_strawberry_framework/routers.py` is empty.
- **Permanent tests and pinned behavior:**
  - `tests/test_routers.py` (166 tests) completely pins the behavior of `routers.py`, including lazy import guards, channels absence/degraded install errors, parameter validation (`django_application`, `websocket_url_pattern`, `websocket_revalidation_window`), consumer injection seam mechanics, and middleware composition order.
- **Scratch verification:**
  - `docs/review/temp-tests/routers/test_routers_scratch.py` passed (6/6 tests), verifying lazy export resolution, parameter error branches, consumer subclass/factory resolution, coroutine closure, and middleware stack hierarchy.
- **Formatter and linter results:**
  - `uv run ruff check django_strawberry_framework/routers.py` passed with 0 errors.
  - `uv run ruff format --check django_strawberry_framework/routers.py` passed with 0 errors.
  - `python3 scripts/check_trailing_commas.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

Independently traced and verified the Channels ASGI integration, protocol routing split, lazy export boundary, constructor parameter validation, consumer injection seam, and WebSocket security middleware composition in `django_strawberry_framework/routers.py`.

### 1. Scoped diff and zero-edit confirmation
- Target: `django_strawberry_framework/routers.py`
- Baseline: `HEAD` (`12779c99`)
- Scoped diff: `git diff 12779c99 -- django_strawberry_framework/routers.py` is completely empty.

### 2. Behavioral re-trace and contracts verified
- **Lazy export & soft-dependency boundary (`__getattr__`, `require_channels`, `_build_router_class`)**:
  - Confirmed `import django_strawberry_framework` and `import django_strawberry_framework.routers` remain channels-free.
  - Verified PEP 562 `__getattr__` lazily materializes `DjangoGraphQLProtocolRouter` and raises standard `AttributeError` on unknown attributes.
  - Verified `_build_router_class()` uses double-checked locking across `_ROUTER_CLASS_LOCK` for thread-safe class synthesis.
  - Verified actionable and split error messages for missing channels (`_CHANNELS_INSTALL_HINT`) versus degraded channels/strawberry dependencies (`_CHANNELS_BROKEN_HINT`, `_STRAWBERRY_CHANNELS_BROKEN_HINT`).
- **Constructor parameter validation**:
  - `django_application`: verified omission raises Python `TypeError`, while passing `None` or non-callable objects raises `ConfigurationError` with detailed migration guidance (`_MISSING_DJANGO_APPLICATION_HINT`).
  - `websocket_url_pattern`: verified strict string type validation and immediate regex compilation (`_INVALID_WEBSOCKET_URL_PATTERN_HINT`), preventing malformed patterns or late handshake runtime failures.
  - `websocket_revalidation_window`: verified validation through `consumers.resolved_revalidation_window` and confirmed rejection of combining a positive window with a custom `websocket_consumer_class` (`_WINDOW_WITH_INJECTED_CONSUMER_HINT`).
- **Consumer injection seam (`_websocket_application`, `_factory_application`, `_require_factory_calling_convention`)**:
  - `None`: resolves package `build_revalidating_consumer_class(GraphQLWSConsumer)` configured with the validated window.
  - `GraphQLWSConsumer` subclass: verified direct mount via `candidate.as_asgi(schema=schema)`.
  - Factory callables: verified signature pre-validation via `inspect.signature(...).bind` (allowing unintrospectable callables without false rejections), verified returned object callability, verified unawaited coroutine closure preventing event loop warnings/crashes (`_ASYNC_FACTORY_HINT`), and confirmed factory body exceptions propagate directly without normalization.
- **Protocol composition & security middleware ordering**:
  - Verified `"http"` branch routes directly to `django_application` without middleware wrapping, maintaining native Django HTTP lifecycle (`ALLOWED_HOSTS`, CSRF, security headers, sessions) routed to `DjangoGraphQLView`.
  - Verified `"websocket"` branch composed in strict security hierarchy:
    1. `DjangoWebSocketHostValidator` (handshake Host header validation against Django `HttpRequest.get_host()`)
    2. `AllowedHostsOriginValidator` (Origin header validation against `settings.ALLOWED_HOSTS`)
    3. `AuthMiddlewareStack` (session middleware and `scope["user"]` population)
    4. `URLRouter` with `re_path(websocket_url_pattern, websocket_application)`.

### 3. Test executions and scratch tests
- **Permanent tests**:
  - `uv run pytest tests/test_routers.py --no-cov` (166 passed).
- **Scratch tests**:
  - `docs/review/temp-tests/routers/test_routers_scratch.py` (8 passed), verifying:
    - Lazy module exports and attribute access error handling.
    - Multi-threaded concurrent lazy class initialization thread safety.
    - `django_application` callable validation and error formatting.
    - `websocket_url_pattern` type checking and regex validation.
    - `websocket_consumer_class` subclass and factory resolution.
    - Revalidation window incompatibility with custom consumer class.
    - Async factory coroutine rejection and proper closure.
    - Unintrospectable callable factories and intact exception propagation.
    - Outermost-to-innermost WebSocket security middleware hierarchy.

### 4. Disposition of findings
- High / Medium / Low findings: None.
- All contracts, boundaries, and safety invariants are fully upheld.
- Review complete; verified.
