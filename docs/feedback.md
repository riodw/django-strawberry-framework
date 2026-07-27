# Fresh adversarial implementation review: transport security

## Scope and verdict

This review covers the current working-tree implementation of [spec 065][spec-065]:

- S1: Django-owned HTTP;
- S2: the request-body cap;
- S9: the strict UTF-8 wire contract; and
- the currently present S11 WebSocket consumer/revalidation implementation.

The concurrent row-preserving filter changes are outside this review. Slice 5's documentation
fold-in is also not judged as missing while the active [build plan][build-065] still marks it
unbuilt.

S1 is architecturally strong. The router now delegates HTTP directly to the supplied Django ASGI
application, the package view is a narrow upstream subclass, the WebSocket route is exact by
default, and the live tests exercise Django's Host, CSRF, security-header, cache, and URLconf
boundaries.

S11's central shape is also good: both WebSocket protocols delegate through small upstream handler
subclasses, one shared function owns the revalidation decision, invalid sessions fail closed, and
the router—not an injected consumer—owns the Origin and authentication wrappers.

The implementation is not ready to close, however. S2 still contains a blocker at the exact
Django 5.2.0 compatibility floor the card is meant to protect. Three additional boundary problems
remain around the UTF-8 policy, the consumer factory, and the auth subsystem's import boundary.

No pytest invocation was run for this review, per [AGENTS.md][agents]. The findings come from
source inspection plus narrow read-only runtime probes of the public/configuration seams.

## Blocker 1 — the counted body cap materializes the unbounded body before rejecting it

[`_RequestBodyLimitMixin._enforce_request_body_limit`][views] ends its non-multipart path with:

```python
if len(request.body) > limit:
    raise HTTPException(413, _BODY_LIMIT_REASON)
```

That comparison obtains the correct length, but only **after** `HttpRequest.body` has read the
entire stream into one in-memory `bytes` value and cached it as `request._body`.

This is especially important on ASGI:

1. `ASGIHandler.read_body` has already drained the network request into a
   `SpooledTemporaryFile`.
2. Above `FILE_UPLOAD_MAX_MEMORY_SIZE`, the spool has safely rolled to disk.
3. The package view then accesses `request.body`.
4. `HttpRequest.body` calls an unbounded `self.read()` and copies the complete file back into
   memory.
5. Only after that attacker-sized allocation does `len(...) > limit` produce the package's
   `413`.

Django 6.0 reduces the exposure only when its own `DATA_UPLOAD_MAX_MEMORY_SIZE` check runs first:
it seeks a seekable stream to its end before materializing it. The required Django 5.2.0 floor
does not have that seekable-stream check at all. With no `Content-Length`, an understated
declaration, or `DATA_UPLOAD_MAX_MEMORY_SIZE=None`, the package therefore performs an unbounded
allocation before enforcing its smaller GraphQL limit. The async package view performs the same
synchronous disk read on the event loop, adding event-loop starvation to the memory-amplification
path.

The existing ASGI tests prove status, cumulative fragment accounting, and no GraphQL parse or
schema execution. Their payloads cross the limit by only a few bytes, so they do not prove the
security property that the rejecting operation itself is bounded. The build notes repeatedly
describe the package check as the floor's “only application-level bound,” but detection after an
unbounded allocation is not a memory bound.

### Required root-cause correction

The package must inspect or consume the request stream without first asking Django to materialize
the whole body:

1. Keep the declared-over-limit early refusal.
2. When the body has already been cached by earlier middleware, compare `len(request._body)`; the
   allocation has already happened and cannot be undone, but the package must still refuse it.
3. For a seekable ASGI spool, inspect its actual size with `seek`/`tell`, restore the original
   position, and reject before `request.body` is evaluated.
4. For a genuinely non-seekable stream, read in bounded chunks only up to `limit + 1`. If the body
   is allowed, preserve those bytes in the request shape Django expects so Strawberry can read
   them normally; if it is over the limit, stop and reject without concatenating the remainder.
5. Keep multipart on its deliberately separate streaming/declaration contract.

The implementation must centralize the private-Django interaction in one compatibility helper and
pin its behavior on both Django 5.2.0/Python 3.10 and the current stack. Do not spread `_stream`,
`_body`, and `_read_started` manipulation across the view classes.

Required regressions:

- a seekable ASGI stream much larger than the GraphQL cap whose unbounded `read()` raises if
  called;
- absent and understated `Content-Length`;
- an over-limit body proving no allocation/read larger than `limit + 1`;
- an under-limit control proving Strawberry receives the original bytes unchanged;
- middleware-prepopulated `request._body`;
- sync and async package views; and
- the exact Django 5.2.0/Python 3.10 floor.

## High 2 — a package security policy is disabled by the unrelated upstream-patch kill switch

