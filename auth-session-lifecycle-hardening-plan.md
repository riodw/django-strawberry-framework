# Auth session-lifecycle hardening plan

Status: implementation-ready research plan; no production or test code has been changed.

Primary owner: [`django_strawberry_framework/auth/mutations.py`][auth-mutations].

Supporting boundary: [`django_strawberry_framework/utils/permissions.py`][utils-permissions], whose
`ChannelsRequestAdapter` is deliberately sufficient for request reads but is not a safe substitute
for an `HttpRequest` during session mutation.

## Objective

Make `login_mutation()` and `logout_mutation()` preserve Django's authentication-backend contract,
session-fixation defenses, actor state, and persistence semantics on every transport the package
claims to support. The resolver must never report success while the request/scope and durable
session disagree.

The work covers:

- anonymous, same-user, different-user, and auth-hash-mismatch login rotation;
- Channels HTTP and WebSocket transport differences;
- authentication-backend selection and backend-defined inactive-user policy;
- public account-enumeration behavior without false constant-time claims;
- malformed credentials without normalization, crashes, or credential leakage;
- same-scope concurrent login/logout;
- failures after successful authentication but before durable session establishment;
- logout failures that cannot prove durable invalidation.

The public factories, GraphQL argument names, payload shapes, permission defaults, and failed-login
envelope remain unchanged.

## Research baseline

This plan was checked against the current local implementation and tests in
[`auth/mutations.py`][auth-mutations], [`auth/queries.py`][auth-queries],
[`utils/permissions.py`][utils-permissions], [`tests/auth/test_mutations.py`][test-auth-mutations],
[`tests/test_routers.py`][test-routers], and the live
[`test_auth_api.py`][test-auth-api]. It also follows the shipped decisions recorded in
[`spec-040`][spec-040] and [`spec-041`][spec-041].

The upstream contract was verified against:

