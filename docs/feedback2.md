# Security hardening audit

Audit date: 2026-07-24.

## Scope and threat model

This is a security-focused review of the current package, the fakeshop integration, the
test/deployment guidance, dependency governance, and CI. It is intentionally broader than
the row-preserving-predicate work. The findings in [`docs/feedback.md`][feedback] still
govern that feature's correctness review; this document does not duplicate or supersede
them.

The primary threat model is:

- an unauthenticated internet client sending arbitrary GraphQL documents, variables,
  headers, bodies, and WebSocket operations;
- an authenticated client using a cookie-backed Django session;
- a deployment behind a reverse proxy or shared cache;
- a trusted application developer who can misconfigure a powerful opt-in surface by
  accident; and
- untrusted pull-request contents executing in CI.

Consumer-written resolvers, permission backends, storage backends, and hooks are trusted
application code. The audit does not pretend the framework can sandbox deliberately
malicious Python code. The fakeshop is also correctly advertised as a development example,
not a production deployment in the [root README][readme]. Its unsafe development settings
are therefore documentation and test-fixture risks, not package vulnerabilities by
themselves.

The review used source inspection plus focused, non-pytest probes. Per repository policy,
the full test suite was not run. This is not a substitute for a dedicated dependency
scanner, dynamic application scan, or external penetration test.

## Executive verdict

The ORM authorization and write-integrity boundaries are unusually strong. Generated
model writes deny by default, row visibility is applied to read/refetch/update/delete
paths, relation inputs are visibility-checked, mutation transactions include GraphQL
completion, keyset cursors are authenticated, and the custom SQL paths quote identifiers
and bind values. Those are meaningful security strengths.

The package is nevertheless not ready for an internet-facing production claim. The
highest risks sit outside the row-preserving rewrite:

| ID | Severity | Finding | Required disposition |
|---|---|---|---|
| S1 | Blocker | Channels HTTP bypasses Django's HTTP security middleware | Redesign the router boundary |
| S2 | Blocker | Channels HTTP buffers an unbounded body in process memory | Enforce a real transport limit |
| S3 | High | Query and response work have no coherent resource budget | Add one central execution policy |
| S4 | High | Variable-driven input cardinality is unbounded | Extend the same policy to values |
| S5 | High | Generated file output exposes absolute server paths | Remove from the safe default |
| S6 | High | The checked-in Django resolutions are security-stale | Patch the lock and automate auditing |
| S7 | Medium | The CI test job has unnecessary repository write authority | Apply least privilege and immutable pins |
| S8 | Medium | The debug extension does not fail closed under `DEBUG=False` | Require an explicit unsafe-production acknowledgement |
| S9 | Medium | The request parser accepts UTF-16/32 network JSON | Enforce one UTF-8 wire contract |
| S10 | Medium | Production exception masking remains opt-in | Give `DjangoSchema` a safe production profile |
| S11 | Medium | Long-lived WebSockets retain a stale session actor | Revalidate per operation or bound connection life |
| S12 | Low/docs | Relay IDs, uploads, and fakeshop posture need a consolidated deployment contract | Add explicit security guidance and acceptance tests |

S1 and S2 should block any move from the current “not production” alpha posture. S3-S6
should block a production-readiness milestone even if consumers can currently compensate
with their own middleware and deployment controls. A framework's secure architecture
cannot depend on every consumer independently discovering these gaps.

## S1 — Blocker: Channels HTTP bypasses Django's security middleware

### Evidence

[`django_strawberry_framework/routers.py::_build_router_class`][routers] builds the HTTP
branch as:

```python
AuthMiddlewareStack(
    URLRouter(
        [re_path(url_pattern, GraphQLHTTPConsumer.as_asgi(schema=schema)), ...],
    ),
)
```

`AuthMiddlewareStack` supplies cookies, sessions, and `scope["user"]`; it is not Django's
ASGI request handler and does not execute the project's `MIDDLEWARE`. The GraphQL HTTP
route therefore bypasses, among other things:

- `SecurityMiddleware`;
- `CsrfViewMiddleware`;
- `CommonMiddleware` and the normal `ALLOWED_HOSTS` request boundary;
- `AuthenticationMiddleware`'s normal `HttpRequest` lifecycle;
- consumer tenant, rate-limit, audit, cache, and security-header middleware; and
- middleware-managed `Vary`, cache-control, HSTS, MIME-sniffing, referrer-policy, and
  clickjacking headers.