[`_patched_parse_json`][strawberry-patches] implements two different categories of behavior:

- compatibility fixes for upstream malformed-body bugs; and
- the package-authored strict UTF-8 wire policy from S9.

Yet both remain governed by `APPLY_UPSTREAM_PATCHES`. Setting that broad switch to `False`, or
disabling only its `"strawberry"` member, restores UTF-16/32 acceptance. The spec explicitly
documents that consequence, so this is not an implementation/spec mismatch; it is an
architectural problem in the contract itself.

The strict wire policy is not an upstream patch and does not share the patch's lifecycle. The
module correctly says it must survive after the upstream bugs retire, but the runtime ownership
still says the opposite: a consumer disabling temporary monkeypatches also disables a permanent
security policy. This creates two predictable regressions:

- an upstream shape change can force a consumer to disable the patch and silently reopen the
  parser differential; and
- when the compatibility patches are retired, moving or deleting their gated installer can
  accidentally retire the policy with them.

### Required root-cause correction

Move strict UTF-8 decoding onto a package-owned HTTP-view parsing boundary, shared by
`DjangoGraphQLView` and `AsyncDjangoGraphQLView`, and leave `APPLY_UPSTREAM_PATCHES` responsible
only for upstream bug workarounds. A single private view mixin/helper can keep the policy DRY
without globally reimplementing Strawberry's parser: decode byte input strictly, then delegate
to upstream parsing.

Consumers mounting an upstream view directly may retain upstream semantics; consumers choosing
the package's secure view must not lose a package security contract because they disabled an
unrelated compatibility patch.

Add a regression that mounts the package view with
`APPLY_UPSTREAM_PATCHES={"strawberry": False}` and still rejects UTF-16/32 and a UTF-8 BOM. Keep
separate tests proving that the actual upstream bug workarounds do respect their opt-out.

## High 3 — the consumer factory contract accepts a non-ASGI result

[`_websocket_application`][routers] validates that a factory candidate is callable, invokes it as
`factory(schema=schema)`, and returns its result without validation:

```python
elif callable(candidate):
    return candidate(schema=schema)
```

A factory returning `None`, an integer, a coroutine object, or any other non-callable value is
therefore accepted at router construction. The invalid object is installed as a URL route
callback, and the first matching handshake fails later inside routing rather than producing the
documented `ConfigurationError`.

A narrow probe currently returns `None` successfully from `_websocket_application`, confirming
that this is a live branch rather than a theoretical typing concern.

Validate the factory's return value before mounting it. The resulting `ConfigurationError` should
name both the factory and the received result type/value, while preserving the original exception
as `__cause__` if factory invocation itself fails in a way the package chooses to normalize.

Required regressions:

- factory returns `None`;
- factory returns a non-callable scalar;
- `async def factory(...)` returns a coroutine instead of an ASGI callable;
- valid synchronous factory returns an async ASGI callable; and
- the two Origin/auth wrappers remain outside the validated result.

## Medium 4 — the revalidation helper breaks the auth subsystem's opt-in import boundary

[`consumers.py::_refreshed_actor`][consumers] imports:

```python
from .auth.sessions import session_store_class
```

Importing a Python submodule first executes its package's `__init__.py`.
[`django_strawberry_framework.auth.__init__`][auth-init] eagerly imports `auth.mutations` and
`auth.queries`, which in turn load the generated-mutation, registry, permissions, and Strawberry
type machinery. Consequently, the first authenticated WebSocket operation in a process that has
not opted into the GraphQL auth fields imports and registers the entire opt-in auth subsystem on
the event loop merely to resolve a session-store class.

The current tests mask this cold path by importing
`django_strawberry_framework.auth.sessions` at test-module collection time. The production module
docstring's claim that the revalidation reaches only the session-store resolver is therefore not
true at the Python import boundary.

This is avoidable without duplicating the `SESSION_ENGINE` expression. Move the generic
session-store-class resolver to a cycle-neutral private module—outside the eager `auth` package—and
have both `auth/sessions.py` and `consumers.py` import it. Preserve `auth` as structurally opt-in.

Add a fresh-process or strict module-eviction regression proving that resolving the store for
WebSocket revalidation does not add `django_strawberry_framework.auth.mutations` or
`django_strawberry_framework.auth.queries` to `sys.modules`.

## Medium 5 — the revocation acceptance row does not reproduce the promised separate-request flow

The S11 test plan requires establishing a socket, revoking/flushing/disabling through a
**separate request**, and proving the next operation is denied without reconnecting.
[`test_a_revoked_session_is_denied_on_the_next_operation_without_reconnecting`][test-routers]
does prove the last and most important half, but its “separate request” is represented by direct
ORM/session-store mutation:

