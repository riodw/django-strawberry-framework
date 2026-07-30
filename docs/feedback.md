# Fresh adversarial implementation review: transport security

## Scope and verdict

This review is against the current working tree for [spec 065][spec-065], not the
implementation state from the previous feedback pass. I read every dirty file:

- the active [spec][spec-065];
- the concurrent documentation-only edit in [`views.py`][views];
- the broader DRY inventory in [`drys.md`][drys]; and
- the broader security inventory in [`vulns.md`][vulns].

I then reread the related production paths, package tests, live fakeshop transport tests,
the active [build plan][build-065], Django's multipart/CSRF implementation, Channels'
Origin validator, and Strawberry's two WebSocket protocol handlers. Slice 5 is still
unbuilt in the plan, so its planned documentation fold-in is not treated as a missing
implementation. Likewise, unchecked future work in [`vulns.md`][vulns] is not charged to this
card.

The earlier review's body-allocation, patch-lifecycle, consumer-factory, auth-import,
real-logout, huge-window, explicit-zero, and database-router findings are now materially
fixed. The bounded-body helper is a substantial improvement and the router remains a
good direct handoff to Django for HTTP.

The implementation is still not ready to close. The strongest S11 security statement is
false for an already-running subscription, and the multipart path sits outside both the
strict UTF-8 boundary and the claimed pre-parse declared-size boundary. Those are
architectural gaps, not test wording.

No pytest invocation was run, per [AGENTS.md][agents]. The findings below come from source
inspection and narrow read-only runtime probes against the installed project environment.

## Blocker 1 — revocation does not stop an already-running subscription

[`build_revalidating_consumer_class`][consumers] overrides only the two operation-admission
methods:

- `handle_subscribe` for `graphql-transport-ws`; and
- `handle_start` for legacy `graphql-ws`.

That revalidates before Strawberry starts an operation. It does **not** revalidate an
operation again.

The distinction is security-critical for subscriptions. In Strawberry's installed
[`BaseGraphQLTransportWSHandler.run_operation`][transport-handler], the admission method
creates one task and that task iterates `async for result in result_source`, sending every
later result without returning through `handle_subscribe`. The legacy handler does the
same in [`BaseGraphQLWSHandler.handle_async_results`][legacy-handler]. A subscription may
remain in either loop for hours.

Consequently, this sequence is currently possible:

1. authenticate and open a socket;
2. start a multi-yield subscription while the session is valid;
3. receive its first result;
4. log out, flush the session, disable the user, or rotate the password through another
   request; and
5. continue receiving later results from the already-admitted subscription.

This contradicts the production claim in
[`django_strawberry_framework/consumers.py::GraphQLWebSocketConsumer`][consumers] that “a
revoked session stops executing” and makes maximum connection/operation lifetime
security-relevant again. It also means a long-lived subscription can keep evaluating
resolvers against the connect-time actor after revocation.

The current acceptance tests cannot detect this.
[`tests/test_routers.py::Subscription.tick`][test-routers] yields exactly once, and every
revocation row lets operation 1 finish before it revokes the session and submits operation
2. Those tests prove **new-operation admission** only.

### Required root-cause correction

The spec must distinguish operation admission from the lifetime of an admitted operation,
then implement the stronger contract it currently claims. At minimum, no subscription
payload may be emitted after its actor becomes invalid, and the active operation must be
cancelled/completed rather than silently continuing.

Do not copy either upstream protocol loop. Find one small package-owned lifecycle seam
shared by the two protocols—for example, a result-send guard plus operation cancellation,
or a protocol-neutral revocation monitor attached to active operation tasks. If the
contract is that resolver work itself must stop rather than merely preventing disclosure
of the result, a send-time check alone is insufficient: the design needs to cancel before
the next event is evaluated. This deserves a spec decision before more code because
`websocket_revalidation_window` must also define its meaning for active subscriptions.

Required regression, for **both** protocols:

1. use a controlled multi-yield async subscription;
2. receive result 1;
3. revoke through the existing real second HTTP request while the operation remains open;
4. release result 2's event;
5. prove result 2 is never delivered and the operation is completed/cancelled; and
6. include a valid-session control that receives both results.

## High 2 — multipart `operations` and `map` bypass the strict UTF-8 wire contract

[`django_strawberry_framework/views.py::_RequestBodyBoundaryMixin.parse_json`][views]
strictly decodes `bytes`, but deliberately passes `str` through untouched. That is correct
for GET query parameters; it is not sufficient to establish a wire-encoding contract for
multipart.

Strawberry obtains multipart `operations` and `map` from `request.POST`. Before the package
sees either value, Django's [`MultiPartParser._parse`][django-multipart] converts field
bytes through `force_str(..., encoding, errors="replace")`. The original bytes and any
decoding failure are therefore gone. The package receives a `str` regardless of whether
the wire contained UTF-8, Latin-1, or malformed UTF-8.