This is especially dangerous because the same branch deliberately accepts the session
cookie and turns it into an authenticated actor. The authenticated session round trip is
already proven by
[`tests/test_routers.py::test_authenticated_session_round_trip_reaches_the_resolver`][test-routers].
The package documentation simultaneously states that Channels GraphQL consumers do not
enforce CSRF in [`docs/README.md #"Channels GraphQL consumers do not enforce CSRF"`][docs-readme].

A focused request probe against the current router produced:

```text
POST /graphql       Host: evil.example  Origin: https://evil.example  -> 200
POST /graphql-admin Host: evil.example  Origin: https://evil.example  -> 200
response headers -> content-type only
```

The second result is a separate routing defect. The default `url_pattern="^graphql"` is a
prefix regex, so `/graphql-admin`, `/graphqlanything`, and similar paths are claimed by
the GraphQL consumer before the Django fallback. A deployment can therefore believe a
Django URL and its middleware policy own a path that the router actually intercepts.

The bare consumer also defaults to GraphiQL enabled and queries over GET enabled. The
router exposes no constructor controls for the IDE, GET behavior, multipart behavior,
HTTP consumer class, or WebSocket consumer class. Authenticated GET results carry no
`Vary: Cookie` or private/no-store policy, creating a cross-user disclosure risk when a
consumer or intermediary enables caching.

This audit is not claiming that a stock hostile website can always perform a one-click
CSRF mutation today. JSON POSTs normally trigger a CORS preflight, the current Channels
consumer has multipart disabled, GET mutations are rejected, and modern session cookies
add SameSite protection. Those are contingent mitigations, not a sound framework
boundary. Credentialed CORS, same-site sibling origins, a future multipart switch, or a
custom consumer can remove them. The concrete defects—middleware bypass, Host bypass,
missing response policy, and route overmatch—exist without that stronger claim.

### Required root correction

Do not reproduce a partial Django security stack around a bare Channels HTTP consumer.
Route HTTP through the consumer's Django ASGI application and reserve the Channels
consumer for WebSockets:

```text
ProtocolTypeRouter
├── http      -> get_asgi_application() -> Django URLconf -> GraphQL Django view
└── websocket -> exact GraphQL route -> origin/auth middleware -> GraphQL WS consumer
```

The HTTP GraphQL endpoint then has one authoritative home in the Django URLconf and gets
the same middleware as the rest of the application. The router should require or clearly
derive the Django ASGI application instead of making the security-preserving branch an
optional fallback.

If a direct Channels HTTP mode must remain, it should be explicitly named as a separate,
advanced transport and implement a package-owned, tested equivalent boundary: exact route
matching, Host validation, cookie-auth CSRF, cache variation, body limits, response
security headers, IDE/GET controls, and consumer-class injection. That is materially more
code and more drift risk than using Django's existing boundary, so it is not the preferred
architecture.

### Required regressions

- A hostile `Host` is rejected on GraphQL HTTP, not only WebSocket.
- Cookie-authenticated mutations cover missing, wrong, and correct CSRF tokens.
- An authenticated GET response is non-cacheable or varies on `Cookie`.
- Security middleware's configured headers appear on GraphQL HTTP responses.
- `/graphql` and `/graphql/` match according to an explicit policy, while
  `/graphql-admin` and `/graphqlanything` reach Django or 404.
- `graphql_ide=None` and `allow_queries_via_get=False` are supported and proven.
- A project middleware sentinel executes on the GraphQL HTTP route.
- The existing WebSocket Host/Origin direction tests remain intact.

## S2 — Blocker: Channels HTTP buffers an unbounded body in process memory

### Evidence

The routed Strawberry HTTP consumer inherits
`channels.generic.http.AsyncHttpConsumer`. Its installed
`AsyncHttpConsumer.http_request` appends every ASGI body fragment to a Python list and
then calls `b"".join(self.body)` before Strawberry sees the request. There is no
application-level maximum in the package router, and Django's
`DATA_UPLOAD_MAX_MEMORY_SIZE` is never consulted because the request bypasses Django's
ASGI handler.