- `SessionStore(session_key).flush()`;
- `user.is_active = False; user.save()`; and
- `user.set_password(...); user.save()`.

Those are useful package-tier controls, but they do not prove that a real second HTTP request's
session lifecycle invalidates the cookie/session shape held by the already-open socket. In
particular, a future change in the logout view, cookie handling, session-key rotation, or session
backend integration could break the real revocation path while these tests remain green.

Keep the direct mutators as precise unit controls, and add at least one real secondary HTTP
logout/session-flush round trip while the communicator remains open. The test does not require a
fakeshop `asgi.py`: the socket can stay package-tier while an `AsyncClient` or a
`database_sync_to_async`-wrapped Django client performs the second request against a probe
URLconf. Assert that it targets the same session key/cookie, then deny operation two on the
original communicator.

## Lower-severity configuration and reconciliation gaps

### An enormous integer window escapes the typed configuration boundary

[`resolved_revalidation_window`][consumers] calls `math.isfinite(value)` before converting the
accepted number to `float`. A sufficiently large Python integer raises `OverflowError` inside
`math.isfinite`; it does not become the promised `ConfigurationError`. A narrow probe with
`10**10000` reproduces the raw exception.

Perform the conversion in a guarded step, reject `OverflowError` alongside the existing invalid
domain, then run `math.isfinite` on the converted float. Add the huge-positive-integer row to the
unusable-value matrix.

### The explicit-zero injection rule remains contradictory

The spec's edge-case prose says injecting a consumer class and passing a revalidation window is a
construction error because the knob is meaningless, and test-plan row 29 says the same. The
implementation rejects only a **positive** window and deliberately accepts an explicitly passed
`0.0`.

The implementation's behavior is reasonable—the public default is already `0.0`, so an explicit
zero has no additional effect—but the spec must say “positive window” everywhere if that is the
contract. Otherwise the API would need a private omitted-value sentinel to distinguish omission
from an explicit zero. Reconcile the spec and tests rather than leaving the exception only in a
source comment.

### The multi-database claim overstates what the implementation pins

The spec says revalidation is pinned to “the operation's own resolved alias.” The implementation
delegates to the configured session engine and `channels.auth.get_user`; those components perform
ordinary Django router selection, but no operation alias is captured or passed.

Delegating to Django's routers is probably the correct architecture, and reimplementing
`get_user` to force an alias would be worse. The contract should therefore say that session and
user reads honor their models' normal Django database-router decisions. If a stronger
same-operation-alias guarantee is intended, the current code and tests do not implement it.

## What is satisfactorily closed

- HTTP is a direct handoff to the consumer-supplied Django ASGI application; the package does not
  rebuild Django middleware.
- `GraphQLHTTPConsumer` has left the router composition.
- `django_application` is required and the explicit invalid-value error is actionable.
- HTTP and WebSocket URL ownership are separated, and the default WebSocket regex is exact.
- The package view keeps the upstream `as_view` surface rather than forking Strawberry's HTTP
  engine.
- Host validation, CSRF, security headers, cache variation, IDE/GET controls, and URL routing are
  exercised through fakeshop's live Django endpoint.
- Declared-over-limit bodies are refused before body access.
- Multipart is not accidentally materialized by the package cap.
- Sync and async views share one cap implementation.
- UTF-8/BOM behavior is explicitly tested across sync and async transports.
- Both WebSocket subprotocols revalidate at their actual per-operation hooks.
- The default revalidation window is secure (`0.0`), positive windows are explicit, invalid
  sessions fail closed, and a failure does not silently downgrade the socket to anonymous.
- Injected consumers remain structurally inside `AllowedHostsOriginValidator` and
  `AuthMiddlewareStack`.

## Recommended correction order

1. Replace the unbounded `request.body` count with a bounded/size-probed implementation and repeat
   the Django 5.2.0/Python 3.10 floor gate.
2. Separate the permanent UTF-8 policy from `APPLY_UPSTREAM_PATCHES`.
3. Validate the injected factory's returned ASGI application.
4. Move session-store resolution outside the eager opt-in auth package.
5. Add the real secondary-request revocation acceptance row.
6. Close the numeric and spec-reconciliation gaps.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md

<!-- docs/ -->
[spec-065]: spec-065-transport_security-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-065]: builder/build-065-transport_security-0_0_15.md

<!-- django_strawberry_framework/ -->
[auth-init]: ../django_strawberry_framework/auth/__init__.py
[consumers]: ../django_strawberry_framework/consumers.py
[routers]: ../django_strawberry_framework/routers.py
[strawberry-patches]: ../django_strawberry_framework/_strawberry_patches.py
[views]: ../django_strawberry_framework/views.py

<!-- tests/ -->
[test-routers]: ../tests/test_routers.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