Two live probes against the package view confirmed the bypass:

- an `operations` field declared with `charset=iso-8859-1` and carrying a raw Latin-1
  byte executed successfully with HTTP `200`; and
- an `operations` field with no charset and a malformed UTF-8 byte (`0x80`) was
  replacement-decoded by Django and also executed successfully with HTTP `200`.

The latter is the clearest contradiction: a byte sequence the package calls invalid UTF-8
is accepted on one GraphQL-over-HTTP body shape. The statement “request JSON is UTF-8-only”
is therefore true only for the ordinary JSON body, not for all JSON control documents the
endpoint parses.

### Required root-cause correction

Choose and document one honest multipart contract before implementing it:

- **Strongest practical contract:** require multipart `operations` and `map` to use an
  ASCII JSON serialization after Django decoding. JSON escapes preserve arbitrary Unicode,
  so clients can send `caf\u00e9` without loss. Reject non-ASCII control-field text and
  `U+FFFD`. This is enforceable at the shared sync/async form-data adapter without copying
  Django's multipart parser, but it is intentionally narrower than “raw UTF-8.”
- **Full raw UTF-8 contract:** introduce a raw-preserving, streaming validation seam before
  Django replacement-decodes the fields. Django exposes no narrow strict-field-decoding
  hook, so this is materially heavier and must not be implemented by copying
  `MultiPartParser._parse`.
- **Narrower product contract:** explicitly scope strict UTF-8 to
  `application/json` and acknowledge that multipart control fields inherit Django's
  replacement-decoding semantics. This is accurate but weakens the current security
  promise.

Whichever direction is chosen, add real multipart requests for malformed UTF-8 with no
charset, explicit Latin-1, escaped Unicode, and the chosen treatment of genuine multibyte
UTF-8. Exercise both package views; a direct `parse_json(str)` unit test cannot prove this
wire boundary.

## High 3 — the multipart declared cap runs after CSRF has already parsed the body

The package calls
[`django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_request_body_limit`][views]
from the view's `run`. In a real Django request,
[`django.middleware.csrf.CsrfViewMiddleware._check_token`][django-csrf] runs earlier in
`process_view`. For every cookie-bearing POST it first reads
`request.POST.get("csrfmiddlewaretoken", "")`, even when the request will ultimately use
the `X-CSRFToken` header.

On multipart requests that access invokes Django's multipart parser and upload handlers
**before the package view can inspect the declared length**. The package may still return
`413`, but it did not reject before multipart parsing/spooling.

The live test
[`examples/fakeshop/test_query/test_transport_api.py::test_a_multipart_request_over_the_declared_cap_is_refused`][transport-tests]
does not expose the ordering. It uses plain `Client()`, whose CSRF checks are disabled, so
the middleware exits before `_check_token` reads `request.POST`. The test proves only the
view-local branch.

This does not mean the new bounded non-multipart helper is wrong. It means the multipart
claim is too strong for a view-level boundary. ASGI has already received/spooled the raw
body in either case, but CSRF can additionally parse fields and invoke file upload handlers
before the package's “declared gate.”

### Required root-cause correction

If “reject before Django parses multipart” remains a requirement, the check must run in a
narrow package middleware placed before `CsrfViewMiddleware`, with a system check that
detects missing or incorrect ordering. Its `process_view` can identify package view mounts
and read the per-mount cap without rebuilding Django's HTTP stack.

If that extra deployment surface is not justified, narrow the contract instead: the view
cap prevents Strawberry parsing and schema execution, while proxy/server limits, Django's
upload settings, and upload handlers own multipart resource consumption. Do not keep
claiming that the package's declared gate itself prevents multipart parsing.

The regression must use `Client(enforce_csrf_checks=True)`, a valid CSRF cookie and header,
an over-package-limit multipart body, and an upload-handler or parser sentinel. Status
`413` alone is not evidence of ordering.

## Medium 4 — `AllowedHostsOriginValidator` does not validate the WebSocket `Host`

The router and spec repeatedly promise that an injected consumer cannot escape
“Host/Origin validation.” Channels' `AllowedHostsOriginValidator` name is misleading here:
it is a factory for `OriginValidator(settings.ALLOWED_HOSTS)`.
[`channels.security.websocket.OriginValidator.__call__`][channels-security] reads only the
`Origin` header. It never reads or validates `Host`.

A direct communicator probe with `Origin: http://localhost` and
`Host: evil.example` connected successfully: `(True, None)`. The current router tests cover
allowed, rejected, and missing `Origin`; none supplies an allowed Origin with a hostile
Host.