This gives an unauthenticated client a direct memory-amplification path. The body need not
be valid JSON and need not declare an honest `Content-Length`; allocation occurs before
GraphQL parsing or schema execution. Daphne's request buffer size controls fragment
delivery, not the total accepted body. Another ASGI server or proxy may impose its own
limit, but that is not a package guarantee.

### Required root correction

S1's Django-HTTP redesign removes the worst all-in-memory implementation, but it does not
eliminate the need for a total request-size policy. Django itself recommends a web-server
body cap for uploads because ASGI requests can be spooled before application validation
in its [security guidance][django-security].

Enforce the same explicit maximum at two layers:

1. Document and test a reverse-proxy/ASGI-server hard cap.
2. Enforce an actual cumulative-byte cap in the application path before parsing or schema
   execution.

The application check must count received bytes, not trust `Content-Length`. A declared
over-limit request may reject immediately; an absent or lying header must reject as soon
as cumulative bytes cross the limit. Multipart file count, individual file size, and
aggregate file size need their own limits in S4.

### Required regressions

- no `Content-Length`;
- declared size below, at, and above the limit;
- a declared small length whose streamed body exceeds the limit;
- multiple ASGI fragments crossing the boundary;
- JSON, malformed JSON, and multipart bodies;
- an early `413` with proof that neither JSON parsing nor schema execution ran; and
- parity across the supported Python 3.10 / Django 5.2.0 compatibility floor and the
  current supported stack.

## S3 — High: query and response work have no coherent resource budget

### Evidence

The fakeshop schema in
[`examples/fakeshop/config/schema.py #"schema = DjangoSchema"`][fakeshop-schema] installs
the optimizer only. Neither the package nor the example installs Strawberry's token or
query-depth limiters, and there is no package-level selection-count, complexity, timeout,
or aggregate-row budget.

Pagination is not a complete defense:

- `DjangoConnectionField` respects `relay_max_results`;
- [`django_strawberry_framework/list_field.py::DjangoListField`][list-field] evaluates an
  unrestricted queryset;
- [`django_strawberry_framework/types/base.py #"DEFAULT_RELATION_SHAPE = \"both\""`][type-base]
  exposes a raw many-side list alongside the bounded connection by default; and
- a client can therefore bypass the connection cap by selecting the list sibling.

A generated-SDL probe confirmed the current fakeshop schema contains both raw many-side
lists and connection siblings, as well as three separate root
`DjangoListField` example surfaces. Deep aliases and fragments can multiply those
unbounded collections. The optimizer reduces query count; it does not bound database
work, serialized rows, Python memory, or response bytes. A deeply nested document can
also drive recursive GraphQL and optimizer walkers toward the Python recursion limit.

### Required root correction

Introduce one immutable resource-policy object consumed by `DjangoSchema`, collection
fields, the optimizer, and the transports. It should own at least:

- maximum document tokens;
- maximum selection/alias count after fragment expansion;
- maximum depth;
- maximum page size;
- maximum raw-list rows;
- maximum aggregate collection cost across a request; and
- optional execution deadline/cancellation integration.

Do not scatter unrelated settings reads across resolvers. Normalize and validate the
policy once at schema construction, then pass the immutable result through request
context. Per-field overrides may only narrow the schema policy unless an explicit trusted
schema declaration widens it.

For Relay-shaped types, change the secure default for many-side relations from `"both"`
to `"connection"`. A raw list should require explicit opt-in and an enforced maximum.
`DjangoListField` likewise needs a required/effective bound; merely documenting it as
dangerous leaves an easy production footgun.

### Required regressions

- token, expanded-selection, alias, depth, and aggregate-cost boundaries;
- fragments and directives cannot evade accounting;
- the same expensive field selected under many aliases is charged many times;
- a connection's `relay_max_results` cannot be bypassed through a generated list sibling;
- raw root and relation lists stop at the configured maximum;
- rejection occurs before ORM access where possible; and
- sync HTTP, async HTTP, and WebSocket operations receive the same typed error code.

## S4 — High: variable-driven input cardinality is unbounded

### Evidence

Document limits do not constrain values supplied through variables. A tiny GraphQL
document can currently carry:

- an unlimited `ids:` list through
  [`django_strawberry_framework/relay.py::DjangoNodesField`][relay];