- [Django 5.2 authentication documentation](https://docs.djangoproject.com/en/5.2/topics/auth/default/):
  `authenticate()` tries compatible backends in order, `PermissionDenied` stops the search,
  `login()` records the selected backend, and `logout()` completely clears the session;
- [Django 5.2 session documentation](https://docs.djangoproject.com/en/5.2/topics/http/sessions/):
  `cycle_key()` is the fixation defense, `flush()` removes the current data and key, concurrent
  deletion can interrupt a later response save, and signed-cookie sessions cannot revoke a stolen
  cookie on logout;
- [Django 5.2 custom-backend documentation](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/):
  the default `ModelBackend` rejects inactive users, custom backends may intentionally allow them,
  backend ordering is policy, and Django does not provide brute-force rate limiting;
- [Channels 4.3.2 authentication documentation](https://channels.readthedocs.io/en/stable/topics/authentication.html):
  Channels owns async scope-based `login()` / `logout()`, and long-lived/WebSocket session changes
  are not automatically saved;
- [Channels 4.3.2 session documentation](https://channels.readthedocs.io/en/stable/topics/sessions.html):
  HTTP response start persists modified sessions and can send a replacement cookie, while a
  WebSocket cannot do either automatically after the handshake.

The installed dependency floor is Django 5.2 with Django 6.0 also advertised, Channels 4.3.2 as a
soft dependency, and Strawberry GraphQL 0.316.0 or newer. The implementation must hold on both
advertised Django versions; it must not key behavior to the locally installed Django 6.0 alone.

Only Django 6.0.5 is installed locally, so the Django 5.2 behavior above is derived from source and
release-note reading and remains unverified until Commit 6 runs the 5.2/6.0 matrix. No public API this
plan calls is expected to differ between the two versions: the `login()`/`logout()`/`authenticate()`
signatures, `SessionBase.cycle_key()`/`flush()`, the `BACKEND_SESSION_KEY` contract, and the
`channels.auth` `login`/`logout` signatures are stable across 5.2 and 6.0. Commit 6 must confirm this
rather than assume it.

## Current root causes

### 1. A read adapter is being used as a write transport

`request_from_info()` wraps a Channels context in `ChannelsRequestAdapter`. The adapter exposes
read-only `user` and `session` properties backed by the ASGI scope. Passing it to
`django.contrib.auth.login()` or `logout()` is not a supported emulation:

- Django assigns `request.user`; the adapter's read-only property cannot accept that assignment;
- Django's login path rotates CSRF state through `HttpRequest`-specific state that a Strawberry
  Channels request does not carry;
- a failure can occur after the session has already been cycled, flushed, or populated;
- assigning an attribute on a wrapper would still not guarantee `scope["user"]` changed;
- WebSocket persistence is not performed by response middleware.

The root fix is a transport-owned mutation boundary, not a setter added to the adapter and not an
`AttributeError` fallback around the current resolver.

### 2. Resolver success currently precedes no explicit persistence guarantee

The Django request path relies on middleware to persist after resolver completion. That is normal
for a view, but this mutation promises a successful session transition in its payload. The Channels
path has an even sharper gap because WebSocket changes are never automatically saved. A successful
authentication result therefore needs a second, explicit establishment phase whose failure cannot
fall through to a success payload.

### 3. WebSocket cookies impose a real support boundary

Login normally cycles the session key. A WebSocket cannot send the replacement session cookie
after its handshake, so a login mutation could authenticate only the current in-memory scope while
silently failing to establish a reusable browser session. The harm is worse than an in-memory-only
authentication: on a server-side session engine, `channels.auth.login` over an established WebSocket
would still write the rotated session row to the store, durably persisting an orphaned server-side
session that the browser can never claim because it never receives the replacement cookie. Logout is
supportable for server-side
session engines because deleting the record invalidates the old cookie without sending a new one.
It is not supportable for Django's signed-cookie engine because there is no server-side record to
revoke and no way to delete or replace the browser cookie over an established socket.

The implementation must encode this boundary rather than claim a success it cannot deliver.

### 4. Concurrency needs a scoped guarantee, not a global fiction

Several operations can execute concurrently on one Strawberry WebSocket consumer and mutate the
same scope/session object. Those transitions must be serialized. Separate HTTP requests, separate
WebSocket connections, processes, and hosts cannot be globally serialized by this package; their
conflict behavior remains the configured Django session backend's contract. Tests and docs must not
promise “last mutation wins” across independent requests.

## Security invariants

1. Permission checks finish before credential authentication begins.
2. Authentication success does not imply mutation success; the session transition and required
   persistence must complete first.
3. A success payload is constructed before the first session mutation, then returned only after the
   transport transition succeeds.
4. A failed login transition never leaves the current request/scope authenticated as the candidate
   user. Cleanup is fail-closed and the original failure remains observable.
5. A failed logout never returns `{ok: true}`. The local actor is made anonymous even when durable
   invalidation cannot be proven, and the persistence failure propagates.
6. Django HTTP keeps Django's native session rotation, backend selection, CSRF rotation, signals,
   and actor assignment.
7. Channels uses Channels' native scope functions. The package does not copy Django or Channels
   private session algorithms.
8. The backend returned by `authenticate()` remains authoritative. The framework does not perform a
   second user lookup, override backend order, or add its own `is_active` rule.
9. Failed authentication for unknown users, wrong passwords, inactive users under `ModelBackend`,
   and backend `PermissionDenied` retains one byte-identical public envelope.
10. The framework makes no constant-time guarantee across arbitrary custom backends. It adds no
    user-existence lookup or response-shape distinction and preserves Django's backend call path for
    every storable credential.
11. Credentials are opaque strings: no trimming, case-folding, Unicode normalization, truncation,
    logging, signal payload, permission payload, or exception text may expose the password.
12. Session mutations on one Channels scope are linearized by one scope-owned async lock. No lock is
    stored in a process-global registry or `ContextVar`.

## Transport contract

Introduce a private transport module, preferably
`django_strawberry_framework/auth/sessions.py`, and keep it out of `auth.__all__`.

The module should resolve one of these explicit modes from the result of `request_from_info()`:

| Context | Login | Logout | Persistence rule |
| --- | --- | --- | --- |
| Django `HttpRequest`, sync execution | supported through Django `authenticate` / `login` | supported through Django `logout` | login is explicitly saved before success; middleware still owns the response cookie |
| Django `HttpRequest`, async execution | supported inside the existing thread-sensitive sync boundary | supported inside the same boundary | same contract as sync HTTP |
| Channels HTTP scope (native async, direct sync bridge for `SyncGraphQLHTTPConsumer`) | supported through `channels.auth.login` | supported through `channels.auth.logout` | explicitly persist before success; Channels response middleware sends/deletes the cookie |
| Channels WebSocket, server-side session engine | reject login before authentication/session mutation | supported through `channels.auth.logout` | `flush()` must durably invalidate the old server-side key; same-scope actor becomes anonymous |
| Channels WebSocket, signed-cookie session engine | reject login | reject logout before mutation | established WebSocket cannot rotate or revoke the browser cookie truthfully |
| Missing session middleware | reject before authentication | reject before reporting an actor or success | actionable transport-specific configuration error |

Channels imports stay lazy and occur only after a real Channels scope has been classified. Ordinary
package import, Django-only auth use, and `django_strawberry_framework.auth` import must remain
Channels-free. If a Channels-shaped context somehow reaches the path without the optional dependency,
raise the same actionable install-hint family used by the router rather than swallowing the failure.

Do not detect the transport by catching `AttributeError` from Django auth. Classify it before any
credential or session work. Begin with an explicit `isinstance(request, ChannelsRequestAdapter)`
branch rather than sniffing for the presence of scope-like attributes: the adapter's `__getattr__`
delegation makes attribute-presence checks unreliable. Only once the request is known to be an
adapter may `scope["type"]` distinguish an HTTP scope from a WebSocket scope; a Django `HttpRequest`
takes the native path. Reject missing/unknown scope types explicitly.

## Resolver state machine

Refactor `_make_auth_field` so it can dispatch a real sync body and a real async body. Do not hide
native Channels async work inside the old all-sync resolver by adding nested `async_to_sync` calls to
the current async implementation. A directly invoked Strawberry `SyncGraphQLHTTPConsumer` may use a
single `async_to_sync` bridge at the private transport boundary; the package router's async consumer
must await Channels natively.

### Login

Run this sequence:

1. Resolve and classify the transport; verify the required session capability.
2. Run `authorize_or_raise()` with only `{"username": username}`.
3. Reject unencodable text through the existing shared storability preflight. The public result is
   the existing undifferentiated failed-login envelope.
4. Call Django's sync or async authentication dispatcher exactly once with the original username,
   password, and request-like object. Do not query the user model locally.
5. On `None`, return the existing failed-login payload without touching the session.
6. Resolve the payload type/slot and construct the success payload before session mutation. A
   payload-construction failure therefore cannot create a session the client never sees.
7. Enter the transport's mutation critical section.
8. Establish the session with the native Django or Channels login function. Allow it to select the
   backend from the `user.backend` annotation produced by authentication.
9. Persist where the transport contract requires it.
10. Only then return the prebuilt success payload.

If steps 8-9 fail after partial mutation, run transport-specific compensation while still holding
the critical section: make the local actor anonymous, remove candidate auth keys or flush the
partially established session, and never return the payload. If cleanup also fails, retain the
original establishment failure and chain/report the cleanup failure without claiming a clean durable
state.

### Logout

Run this sequence:

1. Resolve/classify the transport and reject unsupported WebSocket/session-engine combinations
   before mutation.
2. Run the permission gate.
3. Resolve the payload class without mutating the session.
4. Enter the transport critical section, read the actor under the lock, and construct the
   `{ok, errors}` payload before teardown so `ok` describes the state actually being transitioned
   and payload construction cannot fail after logout.
5. Call the native Django or Channels logout operation unconditionally, including for anonymous
   sessions with residual data.
6. Complete the transport's durability requirement.
7. Return the payload using the under-lock actor state.

On failure, do not return `ok`. Make the current request/scope actor anonymous where possible and
propagate the error. For a storage outage, document the unavoidable distinction between local
fail-closed state and unproven revocation of a previously durable remote session.

## Session rotation and backend rules to preserve

Tests must pin Django's three login branches on both ordinary Django HTTP and Channels HTTP:

- anonymous to authenticated: cycle the session key and preserve non-auth anonymous data;
- authenticated as a different user: flush the old session and its data, then establish a new key;
- same user with a matching session auth hash: retain the session key;
- same user with a mismatched auth hash: flush and replace the session.

Also pin:

- the backend path stored in `BACKEND_SESSION_KEY` is the exact backend that authenticated;
- multiple compatible backends are tried in configured order and the first success wins;
- `PermissionDenied` stops backend iteration and maps to the same failed-login envelope;
- a backend exception other than Django's normal authentication failure propagates and leaves the
  session untouched;
- multiple backends plus a user lacking a usable backend annotation fails before a success response,
  with partial session state compensated;
- default `ModelBackend` rejects inactive users with the ordinary envelope;
- a custom backend that intentionally authenticates an inactive user is honored. The framework must
  not silently replace backend policy with `if not user.is_active`.

## Enumeration and malformed-credential posture

The implementation must preserve one public failure shape, but the tests should avoid flaky wall
clock thresholds masquerading as a timing proof.

Use deterministic assertions instead:

- known-user/wrong-password and unknown-user credentials both enter `authenticate()` once and
  produce byte-identical GraphQL payloads;
- inactive-under-`ModelBackend` and backend `PermissionDenied` produce that same payload;
- storable empty, whitespace, NUL-containing, long, and non-ASCII strings reach the backend
  unchanged unless GraphQL itself rejects the input type;
- missing, `null`, list/object, and other wrong GraphQL types fail validation before the resolver;
- lone-surrogate username/password values retain the existing safe envelope and never reach database
  or password-hasher code that cannot encode them;
- password values never appear in permission-gate data, logs captured by the test, exception text,
  signals emitted by package code, or `repr()` of any new transport/state object.

The docs must say that Django/custom backends own brute-force protection and fine-grained timing
behavior. This package guarantees response indistinguishability and introduces no account lookup;
it does not claim arbitrary backend stacks are constant-time.

## Concurrent mutation policy

For a Channels scope, store one lazily created `asyncio.Lock` under a private, collision-resistant
scope key. All login/logout state changes and persistence for that scope occur under the lock. Actor
capture for logout occurs inside it.

Prove with deterministic barrier-based tests that operations multiplexed on one WebSocket do not
interleave supported session writes. Cover:

- two concurrent logout operations: the first observes the authenticated actor, the second observes
  anonymous state, both serialize, and the final scope/session is anonymous;
- logout racing an attempted WebSocket login: the unsupported login fails before authentication and
  cannot revive or partially mutate the scope.

For the requested concurrent login/logout case across Channels HTTP and Django HTTP requests sharing
one cookie, test the framework's behavior when persistence detects that the other request deleted
the session: propagate the upstream interruption instead of recreating or overwriting the logged-out
session. Do not add a process-local lock keyed by session ID; it would give a false guarantee in
multi-process deployments and leak lock entries.

## Failure-injection matrix

Every row must assert “no success payload” plus request/scope and durable-session state:

| Failure point | Required result |
| --- | --- |
| permission gate | authentication not called; session unchanged |
| malformed credential preflight | authentication not called; standard failed-login envelope; session unchanged |
| backend returns `None` | standard failed-login envelope; session unchanged |
| backend raises | top-level execution error; session unchanged |
| payload construction after authentication | top-level execution error; session unchanged |
| backend selection during login raises | no success; candidate actor removed; partial auth keys removed/flushed |
| session cycle/flush raises | no success; local actor anonymous; original failure observable |
| login signal receiver raises after auth keys were written | compensation runs; no success; no candidate actor remains |
| explicit session save raises | compensation runs; no success; no candidate actor remains |
| logout signal receiver raises | no `ok` payload; no false durable-invalidation claim |
| logout flush/delete raises | no `ok` payload; local actor anonymous where possible; persistence failure propagates |
| cleanup after a primary failure also raises | primary error retained with cleanup error chained; no success |

Use real session stores, signals, schema execution, and communicators wherever reachable. Mock only
the precise failure behavior that cannot be induced safely with a real backend/store.

This matrix received the least prior verification, so before implementation each injection point's
reachability must be confirmed against the real code path — for example, that a login-signal receiver
can fail after the auth keys are already written, and that a cleanup failure genuinely chains onto the
primary establishment failure. Any row that proves unreachable with a real store must document why it
is mocked rather than silently substitute a mock for an untested contract.

## Linear implementation and commit plan

Each commit includes its production change, directly corresponding tests, and any source comments it
invalidates. Do not land a production-only commit followed by a test-only repair.

### Commit 1 — `Add a transport-owned auth session boundary`

Files:

- new `django_strawberry_framework/auth/sessions.py`;
- [`django_strawberry_framework/utils/permissions.py`][utils-permissions];
- new or focused tests under `tests/auth/` and
  [`tests/utils/test_permissions.py`][test-utils-permissions].

Work:

- add explicit Django HTTP / Channels HTTP / Channels WebSocket classification that begins with an
  `isinstance(request, ChannelsRequestAdapter)` branch before reading `scope["type"]`, because the
  adapter's `__getattr__` delegation makes attribute-presence sniffing unreliable; `scope["type"]`
  then distinguishes the HTTP scope from the WebSocket scope;
- expose only the minimal adapter metadata required by the private transport. Session-engine
  detection (signed-cookie versus server-side) is a settings/session-store read, not adapter
  metadata, and must not be bolted onto the adapter;
- add lazy Channels loading with the established install hint;
- validate session presence and scope type before mutation. A missing session middleware is
  detectable today as `adapter.session is None`; without a pre-check it currently surfaces downstream
  as a raw `AttributeError` (`None.cycle_key()`), so the explicit pre-check converts that into the
  actionable transport-specific configuration error. This missing-session error message is *not* part
  of the byte-compatible failed-login envelope promise (only the failed-login envelope is), so its
  wording may be chosen freely — but it must keep the substring `"session"`, because
  [`tests/auth/test_mutations.py`][test-auth-mutations]
  `test_sessionless_request_surfaces_djangos_own_error` (lines ~459-473) asserts that substring; if a
  new wording drops it, update that test in this same commit;
- introduce the private per-scope `asyncio.Lock` here (Commit 4 only holds it across phases).
  `ChannelsRequestAdapter.scope` is typed as a read-only `Mapping`
  ([`utils/permissions.py`][utils-permissions] line 121), but lock storage requires a mutable dict, so
  require/assert a `MutableMapping` scope before storing the lock and define the rejection behavior
  when the scope is not mutable (a loud, actionable error, never a silent fallback to an unserialized
  path);
- add the signed-cookie WebSocket capability check;
- keep `request_from_info()` and the adapter's read behavior backward-compatible.

Exit gate: classification and soft-dependency tests pass conceptually; importing the package/auth
submodule does not import Channels.

### Commit 2 — `Make login persistence-safe across Django and Channels HTTP`

Files:

- [`django_strawberry_framework/auth/mutations.py`][auth-mutations];
- [`django_strawberry_framework/auth/queries.py`][auth-queries], because `_make_auth_field` is shared
  with `current_user` (queries.py line 111), so the sync/async resolver-body split ripples into the
  query field builder;
- new private transport module from Commit 1;
- [`tests/auth/test_mutations.py`][test-auth-mutations];
- [`tests/test_routers.py`][test-routers];
- [`examples/fakeshop/test_query/test_auth_api.py`][test-auth-api] for live Django HTTP behavior.

Work:

- give the auth field builder separate sync/async resolver bodies;
- keep the shared `_make_auth_field` seam working for `current_user`: splitting the resolver body
  must not break `current_user` dispatch on either the sync or async path;
- implement the staged login state machine and explicit persistence boundary;
- preserve backend annotation/selection and backend-defined inactive-user policy;
- add rotation, backend-order, malformed-input, and failure-compensation coverage;
- add a real Channels `HttpCommunicator` login round trip that asserts `Set-Cookie`, stored auth
  keys/backend, and authenticated follow-up request behavior.

Exit gate: no login path returns the user payload before persistence; all four rotation branches and
the backend matrix are pinned.

### Commit 3 — `Make logout durable and fail closed on every supported transport`

Files:

- [`django_strawberry_framework/auth/mutations.py`][auth-mutations];
- private transport module;
- [`tests/auth/test_mutations.py`][test-auth-mutations];
- [`tests/test_routers.py`][test-routers];
- [`examples/fakeshop/test_query/test_auth_api.py`][test-auth-api].

Work:

- implement under-lock actor capture and native transport logout;
- preserve anonymous-session residue flushing on Django/Channels HTTP;
- add Channels HTTP logout cookie/session invalidation;
- add real WebSocket authenticated-cookie logout, same-socket `me: null`, and reconnect-with-old-cookie
  invalidation for a server-side session engine;
- reject WebSocket login and signed-cookie WebSocket logout before mutation with actionable errors;
- inject signal/flush/persistence failures and prove no false `{ok: true}`.

Exit gate: authenticated logout over the Channels adapter is no longer routed through Django's
`HttpRequest` function, and the old cookie cannot authenticate a new connection on supported
server-side engines.

### Commit 4 — `Serialize same-scope auth mutations and pin race behavior`

Files:

- private transport module;
- [`tests/test_routers.py`][test-routers];
- focused package tests under `tests/auth/` only for failure shapes unreachable through a real
  communicator.

Work:

- hold the scope lock across actor capture, session mutation, persistence, and compensation;
- add deterministic multiplexed WebSocket race tests;
- add concurrent HTTP session-deletion/interruption tests that preserve upstream behavior;
- prove locks are scope-owned and released after cancellation/failure.

Exit gate: no same-scope split brain; no package-global lock registry or cross-process promise.

### Commit 5 — `Document the hardened auth transport contract`

Files:

- [`README.md`][readme]: required, not conditional. Line 67 carries the literal
  "constrained to the session transport (no Channels)" claim that this work replaces;
- [`docs/README.md`][docs-readme]: line 132 carries a parallel boundary claim;
- [`docs/GLOSSARY.md`][glossary]: DB-generated. Its four stale boundary claims (lines ~279, 307, 496,
  and 1414) must be changed in the fakeshop glossary app database and re-rendered via
  `scripts/build_glossary_md.py`; the file is never hand-edited;
- [`docs/TREE.md`][tree];
- [`KANBAN.md`][kanban] and its generated HTML only through the repository's Kanban source/render
  workflow, if this work is assigned a card before implementation.

There are six live boundary-claim sites that must be updated coordinately so no stale claim survives:
`README.md` line 67, `docs/README.md` line 132, and the four `docs/GLOSSARY.md` sites (lines ~279,
307, 496, 1414). The shipped specification records [`spec-040`][spec-040] and [`spec-041`][spec-041]
are historical and must **not** be rewritten.

Work:

- replace “session transport only (no Channels)” and “mutating path unverified” with the exact
  support matrix at every one of the six live sites above;
- for the four GLOSSARY sites, edit the glossary app database and regenerate through
  `scripts/build_glossary_md.py` rather than editing `docs/GLOSSARY.md` directly;
- document WebSocket login and signed-cookie logout rejection;
- document backend-owned inactive-user/rate-limit/timing policy;
- document the scoped concurrency guarantee and storage-failure limit;
- remove/update stale source comments in `auth/mutations.py`, `auth/queries.py`, and the adapter;
- do not edit `CHANGELOG.md` unless the maintainer explicitly requests it, and do not rewrite the
  shipped spec-040/spec-041 records.

Exit gate: no standing doc claims broader WebSocket persistence than the tests prove, and all local
links use the repository's canonical reference-link block.

### Commit 6 — `Verify the authentication lifecycle matrix`

This is a verification gate, not a code-only cleanup commit. Fix any discovered defect in the commit
that introduced it before finalizing history.

Required checks after every edit:

```text
uv run ruff format .
uv run ruff check --fix .
git diff --check
```

Also run the trailing-comma/spec-link checks used by the repository. Add the following targeted test
commands to the handoff, but do not execute pytest unless the maintainer explicitly authorizes it,
per [`AGENTS.md`][agents]:

```text
uv run pytest tests/auth/test_mutations.py tests/utils/test_permissions.py tests/test_routers.py
uv run pytest examples/fakeshop/test_query/test_auth_api.py
```

Before push, run the project-supported Django 5.2 and Django 6.0 matrix, the default full suite with
100% package coverage, and the existing soft-dependency absence/degraded-install router tests.

## Acceptance checklist

- [ ] Existing public imports, factory kwargs, SDL, payload field names, and failure message remain
      byte-compatible.
- [ ] Anonymous Django/Channels HTTP login rotates the session key and preserves anonymous data.
- [ ] Different-user and auth-hash-mismatch login flush; same-user matching-hash login retains the
      key.
- [ ] Selected backend path is persisted exactly and custom inactive-user policy is honored.
- [ ] Wrong password, unknown user, default-backend inactive user, and `PermissionDenied` are one
      public envelope without a package-added account lookup.
- [ ] Malformed credentials cannot crash encoding/backend code or expose the password.
- [ ] Channels HTTP login/logout round trips through real middleware and cookies.
- [ ] WebSocket logout invalidates the old server-side session, updates the current scope actor, and
      remains invalid after reconnect.
- [ ] WebSocket login and signed-cookie WebSocket logout fail before mutation.
- [ ] Same-scope concurrent mutations are serialized; cancellations release the lock.
- [ ] Every post-authentication/pre-persistence failure returns no success and compensates local
      actor/session state.
- [ ] Missing middleware, optional dependency absence, unknown scope types, and persistence failures
      are loud and actionable.
- [ ] No Django/Channels private login algorithm is copied into the package.
- [ ] No unrelated dirty worktree file is staged, reformatted by hand, reverted, or committed.

## Explicit non-goals

- token/JWT authentication, MFA, password reset/change, registration auto-login, or new public auth
  settings;
- globally serializing independent requests, connections, processes, or hosts;
- promising constant-time behavior for arbitrary custom authentication backends;
- making signed-cookie WebSocket logout revocable when Django itself has no server-side revocation
  record;
- making WebSocket login appear durable without a protocol capable of returning the rotated cookie;
- replacing Django/Channels signals, backend selection, session stores, or CSRF policy with framework
  inventions.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[agents]: AGENTS.md
[readme]: README.md
[kanban]: KANBAN.md

<!-- docs/ -->

[docs-readme]: docs/README.md
[glossary]: docs/GLOSSARY.md
[tree]: docs/TREE.md

<!-- docs/SPECS/ -->

[spec-040]: docs/SPECS/spec-040-auth_mutations-0_0_13.md
[spec-041]: docs/SPECS/spec-041-channels_router-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

[auth-mutations]: django_strawberry_framework/auth/mutations.py
[auth-queries]: django_strawberry_framework/auth/queries.py
[utils-permissions]: django_strawberry_framework/utils/permissions.py

<!-- tests/ -->

[test-auth-mutations]: tests/auth/test_mutations.py
[test-routers]: tests/test_routers.py
[test-utils-permissions]: tests/utils/test_permissions.py

<!-- examples/ -->

[test-auth-api]: examples/fakeshop/test_query/test_auth_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