The least surprising correction is to narrow every claim to **Origin validation**. That is
the upstream wrapper the router intentionally composes, while Django still owns Host
validation on HTTP. If WebSocket Host validation is an intentional package guarantee, add a
separate small validator using Django's host utilities and pin the hostile-Host/allowed-
Origin direction. Do not rely on the upstream class name as evidence of behavior.

## Medium 5 — the broken-Strawberry install hint advertises an unsupported floor

The hard dependency and minimum CI node now correctly pin
`strawberry-graphql>=0.316.0`. However,
[`django_strawberry_framework/routers.py::_STRAWBERRY_CHANNELS_BROKEN_HINT`][routers] still
tells a consumer that `>=0.262.0` is sufficient, and [`tests/test_routers.py`][test-routers]
deliberately pins that stale text.

This is a user-facing recovery path: following the error's advice can install a version the
package metadata rejects and that CI no longer supports. Update the hint and its test to
`0.316.0`, then reconcile the historical 0.262.0 language in [spec 041][spec-041] during
Slice 5. There is no new Python 3.10 problem here—the current dependency floor and minimum
CI node already agree on Strawberry 0.316.0.

## Low 6 — unusual stream capability failures escape the body boundary as raw errors

[`django_strawberry_framework/_request_body.py::_measured_remaining`][request-body] catches
failures from `tell()`, but it calls `seekable()`, both `seek()` operations, and
`end - position` unguarded. A middleware- or server-supplied stream whose capability method
raises can therefore turn a request into an unrelated `500`; a failed restore may also
leave the body position corrupted.

The production Django streams are well behaved, so this is not a current cap bypass. It is
still an avoidable fragility at the one private compatibility seam the design explicitly
centralized. Model the probe outcome explicitly:

- measurable;
- safely unmeasurable with the original position intact, so bounded read may run; or
- position potentially corrupted, so fail closed with the package's controlled rejection.

Add stand-ins whose `seekable`, seek-to-end, subtraction result, and restore each fail.
Never fall through to a bounded read after a failed restore unless the original position is
known to be intact.

## What the current pass satisfactorily closed

- Non-multipart over-limit bodies are measured without an unbounded
  `request.body` allocation, including the Django 5.2/Python 3.10 ASGI spool shape.
- The strict decode is package-view policy and remains active when upstream patches are
  disabled; the sync adapter now supplies raw bytes through an upstream extension seam.
- Factory results are validated before mounting, including coroutine cleanup and safe value
  rendering.
- WebSocket session-store resolution no longer imports the opt-in auth subsystem.
- A real second HTTP logout request now invalidates a still-open socket before a **new**
  operation.
- Huge integers fail through `ConfigurationError`; explicit zero and database-router
  language are reconciled.
- The router continues to hand HTTP directly to the consumer's Django ASGI application,
  preserving Django's middleware, URLconf, CSRF, cache, and security-header behavior.

## Recommended correction order

1. Resolve the active-subscription revocation contract and lifecycle seam.
2. Choose the multipart control-field encoding contract.
3. Decide whether the multipart cap is an early-middleware guarantee or a view/schema
   boundary, then make the claim and acceptance test honest.
4. Reconcile Origin-versus-Host language (or add the missing validator).
5. Correct the Strawberry floor and harden the stream probe.
6. Finish Slice 5's planned prose/integration sweep only after the behavior above is stable.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[agents]: ../AGENTS.md
[drys]: ../drys.md
[vulns]: ../vulns.md

<!-- docs/ -->

[spec-065]: spec-065-transport_security-0_0_15.md

<!-- docs/SPECS/ -->

[spec-041]: SPECS/spec-041-channels_router-0_0_14.md

<!-- docs/builder/ -->

[build-065]: builder/build-065-transport_security-0_0_15.md

<!-- django_strawberry_framework/ -->

[consumers]: ../django_strawberry_framework/consumers.py
[request-body]: ../django_strawberry_framework/_request_body.py
[routers]: ../django_strawberry_framework/routers.py
[views]: ../django_strawberry_framework/views.py

<!-- tests/ -->

[test-routers]: ../tests/test_routers.py

<!-- examples/ -->

[transport-tests]: ../examples/fakeshop/test_query/test_transport_api.py

<!-- scripts/ -->

<!-- .venv/ -->

[channels-security]: ../.venv/lib/python3.14/site-packages/channels/security/websocket.py
[django-csrf]: ../.venv/lib/python3.14/site-packages/django/middleware/csrf.py
[django-multipart]: ../.venv/lib/python3.14/site-packages/django/http/multipartparser.py
[legacy-handler]: ../.venv/lib/python3.14/site-packages/strawberry/subscriptions/protocols/graphql_ws/handlers.py
[transport-handler]: ../.venv/lib/python3.14/site-packages/strawberry/subscriptions/protocols/graphql_transport_ws/handlers.py

<!-- External -->