- unlimited `in` lookup values, including `GlobalIDMultipleChoiceFilter`;
- an `and`/`or` filter tree whose depth is capped but whose width and total node count are
  not;
- unlimited M2M IDs in generated model, form, and serializer mutations;
- wide nested serializer lists; and
- multipart uploads without a package-owned aggregate byte, file-count, or per-file cap.

`DjangoNodesField` preserves duplicates positionally. The database may deduplicate an
`IN` predicate, but the framework still decodes, stores, reassembles, and serializes every
position. Similar large inputs can exceed database parameter limits, create very large
SQL statements, hold write locks for excessive periods, or consume memory before the ORM
is reached.

### Required root correction

Extend S3's resource policy with a single iterative value-budget walker. It should charge:

- total input nodes;
- maximum container width;
- membership-list items;
- node-refetch IDs;
- relation IDs per mutation and in aggregate;
- nested serializer rows;
- upload count, per-file bytes, and aggregate bytes; and
- string/scalar byte size where a parser or validator has nonlinear behavior.

The walker must be iterative and cycle-safe, continue to support Python 3.10, and stop
before decoding IDs or touching the ORM once the budget is exhausted. The transport body
cap in S2 remains necessary because the JSON body is allocated and parsed before
GraphQL-coerced values exist.

### Required regressions

Each input family needs under/at/over-boundary tests, including a very small query with a
large variable payload. Also cover duplicate IDs, empty lists, multiple simultaneous
bounded fields whose aggregate exceeds the request budget, sync/async parity, and proof
of zero ORM work after rejection.

## S5 — High: generated file output exposes absolute server paths

### Evidence

[`django_strawberry_framework/types/converters.py::DjangoFileType.path`][converters]
returns `FieldFile.path`, and its public description explicitly calls this “the absolute
filesystem path.” `DjangoImageType` inherits it. Every generated file/image output
therefore offers clients a server-internal path whenever the storage backend supports
one.

Row visibility still controls which file-bearing object a client can reach, but an
absolute deployment path is unnecessary sensitive metadata. It can reveal usernames,
release directories, container mounts, tenant layout, storage conventions, and material
useful for chaining a later traversal, template, or logging defect. A focused SDL probe
found four `path: String` occurrences in the current fakeshop schema.

The stored `name` can also expose storage keys, so its sensitivity should be documented,
but it is often application data and does not justify the same unconditional removal.

### Required root correction

Remove `path` from the public generated type's safe default. The default output should be
limited to fields intended for remote clients, such as `name`, `size`, and `url`.

If a real consumer needs a filesystem path, require an explicit, server-owned field or an
explicit `Meta` opt-in with a loud security description. Do not mask path failures while
continuing to expose successful absolute paths. This is a justified pre-1.0 compatibility
break and should carry a migration note.

Required tests should prove the default SDL lacks `path`, remote-storage failures still
degrade safely for retained fields, and any explicit opt-in is absent unless deliberately
declared.

## S6 — High: checked-in Django resolutions are security-stale

### Evidence

[`uv.lock #"version = \"5.2.14\""`][uv-lock] resolves Django 5.2.14 for older Python
and Django 6.0.5 for newer Python. As of the audit date, the Django project has issued
[security releases 5.2.16 and 6.0.7][django-5-2-16-security] and urges users to upgrade.
The July release includes CVE-2026-48588, a shared-cache private-data exposure affecting
Django versions before those patched releases. [Django 5.2.15][django-5-2-15] and 6.0.6
also fixed five security issues in the versions currently locked.

The “latest” CI cell upgrades Django and is useful, but lint, ordinary local syncs, and
several workflow steps still consume the stale lock. No dependency-audit command,
scheduled security workflow, or dependency-update configuration was found.

The exact Django 5.2.0 / Python 3.10 CI node is still required. It proves API
compatibility with the advertised floor and must not be removed. Compatibility support
and secure deployment support are different contracts: running an old release in an
isolated CI cell does not mean recommending it for production.

### Required root correction

- Refresh the lock to at least Django 5.2.16 and 6.0.7 for their respective Python
  markers.
- Keep the exact 5.2.0 compatibility cell, but label it as compatibility-only and do not
  use it for deployment examples or security assertions.
- Add an automated dependency audit on pull requests and a scheduled run. Audit the
  production dependency resolution and optional extras; handle the intentional 5.2.0
  compatibility environment separately and explicitly.
- Add automated update coverage for Python dependencies and GitHub Actions.
- State that production users must install the newest security patch in their chosen
  supported Django series. The package's `Django>=5.2` compatibility floor is not a
  secure-version recommendation.

## S7 — Medium: CI authority and supply-chain pins exceed what is needed

### Evidence

The test job in
[`.github/workflows/django.yml #"permissions:"`][django-workflow] grants
`contents: write`. The only apparent consumer is the Coveralls upload on pushes to
`main`; repository-content write authority is not required to submit coverage data.
`actions/checkout` also persists its credential by default, so later test steps can reach
the job token through Git even though `GITHUB_TOKEN` is only explicitly exported on the
Coveralls step. Fork pull requests receive a restricted token, but same-repository pull
requests and pushes do not justify this authority. Running repository code and newly
installed tooling with an unnecessarily write-capable credential increases the impact of
a compromised dependency or malicious merged change.

The repository carefully pins `astral-sh/setup-uv` by commit, but first-party actions are
referenced by mutable major tags (`actions/checkout@v6`,
`actions/configure-pages@v6`, and the Pages upload/deploy actions). The Postgres job also
uses mutable `postgres:16` rather than an image digest.

### Required root correction

- Set top-level workflow permissions to `contents: read`.
- Grant only the exact additional permission to the one step/job that demonstrably needs
  it. Do not retain `contents: write` for Coveralls without evidence it is required.
- Set `persist-credentials: false` on checkout in every job that never pushes.
- Pin every action to a reviewed full commit SHA and keep the readable version comment.
- Pin the Postgres image by digest and update it through an automated, reviewed process.
- Add `timeout-minutes` to every networked/test job, not only Pages jobs.

This is defense in depth rather than a currently demonstrated repository takeover. The
important correction is to remove unnecessary capability before a separate compromise
can use it.

## S8 — Medium: the debug extension does not fail closed under `DEBUG=False`

### Evidence

[`django_strawberry_framework/extensions/debug.py::DjangoDebugExtension`][debug-extension]
returns interpolated SQL values, exception messages, exception types, and traceback paths.
The documentation correctly warns never to enable it on an internet-facing schema.
However, the implementation intentionally operates independently of Django's `DEBUG`
setting. A single production schema-list entry silently activates the disclosure.

Documentation is not a sufficient guard for a response feature whose purpose is to
publish secrets and internal paths.

### Required root correction

At operation start, fail closed when `settings.DEBUG` is false. If a maintainer has a
rare, controlled reason to run it there, require an explicit constructor acknowledgement
such as:

```python
extensions=[
    lambda: DjangoDebugExtension(allow_unsafe_production=True),
]
```

The factory preserves the required fresh-per-operation instance. A global setting that
silently permits every schema is broader and less auditable.

Also cap the number and serialized byte size of SQL and exception rows so the diagnostic
cannot amplify an already large operation into an enormous response.

Required tests: `DEBUG=False` rejects by default, the explicit acknowledgement works,
fresh-instance isolation remains intact, payload limits truncate deterministically, and
the normal aggregate fakeshop schema remains debug-free.

## S9 — Medium: the request parser accepts UTF-16/32 network JSON

### Evidence

[`django_strawberry_framework/_cross_web_patches.py::_patched_body`][cross-web-patch]
returns raw bytes so `json.loads` can auto-detect encodings. Current source and live tests
deliberately treat BOM-less UTF-16/32, BOM-bearing UTF-16/32, and UTF-8 with a BOM as
successful GraphQL HTTP requests.

That description misapplies RFC 8259. Network JSON exchanged outside a closed ecosystem
must be UTF-8 under [RFC 8259][rfc-8259]. Python's decoder accepting additional
encodings is an implementation feature, not the wire contract. Accepting representations
that proxies, WAFs, access logs, body scanners, or another framework path interpret as
UTF-8 creates a parser differential and weakens request normalization.

### Required root correction

Decode request bytes explicitly with strict UTF-8 before `json.loads`, translate
`UnicodeDecodeError` to the existing controlled `400`, and keep sync/async behavior
identical. Decide and document one policy for a UTF-8 BOM: RFC 8259 permits parsers to
ignore it but does not require them to, so accepting or rejecting that BOM can be valid;
accepting UTF-16/32 is not the interoperable HTTP contract.

Invert the current UTF-16/32 success tests to `400`, preserve ordinary UTF-8 success, and
test malformed UTF-8 plus the chosen UTF-8-BOM direction.

## S10 — Medium: production exception masking remains opt-in

### Evidence

[`SECURITY.md #"Mask resolver errors in production"`][security] accurately warns that
unhandled resolver and hook exceptions are returned to clients unless the consumer adds
`MaskErrors` or overrides `Schema.process_errors`. A focused `DjangoSchema.execute_sync`
probe confirmed that `ValueError("internal tenant secret /srv/private")` returns that
literal message to the GraphQL client.

This is standard graphql-core behavior and is documented, so it is not an undisclosed
vulnerability. It remains a weak default for the package's required schema class:
[`django_strawberry_framework/schema.py::DjangoSchema`][schema] centralizes mutation
integrity but offers no production error policy.

### Required root correction

Give `DjangoSchema` a first-class production error policy. Under `DEBUG=False`, unexpected
exceptions should log server-side with a correlation identifier and return a stable,
non-sensitive message. Deliberate client-facing framework errors—validation envelopes and
audited `GraphQLError` codes—must retain their contract. Consumer code remains trusted and
may explicitly opt out, but a production deployment should not become unsafe merely by
forgetting one Strawberry extension.

Tests must distinguish parse/validation errors, audited client-safe GraphQL errors,
permission denials, and unexpected resolver/hook exceptions. Verify sync/async parity and
that the correlation identifier—not the sensitive original message—reaches the client.

## S11 — Medium: long-lived WebSockets retain a stale session actor

### Evidence

The router authenticates a WebSocket scope at connection establishment. GraphQL
operations on that connection continue to read the same `scope["user"]`. A logout,
password reset, account disable, or session revocation elsewhere does not automatically
refresh the established scope. Channels itself documents periodic `get_user(scope)` for
long-running consumers in its [authentication guidance][channels-auth].

The framework handles logout initiated on the same supported WebSocket carefully, but
that does not cover revocation from another request or administrative action.

### Required root correction

Provide a per-operation authentication revalidation hook for cookie/session WebSockets,
enabled by the secure router profile. It should reload the session actor before execution
and close or reject the operation when the session is no longer valid. A bounded cache
window may be configurable for deployments that accept a short revocation delay to avoid
one auth query per operation, but the delay must be explicit.

At minimum, document a maximum connection lifetime and a consumer-class injection seam so
applications can enforce stronger revocation. S1's router redesign should include that
transport configurability rather than freezing the upstream consumer classes.

Required tests should establish a socket, revoke/flush/disable through a separate request,
then prove the next operation is denied without reconnecting.

## S12 — Low/documentation: consolidate the deployment contract

Several facts are individually documented but not assembled into one auditable production
checklist:

- Relay GlobalIDs are encodings, not capabilities. The model strategy reveals a decodable
  model label and predictable primary key. Visibility checks are the authorization
  boundary; applications must never treat possession of a GlobalID as permission.
- Upload safety is more than scalar typing: body size, file count, per-file size,
  extension/content validation, malware quarantine, storage permissions, download
  `Content-Disposition`, and signed/private URL policy remain deployment responsibilities.
- `DjangoFileType.name` may expose a storage object key, and `url` may be public or signed
  depending on the backend.
- Introspection, GraphiQL, GET queries, CORS, trusted proxy headers, HTTPS/HSTS, secure
  cookies, SameSite policy, cache policy, and rate limiting need explicit production
  directions.
- Login/register are intentionally anonymous surfaces. The existing warning about
  throttling is correct; add a concrete integration example and a testable deployment
  expectation.
- The fakeshop has `DEBUG=True`, a checked-in secret, GraphiQL, debug toolbar, multipart
  uploads, and many intentional `permission_classes = []` demonstrations. Those are
  appropriate fixtures only if the repository says conspicuously that the project must
  never be deployed and cannot be made production-ready by changing only `DEBUG`.

Add a “production security profile” section to [`SECURITY.md`][security] and
[`docs/README.md`][docs-readme], plus a `manage.py check --deploy`-style checklist where
framework-specific conditions can be checked mechanically.

The live fakeshop suite should add:

- `Client(enforce_csrf_checks=True)` directions for a session-authenticated query,
  mutation, login/logout, and multipart upload;
- production-profile schema tests with IDE/GET/introspection/error masking controls;
- upload boundary tests;
- cache-header and `Vary` assertions; and
- a pin that the development settings cannot accidentally be imported as a production
  settings module without a loud failure.

## Security strengths confirmed

The review did not find a reason to weaken the following existing designs:

- Generated model/form/serializer mutations are deny-by-default unless the consumer
  explicitly supplies `permission_classes = []`.
- Permission hook results must be real booleans; accidental truthy objects and awaitable
  mismatches fail closed.
- Update/delete/refetch paths locate through visibility policy and collapse hidden versus
  missing rows where required.
- Relation IDs are type-checked and visibility-checked before writes.
- Generated writes are alias-pinned, transaction-wrapped, row-locked where required, and
  rolled back when GraphQL value completion fails.
- Serializer hooks receive immutable views and cannot replace authoritative input,
  instance, alias, or request state.
- Cascading visibility rejects unsupported forward relation shapes instead of silently
  skipping them.
- Keyset cursors use authenticated deterministic encryption, key rotation fallback, and
  ordering fingerprints rather than exposing raw pagination state.
- Lateral SQL quotes identifiers and parameterizes values, with conservative structural
  fallback.
- WebSocket handshakes already reject mismatched and missing Origin headers against
  `ALLOWED_HOSTS`.
- Login failures intentionally collapse unknown user, wrong password, inactive user, and
  backend denial into one response shape.
- Registration excludes privilege-control fields and hashes the password.
- Optimizer and metadata caches inspected in this pass are bounded or tied to schema
  finalization rather than growing per arbitrary request.

These controls are a good foundation. The priority is to put an equally strong boundary
around transport and resource consumption, where the current framework still delegates
too much to accidental deployment configuration.

## Recommended correction order

1. Redesign the Channels router so Django owns all HTTP requests, then add exact route,
   Host, CSRF, cache, header, IDE, and GET tests.
2. Add transport body limits and the central request resource-policy object.
3. Make collection and variable cardinality consume that policy; change Relay many-side
   defaults to bounded connections.
4. Remove `DjangoFileType.path` from the safe generated output.
5. Refresh Django locks and add dependency/security automation.
6. Harden CI permissions and immutable dependency/action pins.
7. Make debug disclosure and unexpected-error disclosure fail closed under
   `DEBUG=False`.
8. Normalize network JSON to UTF-8 and add WebSocket actor revalidation.
9. Fold the complete deployment contract into `SECURITY.md`, the user guide, and live
   acceptance tests.

Do not split these into “ship the warning now, fix the architecture later” work. Warnings
are useful only alongside the root correction; they are not substitutes for it.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[django-workflow]: ../.github/workflows/django.yml
[readme]: ../README.md
[security]: ../SECURITY.md
[uv-lock]: ../uv.lock

<!-- docs/ -->

[docs-readme]: README.md
[feedback]: feedback.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

[converters]: ../django_strawberry_framework/types/converters.py
[cross-web-patch]: ../django_strawberry_framework/_cross_web_patches.py
[debug-extension]: ../django_strawberry_framework/extensions/debug.py
[list-field]: ../django_strawberry_framework/list_field.py
[relay]: ../django_strawberry_framework/relay.py
[routers]: ../django_strawberry_framework/routers.py
[schema]: ../django_strawberry_framework/schema.py
[type-base]: ../django_strawberry_framework/types/base.py

<!-- tests/ -->

[test-routers]: ../tests/test_routers.py

<!-- examples/ -->

[fakeshop-schema]: ../examples/fakeshop/config/schema.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

[channels-auth]: https://channels.readthedocs.io/en/stable/topics/authentication.html
[django-5-2-15]: https://docs.djangoproject.com/en/5.2/releases/5.2.15/
[django-5-2-16-security]: https://www.djangoproject.com/weblog/2026/jul/07/security-releases/
[django-security]: https://docs.djangoproject.com/en/5.2/topics/security/
[rfc-8259]: https://www.rfc-editor.org/rfc/rfc8259
